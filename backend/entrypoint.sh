#!/bin/sh
set -e

# Uso:
#   ./entrypoint.sh           → levanta la API (comportamiento default en Docker)
#   ./entrypoint.sh dev       → sh interactivo (make dev)
#   ./entrypoint.sh populate  → corre el script de populate para hoy
#   ./entrypoint.sh populate-all → corre el script de populate para todo el año

CMD=${1:-serve}

case "$CMD" in
  serve)
    echo "→ Iniciando API..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
    ;;
  dev)
    echo "→ Shell interactivo. Para levantar la API: ./entrypoint.sh serve"
    exec sh
    ;;
  populate)
    echo "→ Populando ${2:-hoy}..."
    exec python scripts/populate.py ${2:+--day $2 --month $3}
    ;;
  populate-all)
    echo "→ Populando todo el año..."
    exec python scripts/populate.py --all
    ;;
  *)
    exec "$@"
    ;;
esac
