import { useState, type FormEvent, type ReactNode } from "react";
import { X } from "lucide-react";
import { isStreamUrl, KEYS, newId, type Station } from "@/lib/stations";

function Frame({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <div
      className="fixed inset-0 z-30 flex items-end justify-center bg-black/55 p-4 backdrop-blur-[2px] sm:items-center"
      role="presentation"
      onMouseDown={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="vela-dialog-title"
        className="w-full max-w-md rounded-md border border-line bg-surface p-5 shadow-2xl shadow-black/50"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 id="vela-dialog-title" className="text-lg font-medium text-balance">
            {title}
          </h2>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="grid size-11 place-items-center text-muted"
          >
            <X className="size-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

const field =
  "h-11 w-full rounded-md border border-line bg-bg px-3 text-sm text-fg placeholder:text-muted/80 focus-visible:border-dial";

export function AddStation({
  onClose,
  onAdd,
}: {
  onClose: () => void;
  onAdd: (station: Station) => void;
}) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [place, setPlace] = useState("");
  const [error, setError] = useState<string | null>(null);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Give it a name.");
      return;
    }
    if (!isStreamUrl(url)) {
      setError("The stream needs an http or https address.");
      return;
    }
    onAdd({
      id: newId(),
      name: name.trim(),
      streamUrl: url.trim(),
      homepage: "",
      tags: "",
      country: place.trim(),
      countryCode: "",
      language: "",
      codec: "",
      bitrate: 0,
      votes: 0,
      custom: true,
    });
  }

  return (
    <Frame title="Add a stream" onClose={onClose}>
      <form onSubmit={submit} className="flex flex-col gap-3">
        <label className="flex flex-col gap-1 text-sm text-muted">
          Name
          <input
            autoFocus
            value={name}
            onChange={(event) => setName(event.target.value)}
            className={field}
            placeholder="Night desk"
            maxLength={120}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-muted">
          Stream address
          <input
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            className={field}
            placeholder="https://"
            inputMode="url"
            autoComplete="off"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-muted">
          Place, optional
          <input
            value={place}
            onChange={(event) => setPlace(event.target.value)}
            className={field}
            placeholder="Lisbon"
            maxLength={60}
          />
        </label>
        {error ? <p className="text-sm text-fg">{error}</p> : null}
        <button
          type="submit"
          className="mt-1 h-11 rounded-md bg-dial px-4 text-sm font-medium text-dial-ink"
        >
          Put it on the dial
        </button>
      </form>
    </Frame>
  );
}

export function HelpCard({ onClose }: { onClose: () => void }) {
  return (
    <Frame title="Keys" onClose={onClose}>
      <ul className="flex flex-col">
        {KEYS.map((item) => (
          <li key={item.keys} className="flex items-baseline justify-between gap-4 border-b border-line py-2">
            <span className="font-mono text-sm text-dial">{item.keys}</span>
            <span className="text-sm text-muted">{item.does}</span>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-sm text-pretty text-muted">
        In the terminal, Enter on a line starting with :add, :place, or :tag runs that command.
      </p>
    </Frame>
  );
}
