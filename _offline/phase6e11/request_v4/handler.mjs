import {createBridgeHandler} from '../edge_bridge_v2/handler.mjs';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
export function createRequestHandler(options) {
  return async req=>{
    const requestId=req.headers.get('x-fmz6e11-request-id')||crypto.randomUUID();
    if(!UUID.test(requestId))return Response.json({error:'request_id_invalid'},{status:400});
    // Each invocation keeps its own verified claims and ID. Never share session state.
    return createBridgeHandler({...options,
      transport:args=>options.transport({...args,requestId})})(req);
  };
}
