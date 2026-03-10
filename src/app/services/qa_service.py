"""Service layer for wrapping the conversational QA graph.

Feature 5: history and conversation_summary are threaded through.
"""

from typing import Any, Dict, List, Optional

from ..core.agents.graph import run_qa_flow


def answer_question(
    question: str,
    history: Optional[List[dict]] = None,
    conversation_summary: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the conversational multi-agent QA flow.

    Args:
        question: The user's current question.
        history: Previous conversation turns for this session.
        conversation_summary: Compressed summary for long histories.
        session_id: Optional session identifier.

    Returns:
        Final state dict containing answer, context, and updated history fields.
    """
    return run_qa_flow(
        question=question,
        history=history,
        conversation_summary=conversation_summary,
        session_id=session_id,
    )