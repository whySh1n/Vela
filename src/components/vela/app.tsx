import { useEffect, useState } from "react";
import { Download, Moon, Volume2, VolumeX } from "lucide-react";
import { searchStations } from "@/lib/radio.functions";
import { filterStations, formatClock, isStreamUrl, newId, type Station } from "@/lib/stations";
import { useLibrary } from "@/lib/store";
import { EngineProvider, useEngine } from "@/components/vela/engine";
import { Desk } from "@/components/vela/desk";
import { Terminal } from "@/components/vela/terminal";
import { AddStation, HelpCard } from "@/components/vela/overlays";
import type { Scope } from "@/components/vela/dial";

export function VelaApp() {
  useEffect(() => {
    void useLibrary.persist.rehydrate();
  }, []);

  return (
    <EngineProvider>
      <Shell />
    </EngineProvider>
  );
}

function Shell() {
  const mode = useLibrary((state) => state.mode);
  const setMode = useLibrary((state) => state.setMode);
  const volume = useLibrary((state) => state.volume);
  const setVolume = useLibrary((state) => state.setVolume);
  const muted = useLibrary((state) => state.muted);
  const toggleMute = useLibrary((state) => state.toggleMute);
  const favorites = useLibrary((state) => state.favorites);
  const custom = useLibrary((state) => state.custom);
  const addCustom = useLibrary((state) => state.addCustom);
  const toggleSaved = useLibrary((state) => state.toggleSaved);
  const engine = useEngine();

  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("");
  const [tag, setTag] = useState("");
  const [scope, setScope] = useState<Scope>("dial");
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [selected, setSelected] = useState(0);
  const [retry, setRetry] = useState(0);
  const [help, setHelp] = useState(false);
  const [adding, setAdding] = useState(false);
  const [commandNote, setCommandNote] = useState<string | null>(null);

  const visible =
    scope === "saved" ? filterStations(favorites, query) : scope === "mine" ? filterStations(custom, query) : stations;

  useEffect(() => {
    if (scope !== "dial") return;
    const controller = new AbortController();
    const delay = query.trim() || country.trim() ? 280 : 0;
    if (delay === 0) setLoading(true);
    const timer = window.setTimeout(() => {
      setLoading(true);
      setFetchError(null);
      const data: { name?: string; tag?: string; country?: string } = {};
      const name = query.trim();
      const place = country.trim();
      if (name) data.name = name;
      if (tag) data.tag = tag;
      if (place) data.country = place;
      void searchStations({
        data,
        signal: controller.signal,
      })
        .then((result) => {
          if (controller.signal.aborted) return;
          setStations(result.stations);
          setFetchError(result.ok ? null : result.message);
          setSelected(0);
          setLoading(false);
        })
        .catch(() => {
          if (controller.signal.aborted) return;
          setStations([]);
          setFetchError("The directory did not answer.");
          setLoading(false);
        });
    }, delay);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [scope, query, country, tag, retry]);

  useEffect(() => {
    setSelected((index) => {
      if (visible.length === 0) return 0;
      return Math.min(index, visible.length - 1);
    });
  }, [visible.length, scope]);

  function playAt(index: number) {
    const station = visible[index];
    if (!station) return;
    setSelected(index);
    engine.play(station);
  }

  function move(delta: number) {
    if (visible.length === 0) return;
    setSelected((index) => Math.min(visible.length - 1, Math.max(0, index + delta)));
  }

  function stepStation(delta: number) {
    if (visible.length === 0) return;
    const currentIndex = engine.current
      ? visible.findIndex((station) => station.id === engine.current?.id)
      : selected;
    const start = currentIndex >= 0 ? currentIndex : selected;
    playAt(Math.min(visible.length - 1, Math.max(0, start + delta)));
  }

  function onCommand(raw: string) {
    const line = raw.trim();
    if (!line) return;
    if (line === ":help" || line === "help" || line === "?") {
      setHelp(true);
      setCommandNote(null);
      return;
    }
    if (line.startsWith(":place")) {
      setCountry(line.slice(6).trim());
      setScope("dial");
      setCommandNote(line.slice(6).trim() ? `place ${line.slice(6).trim()}` : "place cleared");
      return;
    }
    if (line.startsWith(":tag")) {
      const next = line.slice(4).trim().toLowerCase();
      setTag(next);
      setScope("dial");
      setCommandNote(next ? `tag ${next}` : "tag cleared");
      return;
    }
    if (line.startsWith(":add")) {
      const parsed = parseAdd(line.slice(4).trim());
      if (!parsed || !isStreamUrl(parsed.url)) {
        setCommandNote("use :add Name | https://stream");
        return;
      }
      const station: Station = {
        id: newId(),
        name: parsed.name || "My stream",
        streamUrl: parsed.url,
        homepage: "",
        tags: "",
        country: "",
        countryCode: "",
        language: "",
        codec: "",
        bitrate: 0,
        votes: 0,
        custom: true,
      };
      addCustom(station);
      setScope("mine");
      engine.play(station);
      setCommandNote(`added ${station.name}`);
      return;
    }
    const search = line.startsWith("/") ? line.slice(1).trim() : line;
    setQuery(search);
    setScope("dial");
    setCommandNote(null);
  }

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      const typing = !!target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA");
      if (event.key === "Escape") {
        setHelp(false);
        setAdding(false);
        setCommandNote(null);
        if (typing) target.blur();
        return;
      }
      if (help || adding || typing) return;

      const key = event.key;
      if (key === " ") {
        event.preventDefault();
        if (engine.current) engine.toggle();
        else playAt(selected);
        return;
      }
      if (key === "Enter") {
        event.preventDefault();
        playAt(selected);
        return;
      }
      if (key === "/" ) {
        event.preventDefault();
        const id = mode === "terminal" ? "vela-command" : "vela-search";
        document.getElementById(id)?.focus();
        return;
      }
      if (key === "?") {
        setHelp(true);
        return;
      }
      if (key === "j" || key === "ArrowDown") {
        event.preventDefault();
        move(1);
        return;
      }
      if (key === "k" || key === "ArrowUp") {
        event.preventDefault();
        move(-1);
        return;
      }
      if (key === "n") {
        stepStation(1);
        return;
      }
      if (key === "p") {
        stepStation(-1);
        return;
      }
      if (key === "f") {
        const station = visible[selected];
        if (station) toggleSaved(station);
        return;
      }
      if (key === "m") {
        toggleMute();
        return;
      }
      if (key === "s") {
        engine.cycleSleep();
        return;
      }
      if (key === "a") {
        setAdding(true);
        return;
      }
      if (key === "\\") {
        setMode(mode === "desk" ? "terminal" : "desk");
        return;
      }
      if (key === "+" || key === "=") {
        setVolume(Math.min(1, volume + 0.05));
        return;
      }
      if (key === "-" || key === "_") {
        setVolume(Math.max(0, volume - 0.05));
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const dial = {
    stations: visible,
    loading,
    error: fetchError,
    selected,
    scope,
    query,
    country,
    tag,
    savedCount: favorites.length,
    mineCount: custom.length,
    onQuery: setQuery,
    onCountry: (value: string) => {
      setCountry(value);
      if (scope !== "dial") setScope("dial");
    },
    onTag: (value: string) => {
      setTag(value);
      setScope("dial");
    },
    onScope: (next: Scope) => {
      setScope(next);
      setSelected(0);
    },
    onPlay: (station: Station, index: number) => {
      setSelected(index);
      engine.play(station);
    },
    onOpenAdd: () => setAdding(true),
    onRetry: () => setRetry((value) => value + 1),
    onCommand,
    commandNote,
  };

  const live = engine.current
    ? `${engine.current.name}. ${engine.status}.`
    : "Nothing on the air.";

  const air =
    engine.status === "playing"
      ? "On air"
      : engine.status === "connecting"
        ? "Tuning"
        : engine.status === "paused"
          ? "Paused"
          : engine.status === "error"
            ? "Off air"
            : engine.rested
              ? "Rested"
              : "Quiet";

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-bg text-fg">
      <header className="flex h-16 shrink-0 items-center gap-3 border-b border-line px-3 sm:px-5">
        <img src="/favicon.svg" alt="" className="size-7 shrink-0" />
        <div className="min-w-0">
          <p className="text-[15px] font-medium leading-none tracking-tight">Vela</p>
          <p className="mt-1 truncate font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
            <span className={engine.status === "playing" ? "text-dial" : undefined}>{air}</span>
            {engine.current ? <span className="hidden normal-case tracking-normal sm:inline"> · {engine.current.name}</span> : null}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-1">
          <a
            href="/vela-linux.zip"
            download="vela-linux.zip"
            aria-label="Download for Arch and Debian"
            className="inline-flex h-11 items-center gap-2 rounded-md px-2.5 text-sm text-muted hover:bg-surface hover:text-fg"
          >
            <Download className="size-4" />
            <span className="hidden lg:inline">Linux</span>
          </a>
          <button
            type="button"
            aria-label={muted || volume === 0 ? "Unmute" : "Mute"}
            aria-pressed={muted}
            onClick={toggleMute}
            className="grid size-11 place-items-center rounded-md text-muted hover:bg-surface hover:text-fg"
          >
            {muted || volume === 0 ? <VolumeX className="size-4" /> : <Volume2 className="size-4" />}
          </button>
          <button
            type="button"
            onClick={engine.cycleSleep}
            className="inline-flex h-11 items-center gap-1.5 rounded-md px-2 font-mono text-xs text-muted tabular-nums hover:bg-surface hover:text-fg"
            aria-label="Sleep timer"
          >
            <Moon className="size-4" />
            <span className={engine.sleepLeft == null ? "hidden sm:inline" : undefined}>
              {engine.sleepLeft == null ? "Sleep" : formatClock(engine.sleepLeft)}
            </span>
          </button>
          <div className="ml-1 flex rounded-md bg-surface p-1" role="group" aria-label="View">
            <button
              type="button"
              aria-pressed={mode === "desk"}
              onClick={() => setMode("desk")}
              className={
                "h-9 rounded-sm px-3 text-sm " +
                (mode === "desk" ? "bg-dial text-dial-ink" : "text-muted hover:text-fg")
              }
            >
              Desk
            </button>
            <button
              type="button"
              aria-pressed={mode === "terminal"}
              onClick={() => setMode("terminal")}
              className={
                "h-9 rounded-sm px-3 text-sm " +
                (mode === "terminal" ? "bg-dial text-dial-ink" : "text-muted hover:text-fg")
              }
            >
              <span className="sm:hidden">Term</span>
              <span className="hidden sm:inline">Terminal</span>
            </button>
          </div>
        </div>
      </header>
      {mode === "desk" ? <Desk {...dial} /> : <Terminal {...dial} />}
      <p className="sr-only" aria-live="polite">
        {live}
      </p>
      {help ? <HelpCard onClose={() => setHelp(false)} /> : null}
      {adding ? (
        <AddStation
          onClose={() => setAdding(false)}
          onAdd={(station) => {
            addCustom(station);
            setScope("mine");
            setAdding(false);
            engine.play(station);
          }}
        />
      ) : null}
    </div>
  );
}

function parseAdd(rest: string): { name: string; url: string } | null {
  if (!rest) return null;
  const parts = rest.split("|");
  if (parts.length >= 2) return { name: parts[0].trim(), url: parts.slice(1).join("|").trim() };
  const match = rest.match(/^(.*)\s+(https?:\/\/\S+)$/);
  if (!match) return null;
  return { name: match[1].trim(), url: match[2].trim() };
}
