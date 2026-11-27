import { AESEncryptionKey, AESSealedData, aesEncryptAsync, aesDecryptAsync } from 'expo-crypto';
import { BACKUP_KIND, parseEnvelope, requireSQLiteHeader, validateRecoveryKey } from './backupFormat.ts';
export async function generateRecoveryKey(): Promise<string> {return (await AESEncryptionKey.generate()).encoded('hex');}
export async function sealDatabase(bytes: Uint8Array, keyHex: string): Promise<string> {
  requireSQLiteHeader(bytes);
  const key=await AESEncryptionKey.import(validateRecoveryKey(keyHex),'hex');
  const sealed=await aesEncryptAsync(bytes,key);
  return JSON.stringify({kind:BACKUP_KIND,version:1,sealed:await sealed.combined('base64')});
}
export async function openDatabaseBackup(content: string, keyHex: string): Promise<Uint8Array> {
  const envelope=parseEnvelope(content);
  const key=await AESEncryptionKey.import(validateRecoveryKey(keyHex),'hex');
  let plaintext: Uint8Array;
  try { plaintext=await aesDecryptAsync(AESSealedData.fromCombined(envelope.sealed),key); }
  catch {throw new Error('Could not authenticate the backup. The recovery key may be incorrect or the file damaged.');}
  requireSQLiteHeader(plaintext);
  return plaintext;
}
