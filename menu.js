// Header menus: a toggle opens and closes its list, and any other click, or Escape, closes it.
// The stylesheet shows a list while its toggle is expanded; a hidden toggle is shown once wired.

for (const menu of document.querySelectorAll(".menu")) {
  const toggle = menu.querySelector(".menu-toggle");
  const open = (on) => toggle.setAttribute("aria-expanded", on);

  toggle.addEventListener("click", () => open(toggle.getAttribute("aria-expanded") !== "true"));
  addEventListener("click", (ev) => {
    if (!toggle.contains(ev.target)) open(false);
  });
  addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") open(false);
  });
  toggle.hidden = false;
}
