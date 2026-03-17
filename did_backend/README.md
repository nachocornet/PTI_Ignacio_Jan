# 🛡️ DID Verifier Node (Backend)

Este repositorio contiene la implementación del servidor **Verificador (Verifier)** para nuestro sistema de Autenticación mediante Identidad Auto-Soberana (SSI). Está construido con **Python** y el framework **FastAPI**.

El objetivo de este nodo es recibir peticiones de acceso de usuarios (Holders), resolver sus Identificadores Descentralizados (DIDs) a través de redes públicas y verificar sus firmas criptográficas para conceder o denegar el acceso.

---

## 🚀 Novedades de la Versión Actual (Sprint 2)
En esta fase, el servidor ha dejado de ser un simulador local y ahora interactúa con el ecosistema SSI real:
* **Conexión al Universal Resolver:** El servidor realiza peticiones HTTP a la API pública de la DIF/W3C (`dev.uniresolver.io`) para resolver DIDs en tiempo real.
* **Extracción de Claves:** Lógica implementada para analizar el `DID Document` descargado y extraer la Clave Pública (`verificationMethod`) del usuario.
* **Control de Errores Robusto:** Si la red de un método DID concreto está caída o el DID no existe, la API captura la excepción y devuelve un error HTTP 404/400 controlado.
* **Flujo Challenge-Response:** Generación de *nonces* aleatorios (retos) vinculados a un `session_id` para evitar ataques de repetición (*replay attacks*).

---

## 🛠️ Requisitos e Instalación

Necesitarás tener instalado **Python 3.8+** en tu sistema. Sigue estos pasos para configurar el entorno local:

1. **Clona el repositorio:**
   ```bash
   git clone <URL_DE_TU_REPO>
   cd did_backend
   ```

2. **Crea y activa un entorno virtual:**
   * En Linux / Mac / WSL:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   * En Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Instala las dependencias necesarias:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Asegúrate de que el archivo contiene `fastapi`, `uvicorn`, `pydantic` y `requests`).*

---

## 🏃‍♂️ Cómo Arrancar el Servidor

Para levantar el servidor en modo desarrollo (con recarga automática si haces cambios en el código), ejecuta el siguiente comando en tu terminal:

```bash
uvicorn main:app --reload --port 5010
```

El servidor estará escuchando activamente en `http://localhost:5010`.

---

## 🧪 Guía de Pruebas (Paso a Paso)

Gracias a FastAPI, la API incluye una interfaz gráfica de pruebas (Swagger UI). No necesitas usar Postman ni programar un cliente para comprobar que funciona.

1. Abre tu navegador y ve a: **`http://localhost:5010/docs`**
2. **Paso 1: Solicitar el Reto (Challenge)**
   * Despliega la ruta `GET /api/auth/challenge`.
   * Haz clic en **"Try it out"** y luego en **"Execute"**.
   * El servidor te devolverá un JSON. **Copia el valor del `session_id`**.
3. **Paso 2: Enviar la Verificación**
   * Despliega la ruta `POST /api/auth/verify`.
   * Haz clic en **"Try it out"**.
   * Pega el siguiente JSON en la caja de texto (⚠️ **Importante:** sustituye el `session_id` por el que copiaste en el paso anterior):

   ```json
   {
     "session_id": "PEGA_AQUÍ_EL_SESSION_ID_DEL_PASO_1",
     "did": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
     "signature": "firma_de_prueba",
     "presentation": {}
   }
   ```
   *(Nota: Para esta prueba estamos utilizando un `did:key` real y público que el Universal Resolver puede descifrar sin problemas de conexión).*
4. Dale a **"Execute"**. 
5. Comprueba la respuesta del servidor. Deberías recibir un código `200 OK` con un mensaje indicando que el DID ha sido resuelto y validado correctamente.

---

## 🤝 Próximos Pasos (Sprint 3)
* **[Para el Cliente/Holder]:** Programar el script en Python que genere un par de claves (Pública/Privada), cree un DID local y sea capaz de firmar matemáticamente el *nonce* devuelto por `/api/auth/challenge`.
* **[Para el Backend/Verifier]:** Sustituir el validador "dummy" actual por la lógica criptográfica real (`cryptography` o `ecdsa`) que utilice la Clave Pública extraída del Resolver para verificar la firma del cliente.