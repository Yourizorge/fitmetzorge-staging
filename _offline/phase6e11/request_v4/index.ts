import postgres from 'npm:postgres@3.4.7';
import {createRequestHandler} from './handler.mjs';
import {createRequestTransport} from './transport.mjs';
import {CA,SESSION_HOST} from '../edge_bridge_v2/ca.mjs';
const transport=createRequestTransport({postgres,connectionUrl:Deno.env.get('SUPABASE_DB_URL'),ca:CA,sessionHost:SESSION_HOST});
Deno.serve(createRequestHandler({url:Deno.env.get('SUPABASE_URL'),key:Deno.env.get('SUPABASE_ANON_KEY'),
 proof:Deno.env.get('FMZ6E11_PROOF'),transport}));
