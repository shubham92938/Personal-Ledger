/** Versioned encrypted-backup envelope. It never contains plaintext ledger rows. */
export const BACKUP_KIND = 'PocketLedger encrypted SQLite backup';
export const MAX_ENVELOPE_CHARS = 40 * 1024 * 1024;
export const MAX_DATABASE_BYTES = 25 * 1024 * 1024;
export type BackupEnvelope = { kind: typeof BACKUP_KIND; version: 1; sealed: string };
export function validateRecoveryKey(key: string): string {
  const normalized = key.trim().toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(normalized)) throw new Error('Enter the 64-character hexadecimal recovery key.');
  return normalized;
}
export function parseEnvelope(content: string): BackupEnvelope {
  if (content.length > MAX_ENVELOPE_CHARS) throw new Error('Backup file is too large.');
  let value: unknown;
  try {value = JSON.parse(content);} catch {throw new Error('This is not a valid PocketLedger backup.');}
  if (!value || typeof value !== 'object') throw new Error('This is not a valid PocketLedger backup.');
  const data = value as Record<string, unknown>;
  if (data.kind !== BACKUP_KIND || data.version !== 1 || typeof data.sealed !== 'string' || data.sealed.length < 40 || data.sealed.length % 4 !== 0 || !/^[A-Za-z0-9+/]+={0,2}$/.test(data.sealed)) throw new Error('This backup format is invalid or unsupported.');
  return {kind: BACKUP_KIND, version: 1, sealed: data.sealed};
}
export function requireSQLiteHeader(bytes: Uint8Array): void {
  const signature = [83,81,76,105,116,101,32,102,111,114,109,97,116,32,51,0];
  if (bytes.length < 100 || bytes.length > MAX_DATABASE_BYTES || !signature.every((value,index)=>bytes[index]===value)) throw new Error('Decrypted file is not a supported SQLite database.');
}
export type SchemaRow = {type: string; name: string; sql: string | null};
export function sameSchema(expected: SchemaRow[], actual: SchemaRow[]): boolean {
  const canonical = (rows: SchemaRow[]) => rows.map(({type,name,sql})=>`${type}\u0000${name}\u0000${sql?.replace(/\s+/g,' ').trim() ?? ''}`).sort();
  const left=canonical(expected),right=canonical(actual);
  return left.length===right.length && left.every((value,index)=>value===right[index]);
}
/** SQLite serialized from a WAL-mode database has WAL header flags but no WAL
 * sidecar. A consistent serialize() snapshot contains the current pages; mark
 * its detached copy as rollback-journal format before opening it in memory. */
export function normalizeSQLiteSnapshot(bytes: Uint8Array): Uint8Array {
  requireSQLiteHeader(bytes);
  const copy = new Uint8Array(bytes);
  if (copy[18] === 2 && copy[19] === 2) {copy[18] = 1; copy[19] = 1;}
  else if (copy[18] !== 1 || copy[19] !== 1) throw new Error('Unsupported SQLite journal format.');
  return copy;
}
