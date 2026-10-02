# -*- coding: utf-8 -*-
"""One-off, applied 2026-10-02: the LED rail V_Z is now designed (sheet
16.1b) instead of assumed, so the workbook takes the sheet's value.

    CompensationNet&Check  D14  V_Z   12 -> 12.05085 V
                                      = V.R (1 + R.Z1/R.Z2), a TL431B shunt
                                        regulator, 2.495 V x (1 + 38.3/10)

D42 - D44 (the R_B window and the LED current) read D14 and keep their old
cached values until the book is opened in Excel once and saved.  The value
is computed from the sheet builder's constants, not typed here.  Cells are
edited in the zip (xlsx_patch) - openpyxl must not save this book.  The
variant workbook is the same file, so it is copied over afterwards.

    python vz_xl.py
"""
import os
import re
import shutil

import xlsx_patch as X
from an_pdf import _builder_const

HERE = os.path.dirname(os.path.abspath(__file__))
XL = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                                   'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx'))
VAR = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                                    'variants', 'L6790_workbook_7p5to1_x1.xlsx'))
LOG = 'xl/worksheets/sheet1.xml'           # CHANGELOG_rev0_6
CN = 'xl/worksheets/sheet7.xml'            # CompensationNet&Check

VZ = _builder_const('V.R') * (1 + _builder_const('R.Z1') / _builder_const('R.Z2'))
WAS = '12'
NOW = '%.5f' % VZ
MARK = 'LED rail V_Z designed'
WHY = ('LED rail V_Z designed (sheet 16.1b), 2026-10-02: a TL431B shunt '
       'regulator fed from V_out through R_Z 2.2 kOhm, divider 38.3k / 10k. '
       'A +-5 % Zener does not fit the R_B window (k 1.07 / 1.051).')


def main():
    parts = X.open_book(XL)
    xml = parts[CN].decode('utf-8')
    cur = re.search(r'<c r="D14"[^>]*><v>([^<]*)</v>', xml).group(1)
    if abs(float(cur) - float(NOW)) < 1e-9:
        print('D14 already', NOW)
    else:
        assert abs(float(cur) - float(WAS)) < 1e-12, 'D14 is %s' % cur
        xml = X.set_cell(xml, 'D14', X.cell_n('D14', X.style_of(xml, 'D14'),
                                              NOW))
        parts[CN] = xml.encode('utf-8')
    log = parts[LOG].decode('utf-8')
    if MARK not in log:
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
        rows = [(None, None, None, None, WHY),
                ('CompensationNet&Check', 'D14', WAS, NOW,
                 'V_Z = V.R (1 + R.Z1/R.Z2)')]
        for sheet, ref, was, now, why in rows:
            log = X.ensure_row(log, r)
            for col, text in (('B', sheet), ('C', ref), ('D', was), ('E', now),
                              ('F', why)):
                if text is not None:
                    log = X.set_cell(log, col + str(r),
                                     X.cell_t(col + str(r), '8', text))
            r += 1
        parts[LOG] = log.encode('utf-8')
    X.write_book(XL, parts)
    shutil.copyfile(XL, VAR)
    print('written:', XL, '\ncopied :', VAR)


if __name__ == '__main__':
    main()
