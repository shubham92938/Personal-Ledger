import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
const source = readFileSync(new URL('../src/database/database.ts', import.meta.url), 'utf8');
const schema = source.match(/await db\.execAsync\(`(BEGIN IMMEDIATE;[\s\S]*?COMMIT;)`\)/)?.[1];
const balances = source.match(/getAllAsync<Account>\(`(SELECT a\.\*,[\s\S]*?)`\)/)?.[1];
if (!schema || !balances) throw new Error('Could not find production migration or balance query');
function setup() { const db = new DatabaseSync(':memory:'); db.exec('PRAGMA foreign_keys = ON;'); db.exec(schema!); return db; }
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
