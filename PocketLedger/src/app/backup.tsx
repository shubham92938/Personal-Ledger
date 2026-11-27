import React from 'react';
import { Text } from 'react-native';
import { CloudOff } from 'lucide-react-native';
import { Empty, Header, Screen } from '../components/ui';
import { colors as c } from '../constants/theme';
export default function Backup(){return <Screen><Header title="Backup & Restore" back/><Empty icon={CloudOff} title="Backup is not available yet" description="Google Drive backup, encryption and restore have not been implemented or tested. No automatic backups are being made."/><Text style={{color:c.muted,fontSize:13,lineHeight:21,marginTop:20}}>Your data currently exists only on this device. If the app is uninstalled or the device is lost, it may not be recoverable. Do not rely on this development version for irreplaceable financial records.</Text></Screen>}
