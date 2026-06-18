import concurrent.futures
from urllib.parse import urlparse
import subprocess
import json
from ai_engine import ai_determine_attack_path
from intelligent_fuzzer import fuzz_endpoint

# FIXED: Added the missing run_command function definition
def run_command(command_list, timeout=300):
    """Executes a shell command and returns output or timeout message."""
    try:
        result = subprocess.run(command_list, capture_output=True, text=True, timeout=timeout)
        return result.stdout
    except subprocess.TimeoutExpired:
        return f"⚠️ Command timed out after {timeout} seconds."
    except Exception as e:
        return f"⚠️ Command failed: {e}"

def run_agentic_pipeline(target_url, recon_data, logger_callback):
    """Orchestrates the deep crawling and vulnerability scanning phase."""
    vuln_results = {"Raw_Findings": {}, "AI_Fuzzer": []}
    
    logger_callback("[+] AI Engine formulating aggressive attack strategy...")
    strategy = ai_determine_attack_path(recon_data, logger_callback)
    
    tasks = strategy.get("tasks", [])
    
    # 1. Run the Deep Crawler and Fuzzer
    logger_callback("[*] Launching Deep Crawler and Intelligent Fuzzer...")
    # This function now handles its own internal parameter mapping
    fuzzer_results = fuzz_endpoint(target_url, logger_callback)
    vuln_results["AI_Fuzzer"] = fuzzer_results

    # 2. Run traditional tools with increased 180s timeout
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for task in tasks:
            tool = task.get("tool")
            logger_callback(f"    -> AI Strategy Deployment: {tool}")
            
            if tool == "sqlmap":
                # Fast scan for Render free tier compatibility
                cmd = ["sqlmap", "-u", target_url, "--batch", "--forms", "--crawl=1", "--level=1"]
                futures["SQLMap"] = executor.submit(run_command, cmd, 20) 
            elif tool == "nmap_vuln":
                clean_target = target_url.replace("http://", "").replace("https://", "").split("/")[0]
                futures["Nmap"] = executor.submit(run_command, ["nmap", "--script", "vuln", clean_target], 20)

        # 3. Collect Results
        for tool_name, future in futures.items():
            vuln_results["Raw_Findings"][tool_name] = future.result()

    vuln_results["Extracted_Vulnerabilities"] = extract_vulnerabilities(str(vuln_results["Raw_Findings"]), vuln_results["AI_Fuzzer"])
    
    return vuln_results

VULN_TO_EXPLOIT = {
    "vsftpd 2.3.4": "exploit/unix/ftp/vsftpd_234_backdoor",
    "Apache Struts": "exploit/multi/http/struts2_exec",
    "SMBv1": "exploit/windows/smb/ms17_010_eternalblue"
}

def extract_vulnerabilities(raw_scan_results, fuzzer_results):
    """Maps raw string findings to specific Metasploit modules."""
    found_vulnerabilities = []
    for vuln, exploit in VULN_TO_EXPLOIT.items():
        if vuln.lower() in raw_scan_results.lower():
            found_vulnerabilities.append((vuln, exploit))
            
    # Link fuzzer successes to the Metasploit scanner module
    if any("Injection" in item.get("vulnerability", "") for item in fuzzer_results):
        found_vulnerabilities.append(("AI Detected Injection", "auxiliary/scanner/http/error_sql_injection"))
        
    return found_vulnerabilities
