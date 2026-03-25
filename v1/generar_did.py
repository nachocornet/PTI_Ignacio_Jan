from eth_account import Account
import secrets
import json

print("Generando nueva identidad descentralizada...")

priv_key_hex = "0x" + secrets.token_hex(32)

cuenta = Account.from_key(priv_key_hex)

myDID = f"did:ethr:sepolia:{cuenta.address}"
wallet_data = {
    "did": myDID,
    "private_key": priv_key_hex
}

# 5. Guardarlo en un archivo JSON local
with open("wallet.json", "w") as archivo:
    json.dump(wallet_data, archivo, indent=4)

print(f"¡Identidad creada con éxito!")
print(f"DID público: {myDID}")
print(f"Tus claves se han guardado localmente en el archivo 'wallet.json'.")