"""
================================================================================
CHUNK ENRICHMENT PIPELINE - AWS BEDROCK VERSION
================================================================================

This script:
1. Reads chunked document (JSON output from semantic chunker)
2. Enriches each chunk with metadata (AWS Bedrock + custom patterns)
3. Saves enriched chunks to new JSON file

DIFFERENCE FROM COMPREHEND VERSION:
───────────────────────────────────
Uses AWS Bedrock (Claude) instead of AWS Comprehend
- More expensive (~3x cost)
- More flexible (custom extraction schema)
- Deeper analysis (sentiment, insights, topics)
- Better quality (95-99% vs 90-95% accuracy)

Author: Prudhvi
Created: 2025-01-05
Version: 1.0.0
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Import Bedrock enricher instead of Comprehend
from metadata_enricher_bedrock import BedrockMetadataEnricher


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# BEDROCK CHUNK ENRICHMENT PIPELINE
# ============================================================================

class BedrockChunkEnrichmentPipeline:
    """
    End-to-end pipeline for enriching chunked documents with Bedrock.
    
    Same interface as ChunkEnrichmentPipeline but uses Bedrock enricher.
    
    Usage
    -----
    ```python
    pipeline = BedrockChunkEnrichmentPipeline(
        region_name='us-east-1',
        model_id='anthropic.claude-3-5-sonnet-20241022-v1:0'
    )
    
    pipeline.process('chunks_output.json')
    # Creates: chunks_output_enriched_metadata.json
    ```
    """
    
    def __init__(
        self,
        region_name: str = 'us-east-1',
        model_id: str = 'anthropic.claude-3-5-sonnet-20241022-v1:0',
        enable_bedrock: bool = True,
        enable_patterns: bool = True,
        temperature: float = 0.0,
        batch_size: int = 100
    ):
        """
        Initialize the Bedrock enrichment pipeline.
        
        Parameters
        ----------
        region_name : str
            AWS region for Bedrock
            
        model_id : str
            Bedrock model ID
            Options:
            - 'anthropic.claude-3-5-sonnet-20241022-v1:0' (best quality)
            - 'anthropic.claude-3-haiku-20240307-v1:0' (cheapest)
            
        enable_bedrock : bool
            Use AWS Bedrock
            
        enable_patterns : bool
            Use custom regex patterns
            
        temperature : float
            Model temperature (0.0 = deterministic)
            
        batch_size : int
            Progress update frequency
        """
        self.region_name = region_name
        self.model_id = model_id
        self.enable_bedrock = enable_bedrock
        self.enable_patterns = enable_patterns
        self.temperature = temperature
        self.batch_size = batch_size
        
        # Initialize Bedrock enricher
        logger.info("Initializing BedrockMetadataEnricher...")
        self.enricher = BedrockMetadataEnricher(
            region_name=region_name,
            model_id=model_id,
            enable_bedrock=enable_bedrock,
            enable_patterns=enable_patterns,
            temperature=temperature
        )
        logger.info("✓ BedrockMetadataEnricher initialized")
    
    @staticmethod
    def generate_output_filename(input_file: str) -> str:
        """Generate output filename: <base>_enriched_metadata.json"""
        input_path = Path(input_file)
        input_stem = input_path.stem
        input_dir = input_path.parent
        output_filename = f"{input_stem}_enriched_metadata.json"
        return str(input_dir / output_filename)
    
    def load_chunks(self, input_file: str) -> List[Dict]:
        """Load chunks from JSON file."""
        logger.info(f"Loading chunks from: {input_file}")
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'chunks' in data:
            chunks = data['chunks']
        elif isinstance(data, list):
            chunks = data
        else:
            raise ValueError(
                "Invalid input format. Expected dict with 'chunks' key or list of chunks"
            )
        
        logger.info(f"✓ Loaded {len(chunks)} chunks")
        return chunks
    
    def validate_chunk(self, chunk: Dict, index: int) -> bool:
        """Validate chunk has required fields."""
        required_fields = ['id', 'text', 'content_only', 'metadata']
        
        for field in required_fields:
            if field not in chunk:
                logger.warning(
                    f"Chunk {index} missing required field '{field}'. Skipping."
                )
                return False
        
        if not chunk['content_only'] or not chunk['content_only'].strip():
            logger.warning(
                f"Chunk {index} (id: {chunk['id']}) has empty content_only. Skipping."
            )
            return False
        
        return True
    
    def enrich_chunks(
        self,
        chunks: List[Dict],
        show_progress: bool = True
    ) -> List[Dict]:
        """Enrich all chunks with Bedrock metadata."""
        logger.info(f"Starting enrichment of {len(chunks)} chunks...")
        logger.info(f"Bedrock Model: {self.model_id}")
        logger.info(f"Bedrock: {'ENABLED' if self.enable_bedrock else 'DISABLED'}")
        logger.info(f"Patterns: {'ENABLED' if self.enable_patterns else 'DISABLED'}")
        
        enriched_chunks = []
        skipped_count = 0
        
        for i, chunk in enumerate(chunks, 1):
            if not self.validate_chunk(chunk, i):
                skipped_count += 1
                enriched_chunks.append(chunk)
                continue
            
            try:
                enriched = self.enricher.enrich_chunk(chunk)
                enriched_chunks.append(enriched)
            except Exception as e:
                logger.error(f"Error enriching chunk {i} (id: {chunk['id']}): {e}")
                enriched_chunks.append(chunk)
                skipped_count += 1
            
            if show_progress and i % self.batch_size == 0:
                pct = (i / len(chunks)) * 100
                logger.info(f"Progress: {i}/{len(chunks)} ({pct:.1f}%)")
        
        logger.info(f"✓ Enrichment complete!")
        logger.info(f"  - Successfully enriched: {len(chunks) - skipped_count}")
        logger.info(f"  - Skipped/Failed: {skipped_count}")
        
        return enriched_chunks
    
    def save_enriched_chunks(
        self,
        enriched_chunks: List[Dict],
        output_file: str,
        include_statistics: bool = True
    ):
        """Save enriched chunks to JSON file."""
        logger.info(f"Saving enriched chunks to: {output_file}")
        
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        
        output_data = {
            "metadata": {
                "enriched_at": datetime.now().isoformat(),
                "total_chunks": len(enriched_chunks),
                "enrichment_config": {
                    "enricher": "bedrock",
                    "region_name": self.region_name,
                    "model_id": self.model_id,
                    "bedrock_enabled": self.enable_bedrock,
                    "patterns_enabled": self.enable_patterns,
                    "temperature": self.temperature
                }
            },
            "chunks": enriched_chunks
        }
        
        if include_statistics:
            output_data["statistics"] = {
                "enrichment_stats": self.enricher.get_statistics()
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        file_size = os.path.getsize(output_file)
        file_size_mb = file_size / (1024 * 1024)
        
        logger.info(f"✓ Saved enriched chunks")
        logger.info(f"  - Output file: {output_file}")
        logger.info(f"  - File size: {file_size_mb:.2f} MB")
    
    def process(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        show_progress: bool = True,
        print_statistics: bool = True
    ):
        """Complete end-to-end processing pipeline."""
        if output_file is None:
            output_file = self.generate_output_filename(input_file)
            logger.info(f"Auto-generated output filename: {output_file}")
        
        logger.info("="*70)
        logger.info("BEDROCK CHUNK ENRICHMENT PIPELINE - Starting")
        logger.info("="*70)
        logger.info(f"Input file:  {input_file}")
        logger.info(f"Output file: {output_file}")
        logger.info("")
        
        try:
            logger.info("STEP 1: Loading chunks...")
            chunks = self.load_chunks(input_file)
            logger.info("")
            
            logger.info("STEP 2: Enriching chunks with Bedrock...")
            enriched_chunks = self.enrich_chunks(chunks, show_progress)
            logger.info("")
            
            logger.info("STEP 3: Saving enriched chunks...")
            self.save_enriched_chunks(enriched_chunks, output_file)
            logger.info("")
            
            if print_statistics:
                logger.info("STEP 4: Enrichment statistics")
                self.enricher.print_statistics()
            
            logger.info("="*70)
            logger.info("BEDROCK CHUNK ENRICHMENT PIPELINE - Completed Successfully!")
            logger.info("="*70)
            
        except Exception as e:
            logger.error("="*70)
            logger.error("BEDROCK CHUNK ENRICHMENT PIPELINE - FAILED")
            logger.error("="*70)
            logger.error(f"Error: {e}")
            raise


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Command-line interface for Bedrock enrichment pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enrich semantic chunks with metadata using AWS Bedrock (Claude)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (auto-generates output filename)
  python enrich_chunks_bedrock.py chunks_output.json
  → Creates: chunks_output_enriched_metadata.json
  
  # Specify custom output filename
  python enrich_chunks_bedrock.py chunks_output.json my_enriched.json
  
  # Use cheaper Haiku model
  python enrich_chunks_bedrock.py input.json --model haiku
  
  # Disable Bedrock (patterns only, free)
  python enrich_chunks_bedrock.py input.json --no-bedrock
  
  # Custom temperature (more creative)
  python enrich_chunks_bedrock.py input.json --temperature 0.3
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Input JSON file with chunks'
    )
    
    parser.add_argument(
        'output_file',
        nargs='?',
        default=None,
        help='Output JSON file (default: <input_base>_enriched_metadata.json)'
    )
    
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region for Bedrock (default: us-east-1)'
    )
    
    parser.add_argument(
        '--model',
        choices=['sonnet', 'haiku', 'opus'],
        default='sonnet',
        help='Claude model to use (default: sonnet)'
    )
    
    parser.add_argument(
        '--no-bedrock',
        action='store_true',
        help='Disable AWS Bedrock (use patterns only)'
    )
    
    parser.add_argument(
        '--no-patterns',
        action='store_true',
        help='Disable custom patterns (use Bedrock only)'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.0,
        help='Model temperature 0.0-1.0 (default: 0.0)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Progress update frequency (default: 100)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )
    
    args = parser.parse_args()
    
    # Generate output filename if not provided
    if args.output_file is None:
        input_path = Path(args.input_file)
        input_stem = input_path.stem
        input_dir = input_path.parent
        output_filename = f"{input_stem}_enriched_metadata.json"
        args.output_file = str(input_dir / output_filename)
        logger.info(f"No output file specified. Using: {args.output_file}")
    
    # Validate temperature
    if not 0.0 <= args.temperature <= 1.0:
        parser.error("Temperature must be between 0.0 and 1.0")
    
    # Map model choice to model ID
    model_ids = {
        'sonnet': 'anthropic.claude-3-5-sonnet-20241022-v1:0',
        'haiku': 'anthropic.claude-3-haiku-20240307-v1:0',
        'opus': 'anthropic.claude-3-opus-20240229-v1:0'
    }
    model_id = model_ids[args.model]
    
    # Create pipeline
    pipeline = BedrockChunkEnrichmentPipeline(
        region_name=args.region,
        model_id=model_id,
        enable_bedrock=not args.no_bedrock,
        enable_patterns=not args.no_patterns,
        temperature=args.temperature,
        batch_size=args.batch_size
    )
    
    # Run pipeline
    pipeline.process(
        input_file=args.input_file,
        output_file=args.output_file,
        show_progress=not args.quiet,
        print_statistics=not args.quiet
    )


# ============================================================================
# PROGRAMMATIC USAGE EXAMPLES
# ============================================================================

def example_bedrock_basic():
    """Example: Basic Bedrock enrichment."""
    print("\n" + "="*70)
    print("EXAMPLE: Basic Bedrock Enrichment")
    print("="*70 + "\n")
    
    pipeline = BedrockChunkEnrichmentPipeline(
        region_name='us-east-1',
        model_id='anthropic.claude-3-5-sonnet-20241022-v1:0'
    )
    
    pipeline.process('chunks_output.json')


def example_bedrock_haiku():
    """Example: Use cheaper Haiku model."""
    print("\n" + "="*70)
    print("EXAMPLE: Bedrock with Haiku (Cheaper)")
    print("="*70 + "\n")
    
    pipeline = BedrockChunkEnrichmentPipeline(
        region_name='us-east-1',
        model_id='anthropic.claude-3-haiku-20240307-v1:0'  # Cheaper!
    )
    
    pipeline.process(
        input_file='chunks_output.json',
        output_file='enriched_chunks_haiku.json'
    )


def example_bedrock_patterns_only():
    """Example: Patterns only (no Bedrock, free)."""
    print("\n" + "="*70)
    print("EXAMPLE: Patterns Only (No Bedrock)")
    print("="*70 + "\n")
    
    pipeline = BedrockChunkEnrichmentPipeline(
        enable_bedrock=False,  # No Bedrock = FREE
        enable_patterns=True
    )
    
    pipeline.process(
        input_file='chunks_output.json',
        output_file='enriched_chunks_patterns_only.json'
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    """
    Run the Bedrock pipeline.
    
    Usage:
    1. Command line: python enrich_chunks_bedrock.py input.json
    2. Examples: Comment out main() and uncomment examples
    """
    
    # Command line mode
    main()
    
    # Example mode (uncomment to run)
    # example_bedrock_basic()
    # example_bedrock_haiku()
    # example_bedrock_patterns_only()
