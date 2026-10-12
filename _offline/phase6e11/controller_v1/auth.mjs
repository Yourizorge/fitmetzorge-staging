import {Halt,UUID,sha} from './core.mjs';
import {verifiedClaims,BASE} from '../edge_bridge_v2/handler.mjs';
export const EMAILS=Object.freeze({a_member:'zorgeyouri+6e9-a-lid@gmail.com',a_trainer:'zorgeyouri+6e9-a-trainer@gmail.com',b_member:'zorgeyouri+6e9-b-lid@gmail.com'});
export function assertIdentity(identity,expected){
 if(!expected||!UUID.test(expected.id)||!Object.hasOwn(EMAILS,expected.role)||
    identity?.id!==expected.id||identity.email!==EMAILS[expected.role]||identity.registered_role!==expected.role||
    identity.profile_role!==(expected.role==='a_trainer'?'trainer':'client')||identity.trainer_id!==expected.trainer_id||
    identity.enabled!==true||identity.operator!==(expected.role==='a_trainer'))throw new Halt('auth','identity_not_allowlisted');
}
export class SyntheticAuth {
 #access=null;#refresh=null;#link=null;#claims=null;#revoked=false;#issued=false;#request;#issueRequest;
 constructor({expected,identity,key,admin,fetcher=fetch,now=Date.now,check=()=>{},guard}){
  assertIdentity(identity,expected);
  if(typeof key!=='string'||!key||typeof admin!=='string'||!admin)throw new Halt('configuration','auth_credentials_absent');
  this.expected=Object.freeze(structuredClone(expected));this.fetcher=fetcher;this.now=now;this.check=check;
  // Credentials are captured, not object properties serialized into evidence.
  this.#request=async(path,method,body,authorization,privileged=false)=>{
   this.check();
   const allowed=new Set(['/admin/generate_link','/verify','/user','/token?grant_type=refresh_token','/logout?scope=local']);
   if(!allowed.has(path))throw new Halt('auth','auth_path_denied');
   const send=async()=>{
   let response;
   try{response=await fetcher(BASE+'/auth/v1'+path,{method,redirect:'error',signal:AbortSignal.timeout(5000),
     headers:{apikey:privileged?admin:key,...(authorization?{Authorization:'Bearer '+authorization}:{}),'Content-Type':'application/json'},
     ...(body===undefined?{}:{body:JSON.stringify(body)})});}catch{throw new Halt('auth','auth_transport_failed');}
   const raw=await response.text();if(raw.length>65536)throw new Halt('auth','auth_response_budget');
   let value=null;try{value=raw?JSON.parse(raw):null;}catch{throw new Halt('auth','auth_response_invalid');}
   const requestId=response.headers.get('x-request-id')||response.headers.get('sb-request-id');
   const receipt={http_status:response.status,request_id:UUID.test(requestId||'')?requestId:null};
   if(!response.ok)throw new Halt('auth',response.status===429?'auth_rate_limited':'auth_request_rejected');
   return {value,receipt};
   };
   // Verification and refresh issue session tokens too. None of the three
   // issuing endpoints may run on the strength of an earlier guard check.
   if(['/admin/generate_link','/verify','/token?grant_type=refresh_token'].includes(path)){
    if(typeof guard!=='function')throw new Halt('auth_guard','identity_guard_absent');
    return guard(this.expected,send);
   }
   return send();
  };
  this.#issueRequest=()=>{
   return this.#request('/admin/generate_link','POST',{type:'magiclink',email:EMAILS[this.expected.role]},admin,true);
  };
 }
 async issue(){
  if(this.#issued||this.#revoked)throw new Halt('auth','auth_sequence');
  this.#issued=true;
  const {value,receipt}=await this.#issueRequest();
  const user=value?.user||value,properties=value?.properties||value;
  if(user?.id!==this.expected.id||user.email!==EMAILS[this.expected.role]||typeof properties.hashed_token!=='string'||!properties.hashed_token)
    throw new Halt('auth','issued_identity_mismatch');
  this.#link=properties.hashed_token;return {...receipt,user_sha:await sha(this.expected.id)};
 }
 async verify(){
  if(!this.#link||this.#access||this.#revoked)throw new Halt('auth','auth_sequence');
  const token=this.#link;this.#link=null;
  const {value,receipt}=await this.#request('/verify','POST',{type:'magiclink',token_hash:token},'');
  this.#adopt(value);return {...receipt,session_sha:await sha(this.#claims.session_id)};
 }
 #adopt(value){
  if(typeof value?.access_token!=='string'||typeof value?.refresh_token!=='string'||!value.refresh_token)throw new Halt('auth','session_missing');
  let claims;try{claims=verifiedClaims('Bearer '+value.access_token,value.user,this.now());}catch{throw new Halt('auth','session_identity_mismatch');}
  if(claims.sub!==this.expected.id||value.user.email!==EMAILS[this.expected.role]||this.#claims&&claims.session_id!==this.#claims.session_id)
    throw new Halt('auth','session_identity_mismatch');
  this.#access=value.access_token;this.#refresh=value.refresh_token;this.#claims=claims;
 }
 async getUser(){
  if(!this.#access||this.#revoked)throw new Halt('auth','auth_sequence');
  const {value,receipt}=await this.#request('/user','GET',undefined,this.#access);
  let claims;try{claims=verifiedClaims('Bearer '+this.#access,value,this.now());}catch{throw new Halt('auth','session_identity_mismatch');}
  if(claims.sub!==this.expected.id||claims.session_id!==this.#claims.session_id)throw new Halt('auth','session_identity_mismatch');
  return {...receipt,session_sha:await sha(claims.session_id)};
 }
 async refresh(){
  if(!this.#access||!this.#refresh||this.#revoked)throw new Halt('auth','auth_sequence');
  const old=this.#refresh;this.#refresh=null;
  const {value,receipt}=await this.#request('/token?grant_type=refresh_token','POST',{refresh_token:old},'');
  this.#adopt(value);return {...receipt,session_sha:await sha(this.#claims.session_id)};
 }
 async logout(){
  if(!this.#access||this.#revoked)throw new Halt('auth','auth_sequence');
  const {receipt}=await this.#request('/logout?scope=local','POST',undefined,this.#access);
  this.#revoked=true;this.#refresh=null;return {...receipt,session_sha:await sha(this.#claims.session_id)};
 }
 async withToken(callback){
  if(!this.#access||this.#revoked||this.#claims.exp*1000<=this.now())throw new Halt('auth','auth_sequence');
  this.check();return callback(this.#access);
 }
 session(){if(!this.#claims)throw new Halt('auth','session_missing');return this.#claims.session_id;}
 clear(){this.#access=null;this.#refresh=null;this.#link=null;this.#claims=null;this.#revoked=true;}
}
