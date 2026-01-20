#!/usr/bin/env python3
"""
search_pinecone.py

Interactive search program for Pinecone vector database.
Converts user queries to embeddings and performs similarity search.
Optionally uses OpenAI to consolidate and summarize results.

Usage:
    python search_pinecone.py [options]

Examples:
    # Interactive mode (basic)
    python search_pinecone.py --index-name financial-docs-384

    # With OpenAI summaries
    python search_pinecone.py --index-name financial-docs-384 --summarize

    # Search in specific namespace
    python search_pinecone.py --index-name my-docs --namespace earnings-reports

Requirements:
    pip install pinecone-client sentence-transformers openai

Author: Prudhvi
Date: January 2025
"""

import argparse
import sys
from sentence_transformers import SentenceTransformer
import time
from pinecone import Pinecone
from openai import OpenAI
import os


class PineconeSearcher:
    """Search embeddings in Pinecone with optional OpenAI summarization."""
    
    def __init__(self, api_key, index_name, model_name='all-MiniLM-L6-v2', 
                 openai_model='gpt-4o-mini', openai_api_key=None, use_openai=False):
        """
        Initialize searcher.
        
        Args:
            api_key: Pinecone API key
            index_name: Name of Pinecone index
            model_name: Sentence Transformers model name
            openai_model: OpenAI model for summarization
            openai_api_key: OpenAI API key
            use_openai: Whether to use OpenAI for summaries
        """
        self.api_key = api_key
        self.index_name = index_name
        self.model_name = model_name
        self.openai_model = openai_model
        self.use_openai = use_openai
        self.pc = None
        self.index = None
        self.model = None
        self.openai_client = None
        
        # Initialize OpenAI if requested
        if use_openai:
            api_key_openai = openai_api_key or os.getenv('OPENAI_API_KEY')
            if not api_key_openai:
                print("⚠ Warning: OpenAI summarization requested but no API key found!")
                print("Set OPENAI_API_KEY environment variable or use --openai-api-key")
                self.use_openai = False
            else:
                self.openai_client = OpenAI(api_key=api_key_openai)
        
    def connect(self):
        """Connect to Pinecone."""
        print(f"\n{'='*70}")
        print("CONNECTING TO PINECONE")
        print(f"{'='*70}")
        print(f"Index: {self.index_name}")
        
        try:
            self.pc = Pinecone(api_key=self.api_key)
            print("✓ Pinecone client initialized")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            print(f"✓ Connected to index '{self.index_name}'")
            
            return True
        except Exception as e:
            print(f"✗ Connection failed: {str(e)}")
            print(f"\nMake sure:")
            print(f"  1. Index '{self.index_name}' exists")
            print(f"  2. API key is correct")
            print(f"\nCheck Pinecone Console: https://app.pinecone.io/")
            return False
    
    def load_model(self):
        """Load the embedding model."""
        print(f"\n{'='*70}")
        print("LOADING EMBEDDING MODEL")
        print(f"{'='*70}")
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
    
    def get_index_info(self):
        """Get information about the index."""
        print(f"\n{'='*70}")
        print("INDEX INFORMATION")
        print(f"{'='*70}")
        
        try:
            # Get index stats
            stats = self.index.describe_index_stats()
            
            print(f"Index: {self.index_name}")
            print(f"Total vectors: {stats['total_vector_count']}")
            print(f"Dimension: {stats['dimension']}")
            
            if 'namespaces' in stats and stats['namespaces']:
                print(f"\nNamespaces:")
                for ns, ns_data in stats['namespaces'].items():
                    count = ns_data.get('vector_count', 0)
                    ns_display = ns if ns else 'default'
                    print(f"  - {ns_display}: {count} vectors")
            else:
                print(f"Namespaces: default only")
            
            return stats
            
        except Exception as e:
            print(f"✗ Error getting index info: {str(e)}")
            return None
    
    def generate_embedding(self, text):
        """Generate embedding for text."""
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"✗ Error generating embedding: {str(e)}")
            return None
    
    def search(self, query_text, namespace=None, top_k=5, filter_dict=None):
        """
        Search for similar documents.
        
        Args:
            query_text: User's search query
            namespace: Namespace to search in
            top_k: Number of results to return
            filter_dict: Metadata filters
            
        Returns:
            List of results or None
        """
        print(f"\n{'='*70}")
        print("SEARCHING")
        print(f"{'='*70}")
        print(f"Query: {query_text}")
        if namespace:
            print(f"Namespace: {namespace}")
        print(f"Top-K: {top_k}")
        if filter_dict:
            print(f"Filters: {filter_dict}")
        
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
            print("Searching Pinecone...")
            search_start = time.time()
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=namespace or "",
                filter=filter_dict,
                include_metadata=True
            )
            
            search_time = time.time() - search_start
            
            matches = results.get('matches', [])
            
            print(f"✓ Search completed in {search_time:.3f} seconds")
            print(f"✓ Found {len(matches)} results")
            
            return matches
            
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
            results: List of result matches from Pinecone
            
        Returns:
            Dictionary with summary and analysis
        """
        if not self.openai_client:
            return None
        
        print(f"\n{'='*70}")
        print("GENERATING AI SUMMARY")
        print(f"{'='*70}")
        print(f"Using model: {self.openai_model}")
        print("Processing chunks...")
        
        try:
            # Prepare chunks for OpenAI
            chunks_text = []
            for i, match in enumerate(results, 1):
                metadata = match.get('metadata', {})
                score = match.get('score', 0)
                
                text = metadata.get('text', 'No text available')
                source = metadata.get('source', 'Unknown')
                page = metadata.get('page', 'N/A')
                
                chunk_info = f"""
CHUNK #{i} (Similarity: {score:.1%})
Source: {source}
Page: {page}
Content: {text}
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
                    {"role": "system", "content": "You are a helpful AI assistant that synthesizes information from document chunks to provide comprehensive answers."},
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
    
    def display_results(self, query_text, results):
        """
        Display search results.
        
        Args:
            query_text: User's original query
            results: List of result matches from Pinecone
        """
        if not results:
            print("\nNo results found.")
            return
        
        # Show individual chunks
        print(f"\n{'='*70}")
        print(f"SEARCH RESULTS ({len(results)} found)")
        print(f"{'='*70}\n")
        
        for i, match in enumerate(results, 1):
            metadata = match.get('metadata', {})
            score = match.get('score', 0)
            doc_id = match.get('id', 'unknown')
            
            print(f"{'─'*70}")
            print(f"Result #{i}")
            print(f"{'─'*70}")
            print(f"Score: {score:.4f} ({score*100:.1f}%)")
            print(f"ID: {doc_id}")
            
            # Show metadata
            if 'source' in metadata:
                print(f"Source: {metadata['source']}")
            if 'page' in metadata:
                print(f"Page: {metadata['page']}")
            if 'key_phrases' in metadata:
                print(f"Key Phrases: {metadata['key_phrases'][:100]}")
            
            # Show text content
            if 'text' in metadata:
                text = metadata['text']
                # Show first 400 characters
                content_preview = text[:400] + "..." if len(text) > 400 else text
                print(f"\nContent:")
                print(f"{content_preview}")
            
            print()
        
        # Generate AI summary if enabled
        if self.use_openai:
            summary_data = self.summarize_with_openai(query_text, results)
            
            if summary_data:
                print(f"\n{'#'*70}")
                print(f"# AI-GENERATED SUMMARY")
                print(f"{'#'*70}")
                print(f"Model: {summary_data['model']}")
                print(f"Tokens: {summary_data['tokens_used']}")
                print(f"{'#'*70}\n")
                
                print(summary_data['summary'])
                print()
    
    def interactive_search(self, namespace=None, top_k=5, filter_dict=None):
        """
        Interactive search loop.
        
        Args:
            namespace: Namespace to search in
            top_k: Number of results to return
            filter_dict: Metadata filters
        """
        print(f"\n{'='*70}")
        if self.use_openai:
            print("INTERACTIVE SEARCH MODE (WITH AI SUMMARIES)")
        else:
            print("INTERACTIVE SEARCH MODE")
        print(f"{'='*70}")
        print(f"Index: {self.index_name}")
        if namespace:
            print(f"Namespace: {namespace}")
        print(f"Top-K: {top_k}")
        if filter_dict:
            print(f"Filters: {filter_dict}")
        if self.use_openai:
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
                results = self.search(query, namespace, top_k, filter_dict)
                
                if results:
                    self.display_results(query, results)
                
                print()  # Blank line before next query
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n✗ Error: {str(e)}\n")


def main():
    """Main function."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Search Pinecone vector database interactively',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic interactive search
  %(prog)s --index-name my-docs
  
  # With AI summaries
  %(prog)s --index-name my-docs --summarize
  
  # Search in specific namespace
  %(prog)s --index-name my-docs --namespace earnings-reports
  
  # Return more results
  %(prog)s --index-name my-docs --top-k 10
  
  # Use different embedding model
  %(prog)s --index-name my-docs --model all-mpnet-base-v2
  
  # Provide API keys
  %(prog)s --index-name my-docs --api-key pc-xxx --openai-api-key sk-xxx
        """
    )
    
    parser.add_argument('--index-name', required=True, help='Pinecone index name (required)')
    parser.add_argument('--api-key', help='Pinecone API key (or use PINECONE_API_KEY env var)')
    parser.add_argument('--namespace', help='Namespace to search in (optional)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2', 
                        help='Sentence Transformers model (default: all-MiniLM-L6-v2)')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results to return (default: 5)')
    parser.add_argument('--summarize', action='store_true', help='Use OpenAI to generate summaries')
    parser.add_argument('--openai-model', default='gpt-4o-mini', 
                        help='OpenAI model for summarization (default: gpt-4o-mini)')
    parser.add_argument('--openai-api-key', help='OpenAI API key (or use OPENAI_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Get Pinecone API key
    api_key = args.api_key or os.getenv('PINECONE_API_KEY')
    if not api_key:
        print("Error: Pinecone API key required!")
        print("Either:")
        print("  1. Set PINECONE_API_KEY environment variable")
        print("  2. Use --api-key parameter")
        print("\nGet your API key from: https://app.pinecone.io/")
        sys.exit(1)
    
    # Print header
    print(f"\n{'#'*70}")
    print(f"# PINECONE INTERACTIVE SEARCH")
    print(f"{'#'*70}")
    print(f"Index: {args.index_name}")
    if args.namespace:
        print(f"Namespace: {args.namespace}")
    print(f"Embedding Model: {args.model}")
    if args.summarize:
        print(f"OpenAI Summaries: Enabled ({args.openai_model})")
    else:
        print(f"OpenAI Summaries: Disabled")
    
    # Initialize searcher
    searcher = PineconeSearcher(
        api_key=api_key,
        index_name=args.index_name,
        model_name=args.model,
        openai_model=args.openai_model,
        openai_api_key=args.openai_api_key,
        use_openai=args.summarize
    )
    
    try:
        # Step 1: Connect to Pinecone
        if not searcher.connect():
            sys.exit(1)
        
        # Step 2: Get index info
        stats = searcher.get_index_info()
        if not stats:
            sys.exit(1)
        
        # Validate namespace if specified
        if args.namespace:
            namespaces = stats.get('namespaces', {})
            if args.namespace not in namespaces:
                print(f"\n⚠ Warning: Namespace '{args.namespace}' not found in index")
                print(f"Available namespaces: {list(namespaces.keys())}")
                response = input("\nContinue anyway? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    sys.exit(1)
        
        # Step 3: Load embedding model
        if not searcher.load_model():
            sys.exit(1)
        
        # Check model dimensions match index dimensions
        test_embedding = searcher.generate_embedding("test")
        model_dims = len(test_embedding)
        index_dims = stats['dimension']
        
        if model_dims != index_dims:
            print(f"\n⚠ WARNING: Model dimensions ({model_dims}) don't match index dimensions ({index_dims})")
            print(f"⚠ Search results will be incorrect!")
            print(f"\nTo fix this:")
            print(f"  1. Use correct model for your index dimensions")
            print(f"  2. Or reload embeddings with current model")
            
            response = input("\nContinue anyway? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                sys.exit(1)
        
        # Step 4: Start interactive search
        searcher.interactive_search(
            namespace=args.namespace,
            top_k=args.top_k
        )
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
