const genres = ["", "jazz", "classical", "ambient", "electronic", "rock", "soul", "folk", "news", "talk", "world"];
const audio = document.querySelector("#audio");
const state = {
  stations: [],
  favorites: [],
  custom: [],
  volume: 82,
  scope: "dial",
  tag: "",
  query: "",
  country: "",
  selected: 0,
  current: null,
  status: "idle",
  error: "",
  sleepTimer: 0,
  sleepStep: 0,
};

const $ = (id) => document.getElementById(id);

function esc(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({ "&": "&", "<": "<", ">": ">", '"': """, "'": "&#39;" }[ch]));
}

function mono(name) {
  const parts = String(name).replace(/[^\p{L}\p{N} ]+/gu, " ").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "·";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

function place(station) {
  const tags = String(station.tags || "").split(",").map((tag) => tag.trim()).filter(Boolean).slice(0, 2);
  return [station.country, ...tags].filter(Boolean).join(" · ") || "Your stream";
}

function visible() {
  const source = state.scope === "saved" ? state.favorites : state.scope === "mine" ? state.custom : state.stations;
  const needle = state.scope === "dial" ? "" : state.query.trim().toLowerCase();
  if (!needle) return source;
  return source.filter((station) => `${station.name} ${station.country} ${station.tags}`.toLowerCase().includes(needle));
}

async function loadLibrary() {
  const response = await fetch("/api/library");
  const data = await response.json();
  state.favorites = data.favorites || [];
  state.custom = data.custom || [];
  state.volume = Number(data.volume ?? 82);
  audio.volume = state.volume / 100;
  $("vol").value = String(state.volume);
  $("vol-label").textContent = String(state.volume);
}

let saveTimer = 0;
function saveLibrary() {
  window.clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => {
    void fetch("/api/library", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        favorites: state.favorites,
        custom: state.custom,
        volume: state.volume,
      }),
    });
  }, 200);
}

async function search() {
  if (state.scope !== "dial") {
    render();
    return;
  }
  const params = new URLSearchParams();
  if (state.query.trim()) params.set("name", state.query.trim());
  if (state.tag) params.set("tag", state.tag);
  if (state.country.trim()) params.set("country", state.country.trim());
  $("list").innerHTML = '<p class="empty">Tuning the directory…</p>';
  try {
    const response = await fetch(`/api/search?${params.toString()}`);
    const data = await response.json();
    state.stations = data.stations || [];
    state.error = data.ok ? "" : data.message || "The directory did not answer.";
  } catch {
    state.stations = [];
    state.error = "The directory did not answer.";
  }
  state.selected = 0;
  render();
}

function renderGenres() {
  $("genres").innerHTML = genres
    .map((genre) => {
      const on = state.tag === genre && state.scope === "dial" ? " on" : "";
      return `<button type="button" class="${on}" data-tag="${esc(genre)}">${esc(genre || "Top")}</button>`;
    })
    .join("");
}

function render() {
  renderGenres();
  document.querySelectorAll("[data-scope]").forEach((button) => {
    button.classList.toggle("on", button.dataset.scope === state.scope);
    if (button.dataset.scope === "saved") button.textContent = `Saved ${state.favorites.length || ""}`.trim();
    if (button.dataset.scope === "mine") button.textContent = `Mine ${state.custom.length || ""}`.trim();
  });
  const rows = visible();
  if (!rows.length) {
    const message = state.error && state.scope === "dial"
      ? state.error
      : state.scope === "saved"
        ? "Nothing saved yet. Star a station and it stays on this dial."
        : state.scope === "mine"
          ? "No streams of your own yet."
          : "Nothing under that name.";
    $("list").innerHTML = `<p class="empty">${esc(message)}</p>`;
  } else {
    $("list").innerHTML = rows
      .map((station, index) => {
        const saved = state.favorites.some((item) => item.id === station.id);
        return `<div class="station${index === state.selected ? " on" : ""}" role="option">
          <button type="button" class="main" data-play="${index}">
            <span class="name">${esc(station.name)}</span>
            <span class="sub">${esc(place(station))}</span>
          </button>
          <span class="rate">${station.bitrate ? esc(station.bitrate) : ""}</span>
          <button type="button" class="star${saved ? " on" : ""}" data-star="${index}" aria-label="${saved ? "Unsave" : "Save"}">${saved ? "saved" : "save"}</button>
        </div>`;
      })
      .join("");
  }
  const current = state.current;
  $("title").textContent = current ? current.name : "Nothing on the air";
  $("mark").textContent = current ? mono(current.name) : "·";
  $("mark").classList.toggle("live", state.status === "playing");
  $("meta").textContent = current
    ? [current.codec, current.bitrate ? `${current.bitrate} kbps` : "", current.country].filter(Boolean).join(" · ") || "Your stream"
    : "Choose a station. Star the ones you want to keep.";
  const eyebrows = { idle: "QUIET", connecting: "TUNING", playing: "ON AIR", paused: "PAUSED", error: "OFF AIR" };
  $("eyebrow").textContent = eyebrows[state.status] || "QUIET";
  $("err").hidden = !state.error || state.status !== "error";
  $("err").textContent = state.error;
  $("play").textContent = state.status === "playing" ? "Pause" : state.status === "connecting" ? "…" : "Play";
  $("play").setAttribute("aria-label", state.status === "playing" ? "Pause" : "Play");
}

function candidates(url) {
  if (url.startsWith("https://")) return [url];
  if (!url.startsWith("http://")) return [];
  const secure = location.protocol === "https:";
  const upgraded = `https://${url.slice("http://".length)}`;
  return secure ? [upgraded] : [upgraded, url];
}

function tryUrl(url) {
  return new Promise((resolve) => {
    let done = false;
    const finish = (ok) => {
      if (done) return;
      done = true;
      window.clearTimeout(timer);
      audio.removeEventListener("playing", onPlaying);
      audio.removeEventListener("error", onError);
      resolve(ok);
    };
    const onPlaying = () => finish(true);
    const onError = () => finish(false);
    const timer = window.setTimeout(() => finish(false), 10000);
    audio.addEventListener("playing", onPlaying);
    audio.addEventListener("error", onError);
    audio.src = url;
    audio.play().catch((error) => {
      if (error && error.name === "AbortError") return;
      finish(false);
    });
  });
}

async function play(station) {
  state.current = station;
  state.status = "connecting";
  state.error = "";
  render();
  for (const url of candidates(station.streamUrl)) {
    if (state.current !== station) return;
    if (await tryUrl(url)) {
      state.status = "playing";
      render();
      return;
    }
  }
  if (state.current !== station) return;
  state.status = "error";
  state.error = "This station did not answer. Try another.";
  render();
}

function toggle() {
  if (!state.current) {
    const rows = visible();
    if (rows[state.selected]) play(rows[state.selected]);
    return;
  }
  if (state.status === "playing" || state.status === "connecting") {
    audio.pause();
    state.status = "paused";
    render();
    return;
  }
  play(state.current);
}

function step(delta) {
  const rows = visible();
  if (!rows.length) return;
  const found = state.current ? rows.findIndex((station) => station.id === state.current.id) : state.selected;
  const next = Math.max(0, Math.min(rows.length - 1, (found >= 0 ? found : 0) + delta));
  state.selected = next;
  play(rows[next]);
}

let searchTimer = 0;
function queueSearch() {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => void search(), state.query || state.country ? 280 : 0);
}

$("q").addEventListener("input", (event) => {
  state.query = event.target.value;
  queueSearch();
  if (state.scope !== "dial") render();
});
$("place").addEventListener("input", (event) => {
  state.country = event.target.value;
  state.scope = "dial";
  queueSearch();
});
$("genres").addEventListener("click", (event) => {
  const button = event.target.closest("[data-tag]");
  if (!button) return;
  state.tag = button.dataset.tag;
  state.scope = "dial";
  void search();
});
document.querySelector(".scopes").addEventListener("click", (event) => {
  const button = event.target.closest("[data-scope]");
  if (!button) return;
  state.scope = button.dataset.scope;
  state.selected = 0;
  if (state.scope === "dial") void search();
  else render();
});
$("list").addEventListener("click", (event) => {
  const playButton = event.target.closest("[data-play]");
  const star = event.target.closest("[data-star]");
  const rows = visible();
  if (star) {
    const station = rows[Number(star.dataset.star)];
    if (!station) return;
    if (state.favorites.some((item) => item.id === station.id)) {
      state.favorites = state.favorites.filter((item) => item.id !== station.id);
    } else {
      state.favorites = [station, ...state.favorites.filter((item) => item.id !== station.id)].slice(0, 200);
    }
    saveLibrary();
    render();
    return;
  }
  if (playButton) {
    const index = Number(playButton.dataset.play);
    state.selected = index;
    play(rows[index]);
  }
});
$("play").addEventListener("click", toggle);
$("prev").addEventListener("click", () => step(-1));
$("next").addEventListener("click", () => step(1));
$("vol").addEventListener("input", (event) => {
  state.volume = Number(event.target.value);
  audio.volume = state.volume / 100;
  $("vol-label").textContent = String(state.volume);
  saveLibrary();
});
$("sleep").addEventListener("click", () => {
  const steps = [0, 15, 30, 45, 60, 90];
  state.sleepStep = steps[(steps.indexOf(state.sleepStep) + 1) % steps.length];
  window.clearTimeout(state.sleepTimer);
  if (state.sleepStep === 0) {
    $("sleep").textContent = "Sleep off";
    return;
  }
  $("sleep").textContent = `Sleep ${state.sleepStep}m`;
  state.sleepTimer = window.setTimeout(() => {
    audio.pause();
    state.status = state.current ? "paused" : "idle";
    state.sleepStep = 0;
    $("sleep").textContent = "The dial rested";
    render();
  }, state.sleepStep * 60 * 1000);
});
$("open-add").addEventListener("click", () => {
  $("add").hidden = false;
  $("add-name").focus();
});
$("add-cancel").addEventListener("click", () => {
  $("add").hidden = true;
});
$("add").addEventListener("submit", (event) => {
  event.preventDefault();
  const name = $("add-name").value.trim();
  const url = $("add-url").value.trim();
  if (!/^https?:\/\//.test(url)) {
    $("add-err").hidden = false;
    $("add-err").textContent = "The stream needs an http or https address.";
    return;
  }
  const station = {
    id: `custom:${crypto.randomUUID()}`,
    name,
    streamUrl: url,
    homepage: "",
    tags: "",
    country: "",
    countryCode: "",
    language: "",
    codec: "",
    bitrate: 0,
    custom: true,
  };
  state.custom = [station, ...state.custom].slice(0, 200);
  state.favorites = [station, ...state.favorites.filter((item) => item.id !== station.id)].slice(0, 200);
  saveLibrary();
  $("add").hidden = true;
  $("add-name").value = "";
  $("add-url").value = "";
  state.scope = "mine";
  play(station);
});

window.addEventListener("keydown", (event) => {
  const typing = event.target.matches("input, textarea");
  if (event.key === "Escape") {
    $("add").hidden = true;
    return;
  }
  if (typing || event.metaKey || event.ctrlKey || event.altKey) return;
  if (event.key === " ") {
    event.preventDefault();
    toggle();
  } else if (event.key === "j" || event.key === "ArrowDown") {
    const rows = visible();
    state.selected = Math.min(rows.length - 1, state.selected + 1);
    render();
  } else if (event.key === "k" || event.key === "ArrowUp") {
    state.selected = Math.max(0, state.selected - 1);
    render();
  } else if (event.key === "Enter") {
    const rows = visible();
    if (rows[state.selected]) play(rows[state.selected]);
  } else if (event.key === "f") {
    const station = visible()[state.selected];
    if (!station) return;
    if (state.favorites.some((item) => item.id === station.id)) {
      state.favorites = state.favorites.filter((item) => item.id !== station.id);
    } else state.favorites = [station, ...state.favorites].slice(0, 200);
    saveLibrary();
    render();
  } else if (event.key === "/") {
    event.preventDefault();
    $("q").focus();
  }
});

loadLibrary().then(() => search());
