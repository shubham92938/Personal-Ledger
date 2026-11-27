import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { buildHistory, filterHistory, historyKey, loanActivityIncoming, loanActivityLabel } from '../src/services/history.ts';
import type { LedgerTransaction, LoanActivity } from '../src/types/index.ts';
const base:LoanActivity={event_type:'loan',id:1,loan_id:1,direction:'lent',person_name:'Asha',amount_paise:10000,occurred_at:'2026-01-01',account_kind:'cash',notes:'rent'};
const transaction:LedgerTransaction={id:1,kind:'income',amount_paise:500,account_id:1,destination_id:null,occurred_at:'2026-01-03T14:00:00',description:'Salary',category:'work',account_name:'Cash',account_kind:'cash',destination_name:null,destination_kind:null};
test('loan movement and labels reflect actual cash flow in both directions',()=>{
 assert.equal(loanActivityIncoming(base),false);assert.equal(loanActivityLabel(base),'Lent to');
 assert.equal(loanActivityIncoming({...base,direction:'borrowed'}),true);assert.equal(loanActivityLabel({...base,direction:'borrowed'}),'Borrowed from');
 assert.equal(loanActivityIncoming({...base,event_type:'repayment'}),true);assert.equal(loanActivityLabel({...base,event_type:'repayment'}),'Repayment from');
 assert.equal(loanActivityIncoming({...base,event_type:'repayment',direction:'borrowed'}),false);assert.equal(loanActivityLabel({...base,event_type:'repayment',direction:'borrowed'}),'Repayment to');
});
test('history interleaves records, filters without counting loans as income, and searches people',()=>{
 const items=buildHistory([transaction],[base,{...base,id:1,event_type:'repayment',occurred_at:'2026-01-02'}]);
 assert.deepEqual(items.map(historyKey),['transaction-1','repayment-1','loan-1']);
 assert.equal(filterHistory(items,'all','','').length,3);assert.equal(filterHistory(items,'income','','').length,1);assert.equal(filterHistory(items,'expense','','').length,0);assert.equal(filterHistory(items,'loans','','').length,2);
 assert.equal(filterHistory(items,'all','','ASHA').length,2);assert.equal(filterHistory(items,'all','2026-01-02','').length,1);assert.equal(filterHistory(items,'all','','rent').length,2);
});
