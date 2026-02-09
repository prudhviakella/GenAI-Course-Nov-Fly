"""
================================================================================
              Simple Chunker Using Boundary Markers
================================================================================

PURPOSE:
========
This script shows how EASY chunking becomes with boundary markers!

Instead of complex regex and parsing logic, we just:
1. Find all BOUNDARY_START markers
2. Extract content between START and END
3. Parse metadata from marker attributes

That's it! No guessing where paragraphs end, no complex state machines!

USAGE:
======
    # Chunk a single page
    python simple_chunker.py path/to/page_1.md

    # Chunk all pages in a directory
    python simple_chunker.py path/to/pages/

    # Output to JSON
    python simple_chunker.py path/to/pages/ --output chunks.json

EXAMPLE OUTPUT:
===============
{
  "chunks": [
    {
      "id": "p3_text_5",
      "type": "paragraph",
      "page": 3,
      "content": "This is the paragraph content...",
      "metadata": {
        "char_count": 145,
        "word_count": 25,
        "breadcrumbs": "Section > Subsection"
      }
    },
    ...
  ]
}
"""

import re
import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional


def extract_chunks_from_markdown(markdown_text: str) -> List[Dict]:
    """
    Extract all chunks from markdown with boundary markers

    This is THE KEY FUNCTION that shows why boundary markers are awesome!

    Args:
        markdown_text: Markdown content with boundary markers

    Returns:
        List of chunk dictionaries

    Example:
        Input markdown:
        '''
        <!-- BOUNDARY_START type="paragraph" id="p3_text_5" page="3" char_count="145" -->
        This is the paragraph content.
        <!-- BOUNDARY_END type="paragraph" id="p3_text_5" -->
        '''

        Output:
        [
            {
                'id': 'p3_text_5',
                'type': 'paragraph',
                'page': '3',
                'content': 'This is the paragraph content.',
                'metadata': {'char_count': '145'}
            }
        ]
    """
    # Pattern to match boundary markers and content between them
    pattern = r'<!-- BOUNDARY_START (.*?) -->\n(.*?)\n<!-- BOUNDARY_END (.*?) -->'

    # Find all matches (DOTALL flag to match across newlines)
    matches = re.findall(pattern, markdown_text, re.DOTALL)

    chunks = []

    for start_attrs, content, end_attrs in matches:
        # Parse attributes from START marker
        # Attributes are in format: key="value" key2="value2"
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', start_attrs))  # Fixed with raw string

        # Extract core fields
        chunk = {
            'id': attrs.get('id', 'unknown'),
            'type': attrs.get('type', 'unknown'),
            'page': attrs.get('page', '0'),
            'content': content.strip()
        }

        # Add all other attributes as metadata
        metadata = {k: v for k, v in attrs.items()
                   if k not in ['id', 'type', 'page']}

        if metadata:
            chunk['metadata'] = metadata

        chunks.append(chunk)

    return chunks


def chunk_file(file_path: Path) -> List[Dict]:
    """
    Extract chunks from a single markdown file

    Args:
        file_path: Path to markdown file

    Returns:
        List of chunks
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return extract_chunks_from_markdown(content)


def chunk_directory(dir_path: Path) -> Dict[str, List[Dict]]:
    """
    Extract chunks from all markdown files in directory

    Automatically handles both:
    - Direct pages directory: extracted_docs/doc_name/pages/
    - Parent directory: extracted_docs/doc_name/ (will find pages/ inside)
    - Batch directory: extracted_docs/ (will find all pages/ subdirs)

    Args:
        dir_path: Path to directory containing markdown files or parent directory

    Returns:
        Dictionary mapping filename to list of chunks
    """
    results = {}

    # Check if this directory contains .md files directly
    md_files = list(dir_path.glob("*.md"))

    if md_files:
        # This is a pages directory
        for md_file in sorted(md_files):
            chunks = chunk_file(md_file)
            results[md_file.name] = chunks
    else:
        # Look for pages/ subdirectories
        # Pattern 1: dir_path/pages/ (single document)
        pages_dir = dir_path / "pages"
        if pages_dir.exists() and pages_dir.is_dir():
            for md_file in sorted(pages_dir.glob("*.md")):
                chunks = chunk_file(md_file)
                results[md_file.name] = chunks
        else:
            # Pattern 2: dir_path/*/pages/ (multiple documents)
            for pages_dir in dir_path.glob("*/pages"):
                if pages_dir.is_dir():
                    for md_file in sorted(pages_dir.glob("*.md")):
                        chunks = chunk_file(md_file)
                        # Include parent folder name to avoid collisions
                        key = f"{pages_dir.parent.name}/{md_file.name}"
                        results[key] = chunks

    return results


def filter_chunks_by_type(chunks: List[Dict], chunk_type: str) -> List[Dict]:
    """
    Filter chunks by type

    Args:
        chunks: List of chunks
        chunk_type: Type to filter (paragraph, header, image, table, etc.)

    Returns:
        Filtered list of chunks
    """
    return [c for c in chunks if c['type'] == chunk_type]


def filter_chunks_by_page(chunks: List[Dict], page: int) -> List[Dict]:
    """
    Filter chunks by page number

    Args:
        chunks: List of chunks
        page: Page number

    Returns:
        Filtered list of chunks
    """
    return [c for c in chunks if int(c['page']) == page]


def combine_chunks_by_breadcrumb(chunks: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group chunks by breadcrumb path

    Args:
        chunks: List of chunks

    Returns:
        Dictionary mapping breadcrumb path to chunks
    """
    grouped = {}

    for chunk in chunks:
        breadcrumb = chunk.get('metadata', {}).get('breadcrumbs', 'No Context')

        if breadcrumb not in grouped:
            grouped[breadcrumb] = []

        grouped[breadcrumb].append(chunk)

    return grouped


def create_semantic_chunks(
    chunks: List[Dict],
    target_size: int = 1500,
    min_size: int = 800
) -> List[Dict]:
    """
    Combine small chunks into larger semantic chunks

    This is a simple example - you can make it much more sophisticated!

    Args:
        chunks: List of atomic chunks from boundary markers
        target_size: Target character count per chunk
        min_size: Minimum character count

    Returns:
        List of combined semantic chunks
    """
    semantic_chunks = []
    buffer = []
    buffer_size = 0
    current_breadcrumb = None

    for chunk in chunks:
        # Get breadcrumb for this chunk
        breadcrumb = chunk.get('metadata', {}).get('breadcrumbs', '')

        # If breadcrumb changes and buffer has content, flush
        if current_breadcrumb and breadcrumb != current_breadcrumb and buffer_size >= min_size:
            semantic_chunks.append({
                'combined_content': '\n\n'.join([c['content'] for c in buffer]),
                'chunk_ids': [c['id'] for c in buffer],
                'breadcrumbs': current_breadcrumb,
                'char_count': buffer_size,
                'num_chunks': len(buffer)
            })
            buffer = []
            buffer_size = 0

        # Add to buffer
        buffer.append(chunk)
        buffer_size += len(chunk['content'])
        current_breadcrumb = breadcrumb

        # If buffer reaches target size, flush
        if buffer_size >= target_size:
            semantic_chunks.append({
                'combined_content': '\n\n'.join([c['content'] for c in buffer]),
                'chunk_ids': [c['id'] for c in buffer],
                'breadcrumbs': current_breadcrumb,
                'char_count': buffer_size,
                'num_chunks': len(buffer)
            })
            buffer = []
            buffer_size = 0

    # Flush remaining
    if buffer:
        semantic_chunks.append({
            'combined_content': '\n\n'.join([c['content'] for c in buffer]),
            'chunk_ids': [c['id'] for c in buffer],
            'breadcrumbs': current_breadcrumb,
            'char_count': buffer_size,
            'num_chunks': len(buffer)
        })

    return semantic_chunks


def print_chunk_summary(chunks: List[Dict]):
    """Print summary statistics about chunks"""
    total = len(chunks)

    # Count by type
    type_counts = {}
    for chunk in chunks:
        chunk_type = chunk['type']
        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1

    # Count by page
    page_counts = {}
    for chunk in chunks:
        page = chunk['page']
        page_counts[page] = page_counts.get(page, 0) + 1

    print(f"\nChunk Summary")
    print(f"{'='*50}")
    print(f"Total chunks: {total}")
    print(f"\nBy type:")
    for chunk_type, count in sorted(type_counts.items()):
        print(f"  {chunk_type:15s}: {count:4d}")
    print(f"\nBy page:")
    for page, count in sorted(page_counts.items(), key=lambda x: int(x[0])):
        print(f"  Page {page:3s}: {count:4d} chunks")
    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Simple Chunker for Boundary-Marked Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract chunks from single file
  python simple_chunker.py page_1.md
  
  # Extract from all files in directory
  python simple_chunker.py pages/
  
  # Save to JSON
  python simple_chunker.py pages/ --output chunks.json
  
  # Filter by type
  python simple_chunker.py pages/ --type paragraph
  
  # Filter by page
  python simple_chunker.py pages/ --page 3
  
  # Create semantic chunks
  python simple_chunker.py pages/ --semantic --target-size 1500
        """
    )

    parser.add_argument(
        "path",
        type=Path,
        help="Path to markdown file or directory"
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON file (default: auto-saved as chunks.json in input directory)"
    )

    parser.add_argument(
        "--type",
        help="Filter by chunk type (paragraph, header, image, table, etc.)"
    )

    parser.add_argument(
        "--page",
        type=int,
        help="Filter by page number"
    )

    parser.add_argument(
        "--semantic",
        action="store_true",
        help="Combine into larger semantic chunks"
    )

    parser.add_argument(
        "--target-size",
        type=int,
        default=1500,
        help="Target size for semantic chunks (default: 1500)"
    )

    parser.add_argument(
        "--min-size",
        type=int,
        default=800,
        help="Minimum size for semantic chunks (default: 800)"
    )

    args = parser.parse_args()

    # Extract chunks
    if args.path.is_file():
        print(f"Processing file: {args.path.name}")
        chunks = chunk_file(args.path)
    else:
        print(f"Processing directory: {args.path}")
        results = chunk_directory(args.path)

        # Show what was found
        if not results:
            print("\nWARNING: No markdown files found!")
            print("\nExpected structure:")
            print("  extracted_docs_bounded/")
            print("  └── document_name/")
            print("      └── pages/")
            print("          ├── page_1.md")
            print("          └── page_2.md")
            print("\nTry:")
            print(f"  python {sys.argv[0]} {args.path}/document_name/pages/")
            print(f"  python {sys.argv[0]} {args.path}/document_name/")
            return

        # Show found files
        print(f"\nFound {len(results)} markdown file(s):")
        for filename in list(results.keys())[:5]:
            print(f"  - {filename}")
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more")

        # Flatten all chunks
        chunks = []
        for file_chunks in results.values():
            chunks.extend(file_chunks)

    print(f"SUCCESS: Extracted {len(chunks)} atomic chunks")

    if not chunks:
        print("\nNo chunks found! Check that:")
        print("1. Markdown files contain boundary markers")
        print("2. Files are in the correct directory")
        print("3. Boundary markers are in correct format:")
        print("   <!-- BOUNDARY_START type=\"...\" id=\"...\" page=\"...\" -->")
        return

    # Apply filters
    if args.type:
        chunks = filter_chunks_by_type(chunks, args.type)
        print(f"FILTERED: {len(chunks)} chunks of type '{args.type}'")

    if args.page:
        chunks = filter_chunks_by_page(chunks, args.page)
        print(f"FILTERED: {len(chunks)} chunks from page {args.page}")

    # Create semantic chunks if requested
    if args.semantic:
        semantic_chunks = create_semantic_chunks(
            chunks,
            target_size=args.target_size,
            min_size=args.min_size
        )
        print(f"COMBINED: {len(semantic_chunks)} semantic chunks")
        output_data = {
            'atomic_chunks': chunks,
            'semantic_chunks': semantic_chunks
        }
    else:
        output_data = {'chunks': chunks}

    # Print summary
    print_chunk_summary(chunks)

    # Auto-generate output path if not specified
    output_path = args.output
    if not output_path:
        # Determine base directory
        if args.path.is_file():
            base_dir = args.path.parent
        else:
            base_dir = args.path

        # Generate filename
        if args.semantic:
            output_filename = "semantic_chunks.json"
        else:
            output_filename = "chunks.json"

        output_path = base_dir / output_filename

    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\nSAVED: {output_path}")
    print(f"       ({len(chunks)} atomic chunks)")
    if args.semantic:
        print(f"       ({len(output_data['semantic_chunks'])} semantic chunks)")

    # Print sample chunks
    print("\nSample Chunks (first 3):")
    print("="*70)
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\nChunk {i}:")
        print(f"  ID: {chunk['id']}")
        print(f"  Type: {chunk['type']}")
        print(f"  Page: {chunk['page']}")
        if 'metadata' in chunk:
            print(f"  Metadata: {chunk['metadata']}")
        print(f"  Content: {chunk['content'][:100]}...")
    print("="*70)


if __name__ == "__main__":
    main()