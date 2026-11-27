import { test, mock } from 'node:test';
import { strict as assert } from 'node:assert';
import { createCipheriv, createDecipheriv, randomBytes } from 'node:crypto';
import { BACKUP_KIND, normalizeSQLiteSnapshot, parseEnvelope, sameSchema, validateRecoveryKey } from '../src/services/backupFormat.ts';

function sqliteBytes() {const value=new Uint8Array(512);value.set(Buffer.from('SQLite format 3\0','binary'));value[18]=2;value[19]=2;return value;}
test('WAL snapshots are detached without mutating the original',()=>{
 const bytes=sqliteBytes(), normalized=normalizeSQLiteSnapshot(bytes);
 assert.equal(bytes[18],2);assert.equal(normalized[18],1);assert.equal(normalized[19],1);
 assert.throws(()=>normalizeSQLiteSnapshot(new Uint8Array(200)));bytes[19]=1;assert.throws(()=>normalizeSQLiteSnapshot(bytes));
});
test('backup envelope rejects malformed input and schema mismatch',()=>{
 assert.equal(validateRecoveryKey('A'.repeat(64)),'a'.repeat(64));assert.throws(()=>validateRecoveryKey('password'));
 assert.throws(()=>parseEnvelope('{}')); assert.throws(()=>parseEnvelope('{garbage'));
 assert.throws(()=>parseEnvelope(JSON.stringify({kind:BACKUP_KIND,version:2,sealed:'A'.repeat(40)})));
 const schema=[{type:'table',name:'accounts',sql:'CREATE TABLE accounts (id INTEGER)'}];
 assert.equal(sameSchema(schema,[{...schema[0],sql:'CREATE   TABLE accounts (id INTEGER)'}]),true);
 assert.equal(sameSchema(schema,[{...schema[0],sql:'CREATE TABLE accounts (id TEXT)'}]),false);
});
// Exercise our envelope logic against a Node AES-256-GCM adapter matching Expo's API.
// This does not replace an on-device test of the native Expo implementation.
test('encrypted envelope round trips and rejects wrong keys and tampering',async()=>{
 class Key {
   bytes: Buffer;
   constructor(bytes: Buffer) {this.bytes=bytes;}
   static async generate(){return new Key(randomBytes(32));}
   static async import(hex:string){return new Key(Buffer.from(hex,'hex'));}
   async encoded(){return this.bytes.toString('hex');}
 }
 class Sealed {
   bytes: Buffer;
   constructor(bytes: Buffer) {this.bytes=bytes;}
   static fromCombined(value:string){return new Sealed(Buffer.from(value,'base64'));}
   async combined(){return this.bytes.toString('base64');}
 }
 const context=mock.module('expo-crypto',{namedExports:{AESEncryptionKey:Key,AESSealedData:Sealed,
   aesEncryptAsync:async (bytes:Uint8Array,key:Key)=>{const iv=randomBytes(12);const cipher=createCipheriv('aes-256-gcm',key.bytes,iv);const encrypted=Buffer.concat([cipher.update(bytes),cipher.final()]);return new Sealed(Buffer.concat([iv,encrypted,cipher.getAuthTag()]));},
   aesDecryptAsync:async (sealed:Sealed,key:Key)=>{const iv=sealed.bytes.subarray(0,12),tag=sealed.bytes.subarray(-16),encrypted=sealed.bytes.subarray(12,-16);const cipher=createDecipheriv('aes-256-gcm',key.bytes,iv);cipher.setAuthTag(tag);return new Uint8Array(Buffer.concat([cipher.update(encrypted),cipher.final()]));},
 }});
 try {
   const {generateRecoveryKey,sealDatabase,openDatabaseBackup}=await import('../src/services/backupCrypto.ts');
   const key=await generateRecoveryKey(), bytes=normalizeSQLiteSnapshot(sqliteBytes());
   const first=await sealDatabase(bytes,key), second=await sealDatabase(bytes,key);
   assert.notEqual(first,second); assert.deepEqual(await openDatabaseBackup(first,key),bytes);
   await assert.rejects(()=>openDatabaseBackup(first,'0'.repeat(64)),/authenticate/);
   const envelope=JSON.parse(first);const raw=Buffer.from(envelope.sealed,'base64');raw[15]^=1;envelope.sealed=raw.toString('base64');
   await assert.rejects(()=>openDatabaseBackup(JSON.stringify(envelope),key),/authenticate/);
 } finally {context.restore();}
});

test('WAL snapshot can be detached, checked and restored to a WAL database',async t=>{
 const {spawnSync}=await import('node:child_process'); const {mkdtempSync,readFileSync,writeFileSync,rmSync}=await import('node:fs'); const {join}=await import('node:path'); const {tmpdir}=await import('node:os');
 const python=['python3','python'].find(cmd=>spawnSync(cmd,['-c','import sqlite3; assert hasattr(sqlite3.Connection,"serialize")']).status===0);
 if(!python){t.skip('Python sqlite3 serialize/deserialize is unavailable');return;}
 const dir=mkdtempSync(join(tmpdir(),'pocketledger-wal-')); const source=join(dir,'source.db'),snapshot=join(dir,'snapshot.db'),dest=join(dir,'destination.db');
 try {
   const create=spawnSync(python,['-c',`import sqlite3,sys\nd=sqlite3.connect(sys.argv[1]);d.execute('pragma journal_mode=wal');d.execute('create table ledger (amount integer)');d.execute('insert into ledger values(12345)');d.commit();open(sys.argv[2],'wb').write(d.serialize());d.close()`,source,snapshot],{encoding:'utf8'});
   assert.equal(create.status,0,create.stderr);
   const normalized=normalizeSQLiteSnapshot(readFileSync(snapshot));writeFileSync(snapshot,normalized);
   const restore=spawnSync(python,['-c',`import sqlite3,sys\ns=sqlite3.connect(':memory:');s.deserialize(open(sys.argv[1],'rb').read());assert s.execute('pragma integrity_check').fetchone()[0]=='ok'; assert s.execute('select amount from ledger').fetchone()[0]==12345\nd=sqlite3.connect(sys.argv[2]);d.execute('pragma journal_mode=wal');d.execute('create table old(x)');d.commit();s.backup(d);assert d.execute('select amount from ledger').fetchone()[0]==12345;assert d.execute('pragma integrity_check').fetchone()[0]=='ok';d.close();s.close()`,snapshot,dest],{encoding:'utf8'});
   assert.equal(restore.status,0,restore.stderr);
 } finally {rmSync(dir,{recursive:true,force:true});}
});
