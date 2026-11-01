import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({ component: Home });

const INSTALL = "curl -fsSL https://raw.githubusercontent.com/whySh1n/Vela/main/linux/install.sh | sh";

function Home() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-5xl flex-col gap-8 px-5 py-8 sm:px-8">
      <header className="flex items-center gap-3">
        <img src="/favicon.svg" alt="" className="size-8" />
        <div>
          <h1 className="text-lg font-medium tracking-tight">Vela</h1>
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted">Linux player</p>
        </div>
      </header>
      <img
        src="/vela-window.png"
        alt="The Vela window: station list, now playing, output, balance, and tone"
        className="w-full rounded-md border border-line"
      />
      <section className="max-w-2xl">
        <h2 className="text-base font-medium">Install</h2>
        <p className="mt-2 text-pretty text-muted">
          On Arch or Debian, paste this into a terminal. It asks for your password once.
        </p>
        <pre className="mt-4 overflow-x-auto rounded-md bg-surface px-4 py-3 text-sm text-fg">
          <code>{INSTALL}</code>
        </pre>
        <p className="mt-4 text-pretty text-muted">Then open Vela from your applications.</p>
      </section>
    </main>
  );
}
