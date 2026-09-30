# -*- coding: utf-8 -*-
"""Device Setting D71: the start-up end threshold at the ZCD pin, 1.35 -> 1.36 V.

The ST tool carries V_ZCD_SUend = 1.35 V. The draft datasheet's electrical
characteristics table gives 1.36 V (typ), and the user decided on the
datasheet (2026-09-24). D71 feeds three formulas in the same sheet:

    D88  peak aux voltage at end of start-up   = D86/D72*D71
    D98  actual end-start-up voltage on aux    = (D96/D72)*D71
    D99  actual end-start-up voltage on output = D98/F83

They keep their formulas; their cached values are recomputed here from the
cached inputs, so xl_sm_compare (which reads caches) sees the new numbers
before Excel has opened the file. fullCalcOnLoad makes Excel redo them anyway.

    python fix_xl_suend.py            canonical 7.5:1 workbook, its copy in
                                      variants/, and the 6:1 workbook
"""
import io
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx_patch as X                                               # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XLD = os.path.join(ROOT, 'Calculation Excel Sheet')
CANON = os.path.join(XLD, 'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')
COPY = os.path.join(XLD, 'variants', 'L6790_workbook_7p5to1.xlsx')
SIX = os.path.join(XLD, 'variants', 'L6790_workbook_6to1.xlsx')

NEW = 1.36
LOG = ('Device Setting', 'D71 (and cached D88, D98, D99)',
       'D71 "DS_IC start-up phase end th at ZCD pin" held 1.35 V, the ST tool '
       'value. The draft datasheet electrical characteristics table gives '
       'V_ZCD_SUend = 1.36 V (typ).',
       'D71 = 1.36 V, the datasheet value (user decision 2026-09-24). D88, '
       'D98 and D99 keep their formulas; their cached values were recomputed.',
       'The output voltage at which start-up hands over to the loop (D99) '
       'moves by +0.7 %. Nothing else reads these cells; no margin moves.')


def part_of(parts, name):
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                          parts['xl/_rels/workbook.xml.rels'].decode('utf-8')))
    for nm, r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
        if nm.replace('&amp;', '&') == name:
            return 'xl/' + rid[r].lstrip('/')
    raise KeyError(name)


def cached(xml, ref):
    m = re.search(r'<c r="%s"[^>]*>(.*?)</c>' % ref, xml, re.S)
    v = re.search(r'<v>([^<]*)</v>', m.group(1)) if m else None
    if not v:
        raise KeyError('no cached value in %s' % ref)
    return float(v.group(1))


def formula(xml, ref):
    m = re.search(r'<c r="%s"[^>]*>.*?<f>([^<]*)</f>' % ref, xml, re.S)
    if not m:
        raise KeyError('no formula in %s' % ref)
    return m.group(1).replace('&amp;', '&')


def cell_fv(ref, style, f, v):
    """formula WITH a cached value"""
    return '<c r="%s" s="%s"><f>%s</f><v>%r</v></c>' % (ref, style, X.esc(f), v)


def patch(path):
    print('백업 %s' % os.path.basename(X.backup(path)))
    parts = X.open_book(path)
    p = part_of(parts, 'Device Setting')
    xml = parts[p].decode('utf-8')

    old = cached(xml, 'D71')
    d72, d86, d96, f83 = (cached(xml, r) for r in ('D72', 'D86', 'D96', 'F83'))
    expect = {'D88': formula(xml, 'D88'), 'D98': formula(xml, 'D98'),
              'D99': formula(xml, 'D99')}
    assert expect['D88'] == 'D86/D72*D71', expect
    assert expect['D98'] == '(D96/D72)*(D71)', expect
    assert expect['D99'] == 'D98/F83', expect
    d88 = d86 / d72 * NEW
    d98 = (d96 / d72) * NEW
    d99 = d98 / f83
    print('  D71 %.2f -> %.2f   D88 %.4f -> %.4f   D98 %.4f -> %.4f   '
          'D99 %.4f -> %.4f'
          % (old, NEW, cached(xml, 'D88'), d88, cached(xml, 'D98'), d98,
             cached(xml, 'D99'), d99))

    xml = X.set_cell(xml, 'D71', X.cell_n('D71', X.style_of(xml, 'D71'), NEW))
    for ref, v in (('D88', d88), ('D98', d98), ('D99', d99)):
        xml = X.set_cell(xml, ref, cell_fv(ref, X.style_of(xml, ref),
                                           expect[ref], v))
    parts[p] = xml.encode('utf-8')

    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    m = re.search(r'<c r="C(\d+)"[^>]*><is><t[^>]*>D71 \(and cached', xml)
    r = int(m.group(1)) if m else \
        max(int(x) for x in re.findall(r'<row r="(\d+)"', xml)) + 1
    xml = X.ensure_row(xml, r)
    for col, text, st in (('B', LOG[0], '7'), ('C', LOG[1], '7'),
                          ('D', LOG[2], '8'), ('E', LOG[3], '8'),
                          ('F', LOG[4], '8')):
        xml = X.set_cell(xml, col + str(r), X.cell_t(col + str(r), st, text))
    parts[cl] = xml.encode('utf-8')
    print('  CHANGELOG 행 %d' % r)

    X.write_book(path, parts)
    return d99


def main():
    v = patch(CANON)
    shutil.copyfile(CANON, COPY)
    print('복사 -> variants/%s' % os.path.basename(COPY))
    v6 = patch(SIX)
    print()
    print('기동 종료 출력 전압: 7.5:1 %.2f V, 6:1 %.2f V' % (v, v6))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
