import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { listHistory } from '../database/database';
import { buildHistory } from '../services/history';
import { HistoryItem } from '../types';
export function useHistory(){
 const [items,setItems]=useState<HistoryItem[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState('');
 useFocusEffect(useCallback(()=>{let active=true;setLoading(true);listHistory().then(data=>{if(active){setItems(buildHistory(data.transactions,data.loanActivity));setError('');}}).catch(e=>{if(active)setError(e instanceof Error?e.message:'Unable to load history.');}).finally(()=>{if(active)setLoading(false);});return()=>{active=false;};},[]));
 return {items,loading,error};
}
