# Docling PDF Extractor - Complete Technical Guide

## Table of Contents
1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Architecture](#architecture)
4. [Data Flow](#data-flow)
5. [Boundary Marker System](#boundary-marker-system)
6. [Processing Pipeline](#processing-pipeline)
7. [Function Reference](#function-reference)
8. [Complete Examples](#complete-examples)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### What This Tool Does

This tool extracts content from PDF files and adds **invisible boundary markers** around each piece of content. This makes downstream processing (like chunking for RAG) extremely simple and reliable.

**Traditional Approach (Complex):**
```python
# Parse markdown with complex regex
# Guess where paragraphs end
# Risk splitting mid-sentence
# Different logic for tables, images, lists
```

**Our Approach (Simple):**
```python
# Find boundary markers
# Extract content between START and END
# Each boundary = one complete semantic unit
# Metadata embedded in markers
```

### Key Benefits

1. **No Guessing** - Boundaries mark exact content units
2. **Rich Metadata** - Type, page, breadcrumbs all embedded
3. **Simple Chunking** - Just split on markers
4. **Semantic Integrity** - Never split mid-paragraph
5. **AI Descriptions** - Every image/table gets GPT-4 analysis

---

## Core Concepts

### 1. Boundary Markers

**What are they?**

HTML comments that wrap each content piece:

```markdown
<!-- BOUNDARY_START type="paragraph" id="p3_text_5" page="3" char_count="145" -->
Machine learning models require large datasets for training.
<!-- BOUNDARY_END type="paragraph" id="p3_text_5" -->
```

**Why HTML comments?**
- Invisible when markdown is rendered
- Don't interfere with content display
- Easy to parse with regex
- Can contain unlimited metadata

### 2. Content Types

| Type | What It Is | Example |
|------|------------|---------|
| `paragraph` | Regular text | Body paragraphs |
| `header` | Section titles | "# Introduction" |
| `table` | Data tables | Markdown tables |
| `image` | Pictures/charts | ![chart.png] |
| `list` | Bullet/numbered lists | "- Item 1" |
| `code` | Code blocks | ```python ... ``` |
| `formula` | Math equations | $E = mc^2$ |

### 3. Unique IDs

**Format:** `p{page}_{type}_{counter}`

**Examples:**
- `p3_text_5` = 5th text item on page 3
- `p7_image_2` = 2nd image on page 7
- `p1_table_1` = 1st table on page 1

**Why this format?**
- Human readable
- Easy to debug
- Sortable by page
- Unique per document

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT: PDF File                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              DOCLING CONVERTER                               │
│  • Analyzes PDF layout                                       │
│  • Extracts text with structure                              │
│  • Identifies tables, images, headers                        │
│  • Maintains hierarchy                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ITEM PROCESSORS                                 │
│  • process_header()    → Headers with breadcrumbs           │
│  • process_text()      → Regular paragraphs                 │
│  • process_table()     → Tables (text or image)             │
│  • process_image()     → Images with AI descriptions        │
│  • process_list()      → Bullet/numbered lists              │
│  • process_special_text() → Code/formulas                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              BOUNDARY WRAPPER                                │
│  • Adds START marker with metadata                          │
│  • Adds content                                              │
│  • Adds END marker                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              OUTPUT: Markdown Files                          │
│  • extracted_docs_bounded/                                   │
│    └── document_name/                                        │
│        ├── pages/                                            │
│        │   ├── page_1.md                                     │
│        │   ├── page_2.md                                     │
│        │   └── ...                                           │
│        ├── figures/                                          │
│        │   ├── fig_p1_1.png                                  │
│        │   └── ...                                           │
│        └── metadata.json                                     │
└─────────────────────────────────────────────────────────────┘
```

### Function Hierarchy

```
main()
  └── process_batch()
        ├── create_docling_converter()
        └── process_pdf() [for each PDF]
              ├── Docling conversion
              ├── Collect items by page
              └── For each page:
                    ├── process_header()
                    │     └── wrap_with_boundaries()
                    │
                    ├── process_text()
                    │     ├── process_special_text() [code/formula detection]
                    │     └── wrap_with_boundaries()
                    │
                    ├── process_image()
                    │     ├── extract_and_save_image()
                    │     │     ├── get image from PDF
                    │     │     ├── save to disk
                    │     │     └── describe_image_with_ai()
                    │     └── wrap_with_boundaries()
                    │
                    ├── process_table()
                    │     ├── Try text extraction
                    │     │     ├── export to dataframe
                    │     │     ├── describe_table_with_ai()
                    │     │     └── wrap_with_boundaries()
                    │     └── If failed, try image extraction
                    │           └── [same as process_image]
                    │
                    └── process_list()
                          └── wrap_with_boundaries()
```

---

## Data Flow

### End-to-End Example

Let's trace a single paragraph through the system:

#### Step 1: PDF Input

```
PDF Page 3 contains:
┌────────────────────────────────────┐
│ # Methods                          │
│                                    │
│ We collected data from 1000        │
│ participants over 6 months.        │
└────────────────────────────────────┘
```

#### Step 2: Docling Extraction

Docling identifies:
```python
[
    SectionHeaderItem(text="Methods", level=1),
    TextItem(text="We collected data from 1000 participants over 6 months.")
]
```

#### Step 3: Header Processing

```python
# Input
item = SectionHeaderItem(text="Methods", level=1)
page = 3
breadcrumbs = ["Introduction"]

# Processing
generate_unique_id(3, "header")  # Returns "p3_header_1"
breadcrumbs.append("Methods")     # Updates to ["Introduction", "Methods"]

# Output
```markdown
<!-- BOUNDARY_START type="header" id="p3_header_1" page="3" level="1" breadcrumbs="Introduction > Methods" -->
## Methods
<!-- BOUNDARY_END type="header" id="p3_header_1" -->
```
```

#### Step 4: Text Processing

```python
# Input
item = TextItem(text="We collected data from 1000 participants over 6 months.")
page = 3
breadcrumbs = ["Introduction", "Methods"]

# Processing
text = "We collected data from 1000 participants over 6 months."
generate_unique_id(3, "text")  # Returns "p3_text_1"
char_count = 58
word_count = 10

# Output
```markdown
<!-- BOUNDARY_START type="paragraph" id="p3_text_1" page="3" char_count="58" word_count="10" breadcrumbs="Introduction > Methods" -->
We collected data from 1000 participants over 6 months.
<!-- BOUNDARY_END type="paragraph" id="p3_text_1" -->
```
```

#### Step 5: File Output

`page_3.md`:
```markdown
<!-- Context: Introduction > Methods -->

# Page 3

<!-- BOUNDARY_START type="header" id="p3_header_1" page="3" level="1" breadcrumbs="Introduction > Methods" -->
## Methods
<!-- BOUNDARY_END type="header" id="p3_header_1" -->

<!-- BOUNDARY_START type="paragraph" id="p3_text_1" page="3" char_count="58" word_count="10" breadcrumbs="Introduction > Methods" -->
We collected data from 1000 participants over 6 months.
<!-- BOUNDARY_END type="paragraph" id="p3_text_1" -->
```

---

## Boundary Marker System

### Anatomy of a Boundary

```markdown
<!-- BOUNDARY_START type="paragraph" id="p3_text_5" page="3" char_count="145" word_count="25" breadcrumbs="Intro > Methods" -->
                    ^              ^          ^            ^                  ^                  ^
                    |              |          |            |                  |                  |
                What type?    Unique ID   Page number  How many chars?  How many words?  Where in doc?
```

### Metadata Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `type` | Required | Content type | "paragraph", "header", "image" |
| `id` | Required | Unique identifier | "p3_text_5" |
| `page` | Required | Page number | "3" |
| `level` | Headers only | Hierarchy level | "1", "2", "3" |
| `char_count` | Paragraphs | Character count | "145" |
| `word_count` | Paragraphs | Word count | "25" |
| `breadcrumbs` | All | Section hierarchy | "Intro > Methods > Analysis" |
| `rows` | Tables | Row count | "12" |
| `columns` | Tables | Column count | "4" |
| `filename` | Images | Image filename | "fig_p3_1.png" |
| `has_caption` | Images/Tables | Caption present? | "yes", "no" |
| `language` | Code | Programming language | "python", "javascript" |

### Parsing Boundaries

**Simple Regex Pattern:**

```python
import re

# Pattern to extract boundaries
pattern = r'<!-- BOUNDARY_START (.*?) -->\n(.*?)\n<!-- BOUNDARY_END (.*?) -->'

# Extract all chunks
matches = re.findall(pattern, markdown_text, re.DOTALL)

for start_attrs, content, end_attrs in matches:
    # Parse attributes from START marker
    attrs = dict(re.findall(r'(\w+)="([^"]*)"', start_attrs))
    
    chunk = {
        'id': attrs['id'],
        'type': attrs['type'],
        'page': attrs['page'],
        'content': content.strip(),
        'metadata': {k: v for k, v in attrs.items() 
                    if k not in ['id', 'type', 'page']}
    }
```

**Result:**

```python
{
    'id': 'p3_text_5',
    'type': 'paragraph',
    'page': '3',
    'content': 'Machine learning models require...',
    'metadata': {
        'char_count': '145',
        'word_count': '25',
        'breadcrumbs': 'Intro > Methods'
    }
}
```

---

## Processing Pipeline

### 1. PDF Conversion

```python
def create_docling_converter():
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = 3.0        # 216 DPI (high quality)
    pipeline_options.generate_picture_images = True
    pipeline_options.generate_table_images = True
    pipeline_options.do_ocr = False            # Digital PDFs
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    
    return DocumentConverter(...)
```

**What Docling Does:**
1. Analyzes PDF layout and structure
2. Identifies content types (text, tables, images, headers)
3. Maintains hierarchical relationships
4. Extracts images at high resolution
5. Converts tables to structured data

### 2. Caption Detection

**The Problem:**
```markdown
[Image of chart]
Exhibit 5: Quarterly revenue trends

↓ Without caption detection:

<!-- BOUNDARY: image -->
[chart image]
<!-- END -->

<!-- BOUNDARY: paragraph -->
Exhibit 5: Quarterly revenue trends
<!-- END -->
```

**The Solution:**
```python
# Check if next item is a caption
if next_item and isinstance(next_item, TextItem):
    text = next_item.text.strip()
    is_caption = (
        text.startswith(('Exhibit', 'Figure', 'Table', 'Chart', 'Source:')) or
        'Source:' in text or
        (len(text) < 200 and ':' in text)
    )
    if is_caption:
        caption = text
        skip_indices.add(next_item_index)  # Don't process separately
```

**Result:**
```markdown
<!-- BOUNDARY: image -->
*Caption:* Exhibit 5: Quarterly revenue trends
[chart image]
*AI Analysis:* [GPT-4 analyzed with caption context]
<!-- END -->
```

### 3. Image Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Extract image from PDF                                    │
│    img_obj = item.get_image(doc)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Save to disk (PNG, 216 DPI)                              │
│    img_obj.save("figures/fig_p3_1.png")                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Get AI description (with caption)                        │
│    • Encode image as base64                                 │
│    • Send to GPT-4 Vision                                   │
│    • Include caption for context                            │
│    • Get analysis of axes, trends, insights                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Create markdown with boundary                            │
│    <!-- BOUNDARY_START ... -->                              │
│    *Caption:* [if present]                                  │
│    ![image.png](path)                                       │
│    *AI Analysis:* [description]                             │
│    <!-- BOUNDARY_END ... -->                                │
└─────────────────────────────────────────────────────────────┘
```

### 4. Table Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Try Text Extraction First                                   │
│ df = item.export_to_dataframe()                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                ┌──────┴──────┐
                │             │
           SUCCESS         FAIL
                │             │
                ▼             ▼
┌─────────────────────┐  ┌──────────────────────┐
│ Use Text Table      │  │ Try Image Extraction │
│                     │  │                      │
│ • to_markdown()     │  │ • Extract as image   │
│ • Get AI analysis   │  │ • Save to disk       │
│   of table content  │  │ • Get AI description │
│ • Add boundaries    │  │ • Add boundaries     │
└─────────────────────┘  └──────────────────────┘
         │                        │
         └────────┬───────────────┘
                  ▼
      ┌─────────────────────┐
      │ Output with         │
      │ Caption +           │
      │ AI Analysis         │
      └─────────────────────┘
```

**Why prioritize text extraction?**
- Preserves exact data values
- Searchable text content
- Smaller file size
- Can be processed by LLMs directly

**When to use image extraction?**
- Text extraction produces garbled data
- Complex table layouts
- Charts misclassified as tables
- Visual formatting important

### 5. Code/Formula Detection

Since older Docling versions don't have `CodeItem`/`FormulaItem`, we detect them from `TextItem`:

```python
def process_special_text(item: TextItem, page, breadcrumbs):
    text = item.text.strip()
    
    # Code detection patterns
    is_code = (
        text.startswith('    ') or      # Indented
        text.startswith('\t') or        # Tabs
        '```' in text or                # Code fence
        'def ' in text or               # Python
        'function' in text or           # JavaScript
        '{' in text and '}' in text     # Curly braces
    )
    
    # Formula detection patterns
    is_formula = (
        '$' in text or                  # LaTeX
        '∫' in text or                  # Integral
        '∑' in text or                  # Summation
        ('=' in text and any(c.isdigit() for c in text))  # Equation
    )
    
    if is_code:
        # Detect language
        language = detect_language(text)
        return wrap_code(text, language)
    
    elif is_formula:
        return wrap_formula(text)
    
    else:
        return None  # Regular text
```

---

## Function Reference

### Core Functions

#### `create_boundary_start(item_type, item_id, page, **attrs)`

Creates opening HTML comment marker.

**Parameters:**
- `item_type`: Content type (paragraph, header, etc.)
- `item_id`: Unique ID (p3_text_5)
- `page`: Page number
- `**attrs`: Additional metadata (char_count, breadcrumbs, etc.)

**Returns:**
```
<!-- BOUNDARY_START type="paragraph" id="p3_text_5" page="3" char_count="145" -->
```

#### `generate_unique_id(page, item_type)`

Generates unique IDs for content items.

**Parameters:**
- `page`: Page number (int)
- `item_type`: Type of content (str)

**Returns:** String like "p3_text_5"

**How it works:**
```python
_id_counters = {
    "p3_text": 5,      # 5 text items on page 3
    "p3_header": 2,    # 2 headers on page 3
    "p5_image": 1      # 1 image on page 5
}

generate_unique_id(3, "text")  # Returns "p3_text_6"
_id_counters["p3_text"] += 1   # Now 6
```

#### `wrap_with_boundaries(content, item_type, item_id, page, **attrs)`

Wraps content with START and END markers.

**Example:**
```python
wrap_with_boundaries(
    content="Machine learning is...",
    item_type="paragraph",
    item_id="p3_text_5",
    page=3,
    char_count=145,
    breadcrumbs="Intro > Methods"
)
```

**Output:**
```markdown
<!-- BOUNDARY_START type="paragraph" id="p3_text_5" page="3" char_count="145" breadcrumbs="Intro > Methods" -->
Machine learning is...
<!-- BOUNDARY_END type="paragraph" id="p3_text_5" -->
```

### Processing Functions

#### `process_header(item, page, level, breadcrumbs)`

Processes section headers.

**What it does:**
1. Updates breadcrumb trail
2. Creates markdown header (## for level 2, ### for level 3)
3. Generates unique ID
4. Wraps with boundaries

**Example:**
```python
# Input
item = SectionHeaderItem(text="Methods")
page = 3
level = 1
breadcrumbs = ["Introduction"]

# Updates breadcrumbs
breadcrumbs = ["Introduction", "Methods"]

# Returns
(output_markdown, updated_breadcrumbs)
```

#### `process_image(item, page, output_dir, image_counter, openai_client, breadcrumbs, next_item)`

Processes images with caption detection.

**Flow:**
1. Check if next_item is a caption
2. Extract image from PDF → save as PNG
3. Get AI description (pass caption for context)
4. Create markdown with caption + image + AI analysis
5. Wrap with boundaries

**Output:**
```markdown
<!-- BOUNDARY_START type="image" id="p3_image_1" page="3" filename="fig_p3_1.png" has_caption="yes" -->
*Caption:* Exhibit 5: Market trends over time
![fig_p3_1.png](../figures/fig_p3_1.png)
*AI Analysis:* Bar chart showing quarterly revenue from Q1 2020 to Q4 2024...
<!-- BOUNDARY_END type="image" id="p3_image_1" -->
```

#### `process_table(item, page, output_dir, image_counter, openai_client, breadcrumbs, next_item)`

Processes tables with dual extraction strategy.

**Decision tree:**
```
Check for caption
    ↓
Try text extraction
    ↓
  Valid?
  /    \
YES     NO
 ↓       ↓
Use     Try
text    image
 ↓       ↓
Get     Get
AI      AI
desc    desc
 ↓       ↓
Output with boundaries
```

**Text table output:**
```markdown
<!-- BOUNDARY_START type="table" id="p2_table_1" page="2" rows="8" columns="2" has_caption="yes" -->
*Caption:* Table 1: Contact information

| Name | Email | Phone |
|------|-------|-------|
| John | j@m.com | 123 |

*AI Analysis:* Contact directory listing team members with roles, emails, and phone numbers.
<!-- BOUNDARY_END type="table" id="p2_table_1" -->
```

### AI Description Functions

#### `describe_image_with_ai(image_path, openai_client, caption=None)`

Gets GPT-4 Vision analysis of images.

**Prompt:**
```
Analyze this visual. Is it a Chart, Diagram, or Data Table?
Describe the axes, trends, and key insights concisely.

Caption/Context: Exhibit 5: Quarterly revenue trends

[Image data as base64]
```

**Response example:**
```
Bar chart showing quarterly revenue from 2020-2024. X-axis shows quarters,
Y-axis shows revenue in millions. Notable spike in Q2 2023 reaching $45M,
followed by steady decline to $32M in Q4 2024.
```

#### `describe_table_with_ai(table_text, openai_client, caption=None)`

Gets GPT-4 analysis of table content.

**Prompt:**
```
Analyze this table. Describe its purpose, structure, and key information concisely.

Caption: Contact Information

Table:
| Name | Email | Phone |
|------|-------|-------|
| John | j@m.com | 123 |
```

**Response example:**
```
Contact information table listing team members. Contains 3 columns (Name, Email, Phone)
with contact details for internal directory purposes.
```

---

## Complete Examples

### Example 1: Simple Document

**Input PDF (page 1):**
```
Introduction

Machine learning models require large datasets.
They learn patterns from examples.
```

**Output `page_1.md`:**
```markdown
# Page 1

<!-- BOUNDARY_START type="header" id="p1_header_1" page="1" level="1" breadcrumbs="Introduction" -->
## Introduction
<!-- BOUNDARY_END type="header" id="p1_header_1" -->

<!-- BOUNDARY_START type="paragraph" id="p1_text_1" page="1" char_count="48" word_count="7" breadcrumbs="Introduction" -->
Machine learning models require large datasets.
<!-- BOUNDARY_END type="paragraph" id="p1_text_1" -->

<!-- BOUNDARY_START type="paragraph" id="p1_text_2" page="1" char_count="35" word_count="5" breadcrumbs="Introduction" -->
They learn patterns from examples.
<!-- BOUNDARY_END type="paragraph" id="p1_text_2" -->
```

### Example 2: Document with Image

**Input PDF (page 2):**
```
Results

[Bar chart image]
Figure 1: Model accuracy comparison
```

**Output `page_2.md`:**
```markdown
# Page 2

<!-- BOUNDARY_START type="header" id="p2_header_1" page="2" level="1" breadcrumbs="Introduction > Results" -->
## Results
<!-- BOUNDARY_END type="header" id="p2_header_1" -->

<!-- BOUNDARY_START type="image" id="p2_image_1" page="2" filename="fig_p2_1.png" has_caption="yes" breadcrumbs="Introduction > Results" -->
*Caption:* Figure 1: Model accuracy comparison
![fig_p2_1.png](../figures/fig_p2_1.png)
*AI Analysis:* Bar chart comparing accuracy of three models (Model A: 85%, Model B: 92%, Model C: 88%). Model B shows highest accuracy with significant lead over alternatives.
<!-- BOUNDARY_END type="image" id="p2_image_1" -->
```

**File structure:**
```
extracted_docs_bounded/
└── document/
    ├── pages/
    │   ├── page_1.md
    │   └── page_2.md
    ├── figures/
    │   └── fig_p2_1.png
    └── metadata.json
```

### Example 3: Document with Table

**Input PDF (page 3):**
```
Table 1: Team contacts

Name        Email           Phone
John Smith  john@m.com      123-456
Jane Doe    jane@m.com      123-457
```

**Output `page_3.md`:**
```markdown
# Page 3

<!-- BOUNDARY_START type="table" id="p3_table_1" page="3" rows="2" columns="3" has_caption="yes" breadcrumbs="Introduction > Results > Team" -->
*Caption:* Table 1: Team contacts

| Name       | Email      | Phone   |
|:-----------|:-----------|:--------|
| John Smith | john@m.com | 123-456 |
| Jane Doe   | jane@m.com | 123-457 |

*AI Analysis:* Contact directory table with 2 team members. Contains names, email addresses, and phone extensions for internal communication.
<!-- BOUNDARY_END type="table" id="p3_table_1" -->
```

### Example 4: Chunking the Output

**Using the chunker:**

```python
import re

def extract_chunks(markdown_file):
    with open(markdown_file, 'r') as f:
        text = f.read()
    
    pattern = r'<!-- BOUNDARY_START (.*?) -->\n(.*?)\n<!-- BOUNDARY_END (.*?) -->'
    matches = re.findall(pattern, text, re.DOTALL)
    
    chunks = []
    for start_attrs, content, end_attrs in matches:
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', start_attrs))
        chunks.append({
            'id': attrs['id'],
            'type': attrs['type'],
            'page': attrs['page'],
            'content': content.strip(),
            'metadata': attrs
        })
    
    return chunks

# Use it
chunks = extract_chunks('page_1.md')

# Filter paragraphs only
paragraphs = [c for c in chunks if c['type'] == 'paragraph']

# Filter by page
page_2_chunks = [c for c in chunks if c['page'] == '2']

# Group by section
from collections import defaultdict
by_section = defaultdict(list)
for chunk in chunks:
    section = chunk['metadata'].get('breadcrumbs', 'No section')
    by_section[section].append(chunk)
```

---

## Troubleshooting

### Common Issues

#### 1. "OPENAI_API_KEY not set"

**Problem:** OpenAI client can't find API key.

**Solution:**
```bash
export OPENAI_API_KEY='sk-...'
```

Or add to `.bashrc`:
```bash
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
source ~/.bashrc
```

#### 2. "No PDF files found"

**Problem:** PDF files have wrong extension or are in wrong directory.

**Solution:**
```bash
# Check files
ls -la *.pdf

# Rename if needed
mv Document.PDF document.pdf
```

#### 3. "Image extraction failed"

**Possible causes:**
- PDF is encrypted
- Image is vector graphics (SVG)
- Unsupported image format

**Solution:**
- Unlock PDF if encrypted
- Check Docling logs for details
- Try with different PDF

#### 4. Duplicate tables/images

**Problem:** Same content appears as both image and table.

**This is fixed!** The code now:
1. Tries text extraction first
2. If successful → uses text only
3. If failed → tries image
4. Never outputs both

#### 5. Captions appearing separately

**Problem:** Image captions show as separate paragraphs.

**This is fixed!** The code now:
1. Checks if next item is a caption
2. Includes caption in image/table boundary
3. Skips caption in main loop
4. Passes caption to AI for context

### Performance Tips

#### Speed up processing

```python
# Reduce image quality (faster, smaller files)
IMAGE_SCALE = 2.0  # Instead of 3.0

# Use FAST table mode (less accurate but faster)
pipeline_options.table_structure_options.mode = TableFormerMode.FAST

# Disable AI descriptions (much faster but loses context)
ai_desc = "Description not available"  # Skip API call
```

#### Reduce costs

```python
# AI descriptions cost ~$0.01 per image
# For 100 images = ~$1.00

# Option 1: Skip AI for images (keep for tables)
if is_table:
    ai_desc = describe_table_with_ai(...)
else:
    ai_desc = "See image for details"

# Option 2: Batch process (same cost, faster)
# Process all PDFs in one run

# Option 3: Cache descriptions
# Save descriptions to avoid re-processing same images
```

### Debug Mode

Add logging to see what's happening:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In functions:
logger.debug(f"Processing item: {item.text[:50]}")
logger.debug(f"Generated ID: {item_id}")
logger.debug(f"Caption detected: {caption}")
```

---

## Advanced Usage

### Custom Caption Patterns

Modify caption detection for your PDFs:

```python
def is_caption(text):
    # Your custom patterns
    return (
        text.startswith(('Exhibit', 'Figure', 'Table', 'Chart')) or
        text.startswith('Source:') or
        text.startswith('Note:') or
        re.match(r'^Fig\\.? \\d+:', text) or  # "Fig. 1:", "Fig 2:"
        (len(text) < 200 and ':' in text)
    )
```

### Custom Metadata

Add your own metadata to boundaries:

```python
output = wrap_with_boundaries(
    content=text,
    item_type="paragraph",
    item_id=item_id,
    page=page,
    # Custom metadata
    author="John Smith",
    department="Research",
    confidential="no",
    version="1.2"
)
```

Result:
```markdown
<!-- BOUNDARY_START type="paragraph" id="p3_text_1" page="3" author="John Smith" department="Research" confidential="no" version="1.2" -->
...
<!-- BOUNDARY_END type="paragraph" id="p3_text_1" -->
```

### Batch Processing with Progress

```python
from tqdm import tqdm

pdf_files = list(Path("pdfs").glob("*.pdf"))

for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
    try:
        process_pdf(pdf_path, output_dir, openai_client)
    except Exception as e:
        logger.error(f"Failed {pdf_path.name}: {e}")
        continue
```

### Integration with RAG Pipeline

```python
# 1. Extract PDFs
python docling_simple_bounded.py documents/

# 2. Chunk with boundaries
from simple_chunker import extract_chunks_from_markdown

chunks = []
for md_file in Path("extracted_docs_bounded").rglob("*.md"):
    chunks.extend(extract_chunks_from_markdown(md_file.read_text()))

# 3. Create embeddings
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

for chunk in chunks:
    chunk['embedding'] = model.encode(chunk['content'])

# 4. Store in vector DB
from pinecone import Pinecone

pc = Pinecone(api_key="...")
index = pc.Index("documents")

index.upsert([
    (chunk['id'], chunk['embedding'], chunk['metadata'])
    for chunk in chunks
])

# 5. Query
query_embedding = model.encode("How does machine learning work?")
results = index.query(vector=query_embedding, top_k=5)
```

---

## Summary

### Key Takeaways

1. **Boundary markers** make chunking trivial
2. **Metadata embedding** provides rich context
3. **AI descriptions** enhance searchability
4. **Caption detection** improves semantic integrity
5. **Dual extraction** (text/image) handles edge cases
6. **Functional design** makes code simple and testable

### Next Steps

1. Extract your first PDF
2. Look at the output markdown
3. Try the simple_chunker.py
4. Integrate with your RAG pipeline
5. Customize for your needs

### Support

For issues or questions:
- Check this guide first
- Review the code comments
- Test with simple PDFs first
- Check error messages carefully

Good luck!
