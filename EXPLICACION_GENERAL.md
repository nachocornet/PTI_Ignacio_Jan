# Explicación General del Proyecto

## Qué es este proyecto

Es una implementación de identidad autosoberana (SSI) en dos etapas:
- v1: MVP de autenticación con DID y firma.
- v2: sistema completo de credenciales verificables con estado de confianza en blockchain local.

## Problema que resuelve

Permitir autenticación y verificación de credenciales sin depender de contraseñas tradicionales y con trazabilidad de revocación verificable.

## Principios de diseño

1. Separación de responsabilidades.
2. Verificación en dos capas (cripto + on-chain).
3. Estado auditable en contrato.
4. Operación reproducible local.
5. Preparado para migración a testnet/cloud.

## Componentes principales

## Backend
- Issuer API: emite y revoca.
- Verifier API: verifica presentación.
- Blockchain client: abstrae Web3 y contrato.

## Blockchain
- Hardhat local para entorno reproducible.
- Contrato SSIRegistry con lógica de estado SSI.

## Frontend
- Interfaz única para ejecutar flujo completo.
- Firma de presentación y consumo de APIs.

## Datos
- SQLite local para ciudadanos/sesiones.
- JSON local para wallets y metadata de contrato.

## Estado funcional actual

- Flujo end-to-end validado:
  - emitir (200),
  - verificar (200),
  - revocar (200),
  - verificar post-revocación (401).
- Suite pytest pasando.

## Estado de madurez

El sistema está completo para entorno local y demo técnica.

Pendiente estratégico principal:
- migración de infraestructura blockchain a testnet (Sepolia) y despliegue cloud integral.

## Siguiente etapa recomendada

1. Configurar red Sepolia en Hardhat.
2. Externalizar secretos y configuración por entorno.
3. Desplegar APIs (contenedores) y frontend en cloud.
4. Añadir CI/CD y observabilidad.
