# Σlux 0.1.0a5 — audio cancelable, Markdown y veracidad

- Audio: cancelación de `phonem`, `pronounce` y `ffplay` por grupos de proceso dedicados. Nueva petición reemplaza la anterior; botón y menú «Detener voz».
- Limpieza de Markdown separada del historial visible; realce suave de negritas 1,12× sin cambiar configuración Piper/phonem ni velocidad es-uy.
- Chat: renderizado Markdown en QTextBrowser, conservando el Markdown original en SQLite.
- Honestidad: prompt explícito de no inventar hardware, tiempos ni resultados, interceptor de pedidos explícitos de ejecutar comandos y filtro defensivo contra ciertas falsas afirmaciones de ejecución. No es un verificador universal.
- Ejecución de comandos: NO implementada; diseño de allowlist, comprobación de no destrucción/no escalada y confirmación por cada ejecución en COMMAND_POLICY.md.
- Conserva el avatar verde; no empaqueta Lumen Delicate; respeta preferencias y memoria existentes.
