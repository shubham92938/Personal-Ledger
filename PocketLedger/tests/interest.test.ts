import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { calculateLoan, dateDay } from '../src/services/interest.ts';
const loan = {principal_paise: 100000, rate_bps: 200, rate_period:'monthly' as const, started_on:'2026-01-01'};
test('monthly simple interest accrues daily and does not compound',()=>{
 const result=calculateLoan(loan,[], '2026-01-31');
 assert.equal(result.accruedInterest,2000); assert.equal(result.outstanding,102000);
 assert.equal(calculateLoan(loan,[],'2026-03-02').outstanding,104000);
});
test('repayments pay interest first and reduce principal for future interest',()=>{
 const payments=[{amount_paise:51000,paid_on:'2026-01-31'}];
 const result=calculateLoan(loan,payments,'2026-03-02');
 assert.equal(result.principalRemaining,51000); assert.equal(result.accruedInterest,3020);
 assert.equal(result.interestRemaining,1020); assert.equal(result.outstanding,52020);
 const settled=calculateLoan(loan,[...payments,{amount_paise:52020,paid_on:'2026-03-02'}],'2026-06-01');
 assert.equal(settled.outstanding,0); assert.equal(settled.settled,true);
});
test('zero interest and annual rates, with calendar day counts',()=>{
 assert.equal(calculateLoan({...loan,rate_bps:0},[],'2027-01-01').outstanding,100000);
 assert.equal(calculateLoan({...loan,rate_period:'yearly'},[],'2027-01-01').outstanding,102000);
 assert.equal(dateDay('2024-03-01')-dateDay('2024-02-28'),2);
});
test('invalid dates, rates, history, and overpayments are rejected',()=>{
 assert.throws(()=>dateDay('2026-02-30')); assert.throws(()=>calculateLoan({...loan,rate_bps:10001},[],'2026-01-01'));
 assert.throws(()=>calculateLoan(loan,[{amount_paise:100001,paid_on:'2026-01-01'}],'2026-01-01'));
 assert.throws(()=>calculateLoan(loan,[{amount_paise:1,paid_on:'2025-12-31'}],'2026-01-01'));
 assert.throws(()=>calculateLoan(loan,[{amount_paise:1,paid_on:'2026-01-03'},{amount_paise:1,paid_on:'2026-01-02'}],'2026-01-03'));
});
test('large valid amounts remain exact at boundaries',()=>{
 const big={...loan,principal_paise:900000000000,rate_bps:10000};
 assert.equal(calculateLoan(big,[],'2026-01-31').outstanding,1800000000000);
});
