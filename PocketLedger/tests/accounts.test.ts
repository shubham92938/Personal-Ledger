import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { accountTotals, assertEditableTransaction, soleAccountId } from '../src/services/accounts.ts';
test('cash and online balances and total use all account balances',()=>{
 const accounts=[{id:1,kind:'cash' as const,balance_paise:500000},{id:2,kind:'online' as const,balance_paise:1200000},{id:3,kind:'cash' as const,balance_paise:-50}];
 assert.deepEqual(accountTotals(accounts),{cash:499950,online:1200000,total:1699950});
 assert.throws(()=>accountTotals([{id:1,kind:'cash',balance_paise:Number.MAX_SAFE_INTEGER},{id:2,kind:'cash',balance_paise:1}]));
});
test('select the only matching account automatically; multiple need a choice',()=>{
 const accounts=[{id:1,kind:'cash' as const},{id:2,kind:'online' as const},{id:3,kind:'online' as const}];
 assert.equal(soleAccountId(accounts,'cash'),1); assert.equal(soleAccountId(accounts,'online'),null); assert.equal(soleAccountId([],'cash'),null);
});
test('new transfers and edits to historic transfers are blocked',()=>{
 assert.doesNotThrow(()=>assertEditableTransaction('income',null)); assert.doesNotThrow(()=>assertEditableTransaction('expense',null));
 assert.throws(()=>assertEditableTransaction('transfer',2)); assert.throws(()=>assertEditableTransaction('income',2)); assert.throws(()=>assertEditableTransaction('income',null,'transfer'));
});
