import { useLanguage } from '../../localization/LanguageProvider';
import React, { useMemo, useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Plus, ReceiptText } from 'lucide-react-native';
import { Chip, Empty, Field, Header, Loading, Screen } from '../../components/ui';
import { useLedger } from '../../components/useLedger';
import { TransactionRow } from './index';
import { colors as c } from '../../constants/theme';
export default function Transactions(){const {t}=useLanguage();const {transactions,loading,error}=useLedger();const [filter,setFilter]=useState('all');const [query,setQuery]=useState('');const [date,setDate]=useState('');const filtered=useMemo(()=>transactions.filter(t=>(filter==='all'||t.kind===filter)&&(!date||t.occurred_at.slice(0,10).startsWith(date))&&(!query||`${t.description} ${t.category}`.toLowerCase().includes(query.toLowerCase()))),[transactions,filter,date,query]);return <Screen><Header title="Transactions" right={<Pressable onPress={()=>router.push('/transaction/add')} accessibilityLabel={t("Add transaction")}><Plus color={c.red} size={26}/></Pressable>}/><View style={{flexDirection:'row',gap:7,marginBottom:16}}>{['all','income','expense'].map(f=><View key={f} style={{flex:1}}><Chip label={f[0].toUpperCase()+f.slice(1)} active={filter===f} onPress={()=>setFilter(f)}/></View>)}</View><Field label="Search" placeholder="Description or category" value={query} onChangeText={setQuery}/><Field label="Date filter (optional)" placeholder="YYYY-MM or YYYY-MM-DD" value={date} onChangeText={setDate}/>{loading?<Loading/>:error?<Text style={{color:c.red}}>{t(error)}</Text>:filtered.length?<View style={{backgroundColor:c.card,paddingHorizontal:14,borderRadius:15}}>{filtered.map(t=><TransactionRow key={t.id} item={t}/>)}</View>:<Empty icon={ReceiptText} title="No transactions found" description="Add a transaction or adjust your filters."/>}</Screen>}
