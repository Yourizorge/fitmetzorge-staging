(async () => {
  const bundleResponse = await fetch("app.bundle.js?v=20260810-agenda-wide-final", { cache: "no-cache" });
  if (!bundleResponse.ok) {
    throw new Error(`App bundle laden mislukt: ${bundleResponse.status}`);
  }

  const githubStagingPath = "/fitmetzorge-staging/";
  const stagingRedirectSource = `const FMZ_CONFIG = window.FMZ_CONFIG || {};
const APP_AUTH_REDIRECT_URL = (() => {
  if (window.location.hostname === "yourizorge.github.io") {
    return `${window.location.origin}${githubStagingPath}`;
  }
  return `${window.location.origin}/`;
})();`;

  let source = await bundleResponse.text();
  source = source.replace('const APP_AUTH_REDIRECT_URL = "https://appfmz.nl";', stagingRedirectSource);
  source = source.replace('const FMZ_CONFIG = window.FMZ_CONFIG || {};', "");

  (0, eval)(`${source}\n//# sourceURL=app.bundle.js`);
})().catch((error) => {
  console.error(error);
  document.body.classList.add("logged-out");
  const target = document.getElementById("onlineStatus") || document.body;
  target.textContent = "App laden mislukt. Ververs de pagina of controleer de stagingbestanden.";
});
