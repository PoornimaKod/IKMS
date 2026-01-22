"""Pydantic models for the API layer."""

from typing import List, Optional
from pydantic import BaseModel


class QuestionRequest(BaseModel):
    """Request schema for the QA endpoint."""
    question: str


class QAResponse(BaseModel):
    """Response schema for the QA endpoint."""
    answer: str
    draft_answer: Optional[str] = None
    context: Optional[str] = None
