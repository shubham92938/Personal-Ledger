import * as SQLite from 'expo-sqlite';
import { Account, AccountKind, LedgerTransaction, TransactionInput, Loan, LoanInput, Repayment, LoanActivity } from '../types';
import { calculateLoan, dateDay, localToday } from '../services/interest';
import { assertEditableTransaction } from '../services/accounts';

let connection: Promise<SQLite.SQLiteDatabase> | undefined;
export function database() {
  if (!connection) connection = initialize().catch(error => { connection = undefined; throw error; });
  return connection;
}
async function initialize() {
  const db = await SQLite.openDatabaseAsync('pocketledger.db');
  try {
  await db.execAsync('PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;');
  const version = await db.getFirstAsync<{user_version: number}>('PRAGMA user_version');
  if ((version?.user_version ?? 0) > 3) throw new Error('This database was created by a newer version of PocketLedger.');
  if (!version?.user_version) {
    await db.execAsync(`BEGIN IMMEDIATE;
      CREATE TABLE accounts (id INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('cash','online')), opening_paise INTEGER NOT NULL CHECK(opening_paise >= 0));
      CREATE TABLE transactions (id INTEGER PRIMARY KEY NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('income','expense','transfer')), amount_paise INTEGER NOT NULL CHECK(amount_paise > 0), account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT, destination_id INTEGER REFERENCES accounts(id) ON DELETE RESTRICT, occurred_at TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT '', deleted_at TEXT, CHECK ((kind = 'transfer' AND destination_id IS NOT NULL AND destination_id != account_id) OR (kind != 'transfer' AND destination_id IS NULL)));
      CREATE TABLE audit_logs (id INTEGER PRIMARY KEY NOT NULL, entity TEXT NOT NULL, entity_id INTEGER NOT NULL, action TEXT NOT NULL, before_json TEXT, after_json TEXT, created_at TEXT NOT NULL);
      CREATE INDEX transactions_date_idx ON transactions(occurred_at); CREATE INDEX transactions_account_idx ON transactions(account_id); CREATE INDEX transactions_destination_idx ON transactions(destination_id);
      PRAGMA user_version = 1; COMMIT;`);
  }
  if ((version?.user_version ?? 0) < 2) {
    await db.execAsync(`BEGIN IMMEDIATE;
      CREATE TABLE people (id INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '');
      CREATE TABLE loans (id INTEGER PRIMARY KEY NOT NULL, person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE RESTRICT, direction TEXT NOT NULL CHECK(direction IN ('borrowed','lent')), principal_paise INTEGER NOT NULL CHECK(principal_paise > 0), account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT, rate_bps INTEGER NOT NULL DEFAULT 0 CHECK(rate_bps BETWEEN 0 AND 10000), rate_period TEXT NOT NULL CHECK(rate_period IN ('monthly','yearly')), started_on TEXT NOT NULL, due_on TEXT, notes TEXT NOT NULL DEFAULT '');
      CREATE TABLE repayments (id INTEGER PRIMARY KEY NOT NULL, loan_id INTEGER NOT NULL REFERENCES loans(id) ON DELETE RESTRICT, account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT, amount_paise INTEGER NOT NULL CHECK(amount_paise > 0), paid_on TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '');
      CREATE INDEX loans_person_idx ON loans(person_id); CREATE INDEX loans_account_idx ON loans(account_id); CREATE INDEX repayments_loan_idx ON repayments(loan_id, paid_on, id); CREATE INDEX repayments_account_idx ON repayments(account_id);
      PRAGMA user_version = 2; COMMIT;`);
  }
  if ((version?.user_version ?? 0) < 3) {
    await db.execAsync(`BEGIN IMMEDIATE;
      ALTER TABLE loans ADD COLUMN deleted_at TEXT;
      ALTER TABLE repayments ADD COLUMN deleted_at TEXT;
      PRAGMA user_version = 3; COMMIT;`);
  }
  return db;
  } catch (error) {
    // A failed migration must not leave an open transaction or connection behind.
    try { if (await db.isInTransactionAsync()) await db.execAsync('ROLLBACK'); } catch { /* Preserve the original error. */ }
    try { await db.closeAsync(); } catch { /* Preserve the original error. */ }
    throw error;
  }
}
async function listAccountsInternal(): Promise<Account[]> {
  const db = await database();
  const accounts = await db.getAllAsync<Account>(`SELECT a.*, a.opening_paise + COALESCE((SELECT SUM(CASE WHEN t.account_id=a.id THEN CASE WHEN t.kind='income' THEN t.amount_paise ELSE -t.amount_paise END ELSE 0 END + CASE WHEN t.kind='transfer' AND t.destination_id=a.id THEN t.amount_paise ELSE 0 END) FROM transactions t WHERE t.deleted_at IS NULL AND (t.account_id=a.id OR t.destination_id=a.id)),0) + COALESCE((SELECT SUM(CASE WHEN l.direction='borrowed' THEN l.principal_paise ELSE -l.principal_paise END) FROM loans l WHERE l.account_id=a.id AND l.deleted_at IS NULL),0) + COALESCE((SELECT SUM(CASE WHEN l.direction='borrowed' THEN -r.amount_paise ELSE r.amount_paise END) FROM repayments r JOIN loans l ON l.id=r.loan_id WHERE r.account_id=a.id AND r.deleted_at IS NULL AND l.deleted_at IS NULL),0) AS balance_paise FROM accounts a ORDER BY a.id`);
  if (accounts.some(account => !Number.isSafeInteger(account.balance_paise))) throw new Error('An account balance exceeds the supported range.');
  return accounts;
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
  return db.getAllAsync<LedgerTransaction>(`SELECT t.*, a.name account_name, a.kind account_kind, d.name destination_name, d.kind destination_kind FROM transactions t JOIN accounts a ON a.id=t.account_id LEFT JOIN accounts d ON d.id=t.destination_id WHERE t.deleted_at IS NULL ORDER BY t.occurred_at DESC, t.id DESC`);
}
/** Project existing loan and repayment records into history without creating duplicate balance entries. */
async function listLoanActivityInternal(): Promise<LoanActivity[]> {
  const db=await database();
  return db.getAllAsync<LoanActivity>(`SELECT 'loan' AS event_type,l.id AS id,l.id AS loan_id,l.direction,p.name AS person_name,l.principal_paise AS amount_paise,l.started_on AS occurred_at,a.kind AS account_kind,l.notes AS notes
    FROM loans l JOIN people p ON p.id=l.person_id JOIN accounts a ON a.id=l.account_id WHERE l.deleted_at IS NULL
    UNION ALL
    SELECT 'repayment' AS event_type,r.id AS id,l.id AS loan_id,l.direction,p.name AS person_name,r.amount_paise AS amount_paise,r.paid_on AS occurred_at,a.kind AS account_kind,r.notes AS notes
    FROM repayments r JOIN loans l ON l.id=r.loan_id JOIN people p ON p.id=l.person_id JOIN accounts a ON a.id=r.account_id WHERE r.deleted_at IS NULL AND l.deleted_at IS NULL`);
}
/** Keep legacy account rows intact, but choose a backing row automatically per balance type. */
async function resolveBalanceAccount(db: SQLite.SQLiteDatabase, kind?: AccountKind, preferredId = 0): Promise<number> {
  if (kind !== 'cash' && kind !== 'online') throw new Error('Choose cash or online.');
  if (preferredId) {
    const preferred = await db.getFirstAsync<{id: number}>('SELECT id FROM accounts WHERE id=? AND kind=?',preferredId,kind);
    if (preferred) return preferred.id;
  }
  const existing = await db.getFirstAsync<{id: number}>('SELECT id FROM accounts WHERE kind=? ORDER BY id LIMIT 1',kind);
  if (existing) return existing.id;
  const name = kind === 'cash' ? 'Cash' : 'Online';
  const created = await db.runAsync('INSERT INTO accounts(name,kind,opening_paise) VALUES(?,?,0)',name,kind);
  await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,after_json,created_at) VALUES(?,?,?,?,?)','account',created.lastInsertRowId,'create',JSON.stringify({name,kind,opening_paise:0}),new Date().toISOString());
  return created.lastInsertRowId;
}
async function saveTransactionInternal(input: TransactionInput, id?: number, accountKind?: AccountKind) {
  if (!Number.isSafeInteger(input.amount_paise) || input.amount_paise <= 0 || (!input.account_id && !accountKind) || !Number.isFinite(Date.parse(input.occurred_at))) throw new Error('Enter a valid amount, account and date.');
  assertEditableTransaction(input.kind, input.destination_id);
  const db = await database();
  await db.withTransactionAsync(async () => {
    const before = id ? await db.getFirstAsync<{kind: string}>('SELECT * FROM transactions WHERE id=? AND deleted_at IS NULL',id) : null;
    if (id && !before) throw new Error('Transaction not found.');
    assertEditableTransaction(input.kind, input.destination_id, before?.kind);
    const accountId = await resolveBalanceAccount(db, accountKind, input.account_id);
    const values = [input.kind,input.amount_paise,accountId,input.destination_id,input.occurred_at,input.description.trim(),input.category.trim()] as const;
    const result = id ? await db.runAsync('UPDATE transactions SET kind=?,amount_paise=?,account_id=?,destination_id=?,occurred_at=?,description=?,category=? WHERE id=?',...values,id) : await db.runAsync('INSERT INTO transactions(kind,amount_paise,account_id,destination_id,occurred_at,description,category) VALUES(?,?,?,?,?,?,?)',...values);
    const target = id ?? result.lastInsertRowId;
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,before_json,after_json,created_at) VALUES(?,?,?,?,?,?)','transaction',target,id?'edit':'create',before ? JSON.stringify(before) : null,JSON.stringify({...input,account_id:accountId}),new Date().toISOString());
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
    const loanReferences = await db.getFirstAsync<{count: number}>('SELECT (SELECT COUNT(*) FROM loans WHERE account_id=?) + (SELECT COUNT(*) FROM repayments WHERE account_id=?) AS count', id, id);
    if (references?.count || loanReferences?.count) throw new Error('This account has transaction or loan history and cannot be deleted.');
    await db.runAsync('DELETE FROM accounts WHERE id=?',id);
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,before_json,created_at) VALUES(?,?,?,?,?)','account',id,'delete',JSON.stringify(before),new Date().toISOString());
  });
}

async function listLoansInternal(): Promise<Loan[]> {
  const db = await database();
  return db.getAllAsync<Loan>(`SELECT l.*, p.name AS person_name, p.phone, a.name AS account_name, a.kind AS account_kind FROM loans l JOIN people p ON p.id=l.person_id JOIN accounts a ON a.id=l.account_id WHERE l.deleted_at IS NULL ORDER BY l.started_on DESC,l.id DESC`);
}
async function listRepaymentsInternal(loanId: number): Promise<Repayment[]> {
  const db = await database();
  return db.getAllAsync<Repayment>(`SELECT r.*, a.name AS account_name, a.kind AS account_kind FROM repayments r JOIN accounts a ON a.id=r.account_id WHERE r.loan_id=? AND r.deleted_at IS NULL ORDER BY r.paid_on,r.id`, loanId);
}
async function createLoanInternal(input: LoanInput, balanceKind?: AccountKind): Promise<number> {
  const today = localToday();
  if (!input.person_name.trim() || (!input.account_id && !balanceKind) || !['borrowed','lent'].includes(input.direction)) throw new Error('Enter a name and select an account.');
  dateDay(input.started_on);
  if (input.started_on > today) throw new Error('Loan date cannot be in the future.');
  if (input.due_on) {
    dateDay(input.due_on);
    if (input.due_on < input.started_on) throw new Error('Due date cannot be before the loan date.');
  }
  calculateLoan(input, [], input.started_on);
  const db = await database(); let loanId = 0;
  await db.withTransactionAsync(async () => {
    const accountId = await resolveBalanceAccount(db, balanceKind, input.account_id);
    const person = await db.runAsync('INSERT INTO people(name,phone) VALUES(?,?)', input.person_name.trim(), input.phone.trim());
    const result = await db.runAsync('INSERT INTO loans(person_id,direction,principal_paise,account_id,rate_bps,rate_period,started_on,due_on,notes) VALUES(?,?,?,?,?,?,?,?,?)',person.lastInsertRowId,input.direction,input.principal_paise,accountId,input.rate_bps,input.rate_period,input.started_on,input.due_on,input.notes.trim());
    loanId = result.lastInsertRowId;
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,after_json,created_at) VALUES(?,?,?,?,?)','loan',loanId,'create',JSON.stringify({...input,account_id:accountId}),new Date().toISOString());
  });
  return loanId;
}
async function addRepaymentInternal(loanId: number, accountId: number, amount: number, paidOn: string, notes: string, balanceKind?: AccountKind): Promise<void> {
  const db = await database();
  await db.withTransactionAsync(async () => {
    const loan = await db.getFirstAsync<Loan>('SELECT * FROM loans WHERE id=? AND deleted_at IS NULL', loanId);
    if (!loan || (!accountId && !balanceKind) || !Number.isSafeInteger(amount) || amount <= 0) throw new Error('Select an account and enter a positive repayment.');
    const payments = await db.getAllAsync<Repayment>('SELECT * FROM repayments WHERE loan_id=? AND deleted_at IS NULL ORDER BY paid_on,id', loanId);
    dateDay(paidOn);
    if (paidOn > localToday() || paidOn < loan.started_on || (payments.length && paidOn < payments[payments.length-1].paid_on)) throw new Error('Repayment must be today or earlier and not before the loan or last repayment.');
    // Re-evaluate the whole history including the proposed payment before writing.
    calculateLoan(loan, [...payments, {amount_paise: amount, paid_on: paidOn}], paidOn);
    const resolvedAccount = await resolveBalanceAccount(db, balanceKind, accountId);
    const result = await db.runAsync('INSERT INTO repayments(loan_id,account_id,amount_paise,paid_on,notes) VALUES(?,?,?,?,?)',loanId,resolvedAccount,amount,paidOn,notes.trim());
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,after_json,created_at) VALUES(?,?,?,?,?)','repayment',result.lastInsertRowId,'create',JSON.stringify({loanId,accountId:resolvedAccount,amount,paidOn,notes:notes.trim()}),new Date().toISOString());
  });
}

async function updateLoanDetailsInternal(id: number, name: string, phone: string, dueOn: string | null, notes: string): Promise<void> {
  if (!name.trim()) throw new Error('Enter a person name.');
  const db = await database();
  await db.withTransactionAsync(async () => {
    const before = await db.getFirstAsync<Loan>('SELECT l.*, p.name AS person_name, p.phone FROM loans l JOIN people p ON p.id=l.person_id WHERE l.id=? AND l.deleted_at IS NULL',id);
    if (!before) throw new Error('Loan not found.');
    if (dueOn) { dateDay(dueOn); if (dueOn < before.started_on) throw new Error('Due date cannot be before the loan date.'); }
    await db.runAsync('UPDATE people SET name=?,phone=? WHERE id=?',name.trim(),phone.trim(),before.person_id);
    await db.runAsync('UPDATE loans SET due_on=?,notes=? WHERE id=?',dueOn,notes.trim(),id);
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,before_json,after_json,created_at) VALUES(?,?,?,?,?,?)','loan',id,'edit',JSON.stringify(before),JSON.stringify({name:name.trim(),phone:phone.trim(),due_on:dueOn,notes:notes.trim()}),new Date().toISOString());
  });
}
async function deleteLoanInternal(id: number): Promise<void> {
  const db = await database();
  await db.withTransactionAsync(async () => {
    const before = await db.getFirstAsync('SELECT * FROM loans WHERE id=? AND deleted_at IS NULL',id);
    if (!before) throw new Error('Loan not found.');
    const repayments = await db.getAllAsync('SELECT * FROM repayments WHERE loan_id=? AND deleted_at IS NULL ORDER BY paid_on,id',id);
    const now = new Date().toISOString();
    await db.runAsync('UPDATE loans SET deleted_at=? WHERE id=?',now,id);
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,before_json,created_at) VALUES(?,?,?,?,?)','loan',id,'delete',JSON.stringify({loan:before,repayments}),now);
  });
}
async function deleteRepaymentInternal(id: number): Promise<void> {
  const db = await database();
  await db.withTransactionAsync(async () => {
    const before = await db.getFirstAsync<Repayment>('SELECT * FROM repayments WHERE id=? AND deleted_at IS NULL',id);
    if (!before) throw new Error('Repayment not found.');
    const loan = await db.getFirstAsync<Loan>('SELECT * FROM loans WHERE id=? AND deleted_at IS NULL',before.loan_id);
    if (!loan) throw new Error('Loan not found.');
    const rest = await db.getAllAsync<Repayment>('SELECT * FROM repayments WHERE loan_id=? AND id<>? AND deleted_at IS NULL ORDER BY paid_on,id',before.loan_id,id);
    calculateLoan(loan, rest, localToday());
    const now = new Date().toISOString();
    await db.runAsync('UPDATE repayments SET deleted_at=? WHERE id=?',now,id);
    await db.runAsync('INSERT INTO audit_logs(entity,entity_id,action,before_json,created_at) VALUES(?,?,?,?,?)','repayment',id,'delete',JSON.stringify(before),now);
  });
}
export type AuditLog = { id: number; entity: string; entity_id: number; action: string; before_json: string | null; after_json: string | null; created_at: string };
async function listAuditLogsInternal(): Promise<AuditLog[]> {
  const db = await database();
  return db.getAllAsync<AuditLog>('SELECT * FROM audit_logs ORDER BY id DESC LIMIT 500');
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
/** Read both parts together on the ledger queue to avoid interleaving financial writes. */
export const listHistory = () => serial(async () => ({transactions:await listTransactionsInternal(),loanActivity:await listLoanActivityInternal()}));
export const saveAccount = (name: string, kind: AccountKind, opening: number, id?: number) => serial(() => saveAccountInternal(name,kind,opening,id));
export const saveTransaction = (input: TransactionInput, id?: number, accountKind?: AccountKind) => serial(() => saveTransactionInternal(input,id,accountKind));
export const deleteTransaction = (id: number) => serial(() => deleteTransactionInternal(id));
export const deleteAccount = (id: number) => serial(() => deleteAccountInternal(id));

export const listLoans = () => serial(listLoansInternal);
export const listRepayments = (id: number) => serial(() => listRepaymentsInternal(id));
export const createLoan = (input: LoanInput, balanceKind: AccountKind) => serial(() => createLoanInternal(input,balanceKind));
export const addRepayment = (id: number, amount: number, paidOn: string, notes: string, balanceKind: AccountKind) => serial(() => addRepaymentInternal(id,0,amount,paidOn,notes,balanceKind));

export const updateLoanDetails = (id: number, name: string, phone: string, dueOn: string | null, notes: string) => serial(() => updateLoanDetailsInternal(id,name,phone,dueOn,notes));
export const deleteLoan = (id: number) => serial(() => deleteLoanInternal(id));
export const deleteRepayment = (id: number) => serial(() => deleteRepaymentInternal(id));
export const listAuditLogs = () => serial(listAuditLogsInternal);

/** All backup work must share the ledger queue; never race with a financial write. */
export const withLedgerDatabase = <T>(operation: (db: SQLite.SQLiteDatabase) => Promise<T>) => serial(async () => operation(await database()));
