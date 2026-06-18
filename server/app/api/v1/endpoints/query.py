from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from shared_lib.core.exceptions import BaseAPIException
from shared_lib.qdrant.embed_model import EmbedModel
from pydantic import BaseModel
from shared_lib.qdrant.vector_store import QdrantVectorService
from app.lib.llm import LLM
from fastapi.responses import StreamingResponse
from shared_lib.core.config import settings
from shared_lib.models.messages import Messages
from shared_lib.models.conversation import Conversation
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi
import re
from shared_lib.db.session import get_db
from sqlalchemy.orm import Session

class SearchRequest(BaseModel):
    query: str
    doc_id: str | None = None
    conversation_id:str

router = APIRouter()
text_embedding_model = EmbedModel.get_embed_model()
qdrant = QdrantVectorService()
llm_layer = LLM()
cross_encoder = CrossEncoder("BAAI/bge-reranker-base", max_length=512)

def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w\-]+", text.lower())

def _bm25_ranking(query: str, results: list[dict]) -> list[int]:
    corpus = [_tokenize(r.get("text", "")) for r in results]
    bm25   = BM25Okapi(corpus)
    scores = bm25.get_scores(_tokenize(query))
    return sorted(range(len(results)), key=lambda i: scores[i], reverse=True)

def _rrf_fuse(rankings: list[list[int]], k: int = 60) -> list[int]:
    rrf_scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (k + rank + 1)
    return sorted(rrf_scores, key=rrf_scores.get, reverse=True)

def _cross_encode(query: str, results: list[dict], indices: list[int], top_n: int) -> list[dict]:
    candidates = [results[i] for i in indices]
    pairs      = [(query, r.get("text", "")) for r in candidates]
    scores     = cross_encoder.predict(pairs, batch_size=8, show_progress_bar=False)
    ranked     = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
    return [r for _, r in ranked[:top_n]]

def rerank(query: str, results: list[dict], final_top_n: int = 5) -> list[dict]:
    if not results:
        return results

    n = len(results)

    bm25_rank = _bm25_ranking(query, results)

    vector_rank = list(range(n))
    top_10      = _rrf_fuse([vector_rank, bm25_rank])[:10]

    return _cross_encode(query, results, top_10, top_n=final_top_n)

#* to improve: Reduce db calls on saving messages
@router.post("/ask")
def query_documents(req: SearchRequest, current_user=Depends(get_current_user),db: Session = Depends(get_db)):
    doc_id = None
    if not req.query:
        raise BaseAPIException(message="Please provide query", status_code=400)
    if req.doc_id:
        doc_id = req.doc_id
    try:

        user_conversation = db.query(Conversation).filter(Conversation.id == req.conversation_id, Conversation.user_id == current_user['id']).first()

        if not user_conversation:
            raise BaseAPIException(status_code=404,message="User conversation not found")
        
        new_message = Messages(role="user",content=req.query,conversation_id=req.conversation_id)
        db.add(new_message)
        db.commit()
        

        embeddings   = text_embedding_model.get_text_embedding(req.query)
        user_id      = current_user["id"]

        search_results = qdrant.query(
            query_embedding=embeddings,
            user_id=user_id,
            limit=50,
            doc_id=doc_id
        )

        reranked = rerank(req.query, search_results, final_top_n=5)

        context = "\n\n".join([
            f"[Source {i+1} | page {r.get('page')} | access_url {settings.SERVER_URL}/document/view/{r.get('server_file_name')} | filename {r.get('file_name')}]\n{r.get('text', '')}"
            for i, r in enumerate(reranked)
        ])

        messages   = llm_layer.get_messages(context=context, query=req.query)
        llm_client = llm_layer.get_llm()
        def generate():
            final_response = ""
            for chunk in llm_client.stream(messages):
                final_response += chunk.content
                yield chunk.content
            assistant_message = Messages(
                role="assistant",
                content=final_response,
                conversation_id=req.conversation_id
            )
            db.add(assistant_message)
            db.commit()

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        print(e)
        raise BaseAPIException(message="Something went wrong", status_code=500)