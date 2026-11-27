import * as SQLite from 'expo-sqlite';
import { File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import * as DocumentPicker from 'expo-document-picker';
import { Platform } from 'react-native';
import { withLedgerDatabase } from '../database/database';
import { MAX_ENVELOPE_CHARS, normalizeSQLiteSnapshot, sameSchema, SchemaRow } from './backupFormat';
import { openDatabaseBackup, sealDatabase } from './backupCrypto';

async function schema(db: SQLite.SQLiteDatabase) {
  return db.getAllAsync<SchemaRow>("SELECT type,name,sql FROM sqlite_master WHERE type IN ('table','index','view','trigger') AND name NOT LIKE 'sqlite_%' ORDER BY type,name");
}
async function verify(db: SQLite.SQLiteDatabase, expectedSchema: SchemaRow[]) {
  const version=await db.getFirstAsync<{user_version:number}>('PRAGMA user_version');
  if (version?.user_version !== 3) throw new Error('This backup has an unsupported database version. Only version 3 can currently be restored.');
  const check=await db.getAllAsync<Record<string,string>>('PRAGMA integrity_check');
  if (check.length !== 1 || Object.values(check[0])[0] !== 'ok') throw new Error('Database integrity check failed.');
  const foreignKeys=await db.getAllAsync('PRAGMA foreign_key_check');
  if (foreignKeys.length) throw new Error('Backup contains broken references.');
  if (!sameSchema(expectedSchema,await schema(db))) throw new Error('Backup database structure does not match this app version.');
}
function supported() {if (Platform.OS === 'web') throw new Error('Manual backup is available on Android and iOS, not in the web preview.');}
/** Create an authenticated snapshot; shared by file export and Drive. */
export async function createEncryptedBackup(key: string): Promise<string> {
  supported();
  const bytes=await withLedgerDatabase(async db=>{
    const expected=await schema(db); await verify(db,expected);
    const data=normalizeSQLiteSnapshot(await db.serializeAsync());
    const snapshot=await SQLite.deserializeDatabaseAsync(data);
    try {await verify(snapshot,expected);} finally {await snapshot.closeAsync();}
    return data;
  });
  return sealDatabase(bytes,key);
}
/** Opens a share sheet for an encrypted file; this does not prove it was saved elsewhere. */
export async function shareEncryptedBackup(key: string) {
  supported();
  if (!(await Sharing.isAvailableAsync())) throw new Error('File sharing is unavailable on this device.');
  const content=await createEncryptedBackup(key);
  const file=new File(Paths.cache,`PocketLedger-${Date.now()}.plbackup`);
  await file.write(content);
  await Sharing.shareAsync(file.uri,{mimeType:'application/octet-stream',dialogTitle:'Save encrypted PocketLedger backup'});
}
/** Pick the encrypted file. Never interpret opening the picker as a successful backup. */
export async function pickEncryptedBackup(): Promise<string | null> {
  supported();
  const picked=await DocumentPicker.getDocumentAsync({type:'*/*',copyToCacheDirectory:true,multiple:false});
  if (picked.canceled) return null;
  const file=new File(picked.assets[0].uri);
  if ((picked.assets[0].size ?? file.size ?? 0) > MAX_ENVELOPE_CHARS) throw new Error('Backup file is too large.');
  return file.text();
}
/** Validate and authenticate before overwriting. A verified encrypted safety copy is written first. */
export async function restoreEncryptedBackup(content: string, key: string): Promise<string> {
  supported();
  const restoredBytes=normalizeSQLiteSnapshot(await openDatabaseBackup(content,key));
  return withLedgerDatabase(async current=>{
    const expected=await schema(current);
    await verify(current,expected);
    const candidate=await SQLite.deserializeDatabaseAsync(restoredBytes);
    try {
      await verify(candidate,expected);
      const before=normalizeSQLiteSnapshot(await current.serializeAsync());
      const safetyDb=await SQLite.deserializeDatabaseAsync(before);
      try {await verify(safetyDb,expected);} finally {await safetyDb.closeAsync();}
      const safetyContent=await sealDatabase(before,key);
      const safety=new File(Paths.document,`PocketLedger-safety-${Date.now()}.plbackup`);
      await safety.write(safetyContent);
      const checked=await openDatabaseBackup(await safety.text(),key);
      if (checked.length!==before.length || checked.some((value,index)=>value!==before[index])) throw new Error('Safety backup verification failed; nothing was restored.');
      try {
        await SQLite.backupDatabaseAsync({sourceDatabase:candidate,destDatabase:current});
        await verify(current,expected);
      } catch (error) {
        // SQLite's backup operation is transactional, but also attempt recovery from
        // the in-memory pre-restore snapshot if verification or replacement fails.
        const previous=await SQLite.deserializeDatabaseAsync(before);
        try {await SQLite.backupDatabaseAsync({sourceDatabase:previous,destDatabase:current}); await verify(current,expected);}
        catch {throw new Error('Restore failed and automatic recovery could not be verified. The encrypted safety copy is retained on this device.');}
        finally {await previous.closeAsync();}
        throw error;
      }
      return safety.uri;
    } finally {await candidate.closeAsync();}
  });
}
/** Allow the user to take the most recent pre-restore safety copy off this device. */
export async function shareLatestSafetyBackup() {
  supported();
  if (!(await Sharing.isAvailableAsync())) throw new Error('File sharing is unavailable on this device.');
  const files=Paths.document.list().filter((entry): entry is File => entry instanceof File && /^PocketLedger-safety-\d+\.plbackup$/.test(entry.name)).sort((a,b)=>b.name.localeCompare(a.name));
  if (!files.length) throw new Error('No pre-restore safety copy is available on this device.');
  await Sharing.shareAsync(files[0].uri,{mimeType:'application/octet-stream',dialogTitle:'Save encrypted pre-restore safety copy'});
}
