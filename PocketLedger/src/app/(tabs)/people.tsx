import React from 'react';
import { Text, View } from 'react-native';
import { UsersRound } from 'lucide-react-native';
import { Empty, Header, Screen } from '../../components/ui';
import { colors as c } from '../../constants/theme';
export default function People(){return <Screen><Header title="People"/><View style={{flexDirection:'row',gap:8,marginBottom:18}}><View style={{flex:1,padding:13,borderRadius:13,backgroundColor:c.card,alignItems:'center'}}><Text style={{color:c.muted,fontSize:12,fontWeight:'600'}}>I have to receive</Text></View><View style={{flex:1,padding:13,borderRadius:13,backgroundColor:c.card,alignItems:'center'}}><Text style={{color:c.muted,fontSize:12,fontWeight:'600'}}>I have to give</Text></View></View><Empty icon={UsersRound} title="Borrowing & lending is next" description="Loan tracking, interest and repayments are not available yet. No loan data is being recorded."/></Screen>}
