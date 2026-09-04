(() => {
  "use strict";
  if (window.FMZ_PHASE6D0_LEGACY_AUTH) return;
  const inviteKey = "fmz.staging.verified-invite.v1";
  const url = new URL(window.location.href);
  let inviteToken = url.searchParams.get("fmz_invite") || "";
  try {
    if (/^[0-9a-f]{64}$/.test(inviteToken)) sessionStorage.setItem(inviteKey, inviteToken);
    else inviteToken = sessionStorage.getItem(inviteKey) || "";
  } catch { /* In-memory callback still works when storage is unavailable. */ }
  if (url.searchParams.has("fmz_invite")) {
    url.searchParams.delete("fmz_invite");
    history.replaceState({}, "", url.pathname + url.search + url.hash);
  }
  const clearInvite = () => {
    inviteToken = "";
    try { sessionStorage.removeItem(inviteKey); } catch { /* No persistence required. */ }
  };
  let ownRevision = null;
  let ownUser = null;
  let ownTrainer = null;
  let ensurePending = null;
  const legacyLoad = loadOnlineWorkspace;
  const legacySave = saveStateToCloud;

  ensureOnlineProfile = async function ensureOnlineProfileVerified(_roleHint = "", nameHint = "") {
    if (ensurePending) return ensurePending;
    ensurePending = (async () => {
      const auth = await supabaseClient.auth.getUser();
      if (auth.error || !auth.data?.user) throw new Error("authentication_required");
      const user = auth.data.user;
      if (inviteToken) {
        const accepted = await supabaseClient.rpc("fmz_phase6d0_accept_client_invite", { p_token: inviteToken });
        if (accepted.error) {
          if (accepted.error.code === "42501") clearInvite();
          throw new Error("De uitnodiging is ongeldig, verlopen of al gebruikt. Vraag je trainer om een nieuwe uitnodiging.");
        }
        clearInvite();
      }
      const existing = await supabaseClient.from("profiles").select("*").eq("id", user.id).maybeSingle();
      if (existing.error) throw existing.error;
      if (existing.data) { onlineProfile = existing.data; return existing.data; }
      const created = await supabaseClient.rpc("fmz_bootstrap_trainer_profile", {
        p_user_id: user.id, p_name: nameHint || profileDisplayName(user)
      });
      if (created.error) throw created.error;
      onlineProfile = created.data;
      return created.data;
    })();
    try { return await ensurePending; } finally { ensurePending = null; }
  };

  loadOnlineWorkspace = async function loadOnlineWorkspaceVerified(profile) {
    if (profile?.role !== "client" || !profile.trainer_id) return legacyLoad(profile);
    const result = await supabaseClient.rpc("fmz_phase6d0_read_own_workspace");
    if (result.error) throw result.error;
    ownRevision = result.data.revision;
    ownUser = profile.id;
    ownTrainer = profile.trainer_id;
    applyOnlineState(result.data.state, profile);
  };

  let savePending = null;
  saveStateToCloud = async function saveOwnWorkspaceVerified() {
    if (onlineProfile?.role !== "client" || !onlineProfile.trainer_id) return legacySave();
    if (savePending) await savePending;
    const user = onlineProfile?.id;
    if (user !== ownUser || onlineProfile?.trainer_id !== ownTrainer || !ownRevision) {
      return { ok: false, error: new Error("workspace_reload_required") };
    }
    const selected = state.clients.find((item) => item.id === onlineProfile.client_id);
    if (!selected) return { ok: false, error: new Error("own_client_slot_required") };
    const draft = JSON.parse(JSON.stringify(selected));
    delete draft.password;
    savePending = (async () => {
      const result = await supabaseClient.rpc("fmz_phase6d0_save_own_workspace", {
        p_client: draft, p_expected_revision: ownRevision
      });
      if (result.error) {
        onlineErrorMessage = "Opslaan mislukt";
        syncStatus(onlineErrorMessage, "error");
        return { ok: false, error: result.error };
      }
      if (onlineProfile?.id === user) ownRevision = result.data.revision;
      onlineErrorMessage = "";
      syncStatus("Online opgeslagen", "ok");
      return { ok: true };
    })();
    try { return await savePending; } finally { savePending = null; }
  };
  if (supabaseClient?.auth?.onAuthStateChange) supabaseClient.auth.onAuthStateChange((event) => {
    // Recovery deliberately signs out before the next login. The one-use token remains
    // email-bound on the server and expires in 24 hours; do not lose it at that transition.
    if (event === "SIGNED_OUT") { ownRevision = null; ownUser = null; ownTrainer = null; }
  });
  window.FMZ_PHASE6D0_LEGACY_AUTH = Object.freeze({ version: "20260904-phase6d0-auth1" });
})();
