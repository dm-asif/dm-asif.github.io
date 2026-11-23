# Phase 3 — Database Schema Documentation

## 3.1 Technology
**Room** (AndroidX's SQLite ORM) over local **SQLite**, confirmed directly by class inheritance: `com.progoti.tallykhata.v2.arch.persistence.TallyKhataDatabase extends androidx.room.RoomDatabase`, with a compiler-generated `TallyKhataDatabase_Impl` and **18 anonymous `Migration` subclasses** (`TallyKhataDatabase$a` through `$v`), indicating at least 18 shipped schema migrations over the app's lifetime. 24 `@Dao`-pattern interfaces sit on top of the 32 tables (one DAO sometimes covers more than one related table).

**Method of recovery:** Room's annotation processor bakes the exact `CREATE TABLE` SQL for every entity, as a literal string, into the generated `*_Impl` classes (used at `onCreate`/migration time). Because R8 obfuscates identifiers but **cannot rewrite string-literal contents**, these full DDL statements survive intact in the DEX string pool and were recovered verbatim by scanning all 3 app DEX files for strings beginning `CREATE TABLE`. **This is schema structure only — no row data, because the APK does not ship a populated database file; Room creates an empty DB on first app run on-device.** No personal/customer data of any kind was extracted or is present in this analysis.

89 raw `CREATE TABLE` strings were found; 7 belong to AndroidX WorkManager's internal job-queue tables (`WorkSpec`, `WorkTag`, `WorkName`, `Dependency`, `Preference`, `SystemIdInfo`, `WorkProgress` — infrastructure, not app data) and are excluded below. The remaining 82 strings collapse to **32 distinct application tables** (most tables have 2 recovered variants, representing before/after a migration — the most complete/recent variant is shown).

## 3.2 Entity-relationship summary
| Table | Cols | Primary Key | Foreign Keys |
|---|---|---|---|
| `account` | 17 | id | — |
| `account_media` | 9 | id | account_id → account.id |
| `cash_sales` | 4 | _id | — |
| `cashbox_adjustment` | 6 | id | journal_id → journal.id |
| `closing_balance` | 7 | id | — |
| `costs` | 5 | _id | — |
| `credit_collection_adjustment` | 9 | id | journal_id → journal.id |
| `credit_collection_adjustment_backup` | 8 | id | journal_id → journal.id |
| `credits` | 7 | _id | customer → customers.id |
| `customers` | 6 | _id | — |
| `digital_sales` | 8 | _id | — |
| `digital_transaction` | 17 | id | journal_id → journal.id; account_id → account.id |
| `dynamic_form` | 10 | id | — |
| `dynamic_form_answer` | 10 | id | — |
| `event_logger` | 6 | id | — |
| `file_upload_history` | 12 | id | — |
| `gallery_media` | 7 | id | — |
| `inbox_message` | 22 | id | — |
| `journal` | 15 | id | orig_account_id → account.id |
| `journal_media` | 8 | id | journal_id → journal.id |
| `ledger` | 9 | id | journal_id → journal.id; account_id → account.id |
| `locations` | 7 | _id | — |
| `log` | 8 | id | — |
| `opening_balance` | 6 | id | — |
| `popup_message` | 25 | id | — |
| `recharge_packages` | 28 | (none declared) | — |
| `reconciliations` | 7 | _id | — |
| `supplier_payment_adjustment` | 13 | id | journal_id → journal.id |
| `suppliers` | 6 | _id | — |
| `supplies` | 10 | _id | supplier → suppliers.id |
| `tagada_log` | 6 | id | account_id → account.id |
| `transaction_settlement_action` | 6 | id | — |

**Core domain model** (inferred from table/column names — this is "TallyKhata," literally "tally ledger" in Bengali/Hindi, a bookkeeping app for small merchants):
- `account` is the central entity — a customer or supplier ledger account (`type` column distinguishes them; `start_balance`, `contact`, `ac_date`). `account_media` stores a photo per account (`is_profile` flag).
- `journal` is the core double-entry-style transaction record, referencing `orig_account_id`; `ledger` and `cashbox_adjustment`/`credit_collection_adjustment`/`supplier_payment_adjustment` all hang off a `journal_id`, forming a transaction + adjustments/settlements pattern. `journal_media` attaches receipt photos to a journal entry.
- `customers` / `suppliers` are simpler, separate legacy-looking tables (older `_id` integer PK convention, vs. the newer `id` convention used by `account` — consistent with the 18 recorded migrations gradually consolidating the model).
- `cash_sales`, `costs`, `digital_sales`, `digital_transaction`, `supplies` are transaction-type-specific tables.
- `opening_balance` / `closing_balance` — daily cash-register open/close balances (ties to the "CashBox" feature module).
- `dynamic_form` / `dynamic_form_answer` — a generic, server-driven dynamic-form system (likely used for eKYC or merchant-onboarding data collection without needing an app update per field change).
- `inbox_message` / `popup_message` — in-app messaging/notification-center tables (22 and 25 columns respectively — the largest non-transactional tables, suggesting rich rendering metadata e.g. deep-links, images, CTAs).
- `recharge_packages` (28 columns, no declared PK — likely a reference/lookup table for TallyPay mobile-recharge SKUs, refreshed by `RechargePackageFetchWorker`, see `02_application_architecture.md`).
- `tagada_log`, `event_logger`, `log` — telemetry/audit-trail tables.
- `locations` — presumably ties to the `ACCESS_FINE_LOCATION`/`ACCESS_COARSE_LOCATION` permissions (see Phase 6).
- `file_upload_history`, `gallery_media` — generic media-upload bookkeeping, used across eKYC document upload and receipt-photo features.

**Recurring columns across almost every table** — `synced` (INTEGER), `is_updated` (INTEGER, `DEFAULT 0`), `last_update_date`, `server_id`, `synced_date`, `create_date` — confirm the **local-first / background-sync architecture** described in `02_application_architecture.md`: every row is written locally first and carries its own sync-state flags for the WorkManager-driven background sync to reconcile against the server (`server_id` is the server-assigned identifier once synced; the local `id`/`_id` is a separate autoincrement local key).

## 3.3 Full recovered DDL
The complete, verbatim `CREATE TABLE` statements (all migration variants) are in `evidence/06_recovered_schema.sql.txt`. Representative examples:

```sql
CREATE TABLE IF NOT EXISTS `account` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT NOT NULL, `contact` TEXT NOT NULL,
  `type` INTEGER NOT NULL, `ac_date` TEXT NOT NULL, `start_balance` REAL NOT NULL,
  `description` TEXT, `create_date` TEXT NOT NULL, `synced` INTEGER NOT NULL,
  `share_link` TEXT, `last_share_media` TEXT, `is_updated` INTEGER NOT NULL DEFAULT 0,
  `last_update_date` TEXT, `is_active` INTEGER NOT NULL DEFAULT 1, `server_id` INTEGER,
  `synced_date` TEXT, `report_visibility` INTEGER NOT NULL DEFAULT 1
)

CREATE TABLE IF NOT EXISTS `journal` ( /* see evidence file for full 15-column DDL incl. orig_account_id FK */ )

CREATE TABLE IF NOT EXISTS `digital_transaction` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT, /* 17 columns total */
  FOREIGN KEY(`journal_id`) REFERENCES `journal`(`id`) ...,
  FOREIGN KEY(`account_id`) REFERENCES `account`(`id`) ...
)
```

## 3.4 DAO ↔ table mapping (structural)
| DAO interface | Likely table(s) |
|---|---|
| `CashBoxAdjustmentDao` | `cashbox_adjustment` |
| `CashSaleDao` | `cash_sales` |
| `ClosingBalanceDao` / `OpeningBalanceDao` | `closing_balance` / `opening_balance` |
| `CostDao` | `costs` |
| `CreditCollectionAdjustmentDao` | `credit_collection_adjustment`(`_backup`) |
| `CreditDao` | `credits` |
| `CustomerDao` | `customers` |
| `DigitalSaleDao` / `DigitalTransactionDao` | `digital_sales` / `digital_transaction` |
| `DynamicFormDao` / `DynamicFormAnswersDao` | `dynamic_form` / `dynamic_form_answer` |
| `EventLoggerDao` | `event_logger` |
| `FileUploadHistoryDao` | `file_upload_history` |
| `InboxMessageDao` | `inbox_message` |
| `LedgerDao` | `ledger` |
| `LocationDao` | `locations` |
| `LogDao` | `log` |
| `PopupMessageDao` | `popup_message` |
| `ReconciliationDao` | `reconciliations` |
| `ReportDao` | cross-table read queries (26 methods — reporting/aggregation layer over multiple tables) |
| `SupplierDao` / `SupplyDao` / `SupplierPaymentAdjustmentDao` | `suppliers` / `supplies` / `supplier_payment_adjustment` |
| `TagadaLogDao` | `tagada_log` |
| `TransactionSettlementActionDao` | `transaction_settlement_action` |
| `BaseDao` | generic shared insert/update/delete base (3 methods) |

Individual query semantics (the actual `@Query` SQL for `SELECT`/`UPDATE` operations, as opposed to the DDL) are **not** recoverable this way — Room only embeds literal `CREATE TABLE`/migration SQL in generated code as plain strings; `@Query` annotation values are consumed at compile time to generate bytecode, not re-emitted as a string constant, so they are invisible to string-pool scanning and would require full method-body decompilation (see `09_technical_limitations.md`).

## 3.5 Evidence files
- `evidence/05_room_create_table_statements.txt` — raw, as-found strings (89 total, incl. WorkManager)
- `evidence/06_recovered_schema.sql.txt` — deduplicated, app-table-only, grouped by table (32 tables)
