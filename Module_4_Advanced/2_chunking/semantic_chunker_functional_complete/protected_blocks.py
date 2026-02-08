"""
Protected Blocks Detection Module
==================================

EDUCATIONAL PURPOSE
-------------------
This module identifies "atomic" content blocks that must NEVER be split
during chunking: tables, images with descriptions, and code blocks.

WHY SEPARATE THIS MODULE?
--------------------------
1. COMPLEXITY: Protected block detection is complex with multiple patterns
2. REUSABILITY: Can be used by other document processing tools
3. TESTABILITY: Easy to test pattern matching in isolation
4. MAINTAINABILITY: All pattern logic in one place

CORE CONCEPT: ATOMIC BLOCKS
----------------------------
An atomic block is content that loses its meaning if split:
- Tables: Column headers must stay with data rows
- Images: Caption/description must stay with image reference
- Code: Syntax breaks if split mid-function

Example of BAD splitting:
    Chunk 1: | Name | Age |
             |------|-----|
    Chunk 2: | Alice | 30 |
    Result: Lost column-to-value mapping!

Example of GOOD atomic handling:
    Chunk 1: | Name | Age |
             |------|-----|
             | Alice | 30 |
             | Bob   | 25 |
    Result: Complete, usable table!
"""

import re
import logging
from typing import List, Tuple, Dict, Any


# ============================================================================
# BLOCK IDENTIFICATION
# ============================================================================

def identify_protected_blocks(
    text: str,
    config: Dict[str, Any],
    logger: logging.Logger
) -> List[Tuple[int, int, str, str]]:
    """
    Identify all protected blocks in text.
    
    ALGORITHM OVERVIEW
    ------------------
    1. Match image patterns → collect image blocks
    2. Match table pattern → collect table blocks
    3. Match code pattern → collect code blocks
    4. Sort all blocks by position
    5. Merge overlapping blocks
    
    WHY MERGE OVERLAPS?
    -------------------
    Multiple patterns can match overlapping regions.
    
    Example:
        Text: **Complete Page Visual Analysis**
              **Image 1:** Architecture
              ![](arch.png)
    
        Pattern 1 matches: (0, 200, 'image', full analysis)
        Pattern 2 matches: (50, 150, 'image', just Image 1)
    
        These overlap! We need ONE block (0, 200), not two.
    
    Parameters
    ----------
    text : str
        Full markdown text to analyze
    config : Dict[str, Any]
        Configuration with pattern definitions
    logger : logging.Logger
        Logger for debug output
    
    Returns
    -------
    List[Tuple[int, int, str, str]]
        Protected blocks as (start_pos, end_pos, type, content)
        Sorted by position with overlaps merged
    
    Example Return
    --------------
    [
        (120, 450, 'image', '**Image 1:**\n![](img.png)\n...'),
        (600, 850, 'table', '| A | B |\n|---|---|\n| 1 | 2 |'),
        (900, 1100, 'code', '```python\ncode\n```')
    ]
    """
    
    logger.debug("Identifying protected blocks...")
    
    blocks = []
    
    # ========================================================================
    # STEP 1: Find image blocks
    # ========================================================================
    
    image_patterns = config['image_patterns']
    
    for pattern in image_patterns:
        matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            blocks.append((
                match.start(),
                match.end(),
                "image",
                match.group(0)
            ))
    
    logger.debug(f"  Found {len([b for b in blocks if b[2] == 'image'])} image blocks")
    
    # ========================================================================
    # STEP 2: Find table blocks
    # ========================================================================
    
    table_pattern = config['table_pattern']
    matches = re.finditer(table_pattern, text, re.DOTALL)
    
    for match in matches:
        blocks.append((
            match.start(),
            match.end(),
            "table",
            match.group(0)
        ))
    
    logger.debug(f"  Found {len([b for b in blocks if b[2] == 'table'])} table blocks")
    
    # ========================================================================
    # STEP 3: Find code blocks
    # ========================================================================
    
    code_pattern = config['code_pattern']
    matches = re.finditer(code_pattern, text, re.DOTALL)
    
    for match in matches:
        blocks.append((
            match.start(),
            match.end(),
            "code",
            match.group(0)
        ))
    
    logger.debug(f"  Found {len([b for b in blocks if b[2] == 'code'])} code blocks")
    
    # ========================================================================
    # STEP 4: Sort by position
    # ========================================================================
    blocks = list(set(blocks))

    blocks.sort(key=lambda x: x[0])

    print(blocks)
    
    # ========================================================================
    # STEP 5: Merge overlapping blocks
    # ========================================================================
    
    merged = _merge_overlapping_blocks(blocks, text, logger)
    
    logger.debug(f"  After merging: {len(merged)} protected blocks")
    
    return merged


# ============================================================================
# OVERLAP MERGING
# ============================================================================

def _merge_overlapping_blocks(
    blocks: List[Tuple[int, int, str, str]],
    text: str,
    logger: logging.Logger
) -> List[Tuple[int, int, str, str]]:
    """
    Merge blocks that overlap in position.
    
    ALGORITHM
    ---------
    Process blocks sequentially, maintaining a "merged" list.
    For each block:
    - If it overlaps with last merged block → extend that block
    - If it doesn't overlap → add as new block
    
    OVERLAP TYPES
    -------------
    
    Type 1: No overlap (blocks separate)
        prev:  |====|
        curr:          |====|
        Action: Add curr as new block
    
    Type 2: Partial overlap (curr extends beyond prev)
        prev:  |==========|
        curr:       |==========|
        Action: Extend prev to cover both
    
    Type 3: Full containment (curr inside prev)
        prev:  |==============|
        curr:     |======|
        Action: Do nothing (already covered)
    
    Parameters
    ----------
    blocks : List[Tuple[int, int, str, str]]
        Sorted blocks (by start position)
    text : str
        Original text (to extract merged content)
    logger : logging.Logger
        Logger for debug output
    
    Returns
    -------
    List[Tuple[int, int, str, str]]
        Blocks with overlaps merged
    """
    
    if not blocks:
        return []
    
    merged = []
    
    for block in blocks:
        # First block - nothing to merge with
        if not merged:
            merged.append(block)
            continue
        
        previous = merged[-1]
        
        # Extract positions
        curr_start, curr_end = block[0], block[1]
        prev_start, prev_end = previous[0], previous[1]
        
        # Check for overlap
        # No overlap: current starts at or after previous ends
        if curr_start >= prev_end:
            merged.append(block)
            continue
        
        # Overlap detected
        # Partial overlap: current extends beyond previous
        if curr_end > prev_end:
            logger.debug(
                f"    Merging blocks: ({prev_start}-{prev_end}) + "
                f"({curr_start}-{curr_end}) → ({prev_start}-{curr_end})"
            )
            
            # Extend previous block
            merged[-1] = (
                prev_start,
                curr_end,
                previous[2],  # Keep outer block type
                text[prev_start:curr_end]  # Extract combined content
            )
        
        # Full containment: current inside previous
        # Do nothing - current block is already covered by previous
    
    return merged


# ============================================================================
# BLOCK POSITION CHECKING
# ============================================================================

def get_block_at_position(
    blocks: List[Tuple[int, int, str, str]],
    position: int
) -> Tuple[int, int, str, str] | None:
    """
    Check if cursor is at the START of a protected block.
    
    WHY ONLY CHECK START?
    ---------------------
    The parsing algorithm moves cursor through text sequentially.
    When cursor hits the start of a protected block, we need to:
    1. Emit the block as a single chunk
    2. Jump cursor to the end of the block
    3. Continue parsing after the block
    
    We only care about detecting the START because once we're inside
    a block, we've already jumped past it.
    
    Parameters
    ----------
    blocks : List[Tuple[int, int, str, str]]
        Protected blocks from identify_protected_blocks
    position : int
        Current cursor position in text
    
    Returns
    -------
    Tuple[int, int, str, str] | None
        The block at this position, or None if no block starts here

    """
    
    for block in blocks:
        if block[0] == position:  # block[0] is start position
            return block
    
    return None


# ============================================================================
# STATISTICS TRACKING
# ============================================================================

def count_protected_blocks_by_type(
    blocks: List[Tuple[int, int, str, str]]
) -> Dict[str, int]:
    """
    Count how many blocks of each type were found.
    
    Parameters
    ----------
    blocks : List[Tuple[int, int, str, str]]
        Protected blocks
    
    Returns
    -------
    Dict[str, int]
        Counts by type: {'image': 5, 'table': 3, 'code': 2}
    """
    
    counts = {'image': 0, 'table': 0, 'code': 0}
    
    for block in blocks:
        block_type = block[2]
        if block_type in counts:
            counts[block_type] += 1
    
    return counts


# ============================================================================
# VALIDATION
# ============================================================================

def validate_protected_blocks(
    blocks: List[Tuple[int, int, str, str]],
    text: str,
    logger: logging.Logger
) -> bool:
    """
    Validate that protected blocks are well-formed.
    
    CHECKS
    ------
    1. Positions are valid (within text bounds)
    2. Start < End for each block
    3. No overlaps remain after merging
    
    Parameters
    ----------
    blocks : List[Tuple[int, int, str, str]]
        Protected blocks to validate
    text : str
        Original text
    logger : logging.Logger
        Logger for warnings
    
    Returns
    -------
    bool
        True if all blocks are valid
    """
    
    text_len = len(text)
    
    for i, block in enumerate(blocks):
        start, end, block_type, content = block
        
        # Check 1: Valid positions
        if start < 0 or end > text_len:
            logger.warning(
                f"Block {i} has invalid positions: "
                f"start={start}, end={end}, text_len={text_len}"
            )
            return False
        
        # Check 2: Start < End
        if start >= end:
            logger.warning(
                f"Block {i} has start >= end: start={start}, end={end}"
            )
            return False
        
        # Check 3: No overlaps with next block
        if i < len(blocks) - 1:
            next_block = blocks[i + 1]
            next_start = next_block[0]
            
            if end > next_start:
                logger.warning(
                    f"Block {i} overlaps with block {i+1}: "
                    f"end={end}, next_start={next_start}"
                )
                return False
    
    return True


# ============================================================================
# DEBUGGING UTILITIES
# ============================================================================

def visualize_protected_blocks(
    text: str,
    blocks: List[Tuple[int, int, str, str]],
    context_chars: int = 50
) -> str:
    """
    Create a visualization of where protected blocks are in the text.
    
    Useful for debugging pattern matching issues.
    
    Parameters
    ----------
    text : str
        Original text
    blocks : List[Tuple[int, int, str, str]]
        Protected blocks
    context_chars : int
        How many characters of context to show
    
    Returns
    -------
    str
        Human-readable visualization
    
    Example Output
    --------------
    Protected Blocks Visualization:
    
    Block 1: image (100-200)
      Context: ...some text before **Image 1:** description text...
      Type: image
      Length: 100 chars
    
    Block 2: table (300-450)
      Context: ...text before | Header | Data |...
      Type: table
      Length: 150 chars
    """
    
    lines = ["Protected Blocks Visualization:", ""]
    
    for i, block in enumerate(blocks, 1):
        start, end, block_type, content = block
        
        # Extract context
        context_start = max(0, start - context_chars)
        context_end = min(len(text), end + context_chars)
        context = text[context_start:context_end]
        
        # Show ellipsis if truncated
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."
        
        # Format
        lines.append(f"Block {i}: {block_type} ({start}-{end})")
        lines.append(f"  Context: {context[:100]}...")
        lines.append(f"  Type: {block_type}")
        lines.append(f"  Length: {end - start} chars")
        lines.append("")
    
    return "\n".join(lines)
