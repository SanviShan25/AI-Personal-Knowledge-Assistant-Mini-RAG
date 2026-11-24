"""Retrieval benchmark: how often does the right passage come back for a question?

Runs fully in memory (no database or server) with the real embedding model.

    cd backend
    python -m scripts.eval_retrieval                         # built-in OS-notes benchmark
    python -m scripts.eval_retrieval --configs 800:150,500:100,120:0   # compare chunking settings
    python -m scripts.eval_retrieval --check                 # fail if below eval/thresholds.json (used in CI)
    python -m scripts.eval_retrieval --pdf notes.pdf --questions my.jsonl -v   # your own documents

questions.jsonl: one JSON object per line
    {"question": "...", "pages": [3], "evidence": "a short exact phrase from the answer"}

A retrieved chunk counts as correct if it is on one of the expected pages and contains
most of the evidence phrase (>= 60% of its words, so smaller chunk sizes are judged fairly).
Without "evidence", any chunk from an expected page counts.

Metrics: hit@k = share of questions with a correct chunk in the top k;
MRR = mean of 1/rank of the first correct chunk (0 if none in the top 10).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np

from app.config import settings
from app.services import embeddings
from app.services.chunking import Chunk, chunk_pages
from app.services.pdf import extract_pages

EVAL_DIR = Path(__file__).resolve().parent.parent / "eval"
DEFAULT_PDF = EVAL_DIR / "os-notes.pdf"
DEFAULT_QUESTIONS = EVAL_DIR / "questions.jsonl"
THRESHOLDS = EVAL_DIR / "thresholds.json"
KS = (1, 3, 5)
MRR_DEPTH = 10

_words = lambda text: set(re.findall(r"[a-z0-9]+", text.lower()))  # noqa: E731


def is_relevant(chunk: Chunk, item: dict) -> bool:
    if chunk.page not in item["pages"]:
        return False
    evidence = item.get("evidence")
    if not evidence:
        return True
    wanted = _words(evidence)
    return len(wanted & _words(chunk.text)) / max(len(wanted), 1) >= 0.6


def evaluate(
    pages: list[str],
    items: list[dict],
    chunk_size: int,
    overlap: int,
    embed_documents: Callable[[list[str]], np.ndarray],
    query_vectors: np.ndarray,
) -> dict:
    chunks = chunk_pages(pages, chunk_size, overlap)
    matrix = embed_documents([c.text for c in chunks])
    ranks: list[int | None] = []
    details = []
    for item, qv in zip(items, query_vectors):
        order = np.argsort(-(matrix @ qv))[:MRR_DEPTH]
        rank = next((i + 1 for i, idx in enumerate(order) if is_relevant(chunks[idx], item)), None)
        ranks.append(rank)
        details.append({"question": item["question"], "rank": rank, "top_pages": [chunks[i].page for i in order[:5]]})

    n = len(items)
    metrics = {f"hit@{k}": sum(1 for r in ranks if r and r <= k) / n for k in KS}
    metrics["mrr"] = sum(1 / r for r in ranks if r) / n
    return {"chunk_size": chunk_size, "overlap": overlap, "chunks": len(chunks), "metrics": metrics, "details": details}


def markdown_table(results: list[dict], model: str, n_questions: int) -> str:
    lines = [
        f"### Retrieval benchmark ({n_questions} questions, `{model}`)",
        "",
        "| chunk size / overlap | chunks | hit@1 | hit@3 | hit@5 | MRR |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        m = r["metrics"]
        lines.append(
            f"| {r['chunk_size']} / {r['overlap']} | {r['chunks']} | {m['hit@1']:.1%} | {m['hit@3']:.1%} "
            f"| {m['hit@5']:.1%} | {m['mrr']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def check(result: dict, thresholds: dict) -> list[str]:
    """Return a list of failures (empty if every metric meets its minimum)."""
    return [
        f"{name} {result['metrics'][name]:.3f} is below the minimum {minimum:.3f}"
        for name, minimum in thresholds["min"].items()
        if result["metrics"][name] < minimum
    ]


def parse_configs(text: str) -> list[tuple[int, int]]:
    configs = []
    for part in text.split(","):
        size, _, overlap = part.strip().partition(":")
        configs.append((int(size), int(overlap or 0)))
    return configs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument(
        "--configs",
        default=f"{settings.CHUNK_SIZE}:{settings.CHUNK_OVERLAP}",
        help="comma-separated chunk_size:overlap pairs; the first one is checked against thresholds",
    )
    parser.add_argument("--check", action="store_true", help=f"exit 1 if the first config is below {THRESHOLDS.name}")
    parser.add_argument("--json", type=Path, help="write the full report as JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="show every question and its rank")
    args = parser.parse_args()

    pages = extract_pages(args.pdf.read_bytes())
    items = [json.loads(line) for line in args.questions.read_text().splitlines() if line.strip()]

    started = time.perf_counter()
    query_vectors = np.stack([embeddings.embed_query(i["question"]) for i in items])
    results = [
        evaluate(pages, items, size, overlap, embeddings.embed_documents, query_vectors)
        for size, overlap in parse_configs(args.configs)
    ]
    elapsed = time.perf_counter() - started

    table = markdown_table(results, settings.EMBEDDING_MODEL, len(items))
    print(table)
    if args.verbose:
        for d in results[0]["details"]:
            mark = f"#{d['rank']}" if d["rank"] else "MISS"
            print(f"[{mark:>4}] {d['question']}  (top pages {d['top_pages']})")
    print(f"{len(items)} questions, {len(pages)} pages, {elapsed:.1f}s")

    if summary := os.getenv("GITHUB_STEP_SUMMARY"):  # shows the table on the GitHub Actions run page
        with open(summary, "a") as f:
            f.write(table)
    if args.json:
        args.json.write_text(json.dumps({"model": settings.EMBEDDING_MODEL, "results": results}, indent=2))

    if args.check:
        failures = check(results[0], json.loads(THRESHOLDS.read_text()))
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        if failures:
            return 1
        print("All retrieval metrics meet the thresholds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
