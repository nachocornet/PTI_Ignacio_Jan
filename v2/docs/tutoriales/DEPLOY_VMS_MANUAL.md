# Tutorial Manual: Deploy en VMs (Virtech)

Este tutorial usa el archivo unico [ .env ](.env) ya preparado en la raiz del proyecto.

## 1. Preparacion local

1. Ve a la raiz del repo:

```bash
cd /home/nacho/PTI_Ignacio_Jan/v2
```

2. Comprueba que existe el .env unico:

```bash
test -f .env && echo "OK .env" || echo "Falta .env"
```

3. Comprueba que tienes clave SSH local:

```bash
ls -la ~/.ssh
```

## 2. Validar conectividad a las 3 VMs

```bash
set -a; source .env; set +a

ssh -p "$DB_SSH_PORT" "$SSH_USER@$NATTECH_HOST" "echo DB OK"
ssh -p "$BACKEND_SSH_PORT" "$SSH_USER@$NATTECH_HOST" "echo BACKEND OK"
ssh -p "$FRONTEND_SSH_PORT" "$SSH_USER@$NATTECH_HOST" "echo FRONTEND OK"
```

Si alguna conexion falla, primero corrige SSH (clave publica/known hosts).

## 3. Validar Docker en las VMs

```bash
set -a; source .env; set +a

ssh -p "$DB_SSH_PORT" "$SSH_USER@$NATTECH_HOST" "docker --version && docker compose version"
ssh -p "$BACKEND_SSH_PORT" "$SSH_USER@$NATTECH_HOST" "docker --version && docker compose version"
ssh -p "$FRONTEND_SSH_PORT" "$SSH_USER@$NATTECH_HOST" "docker --version && docker compose version"
```

Si sale "docker: command not found", instala en esa VM:

```bash
sudo apt-get update -y
sudo apt-get install -y docker.io docker-compose-plugin
```

## 4. Ejecutar deploy remoto

Desde la raiz del repo:

```bash
bash scripts/deploy_vms.sh
```

Tambien funciona desde [scripts/deploy_vms.sh](scripts/deploy_vms.sh):

```bash
cd scripts
./deploy_vms.sh
```

## 5. Verificacion post-deploy

```bash
set -a; source .env; set +a

curl -I "$FRONTEND_EXTERNAL_URL/frontend_portal.html"
curl "$BACKEND_EXTERNAL_URL/health"
curl "$BACKEND_EXTERNAL_URL/health/verifier"
```

## 6. Flujo funcional rapido (E2E)

1. Abre portal: `http://nattech.fib.upc.edu:40560/frontend_portal.html`
2. Emite VC en issuer dashboard.
3. Verifica VP en verifier dashboard.
4. Revoca VC y vuelve a verificar (debe fallar por revocacion).

## 7. Parar despliegue remoto

```bash
bash scripts/teardown.sh vms
```

## 8. Troubleshooting rapido

1. Error: variable faltante

```bash
set -a; source .env; set +a
bash scripts/deploy_vms.sh
```

2. Error: docker no encontrado en VM

```bash
ssh -p "$BACKEND_SSH_PORT" "$SSH_USER@$NATTECH_HOST" "sudo apt-get update -y && sudo apt-get install -y docker.io docker-compose-plugin"
```

3. Error: health check backend falla

```bash
ssh -p "$BACKEND_SSH_PORT" "$SSH_USER@$NATTECH_HOST" \
  "cd '$DEPLOY_PATH' && docker compose -f config/compose_vms/vm_servers/docker_compose.yml logs --tail=200"
```

4. Error: frontend no responde

```bash
ssh -p "$FRONTEND_SSH_PORT" "$SSH_USER@$NATTECH_HOST" \
  "cd '$DEPLOY_PATH' && docker compose -f config/compose_vms/vm-frontend/docker_compose.yml logs --tail=200"
```
