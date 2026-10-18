# -*- coding: utf-8 -*-
"""Composite tank-current peak over the load range, added to a workbook (2026-10-18,
user: "does the load current add to the magnetizing peak, or not? compute it").

Below resonance the magnetizing current is a triangle that peaks at the END of the
half cycle and the reflected load current a half sine that peaks in the MIDDLE.
While 2*I.Lm/(pi*I.trafo) >= 1 (light load) the sum peaks at the magnetizing value
alone; beyond that the load raises the peak (sheet section 9, [79] - the same
formula the ST tool already carries in Device Setting D32 for 100 % load).  This
block repeats it at 0 / 25 / 50 / 75 / 100 % load at the line peak of Vin.min, the
frequency re-solved at each load with the closed-form cubic of sheet section 8
(the FHA gain equation in x = 1/fn^2, middle root), so every column is a live
formula on the book's own inputs - nothing is typed.  It is sheet section 9b in
the SMath builder; xl_sm_compare reads the two against each other.

Rows 116-141 of 'Device Setting' (empty in every copy of the rev0_6 book):

    117  ld        load fraction                       0  0.25  0.5  0.75  1
    118-127        Q, the cubic (q a2 a1 a0 p r ang x) and f.n
    128  f.sw      switching frequency at the line peak            kHz
    129-133        f.ss, I.out.inst, I.sec.pk, I.trafo.pk, I.lm.pk
    134-135        r.mix = 2 I.lm / (pi I.trafo), x.pk
    136  I.Lr.pk   composite peak                                    A
    137  r.add     composite / magnetizing (1 = the load adds nothing)
    138            which one sets the peak (text)
    139  m.OCP1    OCP1 trip current (D49) / composite peak
    140  I.lm.zc   magnetizing peak at the line zero crossing (f.Min, any load), OCP1 margin
    141            check: the 100 % column against D32 (RTC grid frequency)

    python peak_xl.py <workbook.xlsx>        idempotent - skips a book that has the block
"""
import os
import re
import sys

import xlsx_patch as X
from measured200_xl import sheet_parts

MARK = 'composite peak over the load range'
R0 = 116
LOADS = (0, 0.25, 0.5, 0.75, 1)
COLS = 'DEFGH'

RT = "'Res. Tank Design'!"
DS = "'Design Spec'!"
PC = "'Preliminary Calculation'!"
n = RT + '$D$42'
lam = RT + '$D$50'
Mpk = RT + '$D$10'
Qpk = '(%s$D$52/%s$D$17)' % (RT, RT)
fr = RT + '$D$55'
Lm = 'IF(%s$F$45,%s$F$45,%s$D$45)' % (RT, RT, RT)
Vo = '(%s$D$95+%s$D$107*%s$D$106)' % (DS, DS, DS)
Iout = PC + '$D$7'


def rows(c):
    """(row, name, formula, unit) for column letter c"""
    r = lambda k: '%s%d' % (c, R0 + k)
    return [
        (2, 'Q', '%s*%s' % (Qpk, r(1)), '-'),
        (3, 'q', '%s^2' % r(2), '-'),
        (4, 'a2', '(%s-2*%s*(1+%s))/%s^2' % (r(3), lam, lam, lam), '-'),
        (5, 'a1', '((1+%s)^2-2*%s-1/%s^2)/%s^2' % (lam, r(3), Mpk, lam), '-'),
        (6, 'a0', '%s/%s^2' % (r(3), lam), '-'),
        (7, 'p', '%s-%s^2/3' % (r(5), r(4)), '-'),
        (8, 'r', '2*%s^3/27-%s*%s/3+%s' % (r(4), r(4), r(5), r(6)), '-'),
        (9, 'ang', 'ACOS(3*%s/(2*%s)*SQRT(-3/%s))/3' % (r(8), r(7), r(7)), 'rad'),
        (10, 'x', '2*SQRT(-%s/3)*COS(%s-2*PI()/3)-%s/3' % (r(7), r(9), r(4)), '-'),
        (11, 'f.n', '1/SQRT(%s)' % r(10), '-'),
        (12, 'f.sw', '%s*%s' % (r(11), fr), 'kHz'),
        (13, 'f.ss', 'MAX(%s,%s)' % (r(12), fr), 'kHz'),
        (14, 'I.out.inst', '2*%s*%s' % (Iout, r(1)), 'A'),
        (15, 'I.sec.pk', 'PI()*(%s/%s)*%s/(1-COS(PI()*%s/%s))' % (fr, r(12), r(14), fr, r(13)), 'A'),
        (16, 'I.trafo.pk', '%s/%s' % (r(15), n), 'A'),
        (17, 'I.lm.pk', '0.25*%s*%s/(%s*10^(-6)*%s*1000)' % (n, Vo, Lm, r(13)), 'A'),
        (18, 'r.mix', 'IF(%s>0,2*%s/(PI()*%s),1E+9)' % (r(16), r(17), r(16)), '-'),
        (19, 'x.pk', 'ACOS(-MIN(%s,0.999999999))/PI()' % r(18), '-'),
        (20, 'I.Lr.pk', 'IF(%s>=1,%s,%s*(2*%s-1)+%s*SIN(PI()*%s))'
         % (r(18), r(17), r(17), r(19), r(16), r(19)), 'A'),
        (21, 'r.add', '%s/%s' % (r(20), r(17)), '-'),
        (22, 'set by', 'IF(%s>=1,"magnetizing alone","load + magnetizing")' % r(18), ''),
        (23, 'm.OCP1', '$D$49/%s' % r(20), '-'),
    ]


LABELS = {
    1: 'Load fraction at the line peak of Vin.min  [sheet 9b - ADDED 2026-10-18]',
    2: 'Quality factor at that load (Q.pk x ld)', 3: 'q = Q^2  (cubic of sheet section 8)',
    4: 'a2', 5: 'a1  (with 1/M.pk^2 of Res. Tank Design D10)', 6: 'a0',
    7: 'p = a1 - a2^2/3', 8: 'r', 9: 'ang (middle root)', 10: 'x = 1/fn^2', 11: 'Normalised frequency',
    12: 'Switching frequency at the line peak', 13: 'Frequency of the magnetizing ramp, max(f.sw, f.r)',
    14: 'Instantaneous output current at the line peak', 15: 'Secondary peak current',
    16: 'Reflected load current peak', 17: 'Magnetizing current peak (trapezoid below f.r)',
    18: 'r.mix = 2 I.lm / (pi I.trafo): >= 1 means the peak IS the magnetizing current',
    19: 'Position of the composite peak in the half cycle', 20: 'COMPOSITE TANK CURRENT PEAK  [79]',
    21: 'Composite over magnetizing (1.000 = the load adds nothing)',
    22: 'What sets the peak', 23: 'OCP1 margin: I.OCP1 (D49) over the composite peak',
}


def main(path):
    parts = X.open_book(path)
    sp = sheet_parts(parts)
    dev, log = sp['Device Setting'], sp['CHANGELOG_rev0_6']
    xml = parts[dev].decode('utf-8')
    if MARK in parts[log].decode('utf-8'):          # the rows exist as empty styled cells
        print('block already present in', os.path.basename(path))
        return
    s_lab, s_num, s_nam, s_unit = (X.style_of(xml, 'B32'), X.style_of(xml, 'D32'),
                                   X.style_of(xml, 'C32'), X.style_of(xml, 'E32'))
    s_hdr = X.style_of(xml, 'B35')
    put = lambda ref, cell: X.set_cell(xml, ref, cell)
    xml = X.ensure_row(xml, R0)
    xml = put('B%d' % R0, X.cell_t('B%d' % R0, s_hdr,
              'Composite tank-current peak over the load range - does the load current add '
              'to the magnetizing peak?  [79], SMath sheet 9b - ADDED 2026-10-18'))
    for k in range(1, 24):
        xml = X.ensure_row(xml, R0 + k)
        xml = put('B%d' % (R0 + k), X.cell_t('B%d' % (R0 + k), s_lab, LABELS[k]))
    for c, ld in zip(COLS, LOADS):
        xml = put('%s%d' % (c, R0 + 1), X.cell_n('%s%d' % (c, R0 + 1), s_num, ld))
        for k, name, f, unit in rows(c):
            xml = put('%s%d' % (c, R0 + k), X.cell_f('%s%d' % (c, R0 + k), s_num, f))
            if c == 'D':
                xml = put('C%d' % (R0 + k), X.cell_t('C%d' % (R0 + k), s_nam, name))
                xml = put('I%d' % (R0 + k), X.cell_t('I%d' % (R0 + k), s_unit, unit))
    xml = put('C%d' % (R0 + 1), X.cell_t('C%d' % (R0 + 1), s_nam, 'ld'))
    xml = put('I%d' % (R0 + 1), X.cell_t('I%d' % (R0 + 1), s_unit, '-'))
    # the floor: magnetizing peak at the line zero crossing (f.Min, any load)
    r = R0 + 24
    xml = X.ensure_row(xml, r)
    xml = put('B%d' % r, X.cell_t('B%d' % r, s_lab,
              'Magnetizing peak at the line ZERO crossing - f.Min (D28), below f.r, at ANY load; '
              'then the OCP1 margin over it'))
    xml = put('C%d' % r, X.cell_t('C%d' % r, s_nam, 'I.lm.zc'))
    xml = put('D%d' % r, X.cell_f('D%d' % r, s_num,
              '0.25*%s*%s/(%s*10^(-6)*MAX($D$28,%s)*1000)' % (n, Vo, Lm, fr)))
    xml = put('E%d' % r, X.cell_f('E%d' % r, s_num, '$D$49/D%d' % r))
    xml = put('I%d' % r, X.cell_t('I%d' % r, s_unit, 'A, -'))
    r = R0 + 25
    xml = X.ensure_row(xml, r)
    xml = put('B%d' % r, X.cell_t('B%d' % r, s_lab,
              'Check: the 100 % column against D32, which takes its frequency from the RTC '
              'grid (f.r/69 steps) - expect 0.99-1.01'))
    xml = put('C%d' % r, X.cell_t('C%d' % r, s_nam, 'H%d / D32' % (R0 + 20)))
    xml = put('D%d' % r, X.cell_f('D%d' % r, s_num, 'H%d/D32' % (R0 + 20)))
    parts[dev] = xml.encode('utf-8')

    lg = parts[log].decode('utf-8')
    if MARK not in lg:
        rr = max(int(x) for x in re.findall(r'<row r="(\d+)"', lg)) + 2
        why = ('Device Setting rows %d-%d, %s - ADDED 2026-10-18 (user): the composite tank peak '
               '[79] of D32 repeated at 0 / 25 / 50 / 75 / 100 %% load at the line peak of Vin.min, '
               'the frequency re-solved at each load with the closed-form cubic of the SMath sheet '
               '(section 8; section 9b holds the same table). Shows whether the load current adds '
               'to the magnetizing peak (r.mix < 1) or the peak is the magnetizing current alone, '
               'the OCP1 margin at each load, and the magnetizing floor at the line zero crossing. '
               'All live formulas on the book\'s inputs; no cell above is changed.'
               % (R0, R0 + 25, MARK))
        for sheet, ref, was, now, text in [(None, None, None, None, why),
                                           ('Device Setting', 'D%d:H%d' % (R0 + 20, R0 + 20), '', 'composite peak per load column', 'I.Lr.pk'),
                                           ('Device Setting', 'D%d' % (R0 + 24), '', 'magnetizing peak at f.Min', 'I.lm.zc')]:
            lg = X.ensure_row(lg, rr)
            for col, t in (('B', sheet), ('C', ref), ('D', was), ('E', now), ('F', text)):
                if t is not None:
                    lg = X.set_cell(lg, col + str(rr), X.cell_t(col + str(rr), '8', t))
            rr += 1
        parts[log] = lg.encode('utf-8')
    X.write_book(path, parts)
    print('written:', path)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(os.path.abspath(sys.argv[1]))
