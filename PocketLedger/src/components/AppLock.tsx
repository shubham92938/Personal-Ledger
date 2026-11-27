import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AppState, Platform, Text, View } from 'react-native';
import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import { LockKeyhole } from 'lucide-react-native';
import { Button } from './ui';
import { colors as c } from '../constants/theme';

const LOCK_KEY = 'pocketledger.device-lock.enabled';
type LockContextValue = { enabled: boolean; setEnabled: (next: boolean) => Promise<void> };
const LockContext = createContext<LockContextValue | null>(null);
export function useAppLock() {
  const value = useContext(LockContext);
  if (!value) throw new Error('App lock context is unavailable.');
  return value;
}
async function authenticate(message: string) {
  const result = await LocalAuthentication.authenticateAsync({promptMessage:message, disableDeviceFallback:false, biometricsSecurityLevel:'strong'});
  if (!result.success) throw new Error('Authentication was cancelled or failed. Check your device screen-lock settings and try again.');
}
export function AppLockProvider({children}: {children: React.ReactNode}) {
  const [enabled,setEnabled] = useState(false);
  const [state,setState] = useState<'loading'|'locked'|'unlocked'|'error'>('loading');
  const [message,setMessage] = useState('');
  const [busy,setBusy] = useState(false);
  const enabledRef = useRef(false);
  const load = useCallback(async () => {
    await Promise.resolve();
    if (Platform.OS === 'web') { setState('unlocked'); return; }
    try {
      const stored = await SecureStore.getItemAsync(LOCK_KEY);
      if (stored !== null && stored !== 'enabled') throw new Error('Invalid app-lock setting.');
      const on = stored === 'enabled'; enabledRef.current = on; setEnabled(on); setState(on?'locked':'unlocked');
    } catch {setMessage('Could not read the app-lock setting. Try again.');setState('error');}
  },[]);
  // Read the persisted setting before displaying any ledger screen.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(()=>{void load();},[load]);
  useEffect(()=>{const subscription=AppState.addEventListener('change',next=>{if(next==='background' && enabledRef.current) setState('locked');}); return ()=>subscription.remove();},[]);
  async function change(next: boolean) {
    if (Platform.OS === 'web') throw new Error('Device authentication is available only on Android or iOS.');
    await authenticate(next?'Enable PocketLedger app lock':'Disable PocketLedger app lock');
    if (next) await SecureStore.setItemAsync(LOCK_KEY,'enabled'); else await SecureStore.deleteItemAsync(LOCK_KEY);
    enabledRef.current=next;setEnabled(next);setState(next && AppState.currentState !== 'active' ? 'locked' : 'unlocked');
  }
  async function unlock(){setBusy(true);setMessage('');try{await authenticate('Unlock PocketLedger');setState(AppState.currentState === 'active' ? 'unlocked' : 'locked');}catch(e){setMessage(e instanceof Error?e.message:'Unable to unlock.');}finally{setBusy(false);}}
  const locked = state !== 'unlocked';
  return <LockContext.Provider value={{enabled,setEnabled:change}}>
    <View style={{flex:1}} pointerEvents={locked?'none':'auto'} accessibilityElementsHidden={locked} importantForAccessibility={locked?'no-hide-descendants':'auto'}>{children}</View>
    {locked && <View style={{position:'absolute',top:0,bottom:0,left:0,right:0,backgroundColor:c.background,alignItems:'center',justifyContent:'center',padding:28,gap:16}}><LockKeyhole color={c.red} size={36}/><Text style={{color:c.white,fontWeight:'700',fontSize:22}}>{state==='loading'?'Opening PocketLedger':state==='error'?'Unable to check app lock':'PocketLedger is locked'}</Text><Text style={{color:c.muted,textAlign:'center',lineHeight:20}}>{message || (state==='locked'?'Use your device authentication to continue.':'Please wait.')}</Text>{state==='locked'&&<View style={{alignSelf:'stretch'}}><Button title={busy?'Waiting…':'Unlock'} onPress={()=>void unlock()} disabled={busy}/></View>}{state==='error'&&<View style={{alignSelf:'stretch'}}><Button title="Try again" onPress={()=>void load()}/></View>}</View>}
  </LockContext.Provider>;
}
