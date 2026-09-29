"use strict";
const block=()=>{throw Error("offline_network_forbidden");};
globalThis.fetch=block;
for(const n of ["http","https"]){const m=require("node:"+n);m.request=block;m.get=block;}
const net=require("node:net");net.connect=block;net.createConnection=block;net.Socket.prototype.connect=block;
require("node:tls").connect=block;
for(const m of [require("node:dns"),require("node:dns/promises")])for(const n of ["lookup","resolve","resolve4","resolve6"])m[n]=block;
