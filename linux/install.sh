#!/bin/sh
# One step. From a terminal on Arch or Debian:
#   curl -fsSL https://raw.githubusercontent.com/whySh1n/Vela/main/linux/install.sh | sh
set -eu

if [ "$(id -u)" -eq 0 ]; then
  echo "Run this as your user. Vela will ask for your password."
  exit 1
fi

PREFIX="${PREFIX:-$HOME/.local}"
case "$PREFIX" in
  /*) ;;
  *) echo "PREFIX must be a full path."; exit 1 ;;
esac
case "$PREFIX" in
  *[!A-Za-z0-9/_.-]*) echo "PREFIX has characters Vela will not use."; exit 1 ;;
esac
FETCHED=""

cleanup() {
  if [ -n "$FETCHED" ]; then
    rm -rf "$FETCHED"
  fi
}
trap cleanup EXIT

if [ -f "${0:-}" ]; then
  ROOT="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
fi
if [ -z "${ROOT:-}" ] || [ ! -f "$ROOT/vela/__main__.py" ]; then
  FETCHED="$(mktemp -d)"
  echo "Downloading Vela…"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "https://github.com/whySh1n/Vela/archive/refs/heads/main.tar.gz" | tar -xz -C "$FETCHED"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "https://github.com/whySh1n/Vela/archive/refs/heads/main.tar.gz" | tar -xz -C "$FETCHED"
  else
    echo "This installer needs curl. Install curl, then run the command again."
    exit 1
  fi
  ROOT="$FETCHED/Vela-main/linux"
fi

if [ ! -f "$ROOT/vela/__main__.py" ]; then
  echo "Vela did not download. Check the network and run the command again."
  exit 1
fi

has_window() {
  python3 -c "from PySide6.QtWidgets import QApplication" >/dev/null 2>&1
}

install_packages() {
  if command -v pacman >/dev/null 2>&1; then
    echo "Installing mpv and the window library…"
    if [ "$(id -u)" -eq 0 ]; then
      pacman -S --needed --noconfirm python mpv pyside6
    else
      sudo pacman -S --needed --noconfirm python mpv pyside6
    fi
  elif command -v apt-get >/dev/null 2>&1; then
    echo "Installing mpv and the window library…"
    if [ "$(id -u)" -eq 0 ]; then
      apt-get update
      apt-get install -y python3 mpv python3-pyside6.qtwidgets python3-pyside6.qtgui python3-pyside6.qtcore
    else
      sudo apt-get update
      sudo apt-get install -y python3 mpv python3-pyside6.qtwidgets python3-pyside6.qtgui python3-pyside6.qtcore
    fi
  else
    echo "Vela installs on Arch (pacman) and Debian (apt)."
    exit 1
  fi
}

if ! command -v python3 >/dev/null 2>&1 || ! command -v mpv >/dev/null 2>&1 || ! has_window; then
  install_packages || true
fi

if ! has_window; then
  echo "Installing the window library for this user…"
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

remember_path() {
  bin="$PREFIX/bin"
  line="export PATH=\"$bin:\$PATH\""
  for rc in "$HOME/.bashrc" "$HOME/.profile"; do
    if [ -f "$rc" ] && grep -F -q "$bin" "$rc"; then
      continue
    fi
    printf '\n# Vela\n%s\n' "$line" >> "$rc"
  done
  if [ -f "$HOME/.zshrc" ] && ! grep -F -q "$bin" "$HOME/.zshrc"; then
    printf '\n# Vela\n%s\n' "$line" >> "$HOME/.zshrc"
  fi
  export PATH="$bin:$PATH"
}

remember_path

echo
echo "Vela is ready."
echo "Open Vela from your applications."
echo "A new terminal can also run:  vela"
