import type { HistoryItem, LedgerTransaction, LoanActivity } from '../types';
export type HistoryFilter = 'all' | 'income' | 'expense' | 'loans';
/** Incoming and outgoing describe actual cash movement, not ordinary income or expense. */
export function loanActivityIncoming(activity: Pick<LoanActivity,'direction'|'event_type'>): boolean {
  return activity.event_type === 'loan' ? activity.direction === 'borrowed' : activity.direction === 'lent';
}
export function loanActivityLabel(activity: Pick<LoanActivity,'direction'|'event_type'>): string {
  if (activity.event_type === 'loan') return activity.direction === 'borrowed' ? 'Borrowed from' : 'Lent to';
  return activity.direction === 'borrowed' ? 'Repayment to' : 'Repayment from';
}
export function historyDate(item: HistoryItem): string {return item.type==='transaction' ? item.transaction.occurred_at : item.activity.occurred_at;}
export function historyKey(item: HistoryItem): string {return item.type==='transaction' ? `transaction-${item.transaction.id}` : `${item.activity.event_type}-${item.activity.id}`;}
/** Date-only loan events sort at the start of the day; their actual time was never recorded. */
export function buildHistory(transactions: LedgerTransaction[], loanActivity: LoanActivity[]): HistoryItem[] {
  const rows:HistoryItem[]=[...transactions.map(transaction=>({type:'transaction' as const,transaction})),...loanActivity.map(activity=>({type:'loan' as const,activity}))];
  return rows.sort((a,b)=>historyDate(b).localeCompare(historyDate(a)) || historyKey(b).localeCompare(historyKey(a),undefined,{numeric:true}));
}
export function filterHistory(items: HistoryItem[], filter: HistoryFilter, date: string, query: string): HistoryItem[] {
  const q=query.trim().toLocaleLowerCase();
  return items.filter(item=>{
    if (filter==='loans' && item.type!=='loan') return false;
    if ((filter==='income' || filter==='expense') && (item.type!=='transaction' || item.transaction.kind!==filter)) return false;
    if (date && !historyDate(item).slice(0,10).startsWith(date)) return false;
    if (!q) return true;
    const search=item.type==='transaction' ? `${item.transaction.description} ${item.transaction.category}` : `${item.activity.person_name} ${item.activity.notes} ${loanActivityLabel(item.activity)}`;
    return search.toLocaleLowerCase().includes(q);
  });
}
