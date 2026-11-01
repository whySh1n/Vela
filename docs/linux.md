# Vela on Linux — short manual

The installable player for Arch Linux and Debian. It is the `linux/` folder in this repo, and the **Arch & Debian** download in the browser app.

You get two programs and one library:

- `vela` — terminal, sound through mpv
- `vela --desk` — desktop page, served only on your machine

## Install

From the `linux/` directory:

```sh
chmod +x install.sh
./install.sh
```

The script installs `python3` and `mpv` with pacman or apt, then copies Vela to `~/.local` and adds `~/.local/bin/vela`.

If a new terminal cannot find the command:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

Application menu entries are **Vela** (desktop) and **Vela Terminal**.

## Listen

```sh
vela
vela --desk
```

Leave the desktop command running. Ctrl-C closes it.

The terminal starts on the top of the directory. `j` and `k` move, Enter plays, `q` quits.

| Key | Action |
| --- | --- |
| j k or arrows | Move |
| Enter | Play |
| Space | Pause |
| f | Save or unsave |
| n p | Next or previous |
| m | Mute |
| s | Sleep |
| + − | Volume |
| / | Search. Also `:place France`, `:tag jazz`, `:add Name \| https://stream` |
| a | Add a stream (it asks for a name, then the address) |
| 1 | Cycle Dial, Saved, Mine |
| ? | Keys |
| q | Quit |

Click a row if your terminal sends mouse clicks.

## Your stations

Saved stations and streams you added are in `~/.config/vela/library.json`. The terminal and the desktop read and write that same file. Volume is stored there too.

A stream address must start with `http://` or `https://`.

## When a browser station will not play

Some stations only offer `http://`. The browser may refuse that on a secure page. mpv does not. If a station failed in the browser, try it here.
