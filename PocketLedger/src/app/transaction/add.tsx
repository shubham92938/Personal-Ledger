import React, { useState } from 'react';
import { Alert, Pressable, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Button, Chip, Field, Header, Loading, Screen } from '../../components/ui';
import { useLedger } from '../../components/useLedger';
import { colors as c } from '../../constants/theme';
import { deleteTransaction, saveTransaction } from '../../database/database';
import { parseRupees, formatMoney } from '../../services/money';
import { soleAccountId } from '../../services/accounts';
import { Account, AccountKind, LedgerTransaction } from '../../types';

export default function TransactionScreen() {
  const params = useLocalSearchParams<{kind?: string; id?: string}>();
  const {accounts, transactions, loading, error} = useLedger();
  const existing = transactions.find(t => String(t.id) === params.id);
  if (loading) return <Screen><Header title="Transaction" back/><Loading/></Screen>;
  if (error || (params.id && !existing)) return <Screen><Header title="Transaction" back/><Text style={{color:c.red}}>{error || 'Transaction not found.'}</Text></Screen>;
  return <TransactionForm accounts={accounts} existing={existing} initialKind={params.kind}/>;
}
function TransactionForm({accounts, existing, initialKind}: {accounts: Account[]; existing?: LedgerTransaction; initialKind?: string}) {
  const [kind, setKind] = useState<'income'|'expense'>(existing?.kind === 'income' || (!existing && initialKind === 'income') ? 'income' : 'expense');
  const [amount, setAmount] = useState(existing ? (existing.amount_paise / 100).toFixed(2) : '');
  const [account, setAccount] = useState<number|null>(existing?.account_id ?? null);
  const [accountKind, setAccountKind] = useState<AccountKind|null>(accounts.find(a => a.id === existing?.account_id)?.kind ?? null);
  const [description, setDescription] = useState(existing?.description || '');
  const [category, setCategory] = useState(existing?.category || '');
  const now = new Date();
  const [date, setDate] = useState(existing?.occurred_at.slice(0,10) || `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`);
  const [time, setTime] = useState(existing?.occurred_at.slice(11,16) || `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`);
  const [problem, setProblem] = useState('');
  const [busy, setBusy] = useState(false);
  const matching = accounts.filter(a => a.kind === accountKind);
  const effectiveAccount = account ?? (accountKind ? soleAccountId(accounts, accountKind) : null);
  function chooseKind(next: AccountKind) {
    setAccountKind(next);
    setAccount(soleAccountId(accounts, next));
  }
  async function save() {
    const value = parseRupees(amount);
    const d = /^\d{4}-\d{2}-\d{2}$/.test(date) ? new Date(`${date}T12:00:00`) : null;
    if (value === null || value <= 0 || !accountKind || (matching.length > 0 && !accounts.some(a => a.id === effectiveAccount && a.kind === accountKind)) || !/^([01]\d|2[0-3]):[0-5]\d$/.test(time) || !d || !Number.isFinite(d.getTime()) || `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` !== date) {
      setProblem('Enter a positive amount, choose a payment account, and enter a valid date and time.'); return;
    }
    setBusy(true);
    try { await saveTransaction({kind, amount_paise:value, account_id:effectiveAccount ?? 0, destination_id:null, occurred_at:`${date}T${time}:00`, description, category}, existing?.id, accountKind); router.back(); }
    catch (e) { setProblem(e instanceof Error ? e.message : 'Unable to save transaction.'); }
    finally { setBusy(false); }
  }
  function remove() {
    if (!existing) return;
    Alert.alert('Delete transaction?', 'The balance will be recalculated. An audit record will be retained.', [
      {text:'Cancel', style:'cancel'},
      {text:'Delete', style:'destructive', onPress:async()=>{try {await deleteTransaction(existing.id); router.back();} catch(e){setProblem(e instanceof Error ? e.message : 'Unable to delete.');}}},
    ]);
  }
  if (existing?.kind === 'transfer') return <Screen><Header title="Past Transfer" back/><View style={{backgroundColor:c.card,borderRadius:16,padding:18,gap:12}}><Text style={{color:c.white,fontSize:23,fontWeight:'700'}}>{formatMoney(existing.amount_paise)}</Text><Text style={{color:c.white}}>{existing.account_name} → {existing.destination_name}</Text><Text style={{color:c.muted,fontSize:13}}>{existing.occurred_at.replace('T',' ').slice(0,16)}</Text><Text style={{color:c.muted,lineHeight:19}}>Transfers are no longer available. This historical entry is kept so your account balances remain correct.</Text></View>{!!problem && <Text style={{color:c.red,marginTop:14}}>{problem}</Text>}<Pressable onPress={remove} style={{alignItems:'center',padding:20}}><Text style={{color:c.red,fontWeight:'700'}}>Delete historical transfer</Text></Pressable></Screen>;
  return <Screen><Header title={existing ? 'Edit Transaction' : 'Add Transaction'} back/>
    <View style={{flexDirection:'row',gap:8,marginBottom:20}}>{(['expense','income'] as const).map(k=><View style={{flex:1}} key={k}><Chip label={k === 'income' ? 'Income' : 'Expense'} active={kind === k} onPress={()=>setKind(k)}/></View>)}</View>
    <Field label="Amount (₹)" placeholder="0.00" keyboardType="decimal-pad" value={amount} onChangeText={setAmount} style={{fontSize:24,fontWeight:'700'}}/>
    <Text style={{color:c.white,fontWeight:'700',marginBottom:10}}>{kind === 'income' ? 'Add income to' : 'Pay using'}</Text>
    <View style={{flexDirection:'row',gap:8,marginBottom:16}}><View style={{flex:1}}><Chip label="Cash" active={accountKind==='cash'} onPress={()=>chooseKind('cash')}/></View><View style={{flex:1}}><Chip label="Online" active={accountKind==='online'} onPress={()=>chooseKind('online')}/></View></View>
    {accountKind && (matching.length ? <><Text style={{color:c.muted,fontSize:12,marginBottom:10}}>Payment account{matching.length === 1 ? ' (selected automatically)' : ' (choose one)'}</Text><View style={{flexDirection:'row',flexWrap:'wrap',gap:8,marginBottom:20}}>{matching.map(a=><Chip key={a.id} label={a.name} active={effectiveAccount===a.id} onPress={()=>setAccount(a.id)}/>)}</View></> : <View style={{marginBottom:20}}><Text style={{color:c.muted,marginBottom:12}}>A {accountKind === 'cash' ? 'Cash' : 'Online'} account with a zero opening balance will be created when you save. You can also add a custom account.</Text><Button title="Add custom account" secondary onPress={()=>router.push('/accounts')}/></View>)}
    <Field label="Date (YYYY-MM-DD)" placeholder="2026-01-01" value={date} onChangeText={setDate}/><Field label="Time (24-hour HH:MM)" placeholder="14:30" value={time} onChangeText={setTime}/><Field label="Description (optional)" placeholder="What was this for?" value={description} onChangeText={setDescription} maxLength={160}/><Field label="Category (optional)" placeholder="e.g. Food" value={category} onChangeText={setCategory} maxLength={60}/>
    {!!problem && <Text style={{color:c.red,marginBottom:14}}>{problem}</Text>}
    <Button title={busy ? 'Saving…' : existing ? 'Save Changes' : `Add ${kind === 'income' ? 'Income' : 'Expense'}`} onPress={()=>void save()} disabled={busy}/>
    {existing && <Pressable onPress={remove} style={{alignItems:'center',padding:18}}><Text style={{color:c.red,fontWeight:'700'}}>Delete transaction</Text></Pressable>}
  </Screen>;
}
