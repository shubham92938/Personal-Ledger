import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
import { uploadVerifiedBackup, downloadBackup, listDriveBackups } from '../src/services/driveApi.ts';
import * as format from '../src/services/backupFormat.ts';
const envelope=JSON.stringify({kind:format.BACKUP_KIND,version:1,sealed:'A'.repeat(40)});
function mockDrive(options:{mismatch?:boolean;badSession?:boolean;unauthorized?:boolean;badSize?:boolean}={}){
 let refreshed=0, calls:string[]=[], token='old';
 const tokens={get:async()=>token,invalidate:async()=>{refreshed++;token='new';}};
 const fetcher:typeof fetch=async(input,init)=>{
  const url=String(input);calls.push(`${init?.method??'GET'} ${url}`);
  if(options.unauthorized && (init?.headers as Record<string,string>).Authorization==='Bearer old') return new Response('',{status:401});
  if(url.includes('uploadType=resumable'))return new Response('',{status:200,headers:{Location:options.badSession?'https://evil.example/upload/drive/v3/files':'https://www.googleapis.com/upload/drive/v3/files?upload_id=abc'}});
  if(url.includes('upload_id=')){assert.equal(init?.body,envelope);return Response.json({id:'id_123',name:'PocketLedger-backup-a.plbackup',createdTime:'2026-01-01T00:00:00Z'});}
  if(url.includes('fields=id,name,size'))return Response.json({id:'id_123',name:'PocketLedger-backup-a.plbackup',size:String(options.badSize?999999999:envelope.length),trashed:false});
  if(url.includes('alt=media'))return new Response(options.mismatch?envelope.replace('AAAA','BBBB'):envelope);
  if(url.includes('/files?')){
   if(url.includes('pageToken=next'))return Response.json({files:[{id:'id_2',name:'PocketLedger-backup-b.plbackup',createdTime:'2026-01-01'}]});
   return Response.json({files:[{id:'id_123',name:'PocketLedger-backup-a.plbackup',createdTime:'2026-01-02'}],nextPageToken:'next'});
  }
  throw new Error(`Unexpected request ${url}`);
 };
 return {tokens,fetcher,calls,get refreshed(){return refreshed;}};
}
test('Drive uploads are encrypted envelopes and must be downloaded and verified',async()=>{
 const fake=mockDrive({unauthorized:true});
 const result=await uploadVerifiedBackup(envelope,fake.tokens,fake.fetcher);
 assert.equal(result.id,'id_123');assert.equal(fake.refreshed,1);assert(fake.calls.some(x=>x.includes('alt=media')));
 assert.equal((await listDriveBackups(fake.tokens,fake.fetcher)).length,2);
});
test('Drive refuses untrusted sessions, mismatched contents and oversized downloads',async()=>{
 let fake=mockDrive({badSession:true});await assert.rejects(()=>uploadVerifiedBackup(envelope,fake.tokens,fake.fetcher),/Invalid Google Drive upload session/);assert(!fake.calls.some(x=>x.includes('evil.example')));
 fake=mockDrive({mismatch:true});await assert.rejects(()=>uploadVerifiedBackup(envelope,fake.tokens,fake.fetcher),/verification failed/);
 fake=mockDrive({badSize:true});await assert.rejects(()=>downloadBackup('id_123',fake.tokens,fake.fetcher),/too large/);assert(!fake.calls.some(x=>x.includes('alt=media')));
 await assert.rejects(()=>downloadBackup('../bad',fake.tokens,fake.fetcher),/file ID/);
 await assert.rejects(()=>uploadVerifiedBackup('plaintext',fake.tokens,fake.fetcher),/valid PocketLedger/);
});

test('backup orchestration binds account and records success only after verification',async()=>{
 const values=new Map<string,string>();const secure=new Map<string,string>();let user={id:'user-one',email:'a',granted:true};let fail=false;let calls=0;
 const storage={getItem:async(k:string)=>values.get(k)??null,setItem:async(k:string,v:string)=>{values.set(k,v);}};
 const keyStore={getItemAsync:async(k:string)=>secure.get(k)??null,setItemAsync:async(k:string,v:string)=>{secure.set(k,v);},deleteItemAsync:async(k:string)=>{secure.delete(k);}};
 const deps:Record<string,unknown>={
  'expo-secure-store':keyStore,'expo-sqlite/kv-store':storage,'./backupFormat':format,
  './manualBackup':{createEncryptedBackup:async()=>envelope,restoreEncryptedBackup:async()=>'/safety'},
  './googleAuth':{currentGoogleUser:()=>user,googleTokens:{},connectGoogle:async()=>user,signOutGoogle:async()=>{}},
  './driveApi':{uploadVerifiedBackup:async()=>{calls++;if(fail)throw new Error('verification failed');return {id:'id_123'};},listDriveBackups:async()=>[],downloadBackup:async()=>envelope},
 };
 const source=readFileSync(new URL('../src/services/driveBackup.ts',import.meta.url),'utf8');
 const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText;
 const module:{exports:any}={exports:{}};
 new Function('require','exports','module',js)((name:string)=>{if(!(name in deps))throw new Error(name);return deps[name];},module.exports,module);
 const api=module.exports;const key='a'.repeat(64);
 await assert.rejects(()=>api.enableDriveBackup(key,'b'.repeat(64)),/does not match/);
 await api.enableDriveBackup(key,key);assert.equal(secure.size,1);
 fail=true;await assert.rejects(()=>api.runDriveBackup(),/verification failed/);
 let status=await api.driveStatus();assert.equal(status.settings.lastVerified,undefined);assert.equal(status.settings.lastError,'verification failed');
 fail=false;await api.runDriveBackup();status=await api.driveStatus();assert(status.settings.lastVerified);assert.equal(status.settings.lastError,undefined);
 await api.runDriveBackup(true);assert.equal(calls,2);
 user={...user,id:'different'};await assert.rejects(()=>api.runDriveBackup(),/same Google account/);status=await api.driveStatus();assert(status.settings.lastVerified);assert.match(status.settings.lastError,/same Google account/);
 await api.disableDriveBackup();assert.equal(secure.size,0);assert.equal((await api.driveStatus()).settings.enabled,false);
});
