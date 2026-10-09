# -*- coding: utf-8 -*-
"""Copy of the three-core (5:2 x 3) workbook for a 200 W bench test with the
transformers the vendor actually wound (2026-10-09, user measurement).

Measured per unit, LCR 100 kHz / 1 V, series Ls:
    1-4 open, all other windings open          10.3 uH   (all three units)
    1-4, 5-9 and 7-11 shorted, 2-3 open        1.9 / 2.0 / 1.8 uH
    1-4, one half shorted (one unit)           ~2.0 uH where both-shorted read 1.8
Three primaries in series, so
    L.r = 1.9 + 2.0 + 1.8 = 5.7 uH   (both halves shorted; one half alone reads
                                      about 10 % more, which only adds margin)
    L.m = 3 x 10.3 - 5.7  = 25.2 uH
    n   = 7.5 / sqrt(1 + L.r/L.m) = 6.773   (same rule as F9 in pq50_xl.py)

C.r stays 100 nF and R.T 11 kOhm: of 68-150 nF this is the one that keeps the
264 Vac line-peak frequency at least 12 % under f.Max with the lowest primary
current and flux (scratch scan, 2026-10-09).  Pout 657.5 -> 200 W.

The frozen source book is not touched; the copy is written beside it.  Cells
are edited in the zip (xlsx_patch) - openpyxl must not save this book.
Dependent formulas keep their old cached values until the copy is opened in
Excel once (full_calc is set, so Excel recalculates on open).

    python measured200_xl.py
"""
import os
import re

import xlsx_patch as X

HERE = os.path.dirname(os.path.abspath(__file__))
VAR = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet', 'variants'))
SRC = os.path.join(VAR, 'L6790_workbook_7p5to1.xlsx')
DST = os.path.join(VAR, 'L6790_workbook_7p5to1_measured_200W.xlsx')

L_R, L_OPEN = 5.7, 3 * 10.3
L_M = round(L_OPEN - L_R, 2)
N_EFF = round(7.5 / (1 + L_R / L_M) ** 0.5, 4)

PICKS = (('Design Spec', 'D27', '657.5', '200', 'Pout, W - 200 W bench test'),
         ('Res. Tank Design', 'F9', '6.0241', str(N_EFF),
          'n effective = 7.5/sqrt(1 + L.r/L.m), measured lambda %.3f' % (L_R / L_M)),
         ('Res. Tank Design', 'F43', '100', '100', 'C.r, nF - kept (best of 68-150 nF at 200 W)'),
         ('Res. Tank Design', 'F44', '11', str(L_R), 'L.r, uH - measured 1.9+2.0+1.8'),
         ('Res. Tank Design', 'F45', '20', str(L_M), 'L.m, uH - 3 x 10.3 measured open minus L.r'),
         ('Device Setting', 'F24', '11', '11', 'R.T, kOhm - kept (f.Min 92.3 kHz > f.o 90.5 kHz)'))
MARK = 'measured 200 W copy'
WHY = ('%s, 2026-10-09 (user): the vendor-wound 5:2 transformers measure 10.3 uH '
       'open and 1.9/2.0/1.8 uH leakage (secondaries shorted) per unit, about half '
       'the 3.67 uH the tank was designed for. Tank re-checked for a 200 W test; '
       'stay out of 150-180 Vac, where the full-bridge line peak needs more than f.Max.'
       % MARK)


def sheet_parts(parts):
    """sheet name -> 'xl/worksheets/sheetN.xml'"""
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rels = parts['xl/_rels/workbook.xml.rels'].decode('utf-8')
    rid = {m.group(1): m.group(2) for m in
           re.finditer(r'<Relationship[^>]*Id="([^"]+)"[^>]*Target="([^"]+)"', rels)}
    out = {}
    for m in re.finditer(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', wb):
        name = m.group(1).replace('&amp;', '&')
        out[name] = 'xl/' + rid[m.group(2)].lstrip('/').replace('xl/', '')
    return out


def main():
    parts = X.open_book(SRC)
    where = sheet_parts(parts)
    for sheet, ref, was, now, _ in PICKS:
        part = where[sheet]
        xml = parts[part].decode('utf-8')
        cur = re.search(r'<c r="%s"[^>]*><v>([^<]*)</v>' % ref, xml).group(1)
        assert abs(float(cur) - float(was)) < 1e-9, '%s!%s is %s, expected %s' % (sheet, ref, cur, was)
        if was != now:
            xml = X.set_cell(xml, ref, X.cell_n(ref, X.style_of(xml, ref), now))
            parts[part] = xml.encode('utf-8')
    log_part = where['CHANGELOG_rev0_6']
    log = parts[log_part].decode('utf-8')
    if MARK not in log:
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
        rows = [(None, None, None, None, WHY)] + [p for p in PICKS if p[2] != p[3]]
        for sheet, ref, was, now, why in rows:
            log = X.ensure_row(log, r)
            for col, text in (('B', sheet), ('C', ref), ('D', was), ('E', now), ('F', why)):
                if text is not None:
                    log = X.set_cell(log, col + str(r), X.cell_t(col + str(r), '8', text))
            r += 1
        parts[log_part] = log.encode('utf-8')
    X.write_book(DST, parts)
    print('written:', DST)
    print('L.r %.2f uH  L.m %.2f uH  n %.4f' % (L_R, L_M, N_EFF))


if __name__ == '__main__':
    main()
