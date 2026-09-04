const STAGING_ORIGIN = "https://yourizorge.github.io";
const REDIRECT = STAGING_ORIGIN + "/fitmetzorge-staging/";

export async function handleInvite(req: Request, clients: {
  user: any; admin: any;
}): Promise<Response> {
  const origin = req.headers.get("Origin");
  const headers: Record<string, string> = {
    "Content-Type": "application/json", "Cache-Control": "no-store", "Vary": "Origin",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS"
  };
  if (origin === STAGING_ORIGIN || origin === "https://test.appfmz.nl") headers["Access-Control-Allow-Origin"] = origin;
  const reply = (body: object, status = 200) => new Response(JSON.stringify(body), { status, headers });
  if (origin && !headers["Access-Control-Allow-Origin"]) return reply({ error: "origin_forbidden" }, 403);
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers });
  if (req.method !== "POST") return reply({ error: "method_not_allowed" }, 405);
  if (!/^Bearer \S+$/.test(req.headers.get("Authorization") || "")) return reply({ error: "authentication_required" }, 401);
  const auth = await clients.user.auth.getUser();
  if (auth.error || !auth.data?.user) return reply({ error: "authentication_required" }, 401);
  const body = await req.json().catch(() => null);
  if (!body || typeof body.clientId !== "string" || body.clientId.length > 160) return reply({ error: "client_slot_required" }, 400);
  // The caller's JWT and stored workspace determine trainer, target email and slot.
  // Browser email/name/redirect/role are never used as linking authority.
  const issued = await clients.user.rpc("fmz_phase6d0_issue_client_invite", { p_client_id: body.clientId });
  if (issued.error || !issued.data?.token) return reply({ error: "invitation_not_authorized" }, 403);
  const invitation = issued.data;
  const redirect = new URL(REDIRECT);
  redirect.searchParams.set("fmz_invite", invitation.token);
  let sent = false;
  try {
    const invite = await clients.admin.auth.admin.inviteUserByEmail(invitation.email, {
      redirectTo: redirect.href, data: { name: invitation.name }
    });
    if (!invite.error) sent = true;
    else if (["email_exists", "user_already_exists"].includes(invite.error.code)
      || /already.*(registered|exists)/i.test(invite.error.message || "")) {
      const recovery = await clients.admin.auth.resetPasswordForEmail(invitation.email, { redirectTo: redirect.href });
      sent = !recovery.error;
    }
    if (!sent) return reply({ error: "invitation_delivery_failed" }, 400);
    return reply({ ok: true, message: "Uitnodiging verzonden." });
  } catch {
    return reply({ error: "invitation_delivery_failed" }, 502);
  } finally {
    if (!sent) await clients.user.rpc("fmz_phase6d0_revoke_client_invite", { p_invitation_id: invitation.invitation_id });
  }
}
