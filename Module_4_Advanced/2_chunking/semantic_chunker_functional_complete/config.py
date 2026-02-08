"""
Configuration and Constants Module
===================================

EDUCATIONAL PURPOSE
-------------------
This module centralizes all configuration parameters and constants used across
the chunking system. This follows the "Single Source of Truth" principle.

WHY SEPARATE CONFIGURATION?
---------------------------
1. MAINTAINABILITY: Change parameters in one place
2. TESTABILITY: Easy to create test configurations
3. DOCUMENTATION: All settings explained in one location
4. VALIDATION: Can validate config before processing starts

ARCHITECTURE DECISION
---------------------
We use a dictionary-based approach instead of a Config class to maintain
the functional programming paradigm throughout the codebase.
"""

import re
from typing import Dict, Any


# ============================================================================
# DEFAULT CHUNKING PARAMETERS
# ============================================================================

DEFAULT_TARGET_SIZE = 1500
"""
Target chunk size in characters.

WHY 1500?
- Embedding models: ~300-400 tokens (optimal for most models)
- Semantic completeness: Contains 3-5 complete paragraphs
- Retrieval balance: Precision vs recall tradeoff
- Real-world testing: Best RAG quality at this size
"""

DEFAULT_MIN_SIZE = 800
"""
Minimum acceptable chunk size in characters.

WHY 800?
- Prevents fragment chunks (headers, captions alone)
- Ensures sufficient context (~150-200 tokens)
- Allows flexibility at section boundaries
"""

DEFAULT_MAX_SIZE = 2500
"""
Maximum acceptable chunk size in characters.

WHY 2500?
- Embedding model limits: ~500-600 tokens (within limits)
- Cognitive load: Human-readable chunk size
- Vector DB performance: Optimal search speed
- Forces splitting at sentence boundaries
"""

DEFAULT_ENABLE_MERGING = True
"""
Whether to merge chunks across page boundaries.

WHY TRUE BY DEFAULT?
- PDFs don't respect semantic boundaries
- Prevents broken sentences at page breaks
- Creates more coherent chunks
"""


# ============================================================================
# COMPILED REGEX PATTERNS
# ============================================================================
# Compiled once for performance - used throughout the system

PATTERNS = {
    # Markdown headers: # Title, ## Section, ### Subsection
    'header': re.compile(r'^(#{1,6})\s+(.+)'),
    
    # List items: - item, * item, + item, 1. item
    'list': re.compile(r'^[-*+]|\d+\.'),
    
    # Sentence boundaries: periods, exclamation, question marks
    'sentence': re.compile(r'(?<=[.!?])\s+'),
    
    # Exhibits/Figures: "Exhibit 7:", "Figure 1:", "Table 3:"
    'exhibit': re.compile(r'(?:Exhibit|Figure|Table)\s+\d+:', re.IGNORECASE),
    
    # Source attribution: "Source: Bloomberg Terminal"
    'source': re.compile(r'Source:\s*(.+?)(?:\n|$)'),
    
    # Dates: "Jan 15, 2024", "February 5, 2025"
    'date': re.compile(
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b'
    ),
    
    # Numbers: Any digit sequence
    'number': re.compile(r'\d+'),
    
    # Named entities: Capitalized words (simple heuristic)
    'entity': re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'),
}


# ============================================================================
# PROTECTED BLOCK PATTERNS
# ============================================================================
# These patterns identify content that must NEVER be split

IMAGE_PATTERNS = [
    # Pattern 1: Blockquote sections with $$$$$ boundaries
    r">\$\$\$\$\$.*?\$\$\$\$\$",

    # Pattern 2: More specific - Visual Element with $$$$$ boundaries
    r">\$\$\$\$\$\s*\n\s*\*\*Visual Element\*\*.*?\$\$\$\$\$",

    # Pattern 3: More specific - Table/Chart with $$$$$ boundaries
    r">\$\$\$\$\$\s*\n\s*\*\*Table/Chart\*\*.*?\$\$\$\$\$",

    # Pattern 4: Batch image section "**Images on this page:**"
    r"\*\*Images? on this page:?\*\*.*?(?=\n#{1,3}\s|\n---|\Z)",

    # Pattern 5: Individual images "**Image 1:**"
    r"\*\*Image \d+:?\*\*.*?(?:\*AI Description:\*.*?)?(?=\n\*\*Image|\n#{1,3}\s|\n---|\Z)",

    # Pattern 6: Visual content section (non-blockquote)
    r"\*\*Visual Content.*?\*\*.*?(?=\n#{1,3}\s|\n---|\Z)",

    # Pattern 7: Complete visual analysis
    r"\*\*Complete Page Visual Analysis.*?\*\*.*?(?=\n#{1,3}\s|\n---|\Z)",

    # Pattern 8: Blockquote figures without $$$$$ markers
    r"> \*\*Figure \d+.*?(?=\n\n(?!>)|\Z)",
]

TABLE_PATTERN = (
    # Header row: | Col1 | Col2 |
    r"\n(\|[^\n]+\|\n)"
    # Separator: |------|------|
    r"(\|[-:\s|]+\|\n)"
    # Data rows (one or more)
    r"((?:\|[^\n]+\|\n)+)"
    # Optional caption: **Table 1:** Description
    r"(?:\n\*\*Table.*?(?=\n\n|\n#{1,3}\s|\Z))?"
    # Optional summary: **Table 1 Summary:** Analysis
    r"(?:\n\*\*Table \d+ Summary:?\*\*.*?(?=\n\n|\n#{1,3}\s|\n\*\*Table|\n\*\*Image|\Z))?"
)

CODE_PATTERN = r"```.*?```"


# ============================================================================
# CONTINUATION DETECTION SIGNALS
# ============================================================================

CONTINUATION_WORDS = [
    'and', 'or', 'but', 'the', 'a', 'an', 'of', 'to', 'in', 
    'with', 'for', 'on', 'at', 'by', 'from'
]
"""
Words that typically indicate sentence continuation.
If a page ends with these words, it likely continues on the next page.
"""

TERMINAL_PUNCTUATION = ('.', '!', '?', ':', '---')
"""
Punctuation that typically ends a complete thought.
If missing at page end, content likely continues.
"""


# ============================================================================
# STATISTICS TRACKING TEMPLATE
# ============================================================================

def create_stats_dict() -> Dict[str, Any]:
    """
    Create a fresh statistics tracking dictionary.
    
    This function replaces the instance variable approach from OOP.
    Each processing run gets its own stats dictionary.
    
    Returns
    -------
    Dict[str, Any]
        Empty statistics dictionary with all counters initialized to 0
    """
    return {
        'total_pages': 0,
        'total_chunks': 0,
        'merged_boundaries': 0,
        'duplicates_prevented': 0,
        'validation_failures': 0,
        'protected_blocks': {
            'image': 0,
            'table': 0,
            'code': 0
        },
        'continuation_signals': []
    }


# ============================================================================
# CONFIGURATION BUILDER
# ============================================================================

def create_config(
    target_size: int = DEFAULT_TARGET_SIZE,
    min_size: int = DEFAULT_MIN_SIZE,
    max_size: int = DEFAULT_MAX_SIZE,
    enable_merging: bool = DEFAULT_ENABLE_MERGING,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Create a configuration dictionary with validation.
    
    FUNCTIONAL APPROACH
    -------------------
    Instead of a Config class with methods, we use a simple dictionary.
    This makes the config:
    - Immutable (can freeze if needed)
    - Serializable (can save/load as JSON)
    - Easy to pass around
    - No hidden state
    
    Parameters
    ----------
    target_size : int
        Desired chunk size in characters
    min_size : int
        Minimum acceptable chunk size
    max_size : int
        Maximum acceptable chunk size
    enable_merging : bool
        Whether to merge across page boundaries
    verbose : bool
        Enable verbose DEBUG logging
    
    Returns
    -------
    Dict[str, Any]
        Validated configuration dictionary
    
    Raises
    ------
    ValueError
        If configuration parameters are invalid
    """
    # Validation
    if min_size <= 0:
        raise ValueError(f"min_size must be positive, got {min_size}")
    
    if target_size < min_size:
        raise ValueError(
            f"target_size ({target_size}) must be >= min_size ({min_size})"
        )
    
    if max_size < target_size:
        raise ValueError(
            f"max_size ({max_size}) must be >= target_size ({target_size})"
        )
    
    return {
        'target_size': target_size,
        'min_size': min_size,
        'max_size': max_size,
        'enable_merging': enable_merging,
        'verbose': verbose,
        
        # Include compiled patterns
        'patterns': PATTERNS,
        
        # Include protected block patterns
        'image_patterns': IMAGE_PATTERNS,
        'table_pattern': TABLE_PATTERN,
        'code_pattern': CODE_PATTERN,
        
        # Include continuation detection data
        'continuation_words': CONTINUATION_WORDS,
        'terminal_punctuation': TERMINAL_PUNCTUATION,
    }


# ============================================================================
# CONFIGURATION DISPLAY
# ============================================================================

def config_to_string(config: Dict[str, Any]) -> str:
    """
    Format configuration as readable string for logging.
    
    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary
    
    Returns
    -------
    str
        Formatted configuration string
    """
    lines = [
        "=" * 70,
        "CHUNKING CONFIGURATION",
        "=" * 70,
        f"Target Size: {config['target_size']} characters",
        f"Min Size: {config['min_size']} characters",
        f"Max Size: {config['max_size']} characters",
        f"Cross-Page Merging: {'Enabled' if config['enable_merging'] else 'Disabled'}",
        f"Verbose Logging: {'Enabled' if config['verbose'] else 'Disabled'}",
        "=" * 70,
    ]
    return "\n".join(lines)
