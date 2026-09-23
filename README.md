# Σlux 0.1.0a3 — Lumen (avatar público)

First standalone functional version for Linux/X11, initially designed for XFCE. It includes the Lumen avatar, which is compatible with OpenPets from the Lumen package. The public green OpenPets ZIP is preserved in sumlux/assets/. No private variant is shipped. Σlux renders the atlas internally; it does not require installing or running OpenPets.

## Running

This release corrects avatar selection in the previous source archive: a stale build/lib directory contained a different avatar while the source assets had been replaced. This release ships a single public avatar, removes stale build artifacts, and increments the version so an installer can replace an older installation.

On Linux with Python 3.11+ and an X11 graphical environment (XFCE recommended):

```bash
cd sumlux-0.1.0a2
bash scripts/install.sh
~/.local/bin/sumlux
```

The installer creates a dedicated venv at `~/.local/share/sum/lux/venv`, installs `PySide6` via pip, and adds the application to the menu with the `Σlux` icon. **Requires access to PyPI or a local cache containing PySide6.** Root permissions are not required. Installation does not launch Σlux automatically. To enable autostart: `bash scripts/install.sh --autostart`.

Manual mode without installing the launcher: `python3 -m venv .venv && .venv/bin/pip install . && .venv/bin/sumlux`.

## Avatar

- Transparent, frameless, always-on-top, draggable window; double-click: chat; right-click: menu.
- Animated states from the OpenPets 8×9 atlas: idle (6), right (8), left (8), wave (4), jump (5), rest (8), wait (6), walk (6), think (6).
- Configurable scale and walking behavior; by default, it does **not** walk across the desktop.
- Visual testing was not performed on a real X11 desktop within the build environment; Wayland may limit transparency, always-on-top behavior, input masking, and repositioning.

## Conversation and Memory

Optional dialogue connects to an **OpenAI Chat Completions-compatible** server. **Local Ollama** is suggested by default, though it is not automatically enabled or installed. For Ollama: download your chosen model and run the service—e.g., `ollama pull llama3.2`. Open Right-click → Preferences, activate the model, and select the URL/model. Defaults: `http://127.0.0.1:11434/v1/chat/completions`, model `llama3.2`. A different compatible server can be used via a configurable URL. For a remote server, **sent messages are directed to that server**. If required, the API token is read from the `SUMLUX_API_KEY` environment variable; it is never written to the configuration file.

Sent messages and received responses are stored in an SQLite database at `~/.local/share/sum/lux/lumen.sqlite3` (or under `$XDG_DATA_HOME`); up to the **24 most recent messages** are sent to the model to maintain contextual continuity. There is no semantic summarization or automatic access to ChatGPT memories or past conversations. A **Clear history…** button allows for the deletion of local messages from within the app; user-created backup files remain unaffected.

Preferences are stored in `~/.config/sum/lux.toml` (or under `$XDG_CONFIG_HOME`) with restricted user permissions.

## Voz — integración con phonem 1.6.0 / pronounce 0.6.1

El motor preferido es el proyecto independiente `phonem` + `pronounce` ya instalado por el usuario. No se distribuye ni reinstala su toolkit, modelos Piper ni configuraciones personales dentro de Σlux. De manera predeterminada, el perfil de voz es `es-uy`; `es` también es un alias de `es-uy` en phonem. La voz y su velocidad se consultan a la configuración existente de phonem, **no se duplican ni sobrescriben** en Σlux.

El flujo lógico es `phonem -t "texto" -l es-uy | pronounce -l es-uy`, con salida WAV a un temporal y `ffplay` para reproducir sin depender de que stdout de una ventana gráfica sea una TTY. Los procesos se ejecutan como argumentos, no mediante un shell. La reproducción corre en un hilo para no congelar la ventana. La opción eSpeak sigue disponible explícitamente, **no hay fallback silencioso** a una voz distinta cuando falla phonem.

Verificar desde la terminal: `phonem -t "La casa roja" -l es-uy | pronounce -l es-uy` y `pronounce --list-models es`. Si el lanzador gráfico no hereda `~/.local/bin` en PATH, Σlux busca los ejecutables ahí también, o en `PHONEM_BIN_DIR` si está definida. La síntesis informa errores en stderr de Σlux; en una futura versión se mostrarán dentro de la ventana.

La voz está desactivada hasta que se marque «Leer las respuestas en voz alta». Preferencias ofrece motor, perfil y botón de prueba. **Reconocimiento de micrófono, lip-syncing y ajustes de voz finos en UI todavía no están implementados**. El usuario administra esos ajustes desde su proyecto phonem.


## Status and Next Steps

Implemented in this alpha: animated avatar, manual gestures, chat interface, compatible model protocol, SQLite history, optional local TTS, preferences, and a Linux launcher. Pending: actual visual testing on XFCE, formal integration into `sum.sh`/`sumBuild`, an in-app phonem voice inventory, STT/microphone support, memory with summarization/retrieval, desktop capabilities with explicit permissions, and Windows/Android packages.

This release is a **new and separate** package; it does not alter any previous SUM releases. Automatic integration with `sumGUI` or `sumTerminal` is not guaranteed without inspecting the current SUM snapshot. ## Testing

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q sumlux
```

On a system with X11: launch `sumlux`, drag the window, open the menu via right-click, chat after connecting to Ollama, restart, and verify that the history persists.

## Uninstalling

`bash scripts/uninstall.sh` removes the virtual environment and launchers while preserving local memory and configuration. To delete the data, the user must separately remove `~/.local/share/sum/lux/lumen.sqlite3` and `~/.config/sum/lux.toml` (and their copies).

License: GNU GPL v2 or later (see `COPYING`).

<p align=center><b>- oOo -</b></p>
