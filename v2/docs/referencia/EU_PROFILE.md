# Perfil Europeo del Proyecto SSI v2

## Aviso importante

Este proyecto no puede declararse legalmente "conforme" a eIDAS/EUDI sin un proceso formal de evaluación, auditoría y certificación.

Lo que sí hace el sistema es alinearse técnicamente con un perfil interoperable basado en:

- W3C Verifiable Credentials
- DID como identificador descentralizado
- firma criptográfica verificable
- estado de revocación consultable
- trazabilidad y autenticidad de emisor/titular

## Qué se ha ajustado para alinearlo mejor

- VC con `credentialSchema`
- VC con `credentialStatus`
- VC con `termsOfUse`
- vigencia explícita (`validFrom` / `expirationDate`)
- verificación de firma + estado on-chain

## Qué falta para hablar de conformidad real

- revisión jurídica especializada
- auditoría de seguridad
- validación contra el perfil técnico exacto exigido por el despliegue objetivo
- adaptación al método DID y formato de credencial exigidos por el ecosistema destino

## Interpretación práctica

- Para un demo o una arquitectura SSI, el proyecto queda más cerca de un perfil europeo/interoperable.
- Para afirmar cumplimiento legal o certificación eIDAS, hace falta un proceso externo al código.
