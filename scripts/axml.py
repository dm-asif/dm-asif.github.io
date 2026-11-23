#!/usr/bin/env python3
"""Minimal Android binary XML (AXML) decoder. No third-party deps.
Parses chunk types: STRING_POOL (0x0001), XML (0x0003), RESOURCE_MAP (0x0180),
START_NS/END_NS (0x100/0x101), START_ELEMENT (0x102), END_ELEMENT (0x103), CDATA (0x104).
"""
import struct, sys

ANDROID_NS = "http://schemas.android.com/apk/res/android"

# NOTE: attribute names are taken from the AXML string pool only (no guessed ID table).
FRAMEWORK_ATTRS = {}


class StringPool:
    def __init__(self, data, off):
        (self.type, self.hsize, self.size, self.count, self.style_count,
         self.flags, self.str_start, self.style_start) = struct.unpack_from("<HHIIIIII", data, off)
        self.utf8 = bool(self.flags & 0x100)
        offs = struct.unpack_from("<%dI" % self.count, data, off + self.hsize)
        base = off + self.str_start
        self.strings = []
        for o in offs:
            self.strings.append(self._read(data, base + o))

    def _read(self, data, p):
        if self.utf8:
            # utf16 length (ignored), utf8 length
            n = data[p]; p += 1
            if n & 0x80: p += 1
            m = data[p]; p += 1
            if m & 0x80:
                m = ((m & 0x7f) << 8) | data[p]; p += 1
            return data[p:p + m].decode("utf-8", "replace")
        else:
            n = struct.unpack_from("<H", data, p)[0]; p += 2
            if n & 0x8000:
                n = ((n & 0x7fff) << 16) | struct.unpack_from("<H", data, p)[0]; p += 2
            return data[p:p + n * 2].decode("utf-16le", "replace")

    def __getitem__(self, i):
        if i == 0xFFFFFFFF or i >= len(self.strings): return None
        return self.strings[i]


TYPE_NAMES = {0x00: "null", 0x01: "ref", 0x02: "attr", 0x03: "string", 0x04: "float",
              0x05: "dimension", 0x06: "fraction", 0x10: "int", 0x11: "hex", 0x12: "bool",
              0x1c: "color", 0x1d: "color", 0x1e: "color", 0x1f: "color"}


def fmt_value(sp, vtype, vdata, raw):
    if raw is not None and raw != 0xFFFFFFFF:
        s = sp[raw]
        if s is not None: return s
    if vtype == 0x03: return sp[vdata]
    if vtype == 0x12: return "true" if vdata else "false"
    if vtype == 0x10: return str(struct.unpack("<i", struct.pack("<I", vdata))[0])
    if vtype == 0x11: return "0x%x" % vdata
    if vtype == 0x01: return "@0x%08x" % vdata
    if vtype == 0x02: return "?0x%08x" % vdata
    if vtype in (0x1c, 0x1d, 0x1e, 0x1f): return "#%08x" % vdata
    if vtype == 0x04: return str(struct.unpack("<f", struct.pack("<I", vdata))[0])
    if vtype == 0x05: return "dim:0x%x" % vdata
    return "type0x%x:0x%x" % (vtype, vdata)


def parse_axml(data):
    """Return list of events: ('start', ns_uri, tag, [(ns_uri,name,value,rawtype)]) / ('end', ...)."""
    magic, hsize, fsize = struct.unpack_from("<HHI", data, 0)
    assert magic == 0x0003, "not AXML"
    off = hsize
    sp = None; resmap = []
    events = []; nsmap = {}
    while off < len(data):
        ctype, chsize, csize = struct.unpack_from("<HHI", data, off)
        if csize == 0: break
        if ctype == 0x0001:
            sp = StringPool(data, off)
        elif ctype == 0x0180:
            n = (csize - chsize) // 4
            resmap = list(struct.unpack_from("<%dI" % n, data, off + chsize))
        elif ctype in (0x100, 0x101):
            line, cmt, pfx, uri = struct.unpack_from("<IIII", data, off + 8)
            if ctype == 0x100: nsmap[sp[uri]] = sp[pfx]
        elif ctype == 0x102:
            line, cmt, ns, name, astart, asize, acount, idx, cidx, sidx = struct.unpack_from("<IIIIHHHHHH", data, off + 8)
            attrs = []
            ap = off + 16 + astart
            for i in range(acount):
                ans, aname, araw, vsize, res0, vtype, vdata = struct.unpack_from("<IIIHBBI", data, ap)
                ap += 20
                nm = sp[aname]
                if (not nm) and aname < len(resmap):
                    nm = FRAMEWORK_ATTRS.get(resmap[aname], "attr_0x%08x" % resmap[aname])
                elif aname < len(resmap) and resmap[aname] in FRAMEWORK_ATTRS and (nm is None or nm == ""):
                    nm = FRAMEWORK_ATTRS[resmap[aname]]
                attrs.append((sp[ans], nm, fmt_value(sp, vtype, vdata, araw), vtype))
            events.append(("start", sp[ns], sp[name], attrs, line))
        elif ctype == 0x103:
            line, cmt, ns, name = struct.unpack_from("<IIII", data, off + 8)
            events.append(("end", sp[ns], sp[name], [], line))
        elif ctype == 0x104:
            # ResXMLTree_node common header (line,comment) at off+8; cdata data (string pool ref) at off+16
            data_idx = struct.unpack_from("<I", data, off + 16)[0]
            events.append(("cdata", None, None, [("text", sp[data_idx])], 0))
        off += csize
    return events, sp, resmap


def to_text(data):
    events, sp, resmap = parse_axml(data)
    out = []; depth = 0
    for ev in events:
        if ev[0] == "start":
            attrs = " ".join('%s="%s"' % (("android:" if a[0] == ANDROID_NS else "") + (a[1] or "?"), a[2]) for a in ev[3])
            out.append("  " * depth + "<%s%s>" % (ev[2], (" " + attrs) if attrs else ""))
            depth += 1
        elif ev[0] == "end":
            depth -= 1
            out.append("  " * depth + "</%s>" % ev[2])
        elif ev[0] == "cdata":
            txt = ev[3][0][1]
            out.append("  " * depth + (txt or ""))
    return "\n".join(out)


if __name__ == "__main__":
    print(to_text(open(sys.argv[1], "rb").read()))
