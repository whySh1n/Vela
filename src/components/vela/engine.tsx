import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { streamCandidates, type Station } from "@/lib/stations";
import { useLibrary } from "@/lib/store";

export type PlayStatus = "idle" | "connecting" | "playing" | "paused" | "error";

const SLEEP_STEPS = [0, 15, 30, 45, 60, 90] as const;

type Slot = 0 | 1;

type Engine = {
  current: Station | null;
  status: PlayStatus;
  error: string | null;
  rested: boolean;
  listened: number;
  sleepLeft: number | null;
  sinkNote: string | null;
  play: (station: Station) => void;
  toggle: () => void;
  cycleSleep: () => void;
};

const EngineContext = createContext<Engine | null>(null);

function sinkSetter(audio: HTMLAudioElement) {
  const setSinkId = (audio as HTMLAudioElement & { setSinkId?: (id: string) => Promise<void> }).setSinkId;
  return typeof setSinkId === "function" ? setSinkId.bind(audio) : null;
}

export function EngineProvider({ children }: { children: ReactNode }) {
  const primaryRef = useRef<HTMLAudioElement | null>(null);
  const secondaryRef = useRef<HTMLAudioElement | null>(null);
  const detachRef = useRef<(() => void) | null>(null);
  const attemptRef = useRef(0);
  const statusRef = useRef<PlayStatus>("idle");
  const currentRef = useRef<Station | null>(null);
  const activeSlot = useRef<Slot>(0);
  const desiredSlot = useRef<Slot>(0);
  const gains = useRef<[number, number]>([1, 0]);
  const fadeRef = useRef<number | null>(null);
  const volume = useLibrary((state) => state.volume);
  const muted = useLibrary((state) => state.muted);
  const sinkId = useLibrary((state) => state.sinkId);

  const [current, setCurrent] = useState<Station | null>(null);
  const [status, setStatus] = useState<PlayStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [rested, setRested] = useState(false);
  const [listened, setListened] = useState(0);
  const [sleepUntil, setSleepUntil] = useState<number | null>(null);
  const [sleepStep, setSleepStep] = useState(0);
  const [now, setNow] = useState(0);
  const [sinkNote, setSinkNote] = useState<string | null>(null);

  function element(slot: Slot) {
    return slot === 0 ? primaryRef.current : secondaryRef.current;
  }

  function stopFade() {
    if (fadeRef.current != null) cancelAnimationFrame(fadeRef.current);
    fadeRef.current = null;
  }

  function writeVolumes() {
    const library = useLibrary.getState();
    const level = library.muted ? 0 : library.volume;
    const primary = primaryRef.current;
    const secondary = secondaryRef.current;
    if (primary) primary.volume = level * gains.current[0];
    if (secondary) secondary.volume = level * gains.current[1];
  }

  function silence(slot: Slot) {
    const audio = element(slot);
    if (!audio) return;
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
  }

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    currentRef.current = current;
  }, [current]);

  useEffect(() => {
    writeVolumes();
  }, [muted, volume]);

  useEffect(() => {
    let cancelled = false;
    const audios = [primaryRef.current, secondaryRef.current];
    void (async () => {
      let failed = false;
      let supported = false;
      for (const audio of audios) {
        if (!audio) continue;
        const setSinkId = sinkSetter(audio);
        if (!setSinkId) continue;
        supported = true;
        try {
          await setSinkId(sinkId);
        } catch {
          failed = true;
        }
      }
      if (cancelled) return;
      if (!supported || !failed) {
        setSinkNote(null);
        return;
      }
      if (sinkId) {
        setSinkNote("That output is unavailable. Sound stays on the system device.");
        useLibrary.getState().setSink("", "System default");
      } else {
        setSinkNote("This browser cannot change the output.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sinkId]);

  useEffect(() => {
    const id = window.setInterval(() => {
      setNow(Date.now());
      if (statusRef.current === "playing") setListened((value) => value + 1);
    }, 1000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    if (sleepUntil == null) return;
    const delay = sleepUntil - Date.now();
    if (delay <= 0) {
      rest();
      return;
    }
    const id = window.setTimeout(() => rest(), delay);
    return () => window.clearTimeout(id);
  }, [sleepUntil]);

  function rest() {
    attemptRef.current += 1;
    stopFade();
    detachRef.current?.();
    primaryRef.current?.pause();
    secondaryRef.current?.pause();
    setStatus((value) => (value === "idle" ? "idle" : "paused"));
    setSleepUntil(null);
    setSleepStep(0);
    setRested(true);
  }

  function ramp(from: Slot, to: Slot, ms: number, attempt: number) {
    stopFade();
    const started = performance.now();
    const tick = (time: number) => {
      if (attempt !== attemptRef.current) return;
      const amount = Math.min(1, (time - started) / ms);
      gains.current[from] = 1 - amount;
      gains.current[to] = amount;
      writeVolumes();
      if (amount < 1) {
        fadeRef.current = requestAnimationFrame(tick);
        return;
      }
      fadeRef.current = null;
      silence(from);
      gains.current[from] = 0;
      gains.current[to] = 1;
      activeSlot.current = to;
      writeVolumes();
    };
    fadeRef.current = requestAnimationFrame(tick);
  }

  function tryUrl(audio: HTMLAudioElement, url: string, attempt: number): Promise<boolean> {
    detachRef.current?.();
    return new Promise((resolve) => {
      let done = false;
      const finish = (ok: boolean) => {
        if (done) return;
        done = true;
        window.clearTimeout(timer);
        audio.removeEventListener("playing", onPlaying);
        audio.removeEventListener("error", onError);
        if (detachRef.current === cancel) detachRef.current = null;
        resolve(ok && attempt === attemptRef.current);
      };
      const cancel = () => finish(false);
      const onPlaying = () => finish(true);
      const onError = () => finish(false);
      const timer = window.setTimeout(() => finish(false), 10000);
      detachRef.current = cancel;
      audio.addEventListener("playing", onPlaying);
      audio.addEventListener("error", onError);
      audio.src = url;
      void audio.play().catch((err: unknown) => {
        const name = err instanceof DOMException ? err.name : "";
        if (name === "AbortError") return;
        finish(false);
      });
    });
  }

  function play(station: Station) {
    const primary = primaryRef.current;
    const secondary = secondaryRef.current;
    if (!primary || !secondary) return;
    const playingNow = statusRef.current === "playing" || statusRef.current === "connecting";
    if (currentRef.current?.id === station.id && playingNow) return;
    if (currentRef.current?.id === station.id && statusRef.current === "paused") {
      const audio = element(activeSlot.current);
      if (!audio) return;
      setRested(false);
      setError(null);
      setStatus("connecting");
      void audio.play().then(
        () => {
          if (statusRef.current !== "paused" && statusRef.current !== "connecting") return;
          setStatus("playing");
        },
        () => setStatus("error"),
      );
      return;
    }

    const attempt = ++attemptRef.current;
    const crossfade = useLibrary.getState().crossfade;
    const fading = crossfade > 0 && statusRef.current === "playing";
    const from = activeSlot.current;
    const next: Slot = fading ? (from === 0 ? 1 : 0) : from;
    const nextAudio = next === 0 ? primary : secondary;
    desiredSlot.current = next;
    setCurrent(station);
    currentRef.current = station;
    setStatus("connecting");
    setError(null);
    setRested(false);
    setListened(0);

    if (!fading) {
      stopFade();
      silence(next === 0 ? 1 : 0);
      gains.current = next === 0 ? [1, 0] : [0, 1];
      activeSlot.current = next;
      writeVolumes();
    } else {
      gains.current[next] = 0;
      writeVolumes();
    }

    const secure = window.location.protocol === "https:";
    const urls = streamCandidates(station.streamUrl, secure);

    void (async () => {
      for (const url of urls) {
        if (attempt !== attemptRef.current) return;
        const ok = await tryUrl(nextAudio, url, attempt);
        if (attempt !== attemptRef.current) return;
        if (ok) {
          setStatus("playing");
          setError(null);
          if (fading) ramp(from, next, crossfade, attempt);
          else activeSlot.current = next;
          return;
        }
      }
      if (attempt !== attemptRef.current) return;
      stopFade();
      silence(0);
      silence(1);
      gains.current = [1, 0];
      activeSlot.current = 0;
      desiredSlot.current = 0;
      setStatus("error");
      setError(
        secure
          ? "This station has no secure stream, so the browser cannot play it. The Linux app can."
          : "This station did not answer. Try another.",
      );
    })();
  }

  function toggle() {
    const audio = element(desiredSlot.current);
    if (!audio || !currentRef.current) return;
    if (statusRef.current === "playing" || statusRef.current === "connecting") {
      attemptRef.current += 1;
      stopFade();
      detachRef.current?.();
      activeSlot.current = desiredSlot.current;
      gains.current = desiredSlot.current === 0 ? [1, 0] : [0, 1];
      primaryRef.current?.pause();
      secondaryRef.current?.pause();
      writeVolumes();
      setStatus("paused");
      return;
    }
    if (statusRef.current === "paused" || statusRef.current === "error") {
      play(currentRef.current);
    }
  }

  function cycleSleep() {
    const index = SLEEP_STEPS.indexOf(sleepStep as (typeof SLEEP_STEPS)[number]);
    const next = SLEEP_STEPS[(index + 1) % SLEEP_STEPS.length];
    setSleepStep(next);
    setRested(false);
    setSleepUntil(next === 0 ? null : Date.now() + next * 60_000);
  }

  const sleepLeft = sleepUntil == null ? null : Math.max(0, Math.ceil((sleepUntil - now) / 1000));

  const value: Engine = {
    current,
    status,
    error,
    rested,
    listened,
    sleepLeft,
    sinkNote,
    play,
    toggle,
    cycleSleep,
  };

  return (
    <EngineContext.Provider value={value}>
      {children}
      <audio ref={primaryRef} preload="none" className="pointer-events-none absolute h-0 w-0 opacity-0" />
      <audio ref={secondaryRef} preload="none" className="pointer-events-none absolute h-0 w-0 opacity-0" />
    </EngineContext.Provider>
  );
}

export function useEngine(): Engine {
  const engine = useContext(EngineContext);
  if (!engine) throw new Error("Vela player is missing");
  return engine;
}
