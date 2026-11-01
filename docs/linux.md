# Vela

A radio player for Arch Linux and Debian. The window and the terminal share one library.

## Install

```sh
chmod +x install.sh
./install.sh
```

The script installs `python3`, `mpv`, and PySide6 with pacman or apt, then copies Vela to `~/.local`.

```sh
vela          # window
vela --term   # terminal
```

If the command is not found:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

The application menu has **Vela** and **Vela Terminal**.

## Window

The list is the directory. Type in **Search stations**, or a **Country**, or pick a genre. **Dial** is the directory, **Saved** is what you starred, **Mine** is a stream you added.

Click a row to play it. The amber button pauses. **Prev** and **Next** move through the list you are looking at. The star saves a station.

**Add** asks for a name and an `http://` or `https://` address.

**Sleep** cycles 15, 30, 45, 60, and 90 minutes, then off. At the end, Vela pauses.

**Output** is the device mpv can see: speakers, headphones, HDMI, a PipeWire or Pulse sink. **Balance** moves the stereo image. **Tone** is flat, voice, night, or bass. These are remembered.

| Key | Action |
| --- | --- |
| Space | Play or pause |
| J / K or arrows | Move |
| Enter | Play the highlighted station |
| F | Save or unsave |
| N / P | Next or previous |
| M | Mute |
| S | Sleep |
| A | Add a stream |
| / | Search |
| Esc | Leave the search field |
| Ctrl+Q | Quit |

## Terminal

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
| s | Sleep |
| / | Search. Also `:place France`, `:tag jazz`, `:add Name \| https://stream` |
| a | Add a stream |
| 1 | Cycle Dial, Saved, Mine |
| q | Quit |

## Your stations

`~/.config/vela/library.json` holds saved stations, your own streams, volume, output, balance, and tone. Both programs read and write that file.
