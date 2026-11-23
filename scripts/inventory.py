#!/usr/bin/env python3
import sys, json, collections, glob
sys.path.insert(0, "/home/claude/tallykhata/scripts")
from dexparse import Dex

ROOT = "/home/claude/tallykhata"
dex_files = sorted(glob.glob(ROOT + "/work/extracted/classes*.dex"))

APP_PREFIXES = ("com.progoti.", "com.tallykhata.")

all_classes = []
per_dex_counts = {}
for path in dex_files:
    d = Dex(path)
    per_dex_counts[path.split("/")[-1]] = len(d.classes)
    for c in d.classes:
        s = d.class_summary(c)
        s["dex"] = path.split("/")[-1]
        all_classes.append(s)

print("DEX class counts:", per_dex_counts, "total:", len(all_classes))

# top-level package grouping (2-3 segments) to identify libraries
pkg_counts = collections.Counter()
app_pkg_counts = collections.Counter()
for c in all_classes:
    cn = c["class"] or ""
    parts = cn.split(".")
    top = ".".join(parts[:3]) if len(parts) >= 3 else cn
    pkg_counts[top] += 1
    if cn.startswith(APP_PREFIXES):
        app_pkg = ".".join(parts[:4]) if len(parts) >= 4 else cn
        app_pkg_counts[app_pkg] += 1

json.dump(all_classes, open(ROOT + "/evidence/02_all_classes.json", "w"))

with open(ROOT + "/evidence/02_package_inventory.txt", "w") as f:
    f.write("DEX class counts: %s total=%d\n\n" % (per_dex_counts, len(all_classes)))
    f.write("=== Top (3-segment) package clusters by class count (all code, app+library) ===\n")
    for p, c in pkg_counts.most_common(120):
        f.write("%6d  %s\n" % (c, p))
    f.write("\n=== App package clusters (com.progoti.* / com.tallykhata.*), 4-segment ===\n")
    for p, c in sorted(app_pkg_counts.items(), key=lambda x: -x[1]):
        f.write("%6d  %s\n" % (c, p))

app_classes = [c for c in all_classes if (c["class"] or "").startswith(APP_PREFIXES)]
json.dump(app_classes, open(ROOT + "/evidence/03_app_classes.json", "w"))
print("app classes:", len(app_classes))
print("distinct app packages (4-seg):", len(app_pkg_counts))
