export type BalanceAccount = { id: number; kind: 'cash' | 'online'; balance_paise: number };
/** A category is unambiguous only when it contains exactly one account. */
export function soleAccountId(accounts: readonly Pick<BalanceAccount, 'id' | 'kind'>[], kind: BalanceAccount['kind']): number | null {
  const matches = accounts.filter(account => account.kind === kind);
  return matches.length === 1 ? matches[0].id : null;
}
/** Totals use the calculated balances, never manually maintained dashboard values. */
export function accountTotals(accounts: readonly BalanceAccount[]) {
  let cash = 0, online = 0;
  for (const account of accounts) {
    if (!Number.isSafeInteger(account.balance_paise)) throw new Error('An account balance exceeds the supported range.');
    if (account.kind === 'cash') cash += account.balance_paise;
    else online += account.balance_paise;
    if (!Number.isSafeInteger(cash) || !Number.isSafeInteger(online)) throw new Error('The total balance exceeds the supported range.');
  }
  const total = cash + online;
  if (!Number.isSafeInteger(total)) throw new Error('The total balance exceeds the supported range.');
  return {cash, online, total};
}
export function assertEditableTransaction(kind: string, destinationId: number | null, existingKind?: string): void {
  if ((kind !== 'income' && kind !== 'expense') || destinationId !== null) throw new Error('New transfers are no longer supported.');
  if (existingKind === 'transfer') throw new Error('Existing transfers are read-only.');
}
