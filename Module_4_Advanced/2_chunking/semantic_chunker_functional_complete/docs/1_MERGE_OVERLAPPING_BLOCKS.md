# `_merge_overlapping_blocks()` - Complete Documentation

## 📋 Function Overview

```python
def _merge_overlapping_blocks(
    blocks: List[Tuple[int, int, str, str]],
    text: str,
    logger: logging.Logger
) -> List[Tuple[int, int, str, str]]
```

**Purpose**: Merge protected blocks that overlap in position to avoid duplicate or conflicting chunk boundaries.

**Module**: `protected_blocks.py`

**Called By**: `identify_protected_blocks()`

---

## 🎯 Why This Function Exists

### The Problem

When multiple regex patterns search a document, they can match **overlapping regions**:

```python
# Document text:
"""
**Complete Page Visual Analysis**
This page contains diagrams and tables.

**Image 1:** Architecture diagram
![](architecture.png)

**Table 1:** Performance metrics
| Metric | Value |
|--------|-------|
| Speed  | Fast  |
"""

# Pattern 1: Matches "Complete Page Visual Analysis" section
# Result: (0, 500, 'image', 'Complete Page Visual...')

# Pattern 2: Matches "Image 1" specifically  
# Result: (80, 200, 'image', '**Image 1:**...')

# Pattern 3: Matches the table
# Result: (250, 400, 'table', '| Metric | Value |...')
```

**Without merging**: We'd have 3 blocks, with Pattern 2 nested inside Pattern 1.

**With merging**: We intelligently combine overlapping blocks into coherent units.

---

## 📊 Algorithm Explanation

### High-Level Strategy

```
1. Start with empty merged list
2. For each block (already sorted by start position):
   a. If merged list is empty → add this block
   b. If this block doesn't overlap with last merged block → add as new
   c. If this block overlaps AND extends beyond → extend the last merged block
   d. If this block is fully contained → do nothing (already covered)
3. Return merged list
```

### Visual Algorithm Flow

```
Input: [(10,50), (30,70), (80,100)]
         |         |        |
         v         v        v
    ┌────────┬─────────┬────────┐
    │ Block1 │ Block2  │ Block3 │
    │(10-50) │ (30-70) │(80-100)│
    └────────┴─────────┴────────┘
         │         │        │
         │         └────────┼─── OVERLAP!
         │                  │
         v                  v
    Merge → (10-70)    Add → (80-100)
         │                  │
         └──────────────────┘
                │
                v
         Output: [(10-70), (80-100)]
```

---

## 🔍 Three Types of Overlap

### Type 1: No Overlap (Blocks Separate)

```python
# Visual:
#         prev              curr
# Pos:    |====|            |====|
#         10   50           80   100
#
# Condition: curr_start >= prev_end
# Example:   80 >= 50? YES
# Action:    Add curr as new block

blocks = [
    (10, 50, 'image', 'content_A'),
    (80, 100, 'table', 'content_B')
]

# Process:
merged = []
merged.append((10, 50, 'image', 'content_A'))  # First block

# Check second block:
curr_start = 80
prev_end = 50
if curr_start >= prev_end:  # 80 >= 50? YES!
    merged.append((80, 100, 'table', 'content_B'))

# Result: 2 separate blocks
merged = [(10, 50, 'image', '...'), (80, 100, 'table', '...')]
```

**Real-World Example**:

```python
text = """
**Image 1:** Logo
![](logo.png)

Some text between blocks.

| Name | Age |
|------|-----|
| Bob  | 25  |
"""

blocks = [
    (0, 50, 'image', '**Image 1:**\n![](logo.png)'),
    (100, 200, 'table', '| Name | Age |\n...')
]

# Gap of 50 chars between blocks (50-100)
# No merge needed: they're separate content
```

---

### Type 2: Partial Overlap (Current Extends Beyond Previous)

```python
# Visual:
#         prev              
# Pos:    |==========|      
#         10         50
#              curr
#              |==========|
#              30         70
#              ↑↑↑↑↑↑↑↑↑↑
#              OVERLAP!
#
# Condition: curr_start < prev_end AND curr_end > prev_end
# Example:   30 < 50 AND 70 > 50? YES
# Action:    Extend prev to (10, 70)

blocks = [
    (10, 50, 'image', 'content_A'),
    (30, 70, 'image', 'content_B')  # Overlaps with first!
]

# Process:
merged = []
merged.append((10, 50, 'image', 'content_A'))  # First block

# Check second block:
curr_start, curr_end = 30, 70
prev_start, prev_end = 10, 50

if curr_start >= prev_end:  # 30 >= 50? NO!
    # OVERLAP DETECTED!
    if curr_end > prev_end:  # 70 > 50? YES!
        # PARTIAL OVERLAP - Extend previous block
        merged[-1] = (
            prev_start,           # 10 (keep original start)
            curr_end,             # 70 (extend to new end)
            'image',              # Keep type
            text[prev_start:curr_end]  # Extract text[10:70]
        )

# Result: 1 merged block covering both regions
merged = [(10, 70, 'image', text[10:70])]
```

**Real-World Example**:

```python
text = """
**Complete Page Visual Analysis**
This page contains multiple diagrams.

**Image 1:** Architecture
![](architecture.png)
*AI Description:* The diagram shows...
"""

blocks = [
    (0, 100, 'image', '**Complete Page Visual Analysis**\n...'),
    (60, 150, 'image', '**Image 1:**\n...*AI Description:*...')
]

# Visual:
# Pos: 0    60   100  150
#      |====|====|====|
#      |=========|         Block 1 (0-100)
#           |=========|    Block 2 (60-150) - extends beyond!
#
# After merge: (0, 150) covering full content
```

---

### Type 3: Full Containment (Current Inside Previous)

```python
# Visual:
#         prev              
# Pos:    |==============|  
#         10             80
#              curr
#              |======|
#              30     50
#              ↑↑↑↑↑↑
#           CONTAINED!
#
# Condition: curr_start < prev_end AND curr_end <= prev_end
# Example:   30 < 80 AND 50 <= 80? YES
# Action:    Do nothing (implicit - no code branch)

blocks = [
    (10, 80, 'image', 'content_A'),  # Big container
    (30, 50, 'image', 'content_B')   # Inside first block
]

# Process:
merged = []
merged.append((10, 80, 'image', 'content_A'))  # First block

# Check second block:
curr_start, curr_end = 30, 50
prev_start, prev_end = 10, 80

if curr_start >= prev_end:  # 30 >= 80? NO!
    # OVERLAP DETECTED!
    if curr_end > prev_end:  # 50 > 80? NO!
        # FULL CONTAINMENT - do nothing
        # Code doesn't enter this branch
        # The block is already covered by previous

# Result: Only the container block
merged = [(10, 80, 'image', 'content_A')]
```

**Real-World Example**:

```python
text = """
**Images on this page:**

**Image 1:** Logo
![](logo.png)

**Image 2:** Chart  
![](chart.png)

**Image 3:** Diagram
![](diagram.png)
"""

blocks = [
    (0, 250, 'image', '**Images on this page:**\n... all 3 images'),
    (30, 80, 'image', '**Image 1:** Logo\n![](logo.png)'),
    (90, 140, 'image', '**Image 2:** Chart\n![](chart.png)'),
    (150, 200, 'image', '**Image 3:** Diagram\n![](diagram.png)')
]

# Visual:
# Pos: 0    30   80 90  140 150 200 250
#      |====|====|==|===|===|===|===|
#      |===========================|    Block 1 (0-250) - Container
#           |======|                    Block 2 (30-80) - INSIDE
#                  |=====|              Block 3 (90-140) - INSIDE  
#                      |=====|          Block 4 (150-200) - INSIDE
#
# After merge: Only (0, 250) - all others are contained
```

---

## 📝 Complete Code with Detailed Comments

```python
def _merge_overlapping_blocks(
    blocks: List[Tuple[int, int, str, str]],
    text: str,
    logger: logging.Logger
) -> List[Tuple[int, int, str, str]]:
    """
    Merge blocks that overlap in position.
    
    Parameters
    ----------
    blocks : List[Tuple[int, int, str, str]]
        Sorted blocks (by start position)
        Format: (start_pos, end_pos, type, content)
    text : str
        Original text (to extract merged content)
    logger : logging.Logger
        Logger for debug output
    
    Returns
    -------
    List[Tuple[int, int, str, str]]
        Blocks with overlaps merged
    """
    
    # =================================================================
    # EDGE CASE: Empty input
    # =================================================================
    if not blocks:
        return []
    
    # =================================================================
    # INITIALIZATION
    # =================================================================
    merged = []  # Output: Will contain merged blocks
    
    # =================================================================
    # MAIN LOOP: Process each block
    # =================================================================
    for block in blocks:
        # -------------------------------------------------------------
        # CASE 1: First block (nothing to compare with)
        # -------------------------------------------------------------
        if not merged:
            merged.append(block)
            continue
        
        # -------------------------------------------------------------
        # EXTRACT POSITIONS for comparison
        # -------------------------------------------------------------
        previous = merged[-1]  # Last block in merged list
        
        # Current block positions
        curr_start = block[0]
        curr_end = block[1]
        
        # Previous (last merged) block positions
        prev_start = previous[0]
        prev_end = previous[1]
        
        # -------------------------------------------------------------
        # CASE 2: No overlap (current starts at/after previous ends)
        # -------------------------------------------------------------
        # This means: previous ends BEFORE current starts
        # Visual: |prev|___gap___|curr|
        
        if curr_start >= prev_end:
            # No overlap - add as new block
            merged.append(block)
            continue
        
        # -------------------------------------------------------------
        # IF WE'RE HERE: OVERLAP DETECTED!
        # (curr_start < prev_end)
        # -------------------------------------------------------------
        
        # -------------------------------------------------------------
        # CASE 3: Partial overlap (current extends beyond previous)
        # -------------------------------------------------------------
        # Current block starts inside previous BUT ends after it
        # Visual: |====prev====|
        #              |====curr====|
        
        if curr_end > prev_end:
            # Log the merge operation
            logger.debug(
                f"    Merging blocks: ({prev_start}-{prev_end}) + "
                f"({curr_start}-{curr_end}) → ({prev_start}-{curr_end})"
            )
            
            # Extend the previous block
            merged[-1] = (
                prev_start,              # Keep original start
                curr_end,                # Extend to current's end
                previous[2],             # Keep outer block type
                text[prev_start:curr_end]  # Extract combined content from original text
            )
        
        # -------------------------------------------------------------
        # CASE 4: Full containment (implicit - no code needed)
        # -------------------------------------------------------------
        # Current block is completely inside previous block
        # Visual: |=====prev=====|
        #            |curr|
        #
        # This case is handled by NOT entering the if-block above
        # Since curr_end <= prev_end, we don't modify merged[-1]
        # The inner block is simply ignored (already covered)
    
    # =================================================================
    # RETURN merged blocks
    # =================================================================
    return merged
```

---

## 🎮 Step-by-Step Execution Examples

### Example 1: Three Blocks with Different Relationships

```python
# Input
text = "0123456789" * 20  # 200 characters
blocks = [
    (10, 50, 'image', 'A'),   # Block A
    (30, 70, 'image', 'B'),   # Block B - overlaps with A
    (90, 130, 'table', 'C')   # Block C - separate
]

# =================================================================
# EXECUTION TRACE
# =================================================================

merged = []

# -----------------------------------------------------------------
# ITERATION 1: Process block A (10, 50, 'image', 'A')
# -----------------------------------------------------------------
if not merged:  # True (merged is empty)
    merged.append((10, 50, 'image', 'A'))
    continue

# State after iteration 1:
# merged = [(10, 50, 'image', 'A')]

# -----------------------------------------------------------------
# ITERATION 2: Process block B (30, 70, 'image', 'B')
# -----------------------------------------------------------------
previous = merged[-1]  # (10, 50, 'image', 'A')

curr_start, curr_end = 30, 70
prev_start, prev_end = 10, 50

# Check: No overlap?
if curr_start >= prev_end:  # 30 >= 50? NO!
    # Don't execute this branch

# We're here, so overlap detected!

# Check: Partial overlap?
if curr_end > prev_end:  # 70 > 50? YES!
    # Extend previous block
    merged[-1] = (
        10,              # prev_start
        70,              # curr_end
        'image',         # Keep type
        text[10:70]      # Extract text from pos 10 to 70
    )

# State after iteration 2:
# merged = [(10, 70, 'image', text[10:70])]

# -----------------------------------------------------------------
# ITERATION 3: Process block C (90, 130, 'table', 'C')
# -----------------------------------------------------------------
previous = merged[-1]  # (10, 70, 'image', text[10:70])

curr_start, curr_end = 90, 130
prev_start, prev_end = 10, 70

# Check: No overlap?
if curr_start >= prev_end:  # 90 >= 70? YES!
    merged.append((90, 130, 'table', 'C'))
    continue

# State after iteration 3:
# merged = [(10, 70, 'image', text[10:70]), (90, 130, 'table', 'C')]

# =================================================================
# FINAL RESULT
# =================================================================
return merged  # 2 blocks: merged A+B, separate C
```

### Example 2: Nested Blocks (Full Containment)

```python
# Input
blocks = [
    (0, 200, 'image', 'Container'),  # Big container
    (30, 80, 'image', 'Inner1'),     # Inside container
    (90, 140, 'image', 'Inner2'),    # Inside container
    (250, 300, 'table', 'Separate')  # Separate block
]

# =================================================================
# EXECUTION TRACE
# =================================================================

merged = []

# -----------------------------------------------------------------
# ITERATION 1: Process container (0, 200)
# -----------------------------------------------------------------
merged.append((0, 200, 'image', 'Container'))
# merged = [(0, 200, 'image', 'Container')]

# -----------------------------------------------------------------
# ITERATION 2: Process Inner1 (30, 80)
# -----------------------------------------------------------------
previous = (0, 200, 'image', 'Container')

curr_start, curr_end = 30, 80
prev_start, prev_end = 0, 200

# Check: No overlap?
if curr_start >= prev_end:  # 30 >= 200? NO!
    # Overlap detected!

# Check: Partial overlap?
if curr_end > prev_end:  # 80 > 200? NO!
    # Don't extend - Inner1 is fully contained
    # Do nothing (implicit)

# merged = [(0, 200, 'image', 'Container')]  # Unchanged!

# -----------------------------------------------------------------
# ITERATION 3: Process Inner2 (90, 140)
# -----------------------------------------------------------------
previous = (0, 200, 'image', 'Container')

curr_start, curr_end = 90, 140
prev_start, prev_end = 0, 200

# Check: No overlap?
if curr_start >= prev_end:  # 90 >= 200? NO!
    # Overlap detected!

# Check: Partial overlap?
if curr_end > prev_end:  # 140 > 200? NO!
    # Don't extend - Inner2 is fully contained
    # Do nothing (implicit)

# merged = [(0, 200, 'image', 'Container')]  # Still unchanged!

# -----------------------------------------------------------------
# ITERATION 4: Process Separate (250, 300)
# -----------------------------------------------------------------
previous = (0, 200, 'image', 'Container')

curr_start, curr_end = 250, 300
prev_start, prev_end = 0, 200

# Check: No overlap?
if curr_start >= prev_end:  # 250 >= 200? YES!
    merged.append((250, 300, 'table', 'Separate'))

# merged = [(0, 200, 'image', 'Container'), (250, 300, 'table', 'Separate')]

# =================================================================
# FINAL RESULT
# =================================================================
return merged  # 2 blocks: Container (with inner blocks inside), Separate
```

---

## 🔑 Key Questions & Answers

### Q1: Why extract `text[prev_start:curr_end]` instead of using block content?

**Answer**: The regex match might have captured modified or incomplete content. We want the ACTUAL text from the original document.

```python
# Example:
block1_content = '**Image 1:**\n![](img.png)'  # From regex match
block2_content = 'another match'  # From different regex

# After merge, we want ACTUAL text:
merged_content = text[0:80]  # Actual document text from pos 0 to 80
# Not: block1_content + block2_content (could be incomplete/modified)
```

### Q2: Why keep `previous[2]` (the type)?

**Answer**: The outer (first) block type represents the broader context.

```python
outer = (0, 500, 'image', 'Complete Page Visual Analysis...')
inner = (100, 200, 'image', 'Image 1: specific image')

# After merge: Keep 'image' from outer
# Makes sense: The whole region is visual content
```

### Q3: Why only compare with `merged[-1]`?

**Answer**: Blocks are pre-sorted by start position. We only need to check the most recent merged block.

```python
# Can't have:
#   merged = [(10, 50), (100, 150)]
#   new = (30, 60)  ← Would overlap with first, not last
#
# Because blocks are sorted, (30, 60) would have been
# processed BEFORE (100, 150), so already merged
```

### Q4: What if two blocks are "touching" (end of one = start of next)?

**Answer**: They're considered separate (no overlap).

```python
block1 = (0, 50, 'image', '...')
block2 = (50, 100, 'table', '...')

# Check: curr_start >= prev_end?
# 50 >= 50? YES! → Add as separate block

# Result: 2 blocks
# They share position 50 but don't overlap
```

---

## 📊 Decision Tree

```
For each block in sorted blocks:
│
├─ Is merged list empty?
│  ├─ YES → Add block to merged
│  └─ NO → Continue to next check
│
├─ Does current start at/after previous end?
│  │  (curr_start >= prev_end)
│  │
│  ├─ YES → No overlap
│  │        Add block as new
│  │
│  └─ NO → Overlap detected!
│           Continue to next check
│
└─ Does current end after previous end?
   │  (curr_end > prev_end)
   │
   ├─ YES → Partial overlap
   │        Extend previous block:
   │        (prev_start, curr_end, type, text[prev_start:curr_end])
   │
   └─ NO → Full containment
            Do nothing (already covered)
```

---

## 🎯 Summary Table

| Scenario | Condition | Action | Example |
|----------|-----------|--------|---------|
| **Empty list** | `not merged` | Add block | First block always added |
| **No overlap** | `curr_start >= prev_end` | Add as new | Gap between blocks |
| **Touching** | `curr_start == prev_end` | Add as new | Adjacent blocks |
| **Partial overlap** | `curr_start < prev_end AND curr_end > prev_end` | Extend previous | Current extends beyond |
| **Full containment** | `curr_start < prev_end AND curr_end <= prev_end` | Do nothing | Current inside previous |

---

## 💡 Common Pitfalls & Solutions

### Pitfall 1: Forgetting blocks are sorted

```python
# ❌ WRONG: Thinking you need to check all previous blocks
for block in blocks:
    for prev in merged:  # Checking all is unnecessary!
        if overlaps(block, prev):
            merge()

# ✅ CORRECT: Only check the last merged block
for block in blocks:
    if overlaps(block, merged[-1]):
        merge()
```

### Pitfall 2: Not extracting from original text

```python
# ❌ WRONG: Using regex match content
merged[-1] = (start, end, type, block[3] + previous[3])

# ✅ CORRECT: Extract from original text
merged[-1] = (start, end, type, text[start:end])
```

### Pitfall 3: Modifying during iteration

```python
# ❌ WRONG: Modifying merged while iterating
for block in blocks:
    if overlaps:
        merged.pop()  # Dangerous!
        merged.append(new_block)

# ✅ CORRECT: Only modify merged[-1]
for block in blocks:
    if overlaps:
        merged[-1] = extended_block  # Safe!
```

---

**This function is crucial for preventing duplicate or conflicting chunk boundaries in the semantic chunking pipeline!**
