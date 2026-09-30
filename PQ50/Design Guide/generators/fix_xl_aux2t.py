# -*- coding: utf-8 -*-
"""Device Setting F83 / F91: the auxiliary winding now SUPPLIES VCC, 2 turns.

2026-09-25, user: design the auxiliary winding for VCC with no external
rail, 2 T and a Zener regulator.  n.aux goes to 1.0 (2 T on N.s = 2) and the
ZCD divider follows it: R.ZCD_H is the E24 value above

    D91 = F90*D86/D72 - F90 = 19 k * 27.5 / 2.3 - 19 k = 208.2 k   ->  220 k

The ST tool assumes the winding is wired straight to VCC, so D83/D84 still
ask whether V.aux at OVP2 stays under D74 = 25 V.  With n.aux = 1.0 it does
not (D84 = 0.84), and that is intended: a Zener-referenced emitter follower
sits between the winding and the VCC pin and holds VCC at about 13.6 V.  The
SMath sheet checks the regulator output instead (section 14c, k.VCC).  B84
says so, the CHANGELOG records it, and this is the one place the workbook
and the SMath sheet deliberately ask different questions.

Formulas are kept; the cached values of every cell that reads F83 or F91 are
recomputed here from the cached inputs, so xl_sm_compare and bom_compare
(which read caches) see the new numbers before Excel has opened the file.

    python fix_xl_aux2t.py        canonical 7.5:1 workbook, its copy in
                                  variants/, and the 6:1 workbook
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx_patch as X                                               # noqa: E402
#  fix_xl_suend already wraps stdout for UTF-8 on import; wrapping it again
#  here closes the first wrapper's stream.
from fix_xl_suend import part_of, cached, formula, cell_fv           # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XLD = os.path.join(ROOT, 'Calculation Excel Sheet')
CANON = os.path.join(XLD, 'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')
COPY = os.path.join(XLD, 'variants', 'L6790_workbook_7p5to1.xlsx')
SIX = os.path.join(XLD, 'variants', 'L6790_workbook_6to1.xlsx')

NAUX = 1.0
RZH = 220.0

B84 = ('Auxiliary ratio check for a winding wired STRAIGHT to VCC. This '
       'design feeds VCC through a Zener regulator (about 13.6 V), so D84 < 1 '
       'is intended: the 25 V limit applies to the regulator output, checked '
       'in the SMath sheet section 14c (k.VCC).')

LOG = ('Device Setting', 'F83, F91, B84 (and cached D84-D100, BOM E56)',
       'The auxiliary winding was a ZCD sense winding (n.aux 1.5, three turns '
       'on three cores in series, R.ZCD_H 330 k) and VCC came from an external '
       '12 V rail. The user decided (2026-09-25) that there is no external '
       'rail: the auxiliary winding supplies VCC, 2 turns, through a Zener '
       'regulator.',
       'F83 = 1.0 (2 T on N.s = 2), F91 = 220 k (E24 above the calculated '
       '208.2 k). B84 explains that D84 < 1 is intended. Formulas unchanged; '
       'cached values recomputed.',
       'OVP1 28.93 V, OVP2 31.45 V, start-up hand-over 17.11 V. D84 = 0.84 '
       'reads as a failure in the ST tool and is not one here - the regulator '
       'between the winding and VCC is a deliberate difference from the ST '
       'tool\'s direct-feed assumption.')


def patch(path):
    print('백업 %s' % os.path.basename(X.backup(path)))
    parts = X.open_book(path)
    p = part_of(parts, 'Device Setting')
    xml = parts[p].decode('utf-8')

    c = {r: cached(xml, r) for r in ('D71', 'D72', 'D73', 'D78', 'D83', 'F90')}
    f = {r: formula(xml, r) for r in ('D84', 'D86', 'D87', 'D88', 'D89', 'D91',
                                      'D94', 'D95', 'D96', 'D97', 'D98', 'D99',
                                      'D100')}
    want = {'D84': 'D83/IF(ISNUMBER(F83),F83,D83)', 'D86': 'F83*D78',
            'D87': 'D86/D72*D73', 'D88': 'D86/D72*D71', 'D89': 'D88/F83',
            'D91': '(F90*D86/D72)-F90', 'D94': '(D72/F83)*((F91/F90)+1)',
            'D95': '(D73/F83)*((F91/F90)+1)', 'D96': 'F83*D94',
            'D97': 'F83*D95', 'D98': '(D96/D72)*(D71)', 'D99': 'D98/F83',
            'D100': "'Design Spec'!D95*F83"}
    assert f == want, {k: f[k] for k in f if f[k] != want[k]}
    vout = cached(parts[part_of(parts, 'Design Spec')].decode('utf-8'), 'D95')

    v = {}
    v['D84'] = c['D83'] / NAUX
    v['D86'] = NAUX * c['D78']
    v['D87'] = v['D86'] / c['D72'] * c['D73']
    v['D88'] = v['D86'] / c['D72'] * c['D71']
    v['D89'] = v['D88'] / NAUX
    v['D91'] = c['F90'] * v['D86'] / c['D72'] - c['F90']
    v['D94'] = (c['D72'] / NAUX) * (RZH / c['F90'] + 1)
    v['D95'] = (c['D73'] / NAUX) * (RZH / c['F90'] + 1)
    v['D96'] = NAUX * v['D94']
    v['D97'] = NAUX * v['D95']
    v['D98'] = (v['D96'] / c['D72']) * c['D71']
    v['D99'] = v['D98'] / NAUX
    v['D100'] = vout * NAUX
    for r in sorted(v, key=lambda t: int(t[1:])):
        print('  %-5s %10.4f -> %10.4f' % (r, cached(xml, r), v[r]))

    xml = X.set_cell(xml, 'F83', X.cell_n('F83', X.style_of(xml, 'F83'), NAUX))
    xml = X.set_cell(xml, 'F91', X.cell_n('F91', X.style_of(xml, 'F91'), RZH))
    xml = X.ensure_row(xml, 84)
    xml = X.set_cell(xml, 'B84', X.cell_t('B84', X.style_of(xml, 'B83'), B84))
    for r, val in v.items():
        xml = X.set_cell(xml, r, cell_fv(r, X.style_of(xml, r), want[r], val))
    parts[p] = xml.encode('utf-8')

    # BOM&Schematics E56 = IF('Device Setting'!F91, F91, D91) - cached 330
    b = part_of(parts, 'BOM&Schematics')
    xml = parts[b].decode('utf-8')
    fb = formula(xml, 'E56')
    assert 'F91' in fb, fb
    xml = X.set_cell(xml, 'E56', cell_fv('E56', X.style_of(xml, 'E56'), fb, RZH))
    parts[b] = xml.encode('utf-8')
    print('  BOM E56 -> %g' % RZH)

    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    m = re.search(r'<c r="C(\d+)"[^>]*><is><t[^>]*>F83, F91, B84', xml)
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
    return v


def main():
    v = patch(CANON)
    shutil.copyfile(CANON, COPY)
    print('복사 -> variants/%s' % os.path.basename(COPY))
    v6 = patch(SIX)
    print()
    print('OVP1 %.2f V  OVP2 %.2f V  기동 종료 %.2f V  (6:1 %.2f / %.2f / %.2f)'
          % (v['D94'], v['D95'], v['D99'], v6['D94'], v6['D95'], v6['D99']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
