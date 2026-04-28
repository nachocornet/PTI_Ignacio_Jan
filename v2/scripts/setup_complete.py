#!/usr/bin/env python3
"""
Setup automatizado para SSI v2
Ejecuta todos los pasos necesarios para levantar el sistema completo
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.settings import SETTINGS

def log(msg, level="INFO"):
    print(f"[{level}] {msg}", flush=True)

def run_cmd(cmd, cwd=None, check=True):
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0 and check:
            log(f"Command failed: {cmd}", "ERROR")
            log(f"Stderr: {result.stderr}", "ERROR")
            return False
        return True
    except Exception as e:
        log(f"Exception: {str(e)}", "ERROR")
        return False

def setup_node_modules():
    log("Installing blockchain dependencies...")
    if not run_cmd("npm install", cwd="blockchain"):
        return False
    log("Blockchain dependencies installed", "OK")
    return True

def compile_contract():
    log("Compiling Solidity contract...")
    if not run_cmd("npm run compile", cwd="blockchain"):
        return False
    log("Contract compiled", "OK")
    return True

def setup_python_env():
    log("Checking Python dependencies...")
    if not run_cmd("pip install -r config/requirements.txt"):
        return False
    log("Python dependencies installed", "OK")
    return True

def generate_issuer_wallet():
    log("Generating issuer wallet...")
    if not os.path.exists(SETTINGS.issuer_wallet_file):
        if not run_cmd("python3 scripts/setup_issuer.py"):
            return False
        log("Issuer wallet generated", "OK")
    else:
        log("Issuer wallet already exists", "INFO")
    return True

def seed_database():
    log("Seeding database...")
    if not run_cmd("python3 scripts/seed_db.py"):
        return False
    log("Database seeded", "OK")
    return True

def generate_holder_wallet():
    log("Generating holder wallet...")
    if not os.path.exists(SETTINGS.holder_wallet_file):
        if not run_cmd("python3 scripts/generar_did.py"):
            return False
        log("Holder wallet generated", "OK")
    else:
        log("Holder wallet already exists", "INFO")
    return True

def check_prerequisites():
    log("Checking prerequisites...")
    
    # Check Node
    if not run_cmd("node --version", check=False):
        log("Node.js not found", "ERROR")
        return False
    
    # Check Python
    if not run_cmd("python3 --version", check=False):
        log("Python3 not found", "ERROR")
        return False
    
    log("All prerequisites satisfied", "OK")
    return True

def print_next_steps():
    log("\n" + "="*60, "INFO")
    log("SETUP COMPLETE - NEXT STEPS", "INFO")
    log("="*60, "INFO")
    print(f"""
Startup options:

Option A) Local blockchain (auto deploy each run)
    export SSI_BLOCKCHAIN_NETWORK=local
    python3 scripts/start_all.py

Option B) Predeployed testnet contract (recommended once Sepolia is deployed)
    export SSI_BLOCKCHAIN_NETWORK=sepolia
    export SSI_CONTRACT_FILE=deployments/blockchain_contract.sepolia.json
    export SEPOLIA_RPC_URL=<your_sepolia_rpc>
    python3 scripts/start_all.py

Manual mode (separate terminals) remains available, but scripts/start_all.py is now network-aware.
""")
    log("="*60, "INFO")

def main():
    log("Starting SSI v2 Complete Setup")
    
    # Change to v2 directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    steps = [
        ("Prerequisites", check_prerequisites),
        ("Python Dependencies", setup_python_env),
        ("Node Dependencies", setup_node_modules),
        ("Solidity Compilation", compile_contract),
        ("Issuer Wallet", generate_issuer_wallet),
        ("Database", seed_database),
        ("Holder Wallet", generate_holder_wallet),
    ]
    
    for name, func in steps:
        if not func():
            log(f"Setup failed at: {name}", "ERROR")
            return 1
    
    print_next_steps()
    return 0

if __name__ == "__main__":
    sys.exit(main())
