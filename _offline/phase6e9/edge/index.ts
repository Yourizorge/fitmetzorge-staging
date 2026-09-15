import {createHandler} from "./handler.mjs";
Deno.serve(createHandler({
 url:Deno.env.get("SUPABASE_URL")||"",
 key:Deno.env.get("SUPABASE_ANON_KEY")||"",
 proof:Deno.env.get("FMZ6E9_PROOF")||""
}));
