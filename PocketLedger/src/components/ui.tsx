import React from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, TextInputProps, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ChevronLeft, LucideIcon } from 'lucide-react-native';
import { router } from 'expo-router';
import { colors as c } from '../constants/theme';

export function Screen({children, scroll=true}: {children: React.ReactNode; scroll?: boolean}) {
  const insets=useSafeAreaInsets();
  return <View style={{flex:1,backgroundColor:c.background,paddingTop:insets.top}}>{scroll ? <ScrollView contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">{children}</ScrollView> : <View style={s.content}>{children}</View>}</View>;
}
export function Header({title,back=false,right}: {title:string;back?:boolean;right?:React.ReactNode}) { return <View style={s.header}>{back && <Pressable accessibilityRole="button" accessibilityLabel="Go back" onPress={()=>router.back()} style={s.back}><ChevronLeft color={c.white} size={24}/></Pressable>}<Text style={s.title}>{title}</Text>{right}</View>; }
export function Button({title,onPress,secondary=false,disabled=false}: {title:string;onPress:()=>void;secondary?:boolean;disabled?:boolean}) {return <Pressable accessibilityRole="button" disabled={disabled} onPress={onPress} style={[s.button,secondary && s.secondary,disabled && {opacity:.45}]}><Text style={s.buttonText}>{title}</Text></Pressable>}
export function Field({label,...props}: TextInputProps & {label:string}) {return <View style={{gap:8,marginBottom:18}}><Text style={s.label}>{label}</Text><TextInput placeholderTextColor="#777D8C" {...props} style={[s.input,props.style]}/></View>}
export function Chip({label,active,onPress}: {label:string;active:boolean;onPress:()=>void}) {return <Pressable accessibilityRole="button" accessibilityState={{selected:active}} onPress={onPress} style={[s.chip,active && s.chipActive]}><Text style={[s.chipText,active && {color:c.white}]}>{label}</Text></Pressable>}
export function Empty({icon:Icon,title,description}: {icon:LucideIcon;title:string;description:string}) {return <View style={s.empty}><View style={s.emptyIcon}><Icon size={24} color={c.muted}/></View><Text style={s.emptyTitle}>{title}</Text><Text style={s.emptyText}>{description}</Text></View>}
export function Loading(){return <View style={s.loading}><ActivityIndicator color={c.red}/><Text style={s.emptyText}>Opening your ledger…</Text></View>}
export const s=StyleSheet.create({
 content:{paddingHorizontal:20,paddingTop:16,paddingBottom:32}, header:{height:44,flexDirection:'row',alignItems:'center',marginBottom:20,gap:10},back:{padding:4,marginLeft:-4},title:{fontSize:23,fontWeight:'700',color:c.white,flex:1,letterSpacing:-.5},
 button:{backgroundColor:c.red,borderRadius:14,minHeight:52,alignItems:'center',justifyContent:'center',paddingHorizontal:18},secondary:{backgroundColor:'transparent',borderWidth:1,borderColor:'#535865'},buttonText:{color:c.white,fontWeight:'700',fontSize:15},label:{color:c.white,fontSize:13,fontWeight:'600'},input:{backgroundColor:c.card,borderWidth:1,borderColor:c.border,borderRadius:12,color:c.white,fontSize:15,paddingHorizontal:14,minHeight:50},chip:{backgroundColor:c.card,borderRadius:12,paddingHorizontal:16,paddingVertical:11,alignItems:'center',justifyContent:'center'},chipActive:{backgroundColor:c.red},chipText:{color:c.muted,fontSize:13,fontWeight:'600'},empty:{padding:26,alignItems:'center',borderRadius:16,backgroundColor:c.card,gap:8},emptyIcon:{width:46,height:46,borderRadius:23,backgroundColor:c.elevated,alignItems:'center',justifyContent:'center',marginBottom:4},emptyTitle:{color:c.white,fontSize:15,fontWeight:'700'},emptyText:{color:c.muted,fontSize:13,lineHeight:19,textAlign:'center'},loading:{padding:36,alignItems:'center',gap:12}
});
