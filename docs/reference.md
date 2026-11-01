# Vela — reference

Full behavior of the browser app and the Linux player.

## What it is

Vela plays live internet radio. It does not store shows, build a library of files, or sign you in.

There are three lists:

| List | Contents |
| --- | --- |
| Dial | Results from the station directory |
| Saved | Stations you starred |
| Mine | Streams you added by address |

A station you add is also starred, so it shows under both Mine and Saved.

## Directory

Search goes to the public Radio Browser API. Vela tries `de1`, then `de2`, then `fi1` of `api.radio-browser.info`, with a Vela user agent. Broken stations are hidden. Results are ordered by votes, up to 40, and duplicates are dropped.

Search fields:

| Field | Sent as |
| --- | --- |
| Search stations | `name` |
| Place | `country` |
| Genre chip or `:tag` | `tag` |

Name and place wait briefly before a new request, so typing does not hit the directory on every letter. Choosing a genre searches immediately and returns you to Dial.

The stream address prefers an `https://` URL from the directory. If the catalog only has `http://`, that address is kept.

Vela does not count a “click” back to Radio Browser. Playback uses the URL from search.

## Playback in the browser

One audio element is shared by Desk and Terminal.

On play, Vela tries the address as `https://` first. On an ordinary `http://` page it then tries the original `http://` URL. On an `https://` page it does not fall back to `http://`, because the browser would block it. The message in that case says the Linux app can still play the station.

A station that does not start within 10 seconds is marked off air. Switching station cancels the attempt in progress. Pausing during “tuning” cancels it too.

The clock next to the transport is how long you have been playing this station, not a position in a file. Live streams do not have a meaningful position.

Volume is 0–100 in the interface and 0–1 on the audio element. Mute keeps your level and sends silence. Moving the slider above zero unmutes.

## Sleep

The header button cycles 15, 30, 45, 60, 90 minutes, then off. The countdown is from the moment you set it. At zero, playback pauses, the timer clears, and the stage says the dial rested. Starting a station clears that note. Sleep is not remembered after you close the tab.

## Keyboard

Handled on the window, ignored while Ctrl, Alt, or a meta key is held, and ignored while a text field is focused (except Escape, which blurs the field and closes dialogs).

| Key | Action |
| --- | --- |
| Space | Pause, or play the highlight if nothing is loaded |
| Enter | Play the highlight |
| J, Arrow Down | Highlight moves down, and stops at the end |
| K, Arrow Up | Highlight moves up, and stops at the start |
| N / P | Play the next or previous station in the visible list |
| F | Star or unstar the highlight |
| M | Mute |
| S | Cycle sleep |
| A | Open Add |
| / | Focus search (Desk) or the command line (Terminal) |
| \ | Toggle Desk and Terminal |
| + or = | Volume up 5 points |
| − | Volume down 5 points |
| ? | Key card |
| Escape | Close the card or the add form |

Terminal commands are the Enter key inside the command field, not the global keys above.

| Command | Effect |
| --- | --- |
| text, or `/text` | Set the search and show Dial |
| `:place France` | Set the country and show Dial. Empty clears it |
| `:tag jazz` | Set the tag and show Dial. Empty clears it |
| `:add Name \| https://…` | Add a stream, show Mine, and play it |
| `:add Name https://…` | Same, when the address is the last word |
| `:help`, `help`, `?` | Open the key card |

Add fails closed: the address must be a real `http:` or `https:` URL. `javascript:` and other schemes are rejected.

## What the browser stores

`localStorage` key `vela`, via Zustand persist. Hydration waits until after the first paint so the server render and the first client render match.

Stored:

- mode (`desk` or `terminal`)
- volume and mute
- favorites (up to 200)
- custom streams (up to 200)

Not stored: the current station, sleep, or the search you had typed. The page does not autoplay.

Removing a custom stream also removes it from Saved.

## Desk

Wide screens: a scrolling list and a stage. Narrow screens: the list first, then a compact now-playing bar with play and volume.

Each row shows a two-letter monogram, the name, a short place and up to two tags, and the bitrate when the directory sent one. Country names that are the long official forms are shortened (`United States`, `United Kingdom`). If a name is still very long, the country code is shown instead.

The stage states are Quiet, Tuning, On air, Paused, Off air, and Rested.

## Terminal

Same data and the same player. The highlight is a `>` on the selected row. Genre names and Dial / Saved / Mine are buttons, so a mouse or a phone still works.

## Linux player

Python 3, standard library only, plus mpv for sound. No pip packages.

| File | Role |
| --- | --- |
| `linux/vela/__main__.py` | `vela` or `vela --desk` |
| `linux/vela/radio.py` | Directory client, same servers and the same field mapping |
| `linux/vela/library.py` | `~/.config/vela/library.json`, written atomically |
| `linux/vela/player.py` | mpv, with a JSON IPC socket for pause, mute, and volume |
| `linux/vela/tui.py` | Curses interface |
| `linux/vela/desk.py` | Local server on `127.0.0.1` and a random port |
| `linux/vela/desk_web/` | The desktop page |

`install.sh` detects pacman or apt, installs `python3` and `mpv` if they are missing, and installs under `~/.local` (override with `PREFIX`).

The desktop page talks only to that local server: `/api/search` and `/api/library`. It is not an open proxy. Library posts are capped at 256 KB and checked before they are saved.

mpv is started with `--no-video`. An `http://` URL is tried as `https://` first, then as `http://`. If mpv is missing, the terminal says so instead of failing silently.

Sleep, favorites, and custom streams behave like the browser app. The `1` key cycles Dial, Saved, and Mine. Mouse clicks play a row when the list is not scrolled.

## Web app layout

TanStack Start, React, and Tailwind CSS 4.

| Path | Role |
| --- | --- |
| `src/routes/index.tsx` | The page |
| `src/components/vela/app.tsx` | Header, search, keyboard, mode |
| `src/components/vela/desk.tsx` | Desk layout |
| `src/components/vela/terminal.tsx` | Terminal layout |
| `src/components/vela/engine.tsx` | Audio |
| `src/components/vela/rows.tsx` | Station rows |
| `src/components/vela/overlays.tsx` | Add form and key card |
| `src/lib/radio.functions.ts` | Server-side directory proxy |
| `src/lib/stations.ts` | Types, genres, formatting |
| `src/lib/store.ts` | Saved state |
| `src/styles.css` | Color and type |

The palette is a warm charcoal with one amber accent. Type is Outfit for the desk and IBM Plex Mono for the terminal, metadata, and the command line.

## Develop

```sh
npm install
npm run dev        # local dev server
npm run build      # production build
npm run typecheck
```

The directory proxy runs on the server so the browser does not have to send a custom user agent and so a failed Radio Browser host can be retried.

## Limits

- 40 stations per search.
- 200 saved stations and 200 custom streams.
- No accounts, no sync between browsers, and no sync between the browser and the Linux library. They are separate on purpose: the browser uses `localStorage`, Linux uses `~/.config/vela/library.json`.
- Playback depends on the station. A listing can be up and the stream can still be down.
- Secure pages cannot play a stream that is only available as `http://`.
