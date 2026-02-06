# Semantic Chunker Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         MAIN ENTRY POINT                        │
│                           main.py                               │
│                    (CLI argument parsing)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                             │
│                       orchestrator.py                           │
│                 (Pipeline coordination)                         │
└─────┬────────┬────────┬────────┬────────┬────────┬─────────────┘
      │        │        │        │        │        │
      ▼        ▼        ▼        ▼        ▼        ▼
   ┌────┐  ┌────┐  ┌────┐  ┌────┐  ┌────┐  ┌────┐
   │CFG │  │LOG │  │BLK │  │PARSE│  │CHK │  │I/O │
   └────┘  └────┘  └────┘  └────┘  └────┘  └────┘
   config  logger  protect semantic chunk   file_io
           _utils  _blocks  _parser  _engine
```

## Module Dependency Graph

```
main.py
  └─→ orchestrator.py
        ├─→ config.py
        ├─→ logger_utils.py
        ├─→ file_io.py
        ├─→ protected_blocks.py
        │     └─→ config.py
        ├─→ semantic_parser.py
        │     ├─→ config.py
        │     └─→ protected_blocks.py
        ├─→ chunking_engine.py
        │     └─→ config.py
        ├─→ continuation_detection.py
        │     └─→ config.py
        ├─→ page_merging.py
        │     └─→ chunking_engine.py
        └─→ statistics_calculator.py
```

## Data Flow

### Input Phase
```
Input Directory
    ├── metadata.json
    └── pages/
          ├── page_001.md
          ├── page_002.md
          └── ...
```

### Processing Pipeline

```
┌──────────────────────────────────────────────────────┐
│ 1. LOAD METADATA                                     │
│    file_io.load_metadata()                           │
│    → Dict[document, pages[]]                         │
└─────────────────┬────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────┐
│ 2. FOR EACH PAGE:                                    │
│                                                      │
│    a) Load markdown text                            │
│       file_io → str                                 │
│                                                      │
│    b) Identify protected blocks                     │
│       protected_blocks.identify()                   │
│       → List[(start, end, type, content)]           │
│                                                      │
│    c) Parse semantic sections                       │
│       semantic_parser.parse_sections()              │
│       → List[{type, content, breadcrumbs}]          │
│                                                      │
│    d) Consolidate paragraphs                        │
│       semantic_parser.consolidate_paragraphs()      │
│       → List[{merged sections}]                     │
│                                                      │
│    e) Build chunks                                  │
│       chunking_engine.build_chunks()                │
│       → List[{id, text, metadata}]                  │
└─────────────────┬────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────┐
│ 3. CROSS-PAGE PROCESSING:                            │
│                                                      │
│    a) Detect continuation                           │
│       continuation_detection.detect()               │
│       → bool                                        │
│                                                      │
│    b) If continues, merge boundary chunks           │
│       page_merging.merge_continued_pages()          │
│       → List[{merged chunks}]                       │
└─────────────────┬────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────┐
│ 4. FINALIZATION:                                     │
│                                                      │
│    a) Calculate statistics                          │
│       statistics_calculator.calculate()             │
│       → Dict[comprehensive stats]                   │
│                                                      │
│    b) Save output                                   │
│       file_io.save_chunks_output()                  │
│       → Path to output file                         │
└──────────────────────────────────────────────────────┘
```

### Output Phase
```
Input Directory
    ├── chunks_output.json
    └── logs/
          └── chunking_YYYYMMDD_HHMMSS.log
```

## State Management

### No Global State
All state is passed explicitly through function parameters:

```python
# Configuration
config = create_config(target_size=1500)

# Statistics accumulator
stats = create_stats_dict()

# Process with explicit state
chunks = process_page(page, config, stats, logger)
```

### State Types

1. **Configuration** (Immutable)
   ```python
   config = {
       'target_size': 1500,
       'patterns': {...},
       'enable_merging': True
   }
   ```

2. **Statistics** (Mutable accumulator)
   ```python
   stats = {
       'total_pages': 0,
       'total_chunks': 0,
       'duplicates_prevented': 0,
       ...
   }
   ```

3. **Logger** (Side effects isolated)
   ```python
   logger = setup_logger(input_dir, verbose=True)
   ```

## Error Handling Strategy

### Layered Error Handling

```
main.py
  ├─ KeyboardInterrupt → Exit gracefully
  ├─ Exception → Log and exit with code 1
  └─→ orchestrator.py
       ├─ Validation errors → Log and return {}
       ├─ File errors → Log and continue
       └─→ Module functions
            ├─ Invalid input → Log warning, skip
            └─ Critical error → Raise to orchestrator
```

### Error Recovery

```python
# File not found → Skip page
if not page_path.exists():
    logger.warning(f"Page not found: {page_path}")
    return []

# Invalid chunk → Skip chunk
if not validate_chunk(chunk):
    logger.warning(f"Invalid chunk: {chunk_id}")
    stats['validation_failures'] += 1
    return False

# Duplicate chunk → Skip silently
if chunk_id in recent_chunks:
    stats['duplicates_prevented'] += 1
    return  # Don't add
```

## Performance Optimizations

### 1. Compiled Regex Patterns
```python
# In config.py - compiled once
PATTERNS = {
    'header': re.compile(r'^(#{1,6})\s+(.+)'),
    'list': re.compile(r'^[-*+]|\d+\.'),
    ...
}
```

### 2. Bounded Deduplication
```python
# Only check last 5 chunks (O(1) instead of O(n))
for existing in chunks[-5:]:
    if existing['id'] == new_hash:
        return  # Duplicate
```

### 3. Streaming Processing
```python
# Process one page at a time
for page in pages:
    chunks = process_page(page)
    all_chunks.extend(chunks)
```

### 4. Early Returns
```python
# Skip empty content early
if not text.strip():
    return []

# Skip invalid paths
if not path.exists():
    return None
```

## Testing Strategy

### Unit Testing (per module)
```python
# test_protected_blocks.py
def test_image_detection():
    blocks = identify_protected_blocks(sample_text, config, logger)
    assert len(blocks) == 2
    assert blocks[0][2] == 'image'

# test_semantic_parser.py
def test_header_breadcrumbs():
    sections = parse_semantic_sections(text, [], config, logger)
    assert sections[0]['breadcrumbs'] == ['Chapter 1']
```

### Integration Testing
```python
# test_integration.py
def test_full_pipeline():
    results = process_document('test_data', ...)
    assert results['total_chunks'] > 0
    assert Path('test_data/chunks_output.json').exists()
```

### Property-Based Testing
```python
# test_properties.py
@given(text=st.text(), target=st.integers(500, 3000))
def test_chunk_sizes(text, target):
    config = create_config(target_size=target)
    chunks = process_document(...)
    for chunk in chunks:
        assert len(chunk['content_only']) <= config['max_size']
```

## Extensibility Points

### Adding New Chunk Types
```python
# In protected_blocks.py
def identify_protected_blocks():
    # ... existing code ...
    
    # Add new pattern
    equation_pattern = r"\$\$.*?\$\$"
    for match in re.finditer(equation_pattern, text, re.DOTALL):
        blocks.append((match.start(), match.end(), "equation", match.group(0)))
```

### Adding New Statistics
```python
# In statistics_calculator.py
def calculate_comprehensive_statistics():
    # ... existing code ...
    
    # Add new metric
    chunks_with_equations = sum(
        1 for c in chunks 
        if c['metadata']['type'] == 'equation'
    )
```

### Adding New Continuation Signals
```python
# In continuation_detection.py
def detect_page_continuation():
    # ... existing signals ...
    
    # Add new signal
    formula_signal = _check_formula_continuation(curr_end, next_start)
    signals.append(formula_signal)
```

## Design Patterns Used

1. **Pipeline Pattern**: Data flows through sequence of transformations
2. **Strategy Pattern**: Different processing strategies for different content types
3. **Template Method**: Consistent structure with pluggable steps
4. **Facade Pattern**: Orchestrator provides simple interface to complex subsystem
5. **Factory Pattern**: Functions create configured objects (logger, config)

## Future Enhancements

1. **Parallel Processing**: Process multiple pages concurrently
2. **Streaming Output**: Write chunks as they're created
3. **Plugin System**: Load custom processing modules
4. **Configuration Profiles**: Pre-defined configs for different use cases
5. **Metrics Dashboard**: Real-time processing visualization
