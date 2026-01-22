"""LangGraph orchestration for the linear multi-agent QA flow."""

from functools import lru_cache
from typing import Any, Dict

from langgraph.constants import END, START
from langgraph.graph import StateGraph

from .agents import retrieval_node, summarization_node, verification_node
from .state import QAState


def create_qa_graph() -> Any:
    """Create and compile the linear multi-agent QA graph.

    The graph executes in order:
    1. Retrieval Agent: gathers context from vector store
    2. Summarization Agent: generates draft answer from context
    3. Verification Agent: verifies and corrects the answer

    Returns:
        Compiled graph ready for execution.
    """
    builder = StateGraph(QAState)

    # Add nodes for each agent
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("summarization", summarization_node)
    builder.add_node("verification", verification_node)

    # Define linear flow: START -> retrieval -> summarization -> verification -> END
    builder.add_edge(START, "retrieval")
    builder.add_edge("retrieval", "summarization")
    builder.add_edge("summarization", "verification")
    builder.add_edge("verification", END)

    return builder.compile()


@lru_cache(maxsize=1)
def get_qa_graph() -> Any:
    """Get the compiled QA graph instance (singleton via LRU cache)."""
    return create_qa_graph()


def run_qa_flow(question: str, history: list[dict] = None) -> Dict[str, Any]:
    """Run the QA graph for a single question.

    Args:
        question: The user's question string.
        history: Optional conversation history.

    Returns:
        The final state dict containing the answer and context.
    """
    app = create_qa_graph()
    
    initial_state: QAState = {
        "question": question,
        "history": history or [],
        "context": None,
        "conversation_summary": None,
        "session_id": None,
        "draft_answer": None,
        "answer": None,
    }

    # Run the graph
    final_state = app.invoke(initial_state)

    return final_state