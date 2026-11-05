// Scroll-driven state: the nav tab of the section in view is marked, as the app's start
// page marks its filter; the hero's sea moves and the clips play only while in view.

const tabs = [...document.querySelectorAll(".top nav a[href^='#']")];
const sections = tabs.map((a) => document.querySelector(a.hash));
const horizon = document.querySelector(".horizon");
const clips = [...document.querySelectorAll("video")];

// A section counts as in view once its top passes this share of the viewport.
const READ_LINE = 0.3;

// Servo repaints the whole page every frame an animation runs, which a handheld
// without a GPU draws on its CPU.
const STILL_SEA = navigator.userAgent.includes("Servo/");

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
  horizon.classList.toggle("live", !STILL_SEA && inView(horizon));
  for (const clip of clips) {
    if (!inView(clip)) clip.pause();
    else if (clip.paused) clip.play().catch(() => {});
  }
};

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
