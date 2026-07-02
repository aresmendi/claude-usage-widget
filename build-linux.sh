#!/bin/sh
# Genera claude-usage-widget-x86_64.AppImage. Ejecutar desde la raíz del proyecto.
set -e

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python3 -m venv .venv
    .venv/bin/pip install -q -r requirements.txt
fi

.venv/bin/pip install -q -r requirements-build.txt

.venv/bin/pyinstaller widget-linux.spec --noconfirm

rm -rf AppDir
mkdir -p AppDir/usr/bin
cp dist/claude-usage-widget AppDir/usr/bin/
cp assets/icon.png AppDir/claude-usage-widget.png
cp claude-usage-widget.desktop AppDir/claude-usage-widget.desktop

cat > AppDir/AppRun << 'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/claude-usage-widget" "$@"
EOF
chmod +x AppDir/AppRun

if [ ! -f appimagetool ]; then
    curl -L -o appimagetool -s \
        https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool
fi

ARCH=x86_64 ./appimagetool --appimage-extract-and-run AppDir claude-usage-widget-x86_64.AppImage

echo
echo "Listo: claude-usage-widget-x86_64.AppImage"
