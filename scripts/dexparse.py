#!/usr/bin/env python3
"""Minimal DEX file structural parser.
Extracts: string pool, type pool, class defs (name, superclass, interfaces,
access flags, source file), method_ids and field_ids (declaring class, name,
shorty/descriptor), and per-class method/field membership via class_data_item.
This is a structural inventory (class/method/field names + signatures), not a
bytecode decompiler -- it does not recover method bodies / Java source.
"""
import struct, sys, os, json, collections

def uleb128(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off

def sleb128(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        shift += 7
        if not (b & 0x80):
            if b & 0x40: result -= (1 << shift)
            break
    return result, off

ACC = [
    (0x1,"public"),(0x2,"private"),(0x4,"protected"),(0x8,"static"),(0x10,"final"),
    (0x20,"synchronized"),(0x40,"bridge"),(0x80,"varargs"),(0x100,"native"),
    (0x200,"interface"),(0x400,"abstract"),(0x800,"strictfp"),(0x1000,"synthetic"),
    (0x2000,"annotation"),(0x4000,"enum"),(0x10000,"constructor"),(0x20000,"declared_synchronized"),
]
def acc_str(v):
    return "|".join(n for b,n in ACC if v & b)

class Dex:
    def __init__(self, path):
        self.path = path
        self.buf = open(path, "rb").read()
        self._parse_header()
        self._parse_strings()
        self._parse_types()
        self._parse_protos()
        self._parse_fields()
        self._parse_methods()
        self._parse_classes()

    def _parse_header(self):
        b = self.buf
        self.magic = b[0:8]
        (self.checksum,) = struct.unpack_from("<I", b, 8)
        self.sig = b[12:32]
        (self.file_size, self.header_size, self.endian_tag,
         self.link_size, self.link_off,
         self.map_off,
         self.string_ids_size, self.string_ids_off,
         self.type_ids_size, self.type_ids_off,
         self.proto_ids_size, self.proto_ids_off,
         self.field_ids_size, self.field_ids_off,
         self.method_ids_size, self.method_ids_off,
         self.class_defs_size, self.class_defs_off,
         self.data_size, self.data_off) = struct.unpack_from("<20I", b, 32)

    def _mutf8(self, off):
        # skip uleb128 utf16 length, then read null-terminated modified utf8
        _, off = uleb128(self.buf, off)
        start = off
        end = self.buf.index(b"\x00", off)
        raw = self.buf[start:end]
        try:
            return raw.decode("utf-8", "replace")
        except Exception:
            return raw.decode("latin1")

    def _parse_strings(self):
        b = self.buf
        offs = struct.unpack_from("<%dI" % self.string_ids_size, b, self.string_ids_off) if self.string_ids_size else ()
        self.strings = [self._mutf8(o) for o in offs]

    def _parse_types(self):
        b = self.buf
        idxs = struct.unpack_from("<%dI" % self.type_ids_size, b, self.type_ids_off) if self.type_ids_size else ()
        self.types = [self.strings[i] for i in idxs]

    def _parse_protos(self):
        b = self.buf
        self.protos = []
        off = self.proto_ids_off
        for i in range(self.proto_ids_size):
            shorty_idx, return_idx, params_off = struct.unpack_from("<III", b, off)
            off += 12
            params = []
            if params_off:
                size = struct.unpack_from("<I", b, params_off)[0]
                tlist = struct.unpack_from("<%dH" % size, b, params_off + 4)
                params = [self.types[t] for t in tlist]
            self.protos.append((self.strings[shorty_idx], self.types[return_idx], params))

    def _parse_fields(self):
        b = self.buf
        self.fields = []
        off = self.field_ids_off
        for i in range(self.field_ids_size):
            class_idx, type_idx, name_idx = struct.unpack_from("<HHI", b, off)
            off += 8
            self.fields.append((self.types[class_idx], self.types[type_idx], self.strings[name_idx]))

    def _parse_methods(self):
        b = self.buf
        self.methods = []
        off = self.method_ids_off
        for i in range(self.method_ids_size):
            class_idx, proto_idx, name_idx = struct.unpack_from("<HHI", b, off)
            off += 8
            shorty, ret, params = self.protos[proto_idx]
            self.methods.append((self.types[class_idx], self.strings[name_idx], ret, params))

    def _encoded_field(self, off, prev_idx):
        d, off = uleb128(self.buf, off)
        idx = prev_idx + d
        flags, off = uleb128(self.buf, off)
        return idx, flags, off

    def _encoded_method(self, off, prev_idx):
        d, off = uleb128(self.buf, off)
        idx = prev_idx + d
        flags, off = uleb128(self.buf, off)
        code_off, off = uleb128(self.buf, off)
        return idx, flags, code_off, off

    def _parse_classes(self):
        b = self.buf
        self.classes = []
        off = self.class_defs_off
        for i in range(self.class_defs_size):
            (class_idx, access_flags, superclass_idx, interfaces_off,
             source_file_idx, annotations_off, class_data_off, static_values_off) = struct.unpack_from("<8I", b, off)
            off += 32
            name = self.types[class_idx]
            super_ = self.types[superclass_idx] if superclass_idx != 0xffffffff else None
            ifaces = []
            if interfaces_off:
                size = struct.unpack_from("<I", b, interfaces_off)[0]
                tl = struct.unpack_from("<%dH" % size, b, interfaces_off + 4)
                ifaces = [self.types[t] for t in tl]
            srcfile = self.strings[source_file_idx] if source_file_idx != 0xffffffff else None
            sfields, ifields, dmethods, vmethods = [], [], [], []
            if class_data_off:
                p = class_data_off
                n_static, p = uleb128(b, p); n_instance, p = uleb128(b, p)
                n_direct, p = uleb128(b, p); n_virtual, p = uleb128(b, p)
                prev = 0
                for _ in range(n_static):
                    idx, flags, p = self._encoded_field(p, prev); prev = idx
                    sfields.append((idx, flags))
                prev = 0
                for _ in range(n_instance):
                    idx, flags, p = self._encoded_field(p, prev); prev = idx
                    ifields.append((idx, flags))
                prev = 0
                for _ in range(n_direct):
                    idx, flags, code_off, p = self._encoded_method(p, prev); prev = idx
                    dmethods.append((idx, flags, code_off))
                prev = 0
                for _ in range(n_virtual):
                    idx, flags, code_off, p = self._encoded_method(p, prev); prev = idx
                    vmethods.append((idx, flags, code_off))
            self.classes.append({
                "name": name, "super": super_, "interfaces": ifaces, "access": access_flags,
                "source_file": srcfile,
                "static_fields": sfields, "instance_fields": ifields,
                "direct_methods": dmethods, "virtual_methods": vmethods,
            })

    def class_summary(self, c):
        def jname(t):
            return t[1:-1].replace("/", ".") if t and t.startswith("L") else t
        def mname(idx):
            cls, nm, ret, params = self.methods[idx]
            return nm, ret, params
        dm = [mname(idx) for idx, f, co in c["direct_methods"]]
        vm = [mname(idx) for idx, f, co in c["virtual_methods"]]
        return {
            "class": jname(c["name"]), "super": jname(c["super"]),
            "interfaces": [jname(x) for x in c["interfaces"]],
            "access": acc_str(c["access"]), "source_file": c["source_file"],
            "n_static_fields": len(c["static_fields"]), "n_instance_fields": len(c["instance_fields"]),
            "methods": [m[0] for m in dm] + [m[0] for m in vm],
            "n_methods": len(dm) + len(vm),
        }


if __name__ == "__main__":
    d = Dex(sys.argv[1])
    print("strings=%d types=%d protos=%d fields=%d methods=%d classes=%d" % (
        len(d.strings), len(d.types), len(d.protos), len(d.fields), len(d.methods), len(d.classes)))
