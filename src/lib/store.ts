import { create } from "zustand";
import { persist } from "zustand/middleware";
import { isStation, type Station } from "@/lib/stations";

export type Mode = "desk" | "terminal";

const MAX_STATIONS = 200;

type Library = {
  mode: Mode;
  volume: number;
  muted: boolean;
  favorites: Station[];
  custom: Station[];
  setMode: (mode: Mode) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  isSaved: (id: string) => boolean;
  toggleSaved: (station: Station) => void;
  addCustom: (station: Station) => void;
  removeCustom: (id: string) => void;
};

function keep(list: Station[], station: Station): Station[] {
  return [station, ...list.filter((item) => item.id !== station.id)].slice(0, MAX_STATIONS);
}

export const useLibrary = create<Library>()(
  persist(
    (set, get) => ({
      mode: "desk",
      volume: 0.82,
      muted: false,
      favorites: [],
      custom: [],
      setMode: (mode) => set({ mode }),
      setVolume: (volume) =>
        set({
          volume: Math.min(1, Math.max(0, volume)),
          muted: volume <= 0 ? true : get().muted && volume > 0 ? false : get().muted,
        }),
      toggleMute: () => set({ muted: !get().muted }),
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
        };
      },
    },
  ),
);
