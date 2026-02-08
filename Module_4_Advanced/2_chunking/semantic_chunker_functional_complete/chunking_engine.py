"""
Chunking Engine Module
=======================

EDUCATIONAL PURPOSE
-------------------
This module converts semantic sections into final chunks, handling:
- Size constraints (target, min, max)
- Smart splitting at sentence boundaries
- Buffer management and flushing

WHY SEPARATE CHUNKING FROM PARSING?
------------------------------------
SEPARATION OF CONCERNS:
- Parsing: Identify meaningful units in document
- Chunking: Group units to meet size requirements

This makes each part:
- Easier to understand
- Easier to test
- Easier to modify independently

CORE ALGORITHM
--------------
We use a BUFFER ACCUMULATOR pattern:

    buffer = []
    for each section:
        add to buffer
        if buffer_size >= target:
            flush buffer → create chunk
            reset buffer

This ensures chunks respect semantic boundaries while meeting size goals.
"""

import hashlib
import re
import logging
from typing import List, Dict, Any, Tuple


# ============================================================================
# MAIN CHUNKING FUNCTION
# ============================================================================

def build_chunks_from_sections(
    sections: List[Dict[str, Any]],
    page_meta: Dict[str, Any],
    config: Dict[str, Any],
    stats: Dict[str, Any],
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Convert semantic sections into final chunks.
    
    ALGORITHM
    ---------
    1. For each section:
        - If protected block → emit directly
        - If major header → flush buffer first
        - If minor header → update context only
        - If text → accumulate in buffer
    
    2. When buffer reaches target size → flush
    
    3. At end → flush remaining buffer
    
    Parameters
    ----------
    sections : List[Dict[str, Any]]
        Semantic sections from parsing
    page_meta : Dict[str, Any]
        Page metadata (file_name, page_number)
    config : Dict[str, Any]
        Configuration settings
    stats : Dict[str, Any]
        Statistics accumulator
    logger : logging.Logger
        Logger for debug output
    
    Returns
    -------
    List[Dict[str, Any]]
        Final chunks ready for output
    """
    
    logger.debug("  Building chunks from sections...")
    
    chunks = []
    text_buffer = []
    current_size = 0
    current_breadcrumbs = []
    
    target_size = config['target_size']
    min_size = config['min_size']
    
    for section in sections:
        section_type = section['type']
        section_content = section['content']
        section_breadcrumbs = section['breadcrumbs']
        
        # ====================================================================
        # CASE 1: Protected block (table, image, code)
        # ====================================================================
        
        if section_type in ['image', 'table', 'code']:
            # Flush any accumulated text first
            if text_buffer:
                _flush_buffer(
                    text_buffer, current_breadcrumbs, page_meta,
                    config, chunks, stats, logger
                )
                text_buffer = []
                current_size = 0
            
            # Create chunk for protected block
            context_str = " > ".join(section_breadcrumbs)
            chunk = create_chunk(
                section_content, context_str, page_meta,
                section_type, config, logger
            )
            
            # Add with deduplication
            if validate_chunk(chunk, config, stats, logger):
                add_chunk_with_dedup(chunks, chunk, stats, logger)
        
        # ====================================================================
        # CASE 2: Major header (H1, H2)
        # ====================================================================
        
        elif section_type == 'major_header':
            # Flush buffer at major boundaries
            if text_buffer and current_size >= min_size:
                _flush_buffer(
                    text_buffer, current_breadcrumbs, page_meta,
                    config, chunks, stats, logger
                )
                text_buffer = []
                current_size = 0
            
            # Update breadcrumbs
            current_breadcrumbs = section_breadcrumbs
        
        # ====================================================================
        # CASE 3: Minor header (H3-H6)
        # ====================================================================
        
        elif section_type == 'minor_header':
            # Just update context, don't flush
            current_breadcrumbs = section_breadcrumbs
        
        # ====================================================================
        # CASE 4: Text content
        # ====================================================================
        
        elif section_type == 'text':
            # Accumulate text
            text_buffer.append(section_content)
            current_size += len(section_content)
            
            # Flush if exceeded target
            if current_size >= target_size:
                _flush_buffer(
                    text_buffer, current_breadcrumbs, page_meta,
                    config, chunks, stats, logger
                )
                text_buffer = []
                current_size = 0
    
    # Final flush
    if text_buffer:
        _flush_buffer(
            text_buffer, current_breadcrumbs, page_meta,
            config, chunks, stats, logger
        )
    
    logger.debug(f"    Created {len(chunks)} chunks")
    
    return chunks


# ============================================================================
# BUFFER FLUSHING
# ============================================================================

def _flush_buffer(
    buffer: List[str],
    breadcrumbs: List[str],
    page_meta: Dict[str, Any],
    config: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    stats: Dict[str, Any],
    logger: logging.Logger
):
    """
    Flush accumulated text buffer into chunks.
    
    Handles two cases:
    1. Buffer fits in max_size → create single chunk
    2. Buffer exceeds max_size → split at sentence boundaries
    """
    
    full_text = "".join(buffer).strip()
    if not full_text:
        return
    
    context_str = " > ".join(breadcrumbs)
    max_size = config['max_size']
    
    logger.debug(f"    Flushing buffer: {len(full_text)} chars")
    
    # Case 1: Fits in single chunk
    if len(full_text) <= max_size:
        chunk = create_chunk(
            full_text, context_str, page_meta, "text", config, logger
        )
        if validate_chunk(chunk, config, stats, logger):
            add_chunk_with_dedup(chunks, chunk, stats, logger)
        return
    
    # Case 2: Need to split
    sub_chunks = smart_split(full_text, config, logger)
    for sub_text in sub_chunks:
        chunk = create_chunk(
            sub_text, context_str, page_meta, "text", config, logger
        )
        if validate_chunk(chunk, config, stats, logger):
            add_chunk_with_dedup(chunks, chunk, stats, logger)
    
    logger.debug(f"    Split into {len(sub_chunks)} sub-chunks")


# ============================================================================
# SMART SPLITTING
# ============================================================================

def smart_split(
    text: str,
    config: Dict[str, Any],
    logger: logging.Logger
) -> List[str]:
    """
    Split text at sentence boundaries to stay within size limits.
    
    ALGORITHM
    ---------
    1. Split text into sentences
    2. Accumulate sentences until reaching target size
    3. When exceeding target (but above min), create chunk
    4. Continue with remaining sentences
    
    WHY SENTENCE BOUNDARIES?
    ------------------------
    Splitting mid-sentence creates broken, unusable chunks:
        BAD:  "The system uses three components: data ingestion, proce"
        GOOD: "The system uses three components: data ingestion."
    
    Parameters
    ----------
    text : str
        Text to split
    config : Dict[str, Any]
        Configuration with size limits
    logger : logging.Logger
        Logger for debug output
    
    Returns
    -------
    List[str]
        Text split into chunks at sentence boundaries
    """
    
    target_size = config['target_size']
    min_size = config['min_size']
    sentence_pattern = config['patterns']['sentence']
    
    # Split into sentences
    sentences = sentence_pattern.split(text)
    
    chunks = []
    current_chunk = []
    current_len = 0
    
    for sentence in sentences:
        sent_len = len(sentence)
        
        # Would adding this sentence exceed target?
        if current_len + sent_len > target_size and current_len >= min_size:
            # Flush current chunk
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_len = sent_len
        else:
            # Add to current chunk
            current_chunk.append(sentence)
            current_len += sent_len
    
    # Flush remaining
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    logger.debug(f"      Smart split: {len(text)} chars → {len(chunks)} chunks")
    
    return chunks


# ============================================================================
# CHUNK CREATION
# ============================================================================

def create_chunk(
    content: str,
    context: str,
    page_meta: Dict[str, Any],
    chunk_type: str,
    config: Dict[str, Any],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Create a chunk with comprehensive metadata.
    
    CHUNK STRUCTURE
    ---------------
    {
        "id": "abc123...",  # MD5 hash of content
        "text": "Context: ...\n\nContent",  # For embedding
        "content_only": "Content",  # For display
        "metadata": {
            "source": "page_005.md",
            "page_number": 5,
            "type": "text",
            "breadcrumbs": ["Section", "Subsection"],
            "quality_metrics": {...}
        }
    }
    
    Parameters
    ----------
    content : str
        Chunk content
    context : str
        Hierarchical context (breadcrumbs joined with " > ")
    page_meta : Dict[str, Any]
        Page metadata
    chunk_type : str
        Type: text, table, image, or code
    config : Dict[str, Any]
        Configuration
    logger : logging.Logger
        Logger
    
    Returns
    -------
    Dict[str, Any]
        Complete chunk dictionary
    """
    
    # Build RAG text with context
    if context:
        rag_text = f"Context: {context}\n\n{content}"
    else:
        rag_text = content
    
    # Generate deterministic ID
    chunk_id = hashlib.md5(rag_text.encode('utf-8')).hexdigest()
    
    # Extract quality metrics
    metrics = _extract_quality_metrics(content, config)
    
    # Extract additional features
    img_path = _extract_image_path(content)
    source_attr = _extract_source_attribution(content, config)
    
    # Build hierarchical context
    breadcrumbs = context.split(" > ") if context else []
    hierarchical = _build_hierarchical_context(breadcrumbs)
    
    chunk = {
        "id": chunk_id,
        "text": rag_text,
        "content_only": content,
        "metadata": {
            "source": page_meta.get('file_name') or page_meta.get('file'),
            "page_number": page_meta.get('page_number'),
            "type": chunk_type,
            "breadcrumbs": breadcrumbs,
            "hierarchical_context": hierarchical,
            "image_path": img_path,
            "source_attribution": source_attr,
            "has_citations": bool(source_attr),
            "char_count": len(content),
            "quality_metrics": metrics
        }
    }
    
    logger.debug(
        f"      Created {chunk_type} chunk {chunk_id[:8]}... "
        f"({len(content)} chars)"
    )
    
    return chunk


# ============================================================================
# QUALITY METRICS EXTRACTION
# ============================================================================

def _extract_quality_metrics(
    content: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract quality metrics from content."""
    
    patterns = config['patterns']
    
    # Word and sentence counts
    words = content.split()
    word_count = len(words)
    
    sentences = patterns['sentence'].findall(content)
    sentence_count = len(sentences) if sentences else 1
    
    avg_sentence_length = word_count / max(sentence_count, 1)
    
    # Feature detection
    has_numbers = bool(patterns['number'].search(content))
    has_dates = bool(patterns['date'].search(content))
    has_entities = bool(patterns['entity'].search(content))
    has_exhibits = bool(patterns['exhibit'].search(content))
    
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 1),
        "has_numerical_data": has_numbers,
        "has_dates": has_dates,
        "has_named_entities": has_entities,
        "has_exhibits": has_exhibits
    }


def _extract_image_path(content: str) -> str | None:
    """Extract image path from markdown image syntax."""
    match = re.search(r'\((figures/[^)]+\.png)\)', content)
    return match.group(1) if match else None


def _extract_source_attribution(content: str, config: Dict[str, Any]) -> str | None:
    """Extract source attribution."""
    source_pattern = config['patterns']['source']
    match = source_pattern.search(content)
    return match.group(1).strip() if match else None


def _build_hierarchical_context(breadcrumbs: List[str]) -> Dict[str, Any]:
    """Build hierarchical context dictionary."""
    context = {
        "full_path": " > ".join(breadcrumbs),
        "depth": len(breadcrumbs)
    }
    
    for i, crumb in enumerate(breadcrumbs, 1):
        context[f"level_{i}"] = crumb
    
    return context


# ============================================================================
# CHUNK VALIDATION
# ============================================================================

def validate_chunk(
    chunk: Dict[str, Any],
    config: Dict[str, Any],
    stats: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Validate chunk structure and content.
    
    CHECKS
    ------
    1. Required top-level fields present
    2. Required metadata fields present
    3. Content not empty
    4. Size within reasonable bounds
    
    Parameters
    ----------
    chunk : Dict[str, Any]
        Chunk to validate
    config : Dict[str, Any]
        Configuration
    stats : Dict[str, Any]
        Statistics accumulator
    logger : logging.Logger
        Logger
    
    Returns
    -------
    bool
        True if valid, False otherwise
    """
    
    # Check 1: Top-level fields
    required_fields = ['id', 'text', 'content_only', 'metadata']
    if not all(field in chunk for field in required_fields):
        logger.error(f"Chunk missing required fields: {chunk.get('id', 'unknown')}")
        stats['validation_failures'] += 1
        return False
    
    # Check 2: Metadata fields
    required_metadata = ['source', 'page_number', 'type', 'breadcrumbs']
    if not all(field in chunk['metadata'] for field in required_metadata):
        logger.error(f"Chunk metadata incomplete: {chunk['id']}")
        stats['validation_failures'] += 1
        return False
    
    # Check 3: Content not empty
    if not chunk['content_only'].strip():
        logger.warning(f"Empty chunk content: {chunk['id']}")
        stats['validation_failures'] += 1
        return False
    
    # Check 4: Reasonable size (warning only)
    content_len = len(chunk['content_only'])
    max_size = config['max_size']
    if content_len > max_size * 1.5:
        logger.warning(f"Chunk exceeds max size: {content_len} chars")
    
    return True


# ============================================================================
# DEDUPLICATION
# ============================================================================

def add_chunk_with_dedup(
    chunks: List[Dict[str, Any]],
    new_chunk: Dict[str, Any],
    stats: Dict[str, Any],
    logger: logging.Logger
):
    """
    Add chunk with deduplication check.
    
    Checks last 5 chunks for duplicates (hash-based).
    
    Parameters
    ----------
    chunks : List[Dict[str, Any]]
        Existing chunks
    new_chunk : Dict[str, Any]
        Chunk to add
    stats : Dict[str, Any]
        Statistics accumulator
    logger : logging.Logger
        Logger
    """
    
    new_hash = new_chunk['id']
    
    # Check last 5 chunks
    for existing in chunks[-5:]:
        if existing['id'] == new_hash:
            logger.debug(f"      Duplicate detected: {new_hash[:8]}...")
            stats['duplicates_prevented'] += 1
            return
    
    # No duplicate, add it
    chunks.append(new_chunk)
