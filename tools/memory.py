from database.memory_repository import search_memory


def memory_search(query: str) -> str:
    results = search_memory(query)
    if not results:
        return f'No memories found for "{query}".'
    lines = []
    for memory in results:
        lines.append(
            f"[{memory['memory_type']}] "
            f"importance={memory['importance']} | "
            f"{memory['title']} | "
            f"{memory['context']} | "
            f"{memory['outcome']}"
        )
    return "\n".join(lines)
