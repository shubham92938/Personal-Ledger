import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { parseRupees, formatMoney, balanceFor } from '../src/services/money.ts';
test('money parsing is exact and rejects invalid precision', () => {
  assert.equal(parseRupees('5000.05'), 500005); assert.equal(parseRupees('0.1'), 10);
  for (const value of ['-1', '1.001', '1e2', '', 'abc']) assert.equal(parseRupees(value), null);
});
test('format INR and preserve paise', () => { assert.equal(formatMoney(123456789), '₹12,34,567.89'); assert.equal(formatMoney(-50), '-₹0.50'); });
test('income, expense and transfers produce correct balances and preserve total', () => {
  const entries = [{kind:'income',amount:200000,source:1,destination:null},{kind:'expense',amount:50000,source:1,destination:null},{kind:'transfer',amount:100000,source:1,destination:2}];
  assert.equal(balanceFor(500000,entries,1),550000); assert.equal(balanceFor(0,entries,2),100000);
  assert.equal(balanceFor(500000,entries,1)+balanceFor(0,entries,2),650000);
});
