# Vela

A radio player for Arch Linux and Debian. The window and the terminal share one library.

## Install

Paste this into a terminal on Arch or Debian. It asks for your password once.

```sh
curl -fsSL https://raw.githubusercontent.com/whySh1n/Vela/main/linux/install.sh | sh
```

Open **Vela** from your applications. A new terminal can also run `vela`, or `vela --term` for the keyboard player.

## Window

The list fills the window. Type in **Search stations**, or a **Country**, or pick a genre. **Dial**, **Saved**, and **Mine** sit in the top bar. **Dial** is the directory, **Saved** is what you starred, **Mine** is a stream you added.

Click a row to play it. The round button plays and pauses. **Prev** and **Next** move through the list you are looking at. The star saves a station. What is playing, the volume, and **Sleep** sit on the bar along the bottom, with **Output**, **Balance**, and **Tone**. When the station sends it, that bar also names the artist and the song.

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

The line under the station names the artist and the song when the station sends them.

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
