@echo off
setlocal
title Pasantia - Servidor Flask
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    set "PYTHON=python"
) else (
    set "PYTHON=py -3"
)

%PYTHON% --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python 3. Instala Python y habilita "Add Python to PATH".
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo [1/4] Creando entorno virtual...
    %PYTHON% -m venv venv
    if errorlevel 1 goto error_venv
)

echo [2/4] Instalando o verificando dependencias...
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error_dependencies

echo [3/4] Comprobando la configuracion de la base de datos...
"venv\Scripts\python.exe" -c "from dotenv import load_dotenv; import os, sys; load_dotenv(); sys.exit(0 if os.getenv('DATABASE_URL') else 1)"
if errorlevel 1 goto error_database

echo [4/4] Iniciando la aplicacion...
start "" http://127.0.0.1:5000
"venv\Scripts\python.exe" app.py
if errorlevel 1 (
    echo [ERROR] La aplicacion termino con un error. Revisa el mensaje anterior.
    pause
    exit /b 1
)
exit /b 0

:error_venv
echo [ERROR] No se pudo crear el entorno virtual.
pause
exit /b 1

:error_dependencies
echo [ERROR] No se pudieron instalar las dependencias.
pause
exit /b 1

:error_database
echo [ERROR] No se encontro DATABASE_URL. Configurala en el archivo .env.
pause
exit /b 1
