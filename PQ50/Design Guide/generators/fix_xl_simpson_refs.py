# -*- coding: utf-8 -*-
"""Four design cells still read the theta=pi/4 column, patched by hand on top.

When C.18 was closed, the CC sheet gained a Simpson integral in column J and
three design cells were re-pointed at it:

    Res. Tank Design D65 -> CC!J29     Res. Tank Design D67 -> CC!J25
    Power Components D28 -> CC!J31

Four others were not. D60, D61, D84 and D85 still read CC!C29, C30, C25 and
C26 - the SINGLE theta=pi/4 sample - and carry a hand-typed yellow override in
column F holding the line-cycle number copied out of the SMath sheet. That
override was added before the Simpson columns existed and nothing removed it
afterwards.

It is the C.27 defect: a typed constant sitting on top of a live reference.
Change an input and J25/J26/J29/J30 follow while F60/F61/F84/F85 do not, so
the design quietly keeps using yesterday's numbers - and the typed values are
rounded besides (10.9 against 10.8976, 28.31 against 28.3008).

    python fix_xl_simpson_refs.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx_patch as X                                               # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')
SHEET = 'Power Components'

# ref -> (live Simpson cell, what it is, the hand-typed value it replaces)
MOVE = {
    'D60': ('CC!J29', 'primary rms, whole tank',      '10.9'),
    'D61': ('CC!J30', 'primary rms per switch position', '7.707'),
    'D84': ('CC!J25', 'secondary rms per winding',    '28.31'),
    'D85': ('CC!J26', 'secondary rms per leg',        '28.31'),
}
CLEAR = ['F60', 'F61', 'F84', 'F85']

LABELS = {
    'C60': 'Ipri.rms (line cycle, Simpson)',
    'C61': 'Imos.rms per position (line cycle, Simpson)',
    'C84': 'Isec.rms per winding (line cycle, Simpson)',
    'C85': 'Idiode.rms per leg (line cycle, Simpson)',
}

LOG = (SHEET, 'D60 · D61 · D84 · D85 · F60 · F61 · F84 · F85',
       'These four read CC!C29, C30, C25 and C26 - the SINGLE theta=pi/4 sample '
       '- with a hand-typed yellow override in column F carrying the line-cycle '
       'value copied from the SMath sheet. The override dates from before the '
       'C.18 fix, which gave CC a Simpson integral in column J and re-pointed '
       'Res. Tank Design D65 and D67 and Power Components D28 at it. These four '
       'were missed.',
       'D60 -> CC!J29, D61 -> CC!J30, D84 -> CC!J25, D85 -> CC!J26, and the four '
       'F overrides cleared so nothing is typed by hand any more. Column C '
       'labels now say "line cycle, Simpson" instead of "@theta=pi/4".',
       'This is the C.27 pattern: a typed constant on top of a live reference. '
       'Change an input and the J column follows while the typed F cells do '
       'not, so the design silently keeps yesterday\'s numbers. The typed '
       'values were rounded as well - 10.9 against 10.8976 and 28.31 against '
       '28.3008 - so the loss and rating rows built on them were out by up to '
       '0.04 %. Nothing moves visibly today because the typed values were '
       'correct when they were typed; the point is that they could not stay '
       'correct.')


def part_of(parts, name):
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                          parts['xl/_rels/workbook.xml.rels'].decode('utf-8')))
    for nm, r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
        if nm.replace('&amp;', '&') == name:
            return 'xl/' + rid[r].lstrip('/')
    raise KeyError(name)


def main():
    print('백업 %s' % os.path.basename(X.backup(XL)))
    parts = X.open_book(XL)
    p = part_of(parts, SHEET)
    xml = parts[p].decode('utf-8')

    for ref, (src, what, was) in MOVE.items():
        xml = X.set_cell(xml, ref, X.cell_f(ref, X.style_of(xml, ref), src))
        print('  %-5s -> %-8s %-32s (손입력 %s 제거)' % (ref, src, what, was))
    for ref in CLEAR:
        xml = X.set_cell(xml, ref,
                         '<c r="%s" s="%s"/>' % (ref, X.style_of(xml, ref)))
    print('  노란 손입력 %d칸 삭제  %s' % (len(CLEAR), ' '.join(CLEAR)))
    for ref, text in LABELS.items():
        xml = X.set_cell(xml, ref, X.cell_t(ref, X.style_of(xml, ref), text))
    parts[p] = xml.encode('utf-8')

    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    m = re.search(r'<c r="C(\d+)"[^>]*><is><t[^>]*>D60 · D61', xml)
    r = int(m.group(1)) if m else \
        max(int(x) for x in re.findall(r'<row r="(\d+)"', xml)) + 1
    xml = X.ensure_row(xml, r)
    for col, text, st in (('B', LOG[0], '7'), ('C', LOG[1], '7'),
                          ('D', LOG[2], '8'), ('E', LOG[3], '8'),
                          ('F', LOG[4], '8')):
        xml = X.set_cell(xml, col + str(r), X.cell_t(col + str(r), st, text))
    print('  CHANGELOG 행 %d' % r)
    parts[cl] = xml.encode('utf-8')

    X.write_book(XL, parts)
    print()
    print('예상: D60 10.8976 · D61 7.70575 · D84 28.3008 · D85 28.3008 A')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
