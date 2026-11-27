import { useLanguage } from '../localization/LanguageProvider';
import React, { useState } from 'react';
import { Alert, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Button, Field, Header, Screen } from '../components/ui';
import { colors as c } from '../constants/theme';
import { generateRecoveryKey } from '../services/backupCrypto';
import { validateRecoveryKey } from '../services/backupFormat';
import { pickEncryptedBackup, restoreEncryptedBackup, shareEncryptedBackup, shareLatestSafetyBackup } from '../services/manualBackup';
export default function Backup(){const {t}=useLanguage();
  const [key,setKey]=useState(''); const [generatedKey,setGeneratedKey]=useState(''); const [confirmation,setConfirmation]=useState(''); const [content,setContent]=useState<string|null>(null); const [busy,setBusy]=useState(false); const [status,setStatus]=useState('');
  async function generate(){setBusy(true);setStatus('');try{const generated=await generateRecoveryKey();setKey(generated);setGeneratedKey(generated);setConfirmation('');}catch(e){setStatus(e instanceof Error?e.message:'Unable to generate a key.');}finally{setBusy(false);}}
  async function share(){setBusy(true);setStatus('');try{const normalized=validateRecoveryKey(key);if(normalized!==generatedKey)throw new Error('Generate a new random recovery key for this backup.');if(normalized!==validateRecoveryKey(confirmation))throw new Error('The recovery key confirmation does not match.');await shareEncryptedBackup(normalized);setStatus('Share sheet closed. Verify that you saved the encrypted file outside this device; sharing does not confirm delivery.');}catch(e){setStatus(e instanceof Error?e.message:'Unable to create backup.');}finally{setBusy(false);}}
  async function pick(){setBusy(true);setStatus('');try{const selected=await pickEncryptedBackup();if(selected){setContent(selected);setStatus('Backup file selected. Enter its recovery key before restoring.');}}catch(e){setStatus(e instanceof Error?e.message:'Unable to open file.');}finally{setBusy(false);}}
  function restore(){
    if (!content){setStatus('Select a backup file first.');return;}
    try {validateRecoveryKey(key);} catch(e){setStatus(e instanceof Error?e.message:'Enter the recovery key.');return;}
    Alert.alert(t("Replace all local data?"), t("Restoring replaces your current transactions, people and loans with the selected backup. An encrypted safety copy is created on this device first. Continue?"),[
      {text:t('Cancel'),style:'cancel'},
      {text:t('Restore'),style:'destructive',onPress:async()=>{setBusy(true);setStatus('');try{await restoreEncryptedBackup(content,key);setContent(null);setStatus('Restore completed. An encrypted pre-restore safety copy was saved on this device using the same recovery key. Verify your records.');}catch(e){setStatus(e instanceof Error?e.message:'Restore failed.');}finally{setBusy(false);}}},
    ]);
  }
  async function safety(){setBusy(true);setStatus('');try{await shareLatestSafetyBackup();setStatus('Share sheet closed. Verify that the safety copy was saved elsewhere. Use the recovery key entered during that restore.');}catch(e){setStatus(e instanceof Error?e.message:'Unable to share the safety copy.');}finally{setBusy(false);}}
  return <Screen><Header title="Backup & Restore" back/>
    <Button title="Google Drive backup" onPress={()=>router.push('/drive-backup')}/><View style={{height:18}}/>
    <View style={{backgroundColor:'#3d2520',padding:16,borderRadius:14,marginBottom:18}}><Text style={{color:'#ffcfb5',fontWeight:'700',marginBottom:6}}>{t("Experimental manual backup")}</Text><Text style={{color:'#ffcfb5',fontSize:12,lineHeight:19}}>{t("Manual export and restore has not yet been tested on an Android device. Do not rely on it as your only backup.")}</Text></View>
    <Text style={{color:c.white,fontWeight:'700',fontSize:16,marginBottom:10}}>{t("Recovery key")}</Text><Text style={{color:c.muted,fontSize:13,lineHeight:20,marginBottom:14}}>{t("Generate a new random key for each backup. The app does not save it. Store it somewhere safe, separately from your backup file. If you lose it, the backup cannot be decrypted. Anyone with the key and file can read your records.")}</Text>
    <Field label="64-character recovery key" value={key} onChangeText={setKey} autoCapitalize="none" autoCorrect={false} placeholder="Generate or enter your key" multiline/>
    <Button title="Generate new recovery key" secondary disabled={busy} onPress={()=>void generate()}/><View style={{height:18}}/>
    <Text style={{color:c.white,fontWeight:'700',fontSize:16,marginBottom:10}}>{t("Create encrypted backup")}</Text><Text style={{color:c.muted,fontSize:12,lineHeight:19,marginBottom:12}}>{t("Save the key first, then re-enter it below. The share sheet can save the file to your chosen app or storage; it is not an automatic Google Drive backup.")}</Text>
    <Field label="Re-enter recovery key" value={confirmation} onChangeText={setConfirmation} autoCapitalize="none" autoCorrect={false} placeholder="Confirm key" multiline/>
    <Button title={busy?'Working…':'Share encrypted backup'} disabled={busy} onPress={()=>void share()}/><View style={{height:24}}/>
    <Text style={{color:c.white,fontWeight:'700',fontSize:16,marginBottom:10}}>{t("Restore from file")}</Text><Text style={{color:c.muted,fontSize:12,lineHeight:19,marginBottom:14}}>{t("Choose a version 3 PocketLedger backup, enter the key used to create it, and confirm replacement. Newer changes after that backup will not be included.")}</Text><Button title={content?'Backup selected · choose another':'Choose encrypted backup'} secondary disabled={busy} onPress={()=>void pick()}/><View style={{height:10}}/><Button title="Restore selected backup" disabled={busy||!content} onPress={restore}/><View style={{height:12}}/><Button title="Share latest pre-restore safety copy" secondary disabled={busy} onPress={()=>void safety()}/>
    {!!status&&<Text selectable style={{color:c.white,fontSize:13,lineHeight:20,marginTop:18}}>{t(status)}</Text>}
  </Screen>;
}
