import json
import secrets
from eth_account import Account

def generate_issuer_wallet():
    # Generamos entropía extra segura
    priv_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(priv_key)
    
    # Construimos el DID del servidor
    did = f"did:ethr:{account.address}"
    
    wallet_data = {
        "entity": "Universidad (Backend Issuer)",
        "did": did,
        "private_key": priv_key,
        "address": account.address
    }
    
    # Lo guardamos en un archivo local que el main.py leerá luego
    with open("issuer_wallet.json", "w") as f:
        json.dump(wallet_data, f, indent=4)
        
    print("¡Identidad del Emisor (Servidor) creada con éxito!")
    print("DID del Servidor: {did}")


if __name__ == "__main__":
    generate_issuer_wallet()