'use strict';
const D=require('./domain.cjs');
const R=require('./registration12.cjs');
const W=require('./workout12.cjs');
const A=require('./account_center.cjs');
let raw='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',chunk=>{raw+=chunk;if(Buffer.byteLength(raw)>10*1024*1024)process.exit(2);});
process.stdin.on('end',()=>{
 try{
  const p=JSON.parse(raw);
  const value=p.op==='access'?A.access(p.source,p.now):p.op==='workout12_view'?W.view(p.state):p.op==='workout12_transition'?W.transition(p.state,p.request):p.op==='registration_initial'?R.initial(p.scenario):p.op==='registration_view'?R.view(p.state):
   p.op==='registration_transition'?R.transition(p.state,p.request):p.op==='initial'?D.initial(p.route):p.op==='view'?D.view(p.state):
   p.op==='transition'?D.transition(p.state,p.request,p.role):null;
  if(value===null)throw Error('operation');
  process.stdout.write(JSON.stringify({ok:true,value}));
 }catch(e){const code=/^(missing|not_applicable):[a-zA-Z]+$/.test(e.message)?e.message.replace(':','_'):e.message;process.stdout.write(JSON.stringify({ok:false,code:/^[a-zA-Z_]+$/.test(code)?code:'domain_error'}));}
});
