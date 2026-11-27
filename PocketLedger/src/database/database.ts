import * as SQLite from 'expo-sqlite';
import { Account, AccountKind, LedgerTransaction, TransactionInput } from '../types';

let connection: Promise<SQLite.SQLiteDatabase> | undefined;
export function database() {
  if (!connection) connection = initialize().catch(error => { connection = undefined; throw error; });
  return connection;
}
async function initialize() {
  const db = await SQLite.openDatabaseAsync('pocketledger.db');
  await db.execAsync('PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;');
  const version = await db.getFirstAsync<{user_version: number}>('PRAGMA user_version');
  if ((version?.user_version ?? 0) > 1) throw new Error('This database was created by a newer version of PocketLedger.');
  if (!version?.user_version) {
    await db.execAsync(`BEGIN IMMEDIATE;
      CREATE TABLE accounts (id INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('cash','online')), opening_paise INTEGER NOT NULL CHECK(opening_paise >= 0));
      CREATE TABLE transactions (id INTEGER PRIMARY KEY NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('income','expense','transfer')), amount_paise INTEGER NOT NULL CHECK(amount_paise > 0), account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT, destination_id INTEGER REFERENCES accounts(id) ON DELETE RESTRICT, occurred_at TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT '', deleted_at TEXT, CHECK ((kind = 'transfer' AND destination_id IS NOT NULL AND destination_id != account_id) OR (kind != 'transfer' AND destination_id IS NULL)));
      CREATE TABLE audit_logs (id INTEGER PRIMARY KEY NOT NULL, entity TEXT NOT NULL, entity_id INTEGER NOT NULL, action TEXT NOT NULL, before_json TEXT, after_json TEXT, created_at TEXT NOT NULL);
      CREATE INDEX transactions_date_idx ON transactions(occurred_at); CREATE INDEX transactions_account_idx ON transactions(account_id); CREATE INDEX transactions_destination_idx ON transactions(destination_id);
      PRAGMA user_version = 1; COMMIT;`);
  }
  return db;
}
async function listAccountsInternal(): Promise<Account[]> {
  const db = await database();
  return db.getAllAsync<Account>(`SELECT a.*, a.opening_paise + COALESCE((SELECT SUM(CASE WHEN t.account_id=a.id THEN CASE WHEN t.kind='income' THEN t.amount_paise ELSE -t.amount_paise END ELSE 0 END + CASE WHEN t.kind='transfer' AND t.destination_id=a.id THEN t.amount_paise ELSE 0 END) FROM transactions t WHERE t.deleted_at IS NULL AND (t.account_id=a.id OR t.destination_id=a.id)),0) AS balance_paise FROM accounts a ORDER BY a.id`);
}
async function saveAccountInternal(name: string, kind: AccountKind, opening: number, id?: number) {
  if (!name.trim() || !Number.isSafeInteger(opening) || opening < 0) throw new Error('Enter a valid name and opening balance.');
  const db = await database();
  await db.withTransactionAsync(async () => {
    const before = id ? await db.getFirstAsync('SELECT * FROM accounts WHERE id=?', id) : null;
    if (id && !before) throw new Error('Account not found.');
    const result = id ? await db.runAsync('UPDATE accounts SET name=?,kind=?,opening_paise=? WHERE id=?',name.trim(),kind,opening,id) : await db.runAsync('INSERT INTO accounts(name,kind,opening_paise) VALUES(?,?,?)',name.trim(),kind,opening);
    const target = id ?? result.lastInsertRowId;
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,before_json,after_json,created_at) VALUES(?,?,?,?,?,?)','account',target,id?'edit':'create',before ? JSON.stringify(before) : null,JSON.stringify({name:name.trim(),kind,opening_paise:opening}),new Date().toISOString());
  });
}
async function listTransactionsInternal(): Promise<LedgerTransaction[]> {
  const db = await database();
  return db.getAllAsync<LedgerTransaction>(`SELECT t.*, a.name account_name, d.name destination_name FROM transactions t JOIN accounts a ON a.id=t.account_id LEFT JOIN accounts d ON d.id=t.destination_id WHERE t.deleted_at IS NULL ORDER BY t.occurred_at DESC, t.id DESC`);
}
async function saveTransactionInternal(input: TransactionInput, id?: number) {
  if (!Number.isSafeInteger(input.amount_paise) || input.amount_paise <= 0 || !input.account_id || !Number.isFinite(Date.parse(input.occurred_at))) throw new Error('Enter a valid amount, account and date.');
  if (input.kind === 'transfer' ? !input.destination_id || input.destination_id === input.account_id : input.destination_id !== null) throw new Error('Choose two different accounts for a transfer.');
  const db = await database();
  await db.withTransactionAsync(async () => {
    const before = id ? await db.getFirstAsync('SELECT * FROM transactions WHERE id=? AND deleted_at IS NULL',id) : null;
    if (id && !before) throw new Error('Transaction not found.');
    const values = [input.kind,input.amount_paise,input.account_id,input.destination_id,input.occurred_at,input.description.trim(),input.category.trim()] as const;
    const result = id ? await db.runAsync('UPDATE transactions SET kind=?,amount_paise=?,account_id=?,destination_id=?,occurred_at=?,description=?,category=? WHERE id=?',...values,id) : await db.runAsync('INSERT INTO transactions(kind,amount_paise,account_id,destination_id,occurred_at,description,category) VALUES(?,?,?,?,?,?,?)',...values);
    const target = id ?? result.lastInsertRowId;
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,before_json,after_json,created_at) VALUES(?,?,?,?,?,?)','transaction',target,id?'edit':'create',before ? JSON.stringify(before) : null,JSON.stringify(input),new Date().toISOString());
  });
}
async function deleteTransactionInternal(id: number) {
  const db = await database();
  await db.withTransactionAsync(async () => {
    const before = await db.getFirstAsync('SELECT * FROM transactions WHERE id=? AND deleted_at IS NULL',id);
    if (!before) throw new Error('Transaction not found.');
    const now = new Date().toISOString();
    await db.runAsync('UPDATE transactions SET deleted_at=? WHERE id=?',now,id);
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,before_json,created_at) VALUES(?,?,?,?,?)','transaction',id,'delete',JSON.stringify(before),now);
  });
}
async function deleteAccountInternal(id: number) {
  const db = await database();
  await db.withTransactionAsync(async () => {
    const before = await db.getFirstAsync('SELECT * FROM accounts WHERE id=?', id);
    if (!before) throw new Error('Account not found.');
    const references = await db.getFirstAsync<{count: number}>('SELECT COUNT(*) AS count FROM transactions WHERE account_id=? OR destination_id=?',id,id);
    if (references?.count) throw new Error('This account has transaction history and cannot be deleted.');
    await db.runAsync('DELETE FROM accounts WHERE id=?',id);
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,before_json,created_at) VALUES(?,?,?,?,?)','account',id,'delete',JSON.stringify(before),new Date().toISOString());
  });
}

// Serialize all access through this connection: withTransactionAsync alone may include
// unrelated async statements that run while a transaction is open.
let pending: Promise<void> = Promise.resolve();
function serial<T>(operation: () => Promise<T>): Promise<T> {
  const result = pending.then(operation);
  pending = result.then(() => undefined, () => undefined);
  return result;
}
export const listAccounts = () => serial(listAccountsInternal);
export const listTransactions = () => serial(listTransactionsInternal);
export const saveAccount = (name: string, kind: AccountKind, opening: number, id?: number) => serial(() => saveAccountInternal(name,kind,opening,id));
export const saveTransaction = (input: TransactionInput, id?: number) => serial(() => saveTransactionInternal(input,id));
export const deleteTransaction = (id: number) => serial(() => deleteTransactionInternal(id));
export const deleteAccount = (id: number) => serial(() => deleteAccountInternal(id));
