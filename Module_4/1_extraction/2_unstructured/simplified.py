"""
PDF Document Extraction using Unstructured.io
==============================================

This module extracts content from PDF documents using the Unstructured library,
which provides high-resolution parsing with support for images and tables.

Key Features:
- High-resolution document parsing
- Automatic image extraction
- Table structure inference
- Organized output directory structure

Author: Prudhvi
"""
import base64
import json
import traceback
from pathlib import Path
from typing import Optional, Dict, List

from openai import OpenAI
from unstructured.partition.auto import partition


# ==============================================================================
# DIRECTORY MANAGEMENT
# ==============================================================================

def _create_output_structure(doc_path: Path, custom_output: Path) -> Path:
    """
    Create Organized Output Directory Structure

    PURPOSE:
    --------
    Sets up a clean directory hierarchy for storing extracted content:

    Structure:
    ----------
    custom_output/
    └── {document_name}/
        ├── tables/      # Extracted table data
        └── figures/     # Extracted images and charts

    Parameters
    ----------
    doc_path : Path
        Path to the source document (used for naming)
    custom_output : Path
        Base directory for all outputs

    Returns
    -------
    Path
        Path to the document-specific output directory

    Notes
    -----
    - Uses document stem (filename without extension) for folder name
    - Creates parent directories if they don't exist
    - Skips creation if directories already exist (idempotent)

    Example
    -------
    Input: doc_path = "reports/Q4-2024.pdf"
           custom_output = "extracted/"

    Creates:
    extracted/
    └── Q4-2024/
        ├── tables/
        └── figures/

    Returns: Path("extracted/Q4-2024")
    """
    # Use custom_output as base directory
    base_dir = custom_output

    # Create document-specific folder using filename (without extension)
    doc_output_dir = base_dir / doc_path.stem

    # Create main document directory
    # parents=True: Create intermediate directories if needed
    # exist_ok=True: Don't raise error if directory already exists
    doc_output_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectory for extracted tables
    (doc_output_dir / 'tables').mkdir(exist_ok=True)

    # Create subdirectory for extracted figures/images
    (doc_output_dir / 'figures').mkdir(exist_ok=True)

    return doc_output_dir


# ==============================================================================
# MAIN EXTRACTION PIPELINE
# ==============================================================================

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

# Input document path
doc_path = Path(
    "/Users/akellaprudhvi/mystuff/Course/GenAI-Course-Modules/"
    "Module_4/1_extraction/docs/AI-Enablers-Adopters-research-report.pdf"
)

# Base output directory for all extractions
base_dir = Path("siplified_extracted_docs")

# ------------------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------------------

# Verify input file exists before processing
if not doc_path.exists():
    raise FileNotFoundError(f"Document not found: {doc_path}")

# ------------------------------------------------------------------------------
# Directory Setup
# ------------------------------------------------------------------------------

# Create output directory structure
# Returns path like: siplified_extracted_docs/AI-Enablers-Adopters-research-report/
doc_output_dir = _create_output_structure(doc_path, custom_output=base_dir)

print(f"Processing: {doc_path.name}")
print(f"Output directory: {doc_output_dir}")



# ------------------------------------------------------------------------------
# Document Extraction
# ------------------------------------------------------------------------------
figures_dir = doc_output_dir / 'figures'
# Extract all elements from PDF using Unstructured's partition function
elements = partition(
    filename=str(doc_path),

    # Strategy: "hi_res" for high-resolution parsing
    strategy="hi_res",

    # DISABLE OCR - For native PDFs with selectable text
    # ---------------------------------------------------
    # OCR (Optical Character Recognition) is used for:
    #   - Scanned documents (images of text)
    #   - PDFs without embedded text layer
    #
    # Disable OCR when:
    #   - Working with native/digital PDFs (not scans)
    #   - Text is already selectable/searchable
    #   - Want faster processing
    #
    # Benefits of disabling OCR:
    #   - Preserves original text quality
    #   - Faster processing
    #   - Better table structure retention
    #   - Avoids OCR errors on clear digital text
    ocr_languages=None,  # Disables OCR entirely

    # Image Extraction: Enable extraction of embedded images
    extract_images_in_pdf=True,
    extract_image_block_output_dir=str(figures_dir),

    # TABLE PRESERVATION ENHANCEMENTS
    # --------------------------------

    # 1. Infer table structure (keeps tabular data organized)
    infer_table_structure=True,

    # 2. Extract tables as images (CRITICAL for preserving visual structure)
    # -----------------------------------------------------------------------
    # This ensures tables are ALSO saved as images, not just converted to text
    # Benefits:
    #   - Preserves exact visual layout
    #   - Maintains formatting, borders, colors
    #   - Useful for complex tables with merged cells
    #   - Enables multimodal processing (text + image)
    extract_image_block_types=["Image", "Table"],  # Extract both images AND tables

    # 3. Chunking strategy for tables
    # --------------------------------
    # Controls how tables are segmented
    # Options:
    #   - "by_title": Groups content by section headings
    #   - "basic": Simple chunking
    #   - None: No chunking (keeps tables intact)
    chunking_strategy=None,  # Prevents table fragmentation

    # 4. Image format and quality
    # ---------------------------
    # High quality for extracted table images
    extract_image_block_to_payload=False,  # Save to disk, not base64 in memory

    # OPTIONAL: PDF-specific optimizations
    # ------------------------------------
    # Skip image analysis if you only care about structure
    skip_infer_table_types=[],  # Don't skip any table types

    # For large documents, consider these memory optimizations:
    # max_partition_length=1500,  # Max chars per element
    # include_page_breaks=True,   # Track page boundaries
)


def _extract_text(elements, output_dir: Path) -> Dict:
    """Extract text from Unstructured elements"""
    global _original_text
    text_parts = []

    for element in elements:
        element_type = type(element).__name__

        # Add appropriate formatting based on element type
        if 'Title' in element_type:
            text_parts.append(f"\n# {element.text}\n")
        elif 'NarrativeText' in element_type or 'Text' in element_type:
            text_parts.append(f"\n{element.text}\n")
        elif 'ListItem' in element_type:
            text_parts.append(f"- {element.text}\n")
        else:
            text_parts.append(f"{element.text}\n")

    full_text = ''.join(text_parts)

    # Save text
    text_file = output_dir / 'text.md'
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(full_text)

    # Store for later merging
    _original_text = full_text
    _text_file = text_file

    return {
        'characters': len(full_text),
        'words': len(full_text.split()),
        'lines': len(full_text.split('\n'))
    }

def _extract_tables(elements, output_dir: Path) -> Dict:
    """Extract tables from Unstructured elements"""
    tables_dir = output_dir / 'tables'
    table_files = []
    table_counter = 0

    for element in elements:
        if type(element).__name__ == 'Table':
            table_counter += 1

            try:
                # Get table as HTML or text
                if hasattr(element, 'metadata') and hasattr(element.metadata, 'text_as_html'):
                    table_content = element.metadata.text_as_html
                else:
                    table_content = element.text

                # Save table
                table_file = tables_dir / f'table_{table_counter}.txt'
                with open(table_file, 'w', encoding='utf-8') as f:
                    f.write(table_content)

                table_files.append(str(table_file))

            except Exception as e:
                print(f"  Warning: Could not extract table {table_counter}: {e}")

    return {'count': len(table_files), 'files': table_files}

def _extract_figures(output_dir: Path) -> Dict:
    """Extract figures from document"""
    figures_dir = output_dir / 'figures'
    figure_files = []
    figure_info_list = []

    try:
        # Use Unstructured's image extraction
        from unstructured.partition.pdf import partition_pdf
        # List extracted images
        for img_file in figures_dir.glob('*.jpg'):
            figure_files.append(str(img_file))
        for img_file in figures_dir.glob('*.png'):
            figure_files.append(str(img_file))

        # Create figure info
        for i, fig_file in enumerate(figure_files, 1):
            figure_info_list.append({
                'figure_number': i,
                'filename': Path(fig_file).name,
                'filepath': fig_file,
                'caption': None
            })
            print(f"  Extracted: {Path(fig_file).name}")

    except Exception as e:
        print(f"  Warning: Image extraction failed: {e}")

    # Store figure info
    _figure_info = figure_info_list

    return {
        'count': len(figure_files),
        'files': figure_files,
        'info': figure_info_list
    }

def _generate_openai_descriptions(figure_files: List[str], output_dir: Path) -> Dict:
    """Generate descriptions using OpenAI Vision API"""

    if not figure_files:
        print("  No figures to describe")
        return {'count': 0}

    descriptions = []
    success_count = 0

    for i, figure_path in enumerate(figure_files, 1):
        try:
            print(f"  [{i}/{len(figure_files)}] Describing {Path(figure_path).name}...", end=' ')

            # Read image and encode to base64
            with open(figure_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Call OpenAI Vision API
            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": vision_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            description = response.choices[0].message.content.strip()

            descriptions.append({
                'figure_number': i,
                'filename': Path(figure_path).name,
                'filepath': figure_path,
                'description': description,
                'model': model
            })

            success_count += 1
            print(f"✓ ({len(description)} chars)")

        except Exception as e:
            print(f"✗ Error: {traceback.format_exc()}")
            descriptions.append({
                'figure_number': i,
                'filename': Path(figure_path).name,
                'filepath': figure_path,
                'description': None,
                'error': str(e)
            })

    # Save descriptions
    if descriptions:
        _save_descriptions(descriptions, output_dir)

    return {'count': success_count, 'descriptions': descriptions}

def _save_descriptions(descriptions: List[Dict], output_dir: Path):
    """Save descriptions to JSON and Markdown"""

    # JSON
    json_file = output_dir / 'figure_descriptions.json'
    with json_file.open('w', encoding='utf-8') as f:
        json.dump(descriptions, f, indent=2, ensure_ascii=False)

    # Markdown
    md_file = output_dir / 'figure_descriptions.md'
    with md_file.open('w', encoding='utf-8') as f:
        f.write("# Figure Descriptions (OpenAI Vision)\n\n")
        f.write(f"**Model:** {model}\n\n")
        f.write("---\n\n")

        for desc in descriptions:
            f.write(f"## Figure {desc['figure_number']}\n\n")
            f.write(f"**File:** `{desc['filename']}`\n\n")

            if desc.get('description'):
                f.write(f"**Description:**\n\n{desc['description']}\n\n")
                f.write(f"*Generated by {desc['model']}*\n\n")
            else:
                f.write("*Description generation failed*\n\n")
                if desc.get('error'):
                    f.write(f"Error: {desc['error']}\n\n")

            f.write("---\n\n")

    # Merge into text.md
    _merge_descriptions_into_text(descriptions, output_dir)

def _merge_descriptions_into_text(descriptions: List[Dict], output_dir: Path):
    """Merge figure descriptions into text.md for RAG"""
    global _original_text
    if not descriptions:
        return

    text_content = _original_text

    # Append all descriptions at end
    text_content += "\n\n# AI-Generated Figure Descriptions\n\n"

    for desc in descriptions:
        if not desc.get('description'):
            continue

        fig_num = desc['figure_number']
        description = desc['description']

        text_content += f"\n## Figure {fig_num}\n\n"
        text_content += f"**AI Description:** {description}\n\n"
        text_content += "---\n\n"

    # Save merged text
    merged_file = output_dir / 'text.md'
    with merged_file.open('w', encoding='utf-8') as f:
        f.write(text_content)

    # Save original
    original_file = output_dir / 'text_original.md'
    with original_file.open('w', encoding='utf-8') as f:
        f.write(_original_text)

    print(f"  ✓ Added {len(descriptions)} figure descriptions to text.md")
    print("  ✓ Original text saved to text_original.md")


# ------------------------------------------------------------------------------
# Output Inspection
# ------------------------------------------------------------------------------

# Display extracted elements for verification
# Elements is a list of Element objects, each representing:
#   - Text blocks
#   - Tables (with structure)
#   - Images (with metadata)
#   - Headers/Titles
#   - List items
#   - etc.
print(f"\nExtracted {len(elements)} elements")
print("\nElements preview:")
print(elements[0].to_dict())
_original_text = ""
openai = OpenAI()
vision_prompt = (
        "Analyze this visual. Is it a Chart, Diagram, or Data Table? "
        "Describe the axes, trends, and key insights concisely."
    )
model = "gpt-4o"

_extract_text(elements, doc_output_dir)
_extract_tables(elements, doc_output_dir)
figures_stats = _extract_figures(doc_output_dir)
descriptions_stats = _generate_openai_descriptions(
    figures_stats['files'],
    doc_output_dir
)