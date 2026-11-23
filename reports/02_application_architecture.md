# Phase 2 — Application Architecture Documentation

## 2.1 Method / toolchain note
No decompiler (JADX) was available in this offline sandbox. All findings below come from **structural DEX parsing** (class/method/field tables, type signatures, and — critically — the DEX string pools, which still contain full literal strings such as embedded SQL and URLs even under ProGuard/R8 member obfuscation) via the custom parser `scripts/dexparse.py`. This recovers the full class/package graph, inheritance, interface implementation, and method *signatures* (names, parameter types, return types) for every class. It does **not** recover method *bodies* (control flow / business-logic implementation) — see `09_technical_limitations.md`.

## 2.2 Overall shape
| Metric | Value |
|---|---|
| Total classes across all 4 DEX files | 34,774 |
| Application-authored classes (`com.progoti.*`) | 2,516 |
| Third-party/library classes | 32,258 (92.8%) |

The app is a thin (relatively speaking — 2,516 classes is still a large app) layer of business logic on top of a very large dependency graph (Google Play Services, Firebase, Facebook SDK, gRPC/Firestore, Jackson, RxJava3, Glide, Lottie, ZXing, Stetho, Apache Commons, etc. — see `03_package_class_structure.md` for the full library inventory).

## 2.3 Application package map
All app code lives under two root namespaces:
- `com.progoti.tallykhata.v2.*` — 2,381 classes (99% of app code) — the TallyKhata ledger app itself
- `com.progoti.surecash.*` — 117 classes — an embedded **SureCash payment SDK** (`paymentsdk` sub-package: `components`, `helper`, `dto`, `views`, `interfaces`, `fcm`, `sdkclient`), confirmed by the manifest meta-data block `com.surecash.sdk.*` and `surecash-client-*` keys (see `05_api_network_architecture.md` and `08_security_permission_analysis.md`)
- `com.progoti.emvqr.*` — 15 classes — an **EMV QR code parser** (Bangladesh Bank's standard QR payment code format used by bKash/Nagad/banks), with `model`, `enums`, `listener`, `helper`, `core` sub-packages

### Top-level module breakdown (`com.progoti.tallykhata.v2.*`, by class count)
| Module | Classes | Role (inferred from name + member types) |
|---|---|---|
| `tallypay` | 968 | Digital-wallet / payment feature ("TallyPay") — by far the largest module |
| `arch` | 369 | App architecture layer: ViewModels, data models, sync, persistence (Room), utils |
| `dialogs` | 134 | Shared dialog/bottom-sheet UI components |
| `utilities` | 89 | Cross-cutting helpers |
| `surecash` | 88 | TallyKhata-side glue code around the embedded SureCash SDK |
| `payments` | 71 | bKash / SMS-credit purchase flows |
| `cstxn` | 63 | "Cash/Customer Transaction" sharing flow |
| `customer_onboard` | 54 | Signup/OTP/shop-setup flow |
| `fragments` | 54 | Shared fragments |
| `apimanager` | 53 | Networking layer (Retrofit service wiring — see Phase 4) |
| `home` | 48 | Main ledger dashboard |
| `activities` / `profile` / `login` | 37 / 37 / 27 | Core screens |
| `cashbox`, `edit_delete_*` (7 modules), `reports`, `report_download`, `data_backup`, `dynamic_form`, `camera`, `security`, `workers`, `fcm`, `tagada`, `help` | 5–20 each | Feature-specific screen/logic clusters (see `03_package_class_structure.md` for full list) |

### `tallypay` sub-modules (the wallet feature)
| Sub-module | Classes |
|---|---|
| `activities` | 411 |
| `nobopayDataModel` | 273 — data/DTO classes for the **Nobopay** payment-gateway integration (see Phase 4: `npapigwnew.nobopay.com`) |
| `ekyc` | 77 — National-ID verification flow |
| `dashboard` | 49 |
| `helper`, `views`, `limit`, `accountManager`, `api`, `aday_kori`, `appgatewayClient` | 12–30 each |

### `arch` sub-modules (app architecture layer)
| Sub-module | Classes | Pattern |
|---|---|---|
| `viewmodels` | 130 | **MVVM** — one ViewModel class roughly per screen/feature |
| `models` | 84 | Domain/DTO model classes |
| `sync` | 58 | Client↔server data-sync logic (paired with Room `synced` / `is_updated` columns seen in every table, Phase 3) |
| `persistence` | 52 | **Room** database: 1 `RoomDatabase` subclass (`TallyKhataDatabase`) + 24 `@Dao` interfaces, confirmed by direct inheritance from `androidx.room.RoomDatabase` and literal `CREATE TABLE` SQL in the generated `_Impl` classes (full detail in `04_database_schema.md`) |
| `util` | 44 | Helpers |

## 2.4 Confirmed architectural pattern
This is a standard **Android MVVM app with a local-first (offline-capable, sync-on-reconnect) Room database**:
- `TallyKhataDatabase extends androidx.room.RoomDatabase`, with a generated `TallyKhataDatabase_Impl` (34 and 48 methods respectively) and 18 anonymous `Migration` subclasses (`TallyKhataDatabase$a` … `$v`, each extending Room's `Migration` base — i.e. **at least 18 historical schema migrations** have shipped), confirming the app has gone through many versions with evolving local schema.
- 24 `@Dao`-style interfaces (`ReportDao`, `CustomerDao`, `LedgerDao`, `CreditDao`, `SupplierDao`, `DigitalTransactionDao`, `InboxMessageDao`, `EventLoggerDao`, `TagadaLogDao`, `TransactionSettlementActionDao`, etc.) back the Room layer — one per logical entity, matching the 32 recovered tables (some tables share a DAO).
- `com.progoti.tallykhata.v2.arch.sync` (58 classes) plus `androidx.work.*` background Workers (`TokenRefreshWorker`, `GAIDSyncWorker`, `EventLoggerWorker`, `OpeningClosingMissingFixWorker`, `BGLoginWorker`, `RechargePackageFetchWorker` — all `extends androidx.work.Worker`) implement **WorkManager-based background sync/retry** — the classic pattern for "write to local Room DB immediately, sync to server in the background."
- `TallykhataApplication extends android.app.Application implements Application.ActivityLifecycleCallbacks, androidx.lifecycle.DefaultLifecycleObserver` — a single Application-level class that also observes the process lifecycle (foreground/background), consistent with the Firebase Remote Config default flags recovered in `evidence` (`app_launched`, `app_closed`, `app_in_background`, `app_opened`) being driven from here.

## 2.5 Obfuscation — what's present and its impact
**Confirmed by direct inspection**: R8/ProGuard minification is enabled, but configured unusually:
- **Class and package names are fully preserved** — every class in `com.progoti.tallykhata.v2.*` keeps its original, readable name (`TallykhataApplication`, `ReportDao`, `MainActivity`, `TpWalletActivity`, …). This is almost certainly intentional, to keep Firebase Crashlytics stack traces and/or Room/Gson reflection-based lookups human-readable without needing a mapping file.
- **Method and field names are aggressively renamed** to short (1–2 character) identifiers. Example — `ReportDao`'s real interface surface is unrecoverable by name; structurally it has 26 methods, all renamed `a`, `b`, `c`, … `z`, each taking `(String, String)`-shaped parameters and returning `androidx.room.u` (an internal Room query-result type), e.g.:
  ```
  a(String, String) -> androidx.room.u
  b(String) -> androidx.room.u
  ...
  x(String) -> java.util.ArrayList
  ```
  Parameter/return **types** survive (they're part of the method signature table), but the semantic *name* of each query does not.

**Impact on this analysis:** package/class architecture, inheritance, DI wiring, and (via embedded strings) SQL schema and network hosts are all fully recoverable, as demonstrated throughout this project. Per-method business logic — *what calculation `ViewModel.q()` performs, what order of operations `arch.sync` uses to resolve conflicts, exact validation rules in the PIN/eKYC flow* — is **not** recoverable without a full bytecode decompiler (JADX), which was not available in this environment. See `09_technical_limitations.md`.

## 2.6 Third-party library inventory (by class count, app-relevant subset)
| Library | Classes | Role |
|---|---|---|
| Google Play Services (various) | 9,894 | Ads, Auth, Location, Measurement, FIDO, etc. |
| Google Common (Guava) | 1,223 | Utility library (transitive dep, likely via gRPC/Firestore) |
| Firebase | 844 | Analytics, Crashlytics, Messaging (FCM), Remote Config, Firestore, Installations |
| Jackson (`com.fasterxml.jackson`) | 824 | JSON (de)serialization |
| RxJava3 | 1,495 (810+685) | Reactive/async programming |
| CameraX (`androidx.camera.*`) | ~1,000 | Camera capture (QR scan, document/NID capture) |
| Stetho (`com.facebook.stetho`) | 519 | **Facebook's Chrome-DevTools debug bridge** — see security note in `08_security_permission_analysis.md` |
| Glide | 418 | Image loading |
| gRPC (`io.grpc`) | ~1,000 (651+356) | Used by Firestore |
| EMV QR parser (`com.emv.qrcode`) | 350 | Third-party library for EMVCo QR payment code parsing |
| Protobuf / Firestore / Google crypto | ~700 combined | Firestore + its crypto helpers |
| Lottie | 249 | Vector animation playback (the `.json` anim files in `res/raw`) |
| WorkManager (`androidx.work.impl`) | 278 | Background job scheduling |
| Apache Commons | 244 | Utility (validation/codec, typically transitive) |
| Hibernate Validator | 142 | Bean validation (likely transitive via a REST client stack) |
| ThreeTenABP | 183 | Date/time backport |
| ZXing | 143 | QR/barcode scanning |
| Retrofit2 / OkHttp3 / okio | 141 / 145 / 7 | HTTP networking (see Phase 4) |
| Gson | 84 | JSON (used alongside Jackson) |
| Facebook SDK (`com.facebook.*`, excl. Stetho) | ~500 | Facebook Login / sharing |
| AndroidX Security (`androidx.security`) | 15 | `EncryptedSharedPreferences`/`EncryptedFile` (Jetpack Security crypto) |

## 2.7 Evidence files for this phase
- `evidence/02_all_classes.json`, `evidence/02_package_inventory.txt`
- `evidence/03_app_classes.json`
- `evidence/04_app_submodules.txt`
