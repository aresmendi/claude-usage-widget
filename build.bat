@echo off
REM Doble clic para compilar claude-usage-widget.exe en Windows.
REM Requiere Python 3.11+ instalado y en el PATH.

cd /d "%~dp0"

if not exist ".venv" (
    echo Creando entorno virtual...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Instalando dependencias...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

pip install -r requirements-build.txt

echo Compilando .exe...
pyinstaller widget.spec --noconfirm

echo.
echo Listo. El ejecutable esta en dist\claude-usage-widget.exe
pause
