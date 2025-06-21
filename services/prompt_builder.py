def build_prompt_with_context(user_prompt: str, context_snippets: list) -> str:
    context_block = "\n\n".join(context_snippets)
    return f"You are an intelligent coding assistant. Use the following code context to help answer the user's request.\n\nContext:\n{context_block}\n\nUser Query:\n{user_prompt}"
