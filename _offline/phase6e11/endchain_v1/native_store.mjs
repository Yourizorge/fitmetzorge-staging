import {Store} from '../controller_v1/store.mjs';
import {Halt,metadata} from '../controller_v1/core.mjs';
// The existing store serializes metadata for text transports. Postgres.js
// serializes JSONB parameters itself; passing that string double-encodes it.
export class NativeStore extends Store{
 async one(sql,args){
  const parameters=[...args],index={11:9,6:4,4:2}[args.length];
  if(index!==undefined){
   if(!sql.includes('$'+(index+1)+'::jsonb')||typeof parameters[index]!=='string')
    throw new Halt('evidence','native_metadata_slot_changed');
   let value;try{value=JSON.parse(parameters[index]);}catch{throw new Halt('evidence','native_metadata_invalid');}
   if(!value||Array.isArray(value)||typeof value!=='object')throw new Halt('evidence','native_metadata_invalid');
   parameters[index]=metadata(value);
  }else if(![3,5].includes(args.length))throw new Halt('evidence','native_store_shape_changed');
  return super.one(sql,parameters);
 }
}
