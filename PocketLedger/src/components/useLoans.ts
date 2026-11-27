import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { listLoans, listRepayments } from '../database/database';
import { Loan, Repayment } from '../types';
export function useLoans() {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [payments, setPayments] = useState<Record<number, Repayment[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const refresh = useCallback(async () => {
    try {
      setError('');
      const records = await listLoans();
      const histories = await Promise.all(records.map(async loan => [loan.id, await listRepayments(loan.id)] as const));
      setLoans(records); setPayments(Object.fromEntries(histories));
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load loans.'); }
    finally { setLoading(false); }
  }, []);
  useFocusEffect(useCallback(() => { void refresh(); }, [refresh]));
  return { loans, payments, loading, error, refresh };
}
