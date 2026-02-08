"""
Main Orchestrator Module
=========================

EDUCATIONAL PURPOSE
-------------------
This module coordinates all components to process documents from start to finish.
It's the "conductor" that directs all the other modules.

WHY AN ORCHESTRATOR?
--------------------
Instead of having all logic in one main() function, we use an orchestrator that:
1. Maintains clean separation between coordination and implementation
2. Makes the overall flow crystal clear
3. Allows easy modification of the pipeline
4. Facilitates testing of the complete workflow

PROCESSING PIPELINE
-------------------
1. Load configuration
2. Setup logging
3. Load metadata
4. For each page:
   - Load markdown text
   - Identify protected blocks
   - Parse semantic sections
   - Consolidate paragraphs
   - Build chunks
5. Detect cross-page continuations
6. Merge boundary chunks if needed
7. Calculate statistics
8. Save output

This module coordinates but delegates actual work to specialized modules.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import all functional modules
from config import create_config, create_stats_dict, config_to_string
from logger_utils import setup_logger, log_section_header, LogTimer
from protected_blocks import identify_protected_blocks, count_protected_blocks_by_type
from semantic_parser import parse_semantic_sections, consolidate_paragraphs
from chunking_engine import build_chunks_from_sections
from continuation_detection import detect_page_continuation
from page_merging import merge_continued_pages
from statistics_calculator import calculate_comprehensive_statistics
from file_io import save_chunks_output, load_metadata


# ============================================================================
# MAIN PROCESSING FUNCTION
# ============================================================================

def process_document(
    input_dir: str,
    target_size: int = 1500,
    min_size: int = 800,
    max_size: int = 2500,
    enable_merging: bool = True,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Process a document through the complete chunking pipeline.
    
    This is the main entry point that coordinates all steps.
    
    FUNCTIONAL DESIGN PRINCIPLE
    ---------------------------
    Each step is a PURE FUNCTION that:
    - Takes inputs
    - Produces outputs
    - Has no side effects (except logging)
    - Can be tested independently
    
    Data flows through the pipeline:
    
        metadata → pages → sections → chunks → output
    
    Each transformation is explicit and traceable.
    
    Parameters
    ----------
    input_dir : str
        Directory containing metadata.json and pages/
    target_size : int
        Target chunk size in characters
    min_size : int
        Minimum chunk size
    max_size : int
        Maximum chunk size
    enable_merging : bool
        Enable cross-page boundary merging
    verbose : bool
        Enable verbose DEBUG logging
    
    Returns
    -------
    Dict[str, Any]
        Processing results with statistics
    """
    
    # ========================================================================
    # STEP 1: INITIALIZATION
    # ========================================================================
    
    input_path = Path(input_dir)
    
    # Create configuration
    config = create_config(
        target_size=target_size,
        min_size=min_size,
        max_size=max_size,
        enable_merging=enable_merging,
        verbose=verbose
    )
    
    # Setup logging
    logger = setup_logger(input_path, verbose=verbose)
    logger.info(config_to_string(config))
    
    # Initialize statistics
    stats = create_stats_dict()
    
    # ========================================================================
    # STEP 2: LOAD METADATA
    # ========================================================================
    
    with LogTimer(logger, "Loading metadata"):
        metadata = load_metadata(input_path, logger)
        if not metadata:
            logger.error("Failed to load metadata")
            return {}
    
    doc_name = metadata.get('document', 'Unknown')
    pages = metadata.get('pages', [])
    stats['total_pages'] = len(pages)
    
    logger.info(f"\nDocument: {doc_name}")
    logger.info(f"Total Pages: {len(pages)}\n")
    
    # ========================================================================
    # STEP 3: PROCESS EACH PAGE
    # ========================================================================
    
    all_chunks = []
    processed_pages = set()
    
    with LogTimer(logger, "Processing all pages"):
        for idx, page in enumerate(pages):
            # Skip if already processed (merged with previous)
            if idx in processed_pages:
                continue
            
            page_num = page.get('page_number', idx + 1)
            logger.info(f"Processing Page {page_num} ({idx+1}/{len(pages)})")
            
            # Process single page
            page_chunks = _process_single_page(
                page, input_path, config, stats, logger
            )
            break
            
            logger.info(f"  Created {len(page_chunks)} chunks")
            
            # ================================================================
            # STEP 4: CHECK FOR CONTINUATION (if enabled)
            # ================================================================
            
            if enable_merging and idx < len(pages) - 1:
                next_page = pages[idx + 1]
                next_page_num = next_page.get('page_number', idx + 2)
                
                logger.debug(f"  Checking continuation to page {next_page_num}")
                
                # Detect continuation
                continues = detect_page_continuation(
                    page, next_page, input_path, config, stats, logger
                )
                
                if continues:
                    logger.info(
                        f"  CONTINUATION: Page {page_num} → {next_page_num}"
                    )
                    
                    # Process next page
                    next_chunks = _process_single_page(
                        next_page, input_path, config, stats, logger
                    )
                    
                    logger.info(f"  Created {len(next_chunks)} chunks from page {next_page_num}")
                    
                    # Merge boundary chunks
                    merged_chunks = merge_continued_pages(
                        page_chunks, next_chunks, page_num, next_page_num,
                        config, stats, logger
                    )
                    
                    all_chunks.extend(merged_chunks)
                    processed_pages.add(idx + 1)  # Mark next page as processed
                    
                    logger.info(f"  After merge: {len(merged_chunks)} chunks")
                    stats['merged_boundaries'] += 1
                else:
                    logger.debug(f"  No continuation detected")
                    all_chunks.extend(page_chunks)
            else:
                # No merging or last page
                all_chunks.extend(page_chunks)
            
            logger.info("")
    
    # ========================================================================
    # STEP 5: CALCULATE STATISTICS
    # ========================================================================
    
    stats['total_chunks'] = len(all_chunks)
    
    with LogTimer(logger, "Calculating statistics"):
        detailed_stats = calculate_comprehensive_statistics(
            all_chunks, stats, config, logger
        )
    
    # ========================================================================
    # STEP 6: SAVE OUTPUT
    # ========================================================================
    
    with LogTimer(logger, "Saving output"):
        output_path = save_chunks_output(
            all_chunks, doc_name, config, detailed_stats, input_path, logger
        )
    
    # ========================================================================
    # STEP 7: LOG SUMMARY
    # ========================================================================
    
    _log_processing_summary(detailed_stats, logger)
    
    logger.info(f"\nOutput saved: {output_path}")
    log_section_header(logger, "PROCESSING COMPLETE")
    
    return {
        'document': doc_name,
        'total_pages': stats['total_pages'],
        'total_chunks': stats['total_chunks'],
        'output_path': str(output_path),
        'statistics': detailed_stats
    }


# ============================================================================
# PAGE PROCESSING
# ============================================================================

def _process_single_page(
    page_meta: Dict[str, Any],
    input_dir: Path,
    config: Dict[str, Any],
    stats: Dict[str, Any],
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Process a single page through the chunking pipeline.
    
    Pipeline for one page:
    1. Load markdown text
    2. Identify protected blocks
    3. Parse semantic sections
    4. Consolidate paragraphs
    5. Build chunks
    
    Parameters
    ----------
    page_meta : Dict[str, Any]
        Page metadata
    input_dir : Path
        Input directory
    config : Dict[str, Any]
        Configuration
    stats : Dict[str, Any]
        Statistics accumulator
    logger : logging.Logger
        Logger
    
    Returns
    -------
    List[Dict[str, Any]]
        Chunks created from this page
    """
    
    # Load page text
    file_name = page_meta.get('file_name') or page_meta.get('file')
    if not file_name:
        logger.warning("No file name in page metadata")
        return []
    
    page_path = input_dir / "pages" / file_name
    if not page_path.exists():
        logger.warning(f"Page file not found: {page_path}")
        return []
    
    with open(page_path, 'r', encoding='utf-8') as f:
        text = f.read()
        print(text)
    
    logger.debug(f"  Loaded {len(text)} characters from {file_name}")
    
    # Identify protected blocks
    protected_blocks = identify_protected_blocks(text, config, logger)

    # # Update statistics
    block_counts = count_protected_blocks_by_type(protected_blocks)
    for block_type, count in block_counts.items():
        stats['protected_blocks'][block_type] += count
    #
    # # Parse semantic sections
    sections = parse_semantic_sections(text, protected_blocks, config, logger)
    #
    # Consolidate paragraphs
    sections = consolidate_paragraphs(sections, config, logger)

    # Build chunks
    chunks = build_chunks_from_sections(sections, page_meta, config, stats, logger)

    return chunks


# ============================================================================
# SUMMARY LOGGING
# ============================================================================

def _log_processing_summary(stats: Dict[str, Any], logger: logging.Logger):
    """Log comprehensive processing summary."""
    
    log_section_header(logger, "PROCESSING SUMMARY")
    
    # Basic counts
    logger.info(f"Total Pages: {stats.get('total_pages', 0)}")
    logger.info(f"Total Chunks: {stats.get('total_chunks', 0)}")
    logger.info(f"Cross-Page Merges: {stats.get('merged_boundaries', 0)}")
    logger.info(f"Duplicates Prevented: {stats.get('duplicates_prevented', 0)}")
    logger.info(f"Validation Failures: {stats.get('validation_failures', 0)}")
    
    # Protected blocks
    protected = stats.get('protected_blocks', {})
    if any(protected.values()):
        logger.info("\nProtected Blocks:")
        for block_type, count in protected.items():
            if count > 0:
                logger.info(f"  {block_type}: {count}")
    
    # Size distribution
    size_dist = stats.get('size_distribution', {})
    if size_dist:
        logger.info("\nChunk Size Distribution:")
        logger.info(f"  Min: {size_dist.get('min', 0)} chars")
        logger.info(f"  Median: {size_dist.get('median', 0)} chars")
        logger.info(f"  Mean: {size_dist.get('mean', 0):.1f} chars")
        logger.info(f"  Max: {size_dist.get('max', 0)} chars")
    
    # Content analysis
    content = stats.get('content_analysis', {})
    if content:
        logger.info("\nContent Analysis:")
        logger.info(f"  Total Words: {content.get('total_words', 0):,}")
        logger.info(f"  Avg Words/Chunk: {content.get('avg_words_per_chunk', 0):.1f}")
        logger.info(f"  Chunks with Numbers: {content.get('chunks_with_numerical_data', 0)}")
        logger.info(f"  Chunks with Citations: {content.get('chunks_with_citations', 0)}")
    
    logger.info("")
