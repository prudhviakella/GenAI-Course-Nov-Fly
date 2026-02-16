"""
ray_tasks.py

Ray Remote Tasks for Document Processing Pipeline
Each task represents a stage in the pipeline.

Stage mapping after module updates:
  Stage 1 – PDFExtractionTask    → docling_bounded_extractor.py  (boundary markers)
  Stage 2 – SemanticChunkingTask → comprehensive_chunker.py      (boundary-aware semantic chunking)
  Stage 3 – EnrichmentTask       → enrich_pipeline_openai.py     (OpenAI PII+NER+key-phrases)
  Stage 4 – EmbeddingTask        → openai_embeddings.py          (tenacity retry + cost tracking)
  Stage 5 – VectorLoadingTask    → load_embeddings_to_pinecone.py (auto-dim + namespace + verify)

Author: Prudhvi
Organization: Thoughtworks
"""

import ray
import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict
from datetime import datetime

# ---------------------------------------------------------------------------
# Updated module imports
# ---------------------------------------------------------------------------
# Stage 1 - new functional extractor with HTML boundary markers
from docling_bounded_extractor import process_pdf as bounded_process_pdf
from openai import OpenAI as _OpenAI  # shared client for extraction AI calls

# Stage 2 - boundary-aware semantic chunker
from comprehensive_chunker import (
    chunk_directory,
    create_semantic_chunks,
    format_chunks_for_output,
)

# Stage 3 - OpenAI enrichment (replaces AWS Comprehend)
from enrich_pipeline_openai import enrich_chunk, init_openai_client

# Stage 4 - OpenAI embeddings with tenacity retry + cost tracking
from openai_embeddings import (
    init_openai_client as init_embedding_client,
    load_chunks as load_embedding_chunks,
    generate_embeddings,
    save_results as save_embedding_results,
)

# Stage 5 - Pinecone loader with auto-dim + namespace + verify
from load_embeddings_to_pinecone import (
    init_pinecone,
    load_json as pinecone_load_json,
    create_or_get_index,
    prepare_vectors,
    upsert_vectors,
    verify as pinecone_verify,
)

# Pipeline config and shared utilities
from config import config
from utils import S3Helper, LocalFileManager, format_duration

logger = logging.getLogger(__name__)


# ============================================================================
# STAGE 1 - PDF EXTRACTION
# ============================================================================

@ray.remote(num_cpus=config.EXTRACTION_NUM_CPUS,
            memory=config.EXTRACTION_MEMORY_MB * 1024 * 1024)
class PDFExtractionTask:
    """
    Ray remote task for PDF extraction.

    Uses docling_bounded_extractor.process_pdf() - the new functional-style
    extractor that wraps every element (headers, paragraphs, tables, images)
    in HTML boundary markers.  Output folder: extracted_docs_bounded/<stem>/

    Key changes from the old DoclingHybridSnapV2:
      - Output folder is now  extracted_docs_bounded/  (was extracted_docs_hybrid_v2/)
      - Markdown pages carry <!-- BOUNDARY_START ... --> / <!-- BOUNDARY_END --> tags
        so Stage 2 can extract atomic chunks with a single regex pass
      - Requires an OpenAI client (for GPT-4o image/table descriptions)
    """

    def __init__(self):
        self.s3_helper = S3Helper(bucket=config.S3_BUCKET, region=config.AWS_REGION)
        self.file_manager = LocalFileManager()
        # OpenAI client is needed by the extractor for image/table AI descriptions
        self._openai_client = _OpenAI(api_key=config.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)

    def process(self, document_id: str, s3_bucket: str, s3_key: str) -> Dict:
        """
        Download PDF from S3, run bounded extraction, upload results to S3.

        Output S3 prefix:  extracted/<document_id>/
          pages/page_1.md ... page_N.md   (boundary-marked Markdown)
          figures/fig_p*.png
          metadata.json
        """
        start_time = time.time()
        workspace = self.file_manager.create_document_workspace(document_id)

        local_pdf = workspace / "input.pdf"
        local_output_base = workspace / "extracted_docs_bounded"
        local_output_base.mkdir(parents=True, exist_ok=True)

        try:
            self.logger.info(f"Starting PDF extraction for {document_id}")

            # 1. Download PDF from S3
            if not self.s3_helper.download_file(s3_key, str(local_pdf)):
                raise Exception(
                    f"Failed to download PDF from s3://{s3_bucket}/{s3_key}"
                )

            # 2. Run bounded extraction (functional API)
            self.logger.info("Running bounded Docling extraction...")
            metadata = bounded_process_pdf(
                pdf_path=local_pdf,
                output_base_dir=local_output_base,
                openai_client=self._openai_client,
            )

            # Output lives at:  local_output_base/<pdf_stem>/
            actual_output = local_output_base / local_pdf.stem
            if not actual_output.exists():
                raise Exception("No extraction output directory found")

            # 3. Upload results to S3
            s3_output_prefix = f"{config.S3_EXTRACTED_PREFIX}/{document_id}"
            if not self.s3_helper.upload_directory(str(actual_output), s3_output_prefix):
                raise Exception("Failed to upload extraction results to S3")

            duration = time.time() - start_time
            total_images = sum(p.get("images", 0) for p in metadata.get("pages", []))
            total_tables = sum(p.get("tables", 0) for p in metadata.get("pages", []))

            result = {
                "status": "COMPLETED",
                "output_s3_key": s3_output_prefix,
                "duration_seconds": int(duration),
                "metadata": {
                    "pages_extracted": len(metadata.get("pages", [])),
                    "images_extracted": total_images,
                    "tables_extracted": total_tables,
                },
            }

            self.logger.info(
                f"Extraction completed for {document_id} in {format_duration(duration)}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Extraction failed for {document_id}: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "duration_seconds": int(time.time() - start_time),
            }

        finally:
            self.file_manager.cleanup_document_workspace(document_id)


# ============================================================================
# STAGE 2 - SEMANTIC CHUNKING
# ============================================================================

@ray.remote(num_cpus=config.CHUNKING_NUM_CPUS,
            memory=config.CHUNKING_MEMORY_MB * 1024 * 1024)
class SemanticChunkingTask:
    """
    Ray remote task for semantic chunking.

    Uses comprehensive_chunker - boundary-aware chunker that:
      1. Reads all page_*.md files and extracts atomic chunks via BOUNDARY markers
      2. Groups them into semantic chunks (target 1500 chars, max 3000 chars)
      3. Formats output to the clean {content, metadata} schema expected by Stage 3

    Key changes from the old SemanticChunker:
      - Input is now the pages/ directory (not raw text files)
      - chunk_directory() -> create_semantic_chunks() -> format_chunks_for_output()
      - Output JSON schema uses 'content' field (was 'text')
    """

    def __init__(self):
        self.s3_helper = S3Helper(bucket=config.S3_BUCKET, region=config.AWS_REGION)
        self.file_manager = LocalFileManager()
        self.logger = logging.getLogger(__name__)

    def process(self, document_id: str, extracted_s3_prefix: str) -> Dict:
        """
        Download extracted pages from S3, chunk, upload chunks JSON to S3.

        Output S3 key:  chunks/<document_id>_chunks.json
        """
        start_time = time.time()
        workspace = self.file_manager.create_document_workspace(document_id)

        local_pages_dir = workspace / "pages"
        output_file = workspace / "chunks.json"

        try:
            self.logger.info(f"Starting chunking for {document_id}")

            # 1. Download pages/ directory from S3
            pages_prefix = f"{extracted_s3_prefix}/pages/"
            if not self.s3_helper.download_directory(pages_prefix, str(local_pages_dir)):
                raise Exception(
                    f"Failed to download pages from s3://{config.S3_BUCKET}/{pages_prefix}"
                )

            # 2. Extract atomic chunks from boundary markers
            self.logger.info("Extracting boundary chunks...")
            raw_results = chunk_directory(local_pages_dir)
            atomic_chunks = []
            for file_chunks in raw_results.values():
                atomic_chunks.extend(file_chunks)

            if not atomic_chunks:
                raise Exception("No atomic chunks extracted from pages")

            # 3. Build semantic chunks
            self.logger.info("Running semantic chunking...")
            semantic_chunks = create_semantic_chunks(
                atomic_chunks,
                target_size=config.CHUNK_TARGET_SIZE,
                min_size=config.CHUNK_MIN_SIZE,
                max_size=config.CHUNK_MAX_SIZE,
            )

            # 4. Format to clean output schema  {content, metadata}
            clean_chunks = format_chunks_for_output(semantic_chunks, keep_ids=False)

            # 5. Persist to local file then upload
            output_data = {
                "metadata": {
                    "document_id": document_id,
                    "total_chunks": len(clean_chunks),
                    "chunked_at": datetime.utcnow().isoformat() + "Z",
                    "chunking_config": {
                        "target_size": config.CHUNK_TARGET_SIZE,
                        "min_size": config.CHUNK_MIN_SIZE,
                        "max_size": config.CHUNK_MAX_SIZE,
                    },
                },
                "chunks": clean_chunks,
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            s3_output_key = f"{config.S3_CHUNKS_PREFIX}/{document_id}_chunks.json"
            if not self.s3_helper.upload_file(str(output_file), s3_output_key):
                raise Exception("Failed to upload chunks to S3")

            duration = time.time() - start_time
            result = {
                "status": "COMPLETED",
                "output_s3_key": s3_output_key,
                "duration_seconds": int(duration),
                "metadata": {
                    "total_chunks": len(clean_chunks),
                    "atomic_chunks_extracted": len(atomic_chunks),
                },
            }

            self.logger.info(
                f"Chunking completed for {document_id} in {format_duration(duration)}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Chunking failed for {document_id}: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "duration_seconds": int(time.time() - start_time),
            }

        finally:
            self.file_manager.cleanup_document_workspace(document_id)


# ============================================================================
# STAGE 3 - METADATA ENRICHMENT  (OpenAI replaces AWS Comprehend)
# ============================================================================

@ray.remote(num_cpus=config.ENRICHMENT_NUM_CPUS,
            memory=config.ENRICHMENT_MEMORY_MB * 1024 * 1024)
class EnrichmentTask:
    """
    Ray remote task for chunk enrichment.

    Uses enrich_pipeline_openai - OpenAI-based single-call enrichment that
    performs PII redaction, NER, and key-phrase extraction in one API call
    per chunk.  Local regex handles monetary values at zero cost.

    Key changes from the old ChunkEnrichmentPipeline (AWS Comprehend):
      - No AWS Comprehend dependency - no IAM/region constraints
      - Single gpt-4o-mini call covers PII + NER + key phrases
      - Output gains: content_sanitised, entities, key_phrases, monetary_values
    """

    def __init__(self):
        self._openai_client = init_openai_client(api_key=config.OPENAI_API_KEY)
        self.s3_helper = S3Helper(bucket=config.S3_BUCKET, region=config.AWS_REGION)
        self.file_manager = LocalFileManager()
        self.logger = logging.getLogger(__name__)

    def process(self, document_id: str, chunks_s3_key: str) -> Dict:
        """
        Download chunks JSON, enrich each chunk, upload enriched JSON to S3.

        Output S3 key:  enriched/<document_id>_enriched.json
        """
        start_time = time.time()
        workspace = self.file_manager.create_document_workspace(document_id)

        local_chunks = workspace / "chunks.json"
        local_enriched = workspace / "enriched.json"

        try:
            self.logger.info(f"Starting enrichment for {document_id}")

            # 1. Download chunks from S3
            if not self.s3_helper.download_file(chunks_s3_key, str(local_chunks)):
                raise Exception(
                    f"Failed to download chunks from s3://{config.S3_BUCKET}/{chunks_s3_key}"
                )

            with open(local_chunks, "r", encoding="utf-8") as f:
                data = json.load(f)

            chunks = data.get("chunks", [])
            if not chunks:
                raise Exception("Chunks file is empty or malformed")

            # 2. Enrich each chunk using OpenAI (PII + NER + key phrases + regex)
            self.logger.info(
                f"Enriching {len(chunks)} chunks via OpenAI gpt-4o-mini..."
            )
            enriched_chunks = [
                enrich_chunk(chunk, self._openai_client, model="gpt-4o-mini")
                for chunk in chunks
            ]

            # 3. Persist enriched data
            enriched_data = {
                "metadata": data.get("metadata", {}),
                "chunks": enriched_chunks,
            }
            with open(local_enriched, "w", encoding="utf-8") as f:
                json.dump(enriched_data, f, indent=2, ensure_ascii=False)

            # 4. Upload to S3
            s3_output_key = (
                f"{config.S3_ENRICHED_PREFIX}/{document_id}_enriched.json"
            )
            if not self.s3_helper.upload_file(str(local_enriched), s3_output_key):
                raise Exception("Failed to upload enriched chunks to S3")

            duration = time.time() - start_time
            pii_count = sum(
                1 for c in enriched_chunks
                if c.get("metadata", {}).get("pii_redacted", False)
            )
            result = {
                "status": "COMPLETED",
                "output_s3_key": s3_output_key,
                "duration_seconds": int(duration),
                "metadata": {
                    "chunks_enriched": len(enriched_chunks),
                    "pii_redacted_count": pii_count,
                },
            }

            self.logger.info(
                f"Enrichment completed for {document_id} in {format_duration(duration)}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Enrichment failed for {document_id}: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "duration_seconds": int(time.time() - start_time),
            }

        finally:
            self.file_manager.cleanup_document_workspace(document_id)


# ============================================================================
# STAGE 4 - EMBEDDING GENERATION
# ============================================================================

@ray.remote(num_cpus=config.EMBEDDING_NUM_CPUS,
            memory=config.EMBEDDING_MEMORY_MB * 1024 * 1024)
class EmbeddingTask:
    """
    Ray remote task for OpenAI embedding generation.

    Uses openai_embeddings.generate_embeddings() - updated to include:
      - tenacity exponential-backoff retry (3 attempts, 4s-60s)
      - tqdm progress bar (visible in Ray worker logs)
      - content_sanitised -> content fallback (privacy-first text selection)
      - Accurate cost tracking from API token counts

    Key changes from the old OpenAIEmbedder:
      - generate_embeddings() returns (enriched_chunks, total_tokens)
      - save_results() writes output file and returns its path
      - Cost info is stored under metadata.cost_tracking in the output JSON
    """

    def __init__(self):
        self._client = init_embedding_client()
        self.s3_helper = S3Helper(bucket=config.S3_BUCKET, region=config.AWS_REGION)
        self.file_manager = LocalFileManager()
        self.logger = logging.getLogger(__name__)

    def process(self, document_id: str, enriched_s3_key: str) -> Dict:
        """
        Download enriched chunks, generate embeddings, upload to S3.

        Output S3 key:  embeddings/<document_id>_embeddings.json
        """
        start_time = time.time()
        workspace = self.file_manager.create_document_workspace(document_id)

        local_enriched = workspace / "enriched.json"

        try:
            self.logger.info(f"Starting embedding generation for {document_id}")

            # 1. Download enriched chunks from S3
            if not self.s3_helper.download_file(enriched_s3_key, str(local_enriched)):
                raise Exception(
                    f"Failed to download enriched chunks from "
                    f"s3://{config.S3_BUCKET}/{enriched_s3_key}"
                )

            # 2. Load chunks (openai_embeddings helper)
            chunks = load_embedding_chunks(str(local_enriched))

            # 3. Generate embeddings in batches with retry + cost tracking
            self.logger.info(
                f"Embedding {len(chunks)} chunks | model={config.OPENAI_MODEL}"
            )
            enriched_chunks, total_tokens = generate_embeddings(
                chunks=chunks,
                client=self._client,
                model=config.OPENAI_MODEL,
                dimensions=config.OPENAI_DIMENSIONS,
                batch_size=config.EMBEDDING_BATCH_SIZE,
            )

            # 4. Save to local file (save_results returns the output path)
            output_path = save_embedding_results(
                chunks=enriched_chunks,
                input_file=str(local_enriched),
                model=config.OPENAI_MODEL,
                dimensions=config.OPENAI_DIMENSIONS,
                total_tokens=total_tokens,
            )

            # 5. Upload to S3
            s3_output_key = (
                f"{config.S3_EMBEDDINGS_PREFIX}/{document_id}_embeddings.json"
            )
            if not self.s3_helper.upload_file(output_path, s3_output_key):
                raise Exception("Failed to upload embeddings to S3")

            # 6. Read cost info for pipeline metadata
            with open(output_path, "r") as f:
                saved_data = json.load(f)
            cost_info = saved_data.get("metadata", {}).get("cost_tracking", {})

            duration = time.time() - start_time
            result = {
                "status": "COMPLETED",
                "output_s3_key": s3_output_key,
                "duration_seconds": int(duration),
                "metadata": {
                    "tokens_processed": cost_info.get("total_tokens", total_tokens),
                    "openai_cost_usd": cost_info.get("total_cost_usd", 0.0),
                    "embeddings_generated": len(enriched_chunks),
                },
            }

            self.logger.info(
                f"Embedding completed for {document_id} in {format_duration(duration)}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Embedding failed for {document_id}: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "duration_seconds": int(time.time() - start_time),
            }

        finally:
            self.file_manager.cleanup_document_workspace(document_id)


# ============================================================================
# STAGE 5 - VECTOR LOADING
# ============================================================================

@ray.remote(num_cpus=config.LOADING_NUM_CPUS,
            memory=config.LOADING_MEMORY_MB * 1024 * 1024)
class VectorLoadingTask:
    """
    Ray remote task for loading vectors into Pinecone.

    Uses the updated load_embeddings_to_pinecone module which adds:
      - Auto-dimension detection from first chunk's embedding
      - Namespace support for logical partitioning
      - Idempotent upsert with post-upload verify()
      - Deterministic MD5 chunk IDs if no id field is present
      - Flat metadata serialisation (key_phrases as comma-joined string)

    Key changes from the old PineconeLoader:
      - init_pinecone()   instead of  PineconeLoader(api_key=...)
      - load_json()       handles auto-dim detection
      - prepare_vectors() does flat metadata and ID generation
      - upsert_vectors()  logs progress and rate
      - verify()          confirms count after upsert (async-safe warning)
    """

    def __init__(self):
        self._pc = init_pinecone(api_key=config.PINECONE_API_KEY)
        self.s3_helper = S3Helper(bucket=config.S3_BUCKET, region=config.AWS_REGION)
        self.file_manager = LocalFileManager()
        self.logger = logging.getLogger(__name__)

    def process(self, document_id: str, embeddings_s3_key: str) -> Dict:
        """
        Download embeddings JSON, prepare and upsert vectors into Pinecone.

        Uses config.PINECONE_INDEX as index name and
        config.PINECONE_NAMESPACE as namespace.
        """
        start_time = time.time()
        workspace = self.file_manager.create_document_workspace(document_id)

        local_embeddings = workspace / "embeddings.json"

        try:
            self.logger.info(f"Starting vector loading for {document_id}")

            # 1. Download embeddings from S3
            if not self.s3_helper.download_file(
                embeddings_s3_key, str(local_embeddings)
            ):
                raise Exception(
                    f"Failed to download embeddings from "
                    f"s3://{config.S3_BUCKET}/{embeddings_s3_key}"
                )

            # 2. Load JSON + auto-detect dimensions
            data = pinecone_load_json(str(local_embeddings))

            # 3. Create or reuse Pinecone index
            index = create_or_get_index(
                pc=self._pc,
                index_name=config.PINECONE_INDEX,
                dimensions=data["dimensions"],
                metric=config.PINECONE_METRIC,
                cloud="aws",
                region=config.AWS_REGION,
            )

            # 4. Prepare vectors (flat metadata, ID generation)
            vectors = prepare_vectors(
                data["chunks"], namespace=config.PINECONE_NAMESPACE
            )
            if not vectors:
                raise Exception("No vectors prepared from embeddings file")

            # 5. Upsert
            self.logger.info(
                f"Upserting {len(vectors)} vectors to Pinecone "
                f"index={config.PINECONE_INDEX} "
                f"namespace={config.PINECONE_NAMESPACE}"
            )
            upsert_vectors(
                index=index,
                vectors=vectors,
                namespace=config.PINECONE_NAMESPACE,
                batch_size=config.PINECONE_BATCH_SIZE,
            )

            # 6. Verify (soft warning if counts don't match yet - async stats)
            time.sleep(2)
            pinecone_verify(index, len(vectors), config.PINECONE_NAMESPACE)

            duration = time.time() - start_time
            result = {
                "status": "COMPLETED",
                "duration_seconds": int(duration),
                "metadata": {
                    "vectors_uploaded": len(vectors),
                    "pinecone_index": config.PINECONE_INDEX,
                    "pinecone_namespace": config.PINECONE_NAMESPACE,
                    "dimensions": data["dimensions"],
                },
            }

            self.logger.info(
                f"Vector loading completed for {document_id} in {format_duration(duration)}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Vector loading failed for {document_id}: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "duration_seconds": int(time.time() - start_time),
            }

        finally:
            self.file_manager.cleanup_document_workspace(document_id)
