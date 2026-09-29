"use strict";
const fs=require("node:fs"),p=require("node:path"),http=require("node:http");
const root=p.resolve(__dirname,"../..");
const allowed=["index.html","demo.css","app.js","copy.js","model.js","data.js"].map(f=>"/proactive-signals-demo/"+f).concat("/training-review-demo/brand.png");
const server=()=>http.createServer((req,res)=>{
 const file=new URL(req.url,"http://127.0.0.1").pathname;
 if(req.method!=="GET"||!allowed.includes(file)){res.writeHead(404);return res.end();}
 const ext=p.extname(file),mime={".html":"text/html",".js":"application/javascript",".css":"text/css",".png":"image/png"};
 res.writeHead(200,{"Content-Type":mime[ext],"Cache-Control":"no-store"});fs.createReadStream(p.join(root,file)).pipe(res);
});
module.exports={server,allowed};
