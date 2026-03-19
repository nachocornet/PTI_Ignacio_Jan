from eth_account import Account
import secrets
import json

print("Generando nueva identidad descentralizada...")

# 1. Generar semilla aleatoria segura
priv_key_hex = "0x" + secrets.token_hex(32)

# 2. Crear cuenta de Ethereum
cuenta = Account.from_key(priv_key_hex)

# 3. Construir el DID
myDID = f"did:ethr:sepolia:{cuenta.address}"

# 4. Crear la estructura de nuestra "cartera" (Wallet)
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