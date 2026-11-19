from __future__ import annotations

import argparse
import math
import re
from collections import Counter
from pathlib import Path
from typing import NamedTuple


TOKEN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{1,}")
STOP_WORDS = {"the", "and", "for", "with", "from", "that", "this", "when", "then", "your", "into"}


class Passage(NamedTuple):
    source: str
    first_line: int
    last_line: int
    text: str


def tokens(text: str) -> list[str]:
    return [token.casefold() for token in TOKEN.findall(text) if token.casefold() not in STOP_WORDS]


def read_passages(root: Path) -> list[Passage]:
    passages: list[Passage] = []
    for path in sorted([*root.rglob("*.md"), *root.rglob("*.txt")]):
        lines = path.read_text(encoding="utf-8").splitlines()
        start = 1
        buffer: list[str] = []
        for line_number, line in enumerate([*lines, ""], start=1):
            if line.strip():
                buffer.append(line.strip())
            elif buffer:
                text = " ".join(buffer)
                passages.append(Passage(str(path), start, line_number - 1, text))
                buffer = []
                start = line_number + 1
    return passages


def rank(query: str, passages: list[Passage], top_k: int) -> list[tuple[float, Passage]]:
    query_terms = set(tokens(query))
    if not query_terms:
        return []
    documents = [Counter(tokens(passage.text)) for passage in passages]
    document_frequency = {
        term: sum(term in document for document in documents) for term in query_terms
    }
    scored: list[tuple[float, Passage]] = []
    for passage, document in zip(passages, documents):
        length = sum(document.values()) or 1
        score = 0.0
        for term in query_terms:
            frequency = document[term]
            if frequency:
                inverse_frequency = math.log(1 + (len(passages) - document_frequency[term] + 0.5)
                                             / (document_frequency[term] + 0.5))
                score += inverse_frequency * (frequency * 2.2) / (
                    frequency + 1.2 * (0.25 + 0.75 * length / 120)
                )
        if score > 0:
            scored.append((score, passage))
    return sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]


def main() -> int:
    parser = argparse.ArgumentParser(description="Busca procedimientos con citas verificables.")
    parser.add_argument("--docs", type=Path, required=True, help="Directorio de políticas .md/.txt")
    parser.add_argument("--query", required=True, help="Pregunta o términos de búsqueda")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    if not args.docs.is_dir():
        parser.error(f"document directory does not exist: {args.docs}")
    if not 1 <= args.top_k <= 20:
        parser.error("--top-k must be between 1 and 20")

    results = rank(args.query, read_passages(args.docs), args.top_k)
    if not results:
        print("No matching policy passages found.")
        return 1

    for position, (score, passage) in enumerate(results, start=1):
        print(f"{position}. {passage.source}:{passage.first_line}-{passage.last_line}  score={score:.3f}")
        print(f"   {passage.text}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
