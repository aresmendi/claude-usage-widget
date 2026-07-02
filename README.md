# Claude Usage Widget

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Widget de escritorio que monitoriza el consumo del plan Pro de claude.ai en tiempo real,
sin necesidad de abrir el navegador ni la app. Vive en la bandeja del sistema, se actualiza
solo cada minuto y notifica cuando te acercas al límite de la sesión.

**Plataformas**: Linux (AppImage) · Windows (.exe) — pensado como alternativa a
[Tokenio](https://github.com/elomid/tokenio) (el mismo concepto, pero para macOS).

## Funcionalidades

- Icono de bandeja con color según estado: verde (sesión activa) / rojo (caducada o error).
- Popup con barra de uso de la sesión actual (5h) y del uso semanal (7 días), coloreadas
  según el nivel (verde / naranja cerca del límite / rojo al límite).
- Notificación de escritorio antes de agotar la sesión (umbral configurable).
- Sin servidor ni cuenta propia: lee la cookie de sesión ya activa en tu navegador y habla
  directamente con la API de claude.ai — tus credenciales nunca salen de tu máquina.

---

## Instalación

### Linux (AppImage)

```bash
chmod +x claude-usage-widget-x86_64.AppImage
./claude-usage-widget-x86_64.AppImage
```

#### Requisito: AppIndicator GNOME Shell Extension

Sin esta extensión el icono de bandeja no aparece en GNOME:

1. Instala **AppIndicator and KStatusNotifierItem Support** desde
   [extensions.gnome.org](https://extensions.gnome.org/extension/615/appindicator-support/)
2. Reinicia la sesión de GNOME

### Windows (.exe)

Descarga y ejecuta `claude-usage-widget.exe`.

> **Windows Defender**: el widget lee la cookie `sessionKey` de claude.ai desde el
> perfil del navegador para autenticarse. Esta operación puede activar una alerta de
> Defender. Es seguro: la cookie solo se envía a los servidores de claude.ai y nunca
> a terceros.

---

## Uso

Al arrancar por primera vez se pide confirmación de que tienes sesión activa en
**Firefox** en claude.ai. El widget valida la sesión y guarda la preferencia.

> Solo se soporta Firefox. Chrome y los navegadores basados en Chromium (Opera,
> Opera GX) cifran las cookies en Windows con "App-Bound Encryption" desde 2024,
> que no se puede leer de forma fiable sin recurrir a las mismas técnicas que usa
> el malware de robo de cookies — así que no están soportados.

El icono de bandeja:
- **Verde** → sesión activa, polling correcto
- **Rojo** → sesión caducada o error de red

Click en el icono abre el popup con:
- **Sesión actual**: barra de uso de 5h con tiempo de reset
- **Semanal** (expandible): barra de uso de 7 días

---

## Configuración

| Plataforma | Ruta del config |
|-----------|----------------|
| Linux | `~/.config/claude-usage-widget/config.json` |
| Windows | `%APPDATA%\claude-usage-widget\config.json` |

```json
{
  "browser": "firefox",
  "alert_threshold": 70.0,
  "weekly_expanded": false
}
```

| Campo | Valores | Descripción |
|-------|---------|-------------|
| `browser` | `"firefox"` (único soportado) | Navegador de donde leer la cookie |
| `alert_threshold` | `0.0` – `100.0` | Porcentaje a partir del cual se envía notificación |
| `weekly_expanded` | `true` / `false` | Estado persistido del panel semanal |

---

## Dependencias en tiempo de ejecución (Linux)

- `libnotify-bin` — para notificaciones vía `notify-send`
- AppIndicator GNOME Shell Extension — para el icono de bandeja

---

## Compilar los paquetes

### Linux (AppImage)

```bash
./build-linux.sh
```

Genera `claude-usage-widget-x86_64.AppImage` en la raíz del proyecto. Requiere `python3-venv`
y las cabeceras de compilación de Pillow (`libjpeg-dev`, `zlib1g-dev`) si el `.venv` se crea
desde cero.

Para que aparezca con icono propio en el menú de aplicaciones de GNOME (en vez de ejecutarlo
a mano cada vez):

```bash
./install-linux.sh
```

Copia el AppImage a `~/.local/bin`, el icono a `~/.local/share/icons` y crea el lanzador en
`~/.local/share/applications`. Se ejecuta una sola vez; después el widget aparece como
"Claude Usage Widget" en el menú, sin volver a tocar la terminal.

### Windows (.exe)

Copia la carpeta del proyecto a una máquina Windows y haz doble clic en `build.bat`
(requiere Python 3.11+ instalado y en el PATH). Genera `dist\claude-usage-widget.exe`.

No es posible compilar el `.exe` desde Linux/macOS: PyInstaller no compila de forma cruzada,
tiene que ejecutarse en el sistema operativo de destino.

---

## Cómo funciona

El widget lee la cookie `sessionKey` ya activa en tu navegador (sin pedirte usuario ni
contraseña) y llama directamente a la API interna de claude.ai cada 60 segundos. Esa API
no es pública ni está documentada por Anthropic, así que puede cambiar sin aviso.

Los datos de uso solo se intercambian con `claude.ai`. La cookie de sesión no se envía a
ningún otro sitio ni se guarda en texto plano en disco.

## Limitaciones conocidas

- Depende de la API interna de Claude, que puede romperse si Anthropic la cambia.
- Solo Firefox: Chrome y los navegadores Chromium (Opera, Opera GX) cifran las cookies en
  Windows con "App-Bound Encryption" desde 2024, que no se puede leer sin recurrir a las
  mismas técnicas que usa el malware de robo de sesiones.
- macOS no está soportado — para eso existe [Tokenio](https://github.com/elomid/tokenio).

## Licencia

[MIT](LICENSE)
