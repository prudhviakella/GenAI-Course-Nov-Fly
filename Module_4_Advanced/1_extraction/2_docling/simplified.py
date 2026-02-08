"""
PDF Document Extraction & Analysis Pipeline
===========================================

This module extracts content from PDF documents using Docling, processes visual
elements (charts, tables, images), and generates markdown output with AI-powered
descriptions.

Key Features:
- Smart caption reordering for better readability
- Dual-mode visual extraction (handles both images and chart-like tables)
- GPT-4 Vision integration for image analysis
- Structured markdown output organized by page

Author: Prudhvi
"""

import base64
import os
from pathlib import Path
from typing import List, Dict

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import (
    TableItem,
    PictureItem,
    TextItem,
    SectionHeaderItem
)
from openai import OpenAI


# ==============================================================================
# CAPTION REORDERING
# ==============================================================================

def _smart_reorder(items: List[Dict]) -> List[Dict]:
    """
    Smart Caption Reordering Algorithm

    PURPOSE:
    --------
    Fixes a common PDF extraction issue where captions appear AFTER
    their associated visuals. This function detects [Visual, Caption]
    patterns and swaps them to [Caption, Visual] for better readability.

    ALGORITHM:
    ----------
    ┌─────────────────────────────────────────────────────────────┐
    │              SMART REORDERING LOGIC                         │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  FOR each consecutive pair of items:                        │
    │    │                                                         │
    │    ├─▶ Check: Is current item a Visual?                    │
    │    │   (PictureItem or TableItem)                          │
    │    │                                                         │
    │    ├─▶ Check: Is next item a TextItem?                     │
    │    │                                                         │
    │    ├─▶ Check: Does text match caption pattern?             │
    │    │   Pattern: "Exhibit 1:", "Figure 2:", etc.            │
    │    │                                                         │
    │    └─▶ IF all checks pass: SWAP the two items             │
    │        [Visual, Caption] → [Caption, Visual]               │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

    EXAMPLE:
    --------
    Input:
    1. PictureItem (chart image)
    2. TextItem "Exhibit 1: Quarterly Revenue"
    3. TextItem "Revenue increased by 25%..."

    Output:
    1. TextItem "Exhibit 1: Quarterly Revenue"
    2. PictureItem (chart image)
    3. TextItem "Revenue increased by 25%..."

    Parameters
    ----------
    items : List[Dict]
        List of item dictionaries with structure:
        {"item": DoclingItem, "level": int}

    Returns
    -------
    List[Dict]
        Reordered list with caption-visual pairs swapped

    EDGE CASES:
    -----------
    - Less than 2 items: Returns unchanged
    - Multiple visuals in sequence: Each checked independently
    - Caption without visual: No change
    - Visual without caption: No change
    """
    # Need at least 2 items to perform swapping
    if len(items) < 2:
        return items

    # Work on a copy to avoid modifying original
    reordered = items.copy()

    # Index pointer for iteration
    i = 0
    swaps_made = 0

    # Iterate through consecutive pairs
    while i < len(reordered) - 1:
        curr = reordered[i]["item"]
        next_item = reordered[i + 1]["item"]

        # ================================================================
        # SWAP LOGIC: [Visual, Caption] → [Caption, Visual]
        # ================================================================
        # Condition 1: Current item is a visual (Picture or Table)
        # Condition 2: Next item is text
        # Condition 3: Text matches caption pattern
        if (isinstance(curr, (PictureItem, TableItem)) and
                isinstance(next_item, TextItem)):

            # Check if the text item has a caption label
            if next_item.label:
                if next_item.label.strip() == 'caption':
                    # SWAP: Exchange positions
                    reordered[i], reordered[i + 1] = reordered[i + 1], reordered[i]
                    swaps_made += 1

                    # Skip next position since we just swapped it
                    i += 1

        # Move to next pair
        i += 1

    # Optional: Log swap count for debugging
    if swaps_made > 0:
        print(f"      INFO: Made {swaps_made} caption reordering swaps")

    return reordered


# ==============================================================================
# VISUAL ELEMENT EXTRACTION
# ==============================================================================

def _handle_visual(
        item,
        doc,
        p_no: int,
        out_dir: Path,
        img_list: List[str],
        lines: List[str],
        is_table: bool = False
) -> bool:
    """
    Extract and Analyze Visual Elements

    PURPOSE:
    --------
    Dual-purpose visual handler that works for BOTH PictureItem and
    TableItem. This is critical because some charts are misclassified
    as tables in the PDF structure.

    EXTRACTION WORKFLOW:
    --------------------
    ┌─────────────────────────────────────────────────────────────┐
    │              VISUAL EXTRACTION PIPELINE                     │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  Input: Item (PictureItem OR TableItem)                     │
    │    │                                                         │
    │    ├─▶ 1. Attempt get_image() from item                    │
    │    │      Works for both Pictures and Tables!              │
    │    │                                                         │
    │    ├─▶ 2. If image exists:                                 │
    │    │      • Generate filename: fig_pN_M.png                │
    │    │      • Save high-res image (216 DPI)                  │
    │    │      • Call AI vision analysis                        │
    │    │      • Add to image list                              │
    │    │      • Inject Markdown with description               │
    │    │                                                         │
    │    └─▶ 3. Return True if successful, False otherwise       │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

    Parameters
    ----------
    item : PictureItem or TableItem
        Docling item that may contain visual content
    doc : Document
        Parent document (needed for get_image())
    p_no : int
        Page number for filename generation
    out_dir : Path
        Output directory containing figures/ subdirectory
    img_list : List[str]
        Mutable list to append image filenames to
    lines : List[str]
        Mutable list to append Markdown output to
    is_table : bool, optional
        Whether item is a TableItem (affects labeling)

    Returns
    -------
    bool
        True if image was successfully extracted and saved
        False if no image available or extraction failed

    ERROR HANDLING:
    ---------------
    - Catches all exceptions to prevent one visual from crashing entire page
    - Returns False on any error
    - Allows processing to continue with remaining items

    EXAMPLE OUTPUT:
    ---------------
    Markdown injected into lines:

    > **Visual Element**
    > ![fig_p3_1.png](../figures/fig_p3_1.png)
    > *AI Analysis:* Bar chart showing quarterly revenue growth from...
    """
    try:
        # ================================================================
        # STEP 1: Attempt Image Extraction
        # ================================================================
        # Docling's get_image() works for BOTH PictureItem and TableItem
        # This is the key feature that catches misclassified charts
        img_obj = item.get_image(doc)

        # Check if image was successfully retrieved
        if img_obj:
            # ============================================================
            # STEP 2: Generate Filename and Save
            # ============================================================
            # Filename pattern: fig_p{page}_{count}.png
            # Example: fig_p3_1.png (page 3, first image)
            fname = f"fig_p{p_no}_{len(img_list) + 1}.png"
            fpath = out_dir / "figures" / fname

            # Save image at high resolution (216 DPI from 3.0x scale)
            try:
                img_obj.save(fpath)
            except IOError as e:
                print(f"      WARNING: Failed to save {fname}: {str(e)}")
                return False

            # ============================================================
            # STEP 3: AI Vision Analysis
            # ============================================================
            desc = _describe_image(fpath)

            # ============================================================
            # STEP 4: Update Collections
            # ============================================================
            # Add to image list (for metadata)
            img_list.append(f"figures/{fname}")

            # Determine label based on item type
            type_label = "Table/Chart" if is_table else "Visual Element"

            # ============================================================
            # STEP 5: Inject Markdown
            # ============================================================
            # Format as blockquote for visual distinction
            # Include image, relative path, and AI description
            lines.append(
                f"\n> **{type_label}**\n"
                f"> ![{fname}](../figures/{fname})\n"
                f"> *AI Analysis:* {desc}\n"
            )
            print(lines)
            return True

    except AttributeError:
        # Item doesn't have get_image() method
        # This is expected for some item types
        return False
    except Exception as e:
        # Unexpected error during extraction
        # Log but don't crash
        print(f"      WARNING: Visual extraction error for page {p_no}: {str(e)}")
        return False

    return False


# ==============================================================================
# AI-POWERED ANALYSIS FUNCTIONS
# ==============================================================================

def _describe_table(table_md: str) -> str:
    """
    Generate AI Summary of Table Content

    Uses GPT to analyze markdown table and extract key insights,
    trends, and important metrics.

    Parameters
    ----------
    table_md : str
        Markdown-formatted table string

    Returns
    -------
    str
        AI-generated summary or "Summary unavailable" on failure
    """
    table_prompt = (
        "Summarize this table. What are the key takeaways, trends, "
        "and important metrics?"
    )

    response = openai.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": f"{table_prompt}\n\n{table_md}"
        }],
        max_tokens=150
    )

    summary = response.choices[0].message.content.strip()
    return summary if summary else "Summary unavailable"


def _describe_image(path: Path) -> str:
    """
    AI-Powered Image Description

    PURPOSE:
    --------
    Uses GPT-4 Vision to analyze extracted images and generate natural
    language descriptions focusing on chart types, trends, and insights.

    ANALYSIS WORKFLOW:
    ------------------
    ┌─────────────────────────────────────────────────────────────┐
    │            GPT-4 VISION ANALYSIS PIPELINE                   │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  1. Load image file from disk                               │
    │     │                                                        │
    │     ▼                                                        │
    │  2. Encode as base64 string                                 │
    │     (Required format for OpenAI API)                        │
    │     │                                                        │
    │     ▼                                                        │
    │  3. Construct API request:                                  │
    │     • Model: gpt-4o                                         │
    │     • Prompt: vision_prompt                                 │
    │     • Image: base64 data                                    │
    │     • max_tokens: 200                                       │
    │     │                                                        │
    │     ▼                                                        │
    │  4. Call OpenAI Vision API                                  │
    │     │                                                        │
    │     ▼                                                        │
    │  5. Extract and return description                          │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

    Parameters
    ----------
    path : Path
        Path to image file to analyze

    Returns
    -------
    str
        AI-generated description or error message

    ERROR HANDLING:
    ---------------
    Returns "Description failed." on any error to prevent processing
    interruption. Specific errors are not exposed to maintain flow.

    EXAMPLE OUTPUT:
    ---------------
    "Bar chart showing quarterly revenue growth from Q1 to Q4 2024.
    Revenue increased from $10M to $15M, with strongest growth in Q3.
    Y-axis shows revenue in millions, X-axis shows quarters."
    """
    try:
        # ================================================================
        # STEP 1: Load and Encode Image
        # ================================================================
        # Read image file as binary
        with open(path, "rb") as f:
            image_bytes = f.read()
            # Encode to base64 string (required by OpenAI API)
            b64 = base64.b64encode(image_bytes).decode('utf-8')

        # ================================================================
        # STEP 2: Call GPT-4 Vision API
        # ================================================================
        resp = openai.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": [
                    # Text prompt with analysis instructions
                    {
                        "type": "text",
                        "text": vision_prompt
                    },
                    # Image content as base64
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64}"
                        }
                    }
                ]
            }],
            max_tokens=200  # Limit response length for conciseness
        )

        # ================================================================
        # STEP 3: Extract Description
        # ================================================================
        return resp.choices[0].message.content

    except FileNotFoundError:
        return "Description failed: Image file not found."
    except ConnectionError:
        return "Description failed: Network connection error."
    except Exception:
        # Generic fallback for any other errors
        # Prevents one failed description from crashing entire extraction
        return "Description failed."


# ==============================================================================
# MAIN EXECUTION PIPELINE
# ==============================================================================

def main():
    """
    Main PDF Extraction and Analysis Pipeline

    WORKFLOW:
    ---------
    1. Configure Docling pipeline options
    2. Convert PDF to structured document
    3. Create output directory structure
    4. Group items by page
    5. Process each page:
       - Reorder captions
       - Extract text, headers, visuals, tables
       - Generate AI descriptions
       - Save markdown output
    """

    # ==========================================================================
    # CONFIGURATION
    # ==========================================================================

    # Input PDF path
    pdf_path = Path(
        "/Module_4_Advanced/1_extraction/docs/AI-Enablers-Adopters-research-report.pdf"
    )

    # Docling pipeline configuration
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = 3.0  # High-res extraction (216 DPI)
    pipeline_options.generate_picture_images = True  # Extract images
    pipeline_options.generate_table_images = True  # Extract table visuals
    pipeline_options.do_ocr = False  # Disable OCR (not needed for digital PDFs)
    pipeline_options.do_table_structure = True  # Parse table structure
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    # Format-specific options
    format_options = {
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }

    # ==========================================================================
    # PDF CONVERSION
    # ==========================================================================

    print(f"Converting PDF: {pdf_path.name}")
    conv_res = DocumentConverter(format_options=format_options).convert(pdf_path)
    docs = conv_res.document
    print(f"Conversion complete. Processing {len(list(docs.iterate_items()))} items...")

    # ==========================================================================
    # OUTPUT DIRECTORY SETUP
    # ==========================================================================

    # Create base output directory
    base_dir = Path("siplified_extracted_docs")
    base_dir.mkdir(exist_ok=True)

    # Create document-specific subdirectories
    doc_out_dir = base_dir / pdf_path.stem
    (doc_out_dir / "pages").mkdir(parents=True, exist_ok=True)
    (doc_out_dir / "figures").mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {doc_out_dir}")

    # ==========================================================================
    # OPENAI CLIENT INITIALIZATION
    # ==========================================================================

    global openai, vision_prompt, model
    openai = OpenAI()
    vision_prompt = (
        "Analyze this visual. Is it a Chart, Diagram, or Data Table? "
        "Describe the axes, trends, and key insights concisely."
    )
    model = "gpt-4o"

    # ==========================================================================
    # PAGE-LEVEL ITEM GROUPING
    # ==========================================================================

    # Group all items by page number
    pages_items = {}

    for item, level in docs.iterate_items():
        # Get page number from item provenance
        p_no = item.prov[0].page_no

        # Initialize page entry if needed
        if p_no not in pages_items:
            pages_items[p_no] = []

        # Append item with its hierarchy level
        pages_items[p_no].append({
            "item": item,
            "level": level,
        })

    # Sort pages numerically
    pages_items_keys = sorted(pages_items.keys())
    print(f"Found {len(pages_items_keys)} pages to process")

    # ==========================================================================
    # PAGE-BY-PAGE PROCESSING
    # ==========================================================================

    for p_no in pages_items_keys:
        print(f"\n  Processing Page {p_no}...")

        # Get items for this page
        items = pages_items[p_no]

        # Apply smart caption reordering
        ordered_items = _smart_reorder(items)

        # Initialize page-level collections
        page_lines = []  # Markdown content lines
        page_images = []  # Image filenames
        page_tables = []  # Table metadata

        # Add page header
        page_lines.append(f"\n# Page {p_no}\n")

        # ----------------------------------------------------------------------
        # ITEM PROCESSING LOOP
        # ----------------------------------------------------------------------
        for entry in ordered_items:
            item = entry["item"]
            level = entry["level"]

            # ------------------------------------------------------------------
            # Section Headers
            # ------------------------------------------------------------------
            if isinstance(item, SectionHeaderItem):
                text = item.text.strip()
                # Use level+1 because page title is already h1
                page_lines.append(f"\n{'#' * (level + 1)} {text}\n")

            # ------------------------------------------------------------------
            # Text Content
            # ------------------------------------------------------------------
            elif isinstance(item, TextItem):
                text = item.text.strip()
                page_lines.append(text)

            # ------------------------------------------------------------------
            # Picture Items
            # ------------------------------------------------------------------
            elif isinstance(item, PictureItem):
                success = _handle_visual(
                    item, docs, p_no, doc_out_dir,
                    page_images, page_lines, is_table=False
                )

            # ------------------------------------------------------------------
            # Table Items (Dual Extraction)
            # ------------------------------------------------------------------
            elif isinstance(item, TableItem):
                # ATTEMPT 1: Extract as Data Table
                md_table = ""
                try:
                    df = item.export_to_dataframe()
                    if not df.empty:
                        md_table = df.to_markdown(index=False)
                except Exception:
                    # Table text extraction failed, that's okay
                    pass

                # ATTEMPT 2: Extract as Visual (Chart/Graph)
                # TableItem can have images if it's actually a chart
                img_saved = _handle_visual(
                    item, docs, p_no, doc_out_dir,
                    page_images, page_lines, is_table=True
                )

                # If no image was extracted but we have table text, output it
                if not img_saved and md_table:
                    # Generate AI summary of table
                    table_desc = _describe_table(md_table)

                    # Add table markdown
                    page_lines.append(f"\n{md_table}\n")

                    # Add AI summary
                    if table_desc:
                        page_lines.append(
                            f"\n**Summary:** {table_desc}\n"
                        )

                    page_tables.append("Text Table")

        # ----------------------------------------------------------------------
        # SAVE PAGE MARKDOWN
        # ----------------------------------------------------------------------

        # Combine all lines with double newlines for markdown spacing
        final_text = "\n\n".join(page_lines)
        md_name = f"page_{p_no}.md"

        try:
            with open(doc_out_dir / "pages" / md_name, "w", encoding="utf-8") as f:
                f.write(final_text)
                f.flush()

            print(f"    ✓ Saved {md_name} ({len(page_images)} images, {len(page_tables)} tables)")

        except IOError as e:
            print(f"      ERROR: Failed to write {md_name}: {str(e)}")
            raise

    # ==========================================================================
    # COMPLETION
    # ==========================================================================

    print(f"\n✓ Processing complete!")
    print(f"  Output: {doc_out_dir}")
    print(f"  Pages: {len(pages_items_keys)}")


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    main()