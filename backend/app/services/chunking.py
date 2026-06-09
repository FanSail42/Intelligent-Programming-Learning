from app.services.document_parser import ParsedBlock


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chunk_blocks(
    blocks: list[ParsedBlock],
    chunk_size: int = 512,
    overlap: int = 50,
) -> list[tuple[str, int | None, int]]:
    """Return list of (text, source_page, token_count)."""
    char_size = chunk_size * 4
    char_overlap = overlap * 4
    results: list[tuple[str, int | None, int]] = []

    for block in blocks:
        text = block.text
        page = block.page
        start = 0
        while start < len(text):
            end = start + char_size
            piece = text[start:end].strip()
            if piece:
                results.append((piece, page, estimate_tokens(piece)))
            if end >= len(text):
                break
            start = max(end - char_overlap, start + 1)

    return results
