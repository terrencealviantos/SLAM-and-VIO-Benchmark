#!/usr/bin/env bash
# ==============================================================================
# Universal Terminal & GUI Window Launcher
# ==============================================================================
TITLE="${1:-SLAM Terminal}"
CMD="${2:-echo 'No command specified'}"

# Grant X11 access for Docker GUI containers
xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true

if command -v konsole &>/dev/null; then
    konsole --new-tab -p tabtitle="$TITLE" -e bash -c "$CMD; echo; read -p 'Press Enter to exit...' " &
elif command -v gnome-terminal &>/dev/null; then
    gnome-terminal --title="$TITLE" -- bash -c "$CMD; echo; read -p 'Press Enter to exit...' " &
elif command -v xfce4-terminal &>/dev/null; then
    xfce4-terminal --title="$TITLE" -e "bash -c \"$CMD; echo; read -p 'Press Enter to exit...' \"" &
elif command -v xterm &>/dev/null; then
    xterm -T "$TITLE" -e "bash -c \"$CMD; echo; read -p 'Press Enter to exit...' \"" &
else
    echo "[INFO] Launching process in background: $TITLE"
    bash -c "$CMD" &
fi
