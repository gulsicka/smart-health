def build_context(chunks: list) -> str:
    return "\n\n".join(f"[{r.source}] {r.content}" for r in chunks)