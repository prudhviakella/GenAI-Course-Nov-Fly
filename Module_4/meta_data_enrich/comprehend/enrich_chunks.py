"""
================================================================================
CHUNK ENRICHMENT PIPELINE - Functional Version (No Classes)
================================================================================

UPDATED FOR:
============
- Pure functional approach (no classes)
- Works with comprehensive_chunker.py output
- Simple and straightforward functions
- Clean output format

INPUT FORMAT:
=============
{
  "chunks": [
    {
      "content": "## Header\n\nText content...",
      "metadata": {
        "breadcrumbs": "Section Name",
        "char_count": 1500,
        "num_atomic_chunks": 5
      }
    }
  ]
}

OUTPUT FORMAT:
==============
{
  "metadata": {
    "enriched_at": "2025-02-10T10:30:00",
    "total_chunks": 100,
    "enricher_version": "2.0.0"
  },
  "chunks": [...],  # Enriched chunks
  "statistics": {...}
}

USAGE:
======
    # Basic usage
    python enrich_chunks_functional.py semantic_chunks.json

    # Custom output
    python enrich_chunks_functional.py input.json output.json

    # Without AWS Comprehend (free)
    python enrich_chunks_functional.py input.json --no-comprehend
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Import the functional metadata enricher
from metadata_enricher import (
    init_comprehend_client,
    enrich_chunk,
    enrich_chunks_batch,
    get_statistics,
    reset_statistics
)


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


# ============================================================================
# FILE LOADING FUNCTION
# ============================================================================

def load_chunks(input_file: str) -> List[Dict]:
    """
    Load chunks from JSON file

    COMPATIBILITY:
    --------------
    Supports multiple JSON formats:

    Format 1 (comprehensive_chunker.py):
    {
      "chunks": [...]
    }

    Format 2 (legacy):
    {
      "semantic_chunks": [...]
    }

    Parameters
    ----------
    input_file : str
        Path to JSON file

    Returns
    -------
    List[Dict]
        Array of chunks

    Raises
    ------
    FileNotFoundError
        If file doesn't exist
    ValueError
        If JSON format is invalid
    """
    # ───────────────────────────────────────────────────────────────
    # STEP 1: Validate file exists
    # ───────────────────────────────────────────────────────────────
    logger.info(f"Loading chunks from: {input_file}")

    if not os.path.exists(input_file):
        error_msg = (
            f"Input file not found: {input_file}\n\n"
            f"Expected file location:\n"
            f"  Current directory: {os.getcwd()}\n"
            f"  Looking for: {os.path.abspath(input_file)}\n\n"
            f"Make sure you've run comprehensive_chunker.py first!"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Log file size
    file_size_mb = os.path.getsize(input_file) / (1024 * 1024)
    logger.info(f"File size: {file_size_mb:.2f} MB")

    # ───────────────────────────────────────────────────────────────
    # STEP 2: Load and parse JSON
    # ───────────────────────────────────────────────────────────────
    try:
        logger.debug("Parsing JSON file...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug("✓ JSON parsed successfully")

    except json.JSONDecodeError as e:
        error_msg = (
            f"Invalid JSON format in {input_file}\n"
            f"Error at line {e.lineno}, column {e.colno}:\n"
            f"{e.msg}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # ───────────────────────────────────────────────────────────────
    # STEP 3: Extract chunks array
    # ───────────────────────────────────────────────────────────────
    if 'chunks' in data:
        chunks = data['chunks']
        logger.info(f"✓ Detected standard format with 'chunks' key")

    elif 'semantic_chunks' in data:
        chunks = data['semantic_chunks']
        logger.info(f"✓ Detected legacy format with 'semantic_chunks' key")
        logger.warning(
            "Legacy format detected. Consider re-running with "
            "comprehensive_chunker.py for cleaner output."
        )

    else:
        available_keys = list(data.keys())
        error_msg = (
            f"Invalid JSON structure in {input_file}\n\n"
            f"Expected keys: 'chunks' OR 'semantic_chunks'\n"
            f"Found keys: {available_keys}\n\n"
            f"This doesn't look like output from comprehensive_chunker.py.\n"
            f"Make sure you're using the correct input file!"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # ───────────────────────────────────────────────────────────────
    # STEP 4: Validate chunks array
    # ───────────────────────────────────────────────────────────────
    if not isinstance(chunks, list):
        error_msg = (
            f"Expected 'chunks' to be a list, got {type(chunks).__name__}\n"
            f"File may be corrupted or in unexpected format."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    if len(chunks) == 0:
        logger.warning("⚠ Loaded 0 chunks! File is empty or invalid.")
    else:
        logger.info(f"✓ Loaded {len(chunks)} chunks successfully")

        # Log sample chunk info
        sample_chunk = chunks[0]
        logger.debug(f"Sample chunk keys: {list(sample_chunk.keys())}")

        if 'content' in sample_chunk:
            logger.debug("Chunks use 'content' field (new format)")
        elif 'content_only' in sample_chunk:
            logger.debug("Chunks use 'content_only' field (legacy format)")
        else:
            logger.warning(
                f"Chunks have unexpected structure. "
                f"Fields: {list(sample_chunk.keys())}"
            )

    return chunks


# ============================================================================
# CHUNK VALIDATION FUNCTION
# ============================================================================

def validate_chunk(chunk: Dict, index: int) -> bool:
    """
    Validate chunk has required fields

    VALIDATION CHECKS:
    ------------------
    1. Has text field ('content' or 'content_only')?
    2. Is text non-empty?
    3. Is text not just whitespace?

    Parameters
    ----------
    chunk : Dict
        Chunk to validate
    index : int
        Chunk position (for error messages)

    Returns
    -------
    bool
        True if valid, False if invalid
    """
    # ───────────────────────────────────────────────────────────────
    # CHECK 1: Does chunk have a text field?
    # ───────────────────────────────────────────────────────────────
    has_content = 'content' in chunk
    has_content_only = 'content_only' in chunk

    if not has_content and not has_content_only:
        logger.warning(
            f"✗ Chunk {index}: Missing text field\n"
            f"  Expected: 'content' (new) OR 'content_only' (legacy)\n"
            f"  Found fields: {list(chunk.keys())}\n"
            f"  This chunk will be skipped during enrichment."
        )
        return False

    if has_content:
        logger.debug(f"Chunk {index}: Using 'content' field (new format)")
    else:
        logger.debug(f"Chunk {index}: Using 'content_only' field (legacy format)")

    # ───────────────────────────────────────────────────────────────
    # CHECK 2: Is the content non-empty?
    # ───────────────────────────────────────────────────────────────
    content = chunk.get('content') or chunk.get('content_only', '')

    if not content:
        logger.warning(
            f"✗ Chunk {index}: Empty content field\n"
            f"  Content value: {repr(content)}\n"
            f"  This chunk will be skipped during enrichment."
        )
        return False

    # ───────────────────────────────────────────────────────────────
    # CHECK 3: Is the content not just whitespace?
    # ───────────────────────────────────────────────────────────────
    if not content.strip():
        logger.warning(
            f"✗ Chunk {index}: Content is only whitespace\n"
            f"  Content length: {len(content)} chars (all whitespace)\n"
            f"  This chunk will be skipped during enrichment."
        )
        return False

    # ───────────────────────────────────────────────────────────────
    # ALL CHECKS PASSED
    # ───────────────────────────────────────────────────────────────
    content_length = len(content.strip())
    logger.debug(f"✓ Chunk {index}: Valid ({content_length} chars)")

    return True


# ============================================================================
# ENRICHMENT FUNCTION
# ============================================================================

def enrich_all_chunks(
    chunks: List[Dict],
    comprehend_client: Optional[object] = None,
    enable_comprehend: bool = True,
    enable_patterns: bool = True,
    enable_key_phrases: bool = False,
    confidence_threshold: float = 0.7,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    batch_size: int = 100,
    show_progress: bool = True
) -> List[Dict]:
    """
    Enrich all chunks with metadata

    Process:
    1. Validate each chunk
    2. Call enrichment function
    3. Track progress
    4. Handle errors gracefully

    Parameters
    ----------
    chunks : List[Dict]
        Chunks to enrich
    comprehend_client : boto3.client or None
        AWS Comprehend client
    enable_comprehend : bool
        Use AWS Comprehend
    enable_patterns : bool
        Use regex patterns
    enable_key_phrases : bool
        Extract key phrases (disabled by default)
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
    skipped = 0

    logger.info(f"Starting enrichment of {total} chunks...")

    for i, chunk in enumerate(chunks, 1):
        # Validate chunk
        if not validate_chunk(chunk, i):
            logger.warning(f"Skipping invalid chunk {i}/{total}")
            skipped += 1
            # Keep original chunk even if invalid
            enriched_chunks.append(chunk)
            continue

        try:
            # Enrich chunk
            enriched = enrich_chunk(
                chunk,
                comprehend_client,
                enable_comprehend,
                enable_patterns,
                enable_key_phrases,
                confidence_threshold,
                max_retries,
                retry_delay
            )
            enriched_chunks.append(enriched)

            # Progress update
            if show_progress and i % batch_size == 0:
                pct = (i / total) * 100
                logger.info(f"Progress: {i}/{total} ({pct:.1f}%)")

        except Exception as e:
            logger.error(f"Error enriching chunk {i}: {e}")
            # Keep original chunk on error
            enriched_chunks.append(chunk)
            skipped += 1

    logger.info(f"✓ Enrichment complete: {total - skipped} enriched, {skipped} skipped")

    return enriched_chunks


# ============================================================================
# SAVE FUNCTION
# ============================================================================

def save_enriched_chunks(
    enriched_chunks: List[Dict],
    output_file: str,
    config: Dict
):
    """
    Save enriched chunks to JSON file

    Output structure:
    {
      "metadata": {...},
      "chunks": [...],
      "statistics": {...}
    }

    Parameters
    ----------
    enriched_chunks : List[Dict]
        Enriched chunks
    output_file : str
        Output file path
    config : Dict
        Configuration used for enrichment
    """
    logger.info(f"Saving enriched chunks to: {output_file}")

    # Build output structure
    output = {
        'metadata': {
            'enriched_at': datetime.now().isoformat(),
            'total_chunks': len(enriched_chunks),
            'enricher_version': '2.0.0',
            'configuration': config
        },
        'chunks': enriched_chunks,
        'statistics': get_statistics()
    }

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Report file size
    file_size = os.path.getsize(output_file)
    size_mb = file_size / (1024 * 1024)

    logger.info(f"✓ Saved: {output_file}")
    logger.info(f"  File size: {size_mb:.2f} MB")


# ============================================================================
# MAIN PIPELINE FUNCTION
# ============================================================================

def run_enrichment_pipeline(
    input_file: str,
    output_file: Optional[str] = None,
    region_name: str = 'us-east-1',
    enable_comprehend: bool = True,
    enable_patterns: bool = True,
    enable_key_phrases: bool = False,
    confidence_threshold: float = 0.7,
    batch_size: int = 100,
    show_progress: bool = True,
    print_statistics: bool = True
):
    """
    Execute full enrichment pipeline

    Steps:
    1. Load chunks from input file
    2. Initialize AWS Comprehend (if enabled)
    3. Enrich chunks with metadata
    4. Save enriched chunks to output file
    5. Print statistics

    Parameters
    ----------
    input_file : str
        Path to input JSON file
    output_file : str, optional
        Path to output file (auto-generated if not provided)
    region_name : str
        AWS region
    enable_comprehend : bool
        Use AWS Comprehend
    enable_patterns : bool
        Use regex patterns
    confidence_threshold : float
        Minimum confidence
    batch_size : int
        Progress update frequency
    show_progress : bool
        Show progress updates
    print_statistics : bool
        Print enrichment statistics
    """
    try:
        logger.info("="*70)
        logger.info("CHUNK ENRICHMENT PIPELINE - Starting")
        logger.info("="*70)

        # Reset statistics
        reset_statistics()

        # Generate output filename if not provided
        if output_file is None:
            input_path = Path(input_file)
            input_stem = input_path.stem
            input_dir = input_path.parent
            output_filename = f"{input_stem}_enriched.json"
            output_file = str(input_dir / output_filename)
            logger.info(f"Output file: {output_file}")

        # ═══════════════════════════════════════════════════════════
        # STEP 1: Load chunks
        # ═══════════════════════════════════════════════════════════
        logger.info("\nSTEP 1: Loading chunks")
        chunks = load_chunks(input_file)

        # ═══════════════════════════════════════════════════════════
        # STEP 2: Initialize AWS Comprehend
        # ═══════════════════════════════════════════════════════════
        logger.info("\nSTEP 2: Initializing enrichment services")

        comprehend_client = None
        if enable_comprehend:
            comprehend_client = init_comprehend_client(region_name)
            if comprehend_client is None:
                logger.warning("AWS Comprehend initialization failed. Using patterns only.")
                enable_comprehend = False
        else:
            logger.info("AWS Comprehend disabled (patterns only mode)")

        # ═══════════════════════════════════════════════════════════
        # STEP 3: Enrich chunks
        # ═══════════════════════════════════════════════════════════
        logger.info("\nSTEP 3: Enriching chunks with metadata")

        enriched_chunks = enrich_all_chunks(
            chunks,
            comprehend_client,
            enable_comprehend,
            enable_patterns,
            enable_key_phrases,
            confidence_threshold,
            max_retries=3,
            retry_delay=1.0,
            batch_size=batch_size,
            show_progress=show_progress
        )

        # ═══════════════════════════════════════════════════════════
        # STEP 4: Save enriched chunks
        # ═══════════════════════════════════════════════════════════
        logger.info("\nSTEP 4: Saving enriched chunks")

        config = {
            'comprehend_enabled': enable_comprehend,
            'patterns_enabled': enable_patterns,
            'confidence_threshold': confidence_threshold,
            'aws_region': region_name
        }

        save_enriched_chunks(enriched_chunks, output_file, config)

        # ═══════════════════════════════════════════════════════════
        # STEP 5: Print statistics
        # ═══════════════════════════════════════════════════════════
        if print_statistics:
            logger.info("\nSTEP 5: Enrichment statistics")
            from metadata_enricher import print_statistics
            print_statistics()

        logger.info("="*70)
        logger.info("CHUNK ENRICHMENT PIPELINE - Completed Successfully!")
        logger.info("="*70)

    except Exception as e:
        logger.error("="*70)
        logger.error("CHUNK ENRICHMENT PIPELINE - FAILED")
        logger.error("="*70)
        logger.error(f"Error: {e}")
        raise


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Enrich semantic chunks with metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python enrich_chunks_functional.py semantic_chunks.json
  
  # Custom output filename
  python enrich_chunks_functional.py input.json output.json
  
  # Without AWS Comprehend (patterns only, free)
  python enrich_chunks_functional.py input.json --no-comprehend
  
  # Specify AWS region
  python enrich_chunks_functional.py input.json --region us-west-2
  
  # Custom confidence threshold
  python enrich_chunks_functional.py input.json --confidence 0.9
        """
    )

    # Required argument
    parser.add_argument(
        'input_file',
        help='Input JSON file with chunks'
    )

    # Optional arguments
    parser.add_argument(
        'output_file',
        nargs='?',
        default=None,
        help='Output JSON file (default: <input>_enriched.json)'
    )

    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region for Comprehend (default: us-east-1)'
    )

    parser.add_argument(
        '--no-comprehend',
        action='store_true',
        help='Disable AWS Comprehend (use patterns only, free)'
    )

    parser.add_argument(
        '--no-patterns',
        action='store_true',
        help='Disable custom patterns (use Comprehend only)'
    )

    parser.add_argument(
        '--enable-key-phrases',
        action='store_true',
        help='Enable key phrase extraction (disabled by default due to noise)'
    )

    parser.add_argument(
        '--confidence',
        type=float,
        default=0.7,
        help='Confidence threshold (0.0-1.0, default: 0.7)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Progress update frequency (default: 100)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )

    args = parser.parse_args()

    # Validate confidence threshold
    if not 0.0 <= args.confidence <= 1.0:
        parser.error("Confidence threshold must be between 0.0 and 1.0")

    # Run pipeline
    run_enrichment_pipeline(
        input_file=args.input_file,
        output_file=args.output_file,
        region_name=args.region,
        enable_comprehend=not args.no_comprehend,
        enable_patterns=not args.no_patterns,
        enable_key_phrases=args.enable_key_phrases,
        confidence_threshold=args.confidence,
        batch_size=args.batch_size,
        show_progress=not args.quiet,
        print_statistics=not args.quiet
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    main()