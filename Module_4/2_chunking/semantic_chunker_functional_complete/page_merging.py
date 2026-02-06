"""
Page Merging Module
===================

Merges chunks at page boundaries when continuation is detected.
Only merges text chunks; preserves protected blocks intact.
"""

import logging
from typing import List, Dict, Any


def merge_continued_pages(
    current_chunks: List[Dict[str, Any]],
    next_chunks: List[Dict[str, Any]],
    current_page_num: int,
    next_page_num: int,
    config: Dict[str, Any],
    stats: Dict[str, Any],
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Merge boundary chunks from consecutive pages.
    
    Only merges if both boundary chunks are text type.
    Preserves protected blocks (tables, images, code).
    
    Parameters
    ----------
    current_chunks : List[Dict[str, Any]]
        Chunks from current page
    next_chunks : List[Dict[str, Any]]
        Chunks from next page
    current_page_num : int
        Current page number
    next_page_num : int
        Next page number
    config : Dict[str, Any]
        Configuration
    stats : Dict[str, Any]
        Statistics
    logger : logging.Logger
        Logger
    
    Returns
    -------
    List[Dict[str, Any]]
        Merged chunks
    """
    
    if not current_chunks or not next_chunks:
        return current_chunks + next_chunks
    
    last_chunk = current_chunks[-1]
    first_chunk = next_chunks[0]
    
    # Only merge text chunks
    if last_chunk['metadata']['type'] == 'text' and first_chunk['metadata']['type'] == 'text':
        logger.debug("  Merging boundary text chunks")
        
        # Merge content
        merged_content = last_chunk['content_only'] + "\n\n" + first_chunk['content_only']
        
        # Use more specific breadcrumbs
        if len(first_chunk['metadata']['breadcrumbs']) > len(last_chunk['metadata']['breadcrumbs']):
            merged_breadcrumbs = first_chunk['metadata']['breadcrumbs']
        else:
            merged_breadcrumbs = last_chunk['metadata']['breadcrumbs']
        
        # Import create_chunk
        from chunking_engine import create_chunk
        
        # Create merged chunk
        context_str = " > ".join(merged_breadcrumbs)
        merged_chunk = create_chunk(
            merged_content, context_str, last_chunk['metadata'],
            "text", config, logger
        )
        
        # Add merge metadata
        merged_chunk['metadata']['merged_from_pages'] = [current_page_num, next_page_num]
        merged_chunk['metadata']['is_merged'] = True
        
        logger.info(f"  Merged chunk spans pages {current_page_num}-{next_page_num}")
        logger.debug(f"  Merged content length: {len(merged_content)} chars")
        
        return current_chunks[:-1] + [merged_chunk] + next_chunks[1:]
    else:
        logger.debug(
            f"  Cannot merge: types are {last_chunk['metadata']['type']} "
            f"and {first_chunk['metadata']['type']}"
        )
        return current_chunks + next_chunks
