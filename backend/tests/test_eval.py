"""Checks for the retrieval benchmark itself (offline, with the fake embedder)."""

import json
import re

import numpy as np
from conftest import FakeEmbedder

from app.services.chunking import Chunk
from app.services.pdf import extract_pages
from scripts.eval_retrieval import (
    DEFAULT_PDF,
    DEFAULT_QUESTIONS,
    THRESHOLDS,
    check,
    evaluate,
    is_relevant,
    parse_configs,
)


def load():
    pages = extract_pages(DEFAULT_PDF.read_bytes())
    items = [json.loads(line) for line in DEFAULT_QUESTIONS.read_text().splitlines() if line.strip()]
    return pages, items


def test_every_question_points_at_text_that_exists():
    pages, items = load()
    norm = lambda t: re.sub(r"\s+", " ", t).strip().lower()  # noqa: E731
    assert len(items) >= 40
    for item in items:
        assert item["question"].strip()
        for page in item["pages"]:
            assert 1 <= page <= len(pages)
        assert any(norm(item["evidence"]) in norm(pages[p - 1]) for p in item["pages"]), item


def test_relevance_needs_right_page_and_most_of_the_evidence():
    item = {"pages": [2], "evidence": "minimum average waiting time"}
    assert is_relevant(Chunk("SJF gives the minimum average waiting time.", 2, 0), item)
    assert not is_relevant(Chunk("SJF gives the minimum average waiting time.", 3, 0), item)
    assert not is_relevant(Chunk("Round robin uses a time quantum.", 2, 0), item)
    assert is_relevant(Chunk("anything", 2, 0), {"pages": [2]})


def test_evaluate_reports_sane_metrics():
    pages, items = load()
    fake = FakeEmbedder()
    queries = np.stack([fake.embed_query(i["question"]) for i in items])
    result = evaluate(pages, items, 800, 150, fake.embed_documents, queries)
    m = result["metrics"]
    assert result["chunks"] > len(pages)
    assert 0 <= m["hit@1"] <= m["hit@3"] <= m["hit@5"] <= 1
    assert 0 <= m["mrr"] <= 1
    # Even a bag-of-words embedder should find most passages; this guards against a broken pipeline.
    assert m["hit@5"] >= 0.5


def test_threshold_check_and_config_parsing():
    result = {"metrics": {"hit@1": 0.6, "hit@5": 0.9, "mrr": 0.7}}
    assert check(result, {"min": {"hit@1": 0.5, "hit@5": 0.9}}) == []
    assert len(check(result, {"min": {"hit@1": 0.7}})) == 1
    assert parse_configs("800:150, 120:0,500") == [(800, 150), (120, 0), (500, 0)]
    assert set(json.loads(THRESHOLDS.read_text())["min"]) <= {"hit@1", "hit@3", "hit@5", "mrr"}
