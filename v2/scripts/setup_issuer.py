import json
import secrets
import sys
from pathlib import Path

from eth_account import Account

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.settings import SETTINGS

def generate_issuer_wallet():
    priv_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(priv_key)
    did = f"did:ethr:{account.address}"
    
    wallet_data = {
        "entity": "Ministerio de Identidad",
        "did": did,
        "private_key": priv_key,
        "address": account.address
    }
    
    with open(SETTINGS.issuer_wallet_file, "w") as f:
        json.dump(wallet_data, f, indent=4)
    print(f"Identidad del Emisor creada: {did}")

if __name__ == "__main__":
    generate_issuer_wallet()