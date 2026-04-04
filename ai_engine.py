import json
import os
import time
from google import genai
from google.genai import types
import config

def get_ai_client():
    """Forces the use of the new project key from config.py to bypass system caching."""
    if config.GEMINI_API_KEY:
        try:
            # Explicitly passing the key to ensure the new project is used
            return genai.Client(api_key=config.GEMINI_API_KEY)
        except Exception as e:
            print(f"[*] AI Client Initialization Error: {e}")
    return None

def call_gemini_safe(prompt, is_json=False, model_name='gemini-2.5-flash', logger_callback=None):
    """Handles API calls with built-in retry logic and safety delays for quota protection."""
    client = get_ai_client()
    if not client:
        return None

    # Mandatory 3-second breather to prevent 429 Resource Exhausted errors
    time.sleep(3) 

    for attempt in range(3):
        try:
            config_params = {}
            if is_json:
                config_params['response_mime_type'] = "application/json"

            # Utilizing Gemini 2.5 Flash for high-speed agentic reasoning
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config_params)
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                wait = (attempt + 1) * 30
                msg = f"[*] Quota hit. Retrying in {wait}s..."
                if logger_callback:
                    logger_callback(msg, "warning")
                else:
                    print(msg)
                time.sleep(wait)
            else:
                msg = f"[*] Gemini API Error: {error_msg}"
                if logger_callback:
                    logger_callback(msg, "error")
                else:
                    print(msg)
                break
    return None

def ai_determine_attack_path(recon_data, logger_callback=None):
    """The AI analyzes recon data and creates an aggressive attack strategy."""
    prompt = f"""
    You are an elite, highly aggressive DevSecOps orchestrator. Analyze this reconnaissance data:
    {json.dumps(recon_data)}
    
    Determine the next attack phases. Available tools: ['nmap_vuln', 'sqlmap', 'intelligent_api_fuzzer'].
    
    CRITICAL INSTRUCTION: You MUST deploy 'sqlmap' and 'intelligent_api_fuzzer' on every scan. 
    Focus on finding hidden parameters and form actions.
    
    Respond strictly in JSON format with an array of tasks. 
    Example: {{"tasks": [{{"tool": "intelligent_api_fuzzer", "reason": "Deep crawling required"}}]}}
    """
    
    result = call_gemini_safe(prompt, is_json=True, logger_callback=logger_callback)
    if result:
        try:
            return json.loads(result)
        except:
            pass
    return {"tasks": [{"tool": "intelligent_api_fuzzer", "reason": "Default safety trigger"}]}

def ai_generate_payloads(target_url, expected_params, logger_callback=None):
    """The AI writes context-aware payloads specifically for the discovered parameters."""
    prompt = f"""
    Target URL: {target_url}
    Parameters Found: {expected_params}
    
    Write 5 highly advanced, context-specific payloads for SQL Injection and XSS for this exact endpoint. 
    Do not use generic payloads.
    Respond strictly with a JSON array of strings.
    """
    
    result = call_gemini_safe(prompt, is_json=True, logger_callback=logger_callback)
    if result:
        try:
            return json.loads(result)
        except:
            pass
    return ["' OR '1'='1", "<script>alert(1)</script>", "' UNION SELECT NULL--"]

def ai_chain_vulnerabilities(all_findings, logger_callback=None):
    """The AI attempts to link isolated findings into a full exploit chain (e.g., LFI to RCE)."""
    if not all_findings.get("AI_Fuzzer") and not all_findings.get("Raw_Findings"):
        return "No vulnerabilities discovered by the crawler or scanners to analyze."

    prompt = f"""
    You are an expert exploit developer. Analyze these findings:
    {json.dumps(all_findings, indent=2)}

    1. Can these be chained together to achieve Remote Code Execution (RCE) or Data Exfiltration? 
    2. Provide the exact step-by-step logic required to execute the chain using the discovered URLs.
    3. Provide the secure code patches to fix the root causes.
    Format your response in clean Markdown.
    """
    
    result = call_gemini_safe(prompt, logger_callback=logger_callback)
    return result if result else "⚠️ AI Remediation failed due to persistent quota exhaustion."
