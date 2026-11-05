// Vimium-style link hints, drawn like the app's: F labels every link in view,
// typing a label follows that link, Backspace takes a key back, Escape cancels.

const KEYS = "sadfjklewcmpgh";

let active = null;

// Labels of one length, so none is a prefix of another.
const labelsFor = (n) =>
  n <= KEYS.length
    ? [...KEYS].slice(0, n)
    : [...KEYS].flatMap((a) => [...KEYS].map((b) => a + b)).slice(0, n);

const inView = (r) =>
  r.width > 0 && r.height > 0 && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth;

const showHints = () => {
  const links = [...document.querySelectorAll("a[href]")].filter((a) => inView(a.getBoundingClientRect()));
  const layer = document.createElement("div");
  layer.className = "hints";
  const entries = labelsFor(links.length).map((label, i) => {
    const r = links[i].getBoundingClientRect();
    const box = document.createElement("div");
    box.className = "hint-box";
    Object.assign(box.style, { left: r.left + "px", top: r.top + "px", width: r.width + "px", height: r.height + "px" });
    const tag = document.createElement("span");
    tag.className = "hint-label";
    tag.textContent = label;
    Object.assign(tag.style, { left: Math.max(0, r.left - 6) + "px", top: Math.max(0, r.top - 9) + "px" });
    layer.append(box, tag);
    return { label, link: links[i], box, tag };
  });
  document.body.append(layer);
  active = { layer, entries, typed: "" };
};

const hideHints = () => {
  active?.layer.remove();
  active = null;
};

const updateHints = () => {
  const { entries, typed } = active;
  const hits = entries.filter((e) => e.label.startsWith(typed));
  if (hits.length === 1 && hits[0].label === typed) {
    hideHints();
    hits[0].link.click();
    return;
  }
  for (const e of entries) {
    const hit = e.label.startsWith(typed);
    e.box.hidden = e.tag.hidden = !hit;
    if (hit) e.tag.innerHTML = `<i>${typed}</i>${e.label.slice(typed.length)}`;
  }
};

addEventListener("keydown", (ev) => {
  if (ev.ctrlKey || ev.metaKey || ev.altKey || ev.target.closest?.("input, textarea, [contenteditable]")) return;
  const key = ev.key.toLowerCase();
  if (!active) {
    if (key !== "f") return;
    showHints();
  } else if (key === "escape") {
    hideHints();
  } else if (key === "backspace") {
    active.typed = active.typed.slice(0, -1);
    updateHints();
  } else if (KEYS.includes(key) && key.length === 1) {
    active.typed += key;
    updateHints();
  } else {
    return;
  }
  ev.preventDefault();
});

// The labels are pinned to where the links were.
addEventListener("scroll", hideHints, { passive: true });
addEventListener("resize", hideHints);
