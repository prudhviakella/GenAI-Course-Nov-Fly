"""
RAG Evaluation Pipeline — Dual Mode
-------------------------------------
  Part A  →  Hand-coded metrics  →  MLflow Model Training mode
              (log_params / log_metrics / log_artifact)

  Part B  →  mlflow.genai.evaluate() + Scorers  →  MLflow GenAI mode
              (@mlflow.trace / @scorer / built-in scorers)

Prerequisites:
  1. MLflow 3 server running:
       mlflow server \
          --backend-store-uri postgresql://mlflow_user:mlflow_pass@your-rds-endpoint.rds.amazonaws.com:5432/mlflow_db \
          --default-artifact-root s3://your-bucket/mlflow-artifacts \
          --host 0.0.0.0 \
          --port 5000

  2. Env vars:
       export OPENAI_API_KEY="sk-..."
       export PINECONE_API_KEY="pcn-..."

  3. golden_hotpotqa_30.jsonl  (from 1_prepare_dataset.py)
  4. Pinecone index populated  (from 2_ingest.py)

Run:
  python 3_eval.py --mode part_a   # hand-coded → Model Training tab
  python 3_eval.py --mode part_b   # mlflow.genai → GenAI tab
  python 3_eval.py --mode both     # run both (default)
"""

import argparse
import json
import logging
import math
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

import mlflow
import mlflow.genai
from mlflow.genai import scorer
from mlflow.tracking import MlflowClient

import openai
from pinecone import Pinecone

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("rag_eval")

# ── Config ────────────────────────────────────────────────────────────────
GOLDEN_PATH     = Path("ragbench_hotpotqa_exports/golden_hotpotqa_30.jsonl")
INDEX_NAME      = os.getenv("PINECONE_INDEX",   "hotpotqa-ragbench-mini")
NAMESPACE       = os.getenv("PINECONE_NS",      "hotpotqa")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL",  "text-embedding-3-large")
JUDGE_MODEL     = os.getenv("JUDGE_MODEL",      "gpt-4o-mini")
GENERATOR_MODEL = os.getenv("GENERATOR_MODEL",  "gpt-4o-mini")
TOP_K           = int(os.getenv("TOP_K",        "5"))
CHUNK_SIZE      = int(os.getenv("CHUNK_SIZE",   "400"))

# ── MLflow Config ─────────────────────────────────────────────────────────
MLFLOW_URI          = os.getenv("MLFLOW_URI",            "http://localhost:5000")
EXPERIMENT_PART_A   = os.getenv("MLFLOW_EXP_A",          "RAG-HotpotQA-Evaluation")     # Model Training tab
EXPERIMENT_PART_B   = os.getenv("MLFLOW_EXP_B",          "RAG-HotpotQA-GenAI-Eval")     # GenAI tab
MODEL_NAME          = "RAG-HotpotQA-Pipeline"

# Module-level client refs — set in main() and used by @scorer functions
_oai: openai.OpenAI = None
_index              = None


# ══════════════════════════════════════════════════════════════════════════
# MLFLOW SETUP
# ══════════════════════════════════════════════════════════════════════════

def setup_mlflow(experiment_name: str, mode_tag: str) -> str:
    """
    Connect to the tracking server and create the experiment if missing.
    Returns the experiment_id.
    """
    mlflow.set_tracking_uri(MLFLOW_URI)

    exp = mlflow.get_experiment_by_name(experiment_name)
    if exp is None:
        experiment_id = mlflow.create_experiment(
            name=experiment_name,
            artifact_location=f"./mlflow-artifacts/{experiment_name.lower().replace(' ', '-')}",
            tags={
                "project": "Applied GenAI Course",
                "dataset": "RAGBench HotpotQA",
                "owner":   "Prudhvi",
                "mode":    mode_tag,
            },
        )
        log.info(f"Created experiment '{experiment_name}' id={experiment_id}")
    else:
        experiment_id = exp.experiment_id
        log.info(f"Using  experiment '{experiment_name}' id={experiment_id}")

    mlflow.set_experiment(experiment_name)
    return experiment_id


# ══════════════════════════════════════════════════════════════════════════
# CLIENTS
# ══════════════════════════════════════════════════════════════════════════

def build_clients():
    for k in ("OPENAI_API_KEY", "PINECONE_API_KEY"):
        if not os.getenv(k):
            raise RuntimeError(f"Missing env var: {k}")
    oai = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pc  = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    return oai, pc


def load_golden(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


# ══════════════════════════════════════════════════════════════════════════
# RETRIEVAL + GENERATION
# (decorated with @mlflow.trace so Part B captures full span tree)
# ══════════════════════════════════════════════════════════════════════════

@mlflow.trace(name="retrieve", span_type="RETRIEVER")
def retrieve(query: str, oai: openai.OpenAI, index) -> List:
    """Embed the query and fetch top-K chunks from Pinecone."""
    resp   = oai.embeddings.create(model=EMBEDDING_MODEL, input=[query])
    vector = resp.data[0].embedding
    result = index.query(vector=vector, top_k=TOP_K, namespace=NAMESPACE, include_metadata=True)
    return result.matches


@mlflow.trace(name="generate_answer", span_type="LLM")
def generate_answer(query: str, contexts: List[str], oai: openai.OpenAI) -> str:
    """Generate an answer using the retrieved contexts."""
    ctx_block = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    system = (
        "You are a precise QA assistant. Answer ONLY using the provided context. "
        "If the context lacks the answer, say so. Be concise — 1-3 sentences."
    )
    resp = oai.chat.completions.create(
        model=GENERATOR_MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": f"Context:\n{ctx_block}\n\nQuestion: {query}"}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()


@mlflow.trace(name="rag_pipeline", span_type="CHAIN")
def rag_pipeline(query: str, oai: openai.OpenAI, index) -> Dict:
    """
    Full RAG chain: retrieve → generate.
    Traced as a CHAIN span with child RETRIEVER and LLM spans.
    Used by Part B to capture traces for the GenAI UI.
    """
    matches  = retrieve(query, oai, index)
    contexts = [m.metadata.get("text", "") for m in matches]
    ret_ids  = [m.id for m in matches]
    answer   = generate_answer(query, contexts, oai)
    return {"answer": answer, "contexts": contexts, "retrieved_ids": ret_ids}


# ══════════════════════════════════════════════════════════════════════════
# METRIC FAMILY 1 — RETRIEVAL (pure Python)
# ══════════════════════════════════════════════════════════════════════════

def retrieval_metrics(retrieved_ids: List[str], relevant_ids: List[str]) -> Dict:
    ret_set = set(retrieved_ids)
    rel_set = set(relevant_ids)
    hits    = ret_set & rel_set
    k       = len(retrieved_ids) or 1
    n_rel   = len(rel_set) or 1

    precision = len(hits) / k
    recall    = len(hits) / n_rel
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    hit_rate  = 1.0 if hits else 0.0

    dcg  = sum(1.0 / math.log2(i + 2) for i, d in enumerate(retrieved_ids) if d in rel_set)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(rel_set), k)))
    ndcg = dcg / idcg if idcg else 0.0

    return {
        "precision": round(precision, 4),
        "recall":    round(recall,    4),
        "f1":        round(f1,        4),
        "ndcg":      round(ndcg,      4),
        "hit_rate":  round(hit_rate,  4),
    }


# ══════════════════════════════════════════════════════════════════════════
# METRIC FAMILY 2 — LEXICAL (pure Python)
# ══════════════════════════════════════════════════════════════════════════

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", text.lower())).strip()

def exact_match(answer: str, reference: str) -> float:
    return 1.0 if _norm(answer) == _norm(reference) else 0.0

def token_f1(answer: str, reference: str) -> float:
    a = Counter(_norm(answer).split())
    r = Counter(_norm(reference).split())
    common = sum((a & r).values())
    if not common:
        return 0.0
    p   = common / sum(a.values())
    rec = common / sum(r.values())
    return round(2 * p * rec / (p + rec), 4)


# ══════════════════════════════════════════════════════════════════════════
# METRIC FAMILY 3 — LLM JUDGE (shared by Part A and Part B scorers)
# ══════════════════════════════════════════════════════════════════════════

def _judge(prompt: str, oai: openai.OpenAI) -> Tuple[float, str]:
    """Call the judge LLM. Returns (score 0-1, reasoning string)."""
    resp = oai.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content
    try:
        data  = json.loads(raw)
        score = max(0.0, min(1.0, float(data.get("score", 0.0))))
        return score, data.get("reasoning", "")
    except Exception:
        return 0.0, raw


def _context_relevance(query: str, contexts: List[str], oai: openai.OpenAI) -> Tuple[float, str]:
    scores, reasons = [], []
    for ctx in contexts:
        s, r = _judge(
            f"Rate how relevant this context is for answering the question.\n\n"
            f"Question: {query}\nContext: {ctx[:1000]}\n\n"
            f'Return JSON: {{"score": <0.0-1.0>, "reasoning": "<brief>"}}',
            oai,
        )
        scores.append(s)
        reasons.append(r)
    return round(sum(scores) / len(scores), 4) if scores else 0.0, " | ".join(reasons[:2])


def _faithfulness(answer: str, contexts: List[str], oai: openai.OpenAI) -> Tuple[float, str]:
    ctx_block = "\n".join(f"[{i+1}] {c[:600]}" for i, c in enumerate(contexts))
    return _judge(
        f"Check whether every factual claim in the answer is grounded in the context.\n\n"
        f"Context:\n{ctx_block}\n\nAnswer: {answer}\n\n"
        f"score = supported_claims / total_claims\n"
        f'Return JSON: {{"score": <0.0-1.0>, "reasoning": "<unsupported claims if any>"}}',
        oai,
    )


def _answer_relevance(query: str, answer: str, oai: openai.OpenAI) -> Tuple[float, str]:
    return _judge(
        f"Rate how directly the answer addresses the question.\n\n"
        f"Question: {query}\nAnswer: {answer}\n\n"
        f"1.0=fully addresses | 0.5=partial | 0.0=off-topic\n"
        f'Return JSON: {{"score": <0.0-1.0>, "reasoning": "<brief>"}}',
        oai,
    )


def _completeness(answer: str, reference: str, oai: openai.OpenAI) -> Tuple[float, str]:
    return _judge(
        f"Does the generated answer cover all key points from the reference?\n\n"
        f"Reference: {reference}\nGenerated: {answer}\n\n"
        f"score = fraction of reference key points covered\n"
        f'Return JSON: {{"score": <0.0-1.0>, "reasoning": "<missing points>"}}',
        oai,
    )


def _conciseness(query: str, answer: str, oai: openai.OpenAI) -> Tuple[float, str]:
    return _judge(
        f"Rate how concise and focused this answer is.\n\n"
        f"Question: {query}\nAnswer: {answer}\n\n"
        f"1.0=perfectly concise | 0.5=slightly padded | 0.0=excessively verbose\n"
        f'Return JSON: {{"score": <0.0-1.0>, "reasoning": "<brief>"}}',
        oai,
    )


def _rag_triad_score(cr: float, faith: float, ar: float) -> float:
    """Harmonic mean of the three RAG Triad legs — collapses to 0 if any leg is 0."""
    denom = cr * faith + faith * ar + ar * cr
    return round(3 * cr * faith * ar / denom, 4) if denom else 0.0


# ══════════════════════════════════════════════════════════════════════════
# PART B — MLFLOW GENAI SCORERS
# @scorer functions receive the DataFrame columns as keyword args.
# Column names must match what we pass to mlflow.genai.evaluate(data=...).
#
# Columns we provide:
#   inputs            → the question
#   outputs           → generated answer
#   expected_output   → gold reference answer
#   retrieved_context → list of context strings
# ══════════════════════════════════════════════════════════════════════════

@scorer
def context_relevance_scorer(inputs, outputs, retrieved_context, **kwargs) -> float:
    """
    GenAI scorer: average relevance of each retrieved chunk to the query.
    Maps to: avg_context_relevance in Part A.
    """
    score, _ = _context_relevance(inputs, retrieved_context or [], _oai)
    return score


@scorer
def faithfulness_scorer(inputs, outputs, retrieved_context, **kwargs) -> float:
    """
    GenAI scorer: fraction of answer claims supported by the retrieved context.
    Maps to: avg_faithfulness in Part A.
    """
    score, _ = _faithfulness(outputs, retrieved_context or [], _oai)
    return score


@scorer
def answer_relevance_scorer(inputs, outputs, **kwargs) -> float:
    """
    GenAI scorer: does the answer address the question?
    Maps to: avg_answer_relevance in Part A.
    """
    score, _ = _answer_relevance(inputs, outputs, _oai)
    return score


@scorer
def rag_triad_scorer(inputs, outputs, retrieved_context, **kwargs) -> float:
    """
    GenAI scorer: harmonic mean of CR × Faithfulness × AR.
    Maps to: rag_triad_score in Part A.
    """
    cr, _    = _context_relevance(inputs, retrieved_context or [], _oai)
    fa, _    = _faithfulness(outputs, retrieved_context or [], _oai)
    ar, _    = _answer_relevance(inputs, outputs, _oai)
    return _rag_triad_score(cr, fa, ar)


@scorer
def completeness_scorer(inputs, outputs, expected_output, **kwargs) -> float:
    """
    GenAI scorer: does the answer cover all key points from the reference?
    Maps to: avg_completeness in Part A.
    """
    score, _ = _completeness(outputs, expected_output or "", _oai)
    return score


@scorer
def conciseness_scorer(inputs, outputs, **kwargs) -> float:
    """
    GenAI scorer: is the answer focused and free of padding?
    Maps to: avg_conciseness in Part A.
    """
    score, _ = _conciseness(inputs, outputs, _oai)
    return score


# ══════════════════════════════════════════════════════════════════════════
# PART A — HAND-CODED EVALUATION LOOP
# ══════════════════════════════════════════════════════════════════════════

def _evaluate_example_part_a(example: Dict, oai: openai.OpenAI, index) -> Dict:
    query        = example["question"]
    reference    = example["answer"]
    relevant_ids = [str(d) for d in example.get("relevant_doc_ids", [])]

    matches  = retrieve(query, oai, index)
    ret_ids  = [m.id for m in matches]
    contexts = [m.metadata.get("text", "") for m in matches]
    answer   = generate_answer(query, contexts, oai)

    ret_m          = retrieval_metrics(ret_ids, relevant_ids)
    em             = exact_match(answer, reference)
    tf1            = token_f1(answer, reference)
    cr_s, cr_r     = _context_relevance(query, contexts, oai)
    fa_s, fa_r     = _faithfulness(answer, contexts, oai)
    ar_s, ar_r     = _answer_relevance(query, answer, oai)
    triad          = _rag_triad_score(cr_s, fa_s, ar_s)
    comp_s, comp_r = _completeness(answer, reference, oai)
    conc_s, conc_r = _conciseness(query, answer, oai)

    return {
        "query": query, "reference": reference, "generated_answer": answer,
        "retrieved_ids": ret_ids, "relevant_ids": relevant_ids,
        **{f: ret_m[f] for f in ["precision", "recall", "f1", "ndcg", "hit_rate"]},
        "exact_match": em, "token_f1": tf1,
        "context_relevance": cr_s, "faithfulness": fa_s,
        "answer_relevance": ar_s, "rag_triad": triad,
        "completeness": comp_s, "conciseness": conc_s,
        # reasoning — saved to artifact, not logged as metrics
        "cr_reasoning":            cr_r,
        "faithfulness_reasoning":  fa_r,
        "ar_reasoning":            ar_r,
        "completeness_reasoning":  comp_r,
        "conciseness_reasoning":   conc_r,
    }


def _run_part_a_loop(golden_data: List[Dict], oai: openai.OpenAI, index) -> List[Dict]:
    results = []
    for i, ex in enumerate(golden_data):
        log.info(f"[Part A {i+1}/{len(golden_data)}] {ex['question'][:70]}...")
        try:
            results.append(_evaluate_example_part_a(ex, oai, index))
        except Exception as e:
            log.error(f"  Failed: {e}")
    return results


def _compute_aggregates(results: List[Dict]) -> Dict:
    keys = ["precision", "recall", "f1", "ndcg", "hit_rate",
            "exact_match", "token_f1",
            "context_relevance", "faithfulness", "answer_relevance", "rag_triad",
            "completeness", "conciseness"]
    return {
        f"avg_{k}": round(sum(r[k] for r in results if k in r) / len(results), 4)
        for k in keys
    }


def _save_artifacts(results: List[Dict], run_id: str):
    short = run_id[:8]

    # Clean results (no reasoning fields)
    results_path = f"eval_results_{short}.jsonl"
    with open(results_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps({k: v for k, v in r.items() if "reasoning" not in k}) + "\n")
    mlflow.log_artifact(results_path)

    # Judge reasoning (verbose, for debugging)
    reasoning_path = f"judge_reasoning_{short}.json"
    with open(reasoning_path, "w", encoding="utf-8") as f:
        json.dump([
            {
                "query":           r["query"],
                "generated_answer": r["generated_answer"],
                "reference":       r["reference"],
                "context_relevance": {"score": r["context_relevance"], "reasoning": r.get("cr_reasoning")},
                "faithfulness":      {"score": r["faithfulness"],       "reasoning": r.get("faithfulness_reasoning")},
                "answer_relevance":  {"score": r["answer_relevance"],   "reasoning": r.get("ar_reasoning")},
                "completeness":      {"score": r["completeness"],       "reasoning": r.get("completeness_reasoning")},
                "conciseness":       {"score": r["conciseness"],        "reasoning": r.get("conciseness_reasoning")},
            }
            for r in results
        ], f, indent=2, ensure_ascii=False)
    mlflow.log_artifact(reasoning_path)

    log.info(f"  Artifacts: {results_path}, {reasoning_path}")


def run_part_a(golden_data: List[Dict], oai: openai.OpenAI, index) -> Dict:
    """
    Part A — Hand-coded metrics tracked to MLflow Model Training mode.
    Visible in: Model Training tab → RAG-HotpotQA-Evaluation experiment.
    """
    experiment_id = setup_mlflow(EXPERIMENT_PART_A, "model_training")

    with mlflow.start_run(
        run_name=f"part_a_{datetime.now():%Y%m%d_%H%M%S}",
        tags={"part": "A", "mode": "handcoded", "dataset": "hotpotqa"},
    ) as run:
        run_id = run.info.run_id
        log.info(f"[Part A] Run ID : {run_id}")
        log.info(f"[Part A] UI     : {MLFLOW_URI}/#/experiments/{experiment_id}/runs/{run_id}")

        # 1. Log params
        mlflow.log_params({
            "embedding_model":  EMBEDDING_MODEL,
            "generator_model":  GENERATOR_MODEL,
            "judge_model":      JUDGE_MODEL,
            "top_k":            TOP_K,
            "chunk_size":       CHUNK_SIZE,
            "golden_n":         len(golden_data),
            "index_name":       INDEX_NAME,
            "namespace":        NAMESPACE,
        })

        # 2. Run evaluation
        results    = _run_part_a_loop(golden_data, oai, index)
        aggregated = _compute_aggregates(results)

        # 3. Log aggregate metrics
        mlflow.log_metrics(aggregated)

        # 4. Log per-example step metrics (enables time-series chart in UI)
        step_keys = ["precision", "recall", "ndcg", "hit_rate",
                     "faithfulness", "context_relevance", "answer_relevance", "rag_triad"]
        for step, r in enumerate(results):
            mlflow.log_metrics({k: r[k] for k in step_keys if k in r}, step=step)

        # 5. Save artifacts
        _save_artifacts(results, run_id)

        # Summary
        log.info("\n" + "=" * 62)
        log.info(f"  Part A Results — Model Training Mode")
        log.info("=" * 62)
        for k, v in aggregated.items():
            log.info(f"  {k:<35} {v:>8.4f}")
        log.info("=" * 62)
        log.info(f"  UI → {MLFLOW_URI}  (Model Training tab)")

        return aggregated


# ══════════════════════════════════════════════════════════════════════════
# PART B — MLFLOW GENAI EVALUATION
# ══════════════════════════════════════════════════════════════════════════

def _build_eval_dataframe(golden_data: List[Dict], oai: openai.OpenAI, index) -> pd.DataFrame:
    """
    Run the RAG pipeline for every example and build the DataFrame
    that mlflow.genai.evaluate() expects.

    Columns:
      inputs            — question
      outputs           — generated answer  (produced here)
      expected_output   — gold reference answer
      retrieved_context — list of context strings (produced here)
    """
    rows = []
    for i, ex in enumerate(golden_data):
        log.info(f"[Part B prep {i+1}/{len(golden_data)}] {ex['question'][:70]}...")
        try:
            result = rag_pipeline(ex["question"], oai, index)
            rows.append({
                "inputs":            ex["question"],
                "outputs":           result["answer"],
                "expected_output":   ex["answer"],
                "retrieved_context": result["contexts"],
            })
        except Exception as e:
            log.error(f"  Failed on example {i+1}: {e}")

    return pd.DataFrame(rows)


def run_part_b(golden_data: List[Dict], oai: openai.OpenAI, index) -> None:
    """
    Part B — mlflow.genai.evaluate() with custom scorers tracked to GenAI mode.
    Visible in: GenAI tab → RAG-HotpotQA-GenAI-Eval experiment.

    Scorers used:
      Custom  — context_relevance, faithfulness, answer_relevance,
                rag_triad, completeness, conciseness
      Built-in — mlflow.genai.scorers.relevance_to_query()
                 mlflow.genai.scorers.safety()
    """
    experiment_id = setup_mlflow(EXPERIMENT_PART_B, "genai")

    with mlflow.start_run(
        run_name=f"part_b_{datetime.now():%Y%m%d_%H%M%S}",
        tags={"part": "B", "mode": "mlflow_genai", "dataset": "hotpotqa"},
    ) as run:
        run_id = run.info.run_id
        log.info(f"[Part B] Run ID : {run_id}")
        log.info(f"[Part B] UI     : {MLFLOW_URI}/#/experiments/{experiment_id}/runs/{run_id}")

        # Log params so the run is fully reproducible
        mlflow.log_params({
            "embedding_model":  EMBEDDING_MODEL,
            "generator_model":  GENERATOR_MODEL,
            "judge_model":      JUDGE_MODEL,
            "top_k":            TOP_K,
            "chunk_size":       CHUNK_SIZE,
            "golden_n":         len(golden_data),
            "index_name":       INDEX_NAME,
        })

        # Build eval DataFrame (also captures traces via @mlflow.trace)
        log.info("[Part B] Building eval DataFrame (RAG pipeline + tracing)...")
        eval_df = _build_eval_dataframe(golden_data, oai, index)
        log.info(f"[Part B] DataFrame ready: {len(eval_df)} rows")

        # Run mlflow.genai.evaluate() with all scorers
        log.info("[Part B] Running mlflow.genai.evaluate()...")
        results = mlflow.genai.evaluate(
            data=eval_df,
            scorers=[
                # ── Custom scorers (our full RAG Triad + custom judges) ─────
                context_relevance_scorer,
                faithfulness_scorer,
                answer_relevance_scorer,
                rag_triad_scorer,
                completeness_scorer,
                conciseness_scorer,
                # ── Built-in MLflow 3 GenAI scorers ───────────────────────
                mlflow.genai.scorers.relevance_to_query(),
                mlflow.genai.scorers.safety(),
            ],
        )

        # Print aggregate results
        log.info("\n" + "=" * 62)
        log.info(f"  Part B Results — GenAI Mode")
        log.info("=" * 62)
        if hasattr(results, "metrics") and results.metrics:
            for k, v in results.metrics.items():
                log.info(f"  {k:<40} {v:>8.4f}")
        log.info("=" * 62)
        log.info(f"  UI → {MLFLOW_URI}  (GenAI tab)")

        return results


# ══════════════════════════════════════════════════════════════════════════
# MODEL REGISTRATION (call manually after a good Part A run)
# ══════════════════════════════════════════════════════════════════════════

def register_best_model(run_id: str, description: str = ""):
    """
    Register a Part A run as a versioned model in the Model Registry.

    Example:
        register_best_model(
            run_id="abc123de...",
            description="chunk=400, K=5, rag_triad=0.823, faithfulness=0.833"
        )
    """
    mlflow.set_tracking_uri(MLFLOW_URI)
    client = MlflowClient()

    version = mlflow.register_model(
        model_uri=f"runs:/{run_id}/eval_results",
        name=MODEL_NAME,
    )
    log.info(f"Registered '{MODEL_NAME}' version {version.version}")

    if description:
        client.update_model_version(
            name=MODEL_NAME, version=version.version, description=description
        )

    client.transition_model_version_stage(
        name=MODEL_NAME, version=version.version,
        stage="Staging", archive_existing_versions=False,
    )
    log.info("Stage: None → Staging  |  Promote to Production in the UI when ready")
    return version


# ══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(description="RAG Evaluation — dual MLflow mode")
    parser.add_argument(
        "--mode",
        choices=["part_a", "part_b", "both"],
        default="both",
        help=(
            "part_a = hand-coded metrics → Model Training tab | "
            "part_b = mlflow.genai.evaluate() → GenAI tab | "
            "both = run both (default)"
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not GOLDEN_PATH.exists():
        raise FileNotFoundError(f"Not found: {GOLDEN_PATH}. Run 1_prepare_dataset.py first.")

    oai, pc     = build_clients()
    index       = pc.Index(INDEX_NAME)
    golden_data = load_golden(GOLDEN_PATH)
    log.info(f"Loaded {len(golden_data)} examples  |  mode={args.mode}")

    # Inject clients into module-level refs used by @scorer functions
    global _oai, _index
    _oai   = oai
    _index = index

    if args.mode in ("part_a", "both"):
        log.info("\n── PART A: Hand-coded metrics → Model Training mode ──────────────")
        run_part_a(golden_data, oai, index)

    if args.mode in ("part_b", "both"):
        log.info("\n── PART B: mlflow.genai.evaluate() → GenAI mode ──────────────────")
        run_part_b(golden_data, oai, index)

    log.info(f"\nDone. Open MLflow UI → {MLFLOW_URI}")
    log.info("  GenAI tab         → Part B traces + scorer results")
    log.info("  Model Training tab → Part A aggregate metrics + artifacts")


if __name__ == "__main__":
    main()