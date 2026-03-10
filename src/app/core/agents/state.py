"""LangGraph state schema for the multi-agent QA flow.

Feature 5: Conversational Multi-Turn QA with Memory
"""

from typing import TypedDict, Optional, List, Dict


class QAState(TypedDict):
    """State schema for the conversational multi-agent QA flow.

    The state flows through these agents:
    1. Retrieval Agent: gathers context from vector store (history-aware)
    2. Summarization Agent: generates draft_answer using context + history
    3. Verification Agent: verifies and corrects the draft answer
    4. Memory Summarizer: compresses conversation history when > 5 turns

    Feature 5 fields:
    - history: list of previous Q&A turns
    - conversation_summary: compressed summary for long conversations
    - session_id: unique identifier for the conversation session
    """

    # Core QA fields
    question: str
    context: Optional[str]
    draft_answer: Optional[str]
    answer: Optional[str]

    # Feature 5: Conversational Memory
    history: Optional[List[dict]]         # [{turn, question, answer, timestamp}]
    conversation_summary: Optional[str]    # Compressed history summary (> 5 turns)
    session_id: Optional[str]             # Conversation session identifier