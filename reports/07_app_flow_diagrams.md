# Phase 5 (cont.) — Application Flow Diagrams

All diagrams below are reconstructed from the **declared Activity graph and naming** (manifest + class inventory) — they show the plausible screen sequence implied by activity names and feature grouping, not a verified runtime navigation graph (which would require either Intent-extra/method-body decompilation or dynamic tracing, neither available here). Treat arrows as "most likely transition," not confirmed `startActivity()` call sites.

## 7.1 App launch → authentication → home
```mermaid
flowchart TD
    A[SplashScreenActivity] --> B{Existing session?}
    B -- No --> C[OnBoardingActivity]
    C --> D[MobileInput]
    D --> E[OtpVerificationActivity]
    E -- new user --> F[ShopNameEntryActivity]
    E -- existing user --> G[SignUpForExistingUserActivity]
    F --> H[PinSetupActivity]
    G --> H
    H --> I[WalletLookUpAndDecideDestinationActivity]
    B -- Yes, no PIN set --> H
    B -- Yes, PIN set --> J[PinChangeSetupActivity / app-lock prompt]
    J -- correct PIN --> K[Home / MainActivity dashboard]
    I --> K
    J -- forgot PIN --> L[ForgotPinActivity] --> M[PinResetSetupActivity]
    M --> N[PinResetVerifiedFaceImageUpload]
    N --> O[PostVerificationDeviceChooserActivity]
    O --> K
    J -- too many failures --> P[PinBlockedActivity]
```

## 7.2 Core ledger ("Khata") transaction + edit/delete-with-PIN pattern
This exact confirm-with-PIN → success pattern recurs identically for 5 different entity types (malik/owner txn, "jer", cash txn, generic transaction, customer/supplier record) — shown once, generalized:
```mermaid
flowchart LR
    A[Home dashboard] --> B[Add / View Transaction screen]
    B --> C{Edit or Delete?}
    C -- Edit --> D[EditTransactionActivity]
    C -- Delete --> E[EditDeleteTransactionActivity]
    D --> F[ConfirmTxnEditDeleteWithPIN]
    E --> F
    F -- PIN OK --> G[TransactionEditDeleteSuccess]
    F -- PIN fail --> F
    G --> A
```
Concrete instances of this pattern in the codebase: `Confirm{Malik,Cash,CashBox}TxnWithPIN`, `ConfirmEditJerWithPIN`, `EditDeleteCustomerConfirmWithPIN` — each with its own `*EditDeleteSuccessActivity` / `*EditDeleteSelectionActivity` pair.

## 7.3 Reporting
```mermaid
flowchart TD
    A[Home dashboard] --> B[reports module: 11 in-app viewers]
    B --> B1[BakiReportActivity]
    B --> B2[BechaKenaReportActivity]
    B --> B3[CashReportActivity]
    B --> B4[ExpenseReportActivity]
    B --> B5[MalikReportActivity]
    B --> B6[SmsReportActivity]
    A --> C[report_download module: 13 PDF builders]
    C --> C1[DailyBakiPdfBuilderActivity]
    C --> C2[MonthlyBakiPdfBuilderActivity]
    C --> C3[CashBoxSummeryPdfActivity / CashBoxDetailPdfActivity]
    C --> C4[DailyExpensePdfBuilderActivity / MonthlyExpensePdfBuilderActivity]
    C --> C5[BechaKenaSummaryPdfActivity / DailyBechaKenaDetailPdfActivity / MonthlyBechaKenaDetailPdfActivity]
    C --> C6[MalikPdfReportBuilderActivity]
    C --> C7[CustomerListReportBuilderActivity / TxnListReportBuilderActivity]
```

## 7.4 Cashbox daily reconciliation
```mermaid
flowchart TD
    A[CashBoxTodayActivity] --> B{Balance vs. expected}
    B -- Matches --> C[CashAdjustmentConfirmationEvenActivity]
    B -- Surplus --> D[CashAdjustmentConfirmationPositiveActivity]
    B -- Shortfall --> E[CashAdjustmentConfirmationNegativeActivity]
    D --> F[CashAdjustmentSuccessPositiveActivity]
    A --> G[CashSellActivity]
    A --> H{Previous day correction needed?}
    H -- Yes --> I[PreviousDayCashAdjustmentActivity]
    I --> J{Even / Positive / Negative}
    J --> K[PreviousDayCashAdjustmentConfirmation*Activity]
    K --> L[PreviousDayCashAdjustmentSuccess]
```

## 7.5 TallyPay — eKYC / wallet onboarding
```mermaid
flowchart TD
    A[DigitalOnboardActivity] --> B[BusinessInfoChoiceActivity]
    B --> C[EkycInitActivity]
    C --> D[NIDVerificationActivity]
    D --> E[NidInfoActivity]
    E --> F[DocumentUploadActivity]
    F --> G[ImageCaptureActivity]
    G -- ML Kit face match --> H[TpCaptureNidSuccessActivity]
    H --> I[NomineeInfoActivity / TpNomineeInfoActivity]
    I --> J{Business account?}
    J -- Yes --> K[TradeLicenseActivity]
    J -- No --> L[TpWalletPinSetActivity]
    K --> L
    L --> M[TpWalletRegistrationActivity]
    M --> N[CongratulationsActivity]
    N --> O[TpWalletActivity — wallet home]
```

## 7.6 TallyPay — add money (multi-gateway WebView bridge pattern)
```mermaid
flowchart TD
    A[TpWalletActivity] --> B[AddMoneyActivity]
    B --> C{Source}
    C -- Bank --> D[AddMoneyFromBankActivity] --> D1[AddMoneyWebViewActivity]
    C -- Card --> E[AddMoneyFromCardActivity] --> D1
    C -- Nagad --> F[AddMoneyFromNagadActivity] --> F1[AddMoneyNagadWebViewActivity]
    C -- Rocket --> G[AddMoneyFromRocketActivity] --> G1[AddMoneyRocketWebViewActivity]
    D1 --> H{Gateway callback}
    F1 --> H
    G1 --> H
    H -- success --> I[DigitalSaleSuccessActivity / GenericSuccessActivity]
    H -- failure --> J[TransactionErrorActivity / FailedFullScreenActivity]
```
Each WebView bridge activity hosts a provider-hosted checkout page over HTTPS against the Nobopay gateway (`npapigwnew.nobopay.com`, Phase 4) or bKash's bundled asset kit (`assets/bkash/checkout_120.html`), rather than collecting card/bank credentials natively in the app.

## 7.7 Background sync (not a user-facing flow, but completes the architecture picture)
```mermaid
flowchart LR
    A[User action] --> B[(Write to local Room DB\nsynced=0, is_updated=1)]
    B --> C[UI reads from Room immediately\n— offline-first]
    B --> D[WorkManager enqueues sync]
    D --> E[arch.sync layer]
    E --> F{Network available?}
    F -- No --> D
    F -- Yes --> G[POST to backend via apimanager/Retrofit]
    G -- success --> H[(Update row:\nsynced=1, server_id=<id>, synced_date=now)]
    G -- failure --> D
    I[TokenRefreshWorker] -. periodic .-> E
    J[GAIDSyncWorker] -. periodic .-> E
    K[EventLoggerWorker] -. periodic .-> L[(event_logger table)]
    M[OpeningClosingMissingFixWorker] -. periodic .-> N[(opening_balance / closing_balance)]
```

## 7.8 Evidence basis
Derived entirely from `evidence/08_activity_inventory.txt`, `evidence/01_manifest_parsed.json`, `evidence/06_recovered_schema.sql.txt` (for the `synced`/`is_updated`/`server_id` column pattern), and the Worker class list in `02_application_architecture.md §2.4`.
