import requests
import json
import sys
from eth_account import Account
from eth_account.messages import encode_defunct

try:
    with open("wallet.json", "r") as archivo:
        mi_cartera = json.load(archivo)
        myDID = mi_cartera["did"]
        clavePrivada = mi_cartera["private_key"]
except FileNotFoundError:
    print("ERROR: No se encuentra 'wallet.json'.")
    print("Por favor, ejecuta primero 'python3 generar_did.py' para crear tu identidad.")
    sys.exit(1) # Salimos del programa porque no podemos hacer login sin claves

URL_SERVER = "http://localhost:5010"

def hacer_login():
    print(f"\nINICIANDO SESIÓN DESCENTRALIZADA")
    print(f"Intentando acceder como: {myDID}")

    print("\n1 - Pidiendo reto al servidor...")
    try:
        respuesta_reto = requests.get(f"{URL_SERVER}/api/auth/challenge")
        datos_reto = respuesta_reto.json()
        session_id = datos_reto["session_id"]
        nonce = datos_reto["nonce"]
        print(f"Reto recibido: {nonce}")
    except Exception as e:
        print(f"Error conectando al servidor: {e}")
        return

    print("2 - Firmando el reto con Clave Privada local...")
    mensaje_preparado = encode_defunct(text=nonce)
    firma = Account.sign_message(mensaje_preparado, private_key=clavePrivada)
    firma_texto = firma.signature.hex()
    print(f"Firma generada con éxito")

    print("3 - Preparando el paquete JSON para el backend...")
    paquete_json = {
        "session_id": session_id,
        "did": myDID,
        "signature": firma_texto,
        "presentation": {}
    }
    
    print("4 - Enviando al servidor para verificación...")
    respuesta_login = requests.post(f"{URL_SERVER}/api/auth/verify", json=paquete_json)
    
    print("\n--- RESPUESTA DEL SERVIDOR ---")
    print(f"Código HTTP: {respuesta_login.status_code}")
    print(json.dumps(respuesta_login.json(), indent=2))

if __name__ == "__main__":
    hacer_login()