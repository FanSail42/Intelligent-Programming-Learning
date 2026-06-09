from dataclasses import dataclass
from pathlib import Path

import pdfplumber

from app.models.material import MaterialType


@dataclass
class ParsedBlock:
    text: str
    page: int | None = None


def parse_document(file_path: str, material_type: MaterialType) -> list[ParsedBlock]:
    path = Path(file_path)
    if material_type == MaterialType.pdf:
        return _parse_pdf(path)
    if material_type in (MaterialType.txt, MaterialType.md):
        content = path.read_text(encoding="utf-8", errors="ignore")
        return [ParsedBlock(text=content, page=None)]
    raise ValueError(f"Unsupported material type: {material_type}")


def _parse_pdf(path: Path) -> list[ParsedBlock]:
    blocks: list[ParsedBlock] = []
    with pdfplumber.open(path) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                blocks.append(ParsedBlock(text=text, page=idx))
    return blocks
