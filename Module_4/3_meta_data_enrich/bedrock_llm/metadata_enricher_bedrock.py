"""
================================================================================
METADATA ENRICHER - AWS BEDROCK (CLAUDE) VERSION
================================================================================

This module enriches semantic chunks with metadata using:
1. AWS Bedrock (Claude) - LLM-based entity extraction
2. AWS Bedrock (Claude) - Key phrase and metadata extraction
3. Custom Regex Patterns - Financial & Temporal Data (FREE)

BEDROCK vs COMPREHEND:
──────────────────────

AWS Comprehend (metadata_enricher.py):
    Pros: Fast, cheap, reliable
    Cost: ~$0.001 per chunk
    Quality: Good (90-95% accuracy)
    Customization: Limited to 9 entity types
    
AWS Bedrock (this file):
    Pros: Flexible, customizable, deeper understanding
    Cost: ~$0.003 per chunk (3x more expensive)
    Quality: Excellent (95-99% accuracy)
    Customization: Extract ANY metadata you define
    Best for: Domain-specific metadata, complex extraction

WHEN TO USE BEDROCK:
────────────────────
✓ Need custom entity types (not in Comprehend's 9 types)
✓ Need semantic understanding (e.g., sentiment, intent, relationships)
✓ Need structured data extraction (e.g., tables, key-value pairs)
✓ Quality > cost
✓ Complex financial analysis

WHEN TO USE COMPREHEND:
───────────────────────
✓ Standard entity types sufficient
✓ Cost is critical
✓ High volume (millions of chunks)
✓ Speed > customization

COST COMPARISON (500-char chunk):
─────────────────────────────────
Comprehend: $0.001
Bedrock:    $0.003
Custom patterns: FREE

For 10,000 chunks:
Comprehend: $10
Bedrock:    $30

Author: Prudhvi
Created: 2025-01-05
Version: 1.0.0
"""

import boto3
import re
import json
import logging
from typing import Dict, List, Optional
from botocore.exceptions import ClientError
import time
from functools import wraps


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# ============================================================================
# RETRY DECORATOR FOR AWS API CALLS
# ============================================================================

def retry_on_throttle(max_retries=3, base_delay=1.0):
    """
    Decorator to retry AWS Bedrock calls on throttling.
    
    Bedrock rate limits vary by model and account.
    Default Claude 3.5 Sonnet: 40 requests/minute
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    
                    if error_code in ['ThrottlingException', 'TooManyRequestsException'] \
                       and attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logging.warning(
                            f"Throttled by AWS Bedrock. Retrying in {delay}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        raise
            return None
        return wrapper
    return decorator


# ============================================================================
# BEDROCK METADATA ENRICHER CLASS
# ============================================================================

class BedrockMetadataEnricher:
    """
    Enriches semantic chunks with metadata using AWS Bedrock (Claude).
    
    Features
    --------
    1. LLM-Based Entity Extraction
       - Organizations, people, locations, dates, quantities
       - Custom entities: metrics, trends, risks, opportunities
       
    2. Semantic Analysis
       - Key phrases with context
       - Sentiment analysis
       - Topic classification
       - Relationship extraction
       
    3. Custom Pattern Extraction
       - Financial amounts, percentages, quarters
       - Same as Comprehend version (FREE)
    
    Claude Model Options
    --------------------
    - claude-3-5-sonnet-20241022: Best quality, most expensive
    - claude-3-haiku-20240307: Fast, cheap, good for simple tasks
    - claude-3-opus-20240229: Highest quality, very expensive
    
    Cost Estimation
    ---------------
    Claude 3.5 Sonnet pricing:
    - Input: $3 per 1M tokens (~750K words)
    - Output: $15 per 1M tokens
    
    For 500-char chunk:
    - Input: ~125 tokens
    - Output: ~200 tokens (JSON metadata)
    - Cost: ~$0.003 per chunk
    
    For 10,000 chunks: ~$30
    
    Usage
    -----
    ```python
    enricher = BedrockMetadataEnricher(
        region='us-east-1',
        model_id='anthropic.claude-3-5-sonnet-20241022-v1:0'
    )
    
    enriched = enricher.enrich_chunk(chunk)
    ```
    """
    
    def __init__(
        self,
        region_name: str = 'us-east-1',
        model_id: str = 'anthropic.claude-3-5-sonnet-20241022-v1:0',
        enable_bedrock: bool = True,
        enable_patterns: bool = True,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Bedrock MetadataEnricher.
        
        Parameters
        ----------
        region_name : str
            AWS region for Bedrock service
            
        model_id : str
            Bedrock model ID
            Options:
            - 'anthropic.claude-3-5-sonnet-20241022-v1:0' (recommended)
            - 'anthropic.claude-3-haiku-20240307-v1:0' (cheaper)
            - 'anthropic.claude-3-opus-20240229-v1:0' (best quality)
            
        enable_bedrock : bool
            Whether to use AWS Bedrock
            Set to False for testing with patterns only
            
        enable_patterns : bool
            Whether to use custom regex patterns
            
        temperature : float
            Model temperature (0.0 = deterministic, 1.0 = creative)
            Recommended: 0.0 for metadata extraction
            
        max_tokens : int
            Maximum tokens in model response
            1000 sufficient for metadata
            
        logger : logging.Logger
            Custom logger instance
        """
        self.region_name = region_name
        self.model_id = model_id
        self.enable_bedrock = enable_bedrock
        self.enable_patterns = enable_patterns
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize AWS Bedrock client
        if self.enable_bedrock:
            try:
                self.bedrock = boto3.client(
                    'bedrock-runtime',
                    region_name=self.region_name
                )
                self.logger.info(f"AWS Bedrock client initialized (region: {region_name})")
                self.logger.info(f"Using model: {model_id}")
            except Exception as e:
                self.logger.error(f"Failed to initialize Bedrock client: {e}")
                self.enable_bedrock = False
        
        # Compile regex patterns (same as Comprehend version)
        self._compile_patterns()
        
        # Statistics tracking
        self.stats = {
            'chunks_processed': 0,
            'bedrock_calls': 0,
            'bedrock_errors': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'entities_extracted': 0,
            'key_phrases_extracted': 0,
            'patterns_matched': 0
        }
    
    def _compile_patterns(self):
        """Compile regex patterns (same as Comprehend version)."""
        # Financial amounts
        self.money_pattern = re.compile(
            r'\$\d+(?:\.\d+)?(?:[BMK]|(?:\s?(?:billion|million|thousand)))?',
            re.IGNORECASE
        )
        
        # Percentages
        self.percent_pattern = re.compile(r'\d+(?:\.\d+)?%')
        
        # Quarters
        self.quarter_pattern = re.compile(r'Q[1-4]\s*\d{4}')
        
        # Fiscal years
        self.fiscal_year_pattern = re.compile(
            r'(?:FY|Fiscal Year)\s*\d{4}',
            re.IGNORECASE
        )
        
        # Years
        self.year_pattern = re.compile(r'\b(?:19|20)\d{2}\b')
        
        # Financial metrics
        self.financial_metrics = {
            'revenue', 'profit', 'loss', 'earnings', 'ebitda', 'ebit',
            'margin', 'growth', 'decline', 'cash flow', 'operating income',
            'net income', 'gross profit', 'roi', 'roa', 'roe', 'eps',
            'dividend', 'yield', 'valuation', 'market cap', 'enterprise value',
            'debt', 'equity', 'assets', 'liabilities', 'capex', 'opex'
        }
        
        metrics_str = '|'.join(self.financial_metrics)
        self.metrics_pattern = re.compile(
            rf'\b(?:{metrics_str})\b',
            re.IGNORECASE
        )
    
    def _build_extraction_prompt(self, text: str) -> str:
        """
        Build prompt for Claude to extract metadata.
        
        This is the key advantage of Bedrock - we can define
        exactly what metadata to extract!
        
        Returns
        -------
        str
            Structured prompt for Claude
        """
        prompt = f"""Extract structured metadata from the following financial text.

TEXT:
{text}

Extract the following information in JSON format:

1. **entities**: Categorize into:
   - organizations: Company names (e.g., "Morgan Stanley", "Apple")
   - people: Person names (e.g., "James Gorman", "Tim Cook")
   - locations: Places (e.g., "New York", "United States")
   - dates: Temporal references (e.g., "Q3 2024", "October 2024")
   - quantities: Numbers and amounts (e.g., "$15.4B", "25%")
   - titles: Job titles (e.g., "CEO", "Chief Financial Officer")
   - events: Named events (e.g., "Q3 Earnings Call")
   - products: Products/services (e.g., "iPhone 15", "AWS Lambda")

2. **key_phrases**: Important multi-word phrases (5-10 phrases)
   - Extract meaningful phrases that capture key concepts
   - Examples: "quarterly revenue growth", "operating margin expansion"

3. **financial_metrics**: Specific financial metrics mentioned
   - Examples: "revenue", "EBITDA", "profit margin", "EPS"

4. **sentiment**: Overall sentiment
   - "positive", "negative", "neutral", or "mixed"
   - Brief explanation (1 sentence)

5. **topics**: Main topics/themes (3-5 topics)
   - Examples: "quarterly results", "revenue growth", "strategic initiatives"

6. **key_insights**: Important insights or takeaways (2-3 insights)
   - What are the main points?

Return ONLY valid JSON with this exact structure:
{{
  "entities": {{
    "organizations": [list of strings],
    "people": [list of strings],
    "locations": [list of strings],
    "dates": [list of strings],
    "quantities": [list of strings],
    "titles": [list of strings],
    "events": [list of strings],
    "products": [list of strings]
  }},
  "key_phrases": [list of strings],
  "financial_metrics": [list of strings],
  "sentiment": {{
    "label": "positive|negative|neutral|mixed",
    "explanation": "brief explanation"
  }},
  "topics": [list of strings],
  "key_insights": [list of strings]
}}

Important:
- Return ONLY the JSON object, no other text
- Use empty lists [] for categories with no matches
- Be concise but accurate
- Focus on factual information"""
        
        return prompt
    
    @retry_on_throttle(max_retries=3, base_delay=2.0)
    def _call_bedrock(self, prompt: str) -> Dict:
        """
        Call AWS Bedrock with Claude model.
        
        Parameters
        ----------
        prompt : str
            Extraction prompt
            
        Returns
        -------
        Dict
            Bedrock API response
        """
        # Build request body for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Call Bedrock
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        return response_body
    
    def extract_with_bedrock(self, text: str) -> Dict:
        """
        Extract metadata using AWS Bedrock (Claude).
        
        This is the LLM-based extraction that provides:
        - Deeper understanding
        - Custom entity types
        - Semantic analysis
        - Flexible schema
        
        Parameters
        ----------
        text : str
            Text to analyze
            
        Returns
        -------
        Dict
            Extracted metadata:
            {
                'entities': {...},
                'key_phrases': [...],
                'financial_metrics': [...],
                'sentiment': {...},
                'topics': [...],
                'key_insights': [...]
            }
        """
        if not self.enable_bedrock:
            return self._empty_bedrock_metadata()
        
        try:
            # Build prompt
            prompt = self._build_extraction_prompt(text)
            
            # Call Bedrock
            response = self._call_bedrock(prompt)
            self.stats['bedrock_calls'] += 1
            
            # Extract content from response
            content = response.get('content', [])
            if not content:
                self.logger.warning("Empty response from Bedrock")
                return self._empty_bedrock_metadata()
            
            # Get text from first content block
            text_content = content[0].get('text', '')
            
            # Track token usage
            usage = response.get('usage', {})
            self.stats['total_input_tokens'] += usage.get('input_tokens', 0)
            self.stats['total_output_tokens'] += usage.get('output_tokens', 0)
            
            # Parse JSON response
            try:
                # Claude sometimes wraps JSON in markdown code blocks
                # Remove ```json and ``` if present
                text_content = text_content.strip()
                if text_content.startswith('```json'):
                    text_content = text_content[7:]  # Remove ```json
                if text_content.startswith('```'):
                    text_content = text_content[3:]  # Remove ```
                if text_content.endswith('```'):
                    text_content = text_content[:-3]  # Remove ```
                text_content = text_content.strip()
                
                metadata = json.loads(text_content)
                
                # Update statistics
                entities = metadata.get('entities', {})
                total_entities = sum(len(v) for v in entities.values())
                self.stats['entities_extracted'] += total_entities
                self.stats['key_phrases_extracted'] += len(metadata.get('key_phrases', []))
                
                return metadata
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse Bedrock JSON response: {e}")
                self.logger.error(f"Response: {text_content[:200]}...")
                self.stats['bedrock_errors'] += 1
                return self._empty_bedrock_metadata()
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            self.logger.error(f"Bedrock API error: {error_code} - {e}")
            self.stats['bedrock_errors'] += 1
            return self._empty_bedrock_metadata()
        
        except Exception as e:
            self.logger.error(f"Unexpected error in extract_with_bedrock: {e}")
            self.stats['bedrock_errors'] += 1
            return self._empty_bedrock_metadata()
    
    def _empty_bedrock_metadata(self) -> Dict:
        """Return empty Bedrock metadata structure."""
        return {
            'entities': {
                'organizations': [],
                'people': [],
                'locations': [],
                'dates': [],
                'quantities': [],
                'titles': [],
                'events': [],
                'products': []
            },
            'key_phrases': [],
            'financial_metrics': [],
            'sentiment': {
                'label': 'neutral',
                'explanation': 'No sentiment analysis performed'
            },
            'topics': [],
            'key_insights': []
        }
    
    def extract_custom_patterns(self, text: str) -> Dict:
        """
        Extract financial and temporal patterns using regex.
        
        Same implementation as Comprehend version.
        FREE and fast complement to Bedrock.
        """
        if not self.enable_patterns:
            return self._empty_patterns()
        
        results = {}
        
        # Monetary values
        money_matches = self.money_pattern.findall(text)
        results['monetary_values'] = sorted(set(money_matches), key=len, reverse=True)[:20]
        
        # Percentages
        percent_matches = self.percent_pattern.findall(text)
        results['percentages'] = sorted(set(percent_matches), reverse=True)[:20]
        
        # Quarters
        quarter_matches = self.quarter_pattern.findall(text)
        results['quarters'] = sorted(set(quarter_matches), reverse=True)
        
        # Fiscal years
        fy_matches = self.fiscal_year_pattern.findall(text)
        results['fiscal_years'] = sorted(set(fy_matches), reverse=True)
        
        # Years
        year_matches = self.year_pattern.findall(text)
        results['years'] = sorted(set(year_matches), reverse=True)
        
        # Financial metrics
        text_lower = text.lower()
        metrics_found = [
            metric for metric in self.financial_metrics
            if metric in text_lower
        ]
        results['financial_metrics_regex'] = sorted(set(metrics_found))
        
        # Update statistics
        total_patterns = sum(len(v) for v in results.values())
        self.stats['patterns_matched'] += total_patterns
        
        return results
    
    def _empty_patterns(self) -> Dict[str, List]:
        """Return empty patterns structure."""
        return {
            'monetary_values': [],
            'percentages': [],
            'quarters': [],
            'fiscal_years': [],
            'years': [],
            'financial_metrics_regex': []
        }
    
    def enrich_chunk(self, chunk: Dict) -> Dict:
        """
        Enrich a single chunk with metadata using Bedrock.
        
        Process
        -------
        1. Extract text from chunk
        2. Call AWS Bedrock (Claude) for semantic metadata
        3. Extract custom patterns via regex (FREE)
        4. Merge all metadata into chunk
        
        Parameters
        ----------
        chunk : Dict
            Chunk with 'content_only' field
            
        Returns
        -------
        Dict
            Enriched chunk with Bedrock metadata added
        """
        # Get text to analyze
        text = chunk.get('content_only', '')
        
        if not text or not text.strip():
            self.logger.warning(f"Empty text for chunk {chunk.get('id', 'unknown')}")
            return chunk
        
        # Extract metadata using Bedrock (LLM-based)
        bedrock_metadata = self.extract_with_bedrock(text)
        
        # Extract custom patterns (Regex-based, FREE)
        pattern_metadata = self.extract_custom_patterns(text)
        
        # Merge into chunk metadata
        if 'metadata' not in chunk:
            chunk['metadata'] = {}
        
        # Add Bedrock metadata
        chunk['metadata'].update(bedrock_metadata)
        
        # Add pattern metadata
        chunk['metadata'].update(pattern_metadata)
        
        # Update statistics
        self.stats['chunks_processed'] += 1
        
        return chunk
    
    def enrich_chunks_batch(
        self,
        chunks: List[Dict],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Enrich multiple chunks with progress tracking.
        
        Same as Comprehend version but uses Bedrock.
        """
        enriched_chunks = []
        total = len(chunks)
        
        if show_progress:
            self.logger.info(f"Starting enrichment of {total} chunks...")
        
        for i, chunk in enumerate(chunks, 1):
            enriched = self.enrich_chunk(chunk)
            enriched_chunks.append(enriched)
            
            if show_progress and i % batch_size == 0:
                pct = (i / total) * 100
                self.logger.info(f"Progress: {i}/{total} ({pct:.1f}%)")
        
        if show_progress:
            self.logger.info(f"Enrichment complete! Processed {total} chunks")
            self.print_statistics()
        
        return enriched_chunks
    
    def print_statistics(self):
        """Print enrichment statistics with cost estimation."""
        print("\n" + "="*70)
        print("BEDROCK METADATA ENRICHMENT STATISTICS")
        print("="*70)
        print(f"Chunks processed:        {self.stats['chunks_processed']:,}")
        print(f"Bedrock API calls:       {self.stats['bedrock_calls']:,}")
        print(f"Bedrock errors:          {self.stats['bedrock_errors']:,}")
        print(f"Entities extracted:      {self.stats['entities_extracted']:,}")
        print(f"Key phrases extracted:   {self.stats['key_phrases_extracted']:,}")
        print(f"Pattern matches:         {self.stats['patterns_matched']:,}")
        print(f"\nToken Usage:")
        print(f"Input tokens:            {self.stats['total_input_tokens']:,}")
        print(f"Output tokens:           {self.stats['total_output_tokens']:,}")
        
        # Cost estimation for Claude 3.5 Sonnet
        if self.stats['bedrock_calls'] > 0:
            input_cost = (self.stats['total_input_tokens'] / 1_000_000) * 3.0
            output_cost = (self.stats['total_output_tokens'] / 1_000_000) * 15.0
            total_cost = input_cost + output_cost
            
            print(f"\nEstimated AWS Bedrock cost:")
            print(f"Input tokens cost:       ${input_cost:.2f}")
            print(f"Output tokens cost:      ${output_cost:.2f}")
            print(f"Total cost:              ${total_cost:.2f}")
            print(f"Cost per chunk:          ${total_cost/self.stats['chunks_processed']:.4f}")
        
        print("="*70 + "\n")
    
    def get_statistics(self) -> Dict:
        """Return statistics as dictionary."""
        return self.stats.copy()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_bedrock_single_chunk():
    """Example: Enrich chunk with Bedrock."""
    print("\n" + "="*70)
    print("EXAMPLE: Bedrock Single Chunk Enrichment")
    print("="*70)
    
    chunk = {
        'id': 'abc123',
        'content_only': """Morgan Stanley reported Q3 2024 revenue of $15.4B, 
                          representing 25% growth year-over-year. CEO James Gorman 
                          highlighted strong performance in investment banking, with 
                          M&A advisory fees up 30%. The company's EBITDA margin 
                          improved to 28%, and EPS reached $2.15. Looking ahead, 
                          management remains optimistic about continued growth in 
                          wealth management and institutional securities.""",
        'metadata': {
            'source': 'page_005.md',
            'page_number': 5
        }
    }
    
    # Create enricher with Bedrock
    enricher = BedrockMetadataEnricher(
        region_name='us-east-1',
        model_id='anthropic.claude-3-5-sonnet-20241022-v1:0',
        enable_bedrock=True,
        enable_patterns=True
    )
    
    # Enrich chunk
    enriched = enricher.enrich_chunk(chunk)
    
    # Display results
    print("\n--- ENTITIES ---")
    for entity_type, entities in enriched['metadata']['entities'].items():
        if entities:
            print(f"{entity_type}: {entities}")
    
    print("\n--- KEY PHRASES ---")
    print(enriched['metadata']['key_phrases'])
    
    print("\n--- SENTIMENT ---")
    sentiment = enriched['metadata']['sentiment']
    print(f"Label: {sentiment['label']}")
    print(f"Explanation: {sentiment['explanation']}")
    
    print("\n--- TOPICS ---")
    print(enriched['metadata']['topics'])
    
    print("\n--- KEY INSIGHTS ---")
    for insight in enriched['metadata']['key_insights']:
        print(f"- {insight}")
    
    print("\n--- CUSTOM PATTERNS ---")
    print(f"Monetary values: {enriched['metadata']['monetary_values']}")
    print(f"Percentages: {enriched['metadata']['percentages']}")
    print(f"Quarters: {enriched['metadata']['quarters']}")
    
    enricher.print_statistics()


def example_compare_costs():
    """Compare Comprehend vs Bedrock costs."""
    print("\n" + "="*70)
    print("COST COMPARISON: Comprehend vs Bedrock")
    print("="*70)
    
    num_chunks = 10000
    avg_chars = 500
    
    # Comprehend costs
    comprehend_cost = (num_chunks * avg_chars * 0.0001 / 100) * 2  # entities + phrases
    
    # Bedrock costs (estimated)
    avg_input_tokens = avg_chars / 4  # ~125 tokens
    avg_output_tokens = 200  # JSON metadata
    bedrock_input_cost = (num_chunks * avg_input_tokens / 1_000_000) * 3.0
    bedrock_output_cost = (num_chunks * avg_output_tokens / 1_000_000) * 15.0
    bedrock_cost = bedrock_input_cost + bedrock_output_cost
    
    print(f"\nFor {num_chunks:,} chunks ({avg_chars} chars each):")
    print(f"\nAWS Comprehend:")
    print(f"  Total cost: ${comprehend_cost:.2f}")
    print(f"  Per chunk:  ${comprehend_cost/num_chunks:.4f}")
    
    print(f"\nAWS Bedrock (Claude 3.5 Sonnet):")
    print(f"  Total cost: ${bedrock_cost:.2f}")
    print(f"  Per chunk:  ${bedrock_cost/num_chunks:.4f}")
    
    print(f"\nDifference:")
    print(f"  Additional cost: ${bedrock_cost - comprehend_cost:.2f}")
    print(f"  Cost multiplier: {bedrock_cost / comprehend_cost:.1f}x")
    
    print(f"\nTrade-off:")
    print(f"  Comprehend: Cheaper, fast, standard entities")
    print(f"  Bedrock:    More expensive, flexible, deeper analysis")
    print("="*70 + "\n")


if __name__ == '__main__':
    """
    Run examples.
    
    Requirements:
    - AWS credentials configured
    - Access to Bedrock (may need to request model access)
    - boto3 installed: pip install boto3
    """
    print("\n" + "="*70)
    print("BEDROCK METADATA ENRICHER - Examples")
    print("="*70)
    
    # Run examples
    example_bedrock_single_chunk()
    example_compare_costs()
    
    print("\n✓ Examples completed successfully!")
