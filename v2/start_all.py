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

processes = []
FRONTEND_PORT = int(os.getenv("SSI_FRONTEND_PORT", "8080"))

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
            result = sock.connect_ex(('127.0.0.1', port))
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

def main():
    log("="*60, "INFO")
    log("SSI v2 - Automatic Startup Script", "INFO")
    log("="*60, "INFO")
    
    # Change to v2 directory
    v2_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(v2_dir)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Step 1: Start Blockchain Node
    log("\nStep 1: Starting Blockchain Node (port 8545)", "INFO")
    blockchain_cmd = "npm run node"
    run_async(blockchain_cmd, cwd="blockchain", name="Blockchain Node")
    
    # Wait for blockchain to be ready
    if not wait_for_port(8545, timeout=15):
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
    log("\nStep 3: Starting Issuer API (port 5010)", "INFO")
    issuer_cmd = "python3 -m uvicorn issuer:app --host 127.0.0.1 --port 5010"
    run_async(issuer_cmd, name="Issuer API")
    
    if not wait_for_port(5010, timeout=10):
        log("Issuer API failed to start", "ERROR")
        return 1
    log("Issuer API is ready", "OK")
    
    # Step 4: Start Verifier API
    log("\nStep 4: Starting Verifier API (port 5011)", "INFO")
    verifier_cmd = "python3 -m uvicorn verifier:app --host 127.0.0.1 --port 5011"
    run_async(verifier_cmd, name="Verifier API")
    
    if not wait_for_port(5011, timeout=10):
        log("Verifier API failed to start", "ERROR")
        return 1
    log("Verifier API is ready", "OK")
    
    # Step 5: Start Frontend static server
    log(f"\nStep 5: Starting Frontend Server (port {FRONTEND_PORT})", "INFO")
    frontend_cmd = f"python3 -m http.server {FRONTEND_PORT} --bind 127.0.0.1"
    run_async(frontend_cmd, name="Frontend Server")
    if not wait_for_port(FRONTEND_PORT, timeout=10):
        log("Frontend server failed to start", "ERROR")
        return 1
    log("Frontend server is ready", "OK")

    # Step 6: Open Frontend
    log("\nStep 6: Opening Frontend", "INFO")
    time.sleep(2)
    frontend_url = f"http://127.0.0.1:{FRONTEND_PORT}/frontend.html"
    open_frontend(frontend_url)
    
    # Print status
    log("\n" + "=" * 60, "INFO")
    log("ALL SERVICES RUNNING", "OK")
    log("=" * 60, "INFO")
    print(
        f"""
Services ready:
  - Blockchain Node:  http://127.0.0.1:8545
  - Issuer API:       http://127.0.0.1:5010
  - Verifier API:     http://127.0.0.1:5011
  - Frontend Server:  http://127.0.0.1:{FRONTEND_PORT}
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
