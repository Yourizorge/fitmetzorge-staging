"use strict";
const fs=require("node:fs"),path=require("node:path"),http=require("node:http");
const root=path.resolve(__dirname,"../.."),prefix="/workout-reflection-demo/";
const allowed=["index.html","app.js","copy.js","data.js","memory.js","demo.css"].map(x=>prefix+x).concat(["/training-review-demo/model.js","/training-review-demo/brand.png"]);
function server(){return http.createServer((req,res)=>{
 let u;try{u=decodeURIComponent(new URL(req.url,"http://127.0.0.1").pathname);}catch{res.writeHead(400).end();return;}
 if(u===prefix)u+="index.html";
 if(req.method!=="GET"||!allowed.includes(u)){res.writeHead(404).end();return;}
 const file=path.join(root,u.slice(1)),ext=path.extname(file);
 res.setHeader("Content-Type",({".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"application/javascript; charset=utf-8",".png":"image/png"})[ext]);
 res.setHeader("Cache-Control","no-store");res.setHeader("X-Content-Type-Options","nosniff");
 res.end(fs.readFileSync(file));
});}
module.exports={server,allowed};
if(require.main===module){const s=server();s.listen(0,"127.0.0.1",()=>console.log("http://127.0.0.1:"+s.address().port+prefix));}
