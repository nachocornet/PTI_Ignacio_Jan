from eth_account import Account
import secrets
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.settings import SETTINGS

priv_key_hex = "0x" + secrets.token_hex(32)
cuenta = Account.from_key(priv_key_hex)

# El formato debe ser did:ethr:DIRECCION para que coincida con el Verificador
myDID = f"did:ethr:{cuenta.address}"

wallet_data = {
    "did": myDID,
    "private_key": priv_key_hex
}

with open(SETTINGS.holder_wallet_file, "w") as archivo:
    json.dump(wallet_data, archivo, indent=4)

print(f"Identidad creada: {myDID}")