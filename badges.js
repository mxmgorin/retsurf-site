// Fills the hero badges from the GitHub API. Shields SVGs draw their text
// through the engine's SVG fonts, which Servo does not paint reliably.

const REPO = "https://api.github.com/repos/mxmgorin/retsurf";

// Intl may be absent from a SpiderMonkey built without ICU.
const compact = (n) =>
  n < 1000 ? String(n) : (n / 1000).toFixed(n < 10000 ? 1 : 0).replace(/\.0$/, "") + "k";

// Unauthenticated API calls are rate-limited per IP: values are reused for CACHE_MS.
const CACHE_MS = 10 * 60 * 1000;
const CACHE_KEY = "badges";

const loadCache = () => {
  try {
    const cache = JSON.parse(localStorage.getItem(CACHE_KEY));
    return cache && Date.now() - cache.at < CACHE_MS ? cache.values : {};
  } catch {
    return {};
  }
};

const saveCache = (values) => {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ at: Date.now(), values }));
  } catch {}
};

const getJson = (path) =>
  fetch(REPO + path).then((r) => (r.ok ? r.json() : Promise.reject(r.status)));

const BADGES = {
  release: () => getJson("/releases/latest").then((r) => r.tag_name),
  nightly: () => getJson("/releases/tags/nightly").then((r) => r.published_at.slice(0, 10)),
  stars: () => getJson("").then((r) => compact(r.stargazers_count)),
  downloads: () =>
    getJson("/releases?per_page=100").then((rs) =>
      compact(rs.flatMap((r) => r.assets).reduce((n, a) => n + a.download_count, 0)),
    ),
};

// A badge stays hidden until its value is in.
const show = (el, value) => {
  el.textContent = value;
  el.parentElement.classList.add("filled");
};

const cached = loadCache();
const fresh = {};
const pending = [];
for (const el of document.querySelectorAll("[data-badge]")) {
  const name = el.dataset.badge;
  if (name in cached) {
    show(el, cached[name]);
    continue;
  }
  pending.push(
    BADGES[name]()
      .then((value) => {
        show(el, value);
        fresh[name] = value;
      })
      .catch(() => {}),
  );
}
if (pending.length) {
  Promise.all(pending).then(() => {
    if (Object.keys(fresh).length) saveCache({ ...cached, ...fresh });
  });
}
