# -*- coding: utf-8 -*-
"""Lr14 copy only: set the tank and timing picks of the ST workbook for the
ETD 54/28/19 transformer (2026-09-27) and log them in CHANGELOG_rev0_6.

    Res. Tank Design  F43  C.r  100   -> 200    nF
                      F44  L.r  14    -> 23.4   uH
                      F45  L.m  25.46 -> 42.55  uH
    Device Setting    F24  R.T  11    -> 23.2   kOhm

Cells are edited in the zip (xlsx_patch) - openpyxl must not save this book.
The formulas that depend on them keep their old cached values until the book
is opened in Excel once and saved (full_calc is set, so Excel recalculates on
open).  The variant workbook is the same file as the canonical one, so it is
copied over afterwards.

    python etd54_xl.py
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
LOG = 'xl/worksheets/sheet1.xml'           # CHANGELOG_rev0_6
PICKS = (('Res. Tank Design', 'xl/worksheets/sheet4.xml', 'F43', '100', '200',
          'C.r resonant capacitor, nF'),
         ('Res. Tank Design', 'xl/worksheets/sheet4.xml', 'F44', '14', '23.4',
          'L.r leakage (resonant) inductance, uH'),
         ('Res. Tank Design', 'xl/worksheets/sheet4.xml', 'F45', '25.46', '42.55',
          'L.m magnetizing inductance, uH'),
         ('Device Setting', 'xl/worksheets/sheet6.xml', 'F24', '11', '23.2',
          'R.T timing resistor, kOhm'))
MARK = 'ETD 54/28/19'
WHY = ('Lr14 copy, 2026-09-27 (user): the transformer is TDK ETD 54/28/19 on '
       'its catalogue former B66396W with a 2.0 mm partition and nothing left '
       'empty; its leakage, 23.4 uH, is the tank L.r. lambda stays 0.55 (L.m '
       '42.55 uH), C.r 200 nF keeps Q near 0.8; f.r 73.6 kHz, f.o 43.8 kHz, '
       'so R.T moves to 23.2 kOhm (f.Min 44.8 kHz).')


def main():
    parts = X.open_book(XL)
    for _, part, ref, was, now, _ in PICKS:
        xml = parts[part].decode('utf-8')
        cur = re.search(r'<c r="%s"[^>]*><v>([^<]*)</v>' % ref, xml).group(1)
        if cur == now:
            print('%s already %s' % (ref, now))
            continue
        assert cur == was, '%s is %s, expected %s' % (ref, cur, was)
        xml = X.set_cell(xml, ref, X.cell_n(ref, X.style_of(xml, ref), now))
        parts[part] = xml.encode('utf-8')
    log = parts[LOG].decode('utf-8')
    if MARK not in log:
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
        rows = [(None, None, None, None, WHY)] + [
            (sheet, ref, was, now, what)
            for sheet, _, ref, was, now, what in PICKS]
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
