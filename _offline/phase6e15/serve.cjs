"use strict";
const fs=require("node:fs"),p=require("node:path"),http=require("node:http"),root=p.resolve(__dirname,"../..");
const allowed=["index.html","app.js","copy.js","data.js","model.js","demo.css","review.js"].map(f=>"/independent-intake-demo/"+f).concat(["/coach-review-demo/catalog.js","/coach-review-demo/model.js","/training-review-demo/brand.png","/bounded-adjustments-demo/demo.css"]);
const server=()=>http.createServer((q,r)=>{const file=new URL(q.url,"http://localhost").pathname;if(q.method!=="GET"||!allowed.includes(file)){r.writeHead(404);return r.end();}r.writeHead(200,{"Content-Type":{".html":"text/html",".js":"text/javascript",".css":"text/css",".png":"image/png"}[p.extname(file)],"Cache-Control":"no-store"});r.end(fs.readFileSync(p.join(root,file)));});
module.exports={server,allowed};
