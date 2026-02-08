"""
Continuation Detection Module
==============================

EDUCATIONAL PURPOSE
-------------------
This module detects when content continues across PDF page boundaries,
which is crucial for preventing broken chunks.

THE PROBLEM
-----------
PDFs are paginated, but semantic content isn't:

    Page 5 ends:   "The system architecture relies on three core"
    Page 6 starts: "components: ingestion, processing, and storage."

Without detection: Two broken, meaningless chunks
With detection: One complete, useful chunk

DETECTION STRATEGY
------------------
We look for SIGNALS that indicate continuation:

1. SYNTACTIC SIGNALS
   - Incomplete sentences (no terminal punctuation)
   - Ends with conjunction words (and, or, but, the, a, of)

2. STRUCTURAL SIGNALS
   - List continuation (next page starts with bullet/number)
   - Table continuation (pipes at end and start)
   - Header without content (next page has the content)

3. SEMANTIC SIGNALS  
   - Numbered lists continuing across pages
   - Table rows spanning pages

This module identifies these signals so the merging module can act.
"""

import re
import logging
from typing import Dict, Any, List
from pathlib import Path


# ============================================================================
# MAIN CONTINUATION DETECTION
# ============================================================================

def detect_page_continuation(
    current_page: Dict[str, Any],
    next_page: Dict[str, Any],
    input_dir: Path,
    config: Dict[str, Any],
    stats: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Detect if content continues from current page to next page.
    
    ALGORITHM
    ---------
    1. Load text from both pages
    2. Extract boundaries (last 200 chars of current, first 200 of next)
    3. Check for continuation signals
    4. Return True if ANY signal detected
    
    WHY 200 CHARACTERS?
    -------------------
    - Large enough to capture context (2-3 sentences)
    - Small enough to be efficient
    - Empirically tested sweet spot
    
    Parameters
    ----------
    current_page : Dict[str, Any]
        Current page metadata
    next_page : Dict[str, Any]
        Next page metadata
    input_dir : Path
        Directory containing page files
    config : Dict[str, Any]
        Configuration with detection rules
    stats : Dict[str, Any]
        Statistics accumulator
    logger : logging.Logger
        Logger for debug output
    
    Returns
    -------
    bool
        True if continuation detected, False otherwise
    """
    
    if not next_page:
        return False
    
    # Load page texts
    curr_text = _load_page_text(current_page, input_dir, logger)
    next_text = _load_page_text(next_page, input_dir, logger)
    
    if not curr_text or not next_text:
        return False
    
    # Extract boundaries
    curr_end = curr_text[-200:].strip()
    next_start = next_text[:200].strip()
    
    logger.debug(f"    Checking continuation signals...")
    logger.debug(f"      Current ends: ...{curr_end[-50:]}")
    logger.debug(f"      Next starts: {next_start[:50]}...")
    
    # ========================================================================
    # SIGNAL 1: Ends with conjunction word
    # ========================================================================
    
    conjunction_signal = _check_conjunction_ending(
        curr_end, config, stats, logger
    )
    
    # ========================================================================
    # SIGNAL 2: No terminal punctuation
    # ========================================================================
    
    punctuation_signal = _check_terminal_punctuation(
        curr_end, config, stats, logger
    )
    
    # ========================================================================
    # SIGNAL 3: Numbered list continuation
    # ========================================================================
    
    numbered_list_signal = _check_numbered_list_continuation(
        next_start, stats, logger
    )
    
    # ========================================================================
    # SIGNAL 4: Bullet list continuation
    # ========================================================================
    
    bullet_list_signal = _check_bullet_list_continuation(
        next_start, stats, logger
    )
    
    # ========================================================================
    # SIGNAL 5: Table continuation
    # ========================================================================
    
    table_signal = _check_table_continuation(
        curr_end, next_start, stats, logger
    )
    
    # ========================================================================
    # SIGNAL 6: Header without content
    # ========================================================================
    
    header_signal = _check_header_continuation(
        curr_end, stats, logger
    )
    
    # ========================================================================
    # DECISION: Any signal = continuation
    # ========================================================================
    
    signals = [
        conjunction_signal,
        punctuation_signal,
        numbered_list_signal,
        bullet_list_signal,
        table_signal,
        header_signal
    ]
    
    detected = any(signals)
    
    if detected:
        logger.debug(f"    ✓ Continuation detected")
        signal_names = []
        if conjunction_signal:
            signal_names.append("conjunction")
        if punctuation_signal:
            signal_names.append("no_punctuation")
        if numbered_list_signal:
            signal_names.append("numbered_list")
        if bullet_list_signal:
            signal_names.append("bullet_list")
        if table_signal:
            signal_names.append("table")
        if header_signal:
            signal_names.append("header")
        
        logger.debug(f"    Signals: {', '.join(signal_names)}")
    else:
        logger.debug(f"    ✗ No continuation detected")
    
    return detected


# ============================================================================
# SIGNAL DETECTORS
# ============================================================================

def _check_conjunction_ending(
    text_end: str,
    config: Dict[str, Any],
    stats: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Check if text ends with a conjunction word.
    
    Example:
        "The system relies on three components: data, processing, and"
        
    This is VERY likely to continue on next page!
    """
    
    continuation_words = config['continuation_words']
    
    for word in continuation_words:
        if text_end.lower().endswith(word):
            stats['continuation_signals'].append('conjunction')
            logger.debug(f"      Signal: Ends with conjunction '{word}'")
            return True
    
    return False


def _check_terminal_punctuation(
    text_end: str,
    config: Dict[str, Any],
    stats: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Check if text lacks terminal punctuation.
    
    Terminal punctuation: . ! ? : ---
    
    If missing, sentence likely continues.
    """
    
    terminal_punctuation = config['terminal_punctuation']
    
    has_terminal = text_end.endswith(terminal_punctuation)
    
    if not has_terminal:
        stats['continuation_signals'].append('no_punctuation')
        logger.debug(f"      Signal: No terminal punctuation")
        return True
    
    return False


def _check_numbered_list_continuation(
    next_start: str,
    stats: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Check if next page starts with numbered list item.
    
    Pattern: "1. Item", "2. Item", "10. Item"
    
    Indicates list continuation.
    """
    
    if re.match(r'^\d+\.', next_start):
        stats['continuation_signals'].append('numbered_list')
        logger.debug(f"      Signal: Next page starts with numbered list")
        return True
    
    return False


def _check_bullet_list_continuation(
    next_start: str,
    stats: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Check if next page starts with bullet list item.
    
    Pattern: "- Item", "* Item", "+ Item"
    
    Indicates list continuation.
    """
    
    if re.match(r'^[-*+]', next_start):
        stats['continuation_signals'].append('bullet_list')
        logger.debug(f"      Signal: Next page starts with bullet list")
        return True
    
    return False


def _check_table_continuation(
    curr_end: str,
    next_start: str,
    stats: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Check if table continues across pages.
    
    Pattern:
        Current ends with: | col1 | col2 |
        Next starts with:  | val1 | val2 |
    
    Table rows spanning pages.
    """
    
    table_continues = (
        bool(re.search(r'\|.*\|$', curr_end)) and
        bool(re.match(r'^\|', next_start))
    )
    
    if table_continues:
        stats['continuation_signals'].append('table')
        logger.debug(f"      Signal: Table continuation detected")
        return True
    
    return False


def _check_header_continuation(
    curr_end: str,
    stats: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Check if page ends with header (content likely on next page).
    
    Pattern: "## Section Title" at end of page
    
    Content for this section is probably on next page.
    """
    
    if re.search(r'#{1,6}\s+.+$', curr_end):
        stats['continuation_signals'].append('header')
        logger.debug(f"      Signal: Ends with header")
        return True
    
    return False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _load_page_text(
    page_meta: Dict[str, Any],
    input_dir: Path,
    logger: logging.Logger
) -> str | None:
    """
    Load text content from page file.
    
    Parameters
    ----------
    page_meta : Dict[str, Any]
        Page metadata with file_name
    input_dir : Path
        Input directory
    logger : logging.Logger
        Logger
    
    Returns
    -------
    str | None
        Page text content, or None if file not found
    """
    
    file_name = page_meta.get('file_name') or page_meta.get('file')
    if not file_name:
        logger.warning("No file name in page metadata")
        return None
    
    page_path = input_dir / "pages" / file_name
    
    if not page_path.exists():
        logger.warning(f"Page file not found: {page_path}")
        return None
    
    try:
        with open(page_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading page file: {e}")
        return None


# ============================================================================
# STATISTICS ANALYSIS
# ============================================================================

def analyze_continuation_signals(stats: Dict[str, Any]) -> Dict[str, int]:
    """
    Analyze which continuation signals were most common.
    
    Useful for understanding document structure and improving detection.
    
    Parameters
    ----------
    stats : Dict[str, Any]
        Statistics with continuation_signals list
    
    Returns
    -------
    Dict[str, int]
        Signal counts: {'conjunction': 5, 'numbered_list': 3, ...}
    """
    
    signals = stats.get('continuation_signals', [])
    
    counts = {}
    for signal in signals:
        counts[signal] = counts.get(signal, 0) + 1
    
    return counts
