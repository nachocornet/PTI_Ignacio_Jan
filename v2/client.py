import requests
import json
import sys
from eth_account import Account
from eth_account.messages import encode_defunct

def main():
    try:
        with open("wallet.json", "r") as f:
            wallet = json.load(f)
            my_did = wallet["did"]
            my_key = wallet["private_key"]
    except FileNotFoundError:
        print("Error: No se encontro wallet.json")
        sys.exit(1)

    # 1. Obtencion de Credencial (VM1)
    print("Solicitando VC al Ministerio...")
    payload_vc = {"did_ciudadano": my_did, "numero_dni": "12345678A"}
    response_vc = requests.post("http://localhost:5010/api/credentials/issue_dni", json=payload_vc)
    
    if response_vc.status_code != 200:
        print(f"Error en emision: {response_vc.text}")
        return
    
    vc = response_vc.json()["credential"]
    print("VC recibida correctamente.")

    # 2. Generacion de Presentacion (VP)
    print("Generando VP firmada...")
    vp = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiablePresentation"],
        "verifiableCredential": vc
    }
    
    vp_canonical = json.dumps(vp, separators=(',', ':'), sort_keys=True)
    msg = encode_defunct(text=vp_canonical)
    signature = Account.sign_message(msg, private_key=my_key).signature.hex()
    
    vp["proof"] = {"proofValue": signature}

    # 3. Verificacion (VM3)
    print("Enviando VP al verificador...")
    response_verify = requests.post("http://localhost:5011/api/verify_presentation", json={"vp": vp})
    print(f"Resultado: {response_verify.json()}")

if __name__ == "__main__":
    main()