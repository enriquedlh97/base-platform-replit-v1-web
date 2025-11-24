from collections.abc import Sequence


def build_system_prompt(workspace_knowledge_base_text: str) -> str:
    guidance = (
        "You are a helpful assistant for this workspace. Use the knowledge base when it helps, "
        "but do not invent facts. If unsure, ask clarifying questions.\n\n"
        "IMPORTANT: Always acknowledge the user's request before taking action. For example, "
        "if a user asks you to schedule an appointment, first say something like 'Of course, let me schedule that for you' "
        "before using any tools. After completing an action (especially after a tool returns a result), "
        "you MUST provide a clear response to the user explaining what happened. Even if a tool fails, "
        "you must explain the failure to the user in a helpful and clear way.\n\n"
        "CRITICAL: Only use the scheduling tool when the user explicitly requests to schedule an appointment. "
        "Do NOT schedule appointments when the user is just acknowledging, thanking you, or having a general conversation. "
        "If an appointment was already successfully scheduled in this conversation, do NOT call the scheduling tool again "
        "unless the user explicitly requests a NEW appointment (e.g., 'schedule another one', 'book a different time', etc.). "
        "If the user says things like 'thanks', 'great', 'ok', 'perfect', etc. after a successful scheduling, "
        "just acknowledge their message - do NOT schedule again."
    )
    kb = workspace_knowledge_base_text.strip()
    if kb:
        return f"{guidance}\n\nKnowledge Base:\n{kb}"
    return guidance


def build_chat_messages(
    history: Sequence[dict[str, str]], system_prompt: str
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for item in history:
        role = item.get("role", "user")
        content = item.get("content", "")
        if not content:
            continue
        if role not in ("user", "assistant", "system"):
            role = "user"
        messages.append({"role": role, "content": content})
    return messages
