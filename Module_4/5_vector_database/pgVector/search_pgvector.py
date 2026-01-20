#!/usr/bin/env python3
"""
search_pgvector_with_summary.py

Enhanced search program that uses OpenAI to consolidate and summarize results.
Shows individual chunks + AI-generated summary of what they're saying.

Usage:
    python search_pgvector_with_summary.py [options]

Examples:
    # Interactive mode with summaries
    python search_pgvector_with_summary.py --schema analytics

    # Use specific OpenAI model
    python search_pgvector_with_summary.py --schema analytics --openai-model gpt-4o

Requirements:
    pip install psycopg2-binary sentence-transformers openai

Author: Prudhvi
Date: January 2025
"""

import psycopg2
import argparse
import sys
from sentence_transformers import SentenceTransformer
import time
from openai import OpenAI
import os


class PgVectorSearcherWithSummary:
    """Search embeddings in PostgreSQL with pgvector and summarize with OpenAI."""

    def __init__(self, db_config, model_name='all-MiniLM-L6-v2', openai_model='gpt-4o-mini', openai_api_key=None):
        """
        Initialize searcher.

        Args:
            db_config: Dictionary with database connection parameters
            model_name: Sentence Transformers model name
            openai_model: OpenAI model to use for summarization
            openai_api_key: OpenAI API key (or uses OPENAI_API_KEY env var)
        """
        self.db_config = db_config
        self.model_name = model_name
        self.openai_model = openai_model
        self.conn = None
        self.cursor = None
        self.model = None

        # Initialize OpenAI client
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠ Warning: No OpenAI API key found!")
            print("Set OPENAI_API_KEY environment variable or use --openai-api-key")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=api_key)

    def connect(self):
        """Connect to PostgreSQL database."""
        print(f"\n{'=' * 70}")
        print("CONNECTING TO POSTGRESQL")
        print(f"{'=' * 70}")
        print(f"Host:     {self.db_config['host']}")
        print(f"Port:     {self.db_config['port']}")
        print(f"Database: {self.db_config['database']}")
        print(f"User:     {self.db_config['user']}")

        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print("✓ Connected successfully!")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {str(e)}")
            return False

    def load_model(self):
        """Load the embedding model."""
        print(f"\n{'=' * 70}")
        print("LOADING EMBEDDING MODEL")
        print(f"{'=' * 70}")
        print(f"Model: {self.model_name}")
        print("Loading... (this may take a few seconds on first run)")

        try:
            start_time = time.time()
            self.model = SentenceTransformer(self.model_name)
            elapsed = time.time() - start_time

            print(f"✓ Model loaded in {elapsed:.2f} seconds")

            # Get model dimensions
            test_embedding = self.model.encode("test")
            dimensions = len(test_embedding)
            print(f"✓ Embedding dimensions: {dimensions}")

            return True
        except Exception as e:
            print(f"✗ Failed to load model: {str(e)}")
            return False

    def get_table_info(self, schema, table_name):
        """Get information about the table."""
        try:
            # Check if table exists
            self.cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{schema}' 
                AND table_name = '{table_name}'
            """)

            if self.cursor.fetchone()[0] == 0:
                print(f"✗ Table {schema}.{table_name} does not exist")
                return None

            # Get row count
            self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
            row_count = self.cursor.fetchone()[0]

            # Get dimensions
            self.cursor.execute(f"""
                SELECT vector_dims(embedding) 
                FROM {schema}.{table_name} 
                LIMIT 1
            """)
            dimensions = self.cursor.fetchone()[0]

            # Get indexes
            self.cursor.execute(f"""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = '{schema}' 
                AND tablename = '{table_name}'
                AND indexdef LIKE '%vector%'
            """)
            indexes = [row[0] for row in self.cursor.fetchall()]

            return {
                'row_count': row_count,
                'dimensions': dimensions,
                'indexes': indexes
            }

        except Exception as e:
            print(f"✗ Error getting table info: {str(e)}")
            return None

    def generate_embedding(self, text):
        """Generate embedding for text."""
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"✗ Error generating embedding: {str(e)}")
            return None

    def search(self, query_text, schema, table_name, top_k=5, similarity_threshold=0.0):
        """Search for similar documents."""
        print(f"\n{'=' * 70}")
        print("SEARCHING")
        print(f"{'=' * 70}")
        print(f"Query: {query_text}")
        print(f"Target: {schema}.{table_name}")
        print(f"Top-K: {top_k}")
        print(f"Similarity threshold: {similarity_threshold}")

        try:
            # Generate query embedding
            print("\nGenerating query embedding...")
            start_time = time.time()
            query_embedding = self.generate_embedding(query_text)
            if query_embedding is None:
                return None

            embedding_time = time.time() - start_time
            print(f"✓ Embedding generated in {embedding_time:.3f} seconds")

            # Perform similarity search
            print("Searching database...")
            search_start = time.time()

            # Convert embedding to PostgreSQL array format
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            # Search query using cosine distance
            self.cursor.execute(f"""
                SELECT 
                    id,
                    content_only,
                    metadata,
                    1 - (embedding <=> %s::vector) as similarity
                FROM {schema}.{table_name}
                WHERE 1 - (embedding <=> %s::vector) >= %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (embedding_str, embedding_str, similarity_threshold, embedding_str, top_k))

            results = self.cursor.fetchall()
            search_time = time.time() - search_start

            print(f"✓ Search completed in {search_time:.3f} seconds")
            print(f"✓ Found {len(results)} results")

            return results

        except Exception as e:
            print(f"✗ Search failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def summarize_with_openai(self, query_text, results):
        """
        Use OpenAI to consolidate and summarize search results.

        Args:
            query_text: User's original query
            results: List of result tuples from search

        Returns:
            Dictionary with summary and analysis
        """
        if not self.openai_client:
            print("\n⚠ OpenAI client not initialized. Skipping summary.")
            return None

        print(f"\n{'=' * 70}")
        print("GENERATING AI SUMMARY")
        print(f"{'=' * 70}")
        print(f"Using model: {self.openai_model}")
        print("Processing chunks...")

        try:
            # Prepare chunks for OpenAI
            chunks_text = []
            for i, (doc_id, content, metadata, similarity) in enumerate(results, 1):
                chunk_info = f"""
CHUNK #{i} (Similarity: {similarity:.1%})
Source: {metadata.get('source', 'Unknown') if metadata else 'Unknown'}
Page: {metadata.get('page_number', 'N/A') if metadata else 'N/A'}
Content: {content}
"""
                chunks_text.append(chunk_info)

            all_chunks = "\n---\n".join(chunks_text)

            # Create prompt for OpenAI
            prompt = f"""You are analyzing search results from a vector database. A user searched for: "{query_text}"

Here are the top {len(results)} most relevant chunks found:

{all_chunks}

Please provide:

1. **CONSOLIDATED ANSWER**: A direct, comprehensive answer to the user's query "{query_text}" by synthesizing information from all chunks. Be specific and cite which chunks support your points (e.g., "According to Chunk #1...").

2. **KEY INSIGHTS**: 3-5 main takeaways from these chunks that relate to the query.

3. **CHUNK RELEVANCE**: Brief explanation of what each chunk contributes to answering the query.

Format your response clearly with headers.
"""

            # Call OpenAI
            start_time = time.time()
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system",
                     "content": "You are a helpful AI assistant that synthesizes information from document chunks to provide comprehensive answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            elapsed = time.time() - start_time

            summary = response.choices[0].message.content

            print(f"✓ Summary generated in {elapsed:.2f} seconds")
            print(f"✓ Tokens used: {response.usage.total_tokens}")

            return {
                'summary': summary,
                'tokens_used': response.usage.total_tokens,
                'model': self.openai_model
            }

        except Exception as e:
            print(f"✗ Failed to generate summary: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def display_results_with_summary(self, query_text, results):
        """
        Display search results and AI-generated summary.

        Args:
            query_text: User's original query
            results: List of result tuples from search
        """
        if not results:
            print("\nNo results found.")
            return

        # First, show individual chunks
        print(f"\n{'=' * 70}")
        print(f"INDIVIDUAL CHUNKS ({len(results)} found)")
        print(f"{'=' * 70}\n")

        for i, (doc_id, content, metadata, similarity) in enumerate(results, 1):
            print(f"{'─' * 70}")
            print(f"Chunk #{i}")
            print(f"{'─' * 70}")
            print(f"Similarity: {similarity:.4f} ({similarity * 100:.1f}%)")
            print(f"Document ID: {doc_id}")

            # Show metadata highlights if available
            if metadata:
                if 'source' in metadata:
                    print(f"Source: {metadata['source']}")
                if 'page_number' in metadata:
                    print(f"Page: {metadata['page_number']}")
                if 'key_phrases' in metadata:
                    phrases = metadata['key_phrases'][:5]
                    print(f"Key Phrases: {', '.join(phrases)}")

            print(f"\nContent:")
            # Show first 400 characters
            content_preview = content[:400] + "..." if len(content) > 400 else content
            print(f"{content_preview}")
            print()

        # Then, generate and show AI summary
        summary_data = self.summarize_with_openai(query_text, results)

        if summary_data:
            print(f"\n{'#' * 70}")
            print(f"# AI-GENERATED SUMMARY")
            print(f"{'#' * 70}")
            print(f"Model: {summary_data['model']}")
            print(f"Tokens: {summary_data['tokens_used']}")
            print(f"{'#' * 70}\n")

            print(summary_data['summary'])
            print()

    def interactive_search(self, schema, table_name, top_k=5, similarity_threshold=0.0):
        """Interactive search loop with summaries."""
        print(f"\n{'=' * 70}")
        print("INTERACTIVE SEARCH MODE (WITH AI SUMMARIES)")
        print(f"{'=' * 70}")
        print(f"Target: {schema}.{table_name}")
        print(f"Top-K: {top_k}")
        print(f"Similarity threshold: {similarity_threshold}")
        print(f"OpenAI Model: {self.openai_model}")
        print("\nType your search query and press Enter.")
        print("Type 'quit' or 'exit' to stop.\n")

        while True:
            try:
                # Get user input
                query = input("🔍 Search: ").strip()

                if not query:
                    continue

                if query.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break

                # Perform search
                results = self.search(query, schema, table_name, top_k, similarity_threshold)

                if results:
                    self.display_results_with_summary(query, results)

                print()  # Blank line before next query

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n✗ Error: {str(e)}\n")

    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    """Main function."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Search pgvector embeddings with OpenAI summarization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive search with summaries
  %(prog)s --schema analytics

  # Use GPT-4
  %(prog)s --schema analytics --openai-model gpt-4o

  # Provide OpenAI API key
  %(prog)s --schema analytics --openai-api-key sk-...

  # Or set environment variable
  export OPENAI_API_KEY=sk-...
  %(prog)s --schema analytics
        """
    )

    """
    # 1. Set your OpenAI API key
    export OPENAI_API_KEY=sk-your-key-here
    export HF_TOKEN=your-token-here
    
    # 2. Run the enhanced search
    python search_pgvector_with_summary.py \
      --schema analytics \
      --password Root@12345
    """

    parser.add_argument('--host', default='localhost', help='PostgreSQL host (default: localhost)')
    parser.add_argument('--port', type=int, default=5432, help='PostgreSQL port (default: 5432)')
    parser.add_argument('--database', default='vector_demo', help='Database name (default: vector_demo)')
    parser.add_argument('--user', default='postgres', help='Database user (default: postgres)')
    parser.add_argument('--password', default='postgres', help='Database password (default: postgres)')
    parser.add_argument('--schema', default='public', help='Schema name (default: public)')
    parser.add_argument('--table', default='document_chunks', help='Table name (default: document_chunks)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2',
                        help='Sentence Transformers model (default: all-MiniLM-L6-v2)')
    parser.add_argument('--openai-model', default='gpt-4o-mini',
                        help='OpenAI model for summarization (default: gpt-4o-mini)')
    parser.add_argument('--openai-api-key', help='OpenAI API key (or use OPENAI_API_KEY env var)')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results to return (default: 5)')
    parser.add_argument('--similarity-threshold', type=float, default=0.0,
                        help='Minimum similarity score 0-1 (default: 0.0)')

    args = parser.parse_args()

    # Print header
    print(f"\n{'#' * 70}")
    print(f"# PGVECTOR SEARCH WITH AI SUMMARIES")
    print(f"{'#' * 70}")
    print(f"Database: {args.database}")
    print(f"Schema: {args.schema}")
    print(f"Table: {args.table}")
    print(f"Embedding Model: {args.model}")
    print(f"OpenAI Model: {args.openai_model}")

    # Configure database connection
    db_config = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.user,
        'password': args.password
    }

    # Initialize searcher
    searcher = PgVectorSearcherWithSummary(
        db_config,
        args.model,
        args.openai_model,
        args.openai_api_key
    )

    try:
        # Step 1: Connect to database
        if not searcher.connect():
            sys.exit(1)

        # Step 2: Get table info
        print(f"\n{'=' * 70}")
        print("TABLE INFORMATION")
        print(f"{'=' * 70}")

        table_info = searcher.get_table_info(args.schema, args.table)
        if not table_info:
            print(f"\n✗ Table {args.schema}.{args.table} not found!")
            print(f"\nMake sure you've loaded embeddings first:")
            print(f"  python load_embeddings_to_pgvector.py your_file.json --schema {args.schema} --table {args.table}")
            sys.exit(1)

        print(f"Total documents: {table_info['row_count']}")
        print(f"Vector dimensions: {table_info['dimensions']}")
        print(
            f"Indexes: {', '.join(table_info['indexes']) if table_info['indexes'] else 'None (will use sequential scan)'}")

        # Step 3: Load embedding model
        if not searcher.load_model():
            sys.exit(1)

        # Check model dimensions match table dimensions
        test_embedding = searcher.generate_embedding("test")
        model_dims = len(test_embedding)

        if model_dims != table_info['dimensions']:
            print(
                f"\n⚠ WARNING: Model dimensions ({model_dims}) don't match table dimensions ({table_info['dimensions']})")
            print(f"⚠ Search results may be incorrect!")

            response = input("\nContinue anyway? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                sys.exit(1)

        # Step 4: Start interactive search
        searcher.interactive_search(
            schema=args.schema,
            table_name=args.table,
            top_k=args.top_k,
            similarity_threshold=args.similarity_threshold
        )

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        searcher.close()


if __name__ == "__main__":
    main()