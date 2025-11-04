from collections.abc import Sequence


def build_system_prompt(workspace_knowledge_base_text: str) -> str:
    guidance = (
        "You are a helpful assistant for this workspace. Use the knowledge base when it helps, "
        "but do not invent facts. If unsure, ask clarifying questions."
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
