# -*- coding: utf-8 -*-
"""Put the primary rows back on the primary side of the sheet.

Supersedes fix_xl_static_device.py, which created the statically-on loss row at 82 and pointed D79 at it. Re-running that script would undo this, so it was removed; the workbook CHANGELOG keeps both entries.

B81 is the SECONDARY section title - a CONCAT that prints "Secondary Side
Power Switch...". The statically-on primary loss was added at row 82, which is
under that title, so a primary number was sitting in the secondary section.
kT.pri was at row 80, an INPUT dropped into the middle of the results block.

The primary results block has exactly four rows of space, 77 to 80, and
exactly four things to say, so:

    77  Ctot
    78  loss in one SWITCHING device
    79  loss in the STATICALLY-ON device      (was 82)
    80  Rth on the worse of the two           (was 79)
    82  cleared

kT.pri moves to row 58, directly under the section title, where it reads as
what it is: an assumption that applies to the whole primary block rather than
to one row.

    python fix_xl_rowfix.py
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

# row -> (label, name, value-or-formula, unit, style donor row)
ROWS = {
    58: ('Rdson multiplier at Tj,max - applies to this whole block',
         'kT.pri', 2, '-', 70),
    78: ('Maximum Power Losses estimation for ONE SWITCHING device',
         'Pdiss.s', '=D70*D58*D62^2', 'W', 77),
    79: ('Power loss in the STATICALLY-ON device (HB morphing mode)',
         'Pdiss.dc', '=D70*D58*(D60/D68)^2', 'W', 77),
    80: ('Estimated Rth max j-a at Tj = 125˚C, on the WORSE device',
         'Rth', '=(125-D73)/MAX(D78,D79)', '˚C/W', 77),
}
CLEAR = ['B82', 'C82', 'D82', 'E82']

LOG = (SHEET, 'D58 · D78 · D79 · D80 · D82',
       'B81 is the SECONDARY section title, and the statically-on primary loss '
       'had been added at row 82 - below it - so a primary number sat inside '
       'the secondary section. kT.pri was at row 80, an input dropped into the '
       'middle of the primary results block.',
       'The primary results block, rows 77 to 80, now reads Ctot, loss in one '
       'SWITCHING device, loss in the STATICALLY-ON device, and Rth on the '
       'worse of the two. Row 82 is cleared. kT.pri moved to row 58, under the '
       'section title, where it applies to the whole block.',
       'No value changes: D78 2.850 W, D79 5.700 W (was D82), D80 17.54 C/W. '
       'Nothing outside this block read any of the moved cells, so only the '
       'workbook-to-SMath comparison had to follow (P.mos_dev now maps to D79).')


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

    for row, (label, name, val, unit, donor) in sorted(ROWS.items()):
        xml = X.ensure_row(xml, row)
        for col, v in (('B', label), ('C', name), ('D', val), ('E', unit)):
            ref = col + str(row)
            st = X.style_of(xml, '%s%d' % (col, donor))
            if col == 'D' and isinstance(v, str) and v.startswith('='):
                cell = X.cell_f(ref, st, v[1:])
            elif col == 'D':
                cell = X.cell_n(ref, st, v)
            else:
                cell = X.cell_t(ref, st, v)
            xml = X.set_cell(xml, ref, cell)
        print('  %2d  %-9s %-26s %s' % (row, name, str(val)[:26], label[:38]))

    for ref in CLEAR:
        xml = X.set_cell(xml, ref,
                         '<c r="%s" s="%s"/>' % (ref, X.style_of(xml, ref)))
    print('  82  비움  %s' % ' '.join(CLEAR))
    parts[p] = xml.encode('utf-8')

    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    m = re.search(r'<c r="C(\d+)"[^>]*><is><t[^>]*>%s<' % re.escape(LOG[1]), xml)
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
    print('예상: D78 2.850 W · D79 5.700 W · D80 17.54 C/W · D82 빈칸')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
