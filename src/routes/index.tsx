import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({ component: Home });

function Home() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-5xl flex-col gap-8 px-5 py-8 sm:px-8">
      <header className="flex items-center gap-3">
        <img src="/favicon.svg" alt="" className="size-8" />
        <div>
          <h1 className="text-lg font-medium tracking-tight">Vela</h1>
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted">Linux player</p>
        </div>
        <a
          href="/vela-linux.zip"
          download="vela-linux.zip"
          className="ml-auto inline-flex h-11 items-center rounded-md bg-dial px-4 text-sm font-medium text-dial-ink"
        >
          Download
        </a>
      </header>
      <img
        src="/vela-window.png"
        alt="The Vela window: station list, now playing, output, balance, and tone"
        className="w-full rounded-md border border-line"
      />
      <section className="grid gap-8 sm:grid-cols-2">
        <div>
          <h2 className="text-base font-medium">A player for the machine</h2>
          <p className="mt-2 text-pretty text-muted">
            Vela is a window and a terminal for Arch Linux and Debian. Sound goes through mpv, so you can pick the
            speakers, move the balance, and set a tone. It is not a website.
          </p>
        </div>
        <div>
          <h2 className="text-base font-medium">Install</h2>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-muted">
            <li>Unzip the download.</li>
            <li>Run <code className="text-fg">./install.sh</code></li>
            <li>
              <code className="text-fg">vela</code> opens the window. <code className="text-fg">vela --term</code> opens
              the terminal.
            </li>
          </ol>
        </div>
      </section>
    </main>
  );
}

