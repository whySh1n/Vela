export type Station = {
  id: string;
  name: string;
  streamUrl: string;
  homepage: string;
  tags: string;
  country: string;
  countryCode: string;
  language: string;
  codec: string;
  bitrate: number;
  votes: number;
  custom?: boolean;
};

export const GENRES: { id: string; label: string }[] = [
  { id: "", label: "Top" },
  { id: "jazz", label: "Jazz" },
  { id: "classical", label: "Classical" },
  { id: "ambient", label: "Ambient" },
  { id: "electronic", label: "Electronic" },
  { id: "rock", label: "Rock" },
  { id: "soul", label: "Soul" },
  { id: "folk", label: "Folk" },
  { id: "news", label: "News" },
  { id: "talk", label: "Talk" },
  { id: "hip hop", label: "Hip hop" },
  { id: "world", label: "World" },
];

export const KEYS: { keys: string; does: string }[] = [
  { keys: "Space", does: "Play or pause" },
  { keys: "J  K", does: "Move up and down" },
  { keys: "Enter", does: "Play the highlighted station" },
  { keys: "F", does: "Save or unsave" },
  { keys: "N  P", does: "Next or previous" },
  { keys: "M", does: "Mute" },
  { keys: "S", does: "Sleep timer" },
  { keys: "/", does: "Search" },
  { keys: "A", does: "Add your own stream" },
  { keys: "\\", does: "Desk or terminal" },
  { keys: "?", does: "This card" },
];

export function monogram(name: string): string {
  const parts = name
    .replace(/[^\p{L}\p{N} ]+/gu, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length === 0) return "·";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

export function shortPlace(station: Station): string {
  const trimmed = station.country
    .replace(/^The /, "")
    .replace(/ Of America$/, "")
    .replace(/ Of Great Britain And Northern Ireland$/, "");
  if (trimmed.length > 24 && station.countryCode) return station.countryCode;
  return trimmed;
}

export function placeLine(station: Station): string {
  const tags = station.tags
    .split(",")
    .map((tag) => tag.trim())
    .filter((tag) => tag && tag.length < 18 && !/^\d+$/.test(tag))
    .slice(0, 2);
  return [shortPlace(station), ...tags].filter(Boolean).join(" · ");
}

export function techLine(station: Station): string {
  const bits: string[] = [];
  if (station.codec) bits.push(station.codec);
  if (station.bitrate) bits.push(`${station.bitrate} kbps`);
  if (station.country) bits.push(shortPlace(station));
  else if (station.language) bits.push(station.language);
  return bits.join(" · ");
}

export function isStation(value: unknown): value is Station {
  if (!value || typeof value !== "object") return false;
  const row = value as Partial<Station>;
  return (
    typeof row.id === "string" &&
    typeof row.name === "string" &&
    typeof row.streamUrl === "string" &&
    (row.streamUrl.startsWith("http://") || row.streamUrl.startsWith("https://"))
  );
}

export function isStreamUrl(value: string): boolean {
  try {
    const url = new URL(value.trim());
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export function streamCandidates(url: string, pageIsSecure: boolean): string[] {
  if (url.startsWith("https://")) return [url];
  if (!url.startsWith("http://")) return [];
  const upgraded = `https://${url.slice("http://".length)}`;
  return pageIsSecure ? [upgraded] : [upgraded, url];
}

export function formatClock(total: number): string {
  const seconds = Math.max(0, Math.floor(total));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const rest = seconds % 60;
  const mm = String(minutes).padStart(2, "0");
  const ss = String(rest).padStart(2, "0");
  if (hours > 0) return `${hours}:${mm}:${ss}`;
  return `${minutes}:${ss}`;
}

export function filterStations(list: Station[], query: string): Station[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return list;
  return list.filter((station) =>
    `${station.name} ${station.country} ${station.language} ${station.tags}`
      .toLowerCase()
      .includes(needle),
  );
}

export function newId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `custom:${crypto.randomUUID()}`;
  }
  return `custom:${Date.now().toString(36)}-${Math.random().toString(16).slice(2)}`;
}
