#!/bin/sh
# Install Vela for the current user on Arch Linux or Debian.
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
PREFIX="${PREFIX:-$HOME/.local}"

has_window() {
  python3 -c "from PySide6.QtWidgets import QApplication" >/dev/null 2>&1
}

install_packages() {
  if command -v pacman >/dev/null 2>&1; then
    echo "Installing Vela's packages with pacman…"
    if [ "$(id -u)" -eq 0 ]; then
      pacman -S --needed --noconfirm python mpv pyside6
    else
      sudo pacman -S --needed --noconfirm python mpv pyside6
    fi
  elif command -v apt-get >/dev/null 2>&1; then
    echo "Installing Vela's packages with apt…"
    if [ "$(id -u)" -eq 0 ]; then
      apt-get update
      apt-get install -y python3 mpv python3-pyside6.qtwidgets python3-pyside6.qtgui python3-pyside6.qtcore
    else
      sudo apt-get update
      sudo apt-get install -y python3 mpv python3-pyside6.qtwidgets python3-pyside6.qtgui python3-pyside6.qtcore
    fi
  else
    echo "Install python3, mpv, and PySide6, then run this again."
    exit 1
  fi
}

if ! command -v python3 >/dev/null 2>&1 || ! command -v mpv >/dev/null 2>&1 || ! has_window; then
  install_packages || true
fi

if ! has_window; then
  echo "The system package was not enough. Installing PySide6 for this user…"
  python3 -m pip install --user PySide6-Essentials
fi

if ! command -v mpv >/dev/null 2>&1 || ! has_window; then
  echo "Vela still needs python3, mpv, and PySide6."
  exit 1
fi

mkdir -p "$PREFIX/opt/vela" "$PREFIX/bin" "$PREFIX/share/applications" \
  "$PREFIX/share/icons/hicolor/scalable/apps"

cp -a "$ROOT/vela/." "$PREFIX/opt/vela/"
rm -rf "$PREFIX/opt/vela/__pycache__" "$PREFIX/opt/vela/desk_web"
cp "$ROOT/share/icons/vela.svg" "$PREFIX/share/icons/hicolor/scalable/apps/vela.svg"

cat > "$PREFIX/bin/vela" << EOF
#!/bin/sh
exec python3 "$PREFIX/opt/vela/__main__.py" "\$@"
EOF
chmod 755 "$PREFIX/bin/vela"

sed "s|__PREFIX__|$PREFIX|g" "$ROOT/share/applications/vela.desktop" > "$PREFIX/share/applications/vela.desktop"
sed "s|__PREFIX__|$PREFIX|g" "$ROOT/share/applications/vela-term.desktop" > "$PREFIX/share/applications/vela-term.desktop"
chmod 644 "$PREFIX/share/applications/vela.desktop" "$PREFIX/share/applications/vela-term.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$PREFIX/share/applications" >/dev/null 2>&1 || true
fi

echo "Vela is installed."
echo "Window:     vela"
echo "Terminal:   vela --term"
echo "If the command is not found, add $PREFIX/bin to your PATH."
