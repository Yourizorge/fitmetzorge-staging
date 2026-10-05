'use strict';
const http=require('node:http'),fs=require('node:fs'),p=require('node:path'),root=p.resolve(__dirname,'../..');
const html=fs.readFileSync(p.join(root,'daily-coach-demo/index.html'),'utf8'),allowed=fs.readdirSync(p.join(root,'daily-coach-demo')).map(f=>'/daily-coach-demo/'+f).concat([...html.matchAll(/(?:src|href)="\.\.\/([^"]+)"/g)].map(x=>'/'+x[1]));
function server(){return http.createServer((req,res)=>{const file=new URL(req.url,'http://localhost').pathname;if(req.method!=='GET'||!allowed.includes(file)){res.writeHead(404);return res.end();}res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':file.endsWith('.png')?'image/png':'text/html');res.end(fs.readFileSync(p.join(root,file)));});}module.exports={server,allowed};
