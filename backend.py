from flask import Flask, Response, request, send_from_directory
from flask_cors import CORS
import json
import threading
import queue
import time
import os

# Import the existing pentest modules
try:
    from recon import run_recon
    from orchestrator import run_agentic_pipeline
    from exploitation import run_exploit
    from ai_engine import ai_chain_vulnerabilities
    from reporting import generate_security_report
except Exception as e:
    import traceback
    print(f"Error importing modules: {e}")
    traceback.print_exc()
    run_agentic_pipeline = None # Define as None to avoid NameError later
    run_recon = None
    run_exploit = None
    ai_chain_vulnerabilities = None
    generate_security_report = None

app = Flask(__name__)
# Explicitly allow the origin to avoid CORS issues with EventSource
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/')
def index():
    return {"status": "AutoPent API is running. Use the frontend to interact with this service."}


def generate_scan_events(target_url):
    """
    Generator that uses a queue to stream real-time logs and phase updates.
    Includes a heartbeat to keep the connection alive during long tasks.
    """
    log_queue = queue.Queue()

    def stream_logger(text, type="default", phase=None, phaseState=None):
        log_queue.put({
            "text": text,
            "type": type,
            "phase": phase,
            "phaseState": phaseState
        })

    def run_pentest_thread():
        try:
            stream_logger(f"[*] Initialising AI Agentic Engine → {target_url}", "info")
            
            # PHASE 1: RECON
            stream_logger("[+] PHASE 1 · Zero-API Reconnaissance …", "phase", 1, "active")
            if run_recon is None:
                raise Exception("Module 'recon' failed to load. Check server logs.")
            recon_data = run_recon(target_url)
            ip = recon_data.get('IP_Resolution', {}).get('ip', 'Unknown')
            stream_logger(f"    IP Resolved: {ip}")
            stream_logger("", "default", 1, "done")

            # PHASE 2: FUZZING
            stream_logger("[+] PHASE 2 · Gemini AI Orchestrator + Fuzzing …", "phase", 2, "active")
            if run_agentic_pipeline is None:
                raise Exception("Module 'orchestrator' failed to load. Check server logs.")
            vuln_data = run_agentic_pipeline(target_url, recon_data, stream_logger)
            num_vulns = len(vuln_data.get('AI_Fuzzer', []))
            stream_logger(f"    {num_vulns} dynamic vulnerabilities found.")
            stream_logger("", "default", 2, "done")

            # PHASE 3: CHAINING
            stream_logger("[+] PHASE 3 · AI Vulnerability Chaining …", "phase", 3, "active")
            ai_chained_report = ai_chain_vulnerabilities(vuln_data, stream_logger)
            stream_logger("    Exploit chaining logic mapped.")
            stream_logger("", "default", 3, "done")

            # PHASE 4: EXPLOIT
            stream_logger("[+] PHASE 4 · Metasploit RPC Exploitation …", "phase", 4, "active")
            exploit_data = run_exploit(target_url, recon_data, vuln_data)
            msg = exploit_data.get('message', 'Completed')
            stream_logger(f"    Status: {msg}", "success" if "Success" in msg else "default")
            stream_logger("", "default", 4, "done")

            # PHASE 5: REPORT
            stream_logger("[+] PHASE 5 · Compiling DevSecOps PDF Report …", "phase", 5, "active")
            report_path = generate_security_report(target_url, recon_data, vuln_data, exploit_data, ai_chained_report)
            
            if report_path:
                stream_logger(f"✅  Report saved → {report_path}", "success", 5, "done")
            else:
                stream_logger("❌  Failed to generate report.", "error", 5, "error")

        except Exception as e:
            print(f"Pentest Thread Error: {e}")
            stream_logger(f"[!] System Error: {str(e)}", "error")
        finally:
            # Signal the end of the stream
            log_queue.put(None)

    # Start the pentest in a background thread
    threading.Thread(target=run_pentest_thread, daemon=True).start()

    # Send an initial padding to bypass aggressive proxy buffering (some load balancers buffer the first 1KB)
    padding = ": " + (" " * 1024) + "\n\n"
    yield padding

    # Yield items from the queue as SSE data
    while True:
        try:
            # Wait with a timeout to allow heartbeat
            item = log_queue.get(timeout=5)
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"
        except queue.Empty:
            # Heartbeat to keep connection alive and bypass proxy buffers
            yield f"data: {json.dumps({'text': '', 'type': 'heartbeat'})}\n\n"

@app.route('/api/scan')
def scan():
    target_url = request.args.get('url')
    if not target_url:
        return {"error": "No URL provided"}, 400
    
    # SSE headers are critical for EventSource stability
    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Connection': 'keep-alive'
    }
    
    return Response(generate_scan_events(target_url), headers=headers)

if __name__ == '__main__':
    # Running on 127.0.0.1 explicitly
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
