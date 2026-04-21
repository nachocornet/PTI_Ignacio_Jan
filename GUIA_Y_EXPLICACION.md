# Guía y Explicación de Uso

Este documento está pensado para usar el sistema de principio a fin sin ambigüedades.

## Objetivo funcional

Demostrar que una credencial:
1. se emite por un issuer confiable,
2. se verifica por firma,
3. se valida por estado on-chain,
4. puede revocarse y ser rechazada después.

## Flujo recomendado (usuario)

## 1. Arranque

```bash
cd v2
python3 setup_complete.py
python3 start_all.py
```

## 2. Entrar a la interfaz

Abrir:

```text
http://127.0.0.1:8080/frontend.html
```

## 3. Emitir credencial

En la sección de emisión:
- cargar wallet local,
- revisar DID del titular,
- usar DNI válido (`12345678A`),
- pulsar “Emitir credencial”.

Resultado esperado:
- credencial en panel,
- hash generado,
- transacciones de `setDidStatus` y `registerCredential`.

## 4. Verificar credencial

En la sección de verificación:
- mantener la VC generada,
- pulsar “Verificar presentación”.

Resultado esperado:
- estado de éxito,
- validación on-chain positiva.

## 5. Revocar

- pulsar “Revocar credencial”.

Resultado esperado:
- transacción de revocación confirmada.

## 6. Verificar de nuevo

- pulsar nuevamente “Verificar presentación”.

Resultado esperado:
- rechazo con mensaje de credencial revocada.

## Qué está validando el sistema internamente

## Capa criptográfica
- Firma del issuer sobre la VC.
- Firma del holder sobre la VP.
- Propiedad de la credencial por el holder.

## Capa on-chain
- Issuer autorizado.
- DID del titular activo.
- Credencial no revocada.

## Errores típicos y solución

## Error de conexión blockchain
- Asegurar que Hardhat está levantado.
- Verificar deploy/bootstrap hechos.
- Ejecutar `python3 check_blockchain.py`.

## Error CORS en navegador
- Revisar `SSI_CORS_ORIGINS`.
- Incluir origen del frontend.

## Error de wallet en frontend
- Comprobar que `v2/wallet.json` existe y contiene `did` y `private_key`.

## Comandos útiles

```bash
# Test suite
cd v2
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest

# Estado de cambios
cd ..
git status --short
```
