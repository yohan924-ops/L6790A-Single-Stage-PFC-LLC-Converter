# -*- coding: utf-8 -*-
"""Say, in the workbook, that the auxiliary-ratio check does not apply here.

`Device Setting` D84 computes k.naux = n.aux_sec_max / n.aux and labels it
"(>1)", so it reads as a pass/fail. It is 0.28. Nothing on the sheet says
why that is acceptable, and B84 - the column every other row of the block
uses for its description - is EMPTY, so the row arrives with a failing
number and no explanation.

The check asks whether V.aux stays under D74, "DS_Maximum auxiliary
voltage" = 25 V, which is the VCC pin rating. It is the right question for
the usual arrangement, where the auxiliary winding supplies VCC. It is the
wrong question here: VCC comes from an external 12 V rail and this winding
feeds nothing but the ZCD divider, so its voltage is free and only the turn
count constrains it.

This is exactly the kind of gap that C.18 was - a value that is right in one
document and unexplained in another, so the next person re-derives it and
reaches a different answer. One cell, and the changelog row that records it.

    python fix_xl_auxnote.py
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

CELL = 'B84'
TEXT = ('Auxiliary ratio check - DOES NOT APPLY when VCC is supplied '
        'externally (this design: 12 V rail). The winding then only senses '
        'ZCD and its voltage is free; only N.aux has to be a whole number.')

LOG = ('Device Setting', 'B84',
       'D84 = k.naux is labelled "(>1)" and reads 0.28, and B84 - the '
       'description cell every other row in the block uses - was empty. The '
       'check asks whether the auxiliary voltage stays under D74 = 25 V, the '
       'VCC pin rating, which is the right question only when the auxiliary '
       'winding supplies VCC.',
       'B84 now states that the check does not apply when VCC is fed '
       'externally, as it is here (12 V rail, auxiliary winding senses ZCD '
       'only). No formula or value changed - D83, D84 and F83 are untouched, '
       'so the workbook still agrees with the SMath sheet, which carries the '
       'same note at section 14 and marks k.auxr and k.VCC "DOES NOT APPLY" '
       'in its section 17.1 review.')


def part_of(parts, name):
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                          parts['xl/_rels/workbook.xml.rels'].decode('utf-8')))
    for nm, r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
        if nm.replace('&amp;', '&') == name:
            return 'xl/' + rid[r].lstrip('/')
    raise KeyError(name)


def main():
    bak = X.backup(XL)
    print('백업 %s' % os.path.basename(bak))
    parts = X.open_book(XL)

    p = part_of(parts, 'Device Setting')
    xml = parts[p].decode('utf-8')
    xml = X.ensure_row(xml, 84)
    # borrow the style of the label cell directly above, so it matches
    st = X.style_of(xml, 'B83')
    xml = X.set_cell(xml, CELL, X.cell_t(CELL, st, TEXT))
    parts[p] = xml.encode('utf-8')
    print('  %s = %s' % (CELL, TEXT[:64] + '...'))

    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    hay = xml + parts.get('xl/sharedStrings.xml', b'').decode('utf-8')
    if 'Auxiliary ratio check - DOES NOT APPLY' in hay:
        print('  CHANGELOG 건너뜀 (이미 기록돼 있다)')
    else:
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', xml)) + 1
        xml = X.ensure_row(xml, r)
        for col, text, st in (('B', LOG[0], '7'), ('C', LOG[1], '7'),
                              ('D', LOG[2], '8'), ('E', LOG[3], '8')):
            xml = X.set_cell(xml, col + str(r),
                             X.cell_t(col + str(r), st, text))
        parts[cl] = xml.encode('utf-8')
        print('  CHANGELOG_rev0_6 행 %d 에 기록' % r)

    X.write_book(XL, parts)
    print()
    print('값은 하나도 안 바뀐다 - 설명 셀 하나와 기록 한 줄뿐이다.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
