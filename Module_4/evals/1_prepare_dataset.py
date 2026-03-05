"""
RAGBench (HotpotQA) Dataset Loader for RAG Evaluation
-----------------------------------------------------
Produces two files:
  1. golden_hotpotqa_30.jsonl   — 30 examples for evaluation (questions + gold answers + contexts)
  2. rag_corpus_hotpotqa_500.jsonl — 500 document chunks to populate Pinecone

Run:
  pip install datasets
  python 1_prepare_dataset.py
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

# pip install datasets
from datasets import load_dataset

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("ragbench_loader")

# ── Config ───────────────────────────────────────────────────────────────────
DS_NAME    = "rungalileo/ragbench"
CONFIG     = "hotpotqa"
SPLIT      = "train"
GOLDEN_N   = 30
CORPUS_N   = 500
MAX_CHARS  = 8_000

OUT_DIR    = Path("ragbench_hotpotqa_exports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

GOLDEN_PATH = OUT_DIR / "golden_hotpotqa_30.jsonl"
CORPUS_PATH = OUT_DIR / "rag_corpus_hotpotqa_500.jsonl"

# ── Helpers ───────────────────────────────────────────────────────────────────

def as_text_list(documents: Optional[List], documents_sentences: Optional[List] = None) -> List[str]:
    """
    Normalise the 'documents' field into a plain list[str].

    RAGBench shapes we handle:
      • list[str]           — already plain text
      • list[dict]          — dicts with 'text'/'content'/… keys or a 'sentences' list
      • list[list[str]]     — sentences grouped by document (FIX: was silently dropped before)
      • fallback to documents_sentences if nothing else works
    """
    if not documents:                           # None or empty list → skip
        return []

    first = documents[0]

    # Case A: already plain strings
    if isinstance(first, str):
        return [d for d in documents if isinstance(d, str) and d.strip()]

    # Case B: list of lists of strings (e.g. sentences per doc)  ← BUG FIX
    if isinstance(first, list):
        return [
            " ".join(s for s in doc if isinstance(s, str) and s.strip())
            for doc in documents
            if isinstance(doc, list)
        ]

    # Case C: list of dicts
    if isinstance(first, dict):
        candidate_keys = ("text", "content", "page_content", "body")
        out = []
        for d in documents:
            if not isinstance(d, dict):
                continue
            # Try well-known text keys first
            txt = next((d[k].strip() for k in candidate_keys if k in d and isinstance(d[k], str) and d[k].strip()), None)
            # Fallback: 'sentences' list inside the dict
            if txt is None and isinstance(d.get("sentences"), list):
                txt = " ".join(s for s in d["sentences"] if isinstance(s, str) and s.strip())
            if txt:
                out.append(txt)
        if out:
            return out

    # Case D: documents_sentences as last resort
    if documents_sentences and isinstance(documents_sentences, list):
        return [
            " ".join(s for s in sents if isinstance(s, str) and s.strip())
            for sents in documents_sentences
            if isinstance(sents, list)
        ]

    return []


def trunc(s: str, max_chars: int = MAX_CHARS) -> str:
    return s[:max_chars] if len(s) > max_chars else s


def make_id(row: dict, idx: int) -> str:
    """Return a stable string ID — fallback to row index if the field is missing."""
    raw = row.get("id")
    if raw is not None:
        return str(raw)
    # FIX: original code silently stored None when 'id' was absent
    return f"row_{idx}"


# ── Load dataset ──────────────────────────────────────────────────────────────
log.info(f"Loading '{DS_NAME}' config='{CONFIG}' split='{SPLIT}' ...")
ds = load_dataset(DS_NAME, CONFIG, split=SPLIT)
log.info(f"Loaded {len(ds)} rows | fields: {list(ds.features.keys())}")

# ── Step 1 : Golden dataset (first 30 rows) ───────────────────────────────────
golden_n = min(GOLDEN_N, len(ds))
log.info(f"Writing golden dataset ({golden_n} examples) → {GOLDEN_PATH}")

with GOLDEN_PATH.open("w", encoding="utf-8") as f:
    for i, row in enumerate(ds.select(range(golden_n))):
        item = {
            "id":           make_id(row, i),
            "input":        row.get("question", ""),
            "reference":    row.get("response", ""),
            "contexts":     as_text_list(row.get("documents"), row.get("documents_sentences")),
            "dataset_name": row.get("dataset_name", CONFIG),
            "source":       f"{DS_NAME}/{CONFIG}",
        }
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

log.info(f"Golden dataset written → {GOLDEN_PATH.resolve()}")

# ── Step 2 : Corpus dataset (first 500 rows, flat per-doc records) ─────────────
corpus_n = min(CORPUS_N, len(ds))
log.info(f"Writing corpus dataset ({corpus_n} source rows) → {CORPUS_PATH}")

gold_ids = {make_id(row, i) for i, row in enumerate(ds.select(range(golden_n)))}

with CORPUS_PATH.open("w", encoding="utf-8") as f:
    for i, row in enumerate(ds.select(range(corpus_n))):
        ex_id = make_id(row, i)
        docs  = as_text_list(row.get("documents"), row.get("documents_sentences"))

        if not docs:                            # FIX: skip rows with no usable text
            log.warning(f"Row {i} (id={ex_id}) produced no document text — skipping")
            continue

        for k, doc_text in enumerate(docs):
            rec = {
                "id":   f"{ex_id}_d{k}",
                "text": trunc(doc_text),
                "metadata": {
                    "example_id":       ex_id,
                    "question":         trunc(row.get("question", ""), 2_000),
                    "reference_answer": trunc(row.get("response",  ""), 2_000),
                    "dataset":          CONFIG,
                    "source":           f"{DS_NAME}/{CONFIG}",
                    "doc_index":        k,
                    "in_golden":        ex_id in gold_ids,
                },
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

log.info(f"Corpus dataset written → {CORPUS_PATH.resolve()}")
log.info("Done.")
log.info("  Golden  → evaluation set  (LangSmith / MLflow / RAGAS)")
log.info("  Corpus  → Pinecone vector store")
