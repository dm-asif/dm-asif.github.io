#!/usr/bin/env python3
"""Minimal resources.arsc (binary resource table) reader.

Only decodes what is needed for this analysis:
  - global string pool (not usually used for resource *names* but present)
  - per-package type-string pool and key-string pool (resource type/name strings)
  - resource id -> "package:type/name" mapping (table only, not resolved values)
  - ResTable_config locale (language/country) seen per type chunk, to enumerate
    which locales the APK ships configuration-specific resources for.

All chunk traversal uses the generic ResChunk_header {type:u16, headerSize:u16,
size:u32} to skip unknown/unparsed chunks safely, so an imperfect understanding
of less-common chunk subtypes cannot corrupt the walk -- at worst it skips a
chunk's *contents* while still advancing correctly.
"""
import struct, sys
sys.path.insert(0, "/home/claude/tallykhata/scripts")
from axml import StringPool

RES_STRING_POOL_TYPE = 0x0001
RES_TABLE_TYPE = 0x0002
RES_TABLE_PACKAGE_TYPE = 0x0200
RES_TABLE_TYPE_TYPE = 0x0202
RES_TABLE_TYPE_SPEC_TYPE = 0x0201


def read_chunk_header(buf, off):
    ctype, hsize, size = struct.unpack_from("<HHI", buf, off)
    return ctype, hsize, size


def locale_from_config(buf, coff, csize):
    # ResTable_config: size(4) imsi(4) locale(4: language[2]+country[2]) ...
    if csize < 8:
        return None
    size = struct.unpack_from("<I", buf, coff)[0]
    if size < 8:
        return None
    lang = buf[coff + 4:coff + 6]
    country = buf[coff + 6:coff + 8]
    def dec(b):
        if b[0] == 0: return ""
        # packed 2-letter or 3-letter (if high bit set, different packing); handle common 2-byte ascii case
        try:
            s = b.decode("ascii")
            return s.replace("\x00", "")
        except Exception:
            return ""
    l = dec(lang); c = dec(country)
    if not l and not c:
        return None
    return l + ("-r" + c if c else "")


class ArscTable:
    def __init__(self, path):
        self.buf = open(path, "rb").read()
        self.global_sp = None
        self.packages = []  # list of dicts: {id, name, type_sp, key_sp, entries: {resid: (typename, keyname)}, locales:set}
        self._parse()

    def _parse(self):
        buf = self.buf
        ctype, hsize, size = read_chunk_header(buf, 0)
        assert ctype == RES_TABLE_TYPE, "not a valid resources.arsc"
        pkg_count = struct.unpack_from("<I", buf, 8)[0]
        off = hsize
        end = size
        while off < end:
            ctype, chsize, csize = read_chunk_header(buf, off)
            if csize <= 0:
                break
            if ctype == RES_STRING_POOL_TYPE and self.global_sp is None:
                self.global_sp = StringPool(buf, off)
            elif ctype == RES_TABLE_PACKAGE_TYPE:
                self._parse_package(off, chsize, csize)
            off += csize

    def _parse_package(self, off, chsize, csize):
        buf = self.buf
        pkg_id, = struct.unpack_from("<I", buf, off + 8)
        name_raw = buf[off + 12:off + 12 + 256]
        name = name_raw.decode("utf-16le", "replace").split("\x00", 1)[0]
        type_strings_off, last_pub_type, key_strings_off, last_pub_key = struct.unpack_from("<IIII", buf, off + 268)
        pkg = {"id": pkg_id, "name": name, "type_sp": None, "key_sp": None, "entries": {}, "locales": set()}
        type_sp = StringPool(buf, off + type_strings_off) if type_strings_off else None
        key_sp = StringPool(buf, off + key_strings_off) if key_strings_off else None
        pkg["type_sp"] = type_sp
        pkg["key_sp"] = key_sp

        p = off + chsize
        end = off + csize
        cur_type_id = None
        cur_type_name = None
        while p < end:
            ctype, chs, cs = read_chunk_header(buf, p)
            if cs <= 0:
                break
            if ctype == RES_TABLE_TYPE_SPEC_TYPE:
                cur_type_id = buf[p + 8]
                cur_type_name = type_sp[cur_type_id - 1] if type_sp and cur_type_id else None
            elif ctype == RES_TABLE_TYPE_TYPE:
                type_id = buf[p + 8]
                tname = type_sp[type_id - 1] if type_sp else None
                entry_count, entries_start = struct.unpack_from("<II", buf, p + 12)
                # config struct begins right after entries_start field (at p+20), length = chs - 20
                config_off = p + 20
                loc = locale_from_config(buf, config_off, chs - 20)
                if loc:
                    pkg["locales"].add(loc)
                else:
                    pkg["locales"].add("(default)")
                # entry offsets array at p+chs, entry_count * 4 bytes
                off_arr = p + chs
                base = p + entries_start
                for i in range(entry_count):
                    eoff = struct.unpack_from("<I", buf, off_arr + i * 4)[0]
                    if eoff == 0xFFFFFFFF:
                        continue
                    entry_addr = base + eoff
                    esize, eflags, key_idx = struct.unpack_from("<HHI", buf, entry_addr)
                    keyname = key_sp[key_idx] if key_sp else None
                    resid = (pkg_id << 24) | (type_id << 16) | i
                    if resid not in pkg["entries"]:
                        pkg["entries"][resid] = (tname, keyname)
            p += cs
        self.packages.append(pkg)

    def lookup(self, resid):
        for pkg in self.packages:
            if resid in pkg["entries"]:
                t, k = pkg["entries"][resid]
                return "%s:%s/%s" % (pkg["name"], t, k)
        return None


if __name__ == "__main__":
    t = ArscTable(sys.argv[1])
    for pkg in t.packages:
        print("package", pkg["id"], pkg["name"], "entries=", len(pkg["entries"]), "locales=", sorted(pkg["locales"]))
