"""Agent implementations for Feature 5: Conversational Multi-Turn QA with Memory.

Defines LangChain agents and LangGraph node functions for:
- Retrieval Agent (history-aware)
- Summarization Agent (history-aware, builds on previous answers)
- Verification Agent (checks consistency with history)
- Memory Summarizer (compresses history > 5 turns)
"""

import logging
from datetime import datetime, timezone
from typing import List

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.language_models import BaseChatModel

from ..llm.factory import create_chat_model
from .prompts import (
    RETRIEVAL_SYSTEM_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    MEMORY_SUMMARIZER_SYSTEM_PROMPT,
)
from .state import QAState
from .tools import retrieval_tool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_last_ai_content(messages: List[object]) -> str:
    """Extract the content of the last AIMessage in a messages list."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return str(msg.content)
    return ""


def _format_history(history: list[dict], max_turns: int = 5) -> str:
    """Format conversation history into a human-readable string for agent context."""
    if not history:
        return "No previous conversation."

    lines = []
    recent = history[-max_turns:]
    for turn in recent:
        turn_num = turn.get("turn", "?")
        q = turn.get("question", "")
        a = turn.get("answer", "")
        lines.append(f"[Turn {turn_num}]\nUser: {q}\nAssistant: {a}")
    return "\n\n".join(lines)


def _format_summary_plus_history(
    conversation_summary: str | None,
    history: list[dict],
    max_recent: int = 3,
) -> str:
    """Combine compressed summary (for old turns) + recent raw turns."""
    parts = []
    if conversation_summary:
        parts.append(f"=== Conversation Summary (Earlier Turns) ===\n{conversation_summary}")
    recent = history[-max_recent:] if len(history) > max_recent else history
    if recent:
        parts.append("=== Recent Turns ===\n" + _format_history(recent, max_turns=max_recent))
    return "\n\n".join(parts) if parts else "No previous conversation."


# ---------------------------------------------------------------------------
# Agents (module-level singletons)
# ---------------------------------------------------------------------------

retrieval_agent = create_agent(
    model=create_chat_model(),
    tools=[retrieval_tool],
    system_prompt=RETRIEVAL_SYSTEM_PROMPT,
)

summarization_agent = create_agent(
    model=create_chat_model(),
    tools=[],
    system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
)

verification_agent = create_agent(
    model=create_chat_model(),
    tools=[],
    system_prompt=VERIFICATION_SYSTEM_PROMPT,
)

# Plain LLM for memory summarization (no tools needed)
_llm: BaseChatModel = create_chat_model()


# ---------------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------------

def retrieval_node(state: QAState) -> dict:
    """Retrieval Agent node: gathers context from vector store.

    History-aware: analyzes conversation history to resolve references
    (e.g., 'it', 'that', 'the method mentioned earlier') before searching.
    """
    question = state["question"]
    history = state.get("history") or []
    conversation_summary = state.get("conversation_summary")

    history_context = _format_summary_plus_history(conversation_summary, history)

    user_message = (
        f"Current Question: {question}\n\n"
        f"Conversation History:\n{history_context}\n\n"
        "Please retrieve relevant context for the current question, taking the "
        "conversation history into account to resolve any references."
    )

    logger.info("[retrieval_node] Invoking retrieval agent for: %s", question)
    result = retrieval_agent.invoke({"messages": [HumanMessage(content=user_message)]})
    messages = result.get("messages", [])

    # Aggregate ALL ToolMessage contents (not just the last)
    context_parts = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            context_parts.append(str(msg.content))

    context = "\n\n".join(context_parts).strip()
    logger.info("[retrieval_node] Retrieved %d context block(s).", len(context_parts))

    return {"context": context}


def summarization_node(state: QAState) -> dict:
    """Summarization Agent node: generates draft answer using context + history.

    Builds on prior answers and resolves references using conversation history.
    """
    question = state["question"]
    context = state.get("context") or ""
    history = state.get("history") or []
    conversation_summary = state.get("conversation_summary")

    history_context = _format_summary_plus_history(conversation_summary, history)

    user_content = (
        f"Conversation History:\n{history_context}\n\n"
        f"Current Question: {question}\n\n"
        f"Retrieved Context:\n{context}\n\n"
        "Please answer the current question, building on the conversation history "
        "where appropriate and resolving any references (e.g., 'it', 'that')."
    )

    logger.info("[summarization_node] Generating draft answer.")
    result = summarization_agent.invoke({"messages": [HumanMessage(content=user_content)]})
    messages = result.get("messages", [])
    draft_answer = _extract_last_ai_content(messages)

    return {"draft_answer": draft_answer}


def verification_node(state: QAState) -> dict:
    """Verification Agent node: verifies draft answer against context and history."""
    question = state["question"]
    context = state.get("context") or ""
    draft_answer = state.get("draft_answer") or ""
    history = state.get("history") or []

    history_context = _format_history(history, max_turns=3)

    user_content = (
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        f"Conversation History:\n{history_context}\n\n"
        f"Draft Answer:\n{draft_answer}\n\n"
        "Please verify this answer for accuracy and consistency with prior turns. "
        "Remove unsupported claims. Return only the final corrected answer."
    )

    logger.info("[verification_node] Verifying draft answer.")
    result = verification_agent.invoke({"messages": [HumanMessage(content=user_content)]})
    messages = result.get("messages", [])
    answer = _extract_last_ai_content(messages)

    return {"answer": answer}


def memory_summarizer_node(state: QAState) -> dict:
    """Memory Summarizer node: compresses history when it grows beyond 5 turns.

    Older turns (beyond the last 3) are compressed into a summary to manage
    token limits while preserving important context for future questions.
    """
    history = state.get("history") or []
    current_summary = state.get("conversation_summary")

    # Only summarize if history is getting long (> 5 turns)
    if len(history) <= 5:
        logger.info("[memory_summarizer_node] History has %d turns — no summarization needed.", len(history))
        return {}

    logger.info("[memory_summarizer_node] Compressing %d turns into summary.", len(history))

    # Turns to compress = all except the last 3 (keep those raw for full context)
    turns_to_compress = history[:-3]
    recent_turns = history[-3:]

    history_text = _format_history(turns_to_compress, max_turns=len(turns_to_compress))
    if current_summary:
        history_text = f"Previous Summary:\n{current_summary}\n\nNew Turns to Add:\n{history_text}"

    messages = [
        SystemMessage(content=MEMORY_SUMMARIZER_SYSTEM_PROMPT),
        HumanMessage(content=f"Please summarize these conversation turns:\n\n{history_text}"),
    ]

    response = _llm.invoke(messages)
    new_summary = str(response.content)

    logger.info("[memory_summarizer_node] Summary generated. Trimming history to last 3 turns.")

    # Replace history with only recent turns; older turns live in the summary
    return {
        "conversation_summary": new_summary,
        "history": recent_turns,
    }