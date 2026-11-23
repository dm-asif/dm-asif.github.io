#!/usr/bin/env python3
import sys, json, collections
sys.path.insert(0, "/home/claude/tallykhata/scripts")
from axml import parse_axml, ANDROID_NS

data = open("/home/claude/tallykhata/work/extracted/AndroidManifest.xml", "rb").read()
events, sp, _ = parse_axml(data)

def A(attrs, name):
    for ns, n, v, t in attrs:
        if n == name: return v
    return None

M = {"manifest": {}, "uses_sdk": {}, "permissions": [], "declared_permissions": [], "features": [],
     "application": {}, "components": {"activity": [], "activity-alias": [], "service": [], "receiver": [], "provider": []},
     "queries": [], "meta_data": [], "uses_library": []}
stack = []; cur = None; cur_filter = None
pkg = None
for ev in events:
    kind, ns, tag, attrs, line = ev
    if kind == "start":
        stack.append(tag)
        parent = stack[-2] if len(stack) > 1 else None
        if tag == "manifest":
            M["manifest"] = {n: v for _, n, v, _ in attrs}; pkg = M["manifest"].get("package")
        elif tag == "uses-sdk": M["uses_sdk"] = {n: v for _, n, v, _ in attrs}
        elif tag in ("uses-permission", "uses-permission-sdk-23"):
            M["permissions"].append({"name": A(attrs, "name"), "maxSdk": A(attrs, "maxSdkVersion"), "tag": tag})
        elif tag == "permission":
            M["declared_permissions"].append({n: v for _, n, v, _ in attrs})
        elif tag == "uses-feature":
            M["features"].append({"name": A(attrs, "name"), "required": A(attrs, "required"), "glEsVersion": A(attrs, "glEsVersion")})
        elif tag == "application":
            M["application"] = {n: v for _, n, v, _ in attrs}
        elif tag in M["components"] and parent == "application":
            cur = {"name": A(attrs, "name"), "exported": A(attrs, "exported"), "permission": A(attrs, "permission"),
                   "enabled": A(attrs, "enabled"), "process": A(attrs, "process"), "launchMode": A(attrs, "launchMode"),
                   "authorities": A(attrs, "authorities"), "grantUriPermissions": A(attrs, "grantUriPermissions"),
                   "foregroundServiceType": A(attrs, "foregroundServiceType"),
                   "targetActivity": A(attrs, "targetActivity"),
                   "screenOrientation": A(attrs, "screenOrientation"), "filters": [], "meta": [], "kind": tag}
            M["components"][tag].append(cur)
        elif tag == "intent-filter" and cur is not None:
            cur_filter = {"actions": [], "categories": [], "data": [], "autoVerify": A(attrs, "autoVerify")}
            cur["filters"].append(cur_filter)
        elif tag == "action" and cur_filter is not None: cur_filter["actions"].append(A(attrs, "name"))
        elif tag == "category" and cur_filter is not None: cur_filter["categories"].append(A(attrs, "name"))
        elif tag == "data" and cur_filter is not None:
            cur_filter["data"].append({n: v for _, n, v, _ in attrs})
        elif tag == "meta-data":
            md = {"name": A(attrs, "name"), "value": A(attrs, "value"), "resource": A(attrs, "resource"), "parent": parent}
            if parent == "application": M["meta_data"].append(md)
            elif cur is not None: cur["meta"].append(md)
        elif tag == "uses-library":
            M["uses_library"].append({"name": A(attrs, "name"), "required": A(attrs, "required")})
        elif tag == "package" and parent == "queries": M["queries"].append(A(attrs, "name"))
    else:
        t = stack.pop()
        if t == "intent-filter": cur_filter = None
        if t in M["components"]: cur = None

# derived
for kind, lst in M["components"].items():
    for c in lst:
        if c["exported"] is None:
            c["exported_effective"] = "true(implicit: has intent-filter)" if c["filters"] else "false(default)"
        else: c["exported_effective"] = c["exported"]
        n = c["name"] or ""
        if n.startswith("."): n = pkg + n
        c["fqcn"] = n
        c["origin"] = "app" if n.startswith("com.progoti") or n.startswith("com.tallykhata") else "3rd-party/lib"

json.dump(M, open("/home/claude/tallykhata/evidence/01_manifest_parsed.json", "w"), indent=1)

# ---- text summary ----
out = []
P = out.append
P("MANIFEST SUMMARY (decoded from AndroidManifest.xml, %d bytes)" % len(data))
P("package=%s versionCode=%s versionName=%s compileSdk=%s" % (pkg, M["manifest"].get("versionCode"), M["manifest"].get("versionName"), M["manifest"].get("compileSdkVersion")))
P("minSdk=%s targetSdk=%s" % (M["uses_sdk"].get("minSdkVersion"), M["uses_sdk"].get("targetSdkVersion")))
P("")
P("APPLICATION ATTRS:")
for k, v in M["application"].items(): P("  %s = %s" % (k, v))
P("")
P("USES-PERMISSION (%d):" % len(M["permissions"]))
for p in M["permissions"]: P("  %s%s" % (p["name"], (" [maxSdk=%s]" % p["maxSdk"]) if p["maxSdk"] else ""))
P("")
P("DECLARED PERMISSIONS (%d):" % len(M["declared_permissions"]))
for p in M["declared_permissions"]: P("  %s" % p)
P("")
P("USES-FEATURE (%d):" % len(M["features"]))
for f in M["features"]: P("  %s required=%s %s" % (f["name"], f["required"], f["glEsVersion"] or ""))
P("")
for kind, lst in M["components"].items():
    P("%s (%d total; app-origin=%d)" % (kind.upper(), len(lst), sum(1 for c in lst if c["origin"] == "app")))
P("")
for kind in ("activity", "activity-alias", "service", "receiver", "provider"):
    P("=== %s ===" % kind.upper())
    for c in M["components"][kind]:
        extra = []
        if c["permission"]: extra.append("perm=%s" % c["permission"])
        if c["authorities"]: extra.append("auth=%s" % c["authorities"])
        if c["foregroundServiceType"]: extra.append("fgsType=%s" % c["foregroundServiceType"])
        if c["launchMode"]: extra.append("launch=%s" % c["launchMode"])
        if c["process"]: extra.append("proc=%s" % c["process"])
        if c["targetActivity"]: extra.append("target=%s" % c["targetActivity"])
        P("  [%s] %s exported=%s %s" % (c["origin"], c["fqcn"], c["exported_effective"], " ".join(extra)))
        for f in c["filters"]:
            d = ",".join(("%s://%s%s%s" % (x.get("scheme", "*"), x.get("host", "*"), x.get("pathPrefix", x.get("path", "")), "")) for x in f["data"])
            P("      filter: actions=%s cats=%s data=%s" % (f["actions"], [x.split(".")[-1] for x in f["categories"]], d))
    P("")
P("APPLICATION META-DATA (%d):" % len(M["meta_data"]))
for m in M["meta_data"]: P("  %s = %s %s" % (m["name"], m["value"], ("res=" + m["resource"]) if m["resource"] else ""))
P("")
P("QUERIES packages: %s" % M["queries"])
P("USES-LIBRARY: %s" % M["uses_library"])
open("/home/claude/tallykhata/evidence/01_manifest_summary.txt", "w").write("\n".join(out))
print("\n".join(out[:70]))
