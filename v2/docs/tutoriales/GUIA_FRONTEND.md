# Guía del Frontend SSI v2

Esta guía explica cómo leer y usar la interfaz sin necesidad de conocer el código interno.

## Objetivo

El frontend está diseñado para responder tres preguntas durante una demo:

1. ¿Qué se está emitiendo?
2. ¿Quién lo está presentando?
3. ¿Sigue siendo válido en blockchain?

## Configuración del Frontend

El frontend no usa endpoints fijos en el HTML. La configuración viene de:

- `frontend.variables.js` (archivo de variables de UI)
- generado automáticamente por `start_all.py` según `settings.py` y variables de entorno

Si cambias puertos/hosts por entorno, vuelve a lanzar `python3 start_all.py` para regenerar este archivo.

Seguridad de servido:

- El servidor de frontend expone solo `frontend_portal.html`, `issuer_dashboard.html`, `verifier_dashboard.html` y `frontend.variables.js`.
- No hay listado de directorios.
- Los archivos internos del repositorio no quedan accesibles por navegador.

## Mapa visual de la pantalla

- **Cabecera**: endpoints, estado de conexión y banner de feedback.
- **Guía rápida (Paso 1..4)**: secuencia recomendada.
- **Tracker de flujo**: estado de wallet, VC, VP y verificación.
- **Bloque Emisión/Revocación**: operaciones contra Issuer.
- **Bloque Verificación**: operación contra Verifier.
- **Paneles de salida**:
  - VC Bonita
  - VP Firmada
  - Glosario VC vs VP
  - Actividad
  - Payload/Respuesta en formato de resumen legible

Nota UX:

- La interfaz principal evita JSON crudo.
- El JSON queda solo en modo avanzado para depuración o importación manual.

## Flujo recomendado para demos

## 1) Cargar wallet local

Acción:
- Pulsar `Cargar wallet desde archivo`.

Qué debes ver:
- Mensaje indicando carga desde archivo local.
- Estado `Frontend Wallet = loaded`.
- Tracker marca `Wallet lista`.

La autocarga de wallet está desactivada por seguridad.

## 2) Emitir VC

Acción:
- Completar `DID del titular` y `DNI`.
- Pulsar `Emitir credencial`.

Qué debes ver:
- Resumen en `VC Bonita` con issuer, subject, hash y fecha en texto claro.
- Hash de credencial y tx hashes on-chain en resumen de issuer.
- Tracker marca `VC emitida`.

## 3) Verificar VP

Acción:
- Pulsar `Verificar presentación`.

Qué debes ver:
- Mensaje de firma local de VP.
- `VP Firmada` en resumen legible (holder, hash y firma abreviada).
- Resultado de checks on-chain en resumen de verificación.
- Tracker marca `VP firmada` y luego `Verificación final`.

## 4) Revocar y re-verificar

Acción:
- Pulsar `Revocar credencial`.
- Verificar otra vez.

Qué debes ver:
- Revocación confirmada en blockchain.
- Verificación posterior rechazada por estado revocado.

## Glosario rápido

- **VC (Verifiable Credential)**:
  - Documento emitido por Issuer.
  - Incluye claims y firma del emisor.
- **VP (Verifiable Presentation)**:
  - Presentación de una VC por parte del holder.
  - Incluye firma del holder para demostrar control actual de su DID.

Regla corta:
- VC = "qué afirma el emisor".
- VP = "quién lo presenta ahora".

## Errores comunes

- Wallet no carga:
  - Verifica que el frontend se sirva por HTTP.
  - Revisa las rutas en `walletSources` de `frontend.variables.js`.
  - Como fallback, usa carga manual desde archivo.
- Verificación falla por issuer:
  - Revisa bootstrap/autorización del issuer en contrato.
- Verificación falla por revocación:
  - Es esperado si ya ejecutaste `Revocar credencial`.

## Frontend de produccion

- `issuer_dashboard.html`: emisión y revocación.
- `verifier_dashboard.html`: verificación de VP.
- `frontend_portal.html`: punto de entrada y navegación.
