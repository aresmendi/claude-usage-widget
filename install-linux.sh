#!/bin/sh
# Integra el AppImage en el menú de aplicaciones de GNOME (icono + lanzador).
# Ejecutar una sola vez, después de generar el AppImage con build-linux.sh.
set -e

cd "$(dirname "$0")"

APPIMAGE="claude-usage-widget-x86_64.AppImage"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
DESKTOP_DIR="$HOME/.local/share/applications"

if [ ! -f "$APPIMAGE" ]; then
    echo "No se encuentra $APPIMAGE — ejecuta antes ./build-linux.sh"
    exit 1
fi

mkdir -p "$BIN_DIR" "$ICON_DIR" "$DESKTOP_DIR"

cp "$APPIMAGE" "$BIN_DIR/claude-usage-widget.AppImage"
chmod +x "$BIN_DIR/claude-usage-widget.AppImage"

cp assets/icon.png "$ICON_DIR/claude-usage-widget.png"

sed "s|Exec=claude-usage-widget|Exec=$BIN_DIR/claude-usage-widget.AppImage|" \
    claude-usage-widget.desktop > "$DESKTOP_DIR/claude-usage-widget.desktop"
chmod +x "$DESKTOP_DIR/claude-usage-widget.desktop"

command -v update-desktop-database >/dev/null && update-desktop-database "$DESKTOP_DIR" || true
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "Listo. Búscalo como 'Claude Usage Widget' en el menú de aplicaciones."
