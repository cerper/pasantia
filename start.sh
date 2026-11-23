#!/usr/bin/env bash
set -euo pipefail

# Ir al directorio donde está ubicado el script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PY="venv/bin/python"
REQ_STAMP="venv/.req_installed"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] No se encontro python3. Instalalo desde el gestor de paquetes de tu distribucion."
    exit 1
fi

if [ ! -f "app.py" ]; then
    echo "[ERROR] No se encontro app.py en $SCRIPT_DIR."
    exit 1
fi

if [ ! -x "$VENV_PY" ]; then
    echo "[1/4] Creando entorno virtual..."
    python3 -m venv venv || {
        echo "[ERROR] No se pudo crear el entorno virtual. Verifica tener instalado python3-venv."
        exit 1
    }
else
    echo "[1/4] Entorno virtual listo."
fi

NEED_INSTALL=0
if [ ! -f "$REQ_STAMP" ]; then
    NEED_INSTALL=1
elif [ -f "requirements.txt" ] && [ "requirements.txt" -nt "$REQ_STAMP" ]; then
    NEED_INSTALL=1
fi

if [ "$NEED_INSTALL" -eq 1 ]; then
    echo "[2/4] Instalando dependencias desde requirements.txt..."
    "$VENV_PY" -m pip install --upgrade pip >/dev/null 2>&1 || true
    "$VENV_PY" -m pip install -r requirements.txt || {
        echo "[ERROR] No se pudieron instalar las dependencias."
        exit 1
    }
    touch "$REQ_STAMP"
else
    echo "[2/4] Dependencias ya instaladas."
fi

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[3/4] Creando .env desde .env.example..."
    cp ".env.example" ".env"
fi

echo "[3/4] Comprobando DATABASE_URL en .env..."
"$VENV_PY" -c "import os, sys; from dotenv import load_dotenv; load_dotenv(); sys.exit(0 if os.getenv('DATABASE_URL', '').strip() else 1)" || {
    echo "[ERROR] DATABASE_URL no esta definida o esta vacia en el archivo .env."
    exit 1
}

echo "[4/4] Iniciando servidor Flask en http://127.0.0.1:5000 ..."
if command -v wslview >/dev/null 2>&1; then
    (sleep 2 && wslview "http://127.0.0.1:5000" >/dev/null 2>&1) &
elif command -v cmd.exe >/dev/null 2>&1; then
    (sleep 2 && cmd.exe /c start "" "http://127.0.0.1:5000" >/dev/null 2>&1) &
elif command -v xdg-open >/dev/null 2>&1; then
    (sleep 2 && xdg-open "http://127.0.0.1:5000" >/dev/null 2>&1) &
fi

exec "$VENV_PY" app.py