# Vela — reference

Vela is a Linux application. The window is Qt (PySide6). The terminal is curses. Both play through mpv and store the library in `~/.config/vela/library.json`.

## Programs

| Command | What opens |
| --- | --- |
| `vela` | The window |
| `vela --term` | The terminal |
| `vela --desk` | Not used. Older installs may still pass it; the current launcher ignores unknown flags and opens the window. |

`--desk` is not a browser. There is no local web server in the package.

## Files

| Path | Role |
| --- | --- |
| `linux/vela/__main__.py` | Chooses window or terminal |
| `linux/vela/gui.py` | The Qt window |
| `linux/vela/tui.py` | The curses terminal |
| `linux/vela/player.py` | mpv, its IPC socket, devices, balance, tone |
| `linux/vela/radio.py` | Radio Browser search |
| `linux/vela/library.py` | `~/.config/vela/library.json` |
| `packaging/arch/PKGBUILD` | The Arch package. Installs to `/usr/lib/vela` and `/usr/bin/vela`. `build-local.sh` next to it builds from the checkout instead of the release tag. |
| `linux/make_zip.py` | Rebuilds `public/vela-linux.zip`, the download on the web page. `linux/zip_test.py` fails when it is stale. |
| `linux/install.sh` | One command. Installs mpv and PySide6, then copies Vela to `~/.local` and adds that `bin` to the shell path. |

## Directory

Search uses the public Radio Browser API. Vela tries `de1`, then `de2`, then `fi1`, with a Vela user agent. Broken stations are hidden. Results are ordered by votes, up to 40.

| Field | Sent as |
| --- | --- |
| Search stations | `name` |
| Country | `country` |
| Genre | `tag` |

The stream address prefers `https://`. An `http://` address is kept when that is all the directory has. mpv tries the `https://` form first, then the original.

## Playback

One mpv process, started without mpv's own config or scripts. The address has to be plain `http://` or `https://`. Directory stations cannot point at your own machine or a private network. A stream you add yourself may use an address on your network, but still not a file, a password in the URL, or localhost. mpv is limited to those web protocols.

The control socket lives in your runtime directory, not in a shared temp folder. Pause, volume, mute, and the audio filters go through that socket. Changing the output device restarts mpv so the new sink is used from the first sample.

The window does not route audio through Qt. Qt draws the controls. mpv owns the sound.

## Route

| Control | Window | Terminal | Effect |
| --- | --- | --- | --- |
| Output | Output menu | `o` | `mpv --audio-device`. `auto` is the system default. |
| Balance | Slider | `[` `]` | ffmpeg `stereotools`, steps of 0.2 in the terminal. |
| Tone | Flat, voice, night, bass | `e` | Voice is a high-pass and a little treble. Night pulls bass and treble down. Bass lifts the low end. |

The filter string is an allow-list. The device id has to match the characters mpv prints. Both are stored under `route` in the library file. A volume change does not clear the route.

Tone and balance need an mpv build with those ffmpeg filters. If a tone will not open a stream, set it back to flat.

## Library

Saved stations and custom streams, up to 200 each. A custom stream must be `http://` or `https://`. The library file is private to your user and replaced atomically. The window and the terminal share it, including when both are used at different times. They do not sync while both are open. The installer refuses to run as root.

## Keys

The window ignores letter keys while a text field is focused, except Escape, which leaves the field.

The terminal reads a line for `/`, `:place`, `:tag`, and `:add`.

## Install packages

Arch: `python`, `mpv`, `pyside6`.

Debian: `python3`, `mpv`, `python3-pyside6.qtwidgets`, `python3-pyside6.qtgui`, `python3-pyside6.qtcore`.

If the distro packages are not available, the installer uses `pip install --user PySide6-Essentials`.
