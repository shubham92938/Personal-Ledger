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

test('both loan directions, interest, repayments and history share one consistent balance',async()=>{
 const {ledger,sql}=makeLedger();
 try {
  await ledger.database();
  sql.exec("INSERT INTO accounts(name,kind,opening_paise) VALUES('Cash','cash',1000000),('Bank','online',0)");
  const today=interest.localToday();const local=new Date();local.setDate(local.getDate()-30);
  const start=`${local.getFullYear()}-${String(local.getMonth()+1).padStart(2,'0')}-${String(local.getDate()).padStart(2,'0')}`;
  const base={phone:'',principal_paise:100000,account_id:0,rate_bps:200,rate_period:'monthly',started_on:start,due_on:null,notes:''};
  const lent=await ledger.createLoan({...base,person_name:'Lent Person',direction:'lent'},'cash');
  const borrowed=await ledger.createLoan({...base,person_name:'Borrowed Person',direction:'borrowed'},'cash');
  assert.equal((await ledger.listAccounts())[0].balance_paise,1000000);
  const loans=await ledger.listLoans();assert.equal(loans.find((l:any)=>l.id===lent).direction,'lent');assert.equal(loans.find((l:any)=>l.id===borrowed).direction,'borrowed');
  for(const loan of loans)assert.equal(interest.calculateLoan(loan,[],today).outstanding,102000);
  await ledger.addRepayment(lent,3000,today,'received','online');
  await ledger.addRepayment(borrowed,3000,today,'paid','cash');
  assert.deepEqual((await ledger.listAccounts()).map((a:any)=>a.balance_paise),[997000,3000]);
  for(const loan of loans){const payments=await ledger.listRepayments(loan.id);const result=interest.calculateLoan(loan,payments,today);assert.equal(result.accruedInterest,2000);assert.equal(result.interestRemaining,0);assert.equal(result.principalRemaining,99000);}
  let history=await ledger.listHistory();assert.equal(history.transactions.length,0);assert.equal(history.loanActivity.length,4);
  assert.deepEqual(history.loanActivity.map((e:any)=>[e.event_type,e.direction,e.account_kind]).sort(),[['loan','borrowed','cash'],['loan','lent','cash'],['repayment','borrowed','cash'],['repayment','lent','online']].sort());
  const repayment=history.loanActivity.find((e:any)=>e.event_type==='repayment'&&e.loan_id===lent);
  await ledger.deleteRepayment(repayment.id);history=await ledger.listHistory();assert.equal(history.loanActivity.length,3);assert.equal((await ledger.listAccounts())[1].balance_paise,0);
  await ledger.deleteLoan(borrowed);history=await ledger.listHistory();assert.equal(history.loanActivity.length,1);assert.equal(history.loanActivity[0].loan_id,lent);
  assert.equal((await ledger.listAccounts())[0].balance_paise,900000);
  assert.equal(sql.prepare('SELECT COUNT(*) AS n FROM transactions').get()?.n,0);
 } finally {sql.close();}
});
