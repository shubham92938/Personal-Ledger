import * as SecureStore from 'expo-secure-store';
import Storage from 'expo-sqlite/kv-store';
import { createEncryptedBackup, restoreEncryptedBackup } from './manualBackup';
import { validateRecoveryKey } from './backupFormat';
import { connectGoogle, currentGoogleUser, googleTokens, signOutGoogle } from './googleAuth';
import { downloadBackup, listDriveBackups, uploadVerifiedBackup } from './driveApi';
const KEY='pocketledger.drive.recovery-key';
const SETTINGS='pocketledger.drive.settings.v1';
const DAY=24*60*60*1000;
type Settings={enabled:boolean;accountId:string;lastVerified?:string;lastError?:string;lastAttempt?:string};
let active:Promise<unknown>|undefined;
async function settings():Promise<Settings|null>{const raw=await Storage.getItem(SETTINGS);if(!raw)return null;try{const item=JSON.parse(raw) as Settings;return typeof item.accountId==='string' && typeof item.enabled==='boolean'?item:null;}catch{throw new Error('Google Drive settings could not be read.');}}
async function save(value:Settings){await Storage.setItem(SETTINGS,JSON.stringify(value));}
async function exclusive<T>(fn:()=>Promise<T>):Promise<T>{if(active)throw new Error('A Google Drive operation is already in progress.');const task=fn();active=task;try{return await task;}finally{active=undefined;}}
function bound(accountId:string){const current=currentGoogleUser();if(!current || current.id!==accountId || !current.granted)throw new Error('Sign in to the same Google account and grant Drive access.');return current;}
export async function connectDrive(){return exclusive(connectGoogle);}
export async function driveStatus(){const saved=await settings();let user:ReturnType<typeof currentGoogleUser>=null;try{user=currentGoogleUser();}catch{/* Not configured or unavailable. */}return {settings:saved,user};}
/** Explicit opt-in only; secret stays in Keystore and must also be saved by user off-device. */
export async function enableDriveBackup(key:string,confirmation:string){return exclusive(async()=>{
 const normalized=validateRecoveryKey(key);if(normalized!==validateRecoveryKey(confirmation))throw new Error('The recovery key confirmation does not match.');
 const user=currentGoogleUser();if(!user?.id || !user.granted)throw new Error('Sign in and grant Google Drive access first.');
 await SecureStore.setItemAsync(KEY,normalized);
 await save({enabled:true,accountId:user.id});
});}
export async function disableDriveBackup(){return exclusive(async()=>{const saved=await settings();if(saved)await save({...saved,enabled:false});await SecureStore.deleteItemAsync(KEY);});}
export async function disconnectDrive(){return exclusive(async()=>{const saved=await settings();if(saved)await save({...saved,enabled:false});await SecureStore.deleteItemAsync(KEY);await signOutGoogle();});}
export async function runDriveBackup(onlyIfDue=false){return exclusive(async()=>{
 const saved=await settings();if(!saved?.enabled)throw new Error('Automatic Google Drive backup is not enabled.');
 if(onlyIfDue && saved.lastVerified && Date.now()-Date.parse(saved.lastVerified)<DAY)return null;
 const attempted={...saved,lastAttempt:new Date().toISOString()};await save(attempted);
 try {
  bound(saved.accountId);
  const key=await SecureStore.getItemAsync(KEY);if(!key)throw new Error('Recovery key is unavailable on this device. Enable backup again.');
  const content=await createEncryptedBackup(key);
  // Recheck immediately before uploading in case another account was selected.
  bound(saved.accountId);
  const result=await uploadVerifiedBackup(content,googleTokens);
  await save({...attempted,lastVerified:new Date().toISOString(),lastError:undefined});return result;
 }catch(error){await save({...attempted,lastError:error instanceof Error?error.message:'Google Drive backup failed.'});throw error;}
});}
export async function driveBackups(){return exclusive(async()=>{const user=currentGoogleUser();if(!user?.granted)throw new Error('Sign in and grant Google Drive access first.');return listDriveBackups(googleTokens);});}
export async function restoreDriveBackup(id:string,key:string){return exclusive(async()=>{const user=currentGoogleUser();if(!user?.granted)throw new Error('Sign in and grant Google Drive access first.');const content=await downloadBackup(id,googleTokens);return restoreEncryptedBackup(content,validateRecoveryKey(key));});}
