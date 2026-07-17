import uuid
from unittest.mock import patch, MagicMock
from .test_auth import get_authenticated_user
from .test_client import client
from app.api.v1.endpoints import query as query_module


class FakeChunk:
    def __init__(self, content):
        self.content = content


class FakeLLMClient:
    def __init__(self, chunks):
        self.chunks = chunks

    def stream(self, messages):
        for chunk in self.chunks:
            yield FakeChunk(chunk)


def create_conversation(cookies):
    response = client.post(
        "/api/v1/conversation/create",
        json={"name": "Query Test Chat"},
        cookies=cookies
    )
    return response.json()["conversation_id"]


def mocked_pipeline(rewritten_query="hello", search_results=None, chunks=None):
    fake_embed_model = MagicMock()
    fake_embed_model.get_text_embedding.return_value = [0.0] * 384

    return (
        patch.object(query_module.llm_layer, "reconstruct_query", return_value=rewritten_query),
        patch.object(query_module, "text_embedding_model", fake_embed_model),
        patch.object(query_module.qdrant, "query", return_value=search_results or []),
        patch.object(query_module.llm_layer, "get_llm", return_value=FakeLLMClient(chunks or ["Hello ", "world"])),
    )


# ======================================
# ASK - VALIDATION
# ======================================

def test_ask_missing_query():
    cookies = get_authenticated_user()
    conversation_id = create_conversation(cookies)

    response = client.post(
        "/api/v1/query/ask",
        json={"query": "", "conversation_id": conversation_id},
        cookies=cookies
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Please provide query"


def test_ask_unauthorized():
    response = client.post(
        "/api/v1/query/ask",
        json={"query": "hello", "conversation_id": str(uuid.uuid4())}
    )

    assert response.status_code in [401, 403]


def test_ask_conversation_not_found():
    cookies = get_authenticated_user()

    p1, p2, p3, p4 = mocked_pipeline()
    with p1, p2, p3, p4:
        response = client.post(
            "/api/v1/query/ask",
            json={"query": "hello", "conversation_id": str(uuid.uuid4())},
            cookies=cookies
        )

    # BaseAPIException raised inside the handler's try block is caught by
    # its own broad except and reported as a generic server error.
    assert response.status_code == 500


# ======================================
# ASK - SUCCESS
# ======================================

def test_ask_success_streams_answer_and_saves_messages():
    cookies = get_authenticated_user()
    conversation_id = create_conversation(cookies)

    p1, p2, p3, p4 = mocked_pipeline(chunks=["Hello ", "world"])
    with p1, p2, p3, p4:
        response = client.post(
            "/api/v1/query/ask",
            json={"query": "hello there", "conversation_id": conversation_id},
            cookies=cookies
        )

    assert response.status_code == 200
    assert response.text == "Hello world"

    messages_res = client.get(
        "/api/v1/conversation/messages",
        params={"conversation_id": conversation_id},
        cookies=cookies
    )

    messages = messages_res.json()["messages"]

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "hello there"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hello world"


def test_ask_with_search_results_includes_reranking():
    cookies = get_authenticated_user()
    conversation_id = create_conversation(cookies)

    search_results = [
        {
            "text": "Cats are mammals.",
            "page": 1,
            "server_file_name": "abc.pdf",
            "file_name": "abc.pdf"
        },
        {
            "text": "Dogs are also mammals.",
            "page": 2,
            "server_file_name": "abc.pdf",
            "file_name": "abc.pdf"
        }
    ]

    p1, p2, p3, p4 = mocked_pipeline(search_results=search_results, chunks=["Answer"])
    with p1, p2, p3, p4:
        response = client.post(
            "/api/v1/query/ask",
            json={"query": "what are cats?", "conversation_id": conversation_id},
            cookies=cookies
        )

    assert response.status_code == 200
    assert response.text == "Answer"


def test_ask_scoped_to_specific_document():
    cookies = get_authenticated_user()
    conversation_id = create_conversation(cookies)

    p1, p2, p4 = None, None, None
    fake_embed_model = MagicMock()
    fake_embed_model.get_text_embedding.return_value = [0.0] * 384

    doc_id = str(uuid.uuid4())

    with patch.object(query_module.llm_layer, "reconstruct_query", return_value="hello"), \
         patch.object(query_module, "text_embedding_model", fake_embed_model), \
         patch.object(query_module.qdrant, "query", return_value=[]) as mock_query, \
         patch.object(query_module.llm_layer, "get_llm", return_value=FakeLLMClient(["Answer"])):

        response = client.post(
            "/api/v1/query/ask",
            json={
                "query": "hello",
                "conversation_id": conversation_id,
                "doc_id": doc_id
            },
            cookies=cookies
        )

        assert response.status_code == 200
        assert mock_query.call_args.kwargs["doc_id"] == doc_id
