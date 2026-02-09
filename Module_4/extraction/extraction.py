"""
Docling PDF Extractor with Boundary Markers
Functional programming version for easy understanding

See TECHNICAL_GUIDE.md for complete documentation
"""

import os
import sys
import json
import base64
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.document import (
        TableItem, PictureItem, TextItem, SectionHeaderItem, ListItem
    )
    from openai import OpenAI
    import pandas as pd
except ImportError as e:
    print(f"\nMissing library: {e}")
    print("Install: pip install docling openai pandas")
    sys.exit(1)

OUTPUT_DIR = "extracted_docs_bounded"
OPENAI_MODEL = "gpt-4o"
IMAGE_SCALE = 3.0  # 216 DPI

# =============================================================================
# BOUNDARY MARKERS
# =============================================================================

def create_boundary_start(item_type: str, item_id: str, page: int, **attrs) -> str:
    """Create opening boundary marker"""
    attr_str = f'type="{item_type}" id="{item_id}" page="{page}"'
    for key, value in attrs.items():
        attr_str += f' {key}="{value}"'
    return f"<!-- BOUNDARY_START {attr_str} -->"


def create_boundary_end(item_type: str, item_id: str) -> str:
    """Create closing boundary marker"""
    return f'<!-- BOUNDARY_END type="{item_type}" id="{item_id}" -->'


def wrap_with_boundaries(content: str, item_type: str, item_id: str,
                        page: int, **attrs) -> str:
    """Wrap content with START and END markers"""
    filtered_attrs = {k: v for k, v in attrs.items() if v is not None}
    start = create_boundary_start(item_type, item_id, page, **filtered_attrs)
    end = create_boundary_end(item_type, item_id)
    return f"{start}\n{content}\n{end}"


# =============================================================================
# UNIQUE ID GENERATION
# =============================================================================

_id_counters = defaultdict(int)

def generate_unique_id(page: int, item_type: str) -> str:
    """Generate unique ID: p{page}_{type}_{counter}"""
    key = f"p{page}_{item_type}"
    _id_counters[key] += 1
    return f"{key}_{_id_counters[key]}"


def reset_id_counters():
    """Reset counters (call at start of each document)"""
    global _id_counters
    _id_counters = defaultdict(int)


# =============================================================================
# DOCLING SETUP
# =============================================================================

def create_docling_converter():
    """Create configured Docling converter"""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_SCALE
    pipeline_options.generate_picture_images = True
    pipeline_options.generate_table_images = True
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )


# =============================================================================
# AI DESCRIPTIONS
# =============================================================================

def describe_table_with_ai(table_text: str, openai_client, caption: str = None) -> str:
    """Get AI description of table content"""
    try:
        prompt = "Analyze this table. Describe its purpose, structure, and key information concisely."
        if caption:
            prompt += f"\n\nCaption: {caption}"
        prompt += f"\n\nTable:\n{table_text}"

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI description failed: {str(e)}"


def describe_image_with_ai(image_path: Path, openai_client, caption: str = None) -> str:
    """Get AI description of image using GPT-4 Vision"""
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')

        prompt = "Analyze this visual. Is it a Chart, Diagram, or Data Table? "
        prompt += "Describe the axes, trends, and key insights concisely."
        if caption:
            prompt += f"\n\nCaption/Context: {caption}"

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]
            }],
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI description failed: {str(e)}"


# =============================================================================
# IMAGE PROCESSING
# =============================================================================

def extract_and_save_image(item, doc, page_num: int, output_dir: Path,
                           image_counter: int, openai_client,
                           caption: str = None, is_table: bool = False
                          ) -> Optional[Tuple[str, str, str, str]]:
    """Extract image, save to disk, get AI description"""
    try:
        img_obj = item.get_image(doc)
        if not img_obj:
            return None

        filename = f"fig_p{page_num}_{image_counter}.png"
        filepath = output_dir / "figures" / filename
        img_obj.save(filepath)

        ai_desc = describe_image_with_ai(filepath, openai_client, caption)
        type_label = "Table/Chart" if is_table else "Image"

        return (filename, str(filepath.relative_to(output_dir)), ai_desc, type_label)
    except Exception as e:
        print(f"   WARNING: Image extraction failed: {str(e)}")
        return None


# =============================================================================
# ITEM PROCESSORS
# =============================================================================

def process_header(item: SectionHeaderItem, page: int, level: int,
                  breadcrumbs: List[str]) -> Tuple[str, List[str]]:
    """Process section header"""
    text = item.text.strip()

    if len(breadcrumbs) >= level:
        breadcrumbs = breadcrumbs[:level-1]
    breadcrumbs.append(text)

    item_id = generate_unique_id(page, "header")
    content = f"{'#' * (level + 1)} {text}"

    output = wrap_with_boundaries(
        content, "header", item_id, page,
        level=level, breadcrumbs=" > ".join(breadcrumbs)
    )
    return output, breadcrumbs


def process_text(item: TextItem, page: int, breadcrumbs: List[str]) -> str:
    """Process regular text paragraph"""
    text = item.text.strip()
    if len(text) <= 1:
        return ""

    item_id = generate_unique_id(page, "text")

    return wrap_with_boundaries(
        text, "paragraph", item_id, page,
        char_count=len(text), word_count=len(text.split()),
        breadcrumbs=" > ".join(breadcrumbs)
    )


def process_list(item: ListItem, page: int, breadcrumbs: List[str]) -> str:
    """Process list item"""
    marker = getattr(item, 'enumeration', '-')
    text = item.text.strip()
    content = f"{marker} {text}"
    item_id = generate_unique_id(page, "list")

    return wrap_with_boundaries(
        content, "list", item_id, page,
        breadcrumbs=" > ".join(breadcrumbs)
    )


def process_special_text(item: TextItem, page: int, breadcrumbs: List[str]) -> Optional[str]:
    """Detect and process code blocks from TextItem (formula detection disabled)"""
    text = item.text.strip()
    if len(text) < 3:
        return None

    # Only detect code blocks (formulas cause too many false positives)
    is_code = (
        text.startswith('    ') or text.startswith('\t') or '```' in text or
        text.count('def ') > 0 or text.count('class ') > 0 or
        text.count('import ') > 0 or text.count('function ') > 0 or
        ('{' in text and '}' in text and ';' in text)
    )

    if is_code:
        language = ''
        if 'python' in text.lower() or 'def ' in text or 'import ' in text:
            language = 'python'
        elif 'function' in text or 'const ' in text or 'let ' in text:
            language = 'javascript'

        content = f"```{language}\n{text}\n```"
        item_id = generate_unique_id(page, "code")
        return wrap_with_boundaries(
            content, "code", item_id, page,
            language=language if language else "unknown",
            breadcrumbs=" > ".join(breadcrumbs)
        )

    # Formula detection disabled - causes too many false positives
    # If you need formula detection, use LaTeX delimiters: $..$ or $$..$$

    return None


def process_image(item: PictureItem, doc, page: int, output_dir: Path,
                 image_counter: int, openai_client, breadcrumbs: List[str],
                 next_item=None) -> Tuple[str, int]:
    """Process image with caption detection"""

    # Check for caption
    caption = None
    if next_item and isinstance(next_item, TextItem):
        text = next_item.text.strip()
        is_caption = (
            text.startswith(('Exhibit', 'Figure', 'Table', 'Chart', 'Fig', 'Source:')) or
            'Source:' in text or (len(text) < 200 and ':' in text)
        )
        if is_caption:
            caption = text

    # Extract and save image
    img_result = extract_and_save_image(
        item, doc, page, output_dir, image_counter,
        openai_client, caption=caption, is_table=False
    )

    if not img_result:
        return "", image_counter

    filename, filepath, ai_desc, type_label = img_result
    item_id = generate_unique_id(page, "image")

    # Build content
    content_parts = [f"**{type_label}**"]
    if caption:
        content_parts.append(f"*Caption:* {caption}")
    content_parts.append(f"![{filename}](../{filepath})")
    content_parts.append(f"*AI Analysis:* {ai_desc}")
    content = "\n".join(content_parts)

    output = wrap_with_boundaries(
        content, "image", item_id, page,
        filename=filename, has_caption="yes" if caption else "no",
        breadcrumbs=" > ".join(breadcrumbs)
    )

    return output, image_counter + 1


def process_table(item: TableItem, doc, page: int, output_dir: Path,
                 image_counter: int, openai_client, breadcrumbs: List[str],
                 next_item=None) -> Tuple[str, int]:
    """Process table - try text first, then image"""

    # Check for caption
    caption = None
    if next_item and isinstance(next_item, TextItem):
        text = next_item.text.strip()
        is_caption = (
            text.startswith(('Exhibit', 'Figure', 'Table', 'Chart', 'Source:')) or
            'Source:' in text or (len(text) < 200 and ':' in text)
        )
        if is_caption:
            caption = text

    # Try text extraction
    text_table_valid = False
    df = None
    md_table = None

    try:
        df = item.export_to_dataframe()
        if not df.empty and len(df) > 0 and len(df.columns) > 0:
            md_table = df.to_markdown(index=False)
            text_table_valid = len(md_table) > 50
    except:
        text_table_valid = False

    # Use text if valid
    if text_table_valid and md_table:
        item_id = generate_unique_id(page, "table")
        table_desc = describe_table_with_ai(md_table, openai_client, caption)

        content_parts = []
        if caption:
            content_parts.append(f"*Caption:* {caption}")
        content_parts.append(md_table)
        content_parts.append(f"\n*AI Analysis:* {table_desc}")
        content = "\n".join(content_parts)

        output = wrap_with_boundaries(
            content, "table", item_id, page,
            rows=len(df), columns=len(df.columns),
            has_caption="yes" if caption else "no",
            breadcrumbs=" > ".join(breadcrumbs)
        )
        return output, image_counter

    # Try image extraction
    img_result = extract_and_save_image(
        item, doc, page, output_dir, image_counter,
        openai_client, caption=caption, is_table=True
    )

    if img_result:
        filename, filepath, ai_desc, type_label = img_result
        item_id = generate_unique_id(page, "image")

        content_parts = [f"**{type_label}**"]
        if caption:
            content_parts.append(f"*Caption:* {caption}")
        content_parts.append(f"![{filename}](../{filepath})")
        content_parts.append(f"*AI Analysis:* {ai_desc}")
        content = "\n".join(content_parts)

        output = wrap_with_boundaries(
            content, "image", item_id, page,
            filename=filename, has_caption="yes" if caption else "no",
            breadcrumbs=" > ".join(breadcrumbs)
        )
        return output, image_counter + 1

    return "", image_counter


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_pdf(pdf_path: Path, output_base_dir: Path, openai_client) -> Dict:
    """Main function to process a single PDF"""
    print(f"\n{'='*70}")
    print(f"Processing: {pdf_path.name}")
    print(f"{'='*70}")

    reset_id_counters()

    doc_output_dir = output_base_dir / pdf_path.stem
    (doc_output_dir / "pages").mkdir(parents=True, exist_ok=True)
    (doc_output_dir / "figures").mkdir(parents=True, exist_ok=True)

    # Convert PDF
    print("   [1/4] Analyzing PDF layout...")
    converter = create_docling_converter()
    conv_result = converter.convert(pdf_path)
    doc = conv_result.document
    print("      SUCCESS: Layout analysis complete")

    # Collect items by page
    print("   [2/4] Collecting document items...")
    pages_items = defaultdict(list)

    for item, level in doc.iterate_items():
        if not item.prov:
            continue
        page_num = item.prov[0].page_no
        pages_items[page_num].append({"item": item, "level": level})

    print(f"      SUCCESS: Collected {sum(len(items) for items in pages_items.values())} items "
          f"across {len(pages_items)} pages")

    # Process each page
    print("   [3/4] Processing items with boundaries...")

    metadata_pages = []
    global_breadcrumbs = []
    total_images = 0
    total_tables = 0

    for page_num in sorted(pages_items.keys()):
        items = pages_items[page_num]
        page_outputs = []
        page_image_count = 0
        page_table_count = 0
        image_counter = 1
        skip_indices = set()

        if global_breadcrumbs:
            page_outputs.append(f"<!-- Context: {' > '.join(global_breadcrumbs)} -->")
        page_outputs.append(f"\n# Page {page_num}\n")

        for idx, entry in enumerate(items):
            if idx in skip_indices:
                continue

            item = entry["item"]
            level = entry["level"]
            next_item = items[idx + 1]["item"] if idx + 1 < len(items) else None

            if isinstance(item, SectionHeaderItem):
                output, global_breadcrumbs = process_header(item, page_num, level, global_breadcrumbs)
                page_outputs.append(output)

            elif isinstance(item, TextItem):
                special_output = process_special_text(item, page_num, global_breadcrumbs)
                if special_output:
                    page_outputs.append(special_output)
                else:
                    output = process_text(item, page_num, global_breadcrumbs)
                    if output:
                        page_outputs.append(output)

            elif isinstance(item, ListItem):
                output = process_list(item, page_num, global_breadcrumbs)
                page_outputs.append(output)

            elif isinstance(item, PictureItem):
                output, image_counter = process_image(
                    item, doc, page_num, doc_output_dir,
                    image_counter, openai_client, global_breadcrumbs, next_item
                )
                if output:
                    page_outputs.append(output)
                    page_image_count += 1
                    if next_item and isinstance(next_item, TextItem):
                        text = next_item.text.strip()
                        if (text.startswith(('Exhibit', 'Figure', 'Table', 'Chart', 'Fig', 'Source:')) or
                            'Source:' in text or (len(text) < 200 and ':' in text)):
                            skip_indices.add(idx + 1)

            elif isinstance(item, TableItem):
                output, image_counter = process_table(
                    item, doc, page_num, doc_output_dir,
                    image_counter, openai_client, global_breadcrumbs, next_item
                )
                if output:
                    page_outputs.append(output)
                    page_table_count += 1
                    if next_item and isinstance(next_item, TextItem):
                        text = next_item.text.strip()
                        if (text.startswith(('Exhibit', 'Figure', 'Table', 'Chart', 'Source:')) or
                            'Source:' in text or (len(text) < 200 and ':' in text)):
                            skip_indices.add(idx + 1)

        # Save page markdown
        page_text = "\n\n".join(page_outputs)
        page_filename = f"page_{page_num}.md"
        with open(doc_output_dir / "pages" / page_filename, "w", encoding="utf-8") as f:
            f.write(page_text)

        metadata_pages.append({
            "page": page_num,
            "file": page_filename,
            "breadcrumbs": list(global_breadcrumbs),
            "images": page_image_count,
            "tables": page_table_count
        })

        total_images += page_image_count
        total_tables += page_table_count

    print(f"      SUCCESS: Processed {len(pages_items)} pages")
    print(f"         Images: {total_images}")
    print(f"         Tables: {total_tables}")

    # Save metadata
    print("   [4/4] Saving metadata...")
    metadata = {
        "file": pdf_path.name,
        "processed": datetime.now().isoformat(),
        "tool": "Docling Simple Bounded",
        "pages": metadata_pages,
        "total_images": total_images,
        "total_tables": total_tables
    }

    with open(doc_output_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"      SUCCESS: Metadata saved")
    print(f"\n{'='*70}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Output: {doc_output_dir}")
    print(f"Pages: {len(metadata_pages)}")
    print(f"Images: {total_images}")
    print(f"Tables: {total_tables}")
    print(f"{'='*70}\n")

    return metadata


def process_batch(input_path: Path, output_base_dir: Path):
    """Process single PDF or all PDFs in directory"""
    if not input_path.exists():
        print(f"\nERROR: Path not found: {input_path}")
        return

    if input_path.is_file():
        if input_path.suffix.lower() != '.pdf':
            print(f"\nERROR: Not a PDF file: {input_path}")
            return
        pdf_files = [input_path]
    else:
        pdf_files = list(input_path.glob("*.pdf"))
        if not pdf_files:
            print(f"\nERROR: No PDF files found in: {input_path}")
            return

    try:
        openai_client = OpenAI()
    except Exception as e:
        print(f"\nERROR: OpenAI client initialization failed: {str(e)}")
        print("NOTE: Set OPENAI_API_KEY environment variable")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING: {len(pdf_files)} PDF(s)")
    print(f"{'='*70}")

    successful = []
    failed = []

    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] {pdf_path.name}")
        try:
            process_pdf(pdf_path, output_base_dir, openai_client)
            successful.append(pdf_path.name)
        except Exception as e:
            print(f"\nERROR - FAILED: {str(e)}")
            failed.append(pdf_path.name)

    print(f"\n{'='*70}")
    print(f"BATCH SUMMARY")
    print(f"{'='*70}")
    print(f"Successful: {len(successful)}/{len(pdf_files)}")
    print(f"Failed: {len(failed)}/{len(pdf_files)}")

    if successful:
        print("\nSuccessfully processed:")
        for name in successful:
            print(f"   [OK] {name}")

    if failed:
        print("\nFailed to process:")
        for name in failed:
            print(f"   [FAIL] {name}")

    print(f"{'='*70}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Docling Simple Extractor with Boundary Markers"
    )

    parser.add_argument("path", type=Path,
                       help="Path to PDF file or directory containing PDFs")
    parser.add_argument("--output", type=Path, default=Path(OUTPUT_DIR),
                       help=f"Output directory (default: {OUTPUT_DIR})")

    args = parser.parse_args()

    try:
        process_batch(args.path, args.output)
    except KeyboardInterrupt:
        print("\n\nWARNING: Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()