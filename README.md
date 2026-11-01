# Vela

Vela is a Linux radio player for Arch and Debian. One library, two programs:

- **Window** — `vela` opens a dark player. Search, save, add a stream, pick the output, set the balance and the tone.
- **Terminal** — `vela --term` is the same stations from the keyboard. Sound is mpv in both.

It is not a website. The page in this repository is only a picture of the window and the download.

## Install

```sh
unzip vela-linux.zip
cd vela-linux
chmod +x install.sh
./install.sh
```

The script installs `python3`, `mpv`, and PySide6 with pacman or apt, then puts `vela` on your `PATH`.

```sh
vela
vela --term
```

If a new terminal cannot find the command, add `$HOME/.local/bin` to your `PATH`.

## Manuals

- [Window and terminal](docs/linux.md)
- [Reference](docs/reference.md)

## Stations

Listings come from the public [Radio Browser](https://www.radio-browser.info/) directory. Vela does not host the audio. mpv plays the stream, including stations that only offer `http://`.

Saved stations live in `~/.config/vela/library.json`.

## License

[MIT](LICENSE)
