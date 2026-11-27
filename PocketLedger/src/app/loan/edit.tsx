import { useLanguage } from '../../localization/LanguageProvider';
import React, { useState } from 'react';
import { Text } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Button, Field, Header, Loading, Screen } from '../../components/ui';
import { useLoans } from '../../components/useLoans';
import { colors as c } from '../../constants/theme';
import { updateLoanDetails } from '../../database/database';
import { Loan } from '../../types';
export default function EditLoanScreen() {const {t}=useLanguage();
  const {id}=useLocalSearchParams<{id:string}>();
  const {loans,loading,error}=useLoans(); const loan=loans.find(item=>String(item.id)===id);
  if(loading)return <Screen><Header title="Edit Loan" back/><Loading/></Screen>;
  if(error||!loan)return <Screen><Header title="Edit Loan" back/><Text style={{color:c.red}}>{t(error||'Loan not found.')}</Text></Screen>;
  return <EditLoanForm loan={loan}/>;
}
function EditLoanForm({loan}:{loan:Loan}) {const {t}=useLanguage();
  const [name,setName]=useState(loan.person_name); const [phone,setPhone]=useState(loan.phone); const [due,setDue]=useState(loan.due_on||''); const [notes,setNotes]=useState(loan.notes); const [problem,setProblem]=useState(''); const [busy,setBusy]=useState(false);
  async function save(){setBusy(true);setProblem('');try{await updateLoanDetails(loan.id,name,phone,due.trim()||null,notes);router.back();}catch(e){setProblem(e instanceof Error?e.message:'Unable to update loan.');}finally{setBusy(false);}}
  return <Screen><Header title="Edit Loan" back/><Field label="Person name" value={name} onChangeText={setName} maxLength={60}/><Field label="Phone (optional)" value={phone} onChangeText={setPhone} keyboardType="phone-pad" maxLength={30}/><Field label="Due date (optional, YYYY-MM-DD)" value={due} onChangeText={setDue} placeholder="YYYY-MM-DD"/><Field label="Notes (optional)" value={notes} onChangeText={setNotes} maxLength={250}/><Text style={{color:c.muted,fontSize:12,lineHeight:19,marginBottom:18}}>{t("Principal, direction, interest rate, date and balance type cannot be edited because they affect historical calculations. To correct them, delete the loan and create it again.")}</Text>{!!problem&&<Text style={{color:c.red,marginBottom:14}}>{t(problem)}</Text>}<Button title={busy?'Saving…':'Save Changes'} onPress={()=>void save()} disabled={busy}/></Screen>;
}
