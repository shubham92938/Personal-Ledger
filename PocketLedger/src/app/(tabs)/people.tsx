import { useLanguage } from '../../localization/LanguageProvider';
import React, { useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { router } from 'expo-router';
import { UsersRound, ChevronRight } from 'lucide-react-native';
import { Button, Chip, Empty, Header, Loading, Screen } from '../../components/ui';
import { useLoans } from '../../components/useLoans';
import { colors as c } from '../../constants/theme';
import { calculateLoan, localToday } from '../../services/interest';
import { formatMoney } from '../../services/money';
import { LoanDirection } from '../../types';
export default function People() {const {t}=useLanguage();
  const {loans, payments, loading, error} = useLoans();
  const [direction, setDirection] = useState<LoanDirection>('lent');
  const records = loans.filter(loan => loan.direction === direction);
  return <Screen><Header title="People"/>
    <View style={{flexDirection:'row',gap:8,marginBottom:18}}><View style={{flex:1}}><Chip label="I have to receive" active={direction==='lent'} onPress={()=>setDirection('lent')}/></View><View style={{flex:1}}><Chip label="I have to give" active={direction==='borrowed'} onPress={()=>setDirection('borrowed')}/></View></View>
    {loading ? <Loading/> : error ? <Text style={{color:c.red}}>{t(error)}</Text> : records.length ? records.map(loan => {
      let outstanding: string; let status: string;
      try { const result = calculateLoan(loan, payments[loan.id] || [], localToday()); outstanding = formatMoney(result.outstanding); status = result.settled ? 'Settled' : 'Outstanding'; }
      catch { outstanding = 'Unavailable'; status = 'Check loan details'; }
      return <Pressable key={loan.id} onPress={()=>router.push({pathname:'/loan/[id]',params:{id:String(loan.id)}})} style={{backgroundColor:c.card,borderRadius:16,padding:16,marginBottom:10,flexDirection:'row',alignItems:'center',gap:13}}><View style={{backgroundColor:c.blue,width:43,height:43,borderRadius:22,alignItems:'center',justifyContent:'center'}}><Text style={{fontWeight:'700',fontSize:19,color:c.white}}>{loan.person_name.charAt(0).toUpperCase()}</Text></View><View style={{flex:1}}><Text style={{color:c.white,fontWeight:'700',fontSize:15}}>{loan.person_name}</Text><Text style={{color:c.muted,fontSize:12,marginTop:5}}>{t(status)}{loan.due_on ? ` · ${t('Due')} ${loan.due_on}` : ''}</Text></View><Text style={{color:c.green,fontWeight:'700'}}>{outstanding}</Text><ChevronRight color={c.muted} size={17}/></Pressable>;
    }) : <Empty icon={UsersRound} title="No loans yet" description={direction==='lent'?'Money you lend will appear here.':'Money you borrow will appear here.'}/>}
    <View style={{height:20}}/><Button title="+  Add Borrowed or Lent Money" onPress={()=>router.push({pathname:'/loan/add',params:{direction}})}/>
    <Text style={{color:c.muted,fontSize:12,lineHeight:19,marginTop:18}}>{t("Loan principal and repayments change the selected balance. They are not ordinary income or expenses.")}</Text>
  </Screen>;
}
