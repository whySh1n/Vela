# Vela

A radio player for Arch Linux and Debian. Two programs, one library.

- **Window** — `vela`
- **Terminal** — `vela --term`, sound through mpv

Saved stations live in `~/.config/vela/library.json`.

## Install

```sh
chmod +x install.sh
./install.sh
```

The script installs `python3`, `mpv`, and PySide6 with pacman or apt, then puts `vela` in `~/.local/bin`.

If a new terminal cannot find `vela`, add this to your shell profile:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

## Use

```sh
vela
vela --term
```

Menu entries are **Vela** and **Vela Terminal**.

The longer manual is `docs/linux.md` in the source repository.

### Terminal keys

| Key | Action |
| --- | --- |
| j k or arrows | Move |
| Enter | Play |
| Space | Pause |
| f | Save or unsave |
| n p | Next or previous |
| m | Mute |
| o | Next audio output |
| [ ] | Balance, left or right |
| e | Tone: flat, voice, night, bass |
| s | Sleep timer |
| / | Search. Also `:place France`, `:tag jazz`, `:add Name \| https://stream` |
| a | Add your own stream |
| 1 | Cycle Dial, Saved, Mine |
| q | Quit |

Output, balance, and tone are applied by mpv and remembered in the library file. `o` walks the devices mpv can see, including PipeWire and Pulse sinks.

Stations come from the public [Radio Browser](https://www.radio-browser.info/) directory. Streams that are only available over plain http still play here.
