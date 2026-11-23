# TallyKhata APK — Static Analysis Project

**Target:** `com_progoti_tallykhata_8df4df89.apk` (package `com.progoti.tallykhata`, versionName 6.6.1, versionCode 171)
**Analysis date:** 2026-11-03
**Analyst role:** Static reverse-engineering / mobile security research (read-only)

## Scope and method
This is a **static-only** analysis performed entirely offline (this sandbox has no network egress, confirmed — `git clone`, `pip install` to PyPI, and any outbound host connection all fail with DNS resolution errors). No dynamic analysis (emulator run, Frida, network capture against the live backend) was performed or possible in this environment, so "Phase 2 dynamic" style runtime verification is **not** part of this report; all findings below are derived from the bytes inside the APK itself. No live TallyKhata/Nobopay backend was contacted at any point.

Standard RE tools (JADX, apktool, aapt2, androguard, radare2) were **not installed** in this sandbox and could not be fetched (no network). Rather than skip Phases 2–4, I wrote small, purpose-built, from-scratch parsers (in `scripts/`) for the exact binary formats involved — Android Binary XML (AXML), the DEX file format, and (partially) the ARSC resource table — and used them directly against the APK's own bytes. Every artifact in `evidence/` is generated output from these scripts run against the uploaded APK; nothing below is from training-data memory of "what TallyKhata probably does."

## What was / wasn't done, per the request's guardrails
- The original APK was never modified. All work happened on an extracted **copy** in `work/extracted/`.
- No authentication, PIN, payment, or subscription/premium check was bypassed or patched. No code was patched at all — this is read-only inspection.
- No cracked/modified APK was produced.
- No user/customer data was extracted. The SQLite schema in Phase 3 is **table structure (DDL) only**, recovered from Room's generated SQL strings — no app was run and no `.db` file with real records exists in this APK (databases are created at first run on a device, not shipped inside the APK).
- No backend endpoint was called, probed, or fuzzed. Phase 4's findings are the **literal URL/host strings** embedded in the app's code, nothing more.

## Directory layout
```
tallykhata/
├── evidence/     — raw machine-generated extraction output (JSON, txt, decoded XML, SQL)
├── reports/      — the 9 human-readable deliverables requested, plus this README
├── diagrams/     — Mermaid flow diagrams
├── scripts/      — the custom AXML/DEX/ARSC parsers used to produce evidence/
└── work/extracted/ — unmodified copy of the APK's unzipped contents (read-only reference)
```

## Report index
1. `01_apk_analysis_report.md` – Phase 1: structure, manifest, permissions, components, signing
2. `02_application_architecture.md` – Phase 2: code/module architecture, obfuscation
3. `03_package_class_structure.md` – Phase 2: package & class inventory detail
4. `04_database_schema.md` – Phase 3: recovered Room/SQLite schema
5. `05_api_network_architecture.md` – Phase 4: networking stack & endpoints
6. `06_ui_ux_screen_inventory.md` – Phase 5: screens & components
7. `07_app_flow_diagrams.md` – Phase 5: Mermaid flow diagrams
8. `08_security_permission_analysis.md` – Phase 6: security & permissions
9. `09_technical_limitations.md` – Phase 6: what could not be recovered, and why
