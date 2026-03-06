"""
╔══════════════════════════════════════════════════════════════════════════╗
║          RAG Evaluation Pipeline — MLflow 3 (GenAI + Model Training)    ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  DATASET  RAGBench HotpotQA (30 golden examples)                        ║
║    input       → question / query                                        ║
║    reference   → gold answer                                             ║
║    contexts    → list[str]  gold context chunks (4 per example)          ║
║    id          → record identifier                                       ║
║                                                                          ║
║  TWO EVALUATION MODES  (select via --mode flag)                          ║
║                                                                          ║
║  Part A  →  Model Training mode                                          ║
║             Hand-coded metrics computed in pure Python + LLM judges.    ║
║             Logged via mlflow.log_params() + mlflow.log_metrics().       ║
║             Visible in MLflow UI: Model Training tab                     ║
║                                                                          ║
║  Part B  →  GenAI mode                                                   ║
║             @mlflow.trace decorates the pipeline → every call creates   ║
║             a waterfall trace (CHAIN → RETRIEVER → LLM) in the UI.      ║
║             mlflow.genai.evaluate() runs 11 scorers over a DataFrame.   ║
║             Visible in MLflow UI: GenAI tab → Traces + Eval Results     ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  PREREQUISITES                                                           ║
║                                                                          ║
║  1. MLflow server running:                                               ║
║       mlflow server                                                      ║
║         --backend-store-uri postgresql://user:pass%40w@host:5432/db     ║
║         --default-artifact-root s3://your-bucket/mlflow-artifacts       ║
║         --host 0.0.0.0 --port 5001                                       ║
║                                                                          ║
║  2. Environment variables:                                               ║
║       export OPENAI_API_KEY="sk-..."                                     ║
║       export PINECONE_API_KEY="pcn-..."                                  ║
║                                                                          ║
║  3. golden_hotpotqa_30.jsonl  →  run 1_prepare_dataset.py first         ║
║  4. Pinecone index populated  →  run 2_ingest.py first                  ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  RUN COMMANDS                                                            ║
║    python 3_eval.py              # Part A only (default)                 ║
║    python 3_eval.py --mode a     # Part A explicitly                     ║
║    python 3_eval.py --mode b     # Part B (GenAI mode)                   ║
║    python 3_eval.py --mode both  # Part A then Part B sequentially       ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ── Standard library ──────────────────────────────────────────────────────
import argparse
import json
import logging
import math
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

# ── Third-party ───────────────────────────────────────────────────────────
import pandas as pd
from openai import OpenAI
from pinecone import Pinecone

# ── MLflow core ───────────────────────────────────────────────────────────
import mlflow
import mlflow.genai

# ── MLflow GenAI scorers ──────────────────────────────────────────────────
# scorer              → @scorer decorator for writing custom code-based scorers
# Correctness         → LLM judge: does the answer match the expected facts?
# RelevanceToQuery    → LLM judge: is the answer on-topic for the question?
# Safety              → LLM judge: no harmful or offensive content?
# RetrievalGroundedness  → LLM judge: is the answer grounded in retrieved chunks?
# RetrievalRelevance     → LLM judge: were the retrieved chunks relevant to the query?
# RetrievalSufficiency   → LLM judge: were the retrieved chunks enough to answer?
from mlflow.genai.scorers import (
    scorer,
    Correctness,       # LLM judge: does answer match expected_response?
    RelevanceToQuery,  # LLM judge: is the answer on-topic for the question?
    Safety,            # LLM judge: no harmful or offensive content?
    # NOTE: RetrievalGroundedness / RetrievalRelevance / RetrievalSufficiency
    # require a 'trace' column from live pipeline tracing — not used here.
    # Our custom faithfulness_scorer and context_relevance_scorer cover the same ground.
)


# ══════════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# All values have sensible defaults — override by setting the env var.
# ══════════════════════════════════════════════════════════════════════════

MLFLOW_URL        = "http://localhost:5001"
EXPERIMENT_A_NAME = "RAG-HotpotQA-Evaluation-v5"    # Part A → Model Training tab
EXPERIMENT_B_NAME = "RAG-HotpotQA-GenAI-Eval-v5"    # Part B → GenAI tab

PINECONE_INDEX    = "hotpotqa-ragbench-mini"
PINECONE_NS       = "hotpotqa"
EMBEDDING_MODEL   = "text-embedding-3-large"
GENERATOR_MODEL   = "gpt-4o-mini"
JUDGE_MODEL       = "gpt-4o-mini"
TOP_K             = 5      # how many chunks to retrieve per question
CHUNK_SIZE        = 400    # logged as a param so we can compare runs later

GOLDEN_FILE       = Path("ragbench_hotpotqa_exports/golden_hotpotqa_30.jsonl")

# Force MLflow to use our local server at import time.
# This overrides any MLFLOW_TRACKING_URI env var left over from a previous
# session (e.g. a 'databricks' value that would cause a 403 error).
mlflow.set_tracking_uri(MLFLOW_URL)


# ══════════════════════════════════════════════════════════════════════════
# GLOBAL CLIENTS
#
# WHY GLOBALS:
#   The @mlflow.trace decorated functions (retrieve_chunks, generate_answer,
#   run_rag_pipeline) cannot accept client objects as arguments through
#   the scorer interface. We store them as globals, set once in main()
#   before evaluation begins, and used by all pipeline functions below.
# ══════════════════════════════════════════════════════════════════════════

oai_client = None   # OpenAI client — set in main()
pine_index = None   # Pinecone index — set in main()


# ══════════════════════════════════════════════════════════════════════════
# LOAD DATA
#
# WHY WE RENAME FIELDS:
#   RAGBench uses different field names from what our pipeline expects.
#   We rename them once here so all downstream functions can safely use
#   'question', 'answer', 'contexts' without any conditionals scattered
#   throughout the code.
#
#   RAGBench schema  →  our internal name
#     input          →  question
#     reference      →  answer
#     contexts       →  contexts   (already a Python list, no change)
#     id             →  id         (no change)
# ══════════════════════════════════════════════════════════════════════════

def load_golden_data(filepath):
    """Load the 30 golden examples and rename fields to our convention."""
    examples = []

    with open(filepath, "r") as f:
        for line in f:
            raw = json.loads(line)
            example = {
                "id":       raw["id"],
                "question": raw["input"],      # RAGBench calls it 'input'
                "answer":   raw["reference"],  # RAGBench calls it 'reference'
                "contexts": raw["contexts"],   # already a Python list of strings
            }
            examples.append(example)

    log.info(f"Loaded {len(examples)} examples")
    log.info(f"  First question : {examples[0]['question'][:80]}")
    log.info(f"  First answer   : {examples[0]['answer'][:80]}")
    return examples


# ══════════════════════════════════════════════════════════════════════════
# RAG PIPELINE  —  Retrieve + Generate
#
# HOW @mlflow.trace WORKS:
#   Each function is decorated with @mlflow.trace so MLflow records what
#   goes in and comes out as a "span". The spans are nested into a tree:
#
#     run_rag_pipeline  [CHAIN]       ← root span, wraps the whole pipeline
#       retrieve_chunks [RETRIEVER]   ← child span, captures query + doc_ids
#       generate_answer [LLM]         ← child span, captures prompt + answer
#
#   In Part B — each call creates a waterfall trace in GenAI → Traces tab.
#   In Part A — the decorator does nothing. Functions run as normal.
# ══════════════════════════════════════════════════════════════════════════

@mlflow.trace(span_type="RETRIEVER")
def retrieve_chunks(question):
    """
    Embed the question and search Pinecone for the most similar chunks.
    Returns:
        doc_ids — Pinecone vector IDs of the matched chunks
        chunks  — actual text content of the matched chunks
    """
    embed_response  = oai_client.embeddings.create(model=EMBEDDING_MODEL, input=[question])
    question_vector = embed_response.data[0].embedding

    search_result = pine_index.query(
        vector=question_vector,
        top_k=TOP_K,
        namespace=PINECONE_NS,
        include_metadata=True
    )

    doc_ids = [match.id for match in search_result.matches]
    chunks  = [match.metadata.get("text", "") for match in search_result.matches]
    return doc_ids, chunks


@mlflow.trace(span_type="LLM")
def generate_answer(question, chunks):
    """
    Send the retrieved chunks + question to GPT and get a concise answer.

    System prompt strategy:
      'ONLY using the provided context' → forces grounding, prevents the
      model using knowledge it learned during training (reduces hallucinations).
      'say so explicitly' → model admits uncertainty rather than fabricating.
    """
    context_text = ""
    for i, chunk in enumerate(chunks):
        context_text += f"[{i+1}] {chunk}\n\n"

    response = oai_client.chat.completions.create(
        model=GENERATOR_MODEL,
        temperature=0,   # deterministic output for reproducible evaluation
        messages=[
            {
                "role": "system",
                "content": "Answer ONLY using the context provided. If the context lacks the answer, say so explicitly. Be concise — 1 to 3 sentences."
            },
            {
                "role": "user",
                "content": f"Context:\n{context_text}\nQuestion: {question}"
            }
        ]
    )
    return response.choices[0].message.content.strip()


@mlflow.trace(span_type="CHAIN")
def run_rag_pipeline(question):
    """
    Full RAG pipeline: retrieve chunks then generate an answer.
    This is the root span (CHAIN) — retrieve and generate are its children.
    In Part B, each call to this function creates ONE trace in the UI.
    """
    doc_ids, chunks = retrieve_chunks(question)
    answer          = generate_answer(question, chunks)
    return {"answer": answer, "doc_ids": doc_ids, "chunks": chunks}


# ══════════════════════════════════════════════════════════════════════════
# METRIC FAMILY 1 — RETRIEVAL METRICS  (pure Python, zero API calls)
#
# These metrics measure how good the RETRIEVER step is.
# They compare what we got from Pinecone against the known-correct doc ID.
#
# IMPORTANT NOTE:
#   All scores will be 0.0 if the Pinecone vector IDs don't match the
#   record IDs in the golden file. This happens when 2_ingest.py used
#   auto-generated chunk IDs. This is a data alignment issue — not a bug.
#   The LLM-judge metrics (Family 3) still work perfectly regardless.
# ══════════════════════════════════════════════════════════════════════════

def compute_retrieval_metrics(retrieved_ids, relevant_ids):
    """
    Precision@K  — of the K chunks we retrieved, what fraction was relevant?
                   High = low noise, Pinecone is returning the right docs.

    Recall@K     — of all relevant docs, what fraction did we retrieve?
                   High = we didn't miss important information.

    F1@K         — harmonic mean of Precision and Recall.
                   Single number when both P and R matter equally.

    Hit Rate     — did we retrieve AT LEAST one relevant chunk? (1.0 or 0.0)
                   Useful binary signal: is the pipeline ever useful at all?

    nDCG@K       — like Recall but position-aware: a relevant chunk at rank 1
                   is worth more than the same chunk at rank 5.
    """
    retrieved_set = set(retrieved_ids)
    relevant_set  = set(relevant_ids)
    hits          = retrieved_set & relevant_set
    k             = max(len(retrieved_ids), 1)
    n_relevant    = max(len(relevant_set), 1)

    precision = len(hits) / k
    recall    = len(hits) / n_relevant
    f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    hit_rate  = 1.0 if hits else 0.0

    # nDCG: penalise relevant docs found at lower rank positions
    dcg  = sum(1.0 / math.log2(i + 2) for i, d in enumerate(retrieved_ids) if d in relevant_set)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(n_relevant, k)))
    ndcg = dcg / idcg if idcg > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall":    round(recall,    4),
        "f1":        round(f1,        4),
        "ndcg":      round(ndcg,      4),
        "hit_rate":  round(hit_rate,  4),
    }


# ══════════════════════════════════════════════════════════════════════════
# METRIC FAMILY 2 — LEXICAL METRICS  (pure Python, zero API calls)
#
# These metrics compare the generated answer to the gold reference answer
# using simple word-level matching — fast and free, no model calls needed.
#
# LIMITATION:
#   Lexical metrics penalise correct paraphrases.
#   "Paris is France's capital" vs "The capital of France is Paris" would
#   score low on exact match but both are correct.
#   That is why we also use LLM-judge metrics (Family 3) which understand
#   meaning and not just word overlap.
# ══════════════════════════════════════════════════════════════════════════

def clean_text(text):
    """
    Lowercase and remove punctuation for fair comparison.
    Example: "It's Apple!" → "its apple"
    """
    result = text.lower()
    result = "".join(ch for ch in result if ch.isalnum() or ch.isspace())
    return result.strip()


def compute_exact_match(generated, reference):
    """
    1.0 if both answers are identical after cleaning, else 0.0.

    Very strict — a single extra word gives 0.0.
    If exact match is high, all other metrics will also be high.
    Use it as a lower bound check.
    """
    return 1.0 if clean_text(generated) == clean_text(reference) else 0.0


def compute_token_f1(generated, reference):
    """
    Word-overlap F1 between generated answer and reference answer.

    Splits both into words, then computes:
      Precision = overlap / generated_word_count
      Recall    = overlap / reference_word_count
      F1        = harmonic mean of P and R

    More forgiving than exact match — gives partial credit for mostly correct answers.
    Standard metric used in SQuAD and HotpotQA benchmarks.
    """
    gen_tokens = Counter(clean_text(generated).split())
    ref_tokens = Counter(clean_text(reference).split())
    overlap    = sum((gen_tokens & ref_tokens).values())

    if overlap == 0:
        return 0.0

    precision = overlap / sum(gen_tokens.values())
    recall    = overlap / sum(ref_tokens.values())
    return round(2 * precision * recall / (precision + recall), 4)


# ══════════════════════════════════════════════════════════════════════════
# METRIC FAMILY 3 — LLM-AS-JUDGE METRICS  (OpenAI API calls)
#
# These metrics use GPT (JUDGE_MODEL) to evaluate quality dimensions that
# word-matching cannot capture — faithfulness, relevance, completeness.
#
# HOW EACH JUDGE WORKS:
#   1. We write a prompt describing exactly what to evaluate
#   2. We ask the judge to return JSON: {"score": 0.0-1.0, "reasoning": "..."}
#   3. We parse the score and store the reasoning for debugging
#
# WHY JSON OUTPUT:
#   response_format={"type": "json_object"} forces the model to return
#   valid JSON every time. Without this the model may wrap the output in
#   markdown fences which breaks json.loads().
#
# These same functions are used by BOTH Part A (called directly) and
# Part B (called inside @scorer decorated functions).
# ══════════════════════════════════════════════════════════════════════════

def ask_judge(prompt):
    """
    Core helper — sends a scoring prompt to JUDGE_MODEL, returns (score, reasoning).
    Falls back to (0.0, raw_text) if the model returns unparseable output
    so evaluation never crashes on a bad judge response.
    """
    response = oai_client.chat.completions.create(
        model=JUDGE_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content
    try:
        result    = json.loads(raw)
        score     = float(result.get("score", 0.0))
        score     = max(0.0, min(1.0, score))   # clamp between 0 and 1
        reasoning = result.get("reasoning", "")
        return score, reasoning
    except Exception:
        return 0.0, raw   # fail soft — return 0 instead of crashing


# ── Context Relevance ────────────────────────────────────────────────────────
# WHAT IT MEASURES:
#   Are the chunks retrieved from Pinecone actually relevant to the question?
#   Scores each chunk individually and returns the average.
#
# WHY IT MATTERS:
#   This is the first leg of the RAG Triad. A low score here means the vector
#   search is returning noisy documents — fix the retriever before the generator.
#
# Score interpretation:
#   1.0 = every chunk directly addresses the question
#   0.5 = some chunks relevant, some tangential
#   0.0 = retrieved chunks completely unrelated to the question

def score_context_relevance(question, chunks):
    """Score how relevant the retrieved chunks are to the question (average across chunks)."""
    if not chunks:
        return 0.0, "no chunks retrieved"

    scores, reasons = [], []
    for chunk in chunks:
        score, reason = ask_judge(
            f"How relevant is this context chunk for answering the question?\n\n"
            f"Question: {question}\n"
            f"Context: {chunk[:800]}\n\n"
            f"1.0 = perfectly relevant | 0.5 = somewhat relevant | 0.0 = not relevant\n"
            f'Reply with JSON only: {{"score": 0.0 to 1.0, "reasoning": "one sentence"}}'
        )
        scores.append(score)
        reasons.append(reason)

    return round(sum(scores) / len(scores), 4), " | ".join(reasons[:2])


# ── Faithfulness ─────────────────────────────────────────────────────────────
# WHAT IT MEASURES:
#   Does the generated answer only contain facts that are present in the context?
#
# WHY IT MATTERS:
#   This is your primary HALLUCINATION detector.
#   A low score means the model used knowledge it learned during training
#   instead of the retrieved context — you lose source traceability.
#   This is the second leg of the RAG Triad.
#
# Score interpretation:
#   1.0 = every claim in the answer is directly supported by the context
#   0.5 = half the claims are supported, half are hallucinated
#   0.0 = the answer is entirely hallucinated, not grounded at all

def score_faithfulness(generated_answer, chunks):
    """Score whether the answer is fully supported by the retrieved context."""
    if not chunks:
        return 0.0, "no chunks retrieved"

    context_block = "\n".join(f"[{i+1}] {c[:500]}" for i, c in enumerate(chunks))

    return ask_judge(
        f"Does the answer only contain facts that are found in the context?\n\n"
        f"Context:\n{context_block}\n\n"
        f"Answer: {generated_answer}\n\n"
        f"Score = fraction of answer claims supported by the context.\n"
        f"1.0 = fully supported | 0.5 = partially | 0.0 = entirely hallucinated\n"
        f'Reply with JSON only: {{"score": 0.0 to 1.0, "reasoning": "list any unsupported claims"}}'
    )


# ── Answer Relevance ──────────────────────────────────────────────────────────
# WHAT IT MEASURES:
#   Does the generated answer actually address the question that was asked?
#
# WHY IT MATTERS:
#   Catches cases where the answer is factually correct and well-grounded
#   but doesn't answer what was asked (e.g. answers a different question).
#   This is the third leg of the RAG Triad.
#
# Score interpretation:
#   1.0 = fully addresses the question, no irrelevant content
#   0.5 = partially addresses, missing key aspects or slightly off-topic
#   0.0 = completely off-topic, refuses, or addresses a different question

def score_answer_relevance(question, generated_answer):
    """Score how directly the answer addresses the question."""
    return ask_judge(
        f"Does this answer properly address the question?\n\n"
        f"Question: {question}\n"
        f"Answer: {generated_answer}\n\n"
        f"1.0 = fully answers | 0.5 = partial answer | 0.0 = off-topic or refuses\n"
        f'Reply with JSON only: {{"score": 0.0 to 1.0, "reasoning": "one sentence"}}'
    )


# ── Completeness ──────────────────────────────────────────────────────────────
# WHAT IT MEASURES:
#   Does the answer cover ALL key points from the gold reference answer?
#
# WHY IT MATTERS:
#   A faithful answer can still be incomplete — it might be grounded in the
#   context but miss key facts from the reference. Catches answers that are
#   too brief or skip important details.
#
#   Example: Reference = "Paris is the capital and largest city of France."
#            Generated = "Paris is in France." → faithful but only 50% complete.
#
# Score interpretation:
#   1.0 = all key points from the reference are present in the answer
#   0.5 = roughly half the reference points are covered
#   0.0 = answer covers none of the expected key points

def score_completeness(generated_answer, reference_answer):
    """Score what fraction of the reference answer's key points appear in the generated answer."""
    return ask_judge(
        f"Does the generated answer cover all key points from the reference answer?\n\n"
        f"Reference: {reference_answer}\n"
        f"Generated: {generated_answer}\n\n"
        f"Score = fraction of reference key points present in generated answer.\n"
        f"1.0 = covers everything | 0.5 = covers half | 0.0 = misses everything\n"
        f'Reply with JSON only: {{"score": 0.0 to 1.0, "reasoning": "list any missing points"}}'
    )


# ── Conciseness ───────────────────────────────────────────────────────────────
# WHAT IT MEASURES:
#   Is the answer short and focused, or unnecessarily long and padded?
#
# WHY IT MATTERS:
#   Verbose answers are a UX problem for QA pipelines — especially for voice
#   assistants or chat snippets. Also, overly hedged verbose answers often
#   signal that the model is uncertain and padding instead of answering.
#
# Score interpretation:
#   1.0 = perfectly concise, every sentence contributes information
#   0.5 = slightly padded, a few unnecessary phrases
#   0.0 = excessively verbose, heavily padded or repeats the question

def score_conciseness(question, generated_answer):
    """Score how concise and focused the answer is."""
    return ask_judge(
        f"Is this answer concise and to the point, or too long and padded?\n\n"
        f"Question: {question}\n"
        f"Answer: {generated_answer}\n\n"
        f"1.0 = perfectly concise | 0.5 = slightly wordy | 0.0 = far too long\n"
        f'Reply with JSON only: {{"score": 0.0 to 1.0, "reasoning": "one sentence"}}'
    )


# ── RAG Triad ─────────────────────────────────────────────────────────────────
# WHAT IT MEASURES:
#   A single composite score that captures the entire RAG pipeline health.
#   Combines the three legs: Context Relevance + Faithfulness + Answer Relevance.
#
# WHY HARMONIC MEAN (not arithmetic mean):
#   Unlike arithmetic mean, harmonic mean collapses the score toward zero if
#   ANY single leg is near zero. This is intentional — a pipeline that retrieves
#   irrelevant context, hallucinates, OR answers the wrong question should score
#   near zero overall, regardless of how well the other two legs perform.
#
#   Example:
#     CR=1.0, Faith=1.0, AR=0.0  →  triad = 0.0  (useless, wrong question answered)
#     CR=0.8, Faith=0.8, AR=0.8  →  triad = 0.8  (solid, well-balanced pipeline)
#
# HOW TO USE IT:
#   Start with the RAG Triad as your headline metric.
#   When it's low, drill into the three individual legs to find the weak link.

def compute_rag_triad(context_relevance, faithfulness, answer_relevance):
    """Harmonic mean of context relevance, faithfulness, and answer relevance."""
    cr, fa, ar = context_relevance, faithfulness, answer_relevance
    denom = cr * fa + fa * ar + ar * cr
    if denom == 0:
        return 0.0
    return round(3 * cr * fa * ar / denom, 4)


# ══════════════════════════════════════════════════════════════════════════
# PART A — MODEL TRAINING MODE
#
# HOW IT WORKS:
#   We run the RAG pipeline on all 30 examples ourselves, compute every
#   metric manually, and log results to MLflow using the classic tracking API.
#
# MLFLOW LOGGING BREAKDOWN:
#   log_params()        → config (model names, top_k, chunk_size, etc.)
#   log_metrics()       → 13 aggregate averages  (avg_faithfulness, etc.)
#   log_metrics(step=i) → 4 per-example metrics as time-series line charts
#   log_artifact()      → eval_results.jsonl + judge_reasoning.json
#
# WHERE TO SEE RESULTS:
#   MLflow UI → Model Training tab → RAG-HotpotQA-Evaluation → this run
# ══════════════════════════════════════════════════════════════════════════

def evaluate_one_example(example):
    """
    Run the full pipeline + all three metric families on ONE example.
    Called 30 times — once per golden example — inside run_part_a().

    Each call makes approximately 9 OpenAI API calls:
      1  embeddings call  (retrieve_chunks)
      1  chat call        (generate_answer)
      5+ chat calls       (LLM judges — context_relevance loops per chunk)
    """
    question  = example["question"]
    reference = example["answer"]

    # Run retrieval + generation
    doc_ids, chunks = retrieve_chunks(question)
    generated       = generate_answer(question, chunks)

    # Family 1 — Retrieval metrics (pure Python, no API calls)
    # We use the example's own id as the single "correct" doc to retrieve.
    retrieval = compute_retrieval_metrics(doc_ids, [example["id"]])

    # Family 2 — Lexical metrics (pure Python, no API calls)
    em  = compute_exact_match(generated, reference)
    tf1 = compute_token_f1(generated, reference)

    # Family 3 — LLM-judge metrics (API calls to JUDGE_MODEL)
    cr_score,   cr_reason   = score_context_relevance(question, chunks)
    fa_score,   fa_reason   = score_faithfulness(generated, chunks)
    ar_score,   ar_reason   = score_answer_relevance(question, generated)
    comp_score, comp_reason = score_completeness(generated, reference)
    conc_score, conc_reason = score_conciseness(question, generated)
    triad                   = compute_rag_triad(cr_score, fa_score, ar_score)

    return {
        # Inputs and outputs — saved to file for review
        "question":         question,
        "reference":        reference,
        "generated_answer": generated,
        "retrieved_ids":    doc_ids,

        # Retrieval scores
        "precision": retrieval["precision"],
        "recall":    retrieval["recall"],
        "f1":        retrieval["f1"],
        "ndcg":      retrieval["ndcg"],
        "hit_rate":  retrieval["hit_rate"],

        # Lexical scores
        "exact_match": em,
        "token_f1":    tf1,

        # LLM-judge scores
        "context_relevance": cr_score,
        "faithfulness":      fa_score,
        "answer_relevance":  ar_score,
        "rag_triad":         triad,
        "completeness":      comp_score,
        "conciseness":       conc_score,

        # Reasoning text — saved to a separate file for debugging low scores
        # NOT logged as MLflow metrics (too verbose)
        "cr_reasoning":   cr_reason,
        "fa_reasoning":   fa_reason,
        "ar_reasoning":   ar_reason,
        "comp_reasoning": comp_reason,
        "conc_reasoning": conc_reason,
    }


def average_scores(all_results):
    """
    Average each metric across all 30 examples.
    The 'avg_' prefix makes the MLflow Metrics tab easy to read and sort.
    """
    metric_names = [
        "precision", "recall", "f1", "ndcg", "hit_rate",
        "exact_match", "token_f1",
        "context_relevance", "faithfulness", "answer_relevance",
        "rag_triad", "completeness", "conciseness",
    ]
    n = len(all_results)
    return {f"avg_{name}": round(sum(r[name] for r in all_results) / n, 4) for name in metric_names}


def _get_or_restore_experiment(name):
    """
    Get experiment by name — handles the 'deleted experiment' edge case.

    If you delete an experiment in the MLflow UI, it enters a soft-deleted state.
    Calling mlflow.set_experiment() on a soft-deleted name raises:
      "Cannot set a deleted experiment as the active experiment"

    This function:
      1. Checks if the experiment exists and is active → use it
      2. Checks if it exists but is deleted → restore it automatically
      3. If it doesn't exist at all → MLflow creates it fresh

    Students: this is why we wrap set_experiment() instead of calling it directly.
    """
    from mlflow.tracking import MlflowClient
    from mlflow.entities import ViewType

    client = MlflowClient()
    exp    = client.get_experiment_by_name(name)

    if exp is not None and exp.lifecycle_stage == "deleted":
        # Restore the soft-deleted experiment so we can use it again
        client.restore_experiment(exp.experiment_id)
        log.info(f"Restored deleted experiment '{name}'  id={exp.experiment_id}")

    mlflow.set_experiment(name)


def run_part_a(golden_data):
    """Part A — evaluate all 30 examples and log to MLflow Model Training tab."""
    mlflow.set_tracking_uri(MLFLOW_URL)
    _get_or_restore_experiment(EXPERIMENT_A_NAME)

    with mlflow.start_run(run_name=f"part_a_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):

        # Log config params — visible in Params tab, enables Compare Runs view
        mlflow.log_params({
            "embedding_model": EMBEDDING_MODEL,
            "generator_model": GENERATOR_MODEL,
            "judge_model":     JUDGE_MODEL,
            "top_k":           TOP_K,
            "chunk_size":      CHUNK_SIZE,
            "num_examples":    len(golden_data),
        })

        # Evaluate every example one by one
        all_results = []
        for i, example in enumerate(golden_data):
            log.info(f"  [{i+1}/{len(golden_data)}] {example['question'][:65]}...")
            result = evaluate_one_example(example)
            all_results.append(result)

        # Log aggregate metrics — visible in Metrics tab as single scalar values.
        # Sort runs by avg_rag_triad in the UI to find the best configuration.
        averages = average_scores(all_results)
        mlflow.log_metrics(averages)

        # Log per-example scores as steps — MLflow shows these as line charts.
        # Useful for spotting hard questions or outlier examples.
        for step, result in enumerate(all_results):
            mlflow.log_metrics({
                "faithfulness":      result["faithfulness"],
                "context_relevance": result["context_relevance"],
                "answer_relevance":  result["answer_relevance"],
                "rag_triad":         result["rag_triad"],
            }, step=step)

        # Save clean scores to JSONL (no reasoning — good for pandas analysis)
        results_file = "eval_results.jsonl"
        with open(results_file, "w") as f:
            for r in all_results:
                clean = {k: v for k, v in r.items() if "reasoning" not in k}
                f.write(json.dumps(clean) + "\n")
        mlflow.log_artifact(results_file)

        # Save verbose judge reasoning to JSON (for debugging low-scoring examples)
        reasoning_file = "judge_reasoning.json"
        reasoning_data = [
            {
                "question":          r["question"],
                "generated_answer":  r["generated_answer"],
                "faithfulness":      {"score": r["faithfulness"],       "why": r["fa_reasoning"]},
                "context_relevance": {"score": r["context_relevance"],  "why": r["cr_reasoning"]},
                "answer_relevance":  {"score": r["answer_relevance"],   "why": r["ar_reasoning"]},
            }
            for r in all_results
        ]
        with open(reasoning_file, "w") as f:
            json.dump(reasoning_data, f, indent=2)
        mlflow.log_artifact(reasoning_file)

        # Print summary table to terminal
        log.info("\n" + "=" * 55)
        log.info("  PART A RESULTS — Model Training Mode")
        log.info("=" * 55)
        log.info(f"  {'Metric':<32} {'Score':>8}")
        log.info("-" * 55)
        for name, value in averages.items():
            log.info(f"  {name:<32} {value:>8.4f}")
        log.info("=" * 55)
        log.info(f"  View → {MLFLOW_URL}  (Model Training tab)")
        log.info("=" * 55)


# ══════════════════════════════════════════════════════════════════════════
# PART B — GENAI MODE
#
# HOW IT WORKS:
#   1. TRACING   — run_rag_pipeline() is decorated with @mlflow.trace so
#      each call creates a CHAIN → RETRIEVER → LLM waterfall in the UI.
#   2. EVALUATION — mlflow.genai.evaluate() runs every scorer on every
#      row of a DataFrame and shows a results table in the GenAI tab.
#
# WHERE TO SEE RESULTS:
#   MLflow UI → GenAI tab → Traces          (waterfall view per example)
#   MLflow UI → GenAI tab → Eval Results    (per-row scorer table)
#
# ── BUILT-IN SCORERS  (MLflow provides these — no prompts needed) ──────────
#
#   Correctness()          → does the answer match the expected gold answer?
#                            Compares outputs vs expected_output using LLM judge.
#
#   RelevanceToQuery()     → is the answer actually addressing the question?
#                            Catches off-topic or tangential answers.
#
#   Safety()               → does the answer contain harmful or offensive content?
#                            Hard gate — should always pass for a QA pipeline.
#
#   RetrievalGroundedness() → is the answer grounded in the retrieved chunks?
#                             Flags hallucinations. Parses the RETRIEVER span.
#
#   RetrievalRelevance()    → were the retrieved chunks relevant to the question?
#                             Low score = Pinecone returning noisy docs.
#                             Parses the RETRIEVER span.
#
#   RetrievalSufficiency()  → were the chunks enough to fully answer the question?
#                             Low score = right topic retrieved but key facts missing.
#                             Parses the RETRIEVER span.
#
# ── CUSTOM SCORERS  (we wrote the judge prompts ourselves using @scorer) ───
#
#   context_relevance_scorer  → same as score_context_relevance(), continuous 0-1
#   faithfulness_scorer       → same as score_faithfulness(), claim-by-claim check
#   answer_relevance_scorer   → same as score_answer_relevance(), continuous 0-1
#   rag_triad_scorer          → harmonic mean of the three above
#   completeness_scorer       → covers all reference key points?
#   conciseness_scorer        → short and focused?
#
# WHY CUSTOM SCORERS ALONGSIDE BUILT-INS:
#   Built-in scorers use generic prompts for broad evaluation.
#   Our custom scorers use domain-specific RAG prompts — e.g. faithfulness
#   checks claim-by-claim and rag_triad uses harmonic mean which collapses
#   on any weak leg. Both sets complement each other.
# ══════════════════════════════════════════════════════════════════════════

def _decode_outputs(outputs):
    """
    predict_fn returns a JSON string encoding both answer and retrieved_context.
    This helper decodes it so scorers can access both fields.

    Why JSON string instead of a dict:
      mlflow.genai.evaluate() expects outputs to be a string (the generated answer).
      We encode extra data (retrieved_context) in the same string as JSON so we can
      carry it through to our custom scorers without losing it.

    Returns: (answer_str, retrieved_context_list)
    """
    try:
        data = json.loads(outputs)
        return data.get("answer", str(outputs)), data.get("retrieved_context", [])
    except Exception:
        # If outputs is a plain string (not JSON), treat it as just the answer
        return str(outputs), []


@scorer
def context_relevance_scorer(inputs, outputs, expectations, **kwargs):
    """
    Custom scorer: average relevance of each retrieved chunk to the question.

    inputs   → {"query": ...}
    outputs  → JSON string from predict_fn — decode to get answer + retrieved_context
    """
    query              = inputs.get("query", "") if isinstance(inputs, dict) else str(inputs)
    _, retrieved_context = _decode_outputs(outputs)
    if not retrieved_context:
        return 0.0
    score, _ = score_context_relevance(query, list(retrieved_context))
    return score


@scorer
def faithfulness_scorer(inputs, outputs, expectations, **kwargs):
    """
    Custom scorer: does the answer only contain facts from the retrieved chunks?

    outputs → JSON string from predict_fn — decode to get answer + retrieved_context
    """
    answer, retrieved_context = _decode_outputs(outputs)
    if not retrieved_context:
        return 0.0
    score, _ = score_faithfulness(answer, list(retrieved_context))
    return score


@scorer
def answer_relevance_scorer(inputs, outputs, **kwargs):
    """
    Custom scorer: does the answer properly address the question?

    inputs  → {"query": ...}
    outputs → JSON string from predict_fn — decode to get the answer
    """
    query  = inputs.get("query", "") if isinstance(inputs, dict) else str(inputs)
    answer, _ = _decode_outputs(outputs)
    score, _  = score_answer_relevance(query, answer)
    return score


# NOTE: rag_triad_scorer is NOT included in mlflow.genai.evaluate() scorers.
# Running it as a separate scorer would duplicate all the API calls already made
# by context_relevance_scorer, faithfulness_scorer, and answer_relevance_scorer
# — tripling the cost for 30 examples.
#
# Instead, we compute the RAG Triad AFTER evaluation from the per-row results.
# See _compute_rag_triad_from_results() called after mlflow.genai.evaluate().

def _compute_rag_triad_from_results(results_df):
    """
    Compute RAG Triad per row from the individual scorer columns already computed.
    Called after mlflow.genai.evaluate() — zero extra API calls.

    Looks for columns: context_relevance_scorer/score, faithfulness_scorer/score,
    answer_relevance_scorer/score (MLflow names scorer columns as 'scorername/score').
    """
    triad_scores = []
    for _, row in results_df.iterrows():
        cr = row.get("context_relevance_scorer/score", 0.0) or 0.0
        fa = row.get("faithfulness_scorer/score",       0.0) or 0.0
        ar = row.get("answer_relevance_scorer/score",   0.0) or 0.0
        triad_scores.append(compute_rag_triad(float(cr), float(fa), float(ar)))
    return triad_scores


@scorer
def completeness_scorer(inputs, outputs, expectations, **kwargs):
    """
    Custom scorer: does the answer cover all key points from the reference?

    outputs      → JSON string from predict_fn — decode to get the answer
    expectations → dict containing expected_output
    """
    answer, _       = _decode_outputs(outputs)
    expected_output = expectations.get("expected_output", "") if isinstance(expectations, dict) else ""
    if not expected_output:
        return 0.0
    score, _ = score_completeness(answer, str(expected_output))
    return score


@scorer
def conciseness_scorer(inputs, outputs, **kwargs):
    """Custom scorer: is the answer concise and focused?

    inputs  → {"query": ...}
    outputs → JSON string from predict_fn — decode to get the answer
    """
    query  = inputs.get("query", "") if isinstance(inputs, dict) else str(inputs)
    answer, _ = _decode_outputs(outputs)
    score, _  = score_conciseness(query, answer)
    return score


def run_part_b(golden_data):
    """
    Part B — trace the pipeline and evaluate with mlflow.genai.evaluate().

    DATAFRAME FORMAT RULES (MLflow 3 strict requirements):
      inputs            → must be a DICT e.g. {"query": "..."}, not a plain string
      outputs           → plain string — the generated answer
      expected_output   → plain string — the gold reference answer
      retrieved_context → list of strings — the retrieved chunks
      expectations      → dict with {"expected_response": "..."} for Correctness scorer

    BUILT-IN SCORERS USED HERE:
      Correctness()       → needs 'expectations' column with expected_response
      RelevanceToQuery()  → needs 'inputs' dict and 'outputs' string
      Safety()            → needs 'outputs' string only

    SCORERS NOT USED (require a 'trace' column from live pipeline tracing,
    not compatible with a static pre-built DataFrame):
      RetrievalGroundedness, RetrievalRelevance, RetrievalSufficiency
      Our custom faithfulness_scorer and context_relevance_scorer cover
      the same ground using our own judge prompts — no traces needed.
    """
    mlflow.set_tracking_uri(MLFLOW_URL)
    _get_or_restore_experiment(EXPERIMENT_B_NAME)

    with mlflow.start_run(run_name=f"part_b_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):

        mlflow.log_params({
            "embedding_model": EMBEDDING_MODEL,
            "generator_model": GENERATOR_MODEL,
            "judge_model":     JUDGE_MODEL,
            "top_k":           TOP_K,
            "num_examples":    len(golden_data),
        })

        # HOW TRACING + SCORING WORKS IN ONE PASS:
        #
        #   We pass predict_fn to mlflow.genai.evaluate() instead of pre-building
        #   a DataFrame with outputs already filled in.
        #
        #   mlflow.genai.evaluate() then:
        #     1. Calls predict_fn(row["inputs"]) for each row
        #     2. Records the call as a trace (CHAIN → RETRIEVER → LLM) automatically
        #        because run_rag_pipeline is decorated with @mlflow.trace
        #     3. Stores the return value in the 'outputs' column
        #     4. Runs every scorer on that row
        #
        #   This gives us exactly 30 traces, all scored — no duplicates.
        #
        #   WHY WE STORE chunks IN A DICT (not just return the answer string):
        #     Our custom scorers need retrieved_context. predict_fn must return
        #     a string for MLflow's outputs column, but we need the chunks too.
        #     Solution: return a JSON string that encodes both, then unpack in scorers.

        def predict_fn(query):
            """
            Wrapper around run_rag_pipeline for mlflow.genai.evaluate().

            WHY the argument is named 'query' (not 'inputs'):
              MLflow unpacks the inputs dict as **kwargs into predict_fn.
              So {"query": "..."} → predict_fn(query="...").
              The parameter name here MUST match the key in the inputs dict.

            Returns a JSON string so we can carry retrieved_context through
            the outputs column to our custom scorers.
            """
            result = run_rag_pipeline(query)
            # Encode answer + chunks as JSON string — scorers will decode this
            return json.dumps({
                "answer": result["answer"],
                "retrieved_context": result["chunks"],
            })

        # Build input-only DataFrame — predict_fn fills in the outputs column
        eval_df = pd.DataFrame([
            {
                "inputs": {"query": example["question"]},
                "expectations": {
                    "expected_response": example["answer"],  # Correctness() reads this
                    "expected_output":   example["answer"],  # completeness_scorer reads this
                },
            }
            for example in golden_data
        ])

        log.info(f"  Built eval DataFrame with {len(eval_df)} rows")

        # Run evaluation — MLflow calls predict_fn, creates traces, runs scorers
        log.info("  Running mlflow.genai.evaluate() with 8 scorers...")
        results = mlflow.genai.evaluate(
            data=eval_df,
            predict_fn=predict_fn,
            scorers=[

                # ── Built-in MLflow scorers ────────────────────────────────────
                # Compares outputs against expectations.expected_response
                Correctness(),

                # Checks if the answer is relevant and on-topic for the question
                RelevanceToQuery(),

                # Checks for harmful or offensive content in the answer
                Safety(),

                # ── Custom scorers (our own judge prompts) ─────────────────────
                # Are the retrieved chunks relevant to the question? (avg per chunk)
                context_relevance_scorer,

                # Does the answer only contain facts from the retrieved context?
                # This is our hallucination detector — replaces RetrievalGroundedness
                faithfulness_scorer,

                # Does the answer properly address the question?
                answer_relevance_scorer,

                # NOTE: RAG Triad is computed after evaluate() from the 3 scores above.
                # Keeping it here would duplicate ~7 API calls per example × 30 = 210 wasted calls.

                # Does the answer cover all key points from the reference?
                completeness_scorer,

                # Is the answer concise and focused (not padded or verbose)?
                conciseness_scorer,
            ]
        )

        # Compute RAG Triad from individual scorer columns — zero extra API calls
        try:
            triad_scores = _compute_rag_triad_from_results(results.tables["eval_results"])
            avg_triad    = round(sum(triad_scores) / len(triad_scores), 4)
            mlflow.log_metric("avg_rag_triad", avg_triad)
            log.info(f"  RAG Triad (post-eval) = {avg_triad:.4f}")
        except Exception as e:
            log.warning(f"  Could not compute RAG Triad: {e}")

        # Print summary
        log.info("\n" + "=" * 55)
        log.info("  PART B RESULTS — GenAI Mode  (8 scorers + RAG Triad computed post-eval)")
        log.info("=" * 55)
        log.info(f"  {'Scorer':<32} {'Score':>8}")
        log.info("-" * 55)
        for name, value in results.metrics.items():
            if isinstance(value, (int, float)):
                log.info(f"  {name:<32} {float(value):>8.4f}")
        log.info("=" * 55)
        log.info(f"  Traces  → {MLFLOW_URL}  (GenAI tab → Traces)")
        log.info(f"  Results → {MLFLOW_URL}  (GenAI tab → Eval Results)")
        log.info("=" * 55)


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="RAG Evaluation Pipeline — MLflow 3")
    parser.add_argument(
        "--mode",
        choices=["a", "b", "both"],
        default="a",
        help="a = Part A (hand-coded metrics)  |  b = Part B (GenAI mode)  |  both = run both"
    )
    args = parser.parse_args()

    if not GOLDEN_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {GOLDEN_FILE}\n"
            "Please run 1_prepare_dataset.py first."
        )

    golden_data = load_golden_data(GOLDEN_FILE)
    log.info(f"Mode: {args.mode}")

    # Set up clients and store in globals so @mlflow.trace functions can use them
    global oai_client, pine_index
    oai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pc         = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    pine_index = pc.Index(PINECONE_INDEX)

    # Re-assert tracking URI — overrides any env var set after module load
    mlflow.set_tracking_uri(MLFLOW_URL)

    if args.mode in ("a", "both"):
        log.info("\n── PART A ─────────────────────────────────────────────")
        run_part_a(golden_data)

    if args.mode in ("b", "both"):
        log.info("\n── PART B ─────────────────────────────────────────────")
        run_part_b(golden_data)

    log.info(f"\nAll done! Open {MLFLOW_URL} to see your results.")
    if args.mode in ("a", "both"):
        log.info("  Model Training tab → params, metrics, step charts, artifacts")
    if args.mode in ("b", "both"):
        log.info("  GenAI tab          → traces waterfall + 11-scorer eval table")


if __name__ == "__main__":
    main()