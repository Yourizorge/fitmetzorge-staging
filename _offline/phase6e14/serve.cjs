"use strict";
const fs=require("node:fs"),p=require("node:path"),http=require("node:http"),root=p.resolve(__dirname,"../..");
const allowed=["/bounded-adjustments-demo/index.html","/bounded-adjustments-demo/demo.css","/bounded-adjustments-demo/app.js","/bounded-adjustments-demo/copy.js","/bounded-adjustments-demo/model.js","/bounded-adjustments-demo/data.js","/training-review-demo/brand.png","/coach-review-demo/model.js","/coach-review-demo/catalog.js"];
function server(){return http.createServer((q,r)=>{const path=new URL(q.url,"http://localhost").pathname;if(q.method!=="GET"||!allowed.includes(path)){r.writeHead(404);return r.end();}
 const mime={".js":"text/javascript",".css":"text/css",".html":"text/html",".png":"image/png"}[p.extname(path)];
 r.writeHead(200,{"Content-Type":mime,"Cache-Control":"no-store"});r.end(fs.readFileSync(p.join(root,path)));});}
module.exports={server,allowed};
