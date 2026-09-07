(() => {
  "use strict";
  if (window.FMZ_THEME) return;
  const modes = ["system", "light", "dark"];
  const prefix = "fmz.theme.v1:";
  const authKey = "sb-mokxyyullfhkfalopbzd-auth-token";
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  let owner = "", mode = "system";
  const valid = value => modes.includes(value);
  function cached(user) {
    try {
      const value = JSON.parse(localStorage.getItem(prefix + user));
      return value?.user === user && valid(value.mode) ? value.mode : "system";
    } catch { return "system"; }
  }
  function apply() {
    const resolved = mode === "system" ? (media.matches ? "dark" : "light") : mode;
    const root = document.documentElement;
    root.dataset.theme = resolved;
    root.dataset.themeMode = mode;
    root.style.colorScheme = resolved;
    document.body?.classList.toggle("light", resolved === "light");
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", resolved === "light" ? "#f7f8fa" : "#070b12");
    return resolved;
  }
  function setUser(user) {
    if (owner !== (user || "")) {
      owner = user || "";
      mode = owner ? cached(owner) : "system";
    }
    apply();
  }
  function accept(user, value) {
    if (!user || owner !== user || !valid(value)) return false;
    mode = value;
    try { localStorage.setItem(prefix + user, JSON.stringify({user, mode})); } catch { /* Cosmetic cache is optional. */ }
    apply();
    return true;
  }
  function preview(user, value) {
    if (owner !== user || !user || !valid(value)) return false;
    mode = value;
    apply();
    return true;
  }
  function clear() { owner = ""; mode = "system"; apply(); }
  // This session hint selects cosmetic cache only. Auth/RPCs never trust it.
  try {
    const url = new URL(location.href), hash = new URLSearchParams(url.hash.slice(1));
    const publicLink = url.searchParams.has("type") || hash.has("type") || url.searchParams.has("error") || hash.has("error")
      || url.searchParams.has("code") || hash.has("access_token")
      || sessionStorage.getItem("fmz.auth.confirmation-login-required") === "true";
    const raw = localStorage.getItem(authKey) || sessionStorage.getItem(authKey);
    const session = !publicLink && raw && raw.length < 100000 ? JSON.parse(raw) : null;
    if (typeof session?.user?.id === "string" && session.expires_at > Date.now() / 1000) {
      owner = session.user.id;
      mode = cached(owner);
    }
  } catch { /* Public/system colors remain usable when storage is blocked. */ }
  window.FMZ_THEME = Object.freeze({apply, setUser, accept, preview, clear, snapshot: () => ({owner, mode, resolved: apply()})});
  if (media.addEventListener) media.addEventListener("change", apply);
  else media.addListener(apply);
  window.addEventListener("pageshow", apply);
  window.addEventListener("storage", event => {
    if (event.key === authKey && !event.newValue) clear();
    // Another tab's preference is only a reload hint, never server authority.
    if (owner && event.key === prefix + owner) window.dispatchEvent(new Event("fmz:theme-refresh"));
  });
  apply();
})();
