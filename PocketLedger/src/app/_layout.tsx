import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { colors } from '../constants/theme';
import { AppLockProvider } from '../components/AppLock';
export default function RootLayout(){return <><StatusBar style="light"/><AppLockProvider><Stack screenOptions={{headerShown:false,contentStyle:{backgroundColor:colors.background}}}/></AppLockProvider></>}
