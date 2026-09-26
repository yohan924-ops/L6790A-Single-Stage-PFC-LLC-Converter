# -*- coding: utf-8 -*-
"""Lr14 copy only: set the tank picks of the ST workbook to L.r 14 uH and
L.m 25.46 uH ('Res. Tank Design' F44, F45) and log them in CHANGELOG_rev0_6.

Cells are edited in the zip (xlsx_patch) - openpyxl must not save this book.
The formulas that depend on F44/F45 keep their old cached values until the
book is opened in Excel once and saved (full_calc is set, so Excel
recalculates on open).  The variant workbook is the same file as the
canonical one, so it is copied over afterwards.

    python lr14_xl.py
"""
import os
import re
import shutil

import xlsx_patch as X

HERE = os.path.dirname(os.path.abspath(__file__))
XL = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                                   'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx'))
VAR = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                                    'variants', 'L6790_workbook_7p5to1.xlsx'))
TANK = 'xl/worksheets/sheet4.xml'          # Res. Tank Design
LOG = 'xl/worksheets/sheet1.xml'           # CHANGELOG_rev0_6
PICKS = (('F44', '11', '14', 'L.r leakage (resonant) inductance, uH'),
         ('F45', '20', '25.46', 'L.m magnetizing inductance, uH'))
WHY = ('Lr14 copy, 2026-09-26 (user): tank L.r 14 uH / L.m 25.46 uH / C.r '
       '100 nF. lambda stays 0.55, so n is unchanged; f.r falls to 134.5 kHz. '
       'The example transformer (E 60/22/16) then fills its window exactly.')


def main():
    parts = X.open_book(XL)
    tank = parts[TANK].decode('utf-8')
    for ref, was, now, _ in PICKS:
        cur = re.search(r'<c r="%s"[^>]*><v>([^<]*)</v>' % ref, tank).group(1)
        if cur == now:
            print('%s already %s' % (ref, now))
            continue
        assert cur == was, '%s is %s, expected %s' % (ref, cur, was)
        tank = X.set_cell(tank, ref, X.cell_n(ref, X.style_of(tank, ref), now))
    parts[TANK] = tank.encode('utf-8')
    log = parts[LOG].decode('utf-8')
    if 'Lr14 copy' not in log:
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
        rows = [(None, None, None, None, WHY)] + [
            ('Res. Tank Design', ref, was, now, what)
            for ref, was, now, what in PICKS]
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
