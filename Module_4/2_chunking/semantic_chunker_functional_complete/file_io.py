"""
File I/O Module
===============

Handles all file operations: loading metadata, saving output.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List


def load_metadata(input_dir: Path, logger: logging.Logger) -> Dict[str, Any] | None:
    """
    Load metadata.json from input directory.
    
    Parameters
    ----------
    input_dir : Path
        Input directory
    logger : logging.Logger
        Logger
    
    Returns
    -------
    Dict[str, Any] | None
        Metadata dictionary or None if error
    """
    
    metadata_path = input_dir / "metadata.json"
    
    if not metadata_path.exists():
        logger.error(f"metadata.json not found in {input_dir}")
        return None
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        logger.debug(f"Loaded metadata from {metadata_path}")
        return metadata
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metadata.json: {e}")
        return None
    
    except Exception as e:
        logger.error(f"Error loading metadata: {e}")
        return None


def save_chunks_output(
    chunks: List[Dict[str, Any]],
    doc_name: str,
    config: Dict[str, Any],
    detailed_stats: Dict[str, Any],
    input_dir: Path,
    logger: logging.Logger
) -> Path:
    """
    Save chunks and statistics to JSON file.
    
    Parameters
    ----------
    chunks : List[Dict[str, Any]]
        All chunks
    doc_name : str
        Document name
    config : Dict[str, Any]
        Configuration
    detailed_stats : Dict[str, Any]
        Statistics
    input_dir : Path
        Input directory
    logger : logging.Logger
        Logger
    
    Returns
    -------
    Path
        Path to saved output file
    """
    
    output_data = {
        "document": doc_name,
        "total_chunks": len(chunks),
        "chunking_config": {
            "target_size": config['target_size'],
            "min_size": config['min_size'],
            "max_size": config['max_size'],
            "merging_enabled": config['enable_merging']
        },
        "detailed_statistics": detailed_stats,
        "chunks": chunks
    }
    
    output_file = input_dir / "chunks_output.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved output to {output_file}")
        return output_file
    
    except Exception as e:
        logger.error(f"Error saving output: {e}")
        raise
