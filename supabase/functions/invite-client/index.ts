import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";
import { handleInvite } from "./handler.ts";

Deno.serve(async (req: Request) => {
  const url = Deno.env.get("SUPABASE_URL");
  const anon = Deno.env.get("SUPABASE_ANON_KEY") || Deno.env.get("SUPABASE_PUBLISHABLE_KEY");
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (url !== "https://mokxyyullfhkfalopbzd.supabase.co" || !anon || !service) {
    return new Response('{"error":"staging_configuration_required"}', { status: 503 });
  }
  const user = createClient(url, anon, {
    auth: { persistSession: false, autoRefreshToken: false },
    global: { headers: { Authorization: req.headers.get("Authorization") || "" } }
  });
  const admin = createClient(url, service, { auth: { persistSession: false, autoRefreshToken: false } });
  try { return await handleInvite(req, { user, admin }); }
  catch { return new Response('{"error":"invitation_unavailable"}', { status: 503 }); }
});
