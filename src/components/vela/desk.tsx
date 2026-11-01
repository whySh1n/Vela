import { type ReactNode } from "react";
import { Loader2, Pause, Play, Plus, SkipBack, SkipForward } from "lucide-react";
import { GENRES, formatClock, monogram, techLine } from "@/lib/stations";
import { useEngine } from "@/components/vela/engine";
import { useLibrary } from "@/lib/store";
import { SkeletonRows, StationRows } from "@/components/vela/rows";
import type { DialProps } from "@/components/vela/dial";

const field =
  "h-11 w-full rounded-md border border-line bg-bg px-3 text-sm text-fg placeholder:text-muted/80 focus-visible:border-dial";

export function Desk(props: DialProps) {
  const engine = useEngine();
  const volume = useLibrary((state) => state.volume);
  const setVolume = useLibrary((state) => state.setVolume);
  const muted = useLibrary((state) => state.muted);
  const current = engine.current;
  const playing = engine.status === "playing";
  const connecting = engine.status === "connecting";

  function step(delta: number) {
    if (props.stations.length === 0) return;
    const index = current ? props.stations.findIndex((station) => station.id === current.id) : props.selected;
    const start = index >= 0 ? index : props.selected;
    const next = Math.min(props.stations.length - 1, Math.max(0, start + delta));
    const station = props.stations[next];
    if (station) props.onPlay(station, next);
  }

  const eyebrow =
    engine.rested && engine.status !== "playing"
      ? "Rested"
      : engine.status === "playing"
        ? "On air"
        : engine.status === "connecting"
          ? "Tuning"
          : engine.status === "paused"
            ? "Paused"
            : engine.status === "error"
              ? "Off air"
              : "Quiet";

  const countLabel =
    props.loading && props.scope === "dial" && props.stations.length === 0
      ? "Searching"
      : `${props.stations.length}`;

  return (
    <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
      <section className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex flex-col gap-3 px-4 pt-3 sm:px-5">
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              id="vela-search"
              value={props.query}
              onChange={(event) => props.onQuery(event.target.value)}
              placeholder="Search stations"
              aria-label="Search stations"
              className={field}
              autoComplete="off"
            />
            <input
              value={props.country}
              onChange={(event) => props.onCountry(event.target.value)}
              placeholder="Country"
              aria-label="Country or place"
              className={field + " sm:w-44"}
              autoComplete="off"
            />
          </div>
          <div className="flex gap-1.5 overflow-x-auto vela-scroll">
            {GENRES.map((genre) => {
              const active = props.tag === genre.id && props.scope === "dial";
              return (
                <button
                  key={genre.label}
                  type="button"
                  aria-pressed={active}
                  onClick={() => props.onTag(genre.id)}
                  className={
                    "h-11 shrink-0 rounded-full border px-3.5 text-sm " +
                    (active
                      ? "border-transparent bg-dial text-dial-ink"
                      : "border-line bg-transparent text-muted hover:border-muted hover:text-fg")
                  }
                >
                  {genre.label}
                </button>
              );
            })}
          </div>
          <div className="-mx-4 flex items-center border-b border-line px-2 sm:-mx-5 sm:px-3">
            <ScopeButton label="Dial" active={props.scope === "dial"} onClick={() => props.onScope("dial")} />
            <ScopeButton
              label="Saved"
              count={props.savedCount}
              active={props.scope === "saved"}
              onClick={() => props.onScope("saved")}
            />
            <ScopeButton
              label="Mine"
              count={props.mineCount}
              active={props.scope === "mine"}
              onClick={() => props.onScope("mine")}
            />
            <button
              type="button"
              onClick={props.onOpenAdd}
              className="ml-auto inline-flex h-11 items-center gap-1.5 rounded-md px-3 text-sm text-muted hover:bg-surface hover:text-fg"
            >
              <Plus className="size-4" />
              Add
            </button>
          </div>
        </div>
        <div className="flex items-center justify-between px-4 pt-3 pb-1 font-mono text-[10px] uppercase tracking-[0.16em] text-muted sm:px-5">
          <span>{props.scope === "dial" ? "Directory" : props.scope === "saved" ? "Saved" : "Your streams"}</span>
          <span className="tabular-nums">{countLabel}</span>
        </div>
        <ListBody {...props} currentId={current?.id ?? null} />
      </section>

      <aside className="flex shrink-0 flex-col border-t border-line bg-surface lg:w-[22rem] lg:border-t-0 lg:border-l">
        <div className="flex items-center gap-3 px-4 py-3 lg:hidden">
          <Mark live={playing} label={current ? monogram(current.name) : "·"} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-[15px] font-medium">{current?.name ?? "No station"}</p>
            <p className="truncate text-sm text-muted">{statusLine(engine.status, engine.error, engine.rested)}</p>
          </div>
          <PlayButton playing={playing} connecting={connecting} disabled={!current} onClick={engine.toggle} />
        </div>

        <div className="hidden min-h-0 flex-1 flex-col px-6 py-6 lg:flex">
          <p className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.18em] text-dial">
            {playing ? <span className="size-1.5 rounded-full bg-dial" /> : null}
            {eyebrow}
          </p>
          <Mark large live={playing} label={current ? monogram(current.name) : "·"} />
          <div className="mt-6">
            <h2 className="text-[1.75rem] font-medium leading-tight tracking-tight text-balance">
              {current?.name ?? "No station"}
            </h2>
            <p className="mt-2 font-mono text-sm text-pretty text-muted">
              {current ? techLine(current) || "Custom stream" : "Pick a station from the directory."}
            </p>
          </div>
          {engine.error ? <p className="mt-4 text-sm text-pretty text-fg">{engine.error}</p> : null}
          {engine.rested && engine.status !== "playing" ? (
            <p className="mt-4 text-sm text-muted">The dial rested.</p>
          ) : null}
          <div className="mt-auto flex items-center gap-1 pt-8">
            <IconButton label="Previous station" onClick={() => step(-1)} disabled={props.stations.length === 0}>
              <SkipBack className="size-4" />
            </IconButton>
            <PlayButton
              playing={playing}
              connecting={connecting}
              disabled={!current && props.stations.length === 0}
              onClick={() => {
                if (current) engine.toggle();
                else if (props.stations[props.selected]) props.onPlay(props.stations[props.selected], props.selected);
              }}
            />
            <IconButton label="Next station" onClick={() => step(1)} disabled={props.stations.length === 0}>
              <SkipForward className="size-4" />
            </IconButton>
            {engine.listened > 0 ? (
              <span className="ml-auto text-right">
                <span className="block font-mono text-sm tabular-nums text-fg">{formatClock(engine.listened)}</span>
                <span className="block font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Elapsed</span>
              </span>
            ) : null}
          </div>
          {current?.homepage ? (
            <a
              href={current.homepage}
              target="_blank"
              rel="noreferrer"
              className="mt-5 text-sm text-muted underline-offset-4 hover:text-fg hover:underline"
            >
              Station site
            </a>
          ) : null}
        </div>

        <label className="flex items-center gap-3 border-t border-line px-4 py-3 text-sm text-muted lg:px-6">
          <span className="w-8 shrink-0 font-mono text-xs tabular-nums text-fg">
            {muted ? 0 : Math.round(volume * 100)}
          </span>
          <input
            type="range"
            min={0}
            max={100}
            value={Math.round((muted ? 0 : volume) * 100)}
            aria-label="Volume"
            className="vela-volume w-full"
            onChange={(event) => setVolume(Number(event.target.value) / 100)}
          />
        </label>
      </aside>
    </div>
  );
}

function ListBody({
  stations,
  loading,
  error,
  selected,
  scope,
  onPlay,
  onRetry,
  currentId,
}: DialProps & { currentId: string | null }) {
  if (loading && stations.length === 0 && scope === "dial") return <SkeletonRows />;
  if (error && stations.length === 0 && scope === "dial") {
    return (
      <div className="flex flex-1 flex-col items-start justify-center gap-3 px-5 py-16">
        <p className="text-base text-fg">Directory unavailable</p>
        <p className="max-w-sm text-sm text-pretty text-muted">{error}</p>
        <button type="button" onClick={onRetry} className="mt-1 h-11 rounded-md bg-dial px-4 text-sm font-medium text-dial-ink">
          Try again
        </button>
      </div>
    );
  }
  if (stations.length === 0) {
    const title =
      scope === "saved" ? "No saved stations" : scope === "mine" ? "No streams yet" : "No matches";
    const message =
      scope === "saved"
        ? "Star a station and it stays on this dial."
        : scope === "mine"
          ? "Add a stream address and it plays from here."
          : "Try another name, or a different country.";
    return (
      <div className="flex flex-1 flex-col justify-center px-5 py-16">
        <p className="text-base text-fg">{title}</p>
        <p className="mt-1 max-w-sm text-sm text-pretty text-muted">{message}</p>
      </div>
    );
  }
  return (
    <StationRows
      stations={stations}
      selected={selected}
      currentId={currentId}
      layout="desk"
      onPlay={onPlay}
    />
  );
}

function ScopeButton({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count?: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={
        "inline-flex h-11 items-center gap-2 -mb-px border-b-2 px-3 text-sm " +
        (active ? "border-dial text-fg" : "border-transparent text-muted hover:text-fg")
      }
    >
      {label}
      {count ? <span className="font-mono text-xs tabular-nums text-muted">{count}</span> : null}
    </button>
  );
}

function Mark({ live, label, large }: { live: boolean; label: string; large?: boolean }) {
  return (
    <span
      className={
        "relative grid shrink-0 place-items-center rounded-sm border bg-bg font-mono tracking-wide text-dial " +
        (large ? "mt-8 size-24 text-2xl " : "size-11 text-sm ") +
        (live ? "border-dial" : "border-line")
      }
    >
      {live && large ? <span className="absolute top-2.5 right-2.5 size-1.5 rounded-full bg-dial" /> : null}
      {label}
    </span>
  );
}

function PlayButton({
  playing,
  connecting,
  disabled,
  onClick,
}: {
  playing: boolean;
  connecting: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={playing ? "Pause" : "Play"}
      disabled={disabled}
      onClick={onClick}
      className="grid size-14 shrink-0 place-items-center rounded-full bg-dial text-dial-ink shadow-sm disabled:opacity-40"
    >
      {connecting ? (
        <Loader2 className="size-5 animate-spin" />
      ) : playing ? (
        <Pause className="size-5" />
      ) : (
        <Play className="size-5 translate-x-px" />
      )}
    </button>
  );
}

function IconButton({
  label,
  onClick,
  disabled,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="grid size-11 place-items-center rounded-md text-fg hover:bg-bg disabled:opacity-40"
    >
      {children}
    </button>
  );
}

function statusLine(status: string, error: string | null, rested: boolean): string {
  if (error) return error;
  if (rested && status !== "playing") return "The dial rested.";
  if (status === "connecting") return "Tuning";
  if (status === "playing") return "On air";
  if (status === "paused") return "Paused";
  return "Choose a station";
}
