import { Redirect } from 'expo-router';
/** Old links no longer expose account management; existing database records remain intact. */
export default function FormerAccountsScreen() { return <Redirect href="/settings"/>; }
