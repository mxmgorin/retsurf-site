// Fills the hero badges from the GitHub API. Shields SVGs draw their text
// through the engine's SVG fonts, which Servo does not paint reliably.

const REPO = "https://api.github.com/repos/mxmgorin/retsurf";

// Intl may be absent from a SpiderMonkey built without ICU.
const compact = (n) =>
  n < 1000 ? String(n) : (n / 1000).toFixed(n < 10000 ? 1 : 0).replace(/\.0$/, "") + "k";

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

for (const el of document.querySelectorAll("[data-badge]")) {
  BADGES[el.dataset.badge]()
    .then((value) => { el.textContent = value; })
    .catch(() => {});
}
