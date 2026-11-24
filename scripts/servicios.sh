#!/bin/bash
# Levanta, detiene o revisa los 5 microservicios de INVENT-AI-R.
#
#   bash scripts/servicios.sh start    # los levanta en segundo plano
#   bash scripts/servicios.sh status   # dice cuales estan arriba
#   bash scripts/servicios.sh stop     # los detiene
#
# Cada servicio usa su propio venv. Los logs quedan en logs/<servicio>.log

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
SERVICIOS="auth-service:8001 inventario-service:8002 ventas-service:8003 compras-service:8004 analisis-service:8005"

arriba() {
    lsof -ti tcp:"$1" -sTCP:LISTEN > /dev/null 2>&1
}

iniciar() {
    mkdir -p "$RAIZ/logs"
    for par in $SERVICIOS; do
        nombre="${par%%:*}"
        puerto="${par##*:}"
        if arriba "$puerto"; then
            echo "[$nombre] ya estaba arriba en el puerto $puerto"
            continue
        fi
        if [ ! -f "$RAIZ/$nombre/venv/bin/activate" ]; then
            echo "[$nombre] NO se levanto: falta su venv en $nombre/venv"
            continue
        fi
        (
            cd "$RAIZ/$nombre" || exit 1
            source venv/bin/activate
            nohup python manage.py runserver "$puerto" > "$RAIZ/logs/$nombre.log" 2>&1 &
        )
        echo "[$nombre] iniciando en el puerto $puerto (log: logs/$nombre.log)"
    done
    echo "Espera unos segundos y revisa con: bash scripts/servicios.sh status"
}

estado() {
    for par in $SERVICIOS; do
        nombre="${par%%:*}"
        puerto="${par##*:}"
        if arriba "$puerto"; then
            echo "ARRIBA   $nombre (puerto $puerto)"
        else
            echo "ABAJO    $nombre (puerto $puerto)"
        fi
    done
}

detener() {
    for par in $SERVICIOS; do
        nombre="${par%%:*}"
        puerto="${par##*:}"
        if ! arriba "$puerto"; then
            echo "[$nombre] ya estaba detenido"
            continue
        fi
        lsof -ti tcp:"$puerto" -sTCP:LISTEN | xargs kill 2>/dev/null
        sleep 1
        if arriba "$puerto"; then
            lsof -ti tcp:"$puerto" -sTCP:LISTEN | xargs kill -9 2>/dev/null
        fi
        echo "[$nombre] detenido"
    done
}

case "$1" in
    start)  iniciar ;;
    stop)   detener ;;
    status) estado ;;
    *) echo "Uso: bash scripts/servicios.sh {start|stop|status}"; exit 1 ;;
esac
