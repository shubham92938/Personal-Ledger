import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
const source = readFileSync(new URL('../src/database/database.ts', import.meta.url), 'utf8');
const schemas = [...source.matchAll(/await db\.execAsync\(`(BEGIN IMMEDIATE;[\s\S]*?COMMIT;)`\)/g)].map(match => match[1]);
const balances = source.match(/getAllAsync<Account>\(`(SELECT a\.\*,[\s\S]*?)`\)/)?.[1];
if (schemas.length !== 3 || !balances) throw new Error('Could not find production migration or balance query');
function setup() { const db = new DatabaseSync(':memory:'); db.exec('PRAGMA foreign_keys = ON;'); db.exec(schemas[0]); db.exec(schemas[1]); db.exec(schemas[2]); return db; }
test('migration, foreign keys, balance calculation, edit and soft deletion', () => {
 const db=setup();
 db.exec("INSERT INTO accounts(name,kind,opening_paise) VALUES('Cash','cash',500000),('Bank','online',0)");
 db.exec("INSERT INTO transactions(kind,amount_paise,account_id,occurred_at) VALUES('income',200000,1,'2026-01-01'),('expense',50000,1,'2026-01-02')");
 db.exec("INSERT INTO transactions(kind,amount_paise,account_id,destination_id,occurred_at) VALUES('transfer',100000,1,2,'2026-01-03')");
 let a=db.prepare(balances!).all(); assert.equal(a[0].balance_paise,550000);assert.equal(a[1].balance_paise,100000);
 assert.throws(()=>db.exec("DELETE FROM accounts WHERE id=1"));
 assert.throws(()=>db.exec("INSERT INTO transactions(kind,amount_paise,account_id,destination_id,occurred_at) VALUES('transfer',100,1,1,'2026-01-01')"));
 db.exec("UPDATE transactions SET amount_paise=25000 WHERE kind='expense'; UPDATE transactions SET deleted_at='now' WHERE kind='transfer'");
 a=db.prepare(balances!).all(); assert.equal(a[0].balance_paise,675000);assert.equal(a[1].balance_paise,0);
 db.close();
});
test('failed transaction rolls back financial writes',()=>{const db=setup();db.exec("INSERT INTO accounts(name,kind,opening_paise) VALUES('Cash','cash',0); BEGIN;");assert.throws(()=>db.exec("INSERT INTO transactions(kind,amount_paise,account_id,occurred_at) VALUES('income',-1,1,'2026-01-01')"));db.exec('ROLLBACK;');assert.equal(db.prepare('SELECT count(*) as n FROM transactions').get()?.n,0);db.close()});

test('version 1 upgrade preserves existing transactions and adds loan tables', () => {
 const db = new DatabaseSync(':memory:'); db.exec('PRAGMA foreign_keys=ON;'); db.exec(schemas[0]);
 db.exec("INSERT INTO accounts(name,kind,opening_paise) VALUES('Cash','cash',500000); INSERT INTO transactions(kind,amount_paise,account_id,occurred_at) VALUES('income',200000,1,'2026-01-01');");
 db.exec(schemas[1]); db.exec(schemas[2]);
 assert.equal(db.prepare('PRAGMA user_version').get()?.user_version,3);
 assert.equal(db.prepare(balances!).get()?.balance_paise,700000);
 assert.equal(db.prepare('SELECT COUNT(*) AS n FROM transactions').get()?.n,1);
 db.close();
});
test('loan principal and repayments change balances without ordinary transactions', () => {
 const db=setup();
 db.exec("INSERT INTO accounts(name,kind,opening_paise) VALUES('Cash','cash',500000),('Bank','online',0); INSERT INTO people(name) VALUES('Ravi'),('Neha');");
 db.exec("INSERT INTO loans(person_id,direction,principal_paise,account_id,rate_period,started_on) VALUES(1,'borrowed',100000,1,'monthly','2026-01-01'),(2,'lent',200000,1,'yearly','2026-01-01');");
 db.exec("INSERT INTO repayments(loan_id,account_id,amount_paise,paid_on) VALUES(1,1,20000,'2026-01-02'),(2,2,50000,'2026-01-02');");
 const a=db.prepare(balances!).all(); assert.equal(a[0].balance_paise,380000); assert.equal(a[1].balance_paise,50000);
 assert.equal(db.prepare('SELECT COUNT(*) AS n FROM transactions').get()?.n,0);
 assert.throws(()=>db.exec('DELETE FROM accounts WHERE id=2'));
 assert.throws(()=>db.exec("INSERT INTO repayments(loan_id,account_id,amount_paise,paid_on) VALUES(1,999,100,'2026-01-03')"));
 db.close();
});

test('soft deleting a repayment or loan reverses account movements without erasing history',()=>{
 const db=setup();
 db.exec("INSERT INTO accounts(name,kind,opening_paise) VALUES('Cash','cash',500000); INSERT INTO people(name) VALUES('A'); INSERT INTO loans(person_id,direction,principal_paise,account_id,rate_period,started_on) VALUES(1,'borrowed',100000,1,'monthly','2026-01-01'); INSERT INTO repayments(loan_id,account_id,amount_paise,paid_on) VALUES(1,1,20000,'2026-01-02');");
 assert.equal(db.prepare(balances!).get()?.balance_paise,580000);
 db.exec("UPDATE repayments SET deleted_at='now' WHERE id=1");
 assert.equal(db.prepare(balances!).get()?.balance_paise,600000);
 db.exec("UPDATE loans SET deleted_at='now' WHERE id=1");
 assert.equal(db.prepare(balances!).get()?.balance_paise,500000);
 assert.equal(db.prepare('SELECT COUNT(*) AS n FROM repayments').get()?.n,1);
 db.close();
});
test('version 2 loan data survives the version 3 soft-delete migration',()=>{
 const db=new DatabaseSync(':memory:'); db.exec('PRAGMA foreign_keys=ON;'); db.exec(schemas[0]); db.exec(schemas[1]);
 db.exec("INSERT INTO accounts(name,kind,opening_paise) VALUES('Cash','cash',500000); INSERT INTO people(name) VALUES('A'); INSERT INTO loans(person_id,direction,principal_paise,account_id,rate_period,started_on) VALUES(1,'borrowed',100000,1,'monthly','2026-01-01'); INSERT INTO repayments(loan_id,account_id,amount_paise,paid_on) VALUES(1,1,20000,'2026-01-02');");
 db.exec(schemas[2]); assert.equal(db.prepare('PRAGMA user_version').get()?.user_version,3);
 assert.equal(db.prepare(balances!).get()?.balance_paise,580000);
 assert.equal(db.prepare('SELECT deleted_at FROM loans WHERE id=1').get()?.deleted_at,null);
 assert.equal(db.prepare('SELECT deleted_at FROM repayments WHERE id=1').get()?.deleted_at,null);
 db.close();
});
