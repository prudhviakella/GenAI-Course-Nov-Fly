"""
Ingest RAGBench HotpotQA corpus into Pinecone (pure OpenAI + Pinecone, no LangChain)
--------------------------------------------------------------------------------------
Reads:  ragbench_hotpotqa_exports/rag_corpus_hotpotqa_500.jsonl
Does:   chunk → embed (OpenAI) → upsert (Pinecone)

Env vars:
  export OPENAI_API_KEY="sk-..."
  export PINECONE_API_KEY="pcn-..."

Optional:
  PINECONE_INDEX   (default: hotpotqa-ragbench-mini)
  PINECONE_NS      (default: hotpotqa)
  EMBEDDING_MODEL  (default: text-embedding-3-large)
  CHUNK_SIZE       (default: 1000)
  CHUNK_OVERLAP    (default: 150)
  BATCH_SIZE       (default: 100)
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Iterable

import openai
from pinecone import Pinecone, ServerlessSpec

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("pinecone_ingest")

# ── Config ────────────────────────────────────────────────────────────────────
CORPUS_PATH     = Path("ragbench_hotpotqa_exports/rag_corpus_hotpotqa_500.jsonl")
INDEX_NAME      = os.getenv("PINECONE_INDEX", "hotpotqa-ragbench-mini")
NAMESPACE       = os.getenv("PINECONE_NS", "hotpotqa")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
CHUNK_SIZE      = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP   = int(os.getenv("CHUNK_OVERLAP", "0"))
BATCH_SIZE      = int(os.getenv("BATCH_SIZE", "100"))   # Pinecone upsert limit is 100 vectors

MODEL_DIMS = {"text-embedding-3-large": 3072, "text-embedding-3-small": 1536}
DIMENSION  = MODEL_DIMS.get(EMBEDDING_MODEL, 3072)

# ── Helpers ───────────────────────────────────────────────────────────────────

def ensure_env():
    missing = [k for k in ("OPENAI_API_KEY", "PINECONE_API_KEY") if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {missing}")


def load_jsonl(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Simple recursive character splitter — no external deps.

    Strategy:
      1. Try splitting on double-newline (paragraph boundary).
      2. Fall back to single-newline, then sentence end ('. '), then words.
      3. Hard-split if all else fails.

    This replicates the core behaviour of LangChain's RecursiveCharacterTextSplitter.
    """
    separators = ["\n\n", "\n", ". ", " ", ""]

    def _split(text: str, seps: List[str]) -> List[str]:
        if not seps or len(text) <= chunk_size:
            return [text]
        sep = seps[0]
        parts = text.split(sep) if sep else list(text)
        chunks, current = [], ""
        for part in parts:
            candidate = current + (sep if current else "") + part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # Part itself too long → recurse with next separator
                if len(part) > chunk_size:
                    chunks.extend(_split(part, seps[1:]))
                    current = ""
                else:
                    current = part
        if current:
            chunks.append(current)
        return chunks

    raw_chunks = _split(text, separators)

    # Apply overlap: each chunk starts with the tail of the previous one
    if overlap <= 0 or len(raw_chunks) <= 1:
        return raw_chunks

    result = [raw_chunks[0]]
    for chunk in raw_chunks[1:]:
        tail = result[-1][-overlap:]
        result.append(tail + chunk)
    return result


def chunk_records(records: List[Dict]) -> List[Dict]:
    """Split each record's text and return flat list of chunk dicts."""
    out = []
    for rec in records:
        text = rec.get("text", "") or ""
        if not text.strip():
            continue
        meta    = rec.get("metadata", {}) or {}
        base_id = rec["id"]
        parts   = split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)

        if len(parts) == 1:
            out.append({"id": base_id, "text": parts[0],
                        "metadata": {**meta, "chunk_index": 0, "chunk_count": 1}})
        else:
            for i, p in enumerate(parts):
                out.append({"id": f"{base_id}_c{i}", "text": p,
                            "metadata": {**meta, "chunk_index": i, "chunk_count": len(parts)}})
    return out


def embed_texts(texts: List[str], client: openai.OpenAI) -> List[List[float]]:
    """Call OpenAI Embeddings API for a batch of texts."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    # response.data is ordered the same as input
    return [item.embedding for item in response.data]


def batched(items: List, size: int) -> Iterable[List]:
    for i in range(0, len(items), size):
        yield items[i: i + size]


def ensure_index(pc: Pinecone):
    existing = {idx.name for idx in pc.list_indexes()}
    if INDEX_NAME in existing:
        log.info(f"Index '{INDEX_NAME}' already exists — skipping creation")
        return
    log.info(f"Creating index '{INDEX_NAME}' dim={DIMENSION} metric=cosine ...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    # Wait until ready
    for _ in range(20):
        status = pc.describe_index(INDEX_NAME).status
        if status.get("ready"):
            break
        log.info("Waiting for index to become ready ...")
        time.sleep(3)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ensure_env()

    if not CORPUS_PATH.exists():
        raise FileNotFoundError(f"Corpus not found: {CORPUS_PATH}. Run 1_prepare_dataset.py first.")

    # Clients
    oai = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pc  = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    ensure_index(pc)
    index = pc.Index(INDEX_NAME)

    # Load → chunk
    log.info(f"Loading corpus from {CORPUS_PATH} ...")
    records = load_jsonl(CORPUS_PATH)
    log.info(f"Loaded {len(records)} records")

    chunks = chunk_records(records)
    log.info(f"After chunking: {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    # Embed → upsert in batches
    total = 0
    for batch in batched(chunks, BATCH_SIZE):
        texts  = [c["text"] for c in batch]
        embeds = embed_texts(texts, oai)

        vectors = [
            {
                "id":     c["id"],
                "values": emb,
                # Pinecone stores metadata; also stash the text so we can retrieve it
                "metadata": {**c["metadata"], "text": c["text"]},
            }
            for c, emb in zip(batch, embeds)
        ]

        index.upsert(vectors=vectors, namespace=NAMESPACE)
        total += len(batch)
        log.info(f"Upserted {total}/{len(chunks)}")

    log.info("Ingestion complete!")
    log.info(f"Index: {INDEX_NAME} | Namespace: {NAMESPACE} | Vectors: {total}")


if __name__ == "__main__":
    main()
