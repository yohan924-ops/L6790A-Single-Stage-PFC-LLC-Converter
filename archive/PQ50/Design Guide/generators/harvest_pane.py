# -*- coding: utf-8 -*-
"""Take a pane that SMath grew, and make it a pane this project owns.

The TI sheet is the only source of ZedGraph panes here, and the biggest it
has holds five curves. That was the ceiling on NAMED traces, because SMath
draws extra curves but gives them a default colour, a one-pixel line and no
legend entry - the pane owns four labels and nothing can add a fifth.

Except that SMath rewrites the pane when the sheet is saved, and it makes
the curve list match the input. Feed a four-curve pane eight matrices, save,
and the file now holds an EIGHT-curve pane. That pane can be lifted out and
kept, and then all eight are ours to name.

Confirmed on the sandbox sheet:

    a four-curve pane given eight  ->  four curves added
    a one-curve pane given three   ->  two added
    a four-curve pane given two    ->  two removed

The four added curves carry no label of their own: their Label._text is a
MemberReference to the empty string the pane already contains. Replacing
that five-byte reference with a real string record gives them a name, and
because BinaryFormatter addresses records by object id and never by offset,
the stream changing length is harmless - the same reason titles and legend
entries can be rewritten to any length.

Run:  python harvest_pane.py <sheet.sm> <pane index> <out name>
"""
import base64
import io
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import zedpane as Z                                                # noqa: E402

STORE = os.path.join(HERE, 'panes')

LABEL_NAME = b'ZedGraph.Label'


def panes(path):
    s = io.open(path, encoding='utf-8', errors='replace').read()
    out = []
    for attr, blob in re.findall(
            r'<zedgraph([^>]*)>\s*<data encoding="base64">([^<]*)</data>',
            s, re.S):
        out.append((int(re.search(r'width="(\d+)"', attr).group(1)),
                    int(re.search(r'height="(\d+)"', attr).group(1)),
                    base64.b64decode(blob.strip())))
    return out


def _max_id(raw):
    """the largest object id that is certainly an id and not data

    Only records whose shape can be checked are counted: a string record
    whose length byte is sane, and a ClassWithId whose metadata id is small.
    """
    best = 0
    for m in re.finditer(rb'\x06(....)(.)', raw, re.S):
        oid, ln = struct.unpack('<i', m.group(1))[0], m.group(2)[0]
        if 0 < oid < 100000 and ln < 128:
            best = max(best, oid)
    for m in re.finditer(rb'\x01(....)(....)', raw, re.S):
        oid = struct.unpack('<i', m.group(1))[0]
        mid = struct.unpack('<i', m.group(2))[0]
        if 0 < oid < 100000 and 0 < mid < 100000:
            best = max(best, oid)
    return best


def _text_at(raw, p):
    if raw[p] == 6:
        ln = raw[p + 5]
        return (p, 'string', raw[p + 6:p + 6 + ln].decode('utf-8'))
    if raw[p] == 9:
        return (p, 'ref', struct.unpack_from('<i', raw, p + 1)[0])
    raise ValueError('0x%02x where a Label text should be, at %d'
                     % (raw[p], p))


def curve_labels(raw):
    """[(offset, kind, text_or_id)] for every curve Label, in stream order

    Axis titles are not Label objects here: the Label class record appears
    after them in the stream, so what this returns is the curves and
    nothing else. Label serialises as schema, text, isVisible, fontSpec, so
    the text is the record straight after the four schema bytes.
    """
    m = re.search(rb'\x05(....)\x0e' + re.escape(LABEL_NAME), raw, re.S)
    if not m:
        raise ValueError('this pane has no ZedGraph.Label class record')
    cid = struct.unpack('<i', m.group(1))[0]
    out = [_text_at(raw, raw.find(b'\x0a\x00\x00\x00', m.end()) + 4)]
    for mm in re.finditer(rb'\x01(....)' + re.escape(struct.pack('<i', cid)),
                          raw, re.S):
        p = mm.end()
        if raw[p:p + 4] == b'\x0a\x00\x00\x00':
            out.append(_text_at(raw, p + 4))
    return sorted(out)


def set_curve_labels(raw, labels):
    """Name every curve, including the ones SMath added.

    A curve SMath created points its Label at the pane's empty string; a
    curve the pane was built with owns a string record. Both are replaced
    here, back to front so that earlier offsets stay valid.
    """
    hits = curve_labels(raw)
    if len(hits) != len(labels):
        raise ValueError('%d Label records but %d labels given'
                         % (len(hits), len(labels)))
    nid = _max_id(raw) + 1000
    for k in range(len(hits) - 1, -1, -1):
        p, kind, _ = hits[k]
        txt = labels[k].encode('utf-8')
        if len(txt) > 127:
            raise ValueError('label longer than a one-byte length prefix')
        if kind == 'string':
            old = 6 + raw[p + 5]
            new = b'\x06' + raw[p + 1:p + 5] + bytes([len(txt)]) + txt
        else:
            old = 5
            nid += 1
            new = b'\x06' + struct.pack('<i', nid) + bytes([len(txt)]) + txt
        raw = raw[:p] + new + raw[p + old:]
    return raw


def main(path, index, name, width=2.0):
    w, h, raw = panes(path)[index]
    hits = curve_labels(raw)
    print('%s pane %d: %dx%d, %d bytes' % (os.path.basename(path), index,
                                           w, h, len(raw)))
    print('  Label records: %d  (%d named, %d pointing at the empty string)'
          % (len(hits), sum(1 for x in hits if x[1] == 'string'),
             sum(1 for x in hits if x[1] == 'ref')))
    for p, kind, v in hits:
        print('     @%-6d %-6s %r' % (p, kind, v))
    raw, n = Z.set_line_width(raw, width, old=1.0)
    print('  %d one-pixel outlines widened to %g' % (n, width))
    if not os.path.isdir(STORE):
        os.makedirs(STORE)
    out = os.path.join(STORE, name + '.b64')
    io.open(out, 'w', encoding='ascii').write(
        '%d %d\n' % (w, h) + base64.b64encode(raw).decode())
    print('  written %s' % out)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__.strip().splitlines()[-1])
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
