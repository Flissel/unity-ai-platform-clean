#!/usr/bin/env python3
"""
API Integration Script for n8n Integration

This script provides a unified interface for making API calls to various external services
and can be executed directly from n8n workflows using the Execute Command node.

Usage:
  python3 api_client.py --input '{"url": "https://api.example.com/data", "method": "GET"}'
  python3 api_client.py --input-file request.json --operation rest_call
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import time
from urllib.parse import urljoin, urlparse, parse_qs
import base64
import hashlib
import hmac
from datetime import datetime, timezone

# Add shared libs to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'libs'))
from common import (
    handle_errors, setup_logging, validate_input, safe_json_loads,
    create_success_response, create_error_response, measure_execution_time,
    safe_read_file, safe_write_file
)
from config import get_config

# Setup logging
logger = setup_logging()
config = get_config()


@measure_execution_time
@handle_errors
def make_api_call(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict[str, Any], str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    auth: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    verify_ssl: bool = True,
    follow_redirects: bool = True,
    operation: str = "rest_call"
) -> Dict[str, Any]:
    """Make API calls with various authentication and configuration options."""
    
    logger.info(f"Making {method} request to {url}")
    
    if operation == "rest_call":
        return make_rest_call(url, method, headers, params, data, json_data, auth, timeout, verify_ssl, follow_redirects)
    elif operation == "graphql":
        return make_graphql_call(url, json_data, headers, auth, timeout, verify_ssl)
    elif operation == "webhook":
        return send_webhook(url, method, headers, data, json_data, auth, timeout, verify_ssl)
    elif operation == "oauth_request":
        return make_oauth_request(url, method, headers, params, data, json_data, auth, timeout, verify_ssl)
    elif operation == "soap":
        return make_soap_call(url, data, headers, auth, timeout, verify_ssl)
    elif operation == "batch_requests":
        return make_batch_requests(data, timeout, verify_ssl)
    elif operation == "file_upload":
        return upload_file(url, data, headers, auth, timeout, verify_ssl)
    elif operation == "file_download":
        return download_file(url, headers, auth, timeout, verify_ssl, params)
    else:
        return create_error_response(
            f"Unknown operation: {operation}",
            "ValueError",
            {"available_operations": [
                "rest_call", "graphql", "webhook", "oauth_request", "soap", 
                "batch_requests", "file_upload", "file_download"
            ]}
        )


def make_rest_call(
    url: str, method: str, headers: Optional[Dict[str, str]], 
    params: Optional[Dict[str, Any]], data: Optional[Union[Dict[str, Any], str]], 
    json_data: Optional[Dict[str, Any]], auth: Optional[Dict[str, str]], 
    timeout: int, verify_ssl: bool, follow_redirects: bool
) -> Dict[str, Any]:
    """Make a REST API call."""
    
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        # Create session with retry strategy
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Prepare headers
        request_headers = headers or {}
        if 'User-Agent' not in request_headers:
            request_headers['User-Agent'] = 'n8n-python-api-client/1.0'
        
        # Handle authentication
        auth_obj = None
        if auth:
            auth_type = auth.get('type', 'basic')
            
            if auth_type == 'basic':
                auth_obj = (auth['username'], auth['password'])
            elif auth_type == 'bearer':
                request_headers['Authorization'] = f"Bearer {auth['token']}"
            elif auth_type == 'api_key':
                key_location = auth.get('location', 'header')
                key_name = auth.get('key_name', 'X-API-Key')
                
                if key_location == 'header':
                    request_headers[key_name] = auth['api_key']
                elif key_location == 'query':
                    params = params or {}
                    params[key_name] = auth['api_key']
            elif auth_type == 'oauth2':
                request_headers['Authorization'] = f"Bearer {auth['access_token']}"
            elif auth_type == 'custom':
                # Custom headers from auth config
                custom_headers = auth.get('headers', {})
                request_headers.update(custom_headers)
        
        # Make request
        start_time = time.time()
        
        response = session.request(
            method=method.upper(),
            url=url,
            headers=request_headers,
            params=params,
            data=data,
            json=json_data,
            auth=auth_obj,
            timeout=timeout,
            verify=verify_ssl,
            allow_redirects=follow_redirects
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Parse response
        response_data = None
        content_type = response.headers.get('content-type', '').lower()
        
        try:
            if 'application/json' in content_type:
                response_data = response.json()
            elif 'text/' in content_type or 'application/xml' in content_type:
                response_data = response.text
            else:
                # Binary data - encode as base64
                response_data = base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            logger.warning(f"Could not parse response body: {e}")
            response_data = response.text if response.text else None
        
        result = {
            "request": {
                "url": url,
                "method": method.upper(),
                "headers": dict(request_headers),
                "params": params,
                "data": data if isinstance(data, str) else None,
                "json": json_data
            },
            "response": {
                "status_code": response.status_code,
                "status_text": response.reason,
                "headers": dict(response.headers),
                "data": response_data,
                "size_bytes": len(response.content),
                "response_time_seconds": response_time,
                "encoding": response.encoding,
                "url": response.url  # Final URL after redirects
            },
            "success": response.ok,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if response.ok:
            return create_success_response(result, {
                "operation": "rest_call",
                "status_code": response.status_code,
                "response_time": response_time
            })
        else:
            return create_error_response(
                f"HTTP {response.status_code}: {response.reason}",
                "HTTPError",
                result
            )
    
    except ImportError:
        return create_error_response(
            "REST API calls require requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error making REST call: {e}")
        return create_error_response(
            f"REST API call failed: {str(e)}",
            type(e).__name__
        )


def make_graphql_call(
    url: str, query_data: Optional[Dict[str, Any]], headers: Optional[Dict[str, str]], 
    auth: Optional[Dict[str, str]], timeout: int, verify_ssl: bool
) -> Dict[str, Any]:
    """Make a GraphQL API call."""
    
    try:
        import requests
        
        if not query_data:
            return create_error_response(
                "GraphQL query data is required",
                "ValueError",
                {"required_fields": ["query", "variables (optional)", "operationName (optional)"]}
            )
        
        # Prepare headers
        request_headers = headers or {}
        request_headers['Content-Type'] = 'application/json'
        
        # Handle authentication (similar to REST)
        if auth:
            auth_type = auth.get('type', 'bearer')
            if auth_type == 'bearer':
                request_headers['Authorization'] = f"Bearer {auth['token']}"
            elif auth_type == 'api_key':
                key_name = auth.get('key_name', 'X-API-Key')
                request_headers[key_name] = auth['api_key']
        
        # Prepare GraphQL payload
        payload = {
            "query": query_data.get("query"),
            "variables": query_data.get("variables", {}),
            "operationName": query_data.get("operationName")
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            headers=request_headers,
            timeout=timeout,
            verify=verify_ssl
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Parse GraphQL response
        try:
            response_data = response.json()
        except Exception:
            response_data = {"errors": [{"message": "Invalid JSON response"}]}
        
        result = {
            "request": {
                "url": url,
                "query": payload.get("query"),
                "variables": payload.get("variables"),
                "operation_name": payload.get("operationName")
            },
            "response": {
                "status_code": response.status_code,
                "data": response_data.get("data"),
                "errors": response_data.get("errors"),
                "extensions": response_data.get("extensions"),
                "response_time_seconds": response_time
            },
            "success": response.ok and not response_data.get("errors"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if response.ok and not response_data.get("errors"):
            return create_success_response(result, {
                "operation": "graphql",
                "has_data": bool(response_data.get("data")),
                "response_time": response_time
            })
        else:
            error_msg = "GraphQL errors" if response_data.get("errors") else f"HTTP {response.status_code}"
            return create_error_response(error_msg, "GraphQLError", result)
    
    except ImportError:
        return create_error_response(
            "GraphQL calls require requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error making GraphQL call: {e}")
        return create_error_response(
            f"GraphQL call failed: {str(e)}",
            type(e).__name__
        )


def send_webhook(
    url: str, method: str, headers: Optional[Dict[str, str]], 
    data: Optional[Union[Dict[str, Any], str]], json_data: Optional[Dict[str, Any]], 
    auth: Optional[Dict[str, str]], timeout: int, verify_ssl: bool
) -> Dict[str, Any]:
    """Send webhook with optional signature verification."""
    
    try:
        import requests
        
        # Prepare headers
        request_headers = headers or {}
        
        # Add webhook-specific headers
        request_headers['User-Agent'] = request_headers.get('User-Agent', 'n8n-webhook-client/1.0')
        
        # Handle webhook signatures
        if auth and auth.get('type') == 'webhook_signature':
            secret = auth.get('secret')
            algorithm = auth.get('algorithm', 'sha256')
            header_name = auth.get('header_name', 'X-Hub-Signature-256')
            
            if secret:
                # Prepare payload for signing
                if json_data:
                    payload = json.dumps(json_data, separators=(',', ':'))
                    request_headers['Content-Type'] = 'application/json'
                else:
                    payload = data or ''
                
                # Generate signature
                if algorithm == 'sha256':
                    signature = hmac.new(
                        secret.encode('utf-8'),
                        payload.encode('utf-8') if isinstance(payload, str) else payload,
                        hashlib.sha256
                    ).hexdigest()
                    request_headers[header_name] = f"sha256={signature}"
                elif algorithm == 'sha1':
                    signature = hmac.new(
                        secret.encode('utf-8'),
                        payload.encode('utf-8') if isinstance(payload, str) else payload,
                        hashlib.sha1
                    ).hexdigest()
                    request_headers[header_name] = f"sha1={signature}"
        
        # Add timestamp if requested
        if auth and auth.get('include_timestamp'):
            request_headers['X-Timestamp'] = str(int(time.time()))
        
        start_time = time.time()
        
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=request_headers,
            data=data,
            json=json_data,
            timeout=timeout,
            verify=verify_ssl
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        result = {
            "webhook": {
                "url": url,
                "method": method.upper(),
                "headers_sent": dict(request_headers),
                "payload_size": len(str(data or json_data or '')),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "response": {
                "status_code": response.status_code,
                "status_text": response.reason,
                "headers": dict(response.headers),
                "body": response.text,
                "response_time_seconds": response_time
            },
            "success": response.ok
        }
        
        if response.ok:
            return create_success_response(result, {
                "operation": "webhook",
                "delivered": True,
                "response_time": response_time
            })
        else:
            return create_error_response(
                f"Webhook delivery failed: HTTP {response.status_code}",
                "WebhookError",
                result
            )
    
    except ImportError:
        return create_error_response(
            "Webhook sending requires requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error sending webhook: {e}")
        return create_error_response(
            f"Webhook sending failed: {str(e)}",
            type(e).__name__
        )


def make_oauth_request(
    url: str, method: str, headers: Optional[Dict[str, str]], 
    params: Optional[Dict[str, Any]], data: Optional[Union[Dict[str, Any], str]], 
    json_data: Optional[Dict[str, Any]], auth: Optional[Dict[str, str]], 
    timeout: int, verify_ssl: bool
) -> Dict[str, Any]:
    """Make OAuth-authenticated request."""
    
    try:
        import requests
        from requests_oauthlib import OAuth1, OAuth2Session
        
        if not auth or auth.get('type') != 'oauth':
            return create_error_response(
                "OAuth authentication configuration required",
                "ValueError",
                {"required_auth_type": "oauth"}
            )
        
        oauth_version = auth.get('version', '2.0')
        
        if oauth_version == '1.0':
            # OAuth 1.0
            oauth = OAuth1(
                auth['client_key'],
                client_secret=auth['client_secret'],
                resource_owner_key=auth.get('resource_owner_key'),
                resource_owner_secret=auth.get('resource_owner_secret'),
                signature_method=auth.get('signature_method', 'HMAC-SHA1')
            )
            
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                auth=oauth,
                timeout=timeout,
                verify=verify_ssl
            )
        
        elif oauth_version == '2.0':
            # OAuth 2.0
            oauth = OAuth2Session(
                auth['client_id'],
                token=auth.get('token')
            )
            
            response = oauth.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                timeout=timeout,
                verify=verify_ssl
            )
        
        else:
            return create_error_response(
                f"Unsupported OAuth version: {oauth_version}",
                "ValueError",
                {"supported_versions": ["1.0", "2.0"]}
            )
        
        # Parse response
        try:
            response_data = response.json()
        except Exception:
            response_data = response.text
        
        result = {
            "request": {
                "url": url,
                "method": method.upper(),
                "oauth_version": oauth_version
            },
            "response": {
                "status_code": response.status_code,
                "data": response_data,
                "headers": dict(response.headers)
            },
            "success": response.ok
        }
        
        if response.ok:
            return create_success_response(result, {
                "operation": "oauth_request",
                "oauth_version": oauth_version
            })
        else:
            return create_error_response(
                f"OAuth request failed: HTTP {response.status_code}",
                "OAuthError",
                result
            )
    
    except ImportError:
        return create_error_response(
            "OAuth requests require requests-oauthlib library",
            "ImportError",
            {"required_packages": ["requests-oauthlib"]}
        )
    except Exception as e:
        logger.error(f"Error making OAuth request: {e}")
        return create_error_response(
            f"OAuth request failed: {str(e)}",
            type(e).__name__
        )


def make_soap_call(
    url: str, soap_body: Optional[Union[Dict[str, Any], str]], 
    headers: Optional[Dict[str, str]], auth: Optional[Dict[str, str]], 
    timeout: int, verify_ssl: bool
) -> Dict[str, Any]:
    """Make SOAP API call."""
    
    try:
        import requests
        from xml.etree import ElementTree as ET
        
        # Prepare SOAP envelope
        if isinstance(soap_body, dict):
            # Convert dict to SOAP XML (basic implementation)
            soap_envelope = f"""
            <?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    {dict_to_xml(soap_body)}
                </soap:Body>
            </soap:Envelope>
            """.strip()
        else:
            soap_envelope = soap_body or ""
        
        # Prepare headers
        request_headers = headers or {}
        request_headers['Content-Type'] = 'text/xml; charset=utf-8'
        request_headers['SOAPAction'] = request_headers.get('SOAPAction', '""')
        
        # Handle authentication
        auth_obj = None
        if auth and auth.get('type') == 'basic':
            auth_obj = (auth['username'], auth['password'])
        
        response = requests.post(
            url,
            data=soap_envelope,
            headers=request_headers,
            auth=auth_obj,
            timeout=timeout,
            verify=verify_ssl
        )
        
        # Parse SOAP response
        try:
            root = ET.fromstring(response.text)
            # Extract SOAP body (simplified)
            soap_body_response = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            response_data = ET.tostring(soap_body_response, encoding='unicode') if soap_body_response is not None else response.text
        except Exception:
            response_data = response.text
        
        result = {
            "request": {
                "url": url,
                "soap_envelope": soap_envelope,
                "headers": dict(request_headers)
            },
            "response": {
                "status_code": response.status_code,
                "soap_response": response_data,
                "raw_response": response.text,
                "headers": dict(response.headers)
            },
            "success": response.ok
        }
        
        if response.ok:
            return create_success_response(result, {
                "operation": "soap",
                "status_code": response.status_code
            })
        else:
            return create_error_response(
                f"SOAP call failed: HTTP {response.status_code}",
                "SOAPError",
                result
            )
    
    except ImportError:
        return create_error_response(
            "SOAP calls require requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error making SOAP call: {e}")
        return create_error_response(
            f"SOAP call failed: {str(e)}",
            type(e).__name__
        )


def dict_to_xml(data: Dict[str, Any], root_name: str = "data") -> str:
    """Convert dictionary to XML (basic implementation)."""
    
    def _dict_to_xml(d, parent_name):
        xml_str = f"<{parent_name}>"
        for key, value in d.items():
            if isinstance(value, dict):
                xml_str += _dict_to_xml(value, key)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        xml_str += _dict_to_xml(item, key)
                    else:
                        xml_str += f"<{key}>{item}</{key}>"
            else:
                xml_str += f"<{key}>{value}</{key}>"
        xml_str += f"</{parent_name}>"
        return xml_str
    
    return _dict_to_xml(data, root_name)


def make_batch_requests(
    requests_data: List[Dict[str, Any]], timeout: int, verify_ssl: bool
) -> Dict[str, Any]:
    """Make multiple API requests in batch."""
    
    try:
        import requests
        import concurrent.futures
        from threading import Lock
        
        if not isinstance(requests_data, list):
            return create_error_response(
                "Batch requests data must be a list",
                "ValueError",
                {"expected_format": "list of request objects"}
            )
        
        results = []
        results_lock = Lock()
        
        def make_single_request(req_data, index):
            try:
                # Extract request parameters
                url = req_data.get('url')
                method = req_data.get('method', 'GET')
                headers = req_data.get('headers')
                params = req_data.get('params')
                data = req_data.get('data')
                json_data = req_data.get('json')
                
                start_time = time.time()
                
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json_data,
                    timeout=timeout,
                    verify=verify_ssl
                )
                
                end_time = time.time()
                
                # Parse response
                try:
                    response_data = response.json()
                except Exception:
                    response_data = response.text
                
                result = {
                    "index": index,
                    "request": req_data,
                    "response": {
                        "status_code": response.status_code,
                        "data": response_data,
                        "headers": dict(response.headers),
                        "response_time_seconds": end_time - start_time
                    },
                    "success": response.ok
                }
                
                with results_lock:
                    results.append(result)
                
            except Exception as e:
                error_result = {
                    "index": index,
                    "request": req_data,
                    "error": str(e),
                    "success": False
                }
                
                with results_lock:
                    results.append(error_result)
        
        # Execute requests in parallel
        max_workers = min(len(requests_data), 10)  # Limit concurrent requests
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(make_single_request, req_data, i)
                for i, req_data in enumerate(requests_data)
            ]
            
            # Wait for all requests to complete
            concurrent.futures.wait(futures)
        
        # Sort results by index
        results.sort(key=lambda x: x['index'])
        
        # Calculate summary statistics
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = len(results) - successful_requests
        
        summary = {
            "total_requests": len(requests_data),
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / len(requests_data) if requests_data else 0,
            "results": results
        }
        
        return create_success_response(summary, {
            "operation": "batch_requests",
            "total_requests": len(requests_data),
            "success_rate": summary["success_rate"]
        })
    
    except ImportError:
        return create_error_response(
            "Batch requests require requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error making batch requests: {e}")
        return create_error_response(
            f"Batch requests failed: {str(e)}",
            type(e).__name__
        )


def upload_file(
    url: str, file_data: Dict[str, Any], headers: Optional[Dict[str, str]], 
    auth: Optional[Dict[str, str]], timeout: int, verify_ssl: bool
) -> Dict[str, Any]:
    """Upload file to API endpoint."""
    
    try:
        import requests
        
        file_path = file_data.get('file_path')
        field_name = file_data.get('field_name', 'file')
        additional_fields = file_data.get('fields', {})
        
        if not file_path or not os.path.exists(file_path):
            return create_error_response(
                f"File not found: {file_path}",
                "FileNotFoundError",
                {"file_path": file_path}
            )
        
        # Prepare files for upload
        with open(file_path, 'rb') as f:
            files = {field_name: (os.path.basename(file_path), f, 'application/octet-stream')}
            
            # Add additional form fields
            data = additional_fields
            
            # Handle authentication
            auth_obj = None
            request_headers = headers or {}
            
            if auth:
                auth_type = auth.get('type', 'basic')
                if auth_type == 'basic':
                    auth_obj = (auth['username'], auth['password'])
                elif auth_type == 'bearer':
                    request_headers['Authorization'] = f"Bearer {auth['token']}"
            
            start_time = time.time()
            
            response = requests.post(
                url,
                files=files,
                data=data,
                headers=request_headers,
                auth=auth_obj,
                timeout=timeout,
                verify=verify_ssl
            )
            
            end_time = time.time()
        
        # Parse response
        try:
            response_data = response.json()
        except Exception:
            response_data = response.text
        
        file_size = os.path.getsize(file_path)
        
        result = {
            "upload": {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size_bytes": file_size,
                "field_name": field_name,
                "additional_fields": additional_fields,
                "upload_time_seconds": end_time - start_time
            },
            "response": {
                "status_code": response.status_code,
                "data": response_data,
                "headers": dict(response.headers)
            },
            "success": response.ok
        }
        
        if response.ok:
            return create_success_response(result, {
                "operation": "file_upload",
                "file_uploaded": True,
                "file_size": file_size
            })
        else:
            return create_error_response(
                f"File upload failed: HTTP {response.status_code}",
                "UploadError",
                result
            )
    
    except ImportError:
        return create_error_response(
            "File upload requires requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return create_error_response(
            f"File upload failed: {str(e)}",
            type(e).__name__
        )


def download_file(
    url: str, headers: Optional[Dict[str, str]], auth: Optional[Dict[str, str]], 
    timeout: int, verify_ssl: bool, options: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Download file from API endpoint."""
    
    try:
        import requests
        
        output_path = options.get('output_path') if options else None
        chunk_size = options.get('chunk_size', 8192) if options else 8192
        
        # Handle authentication
        auth_obj = None
        request_headers = headers or {}
        
        if auth:
            auth_type = auth.get('type', 'basic')
            if auth_type == 'basic':
                auth_obj = (auth['username'], auth['password'])
            elif auth_type == 'bearer':
                request_headers['Authorization'] = f"Bearer {auth['token']}"
        
        start_time = time.time()
        
        response = requests.get(
            url,
            headers=request_headers,
            auth=auth_obj,
            timeout=timeout,
            verify=verify_ssl,
            stream=True
        )
        
        if not response.ok:
            return create_error_response(
                f"Download failed: HTTP {response.status_code}",
                "DownloadError",
                {"status_code": response.status_code, "url": url}
            )
        
        # Determine output path
        if not output_path:
            # Extract filename from URL or Content-Disposition header
            content_disposition = response.headers.get('content-disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            else:
                filename = os.path.basename(urlparse(url).path) or 'downloaded_file'
            
            output_path = os.path.join(os.getcwd(), filename)
        
        # Download file
        total_size = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        end_time = time.time()
        download_time = end_time - start_time
        
        result = {
            "download": {
                "url": url,
                "output_path": output_path,
                "file_size_bytes": total_size,
                "download_time_seconds": download_time,
                "download_speed_mbps": (total_size / (1024 * 1024)) / download_time if download_time > 0 else 0
            },
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_type": response.headers.get('content-type')
            },
            "success": True
        }
        
        return create_success_response(result, {
            "operation": "file_download",
            "file_downloaded": True,
            "file_size": total_size
        })
    
    except ImportError:
        return create_error_response(
            "File download requires requests library",
            "ImportError",
            {"required_packages": ["requests"]}
        )
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return create_error_response(
            f"File download failed: {str(e)}",
            type(e).__name__
        )


def main():
    """Main function for command-line usage."""
    
    parser = argparse.ArgumentParser(
        description="Make API calls with various authentication and configuration options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple GET request
  python3 api_client.py --input '{"url": "https://api.example.com/data", "method": "GET"}'
  
  # POST with JSON data
  python3 api_client.py --input '{"url": "https://api.example.com/users", "method": "POST", "json_data": {"name": "John"}, "headers": {"Content-Type": "application/json"}}'
  
  # API with authentication
  python3 api_client.py --input '{"url": "https://api.example.com/protected", "auth": {"type": "bearer", "token": "your-token"}}'
  
  # GraphQL query
  python3 api_client.py --input '{"url": "https://api.example.com/graphql", "operation": "graphql", "json_data": {"query": "{ users { id name } }"}}'
"""
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', help='JSON input data as string')
    input_group.add_argument('--input-file', help='Path to JSON input file')
    
    # Operation options
    parser.add_argument(
        '--operation', 
        default='rest_call',
        choices=[
            'rest_call', 'graphql', 'webhook', 'oauth_request', 'soap', 
            'batch_requests', 'file_upload', 'file_download'
        ],
        help='API operation type (default: rest_call)'
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
            "headers": {"type": "object", "required": False},
            "params": {"type": "object", "required": False},
            "data": {"type": ["object", "string"], "required": False},
            "json_data": {"type": "object", "required": False},
            "auth": {"type": "object", "required": False},
            "timeout": {"type": "number", "required": False},
            "verify_ssl": {"type": "boolean", "required": False},
            "follow_redirects": {"type": "boolean", "required": False},
            "operation": {"type": "string", "required": False}
        }
        
        validate_input(input_data, schema)
        
        # Extract parameters
        url = input_data["url"]
        method = input_data.get("method", "GET")
        headers = input_data.get("headers")
        params = input_data.get("params")
        data = input_data.get("data")
        json_data = input_data.get("json_data")
        auth = input_data.get("auth")
        timeout = input_data.get("timeout", 30)
        verify_ssl = input_data.get("verify_ssl", True)
        follow_redirects = input_data.get("follow_redirects", True)
        operation = input_data.get("operation", args.operation)
        
        # Make API call
        result = make_api_call(
            url=url,
            method=method,
            headers=headers,
            params=params,
            data=data,
            json_data=json_data,
            auth=auth,
            timeout=timeout,
            verify_ssl=verify_ssl,
            follow_redirects=follow_redirects,
            operation=operation
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