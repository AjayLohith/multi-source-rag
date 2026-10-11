RAG_SYSTEM_INSTRUCTION = (
    "You are a helpful, precise technical assistant specializing in multi-source intelligence.\n"
    "Answer the user's question strictly and exclusively using the provided context blocks.\n"
    "Rules:\n"
    "1. If the provided context does not contain enough information to answer, state clearly: "
    "'The provided sources do not contain sufficient information to answer this question.'\n"
    "2. Do not fabricate, extrapolate, or use outside unverified facts.\n"
    "3. Where applicable, cite the sources by their header tags (e.g., [Source 1], [Source 2]).\n"
)


def build_rag_prompt(query: str, context: str) -> str:
    """Builds the full grounded RAG prompt."""
    if not context.strip():
        context = "(No source context retrieved)"

    return (
        f"{RAG_SYSTEM_INSTRUCTION}\n"
        f"--- CONTEXT ---\n"
        f"{context}\n"
        f"--- END CONTEXT ---\n\n"
        f"Question: {query}\n"
        f"Answer:"
    )
