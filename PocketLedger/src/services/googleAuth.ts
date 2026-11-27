import { Platform } from 'react-native';
const SCOPE='https://www.googleapis.com/auth/drive.appdata';
const clientId=process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID?.trim();
let configured=false;
function google(){
 if(Platform.OS!=='android')throw new Error('Google Drive backup is available only in an Android development or release build.');
 if(!clientId || !/^[\w-]+\.apps\.googleusercontent\.com$/.test(clientId))throw new Error('Google Drive is not configured. Set the Google web client ID and rebuild the app.');
 try {
  // Lazy loading keeps Expo Go and unsupported platforms from crashing on launch.
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const sdk: typeof import('react-native-nitro-google-signin')=require('react-native-nitro-google-signin');
  if(!configured){sdk.GoogleOneTapSignIn.configure({webClientId:clientId,scopes:[]});configured=true;}
  return sdk;
 } catch {throw new Error('Google sign-in requires a compatible Android development or release build.');}
}
export async function connectGoogle(){
 const sdk=google();await sdk.GoogleOneTapSignIn.checkPlayServices();
 const result=await sdk.GoogleOneTapSignIn.presentExplicitSignIn();
 if(!sdk.isSuccessResponse(result))throw new Error('Google sign-in was cancelled.');
 await sdk.GoogleOneTapSignIn.requestScopes([SCOPE]);
 return {id:result.data.user.id,email:result.data.user.email ?? ''};
}
export function currentGoogleUser(){const user=google().GoogleOneTapSignIn.getCurrentUser();return user ? {id:user.user.id,email:user.user.email ?? '',granted:user.scopes.includes(SCOPE)} : null;}
export async function signOutGoogle(){await google().GoogleOneTapSignIn.signOut();}
export const googleTokens={get:async()=> (await google().GoogleOneTapSignIn.getTokens()).accessToken,invalidate:async(token:string)=>google().GoogleOneTapSignIn.clearCachedAccessToken(token)};
