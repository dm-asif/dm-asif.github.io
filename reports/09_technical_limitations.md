# Phase 6 (cont.) — Technical Limitations and Unrecoverable Components

This document exists so that every claim in reports `01`–`08` can be correctly weighted: what was **directly read from the APK's bytes** (high confidence), what was **inferred from naming/structure** (reasonable but not certain), and what simply **could not be recovered at all** in this environment.

## 9.1 Environment constraints that shaped this analysis
- **No network access.** `git clone`, `pip install`, and any outbound connection all failed with DNS resolution errors at the OS level. The requested reference repo (`github.com/morluto/rea`) could not be fetched or consulted. No standard RE tool (JADX, apktool, aapt2, androguard, radare2/r2, dex2jar, Ghidra) was pre-installed and none could be downloaded.
- **Response:** rather than skip the phases that normally depend on those tools, I wrote minimal, purpose-built parsers from scratch (`scripts/axml.py` for Android Binary XML, `scripts/dexparse.py` for the DEX file format, `scripts/arsc.py` for the compiled resource table) and validated each against the real APK before trusting its output (e.g., confirming the AXML parser round-trips a human-readable manifest, confirming the DEX parser's class/string/method counts are internally consistent, confirming the ARSC parser's package/type-pool names are real, legitimate Android resource type names before using it further).

## 9.2 What IS fully recovered (high confidence, direct evidence)
- Complete `AndroidManifest.xml` content: permissions, all 250 components (activities/services/receivers/providers), intent-filters, meta-data — this is a lossless binary→readable decode, not an approximation.
- Complete class/package architecture: every one of 34,774 classes across 4 DEX files, with accurate superclass, implemented-interfaces, and full method **signatures** (name, parameter types, return type) and field **types**. This is also effectively lossless for structure (DEX's type/method/field tables are simple, well-defined, and not obfuscation-resistant).
- All literal strings embedded in the app, including the **full Room-generated SQL schema** (32 tables, verbatim DDL) and **54 hardcoded URLs/hosts** — string *contents* cannot be hidden by ProGuard/R8 identifier renaming, so this channel was reliably mined.
- Signing certificate metadata (public, standard X.509 fields).
- Native library file inventory (which `.so` files exist, for which ABIs) via filenames/sizes; **not** disassembled.

## 9.3 What is PARTIALLY recovered / inferred (reasonable confidence, not certainty)
- **Feature/module purpose**: inferred from class and package *names* (e.g. `CashBoxDialogCallback`, `TpWalletRegistrationActivity`) cross-referenced with their position in the manifest/DB schema. Names are a strong signal (they are NOT obfuscated in this build — see Phase 2 §2.5) but describing *exactly* what a screen or class does beyond what its name suggests is inference, flagged as such throughout with words like "inferred," "likely," "suggests."
- **Screen navigation graphs** (Phase 5, `07_app_flow_diagrams.md`): built from activity grouping/naming conventions, not from actual `startActivity()` call-site analysis. The real navigation graph could differ in edge cases.
- **DAO-to-table mapping** (`04_database_schema.md §3.4`): inferred from DAO class names matching table names; Room allows a DAO to touch multiple tables via joins, so this is a best-effort mapping, not a verified one.
- **Resource-ID-backed config values**: a handful of `<meta-data>` entries point at `@resource` IDs (e.g. the SureCash base URL, Facebook App ID/Client Token) rather than literal strings. The custom ARSC parser (`scripts/arsc.py`) correctly reads the package/type/key string pools and outer package header, but on attempting to decode individual `ResTable_type` entry chunks to resolve a specific numeric ID to its value, **the chunk header layout encountered did not match the classic/documented AOSP `ResTable_type` struct** (manually verified by inspecting raw bytes: the observed `headerSize` field — 16 bytes — was smaller than the struct I had implemented would predict, consistent with a newer/compact AAPT2 encoding variant this project did not have reference documentation for). Rather than guess and risk reporting a fabricated resolved value, **these resource references are left unresolved** in the reports above, explicitly marked as such. This is recoverable with `aapt2 dump resources resources.arsc` or `apktool`, neither available here.

## 9.4 What is NOT recovered at all
- **Method bodies / bytecode-level logic.** This is the single biggest limitation. The DEX parser used here reads the *structural* tables (classes, methods, fields, strings) but does **not** disassemble Dalvik bytecode instructions. Consequently, none of the following were possible:
  - Control flow, algorithms, validation rules, business calculations (e.g. exactly how interest/fees/limits are computed, exact PIN-retry-lockout logic, exact eKYC face-match threshold).
  - Confirming whether a given library is actually *invoked* at runtime versus merely present as a compiled-in dependency (e.g., the Stetho debug-bridge concern in `08_security_permission_analysis.md §6.5` — its presence is confirmed, its activation is not).
  - Cross-references / call graphs (which class calls which — e.g., confirming which of the 3 OkHttp interceptors does what).
  - Room `@Query` SQL text (only `CREATE TABLE`/migration DDL survives as a literal string in generated code; `SELECT`/`UPDATE` query text is consumed by the annotation processor at compile time and is not re-emitted as a runtime string constant).
  - Exact JSON field names for request/response DTOs (Gson's field↔JSON key mapping, and any `@SerializedName` overrides, live in annotation data this project's parser does not decode).

  **Why not fixed:** implementing a correct Dalvik bytecode disassembler from memory, without network access to verify the ~200-entry opcode format table against an authoritative reference, carries meaningful risk of silent, hard-to-detect errors that could produce *confidently wrong* "recovered logic" — which would be worse than clearly stating the limitation. A real decompiler (JADX) is the appropriate tool for this; it was not available in this sandbox.
- **Full ARSC value resolution** (see §9.3) — type/key names recoverable, specific values for `@reference`-style meta-data not resolved.
- **Per-locale resource variants beyond `bn`/`en`** — confirmed via Play's `splits0.xml` language-split list, but the deeper claim of exactly *which* strings differ per locale (not generally relevant to this architecture-focused report) was not pursued.
- **Native `.so` internals** — confirmed as stock Google ML Kit/CameraX binaries by filename and size; not disassembled (no custom app logic is expected to live there, so this was deprioritized rather than impossible).
- **Any dynamic/runtime behavior** — no emulator, no Frida, no network capture, no live backend interaction of any kind occurred. Everything in Phase 4 (API architecture) is what the client is *configured* to talk to, not what it actually sends/receives at runtime, nor confirmation that any listed endpoint is still live or behaves as its name suggests.
- **The exported-activity question in `08_security_permission_analysis.md §6.2`** — whether the 24 unusually-exported activities are actually reachable/exploitable by a third-party app was explicitly *not* tested (would require installing and running a second "attacker" app against the live installed TallyKhata app — dynamic testing, out of scope and not possible in this static sandbox) and *not* confirmed via decompilation (would require seeing whether each activity's `onCreate` independently re-checks the user's session/PIN).
- **User/customer data** — by design, not pursued at all (no `.db` file exists in the APK to extract from in the first place; Room creates the database on-device at first run).

## 9.5 Tooling produced for this project (for reproducibility / handoff)
| Script | Purpose |
|---|---|
| `scripts/axml.py` | Generic Android Binary XML → readable XML decoder (manifest + any compiled `res/xml`, `res/layout`, etc.) |
| `scripts/dexparse.py` | DEX file structural parser (strings/types/protos/fields/methods/classes, no bytecode) |
| `scripts/inventory.py` | Aggregates class data across all 4 DEX files, splits app vs. library code |
| `scripts/manifest_analyze.py` | Structured manifest → JSON + human-readable summary |
| `scripts/arsc.py` | Partial `resources.arsc` reader (package/type/key string pools; per-entry value resolution incomplete, see §9.3) |

A future pass with JADX/apktool available (e.g. running this same project inside Claude Code or another environment with network/tool access) could close essentially every gap listed in §9.4 except the "dynamic/runtime behavior" and "exported-activity exploitability" items, which inherently require dynamic testing against a running instance of the app — explicitly out of scope for this static-analysis engagement.
