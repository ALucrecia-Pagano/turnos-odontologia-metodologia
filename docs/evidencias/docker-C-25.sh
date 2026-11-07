#!/usr/bin/env bash
# Verificación manual reproducible del servicio frontend de C-25.
# Uso, desde la raíz del repo, con `docker compose up -d frontend` ya corrido:
#   bash docs/evidencias/docker-C-25.sh > docs/evidencias/docker-C-25.txt 2>&1
# No hace `down` ni borra volúmenes. Edita un archivo de frontend/src para probar el HMR
# y lo restaura byte a byte en un trap, aunque algo falle.
set -u

TARGET="frontend/src/pages/HomePage.tsx"
BACKUP="$(mktemp)"
cp "$TARGET" "$BACKUP"
restore() {
  cp "$BACKUP" "$TARGET"
  rm -f "$BACKUP"
}
trap restore EXIT

section() {
  echo
  echo "================================================================"
  echo "$ $*"
  echo "================================================================"
}

section "docker compose ps frontend backend"
docker compose ps frontend backend

section "curl -s -i http://localhost:5173/ (cabecera y HTML)"
curl -s -i http://localhost:5173/ | sed -n '1,25p'

section "docker compose exec frontend printenv VITE_API_URL CHOKIDAR_USEPOLLING"
docker compose exec -T frontend printenv VITE_API_URL CHOKIDAR_USEPOLLING

section "El contenedor frontend no recibe secretos (se espera 0 variables)"
docker compose exec -T frontend sh -c 'env | grep -cE "^(JWT_SECRET|POSTGRES_PASSWORD|POSTGRES_USER|DATABASE_URL|SEED_USER_PASSWORD)="'

section "Base de la API que recibe el navegador: módulo transformado por Vite"
echo "--- import.meta.env que Vite inyecta en el módulo (valor de VITE_API_URL):"
curl -s http://localhost:5173/src/shared/api/client.ts | grep -o '"VITE_API_URL": *"[^"]*"'
curl -s http://localhost:5173/src/shared/api/client.ts | grep -n "API_BASE_URL ="
echo "--- ocurrencias de backend:8000 en el módulo servido (se espera 0):"
curl -s http://localhost:5173/src/shared/api/client.ts | grep -c "backend:8000"

section "Preflight CORS: OPTIONS http://localhost:8000/api/health con Origin http://localhost:5173"
curl -s -i -X OPTIONS http://localhost:8000/api/health \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization,content-type"

section "GET http://localhost:8000/api/health con Origin http://localhost:5173"
curl -s -i http://localhost:8000/api/health -H "Origin: http://localhost:5173"

section "HMR: editar $TARGET en el host y ver que Vite (en el contenedor) detecta el cambio"
SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "--- módulo servido ANTES del cambio:"
curl -s http://localhost:5173/src/pages/HomePage.tsx | grep -o "Bienvenida[^.]*\." | head -1
sed -i 's/Bienvenida a la agenda del consultorio\./Bienvenida a la agenda del consultorio (cambio HMR)./' "$TARGET"
echo "--- archivo editado en el host:"
grep -n "cambio HMR" "$TARGET"
DETECTED="no"
for attempt in $(seq 1 30); do
  sleep 1
  if curl -s http://localhost:5173/src/pages/HomePage.tsx | grep -q "cambio HMR"; then
    DETECTED="si"
    echo "--- Vite sirvió el módulo nuevo tras ${attempt}s sin reiniciar el contenedor:"
    curl -s http://localhost:5173/src/pages/HomePage.tsx | grep -o "Bienvenida[^.]*\." | head -1
    break
  fi
done
echo "--- cambio detectado por Vite: $DETECTED"
sleep 2
echo "--- docker compose logs frontend desde $SINCE:"
docker compose logs --no-log-prefix --since "$SINCE" frontend
echo "--- contenedor sin reinicios (RestartCount y StartedAt):"
docker inspect --format '{{.RestartCount}} {{.State.StartedAt}}' "$(docker compose ps -q frontend)"

restore
trap - EXIT
section "Restauración de $TARGET"
if grep -q "cambio HMR" "$TARGET"; then echo "ERROR: el archivo no se restauró"; else echo "restaurado: sin el texto de prueba"; fi
git diff --stat -- "$TARGET"
