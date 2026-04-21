#!/usr/bin/env python3
"""
Script para levantar TODO el sistema SSI v2 automáticamente
Ejecuta en paralelo todos los servicios necesarios
"""
import os
import sys
import time
import subprocess
import webbrowser
import signal
import json

from settings import SETTINGS

processes = []
FRONTEND_PORT = SETTINGS.frontend_port

def log(msg, level="INFO"):
    print(f"[{level}] {msg}", flush=True)

def signal_handler(sig, frame):
    log("Shutting down all services...", "INFO")
    for p in processes:
        try:
            p.terminate()
        except:
            pass
    sys.exit(0)

def run_async(cmd, cwd=None, name=""):
    """Run command asynchronously and track it"""
    try:
        log(f"Starting {name}...", "INFO")
        p = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        processes.append(p)
        return p
    except Exception as e:
        log(f"Failed to start {name}: {str(e)}", "ERROR")
        return None

def wait_for_port(port, timeout=30):
    """Wait for a service to be ready on a specific port"""
    import socket
    import time
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((SETTINGS.app_host, port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(0.5)
    return False

def open_frontend(url):
    """Open frontend URL in default browser"""
    try:
        webbrowser.open(url)
        log(f"Frontend opened at {url}", "OK")
    except Exception as e:
        log(f"Could not open frontend: {str(e)}", "WARNING")
        log(f"Open manually: {url}", "INFO")


def write_frontend_variables() -> None:
    cfg = {
        "appTitle": "SSI v2 Control Center",
        "appSubtitle": "Emision, verificacion y revocacion de credenciales con validacion on-chain.",
        "badges": [
            f"Issuer: :{SETTINGS.issuer_port}",
            f"Verifier: :{SETTINGS.verifier_port}",
            f"Hardhat: :{SETTINGS.blockchain_port}",
            f"Frontend: :{SETTINGS.frontend_port}",
        ],
        "urls": {
            "issuer": SETTINGS.issuer_url,
            "verifier": SETTINGS.verifier_url,
        },
        "defaults": {
            "dni": "12345678A",
            "refreshMs": 15000,
        },
        "guideSteps": [
            {
                "title": "Paso 1",
                "text": "Carga wallet local del holder para firmar la VP.",
            },
            {
                "title": "Paso 2",
                "text": "Emite VC con Issuer y registra hash en blockchain.",
            },
            {
                "title": "Paso 3",
                "text": "Firma VP con la clave privada del holder.",
            },
            {
                "title": "Paso 4",
                "text": "Verifica y revoca para comprobar estado on-chain.",
            },
        ],
        "walletSources": [
            f"/{SETTINGS.holder_wallet_file}",
            f"./{SETTINGS.holder_wallet_file}",
            SETTINGS.holder_wallet_file,
        ],
    }
    content = "window.SSI_CONFIG = " + json.dumps(cfg, indent=2, ensure_ascii=True) + ";\n"
    with open("frontend.variables.js", "w", encoding="utf-8") as f:
        f.write(content)
    log("frontend.variables.js generado desde settings", "OK")

def main():
    log("="*60, "INFO")
    log("SSI v2 - Automatic Startup Script", "INFO")
    log("="*60, "INFO")
    
    # Change to v2 directory
    v2_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(v2_dir)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    write_frontend_variables()

    # Step 1: Start Blockchain Node
    log(f"\nStep 1: Starting Blockchain Node (port {SETTINGS.blockchain_port})", "INFO")
    blockchain_cmd = "npm run node"
    run_async(blockchain_cmd, cwd="blockchain", name="Blockchain Node")
    
    # Wait for blockchain to be ready
    if not wait_for_port(SETTINGS.blockchain_port, timeout=15):
        log("Blockchain node failed to start", "ERROR")
        return 1
    log("Blockchain node is ready", "OK")
    
    # Step 2: Deploy and Bootstrap
    log("\nStep 2: Deploying contract and bootstrapping issuer", "INFO")
    time.sleep(2)  # Give blockchain a moment
    
    deploy_result = subprocess.run(
        "npm run deploy:local && npm run bootstrap:local",
        shell=True,
        cwd="blockchain",
        capture_output=True,
        text=True
    )
    
    if deploy_result.returncode != 0:
        log(f"Deploy failed: {deploy_result.stderr}", "ERROR")
        return 1
    log("Contract deployed and issuer bootstrapped", "OK")
    
    # Step 3: Start Issuer API
    log(f"\nStep 3: Starting Issuer API (port {SETTINGS.issuer_port})", "INFO")
    issuer_cmd = f"python3 -m uvicorn issuer:app --host {SETTINGS.app_host} --port {SETTINGS.issuer_port}"
    run_async(issuer_cmd, name="Issuer API")
    
    if not wait_for_port(SETTINGS.issuer_port, timeout=10):
        log("Issuer API failed to start", "ERROR")
        return 1
    log("Issuer API is ready", "OK")
    
    # Step 4: Start Verifier API
    log(f"\nStep 4: Starting Verifier API (port {SETTINGS.verifier_port})", "INFO")
    verifier_cmd = f"python3 -m uvicorn verifier:app --host {SETTINGS.app_host} --port {SETTINGS.verifier_port}"
    run_async(verifier_cmd, name="Verifier API")
    
    if not wait_for_port(SETTINGS.verifier_port, timeout=10):
        log("Verifier API failed to start", "ERROR")
        return 1
    log("Verifier API is ready", "OK")
    
    # Step 5: Start Frontend static server
    log(f"\nStep 5: Starting Frontend Server (port {FRONTEND_PORT})", "INFO")
    frontend_cmd = f"python3 -m http.server {FRONTEND_PORT} --bind {SETTINGS.app_host}"
    run_async(frontend_cmd, name="Frontend Server")
    if not wait_for_port(FRONTEND_PORT, timeout=10):
        log("Frontend server failed to start", "ERROR")
        return 1
    log("Frontend server is ready", "OK")

    # Step 6: Open Frontend
    log("\nStep 6: Opening Frontend", "INFO")
    time.sleep(2)
    frontend_url = f"http://{SETTINGS.app_host}:{FRONTEND_PORT}/frontend.html"
    open_frontend(frontend_url)
    
    # Print status
    log("\n" + "=" * 60, "INFO")
    log("ALL SERVICES RUNNING", "OK")
    log("=" * 60, "INFO")
    print(
        f"""
Services ready:
    - Blockchain Node:  {SETTINGS.blockchain_rpc_url}
    - Issuer API:       {SETTINGS.issuer_url}
    - Verifier API:     {SETTINGS.verifier_url}
    - Frontend Server:  {SETTINGS.frontend_url}
  - Frontend App:     {frontend_url}

Press CTRL+C to stop all services.
"""
    )
    log("="*60, "INFO")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
            # Check if any process died
            for i, p in enumerate(processes):
                if p.poll() is not None:
                    log(f"Process {i} died with code {p.returncode}", "WARNING")
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    sys.exit(main())
