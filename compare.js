// The shader comparison's cut follows a drag or a tap; arrow keys step it.

// How far an arrow key moves the cut, in percent of the frame.
const STEP = 5;

const [DOWN, MOVE, UP] = window.PointerEvent
  ? ["pointerdown", "pointermove", "pointerup"]
  : ["mousedown", "mousemove", "mouseup"];

for (const view of document.querySelectorAll(".compare")) {
  let split = Number(view.getAttribute("aria-valuenow"));
  let dragging = false;
  const set = (share) => {
    split = Math.min(100, Math.max(0, share));
    view.style.setProperty("--split", split + "%");
    view.setAttribute("aria-valuenow", Math.round(split));
  };
  const follow = (ev) => {
    const r = view.getBoundingClientRect();
    set(((ev.clientX - r.left) / r.width) * 100);
  };
  view.addEventListener(DOWN, (ev) => {
    dragging = true;
    follow(ev);
    ev.preventDefault();
  });
  addEventListener(MOVE, (ev) => dragging && follow(ev));
  addEventListener(UP, () => (dragging = false));
  view.addEventListener("keydown", (ev) => {
    const dir = { ArrowLeft: -1, ArrowRight: 1 }[ev.key];
    if (!dir) return;
    set(split + dir * STEP);
    ev.preventDefault();
  });
}
