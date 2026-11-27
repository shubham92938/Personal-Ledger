/** Simple daily interest on unpaid principal. Repayments pay accrued interest first.
 * A month is 30 days and a year is 365 days. Each segment between repayments is
 * rounded to the nearest paise; interest is never added to the principal. */
export type InterestLoan = { principal_paise: number; rate_bps: number; rate_period: 'monthly' | 'yearly'; started_on: string };
export type InterestPayment = { amount_paise: number; paid_on: string };
const MAX_PAISE = 900_000_000_000;
export function localToday(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
export function dateDay(value: string): number {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error('Use a valid date in YYYY-MM-DD format.');
  const [year, month, day] = value.split('-').map(Number);
  if (year < 1900 || year > 9999) throw new Error('Date must be between 1900 and 9999.');
  const time = Date.UTC(year, month - 1, day);
  const parsed = new Date(time);
  if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 || parsed.getUTCDate() !== day) throw new Error('Use a valid date in YYYY-MM-DD format.');
  return Math.floor(time / 86400000);
}
function segment(principal: number, rate: number, days: number, period: number): number {
  // principal * rate is safe under the validated limits. Split the division to
  // avoid multiplying that result by the number of days before dividing.
  const numerator = principal * rate;
  const denominator = 10000 * period;
  const value = Math.floor(numerator / denominator) * days + Math.round((numerator % denominator) * days / denominator);
  if (!Number.isSafeInteger(value)) throw new Error('Interest exceeds the supported amount.');
  return value;
}
export function calculateLoan(loan: InterestLoan, payments: InterestPayment[], asOf: string) {
  if (!Number.isSafeInteger(loan.principal_paise) || loan.principal_paise <= 0 || loan.principal_paise > MAX_PAISE || !Number.isSafeInteger(loan.rate_bps) || loan.rate_bps < 0 || loan.rate_bps > 10000 || !['monthly', 'yearly'].includes(loan.rate_period)) throw new Error('Invalid loan terms.');
  let principal = loan.principal_paise, interest = 0, accrued = 0, paid = 0;
  let cursor = dateDay(loan.started_on); const end = dateDay(asOf);
  if (end < cursor) throw new Error('Date cannot be before the loan date.');
  for (const payment of payments) {
    const day = dateDay(payment.paid_on);
    if (day < cursor || day > end || !Number.isSafeInteger(payment.amount_paise) || payment.amount_paise <= 0) throw new Error('Invalid repayment history.');
    const earned = segment(principal, loan.rate_bps, day - cursor, loan.rate_period === 'monthly' ? 30 : 365);
    interest += earned; accrued += earned;
    if (!Number.isSafeInteger(interest) || !Number.isSafeInteger(accrued) || !Number.isSafeInteger(principal + interest)) throw new Error('Loan amount exceeds the supported range.');
    if (payment.amount_paise > principal + interest) throw new Error('Repayment cannot exceed the outstanding amount.');
    const interestPaid = Math.min(interest, payment.amount_paise);
    interest -= interestPaid; principal -= payment.amount_paise - interestPaid; paid += payment.amount_paise; cursor = day;
  }
  const earned = segment(principal, loan.rate_bps, end - cursor, loan.rate_period === 'monthly' ? 30 : 365);
  interest += earned; accrued += earned;
  if (![interest, accrued, paid, principal + interest].every(Number.isSafeInteger)) throw new Error('Loan amount exceeds the supported range.');
  return { principalRemaining: principal, interestRemaining: interest, accruedInterest: accrued, paid, outstanding: principal + interest, settled: principal + interest === 0 };
}
