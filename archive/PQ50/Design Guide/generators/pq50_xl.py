# -*- coding: utf-8 -*-
"""PQ50 copy only: set the tank and timing picks of the ST workbook for the
single TDK PQ 50/50 15 : 2 transformer (2026-09-30) and log them in
CHANGELOG_rev0_6.  The book arrives from the Lr14 copy with the ETD 54 picks.

    Res. Tank Design  F43  C.r  200    -> 180   nF
                      F44  L.r  23.4   -> 25    uH
                      F45  L.m  42.55  -> 45    uH
    Device Setting    F24  R.T  23.2   -> 21.5  kOhm
    Res. Tank Design  F9   n    6.0241 -> 6.0134  (n.T / sqrt(1 + L.r/L.m):
                                λ is 25/45 = 0.556 now, it was 0.55)

Cells are edited in the zip (xlsx_patch) - openpyxl must not save this book.
The formulas that depend on them keep their old cached values until the book
is opened in Excel once and saved (full_calc is set, so Excel recalculates on
open).  The variant workbook is the same file as the canonical one, so it is
copied over afterwards.

    python pq50_xl.py
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
PICKS = (('Res. Tank Design', 'xl/worksheets/sheet4.xml', 'F43', '200', '180',
          'C.r resonant capacitor, nF'),
         ('Res. Tank Design', 'xl/worksheets/sheet4.xml', 'F44', '23.4', '25',
          'L.r leakage (resonant) inductance, uH'),
         ('Res. Tank Design', 'xl/worksheets/sheet4.xml', 'F45', '42.55', '45',
          'L.m magnetizing inductance, uH'),
         ('Device Setting', 'xl/worksheets/sheet6.xml', 'F24', '23.2', '21.5',
          'R.T timing resistor, kOhm'),
         ('Res. Tank Design', 'xl/worksheets/sheet4.xml', 'F9', '6.0241', '6.0134',
          'n effective turns ratio = 7.5/sqrt(1 + L.r/L.m), lambda 25/45'))
MARK = 'PQ 50/50'
WHY = ('PQ50 copy, 2026-09-30 (user): the transformer is ONE TDK PQ 50/50 '
       '(N97) on its catalogue former B65982E with a 3.0 mm partition, 15 : 2 '
       '(NP1 3 x 5 T TIW-Litz d 2.9, NS2 then NS3 2 T layers Litz d 4.0). '
       '2-D FEM leakage 23.3-26.4 uH, so L.r 25 uH; C.r 180 nF (E12), '
       'L.m 45 uH (lambda 0.556), R.T 21.5 kOhm (E96, f.Min 48.3 kHz).')


def main():
    parts = X.open_book(XL)
    for _, part, ref, was, now, _ in PICKS:
        xml = parts[part].decode('utf-8')
        cur = re.search(r'<c r="%s"[^>]*><v>([^<]*)</v>' % ref, xml).group(1)
        if abs(float(cur) - float(now)) < 1e-9:
            print('%s already %s' % (ref, now))
            continue
        assert abs(float(cur) - float(was)) < 1e-9, '%s is %s, expected %s' % (ref, cur, was)
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
