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

type Engine = {
  current: Station | null;
  status: PlayStatus;
  error: string | null;
  rested: boolean;
  listened: number;
  sleepLeft: number | null;
  play: (station: Station) => void;
  toggle: () => void;
  cycleSleep: () => void;
};

const EngineContext = createContext<Engine | null>(null);

export function EngineProvider({ children }: { children: ReactNode }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const detachRef = useRef<(() => void) | null>(null);
  const attemptRef = useRef(0);
  const statusRef = useRef<PlayStatus>("idle");
  const volume = useLibrary((state) => state.volume);
  const muted = useLibrary((state) => state.muted);

  const [current, setCurrent] = useState<Station | null>(null);
  const [status, setStatus] = useState<PlayStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [rested, setRested] = useState(false);
  const [listened, setListened] = useState(0);
  const [sleepUntil, setSleepUntil] = useState<number | null>(null);
  const [sleepStep, setSleepStep] = useState(0);
  const [now, setNow] = useState(0);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = muted ? 0 : volume;
  }, [muted, volume]);

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
    detachRef.current?.();
    audioRef.current?.pause();
    setStatus((value) => (value === "idle" ? "idle" : "paused"));
    setSleepUntil(null);
    setSleepStep(0);
    setRested(true);
  }

  function tryUrl(url: string, attempt: number): Promise<boolean> {
    detachRef.current?.();
    return new Promise((resolve) => {
      const audio = audioRef.current;
      if (!audio) {
        resolve(false);
        return;
      }
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
    const audio = audioRef.current;
    if (!audio) return;
    if (current?.id === station.id && (status === "playing" || status === "connecting")) return;
    if (current?.id === station.id && status === "paused") {
      setRested(false);
      setError(null);
      void audio.play().then(
        () => {
          if (statusRef.current !== "paused" && statusRef.current !== "connecting") return;
          setStatus("playing");
        },
        () => setStatus("error"),
      );
      setStatus("connecting");
      return;
    }

    const attempt = ++attemptRef.current;
    setCurrent(station);
    setStatus("connecting");
    setError(null);
    setRested(false);
    setListened(0);
    const secure = window.location.protocol === "https:";
    const urls = streamCandidates(station.streamUrl, secure);

    void (async () => {
      for (const url of urls) {
        if (attempt !== attemptRef.current) return;
        const ok = await tryUrl(url, attempt);
        if (attempt !== attemptRef.current) return;
        if (ok) {
          setStatus("playing");
          setError(null);
          return;
        }
      }
      if (attempt !== attemptRef.current) return;
      setStatus("error");
      setError(
        secure
          ? "This station has no secure stream, so the browser cannot play it. The Linux app can."
          : "This station did not answer. Try another.",
      );
    })();
  }

  function toggle() {
    const audio = audioRef.current;
    if (!audio || !current) return;
    if (status === "playing" || status === "connecting") {
      attemptRef.current += 1;
      detachRef.current?.();
      audio.pause();
      setStatus("paused");
      return;
    }
    if (status === "paused" || status === "error") {
      play(current);
    }
  }

  function cycleSleep() {
    const index = SLEEP_STEPS.indexOf(sleepStep as (typeof SLEEP_STEPS)[number]);
    const next = SLEEP_STEPS[(index + 1) % SLEEP_STEPS.length];
    setSleepStep(next);
    setRested(false);
    setSleepUntil(next === 0 ? null : Date.now() + next * 60_000);
  }

  const sleepLeft =
    sleepUntil == null ? null : Math.max(0, Math.ceil((sleepUntil - now) / 1000));

  const value: Engine = {
    current,
    status,
    error,
    rested,
    listened,
    sleepLeft,
    play,
    toggle,
    cycleSleep,
  };

  return (
    <EngineContext.Provider value={value}>
      {children}
      <audio ref={audioRef} preload="none" className="pointer-events-none absolute h-0 w-0 opacity-0" />
    </EngineContext.Provider>
  );
}

export function useEngine(): Engine {
  const engine = useContext(EngineContext);
  if (!engine) throw new Error("Vela player is missing");
  return engine;
}
