# Phase 2 — Package and Class Structure (detail)

Full machine-generated listing of all 2,516 app classes grouped by package: `evidence/09_full_app_package_class_listing.md` (197 distinct packages). This document curates the structurally interesting parts of that listing.

## 3.1 Callback / listener interfaces (`com.progoti.tallykhata.v2.interfaces`)
21 small single-purpose interfaces, all `public interface abstract`, named descriptively enough to infer UI interaction points even though their *method* names are obfuscated:
`BakiTxnItemClickListener`, `BuySmsItemClickListener`, `CalculatorHandler`, `CalculatorOutputHandler`, `CashBoxDialogCallback`, `CashBoxTxnItemClickListener`, `CashTransactionBehavior`, `CashTxnItemClickListener`, `CreditItemClickListener`, `CustomerInfoHandler`, `CustomerInputHandler`, `DailyCashExpenseItemClickListener`, `DailyCashTxnItemClickListener`, `DatePickerHandler`, `GenericCashBoxTxnItemClickListener`, `HomeRecentReloadListener`, `InboxMessageDeletionListener`, `MalikTxnItemClickListener`, `OnHomePressedListener`, `OperatorItemClickListener`, `RecyclerItemClick`.

This confirms a conventional **RecyclerView adapter + click-listener-interface** pattern used throughout (each list screen — customer list, credit/"Baki" list, cash transactions, "Malik" (owner) transactions, cashbox — has its own typed click listener), plus a `CalculatorHandler`/`CalculatorOutputHandler` pair backing an in-app numeric calculator widget used when entering amounts.

## 3.2 Networking layer (`com.progoti.tallykhata.v2.apimanager`) — 53 classes
This package is the single clearest piece of evidence for the HTTP client architecture (see `05_api_network_architecture.md` for the full write-up):
- **`ApiCaller`**, **`ApiService`**, **`TCApiService`** — the Retrofit service wrapper layer (`TCApiService` likely = "TallyKhata/TrueCaller-style... " or simply a second, differently-configured service — not resolvable by name alone beyond "a second API-service definition").
- **`ApiResponseHandler`**, **`ResponseHeaderHandler`**, **`ApiCallFailedException`** → **`ApiNotRecheableException`**, **`InvalidAPIResponse`** — a small custom exception hierarchy for network-error handling.
- 3 classes implement `okhttp3.Interceptor` (obfuscated names `c`, `i`, `k`) — i.e. **at least 3 OkHttp interceptors** are wired into the HTTP client (typical uses: auth-token injection, request/response logging, retry/error-mapping — exact behavior not recoverable without decompilation).
- 5 classes implement `com.google.gson.JsonDeserializer` (`d`, `e`, `f`, `g`, plus one more) — custom Gson deserializers, commonly used for date formats, `BigDecimal` amounts, or lenient enum parsing.
- 1 class implements `retrofit2.Callback` (`j`) and 1 implements `io.reactivex.rxjava3.functions.Function` (`a`) — confirming **both callback-based and RxJava3-based** Retrofit call sites coexist in the codebase.
- ~34 request/response **DTO classes** (`*Dto`, `*Request`, `*Response`), many implementing `java.io.Serializable` or Android's `Parcelable` (with the standard `$1` `Parcelable.Creator` companion class) — see the full list in `05_api_network_architecture.md` §5.3.

## 3.3 UI adapters (`com.progoti.tallykhata.v2.adapters`)
Only 10 classes live directly in this shared package (most feature-specific adapters live inside their own feature package instead, e.g. `tallypay.*`); the shared ones are `VisaCardAdapter` and `WalletServiceAdapter`, both extending `androidx.recyclerview.widget.RecyclerView.Adapter` (visible via the obfuscated supertype `androidx.recyclerview.widget.RecyclerView$e`) with nested `ViewHolder` subclasses (`RecyclerView$s`) and click/popup/guide listener interfaces.

## 3.4 Persistence layer — DAOs and the Room database
24 `@Dao`-pattern interfaces + 1 `RoomDatabase` subclass + 18 `Migration` subclasses. Full detail (including every recovered `CREATE TABLE` statement) is in `04_database_schema.md`. Class list:
```
BaseDao, ReportDao, CashBoxAdjustmentDao, CashSaleDao, ClosingBalanceDao, CostDao,
CreditCollectionAdjustmentDao, CreditDao, CustomerDao, DigitalSaleDao, DigitalTransactionDao,
DynamicFormAnswersDao, DynamicFormDao, EventLoggerDao, FileUploadHistoryDao, InboxMessageDao,
LedgerDao, LocationDao, LogDao, OpeningBalanceDao, PopupMessageDao, ReconciliationDao,
SupplierDao, SupplierPaymentAdjustmentDao, SupplyDao, TagadaLogDao, TransactionSettlementActionDao
```

## 3.5 ViewModels (`com.progoti.tallykhata.v2.arch.viewmodels`) — 130 classes
One (or a small cluster of) `ViewModel` class(es) per feature screen — this is the largest single evidence point for the **MVVM** pattern claim in `02_application_architecture.md`. Names are preserved (unlike methods), so the feature surface is fully enumerable; representative members include report ViewModels, cashbox ViewModels, customer/supplier ViewModels, and TallyPay wallet ViewModels (full list in `evidence/09_full_app_package_class_listing.md`).

## 3.6 Background workers (confirmed `androidx.work.Worker` subclasses)
| Worker | Package |
|---|---|
| `TokenRefreshWorker` | `v2.workers` |
| `GAIDSyncWorker` | `v2.workers` (syncs Google Advertising ID) |
| `EventLoggerWorker` | `v2.workers` |
| `OpeningClosingMissingFixWorker` | `v2.workers` |
| `BGLoginWorker` | `v2.workers` |
| `RechargePackageFetchWorker` | `v2.tallypay.workers` |

Plus `ShakeService extends android.app.Service` (`v2.tallypay.services`) — a foreground/background service, name suggesting a **shake-to-trigger** gesture feature inside the TallyPay module, and `PushNotificationMessageService extends com.google.firebase.messaging.FirebaseMessagingService` (`v2.fcm`) — standard FCM push-notification handling.

## 3.7 Generated / tooling classes
- `com.progoti.tallykhata.DataBinderMapperImpl` — Android Data Binding's generated mapper, confirming the app uses **Jetpack Data Binding** (`<layout>`-root XML) in addition to plain `findViewById`/ViewBinding-style layouts.
- `com.progoti.tallykhata.generated.callback.*` — Data Binding's generated listener-binding glue.

## 3.8 Full inventory reference
See `evidence/09_full_app_package_class_listing.md` for every one of the 197 app packages and all 2,516 classes with superclass/interface/method-count detail, and `evidence/02_package_inventory.txt` for the full third-party library package census.
