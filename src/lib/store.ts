import { create } from "zustand";
import { persist } from "zustand/middleware";
import { isStation, type Station } from "@/lib/stations";

export type Mode = "desk" | "terminal";
export type Crossfade = 0 | 600 | 1600;

const MAX_STATIONS = 200;

type Library = {
  mode: Mode;
  volume: number;
  muted: boolean;
  favorites: Station[];
  custom: Station[];
  sinkId: string;
  sinkLabel: string;
  crossfade: Crossfade;
  setMode: (mode: Mode) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  setSink: (id: string, label: string) => void;
  setCrossfade: (crossfade: Crossfade) => void;
  isSaved: (id: string) => boolean;
  toggleSaved: (station: Station) => void;
  addCustom: (station: Station) => void;
  removeCustom: (id: string) => void;
};

function keep(list: Station[], station: Station): Station[] {
  return [station, ...list.filter((item) => item.id !== station.id)].slice(0, MAX_STATIONS);
}

function fadeOf(value: unknown): Crossfade {
  return value === 600 || value === 1600 ? value : 0;
}

export const useLibrary = create<Library>()(
  persist(
    (set, get) => ({
      mode: "desk",
      volume: 0.82,
      muted: false,
      favorites: [],
      custom: [],
      sinkId: "",
      sinkLabel: "System default",
      crossfade: 0,
      setMode: (mode) => set({ mode }),
      setVolume: (volume) =>
        set({
          volume: Math.min(1, Math.max(0, volume)),
          muted: volume <= 0 ? true : get().muted && volume > 0 ? false : get().muted,
        }),
      toggleMute: () => set({ muted: !get().muted }),
      setSink: (id, label) =>
        set({
          sinkId: id.trim().slice(0, 256),
          sinkLabel: (label.trim() || "System default").slice(0, 80),
        }),
      setCrossfade: (crossfade) => set({ crossfade: fadeOf(crossfade) }),
      isSaved: (id) => get().favorites.some((station) => station.id === id),
      toggleSaved: (station) =>
        set((state) => {
          const exists = state.favorites.some((item) => item.id === station.id);
          return {
            favorites: exists
              ? state.favorites.filter((item) => item.id !== station.id)
              : keep(state.favorites, station),
          };
        }),
      addCustom: (station) =>
        set((state) => ({
          custom: keep(state.custom, { ...station, custom: true }),
          favorites: keep(state.favorites, { ...station, custom: true }),
        })),
      removeCustom: (id) =>
        set((state) => ({
          custom: state.custom.filter((station) => station.id !== id),
          favorites: state.favorites.filter((station) => station.id !== id),
        })),
    }),
    {
      name: "vela",
      version: 1,
      skipHydration: true,
      partialize: (state) => ({
        mode: state.mode,
        volume: state.volume,
        muted: state.muted,
        favorites: state.favorites,
        custom: state.custom,
        sinkId: state.sinkId,
        sinkLabel: state.sinkLabel,
        crossfade: state.crossfade,
      }),
      merge: (persisted, current) => {
        const saved = (persisted ?? {}) as Partial<Library>;
        const volume =
          typeof saved.volume === "number" ? Math.min(1, Math.max(0, saved.volume)) : current.volume;
        return {
          ...current,
          mode: saved.mode === "terminal" ? "terminal" : "desk",
          volume,
          muted: typeof saved.muted === "boolean" ? saved.muted : current.muted,
          favorites: Array.isArray(saved.favorites) ? saved.favorites.filter(isStation) : [],
          custom: Array.isArray(saved.custom) ? saved.custom.filter(isStation) : [],
          sinkId: typeof saved.sinkId === "string" ? saved.sinkId.slice(0, 256) : "",
          sinkLabel: typeof saved.sinkLabel === "string" && saved.sinkLabel.trim() ? saved.sinkLabel.slice(0, 80) : "System default",
          crossfade: fadeOf(saved.crossfade),
        };
      },
    },
  ),
);
