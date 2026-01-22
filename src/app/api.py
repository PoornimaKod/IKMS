from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .models import QuestionRequest, QAResponse
from .services.qa_service import answer_question
from .services.indexing_service import index_pdf_file


app = FastAPI(
    title="Class 12 Multi-Agent RAG Demo",
    description=(
        "Demo API for asking questions about a vector databases paper. "
        "The `/qa` endpoint currently returns placeholder responses and "
        "will be wired to a multi-agent RAG pipeline in later user stories."
    ),
    version="0.1.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/app/static"), name="static")


@app.get("/")
async def root():
    return JSONResponse(content={"message": "Visit /static/index.html for the UI"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:  # pragma: no cover - simple demo handler
    """Catch-all handler for unexpected errors.

    FastAPI will still handle `HTTPException` instances and validation errors
    separately; this is only for truly unexpected failures so API consumers
    get a consistent 500 response body.
    """

    if isinstance(exc, HTTPException):
        # Let FastAPI handle HTTPException as usual.
        raise exc

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# In-memory session store (for demo purposes)
sessions = {}

@app.post("/qa", response_model=QAResponse, status_code=status.HTTP_200_OK)
async def qa_endpoint(payload: QuestionRequest, session_id: str = None) -> QAResponse:
    """Submit a question about the vector databases paper.
    
    Supports optional `session_id` query param for conversational memory.
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`question` must be a non-empty string.",
        )
    
    # Session Management
    history = []
    if session_id:
        if session_id not in sessions:
             sessions[session_id] = []
        history = sessions[session_id]
        
    # Delegate to service layer (assuming updated signature or wrapper)
    # We need to update `answer_question` in `qa_service` or call graph directly.
    # For now, let's update `answer_question` call to accept history if supported, 
    # OR we need to refactor `qa_service.py` (which I haven't edited yet but should exists).
    
    # Actually, `qa_service.py` likely calls `run_qa_flow`. 
    # I should update `qa_service.py` first or patch it here.
    # Let's inspect `qa_service.py` before finalizing this edit.
    
    # ... Wait, I can't inspect in the middle of a replace. 
    # I'll optimistically assume I can pass `history` to `answer_question` 
    # and will update `qa_service.py` next.
    
    result = answer_question(question, history) 

    # Update History
    new_turn = {
        "question": question,
        "answer": result.get("answer", ""),
        "timestamp": "now" # simplified
    }
    
    if session_id:
        sessions[session_id].append(new_turn)

    return QAResponse(
        answer=result.get("answer", ""),
        draft_answer=result.get("draft_answer", ""),
        context=result.get("context", ""),
        plan=result.get("plan", ""),
        sub_questions=result.get("sub_questions", []),
        retrieval_traces=result.get("retrieval_traces", []),
        citations=result.get("citations", {}),
        context_rationale=result.get("context_rationale", "")
    )


@app.post("/index-pdf", status_code=status.HTTP_200_OK)
async def index_pdf(file: UploadFile = File(...)) -> dict:
    """Upload a PDF and index it into the vector database.

    This endpoint:
    - Accepts a PDF file upload
    - Saves it to the local `data/uploads/` directory
    - Uses PyPDFLoader to load the document into LangChain `Document` objects
    - Indexes those documents into the configured Pinecone vector store
    """

    if file.content_type not in ("application/pdf",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    contents = await file.read()
    file_path.write_bytes(contents)

    # Index the saved PDF
    chunks_indexed = index_pdf_file(file_path)

    return {
        "filename": file.filename,
        "chunks_indexed": chunks_indexed,
        "message": "PDF indexed successfully.",
    }