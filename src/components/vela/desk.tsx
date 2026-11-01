import { type ReactNode } from "react";
import { Loader2, Pause, Play, Plus, SkipBack, SkipForward } from "lucide-react";
import { GENRES, formatClock, monogram, techLine } from "@/lib/stations";
import { useEngine } from "@/components/vela/engine";
import { useLibrary } from "@/lib/store";
import { SkeletonRows, StationRows } from "@/components/vela/rows";
import type { DialProps } from "@/components/vela/dial";

const field =
  "h-11 w-full rounded-md border border-line bg-bg px-3 text-fg placeholder:text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-dial";

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
      ? "RESTED"
      : engine.status === "playing"
        ? "ON AIR"
        : engine.status === "connecting"
          ? "TUNING"
          : engine.status === "paused"
            ? "PAUSED"
            : engine.status === "error"
              ? "OFF AIR"
              : "QUIET";

  return (
    <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
      <section className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex flex-col gap-3 border-b border-line px-4 py-3">
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              id="vela-search"
              value={props.query}
              onChange={(event) => props.onQuery(event.target.value)}
              placeholder="Search the dial"
              aria-label="Search stations"
              className={field}
              autoComplete="off"
            />
            <input
              value={props.country}
              onChange={(event) => props.onCountry(event.target.value)}
              placeholder="Place"
              aria-label="Country or place"
              className={field + " sm:w-40"}
              autoComplete="off"
            />
          </div>
          <div className="flex gap-2 overflow-x-auto vela-scroll">
            {GENRES.map((genre) => {
              const active = props.tag === genre.id && props.scope === "dial";
              return (
                <button
                  key={genre.label}
                  type="button"
                  aria-pressed={active}
                  onClick={() => props.onTag(genre.id)}
                  className={
                    "h-11 shrink-0 rounded-md px-3 text-sm " +
                    (active ? "bg-dial text-dial-ink" : "bg-surface text-muted")
                  }
                >
                  {genre.label}
                </button>
              );
            })}
          </div>
          <div className="flex items-center gap-2">
            <ScopeButton
              label="Dial"
              active={props.scope === "dial"}
              onClick={() => props.onScope("dial")}
            />
            <ScopeButton
              label={`Saved ${props.savedCount || ""}`.trim()}
              active={props.scope === "saved"}
              onClick={() => props.onScope("saved")}
            />
            <ScopeButton
              label={`Mine ${props.mineCount || ""}`.trim()}
              active={props.scope === "mine"}
              onClick={() => props.onScope("mine")}
            />
            <button
              type="button"
              onClick={props.onOpenAdd}
              className="ml-auto inline-flex h-11 items-center gap-2 rounded-md px-3 text-sm text-muted"
            >
              <Plus className="size-4" />
              Add
            </button>
          </div>
        </div>
        <ListBody {...props} currentId={current?.id ?? null} />
      </section>

      <aside className="flex shrink-0 flex-col gap-4 border-t border-line bg-surface px-4 py-4 lg:w-96 lg:border-t-0 lg:border-l lg:px-6 lg:py-6">
        <div className="flex items-center gap-3 lg:hidden">
          <Mark live={playing} label={current ? monogram(current.name) : "·"} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-base">{current?.name ?? "Nothing on the air"}</p>
            <p className="truncate text-sm text-muted">{statusLine(engine.status, engine.error, engine.rested)}</p>
          </div>
          <PlayButton
            playing={playing}
            connecting={connecting}
            disabled={!current}
            onClick={engine.toggle}
          />
        </div>

        <div className="hidden min-h-0 flex-1 flex-col gap-6 lg:flex">
          <p className="font-mono text-sm tracking-wide text-dial">{eyebrow}</p>
          <Mark large live={playing} label={current ? monogram(current.name) : "·"} />
          <div>
            <h2 className="text-3xl font-medium text-balance">
              {current?.name ?? "Nothing on the air"}
            </h2>
            <p className="mt-2 text-pretty text-muted">
              {current
                ? techLine(current) || "Your stream"
                : "Choose a station. Star the ones you want to keep."}
            </p>
          </div>
          {engine.error ? <p className="text-sm text-fg">{engine.error}</p> : null}
          {engine.rested && engine.status !== "playing" ? (
            <p className="text-sm text-muted">The dial rested.</p>
          ) : null}
          <div className="mt-auto flex items-center gap-3">
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
              <span className="ml-auto font-mono text-sm text-muted tabular-nums">
                on for {formatClock(engine.listened)}
              </span>
            ) : null}
          </div>
          {current?.homepage ? (
            <a
              href={current.homepage}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-muted underline-offset-4 hover:text-fg hover:underline"
            >
              Station site
            </a>
          ) : null}
        </div>

        <label className="flex items-center gap-3 text-sm text-muted">
          <span className="w-8 shrink-0 font-mono tabular-nums">{muted ? 0 : Math.round(volume * 100)}</span>
          <input
            type="range"
            min={0}
            max={100}
            value={Math.round((muted ? 0 : volume) * 100)}
            aria-label="Volume"
            className="w-full"
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
      <div className="flex flex-1 flex-col items-start gap-3 px-4 py-8">
        <p className="text-pretty text-muted">{error}</p>
        <button type="button" onClick={onRetry} className="h-11 rounded-md bg-dial px-4 text-sm text-dial-ink">
          Try again
        </button>
      </div>
    );
  }
  if (stations.length === 0) {
    const message =
      scope === "saved"
        ? "Nothing saved yet. Star a station and it stays on this dial."
        : scope === "mine"
          ? "No streams of your own yet."
          : "Nothing under that name.";
    return <p className="px-4 py-8 text-pretty text-muted">{message}</p>;
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
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={"h-11 rounded-md px-3 text-sm " + (active ? "bg-surface-2 text-fg" : "text-muted")}
    >
      {label}
    </button>
  );
}

function Mark({ live, label, large }: { live: boolean; label: string; large?: boolean }) {
  return (
    <span
      className={
        "grid shrink-0 place-items-center rounded-sm border border-line bg-bg font-mono text-dial " +
        (large ? "size-20 text-xl" : "size-11 text-sm") +
        (live ? " vela-live" : "")
      }
    >
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
      className="grid size-14 shrink-0 place-items-center rounded-full bg-dial text-dial-ink disabled:opacity-40"
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
      className="grid size-11 place-items-center rounded-md text-fg disabled:opacity-40"
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
