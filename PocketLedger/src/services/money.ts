/** Parse INR without floating point rounding. Reject more than two decimal places. */
export function parseRupees(value: string): number | null {
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(value.trim());
  if (!match) return null;
  const whole = Number(match[1]);
  const paise = whole * 100 + Number((match[2] || '').padEnd(2, '0'));
  return Number.isSafeInteger(paise) && paise <= 900000000000 ? paise : null;
}
export function formatMoney(paise: number): string {
  const sign = paise < 0 ? '-' : '';
  const abs = Math.abs(paise);
  const whole = Math.floor(abs / 100).toLocaleString('en-IN');
  const decimals = abs % 100;
  return `${sign}₹${whole}${decimals ? `.${String(decimals).padStart(2, '0')}` : ''}`;
}
export function balanceFor(opening: number, entries: {kind: string; amount: number; source: number; destination: number | null}[], account: number): number {
  return entries.reduce((sum, e) => sum + (e.source === account ? (e.kind === 'income' ? e.amount : -e.amount) : 0) + (e.kind === 'transfer' && e.destination === account ? e.amount : 0), opening);
}
