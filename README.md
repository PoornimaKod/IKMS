# IKMS — Conversational Multi-Agent RAG

> **Feature 5: Conversational Multi-Turn QA with Memory**  
> Built on LangGraph + Pinecone + FastAPI with a React/Vite frontend.

## Features

- **Multi-turn conversations** — follow-up questions using "it", "that", "the method" are resolved automatically
-  **Memory summarization** — conversations > 5 turns are auto-compressed to stay within token limits
-  **History-aware retrieval** — the retrieval agent searches for complementary context, not duplicate info
-  **PDF upload** — index new documents into Pinecone at runtime
-  **Vercel-compatible** — stateless API, history stored client-side (localStorage)

## Architecture

```
Frontend (React/Vite)
  └─ sends: { question, history, conversation_summary, session_id }
  └─ receives: { answer, context, updated_history, conversation_summary }
  └─ persists session to localStorage

Backend (FastAPI + LangGraph)
  └─ retrieval_node     → history-aware vector search
  └─ summarization_node → builds on prior answers
  └─ verification_node  → checks consistency with history
  └─ memory_summarizer  → compresses history > 5 turns
```

## Environment Variables

Create a `.env` file in the project root (or set in Vercel dashboard):

```
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=your-index-name
```

## Local Development

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Start FastAPI dev server (port 8000)
uvicorn src.app.api:app --reload
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server (port 5173, proxies API to :8000)
npm run dev
```

Open `http://localhost:5173`

## Deployment on Vercel

### Step 1 — Deploy Backend

1. Push the root of this repo to GitHub
2. Go to [vercel.com](https://vercel.com) → **New Project** → import your repo
3. Set **Root Directory** to `.` (repo root)
4. Add **Environment Variables**:
   - `OPENAI_API_KEY` → your OpenAI key
   - `PINECONE_API_KEY` → your Pinecone key
   - `PINECONE_INDEX_NAME` → your index name
5. Deploy → note the URL (e.g. `https://ikms-backend.vercel.app`)

### Step 2 — Deploy Frontend

1. Go to Vercel → **New Project** → import the **same repo**
2. Set **Root Directory** to `frontend`
3. Add **Environment Variable**:
   - `VITE_API_URL` → your backend URL from Step 1 (e.g. `https://ikms-backend.vercel.app`)
4. Deploy → your frontend URL is live!

### Alternative Backend: Railway or Render

```bash
# Railway
railway up

# Render — use Procfile:
# web: uvicorn src.app.api:app --host 0.0.0.0 --port $PORT
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/qa/conversation` | Conversational QA (send history in body) |
| `POST` | `/index-pdf` | Upload + index a PDF |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

### Example Request

```json
POST /qa/conversation
{
  "question": "What are its main advantages?",
  "session_id": "sess_abc123",
  "history": [
    {
      "turn": 1,
      "question": "What is HNSW indexing?",
      "answer": "HNSW is...",
      "timestamp": "2026-02-24T00:00:00Z"
    }
  ],
  "conversation_summary": null
}
```

### Example Response

```json
{
  "answer": "Compared to other methods, HNSW offers...",
  "context": "Chunk 1 (page=5): ...",
  "session_id": "sess_abc123",
  "turn_number": 2,
  "used_history": true,
  "updated_history": [...],
  "conversation_summary": null
}
```
