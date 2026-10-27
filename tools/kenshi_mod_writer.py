"""Canonical Kenshi .mod writer + byte-exact round-trip test.

Implements the layout documented by OpenConstructionSet (C#, MIT) / kenshi-modkit
(pure Python) so a file can be re-serialised from scratch and compared with the
original byte for byte:

    file   = i32 type | [type 16/17: header] | i32 lastId | i32 recordCount | records
             header (16) = version, author, description, dependencies, references
             header (17) = i32 B, then the same five strings, then a B-sized body
                           that also holds  saveCount | lastMerge | mergeEntries |
                           deleteRequests, then lastId/recordCount follow the body
    record = i32 size(whole record) | i32 type | i32 id | str name | str key
             | i32 saveData
             | 7 type sections, each  i32 count + count x (str key + value)
                 bool 1B | f32 4B | i32 4B | vec3 12B | vec4 16B | str | str
               keys inside a section are sorted by name (FCS writes them so)
             | i32 refCategoryCount + per category
                 str name | i32 itemCount | itemCount x (str targetId + 3 x i32)
             | i32 instanceCount + instances (0 in .mod files)
             size is recomputed as the whole record length

Every record type present in the game data round-trips byte-identically if the
model is right, so running this over real mods validates the reader; running it
over a generated file proves that file is exactly what a spec writer emits.
"""

import struct


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def put(v):
    return struct.pack('<I', v)


def w_str(s):
    b = s.encode('utf-8') if isinstance(s, str) else s
    return put(len(b)) + b


class Reader(object):
    def __init__(self, b):
        self.b = b

    def string(self, o, end=None):
        end = len(self.b) if end is None else end
        n = u32(self.b, o)
        raw = self.b[o + 4:o + 4 + n]
        return raw.decode('utf-8'), o + 4 + n


def read_record(b, o, end):
    size = u32(b, o)
    if size < 16 or o + size > end:
        return None
    p = o + 4
    typ, rid = u32(b, p), u32(b, p + 4)
    p += 8
    name, p = Reader(b).string(p, end)
    key, p = Reader(b).string(p, end)
    save = u32(b, p)
    p += 4
    sections = []
    for kind in ('bool', 'f32', 'long', 'vec3', 'vec4', 'string', 'filename'):
        cnt = u32(b, p)
        p += 4
        ents = []
        for _ in range(cnt):
            nm, p = Reader(b).string(p, end)
            if kind == 'bool':
                raw = b[p:p + 1]
                p += 1
            elif kind in ('f32', 'long'):
                raw = b[p:p + 4]
                p += 4
            elif kind == 'vec3':
                raw = b[p:p + 12]
                p += 12
            elif kind == 'vec4':
                raw = b[p:p + 16]
                p += 16
            else:
                s, p2 = Reader(b).string(p, end)
                raw = b[p:p2]
                p = p2
            ents.append((nm, kind, raw))
        sections.append(ents)
    ncat = u32(b, p)
    p += 4
    cats = []
    for _ in range(ncat):
        cname, ns = Reader(b).string(p, end)
        q = ns
        ic = u32(b, q)
        q += 4
        for _ in range(ic):
            _tid, q = Reader(b).string(q, end)
            q += 12
        cats.append(b[ns - 4 - len(cname.encode()):q])
        p = q
    inst_at = p
    p += 4
    inst_count = u32(b, inst_at)
    for _ in range(inst_count):                       # saves only
        _id, p = Reader(b).string(p, end)
        _tid, p = Reader(b).string(p, end)
        p += 12 + 16
        st = u32(b, p)
        p += 4
        for _ in range(st):
            _s, p = Reader(b).string(p, end)
    if p != o + size:
        raise ValueError('record at %d: parsed to %d but size says %d'
                         % (o, p - o, size))
    return dict(size=size, type=typ, id=rid, name=name, key=key, save=save,
                sections=sections, cats=cats, inst=b[inst_at:o + size], end=p)


def write_record(rec):
    out = bytearray()
    out += put(0) + put(rec['type']) + put(rec['id'])
    out += w_str(rec['name']) + w_str(rec['key']) + put(rec['save'])
    for ents in rec['sections']:
        # Measured: FCS does NOT sort the entries - the on-disk order (a schema
        # order, which merely looks alphabetical for the first few fields) is
        # preserved, so the writer must not reorder anything.
        out += put(len(ents))
        for nm, _kind, raw in ents:
            out += w_str(nm) + raw
    out += put(len(rec['cats']))
    for c in rec['cats']:
        out += c
    out += rec['inst']
    out[0:4] = put(len(out))
    return bytes(out)


def find_records_start(b):
    """Return the offset where records begin, for filetype 15/16/17."""
    t = u32(b, 0)
    if t == 17:
        B = u32(b, 4)
        return 8 + B + 8
    if t == 16:
        p = 8
        for _ in range(4):
            _s, p = Reader(b).string(p)
        return p + 4
    if t == 15:
        return 8
    raise ValueError('unknown filetype %d' % t)


def roundtrip(path):
    b = open(path, 'rb').read()
    start = find_records_start(b)
    o, out, n = start, bytearray(b[:start]), 0
    while o + 16 <= len(b):
        rec = read_record(b, o, len(b))
        if rec is None:
            break
        out += write_record(rec)
        o = rec['end']
        n += 1
    same = bytes(out) == b
    return dict(path=path.split('\\')[-1], size=len(b), records=n,
                walked=o, consumed_all=(o == len(b)), identical=same,
                first_diff=(None if same else next(
                    (i for i in range(min(len(out), len(b))) if out[i] != b[i]),
                    None)),
                head=start)


if __name__ == '__main__':
    import sys
    paths = sys.argv[1:]
    if not paths:
        W = r'D:\Steam\steamapps\workshop\content\233860'
        K = r'D:\Steam\steamapps\common\Kenshi\data'
        paths = [W + r'\3752962075\MN_Pet Ashland Hat.mod',
                 W + r'\3238799616\bull armor.mod',
                 W + r'\3654362321\bull armor Armor Slot Patch.mod',
                 K + r'\rebirth.mod',
                 r'E:\KenshiProject\3.KenshiGithubProjects\_out\MNFull3.mod',
                 r'E:\KenshiProject\3.KenshiGithubProjects\_out\MNFull2.mod']
    for p in paths:
        try:
            r = roundtrip(p)
            print('%-40s %9d B  recs=%-6d walked=%-9d %s  重写一致=%s%s'
                  % (r['path'], r['size'], r['records'], r['walked'],
                     'EOF OK' if r['consumed_all'] else 'INCOMPLETE',
                     r['identical'],
                     '' if r['identical'] else '  首个差异@%s' % r['first_diff']))
        except Exception as exc:
            print('%-40s 失败: %s' % (p.split('\\')[-1], exc))
