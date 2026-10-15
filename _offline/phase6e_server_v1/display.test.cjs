'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),display=require('./display.js');
test('display-only conversion reuses training model, keeps exact source and null/zero',()=>{
 assert.equal(display.text(40,'kg','imperial','missing'),'≈ 88.18 lb (40 kg)');
 assert.equal(display.text(88.18,'lb','metric','missing'),'≈ 40 kg (88.18 lb)');
 assert.equal(display.text(0,'kg','imperial','missing'),'≈ 0 lb (0 kg)');
 assert.equal(display.text(null,'kg','metric','missing'),'missing');
 assert.equal(display.text(20.123,'kg','metric','missing'),'20.123 kg');
 for(const value of [NaN,Infinity,-1,'0'])assert.equal(display.weight(value,'kg','imperial'),null);
 assert.equal(display.weight(1,'unknown','metric'),null);
});
test('three-language day and intake captions never change technical values',()=>{
 for(const language of [0,1,2]){assert.notEqual(display.caption('mon',language),'mon');assert.ok(display.caption('beginner',language));}
 assert.equal(display.caption('unmapped-rule',0),'unmapped-rule');
});
