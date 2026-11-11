import {inspectConfiguration} from './config_shape.mjs';
const PROJECT_URL='https://mokxyyullfhkfalopbzd.supabase.co';
export function connectionOptions(value, ca, sessionHost) {
  // The driver receives explicit TLS options, never the URL's weaker SSL selector.
  const failures=inspectConfiguration(PROJECT_URL,value,sessionHost)
    .filter(x=>x!=='database_sslmode');
  if(failures.length || sessionHost!=='aws-0-eu-west-2.pooler.supabase.com' ||
     !ca?.includes('-----BEGIN CERTIFICATE-----')) throw Error('database_configuration_invalid');
  const u=new URL(value);
  return {host:u.hostname,port:5432,database:'postgres',username:decodeURIComponent(u.username),
    password:decodeURIComponent(u.password),
    ssl:{ca,rejectUnauthorized:true,servername:u.hostname},
    max:1,max_pipeline:1,prepare:false,fetch_types:false,debug:false,
    connect_timeout:5,idle_timeout:2,max_lifetime:30,
    connection:{application_name:'fmz6e11-request-v4',statement_timeout:5000,lock_timeout:1000},
    onnotice:()=>{}};
}
