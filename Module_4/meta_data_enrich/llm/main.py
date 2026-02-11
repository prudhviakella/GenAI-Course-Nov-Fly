"""
enrich_pipeline_openai.py
-------------------------
OpenAI-powered chunk enrichment pipeline.
"""

import re
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ---------------------------------------------------------------------------
# Logging & Stats
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

STATS = {
    'chunks_processed': 0,
    'openai_calls': 0,
    'openai_errors': 0,
    'entities_extracted': 0,
    'pii_replacements': 0,
}

# Local Regex remains for "Free" extraction
PATTERNS = {
    'monetary_values': re.compile(r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*([BMK])?'),
    'years': re.compile(r'(?:FY|CY)?\s*20\d{2}'),
}


# ===========================================================================
# OpenAI Initialization
# ===========================================================================

def init_openai_client(api_key: Optional[str] = None) -> Optional[OpenAI]:
    if not OPENAI_AVAILABLE:
        logger.error("OpenAI library not installed: pip install openai")
        return None
    try:
        # Defaults to OPENAI_API_KEY env var if api_key is None
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        logger.error(f"Failed to init OpenAI: {e}")
        return None


# ===========================================================================
# The "Intelligence" Call
# ===========================================================================

def analyze_chunk_with_openai(text: str, client: OpenAI, model: str = "gpt-4o-mini") -> Dict:
    """
    Uses OpenAI to perform Redaction, Entities, and Key Phrases in one shot.
    """
    prompt = f"""
    Act as a privacy expert and data analyst. Your goal is to identify PII while preserving the 
    analytical value of the document.

    Analyze the following text and return a JSON object with:

    1. "redacted_text": 
       - Redact ONLY highly sensitive individual identifiers: Personal Names, Personal Emails, 
         Personal Phone Numbers, and specific Home Addresses.
       - Use the format [REDACTED_TYPE].
       - **DO NOT REDACT**:
         * Dates like "2025", "Q1", "January", or fiscal years.
         * Geographies like "USA", "Japan", or "Europe".
         * Company names (e.g., "Morgan Stanley", "Apple").
         * Generic professional roles (e.g., "Analyst", "Manager").
       - **CONTEXT RULE**: If a date refers to a person's Birthday, redact it. If it refers to 
         a report date or fiscal period, KEEP IT.

    2. "entities": 
       - Extract and categorize: 
         - PERSON (Individual names)
         - ORGANIZATION (Companies/Institutions)
         - DATE (Temporal references like "FY25" or "2024-11-20")
         - GPE (Countries, Cities, States)
         - MONEY (Financial amounts like "$5.5M")

    3. "key_phrases": 
       - A list of the top 5 noun phrases that summarize the core "Financial or Business signal" 
         in this text.

    Text:
    {text}
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        STATS['openai_calls'] += 1
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        STATS['openai_errors'] += 1
        return {}


# ===========================================================================
# Processing Logic
# ===========================================================================

def enrich_chunk(chunk: Dict, client: OpenAI, **kwargs) -> Dict:
    text = chunk.get('content') or chunk.get('text', '')
    if not text.strip():
        return chunk

    if 'metadata' not in chunk:
        chunk['metadata'] = {}

    # 1. AI Analysis
    analysis = analyze_chunk_with_openai(text, client, model=kwargs.get('model', 'gpt-4o-mini'))

    if analysis:
        # Redaction
        redacted = analysis.get('redacted_text', text)
        if redacted != text:
            chunk['content_sanitised'] = redacted
            chunk['metadata']['pii_redacted'] = True
            STATS['pii_replacements'] += 1

        # Entities
        chunk['metadata']['entities'] = analysis.get('entities', {})
        STATS['entities_extracted'] += sum(len(v) for v in analysis.get('entities', {}).values())

        # Phrases
        chunk['metadata']['key_phrases'] = analysis.get('key_phrases', [])

    # 2. Local Patterns (Fallback/Structured)
    monetary = PATTERNS['monetary_values'].findall(text)
    chunk['metadata']['monetary_values'] = [f"${amt}{sfx}" if sfx else f"${amt}" for amt, sfx in monetary]

    STATS['chunks_processed'] += 1
    return chunk


def run_pipeline(input_file: str, api_key: Optional[str], **kwargs):
    client = init_openai_client(api_key)
    if not client: return

    with open(input_file, 'r') as f:
        data = json.load(f)

    chunks = data.get('chunks', [])
    logger.info(f"Processing {len(chunks)} chunks via OpenAI...")

    enriched_chunks = [enrich_chunk(c, client, **kwargs) for c in chunks]

    # Output Logic
    output_path = Path(input_file).stem + "_enriched_openai.json"
    with open(output_path, 'w') as f:
        json.dump({'chunks': enriched_chunks, 'stats': STATS}, f, indent=2)

    logger.info(f"Done. Saved to {output_path}")
    print(json.dumps(STATS, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('--api_key', default=None)
    parser.add_argument('--model', default='gpt-4o-mini')
    args = parser.parse_args()

    run_pipeline(args.input_file, args.api_key, model=args.model)