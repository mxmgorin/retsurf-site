// The site's theme, one of the app's: a picked one is kept in this browser, and without
// one the system's light or dark decides. The head picks it up before the page paints.

const KEY = "theme";
const root = document.documentElement;
const menu = document.querySelector(".theme-menu");
const label = menu.querySelector(".theme-name");
const picks = [...menu.querySelectorAll("[data-theme-pick]")];
const themeColor = document.querySelector('meta[name="theme-color"]');

const show = () => {
  const current = root.dataset.theme ?? "";
  for (const pick of picks) {
    const on = pick.dataset.themePick === current;
    pick.classList.toggle("current", on);
    pick.setAttribute("aria-checked", on);
    if (on) label.textContent = pick.textContent;
  }
  if (themeColor) themeColor.content = getComputedStyle(root).getPropertyValue("--bg").trim();
};

for (const pick of picks) {
  pick.addEventListener("click", () => {
    const theme = pick.dataset.themePick;
    try {
      if (theme) localStorage.setItem(KEY, theme);
      else localStorage.removeItem(KEY);
    } catch {}
    if (theme) root.dataset.theme = theme;
    else delete root.dataset.theme;
    show();
  });
}

matchMedia("(prefers-color-scheme: light)").addEventListener?.("change", show);
menu.hidden = false;
show();
