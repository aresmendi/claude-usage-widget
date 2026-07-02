# Manual Smoke Test — Widget Barra Uso Tokens

Ejecutar tras instalar las dependencias (`pip install -r requirements.txt`) y tener
un navegador con sesión activa de claude.ai.

## Requisitos previos (Linux)

- [ ] Extensión GNOME **AppIndicator and KStatusNotifierItem Support** instalada y activa
- [ ] `notify-send` disponible (`libnotify-bin`)

---

## S-01: Arranque y primer ciclo

- [ ] La app arranca sin traza de error en la consola
- [ ] El icono aparece en la bandeja del sistema (color verde)
- [ ] Pasados ~60 s, el popup muestra valores numéricos en "Sesión actual"
- [ ] El label bajo la barra muestra `XX.X% · Reset: <fecha ISO>`

## S-02: Popup — layout por defecto

- [ ] Click en el icono de bandeja abre el popup
- [ ] La sección "Sesión actual" está siempre visible con su barra de progreso
- [ ] La sección "Semanal" aparece **colapsada** (flecha `▶`)
- [ ] Click en `▶` expande la sección y muestra la barra semanal
- [ ] La flecha cambia a `▼`
- [ ] Click en `▼` vuelve a colapsar
- [ ] Reiniciar la app: el estado expandido/colapsado se **persiste**

## S-03: Dismiss por click fuera

- [ ] Con el popup abierto, hacer click fuera de la ventana
- [ ] El popup se cierra inmediatamente

## S-04: Cambio de color del icono

- [ ] Invalidar manualmente el `sessionKey` en el config JSON y reiniciar
- [ ] El icono cambia a **rojo** dentro de los 5 s del siguiente ciclo de polling
- [ ] Restaurar la sesión → el icono vuelve a **verde**

## S-05: Notificación de umbral

- [ ] Cambiar `alert_threshold` a `0.1` en el config JSON y reiniciar
- [ ] En el siguiente ciclo de polling, aparece una notificación del sistema
- [ ] Con el mismo `reset_at`, no llega una segunda notificación
- [ ] Bajar el threshold por debajo del uso actual y subir de nuevo: llega otra notificación

## S-06: Advertencia GNOME (solo Linux sin extensión)

- [ ] Desactivar la extensión AppIndicator y reiniciar la app
- [ ] La consola (o log) muestra el mensaje de advertencia sobre AppIndicator
- [ ] La app no rompe; continúa el ciclo de polling aunque el icono no sea visible
