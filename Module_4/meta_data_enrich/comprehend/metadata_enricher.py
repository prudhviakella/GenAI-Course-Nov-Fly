"""
================================================================================
METADATA ENRICHER - Functional Version (No Classes)
================================================================================

UPDATED FOR:
============
- Pure functional approach (no classes)
- Works with both "content" (new) and "content_only" (legacy) fields
- Handles nested metadata structure
- Compatible with comprehensive_chunker.py output

This is the core enrichment engine that:
1. Calls AWS Comprehend for entities and key phrases
2. Extracts custom patterns using regex
3. Merges metadata into chunk structure

Author: Prudhvi
Version: 2.0.0 (Functional)
"""

import re
import time
import logging
from typing import Dict, List, Optional
from collections import defaultdict

# AWS SDK for Python
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


# ============================================================================
# LOGGING SETUP
# ============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

# Default configuration values
DEFAULT_CONFIG = {
    'region_name': 'us-east-1',
    'enable_comprehend': True,
    'enable_patterns': True,
    'confidence_threshold': 0.7,
    'max_retries': 3,
    'retry_delay': 1.0
}

# Global statistics tracking
STATS = {
    'chunks_processed': 0,
    'comprehend_calls': 0,
    'comprehend_errors': 0,
    'entities_extracted': 0,
    'key_phrases_extracted': 0,
    'patterns_matched': 0
}


# ============================================================================
# AWS COMPREHEND CLIENT INITIALIZATION
# ============================================================================

def init_comprehend_client(region_name: str = 'us-east-1') -> Optional[object]:
    """
    Initialize AWS Comprehend client

    WHAT THIS DOES:
    ---------------
    Creates a connection to AWS Comprehend service for AI-powered
    entity and key phrase extraction.

    Parameters
    ----------
    region_name : str
        AWS region (default: us-east-1)

    Returns
    -------
    boto3.client or None
        Comprehend client if successful, None if failed

    Example
    -------
    >>> client = init_comprehend_client('us-east-1')
    >>> if client:
    ...     print("AWS Comprehend ready!")
    """
    if not BOTO3_AVAILABLE:
        logger.warning(
            "boto3 not installed. Install with: pip install boto3"
        )
        return None

    try:
        client = boto3.client('comprehend', region_name=region_name)
        logger.info(f"✓ AWS Comprehend initialized (region: {region_name})")
        return client

    except Exception as e:
        logger.error(f"✗ Failed to initialize AWS Comprehend: {e}")
        return None


# ============================================================================
# REGEX PATTERN INITIALIZATION
# ============================================================================

def init_patterns() -> Dict[str, re.Pattern]:
    """
    Initialize regex patterns for custom extraction

    PATTERNS EXPLAINED:
    -------------------

    1. Monetary Values: $15.4B, $2.3M, $500K
       Pattern: \$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*([BMK])?

    2. Percentages: 25%, 15.5%
       Pattern: (\d+(?:\.\d+)?)\s*%

    3. Quarters: Q3 2024, Q4, Q1 FY24
       Pattern: Q[1-4]\s*(?:20\d{2}|FY\d{2}|\d{2})?

    4. Years: 2024, FY2024, CY2023
       Pattern: (?:FY|CY)?\s*20\d{2}

    5. Financial Metrics: EBITDA, EPS, ROE, revenue
       Pattern: \b(EBITDA|EPS|ROE|...)\b

    Returns
    -------
    Dict[str, re.Pattern]
        Dictionary of compiled regex patterns
    """
    return {
        'monetary_values': re.compile(
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*([BMK])?'
        ),
        'percentages': re.compile(
            r'(\d+(?:\.\d+)?)\s*%'
        ),
        'quarters': re.compile(
            r'Q[1-4]\s*(?:20\d{2}|FY\d{2}|\d{2})?'
        ),
        'years': re.compile(
            r'(?:FY|CY)?\s*20\d{2}'
        ),
        'financial_metrics': re.compile(
            r'\b(EBITDA|EPS|ROE|ROI|P/E|revenue|profit|margin)\b',
            re.IGNORECASE
        )
    }


# Initialize patterns globally
PATTERNS = init_patterns()


# ============================================================================
# TEXT EXTRACTION FUNCTION
# ============================================================================

def get_text_from_chunk(chunk: Dict) -> str:
    """
    Extract text from chunk (handles both formats)

    COMPATIBILITY LAYER:
    --------------------
    This function provides backward compatibility with multiple chunk formats:

    1. New format (comprehensive_chunker.py):
       {'content': '...', 'metadata': {...}}

    2. Legacy format (old chunker):
       {'content_only': '...', 'text': '...', 'metadata': {...}}

    3. Fallback format:
       {'text': '...'}

    Tries in priority order:
    1. chunk['content'] (new format) - highest priority
    2. chunk['content_only'] (legacy format)
    3. chunk['text'] (fallback)
    4. Empty string (if nothing found)

    Parameters
    ----------
    chunk : Dict
        Chunk dictionary with text content

    Returns
    -------
    str
        Extracted text content, or empty string if not found

    Example
    -------
    >>> chunk = {'content': 'Hello world', 'metadata': {}}
    >>> text = get_text_from_chunk(chunk)
    >>> print(text)
    'Hello world'
    """
    # ───────────────────────────────────────────────────────────────
    # PRIORITY 1: Try new format (comprehensive_chunker.py)
    # ───────────────────────────────────────────────────────────────
    if 'content' in chunk:
        logger.debug("Extracted text from 'content' field (new format)")
        return chunk['content']

    # ───────────────────────────────────────────────────────────────
    # PRIORITY 2: Try legacy format (old chunker)
    # ───────────────────────────────────────────────────────────────
    if 'content_only' in chunk:
        logger.debug("Extracted text from 'content_only' field (legacy format)")
        return chunk['content_only']

    # ───────────────────────────────────────────────────────────────
    # PRIORITY 3: Fallback to 'text' field
    # ───────────────────────────────────────────────────────────────
    if 'text' in chunk:
        logger.debug("Extracted text from 'text' field (fallback)")
        return chunk['text']

    # ───────────────────────────────────────────────────────────────
    # PRIORITY 4: No text found - return empty string
    # ───────────────────────────────────────────────────────────────
    logger.warning(
        f"No text field found in chunk. Available fields: {list(chunk.keys())}"
    )
    return ''


# ============================================================================
# AWS COMPREHEND - ENTITY EXTRACTION
# ============================================================================

def extract_entities(
    text: str,
    comprehend_client: Optional[object],
    confidence_threshold: float = 0.7,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Dict[str, List[Dict]]:
    """
    Extract named entities using AWS Comprehend

    WHAT ARE ENTITIES?
    ------------------
    Named entities are real-world objects mentioned in text:
    - PERSON: "James Gorman", "John Smith"
    - ORGANIZATION: "Morgan Stanley", "Apple Inc."
    - LOCATION: "New York", "California"
    - DATE: "Q3 2024", "January 2025"
    - QUANTITY: "$15.4B", "25%"

    HOW IT WORKS:
    -------------
    1. Validate input text (length, non-empty)
    2. Truncate if needed (AWS limit: 5000 bytes)
    3. Call AWS Comprehend API (with retry logic)
    4. Filter by confidence threshold
    5. Group entities by type
    6. Return organized dictionary

    Parameters
    ----------
    text : str
        Text to analyze
    comprehend_client : boto3.client or None
        AWS Comprehend client
    confidence_threshold : float
        Minimum confidence (0.0-1.0)
    max_retries : int
        Maximum retry attempts
    retry_delay : float
        Base delay for exponential backoff

    Returns
    -------
    Dict[str, List[Dict]]
        Entities grouped by type:
        {
          'PERSON': [{'text': 'John', 'score': 0.99}],
          'ORGANIZATION': [{'text': 'Morgan Stanley', 'score': 0.98}]
        }
    """
    # ───────────────────────────────────────────────────────────────
    # STEP 1: Validate prerequisites
    # ───────────────────────────────────────────────────────────────
    if not comprehend_client:
        logger.debug("AWS Comprehend disabled, skipping entity extraction")
        return {}

    if not text or len(text) < 3:
        logger.debug(f"Text too short for entity extraction: {len(text)} chars")
        return {}

    # ───────────────────────────────────────────────────────────────
    # STEP 2: Truncate text if needed
    # ───────────────────────────────────────────────────────────────
    original_length = len(text)
    text = text[:4500]

    if original_length > 4500:
        logger.warning(
            f"Text truncated from {original_length} to 4500 chars for AWS limits"
        )

    # ───────────────────────────────────────────────────────────────
    # STEP 3: Call AWS Comprehend with retry logic
    # ───────────────────────────────────────────────────────────────
    try:
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Calling AWS Comprehend detect_entities "
                    f"(attempt {attempt + 1}/{max_retries})"
                )

                response = comprehend_client.detect_entities(
                    Text=text,
                    LanguageCode='en'
                )

                STATS['comprehend_calls'] += 1

                logger.debug(
                    f"✓ AWS Comprehend call successful. "
                    f"Found {len(response.get('Entities', []))} raw entities"
                )

                break

            except ClientError as e:
                if e.response['Error']['Code'] == 'ThrottlingException':
                    if attempt < max_retries - 1:
                        delay = retry_delay * (2 ** attempt)
                        logger.warning(
                            f"⚠ AWS throttled request. Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"✗ AWS throttling persisted after {max_retries} attempts"
                        )
                        raise
                else:
                    logger.error(f"✗ AWS Comprehend error: {e.response['Error']['Code']}")
                    raise

        # ───────────────────────────────────────────────────────────
        # STEP 4: Process and filter entities
        # ───────────────────────────────────────────────────────────
        entities_by_type = defaultdict(list)
        total_entities = len(response.get('Entities', []))
        filtered_count = 0

        for entity in response.get('Entities', []):
            if entity['Score'] >= confidence_threshold:
                entity_type = entity['Type']
                entities_by_type[entity_type].append({
                    'text': entity['Text'],
                    'score': entity['Score']
                })
                STATS['entities_extracted'] += 1

                logger.debug(
                    f"✓ Accepted {entity_type}: '{entity['Text']}' "
                    f"(confidence: {entity['Score']:.2f})"
                )
            else:
                filtered_count += 1
                logger.debug(
                    f"✗ Rejected {entity['Type']}: '{entity['Text']}' "
                    f"(confidence: {entity['Score']:.2f} < {confidence_threshold})"
                )

        accepted_count = total_entities - filtered_count
        logger.info(
            f"Entities: {accepted_count} accepted, {filtered_count} filtered "
            f"(threshold: {confidence_threshold})"
        )

        return dict(entities_by_type)

    except Exception as e:
        logger.error(f"✗ Error extracting entities: {type(e).__name__}: {e}")
        STATS['comprehend_errors'] += 1
        return {}


# ============================================================================
# AWS COMPREHEND - KEY PHRASE EXTRACTION
# ============================================================================

def is_quality_phrase(phrase: str) -> bool:
    """
    Check if a phrase is high quality and meaningful

    FILTERING CRITERIA:
    -------------------
    Rejects phrases that are:
    - Too short (< 3 words typically means noise)
    - Generic stopwords ("the report", "this analysis")
    - Navigation/formatting text ("see above", "as follows")
    - Just numbers or symbols
    - Markdown/HTML formatting

    Parameters
    ----------
    phrase : str
        Phrase to evaluate

    Returns
    -------
    bool
        True if quality phrase, False if junk
    """
    phrase_lower = phrase.lower().strip()

    # ───────────────────────────────────────────────────────────────
    # FILTER 1: Remove very short phrases (single word or symbol)
    # ───────────────────────────────────────────────────────────────
    if len(phrase_lower) < 3:
        return False

    # ───────────────────────────────────────────────────────────────
    # FILTER 2: Remove markdown/HTML artifacts
    # ───────────────────────────────────────────────────────────────
    junk_patterns = [
        '**', '##', '![', '](', '*caption', '*ai analysis',
        'image**', 'table**', 'chart**', 'axes:', 'trends:',
        'key insights:', 'source:', '|', '\n', '<', '>'
    ]

    for pattern in junk_patterns:
        if pattern in phrase_lower:
            return False

    # ───────────────────────────────────────────────────────────────
    # FILTER 3: Remove generic navigation/reference phrases
    # ───────────────────────────────────────────────────────────────
    generic_phrases = [
        'see above', 'see below', 'as follows', 'as shown',
        'the following', 'the above', 'the below', 'click here',
        'this report', 'this analysis', 'this visual', 'this chart',
        'this table', 'this diagram', 'this figure', 'this image',
        'exhibit', 'figure', 'page', 'slide'
    ]

    for generic in generic_phrases:
        if phrase_lower == generic or phrase_lower.startswith(generic + ' '):
            return False

    # ───────────────────────────────────────────────────────────────
    # FILTER 4: Remove axis/chart description phrases
    # ───────────────────────────────────────────────────────────────
    chart_junk = [
        'x-axis', 'y-axis', 'horizontal axis', 'vertical axis',
        'the x-axis', 'the y-axis', 'left', 'right', 'blue line',
        'green line', 'gold line', 'red line', 'bar chart',
        'line chart', 'pie chart'
    ]

    for junk in chart_junk:
        if phrase_lower == junk:
            return False

    # ───────────────────────────────────────────────────────────────
    # FILTER 5: Remove phrases that are just numbers or ordinals
    # ───────────────────────────────────────────────────────────────
    if phrase_lower.replace(',', '').replace('.', '').isdigit():
        return False

    # ───────────────────────────────────────────────────────────────
    # FILTER 6: Keep only phrases with meaningful content
    # ───────────────────────────────────────────────────────────────
    # Phrase should have at least one alphabetic character
    if not any(c.isalpha() for c in phrase):
        return False

    return True


def extract_key_phrases(
    text: str,
    comprehend_client: Optional[object],
    confidence_threshold: float = 0.7,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> List[str]:
    """
    Extract key phrases using AWS Comprehend with quality filtering

    WHAT ARE KEY PHRASES?
    ---------------------
    Key phrases are multi-word expressions that capture important meaning:
    - "quarterly revenue growth"
    - "year-over-year performance"
    - "EBITDA margin expansion"

    QUALITY FILTERING:
    ------------------
    Automatically removes:
    - Markdown/HTML artifacts (**, ##, ![, etc.)
    - Generic references ("see above", "this chart")
    - Chart description text ("x-axis", "blue line")
    - Very short phrases (< 3 chars)
    - Just numbers or symbols

    Parameters
    ----------
    text : str
        Text to analyze
    comprehend_client : boto3.client or None
        AWS Comprehend client
    confidence_threshold : float
        Minimum confidence (0.0-1.0)
    max_retries : int
        Maximum retry attempts
    retry_delay : float
        Base delay for exponential backoff

    Returns
    -------
    List[str]
        List of high-quality key phrases
    """
    if not comprehend_client:
        logger.debug("AWS Comprehend disabled, skipping key phrase extraction")
        return []

    if not text or len(text) < 3:
        logger.debug(f"Text too short for key phrase extraction: {len(text)} chars")
        return []

    original_length = len(text)
    text = text[:4500]

    if original_length > 4500:
        logger.warning(
            f"Text truncated from {original_length} to 4500 chars for AWS limits"
        )

    try:
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Calling AWS Comprehend detect_key_phrases "
                    f"(attempt {attempt + 1}/{max_retries})"
                )

                response = comprehend_client.detect_key_phrases(
                    Text=text,
                    LanguageCode='en'
                )

                STATS['comprehend_calls'] += 1

                logger.debug(
                    f"✓ AWS Comprehend call successful. "
                    f"Found {len(response.get('KeyPhrases', []))} raw phrases"
                )

                break

            except ClientError as e:
                if e.response['Error']['Code'] == 'ThrottlingException':
                    if attempt < max_retries - 1:
                        delay = retry_delay * (2 ** attempt)
                        logger.warning(
                            f"⚠ AWS throttled request. Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"✗ AWS throttling persisted after {max_retries} attempts"
                        )
                        raise
                else:
                    logger.error(f"✗ AWS Comprehend error: {e.response['Error']['Code']}")
                    raise

        # ═══════════════════════════════════════════════════════════
        # Extract and filter phrases
        # ═══════════════════════════════════════════════════════════
        phrases = []
        total_phrases = len(response.get('KeyPhrases', []))
        confidence_filtered = 0
        quality_filtered = 0

        for phrase in response.get('KeyPhrases', []):
            # First filter by confidence
            if phrase['Score'] < confidence_threshold:
                confidence_filtered += 1
                logger.debug(
                    f"✗ Rejected (confidence): '{phrase['Text']}' "
                    f"({phrase['Score']:.2f} < {confidence_threshold})"
                )
                continue

            # Then filter by quality
            if not is_quality_phrase(phrase['Text']):
                quality_filtered += 1
                logger.debug(
                    f"✗ Rejected (quality): '{phrase['Text']}'"
                )
                continue

            # Passed both filters - keep it
            phrases.append(phrase['Text'])
            STATS['key_phrases_extracted'] += 1

            logger.debug(
                f"✓ Accepted phrase: '{phrase['Text']}' "
                f"(confidence: {phrase['Score']:.2f})"
            )

        accepted_count = len(phrases)
        total_filtered = confidence_filtered + quality_filtered

        logger.info(
            f"Key phrases: {accepted_count} accepted, {total_filtered} filtered "
            f"({confidence_filtered} confidence, {quality_filtered} quality)"
        )

        return phrases

    except Exception as e:
        logger.error(f"✗ Error extracting key phrases: {type(e).__name__}: {e}")
        STATS['comprehend_errors'] += 1
        return []


# ============================================================================
# CUSTOM PATTERN EXTRACTION
# ============================================================================

def extract_custom_patterns(text: str, patterns: Dict[str, re.Pattern]) -> Dict[str, List]:
    """
    Extract custom patterns using regex (FREE - no AWS costs!)

    WHAT ARE PATTERNS?
    ------------------
    Patterns are recurring structures in text:
    - Monetary values: $15.4B, $2.3M
    - Percentages: 25%, 15.5%
    - Quarters: Q3 2024, Q4
    - Financial metrics: EBITDA, EPS, ROE

    WHY USE PATTERNS?
    -----------------
    ✓ FREE: No API costs
    ✓ FAST: Instant extraction
    ✓ ACCURATE: 100% for exact formats
    ✓ OFFLINE: Works without internet

    Parameters
    ----------
    text : str
        Text to search for patterns
    patterns : Dict[str, re.Pattern]
        Compiled regex patterns

    Returns
    -------
    Dict[str, List]
        Dictionary of extracted patterns
    """
    results = {}

    # ───────────────────────────────────────────────────────────────
    # Extract monetary values
    # ───────────────────────────────────────────────────────────────
    monetary_matches = patterns['monetary_values'].findall(text)
    results['monetary_values'] = [
        f"${amount}{suffix}" if suffix else f"${amount}"
        for amount, suffix in monetary_matches
    ]

    if results['monetary_values']:
        logger.debug(
            f"Found {len(results['monetary_values'])} monetary values: "
            f"{results['monetary_values'][:5]}"
        )

    # ───────────────────────────────────────────────────────────────
    # Extract percentages
    # ───────────────────────────────────────────────────────────────
    pct_matches = patterns['percentages'].findall(text)
    results['percentages'] = [f"{pct}%" for pct in pct_matches]

    if results['percentages']:
        logger.debug(
            f"Found {len(results['percentages'])} percentages: "
            f"{results['percentages'][:5]}"
        )

    # ───────────────────────────────────────────────────────────────
    # Extract quarters
    # ───────────────────────────────────────────────────────────────
    results['quarters'] = patterns['quarters'].findall(text)

    if results['quarters']:
        logger.debug(f"Found {len(results['quarters'])} quarters: {results['quarters']}")

    # ───────────────────────────────────────────────────────────────
    # Extract years
    # ───────────────────────────────────────────────────────────────
    results['years'] = patterns['years'].findall(text)

    if results['years']:
        logger.debug(f"Found {len(results['years'])} years: {results['years']}")

    # ───────────────────────────────────────────────────────────────
    # Extract financial metrics
    # ───────────────────────────────────────────────────────────────
    metrics_matches = patterns['financial_metrics'].findall(text)
    results['financial_metrics'] = list(set(metrics_matches))

    if results['financial_metrics']:
        logger.debug(
            f"Found {len(results['financial_metrics'])} financial metrics: "
            f"{results['financial_metrics']}"
        )

    # ───────────────────────────────────────────────────────────────
    # Update statistics
    # ───────────────────────────────────────────────────────────────
    total_matches = sum(len(v) for v in results.values())
    STATS['patterns_matched'] += total_matches

    logger.info(
        f"Pattern extraction complete: {total_matches} total matches "
        f"across {len(results)} categories"
    )

    return results


# ============================================================================
# MAIN ENRICHMENT FUNCTION
# ============================================================================

def enrich_chunk(
    chunk: Dict,
    comprehend_client: Optional[object] = None,
    enable_comprehend: bool = True,
    enable_patterns: bool = True,
    enable_key_phrases: bool = False,  # Disabled by default due to noise
    confidence_threshold: float = 0.7,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Dict:
    """
    Enrich a single chunk with metadata

    MAIN ENTRY POINT for enrichment

    Process:
    1. Extract text from chunk
    2. Extract entities (AWS Comprehend)
    3. Extract key phrases (AWS Comprehend) - OPTIONAL
    4. Extract custom patterns (regex)
    5. Merge into metadata

    Parameters
    ----------
    chunk : Dict
        Chunk dictionary with text content
    comprehend_client : boto3.client or None
        AWS Comprehend client
    enable_comprehend : bool
        Use AWS Comprehend for entities
    enable_patterns : bool
        Use regex patterns
    enable_key_phrases : bool
        Extract key phrases (disabled by default due to noise)
    confidence_threshold : float
        Minimum confidence for entities/phrases
    max_retries : int
        Maximum retry attempts for AWS
    retry_delay : float
        Base delay for exponential backoff

    Returns
    -------
    Dict
        Enriched chunk with metadata added
    """
    # ───────────────────────────────────────────────────────────────
    # STEP 1: Extract text from chunk
    # ───────────────────────────────────────────────────────────────
    text = get_text_from_chunk(chunk)

    if not text or not text.strip():
        chunk_id = chunk.get('id', 'unknown')
        logger.warning(f"Empty text for chunk: {chunk_id}")
        return chunk

    # ───────────────────────────────────────────────────────────────
    # STEP 2: Extract entities (if enabled)
    # ───────────────────────────────────────────────────────────────
    entities = {}
    if enable_comprehend and comprehend_client:
        entities = extract_entities(
            text,
            comprehend_client,
            confidence_threshold,
            max_retries,
            retry_delay
        )

    # ───────────────────────────────────────────────────────────────
    # STEP 3: Extract key phrases (if enabled)
    # ───────────────────────────────────────────────────────────────
    key_phrases = []
    if enable_key_phrases and enable_comprehend and comprehend_client:
        key_phrases = extract_key_phrases(
            text,
            comprehend_client,
            confidence_threshold,
            max_retries,
            retry_delay
        )

    # ───────────────────────────────────────────────────────────────
    # STEP 4: Extract custom patterns (if enabled)
    # ───────────────────────────────────────────────────────────────
    patterns_result = {}
    if enable_patterns:
        patterns_result = extract_custom_patterns(text, PATTERNS)

    # ───────────────────────────────────────────────────────────────
    # STEP 5: Merge into metadata
    # ───────────────────────────────────────────────────────────────
    if 'metadata' not in chunk:
        chunk['metadata'] = {}

    chunk['metadata']['entities'] = entities

    # Only add key_phrases if enabled
    if enable_key_phrases:
        chunk['metadata']['key_phrases'] = key_phrases

    chunk['metadata'].update(patterns_result)

    # ───────────────────────────────────────────────────────────────
    # STEP 6: Update statistics
    # ───────────────────────────────────────────────────────────────
    STATS['chunks_processed'] += 1

    return chunk


# ============================================================================
# BATCH ENRICHMENT FUNCTION
# ============================================================================

def enrich_chunks_batch(
    chunks: List[Dict],
    comprehend_client: Optional[object] = None,
    enable_comprehend: bool = True,
    enable_patterns: bool = True,
    confidence_threshold: float = 0.7,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    batch_size: int = 100,
    show_progress: bool = True
) -> List[Dict]:
    """
    Enrich multiple chunks with progress tracking

    Parameters
    ----------
    chunks : List[Dict]
        List of chunks to enrich
    comprehend_client : boto3.client or None
        AWS Comprehend client
    enable_comprehend : bool
        Use AWS Comprehend
    enable_patterns : bool
        Use regex patterns
    confidence_threshold : float
        Minimum confidence
    max_retries : int
        Maximum retries
    retry_delay : float
        Retry delay
    batch_size : int
        Progress update frequency
    show_progress : bool
        Show progress messages

    Returns
    -------
    List[Dict]
        Enriched chunks
    """
    enriched_chunks = []
    total = len(chunks)

    if show_progress:
        logger.info(f"Starting enrichment of {total} chunks...")

    for i, chunk in enumerate(chunks, 1):
        enriched = enrich_chunk(
            chunk,
            comprehend_client,
            enable_comprehend,
            enable_patterns,
            confidence_threshold,
            max_retries,
            retry_delay
        )
        enriched_chunks.append(enriched)

        if show_progress and i % batch_size == 0:
            pct = (i / total) * 100
            logger.info(f"Progress: {i}/{total} ({pct:.1f}%)")

    if show_progress:
        logger.info(f"Enrichment complete! Processed {total} chunks")
        print_statistics()

    return enriched_chunks


# ============================================================================
# STATISTICS FUNCTIONS
# ============================================================================

def print_statistics():
    """Print enrichment statistics"""
    print("\n" + "="*70)
    print("METADATA ENRICHMENT STATISTICS")
    print("="*70)
    print(f"Chunks processed:        {STATS['chunks_processed']:,}")
    print(f"Comprehend API calls:    {STATS['comprehend_calls']:,}")
    print(f"Comprehend errors:       {STATS['comprehend_errors']:,}")
    print(f"Entities extracted:      {STATS['entities_extracted']:,}")
    print(f"Key phrases extracted:   {STATS['key_phrases_extracted']:,}")
    print(f"Pattern matches:         {STATS['patterns_matched']:,}")

    # Cost estimation
    if STATS['comprehend_calls'] > 0:
        estimated_cost = (STATS['chunks_processed'] * 500 * 0.0001 / 100) * 2
        print(f"\nEstimated AWS cost:      ${estimated_cost:.2f}")

    print("="*70 + "\n")


def get_statistics() -> Dict:
    """Return statistics as dictionary"""
    return STATS.copy()


def reset_statistics():
    """Reset statistics counters"""
    STATS['chunks_processed'] = 0
    STATS['comprehend_calls'] = 0
    STATS['comprehend_errors'] = 0
    STATS['entities_extracted'] = 0
    STATS['key_phrases_extracted'] = 0
    STATS['patterns_matched'] = 0


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    """
    Example usage of functional metadata enricher
    """
    print("\n" + "="*70)
    print("METADATA ENRICHER - Functional Example")
    print("="*70)

    # Sample chunk
    chunk = {
        'content': """## Q3 Financial Results
        
Morgan Stanley reported Q3 2024 revenue of $15.4B, representing 25% 
growth year-over-year. CEO James Gorman highlighted strong performance 
in investment banking, with M&A advisory fees up 30%. The company's 
EBITDA margin improved to 28%, and EPS reached $2.15.""",
        'metadata': {
            'breadcrumbs': 'Financial Report > Q3 Results',
            'char_count': 250,
            'num_atomic_chunks': 2
        }
    }

    print("\n--- ORIGINAL CHUNK ---")
    print(f"Content: {chunk['content'][:100]}...")
    print(f"Metadata keys: {list(chunk['metadata'].keys())}")

    # Initialize client (patterns only for this example - no AWS needed)
    comprehend_client = None  # Set to init_comprehend_client() if you have AWS

    # Enrich chunk
    enriched = enrich_chunk(
        chunk,
        comprehend_client=comprehend_client,
        enable_comprehend=False,  # Set to True if you have AWS credentials
        enable_patterns=True
    )

    print("\n--- ENRICHED CHUNK ---")
    print(f"Metadata keys: {list(enriched['metadata'].keys())}")
    print(f"\nMonetary values: {enriched['metadata']['monetary_values']}")
    print(f"Percentages: {enriched['metadata']['percentages']}")
    print(f"Quarters: {enriched['metadata']['quarters']}")
    print(f"Financial metrics: {enriched['metadata']['financial_metrics']}")

    print_statistics()

    print("✓ Example completed!")