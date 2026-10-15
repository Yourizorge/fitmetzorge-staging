'use strict';
// Cache only this generic, account-free document and its two dependencies.
const CACHE='fmz-local-offline-shell-v1';
const ASSETS=new Map([['/offline_shell.html','text/html'],['/offline_shell.css','text/css'],['/offline_shell.js','javascript']]);
const allowed=url=>url.origin===self.location.origin&&!url.search&&ASSETS.has(url.pathname);
self.addEventListener('install',event=>event.waitUntil((async()=>{
 const entries=await Promise.all([...ASSETS].map(async([path,mime])=>{
  const response=await fetch(path,{credentials:'omit',cache:'no-store',redirect:'error'});
  if(!response.ok||!response.headers.get('Content-Type')?.includes(mime))throw Error('shell_asset');
  return [path,response];
 }));
 const cache=await caches.open(CACHE);
 for(const [path,response] of entries)await cache.put(path,response);
 // Existing open documents keep their worker until their next navigation.
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
 for(const name of await caches.keys())if(name.startsWith('fmz-local-offline-shell-')&&name!==CACHE)await caches.delete(name);
 await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
 const request=event.request,url=new URL(request.url);
 if(request.method!=='GET'||url.origin!==self.location.origin)return;
 if(request.mode==='navigate'&&url.pathname==='/'&&!url.search){
  event.respondWith((async()=>{
   try{const response=await fetch(request,{cache:'no-store'});if(response.ok)return response;}catch(_){}
   return (await caches.open(CACHE)).match('/offline_shell.html').then(r=>r||Response.error());
  })());
 }else if(allowed(url)){
  event.respondWith((async()=> (await (await caches.open(CACHE)).match(url.pathname))||fetch(request,{cache:'no-store'}))());
 }
 // API, login, authenticated HTML, app scripts and all other URLs are never cached.
});
