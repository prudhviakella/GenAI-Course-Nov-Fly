#!/usr/bin/env python3
"""
load_embeddings_to_pgvector.py

Loads embeddings from JSON file into PostgreSQL with pgvector extension.
Automatically detects embedding dimensions and creates appropriate table.

Usage:
    python load_embeddings_to_pgvector.py <embedding_file.json> [options]

Examples:
    # Load Sentence Transformers embeddings (384D) - auto-detect dimensions
    python load_embeddings_to_pgvector.py large_chunks_sentence_transformers_embeddings.json

    # Load OpenAI embeddings (1536D) - specify dimensions explicitly
    python load_embeddings_to_pgvector.py large_chunks_openai_embeddings.json --dimensions 1536

    # Load Bedrock Titan embeddings (1024D) with custom schema
    python load_embeddings_to_pgvector.py large_chunks_bedrock_titan_embeddings.json \
        --dimensions 1024 --schema analytics --table embeddings

    # Use custom database and schema
    python load_embeddings_to_pgvector.py file.json \
        --database custom_db --schema my_schema --table my_table --dimensions 384

    # Use HNSW index (default)
    python load_embeddings_to_pgvector.py file.json --index-type hnsw

    # Use IVF index with custom schema
    python load_embeddings_to_pgvector.py file.json \
        --index-type ivf --ivf-lists 100 --dimensions 1536 --schema production

Requirements:
    pip install psycopg2-binary

Author: Prudhvi
Date: January 2025
"""

import json
import psycopg2
from psycopg2.extras import execute_values
import sys
import argparse
from pathlib import Path
import time
from datetime import datetime


class PgVectorLoader:
    """Load embeddings into PostgreSQL with pgvector."""

    def __init__(self, db_config):
        """
        Initialize loader.

        Args:
            db_config: Dictionary with database connection parameters
                      {host, port, database, user, password}
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None

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
            self.conn.autocommit = False
            self.cursor = self.conn.cursor()
            print("✓ Connected successfully!")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {str(e)}")
            return False

    def enable_pgvector(self):
        """Enable pgvector extension."""
        print(f"\n{'=' * 70}")
        print("ENABLING PGVECTOR EXTENSION")
        print(f"{'=' * 70}")

        try:
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            self.conn.commit()
            print("✓ pgvector extension enabled")

            # Verify it works
            self.cursor.execute("SELECT '[1,2,3]'::vector")
            result = self.cursor.fetchone()
            print(f"✓ Test vector created: {result[0]}")
            return True
        except Exception as e:
            print(f"✗ Failed to enable pgvector: {str(e)}")
            self.conn.rollback()
            return False

    def load_json_file(self, json_file, override_dimensions=None):
        """
        Load and validate JSON file.

        Args:
            json_file: Path to JSON file with embeddings
            override_dimensions: Optional dimensions override (if provided, skip validation)

        Returns:
            Dictionary with chunks and metadata, or None if failed
        """
        print(f"\n{'=' * 70}")
        print("LOADING JSON FILE")
        print(f"{'=' * 70}")
        print(f"File: {json_file}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate structure
            if 'chunks' not in data:
                print("✗ Error: JSON file must have 'chunks' key")
                return None

            chunks = data['chunks']

            if len(chunks) == 0:
                print("✗ Error: No chunks found in JSON file")
                return None

            # Check for embedding field
            first_chunk = chunks[0]
            if 'embedding' not in first_chunk:
                print("✗ Error: Chunks must have 'embedding' field")
                return None

            # Determine dimensions
            if override_dimensions:
                dimensions = override_dimensions
                print(f"✓ Using specified dimensions: {dimensions}")
                print(f"✓ Loaded {len(chunks)} chunks")

                # Validate against actual embeddings
                detected_dims = len(first_chunk['embedding'])
                if detected_dims != dimensions:
                    print(f"⚠ Warning: Specified dimensions ({dimensions}) != detected dimensions ({detected_dims})")
                    print(f"⚠ Using specified dimensions: {dimensions}")
            else:
                # Auto-detect dimensions
                dimensions = len(first_chunk['embedding'])
                print(f"✓ Loaded {len(chunks)} chunks")
                print(f"✓ Auto-detected {dimensions} dimensions")

            # Validate all chunks have same dimensions (if not overridden)
            if not override_dimensions:
                for i, chunk in enumerate(chunks):
                    if len(chunk['embedding']) != dimensions:
                        print(f"✗ Error: Chunk {i} has {len(chunk['embedding'])} dimensions, expected {dimensions}")
                        return None
                print("✓ All chunks validated")
            else:
                print("✓ Skipping dimension validation (using override)")

            return {
                'chunks': chunks,
                'dimensions': dimensions,
                'metadata': data.get('metadata', {})
            }

        except FileNotFoundError:
            print(f"✗ Error: File not found: {json_file}")
            return None
        except json.JSONDecodeError as e:
            print(f"✗ Error: Invalid JSON: {str(e)}")
            return None
        except Exception as e:
            print(f"✗ Error loading file: {str(e)}")
            return None

    def create_table(self, dimensions, schema='public', table_name='document_chunks'):
        """
        Create table for storing embeddings.

        Args:
            dimensions: Number of dimensions in embeddings
            schema: Schema name (default: public)
            table_name: Name of table to create
        """
        print(f"\n{'=' * 70}")
        print("CREATING TABLE")
        print(f"{'=' * 70}")
        print(f"Schema: {schema}")
        print(f"Table name: {table_name}")
        print(f"Full path: {schema}.{table_name}")
        print(f"Dimensions: {dimensions}")

        try:
            # Create schema if it doesn't exist
            self.cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            print(f"✓ Schema '{schema}' ready")

            # Drop existing table
            self.cursor.execute(f"DROP TABLE IF EXISTS {schema}.{table_name} CASCADE")
            print(f"✓ Dropped existing table (if any)")

            # Create new table
            create_sql = f"""
                CREATE TABLE {schema}.{table_name} (
                    id TEXT PRIMARY KEY,
                    content_only TEXT NOT NULL,
                    full_text TEXT,
                    metadata JSONB,
                    embedding vector({dimensions}),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """

            self.cursor.execute(create_sql)
            self.conn.commit()

            print(f"✓ Created table {schema}.{table_name} with vector({dimensions})")
            print("\nTable structure:")
            print("  - id (TEXT PRIMARY KEY)")
            print("  - content_only (TEXT NOT NULL)")
            print("  - full_text (TEXT)")
            print("  - metadata (JSONB)")
            print(f"  - embedding (vector({dimensions}))")
            print("  - created_at (TIMESTAMP)")

            return True

        except Exception as e:
            print(f"✗ Failed to create table: {str(e)}")
            self.conn.rollback()
            return False

    def insert_chunks(self, chunks, schema='public', table_name='document_chunks', batch_size=100):
        """
        Insert chunks into database.

        Args:
            chunks: List of chunk dictionaries
            schema: Schema name
            table_name: Name of table to insert into
            batch_size: Number of rows to insert per batch
        """
        print(f"\n{'=' * 70}")
        print("INSERTING DATA")
        print(f"{'=' * 70}")
        print(f"Target: {schema}.{table_name}")
        print(f"Total chunks: {len(chunks)}")
        print(f"Batch size:   {batch_size}")

        try:
            # Prepare data
            rows = []
            for chunk in chunks:
                row = (
                    chunk.get('id', chunk.get('chunk_id', '')),
                    chunk.get('content_only', ''),
                    chunk.get('text', chunk.get('full_text', '')),
                    json.dumps(chunk.get('metadata', {})),
                    chunk['embedding']
                )
                rows.append(row)

            print(f"✓ Prepared {len(rows)} rows")

            # Insert in batches
            total_inserted = 0
            start_time = time.time()

            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]

                execute_values(
                    self.cursor,
                    f"""
                    INSERT INTO {schema}.{table_name} 
                    (id, content_only, full_text, metadata, embedding)
                    VALUES %s
                    """,
                    batch
                )

                total_inserted += len(batch)
                elapsed = time.time() - start_time
                rate = total_inserted / elapsed if elapsed > 0 else 0

                print(f"  Inserted {total_inserted}/{len(rows)} rows ({rate:.1f} rows/sec)")

            self.conn.commit()

            total_time = time.time() - start_time
            print(f"\n✓ All data inserted successfully!")
            print(f"  Total time: {total_time:.2f} seconds")
            print(f"  Average rate: {len(rows) / total_time:.1f} rows/second")

            return True

        except Exception as e:
            print(f"\n✗ Failed to insert data: {str(e)}")
            self.conn.rollback()
            return False

    def create_index(self, index_type='hnsw', schema='public', table_name='document_chunks',
                     hnsw_m=16, hnsw_ef_construction=64, ivf_lists=100):
        """
        Create index for fast similarity search.

        Args:
            index_type: 'hnsw' or 'ivf'
            schema: Schema name
            table_name: Name of table
            hnsw_m: HNSW parameter (connections per layer)
            hnsw_ef_construction: HNSW build quality parameter
            ivf_lists: IVF number of clusters
        """
        print(f"\n{'=' * 70}")
        print("CREATING INDEX")
        print(f"{'=' * 70}")
        print(f"Target: {schema}.{table_name}")
        print(f"Index type: {index_type.upper()}")

        try:
            start_time = time.time()

            if index_type.lower() == 'hnsw':
                print(f"Parameters:")
                print(f"  m = {hnsw_m} (connections per layer)")
                print(f"  ef_construction = {hnsw_ef_construction} (build quality)")
                print("\nBuilding HNSW index (this may take 1-2 minutes)...")

                self.cursor.execute(f"""
                    CREATE INDEX ON {schema}.{table_name} 
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = {hnsw_m}, ef_construction = {hnsw_ef_construction})
                """)

            elif index_type.lower() == 'ivf':
                print(f"Parameters:")
                print(f"  lists = {ivf_lists} (number of clusters)")
                print("\nBuilding IVF index (this may take 30-60 seconds)...")

                self.cursor.execute(f"""
                    CREATE INDEX ON {schema}.{table_name} 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = {ivf_lists})
                """)
            else:
                print(f"✗ Unknown index type: {index_type}")
                return False

            self.conn.commit()

            elapsed = time.time() - start_time
            print(f"✓ Index created successfully in {elapsed:.2f} seconds!")

            return True

        except Exception as e:
            print(f"✗ Failed to create index: {str(e)}")
            self.conn.rollback()
            return False

    def verify_data(self, schema='public', table_name='document_chunks'):
        """
        Verify data was loaded correctly.

        Args:
            schema: Schema name
            table_name: Name of table to verify
        """
        print(f"\n{'=' * 70}")
        print("VERIFYING DATA")
        print(f"{'=' * 70}")
        print(f"Target: {schema}.{table_name}")

        try:
            # Count rows
            self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
            count = self.cursor.fetchone()[0]
            print(f"Total rows: {count}")

            # Check embedding dimensions using vector_dims()
            self.cursor.execute(f"""
                SELECT vector_dims(embedding) as dims, COUNT(*) 
                FROM {schema}.{table_name} 
                GROUP BY dims
            """)
            dims_result = self.cursor.fetchall()
            print(f"\nEmbedding dimensions:")
            for dims, cnt in dims_result:
                print(f"  {dims}D: {cnt} rows")

            # Show sample row
            self.cursor.execute(f"""
                SELECT id, LEFT(content_only, 100) as preview, metadata
                FROM {schema}.{table_name}
                LIMIT 1
            """)
            sample = self.cursor.fetchone()
            if sample:
                print(f"\nSample row:")
                print(f"  ID: {sample[0]}")
                print(f"  Content: {sample[1]}...")
                print(f"  Metadata keys: {list(sample[2].keys()) if sample[2] else 'None'}")

            # List indexes
            self.cursor.execute(f"""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE schemaname = '{schema}' AND tablename = '{table_name}'
            """)
            indexes = self.cursor.fetchall()
            print(f"\nIndexes on {schema}.{table_name}:")
            if indexes:
                for idx_name, idx_def in indexes:
                    print(f"  - {idx_name}")
            else:
                print(f"  - No indexes (use --index-type to create)")

            print(f"\n✓ Verification complete!")
            return True

        except Exception as e:
            print(f"✗ Verification failed: {str(e)}")
            return False

    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print(f"\n✓ Database connection closed")


def main():
    """Main function."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Load embeddings into PostgreSQL with pgvector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s large_chunks_openai_embeddings.json
  %(prog)s file.json --dimensions 1536
  %(prog)s file.json --database vector_db --schema analytics --dimensions 384
  %(prog)s file.json --schema production --table embeddings --dimensions 1024
  %(prog)s file.json --index-type ivf --ivf-lists 100 --schema public --dimensions 1536
  %(prog)s file.json --host localhost --port 5432 --schema my_schema --dimensions 1536
        """
    )
    """
    
    """
    parser.add_argument('json_file', help='Path to JSON file with embeddings')
    parser.add_argument('--dimensions', type=int, help='Vector dimensions (auto-detected if not specified)')
    parser.add_argument('--host', default='localhost', help='PostgreSQL host (default: localhost)')
    parser.add_argument('--port', type=int, default=5432, help='PostgreSQL port (default: 5432)')
    parser.add_argument('--database', default='vector_demo', help='Database name (default: vector_demo)')
    parser.add_argument('--user', default='postgres', help='Database user (default: postgres)')
    parser.add_argument('--password', default='postgres', help='Database password (default: postgres)')
    parser.add_argument('--schema', default='public', help='Schema name (default: public)')
    parser.add_argument('--table', default='document_chunks', help='Table name (default: document_chunks)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for inserts (default: 100)')
    parser.add_argument('--index-type', choices=['hnsw', 'ivf'], default='hnsw',
                        help='Index type: hnsw or ivf (default: hnsw)')
    parser.add_argument('--hnsw-m', type=int, default=16, help='HNSW m parameter (default: 16)')
    parser.add_argument('--hnsw-ef-construction', type=int, default=64,
                        help='HNSW ef_construction parameter (default: 64)')
    parser.add_argument('--ivf-lists', type=int, default=100, help='IVF lists parameter (default: 100)')
    parser.add_argument('--no-index', action='store_true', help='Skip index creation')

    args = parser.parse_args()

    # Validate file exists
    if not Path(args.json_file).exists():
        print(f"Error: File not found: {args.json_file}")
        sys.exit(1)

    # Print header
    print(f"\n{'#' * 70}")
    print(f"# LOAD EMBEDDINGS TO PGVECTOR")
    print(f"{'#' * 70}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Input file: {args.json_file}")
    print(f"Database: {args.database}")
    print(f"Schema: {args.schema}")
    print(f"Table: {args.table}")
    print(f"Full path: {args.schema}.{args.table}")
    print(f"Index type: {args.index_type}")

    # Configure database connection
    db_config = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.user,
        'password': args.password
    }

    # Initialize loader
    loader = PgVectorLoader(db_config)

    try:
        # Step 1: Connect to database
        if not loader.connect():
            sys.exit(1)

        # Step 2: Enable pgvector
        if not loader.enable_pgvector():
            sys.exit(1)

        # Step 3: Load JSON file
        data = loader.load_json_file(args.json_file, args.dimensions)
        if not data:
            sys.exit(1)

        # Step 4: Create table
        if not loader.create_table(data['dimensions'], args.schema, args.table):
            sys.exit(1)

        # Step 5: Insert data
        if not loader.insert_chunks(data['chunks'], args.schema, args.table, args.batch_size):
            sys.exit(1)

        # Step 6: Create index (unless --no-index)
        if not args.no_index:
            if not loader.create_index(
                    index_type=args.index_type,
                    schema=args.schema,
                    table_name=args.table,
                    hnsw_m=args.hnsw_m,
                    hnsw_ef_construction=args.hnsw_ef_construction,
                    ivf_lists=args.ivf_lists
            ):
                sys.exit(1)
        else:
            print(f"\n⚠ Skipping index creation (--no-index specified)")

        # Step 7: Verify
        if not loader.verify_data(args.schema, args.table):
            sys.exit(1)

        # Success!
        print(f"\n{'#' * 70}")
        print(f"# SUCCESS!")
        print(f"{'#' * 70}")
        print(f"✓ Loaded {len(data['chunks'])} chunks into PostgreSQL")
        print(f"✓ Database: {args.database}")
        print(f"✓ Schema: {args.schema}")
        print(f"✓ Table: {args.table}")
        print(f"✓ Full path: {args.schema}.{args.table}")
        print(f"✓ Dimensions: {data['dimensions']}")
        print(f"✓ Index: {args.index_type.upper()}")
        print(f"\nYou can now search your embeddings!")
        print(f"Example SQL:")
        print(f"  SELECT content_only, 1 - (embedding <=> '[...]'::vector) as similarity")
        print(f"  FROM {args.schema}.{args.table}")
        print(f"  ORDER BY embedding <=> '[...]'::vector")
        print(f"  LIMIT 5;")
        print(f"{'#' * 70}\n")

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        loader.close()


if __name__ == "__main__":
    main()