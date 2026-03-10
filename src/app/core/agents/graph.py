"""LangGraph orchestration for Feature 5: Conversational Multi-Turn QA with Memory.

Graph flow:
  START → retrieval → summarization → verification → memory_summarizer → END
"""

import uuid
from typing import Any, Dict, List, Optional

from langgraph.constants import END, START
from langgraph.graph import StateGraph

from .agents import (
    retrieval_node,
    summarization_node,
    verification_node,
    memory_summarizer_node,
)
from .state import QAState


def create_qa_graph() -> Any:
    """Create and compile the conversational multi-agent QA graph.

    Flow:
        retrieval → summarization → verification → memory_summarizer

    The memory_summarizer compresses history when it exceeds 5 turns.
    """
    builder = StateGraph(QAState)

    builder.add_node("retrieval", retrieval_node)
    builder.add_node("summarization", summarization_node)
    builder.add_node("verification", verification_node)
    builder.add_node("memory_summarizer", memory_summarizer_node)

    builder.add_edge(START, "retrieval")
    builder.add_edge("retrieval", "summarization")
    builder.add_edge("summarization", "verification")
    builder.add_edge("verification", "memory_summarizer")
    builder.add_edge("memory_summarizer", END)

    return builder.compile()


def run_conversational_qa_flow(
    question: str,
    history: Optional[List[dict]] = None,
    conversation_summary: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the conversational QA graph for a single question turn.

    Args:
        question: The user's current question.
        history: All previous Q&A turns for this session.
        conversation_summary: Compressed summary if history was trimmed.
        session_id: Unique session identifier.

    Returns:
        Final state dict containing answer, context, updated history, etc.
    """
    graph = create_qa_graph()

    initial_state: QAState = {
        "question": question,
        "history": history or [],
        "conversation_summary": conversation_summary,
        "session_id": session_id or str(uuid.uuid4()),
        "context": None,
        "draft_answer": None,
        "answer": None,
    }

    final_state = graph.invoke(initial_state)
    return final_state


# ---------------------------------------------------------------------------
# Backwards-compatible wrapper (used by qa_service.py)
# ---------------------------------------------------------------------------
def run_qa_flow(
    question: str,
    history: Optional[List[dict]] = None,
    conversation_summary: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Alias for run_conversational_qa_flow — maintains backwards compatibility."""
    return run_conversational_qa_flow(
        question=question,
        history=history,
        conversation_summary=conversation_summary,
        session_id=session_id,
    )