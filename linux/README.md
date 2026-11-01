# Vela

A quiet radio for late nights. Two programs, one library of saved stations.

- **Terminal** — keyboard-first, plays through mpv
- **Desktop** — a small window in your browser, served only on your machine

Works on Arch Linux and Debian. Saved stations live in `~/.config/vela/library.json`, shared by both.

## Install

```sh
chmod +x install.sh
./install.sh
```

The script installs `python3` and `mpv` with pacman or apt, then puts `vela` in `~/.local/bin`.

If a new terminal cannot find `vela`, add this to your shell profile:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

## Use

```sh
vela          # terminal
vela --desk   # desktop
```

Menu entries are **Vela** and **Vela Terminal**.

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

Click a row if your terminal sends mouse events.

Stations come from the public [Radio Browser](https://www.radio-browser.info/) directory. Streams that are only available over plain http still play here. A secure browser sometimes cannot play those.

Output, balance, and tone are applied by mpv and remembered in the library file. `o` walks the devices mpv can see, including PipeWire and Pulse sinks. `[` and `]` move the balance. `e` cycles flat, voice, night, and bass.
