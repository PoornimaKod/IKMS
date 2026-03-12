"""FastAPI app — Feature 5: Conversational Multi-Turn QA with Memory.

Vercel-compatible: stateless. The frontend sends conversation history with
each request and receives the updated history to store client-side (localStorage).

Endpoints:
  POST /qa/conversation         — Stateful conversational QA (client sends history)
  POST /index-pdf               — Upload and index a PDF
  GET  /health                  — Health check
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .models import (
    ConversationalQARequest,
    ConversationalQAResponse,
    QuestionRequest,
    QAResponse,
)
from .services.qa_service import answer_question
from .services.indexing_service import index_pdf_file


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="IKMS — Conversational Multi-Agent RAG",
    description=(
        "Feature 5: Conversational Multi-Turn QA with Memory. "
        "All agents are history-aware. Long conversations are auto-summarized. "
        "Client-side history storage makes this compatible with serverless deployments."
    ),
    version="2.0.0",
)

# CORS — required for Vercel frontend ↔ Vercel backend cross-origin calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to your Vercel domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files (serve bundled React build when running as a single service)
# ---------------------------------------------------------------------------
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    # Mount the standard Vite /assets directory explicitly
    assets_dir = _static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    
    # Mount /static as a fallback
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    index = _static_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse(content={
        "message": "IKMS Conversational RAG API is running.",
        "docs": "/docs",
        "chat_endpoint": "POST /qa/conversation",
    })


@app.get("/health")
async def health():
    return {"status": "ok", "feature": "Feature 5 — Conversational Memory"}


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# ---------------------------------------------------------------------------
# Feature 5: Conversational QA — Stateless/Vercel-compatible
# ---------------------------------------------------------------------------

@app.post(
    "/qa/conversation",
    response_model=ConversationalQAResponse,
    status_code=status.HTTP_200_OK,
    summary="Conversational QA with memory",
    tags=["Feature 5 — Conversational Memory"],
)
async def conversational_qa(request: ConversationalQARequest) -> ConversationalQAResponse:
    """Submit a question in a conversation.

    Pass `history` (from previous responses) and `conversation_summary` back 
    with each request. The response returns `updated_history` to persist 
    client-side (localStorage) — no server session state required.

    This makes the endpoint fully compatible with Vercel serverless deployment.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`question` must be a non-empty string.",
        )

    # Client sends history; no server-side session store needed
    history = request.history or []
    conversation_summary = request.conversation_summary
    session_id = request.session_id or str(uuid.uuid4())
    turn_number = len(history) + 1
    used_history = len(history) > 0

    # Run the conversational QA graph
    result = answer_question(
        question=question,
        history=history,
        conversation_summary=conversation_summary,
        session_id=session_id,
    )

    answer = result.get("answer") or ""
    context = result.get("context") or ""

    # Build the new turn record
    new_turn = {
        "turn": turn_number,
        "question": question,
        "answer": answer,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # If memory_summarizer ran, it trimmed history — use its version
    updated_history_raw = result.get("history")
    updated_summary = result.get("conversation_summary")

    if updated_history_raw is not None:
        # memory_summarizer compressed old turns; append new turn to trimmed list
        updated_history = list(updated_history_raw) + [new_turn]
    else:
        updated_history = history + [new_turn]

    # Return updated state for frontend to persist
    return ConversationalQAResponse(
        answer=answer,
        context=context,
        session_id=session_id,
        turn_number=turn_number,
        used_history=used_history,
        updated_history=updated_history,
        conversation_summary=updated_summary or conversation_summary,
    )


# ---------------------------------------------------------------------------
# PDF Indexing
# ---------------------------------------------------------------------------

@app.post(
    "/index-pdf",
    status_code=status.HTTP_200_OK,
    summary="Upload and index a PDF",
    tags=["Knowledge Base"],
)
async def index_pdf(file: UploadFile = File(...)) -> dict:
    """Upload a PDF and index it into the Pinecone vector database."""
    if file.content_type not in ("application/pdf",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    # Use /tmp on serverless environments (like Vercel) to avoid read-only filesystem error
    upload_dir = Path("/tmp/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    contents = await file.read()
    file_path.write_bytes(contents)

    chunks_indexed = index_pdf_file(file_path)

    return {
        "filename": file.filename,
        "chunks_indexed": chunks_indexed,
        "message": "PDF indexed successfully.",
    }