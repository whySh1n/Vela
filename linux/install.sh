#!/bin/sh
# Install Vela for the current user on Arch Linux or Debian.
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
PREFIX="${PREFIX:-$HOME/.local}"

if ! command -v python3 >/dev/null 2>&1 || ! command -v mpv >/dev/null 2>&1; then
  if command -v pacman >/dev/null 2>&1; then
    echo "Installing python and mpv with pacman…"
    if [ "$(id -u)" -eq 0 ]; then
      pacman -S --needed --noconfirm python mpv
    else
      sudo pacman -S --needed --noconfirm python mpv
    fi
  elif command -v apt-get >/dev/null 2>&1; then
    echo "Installing python3 and mpv with apt…"
    if [ "$(id -u)" -eq 0 ]; then
      apt-get update
      apt-get install -y python3 mpv
    else
      sudo apt-get update
      sudo apt-get install -y python3 mpv
    fi
  else
    echo "Install python3 and mpv, then run this again."
    exit 1
  fi
fi

mkdir -p "$PREFIX/opt/vela" "$PREFIX/bin" "$PREFIX/share/applications" \
  "$PREFIX/share/icons/hicolor/scalable/apps"

cp -a "$ROOT/vela/." "$PREFIX/opt/vela/"
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
echo "Terminal:  vela"
echo "Desktop:   vela --desk"
echo "If the command is not found, add $PREFIX/bin to your PATH."
