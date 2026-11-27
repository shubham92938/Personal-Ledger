import { Platform } from 'react-native';
import * as TaskManager from 'expo-task-manager';
import * as BackgroundTask from 'expo-background-task';
import { runDriveBackup } from './driveBackup';
const NAME='pocketledger-google-drive-backup-v1';
if(Platform.OS==='android' && !TaskManager.isTaskDefined(NAME)) TaskManager.defineTask(NAME,async()=>{
 try {await runDriveBackup(true);return BackgroundTask.BackgroundTaskResult.Success;}
 catch {return BackgroundTask.BackgroundTaskResult.Failed;}
});
export async function scheduleDriveBackup(){
 if(Platform.OS!=='android' || !(await TaskManager.isAvailableAsync()) || (await BackgroundTask.getStatusAsync())!==BackgroundTask.BackgroundTaskStatus.Available) throw new Error('Background backup is unavailable on this device.');
 await BackgroundTask.registerTaskAsync(NAME,{minimumInterval:60});
}
export async function unscheduleDriveBackup(){if(Platform.OS==='android' && await TaskManager.isTaskRegisteredAsync(NAME))await BackgroundTask.unregisterTaskAsync(NAME);}
