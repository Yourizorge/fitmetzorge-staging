"use strict";
const http=require('node:http'),fs=require('node:fs'),p=require('node:path'),root=p.resolve(__dirname,'../..');
const allowed=['catalog.js','model.js','fixtures.js','copy.js','review.js','app.js','index.html','demo.css'].map(f=>'/nutrition-rules-demo/'+f).concat('/training-review-demo/brand.png');
function server(){return http.createServer((req,res)=>{const path=new URL(req.url,'http://localhost').pathname;if(req.method!=='GET'||!allowed.includes(path)){res.writeHead(404);return res.end();}res.setHeader('Content-Type',path.endsWith('.js')?'text/javascript':path.endsWith('.css')?'text/css':path.endsWith('.png')?'image/png':'text/html');res.end(fs.readFileSync(p.join(root,path)));});}module.exports={server,allowed};
