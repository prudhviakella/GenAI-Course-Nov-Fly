"""
enrich_pipeline.py
------------------
Single-module chunk enrichment pipeline.

This script acts as a 'data refinery'. It takes raw text chunks (usually from a PDF or document)
and adds layers of intelligence: identifying people/orgs, hiding sensitive data (PII),
and pulling out financial signals like revenue or fiscal years.
"""

import re
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional

# Check for AWS SDK (boto3). If missing, we can still run regex patterns,
# but AWS Comprehend features will be disabled.
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# ---------------------------------------------------------------------------
# Logging Configuration: Outputs to console with timestamps and severity levels
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global Stats: Tracks performance and volume for the final summary report
# ---------------------------------------------------------------------------
STATS: Dict[str, int] = {
    'chunks_processed': 0,
    'comprehend_calls':  0,
    'comprehend_errors': 0,
    'entities_extracted': 0,
    'key_phrases_extracted': 0,
    'patterns_matched': 0,
    'pii_replacements': 0,
}

# ---------------------------------------------------------------------------
# Regex patterns: Compiled once at startup for high performance
# ---------------------------------------------------------------------------
PATTERNS = {
    # Matches $100, $5.5M, $10 Billion etc.
    'monetary_values':   re.compile(r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*([BMK])?'),
    # Matches percentages like 15% or 99.9%
    'percentages':       re.compile(r'(\d+(?:\.\d+)?)\s*%'),
    # Matches Q1, Q4 2023, Q2 FY24
    'quarters':          re.compile(r'Q[1-4]\s*(?:20\d{2}|FY\d{2}|\d{2})?'),
    # Matches 2024, FY2025, CY2022
    'years':             re.compile(r'(?:FY|CY)?\s*20\d{2}'),
    # Matches specific industry standard vocabulary
    'financial_metrics': re.compile(
        r'\b(EBITDA|EPS|ROE|ROI|P/E|revenue|profit|margin)\b', re.IGNORECASE
    ),
}

# Filtering constants to remove "Garbage In, Garbage Out" from key phrases
_NOISE_PHRASES = {
    'see above', 'see below', 'as follows', 'as shown', 'the following',
    'click here', 'this report', 'this analysis', 'this chart', 'this table',
    'exhibit', 'figure', 'page', 'slide', 'x-axis', 'y-axis',
}
_NOISE_SUBSTRINGS = ('**', '##', '![', '](', 'source:', '|')


# ===========================================================================
# AWS client initialization
# ===========================================================================

def init_comprehend_client(region: str = 'us-east-1') -> Optional[object]:
    """Sets up the AWS connection. Returns None if boto3 is missing or credentials fail."""
    if not BOTO3_AVAILABLE:
        logger.warning("boto3 not installed — run: pip install boto3")
        return None
    try:
        client = boto3.client('comprehend', region_name=region)
        logger.info(f"Comprehend client ready (region: {region})")
        return client
    except Exception as exc:
        logger.error(f"Failed to create Comprehend client: {exc}")
        return None


# ===========================================================================
# PII redaction: Privacy Layer
# ===========================================================================

def redact_pii(text: str, client) -> str:
    """
    Identifies and masks PII (Emails, SSNs, Names) with placeholders like [REDACTED_NAME].
    """
    if not client or not text.strip():
        return text

    # AWS Comprehend has a 5KB limit per UTF-8 string; we truncate to stay safe
    safe_text = text[:4500]

    # Optimization: 'contains_pii_entities' is cheaper/faster than full detection.
    # We only call the expensive detection if this returns true.
    try:
        check = client.contains_pii_entities(Text=safe_text, LanguageCode='en')
        STATS['comprehend_calls'] += 1
    except Exception as exc:
        logger.error(f"contains_pii_entities failed: {exc}")
        STATS['comprehend_errors'] += 1
        return text

    if not check.get('Labels'):
        return text  # Clean text, no action needed

    # Step 2: Get exact character coordinates for the PII found
    try:
        detail = client.detect_pii_entities(Text=safe_text, LanguageCode='en')
        STATS['comprehend_calls'] += 1
    except Exception as exc:
        logger.error(f"detect_pii_entities failed: {exc}")
        STATS['comprehend_errors'] += 1
        return text

    entities = detail.get('Entities', [])
    if not entities:
        return text

    # Step 3: Replace text from back-to-front.
    # If we started at the front, character offsets for the end of the string would break.
    redacted = safe_text
    for entity in sorted(entities, key=lambda e: e['BeginOffset'], reverse=True):
        start    = entity['BeginOffset']
        end      = entity['EndOffset']
        pii_type = entity['Type']
        print(redacted)
        print("Redacted text",pii_type, redacted[start:end+1])
        redacted = redacted[:start] + f'[REDACTED_{pii_type}]' + redacted[end:]
        STATS['pii_replacements'] += 1

    logger.info(f"PII: replaced {len(entities)} span(s) in chunk")
    return redacted


# ===========================================================================
# Entity extraction: NLP Layer
# ===========================================================================

def extract_entities(text: str, client,
                     confidence: float = 0.7,
                     max_retries: int = 3,
                     retry_delay: float = 1.0) -> Dict[str, List[Dict]]:
    """
    Detects Names, Organizations, Locations, etc.
    Includes Exponential Backoff to handle AWS rate limits (ThrottlingException).
    """
    if not client or len(text) < 3:
        return {}

    safe_text = text[:4500]
    response  = None

    for attempt in range(max_retries):
        try:
            response = client.detect_entities(Text=safe_text, LanguageCode='en')
            STATS['comprehend_calls'] += 1
            break
        except ClientError as exc:
            code = exc.response['Error']['Code']
            # If AWS says "slow down", we wait and try again
            if code == 'ThrottlingException' and attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
            else:
                logger.error(f"detect_entities failed [{code}]: {exc}")
                STATS['comprehend_errors'] += 1
                return {}

    if not response:
        return {}

    # Group entities by type (e.g., all 'ORGANIZATION' together)
    by_type: Dict[str, list] = defaultdict(list)
    for ent in response.get('Entities', []):
        if ent['Score'] >= confidence:
            by_type[ent['Type']].append({'text': ent['Text'], 'score': round(ent['Score'], 4)})
            STATS['entities_extracted'] += 1

    logger.info(f"Entities extracted: {sum(len(v) for v in by_type.values())}")
    return dict(by_type)


# ===========================================================================
# Key-phrase extraction: Thematic Layer
# ===========================================================================

def _is_quality_phrase(phrase: str) -> bool:
    """Helper to discard low-value phrases like 'click here' or markdown tags."""
    p = phrase.lower().strip()
    if len(p) < 3:
        return False
    if any(sub in p for sub in _NOISE_SUBSTRINGS):
        return False
    if p in _NOISE_PHRASES or any(p.startswith(n + ' ') for n in _NOISE_PHRASES):
        return False
    if p.replace(',', '').replace('.', '').isdigit():
        return False
    return True


def extract_key_phrases(text: str, client,
                        confidence: float = 0.7,
                        max_retries: int = 3,
                        retry_delay: float = 1.0) -> List[str]:
    """Extracts major noun phrases to summarize what the chunk is about."""
    if not client or len(text) < 3:
        return []

    safe_text = text[:4500]
    response  = None

    for attempt in range(max_retries):
        try:
            response = client.detect_key_phrases(Text=safe_text, LanguageCode='en')
            STATS['comprehend_calls'] += 1
            break
        except ClientError as exc:
            code = exc.response['Error']['Code']
            if code == 'ThrottlingException' and attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
            else:
                logger.error(f"detect_key_phrases failed [{code}]: {exc}")
                STATS['comprehend_errors'] += 1
                return []

    if not response:
        return []

    # Filter and deduplicate phrases
    phrases = [
        kp['Text'] for kp in response.get('KeyPhrases', [])
        if kp['Score'] >= confidence and _is_quality_phrase(kp['Text'])
    ]
    STATS['key_phrases_extracted'] += len(phrases)
    logger.info(f"Key phrases extracted: {len(phrases)}")
    return phrases


# ===========================================================================
# Regex pattern extraction: Structural Layer
# ===========================================================================

def extract_patterns(text: str) -> Dict[str, List[str]]:
    """Uses local CPU regex. This is 'free' compared to AWS API calls."""
    monetary = PATTERNS['monetary_values'].findall(text)
    results = {
        'monetary_values':   [f"${amt}{sfx}" if sfx else f"${amt}" for amt, sfx in monetary],
        'percentages':       [f"{p}%" for p in PATTERNS['percentages'].findall(text)],
        'quarters':          PATTERNS['quarters'].findall(text),
        'years':             PATTERNS['years'].findall(text),
        'financial_metrics': list(set(PATTERNS['financial_metrics'].findall(text))),
    }
    total = sum(len(v) for v in results.values())
    STATS['patterns_matched'] += total
    return results


# ===========================================================================
# Enrichment Logic
# ===========================================================================

def enrich_chunk(chunk: Dict, client,
                 enable_comprehend: bool = True,
                 enable_patterns: bool = True,
                 enable_key_phrases: bool = False,
                 enable_pii_redaction: bool = True,
                 confidence: float = 0.7,
                 max_retries: int = 3,
                 retry_delay: float = 1.0) -> Dict:
    """
    Coordinates all enrichment steps for a single piece of text.
    Updates the chunk's 'metadata' dictionary with the findings.
    """
    # Look for text in common JSON keys used by chunkers
    text = chunk.get('content') or chunk.get('content_only') or chunk.get('text', '')
    if not text.strip():
        logger.warning(f"Skipping empty chunk (id={chunk.get('id', '?')})")
        return chunk

    if 'metadata' not in chunk:
        chunk['metadata'] = {}

    use_aws = enable_comprehend and client is not None

    # Redact PII first so we don't send real names/emails to other NLP steps
    if use_aws and enable_pii_redaction:
        sanitised = redact_pii(text, client)
        chunk['metadata']['pii_redacted'] = sanitised != text
        if sanitised != text:
            chunk['content_sanitised'] = sanitised
            text = sanitised  # Work with the clean version moving forward

    # Entity detection
    chunk['metadata']['entities'] = (
        extract_entities(text, client, confidence, max_retries, retry_delay)
        if use_aws else {}
    )

    # Key phrase detection
    if enable_key_phrases and use_aws:
        chunk['metadata']['key_phrases'] = extract_key_phrases(
            text, client, confidence, max_retries, retry_delay
        )

    # Fast local regex matches
    if enable_patterns:
        chunk['metadata'].update(extract_patterns(text))

    STATS['chunks_processed'] += 1
    return chunk


def enrich_chunks(chunks: List[Dict], **kwargs) -> List[Dict]:
    """Iterates through a list of chunks, providing progress logging."""
    total = len(chunks)
    logger.info(f"Enriching {total} chunks...")
    results = []
    log_every = kwargs.pop('log_every', 100)
    # --- ADD THESE TWO LINES ---
    log_every = kwargs.pop('log_every', 100)
    kwargs.pop('region', None)  # Remove region so it's not passed to enrich_chunk
    for i, chunk in enumerate(chunks, 1):
        try:
            results.append(enrich_chunk(chunk, **kwargs))
        except Exception as exc:
            # Failure on one chunk shouldn't crash the whole pipeline
            logger.error(f"Chunk {i} failed: {exc} — keeping original")
            results.append(chunk)

        if i % log_every == 0:
            logger.info(f"Progress: {i}/{total} ({i/total*100:.0f}%)")

    return results


# ===========================================================================
# I/O & Execution
# ===========================================================================

def load_chunks(path: str) -> List[Dict]:
    """Reads the JSON file and validates the structure."""
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)

    # Allow flexibilty in the JSON root key name
    chunks = data.get('chunks') or data.get('semantic_chunks')
    if chunks is None:
        raise ValueError(f"No 'chunks' or 'semantic_chunks' key found in {path}.")

    logger.info(f"Loaded {len(chunks)} chunks from {path}")
    return chunks


def save_output(chunks: List[Dict], path: str, config: Dict) -> None:
    """Saves the final results with a metadata wrapper for auditability."""
    output = {
        'metadata': {
            'enriched_at':      datetime.now().isoformat(),
            'total_chunks':     len(chunks),
            'enricher_version': '3.0.0',
            'config':           config,
        },
        'chunks':     chunks,
        'statistics': STATS.copy(),
    }
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)

    size_mb = Path(path).stat().st_size / (1024 * 1024)
    logger.info(f"Saved → {path}  ({size_mb:.2f} MB)")


def print_stats() -> None:
    """Prints a pretty summary of what was accomplished and estimated costs."""
    sep = '-' * 40
    logger.info(sep)
    logger.info("Enrichment summary")
    logger.info(sep)
    for k, v in STATS.items():
        logger.info(f"  {k:<26} {v:,}")

    # Very rough estimate based on AWS pricing per 100 units
    if STATS['comprehend_calls']:
        cost = (STATS['chunks_processed'] * 500 * 0.0001 / 100) * 2
        logger.info(f"  {'estimated_aws_cost':<26} ${cost:.4f}")
    logger.info(sep)


def run_pipeline(input_file: str, **kwargs) -> None:
    """The main execution controller."""
    # Determine output filename if none provided (e.g., data.json -> data_enriched.json)
    output_file = kwargs.pop('output_file', None)
    if not output_file:
        p = Path(input_file)
        output_file = str(p.parent / f"{p.stem}_enriched.json")

    chunks = load_chunks(input_file)

    # Initialize AWS if the user didn't disable it
    client = None
    if kwargs.get('enable_comprehend'):
        client = init_comprehend_client(kwargs.get('region', 'us-east-1'))

    if kwargs.get('enable_comprehend') and client is None:
        logger.warning("Comprehend unavailable — falling back to patterns only")

    # Run the heavy lifting
    enriched = enrich_chunks(chunks, client=client, **kwargs)

    # Cleanup and Save
    save_output(enriched, output_file, kwargs)
    print_stats()


def main() -> None:
    """CLI Parser: Maps command line flags to pipeline arguments."""
    parser = argparse.ArgumentParser(
        description='Enrich semantic chunks with entities, PII redaction, and financial patterns.',
    )
    parser.add_argument('input_file',          help='Input JSON file')
    parser.add_argument('output_file', nargs='?', default=None, help='Output JSON file')
    parser.add_argument('--region',            default='us-east-1')
    parser.add_argument('--no-comprehend',     action='store_true', help='Patterns only (no AWS)')
    parser.add_argument('--no-patterns',       action='store_true', help='Skip regex patterns')
    parser.add_argument('--no-pii',            action='store_true', help='Skip PII redaction')
    parser.add_argument('--enable-key-phrases',action='store_true', help='Extract key phrases')
    parser.add_argument('--confidence',        type=float, default=0.7,
                        help='Confidence threshold 0.0–1.0 (default: 0.7)')
    args = parser.parse_args()

    run_pipeline(
        input_file=args.input_file,
        output_file=args.output_file,
        region=args.region,
        enable_comprehend=not args.no_comprehend,
        enable_patterns=not args.no_patterns,
        enable_key_phrases=args.enable_key_phrases,
        enable_pii_redaction=not args.no_pii,
        confidence=args.confidence,
    )


if __name__ == '__main__':
    main()