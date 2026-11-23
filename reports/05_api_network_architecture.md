# Phase 4 — API / Network Architecture Report

**Method:** literal URL/host strings embedded in the DEX string pools (`scripts/dexparse.py` string scan, filtered to well-formed `http(s)://` strings), cross-referenced against the `apimanager` package's class/interface structure (`03_package_class_structure.md §3.2`) and the manifest's `<meta-data>` block. **No request was made to any of these hosts** — this is a static inventory of what the client is configured to talk to, not a live probe.

## 4.1 Networking stack (confirmed by class presence)
| Layer | Library | Evidence |
|---|---|---|
| HTTP client | OkHttp3 (145 classes) | `okhttp3.*` package present; 3 app classes implement `okhttp3.Interceptor` |
| REST client | Retrofit2 (141 classes) | `retrofit2.*` present; 1 app class implements `retrofit2.Callback` |
| JSON | Gson (84 classes) **and** Jackson (824 classes) | Both present — Gson appears to be the app's primary serializer (5 custom `JsonDeserializer` implementations in `apimanager`); Jackson is very likely a transitive dependency of Firebase/Firestore/gRPC rather than directly used by app code |
| Async | RxJava3 (1,495 classes combined) | 1 app class in `apimanager` implements `io.reactivex.rxjava3.functions.Function` (Retrofit+RxJava adapter pattern) |
| Realtime/Cloud DB | Firebase Firestore (gRPC-backed, 102+651 classes) | Present; usage within app code not separately confirmed beyond the dependency being bundled |
| Push | Firebase Cloud Messaging | `PushNotificationMessageService extends FirebaseMessagingService` |

## 4.2 App-level HTTP client wiring (`com.progoti.tallykhata.v2.apimanager`)
- `ApiCaller`, `ApiService`, `TCApiService` — Retrofit service-definition/wrapper classes.
- `ApiResponseHandler`, `ResponseHeaderHandler` — response post-processing.
- Custom exception hierarchy: `ApiCallFailedException` → `ApiNotRecheableException`, `InvalidAPIResponse`.
- **3 OkHttp `Interceptor` implementations** — typical purposes (auth header injection, logging, retry) could not be confirmed without method-body decompilation.
- **5 Gson `JsonDeserializer` implementations** — typically custom date/decimal/enum handling.
- ~34 request/response DTOs, e.g. `LoginDto`, `LoginResponseDto` (Parcelable), `OTPDetailsDto` (Parcelable), `AuthInitializationDto`, `AuthVerificationDto`, `ProfileInfoDto`/`ProfileV2Dto`, `FaceMatchRequestDto` (eKYC selfie match), `FileUploadResponseDto`, `NumberChangeConfirmRequest/Response`, `PromoDto`, `SendSmsDto/Response`, `TagadaMessageRequestDto`/`TagadaMessageContentResponseDto`/`TagadaMessageSMSResponseDto`, `TagadaQuotaInfoResponseDto`/`TagadaQuotaRequestDto`, `TokenRegistrationDto/ResponseDto`, `Wallet`, `MigrationResultDto/ResponseDto`, `LoanStatusDto`.

This DTO list, read together, sketches the backend API surface fairly clearly: **login/OTP auth, eKYC face-match verification, phone-number change with OTP confirmation, promo/referral content, SMS-credit purchase ("BuySms"), "Tagada" SMS messaging quota/send, FCM token registration, wallet balance, data-migration status, and loan status** are all backed by dedicated REST calls.

## 4.3 Backend hosts/endpoints found as literal strings
All 54 literal `http(s)://` strings found across the 3 app DEX files are listed in `evidence/07_urls_found.txt`. Grouped by host:

### TallyKhata / own backend
| URL | Notes |
|---|---|
| `https://app.tallykhata.com` | Primary app-facing domain (bare host; path(s) built at runtime, not visible as a literal string) |
| `https://web.tallykhata.com/` | |
| `https://web.tallykhata.com/payment/api/create-payment` | Payment flow endpoint |
| `https://web.tallykhata.com/payment/api/execute-payment` | Payment flow endpoint |
| `https://web.tallykhata.com/payment/api/query-payment` | Payment status-query endpoint |
| `https://www.tallykhata.com/` , `/bn/faq-app`, `/bn/help-app`, `/bn/tk_terms.html` | Marketing/help site, Bengali-language help pages opened in-app |
| `https://upms.tallykhata.com` | A separate subdomain — name suggests "User/Profile Management Service"; purpose not confirmable beyond the bare host string |

### TallyPay payment-gateway ("Nobopay")
| URL | Notes |
|---|---|
| `https://npapigwnew.nobopay.com/` | Base host — **"Nobopay"** is confirmed (via `tallypay.nobopayDataModel`, the largest single sub-package of the `tallypay` module at 273 classes) as the third-party payment-gateway processor behind TallyPay |
| `https://npapigwnew.nobopay.com/api/v1/` , `/api/v2/` | Two concurrent API versions in use |
| `https://npapigwnew.nobopay.com//api/payment/create/order/` | Order-creation (note: literal double-slash in the string as embedded — a likely base-URL + relative-path concatenation artifact, not a transcription error here) |
| `https://npapigwnew.nobopay.com//api/payment/dbbl/create-txn/` | **DBBL** = Dutch-Bangla Bank Limited — bank-specific transaction creation |
| `https://npapigwnew.nobopay.com//api/payment/nagad/checkout/` | **Nagad** (Bangladesh Post Office's mobile financial service) checkout |
| `https://npapigwnew.nobopay.com/static-doc/` | Static document host (likely T&Cs/receipts) |
| ⚠️ `http://gw.staging.nobopay.com/api/v1/` | **A staging/non-production gateway URL, over plain HTTP, left in this production build.** See `08_security_permission_analysis.md` §6.5. |
| `https://tallypay.net/bn/tariff-limits` , `/bn/tp_terms.html` | TallyPay's own marketing/terms microsite |

### SureCash SDK (embedded payment SDK, `com.progoti.surecash.*`)
Per `AndroidManifest.xml` `<meta-data>`:
```
com.surecash.sdk.api_base_url = @0x7f120934   (resource reference; literal value not resolved — see §4.4/limitations)
surecash-client-name          = Uthao
surecash-client-id            = uthao
surecash-client-key           = abcd457865938sdjhf   (hardcoded literal string, in the manifest itself)
```
⚠️ The **`surecash-client-key` is a hardcoded literal value directly in `AndroidManifest.xml`**, not a resource reference like the others — see security note in `08_security_permission_analysis.md` §6.4.

### Third-party SDK endpoints (Ads / Analytics / Social — not app-specific)
`googleads.g.doubleclick.net` (AdMob ad-serving, several static asset URLs for MRAID/native-ad templates), `www.googleapis.com` (OAuth scopes), `app-measurement.com` (Firebase Analytics), `firebaseinstallations.googleapis.com`, `mobilemlaccelerationcompatibility.googleapis.com` (ML Kit), `admob-gmats.uc.r.appspot.com`, `csi.gstatic.com`, `imasdk.googleapis.com` (IMA video ads), `facebook.com`/`.facebook.com` (Facebook SDK/Login), `www.bkash.com/terms-and-conditions`, `www.youtube.com`, `youtu.be` — all standard SDK-internal endpoints for the bundled Google/Facebook/bKash libraries, not TallyKhata-authored.

## 4.4 What could not be resolved
- Several `<meta-data>` and layout attribute values point at **compiled resource IDs** (e.g. `@0x7f120934` for the SureCash base URL, `@0x7f1203bb`/`@0x7f1203bc` for the Facebook App ID/Client Token) rather than literal strings. A resources.arsc parser was written (`scripts/arsc.py`) and successfully extracts the package/type/key string pools (confirmed: type list includes `string`, 13,337 total resource entries), but **per-entry value resolution (mapping a specific numeric ID to its string value) hit an undocumented/newer AAPT2 chunk-layout variant this project's lightweight parser could not reliably decode** (verified by manual byte inspection — the `ResTable_type` header size did not match the classic AOSP struct layout). Rather than report a guessed value, this was left unresolved; see `09_technical_limitations.md`. It can be resolved with `aapt2 dump resources` or `apktool`, neither of which was installable in this offline sandbox.
- Exact request/response JSON payload shapes are only as detailed as the DTO class's declared fields would show under full decompilation; this project recovered DTO **class names** (above) but not their field lists, since (unlike Room's SQL) Gson's field↔JSON-key mapping is resolved via reflection over obfuscated field names at runtime, with no equivalent literal-string giveaway. `@SerializedName` annotation values, if present, are stored in the DEX's annotation tables, which this project's parser does not decode (noted in limitations).
- Whether the 3 OkHttp interceptors do auth, logging, or something else; whether TLS certificate pinning is implemented in code (no literal `sha256/...` app-specific pin hash was found — only OkHttp's own `CertificatePinner` library format-string template, confirming the *capability* exists in the dependency but not that the app configured any pins).

## 4.5 Evidence files
- `evidence/07_urls_found.txt` — all 54 literal URLs
- `evidence/01_manifest_summary.txt` — meta-data block
