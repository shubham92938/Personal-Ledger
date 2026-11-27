import React, { useCallback, useState } from 'react';
import { Text, View } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { ClipboardList } from 'lucide-react-native';
import { Empty, Header, Loading, Screen } from '../components/ui';
import { colors as c } from '../constants/theme';
import { AuditLog, listAuditLogs } from '../database/database';
export default function AuditScreen() {
  const [records,setRecords]=useState<AuditLog[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState('');
  useFocusEffect(useCallback(()=>{let active=true;listAuditLogs().then(items=>{if(active)setRecords(items);}).catch(e=>{if(active)setError(e instanceof Error?e.message:'Unable to load audit trail.');}).finally(()=>{if(active)setLoading(false);});return()=>{active=false;};},[]));
  return <Screen><Header title="Audit Trail" back/><Text style={{color:c.muted,fontSize:12,lineHeight:18,marginBottom:16}}>The latest 500 changes are shown. This history is stored only on this device and is not a backup.</Text>{loading?<Loading/>:error?<Text style={{color:c.red}}>{error}</Text>:records.length?records.map(item=><View key={item.id} style={{backgroundColor:c.card,borderRadius:14,padding:14,marginBottom:10,gap:6}}><Text style={{color:c.white,fontWeight:'700',textTransform:'capitalize'}}>{item.entity} · {item.action}</Text><Text style={{color:c.muted,fontSize:12}}>Record #{item.entity_id} · {new Date(item.created_at).toLocaleString('en-IN')}</Text>{!!item.before_json&&<Text selectable style={{color:c.muted,fontSize:11,lineHeight:17}}>Before: {item.before_json}</Text>}{!!item.after_json&&<Text selectable style={{color:c.muted,fontSize:11,lineHeight:17}}>After: {item.after_json}</Text>}</View>):<Empty icon={ClipboardList} title="No changes yet" description="Edits and other ledger activity will appear here."/>}</Screen>;
}
