import reporting

# Mock data to simulate a real scan
url = "http://test-site.com"
recon = {"IP": "127.0.0.1", "Server": "Apache"}
vulns = {
    "AI_Fuzzer": [{"vulnerability": "SQLi", "payload": "' OR 1=1 --", "url": url}],
    "Raw_Findings": {"Nmap": "Port 80 open"}
}
exploits = {
    "target_ip": "127.0.0.1",
    "success": True,
    "exploits_attempted": [{"module": "test/exploit", "status": "Success"}]
}

# The EXACT problematic string that caused the previous crash
problematic_ai_text = """
### Database Security Analysis
* Avoid **`GRANT ALL PRIVILEGES`** or `GRANT` statements on *`*.*`*.
* Ensure that the `db_user` does not have access to the `mysql.user` table.

```sql
-- Remediation Script
REVOKE ALL PRIVILEGES ON *.* FROM 'user'@'localhost';
GRANT SELECT, INSERT ON my_db.* TO 'user'@'localhost';
```
"""

print("[*] Testing PDF Report Generation...")
result = reporting.generate_security_report(url, recon, vulns, exploits, problematic_ai_text)

if result:
    print(f"✅ Success! Report generated at: {result}")
else:
    print("❌ Failed to generate report.")
