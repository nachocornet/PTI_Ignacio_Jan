#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BLOCKCHAIN_DIR = ROOT / "blockchain"
WALLET_FILE = ROOT / "deployments" / "runtime" / "sepolia_deployer_wallet.json"
DEPLOYMENT_FILE = BLOCKCHAIN_DIR / "deployments" / "sepolia" / "ssi_registry.json"
BOOTSTRAP_FILE = BLOCKCHAIN_DIR / "deployments" / "sepolia" / "bootstrap_issuer.json"


def _run(cmd: list[str], env: dict[str, str]) -> None:
    result = subprocess.run(cmd, cwd=str(BLOCKCHAIN_DIR), env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def _load_wallet_private_key() -> str | None:
    if not WALLET_FILE.exists():
        return None
    data = json.loads(WALLET_FILE.read_text(encoding="utf-8"))
    private_key = data.get("privateKey")
    return private_key if isinstance(private_key, str) and private_key.startswith("0x") else None


def main() -> int:
    env = os.environ.copy()
    env["SSI_BLOCKCHAIN_NETWORK"] = "sepolia"

    rpc = env.get("SEPOLIA_RPC_URL", "").strip()
    if not rpc:
        print("[error] Missing SEPOLIA_RPC_URL.")
        print("Set it first, e.g. export SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/<project_id>")
        return 2

    if not env.get("SEPOLIA_DEPLOYER_PRIVATE_KEY"):
        wallet_pk = _load_wallet_private_key()
        if wallet_pk:
            env["SEPOLIA_DEPLOYER_PRIVATE_KEY"] = wallet_pk
            print("[info] Using deployer private key from sepolia_deployer_wallet.json")
        else:
            print("[error] Missing SEPOLIA_DEPLOYER_PRIVATE_KEY and sepolia_deployer_wallet.json not usable.")
            return 3

    try:
        print("[step] Compiling contract...")
        _run(["npm", "run", "compile"], env)

        print("[step] Deploying to Sepolia...")
        _run(["npm", "run", "deploy:testnet"], env)

        print("[step] Bootstrapping issuer authorization...")
        _run(["npm", "run", "bootstrap:testnet"], env)
    except RuntimeError as exc:
        print(f"[error] {exc}")
        return 4

    if DEPLOYMENT_FILE.exists():
        deployment = json.loads(DEPLOYMENT_FILE.read_text(encoding="utf-8"))
        print("[ok] Contract deployed")
        print(f"[ok] Address: {deployment.get('address')}")
        print(f"[ok] TxHash: {deployment.get('deploymentTxHash')}")
    else:
        print("[warn] Deployment file not found after deploy.")

    if BOOTSTRAP_FILE.exists():
        print("[ok] Bootstrap metadata generated")
    else:
        print("[warn] Bootstrap output file not found.")

    print("[done] Sepolia deployment workflow completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
