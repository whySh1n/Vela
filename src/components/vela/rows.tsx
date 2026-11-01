import { useEffect, useRef } from "react";
import { Star, X } from "lucide-react";
import { monogram, placeLine, type Station } from "@/lib/stations";
import { useLibrary } from "@/lib/store";

export function StationRows({
  stations,
  selected,
  currentId,
  layout,
  onPlay,
}: {
  stations: Station[];
  selected: number;
  currentId: string | null;
  layout: "desk" | "term";
  onPlay: (station: Station, index: number) => void;
}) {
  const rowRefs = useRef<Array<HTMLDivElement | null>>([]);
  const isSaved = useLibrary((state) => state.isSaved);
  const toggleSaved = useLibrary((state) => state.toggleSaved);
  const removeCustom = useLibrary((state) => state.removeCustom);

  useEffect(() => {
    rowRefs.current[selected]?.scrollIntoView({ block: "nearest" });
  }, [selected, stations]);

  return (
    <div role="listbox" aria-label="Stations" className="min-h-0 flex-1 overflow-y-auto vela-scroll">
      {stations.map((station, index) => {
        const active = index === selected;
        const onAir = station.id === currentId;
        const saved = isSaved(station.id);
        return (
          <div
            key={station.id}
            ref={(node) => {
              rowRefs.current[index] = node;
            }}
            role="option"
            aria-selected={active}
            data-station-id={station.id}
            className={
              "flex items-stretch border-b border-line " +
              (active ? "bg-surface-2" : "bg-transparent")
            }
          >
            <span className={"w-0.5 shrink-0 " + (active ? "bg-dial" : "bg-transparent")} />
            <button
              type="button"
              onClick={() => onPlay(station, index)}
              className="flex min-h-11 min-w-0 flex-1 items-center gap-3 px-3 py-2 text-left"
            >
              {layout === "term" ? (
                <span className={"w-4 shrink-0 font-mono " + (active ? "text-dial" : "text-muted")}>
                  {active ? ">" : " "}
                </span>
              ) : (
                <span
                  className={
                    "grid size-11 shrink-0 place-items-center rounded-sm bg-bg font-mono text-sm text-dial " +
                    (onAir ? "ring-1 ring-dial" : "")
                  }
                >
                  {monogram(station.name)}
                </span>
              )}
              <span className="min-w-0 flex-1">
                <span className={"block truncate " + (layout === "term" ? "font-mono" : "")}>
                  {station.name}
                </span>
                <span className="block truncate text-sm text-muted">
                  {placeLine(station) || (station.custom ? "Your stream" : "Live")}
                </span>
              </span>
              <span className="hidden shrink-0 font-mono text-sm text-muted sm:block">
                {station.bitrate ? station.bitrate : station.countryCode}
              </span>
            </button>
            {station.custom ? (
              <button
                type="button"
                aria-label={`Remove ${station.name}`}
                onClick={() => removeCustom(station.id)}
                className="grid size-11 shrink-0 place-items-center text-muted"
              >
                <X className="size-4" />
              </button>
            ) : null}
            <button
              type="button"
              aria-label={saved ? `Unsave ${station.name}` : `Save ${station.name}`}
              aria-pressed={saved}
              onClick={() => toggleSaved(station)}
              className="grid size-11 shrink-0 place-items-center"
            >
              <Star
                className={"size-4 " + (saved ? "fill-dial text-dial" : "text-muted")}
                strokeWidth={1.75}
              />
            </button>
          </div>
        );
      })}
    </div>
  );
}

export function SkeletonRows() {
  return (
    <div className="flex flex-col" aria-hidden="true">
      {Array.from({ length: 7 }, (_, index) => (
        <div key={index} className="flex items-center gap-3 border-b border-line px-4 py-3">
          <span className="size-11 rounded-sm bg-surface-2" />
          <span className="h-3 w-40 rounded-sm bg-surface-2" />
        </div>
      ))}
    </div>
  );
}
