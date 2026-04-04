# config.py
import os
from dotenv import load_dotenv

# The 'override=True' flag is critical to force the reload of your new PORT and PASS
load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Metasploit RPC Configuration - Pulling directly from .env
METASPLOIT_RPC_HOST = os.getenv("METASPLOIT_RPC_HOST", "127.0.0.1")
METASPLOIT_RPC_PORT = int(os.getenv("METASPLOIT_RPC_PORT", 55553))
METASPLOIT_RPC_PASS = os.getenv("METASPLOIT_RPC_PASS", "abhinav2004")

# Attack Machine Details
LHOST = os.getenv("LHOST", "127.0.0.1")
LPORT = int(os.getenv("LPORT", 4444))

# Debug print to confirm the right port is loaded in the console
print(f"[*] System connecting to Metasploit on Port: {METASPLOIT_RPC_PORT}")
