#!/usr/bin/env python3
"""
Web Scraping Script for n8n Integration

This script performs web scraping operations and can be executed
directly from n8n workflows using the Execute Command node.

Usage:
  python3 scrape_website.py --input '{"url": "https://example.com", "method": "basic"}'
  python3 scrape_website.py --input-file input.json --method structured
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

# Add shared libs to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'libs'))
from common import (
    handle_errors, setup_logging, validate_input, safe_json_loads,
    create_success_response, create_error_response, measure_execution_time
)
from config import get_config

# Setup logging
logger = setup_logging()
config = get_config()


@measure_execution_time
@handle_errors
def scrape_website(
    url: str,
    method: str = "basic",
    selectors: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    delay: float = 1.0,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Scrape website content using various methods."""
    
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as e:
        return create_error_response(
            f"Required packages not installed: {e}",
            "ImportError",
            {"required_packages": ["requests", "beautifulsoup4", "lxml"]}
        )
    
    logger.info(f"Starting web scraping for URL: {url} with method: {method}")
    
    # Default headers
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        # Make request with retries
        response = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} to fetch {url}")
                response = requests.get(
                    url,
                    headers=default_headers,
                    timeout=timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                break
            except requests.RequestException as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed: {e}")
        
        if response is None:
            return create_error_response(
                f"Failed to fetch URL after {max_retries} attempts: {last_error}",
                "RequestError",
                {"url": url, "attempts": max_retries}
            )
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        if method == "basic":
            return scrape_basic(soup, url, response)
        elif method == "structured":
            return scrape_structured(soup, url, response, selectors or {})
        elif method == "links":
            return scrape_links(soup, url, response)
        elif method == "images":
            return scrape_images(soup, url, response)
        elif method == "tables":
            return scrape_tables(soup, url, response)
        elif method == "forms":
            return scrape_forms(soup, url, response)
        else:
            return create_error_response(
                f"Unknown scraping method: {method}",
                "ValueError",
                {"available_methods": ["basic", "structured", "links", "images", "tables", "forms"]}
            )
    
    except Exception as e:
        logger.error(f"Error in web scraping: {e}")
        return create_error_response(
            f"Web scraping failed: {str(e)}",
            type(e).__name__
        )


def scrape_basic(soup: 'BeautifulSoup', url: str, response: 'requests.Response') -> Dict[str, Any]:
    """Basic scraping - extract common elements."""
    
    result = {
        "url": url,
        "status_code": response.status_code,
        "title": soup.title.string.strip() if soup.title else None,
        "meta": {},
        "headings": {},
        "text_content": soup.get_text(strip=True),
        "word_count": len(soup.get_text(strip=True).split()),
        "encoding": response.encoding
    }
    
    # Extract meta tags
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
        content = meta.get('content')
        if name and content:
            result["meta"][name] = content
    
    # Extract headings
    for i in range(1, 7):
        headings = soup.find_all(f'h{i}')
        if headings:
            result["headings"][f"h{i}"] = [h.get_text(strip=True) for h in headings]
    
    return create_success_response(result, {
        "method": "basic",
        "elements_found": {
            "meta_tags": len(result["meta"]),
            "headings": sum(len(h) for h in result["headings"].values())
        }
    })


def scrape_structured(soup: 'BeautifulSoup', url: str, response: 'requests.Response', selectors: Dict[str, str]) -> Dict[str, Any]:
    """Structured scraping using CSS selectors."""
    
    result = {
        "url": url,
        "status_code": response.status_code,
        "extracted_data": {}
    }
    
    for field_name, selector in selectors.items():
        try:
            elements = soup.select(selector)
            if elements:
                if len(elements) == 1:
                    # Single element
                    element = elements[0]
                    result["extracted_data"][field_name] = {
                        "text": element.get_text(strip=True),
                        "html": str(element),
                        "attributes": dict(element.attrs) if hasattr(element, 'attrs') else {}
                    }
                else:
                    # Multiple elements
                    result["extracted_data"][field_name] = [
                        {
                            "text": elem.get_text(strip=True),
                            "html": str(elem),
                            "attributes": dict(elem.attrs) if hasattr(elem, 'attrs') else {}
                        }
                        for elem in elements
                    ]
            else:
                result["extracted_data"][field_name] = None
        except Exception as e:
            logger.warning(f"Error extracting field '{field_name}' with selector '{selector}': {e}")
            result["extracted_data"][field_name] = {"error": str(e)}
    
    return create_success_response(result, {
        "method": "structured",
        "selectors_used": len(selectors),
        "fields_extracted": len([v for v in result["extracted_data"].values() if v is not None])
    })


def scrape_links(soup: 'BeautifulSoup', url: str, response: 'requests.Response') -> Dict[str, Any]:
    """Extract all links from the page."""
    
    links = []
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        absolute_url = urljoin(url, href)
        
        links.append({
            "text": link.get_text(strip=True),
            "href": href,
            "absolute_url": absolute_url,
            "is_external": not absolute_url.startswith(base_url),
            "title": link.get('title'),
            "target": link.get('target')
        })
    
    # Categorize links
    internal_links = [link for link in links if not link["is_external"]]
    external_links = [link for link in links if link["is_external"]]
    
    result = {
        "url": url,
        "status_code": response.status_code,
        "links": {
            "all": links,
            "internal": internal_links,
            "external": external_links
        },
        "summary": {
            "total_links": len(links),
            "internal_links": len(internal_links),
            "external_links": len(external_links)
        }
    }
    
    return create_success_response(result, {
        "method": "links",
        "links_found": len(links)
    })


def scrape_images(soup: 'BeautifulSoup', url: str, response: 'requests.Response') -> Dict[str, Any]:
    """Extract all images from the page."""
    
    images = []
    
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            absolute_url = urljoin(url, src)
            
            images.append({
                "src": src,
                "absolute_url": absolute_url,
                "alt": img.get('alt'),
                "title": img.get('title'),
                "width": img.get('width'),
                "height": img.get('height'),
                "class": img.get('class'),
                "id": img.get('id')
            })
    
    result = {
        "url": url,
        "status_code": response.status_code,
        "images": images,
        "summary": {
            "total_images": len(images),
            "images_with_alt": len([img for img in images if img["alt"]])
        }
    }
    
    return create_success_response(result, {
        "method": "images",
        "images_found": len(images)
    })


def scrape_tables(soup: 'BeautifulSoup', url: str, response: 'requests.Response') -> Dict[str, Any]:
    """Extract all tables from the page."""
    
    tables = []
    
    for i, table in enumerate(soup.find_all('table')):
        table_data = {
            "index": i,
            "headers": [],
            "rows": [],
            "summary": {}
        }
        
        # Extract headers
        header_row = table.find('tr')
        if header_row:
            headers = header_row.find_all(['th', 'td'])
            table_data["headers"] = [header.get_text(strip=True) for header in headers]
        
        # Extract rows
        rows = table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            table_data["rows"].append(row_data)
        
        table_data["summary"] = {
            "columns": len(table_data["headers"]),
            "rows": len(table_data["rows"])
        }
        
        tables.append(table_data)
    
    result = {
        "url": url,
        "status_code": response.status_code,
        "tables": tables,
        "summary": {
            "total_tables": len(tables),
            "total_rows": sum(table["summary"]["rows"] for table in tables)
        }
    }
    
    return create_success_response(result, {
        "method": "tables",
        "tables_found": len(tables)
    })


def scrape_forms(soup: 'BeautifulSoup', url: str, response: 'requests.Response') -> Dict[str, Any]:
    """Extract all forms from the page."""
    
    forms = []
    
    for i, form in enumerate(soup.find_all('form')):
        form_data = {
            "index": i,
            "action": form.get('action'),
            "method": form.get('method', 'GET').upper(),
            "enctype": form.get('enctype'),
            "inputs": [],
            "selects": [],
            "textareas": []
        }
        
        # Extract input fields
        for input_field in form.find_all('input'):
            form_data["inputs"].append({
                "type": input_field.get('type', 'text'),
                "name": input_field.get('name'),
                "id": input_field.get('id'),
                "value": input_field.get('value'),
                "placeholder": input_field.get('placeholder'),
                "required": input_field.has_attr('required')
            })
        
        # Extract select fields
        for select in form.find_all('select'):
            options = [{
                "value": option.get('value'),
                "text": option.get_text(strip=True),
                "selected": option.has_attr('selected')
            } for option in select.find_all('option')]
            
            form_data["selects"].append({
                "name": select.get('name'),
                "id": select.get('id'),
                "multiple": select.has_attr('multiple'),
                "required": select.has_attr('required'),
                "options": options
            })
        
        # Extract textarea fields
        for textarea in form.find_all('textarea'):
            form_data["textareas"].append({
                "name": textarea.get('name'),
                "id": textarea.get('id'),
                "placeholder": textarea.get('placeholder'),
                "required": textarea.has_attr('required'),
                "rows": textarea.get('rows'),
                "cols": textarea.get('cols'),
                "value": textarea.get_text()
            })
        
        forms.append(form_data)
    
    result = {
        "url": url,
        "status_code": response.status_code,
        "forms": forms,
        "summary": {
            "total_forms": len(forms),
            "total_inputs": sum(len(form["inputs"]) for form in forms),
            "total_selects": sum(len(form["selects"]) for form in forms),
            "total_textareas": sum(len(form["textareas"]) for form in forms)
        }
    }
    
    return create_success_response(result, {
        "method": "forms",
        "forms_found": len(forms)
    })


def main():
    """Main function for command-line usage."""
    
    parser = argparse.ArgumentParser(
        description="Scrape website content using various methods",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scraping
  python3 scrape_website.py --input '{"url": "https://example.com", "method": "basic"}'
  
  # Structured scraping with selectors
  python3 scrape_website.py --input '{"url": "https://example.com", "method": "structured", "selectors": {"title": "h1", "price": ".price"}}'
  
  # Extract all links
  python3 scrape_website.py --input '{"url": "https://example.com", "method": "links"}'
"""
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', help='JSON input data as string')
    input_group.add_argument('--input-file', help='Path to JSON input file')
    
    # Method options
    parser.add_argument(
        '--method', 
        default='basic',
        choices=['basic', 'structured', 'links', 'images', 'tables', 'forms'],
        help='Scraping method to use (default: basic)'
    )
    
    # Output options
    parser.add_argument('--output-file', help='Path to save output JSON file')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    
    args = parser.parse_args()
    
    try:
        # Parse input data
        if args.input:
            input_data = safe_json_loads(args.input)
        else:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        
        # Validate input structure
        schema = {
            "url": {"type": "string", "required": True},
            "method": {"type": "string", "required": False},
            "selectors": {"type": "object", "required": False},
            "headers": {"type": "object", "required": False},
            "timeout": {"type": "number", "required": False},
            "delay": {"type": "number", "required": False},
            "max_retries": {"type": "number", "required": False}
        }
        
        validate_input(input_data, schema)
        
        # Extract parameters
        url = input_data["url"]
        method = input_data.get("method", args.method)
        selectors = input_data.get("selectors")
        headers = input_data.get("headers")
        timeout = input_data.get("timeout", 30)
        delay = input_data.get("delay", 1.0)
        max_retries = input_data.get("max_retries", 3)
        
        # Perform scraping
        result = scrape_website(
            url=url,
            method=method,
            selectors=selectors,
            headers=headers,
            timeout=timeout,
            delay=delay,
            max_retries=max_retries
        )
        
        # Output result
        output_json = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)
        
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Results saved to {args.output_file}")
        else:
            print(output_json)
    
    except Exception as e:
        error_result = create_error_response(str(e), type(e).__name__)
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()