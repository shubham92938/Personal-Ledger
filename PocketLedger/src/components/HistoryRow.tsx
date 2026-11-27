import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { router } from 'expo-router';
import { ArrowDownLeft, ArrowRightLeft, ArrowUpRight } from 'lucide-react-native';
import { colors as c } from '../constants/theme';
import { useLanguage } from '../localization/LanguageProvider';
import { loanActivityIncoming, loanActivityLabel } from '../services/history';
import { formatMoney } from '../services/money';
import { HistoryItem } from '../types';

export function HistoryRow({item}:{item:HistoryItem}){
 const {t}=useLanguage();
 const transaction=item.type==='transaction'?item.transaction:null;
 const activity=item.type==='loan'?item.activity:null;
 const incoming=activity?loanActivityIncoming(activity):transaction?.kind==='income';
 const transfer=transaction?.kind==='transfer';
 const Icon=transfer?ArrowRightLeft:incoming?ArrowDownLeft:ArrowUpRight;
 const color=transfer?c.blue:incoming?c.green:c.red;
 const date=transaction?.occurred_at ?? activity!.occurred_at;
 // Interpret stored date-only strings as local calendar dates, not UTC.
 const [year,month,day]=date.slice(0,10).split('-').map(Number);
 const dateLabel=new Date(year,month-1,day).toLocaleDateString('en-IN');
 const label=activity ? `${t(loanActivityLabel(activity))} ${activity.person_name}` : transaction!.description || t(transfer?'Transfer':incoming?'Income':'Expense');
 const kind=activity?.account_kind ?? transaction!.account_kind;
 return <Pressable accessibilityRole="button" onPress={()=>activity?router.push({pathname:'/loan/[id]',params:{id:String(activity.loan_id)}}):router.push({pathname:'/transaction/add',params:{id:String(transaction!.id)}})} style={{flexDirection:'row',alignItems:'center',paddingVertical:12,gap:12,borderBottomColor:c.border,borderBottomWidth:1}}>
  <View style={{width:40,height:40,borderRadius:13,backgroundColor:color+'22',alignItems:'center',justifyContent:'center'}}><Icon size={20} color={color}/></View>
  <View style={{flex:1}}><Text style={{color:c.white,fontSize:14,fontWeight:'700'}}>{label}</Text><Text style={{color:c.muted,fontSize:11,marginTop:4}}>{t(kind==='cash'?'Cash':'Online')}{transfer ? ` → ${t(transaction!.destination_kind==='cash'?'Cash':'Online')}`:''} · {dateLabel}{activity?` · ${t('Loan activity')}`:''}</Text></View>
  <Text style={{color:transfer?c.white:color,fontWeight:'700',fontSize:14}}>{transfer?'':incoming?'+':'−'}{formatMoney(activity?.amount_paise ?? transaction!.amount_paise)}</Text>
 </Pressable>;
}
