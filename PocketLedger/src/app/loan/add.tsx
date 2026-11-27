import React, { useState } from 'react';
import { Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Button, Chip, Field, Header, Loading, Screen } from '../../components/ui';
import { useLedger } from '../../components/useLedger';
import { colors as c } from '../../constants/theme';
import { createLoan } from '../../database/database';
import { localToday } from '../../services/interest';
import { parseRupees } from '../../services/money';
import { LoanDirection, RatePeriod } from '../../types';
export default function AddLoan() {
  const params = useLocalSearchParams<{direction?: string}>();
  const {accounts, loading, error} = useLedger();
  const [direction, setDirection] = useState<LoanDirection>(params.direction === 'borrowed' ? 'borrowed' : 'lent');
  const [name,setName]=useState(''); const [phone,setPhone]=useState(''); const [amount,setAmount]=useState(''); const [account,setAccount]=useState<number|null>(null);
  const [rate,setRate]=useState('0'); const [period,setPeriod]=useState<RatePeriod>('monthly'); const [date,setDate]=useState(localToday()); const [due,setDue]=useState(''); const [notes,setNotes]=useState(''); const [problem,setProblem]=useState(''); const [busy,setBusy]=useState(false);
  async function save() {
    const principal=parseRupees(amount); const bps=parseRupees(rate);
    if(!name.trim() || !account || principal===null || principal<=0 || bps===null || bps>10000) {setProblem('Enter a name, account, positive amount and interest rate between 0 and 100%.');return;}
    setBusy(true);setProblem('');
    try {const id=await createLoan({person_name:name,phone,direction,principal_paise:principal,account_id:account,rate_bps:bps,rate_period:period,started_on:date,due_on:due.trim()||null,notes});router.replace({pathname:'/loan/[id]',params:{id:String(id)}});}
    catch(e){setProblem(e instanceof Error?e.message:'Unable to save loan.');}finally{setBusy(false);}
  }
  return <Screen><Header title="Add Loan" back/>{loading?<Loading/>:error?<Text style={{color:c.red}}>{error}</Text>:<>
    <View style={{flexDirection:'row',gap:8,marginBottom:20}}><View style={{flex:1}}><Chip label="I lent money" active={direction==='lent'} onPress={()=>setDirection('lent')}/></View><View style={{flex:1}}><Chip label="I borrowed money" active={direction==='borrowed'} onPress={()=>setDirection('borrowed')}/></View></View>
    <Field label="Person name" value={name} onChangeText={setName} placeholder="Enter name" maxLength={60}/><Field label="Phone (optional)" value={phone} onChangeText={setPhone} placeholder="Phone number" keyboardType="phone-pad" maxLength={30}/><Field label="Principal amount (₹)" value={amount} onChangeText={setAmount} placeholder="0.00" keyboardType="decimal-pad"/>
    <Text style={{color:c.white,fontWeight:'600',marginBottom:10}}>Payment account</Text>{accounts.length?<View style={{flexDirection:'row',flexWrap:'wrap',gap:8,marginBottom:20}}>{accounts.map(a=><Chip key={a.id} label={a.name} active={account===a.id} onPress={()=>setAccount(a.id)}/>)}</View>:<View style={{marginBottom:20}}><Text style={{color:c.muted,marginBottom:12}}>Add an account first.</Text><Button title="Add account" secondary onPress={()=>router.push('/accounts')}/></View>}
    <Field label="Interest rate % (optional)" value={rate} onChangeText={setRate} placeholder="0" keyboardType="decimal-pad"/>{rate!=='0'&&rate!==''&&<><Text style={{color:c.white,fontWeight:'600',marginBottom:10}}>Interest period</Text><View style={{flexDirection:'row',gap:8,marginBottom:20}}><Chip label="Monthly" active={period==='monthly'} onPress={()=>setPeriod('monthly')}/><Chip label="Yearly" active={period==='yearly'} onPress={()=>setPeriod('yearly')}/></View></>}
    <Field label="Loan date (YYYY-MM-DD)" value={date} onChangeText={setDate} placeholder="YYYY-MM-DD"/><Field label="Due date (optional, YYYY-MM-DD)" value={due} onChangeText={setDue} placeholder="YYYY-MM-DD"/><Field label="Notes (optional)" value={notes} onChangeText={setNotes} placeholder="Add a note" maxLength={250}/>
    <Text style={{color:c.muted,fontSize:12,lineHeight:19,marginBottom:18}}>Simple interest is calculated daily on unpaid principal: 30 days per month or 365 days per year. Repayments pay interest first. No compounding. Financial terms cannot be edited later; check the details before saving.</Text>
    {!!problem&&<Text style={{color:c.red,marginBottom:14}}>{problem}</Text>}<Button title={busy?'Saving…':'Save Loan'} disabled={busy||!accounts.length} onPress={()=>void save()}/>
  </>}</Screen>;
}
