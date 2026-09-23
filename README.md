# Σlux 0.1.0a1 — Lumen

First standalone functional version for Linux/X11, initially designed for XFCE. It includes the Lumen avatar, which is compatible with OpenPets from the Lumen package. The original ZIP file is preserved in sumlux/assets/. Σlux renders the atlas internally; it does not require installing or running OpenPets.

## Running

On Linux with Python 3.11+ and an X11 graphical environment (XFCE recommended):

```bash
cd sumLux-0.1.0a1
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

## Voice

In Preferences, you can enable response playback using `espeak-ng`, `espeak`, or `spd-say` (if installed); this feature is disabled by default. **Voice input, dictation, and lip-syncing are not yet implemented**. This generic local voice is not a custom Lumen voice.

## Status and Next Steps

Implemented in this alpha: animated avatar, manual gestures, chat interface, compatible model protocol, SQLite history, optional local TTS, preferences, and a Linux launcher. Pending: actual visual testing on XFCE, formal integration into `sum.sh`/`sumBuild`, custom voice selection and management, STT/microphone support, memory with summarization/retrieval, desktop capabilities with explicit permissions, and Windows/Android packages.

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
