#!/usr/bin/env bash
set -euo pipefail
VENV="${XDG_DATA_HOME:-$HOME/.local/share}/sum/lux/venv"
rm -f "$HOME/.local/bin/sumlux" "$HOME/.local/share/applications/sumlux.desktop" "$HOME/.config/autostart/sumlux.desktop" "$HOME/.local/share/icons/hicolor/128x128/apps/sumlux.png"
rm -rf -- "$VENV"
printf 'Σlux desinstalado; configuración e historial conservados.\n'
