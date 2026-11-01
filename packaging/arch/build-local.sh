#!/bin/sh
# Build the Arch package from this checkout's committed HEAD instead of the
# GitHub tag, for testing before a release. The package lands in
# packaging/arch/out/. Install it with: sudo pacman -U packaging/arch/out/vela-*.pkg.tar.zst
set -eu

HERE="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
REPO="$(git -C "$HERE" rev-parse --show-toplevel)"
VERSION="$(sed -n 's/^pkgver=//p' "$HERE/PKGBUILD")"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cp "$HERE/PKGBUILD" "$WORK/"
git -C "$REPO" archive --format=tar.gz --prefix="Vela-$VERSION/" -o "$WORK/vela-$VERSION.tar.gz" HEAD
mkdir -p "$HERE/out"
(cd "$WORK" && PKGDEST="$HERE/out" makepkg --force --cleanbuild --skipchecksums "$@")
ls -1 "$HERE/out"/vela-*.pkg.tar.zst
