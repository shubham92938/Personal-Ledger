import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import Storage from 'expo-sqlite/kv-store';
import { Language, translate } from './translations';
const KEY='pocketledger.language';
type Context = {language:Language;ready:boolean;setLanguage:(language:Language)=>Promise<void>;t:(text:string)=>string};
const LanguageContext=createContext<Context|null>(null);
export function LanguageProvider({children}:{children:React.ReactNode}) {
  const [language,setValue]=useState<Language>('en'); const [ready,setReady]=useState(false);
  useEffect(()=>{let active=true;Storage.getItem(KEY).then(value=>{if(active&&(value==='en'||value==='hi'))setValue(value);}).catch(()=>{}).finally(()=>{if(active)setReady(true);});return()=>{active=false;};},[]);
  const setLanguage=useCallback(async(value:Language)=>{await Storage.setItem(KEY,value);setValue(value);},[]);
  const t=useCallback((text:string)=>translate(language,text),[language]);
  return <LanguageContext.Provider value={{language,ready,setLanguage,t}}>{children}</LanguageContext.Provider>;
}
export function useLanguage(){const value=useContext(LanguageContext);if(!value)throw new Error('Language provider is missing.');return value;}
