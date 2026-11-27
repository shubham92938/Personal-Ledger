import React, { useCallback, useState } from 'react';
import { Alert, Pressable, Text, View } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { Button, Field, Header, Screen } from '../components/ui';
import { colors as c } from '../constants/theme';
import { useLanguage } from '../localization/LanguageProvider';
import { generateRecoveryKey } from '../services/backupCrypto';
import { connectDrive, disableDriveBackup, disconnectDrive, driveBackups, driveStatus, enableDriveBackup, restoreDriveBackup, runDriveBackup } from '../services/driveBackup';
import { DriveBackup } from '../services/driveApi';
import { scheduleDriveBackup, unscheduleDriveBackup } from '../services/driveTask';

export default function DriveBackupScreen(){
 const {t}=useLanguage();
 const [state,setState]=useState<Awaited<ReturnType<typeof driveStatus>>|null>(null);
 const [key,setKey]=useState('');const [generated,setGenerated]=useState('');const [confirm,setConfirm]=useState('');
 const [restoreKey,setRestoreKey]=useState('');const [files,setFiles]=useState<DriveBackup[]>([]);const [busy,setBusy]=useState(false);const [message,setMessage]=useState('');
 const refresh=useCallback(async()=>{try{setState(await driveStatus());}catch{setMessage('Unable to read backup settings.');}},[]);
 useFocusEffect(useCallback(()=>{void refresh();},[refresh]));
 async function perform(action:()=>Promise<void>){setBusy(true);setMessage('');try{await action();}catch(e){setMessage(e instanceof Error?e.message:'Google Drive backup failed.');}finally{await refresh();setBusy(false);}}
 const connect=()=>perform(async()=>{await connectDrive();setFiles([]);setMessage('Google account connected.');});
 const generate=()=>perform(async()=>{const next=await generateRecoveryKey();setKey(next);setGenerated(next);setConfirm('');});
 const enable=()=>perform(async()=>{if(!generated || key.trim().toLowerCase()!==generated)throw new Error('Generate a new recovery key and save it before enabling backup.');await scheduleDriveBackup();try{await enableDriveBackup(key,confirm);}catch(e){await unscheduleDriveBackup();throw e;}setKey('');setGenerated('');setConfirm('');setMessage('Automatic backup scheduled. No backup is verified yet; use Back up now.');});
 const disable=()=>perform(async()=>{await disableDriveBackup();await unscheduleDriveBackup();setMessage('Automatic backup disabled. Existing Drive backups remain.');});
 const disconnect=()=>perform(async()=>{await disconnectDrive();await unscheduleDriveBackup();setFiles([]);setMessage('Google account disconnected. Existing Drive backups remain.');});
 const backup=()=>perform(async()=>{await runDriveBackup();setMessage('Google Drive backup uploaded and verified.');});
 const list=()=>perform(async()=>{const found=await driveBackups();setFiles(found);setMessage(found.length?'Select a backup to restore.':'No Google Drive backups found.');});
 function confirmStop(action:()=>Promise<void>){Alert.alert(t('Remove the local recovery key?'),t('Automatic backup will stop and the stored key will be removed from this device. Existing Drive backups will remain, but you need the separately saved key to restore them.'),[{text:t('Cancel'),style:'cancel'},{text:t('Continue'),style:'destructive',onPress:()=>void action()}]);}
 function restore(file:DriveBackup){Alert.alert(t('Replace all local data?'),t('Restore this Google Drive backup? Current local data will be replaced after validation. An encrypted safety copy is saved on this device first.'),[{text:t('Cancel'),style:'cancel'},{text:t('Restore'),style:'destructive',onPress:()=>void perform(async()=>{await restoreDriveBackup(file.id,restoreKey);setMessage('Restore completed. Verify your records and save the local safety copy elsewhere.');})}]);}
 return <Screen><Header title="Google Drive backup" back/>
  <View style={{backgroundColor:'#3d2520',borderRadius:14,padding:16,marginBottom:18}}><Text style={{color:'#ffcfb5',lineHeight:19,fontSize:12}}>{t('Experimental: requires a configured Android build and has not been tested on an Android device. Do not rely on this as your only backup.')}</Text></View>
  <Text style={{color:c.white,fontWeight:'700',fontSize:16,marginBottom:10}}>{t('Google account')}</Text>
  <Text style={{color:c.muted,lineHeight:19,marginBottom:12}}>{state?.user ? `${t('Connected')}: ${state.user.email || t('Google account')}` : t('Not connected')}</Text>
  <Button title="Connect Google Drive" disabled={busy} onPress={()=>void connect()}/><View style={{height:10}}/><Button title="Disconnect Google Drive" secondary disabled={busy||!state?.user} onPress={()=>confirmStop(disconnect)}/>
  <Text style={{color:c.white,fontWeight:'700',fontSize:16,marginTop:24,marginBottom:10}}>{t('Automatic encrypted backup')}</Text>
  <Text style={{color:c.muted,lineHeight:19,fontSize:12,marginBottom:12}}>{t('Save the recovery key outside this device before enabling. The app stores a copy in Android Keystore for automatic uploads. Anyone with the key and backup can read your data. Without the key you cannot restore after reinstalling or losing your device.')}</Text>
  <Text style={{color:c.muted,lineHeight:19,fontSize:12,marginBottom:12}}>{t('Android schedules attempts opportunistically, not at an exact time. It may delay or stop them; network, battery, sign-in or consent can prevent a backup. The latest successful time is shown only after Drive read-back verification.')}</Text>
  <Text style={{color:c.white,marginBottom:12}}>{t('Status')}: {t(state?.settings?.enabled?'Enabled':'Disabled')}{state?.settings?.enabled && state.user?.id!==state.settings.accountId ? ` · ${t('Reconnect the original Google account')}`:''}</Text>
  {state?.settings?.enabled && !state.settings.lastVerified && <Text style={{color:c.muted,marginBottom:8}}>{t('No verified backup yet.')}</Text>}
  {state?.settings?.lastVerified && <Text style={{color:c.muted,marginBottom:8}}>{t('Last verified backup')}: {new Date(state.settings.lastVerified).toLocaleString()}</Text>}
  {state?.settings?.lastAttempt && <Text style={{color:c.muted,marginBottom:8}}>{t('Last attempt')}: {new Date(state.settings.lastAttempt).toLocaleString()}</Text>}
  {state?.settings?.lastError && <Text style={{color:c.red,marginBottom:10}}>{t(state.settings.lastError)}</Text>}
  {!state?.settings?.enabled && <><Button title="Generate recovery key" secondary disabled={busy} onPress={()=>void generate()}/><View style={{height:10}}/><Field label="Recovery key" value={key} onChangeText={setKey} autoCapitalize="none" autoCorrect={false} multiline/><Field label="Re-enter recovery key" value={confirm} onChangeText={setConfirm} autoCapitalize="none" autoCorrect={false} multiline/><Button title="Enable automatic backup" disabled={busy||!state?.user?.granted} onPress={()=>void enable()}/></>}
  {state?.settings?.enabled && <><Button title="Back up now" disabled={busy} onPress={()=>void backup()}/><View style={{height:10}}/><Button title="Disable automatic backup" secondary disabled={busy} onPress={()=>confirmStop(disable)}/></>}
  <Text style={{color:c.white,fontWeight:'700',fontSize:16,marginTop:24,marginBottom:10}}>{t('Restore from Google Drive')}</Text><Text style={{color:c.muted,lineHeight:19,fontSize:12,marginBottom:12}}>{t('Backups are in the app’s hidden Drive storage, not the normal Drive folder. Use the recovery key for the selected backup. Older backups may use different keys. Google sign-in alone cannot decrypt them.')}</Text><Text style={{color:c.muted,lineHeight:19,fontSize:12,marginBottom:12}}>{t('Old backups are not automatically deleted and use Drive storage. Removing app data through Google may delete all copies.')}</Text><Field label="Recovery key for selected backup" value={restoreKey} onChangeText={setRestoreKey} autoCapitalize="none" autoCorrect={false} multiline/><Button title="Find Drive backups" secondary disabled={busy||!state?.user?.granted} onPress={()=>void list()}/>
  {files.map(file=><Pressable accessibilityRole="button" key={file.id} disabled={busy} onPress={()=>restore(file)} style={{backgroundColor:c.card,borderRadius:12,padding:14,marginTop:10}}><Text style={{color:c.white,fontWeight:'600'}}>{file.name}</Text><Text style={{color:c.muted,fontSize:12,marginTop:5}}>{new Date(file.createdTime).toLocaleString()} · {t('Tap to restore')}</Text></Pressable>)}
  {!!message&&<Text style={{color:c.white,lineHeight:20,marginTop:16}}>{t(message)}</Text>}
 </Screen>;
}
