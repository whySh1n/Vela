import { useState } from "react";
import { useEngine } from "@/components/vela/engine";
import { useLibrary, type Crossfade } from "@/lib/store";

const FADES: { ms: Crossfade; label: string }[] = [
  { ms: 0, label: "Off" },
  { ms: 600, label: "Short" },
  { ms: 1600, label: "Long" },
];

function canPickOutput() {
  return typeof HTMLMediaElement !== "undefined" && "setSinkId" in HTMLMediaElement.prototype;
}

function canPromptOutput() {
  return typeof navigator !== "undefined" && !!navigator.mediaDevices && "selectAudioOutput" in navigator.mediaDevices;
}

async function listOutputs() {
  if (!navigator.mediaDevices?.enumerateDevices) return [];
  const all = await navigator.mediaDevices.enumerateDevices();
  return all
    .filter((device) => device.kind === "audiooutput" && device.deviceId)
    .map((device, index) => ({
      id: device.deviceId,
      label: device.label || (device.deviceId === "default" ? "System default" : `Output ${index + 1}`),
    }));
}

export function RoutePanel() {
  const sinkId = useLibrary((state) => state.sinkId);
  const sinkLabel = useLibrary((state) => state.sinkLabel);
  const crossfade = useLibrary((state) => state.crossfade);
  const setSink = useLibrary((state) => state.setSink);
  const setCrossfade = useLibrary((state) => state.setCrossfade);
  const sinkNote = useEngine().sinkNote;
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [outputs, setOutputs] = useState<{ id: string; label: string }[]>([]);
  const prompt = canPromptOutput();
  const pick = canPickOutput();

  async function choose() {
    setNote(null);
    const media = navigator.mediaDevices as MediaDevices & {
      selectAudioOutput?: () => Promise<MediaDeviceInfo>;
    };
    try {
      if (media?.selectAudioOutput) {
        const device = await media.selectAudioOutput();
        setSink(device.deviceId, device.label || "Selected output");
        setOutputs([]);
        return;
      }
      const list = await listOutputs();
      setOutputs(list.filter((device) => device.id !== "default"));
      if (!list.length) setNote("This browser only exposes the system output.");
    } catch (error) {
      const name = error instanceof DOMException ? error.name : "";
      if (name === "NotAllowedError" || name === "AbortError") return;
      setNote("The output picker is not available in this browser.");
    }
  }

  return (
    <div className="border-t border-line px-4 py-3 lg:px-6">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="flex h-11 w-full items-center gap-3 text-left"
      >
        <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Route</span>
        <span className="min-w-0 flex-1 truncate text-sm text-fg">{sinkId ? sinkLabel : "System default"}</span>
        <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">{open ? "Close" : "Edit"}</span>
      </button>
      {open ? (
        <div className="flex flex-col gap-4 pb-2">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Output</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {pick ? (
                <button
                  type="button"
                  onClick={() => void choose()}
                  className="h-11 rounded-md bg-surface-2 px-3 text-sm text-fg"
                >
                  {prompt ? "Choose output" : "List outputs"}
                </button>
              ) : null}
              <button
                type="button"
                onClick={() => {
                  setOutputs([]);
                  setNote(null);
                  setSink("", "System default");
                }}
                className="h-11 rounded-md px-3 text-sm text-muted hover:text-fg"
              >
                System default
              </button>
            </div>
            {outputs.length > 0 ? (
              <div className="mt-2 flex flex-col" role="group" aria-label="Outputs">
                {outputs.map((device) => (
                  <button
                    key={device.id}
                    type="button"
                    aria-pressed={device.id === sinkId}
                    onClick={() => setSink(device.id, device.label)}
                    className={
                      "h-11 truncate rounded-md px-3 text-left text-sm " +
                      (device.id === sinkId ? "bg-surface-2 text-fg" : "text-muted hover:text-fg")
                    }
                  >
                    {device.label}
                  </button>
                ))}
              </div>
            ) : null}
            <p className="mt-2 text-sm text-pretty text-muted">
              {sinkNote ||
                note ||
                (pick
                  ? "Headphones, speakers, or a virtual device. Balance and tone are in the Linux player."
                  : "This browser keeps the system output. The Linux player can pick a device, balance, and tone.")}
            </p>
          </div>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Crossfade</p>
            <div className="mt-2 flex gap-1" role="group" aria-label="Crossfade">
              {FADES.map((fade) => (
                <button
                  key={fade.label}
                  type="button"
                  aria-pressed={crossfade === fade.ms}
                  onClick={() => setCrossfade(fade.ms)}
                  className={
                    "h-11 rounded-md px-3 text-sm " +
                    (crossfade === fade.ms ? "bg-dial text-dial-ink" : "bg-surface-2 text-muted")
                  }
                >
                  {fade.label}
                </button>
              ))}
            </div>
            <p className="mt-2 text-sm text-muted">
              {crossfade === 0
                ? "The next station replaces this one."
                : "The next station takes the desk over while this one leaves."}
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
