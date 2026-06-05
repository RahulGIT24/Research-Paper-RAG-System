from fastapi import APIRouter,Depends
from app.middleware.auth import get_current_user
from shared_lib.core.exceptions import BaseAPIException
from shared_lib.qdrant.embed_model import EmbedModel
from pydantic import BaseModel
from shared_lib.qdrant.vector_store import QdrantVectorService
from app.lib.llm import LLM
from fastapi.responses import StreamingResponse

class SearchRequest(BaseModel):
    query: str

router = APIRouter()
text_embedding_model = EmbedModel.get_embed_model()
qdrant = QdrantVectorService()
llm_layer = LLM()

@router.post("/ask")
def query_documents(req:SearchRequest,current_user=Depends(get_current_user)):
    if not req.query:
        raise BaseAPIException(message="Please provide query",status_code=400)
    try:
        embeddings = text_embedding_model.get_text_embedding(req.query)
        user_id = current_user['id']
        search_results = qdrant.query(query_embedding=embeddings,user_id=user_id,limit=5)
        context = "\n\n".join([
                f"[Source {i+1} | page {r.get('page')} | file {r.get('source')}]\n{r.get('text','')}"
            for i, r in enumerate(search_results)
        ])
        # print(context)
        messages = llm_layer.get_messages(context=context,query=req.query)
        llm_client = llm_layer.get_llm()
        def generate():
            for chunk in llm_client.stream(messages):
                yield chunk.content
        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        print(e)
        pass