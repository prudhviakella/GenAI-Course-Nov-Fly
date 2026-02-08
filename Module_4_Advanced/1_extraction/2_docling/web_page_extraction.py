"""
Web Page Content Extraction & Analysis Pipeline
===============================================

This module extracts comprehensive content from web pages including text,
images, tables, forms, and layout structure. Generates markdown output with
AI-powered analysis of visual elements.

Key Features:
- Complete HTML element extraction (text, images, tables, forms, videos)
- Layout structure preservation with semantic HTML mapping
- GPT-4 Vision integration for image analysis
- Structured markdown output organized by sections
- Robust error handling for production use

Author: Prudhvi
"""

import base64
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
from openai import OpenAI


# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================

# Request headers to mimic browser behavior
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# Timeout for HTTP requests (seconds)
REQUEST_TIMEOUT = 30

# Maximum image size to download (bytes) - 10MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024

# HTML tags that represent structural sections
SECTION_TAGS = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']

# HTML tags for headings
HEADING_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

# Tags to skip entirely (scripts, styles, etc.)
SKIP_TAGS = ['script', 'style', 'noscript', 'meta', 'link']


# ==============================================================================
# HTTP REQUEST & PAGE FETCHING
# ==============================================================================

def _fetch_page(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch Web Page Content

    PURPOSE:
    --------
    Downloads HTML content from URL with proper error handling,
    timeout management, and encoding detection.

    WORKFLOW:
    ---------
    ┌─────────────────────────────────────────────────────────────┐
    │              HTTP REQUEST PIPELINE                          │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  1. Validate URL format                                     │
    │     │                                                        │
    │     ▼                                                        │
    │  2. Send GET request with headers & timeout                 │
    │     │                                                        │
    │     ▼                                                        │
    │  3. Check HTTP status code                                  │
    │     │                                                        │
    │     ▼                                                        │
    │  4. Detect and decode content encoding                      │
    │     │                                                        │
    │     ▼                                                        │
    │  5. Return HTML content and final URL                       │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

    Parameters
    ----------
    url : str
        Target URL to fetch

    Returns
    -------
    Tuple[Optional[str], Optional[str]]
        (html_content, final_url) or (None, None) on error
        final_url accounts for redirects

    ERROR HANDLING:
    ---------------
    - Invalid URL format
    - Connection timeout
    - HTTP errors (4xx, 5xx)
    - Network failures
    - Encoding issues
    """
    try:
        # Validate URL has scheme
        parsed = urlparse(url)
        if not parsed.scheme:
            print(f"ERROR: Invalid URL format: {url}")
            return None, None

        print(f"Fetching URL: {url}")

        # Send GET request with timeout
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )

        # Check for HTTP errors
        response.raise_for_status()

        # Get final URL after redirects
        final_url = response.url

        # Detect encoding (fallback to utf-8)
        encoding = response.encoding or 'utf-8'
        html_content = response.content.decode(encoding, errors='ignore')

        print(f"✓ Successfully fetched {len(html_content)} characters")
        return html_content, final_url

    except requests.exceptions.Timeout:
        print(f"ERROR: Request timeout after {REQUEST_TIMEOUT}s")
        return None, None

    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP {e.response.status_code}: {str(e)}")
        return None, None

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error: {str(e)}")
        return None, None

    except Exception as e:
        print(f"ERROR: Unexpected error fetching page: {str(e)}")
        return None, None


# ==============================================================================
# IMAGE HANDLING
# ==============================================================================

def _download_image(img_url: str, base_url: str, out_dir: Path,
                   img_count: int) -> Optional[str]:
    """
    Download and Save Image from URL

    PURPOSE:
    --------
    Downloads images from web pages, handles relative URLs,
    enforces size limits, and saves to output directory.

    Parameters
    ----------
    img_url : str
        Image URL (can be relative or absolute)
    base_url : str
        Base URL for resolving relative paths
    out_dir : Path
        Output directory containing images/ subdirectory
    img_count : int
        Current image count for filename generation

    Returns
    -------
    Optional[str]
        Relative path to saved image or None on failure

    FEATURES:
    ---------
    - Resolves relative URLs using base_url
    - Enforces MAX_IMAGE_SIZE limit
    - Generates sequential filenames: img_1.jpg, img_2.png, etc.
    - Preserves original file extension
    - Handles common image formats (jpg, png, gif, webp, svg)
    """
    try:
        # Resolve relative URLs
        full_url = urljoin(base_url, img_url)

        # Download image with size check
        img_response = requests.get(
            full_url,
            headers=HEADERS,
            timeout=10,
            stream=True
        )
        img_response.raise_for_status()

        # Check content length if available
        content_length = img_response.headers.get('content-length')
        if content_length and int(content_length) > MAX_IMAGE_SIZE:
            print(f"  WARNING: Image too large ({int(content_length)} bytes), skipping")
            return None

        # Read image data
        img_data = img_response.content

        # Double-check actual size
        if len(img_data) > MAX_IMAGE_SIZE:
            print(f"  WARNING: Image exceeds size limit, skipping")
            return None

        # Determine file extension from URL or content-type
        ext = Path(urlparse(img_url).path).suffix
        if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
            content_type = img_response.headers.get('content-type', '')
            ext_map = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.webp',
                'image/svg+xml': '.svg'
            }
            ext = ext_map.get(content_type, '.jpg')

        # Generate filename
        filename = f"img_{img_count}{ext}"
        filepath = out_dir / "images" / filename

        # Save image
        with open(filepath, 'wb') as f:
            f.write(img_data)

        return f"images/{filename}"

    except Exception as e:
        print(f"  WARNING: Failed to download image {img_url}: {str(e)}")
        return None


def _analyze_image(img_path: Path, openai_client: OpenAI, model: str) -> str:
    """
    AI-Powered Image Analysis

    Uses GPT-4 Vision to analyze web page images and generate
    natural language descriptions.

    Parameters
    ----------
    img_path : Path
        Path to saved image file
    openai_client : OpenAI
        OpenAI client instance
    model : str
        Model name (e.g., "gpt-4o")

    Returns
    -------
    str
        AI-generated description or error message
    """
    try:
        with open(img_path, "rb") as f:
            img_bytes = f.read()
            b64 = base64.b64encode(img_bytes).decode('utf-8')

        prompt = (
            "Analyze this web page image. Describe what you see: "
            "Is it a logo, chart, diagram, photo, or UI element? "
            "What information does it convey? Be concise."
        )

        response = openai_client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64}"
                        }
                    }
                ]
            }],
            max_tokens=150
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"  WARNING: Image analysis failed: {str(e)}")
        return "Image analysis unavailable"


# ==============================================================================
# HTML ELEMENT EXTRACTION
# ==============================================================================

def _extract_text(element: Tag) -> str:
    """
    Extract Clean Text from HTML Element

    Removes extra whitespace, normalizes line breaks,
    and cleans up formatting.

    Parameters
    ----------
    element : Tag
        BeautifulSoup tag element

    Returns
    -------
    str
        Cleaned text content
    """
    text = element.get_text(separator=' ', strip=True)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _extract_links(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    """
    Extract All Hyperlinks from Page

    PURPOSE:
    --------
    Extracts all <a> tags with href attributes, resolves
    relative URLs, and categorizes as internal/external.

    Returns
    -------
    List[Dict[str, str]]
        List of dicts with keys: 'text', 'url', 'type'
        type is either 'internal' or 'external'
    """
    links = []
    base_domain = urlparse(base_url).netloc

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        link_domain = urlparse(full_url).netloc

        # Determine if link is internal or external
        link_type = 'internal' if link_domain == base_domain else 'external'

        links.append({
            'text': _extract_text(a_tag) or '[No text]',
            'url': full_url,
            'type': link_type
        })

    return links


def _extract_tables(soup: BeautifulSoup) -> List[Dict[str, any]]:
    """
    Extract All Tables from Page

    PURPOSE:
    --------
    Parses HTML tables into structured format with headers
    and rows. Handles complex tables with rowspan/colspan.

    Returns
    -------
    List[Dict]
        Each dict contains:
        - 'headers': List of column headers
        - 'rows': List of row data (each row is list of cells)
        - 'markdown': Markdown representation
    """
    tables = []

    for idx, table in enumerate(soup.find_all('table')):
        headers = []
        rows = []

        # Extract headers from <thead> or first <tr>
        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                headers = [_extract_text(th) for th in header_row.find_all(['th', 'td'])]

        # If no thead, check first row
        if not headers:
            first_row = table.find('tr')
            if first_row:
                first_cells = first_row.find_all(['th', 'td'])
                if first_cells and first_cells[0].name == 'th':
                    headers = [_extract_text(th) for th in first_cells]

        # Extract data rows from <tbody> or all <tr>
        tbody = table.find('tbody') or table
        for tr in tbody.find_all('tr'):
            # Skip header rows
            if tr.find_parent('thead'):
                continue

            cells = [_extract_text(td) for td in tr.find_all(['td', 'th'])]
            if cells:  # Only add non-empty rows
                rows.append(cells)

        # Generate markdown representation
        if headers and rows:
            # Create markdown table
            md_table = "| " + " | ".join(headers) + " |\n"
            md_table += "| " + " | ".join(['---'] * len(headers)) + " |\n"
            for row in rows:
                # Pad row if necessary
                padded_row = row + [''] * (len(headers) - len(row))
                md_table += "| " + " | ".join(padded_row[:len(headers)]) + " |\n"
        elif rows:
            # Table without headers
            md_table = ""
            for row in rows:
                md_table += "| " + " | ".join(row) + " |\n"
        else:
            md_table = ""

        if md_table:
            tables.append({
                'index': idx + 1,
                'headers': headers,
                'rows': rows,
                'markdown': md_table
            })

    return tables


def _extract_forms(soup: BeautifulSoup) -> List[Dict[str, any]]:
    """
    Extract All Forms from Page

    PURPOSE:
    --------
    Extracts form structure including action, method,
    input fields, and buttons.

    Returns
    -------
    List[Dict]
        Each dict contains form metadata and field information
    """
    forms = []

    for idx, form in enumerate(soup.find_all('form')):
        fields = []

        # Extract all input fields
        for input_tag in form.find_all(['input', 'textarea', 'select']):
            field_type = input_tag.get('type', 'text')
            field_name = input_tag.get('name', f'unnamed_{len(fields)}')
            field_placeholder = input_tag.get('placeholder', '')

            fields.append({
                'type': field_type,
                'name': field_name,
                'placeholder': field_placeholder
            })

        forms.append({
            'index': idx + 1,
            'action': form.get('action', ''),
            'method': form.get('method', 'get').upper(),
            'fields': fields
        })

    return forms


def _extract_media(soup: BeautifulSoup, base_url: str) -> Dict[str, List[str]]:
    """
    Extract Media Elements (Video, Audio, Iframe)

    Returns
    -------
    Dict[str, List[str]]
        Keys: 'videos', 'audio', 'iframes'
        Values: Lists of URLs
    """
    media = {
        'videos': [],
        'audio': [],
        'iframes': []
    }

    # Videos
    for video in soup.find_all('video'):
        src = video.get('src')
        if src:
            media['videos'].append(urljoin(base_url, src))
        # Check for source tags
        for source in video.find_all('source'):
            src = source.get('src')
            if src:
                media['videos'].append(urljoin(base_url, src))

    # Audio
    for audio in soup.find_all('audio'):
        src = audio.get('src')
        if src:
            media['audio'].append(urljoin(base_url, src))

    # Iframes (often used for embedded videos)
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src')
        if src:
            media['iframes'].append(urljoin(base_url, src))

    return media


# ==============================================================================
# STRUCTURE & LAYOUT EXTRACTION
# ==============================================================================

def _extract_structure(soup: BeautifulSoup, base_url: str, out_dir: Path,
                      openai_client: OpenAI, model: str) -> List[Dict]:
    """
    Extract Page Structure with Content

    PURPOSE:
    --------
    Walks through HTML structure preserving semantic layout.
    Extracts headings, paragraphs, lists, images, and maintains
    hierarchical relationships.

    WORKFLOW:
    ---------
    ┌─────────────────────────────────────────────────────────────┐
    │           STRUCTURE EXTRACTION PIPELINE                     │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  1. Find main content area (article, main, or body)         │
    │     │                                                        │
    │     ▼                                                        │
    │  2. Recursively process elements:                           │
    │     ├─ Headings (h1-h6) → Section markers                  │
    │     ├─ Paragraphs → Text content                           │
    │     ├─ Lists (ul, ol) → Bullet/numbered items              │
    │     ├─ Images → Download + AI analysis                     │
    │     ├─ Blockquotes → Quoted text                           │
    │     └─ Divs/Sections → Nested content                      │
    │     │                                                        │
    │     ▼                                                        │
    │  3. Track hierarchy level for markdown headers              │
    │     │                                                        │
    │     ▼                                                        │
    │  4. Return structured content list                          │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

    Returns
    -------
    List[Dict]
        Each dict represents a content block with:
        - 'type': heading, paragraph, list, image, etc.
        - 'level': hierarchy depth (for headings)
        - 'content': actual content
        - 'markdown': pre-formatted markdown
    """
    content_blocks = []
    img_count = [0]  # Mutable counter for images

    def _process_element(elem: Tag, level: int = 1):
        """Recursive helper to process HTML elements"""

        # Skip unwanted tags
        if elem.name in SKIP_TAGS:
            return

        # Process based on element type
        if elem.name in HEADING_TAGS:
            # Extract heading level (h1=1, h2=2, etc.)
            h_level = int(elem.name[1])
            text = _extract_text(elem)
            if text:
                content_blocks.append({
                    'type': 'heading',
                    'level': h_level,
                    'content': text,
                    'markdown': f"{'#' * h_level} {text}\n"
                })

        elif elem.name == 'p':
            text = _extract_text(elem)
            if text:
                content_blocks.append({
                    'type': 'paragraph',
                    'content': text,
                    'markdown': f"{text}\n"
                })

        elif elem.name in ['ul', 'ol']:
            items = []
            for li in elem.find_all('li', recursive=False):
                li_text = _extract_text(li)
                if li_text:
                    items.append(li_text)

            if items:
                prefix = '-' if elem.name == 'ul' else '1.'
                md_list = '\n'.join([f"{prefix} {item}" for item in items])
                content_blocks.append({
                    'type': 'list',
                    'list_type': elem.name,
                    'items': items,
                    'markdown': f"{md_list}\n"
                })

        elif elem.name == 'img':
            img_url = elem.get('src')
            alt_text = elem.get('alt', '')

            if img_url:
                img_count[0] += 1
                saved_path = _download_image(
                    img_url, base_url, out_dir, img_count[0]
                )

                if saved_path:
                    # AI analysis
                    img_path = out_dir / saved_path
                    description = _analyze_image(img_path, openai_client, model)

                    content_blocks.append({
                        'type': 'image',
                        'url': img_url,
                        'alt': alt_text,
                        'path': saved_path,
                        'description': description,
                        'markdown': (
                            f"\n![{alt_text}](../{saved_path})\n"
                            f"*AI Analysis:* {description}\n"
                        )
                    })

        elif elem.name == 'blockquote':
            text = _extract_text(elem)
            if text:
                # Format as markdown blockquote
                quoted = '\n'.join([f"> {line}" for line in text.split('\n')])
                content_blocks.append({
                    'type': 'blockquote',
                    'content': text,
                    'markdown': f"{quoted}\n"
                })

        elif elem.name == 'pre':
            code = elem.get_text()
            if code.strip():
                content_blocks.append({
                    'type': 'code',
                    'content': code,
                    'markdown': f"```\n{code}\n```\n"
                })

        # Recursively process children for container elements
        elif elem.name in ['div', 'section', 'article', 'main', 'aside', 'header', 'footer']:
            for child in elem.children:
                if isinstance(child, Tag):
                    _process_element(child, level)

    # Find main content area
    main_content = (
        soup.find('main') or
        soup.find('article') or
        soup.find('div', {'id': 'content'}) or
        soup.find('div', {'class': 'content'}) or
        soup.body
    )

    if main_content:
        for child in main_content.children:
            if isinstance(child, Tag):
                _process_element(child)

    return content_blocks


# ==============================================================================
# METADATA EXTRACTION
# ==============================================================================

def _extract_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extract Page Metadata

    Extracts title, description, keywords, and Open Graph tags.

    Returns
    -------
    Dict[str, str]
        Metadata key-value pairs
    """
    metadata = {}

    # Title
    title_tag = soup.find('title')
    if title_tag:
        metadata['title'] = title_tag.string.strip()

    # Meta description
    desc_tag = soup.find('meta', {'name': 'description'})
    if desc_tag:
        metadata['description'] = desc_tag.get('content', '')

    # Meta keywords
    keywords_tag = soup.find('meta', {'name': 'keywords'})
    if keywords_tag:
        metadata['keywords'] = keywords_tag.get('content', '')

    # Open Graph tags
    og_title = soup.find('meta', {'property': 'og:title'})
    if og_title:
        metadata['og_title'] = og_title.get('content', '')

    og_desc = soup.find('meta', {'property': 'og:description'})
    if og_desc:
        metadata['og_description'] = og_desc.get('content', '')

    return metadata


# ==============================================================================
# MARKDOWN GENERATION
# ==============================================================================

def _generate_markdown(url: str, metadata: Dict, structure: List[Dict],
                      tables: List[Dict], forms: List[Dict], links: List[Dict],
                      media: Dict) -> str:
    """
    Generate Comprehensive Markdown Report

    Combines all extracted data into well-formatted markdown document.

    Returns
    -------
    str
        Complete markdown content
    """
    lines = []

    # Header
    lines.append(f"# Web Page Extraction Report\n")
    lines.append(f"**Source URL:** {url}\n")
    lines.append(f"**Extracted:** {Path.cwd()}\n")

    # Metadata section
    if metadata:
        lines.append("\n## Page Metadata\n")
        for key, value in metadata.items():
            if value:
                lines.append(f"- **{key.title()}:** {value}")

    # Main content
    lines.append("\n## Main Content\n")
    for block in structure:
        lines.append(block['markdown'])

    # Tables section
    if tables:
        lines.append("\n## Tables\n")
        for table in tables:
            lines.append(f"\n### Table {table['index']}\n")
            lines.append(table['markdown'])

    # Forms section
    if forms:
        lines.append("\n## Forms\n")
        for form in forms:
            lines.append(f"\n### Form {form['index']}\n")
            lines.append(f"- **Action:** {form['action']}")
            lines.append(f"- **Method:** {form['method']}")
            lines.append(f"- **Fields:**")
            for field in form['fields']:
                lines.append(f"  - {field['type']}: {field['name']}")

    # Media section
    if any(media.values()):
        lines.append("\n## Media Elements\n")
        if media['videos']:
            lines.append(f"\n### Videos ({len(media['videos'])})")
            for vid_url in media['videos']:
                lines.append(f"- {vid_url}")
        if media['audio']:
            lines.append(f"\n### Audio ({len(media['audio'])})")
            for aud_url in media['audio']:
                lines.append(f"- {aud_url}")
        if media['iframes']:
            lines.append(f"\n### Embedded Content ({len(media['iframes'])})")
            for iframe_url in media['iframes']:
                lines.append(f"- {iframe_url}")

    # Links section (summary only)
    if links:
        internal = [l for l in links if l['type'] == 'internal']
        external = [l for l in links if l['type'] == 'external']
        lines.append(f"\n## Links Summary\n")
        lines.append(f"- Internal links: {len(internal)}")
        lines.append(f"- External links: {len(external)}")

    return '\n'.join(lines)


# ==============================================================================
# MAIN PIPELINE
# ==============================================================================

def extract_webpage(url: str, output_dir: Optional[Path] = None,
                   use_ai_vision: bool = True) -> Optional[Path]:
    """
    Complete Web Page Extraction Pipeline

    PURPOSE:
    --------
    End-to-end extraction of web page content including text,
    structure, images, tables, forms, and media elements.

    WORKFLOW:
    ---------
    1. Fetch HTML content
    2. Parse with BeautifulSoup
    3. Extract metadata
    4. Extract structure and content
    5. Extract tables, forms, links, media
    6. Download and analyze images (optional AI)
    7. Generate markdown report
    8. Save to output directory

    Parameters
    ----------
    url : str
        Target URL to extract
    output_dir : Optional[Path]
        Custom output directory (default: ./extracted_webpages)
    use_ai_vision : bool
        Whether to use GPT-4 Vision for image analysis

    Returns
    -------
    Optional[Path]
        Path to generated markdown file, or None on failure

    EXAMPLE USAGE:
    --------------
```python
    # Basic extraction
    result = extract_webpage("https://example.com")

    # Custom output directory, no AI
    result = extract_webpage(
        "https://example.com",
        output_dir=Path("./my_extracts"),
        use_ai_vision=False
    )
```
    """

    print(f"\n{'='*70}")
    print(f"WEB PAGE EXTRACTION PIPELINE")
    print(f"{'='*70}\n")

    # ==========================================================================
    # STEP 1: Fetch HTML Content
    # ==========================================================================

    html_content, final_url = _fetch_page(url)
    if not html_content:
        print("ERROR: Failed to fetch page content")
        return None

    # ==========================================================================
    # STEP 2: Parse HTML
    # ==========================================================================

    print("Parsing HTML...")
    soup = BeautifulSoup(html_content, 'html.parser')

    # ==========================================================================
    # STEP 3: Setup Output Directory
    # ==========================================================================

    if output_dir is None:
        output_dir = Path("extracted_webpages")

    # Create subdirectory based on URL domain
    domain = urlparse(final_url).netloc.replace('www.', '')
    page_dir = output_dir / domain
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / "images").mkdir(exist_ok=True)

    print(f"Output directory: {page_dir}")

    # ==========================================================================
    # STEP 4: Initialize OpenAI Client (if using AI vision)
    # ==========================================================================

    openai_client = None
    model = "gpt-4o"

    if use_ai_vision:
        try:
            openai_client = OpenAI()
            print("✓ OpenAI client initialized")
        except Exception as e:
            print(f"WARNING: OpenAI initialization failed: {str(e)}")
            print("Continuing without AI vision analysis...")
            use_ai_vision = False

    # ==========================================================================
    # STEP 5: Extract All Components
    # ==========================================================================

    print("\nExtracting components:")

    # Metadata
    print("  - Metadata...")
    metadata = _extract_metadata(soup)

    # Structure and content
    print("  - Page structure and content...")
    structure = _extract_structure(
        soup, final_url, page_dir,
        openai_client if use_ai_vision else None,
        model
    )

    # Tables
    print("  - Tables...")
    tables = _extract_tables(soup)
    print(f"    Found {len(tables)} tables")

    # Forms
    print("  - Forms...")
    forms = _extract_forms(soup)
    print(f"    Found {len(forms)} forms")

    # Links
    print("  - Links...")
    links = _extract_links(soup, final_url)
    print(f"    Found {len(links)} links")

    # Media
    print("  - Media elements...")
    media = _extract_media(soup, final_url)
    total_media = sum(len(v) for v in media.values())
    print(f"    Found {total_media} media elements")

    # ==========================================================================
    # STEP 6: Generate Markdown
    # ==========================================================================

    print("\nGenerating markdown report...")
    markdown_content = _generate_markdown(
        final_url, metadata, structure, tables, forms, links, media
    )

    # ==========================================================================
    # STEP 7: Save Output
    # ==========================================================================

    output_file = page_dir / "extracted_content.md"

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"\n{'='*70}")
        print(f"✓ EXTRACTION COMPLETE")
        print(f"{'='*70}")
        print(f"Output file: {output_file}")
        print(f"Total size: {len(markdown_content)} characters")
        print(f"Images saved: {len([b for b in structure if b['type'] == 'image'])}")

        return output_file

    except IOError as e:
        print(f"\nERROR: Failed to write output file: {str(e)}")
        return None


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main():
    """
    Example usage of web extraction pipeline
    """

    # Example URLs to extract
    test_urls = [
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        # Add your URLs here
    ]

    for url in test_urls:
        result = extract_webpage(url, use_ai_vision=True)
        if result:
            print(f"\n✓ Successfully extracted: {url}")
        else:
            print(f"\n✗ Failed to extract: {url}")


if __name__ == "__main__":
    main()