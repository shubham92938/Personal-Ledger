import { MAX_ENVELOPE_CHARS, parseEnvelope } from './backupFormat.ts';

const BASE='https://www.googleapis.com/drive/v3';
const UPLOAD='https://www.googleapis.com/upload/drive/v3/files';
const PREFIX='PocketLedger-backup-';
export type DriveBackup = {id:string;name:string;createdTime:string};
type Tokens = {get:()=>Promise<string>;invalidate:(token:string)=>Promise<void>};
type Fetch = typeof fetch;

/** Restrict retry requests to Google; never send an OAuth token to an arbitrary upload URL. */
function uploadUrl(value:string):string {
 let url:URL;
 try {url=new URL(value);} catch {throw new Error('Invalid Google Drive upload session.');}
 if(url.protocol!=='https:' || !['www.googleapis.com','upload.googleapis.com'].includes(url.hostname) || url.username || url.password || url.port || !url.pathname.startsWith('/upload/drive/v3/files')) throw new Error('Invalid Google Drive upload session.');
 return url.toString();
}
function validId(id:string) {if(!/^[a-zA-Z0-9_-]{1,200}$/.test(id))throw new Error('Invalid Google Drive file ID.'); return id;}
async function request(fetcher:Fetch,tokens:Tokens,url:string,init:RequestInit={}):Promise<Response>{
 let token=await tokens.get();
 let response=await fetcher(url,{...init,headers:{...init.headers,Authorization:`Bearer ${token}`}});
 if(response.status===401) {await tokens.invalidate(token);token=await tokens.get();response=await fetcher(url,{...init,headers:{...init.headers,Authorization:`Bearer ${token}`}});}
 if(!response.ok) throw new Error(`Google Drive request failed (HTTP ${response.status}).`);
 return response;
}
/** Upload a new immutable encrypted envelope and read it back before reporting success. */
export async function uploadVerifiedBackup(content:string,tokens:Tokens,fetcher:Fetch=fetch):Promise<DriveBackup>{
 parseEnvelope(content);
 const metadata={name:`${PREFIX}${new Date().toISOString().replace(/[:.]/g,'-')}.plbackup`,parents:['appDataFolder'],mimeType:'application/octet-stream'};
 const start=await request(fetcher,tokens,`${UPLOAD}?uploadType=resumable&fields=id,name,createdTime`,{method:'POST',headers:{'Content-Type':'application/json; charset=UTF-8','X-Upload-Content-Type':'application/octet-stream','X-Upload-Content-Length':String(content.length)},body:JSON.stringify(metadata)});
 const location=start.headers.get('Location'); if(!location)throw new Error('Google Drive did not return an upload session.');
 const uploaded=await request(fetcher,tokens,uploadUrl(location),{method:'PUT',headers:{'Content-Type':'application/octet-stream'},body:content});
 const file=await uploaded.json() as DriveBackup;
 if(!file || typeof file.id!=='string')throw new Error('Google Drive did not confirm the uploaded file.');
 const id=validId(file.id);
 const downloaded=await downloadBackup(id,tokens,fetcher);
 if(downloaded!==content)throw new Error('Google Drive backup verification failed.');
 return {id,name:typeof file.name==='string'?file.name:metadata.name,createdTime:typeof file.createdTime==='string'?file.createdTime:new Date().toISOString()};
}
/** Download only after bounded metadata is checked; the encrypted envelope is validated again. */
export async function downloadBackup(id:string,tokens:Tokens,fetcher:Fetch=fetch):Promise<string>{
 id=validId(id);
 const meta=await (await request(fetcher,tokens,`${BASE}/files/${id}?fields=id,name,size,trashed`)).json() as {id?:string;name?:string;size?:string;parents?:string[];trashed?:boolean};
 const size=Number(meta.size);
 if(meta.id!==id || !meta.name?.startsWith(PREFIX) || meta.trashed || !Number.isSafeInteger(size) || size<=0 || size>MAX_ENVELOPE_CHARS) throw new Error('Google Drive backup metadata is invalid or too large.');
 const response=await request(fetcher,tokens,`${BASE}/files/${id}?alt=media`);
 const content=await response.text();
 if(content.length!==size || content.length>MAX_ENVELOPE_CHARS)throw new Error('Google Drive backup download is incomplete.');
 parseEnvelope(content);return content;
}
export async function listDriveBackups(tokens:Tokens,fetcher:Fetch=fetch):Promise<DriveBackup[]>{
 const files:DriveBackup[]=[];let page:string|undefined;let pages=0;
 do {
  if(++pages>11)throw new Error('Too many Google Drive backups to list safely.');
  const params=new URLSearchParams({spaces:'appDataFolder',q:`name contains '${PREFIX}' and trashed = false`,fields:'nextPageToken,files(id,name,createdTime)',orderBy:'createdTime desc',pageSize:'100'});
  if(page)params.set('pageToken',page);
  const result=await (await request(fetcher,tokens,`${BASE}/files?${params.toString()}`)).json() as {files?:DriveBackup[];nextPageToken?:string};
  if(!Array.isArray(result.files))throw new Error('Google Drive returned an invalid backup list.');
  for(const file of result.files) if(typeof file.id==='string' && /^[a-zA-Z0-9_-]{1,200}$/.test(file.id) && typeof file.name==='string' && file.name.startsWith(PREFIX) && typeof file.createdTime==='string') files.push(file);
  page=result.nextPageToken;
  if(files.length>1000)throw new Error('Too many Google Drive backups to list safely.');
 } while(page);
 return files;
}
