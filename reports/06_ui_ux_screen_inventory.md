# Phase 5 — UI/UX Screen Inventory

**Method:** every `<activity>` declared in `AndroidManifest.xml` with an app-owned (`com.progoti.*`) class, grouped by its Java package (which maps closely to feature area), cross-referenced with the `res/layout` file census (1,117 layout XML files across all configs; 811 in the base `res/layout`, with `-land`, `-sw600dp`, `-v21/22/26`, `-watch-v20`, `-ldrtl-v17` variants for landscape/tablet/RTL/API-level/Wear fallbacks) and the `arch.viewmodels` package (130 ViewModel classes, §3.5 of the architecture report), which together confirm this is a screen-per-Activity, MVVM-bound app rather than a single-Activity/Fragment-navigation app (Fragments exist — 54 classes in `v2.fragments` plus feature-local ones — and are used *within* activities, e.g. for the `TpWalletActivity` wallet tab-bar, but are not the primary navigation unit).

## 5.1 Screen count by feature module
197 app-owned activities, grouped into 28 feature packages:

| Module | Screens | Feature area |
|---|---|---|
| `tallypay` | 52 | Digital wallet: send/receive money, bank-linking, mobile recharge, eKYC/NID verification, QR pay |
| `activities` (shared) | 19 | Reports, inbox, settings, help, security, referral |
| `cashbox` | 14 | Daily cash register adjustment & reconciliation |
| `report_download` | 13 | PDF report generation/export (one activity per report type) |
| (unpackaged/root) | 13 | Core money-movement: login, OTP, PIN change, payments, wallet details |
| `login` | 12 | Authentication, PIN setup/reset/change, device-switch flows |
| `reports` | 11 | In-app (non-PDF) report viewers |
| `customer_onboard` | 8 | Signup, OTP verification, shop setup, splash screen |
| `surecash` | 7 | Embedded SureCash SDK screens (cash-out, credit settlement, supplier payment) |
| `payments` | 6 | bKash checkout, SMS-credit purchase |
| `edit_delete_malik_txn` / `edit_jer` / `edit_delete_cash_txn` / `edit_delete_transaction` | 4 each | Edit/delete flows per transaction type, each gated behind a PIN-confirmation activity |
| `edit_delete_customer` | 4 | Customer/supplier record edit/delete, PIN-gated |
| `edit_delete_cash_box_txn` | 3 | Cashbox-entry edit/delete, PIN-gated |
| `cstxn`, `data_backup`, `tagada`, `add_customer`, `profile` | 2 each | Transaction sharing, backup, bulk-SMS ("Tagada"), add customer, profile |
| `supplier_txn`, `dialogs`, `GetBusinessTypeActivity`, `gallery`, `youtube`, `arch`, `dynamic_form` | 1 each | Single-purpose screens |

## 5.2 Primary feature surfaces

### A. Ledger / "Khata" core (the app's namesake feature)
Customer & supplier account management, credit ("Baki") entries, cash transactions, and edit/delete flows for each — all edit/delete operations route through a dedicated `Confirm*WithPIN` activity before a `*Success` confirmation screen, a consistent **destructive-action confirmation pattern** repeated identically across 5 separate transaction types (malik/owner txn, jer, cash txn, generic txn, cashbox txn, customer/supplier record).

### B. Reports
Two parallel reporting systems: in-app viewers (`reports`, 11 screens: Baki, Becha-Kena [buy-sell], Cash, Expense, Malik, SMS reports) and a **separate PDF-generation module** (`report_download`, 13 screens — one builder activity per report type, each presumably invoking a PDF-rendering library against the same underlying Room queries).

### C. TallyPay (digital wallet) — the largest single feature
52 activities covering: wallet registration & PIN setup, bank-account linking (with OTP verification), add-money (bank card / Nagad / Rocket, each with its own WebView bridge activity for the mobile-banking checkout page), send/transfer money, transaction history & detail, recharge, QR-based payment (own QR + scanning another's QR, "Bangla QR" — the Bangladesh Bank EMVCo QR standard), and a full **eKYC sub-flow**: `EkycInitActivity` → `NIDVerificationActivity`/`NidInfoActivity` (Bangladeshi National ID capture) → `DocumentUploadActivity`/`ImageCaptureActivity` (selfie/liveness, backed by the bundled ML Kit face-detection native library, Phase 1 §1.6) → `NomineeInfoActivity`/`TpNomineeInfoActivity` → `TradeLicenseActivity` (for business accounts) → `CongratulationsActivity`.

### D. Authentication & device security
`SplashScreenActivity` → `OnBoardingActivity` → mobile-number entry → `OtpVerificationActivity` → `ShopNameEntryActivity` (new user) or `SignUpForExistingUserActivity` (returning). Separately, `login` module manages **PIN-based app-lock**: initial setup, change, forgot/reset (with face-image re-verification: `PinResetVerifiedFaceImageUpload`), and a `PinBlockedActivity` (lockout after repeated failures) plus `MigrateTPPinPromptActivity` (migrating an older TallyPay-specific PIN into the unified scheme) and `PostVerificationDeviceChooserActivity` (new-device handoff).

### E. Cashbox (daily register)
Opening/closing balance entry with a 3-way adjustment-confirmation pattern (`*ConfirmationEvenActivity` / `*ConfirmationNegativeActivity` / `*ConfirmationPositiveActivity`) for both same-day and `PreviousDayCashAdjustment*` corrections.

## 5.3 Reusable UI components (confirmed by class structure)
- **RecyclerView adapters + typed click-listener interfaces** — the dominant list-UI pattern (§3.1/3.3 of the architecture report): one listener interface per list type (`CashTxnItemClickListener`, `CreditItemClickListener`, `BakiTxnItemClickListener`, etc.), all implementing the same `RecyclerItemClick` convention.
- **Shared dialogs module** (`v2.dialogs`, 134 classes) — bottom sheets / `AlertDialog` wrappers reused across features (e.g. `CashBoxDialogCallback` interface).
- **Jetpack Data Binding** (`DataBinderMapperImpl` + `generated.callback.*`, §3.7) — layouts use `<layout>` root tags with two-way/one-way bound ViewModels rather than manual `findViewById`.
- **`CalculatorHandler`/`CalculatorOutputHandler`** — a shared numeric-entry calculator widget used wherever an amount is entered (consistent with a bookkeeping app's need for quick arithmetic while entering a transaction).
- **WebView bridge activities** (`AddMoneyWebViewActivity`, `AddMoneyNagadWebViewActivity`, `AddMoneyRocketWebViewActivity`, `BkashCheckoutActivity`, generic `WebViewActivity`) — used to host each mobile-banking provider's own hosted checkout page (bKash's bundled asset kit, `assets/bkash/`, Phase 1 §1.7) inside the app rather than a native payment form.
- 203 `activity_*.xml`, 81 `fragment_*.xml`, 51 `row_*.xml`, 28 `abc_*.xml` (AppCompat framework internals, not app UI), 17 `dialog_*.xml`, 4 `item_*.xml` layouts; 8 `res/menu` files; 2,011 drawables; 15 custom font files (incl. dedicated Bengali-script fonts, Phase 1 §1.7).

## 5.4 Localization
Confirmed via Play's generated `res/xml/splits0.xml` (language-split manifest, decoded with `scripts/axml.py`): the app ships **Bengali (`bn`) and English (`en`)** language splits. This is consistent with the dedicated Bangla fonts in `assets/fonts/` and the `/bn/` paths on the TallyKhata/TallyPay marketing microsites (Phase 4).

## 5.5 Evidence files
- `evidence/08_activity_inventory.txt` — full 197-activity list grouped by module
- `evidence/01_manifest_parsed.json` — raw per-activity attributes (exported, launch mode, etc.)
