#!/usr/bin/env python3
"""
Example web scraping script for UnityAI Python Worker.
"""

import json
import sys
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import time


def scrape_url(url: str, selector: Optional[str] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Scrape content from a URL."""
    
    try:
        # Default headers to avoid being blocked
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        if headers:
            default_headers.update(headers)
        
        # Make request
        response = requests.get(url, headers=default_headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        result = {
            "url": url,
            "status_code": response.status_code,
            "title": soup.title.string if soup.title else None,
            "content_length": len(response.content)
        }
        
        if selector:
            # Extract specific elements using CSS selector
            elements = soup.select(selector)
            result["selected_elements"] = [
                {
                    "text": elem.get_text(strip=True),
                    "html": str(elem),
                    "attributes": dict(elem.attrs) if elem.attrs else {}
                }
                for elem in elements[:50]  # Limit to first 50 elements
            ]
        else:
            # Extract common elements
            result["content"] = {
                "headings": {
                    "h1": [h.get_text(strip=True) for h in soup.find_all('h1')],
                    "h2": [h.get_text(strip=True) for h in soup.find_all('h2')],
                    "h3": [h.get_text(strip=True) for h in soup.find_all('h3')]
                },
                "paragraphs": [p.get_text(strip=True) for p in soup.find_all('p')[:20]],  # First 20 paragraphs
                "links": [
                    {
                        "text": a.get_text(strip=True),
                        "href": a.get('href'),
                        "title": a.get('title')
                    }
                    for a in soup.find_all('a', href=True)[:50]  # First 50 links
                ],
                "images": [
                    {
                        "src": img.get('src'),
                        "alt": img.get('alt'),
                        "title": img.get('title')
                    }
                    for img in soup.find_all('img', src=True)[:20]  # First 20 images
                ]
            }
        
        return result
    
    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Scraping failed: {str(e)}"}


def scrape_multiple_urls(urls: List[str], delay: float = 1.0, **kwargs) -> List[Dict[str, Any]]:
    """Scrape multiple URLs with delay between requests."""
    
    results = []
    
    for i, url in enumerate(urls):
        if i > 0:  # Add delay between requests
            time.sleep(delay)
        
        result = scrape_url(url, **kwargs)
        result["index"] = i
        results.append(result)
    
    return results


def extract_structured_data(url: str, schema: Dict[str, str]) -> Dict[str, Any]:
    """Extract structured data based on a schema."""
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        extracted = {}
        
        for field, selector in schema.items():
            elements = soup.select(selector)
            if elements:
                if len(elements) == 1:
                    extracted[field] = elements[0].get_text(strip=True)
                else:
                    extracted[field] = [elem.get_text(strip=True) for elem in elements]
            else:
                extracted[field] = None
        
        return {
            "url": url,
            "extracted_data": extracted,
            "success": True
        }
    
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python web_scraper.py <url> [selector]"}))
        sys.exit(1)
    
    try:
        url = sys.argv[1]
        selector = sys.argv[2] if len(sys.argv) > 2 else None
        
        result = scrape_url(url, selector)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()