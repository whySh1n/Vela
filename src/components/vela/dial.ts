import type { Station } from "@/lib/stations";

export type Scope = "dial" | "saved" | "mine";

export type DialProps = {
  stations: Station[];
  loading: boolean;
  error: string | null;
  selected: number;
  scope: Scope;
  query: string;
  country: string;
  tag: string;
  savedCount: number;
  mineCount: number;
  onQuery: (value: string) => void;
  onCountry: (value: string) => void;
  onTag: (value: string) => void;
  onScope: (scope: Scope) => void;
  onPlay: (station: Station, index: number) => void;
  onOpenAdd: () => void;
  onRetry: () => void;
  onCommand: (raw: string) => void;
  commandNote: string | null;
};
