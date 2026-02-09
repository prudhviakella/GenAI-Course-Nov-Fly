# Semantic Chunking - Complete Guide

## Table of Contents
1. [The Problem](#the-problem)
2. [What is Semantic Chunking?](#what-is-semantic-chunking)
3. [How It Works](#how-it-works)
4. [Step-by-Step Example](#step-by-step-example)
5. [Parameters Explained](#parameters-explained)
6. [Real-World Example](#real-world-example)
7. [Algorithm Walkthrough](#algorithm-walkthrough)
8. [Use Cases](#use-cases)

---

## The Problem

### Atomic Chunks vs Semantic Chunks

**Atomic Chunks** (from boundary markers):
```
Chunk 1: "Introduction to Machine Learning"    [50 chars]
Chunk 2: "Machine learning is..."               [150 chars]
Chunk 3: "There are three types..."             [120 chars]
Chunk 4: "Supervised learning uses..."          [140 chars]
Chunk 5: "Methods"                              [7 chars]
Chunk 6: "We collected data from..."            [180 chars]
```

**Problems with Atomic Chunks for RAG:**
- Too small (50-180 chars) - not enough context
- Headers separated from content
- Related paragraphs split apart
- Inefficient for retrieval (too many chunks)

**Solution: Combine into Semantic Chunks:**
```
Semantic Chunk 1:
"Introduction to Machine Learning
Machine learning is...
There are three types...
Supervised learning uses..."
[460 chars, coherent context]

Semantic Chunk 2:
"Methods
We collected data from..."
[187 chars, complete section]
```

---

## What is Semantic Chunking?

**Semantic Chunking** = Combining small atomic chunks into larger, meaningful units while preserving semantic boundaries.

### Goals

1. **Right Size** - Large enough for context (800-2000 chars)
2. **Semantic Coherence** - Keep related content together
3. **Section Boundaries** - Don't mix unrelated sections
4. **Efficient Retrieval** - Fewer, better chunks

### Strategy

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: Atomic Chunks (78 small chunks)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ GROUP by Section (using breadcrumbs)                        │
│ - Introduction section chunks                               │
│ - Methods section chunks                                    │
│ - Results section chunks                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ COMBINE until target size (1500 chars)                      │
│ - Add chunks to buffer                                      │
│ - When buffer ≥ 1500 chars → create semantic chunk         │
│ - When section changes → create semantic chunk             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: Semantic Chunks (15-20 larger chunks)               │
│ Each chunk has:                                             │
│ - Combined content (1500 chars)                             │
│ - Source chunk IDs                                          │
│ - Section breadcrumbs                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## How It Works

### The Algorithm

```python
def create_semantic_chunks(chunks, target_size=1500, min_size=800):
    semantic_chunks = []
    buffer = []              # Temporary storage for chunks
    buffer_size = 0          # Total characters in buffer
    current_breadcrumb = None  # Current section
    
    for chunk in chunks:
        breadcrumb = chunk['metadata']['breadcrumbs']
        
        # RULE 1: Section changed + buffer is big enough → FLUSH
        if breadcrumb != current_breadcrumb and buffer_size >= min_size:
            semantic_chunks.append(combine(buffer))
            buffer = []
            buffer_size = 0
        
        # ADD chunk to buffer
        buffer.append(chunk)
        buffer_size += len(chunk['content'])
        current_breadcrumb = breadcrumb
        
        # RULE 2: Buffer reached target size → FLUSH
        if buffer_size >= target_size:
            semantic_chunks.append(combine(buffer))
            buffer = []
            buffer_size = 0
    
    # RULE 3: Flush remaining chunks at end
    if buffer:
        semantic_chunks.append(combine(buffer))
    
    return semantic_chunks
```

### Key Concepts

1. **Buffer** - Temporary storage accumulating chunks
2. **Breadcrumbs** - Section hierarchy (e.g., "Intro > Methods")
3. **Flush** - Create a semantic chunk and clear buffer
4. **Target Size** - Ideal character count (1500)
5. **Min Size** - Minimum before flushing (800)

---

## Step-by-Step Example

### Input: Atomic Chunks

```python
chunks = [
    {
        'id': 'p1_header_1',
        'content': '## Introduction',
        'metadata': {'breadcrumbs': 'Introduction'}
    },
    {
        'id': 'p1_text_1',
        'content': 'Machine learning is a field of AI...',  # 200 chars
        'metadata': {'breadcrumbs': 'Introduction'}
    },
    {
        'id': 'p1_text_2',
        'content': 'There are three main types...',  # 300 chars
        'metadata': {'breadcrumbs': 'Introduction'}
    },
    {
        'id': 'p1_text_3',
        'content': 'Supervised learning uses labeled data...',  # 400 chars
        'metadata': {'breadcrumbs': 'Introduction'}
    },
    {
        'id': 'p2_header_1',
        'content': '## Methods',
        'metadata': {'breadcrumbs': 'Methods'}
    },
    {
        'id': 'p2_text_1',
        'content': 'We collected data from 1000 participants...',  # 600 chars
        'metadata': {'breadcrumbs': 'Methods'}
    }
]
```

### Processing Steps

**Parameters:**
- `target_size = 1000`
- `min_size = 500`

**Step 1: Process p1_header_1**
```
buffer = ['## Introduction']
buffer_size = 17
current_breadcrumb = 'Introduction'

Action: Add to buffer (too small to flush)
```

**Step 2: Process p1_text_1**
```
buffer = ['## Introduction', 'Machine learning...']
buffer_size = 217
current_breadcrumb = 'Introduction'

Action: Add to buffer (still small)
```

**Step 3: Process p1_text_2**
```
buffer = ['## Introduction', 'Machine learning...', 'There are three...']
buffer_size = 517
current_breadcrumb = 'Introduction'

Action: Add to buffer (not at target yet)
```

**Step 4: Process p1_text_3**
```
buffer = ['## Introduction', 'Machine learning...', 'There are three...', 'Supervised learning...']
buffer_size = 917
current_breadcrumb = 'Introduction'

Action: Add to buffer
Check: buffer_size (917) < target_size (1000) → don't flush yet
```

**Step 5: Process p2_header_1**
```
New breadcrumb: 'Methods'
Old breadcrumb: 'Introduction'
buffer_size = 917 >= min_size (500)

Action: FLUSH! Section changed and buffer is big enough.

Create Semantic Chunk 1:
{
    'combined_content': '## Introduction\n\nMachine learning...\n\nThere are three...\n\nSupervised learning...',
    'chunk_ids': ['p1_header_1', 'p1_text_1', 'p1_text_2', 'p1_text_3'],
    'breadcrumbs': 'Introduction',
    'char_count': 917,
    'num_chunks': 4
}

Reset buffer:
buffer = ['## Methods']
buffer_size = 10
current_breadcrumb = 'Methods'
```

**Step 6: Process p2_text_1**
```
buffer = ['## Methods', 'We collected data...']
buffer_size = 610
current_breadcrumb = 'Methods'

Action: Add to buffer
```

**Step 7: End of chunks**
```
Remaining buffer: ['## Methods', 'We collected data...']
buffer_size = 610

Action: FLUSH remaining

Create Semantic Chunk 2:
{
    'combined_content': '## Methods\n\nWe collected data...',
    'chunk_ids': ['p2_header_1', 'p2_text_1'],
    'breadcrumbs': 'Methods',
    'char_count': 610,
    'num_chunks': 2
}
```

### Final Output

```python
semantic_chunks = [
    {
        'combined_content': '## Introduction\n\nMachine learning is...\n\nThere are three...\n\nSupervised learning...',
        'chunk_ids': ['p1_header_1', 'p1_text_1', 'p1_text_2', 'p1_text_3'],
        'breadcrumbs': 'Introduction',
        'char_count': 917,
        'num_chunks': 4
    },
    {
        'combined_content': '## Methods\n\nWe collected data...',
        'chunk_ids': ['p2_header_1', 'p2_text_1'],
        'breadcrumbs': 'Methods',
        'char_count': 610,
        'num_chunks': 2
    }
]
```

---

## Parameters Explained

### target_size (default: 1500)

**What it is:** Target character count for semantic chunks

**How it works:**
- When `buffer_size >= target_size` → FLUSH immediately
- Creates chunks around this size
- Can be slightly larger (adds full chunks, doesn't split mid-chunk)

**Examples:**

```python
# Small chunks (faster retrieval, less context)
target_size = 800
# Result: ~800 char chunks

# Medium chunks (balanced)
target_size = 1500  # DEFAULT
# Result: ~1500 char chunks

# Large chunks (more context, slower retrieval)
target_size = 3000
# Result: ~3000 char chunks
```

**Choosing the right size:**
- **800-1200**: Short documents, Q&A, chatbots
- **1500-2000**: General RAG, articles, reports (RECOMMENDED)
- **2500-4000**: Long-form content, books, legal docs

### min_size (default: 800)

**What it is:** Minimum size before flushing on section change

**How it works:**
- When section changes, only flush if `buffer_size >= min_size`
- Prevents tiny chunks from being created
- If buffer is too small, keep accumulating

**Example:**

```python
# Scenario: Section changes after just 200 chars
buffer_size = 200
min_size = 800

# With min_size check:
if buffer_size >= min_size:  # 200 >= 800 → False
    flush()  # DON'T FLUSH
else:
    continue  # KEEP ADDING to buffer

# Without min_size check:
flush()  # Would create 200-char chunk (too small!)
```

**Edge Case Handling:**

```
Section: Introduction
- Header (20 chars)
- Paragraph (150 chars)

Section: Methods (section changes!)
- buffer_size = 170 < min_size (800)
- DON'T flush yet
- Keep adding Methods content to same buffer
- Now buffer has mixed sections BUT at least it's big enough
```

**Choosing the right min_size:**
- Set to ~50% of target_size
- `target_size = 1500` → `min_size = 800` (good)
- `target_size = 2000` → `min_size = 1000` (good)

---

## Real-World Example

### Document: Research Paper (7 pages, 78 atomic chunks)

**Atomic chunks:**
```python
[
    {'id': 'p1_header_1', 'content': '## Abstract', 'breadcrumbs': 'Abstract'},
    {'id': 'p1_text_1', 'content': 'This study examines...', 'breadcrumbs': 'Abstract'},
    {'id': 'p1_text_2', 'content': 'Our findings show...', 'breadcrumbs': 'Abstract'},
    
    {'id': 'p2_header_1', 'content': '## Introduction', 'breadcrumbs': 'Introduction'},
    {'id': 'p2_text_1', 'content': 'Machine learning has...', 'breadcrumbs': 'Introduction'},
    {'id': 'p2_text_2', 'content': 'Previous work by...', 'breadcrumbs': 'Introduction'},
    {'id': 'p2_text_3', 'content': 'However, these approaches...', 'breadcrumbs': 'Introduction'},
    
    {'id': 'p3_header_1', 'content': '## Methods', 'breadcrumbs': 'Methods'},
    {'id': 'p3_header_2', 'content': '### Data Collection', 'breadcrumbs': 'Methods > Data Collection'},
    {'id': 'p3_text_1', 'content': 'We collected data...', 'breadcrumbs': 'Methods > Data Collection'},
    {'id': 'p3_table_1', 'content': '| Metric | Value |...', 'breadcrumbs': 'Methods > Data Collection'},
    
    # ... 67 more chunks
]
```

**After semantic chunking:**

```python
semantic_chunks = [
    {
        'combined_content': '''## Abstract

This study examines the effectiveness of transformer models in natural language understanding tasks. We conducted experiments across 5 datasets with varying complexity levels.

Our findings show that larger models consistently outperform smaller variants, with performance gains plateauing beyond 1 billion parameters.''',
        
        'chunk_ids': ['p1_header_1', 'p1_text_1', 'p1_text_2'],
        'breadcrumbs': 'Abstract',
        'char_count': 312,
        'num_chunks': 3
    },
    
    {
        'combined_content': '''## Introduction

Machine learning has revolutionized natural language processing over the past decade. From early statistical models to modern neural architectures, the field has seen dramatic improvements in performance.

Previous work by Vaswani et al. (2017) introduced the transformer architecture, which became the foundation for most modern NLP systems. Their attention mechanism allowed models to capture long-range dependencies effectively.

However, these approaches often require massive computational resources and training data, limiting their accessibility to smaller research labs and companies.''',
        
        'chunk_ids': ['p2_header_1', 'p2_text_1', 'p2_text_2', 'p2_text_3'],
        'breadcrumbs': 'Introduction',
        'char_count': 628,
        'num_chunks': 4
    },
    
    {
        'combined_content': '''## Methods

### Data Collection

We collected data from 1000 participants over 6 months. Each participant completed 5 tasks designed to test different aspects of language understanding.

| Metric | Value |
|--------|-------|
| Participants | 1000 |
| Tasks per user | 5 |
| Duration | 6 months |
| Total responses | 5000 |

Data was stored in a PostgreSQL database and preprocessed using standard NLP pipelines.''',
        
        'chunk_ids': ['p3_header_1', 'p3_header_2', 'p3_text_1', 'p3_table_1', 'p3_text_2'],
        'breadcrumbs': 'Methods > Data Collection',
        'char_count': 489,
        'num_chunks': 5
    }
    
    # ... more semantic chunks
]
```

**Results:**
- **Before:** 78 atomic chunks (avg 150 chars each)
- **After:** 15 semantic chunks (avg 1200 chars each)
- **Benefits:**
  - Fewer chunks to search (5x reduction)
  - More context per chunk
  - Sections stay together
  - Better retrieval quality

---

## Algorithm Walkthrough

### Visual Flow Diagram

```
START
  │
  ├─> Initialize:
  │   - buffer = []
  │   - buffer_size = 0
  │   - current_breadcrumb = None
  │
  ├─> FOR each atomic chunk:
  │   │
  │   ├─> Get breadcrumb from chunk
  │   │
  │   ├─> CHECK: Section changed?
  │   │   └─> breadcrumb != current_breadcrumb
  │   │       │
  │   │       └─> CHECK: Buffer big enough?
  │   │           └─> buffer_size >= min_size
  │   │               │
  │   │               YES: FLUSH BUFFER
  │   │               ├─> Create semantic chunk
  │   │               ├─> Add to semantic_chunks list
  │   │               └─> Clear buffer
  │   │
  │   ├─> ADD chunk to buffer
  │   │   └─> buffer.append(chunk)
  │   │   └─> buffer_size += len(chunk)
  │   │   └─> current_breadcrumb = breadcrumb
  │   │
  │   └─> CHECK: Buffer at target?
  │       └─> buffer_size >= target_size
  │           │
  │           YES: FLUSH BUFFER
  │           ├─> Create semantic chunk
  │           ├─> Add to semantic_chunks list
  │           └─> Clear buffer
  │
  └─> END of chunks:
      └─> Any remaining buffer?
          │
          YES: FLUSH BUFFER
          └─> Create final semantic chunk

RETURN semantic_chunks
```

### State Transitions

```
State 1: Empty Buffer
┌─────────────────────┐
│ buffer = []         │
│ buffer_size = 0     │
└─────────────────────┘
         │ Add chunk
         ▼
State 2: Accumulating
┌─────────────────────┐
│ buffer = [c1]       │
│ buffer_size = 200   │
└─────────────────────┘
         │ Add chunk
         ▼
State 3: Growing
┌─────────────────────┐
│ buffer = [c1, c2]   │
│ buffer_size = 500   │
└─────────────────────┘
         │ Add chunk
         ▼
State 4: Near Target
┌─────────────────────┐
│ buffer = [c1,c2,c3] │
│ buffer_size = 1400  │
└─────────────────────┘
         │ Add chunk (reaches 1600)
         ▼
State 5: Flush!
┌─────────────────────┐
│ Create semantic     │
│ chunk from buffer   │
│ → Reset to State 1  │
└─────────────────────┘
```

---

## Use Cases

### Use Case 1: RAG System

**Scenario:** Build a Q&A system over technical documentation

**Without semantic chunking:**
```python
# 500 tiny atomic chunks
query = "How do I configure SSL?"
results = vector_search(query, n=5)

# Results might be:
# 1. "## SSL Configuration"  (just header, no info!)
# 2. "To enable SSL..."  (fragment, missing context)
# 3. "certificates from..."  (mid-sentence!)
```

**With semantic chunking:**
```python
# 50 semantic chunks (10x reduction)
query = "How do I configure SSL?"
results = vector_search(query, n=5)

# Results are:
# 1. "## SSL Configuration
#     To enable SSL, first obtain certificates from a CA.
#     Then configure your server with the paths..."
#     [Complete context, 1500 chars]
```

**Benefits:**
- Fewer irrelevant results
- More complete answers
- Better context for LLM
- Faster retrieval

### Use Case 2: Document Summarization

**Scenario:** Summarize each section of a long report

```python
# Get semantic chunks
semantic_chunks = create_semantic_chunks(atomic_chunks)

# Summarize each section
summaries = []
for chunk in semantic_chunks:
    # Each chunk is a complete section
    summary = llm.summarize(chunk['combined_content'])
    summaries.append({
        'section': chunk['breadcrumbs'],
        'summary': summary
    })

# Result: Section-level summaries
[
    {'section': 'Introduction', 'summary': 'Paper introduces...'},
    {'section': 'Methods', 'summary': 'Data collected from...'},
    {'section': 'Results', 'summary': 'Findings show that...'}
]
```

### Use Case 3: Hierarchical Retrieval

**Scenario:** Two-stage retrieval (coarse → fine)

```python
# Stage 1: Retrieve relevant semantic chunks
semantic_results = search_semantic_chunks(query, n=3)

# Stage 2: Within each semantic chunk, get specific atomic chunks
for sem_chunk in semantic_results:
    atomic_chunk_ids = sem_chunk['chunk_ids']
    atomic_chunks = get_chunks_by_ids(atomic_chunk_ids)
    
    # Now you have both:
    # - Broad context (semantic chunk)
    # - Specific details (atomic chunks)
```

---

## Parameter Tuning Guide

### Choosing Parameters

| Document Type | target_size | min_size | Reason |
|--------------|------------|----------|---------|
| Chat logs | 800 | 400 | Short, conversational |
| Blog posts | 1500 | 800 | Medium-length articles |
| Research papers | 2000 | 1000 | Dense, technical content |
| Legal documents | 2500 | 1200 | Long, detailed sections |
| Books | 3000 | 1500 | Very long-form content |

### Testing Different Sizes

```python
# Experiment with different sizes
for target in [800, 1500, 2000, 3000]:
    min_size = target // 2
    
    semantic = create_semantic_chunks(
        atomic_chunks,
        target_size=target,
        min_size=min_size
    )
    
    print(f"Target: {target}")
    print(f"  Chunks created: {len(semantic)}")
    print(f"  Avg size: {sum(c['char_count'] for c in semantic) / len(semantic)}")
    print(f"  Min size: {min(c['char_count'] for c in semantic)}")
    print(f"  Max size: {max(c['char_count'] for c in semantic)}")
```

**Output:**
```
Target: 800
  Chunks created: 45
  Avg size: 820
  Min size: 650
  Max size: 1100

Target: 1500
  Chunks created: 23
  Avg size: 1480
  Min size: 900
  Max size: 2100

Target: 2000
  Chunks created: 18
  Avg size: 1950
  Min size: 1200
  Max size: 2800
```

---

## Summary

### Key Takeaways

1. **Semantic chunking combines small chunks into meaningful units**
2. **Respects section boundaries (breadcrumbs)**
3. **Two flush triggers:**
   - Buffer reaches target_size
   - Section changes (if buffer >= min_size)
4. **Parameters control chunk size:**
   - `target_size` = ideal size
   - `min_size` = minimum before section flush
5. **Benefits for RAG:**
   - Fewer chunks (faster search)
   - More context (better answers)
   - Semantic coherence (no mixed sections)

### Quick Reference

```python
# Default (good for most use cases)
semantic_chunks = create_semantic_chunks(
    atomic_chunks,
    target_size=1500,
    min_size=800
)

# Short documents
semantic_chunks = create_semantic_chunks(
    atomic_chunks,
    target_size=1000,
    min_size=500
)

# Long documents
semantic_chunks = create_semantic_chunks(
    atomic_chunks,
    target_size=2500,
    min_size=1200
)
```

---

## Next Steps

1. **Experiment** with different `target_size` values
2. **Measure** retrieval quality with your RAG system
3. **Optimize** based on your specific document types
4. **Combine** with other chunking strategies (overlapping, sliding window)

Happy chunking! 🎯
