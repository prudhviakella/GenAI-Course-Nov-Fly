"""
Statistics Calculator Module
=============================

Calculates comprehensive statistics about the chunking results.
"""

import math
from typing import List, Dict, Any
import logging


def calculate_comprehensive_statistics(
    chunks: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Calculate detailed statistics from chunks.
    
    Parameters
    ----------
    chunks : List[Dict[str, Any]]
        All chunks
    stats : Dict[str, Any]
        Basic statistics
    config : Dict[str, Any]
        Configuration
    logger : logging.Logger
        Logger
    
    Returns
    -------
    Dict[str, Any]
        Comprehensive statistics
    """
    
    if not chunks:
        return {}
    
    logger.debug("  Calculating statistics...")
    
    # Collect basic data
    sizes = [len(c['content_only']) for c in chunks]
    types = {}
    pages = {}
    
    # Quality metrics
    total_words = 0
    total_sentences = 0
    chunks_with_numbers = 0
    chunks_with_dates = 0
    chunks_with_entities = 0
    chunks_with_exhibits = 0
    chunks_with_citations = 0
    
    for chunk in chunks:
        # Type distribution
        chunk_type = chunk['metadata']['type']
        types[chunk_type] = types.get(chunk_type, 0) + 1
        
        # Page distribution
        page_num = chunk['metadata']['page_number']
        pages[page_num] = pages.get(page_num, 0) + 1
        
        # Quality metrics
        qm = chunk['metadata'].get('quality_metrics', {})
        total_words += qm.get('word_count', 0)
        total_sentences += qm.get('sentence_count', 0)
        
        if qm.get('has_numerical_data'):
            chunks_with_numbers += 1
        if qm.get('has_dates'):
            chunks_with_dates += 1
        if qm.get('has_named_entities'):
            chunks_with_entities += 1
        if qm.get('has_exhibits'):
            chunks_with_exhibits += 1
        if chunk['metadata'].get('has_citations'):
            chunks_with_citations += 1
    
    # Size statistics
    mean_size = sum(sizes) / len(sizes)
    sorted_sizes = sorted(sizes)
    median_size = sorted_sizes[len(sizes) // 2]
    std_dev = math.sqrt(sum((x - mean_size) ** 2 for x in sizes) / len(sizes))
    
    detailed_stats = {
        "size_distribution": {
            "min": min(sizes),
            "max": max(sizes),
            "mean": round(mean_size, 1),
            "median": median_size,
            "std_dev": round(std_dev, 1),
            "percentile_25": sorted_sizes[len(sizes) // 4],
            "percentile_75": sorted_sizes[3 * len(sizes) // 4]
        },
        "type_distribution": types,
        "chunks_per_page": pages,
        "avg_chunks_per_page": round(len(chunks) / len(pages), 2) if pages else 0,
        "content_analysis": {
            "total_words": total_words,
            "total_sentences": total_sentences,
            "avg_words_per_chunk": round(total_words / len(chunks), 1) if chunks else 0,
            "chunks_with_numerical_data": chunks_with_numbers,
            "chunks_with_dates": chunks_with_dates,
            "chunks_with_entities": chunks_with_entities,
            "chunks_with_exhibits": chunks_with_exhibits,
            "chunks_with_citations": chunks_with_citations
        },
        "processing_stats": {
            "total_pages": stats['total_pages'],
            "total_chunks": stats['total_chunks'],
            "duplicates_prevented": stats['duplicates_prevented'],
            "validation_failures": stats['validation_failures'],
            "merged_boundaries": stats['merged_boundaries'],
            "protected_blocks": stats['protected_blocks']
        }
    }
    
    logger.debug(f"  Statistics calculated for {len(chunks)} chunks")
    
    return detailed_stats
