# -*- coding: utf-8 -*-
"""Bring the 200 W bench workbook in line with the 670 W book where the two describe
the SAME hardware (2026-10-18, user: "match what should match between them").

    Calculation Excel Sheet/variants/BENCH_200W_LGE_workbook_unencrypted.xlsx

Changed (was -> now):
    Design Spec       D47  t.D      270 -> 220 ns   design dead time of the sheets (the IC's
                                                     is adaptive, 40-420 ns); LGE typed 270
    Design Spec       D29  h         30 -> 37 mm    Rubycon PX 6800 uF / 35 V is 18 x 35.5
    Power Components  D25  ESR.single 30 -> 50.7 mohm  tan d 0.26 at 120 Hz / (2 pi 120 Hz
                                                     6800 uF) - the only ESR the PX sheet gives
    Power Components  D58  kT.pri   1.8 -> 1.9      STO60N045DM9 datasheet (fet_xl.py, 81st round)
    Power Components  D72  Cpar      10 -> 2600 pF  100 pF layout + 2200 pF leg snubber + 2 x
                                                     150 pF drain-source, the same parasitic the
                                                     book's c.HB 5529 pF already contains
Left as they are, on purpose: C.r, L.r, L.m, n, R.T, R.ZCD.H, n.aux/n.sec (measured
transformer and fitted parts), BM grounded, R.CFG 13 k, C.in, 5 x 6800 uF, 5 x 10 uF
ceramic, the compensation set (its plant is the 200 W one), fl 50 Hz (the test).

    python bench200_sync_xl.py
"""
import os
import re

import xlsx_patch as X
from lge200_xl import current, shared_strings
from measured200_xl import sheet_parts

HERE = os.path.dirname(os.path.abspath(__file__))
XL = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet', 'variants',
                                   'BENCH_200W_LGE_workbook_unencrypted.xlsx'))
MARK = 'bench book brought in line with the 670 W book'
PICKS = (('Design Spec', 'D47', '270', '220', 't.D, ns - the design dead time of the SMath sheets and the 670 W book '
          '(the IC dead time is adaptive, 40-420 ns); LGE typed 270'),
         ('Design Spec', 'D29', '30', '37', 'h, mm - Rubycon PX 6800 uF / 35 V, 18 x 35.5 mm, L + alpha max 37'),
         ('Power Components', 'D25', '30', '50.7', 'ESR.single, mOhm - PX tan d 0.26 (0.14 + 0.02 per 1000 uF over 1000) at 120 Hz; '
          'no ESR at f.sw in the PX sheet, so an upper bound'),
         ('Power Components', 'D58', '1.8', '1.9', 'kT.pri - STO60N045DM9 datasheet, as the guide and 670 W books (fet_xl.py)'),
         ('Power Components', 'D72', '10', '2600', 'Cpar, pF - 100 layout + 2200 leg snubber (C115/C117) + 2 x 150 drain-source '
          '(C127-C130): the parasitic that c.HB 5529 pF (D46) already contains; feeds D77 for the dv/dt'))


def main():
    parts = X.open_book(XL)
    sp = sheet_parts(parts)
    sst = shared_strings(parts)
    log = parts[sp['CHANGELOG_rev0_6']].decode('utf-8')
    if MARK in log:
        print('already applied')
        return
    for sheet, ref, was, now, _ in PICKS:
        part = sp[sheet]
        xml = parts[part].decode('utf-8')
        cur = current(xml, ref, sst)
        assert abs(float(cur) - float(was)) < 1e-9, '%s!%s is %s, expected %s' % (sheet, ref, cur, was)
        xml = X.set_cell(xml, ref, X.cell_n(ref, X.style_of(xml, ref), now))
        parts[part] = xml.encode('utf-8')
        print('%-17s %-4s %6s -> %s' % (sheet, ref, was, now))
    r = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
    why = ('%s, 2026-10-18 (user): the inputs that describe the same board hardware in both books '
           'now read the same; the measured transformer, the fitted control parts and the 200 W '
           'output bank stay as the bench has them.' % MARK)
    for sheet, ref, was, now, text in [(None, None, None, None, why)] + [p for p in PICKS]:
        log = X.ensure_row(log, r)
        for col, t in (('B', sheet), ('C', ref), ('D', was), ('E', now), ('F', text)):
            if t is not None:
                log = X.set_cell(log, col + str(r), X.cell_t(col + str(r), '8', t))
        r += 1
    parts[sp['CHANGELOG_rev0_6']] = log.encode('utf-8')
    X.write_book(XL, parts)
    print('written:', XL)


if __name__ == '__main__':
    main()
