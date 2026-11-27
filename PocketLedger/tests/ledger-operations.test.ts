import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
import * as interest from '../src/services/interest.ts';
import * as accounts from '../src/services/accounts.ts';
import { translate } from '../src/localization/translations.ts';

// Execute the actual repository database functions against a Node SQLite adapter.
// This covers business/SQL behavior, not Expo's native SQLite bridge.
function makeLedger(){
 const sql = new DatabaseSync(':memory:');
 const adapter = {
  async execAsync(query:string){sql.exec(query);},
  async getFirstAsync(query:string,...args:any[]){return sql.prepare(query).get(...args) ?? null;},
  async getAllAsync(query:string,...args:any[]){return sql.prepare(query).all(...args);},
  async runAsync(query:string,...args:any[]){const result=sql.prepare(query).run(...args);return {lastInsertRowId:Number(result.lastInsertRowid),changes:Number(result.changes)};},
  async withTransactionAsync(fn:()=>Promise<void>){sql.exec('BEGIN');try{await fn();sql.exec('COMMIT');}catch(e){sql.exec('ROLLBACK');throw e;}},
  async isInTransactionAsync(){return sql.isTransaction;},async closeAsync(){sql.close();},
 };
 const text=readFileSync(new URL('../src/database/database.ts',import.meta.url),'utf8');
 const compiled=ts.transpileModule(text,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
 const result:{exports:any}={exports:{}};
 const deps:Record<string,unknown>={'expo-sqlite':{openDatabaseAsync:async()=>adapter},'../services/interest':interest,'../services/accounts':accounts};
 new Function('require','exports','module',compiled)((name:string)=>{if(!(name in deps))throw new Error(`Unexpected module: ${name}`);return deps[name];},result.exports,result);
 return {ledger:result.exports,sql};
}
test('automatic balance backing preserves legacy rows through edits, loans and repayments',async()=>{
 const {ledger,sql}=makeLedger();
 try {
  await ledger.database();
  sql.exec("INSERT INTO accounts(name,kind,opening_paise) VALUES('Old cash','cash',10000),('Old bank','online',20000),('Other bank','online',30000);");
  sql.exec("INSERT INTO transactions(kind,amount_paise,account_id,occurred_at) VALUES('income',1000,3,'2026-01-01T10:00:00');");
  const transaction={kind:'income',amount_paise:1500,account_id:3,destination_id:null,occurred_at:'2026-01-01T10:00:00',description:'',category:''};
  await ledger.saveTransaction(transaction,1,'online');
  assert.equal(sql.prepare('SELECT account_id FROM transactions WHERE id=1').get()?.account_id,3);
  await ledger.saveTransaction({...transaction,account_id:0,amount_paise:500},undefined,'online');
  assert.equal(sql.prepare('SELECT account_id FROM transactions WHERE id=2').get()?.account_id,2);
  await ledger.saveTransaction({...transaction,account_id:0,amount_paise:1500},1,'cash');
  assert.equal(sql.prepare('SELECT account_id FROM transactions WHERE id=1').get()?.account_id,1);
  const today=interest.localToday();
  const loan=await ledger.createLoan({person_name:'A',phone:'',direction:'borrowed',principal_paise:1000,account_id:0,rate_bps:0,rate_period:'monthly',started_on:today,due_on:null,notes:''},'cash');
  await ledger.addRepayment(loan,400,today,'','online');
  assert.deepEqual((await ledger.listAccounts()).map((a:{balance_paise:number})=>a.balance_paise),[12500,20100,30000]);
  assert.equal((await ledger.listLoans())[0].account_kind,'cash');
  assert.equal((await ledger.listRepayments(loan))[0].account_kind,'online');
  await assert.rejects(()=>ledger.addRepayment(loan,1000,today,'','online'),/outstanding/);
  assert.equal(sql.prepare('SELECT count(*) AS n FROM repayments').get()?.n,1);
  await ledger.deleteLoan(loan);
  assert.deepEqual((await ledger.listAccounts()).map((a:{balance_paise:number})=>a.balance_paise),[11500,20500,30000]);
  assert.equal(sql.prepare('SELECT count(*) AS n FROM accounts').get()?.n,3);
  assert.equal(sql.prepare('SELECT count(*) AS n FROM transactions').get()?.n,2);
 } finally {sql.close();}
});
test('new balance type is created atomically and rejected saves leave no account',async()=>{
 const {ledger,sql}=makeLedger();
 try {
  await ledger.database();
  const input={kind:'income',amount_paise:1000,account_id:0,destination_id:null,occurred_at:'2026-01-01T10:00:00',description:'',category:''};
  await assert.rejects(()=>ledger.saveTransaction({...input,amount_paise:-1},undefined,'cash'));
  assert.equal(sql.prepare('SELECT count(*) AS n FROM accounts').get()?.n,0);
  sql.exec("CREATE TRIGGER reject_audit BEFORE INSERT ON audit_logs BEGIN SELECT RAISE(ABORT, 'audit failure'); END;");
  await assert.rejects(()=>ledger.saveTransaction(input,undefined,'cash'),/audit failure/);
  assert.equal(sql.prepare('SELECT count(*) AS n FROM accounts').get()?.n,0);
  assert.equal(sql.prepare('SELECT count(*) AS n FROM transactions').get()?.n,0);
  sql.exec('DROP TRIGGER reject_audit');
  await ledger.saveTransaction(input,undefined,'cash');
  assert.equal(sql.prepare('SELECT count(*) AS n FROM accounts').get()?.n,1);
  assert.equal((await ledger.listAccounts())[0].balance_paise,1000);
  // Invalid repayment is validated before any new online backing row is written.
  const today=interest.localToday();
  const id=await ledger.createLoan({person_name:'A',phone:'',direction:'borrowed',principal_paise:1000,account_id:0,rate_bps:0,rate_period:'monthly',started_on:today,due_on:null,notes:''},'cash');
  await assert.rejects(()=>ledger.addRepayment(id,2000,today,'','online'));
  assert.equal(sql.prepare('SELECT count(*) AS n FROM accounts').get()?.n,1);
  await ledger.addRepayment(id,200,today,'','online');
  assert.equal(sql.prepare('SELECT count(*) AS n FROM accounts').get()?.n,2);
  assert.deepEqual((await ledger.listAccounts()).map((a:{balance_paise:number})=>a.balance_paise),[2000,-200]);
 } finally {sql.close();}
});
test('language translations use English fallback for unknown text',()=>{
 assert.equal(translate('hi','Cash'),'नकद');
 assert.equal(translate('en','Cash'),'Cash');
 assert.equal(translate('hi','A customer name'),'A customer name');
});
