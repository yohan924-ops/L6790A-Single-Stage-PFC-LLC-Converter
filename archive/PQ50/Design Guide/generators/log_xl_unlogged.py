# -*- coding: utf-8 -*-
"""Write the cells that were changed but never logged into the workbook's CHANGELOG.

Compared formula by formula against the decrypted ST original, the seven design
sheets of our workbook differ in 261 formula cells and 18 constants.  The log
named all but 17 of them (2026-09-23; the "48" in older notes predates the rows
that now cover the CompensationNet&Check gain-margin work).  This script adds a
row for each of the 17, with the old and the new content read from the two
files - nothing about Was or Now is typed here, only the Why.

Only cells that really differ from the original in the given workbook are
written, so the same script serves every variant.  A cell already named in
column C of the log is skipped, so running it twice adds nothing.

It changes no formula and no value - it writes log rows only.

    python log_xl_unlogged.py                      the canonical workbook
    python log_xl_unlogged.py <workbook.xlsx> ...   others (variants/)
"""
import os
import re
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx_patch as X                                                # noqa: E402
from log_xl_findings import part_of, XL                              # noqa: E402

# stdout is already wrapped to UTF-8 by log_xl_findings on import
warnings.filterwarnings('ignore')

ORIG = os.path.join(os.path.dirname(XL),
                    'Uncryped_04092026_LGE_670W_L6790A_spread sheet.xlsx')
LOG = 'CHANGELOG_rev0_6'

HEAD = ('rev 0.7 - changes that were made earlier but never written into this '
        'log (found 2026-09-23 by comparing every design-sheet formula and '
        'constant with the ST original). Records only: no cell was changed.')

C18 = ('C.18: the line-cycle rms now comes from the Simpson integral in CC '
       'column J instead of the single-phase theta = pi/4 approximation in '
       'column C. The C.18 rows of this log name the CC cells, not this reader.')

WHY = [
    ('Design Spec', 'G23',
     'Added. Shows the output voltage the fitted divider actually regulates to '
     '(CompensationNet&Check D38) next to the target in D23, so the E-series '
     'rounding of R.I / R.O is visible on the specification page.'),
    ('Design Spec', 'D24',
     'Project specification: hold-up ends at or above this voltage '
     '(docs/DESIGN.md, specification table).'),
    ('Design Spec', 'D25',
     'Project specification: output ripple at most this, peak to peak.'),
    ('Design Spec', 'D26',
     'Project specification: hold-up time at 100 Vac, full load, starting at '
     'the ripple trough.'),
    ('Res. Tank Design', 'D65', C18),
    ('Res. Tank Design', 'D67', C18),
    ('Res. Tank Design', 'F45',
     'Selected magnetizing inductance of this design point, chosen together '
     'with the turns ratio so that n.T = n*sqrt(1+lambda.act) is a ratio that '
     'can be wound. The calculated D45 is the no-load condition at the high '
     'corner, which the design knowingly does not meet (burst mode covers '
     'it), so it is not a value to round to.'),
    ('Power Components', 'D28', C18),
    ('Power Components', 'D71',
     'Entered with the STO60N045DM9 selection. WHICH datasheet capacitance '
     'this is (small-signal Coss, Co(er) or Co(tr)) is not recorded, and ZVS '
     'needs Co(tr). D77 Ctot = 2*D71 + D72 is read by no formula: the ZVS '
     'check uses Design Spec D46 (the midpoint capacitance input). Open item '
     '- confirm against the datasheet.'),
    ('Device Setting', 'F21',
     'Selected timing capacitor, shown in the selection column like the other '
     'blocks. No formula reads F21 - they read D21, which holds the same '
     'value. Keep the two equal.'),
    ('Device Setting', 'D22',
     'Added margin check: the timing capacitor inside its window, '
     'min(CT.max/CT, CT/CT.min) > 1.'),
    ('Device Setting', 'D25',
     'Added margin check: RT.ceil (D24) over the selected RT > 1, i.e. f.Min '
     'stays above f.o. RT.ceil is a MAXIMUM despite the ST label "Minimum '
     'Resistor value".'),
    ('Device Setting', 'D49',
     'Added: OCP1 trip current from the 0.55 V ISEN threshold over R.CS (D46, '
     'mOhm).'),
    ('Device Setting', 'G49',
     'Added: OCP2 trip current from the 0.75 V ISEN threshold over R.CS.'),
    ('Device Setting', 'D50',
     'Added margin check: OCP1 over the composite tank peak D32, target > 1.2.'),
    ('Device Setting', 'F83',
     'Selected auxiliary-to-secondary ratio: 3 auxiliary turns on 2 secondary '
     'turns. The auxiliary winding only senses (ZCD); VCC comes from an '
     'external 12 V rail, so the D83 limit - which protects VCC at OVP2 - does '
     'not apply, and D84 below 1 is expected.'),
    ('Device Setting', 'D84',
     'Added margin check k.naux = D83 / selected ratio. It matters only when '
     'the auxiliary winding supplies VCC; here the winding only senses (ZCD) '
     'and VCC comes from an external rail, so a value below 1 is not a '
     'failure.'),
    ('Device Setting', 'F91',
     'Selected upper ZCD resistor: the E24 value just ABOVE the calculated '
     'one, so that OVP1 lands above the output ripple peak rather than on it.'),
]


def shown(v):
    if v is None:
        return '(empty)'
    if isinstance(v, float):
        return ('%.6g' % v)
    return str(v)


def logged(xml, shared, sheet):
    """cells named in column C of rows whose column B is this sheet"""
    out = set()
    for row in re.findall(r'<row r="\d+"[^>]*>(.*?)</row>', xml, re.S):
        cells = {c: (a, b) for c, a, b in
                 re.findall(r'<c r="([A-Z]+)\d+"([^>/]*)>(.*?)</c>', row, re.S)}

        def text(col):
            attrs, body = cells.get(col, ('', ''))
            if 't="s"' in attrs:
                m = re.search(r'<v>(\d+)</v>', body)
                return shared[int(m.group(1))] if m else ''
            m = re.search(r'<t[^>]*>(.*?)</t>', body, re.S)
            return m.group(1) if m else ''
        if X.xml_text(text('B')).strip() != sheet:
            continue
        for c, r in re.findall(r'\$?([A-Z]{1,3})\$?(\d+)', X.xml_text(text('C'))):
            out.add(c + r)
    return out


def shared_strings(parts):
    s = parts.get('xl/sharedStrings.xml', b'').decode('utf-8')
    return [''.join(re.findall(r'<t[^>]*>(.*?)</t>', si, re.S))
            for si in re.findall(r'<si>(.*?)</si>', s, re.S)]


def run(path):
    import openpyxl
    orig = openpyxl.load_workbook(ORIG, read_only=True)
    ours = openpyxl.load_workbook(path, read_only=True)
    print(os.path.basename(path))
    parts = X.open_book(path)
    cl = part_of(parts, LOG)
    xml = parts[cl].decode('utf-8')
    shared = shared_strings(parts)
    todo = []
    for sheet, ref, why in WHY:
        was, now = orig[sheet][ref].value, ours[sheet][ref].value
        if was == now:
            continue                              # not changed in this file
        if ref in logged(xml, shared, sheet):
            print('  건너뜀 (이미 기록됨): %s %s' % (sheet, ref))
            continue
        todo.append((sheet, ref, shown(was), shown(now), why))
    if not todo:
        print('  더할 것이 없다')
        return 0
    bak = X.backup(path)
    print('  백업 %s' % os.path.basename(bak))
    r = max(int(x) for x in re.findall(r'<row r="(\d+)"', xml)) + 2
    rows = [(None, None, None, None, HEAD)] + todo
    for sheet, ref, was, now, why in rows:
        xml = X.ensure_row(xml, r)
        lines = max(len(why) // 80 + 1, len(str(was)) // 24 + 1,
                    len(str(now)) // 44 + 1)
        xml = xml.replace('<row r="%d"></row>' % r,
                          '<row r="%d" ht="%.2f" customHeight="1"></row>'
                          % (r, 15 * lines + 3))
        for col, text, st in (('B', sheet, '7'), ('C', ref, '7'),
                              ('D', was, '8'), ('E', now, '8'),
                              ('F', why, '8')):
            if text is not None:
                xml = X.set_cell(xml, col + str(r),
                                 X.cell_t(col + str(r), st, text))
        print('  %s 행 %d: %s %s' % (LOG, r, sheet or '(머리)', ref or ''))
        r += 1
    parts[cl] = xml.encode('utf-8')
    # log rows only - no formula changed, so the calculation chain stays
    # valid and the cached values stay current: keep both
    X.write_book(path, parts, drop_calcchain=False, full_calc=False)
    print('  기록 %d 줄 - 수식도 값도 손대지 않았다' % len(todo))
    return 0


if __name__ == '__main__':
    for p in (sys.argv[1:] or [XL]):
        run(os.path.abspath(p))
