import requests
import socket
import whois  # Ensure you ran: pip install python-whois
import dns.resolver
import concurrent.futures
from urllib.parse import urlparse
import re
import time

def clean_domain(target_url):
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    return urlparse(target_url).hostname

def get_ip_address(domain):
    try:
        if domain in ['localhost', '127.0.0.1']:
            return {"ip": "127.0.0.1", "status": "skipped_localhost"}
        ip = socket.gethostbyname(domain)
        return {"ip": ip, "status": "success"}
    except Exception as e:
        return {"ip": None, "error": str(e)}

def get_whois_info(domain):
    """Correctly fetches WHOIS data for live domains."""
    try:
        if domain in ['127.0.0.1', 'localhost'] or re.match(r'^\d{1,3}(\.\d{1,3}){3}$', domain):
            return {"error": "WHOIS skipped for IP/localhost."}
        # FIXED: Use whois.whois() for python-whois compatibility
        info = whois.whois(domain)
        return {k: str(v) for k, v in info.items()}
    except Exception as e:
        return {"error": f"WHOIS error: {str(e)}"}

def get_dns_records(domain):
    records = {}
    for record_type in ['A', 'MX', 'NS', 'TXT']:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            records[record_type] = [r.to_text() for r in answers]
        except Exception:
            records[record_type] = []
    return records

def get_subdomains_crtsh(domain):
    """Fetches subdomains with increased timeout for live sites."""
    if domain in ['127.0.0.1', 'localhost']:
        return {"error": "Subdomain enum skipped for IP."}
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            data = response.json()
            subdomains = list(set([entry['name_value'].strip() for entry in data]))
            return {"subdomains_found": len(subdomains), "list": subdomains[:20]}
        return {"error": "crt.sh returned no data."}
    except Exception:
        return {"error": "Subdomain enum timed out."}

def run_recon(target_url):
    domain = clean_domain(target_url)
    ip_data = get_ip_address(domain)
    ip = ip_data.get("ip")
    recon_results = {"Target": target_url, "Domain": domain, "IP_Resolution": ip_data}

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        f_headers = executor.submit(lambda url: dict(requests.get(url, timeout=5).headers), target_url)
        f_whois = executor.submit(get_whois_info, domain)
        f_dns = executor.submit(get_dns_records, domain)
        f_sub = executor.submit(get_subdomains_crtsh, domain)
        
        recon_results["Headers"] = f_headers.result()
        recon_results["WHOIS"] = f_whois.result()
        recon_results["DNS"] = f_dns.result()
        recon_results["Subdomains"] = f_sub.result()

    return recon_results
