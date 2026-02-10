# Semantic Chunking - Real Example Walkthrough

## Using Your Actual Document Data

This guide walks through **exactly** how semantic chunking works using your real extracted chunks from the Morgan Stanley AI research report.

---

## Your Input Data

### Summary of Atomic Chunks

**Document:** AI-Enablers-Adopters-research-report (7 pages)

**Total atomic chunks:** 78 chunks
- 40 paragraphs
- 19 images
- 13 headers
- 4 formulas (note: formula detection will be removed)
- 2 tables

**Average size:** ~150 chars per chunk (too small for RAG!)

---

## Page 1 Analysis

Let's trace through **exactly** what happens with Page 1 chunks:

### Input: 14 Atomic Chunks from Page 1

```python
page_1_chunks = [
    # Chunk 1
    {
        'id': 'p1_header_1',
        'type': 'header',
        'content': '## Thematics',
        'metadata': {'breadcrumbs': 'Thematics'}
    },
    # Size: 13 chars
    
    # Chunk 2
    {
        'id': 'p1_header_2',
        'type': 'header',
        'content': "## Uncovering Alpha in AI's Rate of Change",
        'metadata': {'breadcrumbs': "Uncovering Alpha in AI's Rate of Change"}
    },
    # Size: 42 chars
    
    # Chunk 3
    {
        'id': 'p1_text_1',
        'type': 'paragraph',
        'content': "More than two years since ChatGPT's launch, we remain in the early innings of AI's diffusion...",
        'metadata': {'breadcrumbs': "Uncovering Alpha in AI's Rate of Change"}
    },
    # Size: 290 chars
    
    # Chunk 4
    {
        'id': 'p1_text_2',
        'type': 'paragraph',
        'content': "AI's Rate of Change Continues to Surprise: Our first AI Adopter survey...",
        'metadata': {'breadcrumbs': "Uncovering Alpha in AI's Rate of Change"}
    },
    # Size: 535 chars
    
    # Chunk 5
    {
        'id': 'p1_text_3',
        'type': 'paragraph',
        'content': "AI's Rate of Change Has Driven Outperformance: Exhibit 1 shows...",
        'metadata': {'breadcrumbs': "Uncovering Alpha in AI's Rate of Change"}
    },
    # Size: 485 chars
    
    # Chunk 6
    {
        'id': 'p1_text_4',
        'type': 'paragraph',
        'content': "2025 - Agentic AI Adopters: As in previous tech cycles...",
        'metadata': {'breadcrumbs': "Uncovering Alpha in AI's Rate of Change"}
    },
    # Size: 630 chars
    
    # Chunk 7 - IMAGE with caption
    {
        'id': 'p1_image_1',
        'type': 'image',
        'content': """**Image**
*Caption:* Exhibit 1: Stock returns where both materiality and exposure were increased
![fig_p1_1.png](../figures/fig_p1_1.png)
*AI Analysis:* This is a line chart showing stock returns...""",
        'metadata': {'breadcrumbs': "Uncovering Alpha in AI's Rate of Change"}
    },
    # Size: ~600 chars (image + caption + AI analysis)
    
    # Chunk 8
    {
        'id': 'p1_text_5',
        'type': 'paragraph',
        'content': 'Source: Eikon, MS Research. Past performance is no guarantee...',
        'metadata': {'breadcrumbs': "Uncovering Alpha in AI's Rate of Change"}
    },
    # Size: 127 chars
    
    # Chunk 9 - Small image (logo)
    {
        'id': 'p1_image_2',
        'type': 'image',
        'content': '**Image**\n![fig_p1_2.png]...',
        'metadata': {'breadcrumbs': "Uncovering Alpha in AI's Rate of Change"}
    },
    # Size: ~150 chars
    
    # Chunk 10 - Large table with AI analysis
    {
        'id': 'p1_table_1',
        'type': 'table',
        'content': """| Name | Phone |
|------|-------|
| Morgan Stanley & Co...
...
*AI Analysis:* Contact information table for Morgan Stanley professionals...""",
        'metadata': {'breadcrumbs': "Uncovering Alpha in AI's Rate of Change"}
    },
    # Size: ~2000 chars (big table!)
    
    # Chunks 11-14: More small paragraphs (100-350 chars each)
]
```

---

## Semantic Chunking Process

### Parameters
```python
target_size = 1500  # Try to create ~1500 char chunks
min_size = 800      # Don't flush if < 800 chars on section change
```

### Step-by-Step Processing

#### **Step 1: Process p1_header_1**

```python
# Current state
buffer = []
buffer_size = 0
current_breadcrumb = None

# Process chunk
chunk = {'id': 'p1_header_1', 'content': '## Thematics', 'breadcrumbs': 'Thematics'}

# Check: Section changed? No (first chunk)
# Action: Add to buffer
buffer = [p1_header_1]
buffer_size = 13
current_breadcrumb = 'Thematics'

# Check: buffer_size >= target_size? 13 >= 1500? NO
# Don't flush
```

#### **Step 2: Process p1_header_2**

```python
# Current state
buffer = [p1_header_1]
buffer_size = 13
current_breadcrumb = 'Thematics'

# Process chunk
chunk = {'id': 'p1_header_2', 'breadcrumbs': "Uncovering Alpha in AI's Rate of Change"}

# Check: Section changed? 'Thematics' != "Uncovering Alpha..."? YES!
# Check: buffer_size >= min_size? 13 >= 800? NO
# Don't flush (buffer too small)

# Action: Add to buffer anyway
buffer = [p1_header_1, p1_header_2]
buffer_size = 55
current_breadcrumb = "Uncovering Alpha in AI's Rate of Change"

# Check: buffer_size >= target_size? 55 >= 1500? NO
# Don't flush
```

**Key Point:** Even though section changed, buffer is too small (13 < 800), so we keep accumulating.

#### **Step 3-6: Process p1_text_1 through p1_text_4**

```python
# After adding p1_text_1
buffer = [p1_header_1, p1_header_2, p1_text_1]
buffer_size = 345
current_breadcrumb = "Uncovering Alpha in AI's Rate of Change"
# Still small, keep going...

# After adding p1_text_2
buffer = [p1_header_1, p1_header_2, p1_text_1, p1_text_2]
buffer_size = 880
current_breadcrumb = "Uncovering Alpha in AI's Rate of Change"
# Getting close to target!

# After adding p1_text_3
buffer = [p1_header_1, p1_header_2, p1_text_1, p1_text_2, p1_text_3]
buffer_size = 1365
current_breadcrumb = "Uncovering Alpha in AI's Rate of Change"
# Almost at target (1365/1500 = 91%)

# After adding p1_text_4
buffer = [p1_header_1, p1_header_2, p1_text_1, p1_text_2, p1_text_3, p1_text_4]
buffer_size = 1995
current_breadcrumb = "Uncovering Alpha in AI's Rate of Change"

# Check: buffer_size >= target_size? 1995 >= 1500? YES!
# FLUSH! Create semantic chunk
```

#### **FLUSH #1: Create First Semantic Chunk**

```python
semantic_chunk_1 = {
    'combined_content': """
## Thematics

## Uncovering Alpha in AI's Rate of Change

More than two years since ChatGPT's launch, we remain in the early innings of AI's diffusion. This is the third iteration of the most comprehensive AI stock mapping exercise in the market. Rate of change continues to drive outperformance, and we believe 2025 will be the year of Agentic AI.

AI's Rate of Change Continues to Surprise: Our first AI Adopter survey was published in January 2024, our second in June 2024. This is our third such analysis. We have been surprised by the continued extent of changes made by our analysts across >3,700 global stocks under coverage. 585 stocks had their AI exposure or materiality changed ($13trn of market cap). AI model capabilities and costs continue to evolve rapidly and corporate adoption is still low. AI's diffusion is accelerating but decidedly remains in its early innings.

AI's Rate of Change Has Driven Outperformance: Exhibit 1 shows the 2H24 outperformance of stocks which previously saw their exposure and materiality increased. Looking forward, overweight rated stocks matching these criteria in this latest survey have 29% upside to price targets. We explain how to access and use our database and sees three opportunities ahead: (1) Enablers with rising materiality; (2) Adopters with pricing power; (3) Financials with AI 'Rate of Change' tailwinds.

2025 - Agentic AI Adopters: As in previous tech cycles, the equity markets are poised for Semiconductor leadership to give way to the Software Layer. That process is underway. Simply put, AI Agents give "agency" to software programs. In other words AI Adopter companies can move from the reactive "chatbot phase" to the proactive "task-fulfillment phase" of AI; entailing broad productivity gains. We believe 2025 will be a year of Agentic AI, robust enterprise adoption, outperformance of favoured Agentic plays, positive surprises in model capabilities, greater breadth of monetisation and thus diminishing focus on ROI debates.
""",
    'chunk_ids': [
        'p1_header_1',
        'p1_header_2', 
        'p1_text_1',
        'p1_text_2',
        'p1_text_3',
        'p1_text_4'
    ],
    'breadcrumbs': "Uncovering Alpha in AI's Rate of Change",
    'char_count': 1995,
    'num_chunks': 6
}

# Reset buffer
buffer = []
buffer_size = 0
```

**Result:** Created a 1995-char semantic chunk (33% overshoot of 1500 target, but preserves integrity!)

#### **Step 7: Process p1_image_1**

```python
# Current state (after flush)
buffer = []
buffer_size = 0
current_breadcrumb = "Uncovering Alpha in AI's Rate of Change"

# Process image chunk (~600 chars)
buffer = [p1_image_1]
buffer_size = 600

# Check: buffer_size >= target_size? 600 >= 1500? NO
# Keep accumulating
```

#### **Step 8-9: Process p1_text_5 and p1_image_2**

```python
# After adding p1_text_5
buffer = [p1_image_1, p1_text_5]
buffer_size = 727

# After adding p1_image_2
buffer = [p1_image_1, p1_text_5, p1_image_2]
buffer_size = 877

# Still under target, keep going...
```

#### **Step 10: Process p1_table_1 (BIG TABLE)**

```python
# Current state
buffer = [p1_image_1, p1_text_5, p1_image_2]
buffer_size = 877

# Process huge table (~2000 chars)
buffer.append(p1_table_1)
buffer_size = 2877  # OVERSHOOT!

# Check: buffer_size >= target_size? 2877 >= 1500? YES!
# FLUSH!
```

#### **FLUSH #2: Create Second Semantic Chunk**

```python
semantic_chunk_2 = {
    'combined_content': """
**Image**
*Caption:* Exhibit 1: Stock returns where both materiality and exposure were increased
![fig_p1_1.png](../figures/fig_p1_1.png)
*AI Analysis:* This is a line chart showing...

Source: Eikon, MS Research. Past performance is no guarantee of future results.

**Image**
![fig_p1_2.png](../figures/fig_p1_2.png)
*AI Analysis:* The image displays a logo with the text "GLOBAL INSIGHT."

| Name | Phone |
|------|-------|
| Morgan Stanley & Co. International Edward Stanley... | +44 20 7425-0840 |
...
*AI Analysis:* Contact information table listing team members...
""",
    'chunk_ids': ['p1_image_1', 'p1_text_5', 'p1_image_2', 'p1_table_1'],
    'breadcrumbs': "Uncovering Alpha in AI's Rate of Change",
    'char_count': 2877,
    'num_chunks': 4
}

# Reset
buffer = []
buffer_size = 0
```

**Result:** Created a 2877-char chunk (92% overshoot, but needed to include complete table!)

#### **Steps 11-14: Process Remaining Paragraphs**

```python
# Small disclaimers/legal text
# After processing all remaining chunks:
buffer = [p1_text_6, p1_text_7, p1_text_8, p1_text_9]
buffer_size = 863

# End of page 1
# FLUSH remaining buffer
```

#### **FLUSH #3: Final Chunk from Page 1**

```python
semantic_chunk_3 = {
    'combined_content': """
Please click here for the full excel database of >3,700 stocks mapped by AI exposure and materiality.

Morgan Stanley does and seeks to do business with companies covered in Morgan Stanley Research. As a result, investors should be aware that the firm may have a conflict of interest that could affect the objectivity of Morgan Stanley Research. Investors should consider Morgan Stanley Research as only a single factor in making their investment decision.

For analyst certification and other important disclosures, refer to the Disclosure Section, located at the end of this report.

+= Analysts employed by non-U.S. affiliates are not registered with FINRA...
""",
    'chunk_ids': ['p1_text_6', 'p1_text_7', 'p1_text_8', 'p1_text_9'],
    'breadcrumbs': "Uncovering Alpha in AI's Rate of Change",
    'char_count': 863,
    'num_chunks': 4
}
```

---

## Page 1 Results Summary

### Before: 14 Atomic Chunks
- Chunk 1: 13 chars (header)
- Chunk 2: 42 chars (header)
- Chunk 3: 290 chars (paragraph)
- Chunk 4: 535 chars (paragraph)
- Chunk 5: 485 chars (paragraph)
- Chunk 6: 630 chars (paragraph)
- Chunk 7: ~600 chars (image)
- Chunk 8: 127 chars (paragraph)
- Chunk 9: ~150 chars (image)
- Chunk 10: ~2000 chars (table)
- Chunks 11-14: ~600 chars total

**Total:** ~5500 chars across 14 tiny chunks

### After: 3 Semantic Chunks
1. **Main content:** 1995 chars (6 chunks combined)
2. **Visual content:** 2877 chars (4 chunks combined)
3. **Legal text:** 863 chars (4 chunks combined)

**Total:** Same ~5500 chars but in 3 coherent chunks instead of 14!

---

## Page 2 Processing

### Section Change Example

Page 2 starts with new section: `"Mapping AI's Rate of Change in Charts"`

```python
# Processing first chunk of page 2
chunk = {
    'id': 'p2_header_1',
    'breadcrumbs': "Mapping AI's Rate of Change in Charts"  # NEW SECTION!
}

# Current state (from end of page 1)
current_breadcrumb = "Uncovering Alpha in AI's Rate of Change"

# Check: Section changed?
"Mapping AI's Rate of Change in Charts" != "Uncovering Alpha in AI's Rate of Change"
# YES! Section changed!

# Check: buffer_size >= min_size?
# (If buffer had content, would check)

# Start new section
buffer = [p2_header_1]
current_breadcrumb = "Mapping AI's Rate of Change in Charts"
```

### Another Section Change (Exhibit 6)

Later on page 2:

```python
# After accumulating several chunks about "Mapping AI's Rate of Change"
buffer_size = 1200
current_breadcrumb = "Mapping AI's Rate of Change in Charts"

# New chunk
chunk = {
    'id': 'p2_header_2',
    'content': '## Exhibit 6:',
    'breadcrumbs': 'Exhibit 6:'  # SECTION CHANGE!
}

# Check: Section changed? YES!
# Check: buffer_size >= min_size? 1200 >= 800? YES!
# FLUSH current buffer

# Then start new buffer with Exhibit 6 content
```

---

## Complete Document Results

### Estimated Final Output

**Original:** 78 atomic chunks
- Page 1: 14 chunks
- Page 2: 12 chunks
- Page 3: 10 chunks
- Page 4: 15 chunks
- Page 5: 9 chunks
- Page 6: 10 chunks
- Page 7: 8 chunks

**After Semantic Chunking (estimated):** ~15-20 semantic chunks
- Average size: ~1500-2000 chars
- Each chunk: 3-6 atomic chunks combined
- Sections preserved
- No broken paragraphs
- Images with their captions
- Tables complete

---

## Key Insights from Your Data

### 1. Headers Get Included Naturally

```python
# Your headers are small (13-42 chars)
# They get combined with following content
# Result: Each semantic chunk has context!

Semantic Chunk:
"## Executive Summary
This is the third mapping of our global coverage..."
```

### 2. Images with Captions Stay Together

```python
# Your images have captions and AI analysis
# Total: ~600 chars per image
# They stay complete in semantic chunks!

Semantic Chunk with image:
"**Image**
*Caption:* Exhibit 1: Stock returns...
![fig_p1_1.png]...
*AI Analysis:* This is a line chart showing..."
```

### 3. Large Tables Cause Overshoot

```python
# Your contact table: ~2000 chars
# When added to 877-char buffer → 2877 chars
# Overshoot: 92% (but table stays complete!)

This is GOOD! Better to have 2877-char chunk
than break table in half.
```

### 4. Section Changes Create Natural Breaks

```python
# Page 1 has one main section: "Uncovering Alpha..."
# → Most content combined into 2-3 big chunks

# Page 2 has TWO sections:
# - "Mapping AI's Rate of Change in Charts"
# - "Exhibit 6:"
# → Creates natural break between sections
```

---

## Size Distribution Analysis

### Your Atomic Chunks (Before)

```
Size Distribution:
13 chars   ████ (headers)
42 chars   ████ (headers)
127 chars  ████████████ (short paragraphs)
290 chars  ████████████████████ (medium paragraphs)
535 chars  ████████████████████████████ (long paragraphs)
600 chars  ███████████████████████████████ (images)
2000 chars █████████████████████████████████████████████ (tables)

Problems:
- Headers too small (no context)
- Short paragraphs lack context
- Inefficient for retrieval (78 chunks!)
```

### After Semantic Chunking

```
Size Distribution:
800 chars  ████████████ (small sections)
1500 chars █████████████████████████ (typical chunks)
2000 chars ████████████████████████████████ (with images)
2877 chars ████████████████████████████████████████ (with tables)

Benefits:
- Headers included with content
- Paragraphs have full context
- Images with captions
- Tables complete
- 15-20 chunks (5x reduction!)
```

---

## Why This Works for RAG

### Query: "What is Agentic AI?"

**With Atomic Chunks (POOR):**
```python
# Vector search returns:
1. "## Uncovering Alpha in AI's Rate of Change"  # Just header!
2. "2025 - Agentic AI Adopters: As in previous..." # Fragment
3. "More than two years since ChatGPT's launch..." # Not relevant

# LLM gets:
- Incomplete context
- Missing connections
- No full explanation
```

**With Semantic Chunks (GOOD):**
```python
# Vector search returns:
1. Entire semantic chunk (1995 chars) including:
   - Headers for context
   - Full explanation of Agentic AI
   - Comparison to previous cycles
   - Forward-looking predictions

# LLM gets:
- Complete context
- Full explanation
- Related information
- Can answer confidently
```

### Query: "Show me the stock performance chart"

**With Atomic Chunks (POOR):**
```python
# Returns:
- Image reference
- Missing caption
- No explanation of what chart shows
```

**With Semantic Chunks (GOOD):**
```python
# Returns entire chunk with:
- Exhibit 1 caption
- Image reference
- AI analysis of chart
- Source citation
- Related context
```

---

## Implementation for Your Data

### Simple Usage

```python
from simple_chunker import chunk_directory, create_semantic_chunks

# 1. Load your atomic chunks
results = chunk_directory(Path("extracted_docs_bounded"))
atomic_chunks = []
for file_chunks in results.values():
    atomic_chunks.extend(file_chunks)

# 2. Create semantic chunks
semantic_chunks = create_semantic_chunks(
    atomic_chunks,
    target_size=1500,  # Good for your content
    min_size=800       # Prevents tiny section chunks
)

# 3. Result
print(f"Reduced from {len(atomic_chunks)} to {len(semantic_chunks)} chunks")
# Output: "Reduced from 78 to ~18 chunks"

# 4. Use in RAG
for chunk in semantic_chunks:
    # Create embedding
    embedding = model.encode(chunk['combined_content'])
    
    # Store in vector DB
    vector_db.upsert({
        'id': chunk['chunk_ids'][0],  # Use first chunk ID
        'content': chunk['combined_content'],
        'metadata': {
            'breadcrumbs': chunk['breadcrumbs'],
            'num_source_chunks': chunk['num_chunks'],
            'char_count': chunk['char_count']
        },
        'embedding': embedding
    })
```

---

## Summary

### Your Document Transformation

**Before:**
- 78 atomic chunks
- Average 150 chars
- Headers isolated
- Images fragmented
- Poor for retrieval

**After:**
- ~18 semantic chunks
- Average 1500-2000 chars
- Headers with context
- Images complete
- Excellent for RAG

### The Algorithm Did This:

1. ✅ Combined related content (same breadcrumbs)
2. ✅ Respected section boundaries
3. ✅ Kept images with captions
4. ✅ Preserved table integrity
5. ✅ Never broke mid-paragraph
6. ✅ Created right-sized chunks for RAG

### Size Overshoot is OK!

Your data shows this perfectly:
- Target: 1500 chars
- Chunk with table: 2877 chars (92% overshoot)
- **But:** Table stays complete! ✅
- **Better than:** Splitting table in half ❌

---

## Next Steps

1. **Run the chunker:**
   ```bash
   python chunker.py extracted_docs_bounded/ --semantic
   ```

2. **Check output:**
   ```bash
   # Creates: extracted_docs_bounded/semantic_chunks.json
   # Contains both atomic and semantic chunks
   ```

3. **Use in your RAG system:**
   - Load semantic_chunks
   - Create embeddings
   - Store in vector DB
   - Query and retrieve!

Your data is perfect for semantic chunking - it will reduce retrieval complexity by 4-5x while improving answer quality! 🎯
