"use strict";
const http=require('node:http'),fs=require('node:fs'),p=require('node:path'),root=p.resolve(__dirname,'../..');
const allowed=fs.readdirSync(p.join(root,'recovery-checkin-demo')).map(f=>'/recovery-checkin-demo/'+f).concat('/training-review-demo/brand.png');
function server(){return http.createServer((req,res)=>{const path=new URL(req.url,'http://localhost').pathname;if(req.method!=='GET'||!allowed.includes(path)){res.writeHead(404);return res.end();}res.setHeader('Content-Type',path.endsWith('.js')?'text/javascript':path.endsWith('.css')?'text/css':path.endsWith('.png')?'image/png':'text/html');res.end(fs.readFileSync(p.join(root,path)));});}module.exports={server,allowed};
