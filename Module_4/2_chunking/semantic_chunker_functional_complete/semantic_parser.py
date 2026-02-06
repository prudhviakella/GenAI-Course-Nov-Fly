"""
Semantic Parsing Module
========================

EDUCATIONAL PURPOSE
-------------------
This module parses markdown text into semantic sections - meaningful units
like headers, paragraphs, lists, tables, and images.

WHY SEMANTIC PARSING?
---------------------
Traditional chunking: "Read 1500 chars → chunk, repeat"
Problem: Splits mid-sentence, mid-paragraph, mid-table!

Semantic chunking: "Identify meaningful units → group intelligently"
Result: Chunks respect document structure and meaning

CORE CONCEPT
------------
A semantic section is a "thought unit" with inherent meaning:
- Header: Introduces a topic
- Paragraph: Explains a concept
- List: Enumerates items
- Table: Shows structured data

This module identifies these units so later functions can group them wisely.
"""

import re
import logging
from typing import List, Dict, Tuple, Any


# ============================================================================
# MAIN PARSING FUNCTION
# ============================================================================

def parse_semantic_sections(
    text: str,
    protected_blocks: List[Tuple[int, int, str, str]],
    config: Dict[str, Any],
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Parse markdown text into semantic sections.
    
    ALGORITHM STRATEGY
    ------------------
    Use CURSOR-BASED PARSER with STATE MACHINE logic.
    
    Cursor: Current position in text (character index)
    State: What we're parsing (list, paragraph, header, etc.)
    
    Flow:
        while not at end of text:
            if at protected block → emit block, jump past it
            elif at header → emit header, update breadcrumbs
            elif at list item → accumulate in buffer
            else → emit as text
    
    STATE MACHINE
    -------------
    START → read line
             |
             ├─ Protected block? → Emit → Continue
             ├─ Header? → Update breadcrumbs → Emit → Continue
             ├─ List item? → Accumulate → Continue
             └─ Text? → Emit → Continue
    
    Parameters
    ----------
    text : str
        Full markdown text of a page
    protected_blocks : List[Tuple[int, int, str, str]]
        Pre-identified atomic blocks (tables, images, code)
    config : Dict[str, Any]
        Configuration with regex patterns
    logger : logging.Logger
        Logger for debug output
    
    Returns
    -------
    List[Dict[str, Any]]
        Semantic sections with structure:
        {
            'type': 'text|major_header|minor_header|image|table|code',
            'content': 'actual content string',
            'breadcrumbs': ['Section', 'Subsection'],
            'start': 0,
            'end': 100
        }
    """
    
    logger.debug("  Parsing semantic sections...")
    
    sections = []
    cursor = 0
    current_breadcrumbs = []
    
    # List accumulation state
    in_list = False
    list_buffer = []
    list_start = 0
    
    # Get patterns from config
    header_pattern = config['patterns']['header']
    list_pattern = config['patterns']['list']
    
    # Import helper function
    from protected_blocks import get_block_at_position
    
    # ========================================================================
    # MAIN PARSING LOOP
    # ========================================================================
    
    while cursor < len(text):
        
        # ====================================================================
        # CHECK 1: Are we at a protected block?
        # ====================================================================
        
        block = get_block_at_position(protected_blocks, cursor)
        
        if block:
            # At start of protected block
            
            # Flush any accumulated list
            if list_buffer:
                sections.append({
                    'type': 'text',
                    'content': ''.join(list_buffer),
                    'breadcrumbs': current_breadcrumbs.copy(),
                    'start': list_start,
                    'end': cursor
                })
                list_buffer = []
                in_list = False
            
            # Extract block info
            start, end, block_type, content = block
            
            # Emit protected block
            sections.append({
                'type': block_type,
                'content': content,
                'breadcrumbs': current_breadcrumbs.copy(),
                'start': start,
                'end': end
            })
            
            # Jump cursor past block
            cursor = end
            continue
        
        # ====================================================================
        # CHECK 2: Read next line
        # ====================================================================
        
        line_end = text.find('\n', cursor)
        if line_end == -1:
            line_end = len(text)
        
        line = text[cursor:line_end + 1]
        line_stripped = line.strip()
        
        # ====================================================================
        # CHECK 3: Skip empty lines and comments
        # ====================================================================
        
        if not line_stripped or line_stripped.startswith('<!--'):
            cursor = line_end + 1
            continue
        
        # ====================================================================
        # CHECK 4: Is this a header?
        # ====================================================================
        
        header_match = header_pattern.match(line_stripped)
        
        if header_match:
            # Flush any accumulated list
            if list_buffer:
                sections.append({
                    'type': 'text',
                    'content': ''.join(list_buffer),
                    'breadcrumbs': current_breadcrumbs.copy(),
                    'start': list_start,
                    'end': cursor
                })
                list_buffer = []
                in_list = False
            
            # Extract header info
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            
            # Skip page headers
            if level == 1 and title.startswith("Page "):
                cursor = line_end + 1
                continue
            
            # Update breadcrumbs
            current_breadcrumbs = _update_breadcrumbs(
                current_breadcrumbs, level, title
            )
            
            # Classify header
            header_type = 'major_header' if level <= 2 else 'minor_header'
            
            # Emit header
            sections.append({
                'type': header_type,
                'content': title,
                'breadcrumbs': current_breadcrumbs.copy(),
                'start': cursor,
                'end': line_end + 1
            })
            
            cursor = line_end + 1
            continue
        
        # ====================================================================
        # CHECK 5: Is this a list item?
        # ====================================================================
        
        is_list_item = bool(list_pattern.match(line_stripped))
        
        if is_list_item:
            # Initialize list if first item
            if not in_list:
                list_start = cursor
                in_list = True
            
            # Accumulate
            list_buffer.append(line)
            cursor = line_end + 1
            continue
        
        # ====================================================================
        # CHECK 6: Regular text
        # ====================================================================
        
        # Flush list if we were in one
        if in_list and list_buffer:
            sections.append({
                'type': 'text',
                'content': ''.join(list_buffer),
                'breadcrumbs': current_breadcrumbs.copy(),
                'start': list_start,
                'end': cursor
            })
            list_buffer = []
            in_list = False
        
        # Emit text line
        sections.append({
            'type': 'text',
            'content': line,
            'breadcrumbs': current_breadcrumbs.copy(),
            'start': cursor,
            'end': line_end + 1
        })
        
        cursor = line_end + 1
    
    # ========================================================================
    # POST-LOOP: Flush any remaining list
    # ========================================================================
    
    if list_buffer:
        sections.append({
            'type': 'text',
            'content': ''.join(list_buffer),
            'breadcrumbs': current_breadcrumbs.copy(),
            'start': list_start,
            'end': cursor
        })
    
    logger.debug(f"    Parsed {len(sections)} sections")
    
    return sections


# ============================================================================
# BREADCRUMB MANAGEMENT
# ============================================================================

def _update_breadcrumbs(
    current_breadcrumbs: List[str],
    level: int,
    title: str
) -> List[str]:
    """
    Update breadcrumb path based on header level.
    
    BREADCRUMB HIERARCHY
    --------------------
    Think of breadcrumbs like a file path:
    ["Chapter 1", "Section A", "Part 1"]
     ^^^^^^^^^^   ^^^^^^^^^^   ^^^^^^^^^
     Level 1      Level 2      Level 3
    
    When we encounter a header, we update the appropriate level
    and discard deeper levels.
    
    Examples
    --------
    Initial: []
    See "# Chapter 1" (level=1)
        → ["Chapter 1"]
    
    See "## Section A" (level=2)
        → ["Chapter 1", "Section A"]
    
    See "### Part 1" (level=3)
        → ["Chapter 1", "Section A", "Part 1"]
    
    See "## Section B" (level=2)
        → ["Chapter 1", "Section B"]  (Part 1 discarded)
    
    Parameters
    ----------
    current_breadcrumbs : List[str]
        Current breadcrumb path
    level : int
        Header level (1-6)
    title : str
        Header title
    
    Returns
    -------
    List[str]
        Updated breadcrumb path
    """
    
    if level == 1:
        # H1: Top level, replace everything
        return [title]
    
    elif level == 2:
        # H2: Keep H1, replace rest
        return current_breadcrumbs[:1] + [title]
    
    elif level == 3:
        # H3: Keep H1 and H2, add H3
        return current_breadcrumbs[:2] + [title]
    
    else:
        # H4-H6: Keep first (level-1) elements, add new
        return current_breadcrumbs[:level-1] + [title]


# ============================================================================
# PARAGRAPH CONSOLIDATION
# ============================================================================

def consolidate_paragraphs(
    sections: List[Dict[str, Any]],
    config: Dict[str, Any],
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Group consecutive regular paragraphs together.
    
    THE PROBLEM
    -----------
    Line-by-line parsing creates many tiny sections:
    
    Without consolidation:
        Section 1: "Para 1" (40 chars)
        Section 2: "Para 2" (50 chars)
        Section 3: "Para 3" (35 chars)
    
    With consolidation:
        Section 1: "Para 1\n\nPara 2\n\nPara 3" (125 chars)
    
    This creates meaningful chunks with complete context.
    
    IMPORTANT
    ---------
    We do NOT consolidate:
    - Lists (already grouped by parse_semantic_sections)
    - Headers
    - Tables/Images/Code
    
    These have their own semantic structure.
    
    Parameters
    ----------
    sections : List[Dict[str, Any]]
        Sections from parse_semantic_sections
    config : Dict[str, Any]
        Configuration with patterns
    logger : logging.Logger
        Logger for debug output
    
    Returns
    -------
    List[Dict[str, Any]]
        Consolidated sections
    """
    
    logger.debug("  Consolidating paragraphs...")
    
    consolidated = []
    text_group = []
    text_breadcrumbs = []
    
    list_pattern = config['patterns']['list']
    
    for section in sections:
        # Check if this is a list
        is_list = (
            section['type'] == 'text' and
            list_pattern.match(section['content'].strip())
        )
        
        if section['type'] == 'text' and not is_list:
            # Regular paragraph - accumulate
            text_group.append(section['content'])
            text_breadcrumbs = section['breadcrumbs']
        else:
            # Non-paragraph - flush accumulated paragraphs
            if text_group:
                consolidated.append({
                    'type': 'text',
                    'content': '\n\n'.join(text_group),
                    'breadcrumbs': text_breadcrumbs,
                    'start': section.get('start', 0),
                    'end': section.get('end', 0)
                })
                text_group = []
            
            # Add non-paragraph section
            consolidated.append(section)
    
    # Flush remaining paragraphs
    if text_group:
        consolidated.append({
            'type': 'text',
            'content': '\n\n'.join(text_group),
            'breadcrumbs': text_breadcrumbs,
            'start': sections[-1].get('start', 0),
            'end': sections[-1].get('end', 0)
        })
    
    logger.debug(f"    After consolidation: {len(consolidated)} sections")
    
    return consolidated


# ============================================================================
# SECTION ANALYSIS
# ============================================================================

def analyze_sections(sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze section distribution and characteristics.
    
    Returns statistics useful for debugging and optimization.
    
    Parameters
    ----------
    sections : List[Dict[str, Any]]
        Sections to analyze
    
    Returns
    -------
    Dict[str, Any]
        Analysis results:
        - counts_by_type: Number of each section type
        - avg_size_by_type: Average size for each type
        - breadcrumb_depth_distribution: How deep breadcrumbs go
    """
    
    counts = {}
    sizes = {}
    depths = []
    
    for section in sections:
        section_type = section['type']
        size = len(section['content'])
        depth = len(section['breadcrumbs'])
        
        # Count by type
        counts[section_type] = counts.get(section_type, 0) + 1
        
        # Track sizes
        if section_type not in sizes:
            sizes[section_type] = []
        sizes[section_type].append(size)
        
        # Track depths
        depths.append(depth)
    
    # Calculate averages
    avg_sizes = {}
    for section_type, size_list in sizes.items():
        avg_sizes[section_type] = sum(size_list) / len(size_list)
    
    return {
        'counts_by_type': counts,
        'avg_size_by_type': avg_sizes,
        'breadcrumb_depths': {
            'min': min(depths) if depths else 0,
            'max': max(depths) if depths else 0,
            'avg': sum(depths) / len(depths) if depths else 0
        }
    }
