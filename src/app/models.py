"""Pydantic models — Feature 5: Conversational Memory (Vercel-compatible).

For stateless serverless deployment (Vercel), the client sends
conversation history with each request instead of relying on server-side sessions.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class QuestionRequest(BaseModel):
    """Single-shot QA request (no memory)."""
    question: str


class ConversationalQARequest(BaseModel):
    """Request for conversational QA. 
    
    For Vercel (stateless deployment): the frontend sends `history` and
    `conversation_summary` directly so no server-side session store is needed.
    """
    question: str
    session_id: Optional[str] = None
    # Client sends history for stateless serverless deployments
    history: Optional[List[Dict[str, Any]]] = None
    conversation_summary: Optional[str] = None


class QAResponse(BaseModel):
    """Response for single-shot QA endpoint."""
    answer: str
    draft_answer: Optional[str] = None
    context: Optional[str] = None
    session_id: Optional[str] = None


class ConversationalQAResponse(BaseModel):
    """Full conversational response with updated session state to store client-side."""
    answer: str
    context: Optional[str] = None
    session_id: str
    turn_number: int
    used_history: bool
    # Updated history + summary to store client-side (localStorage)
    updated_history: List[Dict[str, Any]]
    conversation_summary: Optional[str] = None


class ConversationTurn(BaseModel):
    """A single Q&A turn."""
    turn: int
    question: str
    answer: str
    timestamp: str


class ConversationHistory(BaseModel):
    """Full history for a session."""
    session_id: str
    turns: List[ConversationTurn]
    conversation_summary: Optional[str] = None
    total_turns: int
