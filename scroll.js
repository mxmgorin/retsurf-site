// Scroll-driven state: the nav tab of the section in view is marked, as the app's start
// page marks its filter; the hero's sea moves and the clips play only while in view.
// Sparing frames, the sea stays still and a clip waits for a tap.

import { SPARE_FRAMES } from "./engine.js";

const tabs = [...document.querySelectorAll(".top nav a[href^='#']")];
const sections = tabs.map((a) => document.querySelector(a.hash));
const horizon = document.querySelector(".horizon");
const clips = [...document.querySelectorAll("video")];

// A section counts as in view once its top passes this share of the viewport.
const READ_LINE = 0.3;

// Clips that play whenever they are in view.
const wanted = new Set(SPARE_FRAMES ? [] : clips);

let queued = false;

const inView = (el) => {
  const r = el.getBoundingClientRect();
  return r.bottom > 0 && r.top < innerHeight;
};

const onScroll = () => {
  queued = false;
  const line = innerHeight * READ_LINE;
  let current = -1;
  sections.forEach((s, i) => {
    if (s && s.getBoundingClientRect().top <= line) current = i;
  });
  tabs.forEach((a, i) => a.classList.toggle("current", i === current));
  horizon.classList.toggle("live", !SPARE_FRAMES && inView(horizon));
  for (const clip of clips) {
    if (!wanted.has(clip) || !inView(clip)) clip.pause();
    else if (clip.paused) clip.play().catch(() => {});
  }
};

if (SPARE_FRAMES) {
  for (const clip of clips) {
    const play = document.createElement("button");
    play.className = "play";
    play.setAttribute("aria-label", "Play");
    clip.after(play);
    const toggle = () => {
      if (!wanted.delete(clip)) wanted.add(clip);
      clip.parentElement.classList.toggle("playing", wanted.has(clip));
      onScroll();
    };
    play.addEventListener("click", toggle);
    clip.addEventListener("click", toggle);
  }
}

addEventListener(
  "scroll",
  () => {
    if (!queued) {
      queued = true;
      requestAnimationFrame(onScroll);
    }
  },
  { passive: true },
);
addEventListener("resize", onScroll);
onScroll();
