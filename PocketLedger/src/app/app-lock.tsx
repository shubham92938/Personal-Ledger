import { useLanguage } from '../localization/LanguageProvider';
import React, { useState } from 'react';
import { Text } from 'react-native';
import { Button, Header, Screen } from '../components/ui';
import { useAppLock } from '../components/AppLock';
import { colors as c } from '../constants/theme';
export default function AppLockSettings(){const {t}=useLanguage();
  const {enabled,setEnabled}=useAppLock(); const [busy,setBusy]=useState(false); const [message,setMessage]=useState('');
  async function change(){setBusy(true);setMessage('');try{await setEnabled(!enabled);setMessage(enabled?'App lock disabled.':'App lock enabled.');}catch(e){setMessage(e instanceof Error?e.message:'Unable to change app lock.');}finally{setBusy(false);}}
  return <Screen><Header title="App Lock" back/><Text style={{color:c.white,fontSize:17,fontWeight:'700',marginBottom:12}}>{t('Device authentication:')} {t(enabled?'On':'Off')}</Text><Text style={{color:c.muted,lineHeight:21,marginBottom:20}}>{t("When enabled, PocketLedger asks for your device authentication when you open it or return after leaving it. Your device controls the fingerprint, face or screen-lock options available. This is not a separate app PIN and does not encrypt your database.")}</Text><Text style={{color:c.muted,lineHeight:21,marginBottom:20}}>{t("Make sure your device screen lock works before enabling this. If your device authentication becomes unavailable, you may be unable to unlock the app.")}</Text>{!!message&&<Text style={{color:c.white,marginBottom:14}}>{t(message)}</Text>}<Button title={busy?'Waiting…':enabled?'Disable app lock':'Enable app lock'} onPress={()=>void change()} disabled={busy}/></Screen>;
}
