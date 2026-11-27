import React, { useMemo, useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Plus, ReceiptText } from 'lucide-react-native';
import { Chip, Empty, Field, Header, Loading, Screen } from '../../components/ui';
import { useHistory } from '../../components/useHistory';
import { HistoryRow } from '../../components/HistoryRow';
import { colors as c } from '../../constants/theme';
import { useLanguage } from '../../localization/LanguageProvider';
import { filterHistory, historyKey, HistoryFilter } from '../../services/history';
export default function Transactions(){
 const {t}=useLanguage();const {items,loading,error}=useHistory();const [filter,setFilter]=useState<HistoryFilter>('all');const [query,setQuery]=useState('');const [date,setDate]=useState('');
 const filtered=useMemo(()=>filterHistory(items,filter,date,query),[items,filter,date,query]);
 return <Screen><Header title="Transactions" right={<Pressable onPress={()=>router.push('/transaction/add')} accessibilityLabel={t('Add transaction')}><Plus color={c.red} size={26}/></Pressable>}/>
 <View style={{flexDirection:'row',flexWrap:'wrap',gap:7,marginBottom:16}}>{([['all','All'],['income','Income'],['expense','Expense'],['loans','Loans']] as const).map(([value,label])=><Chip key={value} label={label} active={filter===value} onPress={()=>setFilter(value)}/>)}</View>
 <Field label="Search" placeholder="Description, category or person" value={query} onChangeText={setQuery}/><Field label="Date filter (optional)" placeholder="YYYY-MM or YYYY-MM-DD" value={date} onChangeText={setDate}/>
 {loading?<Loading/>:error?<Text style={{color:c.red}}>{t(error)}</Text>:filtered.length?<View style={{backgroundColor:c.card,paddingHorizontal:14,borderRadius:15}}>{filtered.map(item=><HistoryRow key={historyKey(item)} item={item}/>)}</View>:<Empty icon={ReceiptText} title="No transactions found" description="Add a transaction or adjust your filters."/>}</Screen>;
}
