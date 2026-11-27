import React, { useState } from 'react';
import { Alert, Pressable, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Button, Chip, Field, Header, Loading, Screen } from '../../components/ui';
import { useLoans } from '../../components/useLoans';
import { useLedger } from '../../components/useLedger';
import { colors as c } from '../../constants/theme';
import { addRepayment, deleteLoan, deleteRepayment } from '../../database/database';
import { calculateLoan, localToday } from '../../services/interest';
import { formatMoney, parseRupees } from '../../services/money';
export default function LoanDetails() {
  const {id}=useLocalSearchParams<{id:string}>(); const {loans,payments,loading,error,refresh}=useLoans(); const {accounts}=useLedger();
  const [amount,setAmount]=useState(''); const [account,setAccount]=useState<number|null>(null); const [date,setDate]=useState(localToday()); const [notes,setNotes]=useState(''); const [problem,setProblem]=useState(''); const [busy,setBusy]=useState(false);
  const loan=loans.find(l=>String(l.id)===id); const history=loan ? payments[loan.id]||[] : [];
  async function save() {const value=parseRupees(amount);if(!loan||!account||value===null||value<=0){setProblem('Select an account and enter a positive amount.');return;}setBusy(true);setProblem('');try{await addRepayment(loan.id,account,value,date,notes);setAmount('');setNotes('');await refresh();}catch(e){setProblem(e instanceof Error?e.message:'Unable to save repayment.');}finally{setBusy(false);}}
  function removeLoan() {
    if (!loan) return;
    Alert.alert('Delete loan?', 'This reverses the loan and all of its repayments from your account balances. The records remain in the audit trail.', [
      {text:'Cancel',style:'cancel'}, {text:'Delete',style:'destructive',onPress:async()=>{try{await deleteLoan(loan.id);router.back();}catch(e){setProblem(e instanceof Error?e.message:'Unable to delete loan.');}}},
    ]);
  }
  function removePayment(paymentId: number) {
    Alert.alert('Delete repayment?', 'The account balance and outstanding amount will be recalculated. The audit trail is retained.', [
      {text:'Cancel',style:'cancel'}, {text:'Delete',style:'destructive',onPress:async()=>{try{await deleteRepayment(paymentId);await refresh();}catch(e){setProblem(e instanceof Error?e.message:'Unable to delete repayment.');}}},
    ]);
  }
  if(loading)return <Screen><Header title="Loan Details" back/><Loading/></Screen>;
  if(error||!loan)return <Screen><Header title="Loan Details" back/><Text style={{color:c.red}}>{error||'Loan not found.'}</Text></Screen>;
  let result: ReturnType<typeof calculateLoan>;
  try {result=calculateLoan(loan,history,localToday());}catch(e){return <Screen><Header title="Loan Details" back/><Text style={{color:c.red}}>{e instanceof Error?e.message:'Unable to calculate balance.'}</Text></Screen>;}
  const row=(label:string,value:string)=><View style={{flexDirection:'row',justifyContent:'space-between',gap:12,marginTop:10}}><Text style={{color:c.muted,fontSize:13,flex:1}}>{label}</Text><Text style={{color:c.white,fontSize:13,fontWeight:'600',textAlign:'right'}}>{value}</Text></View>;
  return <Screen><Header title="Loan Details" back right={<Pressable onPress={()=>router.push({pathname:'/loan/edit',params:{id:String(loan.id)}})}><Text style={{color:c.red,fontWeight:'700'}}>Edit</Text></Pressable>}/><View style={{flexDirection:'row',alignItems:'center',gap:12,marginBottom:18}}><View style={{width:48,height:48,borderRadius:24,backgroundColor:c.blue,alignItems:'center',justifyContent:'center'}}><Text style={{fontSize:21,fontWeight:'700',color:c.white}}>{loan.person_name.charAt(0).toUpperCase()}</Text></View><View><Text style={{color:c.white,fontSize:18,fontWeight:'700'}}>{loan.person_name}</Text><Text style={{color:c.muted,marginTop:4,fontSize:12}}>{loan.direction==='borrowed'?'Money I borrowed':'Money I lent'}{loan.phone?` · ${loan.phone}`:''}</Text></View></View>
    <View style={{backgroundColor:c.card,borderRadius:16,padding:18,marginBottom:12}}><Text style={{color:c.muted,fontSize:12}}>REMAINING AMOUNT · {result.settled?'SETTLED':'OPEN'}</Text><Text style={{color:c.white,fontSize:29,fontWeight:'800',marginTop:7}}>{formatMoney(result.outstanding)}</Text>{row('Original principal',formatMoney(loan.principal_paise))}{row('Principal remaining',formatMoney(result.principalRemaining))}{loan.rate_bps>0&&<>{row('Rate',`${loan.rate_bps/100}% ${loan.rate_period}`)}{row('Interest accrued',formatMoney(result.accruedInterest))}{row('Unpaid interest',formatMoney(result.interestRemaining))}</>}{row('Total repaid',formatMoney(result.paid))}{row('Loan date',loan.started_on)}{loan.due_on&&row('Due date',loan.due_on)}{row('Original account',loan.account_name)}{!!loan.notes&&row('Notes',loan.notes)}</View>
    {loan.rate_bps>0&&<Text style={{color:c.muted,fontSize:12,lineHeight:18,marginBottom:18}}>Simple daily interest on unpaid principal. A month is 30 days; a year is 365 days. Each period is rounded to paise. Repayments cover interest first; interest is not compounded.</Text>}
    <Text style={{color:c.white,fontSize:16,fontWeight:'700',marginVertical:14}}>Repayment History</Text>{history.length?history.map(p=><View key={p.id} style={{backgroundColor:c.card,borderRadius:12,padding:14,marginBottom:8}}><View style={{flexDirection:'row',justifyContent:'space-between'}}><Text style={{color:c.white,fontWeight:'700'}}>{formatMoney(p.amount_paise)}</Text><Text style={{color:c.muted,fontSize:12}}>{p.paid_on}</Text></View><Text style={{color:c.muted,fontSize:12,marginTop:6}}>{p.account_name}{p.notes?` · ${p.notes}`:''}</Text><Pressable onPress={()=>removePayment(p.id)} style={{alignSelf:'flex-end',paddingTop:10}}><Text style={{color:c.red,fontSize:12,fontWeight:'600'}}>Delete repayment</Text></Pressable></View>):<Text style={{color:c.muted,fontSize:13,marginBottom:12}}>No repayments yet.</Text>}
    {!result.settled&&<><Text style={{color:c.white,fontSize:16,fontWeight:'700',marginTop:20,marginBottom:16}}>Record Repayment</Text><Field label="Amount (₹)" value={amount} onChangeText={setAmount} keyboardType="decimal-pad" placeholder="0.00"/><Field label="Date (YYYY-MM-DD)" value={date} onChangeText={setDate} placeholder="YYYY-MM-DD"/><Text style={{color:c.white,fontWeight:'600',marginBottom:10}}>Payment account</Text><View style={{flexDirection:'row',flexWrap:'wrap',gap:8,marginBottom:20}}>{accounts.map(a=><Chip key={a.id} label={a.name} active={a.id===account} onPress={()=>setAccount(a.id)}/>)}</View><Field label="Notes (optional)" value={notes} onChangeText={setNotes} maxLength={250} placeholder="Add a note"/><Button title={busy?'Saving…':'Save Repayment'} onPress={()=>void save()} disabled={busy}/><Text style={{color:c.muted,fontSize:12,lineHeight:18,marginTop:14}}>Enter the full outstanding amount to settle the loan. Repayments cannot be backdated before an existing repayment. Check the details before saving.</Text></>}
    {!!problem && <Text style={{color:c.red,marginTop:12}}>{problem}</Text>}<Pressable onPress={removeLoan} style={{alignItems:'center',padding:20,marginTop:12}}><Text style={{color:c.red,fontWeight:'700'}}>Delete loan</Text></Pressable>
  </Screen>;
}
