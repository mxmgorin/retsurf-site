// Gamepad face buttons press the page's buttons that show them, while a pad is connected.

import { SPARE_FRAMES } from "./engine.js";

// The standard mapping's face buttons, labelled the Xbox way.
const FACE = { a: 0, b: 1, x: 2, y: 3 };

const targets = [...document.querySelectorAll("[data-pad]")].map((el) => ({ el, button: FACE[el.dataset.pad] }));
const held = new Set();

let polling = false;

// The Gamepad API has no button events: polls once a frame until no pad is left.
const poll = () => {
  const pads = navigator.getGamepads().filter(Boolean);
  if (!pads.length) {
    polling = false;
    return;
  }
  for (const { el, button } of targets) {
    const down = pads.some((p) => p.buttons[button]?.pressed);
    if (down && !held.has(button)) el.click();
    if (down) held.add(button);
    else held.delete(button);
  }
  requestAnimationFrame(poll);
};

if (!SPARE_FRAMES) {
  addEventListener("gamepadconnected", () => {
    if (!polling) {
      polling = true;
      requestAnimationFrame(poll);
    }
  });
}
