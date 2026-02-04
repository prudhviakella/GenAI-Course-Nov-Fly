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

from pathlib import Path
from typing import Optional

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

# Extract all elements from PDF using Unstructured's partition function
elements = partition(
    # File path (converted to string as required by partition API)
    filename=str(doc_path),

    # Strategy: "hi_res" for high-resolution parsing
    # -----------------------------------------------
    # Options:
    #   - "fast": Quick processing, lower quality
    #   - "hi_res": Slower but better quality, uses vision models
    #   - "auto": Automatically selects strategy
    #
    # "hi_res" is recommended for:
    #   - Complex layouts
    #   - Documents with tables/charts
    #   - High-quality output requirements
    strategy="hi_res",

    # Image Extraction: Enable extraction of embedded images
    # -------------------------------------------------------
    # When True:
    #   - Extracts images from PDF
    #   - Saves to output directory
    #   - Returns image metadata in elements
    #
    # Use cases:
    #   - Charts and diagrams
    #   - Logos and graphics
    #   - Scanned content
    extract_images_in_pdf=True,

    # Table Structure Inference: Parse table structure
    # ------------------------------------------------
    # When True:
    #   - Detects tables in document
    #   - Infers row/column structure
    #   - Preserves table formatting
    #   - Returns structured table data
    #
    # Benefits:
    #   - Maintains data relationships
    #   - Enables easier data extraction
    #   - Better than treating tables as plain text
    infer_table_structure=True
)

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


