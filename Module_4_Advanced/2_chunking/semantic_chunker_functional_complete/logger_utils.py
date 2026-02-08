"""
Logging Utilities Module
=========================

EDUCATIONAL PURPOSE
-------------------
This module handles all logging configuration and utility functions.
Separating logging from business logic makes code cleaner and more testable.

WHY SEPARATE LOGGING?
---------------------
1. SINGLE RESPONSIBILITY: Logging logic isolated from chunking logic
2. REUSABILITY: Can use same logger across modules
3. TESTABILITY: Can mock/disable logging in tests
4. MAINTAINABILITY: Change logging behavior without touching business code

FUNCTIONAL APPROACH
-------------------
Instead of a Logger class, we use functions that create and configure loggers.
This avoids global state and makes it easy to create multiple logger instances.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


# ============================================================================
# LOGGER SETUP
# ============================================================================

def setup_logger(
    input_dir: Path,
    verbose: bool = True,
    name: str = "semantic_chunker"
) -> logging.Logger:
    """
    Create and configure a logger for the chunking system.
    
    DUAL LOGGING STRATEGY
    ----------------------
    We log to TWO destinations:
    
    1. FILE (always DEBUG level)
       - Captures every detail for debugging
       - Persists after program ends
       - Developers can review later
    
    2. CONSOLE (INFO or DEBUG based on verbose flag)
       - Shows progress to user
       - DEBUG if verbose=True (for development)
       - INFO if verbose=False (for production)
    
    WHY DUAL LOGGING?
    -----------------
    - Users want to see progress (console)
    - Developers need full details (file)
    - Same run produces both outputs
    
    FILE NAMING STRATEGY
    --------------------
    Format: chunking_YYYYMMDD_HHMMSS.log
    Example: chunking_20250205_143022.log
    
    Why timestamped?
    - Multiple runs don't overwrite
    - Easy to identify when processing occurred
    - Can compare logs from different runs
    
    Parameters
    ----------
    input_dir : Path
        Directory where log file will be created (in logs/ subdirectory)
    verbose : bool
        If True, console shows DEBUG messages
        If False, console shows only INFO messages
    name : str
        Logger name (for logger hierarchy)
    
    Returns
    -------
    logging.Logger
        Configured logger instance ready to use
    
    Example Usage
    -------------
    >>> logger = setup_logger(Path('/data/docs'), verbose=True)
    >>> logger.info("Processing started")
    >>> logger.debug("Found 5 protected blocks")
    >>> logger.warning("Chunk size exceeded maximum")
    """
    
    # Create logs directory if it doesn't exist
    log_dir = input_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"chunking_{timestamp}.log"
    
    # Create logger instance
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture everything at logger level
    
    # Remove any existing handlers (important for repeated calls)
    logger.handlers.clear()
    
    # ========================================================================
    # HANDLER 1: File Handler (detailed logs)
    # ========================================================================
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # File gets ALL messages
    
    # File formatter: Detailed with timestamp
    # Format: 2025-02-05 14:30:22 | INFO     | Processing page 5
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # ========================================================================
    # HANDLER 2: Console Handler (user-facing progress)
    # ========================================================================
    
    console_handler = logging.StreamHandler()
    
    # Set level based on verbose flag
    # verbose=True  → DEBUG level (shows everything)
    # verbose=False → INFO level (shows only important messages)
    console_level = logging.DEBUG if verbose else logging.INFO
    console_handler.setLevel(console_level)
    
    # Console formatter: Simple, no timestamp
    # Format: Processing page 5
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # ========================================================================
    # LOG THE SETUP
    # ========================================================================
    
    logger.info(f"Logging initialized: {log_file}")
    if verbose:
        logger.info("Verbose mode: DEBUG logs enabled on console")
    
    return logger


# ============================================================================
# LOGGING UTILITIES
# ============================================================================

def log_section_header(logger: logging.Logger, title: str):
    """
    Log a formatted section header for better readability.
    
    Example Output
    --------------
    ======================================================================
    PROCESSING COMPLETE
    ======================================================================
    
    Parameters
    ----------
    logger : logging.Logger
        Logger instance to use
    title : str
        Section title to display
    """
    separator = "=" * 70
    logger.info(f"\n{separator}")
    logger.info(title)
    logger.info(separator)


def log_dict_items(logger: logging.Logger, data: dict, indent: int = 0):
    """
    Log dictionary items in a readable format.
    
    Example Output
    --------------
    Size Distribution:
      min: 100
      max: 2500
      mean: 1500
    
    Parameters
    ----------
    logger : logging.Logger
        Logger instance to use
    data : dict
        Dictionary to log
    indent : int
        Number of spaces to indent (for nested structures)
    """
    indent_str = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            logger.info(f"{indent_str}{key}:")
            log_dict_items(logger, value, indent + 2)
        else:
            logger.info(f"{indent_str}{key}: {value}")


def log_progress(
    logger: logging.Logger,
    current: int,
    total: int,
    item_type: str = "items"
):
    """
    Log progress in a consistent format.
    
    Example Output
    --------------
    Processing page 5/23 (21.7%)
    
    Parameters
    ----------
    logger : logging.Logger
        Logger instance to use
    current : int
        Current item number (1-indexed)
    total : int
        Total number of items
    item_type : str
        Description of what's being processed (pages, chunks, etc.)
    """
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info(f"Processing {item_type} {current}/{total} ({percentage:.1f}%)")


# ============================================================================
# CONTEXT MANAGER FOR TIMED OPERATIONS
# ============================================================================

class LogTimer:
    """
    Context manager for timing and logging operations.
    
    Example Usage
    -------------
    >>> with LogTimer(logger, "parsing document"):
    ...     parse_document()
    Starting: parsing document
    Completed: parsing document (2.34 seconds)
    """
    
    def __init__(self, logger: logging.Logger, operation: str):
        """
        Parameters
        ----------
        logger : logging.Logger
            Logger instance
        operation : str
            Description of the operation being timed
        """
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        """Start timing"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log duration"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            # Success
            self.logger.info(
                f"Completed: {self.operation} ({duration:.2f} seconds)"
            )
        else:
            # Failure
            self.logger.error(
                f"Failed: {self.operation} ({duration:.2f} seconds)"
            )
        
        # Don't suppress exceptions
        return False


# ============================================================================
# SPECIALIZED LOGGING FUNCTIONS
# ============================================================================

def log_chunk_creation(
    logger: logging.Logger,
    chunk_id: str,
    chunk_type: str,
    size: int,
    page_num: int
):
    """
    Log chunk creation in a structured format.
    
    Parameters
    ----------
    logger : logging.Logger
        Logger instance
    chunk_id : str
        Unique chunk identifier (first 8 chars of MD5 hash)
    chunk_type : str
        Type of chunk (text, table, image, code)
    size : int
        Size of chunk in characters
    page_num : int
        Page number where chunk originated
    """
    logger.debug(
        f"Created {chunk_type} chunk {chunk_id[:8]}... "
        f"({size} chars) on page {page_num}"
    )


def log_validation_failure(
    logger: logging.Logger,
    chunk_id: str,
    reason: str
):
    """
    Log chunk validation failure with details.
    
    Parameters
    ----------
    logger : logging.Logger
        Logger instance
    chunk_id : str
        Chunk identifier that failed validation
    reason : str
        Reason for validation failure
    """
    logger.warning(
        f"Chunk validation failed: {chunk_id[:8]}... - {reason}"
    )


def log_merge_operation(
    logger: logging.Logger,
    page1: int,
    page2: int,
    chunk_count_before: int,
    chunk_count_after: int
):
    """
    Log cross-page merge operation details.
    
    Parameters
    ----------
    logger : logging.Logger
        Logger instance
    page1 : int
        First page number
    page2 : int
        Second page number
    chunk_count_before : int
        Number of chunks before merge
    chunk_count_after : int
        Number of chunks after merge
    """
    reduction = chunk_count_before - chunk_count_after
    logger.info(
        f"Merged pages {page1}-{page2}: "
        f"{chunk_count_before} → {chunk_count_after} chunks "
        f"(-{reduction})"
    )


def log_statistics_summary(logger: logging.Logger, stats: dict):
    """
    Log comprehensive statistics in a readable format.
    
    Parameters
    ----------
    logger : logging.Logger
        Logger instance
    stats : dict
        Statistics dictionary with all counters
    """
    log_section_header(logger, "PROCESSING SUMMARY")
    
    logger.info(f"Total Pages: {stats.get('total_pages', 0)}")
    logger.info(f"Total Chunks: {stats.get('total_chunks', 0)}")
    logger.info(f"Merged Boundaries: {stats.get('merged_boundaries', 0)}")
    logger.info(f"Duplicates Prevented: {stats.get('duplicates_prevented', 0)}")
    logger.info(f"Validation Failures: {stats.get('validation_failures', 0)}")
    
    # Protected blocks
    protected = stats.get('protected_blocks', {})
    if any(protected.values()):
        logger.info("\nProtected Blocks:")
        for block_type, count in protected.items():
            if count > 0:
                logger.info(f"  {block_type}: {count}")
    
    logger.info("")
