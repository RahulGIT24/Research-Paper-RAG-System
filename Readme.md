# Research Paper RAG System

A production-ready Retrieval-Augmented Generation (RAG) API for searching and querying research papers. Built with FastAPI, Qdrant, and a 3-stage CPU-optimised reranker — no GPU required.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [How It Works](#how-it-works)
  - [Document Ingestion](#document-ingestion)
  - [Deduplication Strategy](#deduplication-strategy)
  - [Document Deletion & Vector Cleanup](#document-deletion--vector-cleanup)
  - [Conversational Context Handling (Query Rewriting)](#conversational-context-handling-query-rewriting)
  - [3-Stage Reranker](#3-stage-reranker)
  - [Query Pipeline](#query-pipeline)
  - [LLM Prompting](#llm-prompting)
- [API Reference](#api-reference)
- [Key Design Decisions](#key-design-decisions)
- [Race Condition Handling](#race-condition-handling)

---

## Overview

Most RAG tutorials stop at vector search — embed the query, find the closest chunks, pass them to the LLM. In practice, "closest in vector space" does not mean "best answer to the question."

This system adds a 3-stage reranker on top of Qdrant vector search that runs entirely on CPU:

```
Vector search (top-30)
  → BM25 keyword ranking
  → RRF fusion (top-10)
  → Cross-encoder reranking (top-5)
  → LLM with tight context
```

It also handles multi-user document sharing correctly — when two users upload the same PDF, the document is embedded only once and both users get access via a shared vector store. Conversational follow-up questions are resolved against prior turns before retrieval, so vague references like "it" or "this" still retrieve the right chunks.

---

## Architecture

```
Client
  │
  ▼
FastAPI
  ├── /document/upload  →  PDF ingestion pipeline
  └── /ask              →  Query pipeline
          │
          ▼
    Auth middleware (JWT)
          │
          ├── Qdrant (vector store)
          │     └── Payload: text, page, file_name,
          │                  document_hash_id, user_ids[]
          │
          ├── PostgreSQL (metadata + document hash registry)
          │     └── DocumentHash: hash, status, doc_id
          │
          └── LLM (streaming response)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Vector store | Qdrant |
| Embeddings | FastEmbed (ONNX Runtime) |
| Reranker | sentence-transformers CrossEncoder |
| Keyword ranking | rank-bm25 |
| PDF parsing | PyMuPDF (via LangChain PyMuPDFLoader) |
| Chunking | LlamaIndex semantic splitter |
| Database | PostgreSQL via SQLAlchemy |
| LLM | Streaming via LangChain LLM layer |

---

## Project Structure

```
.
├── app/
│   ├── middleware/
│   │   └── auth.py               # JWT auth, get_current_user
│   ├── lib/
│   │   └── llm.py                # LLM client + prompt builders
│   └── routers/
│       ├── document.py           # upload + ingestion endpoints
│       └── search.py             # /ask endpoint with reranker
│
└── shared_lib/
    ├── core/
    │   ├── config.py             # settings (SERVER_URL, etc.)
    │   └── exceptions.py         # BaseAPIException
    └── qdrant/
        ├── embed_model.py        # FastEmbed wrapper
        └── vector_store.py       # QdrantVectorService
```

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/research-rag.git
cd research-rag

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

**requirements.txt additions specific to this system:**

```txt
fastapi
uvicorn
qdrant-client
fastembed
sentence-transformers
rank-bm25
pymupdf
langchain
llama-index
sqlalchemy
psycopg2-binary
python-jose
```

---

## Environment Variables

```env
SERVER_URL=https://your-api-domain.com
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=research_papers
DATABASE_URL=postgresql://user:password@localhost/dbname
JWT_SECRET=your-secret-key
```

---

## How It Works

### Document Ingestion

When a user uploads a PDF, the following pipeline runs in a background worker:

```
PDF file
  → PyMuPDFLoader (page extraction)
  → LlamaIndex semantic splitter (context-aware chunking)
  → Deduplication check (document_hash_id)
  → FastEmbed (ONNX-based CPU embedding, new docs only)
  → Qdrant upsert with user_ids payload
  → DocumentHash status → "embedded"
```

Semantic chunking is used instead of fixed-size chunking because research papers have natural conceptual boundaries — semantic chunks respect section structure, which produces more coherent retrieval units.

---

### Deduplication Strategy

![Deduplication Strategy](images/dedup.png)

Deduplication operates at two levels:

**Database level** — a SHA-256 hash of the PDF binary is stored in the `DocumentHash` table. On upload, if the hash already exists, ingestion is skipped.

**Qdrant level** — instead of storing vectors per user, vectors are stored per content with a `user_ids` list in the payload:

```python
payload = {
    "text": "...",
    "document_hash_id": "abc123",
    "user_ids": ["user_a", "user_b"],   # shared access list
    "page": 4,
    "file_name": "attention_paper.pdf",
    "server_file_name": "abc123.pdf"
}
```

When a second user uploads the same PDF:
- No re-embedding happens
- No duplicate vectors are created
- Their `user_id` is appended to the existing points' `user_ids` list via `set_payload`

When a user deletes a document:
- Their `user_id` is removed from the `user_ids` list
- The vector is physically deleted only when `user_ids` becomes empty

Query filtering uses Qdrant's array membership check:

```python
FieldCondition(
    key="user_ids",
    match=MatchValue(value=user_id)  # checks if user_id is IN the array
)
```

> **Important:** Create payload indexes on `document_hash_id` and `user_ids` to prevent full collection scans.

```python
client.create_payload_index(collection_name, "document_hash_id", "keyword")
client.create_payload_index(collection_name, "user_ids", "keyword")
```

---

### Document Deletion & Vector Cleanup

Because vectors are shared across users (one PDF → one set of vectors → many `user_ids`), deleting a document is **not** a delete operation by default — it's an access-revocation operation. The underlying vectors and chunks belong to the document, not to any single user, so removing one user must never affect another user still relying on that data.

**Deletion flow:**

```
User deletes document
  → Scroll Qdrant for all points matching document_hash_id + containing user_id
  → For each matching point: remove user_id from its user_ids list
  → If user_ids becomes empty → point has zero owners → delete the point + its vector
  → If user_ids still non-empty → other users still need this data, vector stays, set_payload with updated list
```

```python
def remove_user_from_vectors(self, document_hash_id: str, user_id: str) -> bool:
    scroll_filter = Filter(
        must=[
            FieldCondition(key="document_hash_id", match=MatchValue(value=document_hash_id)),
            FieldCondition(key="user_ids", match=MatchValue(value=user_id)),
        ]
    )

    offset = None
    to_delete = []
    to_update = []

    while True:
        points, offset = self.client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            scroll_filter=scroll_filter,
            with_payload=True,
            limit=1000,
            offset=offset,
        )

        for point in points:
            users = point.payload.get("user_ids", [])
            remaining = [u for u in users if u != user_id]

            if remaining:
                to_update.append((point.id, remaining))
            else:
                to_delete.append(point.id)

        if offset is None:
            break

    # Points with no owners left → delete vector + payload entirely
    if to_delete:
        self.client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=PointIdsList(points=to_delete),
        )

    # Points other users still depend on → just strip this user_id
    for point_id, remaining_users in to_update:
        self.client.set_payload(
            collection_name=settings.QDRANT_COLLECTION,
            payload={"user_ids": remaining_users},
            points=[point_id],
        )

    return True
```

**Why this matters:** without the `user_ids` membership model, deleting a document for one user would either (a) delete the actual vectors, breaking retrieval for every other user who uploaded the same PDF, or (b) require storing a fully duplicate copy of the same embeddings per user, multiplying storage cost with every additional user who happens to upload a paper that already exists in the system.

This is the same scroll-filter pattern used during **upload** (where a `user_id` is *added* to `user_ids` on an existing doc instead of re-embedding) — deletion is just the inverse operation, with the added rule that an empty `user_ids` list means the point itself is now orphaned and safe to physically remove.

> **Pagination note:** `scroll()` returns at most 1000 points per call. For documents with more chunks than that, the loop above follows `next_page_offset` until exhausted — a single unpaginated scroll would silently skip later points on large documents.

---

### Conversational Context Handling (Query Rewriting)

Multi-turn conversations break naive RAG: a follow-up question like *"what are vectors in this?"* embeds to something close to nothing useful on its own — "this" carries no semantic content. Vector search needs a query that stands on its own.

To solve this, every incoming query passes through a lightweight rewriting step **before** retrieval:

```
Query + conversation history
  → Small LLM rewrites into a standalone question
      (resolves "it" / "this" / "they" using prior turns)
  → Embed the standalone question
  → Vector search in Qdrant using the standalone embedding
  → Retrieve relevant chunks
  → Pass [relevant chunks + original query] to the main LLM
  → Stream answer back to client
```

**Why a small/cheap LLM for this step specifically:** rewriting is a narrow, low-reasoning task — it doesn't need the main LLM's full reasoning budget, just enough language understanding to resolve references. Using a small model here keeps the added latency low (this step runs on every single query, including ones that don't actually need history) while reserving the larger model's context window and cost for the part that actually requires deep reasoning: answering the question.

**Why the rewrite is embedded separately from the original query:** the standalone question is what actually goes into the vector store — embedding the raw follow-up ("why is it useful?") would retrieve based on a near-empty semantic signal, while embedding the rewritten version ("why is Word2Vec useful for converting words into vector representations?") retrieves against the real topic being discussed.

**Important distinction:** the *original* user query (not the rewritten one) is still what gets passed to the main LLM alongside the retrieved chunks. The rewrite exists purely to improve retrieval — it's a retrieval-time transformation, not a replacement for the user's actual question. This avoids a subtle failure mode where the rewritten query overwrites nuance in what the user actually asked (e.g. tone, scope, or a slightly different framing than the rewrite assumed).

This mirrors a classifier/rewriter pattern: decide whether context is even needed first, and skip the rewrite step entirely for queries that don't depend on history, to save the extra LLM call on every turn that's already self-contained.

---

### 3-Stage Reranker

Vector search alone is insufficient for research papers because:
- Technical synonyms differ between query and paper ("hallucinations" vs "factual inconsistency")
- Exact terms matter — author names, acronyms, equation notation
- Embedding models compress meaning and lose exact-match signal

The reranker runs in three stages after Qdrant returns 30 candidates:

#### Stage 1 — BM25 Keyword Ranking

Pure statistical scoring. No ML. Rewards exact term matches weighted by rarity across the corpus. Runs in ~10ms. Catches what vector search misses when vocabulary differs.

```python
def _bm25_ranking(query, results):
    corpus = [tokenize(r.get("text", "")) for r in results]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(tokenize(query))
    return sorted(range(len(results)), key=lambda i: scores[i], reverse=True)
```

#### Stage 2 — Reciprocal Rank Fusion (RRF)

Merges the BM25 ranking with the original Qdrant vector ranking. RRF uses only rank positions, not raw scores — this avoids the problem of incompatible score distributions between cosine similarity and BM25.

Formula: `score = 1 / (60 + rank)` per method, summed across methods.

```python
def _rrf_fuse(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            scores[idx] = scores.get(idx, 0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)
```

The top-10 from RRF go to the cross-encoder.

#### Stage 3 — Cross-Encoder Reranking

A `MiniLM-L-2` cross-encoder reads the query and each chunk **together** as a single input and outputs a relevance score. Unlike bi-encoders (which embed query and document separately), the cross-encoder can perform joint reasoning — catching cases like "right words, wrong answer."

Model: `cross-encoder/ms-marco-MiniLM-L-2-v2` (~11M parameters, ~300ms for 10 pairs on CPU).

```python
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-2-v2", max_length=512)
scores = cross_encoder.predict([(query, chunk) for chunk in candidates])
```

**Total added latency on CPU: ~400ms** for the full 30 → 10 → 5 funnel.

> The cross-encoder is loaded once at module level at startup. Never load it inside the request handler — it takes 3–5 seconds to initialise.

#### Why FastEmbed for embeddings but sentence-transformers for reranking?

- **FastEmbed** uses ONNX Runtime — ~3× faster than PyTorch on CPU for inference. Used for query embedding, which is on the hot path of every request.
- **sentence-transformers** is used for the cross-encoder because FastEmbed is a bi-encoder-only library and does not support cross-encoder inference. The `CrossEncoder` class in sentence-transformers is the only production-ready API for this.

---

### Query Pipeline

```
POST /ask
  │
  ├── (if needs_context) rewrite query + history into a standalone question via small LLM
  ├── embed query (FastEmbed, ONNX)
  ├── Qdrant vector search → 30 candidates (filtered by user_id)
  ├── BM25 rank 30 candidates
  ├── RRF fuse vector + BM25 rankings → top-10
  ├── Cross-encoder score top-10 → top-5
  ├── Build context string with source metadata
  ├── LLM streaming call (original query + retrieved chunks)
  └── StreamingResponse → client
```

---

### LLM Prompting

The system prompt and user prompt are separated by responsibility:

**System prompt** owns all rules: grounding, citation format, response style, SOURCES block structure. It includes a concrete filled example of the SOURCES JSON so the model has a template to follow.

**User prompt** is minimal — it only slots in the context and question. Keeping it short reduces the chance the model loses the context between instructions and the actual question.

Citation format is inline per sentence:

```
Attention mechanisms allow models to focus on relevant parts of the input. [Source 1]
This was first introduced in the transformer architecture. [Source 1, Source 3]
```

Every response ends with a structured SOURCES block:

```
<SOURCES>
[
  {
    "source_number": 1,
    "page_number": 4,
    "file_name": "attention_is_all_you_need.pdf",
    "access_url": "https://example.com/document/view/attention.pdf"
  }
]
</SOURCES>
```

---

## API Reference

### `POST /ask`

Query your uploaded research papers.

**Auth:** Bearer token required

**Request:**
```json
{
  "query": "What are the limitations of attention mechanisms for long sequences?"
}
```

**Response:** `text/plain` streaming

Each streamed chunk is a fragment of the LLM's answer. The final content includes inline citations and a SOURCES block.

---

### `POST /document/upload`

Upload a PDF for ingestion.

**Auth:** Bearer token required

**Request:** `multipart/form-data` with `file` field

**Behaviour:**
- If the PDF hash already exists in the DB → skips ingestion, grants access only
- If new → ingests, embeds, stores in Qdrant, sets status to `embedded`

---

## Key Design Decisions

**Why retrieve 30 but pass only 5 to the LLM?**
Retrieval recall and LLM context precision are different problems. A wide retrieval net (30) ensures relevant chunks aren't missed by the embedding model. A tight context (5) keeps the LLM focused and avoids the "lost in the middle" problem where models ignore content far from the start and end of a long context.

**Why RRF over score normalisation?**
Cosine similarity scores cluster between 0.7–0.95 for typical results. BM25 scores range from 0 to 40+. Normalising both to [0,1] distorts the distributions. RRF uses only rank order, which is directly comparable across any scoring method.

**Why not pre-index BM25?**
BM25 is built per-request over 30 retrieved chunks. At that scale it takes microseconds. Pre-indexing the full corpus would be worth the complexity only if the BM25 candidate set were in the thousands. The current design avoids the sync complexity of keeping a BM25 index consistent with Qdrant inserts.

**Why `document_hash_id` instead of chunk-level hashing?**
If the document hash matches, every chunk inside it is identical — there is no need to hash individual chunks. Using the document-level hash simplifies the deduplication logic to a single scroll filter and makes the access grant/revoke logic straightforward.

**Why is deletion an access revocation, not a hard delete?**
Vectors are owned by the document's content, not by any individual user. Hard-deleting on every user's "delete" action would break retrieval for any other user who shares that document. Tracking ownership via `user_ids` and only physically deleting a point once that list is empty keeps shared documents intact while still fully removing data for users who no longer have access to it.

**Why rewrite queries with a small LLM before retrieval instead of embedding the raw follow-up?**
Follow-up questions frequently contain little to no semantic content on their own ("why is it useful?"). Embedding them directly produces a near-meaningless vector. A cheap rewriting pass resolves references against prior turns into a standalone question, which is what actually gets embedded and searched — while the original question (not the rewrite) is still what's passed to the main LLM for answering, so user intent and phrasing aren't lost in translation.

---

## Race Condition Handling

When two users upload the same PDF simultaneously, a naive implementation causes both workers to see "not yet ingested" and both embed the full document — creating duplicate vectors and potentially overwriting each other's `user_ids`.

This is solved by using the database as a distributed lock via a conditional update:

```python
rows_updated = db.query(DocumentHash).filter(
    DocumentHash.id == document_hash_id,
    DocumentHash.status == "pending"       # atomic condition
).update({"status": "processing"})
db.commit()
```

Only one worker can update a row from `"pending"` to `"processing"` — the database guarantees this atomically. The worker that gets `rows_updated = 1` owns the ingestion. All others poll until status becomes `"embedded"`, then grant access.

```
Worker A (wins lock)             Worker B (loses lock)
────────────────────────────────────────────────────────
status: pending → processing
                                 rows_updated = 0
                                 polls every 3s...
embed + upsert
user_ids: ["user_a"]
status: processing → embedded
                                 sees status == "embedded"
                                 appends user_b to user_ids ✓
```

If the primary worker fails, status rolls back to `"pending"` so another worker can retry.