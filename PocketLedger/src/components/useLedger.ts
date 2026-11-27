import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { listAccounts, listTransactions } from '../database/database';
import { Account, LedgerTransaction } from '../types';
export function useLedger() {
  const [accounts,setAccounts]=useState<Account[]>([]); const [transactions,setTransactions]=useState<LedgerTransaction[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState('');
  const refresh=useCallback(async()=>{try { setError(''); const [a,t]=await Promise.all([listAccounts(),listTransactions()]); setAccounts(a); setTransactions(t); } catch(e) {setError(e instanceof Error?e.message:'Could not open the database.');} finally {setLoading(false);} },[]);
  useFocusEffect(useCallback(()=>{void refresh();},[refresh]));
  return {accounts,transactions,loading,error,refresh};
}
