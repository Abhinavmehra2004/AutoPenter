import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from ai_engine import ai_generate_payloads

def get_all_links(url, logger_callback=None):
    """Crawls the target page to find all internal endpoints and forms."""
    endpoints = {url: {"method": "GET", "params": []}}
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "AutoPent/1.0"})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Find all Links with Query Parameters
        for a in soup.find_all('a', href=True):
            full_url = urljoin(url, a['href'])
            if urlparse(url).netloc == urlparse(full_url).netloc:
                parsed = urlparse(full_url)
                if parsed.query:
                    params = [p.split('=')[0] for p in parsed.query.split('&')]
                    base_url = full_url.split('?')[0]
                    endpoints[base_url] = {"method": "GET", "params": params}
                elif full_url not in endpoints:
                    endpoints[full_url] = {"method": "GET", "params": []}

        # 2. Find all Forms
        for form in soup.find_all('form'):
            action = form.get('action')
            method = form.get('method', 'get').upper()
            form_url = urljoin(url, action)
            inputs = [i.get('name') for i in form.find_all(['input', 'textarea']) if i.get('name')]
            endpoints[form_url] = {"method": method, "params": inputs}

    except Exception as e:
        if logger_callback:
            logger_callback(f"Crawler Error: {e}")
    return endpoints

def fuzz_endpoint(target_root, logger_callback=None):
    """Orchestrates a deep fuzzing campaign across all discovered endpoints."""
    all_findings = []
    discovered_surface = get_all_links(target_root, logger_callback)
    
    if logger_callback:
        logger_callback(f"[*] Crawler discovered {len(discovered_surface)} unique attack vectors.")

    for url, info in discovered_surface.items():
        method = info['method']
        params = info['params']
        
        if not params:
            # Add a default 'test' parameter if none found to trigger payloads
            params = ['id']

        # Get AI-generated payloads specific to these parameters
        payloads = ai_generate_payloads(url, params, logger_callback)
        
        for payload in payloads:
            try:
                test_params = {p: payload for p in params}
                if method == "GET":
                    response = requests.get(url, params=test_params, timeout=7)
                else:
                    response = requests.post(url, data=test_params, timeout=7)
                
                # Check for SQL/XSS signatures in response
                res_text = response.text.lower()
                if any(err in res_text for err in ["sql syntax", "mysql", "sqlite", "pdoexception", "system.data.sql"]):
                    all_findings.append({
                        "url": url,
                        "parameter": str(params),
                        "vulnerability": "Confirmed SQL Injection",
                        "payload": payload
                    })
                elif payload in response.text: # Simple XSS check
                     all_findings.append({
                        "url": url,
                        "vulnerability": "Potential XSS (Reflected Payload)",
                        "payload": payload
                    })
            except:
                continue
    return all_findings
