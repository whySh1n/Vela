import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import type { Station } from "@/lib/stations";

const SERVERS = [
  "https://de1.api.radio-browser.info",
  "https://de2.api.radio-browser.info",
  "https://fi1.api.radio-browser.info",
];

const searchInput = z.object({
  name: z.string().trim().max(80).optional(),
  tag: z.string().trim().max(40).optional(),
  country: z.string().trim().max(56).optional(),
});

type Raw = Record<string, unknown>;

function text(value: unknown, max = 160): string {
  return typeof value === "string" ? value.trim().slice(0, max) : "";
}

function bestUrl(row: Raw): string {
  const url = text(row.url, 500);
  const resolved = text(row.url_resolved, 500);
  if (url.startsWith("https://")) return url;
  if (resolved.startsWith("https://")) return resolved;
  if (resolved.startsWith("http://")) return resolved;
  if (url.startsWith("http://")) return url;
  return "";
}

function slim(row: Raw): Station | null {
  const id = text(row.stationuuid, 80);
  const name = text(row.name, 120);
  const streamUrl = bestUrl(row);
  if (!id || !name || !streamUrl) return null;
  const homepage = text(row.homepage, 200);
  return {
    id,
    name,
    streamUrl,
    homepage: homepage.startsWith("https://") ? homepage : "",
    tags: text(row.tags, 180),
    country: text(row.country, 60),
    countryCode: text(row.countrycode, 8).toUpperCase(),
    language: text(row.language, 40),
    codec: text(row.codec, 16).toUpperCase(),
    bitrate: Math.max(0, Math.round(Number(row.bitrate) || 0)),
    votes: Math.max(0, Math.round(Number(row.votes) || 0)),
  };
}

async function radioGet(path: string): Promise<unknown> {
  let last = "The directory did not answer.";
  for (const base of SERVERS) {
    try {
      const response = await fetch(base + path, {
        headers: {
          "User-Agent": "Vela/1.0 (quiet radio)",
          Accept: "application/json",
        },
        signal: AbortSignal.timeout(12000),
      });
      if (!response.ok) {
        last = "The directory did not answer.";
        continue;
      }
      return await response.json();
    } catch {
      last = "The directory did not answer.";
    }
  }
  throw new Error(last);
}

export const searchStations = createServerFn({ method: "GET" })
  .validator((input: unknown) => searchInput.parse(input ?? {}))
  .handler(async ({ data }) => {
    const params = new URLSearchParams({
      hidebroken: "true",
      limit: "40",
      order: "votes",
      reverse: "true",
    });
    if (data.name) params.set("name", data.name);
    if (data.tag) params.set("tag", data.tag);
    if (data.country) params.set("country", data.country);
    try {
      const json = await radioGet(`/json/stations/search?${params.toString()}`);
      const rows = Array.isArray(json) ? json : [];
      const seen = new Set<string>();
      const stations: Station[] = [];
      for (const row of rows) {
        if (!row || typeof row !== "object") continue;
        const station = slim(row as Raw);
        if (!station || seen.has(station.id)) continue;
        seen.add(station.id);
        stations.push(station);
      }
      return { ok: true as const, stations, message: "" };
    } catch (error) {
      const message = error instanceof Error ? error.message : "The directory did not answer.";
      return { ok: false as const, stations: [] as Station[], message };
    }
  });
