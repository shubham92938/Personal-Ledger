import { Tabs } from 'expo-router';
import { Home, List, UsersRound, Settings } from 'lucide-react-native';
import { colors as c } from '../../constants/theme';
export default function TabLayout(){return <Tabs screenOptions={{headerShown:false,tabBarActiveTintColor:c.red,tabBarInactiveTintColor:'#858A96',tabBarStyle:{backgroundColor:'#111216',borderTopColor:'#282A30',height:64,paddingTop:6},tabBarLabelStyle:{fontSize:10,fontWeight:'600',paddingBottom:4}}}>
<Tabs.Screen name="index" options={{title:'Home',tabBarIcon:({color})=><Home color={color} size={21}/>}}/>
<Tabs.Screen name="transactions" options={{title:'Transactions',tabBarIcon:({color})=><List color={color} size={21}/>}}/>
<Tabs.Screen name="people" options={{title:'People',tabBarIcon:({color})=><UsersRound color={color} size={21}/>}}/>
<Tabs.Screen name="settings" options={{title:'Settings',tabBarIcon:({color})=><Settings color={color} size={21}/>}}/>
</Tabs>}
