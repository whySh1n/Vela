# Vela

Vela is a late-night internet radio. One dial, two ways to listen: a visual **desk** and a keyboard **terminal**. Search the public station directory, save the ones you keep, or add a stream of your own.

No account. Nothing you save leaves the machine you are using.

## Listen

| | Desk | Terminal |
| --- | --- | --- |
| Where | The browser | The same app, or `vela` on Linux |
| How | Search, tap, play | `j` `k`, Enter, `/` to search |
| Sound | The browser | The browser, or mpv on Linux |

In the browser, **Desk** and **Terminal** in the header switch modes. `\` does the same when you are not typing.

On Arch Linux and Debian, the `linux/` folder is a small player you install later. The terminal uses mpv. The desktop opens a local page. They share one library.

## Manuals

- [Short manual](docs/manual.md) — using Vela in the browser
- [Linux manual](docs/linux.md) — install, keys, and your own streams
- [Reference](docs/reference.md) — full behavior, storage, and how the app is built

## Run it yourself

Node.js 22 or newer.

```sh
npm install
npm run dev
```

Then open the address the dev server prints.

```sh
npm run build
npm run typecheck
```

## Stations

Listings come from the public [Radio Browser](https://www.radio-browser.info/) directory. Vela does not host the audio. Playback goes straight from the station’s stream to your browser or to mpv.

Some stations only publish an `http://` stream. A secure page tries the `https://` version of that address and skips the station if that fails. The Linux player can still open the plain stream.

## License

[MIT](LICENSE)
