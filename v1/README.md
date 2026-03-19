# 🛡️ Sistema de Autenticación Descentralizada (SSI) con DIDs

Este repositorio contiene la prueba de concepto (MVP) de un sistema de Autenticación mediante Identidad Auto-Soberana (SSI). Permite a los usuarios autenticarse en un servidor utilizando **Identificadores Descentralizados (DIDs)** y criptografía de curva elíptica (Ethereum), eliminando la necesidad de contraseñas tradicionales.

## 🏗️ Arquitectura del Proyecto

El proyecto se divide en dos componentes principales:

1. **El Cliente / Holder (`client.py` & `generar_did.py`):**
   * Actúa como la "cartera" (Wallet) del usuario.
   * Capaz de generar identidades matemáticas desde cero (`did:ethr`).
   * Firma criptográficamente los retos del servidor usando una Clave Privada local.
2. **El Servidor / Verifier (`main.py`):**
   * Construido con **FastAPI**.
   * Emite retos (Nonces) aleatorios para evitar ataques de repetición.
   * Resuelve los DIDs consultando la API de la W3C/DIF (`dev.uniresolver.io`).
   * Verifica matemáticamente las firmas entrantes extrayendo la dirección pública.

---

## 🛠️ Requisitos e Instalación

Para ejecutar este proyecto, necesitas **Python 3.8+**. 

1. **Clona el repositorio:**
   ```bash
   git clone <URL_DE_TU_REPO>
   cd did_backend
   ```

2. **Crea y activa el entorno virtual:**
   * En Linux / Mac / WSL:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```


3. **Instala las dependencias necesarias:**
   Asegúrate de que tu archivo `requirements.txt` contiene lo siguiente para evitar conflictos:
   ```text
   fastapi==0.110.0
   uvicorn==0.27.1
   pydantic>=2.9
   requests==2.31.0
   eth-account==0.11.0
   ```
   Instálalo ejecutando:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Cómo ejecutar el flujo completo (Prueba End-to-End)

Para ver la magia en acción, necesitarás abrir **dos terminales** (ambas con el entorno virtual activado).

### Paso 1: Levantar el Servidor (Terminal 1)
Inicia el nodo verificador ejecutando:
```bash
uvicorn main:app --reload --port 5010
```
*El servidor quedará a la escucha en `http://localhost:5010`.*

### Paso 2: Ejecutar el Cliente (Terminal 2)
Simula el intento de inicio de sesión de un usuario ejecutando:
```bash
python3 client.py
```

**¿Qué ocurre por debajo?**
1. El cliente pide permiso para entrar (`GET /api/auth/challenge`).
2. El servidor le devuelve un `session_id` temporal y un reto aleatorio (`nonce`).
3. El cliente usa su Clave Privada de Ethereum para firmar el reto.
4. El cliente envía su DID y la firma al servidor (`POST /api/auth/verify`).
5. El servidor comprueba la firma matemáticamente. Si es correcta, devuelve un `200 OK - Acceso Permitido`.

---

## 🔑 Gestión de Identidades (Extra)
Si deseas crear un usuario completamente nuevo desde cero, puedes ejecutar:
```bash
python3 generar_did.py
```
Este script generará una nueva Clave Privada y un nuevo DID de Ethereum (`did:ethr:sepolia:0x...`). Puedes copiar esos valores y sustituirlos en las variables de la cabecera de `client.py` para probar el inicio de sesión con una identidad fresca.

---

## 📅 Próximos Pasos (Sprint 3)
Tras lograr la autenticación básica mediante DIDs, los siguientes objetivos son:
* **Verifiable Credentials (VCs):** Implementar la emisión y verificación de credenciales (ej. un título universitario o certificado médico) adjuntas a la presentación.
* **Persistencia:** Sustituir los diccionarios en memoria de FastAPI por una base de datos real (SQLite) para registrar las sesiones y los DIDs conocidos.