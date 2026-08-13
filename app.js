(async () => {
  const bundleUrl = new URL("app.bundle.js?v=20260810-agenda-wide-final", document.baseURI);
  const bundleResponse = await fetch(bundleUrl, { cache: "no-cache" });
  if (!bundleResponse.ok) {
    throw new Error(`App bundle laden mislukt: ${bundleResponse.status}`);
  }

  const stagingRedirectSource = [
    'const FMZ_CONFIG = window.FMZ_CONFIG || {};',
    'const APP_AUTH_REDIRECT_URL = (() => {',
    '  const githubStagingPath = "/fitmetzorge-staging/";',
    '  if (window.location.hostname === "yourizorge.github.io") {',
    '    return window.location.origin + githubStagingPath;',
    '  }',
    '  return window.location.origin + "/";',
    '})();'
  ].join("\n");

  let source = await bundleResponse.text();
  source = source.replace(/const APP_AUTH_REDIRECT_URL = "[^"]+";/, stagingRedirectSource);
  source = source.replace('const FMZ_CONFIG = window.FMZ_CONFIG || {};', "");

  (0, eval)(`${source}\n//# sourceURL=app.bundle.js`);

  // Staging guard: keep auth tabs usable even if a later render interrupts app init.
  document.addEventListener("click", (event) => {
    const tab = event.target.closest("[data-auth-mode]");
    if (!tab) return;
    const mode = tab.dataset.authMode;
    document.querySelectorAll("[data-auth-mode]").forEach((button) => {
      button.classList.toggle("active", button.dataset.authMode === mode);
    });
    document.querySelectorAll("[data-auth-panel]").forEach((panel) => {
      panel.classList.toggle("active", panel.dataset.authPanel === mode);
    });
  });
})().catch((error) => {
  console.error(error);
  document.body.classList.add("logged-out");
  const target = document.getElementById("onlineStatus") || document.body;
  target.textContent = "App laden mislukt. Ververs de pagina of controleer de stagingbestanden.";
});
