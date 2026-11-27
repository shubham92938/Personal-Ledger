# PocketLedger

PocketLedger is an **in-progress** offline-first Android personal ledger built with Expo, React Native, TypeScript, Expo Router and SQLite. This is not yet a production-ready finance app. No sample transactions are saved.

> **Data safety:** There is currently **no backup or restore**, encryption, app lock, or sync. Uninstalling the app or losing the device can permanently delete its data. Do not use this development version as the sole record of important finances.

## Implemented so far

- Dark dashboard and four-section navigation, inspired by the supplied reference.
- Local SQLite database with a versioned initial schema, foreign keys and indexes.
- Add/edit accounts and opening balances; delete accounts only when no transaction history references them.
- Add/edit/soft-delete income, expenses and transfers. Writes and audit entries are grouped in SQLite transactions, with application database operations serialized.
- Balances are calculated from the opening balance and non-deleted entries. Amounts are represented as integer paise. Transfers affect both accounts but not their combined total.
- Transaction search and filters by type, account, and date prefix (YYYY-MM or YYYY-MM-DD).
- Loading, empty and error states; EAS APK build profiles and an app icon.

The audit log is stored locally but has no viewer yet. A transaction has a local date and time, description and optional category. SQLite does not currently encrypt the local database.

## Roadmap and implementation plan

1. **Setup & design system:** Expo, TypeScript, dark theme, reusable components.
2. **Navigation & dashboard:** four tabs, balances, recent activity, quick actions.
3. **SQLite & migrations:** initial versioned schema, constraints and audit log. More tables and migrations still needed for the remaining features.
4. **Accounts:** create, edit and safe deletion. Further Android device testing needed.
5. **Transactions:** income, expense, transfer, edit, delete and calculated balances. Further Android integration testing and audit viewer needed.
6. **People & loans:** not implemented. Design loan, interest and repayment rules and tests before recording any loan money.
7. **History & reporting:** basic filters exist; expand and test as needed.
8. **Google authentication & Drive:** not implemented. Configure Google Cloud OAuth and Drive API; use the `drive.appdata` scope and a native-compatible sign-in solution. Android OAuth client registration requires the Android package name and signing certificate SHA-1; a development build will be needed for native integration.
9. **Encrypted automatic backup:** not implemented. Design authenticated encryption, user-held recovery credentials and key lifecycle before uploading. Add an Expo-compatible native WorkManager module with network constraints, retries and best-effort periodic scheduling; test process death, token expiry and retention. Never report success before upload verification.
10. **Restore:** not implemented. Validate encryption, integrity and schema; create a local safety copy, confirm destructive replacement, migrate older versions and test interruption and recovery on actual devices.
11. **APK:** EAS profiles are configured, but no release APK has been built or tested. Configure an EAS project and signing, then test an APK on Android before distributing it.

PIN, configurable themes, data export, Google account management and sync are also not implemented. People and backup screens explicitly say so; they do not create fake records or claim backups have succeeded.

## Setup on Windows

Install Node.js LTS (SDK 58 requires Node 22.13 or later), Git, VS Code and Expo Go on an Android phone. In a terminal from this folder:

```bash
npm ci
npx expo start
```

Scan the QR code with Expo Go. For LAN mode, the computer and phone generally need to be on the same Wi-Fi; `npx expo start --tunnel` is an alternative where LAN does not work. Expo Go can test the current SQLite/UI work, but future native backup/authentication integrations will require a development build. Normal financial operations do not require a server after the app is installed, but the Expo development server is needed while developing.

To run a browser preview, use `npm run web`. Web SQLite is experimental and requires cross-origin isolation; the browser's storage is separate from the Android database. The web preview is not a substitute for Android testing.

## Checks

```bash
npm run typecheck
npm run lint
npm test
```

The automated tests use Node's experimental SQLite and type stripping support. They exercise money parsing, arithmetic, the production migration and balance SQL, constraints, soft deletion, and rollback. They do **not** replace testing Expo SQLite and all flows on an Android device. Google backup/restore and APK tests cannot be performed yet because those features are not built.

## APK build (when ready)

The package identifier is currently `com.pocketledger.app`; change it to a unique identifier you control before configuring Google OAuth or a release build. Install/sign in to EAS and run:

```bash
npx eas-cli@latest login
npx eas-cli@latest build:configure
npx eas-cli@latest build --platform android --profile production
```

The `production` profile in `eas.json` requests an APK. EAS requires an Expo account, project configuration, network access and signing credentials. The EAS project ID and Google OAuth clients are deliberately not hardcoded. Building does not make the currently incomplete app production-ready.
