# `consolidate_paragraphs()` - Complete Documentation

## 📋 Function Overview

```python
def consolidate_paragraphs(
    sections: List[Dict[str, Any]],
    config: Dict[str, Any],
    logger: logging.Logger
) -> List[Dict[str, Any]]
```

**Purpose**: Group consecutive text sections that are regular paragraphs into single coherent sections.

**Module**: `semantic_parser.py`

**Called By**: `_process_single_page()` in `orchestrator.py`

**Called After**: `parse_semantic_sections()`

**Returns**: Sections with consecutive paragraphs merged

---

## 🎯 Why This Function Exists

### The Problem

After `parse_semantic_sections()`, each paragraph is a separate section:

```python
# Input sections from parse_semantic_sections():
sections = [
    {'type': 'major_header', 'content': 'Introduction'},
    {'type': 'text', 'content': 'The AI market is growing rapidly.\n'},
    {'type': 'text', 'content': 'Companies are investing heavily in infrastructure.\n'},
    {'type': 'text', 'content': 'This trend will continue through 2025.\n'},
    {'type': 'major_header', 'content': 'Market Analysis'}
]

# Result: 3 tiny text sections (40-50 chars each)
# Problem: If min_size=800, each becomes a rejected fragment!
```

### The Solution

```python
# After consolidate_paragraphs():
sections = [
    {'type': 'major_header', 'content': 'Introduction'},
    {'type': 'text', 'content': 
        'The AI market is growing rapidly.\n\n' +
        'Companies are investing heavily in infrastructure.\n\n' +
        'This trend will continue through 2025.\n'
    },  # Now 125 chars - meaningful chunk!
    {'type': 'major_header', 'content': 'Market Analysis'}
]

# Result: ONE coherent section with complete context
```

### What Gets Consolidated?

```python
✅ CONSOLIDATE (regular paragraphs):
- Plain text paragraphs
- Multiple consecutive text sections

❌ DON'T CONSOLIDATE:
- Lists (bullet points or numbered)
- Headers
- Tables
- Images
- Code blocks
```

---

## 🏗️ Algorithm Strategy

### High-Level Overview

```
ACCUMULATION PATTERN

1. Initialize: text_group = []
2. For each section:
   a. If regular paragraph → add to text_group
   b. If list/header/other → flush text_group, add section, reset
3. After loop: flush any remaining text_group
4. Return consolidated sections
```

### Visual Flow

```
┌──────────────────────────────────────────────────────┐
│              START CONSOLIDATION                     │
│     text_group=[], consolidated=[]                   │
└─────────────────┬────────────────────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ For each section    │
        └──────────┬──────────┘
                   │
    ┌──────────────┴───────────────┐
    │                              │
    ▼                              ▼
┌───────────┐               ┌──────────────┐
│ Regular   │               │ List/Header/ │
│ Paragraph?│               │ Other?       │
└─────┬─────┘               └──────┬───────┘
      │ YES                        │ YES
      ▼                            ▼
┌────────────┐              ┌──────────────┐
│ Add to     │              │ 1. Flush     │
│ text_group │              │    text_group│
└─────┬──────┘              │ 2. Add section│
      │                     │ 3. Reset     │
      │                     └──────┬───────┘
      │                            │
      └────────────┬───────────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Continue to next    │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ End of sections?    │
        └──┬──────────────┬───┘
      NO  │              │ YES
          │              ▼
          │        ┌──────────────┐
          │        │ Flush final  │
          │        │ text_group   │
          │        └──────┬───────┘
          │               │
          └───────────────┼───────────┐
                          │           │
                          ▼           ▼
                   ┌──────────────────────┐
                   │ RETURN consolidated  │
                   └──────────────────────┘
```

---

## 🔍 Core Logic Explained

### The Accumulation Buffer

```python
text_group = []           # Accumulator for consecutive paragraphs
text_breadcrumbs = []     # Context for the group
consolidated = []         # Final output

# Example accumulation:
# Iteration 1: text_group = ["Para 1"]
# Iteration 2: text_group = ["Para 1", "Para 2"]
# Iteration 3: text_group = ["Para 1", "Para 2", "Para 3"]
# Then: Flush and join with "\n\n"
```

### Key Decision: Is This a List?

```python
# CRITICAL DISTINCTION:
# Text sections can be either paragraphs OR lists

# Example text section (paragraph):
section = {
    'type': 'text',
    'content': 'The system processes data efficiently.\n'
}
# is_list = False → CONSOLIDATE

# Example text section (list):
section = {
    'type': 'text',
    'content': '- MongoDB (Vector Database)\n- Pinecone (Search)\n'
}
# is_list = True → DON'T CONSOLIDATE
```

**Detection Method**:
```python
list_pattern = config['patterns']['list']  # r'^[-*+]|\d+\.'

is_list = (
    section['type'] == 'text' and 
    list_pattern.match(section['content'].strip())
)

# Examples:
"Regular paragraph"           → is_list = False
"- Item 1\n- Item 2"         → is_list = True
"1. First\n2. Second"        → is_list = True
"  - Indented item"          → is_list = False (has leading space)
```

---

## 📝 Complete Walkthrough with Example

### Input Sections

```python
sections = [
    # Header
    {
        'type': 'major_header',
        'content': 'System Overview',
        'breadcrumbs': ['System Overview'],
        'start': 0,
        'end': 20
    },
    
    # Paragraph 1
    {
        'type': 'text',
        'content': 'The system is designed for high performance.\n',
        'breadcrumbs': ['System Overview'],
        'start': 21,
        'end': 67
    },
    
    # Paragraph 2
    {
        'type': 'text',
        'content': 'It uses a microservices architecture.\n',
        'breadcrumbs': ['System Overview'],
        'start': 68,
        'end': 106
    },
    
    # Paragraph 3
    {
        'type': 'text',
        'content': 'Each service is independently scalable.\n',
        'breadcrumbs': ['System Overview'],
        'start': 107,
        'end': 147
    },
    
    # List (should NOT consolidate with paragraphs)
    {
        'type': 'text',
        'content': '- API Gateway\n- User Service\n- Data Service\n',
        'breadcrumbs': ['System Overview'],
        'start': 148,
        'end': 198
    },
    
    # Paragraph 4 (after list)
    {
        'type': 'text',
        'content': 'The services communicate via REST APIs.\n',
        'breadcrumbs': ['System Overview'],
        'start': 199,
        'end': 239
    },
    
    # Minor header (boundary)
    {
        'type': 'minor_header',
        'content': 'Performance',
        'breadcrumbs': ['System Overview', 'Performance'],
        'start': 240,
        'end': 260
    },
    
    # Paragraph 5
    {
        'type': 'text',
        'content': 'Response times average under 100ms.\n',
        'breadcrumbs': ['System Overview', 'Performance'],
        'start': 261,
        'end': 297
    }
]
```

### Step-by-Step Execution

```python
# =================================================================
# INITIALIZATION
# =================================================================

text_group = []
text_breadcrumbs = []
consolidated = []
list_pattern = re.compile(r'^[-*+]|\d+\.')

# =================================================================
# ITERATION 1: Process major_header
# =================================================================

section = sections[0]  # 'System Overview' header
section_type = 'major_header'

# Check: Is this a regular paragraph?
is_list = (section['type'] == 'text' and list_pattern.match(...))
# section['type'] = 'major_header' (not 'text')
# is_list = False

# Check condition:
if section['type'] == 'text' and not is_list:  # False (not text)
    # Don't enter this branch

else:  # Enter this branch (non-paragraph)
    # Flush text_group (currently empty)
    if text_group:  # False (empty)
        # Don't flush
    
    # Add non-paragraph section directly
    consolidated.append(section)

# State:
# text_group = []
# consolidated = [{'type': 'major_header', 'content': 'System Overview', ...}]

# =================================================================
# ITERATION 2: Process paragraph 1
# =================================================================

section = sections[1]  # "The system is designed..."
section_type = 'text'
content = 'The system is designed for high performance.\n'

# Check: Is this a list?
is_list = list_pattern.match(content.strip())
# "The system..." doesn't start with -, *, +, or digit.
# is_list = False

# Check condition:
if section['type'] == 'text' and not is_list:  # True
    # This IS a regular paragraph
    text_group.append(section['content'])
    text_breadcrumbs = section['breadcrumbs']

# State:
# text_group = ['The system is designed for high performance.\n']
# text_breadcrumbs = ['System Overview']

# =================================================================
# ITERATION 3: Process paragraph 2
# =================================================================

section = sections[2]  # "It uses a microservices..."
content = 'It uses a microservices architecture.\n'

is_list = False  # Regular paragraph

# Add to accumulator
text_group.append(section['content'])

# State:
# text_group = [
#     'The system is designed for high performance.\n',
#     'It uses a microservices architecture.\n'
# ]

# =================================================================
# ITERATION 4: Process paragraph 3
# =================================================================

section = sections[3]  # "Each service is independently..."
content = 'Each service is independently scalable.\n'

is_list = False  # Regular paragraph

# Add to accumulator
text_group.append(section['content'])

# State:
# text_group = [
#     'The system is designed for high performance.\n',
#     'It uses a microservices architecture.\n',
#     'Each service is independently scalable.\n'
# ]

# =================================================================
# ITERATION 5: Process list
# =================================================================

section = sections[4]  # "- API Gateway\n- User Service..."
content = '- API Gateway\n- User Service\n- Data Service\n'

# Check: Is this a list?
is_list = list_pattern.match(content.strip())
# "- API Gateway" starts with '-'
# is_list = True

# Check condition:
if section['type'] == 'text' and not is_list:  # False (is_list=True)
    # Don't enter

else:  # Enter (this is a list)
    # FLUSH accumulated paragraphs first!
    if text_group:  # True (has 3 paragraphs)
        consolidated.append({
            'type': 'text',
            'content': '\n\n'.join(text_group),
            'breadcrumbs': text_breadcrumbs,
            'start': sections[1].get('start', 0),
            'end': sections[3].get('end', 0)
        })
        
        # Joined content:
        # 'The system is designed for high performance.\n\n'
        # 'It uses a microservices architecture.\n\n'
        # 'Each service is independently scalable.\n'
        
        text_group = []  # Reset
    
    # Add the list section
    consolidated.append(section)

# State:
# text_group = []  # Reset after flush
# consolidated = [
#     {'type': 'major_header', 'content': 'System Overview', ...},
#     {'type': 'text', 'content': 'The system...architecture...scalable.\n', ...},
#     {'type': 'text', 'content': '- API Gateway\n- User Service\n...', ...}
# ]

# =================================================================
# ITERATION 6: Process paragraph 4
# =================================================================

section = sections[5]  # "The services communicate..."
content = 'The services communicate via REST APIs.\n'

is_list = False  # Regular paragraph

# Start new accumulation
text_group.append(section['content'])
text_breadcrumbs = section['breadcrumbs']

# State:
# text_group = ['The services communicate via REST APIs.\n']

# =================================================================
# ITERATION 7: Process minor_header
# =================================================================

section = sections[6]  # 'Performance' header
section_type = 'minor_header'

# Not a text section, so else branch

else:  # Enter
    # Flush single paragraph
    if text_group:  # True
        consolidated.append({
            'type': 'text',
            'content': '\n\n'.join(text_group),
            'breadcrumbs': text_breadcrumbs,
            'start': sections[5].get('start', 0),
            'end': sections[5].get('end', 0)
        })
        
        # Content: 'The services communicate via REST APIs.\n'
        # (Only one paragraph, so no "\n\n" joining needed)
        
        text_group = []
    
    # Add header
    consolidated.append(section)

# State:
# text_group = []
# consolidated = [
#     {'type': 'major_header', ...},
#     {'type': 'text', 'content': 'The system...scalable.\n', ...},
#     {'type': 'text', 'content': '- API Gateway...', ...},
#     {'type': 'text', 'content': 'The services communicate...', ...},
#     {'type': 'minor_header', 'content': 'Performance', ...}
# ]

# =================================================================
# ITERATION 8: Process paragraph 5
# =================================================================

section = sections[7]  # "Response times average..."
content = 'Response times average under 100ms.\n'

is_list = False  # Regular paragraph

# Add to accumulator
text_group.append(section['content'])
text_breadcrumbs = section['breadcrumbs']

# State:
# text_group = ['Response times average under 100ms.\n']

# =================================================================
# END OF LOOP - Final Flush
# =================================================================

# Check: Any remaining paragraphs?
if text_group:  # True
    consolidated.append({
        'type': 'text',
        'content': '\n\n'.join(text_group),
        'breadcrumbs': text_breadcrumbs,
        'start': sections[-1].get('start', 0),
        'end': sections[-1].get('end', 0)
    })

# State:
# text_group = []  # Flushed
# consolidated = [
#     {'type': 'major_header', ...},
#     {'type': 'text', 'content': 'The system...scalable.\n', ...},
#     {'type': 'text', 'content': '- API Gateway...', ...},
#     {'type': 'text', 'content': 'The services communicate...', ...},
#     {'type': 'minor_header', 'content': 'Performance', ...},
#     {'type': 'text', 'content': 'Response times average...', ...}
# ]

# =================================================================
# RETURN
# =================================================================

return consolidated
```

### Before vs After Comparison

```python
# BEFORE consolidate_paragraphs():
# 8 sections (5 text, 2 headers, 1 list-as-text)
sections = [
    header,
    text (46 chars),    # ← Too small!
    text (38 chars),    # ← Too small!
    text (40 chars),    # ← Too small!
    text (list),
    text (40 chars),    # ← Too small!
    header,
    text (36 chars)     # ← Too small!
]

# AFTER consolidate_paragraphs():
# 6 sections (3 text consolidated, 2 headers, 1 list)
consolidated = [
    header,
    text (124 chars),   # ✓ Merged 3 paragraphs!
    text (list),
    text (40 chars),    # Single paragraph
    header,
    text (36 chars)     # Single paragraph
]
```

---

## 🎯 Why "\n\n" Between Paragraphs?

```python
# Join with double newline
content = '\n\n'.join(text_group)
```

### Reason 1: Markdown Convention

```markdown
This is paragraph 1.

This is paragraph 2.

This is paragraph 3.
```

Double newline (`\n\n`) is the standard markdown paragraph separator.

### Reason 2: Readability

```python
# With \n\n:
"Para 1.\n\nPara 2.\n\nPara 3."
# Displays as:
# Para 1.
# 
# Para 2.
# 
# Para 3.

# Without \n\n (using single \n):
"Para 1.\nPara 2.\nPara 3."
# Displays as:
# Para 1.
# Para 2.
# Para 3.
# Looks like one continuous paragraph!
```

### Reason 3: LLM Training

LLMs are trained on markdown text where `\n\n` means paragraph break. Preserving this helps the model understand structure.

---

## 🔍 List Detection Deep Dive

### The Challenge

Text sections can contain either paragraphs OR lists:

```python
# Both are type='text', but semantically different!

# Regular paragraph:
{'type': 'text', 'content': 'The system uses containers.\n'}

# List:
{'type': 'text', 'content': '- Docker\n- Kubernetes\n- Podman\n'}
```

### Detection Logic

```python
# Pattern matches start of line
list_pattern = re.compile(r'^[-*+]|\d+\.')

# Breakdown:
# ^         = start of string
# [-*+]     = dash, asterisk, or plus
# |         = OR
# \d+\.     = one or more digits followed by period

# Examples:
"- Item"      → Matches (bullet)
"* Item"      → Matches (bullet)
"+ Item"      → Matches (bullet)
"1. Item"     → Matches (numbered)
"99. Item"    → Matches (numbered)
"Item"        → No match (regular text)
"  - Item"    → No match (has leading space)
```

### Why Leading Space Matters

```python
# Indented list items:
content = "  - Nested item\n"
content.strip() = "- Nested item"  # After strip, matches!

# BUT in practice:
is_list = list_pattern.match(content.strip())

# Example with indentation:
content = "  - Docker\n  - Kubernetes\n"
content.strip() = "- Docker\n  - Kubernetes"  # Strip only outer spaces
# Match checks first line: "- Docker" → is_list = True ✓
```

### Edge Cases

```python
# Case 1: Paragraph mentioning list items
content = "The items are: - not a list"
is_list = False  # Doesn't start with '-'

# Case 2: Numbered sentence
content = "1. This is not a list, it's a sentence."
is_list = True  # MATCHES! (starts with "1.")
# Note: This is a known limitation, but rarely happens

# Case 3: Multiple lists
content = "- Item 1\n- Item 2\n\n1. Step 1\n2. Step 2"
first_line = content.split('\n')[0] = "- Item 1"
is_list = True  # Correctly identifies as list

# Case 4: Empty list
content = "\n"
is_list = False  # Empty after strip
```

---

## 📊 State Transitions Diagram

```
                    START
                      │
                      ▼
              ┌───────────────┐
              │ text_group=[] │
              └───────┬───────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
  ┌───────────┐            ┌──────────────┐
  │ Regular   │            │ List/Header  │
  │ Paragraph │            │ /Other       │
  └─────┬─────┘            └──────┬───────┘
        │                         │
        │ Add to                  │ Flush
        │ text_group              │ text_group
        │                         │
        ▼                         ▼
  ┌───────────┐            ┌──────────────┐
  │text_group │            │ Add section  │
  │  grows    │            │ to output    │
  └─────┬─────┘            └──────┬───────┘
        │                         │
        │                         │ Reset
        │                         │ text_group
        │                         │
        └─────────────┬───────────┘
                      │
                      ▼
              ┌───────────────┐
              │ Next section  │
              └───────┬───────┘
                      │
                ┌─────┴─────┐
                │           │
              YES│         │NO
                │           │
                ▼           ▼
            Continue     Flush
             Loop        Final
                         Group
                           │
                           ▼
                        RETURN
```

---

## 🎮 Real-World Examples

### Example 1: Mixed Content

```python
# Input:
sections = [
    {'type': 'text', 'content': 'Introduction paragraph.\n'},
    {'type': 'text', 'content': 'Another paragraph.\n'},
    {'type': 'text', 'content': '- List item 1\n- List item 2\n'},
    {'type': 'text', 'content': 'Concluding paragraph.\n'}
]

# Process:
# Iteration 1-2: Accumulate paragraphs
# text_group = ['Introduction...', 'Another...']

# Iteration 3: Hit list
# → Flush: "Introduction...\n\nAnother..."
# → Add list separately
# → Reset text_group

# Iteration 4: Accumulate single paragraph
# text_group = ['Concluding...']

# Final flush: 'Concluding...'

# Output:
consolidated = [
    {'type': 'text', 'content': 'Introduction paragraph.\n\nAnother paragraph.\n'},
    {'type': 'text', 'content': '- List item 1\n- List item 2\n'},
    {'type': 'text', 'content': 'Concluding paragraph.\n'}
]
```

### Example 2: No Consolidation Needed

```python
# Input: All different types
sections = [
    {'type': 'major_header', 'content': 'Title'},
    {'type': 'text', 'content': '- Item 1\n- Item 2\n'},
    {'type': 'minor_header', 'content': 'Subtitle'},
    {'type': 'table', 'content': '| A | B |\n...'}
]

# Process:
# Each section is non-paragraph or list
# Each gets added directly to output
# text_group never accumulates anything

# Output: Unchanged
consolidated = sections  # Exactly the same!
```

### Example 3: All Paragraphs

```python
# Input: Only paragraphs
sections = [
    {'type': 'text', 'content': 'Para 1.\n'},
    {'type': 'text', 'content': 'Para 2.\n'},
    {'type': 'text', 'content': 'Para 3.\n'},
    {'type': 'text', 'content': 'Para 4.\n'},
    {'type': 'text', 'content': 'Para 5.\n'}
]

# Process:
# All are regular paragraphs
# All accumulate in text_group
# No flush until end of loop
# Final flush combines all

# Output: ONE big section
consolidated = [
    {'type': 'text', 'content': 'Para 1.\n\nPara 2.\n\nPara 3.\n\nPara 4.\n\nPara 5.\n'}
]
```

### Example 4: Headers as Boundaries

```python
# Input:
sections = [
    {'type': 'text', 'content': 'Para 1.\n'},
    {'type': 'text', 'content': 'Para 2.\n'},
    {'type': 'minor_header', 'content': 'Section Break'},
    {'type': 'text', 'content': 'Para 3.\n'},
    {'type': 'text', 'content': 'Para 4.\n'}
]

# Process:
# Para 1-2: Accumulate
# Header: Flush (Para 1-2), add header, reset
# Para 3-4: Accumulate
# End: Flush (Para 3-4)

# Output:
consolidated = [
    {'type': 'text', 'content': 'Para 1.\n\nPara 2.\n'},
    {'type': 'minor_header', 'content': 'Section Break'},
    {'type': 'text', 'content': 'Para 3.\n\nPara 4.\n'}
]
```

---

## 💡 Design Decisions

### Why Not Merge Lists?

```python
# ❌ If we merged lists:
sections = [
    {'type': 'text', 'content': '- Item 1\n- Item 2\n'},
    {'type': 'text', 'content': '- Item 3\n- Item 4\n'}
]
# Would become:
merged = {'type': 'text', 'content': '- Item 1\n- Item 2\n\n- Item 3\n- Item 4\n'}
# Looks like TWO separate lists!

# ✅ Keep lists separate:
# Each list is its own semantic unit
```

### Why Not Merge Across Headers?

```python
# ❌ If we merged across headers:
sections = [
    {'type': 'text', 'content': 'Intro paragraph.\n'},
    {'type': 'major_header', 'content': 'New Section'},
    {'type': 'text', 'content': 'New section paragraph.\n'}
]
# Would become one section mixing topics!

# ✅ Headers are semantic boundaries:
# They signal topic changes
# Don't merge across them
```

### Why Join with "\n\n" Not Single "\n"?

```python
# Single \n:
"Para 1.\nPara 2.\nPara 3."
# Renders as one block - no visual separation

# Double \n\n:
"Para 1.\n\nPara 2.\n\nPara 3."
# Renders with blank lines - clear separation
```

---

## 🔑 Key Edge Cases

### Edge Case 1: Single Paragraph

```python
# Input:
sections = [{'type': 'text', 'content': 'Only one paragraph.\n'}]

# Process:
# Accumulates in text_group
# No flush during loop (only one item)
# Final flush creates section

# Output:
consolidated = [{'type': 'text', 'content': 'Only one paragraph.\n'}]
# No "\n\n" joining (only one element)
```

### Edge Case 2: Empty Sections

```python
# Input:
sections = []

# Process:
# Loop doesn't execute
# text_group stays empty
# Final flush check: if text_group: → False

# Output:
consolidated = []  # Empty
```

### Edge Case 3: All Headers

```python
# Input:
sections = [
    {'type': 'major_header', 'content': 'Title 1'},
    {'type': 'major_header', 'content': 'Title 2'},
    {'type': 'minor_header', 'content': 'Title 3'}
]

# Process:
# Each is non-text, added directly
# text_group never accumulates

# Output:
consolidated = sections  # Unchanged
```

### Edge Case 4: Paragraphs at End

```python
# Input:
sections = [
    {'type': 'major_header', 'content': 'Title'},
    {'type': 'text', 'content': 'Para 1.\n'},
    {'type': 'text', 'content': 'Para 2.\n'}
    # No more sections!
]

# Process:
# Header: Added
# Para 1-2: Accumulated in text_group
# Loop ends with text_group = ['Para 1.\n', 'Para 2.\n']

# Final flush (CRITICAL):
if text_group:  # True
    consolidated.append(...)

# Without final flush, Para 1-2 would be lost!
```

---

## 📈 Performance

### Time Complexity

**O(n)** where n = number of sections

- Single pass through sections
- Each section examined once
- String joining is O(k) where k = accumulated paragraph count (typically small)

### Space Complexity

**O(m)** where m = number of consolidated sections

- text_group is temporary (bounded by consecutive paragraphs, typically < 10)
- consolidated grows with output

### Optimization

```python
# Efficient string joining
content = '\n\n'.join(text_group)
# Not:
# content = text_group[0]
# for t in text_group[1:]:
#     content += '\n\n' + t  # Creates new string each time!
```

---

## 🐛 Debugging Tips

### Tip 1: Log Group Size

```python
if text_group:
    logger.debug(f"Flushing {len(text_group)} paragraphs")
    logger.debug(f"Total length: {sum(len(t) for t in text_group)} chars")
```

### Tip 2: Track List Detection

```python
is_list = ...
if is_list:
    logger.debug(f"Detected list: {section['content'][:50]}...")
```

### Tip 3: Count Before/After

```python
logger.debug(f"Before: {len(sections)} sections")
result = consolidate_paragraphs(sections, config, logger)
logger.debug(f"After: {len(result)} sections (merged {len(sections) - len(result)})")
```

---

## 📋 Quick Reference

| Input Type | Accumulated? | Triggers Flush? |
|-----------|-------------|----------------|
| Regular paragraph | ✅ Yes | ❌ No |
| List (bullet/numbered) | ❌ No | ✅ Yes |
| Header (major/minor) | ❌ No | ✅ Yes |
| Table | ❌ No | ✅ Yes |
| Image | ❌ No | ✅ Yes |
| Code | ❌ No | ✅ Yes |

---

## 🎓 Summary

**`consolidate_paragraphs()`** solves the "tiny paragraph problem" by:

1. ✅ Grouping consecutive regular paragraphs
2. ✅ Preserving list integrity (don't merge)
3. ✅ Respecting semantic boundaries (headers)
4. ✅ Joining with proper markdown separation (`\n\n`)
5. ✅ Maintaining hierarchical context (breadcrumbs)

**Result**: Meaningful text sections ready for intelligent chunking!

### Before → After

```python
# BEFORE: 5 tiny paragraphs (40-50 chars each)
[para1, para2, para3, para4, para5]

# AFTER: 1 coherent section (200+ chars)
[consolidated_section]

# Impact: 
# - Fewer chunks overall
# - More context per chunk
# - Better semantic coherence
# - Meets minimum size requirements
```

**This function is the bridge between parsing and chunking!**
