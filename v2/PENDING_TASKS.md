# 📋 Tareas Pendientes - SSI v2

**Última actualización:** 28 de Abril de 2026  
**Status:** Todo funcional, tareas opcionales para mejorar

---

## 📖 Guía de Lectura Recomendada

Antes de hacer cualquier cosa, lee esto en orden:

1. **[README.md](README.md)** (10 min) - Visión general del proyecto
2. **[REPORT.md](REPORT.md)** (15 min) - Estado completo actual
3. **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** (5 min) - Checklist pre-deploy
4. **Este archivo** (5 min) - Lo que falta por hacer

Luego, según la tarea que quieras hacer:
- Para desarrollo local: [docs/tutoriales/DESARROLLO_LOCAL.md](docs/tutoriales/DESARROLLO_LOCAL.md)
- Para CI/CD: [docs/tutoriales/CI_CD_GITHUB_ACTIONS.md](docs/tutoriales/CI_CD_GITHUB_ACTIONS.md)
- Para troubleshooting: [docs/tutoriales/TROUBLESHOOTING.md](docs/tutoriales/TROUBLESHOOTING.md)

---

## 🎯 Tareas por Prioridad

### 🔴 CRÍTICO (Bloqueante para Producción)

**✅ COMPLETADO - No hay tareas críticas pendientes**

El proyecto está listo para desplegar a Virtech en cualquier momento.

---

### 🟡 IMPORTANTE (Recomendado antes de ir a Producción)

#### Tarea 1: Validar en Staging antes de Producción

**¿Por qué?** Asegurar que todo funciona en las VMs antes de dar acceso a usuarios reales.

**¿Qué tienes que hacer?**

1. Configura secrets en GitHub (si no lo has hecho)
   - Lee: [docs/tutoriales/CI_CD_GITHUB_ACTIONS.md - Paso 1.1: Preparar Secrets](docs/tutoriales/CI_CD_GITHUB_ACTIONS.md#paso-11-preparar-secrets-en-github)
   - Crea estos secrets: `SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS`, `DB_PASSWORD`, `ISSUER_WALLET_JSON_B64`, `SEPOLIA_RPC_URL`

2. Haz push a main
   ```bash
   git add -A
   git commit -m "Deploy to staging"
   git push origin main
   ```

3. Monitorea el deploy
   - Ve a: GitHub → Actions → Deploy SSI v2
   - Espera a que terminen los 4 jobs (test, deploy_db, deploy_backend, deploy_frontend)
   - Verifica que todos estén en verde ✅

4. Test manual en Virtech
   - Abre: `http://nattech.fib.upc.edu:40560/frontend_portal.html`
   - Prueba: Emitir VC → Verificar VP → Revocar → Re-verificar
   - Si todo funciona: ¡Listo para producción!

**¿Cuánto tiempo toma?** ~20 minutos (deploy) + 10 minutos (testing manual) = 30 min

**¿Si falla?** Lee [docs/tutoriales/CI_CD_GITHUB_ACTIONS.md - Troubleshooting](docs/tutoriales/CI_CD_GITHUB_ACTIONS.md#4-troubleshooting)

---

#### Tarea 2: Setup Monitoring y Logging

**¿Por qué?** Una vez en producción, necesitas visibilidad de qué está pasando.

**¿Qué tienes que entender?**
- **Logs:** Dónde se guardan (en Docker: `docker compose logs <servicio>`)
- **Health checks:** Ya existen en `/health` endpoints
- **Alertas:** GitHub Actions notifica si un deploy falla

**¿Qué tienes que hacer?**

Opción A (Fácil - Recomendado ahora):
```bash
# Ver logs en tiempo real desde VM
ssh -p 40571 alumne@nattech.fib.upc.edu \
  "docker compose logs -f issuer verifier"
```

Opción B (Profesional - Futuro):
- Instalar Prometheus + Grafana
- Configurar métricas de Uvicorn
- Crear dashboards
- (Esto es "nice-to-have" para después)

**¿Cuánto tiempo toma?** 
- Opción A: 5 minutos (ya funciona)
- Opción B: 4-6 horas

---

### 🟢 OPCIONAL (Mejoras Futuras)

#### Tarea 3: Backup y Disaster Recovery

**¿Por qué?** Si la BD se daña, necesitas poder recuperarse.

**¿Qué tienes que entender?**
- **Backup automático:** Base de datos PostgreSQL
- **Recovery:** Restaurar desde backup
- **RTO/RPO:** Recovery Time Objective / Recovery Point Objective

**¿Qué tienes que hacer?**

Crea un script `scripts/backup_db.sh`:
```bash
#!/bin/bash
# Backup PostgreSQL en VM DB

BACKUP_DIR="/home/alumne/backups"
DATE=$(date +%Y%m%d_%H%M%S)

ssh -p 40581 alumne@nattech.fib.upc.edu << EOF
mkdir -p $BACKUP_DIR
docker exec db pg_dump -U ssi_user ssi_db > $BACKUP_DIR/ssi_db_$DATE.sql
ls -lh $BACKUP_DIR/ | tail -5
EOF
```

Luego crea un cron job en tu máquina local:
```bash
# Ejecutar backup cada día a las 2 AM
0 2 * * * /path/to/scripts/backup_db.sh
```

**¿Cuánto tiempo toma?** 1 hora

**¿Cuándo hacerlo?** Después del primer deploy a producción

---

#### Tarea 4: Observabilidad Profesional (Prometheus + Grafana)

**¿Por qué?** Ver métricas en tiempo real (latencia, errores, uptime).

**¿Qué tienes que entender?**
- **Prometheus:** Base de datos de métricas
- **Grafana:** Visualización
- **Scraping:** Prometheus lee métricas de `/metrics` endpoints

**¿Qué tienes que hacer?**

1. Lee: Documentación oficial de Prometheus/Grafana
2. Añade prometheus-client a requirements.txt
   ```
   prometheus-client==0.17.1
   ```
3. Modifica `services/issuer/app.py`:
   ```python
   from prometheus_client import Counter, Histogram, generate_latest
   
   issue_counter = Counter('credentials_issued_total', 'Total VCs issued')
   verify_histogram = Histogram('verification_time_seconds', 'Verification time')
   
   @app.get("/metrics")
   def metrics():
       return generate_latest()
   ```
4. Crea `docker-compose-monitoring.yml` con Prometheus + Grafana
5. Configura Grafana dashboards

**¿Cuánto tiempo toma?** 6-8 horas

**¿Cuándo hacerlo?** Semana 2 de producción (después de que todo esté estable)

---

#### Tarea 5: Multi-Chain Support

**¿Por qué?** Permitir que credenciales estén en múltiples blockchains (Sepolia, Ethereum, Polygon, etc).

**¿Qué tienes que entender?**
- Actualmente: Solo 1 red configurada a la vez
- Necesitas: Soporte simultáneo de múltiples redes

**¿Qué tienes que hacer?**

1. Modifica `shared/blockchain_client.py`:
   ```python
   class BlockchainClient:
       def __init__(self, networks: Dict[str, str]):  # {"sepolia": "...", "mainnet": "..."}
           self.web3_clients = {
               name: Web3(Web3.HTTPProvider(rpc))
               for name, rpc in networks.items()
           }
   ```

2. Actualiza endpoints para especificar red:
   ```python
   @app.post("/api/credentials/issue_dni/{blockchain_network}")
   def issue_dni(blockchain_network: str, ...):
       # Emit to specific network
   ```

**¿Cuánto tiempo toma?** 8-10 horas

**¿Cuándo hacerlo?** Cuando tengas múltiples blockchains en tu roadmap

---

#### Tarea 6: Recuperación Automática ante Fallos

**¿Por qué?** Si un servicio cae, que se reinicie automáticamente.

**¿Qué tienes que entender?**
- **Health checks:** Ya existen en Docker
- **Auto-restart:** Kubernetes lo hace automáticamente
- **Alternativa simple:** Docker Compose `restart: always`

**¿Qué tienes que hacer?**

Opción A (Fácil - Docker Compose):
```yaml
services:
  issuer:
    image: ssi-issuer
    restart: always  # ← Añadir esto
    healthcheck:
      test: curl -f http://localhost:5010/health || exit 1
      interval: 10s
      timeout: 5s
      retries: 3
```

Opción B (Profesional - Kubernetes):
```bash
# Instalar Kubernetes en VMs
# Deployer servicios en K8s
# Automático restart + escalado
```

**¿Cuánto tiempo toma?**
- Opción A: 30 minutos
- Opción B: 16+ horas

**¿Cuándo hacerlo?** 
- Opción A: Ahora mismo (fácil)
- Opción B: Cuando necesites escalado automático

---

#### Tarea 7: CI/CD Mejorado (Test de Integración)

**¿Por qué?** Actualmente solo hay tests unitarios. Tests E2E darían más confianza.

**¿Qué tienes que entender?**
- **Tests unitarios:** Componentes aislados (27 tests ✅)
- **Tests de integración:** Componentes juntos (issuer → blockchain → verifier)
- **Tests E2E:** Flujo completo desde UI

**¿Qué tienes que hacer?**

Crea `tests/test_integration_e2e.py`:
```python
def test_e2e_issue_and_verify_flow():
    # 1. Levantar blockchain local
    # 2. Emitir VC via API
    # 3. Verificar VP via API
    # 4. Revocar credencial
    # 5. Verificar que no funciona
    pass

def test_e2e_blockchain_state_sync():
    # 1. Emitir VC
    # 2. Verificar que está en blockchain
    # 3. Verificar que verifier lo ve
    pass
```

Luego en `.github/workflows/deploy.yml`:
```yaml
- name: Run E2E tests
  run: pytest tests/test_integration_e2e.py -v
```

**¿Cuánto tiempo toma?** 3-4 horas

**¿Cuándo hacerlo?** Semana 1 de producción (después de validar en staging)

---

#### Tarea 8: Documentación de API (OpenAPI/Swagger)

**¿Por qué?** Otros equipos necesitan saber cómo usar tus APIs.

**¿Qué tienes que entender?**
- FastAPI genera Swagger automáticamente en `/docs`
- Pero necesita más información (descriptions, ejemplos, etc)

**¿Qué tienes que hacer?**

Mejora los endpoints en `services/issuer/app.py`:
```python
@app.post("/api/credentials/issue_dni", 
    summary="Emit a Verifiable Credential",
    description="Issues a new VC for a citizen DNI",
    responses={
        200: {"description": "VC issued successfully"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized issuer"}
    }
)
def issue_dni(request: IssueRequest) -> IssueResponse:
    """
    Ejemplo:
    {
        "holder_address": "0x...",
        "dni": "12345678A",
        "name": "Juan Pérez"
    }
    """
    pass
```

Resultado: `http://127.0.0.1:5010/docs` tendrá docs interactivas

**¿Cuánto tiempo toma?** 2 horas

**¿Cuándo hacerlo?** Cuando otros equipos necesiten consumir tus APIs

---

#### Tarea 9: Seguridad Mejorada (TLS/HTTPS)

**¿Por qué?** En producción, las credenciales deben viajar por HTTPS, no HTTP.

**¿Qué tienes que entender?**
- **HTTPS:** Encriptación de tráfico
- **Certificados:** Let's Encrypt gratis en el reverse proxy
- **HSTS:** Header para forzar HTTPS

**¿Qué tienes que hacer?**

Opción A (Fácil - Certbot + Nginx):
```bash
# En VM Frontend
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d nattech.fib.upc.edu
# Modifica nginx.conf para usar certs
sudo systemctl restart nginx
```

Opción B (Simple - Auto-renew):
```bash
# Cron job semanal para renovar certs
0 0 * * 0 /usr/bin/certbot renew
```

**¿Cuánto tiempo toma?** 1 hora

**¿Cuándo hacerlo?** Antes de abrir a usuarios externos

---

#### Tarea 10: Incident Response Runbook

**¿Por qué?** Si algo explota, necesitas pasos claros (no improvisar).

**¿Qué tienes que hacer?**

Crea `docs/operacion/INCIDENT_RESPONSE.md`:
```markdown
# Incident Response Runbook

## Escenario 1: La API Issuer no responde

### Síntomas
- curl http://nattech.fib.upc.edu:40570/health → Connection refused

### Checklist
1. SSH a Backend VM
2. Ver logs: docker compose logs issuer
3. Reiniciar: docker compose restart issuer
4. Esperar 10 segundos
5. Retry: curl /health

### Si sigue fallando
1. Shutdown: docker compose down issuer
2. Rebuild: docker compose up -d --build issuer
3. Monitor: docker compose logs -f issuer

### Si persiste
1. Escalación: Contactar a DevOps
2. Rollback: Git revert último commit
3. Re-deploy: bash scripts/deploy_vms.sh

## Escenario 2: Base de datos corrupta

### Recovery
1. SSH a DB VM
2. Backup actual: pg_dump > /tmp/backup.sql
3. Restaurar: psql < deployments/last_known_good.sql
4. Verificar: docker exec db psql -U ssi_user -d ssi_db -c '\dt'

## Escenario 3: Blockchain fuera de sync

...
```

**¿Cuánto tiempo toma?** 3 horas

**¿Cuándo hacerlo?** Después de primer mes en producción

---

## 📊 Matriz de Decisión

Usa esta tabla para decidir qué hacer primero:

| Tarea | Urgencia | Dificultad | Tiempo | ROI | ¿Cuándo? |
|-------|----------|-----------|--------|-----|----------|
| 1. Validar en Staging | 🔴 Alta | Bajo | 30m | Alto | **Ahora** |
| 2. Setup Monitoring | 🟡 Media | Bajo | 5m | Alto | Ahora |
| 3. Backup/DR | 🟡 Media | Bajo | 1h | Alto | Semana 1 |
| 4. Observabilidad Pro | 🟢 Baja | Alto | 6-8h | Medio | Mes 2 |
| 5. Multi-Chain | 🟢 Baja | Alto | 8-10h | Bajo | Roadmap |
| 6. Auto-Recovery | 🟢 Baja | Medio | 30m-16h | Medio | Opción A: Ahora |
| 7. Tests E2E | 🟢 Baja | Medio | 3-4h | Alto | Semana 1 |
| 8. API Docs | 🟢 Baja | Bajo | 2h | Medio | Cuando lo pidan |
| 9. HTTPS/TLS | 🟡 Media | Bajo | 1h | Alto | Mes 1 |
| 10. Incident Runbook | 🟢 Baja | Bajo | 3h | Alto | Mes 1 |

---

## ✅ Plan de Acción Recomendado (Próximas 4 Semanas)

### Semana 1 (Esta semana)
- [ ] Tarea 1: Validar en Staging (30 min)
- [ ] Tarea 2: Setup Monitoring básico (5 min)
- [ ] Tarea 6A: Auto-recovery con Docker (30 min)

**Resultado:** Producción estable

### Semana 2
- [ ] Tarea 3: Backup/DR automático (1 hora)
- [ ] Tarea 7: Tests E2E (3-4 horas)
- [ ] Tarea 9: HTTPS/TLS (1 hora)

**Resultado:** Seguridad y confiabilidad mejoradas

### Semana 3-4
- [ ] Tarea 4: Observabilidad profesional (6-8 horas)
- [ ] Tarea 10: Incident Runbook (3 horas)
- [ ] Tarea 8: API Docs (2 horas)

**Resultado:** Operaciones profesionales

### Después (Roadmap)
- [ ] Tarea 5: Multi-chain
- [ ] Tarea 6B: Kubernetes

---

## 🎓 Recursos de Aprendizaje

Si necesitas aprender algo nuevo:

### Blockchain
- [Web3.py Documentation](https://web3py.readthedocs.io/)
- [Solidity by Example](https://solidity-by-example.org/)

### DevOps/Infrastructure
- [Docker Compose Best Practices](https://docs.docker.com/compose/production/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [SSH Security Guide](https://man.openbsd.org/ssh)

### Observability
- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)

### Security
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Let's Encrypt Guide](https://letsencrypt.org/docs/)

---

## ❓ Preguntas Frecuentes

**P: ¿Puedo hacer todas las tareas a la vez?**  
R: No. Haz primero Tarea 1, luego 2, luego 3. Una cosa a la vez = menos bugs.

**P: ¿Qué pasa si me salto una tarea?**  
R: Depende cuál:
- Tareas Críticas (Rojo): NO SALTES - Proyecto no funciona
- Tareas Importantes (Amarillo): Recomendado antes de producción
- Tareas Opcionales (Verde): Puedes esperar

**P: ¿Cuánto tiempo total?**  
R: 
- Producción básica: ~1 hora (Tarea 1)
- Producción robusta: ~5-6 horas (Tareas 1-3, 6A, 9)
- Producción profesional: ~20+ horas (Todo)

**P: ¿Si algo sale mal?**  
R: Ve a [docs/tutoriales/TROUBLESHOOTING.md](docs/tutoriales/TROUBLESHOOTING.md)

---

## 📞 Soporte

Si necesitas ayuda:

1. Busca el error en [TROUBLESHOOTING.md](docs/tutoriales/TROUBLESHOOTING.md)
2. Revisa el [REPORT.md](REPORT.md) para entender la arquitectura
3. Ejecuta el script de diagnóstico en [TROUBLESHOOTING.md - Paso 8](docs/tutoriales/TROUBLESHOOTING.md#8-diagnóstico-completo)

---

**Documento:** PENDING_TASKS.md  
**Versión:** 1.0  
**Actualizado:** 28 de Abril de 2026  
**Status:** ✅ Listo para seguir
