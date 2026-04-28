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
from urllib import request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.settings import SETTINGS

processes = []
dead_reported = set()
FRONTEND_PORT = SETTINGS.frontend_port

def log(msg, level="INFO"):
    print(f"[{level}] {msg}", flush=True)

def signal_handler(sig, frame):
    log("Shutting down all services...", "INFO")
    for _, p in processes:
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
        processes.append((name or cmd, p))
        return p
    except Exception as e:
        log(f"Failed to start {name}: {str(e)}", "ERROR")
        return None


def is_port_open(port: int) -> bool:
    return wait_for_port(port, timeout=1)

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


def ensure_contract_artifact_exists() -> bool:
    contract_file = Path(SETTINGS.contract_file)
    if contract_file.exists():
        return True
    log(
        f"No se encontro artefacto de contrato: {SETTINGS.contract_file}. "
        "Despliega primero (local/testnet) o ajusta SSI_CONTRACT_FILE.",
        "ERROR",
    )
    return False


def _artifact_contract_address() -> str | None:
    contract_file = Path(SETTINGS.contract_file)
    if not contract_file.exists():
        return None
    try:
        payload = json.loads(contract_file.read_text(encoding="utf-8"))
    except Exception:
        return None
    address = payload.get("address")
    if isinstance(address, str) and address.startswith("0x") and len(address) == 42:
        return address
    return None


def _rpc_get_code(address: str) -> str | None:
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getCode",
        "params": [address, "latest"],
        "id": 1,
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        SETTINGS.blockchain_rpc_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    result = data.get("result")
    return result if isinstance(result, str) else None


def local_contract_is_live() -> bool:
    address = _artifact_contract_address()
    if not address:
        return False
    code = _rpc_get_code(address)
    return bool(code and code != "0x")


def write_frontend_variables() -> None:
    network_badge = (
        f"Hardhat: :{SETTINGS.blockchain_port}"
        if SETTINGS.blockchain_network == "local"
        else f"Network: {SETTINGS.blockchain_network}"
    )

    cfg = {
        "appTitle": "SSI v2 Control Center",
        "appSubtitle": "Emision, verificacion y revocacion de credenciales con validacion on-chain.",
        "badges": [
            f"Issuer: :{SETTINGS.issuer_port}",
            f"Verifier: :{SETTINGS.verifier_port}",
            network_badge,
            f"Frontend: :{SETTINGS.frontend_port}",
        ],
        "urls": {
            "issuerApiBaseUrl": SETTINGS.issuer_url,
            "verifierApiBaseUrl": SETTINGS.verifier_url,
            "apiBaseUrl": f"http://{SETTINGS.app_host}:8080",
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
        "walletSources": [],
    }
    content = "window.SSI_CONFIG = " + json.dumps(cfg, indent=2, ensure_ascii=True) + ";\n"
    frontend_cfg_path = Path("frontend") / "frontend.variables.js"
    with open(frontend_cfg_path, "w", encoding="utf-8") as f:
        f.write(content)
    log("frontend/frontend.variables.js generado desde settings", "OK")

def main():
    log("="*60, "INFO")
    log("SSI v2 - Automatic Startup Script", "INFO")
    log("="*60, "INFO")
    
    # Change to v2 directory
    v2_dir = Path(__file__).resolve().parent.parent
    os.chdir(v2_dir)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    write_frontend_variables()

    if SETTINGS.blockchain_network == "local":
        # Step 1: Start Blockchain Node
        log(f"\nStep 1: Starting Blockchain Node (port {SETTINGS.blockchain_port})", "INFO")
        if is_port_open(SETTINGS.blockchain_port):
            log("Blockchain node already running; reusing existing service", "OK")
        else:
            blockchain_cmd = "npm run node"
            run_async(blockchain_cmd, cwd="blockchain", name="Blockchain Node")

            # Wait for blockchain to be ready
            if not wait_for_port(SETTINGS.blockchain_port, timeout=15):
                log("Blockchain node failed to start", "ERROR")
                return 1
            log("Blockchain node is ready", "OK")

        # Step 2: Deploy and Bootstrap (only when needed)
        if local_contract_is_live():
            log("\nStep 2: Reusing existing local contract deployment", "INFO")
            log("Local contract is live; skipping deploy/bootstrap", "OK")
        else:
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
    else:
        log(
            f"\nStep 1: Using predeployed blockchain network '{SETTINGS.blockchain_network}' "
            f"via {SETTINGS.blockchain_rpc_url}",
            "INFO",
        )
        if not ensure_contract_artifact_exists():
            return 1
        log("Contract artifact found; skipping local blockchain startup/deploy", "OK")
    
    # Step 3: Start Issuer API
    log(f"\nStep 3: Starting Issuer API (port {SETTINGS.issuer_port})", "INFO")
    if is_port_open(SETTINGS.issuer_port):
        log("Issuer API already running; reusing existing service", "OK")
    else:
        issuer_cmd = f"python3 -m uvicorn services.issuer.app:app --host {SETTINGS.app_host} --port {SETTINGS.issuer_port}"
        run_async(issuer_cmd, name="Issuer API")

        if not wait_for_port(SETTINGS.issuer_port, timeout=10):
            log("Issuer API failed to start", "ERROR")
            return 1
        log("Issuer API is ready", "OK")
    
    # Step 4: Start Verifier API
    log(f"\nStep 4: Starting Verifier API (port {SETTINGS.verifier_port})", "INFO")
    if is_port_open(SETTINGS.verifier_port):
        log("Verifier API already running; reusing existing service", "OK")
    else:
        verifier_cmd = f"python3 -m uvicorn services.verifier.app:app --host {SETTINGS.app_host} --port {SETTINGS.verifier_port}"
        run_async(verifier_cmd, name="Verifier API")

        if not wait_for_port(SETTINGS.verifier_port, timeout=10):
            log("Verifier API failed to start", "ERROR")
            return 1
        log("Verifier API is ready", "OK")
    
    # Step 5: Start Frontend static server
    log(f"\nStep 5: Starting Frontend Server (port {FRONTEND_PORT})", "INFO")
    if is_port_open(FRONTEND_PORT):
        log("Frontend server already running; reusing existing service", "OK")
    else:
        frontend_cmd = "python3 frontend/frontend_server.py"
        run_async(frontend_cmd, name="Frontend Server")
        if not wait_for_port(FRONTEND_PORT, timeout=10):
            log("Frontend server failed to start", "ERROR")
            return 1
        log("Frontend server is ready", "OK")

    # Step 6: Open Frontend
    log("\nStep 6: Opening Frontend", "INFO")
    time.sleep(2)
    frontend_url = f"http://{SETTINGS.app_host}:{FRONTEND_PORT}/frontend_portal.html"
    open_frontend(frontend_url)
    
    # Print status
    log("\n" + "=" * 60, "INFO")
    log("ALL SERVICES RUNNING", "OK")
    log("=" * 60, "INFO")
    print(
        f"""
Services ready:
    - Blockchain RPC:   {SETTINGS.blockchain_rpc_url}
    - Contract file:    {SETTINGS.contract_file}
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
            for i, (name, p) in enumerate(processes):
                if p.poll() is not None:
                    key = (i, p.pid)
                    if key not in dead_reported:
                        dead_reported.add(key)
                        log(f"Process {i} ({name}) died with code {p.returncode}", "WARNING")
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    sys.exit(main())
