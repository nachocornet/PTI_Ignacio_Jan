from eth_account import Account
import secrets
import json

priv_key_hex = "0x" + secrets.token_hex(32)
cuenta = Account.from_key(priv_key_hex)

# El formato debe ser did:ethr:DIRECCION para que coincida con el Verificador
myDID = f"did:ethr:{cuenta.address}"

wallet_data = {
    "did": myDID,
    "private_key": priv_key_hex
}

with open("wallet.json", "w") as archivo:
    json.dump(wallet_data, archivo, indent=4)

print(f"Identidad creada: {myDID}")