import { useState, type FormEvent } from "react";
import { GENRES, formatClock, techLine } from "@/lib/stations";
import { useEngine } from "@/components/vela/engine";
import { useLibrary } from "@/lib/store";
import { StationRows } from "@/components/vela/rows";
import { RoutePanel } from "@/components/vela/route";
import type { DialProps } from "@/components/vela/dial";

export function Terminal(props: DialProps) {
  const engine = useEngine();
  const volume = useLibrary((state) => state.volume);
  const muted = useLibrary((state) => state.muted);
  const [draft, setDraft] = useState("");
  const current = engine.current;

  function submit(event: FormEvent) {
    event.preventDefault();
    const value = draft.trim();
    setDraft("");
    if (!value) return;
    props.onCommand(value.startsWith("/") ? value.slice(1) : value);
  }

  const status = engine.rested
    ? "rested"
    : engine.status === "connecting"
      ? "tuning"
      : engine.status === "playing"
        ? "playing"
        : engine.status === "paused"
          ? "paused"
          : engine.status === "error"
            ? "off air"
            : "idle";

  return (
    <div className="flex min-h-0 flex-1 flex-col font-mono text-sm">
      <div className="flex h-10 items-center gap-2 border-b border-line px-4 font-mono text-[11px] uppercase tracking-[0.16em] text-muted">
        <span className="text-dial">vela</span>
        <span aria-hidden="true">/</span>
        <span className="truncate normal-case tracking-normal">
          {props.scope}
          {props.tag ? ` · ${props.tag}` : ""}
          {props.country ? ` · ${props.country}` : ""}
          {props.query ? ` · ${props.query}` : ""}
        </span>
        <span className="ml-auto shrink-0">{status}</span>
      </div>
      <div className="flex gap-2 overflow-x-auto border-b border-line px-3 py-2 vela-scroll">
        {GENRES.map((genre) => {
          const active = props.tag === genre.id && props.scope === "dial";
          return (
            <button
              key={genre.label}
              type="button"
              onClick={() => props.onTag(genre.id)}
              className={"h-11 shrink-0 px-2 " + (active ? "text-dial" : "text-muted")}
            >
              {genre.label.toLowerCase()}
            </button>
          );
        })}
      </div>
      <div className="flex gap-1 border-b border-line px-3 py-1">
        <TermScope label="dial" active={props.scope === "dial"} onClick={() => props.onScope("dial")} />
        <TermScope
          label={`saved ${props.savedCount || ""}`.trim()}
          active={props.scope === "saved"}
          onClick={() => props.onScope("saved")}
        />
        <TermScope
          label={`mine ${props.mineCount || ""}`.trim()}
          active={props.scope === "mine"}
          onClick={() => props.onScope("mine")}
        />
        <button type="button" onClick={props.onOpenAdd} className="ml-auto h-11 px-2 text-muted">
          add
        </button>
      </div>
      {props.loading && props.stations.length === 0 && props.scope === "dial" ? (
        <p className="px-4 py-6 text-muted">tuning the directory…</p>
      ) : props.error && props.stations.length === 0 && props.scope === "dial" ? (
        <div className="px-4 py-6">
          <p className="text-muted">{props.error}</p>
          <button type="button" onClick={props.onRetry} className="mt-3 h-11 text-dial">
            try again
          </button>
        </div>
      ) : props.stations.length === 0 ? (
        <p className="px-4 py-6 text-pretty text-muted">
          {props.scope === "saved"
            ? "nothing saved. press f on a station."
            : props.scope === "mine"
              ? "no streams of your own. press a."
              : "nothing under that name."}
        </p>
      ) : (
        <StationRows
          stations={props.stations}
          selected={props.selected}
          currentId={current?.id ?? null}
          layout="term"
          onPlay={props.onPlay}
        />
      )}
      <div className="border-t border-line px-4 py-3">
        <div className="flex items-baseline justify-between gap-4">
          <p className="min-w-0 truncate text-base text-fg">{current?.name ?? "nothing on the air"}</p>
          <p className="shrink-0 text-muted">{status}</p>
        </div>
        <p className="mt-1 truncate text-muted">
          {current ? techLine(current) || "custom stream" : "pick a station"}
          {" · vol "}
          {muted ? 0 : Math.round(volume * 100)}
          {engine.sleepLeft != null ? ` · sleep ${formatClock(engine.sleepLeft)}` : ""}
          {engine.listened > 0 ? ` · ${formatClock(engine.listened)}` : ""}
        </p>
        {engine.error ? <p className="mt-1 text-fg">{engine.error}</p> : null}
        {props.commandNote ? <p className="mt-1 text-dial">{props.commandNote}</p> : null}
      </div>
      <RoutePanel />
      <form onSubmit={submit} className="flex items-center gap-2 border-t border-line px-4">
        <span className="text-dial" aria-hidden="true">
          /
        </span>
        <input
          id="vela-command"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          aria-label="Command"
          placeholder="search, :add, :place, :tag, :help"
          className="h-11 w-full bg-transparent text-fg placeholder:text-muted focus-visible:outline-none"
          autoComplete="off"
        />
      </form>
      <p className="hidden gap-x-4 px-4 py-2 text-muted sm:flex">
        <span>j k move</span>
        <span>enter play</span>
        <span>f save</span>
        <span>space pause</span>
        <span>? keys</span>
      </p>
    </div>
  );
}

function TermScope({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button type="button" onClick={onClick} className={"h-11 px-2 " + (active ? "text-dial" : "text-muted")}>
      {label}
    </button>
  );
}
