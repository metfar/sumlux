#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${XDG_DATA_HOME:-$HOME/.local/share}/sum/lux/venv"
BIN="$HOME/.local/bin"
APP="$HOME/.local/share/applications"
ICON="$HOME/.local/share/icons/hicolor/128x128/apps/sumlux.png"
mkdir -p "$(dirname "$VENV")" "$BIN" "$APP" "$(dirname "$ICON")"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install "$ROOT"
ln -sfn "$VENV/bin/sumlux" "$BIN/sumlux"
cp "$ROOT/sumlux/assets/sumlux.png" "$ICON"
cat > "$APP/sumlux.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Σlux · Lumen Pet
Comment=Lumen desktop companion for SUM
Exec=$VENV/bin/sumlux
Icon=$ICON
Terminal=false
Categories=Utility;
StartupNotify=false
DESKTOP
if [[ "${1:-}" == "--autostart" ]]; then
    mkdir -p "$HOME/.config/autostart"
    cp "$APP/sumlux.desktop" "$HOME/.config/autostart/sumlux.desktop"
fi
printf '\nInstalado. Ejecutar: %s/bin/sumlux\n' "$VENV"
printf 'El historial local NO se borra al reinstalar.\n'
