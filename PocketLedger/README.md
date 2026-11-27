# PocketLedger

PocketLedger is an **in-progress** offline-first Android personal ledger built with Expo, React Native, TypeScript, Expo Router and SQLite. This is not yet a production-ready finance app. No sample transactions are saved.

> **Data safety:** Google Drive backup, automatic backup and sync are not implemented. Manual encrypted backup/restore and device authentication are experimental and have not been tested on Android. Uninstalling the app or losing the device can permanently delete its data. Do not use this development version as the sole record of important finances.

## Implemented so far

- Dark dashboard and four-section navigation, inspired by the supplied reference.
- Local SQLite database with a versioned initial schema, foreign keys and indexes.
- Cash and Online are display-only balance totals; users no longer manage payment accounts. Existing account rows and opening balances are retained to preserve historical calculations.
- Add/edit/soft-delete income and expenses. Select Cash or Online. An internal backing row is chosen automatically; if none exists it is created with a zero opening balance atomically with the transaction. Editing an existing entry preserves its original backing row when its balance type is unchanged. Writes and audit entries are grouped in SQLite transactions, with application database operations serialized. New transfers are disabled; existing transfers remain visible and continue to affect balances unless explicitly deleted.
- Balances are calculated from the opening balance, non-deleted entries and loan principal/repayments. Amounts are represented as integer paise. Historical transfers affect both accounts but not their combined total. Borrowing and lending are not ordinary income or expenses.
- Create borrowed and lent loans with a person, date, Cash/Online balance, optional due date, notes, and optional monthly or yearly simple interest; view outstanding amounts and record partial or full repayments. Edit contact details, due date and notes; delete loans or repayments with balance recalculation and an audit record.
- Transaction search and filters by type and date prefix (YYYY-MM or YYYY-MM-DD).
- Experimental manual encrypted file export and restore, with a user-held recovery key, pre-restore encrypted safety snapshot and SQLite integrity checks. **Not yet Android-tested.**
- English and Hindi language choice in Settings, saved on the device separately from the ledger backup.
- Optional app lock using device authentication (not a separate app PIN). **Not yet Android-tested.**
- Loading, empty and error states; EAS APK build profiles and an app icon.

The audit trail in Settings displays the latest 500 local changes. A transaction has a local date and time, description and optional category. SQLite does not currently encrypt the local database.

## Roadmap and implementation plan

1. **Setup & design system:** Expo, TypeScript, dark theme, reusable components.
2. **Navigation & dashboard:** four tabs, balances, recent activity, quick actions.
3. **SQLite & migrations:** initial versioned schema, constraints and audit log. More tables and migrations still needed for the remaining features.
4. **Balances:** retain historical account data internally and automatically associate new activity with Cash or Online. Further Android device testing needed.
5. **Transactions:** income and expense with edit, delete and calculated balances. Creating transfers is disabled; historical transfers remain readable and may be deleted. Further Android integration testing is needed.
6. **People & loans:** create/view, metadata editing, deletion and repayment flows are implemented with version 2 and 3 database migrations. Editing financial terms or repayments, managing reusable person profiles, and linking ordinary transactions to people remain to be built. Loan activity is shown in People, not the Transactions history. Android device testing is still needed.
7. **History & reporting:** basic filters exist; expand and test as needed.
8. **Google authentication & Drive:** not implemented. Configure Google Cloud OAuth and Drive API; use the `drive.appdata` scope and a native-compatible sign-in solution. Android OAuth client registration requires the Android package name and signing certificate SHA-1; a development build will be needed for native integration.
9. **Encrypted automatic backup:** not implemented. Manual encrypted export and restore are experimental and do not schedule backups. Design authenticated encryption, user-held recovery credentials and key lifecycle before uploading. Add an Expo-compatible native WorkManager module with network constraints, retries and best-effort periodic scheduling; test process death, token expiry and retention. Never report success before upload verification.
10. **Restore:** experimental manual restore accepts schema version 3 only, validates authentication, schema and integrity, creates an encrypted on-device safety copy, then replaces data after explicit confirmation. Older backup migration, interruption testing and Android device verification remain outstanding.
11. **APK:** EAS profiles are configured, but no release APK has been built or tested. Configure an EAS project and signing, then test an APK on Android before distributing it.

A separate app PIN, configurable themes, CSV data export, Google account management and sync are also not implemented. The backup screen explicitly says this and never treats opening the share sheet as confirmed delivery.

## Loan interest and repayment rules

Interest is optional. When set, simple interest accrues daily on the **unpaid principal**, using a fixed 30-day month or 365-day year. Interest is never compounded. Interest is rounded to the nearest paise for each period between repayments. Repayments pay accrued interest first, then principal. Once principal and interest are fully paid, no further interest accrues. A repayment cannot exceed the amount owed on its date, be future-dated, or precede the loan or last repayment.

Creating a borrowed loan increases the selected Cash or Online balance; creating a lent loan decreases it. Repayments move money in the opposite direction, using the balance type selected for that repayment. Loan and repayment entries are not listed as ordinary income or expense. A loan’s person details, due date and notes can be edited; to change financial terms, delete the loan and recreate it. Loans and repayments can be deleted with confirmation; this recalculates balances and retains the audit trail.

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

The automated tests use Node’s experimental SQLite, type stripping and module mocking. They exercise money and loan calculations, production database operations via a Node SQLite adapter, schema migration, backup format validation, AES-GCM round trips using a Node adapter (not the Expo native crypto implementation), and WAL snapshot recovery using Python sqlite3 when available. They do **not** replace testing native Expo SQLite, encryption, sharing, restore, app lock, or APK installation on real Android devices. Google Drive backup is not implemented.

## Experimental manual backup and restore

This is a manual, file-based feature—not Google Drive integration, an automatic schedule, or a verified backup. Generate a new random 256-bit recovery key for each backup in **Settings → Backup & Restore**, save that key separately in a secure location, and re-enter it to share the encrypted file using Android’s share sheet. You must independently verify that the file was actually saved outside the device. The app does not store the key. Losing the key makes the file unrecoverable; anyone with both the key and file can decrypt the data.

The backup uses Expo Crypto AES-256-GCM over a serialized SQLite snapshot; no recovery key is embedded in the file. Restore authenticates and validates the snapshot, checks its SQLite version and schema, confirms replacement, and writes an encrypted safety copy privately on the device first using the same key. The safety copy can be shared from the backup screen. It is not an off-device backup unless you explicitly save it elsewhere. Only schema version 3 is accepted; older versions are not yet migrated during restore. The local SQLite database itself is **not encrypted**.

**Do not test destructive restore on the only copy of important data.** The Expo native encryption, file sharing, SQLite replacement, interruption/recovery and lock flows still need verification on Android before any backup is relied on. Android’s OS-level backup behavior is separate from this feature and depends on the device and app build; do not assume it is an encrypted PocketLedger backup or that it will restore your data.

## App lock

Settings → App Lock uses the device’s authentication prompt when enabled. It is a UI access gate, **not** database encryption, screenshot protection or a dedicated app PIN. Make sure the device screen lock works before enabling it. If the device cannot authenticate you, the app may be inaccessible. This feature requires Android device testing.

## Automatic application updates

The `expo-updates` dependency and separate `preview`/`production` EAS channels are present, but automatic updates are **not configured or active** without an Expo account and project ID. From the `PocketLedger` folder, sign in and run `npx eas-cli@latest update:configure` to connect your own project; inspect the generated `updates.url`, `extra.eas.projectId` and runtime version before building a new APK. Publish an update to the corresponding channel only after testing. Native dependency or configuration changes require a new APK, not an over-the-air update. Existing APKs without Expo Updates configured cannot receive these updates.

## APK build (when ready)

The package identifier is currently `com.pocketledger.app`; change it to a unique identifier you control before configuring Google OAuth or a release build. Install/sign in to EAS and run:

```bash
npx eas-cli@latest login
npx eas-cli@latest build:configure
npx eas-cli@latest build --platform android --profile production
```

The `production` profile in `eas.json` requests an APK. EAS requires an Expo account, project configuration, network access and signing credentials. The EAS project ID and Google OAuth clients are deliberately not hardcoded. Building does not make the currently incomplete app production-ready.
