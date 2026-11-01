# Vela

A radio player for Arch Linux and Debian. `vela` opens the window. `vela --term` is the same stations in the terminal. Sound is mpv.

## Install

Paste this into a terminal. It asks for your password once, then Vela is in your applications.

```sh
curl -fsSL https://raw.githubusercontent.com/whySh1n/Vela/main/linux/install.sh | sh
```

Open **Vela** from your applications. A new terminal can also run `vela`.

### Arch package

Each [release](https://github.com/whySh1n/Vela/releases) has a package. pacman installs mpv and PySide6 with it.

```sh
sudo pacman -U vela-0.1.0-1-any.pkg.tar.zst
```

To build it yourself: `cd packaging/arch && makepkg -si`.

If you used the install command before, remove that copy so it does not shadow the package:

```sh
rm -rf ~/.local/opt/vela ~/.local/bin/vela ~/.local/share/applications/vela*.desktop ~/.local/share/icons/hicolor/scalable/apps/vela.svg
```

Your saved stations in `~/.config/vela/` are kept.

## Manuals

- [Window and terminal](docs/linux.md)
- [Reference](docs/reference.md)

## Stations

Listings come from the public [Radio Browser](https://www.radio-browser.info/) directory. Vela does not host the audio. Saved stations live in `~/.config/vela/library.json`.

## License

[MIT](LICENSE)
