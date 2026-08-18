(async () => {
  const stagingSupabaseUrl = "https://mokxyyullfhkfalopbzd.supabase.co";
  const stagingSupabaseAnonKey = "sb_publishable_6OiMLMl946arkI71-ylqkQ_EQWL6kKT";

  window.FMZ_CONFIG = {
    ...(window.FMZ_CONFIG || {}),
    SUPABASE_URL: stagingSupabaseUrl,
    SUPABASE_ANON_KEY: stagingSupabaseAnonKey,
    INVITE_FUNCTION_NAME: "invite-client"
  };

  const bundleUrl = new URL("app.bundle.js?v=20260810-agenda-wide-final", document.baseURI);
  const bundleResponse = await fetch(bundleUrl, { cache: "no-cache" });
  if (!bundleResponse.ok) {
    throw new Error(`App bundle laden mislukt: ${bundleResponse.status}`);
  }

  const stagingConfigSource = [
    'const FMZ_CONFIG = {',
    `  ...(window.FMZ_CONFIG || {}),`,
    `  SUPABASE_URL: "${stagingSupabaseUrl}",`,
    `  SUPABASE_ANON_KEY: "${stagingSupabaseAnonKey}",`,
    '  INVITE_FUNCTION_NAME: "invite-client"',
    '};'
  ].join("\n");

  const stagingRedirectSource = [
    'const APP_AUTH_REDIRECT_URL = (() => {',
    '  const githubStagingPath = "/fitmetzorge-staging/";',
    '  if (window.location.hostname === "yourizorge.github.io") {',
    '    return window.location.origin + githubStagingPath;',
    '  }',
    '  return window.location.origin + "/";',
    '})();'
  ].join("\n");

  let source = await bundleResponse.text();
  source = source.replace('const FMZ_CONFIG = window.FMZ_CONFIG || {};', stagingConfigSource);
  source = source.replace(/const APP_AUTH_REDIRECT_URL = "[^"]+";/, stagingRedirectSource);

  const phase1PatchUrl = new URL("assets/phase1-foundation.js?v=20260815-phase1-perf1", document.baseURI);
  const phase1PatchResponse = await fetch(phase1PatchUrl, { cache: "no-cache" });
  if (!phase1PatchResponse.ok) {
    throw new Error(`Phase 1 foundation laden mislukt: ${phase1PatchResponse.status}`);
  }
  const phase1PatchSource = await phase1PatchResponse.text();

  const phase2PatchUrl = new URL("assets/phase2-home-recovery.js?v=20260816-phase2-logout1", document.baseURI);
  const phase2PatchResponse = await fetch(phase2PatchUrl, { cache: "no-cache" });
  if (!phase2PatchResponse.ok) {
    throw new Error(`Phase 2 Home + Recovery laden mislukt: ${phase2PatchResponse.status}`);
  }
  const phase2PatchSource = await phase2PatchResponse.text();

  const phase3PatchUrl = new URL("assets/phase3-training-engine.js?v=20260818-phase3-disclosure-focusfix1", document.baseURI);
  const phase3PatchResponse = await fetch(phase3PatchUrl, { cache: "no-cache" });
  if (!phase3PatchResponse.ok) {
    throw new Error(`Phase 3 Training Engine laden mislukt: ${phase3PatchResponse.status}`);
  }
  const phase3PatchSource = await phase3PatchResponse.text();

  const phase1InitNeedle = "\ninit();";
  if (!source.includes(phase1InitNeedle)) {
    throw new Error("Phase 1 foundation kon niet voor app-init worden ingevoegd.");
  }
  source = source.replace(phase1InitNeedle, `\n${phase1PatchSource}\n${phase2PatchSource}\n${phase3PatchSource}\ninit();`);

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
