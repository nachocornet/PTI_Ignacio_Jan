window.SSI_CONFIG = {
  "appTitle": "SSI v2 Control Center",
  "appSubtitle": "Emision, verificacion y revocacion de credenciales con validacion on-chain.",
  "badges": [
    "Issuer: :5010",
    "Verifier: :5011",
    "Hardhat: :8545",
    "Frontend: :8080"
  ],
  "urls": {
    "issuer": "http://127.0.0.1:5010",
    "verifier": "http://127.0.0.1:5011"
  },
  "defaults": {
    "dni": "12345678A",
    "refreshMs": 15000
  },
  "guideSteps": [
    {
      "title": "Paso 1",
      "text": "Carga wallet local del holder para firmar la VP."
    },
    {
      "title": "Paso 2",
      "text": "Emite VC con Issuer y registra hash en blockchain."
    },
    {
      "title": "Paso 3",
      "text": "Firma VP con la clave privada del holder."
    },
    {
      "title": "Paso 4",
      "text": "Verifica y revoca para comprobar estado on-chain."
    }
  ],
  "walletSources": []
};
