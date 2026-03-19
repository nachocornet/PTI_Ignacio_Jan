# # Sistema de Autenticación Descentralizada (SSI) con DIDs

Este repositorio contiene la prueba de concepto (MVP) de un sistema de Autenticación mediante Identidad Auto-Soberana (SSI). Permite a los usuarios autenticarse en un servidor utilizando Identificadores Descentralizados (DIDs) y criptografía de curva elíptica (Ethereum), leyendo las credenciales desde un archivo de configuración local seguro.

## Arquitectura del Proyecto

El proyecto se divide en dos componentes principales:

1. **El Cliente / Holder (`client.py`, `generar_did.py` y `wallet.json`):**
   * `generar_did.py`: Script de inicialización. Genera identidades matemáticas desde cero (`did:ethr`) y almacena las claves localmente de forma estructurada en `wallet.json`.
   * `client.py`: Actúa como la "cartera" (Wallet) del usuario. Lee las credenciales de `wallet.json` en tiempo de ejecución y firma criptográficamente los retos del servidor.
2. **El Servidor / Verifier (`main.py`):**
   * Construido con FastAPI.
   * Emite retos (Nonces) aleatorios para mitigar ataques de repetición.
   * Resuelve los DIDs consultando la API pública de la W3C/DIF (`dev.uniresolver.io`).
   * Verifica matemáticamente las firmas entrantes validando que la dirección pública recuperada coincida con la del DID.

## Requisitos e Instalación

Para ejecutar este proyecto, es necesario disponer de Python 3.8+.

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DE_TU_REPO>
   cd did_backend
   ```

2. **Crear y activar el entorno virtual:**
   * Entornos basados en Unix (Linux / Mac / WSL):
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instalar dependencias:**
   Asegúrate de que el archivo `requirements.txt` contiene las siguientes especificaciones:
   ```text
   fastapi==0.110.0
   uvicorn==0.27.1
   pydantic>=2.9
   requests==2.31.0
   eth-account==0.11.0
   ```
   Instala los paquetes ejecutando:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración de Identidad y Seguridad

Antes de poder ejecutar el cliente y realizar el inicio de sesión, es necesario generar la identidad local del usuario.
Ejecuta el siguiente comando en la terminal:
```bash
python3 generar_did.py
```
Este proceso creará un archivo `wallet.json` en el directorio raíz que contendrá el DID público y la clave privada de Ethereum.

**Nota de Seguridad:** Es fundamental asegurar que el archivo `.gitignore` incluye la línea `wallet.json`. Esto previene la subida accidental de claves privadas al control de versiones.

## Ejecución del Flujo de Autenticación (Prueba End-to-End)

Para realizar la prueba completa, se requieren dos terminales independientes con el entorno virtual activado.

### 1. Inicializar el Servidor (Terminal 1)
Levanta el nodo verificador ejecutando:
```bash
uvicorn main:app --reload --port 5010
```
El servidor quedará a la escucha en `http://localhost:5010`.

### 2. Ejecutar el Cliente (Terminal 2)
Inicia la solicitud de autenticación ejecutando:
```bash
python3 client.py
```

**Secuencia de operaciones:**
1. El cliente lee `wallet.json` y solicita un reto al servidor (`GET /api/auth/challenge`).
2. El servidor devuelve un `session_id` temporal y un `nonce`.
3. El cliente firma el `nonce` con su clave privada y envía el paquete de datos (`POST /api/auth/verify`).
4. El servidor verifica matemáticamente la firma. Si el resultado es válido, devuelve un código HTTP 200 confirmando el acceso.

## Próximos Pasos (Sprint 3)
* **Verifiable Credentials (VCs):** Implementar la emisión y verificación de credenciales estructuradas que se adjuntarán a la presentación.
* **Persistencia de Datos:** Migrar la gestión de sesiones en memoria de FastAPI hacia una base de datos relacional ligera (SQLite) para un control de acceso más robusto.