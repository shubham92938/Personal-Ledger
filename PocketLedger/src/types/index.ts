export type AccountKind = 'cash' | 'online';
export type TransactionKind = 'income' | 'expense' | 'transfer';
export type Account = { id: number; name: string; kind: AccountKind; opening_paise: number; balance_paise: number };
export type LedgerTransaction = { id: number; kind: TransactionKind; amount_paise: number; account_id: number; destination_id: number | null; occurred_at: string; description: string; category: string; account_name: string; destination_name: string | null };
export type TransactionInput = { kind: TransactionKind; amount_paise: number; account_id: number; destination_id: number | null; occurred_at: string; description: string; category: string };
