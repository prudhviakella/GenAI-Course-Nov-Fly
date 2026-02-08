# `parse_semantic_sections()` - Complete Documentation

## 📋 Function Overview

```python
def parse_semantic_sections(
    text: str,
    protected_blocks: List[Tuple[int, int, str, str]],
    config: Dict[str, Any],
    logger: logging.Logger
) -> List[Dict[str, Any]]
```

**Purpose**: Parse markdown text into semantic sections - meaningful units like headers, paragraphs, lists, tables, and images.

**Module**: `semantic_parser.py`

**Called By**: `_process_single_page()` in `orchestrator.py`

**Returns**: List of semantic sections with type, content, breadcrumbs, and position

---

## 🎯 Why This Function Exists

### The Problem with Character-Based Chunking

```python
# ❌ BAD: Character-based chunking (naive approach)
text = "The system has three components: data, processing, and storage..."
chunk1 = text[0:50]   # "The system has three components: data, proce"
chunk2 = text[50:100] # "ssing, and storage. Each component has..."

# Result: Broken mid-word! Meaningless chunks!
```

### The Solution: Semantic Parsing

```python
# ✅ GOOD: Parse into semantic units first
sections = [
    {'type': 'major_header', 'content': 'System Architecture'},
    {'type': 'text', 'content': 'The system has three components...'},
    {'type': 'text', 'content': '- Data ingestion\n- Processing\n- Storage'},
    {'type': 'table', 'content': '| Component | Status |\n...'}
]

# Then chunk these semantic units intelligently
```

### What is a "Semantic Section"?

A semantic section is a **thought unit** with inherent meaning:

| Type | What It Is | Example |
|------|-----------|---------|
| **Header** | Introduces a topic | `# Introduction`, `## Methods` |
| **Paragraph** | Explains a concept | A complete sentence or group of sentences |
| **List** | Enumerates items | Bullet points or numbered items |
| **Table** | Shows structured data | Markdown table with rows |
| **Image** | Visual content | Image reference with description |
| **Code** | Code block | Fenced code block |

---

## 🏗️ Algorithm Architecture

### High-Level Strategy

```
CURSOR-BASED STATE MACHINE

Initialize: cursor = 0, breadcrumbs = [], sections = []

WHILE cursor < text length:
    ├─ At protected block? → Emit block, jump past it
    ├─ At header? → Update breadcrumbs, emit header
    ├─ At list item? → Accumulate in buffer
    └─ Regular text? → Flush list if needed, emit text

Return: sections
```

### Visual Flow Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    START PARSING                         │
│              cursor=0, sections=[], list_buffer=[]       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────────┐
            │ Read Current Line  │
            └────────┬───────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌────────┐  ┌────────┐  ┌────────┐
   │Protected│  │ Header │  │  List  │
   │ Block? │  │   ?    │  │  Item? │
   └───┬────┘  └───┬────┘  └───┬────┘
       │           │            │
       ▼           ▼            ▼
   Emit & Jump  Update      Accumulate
   Past Block   Breadcrumbs  in Buffer
       │           │            │
       └───────────┴────────────┘
                   │
                   ▼
          ┌────────────────┐
          │ Move to Next   │
          │ Line (cursor++)│
          └────────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │ End of text? │
            └──┬────────┬──┘
          NO  │        │ YES
              │        │
              ▼        ▼
           LOOP     RETURN
           BACK     sections
```

---

## 🔍 Core Components Explained

### Component 1: The Cursor

```python
cursor = 0  # Current position in text (character index)

# Think of it like a reading head on a tape:
# text = "Hello World"
#         ^
#         cursor=0 (points to 'H')

# After reading "Hello":
# text = "Hello World"
#              ^
#              cursor=5 (points to ' ')
```

**Purpose**: Track where we are in the document as we parse line by line.

### Component 2: Breadcrumbs

```python
current_breadcrumbs = []  # Hierarchical context path

# Example evolution as we parse:
# []                                    # Starting state
# ["Introduction"]                      # After "# Introduction"
# ["Introduction", "Overview"]          # After "## Overview"
# ["Introduction", "Overview", "Goals"] # After "### Goals"
# ["Introduction", "Methods"]           # After "## Methods" (Goals dropped)
```

**Purpose**: Track hierarchical context to preserve document structure.

**Breadcrumb Rules**:
```python
# H1: Replace entire breadcrumb
"# Chapter 1" → ["Chapter 1"]

# H2: Keep H1, replace rest
"## Section A" → ["Chapter 1", "Section A"]

# H3: Keep H1+H2, add H3
"### Part 1" → ["Chapter 1", "Section A", "Part 1"]

# Back to H2: Keep H1, replace from H2 (drop H3)
"## Section B" → ["Chapter 1", "Section B"]
```

### Component 3: List Buffer

```python
in_list = False       # Are we currently inside a list?
list_buffer = []      # Accumulates consecutive list items
list_start = 0        # Where did the list start?

# Example accumulation:
# Line 1: "- Item 1" → in_list=True, buffer=["- Item 1\n"]
# Line 2: "- Item 2" → buffer=["- Item 1\n", "- Item 2\n"]
# Line 3: "Paragraph" → Flush buffer, in_list=False
```

**Purpose**: Keep multi-line lists together as ONE semantic unit.

**Why This Matters**:
```python
# ❌ WITHOUT list buffer: 3 separate sections
sections = [
    {'type': 'text', 'content': '- Item 1'},
    {'type': 'text', 'content': '- Item 2'},
    {'type': 'text', 'content': '- Item 3'}
]

# ✅ WITH list buffer: 1 coherent section
sections = [
    {'type': 'text', 'content': '- Item 1\n- Item 2\n- Item 3'}
]
```

### Component 4: Protected Blocks

```python
protected_blocks = [
    (100, 200, 'image', '**Image 1:**\n![](img.png)'),
    (300, 450, 'table', '| Col1 | Col2 |\n...')
]

# Pre-identified regions that must NEVER be split
# Format: (start_pos, end_pos, type, content)
```

**Purpose**: Identify atomic content that parsing should treat as single units.

---

## 📝 Complete Walkthrough with Example

### Input Document

```markdown
# Introduction

This document explains the system architecture.

## Components

The system has three main components:

- Data ingestion
- Processing engine  
- Storage layer

### Processing Details

**Image 1: Flow Diagram**
![](flow.png)

The processing happens in stages.
```

### Step-by-Step Parsing

```python
# =================================================================
# INITIALIZATION
# =================================================================
text = """# Introduction\n\nThis document..."""  # (full text above)
protected_blocks = [(120, 180, 'image', '**Image 1:**\n![](flow.png)')]
cursor = 0
current_breadcrumbs = []
sections = []
in_list = False
list_buffer = []

# =================================================================
# ITERATION 1: Line "# Introduction"
# =================================================================

# Read line
line = "# Introduction\n"
line_stripped = "# Introduction"

# Check: Is this a header?
header_match = HEADER_PATTERN.match("# Introduction")  # Matches!
# group(1) = "#" (1 hash)
# group(2) = "Introduction"

level = len("#") = 1
title = "Introduction"

# Update breadcrumbs (H1 = replace all)
current_breadcrumbs = ["Introduction"]

# Emit header section
sections.append({
    'type': 'major_header',    # H1 or H2 = major
    'content': 'Introduction',
    'breadcrumbs': ['Introduction'],
    'start': 0,
    'end': 16
})

cursor = 16  # Move past this line

# State:
# sections = [{'type': 'major_header', 'content': 'Introduction', ...}]
# breadcrumbs = ['Introduction']

# =================================================================
# ITERATION 2: Empty line
# =================================================================

line = "\n"
line_stripped = ""

# Skip empty lines
cursor = 17
# sections unchanged

# =================================================================
# ITERATION 3: "This document explains..."
# =================================================================

line = "This document explains the system architecture.\n"
line_stripped = "This document explains the system architecture."

# Not header, not list, not protected block → regular text

sections.append({
    'type': 'text',
    'content': 'This document explains the system architecture.\n',
    'breadcrumbs': ['Introduction'],
    'start': 17,
    'end': 65
})

cursor = 65

# State:
# sections = [
#     {'type': 'major_header', 'content': 'Introduction', ...},
#     {'type': 'text', 'content': 'This document...', ...}
# ]

# =================================================================
# ITERATION 4: Empty line
# =================================================================

cursor = 66  # Skip

# =================================================================
# ITERATION 5: "## Components"
# =================================================================

line = "## Components\n"
line_stripped = "## Components"

# Header detected!
header_match = HEADER_PATTERN.match("## Components")
# group(1) = "##" (2 hashes)
# group(2) = "Components"

level = len("##") = 2
title = "Components"

# Update breadcrumbs (H2 = keep H1, add H2)
current_breadcrumbs = ["Introduction"][:1] + ["Components"]
current_breadcrumbs = ["Introduction", "Components"]

sections.append({
    'type': 'major_header',
    'content': 'Components',
    'breadcrumbs': ['Introduction', 'Components'],
    'start': 66,
    'end': 81
})

cursor = 81

# State:
# breadcrumbs = ['Introduction', 'Components']

# =================================================================
# ITERATION 6: Empty line
# =================================================================

cursor = 82  # Skip

# =================================================================
# ITERATION 7: "The system has three..."
# =================================================================

line = "The system has three main components:\n"

sections.append({
    'type': 'text',
    'content': 'The system has three main components:\n',
    'breadcrumbs': ['Introduction', 'Components'],
    'start': 82,
    'end': 120
})

cursor = 120

# =================================================================
# ITERATION 8: Empty line
# =================================================================

cursor = 121  # Skip

# =================================================================
# ITERATION 9: "- Data ingestion"
# =================================================================

line = "- Data ingestion\n"
line_stripped = "- Data ingestion"

# Check: Is this a list item?
is_list_item = LIST_PATTERN.match("- Data ingestion")  # TRUE!

# Initialize list
in_list = True
list_start = 121
list_buffer = ["- Data ingestion\n"]

cursor = 138

# State:
# in_list = True
# list_buffer = ["- Data ingestion\n"]

# =================================================================
# ITERATION 10: "- Processing engine"
# =================================================================

line = "- Processing engine\n"
line_stripped = "- Processing engine"

# Check: Is this a list item?
is_list_item = LIST_PATTERN.match("- Processing engine")  # TRUE!

# Already in list, accumulate
list_buffer.append("- Processing engine\n")

cursor = 158

# State:
# list_buffer = ["- Data ingestion\n", "- Processing engine\n"]

# =================================================================
# ITERATION 11: "- Storage layer"
# =================================================================

line = "- Storage layer\n"
line_stripped = "- Storage layer"

# List item - accumulate
list_buffer.append("- Storage layer\n")

cursor = 174

# State:
# list_buffer = [
#     "- Data ingestion\n",
#     "- Processing engine\n",
#     "- Storage layer\n"
# ]

# =================================================================
# ITERATION 12: Empty line
# =================================================================

cursor = 175  # Skip

# =================================================================
# ITERATION 13: "### Processing Details"
# =================================================================

line = "### Processing Details\n"
line_stripped = "### Processing Details"

# Header detected!

# FIRST: Flush accumulated list
sections.append({
    'type': 'text',
    'content': '- Data ingestion\n- Processing engine\n- Storage layer\n',
    'breadcrumbs': ['Introduction', 'Components'],
    'start': 121,
    'end': 174
})
list_buffer = []
in_list = False

# Process header
level = 3
title = "Processing Details"

# Update breadcrumbs (H3 = keep H1+H2, add H3)
current_breadcrumbs = ["Introduction", "Components"][:2] + ["Processing Details"]
current_breadcrumbs = ["Introduction", "Components", "Processing Details"]

sections.append({
    'type': 'minor_header',  # H3-H6 = minor
    'content': 'Processing Details',
    'breadcrumbs': ['Introduction', 'Components', 'Processing Details'],
    'start': 175,
    'end': 199
})

cursor = 199

# State:
# breadcrumbs = ['Introduction', 'Components', 'Processing Details']
# sections now has the list added!

# =================================================================
# ITERATION 14: Empty line
# =================================================================

cursor = 200  # Skip

# =================================================================
# ITERATION 15: Protected block (image)
# =================================================================

# Check: Are we at protected block position?
cursor = 200
block = get_block_at_position(protected_blocks, 200)
# Returns: (200, 250, 'image', '**Image 1:**\n![](flow.png)')

# Emit protected block
sections.append({
    'type': 'image',
    'content': '**Image 1: Flow Diagram**\n![](flow.png)',
    'breadcrumbs': ['Introduction', 'Components', 'Processing Details'],
    'start': 200,
    'end': 250
})

cursor = 250  # Jump past entire block

# =================================================================
# ITERATION 16: Empty line
# =================================================================

cursor = 251  # Skip

# =================================================================
# ITERATION 17: "The processing happens..."
# =================================================================

line = "The processing happens in stages.\n"

sections.append({
    'type': 'text',
    'content': 'The processing happens in stages.\n',
    'breadcrumbs': ['Introduction', 'Components', 'Processing Details'],
    'start': 251,
    'end': 285
})

cursor = 285

# =================================================================
# END OF TEXT
# =================================================================

cursor = 285 >= len(text)  # Exit loop

# =================================================================
# FINAL SECTIONS OUTPUT
# =================================================================

sections = [
    {
        'type': 'major_header',
        'content': 'Introduction',
        'breadcrumbs': ['Introduction'],
        'start': 0,
        'end': 16
    },
    {
        'type': 'text',
        'content': 'This document explains the system architecture.\n',
        'breadcrumbs': ['Introduction'],
        'start': 17,
        'end': 65
    },
    {
        'type': 'major_header',
        'content': 'Components',
        'breadcrumbs': ['Introduction', 'Components'],
        'start': 66,
        'end': 81
    },
    {
        'type': 'text',
        'content': 'The system has three main components:\n',
        'breadcrumbs': ['Introduction', 'Components'],
        'start': 82,
        'end': 120
    },
    {
        'type': 'text',
        'content': '- Data ingestion\n- Processing engine\n- Storage layer\n',
        'breadcrumbs': ['Introduction', 'Components'],
        'start': 121,
        'end': 174
    },
    {
        'type': 'minor_header',
        'content': 'Processing Details',
        'breadcrumbs': ['Introduction', 'Components', 'Processing Details'],
        'start': 175,
        'end': 199
    },
    {
        'type': 'image',
        'content': '**Image 1: Flow Diagram**\n![](flow.png)',
        'breadcrumbs': ['Introduction', 'Components', 'Processing Details'],
        'start': 200,
        'end': 250
    },
    {
        'type': 'text',
        'content': 'The processing happens in stages.\n',
        'breadcrumbs': ['Introduction', 'Components', 'Processing Details'],
        'start': 251,
        'end': 285
    }
]
```

---

## 🎮 State Machine Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    INITIAL STATE                        │
│  cursor=0, breadcrumbs=[], sections=[], in_list=False  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Read line at cursor   │
        └───────────┬────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Empty or comment?     │
        └───┬───────────────┬───┘
         YES│               │NO
            ▼               ▼
        Skip line    ┌──────────────┐
        cursor++     │ Protected?   │
                     └───┬──────┬───┘
                      YES│      │NO
                         ▼      ▼
                   ┌─────────┐ ┌──────────┐
                   │Flush list│ │ Header?  │
                   │Emit block│ └───┬──┬───┘
                   │Jump past │  YES│  │NO
                   └─────────┘     ▼  ▼
                                ┌──────┐ ┌────────┐
                                │Flush │ │ List?  │
                                │Update│ └───┬─┬──┘
                                │Emit  │  YES│ │NO
                                └──────┘     ▼ ▼
                                          ┌────┐ ┌─────┐
                                          │Accum│ │Flush│
                                          │Buffer│ │ if  │
                                          └────┘ │need │
                                                 │Emit │
                                                 └─────┘
                                                    │
                    ┌───────────────────────────────┘
                    │
                    ▼
        ┌────────────────────┐
        │   cursor++         │
        │   Continue loop    │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  cursor < len(text)│
        └───┬────────────┬───┘
         YES│            │NO
            │            ▼
            │      ┌──────────┐
            │      │Flush any │
            │      │remaining │
            │      │list      │
            │      └────┬─────┘
            │           │
            └───────────┼─────────┐
                        │         │
                        ▼         ▼
                 ┌─────────────────────┐
                 │  RETURN sections    │
                 └─────────────────────┘
```

---

## 🔑 Key Decision Points Explained

### Decision 1: Empty Line or Comment?

```python
if not line_stripped or line_stripped.startswith('<!--'):
    cursor = line_end + 1
    continue

# Example empty line:
line = "\n"
line_stripped = ""  # Falsy!

# Example comment:
line = "<!-- Page metadata -->\n"
line_stripped = "<!-- Page metadata -->"  # Starts with <!--
```

**Why skip?**
- Empty lines: Markdown paragraph separators, not content
- Comments: Extractor metadata, not document content

### Decision 2: Protected Block?

```python
block = get_block_at_position(protected_blocks, cursor)

if block:
    # We're at START of a protected block
    # Example: cursor=200, block=(200, 250, 'image', '...')
    
    # 1. Flush any accumulated list
    # 2. Emit the entire block
    # 3. Jump cursor to end of block
    cursor = block[1]  # Jump to end
    continue
```

**Why check this first?**
Protected blocks take precedence over line-by-line parsing. They can span many lines.

### Decision 3: Header?

```python
header_match = HEADER_PATTERN.match(line_stripped)
# Pattern: r'^(#{1,6})\s+(.+)'

if header_match:
    level = len(header_match.group(1))  # Count # symbols
    title = header_match.group(2).strip()
    
    # Skip page headers (from extractor)
    if level == 1 and title.startswith("Page "):
        continue
    
    # Flush list, update breadcrumbs, emit header
```

**Header Classification**:
```python
if level <= 2:
    header_type = 'major_header'  # H1, H2 = major boundaries
else:
    header_type = 'minor_header'  # H3-H6 = context updates
```

### Decision 4: List Item?

```python
is_list_item = bool(LIST_PATTERN.match(line_stripped))
# Pattern: r'^[-*+]|\d+\.'

if is_list_item:
    if not in_list:
        # Starting a new list
        list_start = cursor
        in_list = True
    
    # Accumulate this item
    list_buffer.append(line)
    cursor = line_end + 1
    continue
```

**Why accumulate?**
Lists are multi-line semantic units:
```markdown
- Item 1
- Item 2
- Item 3
```
Should become ONE section, not three.

### Decision 5: Regular Text

```python
# If we're here: not empty, not protected, not header, not list

# But first: Flush list if we were in one
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

# Emit regular text line
sections.append({
    'type': 'text',
    'content': line,
    'breadcrumbs': current_breadcrumbs.copy(),
    'start': cursor,
    'end': line_end + 1
})
```

---

## 📚 Breadcrumb Update Logic Deep Dive

### The Challenge

Headers create hierarchy, and we need to track it:

```markdown
# Chapter 1
## Section A
### Part 1
#### Detail X
## Section B
### Part 2
```

Should produce:
```python
["Chapter 1"]
["Chapter 1", "Section A"]
["Chapter 1", "Section A", "Part 1"]
["Chapter 1", "Section A", "Part 1", "Detail X"]
["Chapter 1", "Section B"]                          # Part 1, Detail X dropped
["Chapter 1", "Section B", "Part 2"]
```

### The Solution

```python
def _update_breadcrumbs(current_breadcrumbs, level, title):
    """
    Update breadcrumb path based on header level.
    
    Rule: Keep first (level-1) elements, add new title at level
    """
    
    if level == 1:
        # H1: Top level, replace everything
        return [title]
    
    elif level == 2:
        # H2: Keep H1, replace rest
        return current_breadcrumbs[:1] + [title]
    
    elif level == 3:
        # H3: Keep H1+H2, add H3
        return current_breadcrumbs[:2] + [title]
    
    else:
        # H4-H6: Keep first (level-1), add new
        return current_breadcrumbs[:level-1] + [title]
```

### Visual Example

```python
# Start
breadcrumbs = []

# See "# Chapter 1" (level=1)
breadcrumbs = ["Chapter 1"]

# See "## Section A" (level=2)
breadcrumbs = ["Chapter 1"][:1] + ["Section A"]
breadcrumbs = ["Chapter 1", "Section A"]

# See "### Part 1" (level=3)
breadcrumbs = ["Chapter 1", "Section A"][:2] + ["Part 1"]
breadcrumbs = ["Chapter 1", "Section A", "Part 1"]

# See "#### Detail X" (level=4)
breadcrumbs = ["Chapter 1", "Section A", "Part 1"][:3] + ["Detail X"]
breadcrumbs = ["Chapter 1", "Section A", "Part 1", "Detail X"]

# See "## Section B" (level=2)
breadcrumbs = ["Chapter 1", "Section A", "Part 1", "Detail X"][:1] + ["Section B"]
breadcrumbs = ["Chapter 1", "Section B"]
# ^ Part 1 and Detail X are dropped!

# See "### Part 2" (level=3)
breadcrumbs = ["Chapter 1", "Section B"][:2] + ["Part 2"]
breadcrumbs = ["Chapter 1", "Section B", "Part 2"]
```

**Key Insight**: List slicing `[:level-1]` keeps only the parent levels!

---

## 🎯 Common Edge Cases

### Edge Case 1: List at End of Document

```python
text = """
# Title

- Item 1
- Item 2
- Item 3"""  # No newline after last item!

# Problem: Loop exits while in_list=True
# Solution: Post-loop cleanup

# After main loop:
if list_buffer:
    sections.append({
        'type': 'text',
        'content': ''.join(list_buffer),
        'breadcrumbs': current_breadcrumbs.copy(),
        'start': list_start,
        'end': cursor
    })
```

### Edge Case 2: Page Headers from Extractor

```python
text = """
# Page 1

# Introduction

Content here...
"""

# "# Page 1" is NOT real content, it's extractor metadata
# Solution: Filter it out

if level == 1 and title.startswith("Page "):
    cursor = line_end + 1
    continue  # Skip this header
```

### Edge Case 3: Empty Breadcrumbs

```python
# Document starts with regular text (no headers)
text = "Just some text without headers"

# Breadcrumbs stay []
sections = [{
    'type': 'text',
    'content': 'Just some text...',
    'breadcrumbs': [],  # No context
    'start': 0,
    'end': 30
}]
```

### Edge Case 4: Protected Block Inside List

```python
text = """
Steps to follow:
- Step 1
- Step 2
![](diagram.png)
- Step 3
"""

# Protected block at ![](diagram.png)
# When cursor hits it:
# 1. Flush list (Step 1, Step 2)
# 2. Emit protected block
# 3. Step 3 starts new list
```

---

## 📊 Performance Characteristics

### Time Complexity

**O(n)** where n = text length

- Single pass through document
- Each character examined once
- Line-by-line processing

### Space Complexity

**O(m)** where m = number of sections

- Sections list grows with content
- List buffer is temporary (bounded by list size)
- Breadcrumbs bounded by header depth (typically < 6)

### Optimizations

1. **Compiled Regex Patterns**
```python
# In config.py (compiled once)
HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)')
LIST_PATTERN = re.compile(r'^[-*+]|\d+\.')

# NOT in loop:
for line in lines:
    re.match(r'^(#{1,6})\s+(.+)', line)  # ❌ Recompiles each time!
```

2. **Early Continues**
```python
# Skip processing ASAP
if not line_stripped:
    cursor = line_end + 1
    continue  # Don't process further
```

3. **Protected Block Jump**
```python
# Don't parse line-by-line inside protected blocks
if block:
    cursor = block[1]  # Jump to end
    continue  # Skip all lines in block
```

---

## 💡 Why This Design?

### Why Cursor-Based Instead of Split by Lines?

```python
# ❌ Alternative approach: Split all lines first
lines = text.split('\n')
for line in lines:
    process(line)

# Problem: Loses position information!
# Can't jump over protected blocks
```

```python
# ✅ Cursor approach: Know exact position
cursor = 0
while cursor < len(text):
    # Can check if we're at protected block START
    # Can jump to arbitrary positions
```

### Why List Buffer Instead of Immediate Emit?

```python
# ❌ Without buffer: Each line is separate section
"- Item 1" → section
"- Item 2" → section
"- Item 3" → section
# Result: 3 tiny sections

# ✅ With buffer: Accumulate then emit once
"- Item 1\n- Item 2\n- Item 3" → ONE section
# Result: Coherent semantic unit
```

### Why Breadcrumbs?

```python
# Preserves document structure for RAG
section = {
    'content': 'The system uses microservices...',
    'breadcrumbs': ['Architecture', 'Components', 'Backend']
}

# Later, when chunking:
chunk_text = "Context: Architecture > Components > Backend\n\n" + content
# Gives LLM hierarchical context!
```

---

## 🔍 Debugging Tips

### Tip 1: Log Cursor Position

```python
logger.debug(f"Cursor: {cursor}, Line: {line_stripped[:50]}")
```

### Tip 2: Track Breadcrumb Changes

```python
old_breadcrumbs = current_breadcrumbs.copy()
# ... update breadcrumbs ...
if old_breadcrumbs != current_breadcrumbs:
    logger.debug(f"Breadcrumbs: {old_breadcrumbs} → {current_breadcrumbs}")
```

### Tip 3: Count Section Types

```python
from collections import Counter
types = Counter(s['type'] for s in sections)
logger.debug(f"Section types: {dict(types)}")
# Example: {'major_header': 3, 'text': 12, 'image': 2}
```

---

## 📋 Quick Reference

| Input Pattern | Detection | Action |
|--------------|-----------|--------|
| Empty line | `not line_stripped` | Skip |
| Comment | Starts with `<!--` | Skip |
| Page header | `# Page N` | Skip |
| H1, H2 | `#{1,2} Title` | Flush list, update breadcrumbs, emit as `major_header` |
| H3-H6 | `#{3,6} Title` | Flush list, update breadcrumbs, emit as `minor_header` |
| Bullet list | Starts with `-`, `*`, `+` | Accumulate in buffer |
| Numbered list | Starts with `\d+.` | Accumulate in buffer |
| Protected block | cursor == block.start | Flush list, emit block, jump past |
| Regular text | None of above | Flush list if needed, emit as `text` |

---

## 🎓 Summary

**`parse_semantic_sections()`** is the foundation of semantic chunking. It:

1. ✅ Preserves document structure (headers → breadcrumbs)
2. ✅ Groups multi-line units (lists, protected blocks)
3. ✅ Maintains position information (start, end)
4. ✅ Respects atomic content (protected blocks)
5. ✅ Provides hierarchical context (breadcrumbs)

**Result**: Clean semantic sections ready for intelligent chunking!
