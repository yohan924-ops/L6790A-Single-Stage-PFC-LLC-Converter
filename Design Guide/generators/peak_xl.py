# -*- coding: utf-8 -*-
"""Peak tank current over the load range - magnetizing + load - in a workbook
(2026-10-18, user; re-laid 2026-10-19: "too many formulas - put it in Res. Tank
Design, keep the existing format, make it simple").

Below resonance the magnetizing current is a triangle that peaks at the END of the
half cycle and the reflected load current a half sine that peaks in the MIDDLE.
While 2*I.lm/(pi*I.trafo) >= 1 (light load) the sum peaks at the magnetizing value
alone; above that the load raises the peak - the formula the book already uses for
100 % load in Device Setting D32 ([79], SMath sheet section 9 / 9b).

Two places, each in the format of the sheet it sits in:

  Res. Tank Design rows 70-79 - the RESULT, one value per row, the same
  Parameters / Name / Value / Unit table as "Estimated transformer current" above:
      I.Lm.pk      magnetizing current peak at the line peak of Vin.min (any load)
      I.Lm.zc      magnetizing current peak at the line zero crossing (f.Min, any load)
      ld.add       load above which the load current raises the peak (approx.)
      Ilr.pk.25 .. Ilr.pk.100   peak tank current at 25 / 50 / 75 / 100 % load

  CC rows 59-74 - the working, laid out like the CC blocks above it (label in B,
  one column per point): load 0 / 25 / 50 / 75 / 100 % in C-G, the frequency
  re-solved at each load with the closed-form cubic of the SMath sheet (section 8,
  middle root), then I.trafo, I.lm, r.mix and the composite peak.

Every cell is a live formula on the book's own inputs; no existing cell changes.

    python peak_xl.py <workbook.xlsx>        idempotent (CHANGELOG mark)
"""
import os
import re
import sys

import xlsx_patch as X
from measured200_xl import sheet_parts

MARK = 'peak tank current vs load (Res. Tank Design 70-79, CC 59-74)'
COLS = 'CDEFG'
LOADS = (0, 0.25, 0.5, 0.75, 1)

RT = "'Res. Tank Design'!"
DS = "'Design Spec'!"
n = RT + '$D$42'
lam = RT + '$D$50'
Mpk = RT + '$D$10'
Qpk = '(%s$D$52/%s$D$17)' % (RT, RT)
fr = RT + '$D$55'
Lm = 'IF(%s$F$45,%s$F$45,%s$D$45)' % (RT, RT, RT)
Vo = '(%s$D$95+%s$D$107*%s$D$106)' % (DS, DS, DS)
Iout = "'Preliminary Calculation'!$D$7"
C0 = 59                                    # CC: first row of the block


def cc_rows(c):
    """(row, label, formula) of the CC working block, column c"""
    r = lambda k: '%s%d' % (c, C0 + k)
    return [
        (2, 'Q = Q.pk x load', '%s*%s' % (Qpk, r(1))),
        (3, 'a2  (cubic in x = 1/fn^2)', '(%s^2-2*%s*(1+%s))/%s^2' % (r(2), lam, lam, lam)),
        (4, 'a1', '((1+%s)^2-2*%s^2-1/%s^2)/%s^2' % (lam, r(2), Mpk, lam)),
        (5, 'a0', '%s^2/%s^2' % (r(2), lam)),
        (6, 'p', '%s-%s^2/3' % (r(4), r(3))),
        (7, 'q', '2*%s^3/27-%s*%s/3+%s' % (r(3), r(3), r(4), r(5))),
        (8, 'fn (middle root)', '1/SQRT(2*SQRT(-%s/3)*COS(ACOS(3*%s/(2*%s)*SQRT(-3/%s))/3-2*PI()/3)-%s/3)'
         % (r(6), r(7), r(6), r(6), r(3))),
        (9, 'fsw', '%s*%s' % (r(8), fr)),
        (10, 'Itrafo.pk', 'PI()*(%s/%s)*2*%s*%s/(1-COS(PI()*%s/MAX(%s,%s)))/%s'
         % (fr, r(9), Iout, r(1), fr, r(9), fr, n)),
        (11, 'Ilm.pk (trapezoidal)', '0.25*%s*%s/(%s*10^(-6)*MAX(%s,%s)*1000)' % (n, Vo, Lm, r(9), fr)),
        (12, 'r.mix = 2 Ilm / (pi Itrafo)', 'IF(%s>0,2*%s/(PI()*%s),1E+9)' % (r(10), r(11), r(10))),
        (13, 'Ilr.pk (composite)', 'IF(%s>=1,%s,%s*(2*ACOS(-%s)/PI()-1)+%s*SQRT(1-%s^2))'
         % (r(12), r(11), r(11), r(12), r(10), r(12))),
    ]


RT_ROWS = [   # row, label, name, formula, unit
    (73, 'Magnetizing current peak (any load)', 'I.Lm.pk', '=CC!C%d' % (C0 + 11), 'A'),
    (74, 'Magnetizing current peak @ line zero crossing (f.Min)', 'I.Lm.zc', '=CC!C%d' % (C0 + 15), 'A'),
    (75, 'Load above which the load current adds to the peak (approx.)', 'ld.add',
     '=MIN(100,100*2*CC!E%d/PI()/(CC!E%d/CC!E%d))' % (C0 + 11, C0 + 10, C0 + 1), '%'),
    (76, 'Peak tank current @ 25 % load', 'Ilr.pk.25', '=CC!D%d' % (C0 + 13), 'A'),
    (77, 'Peak tank current @ 50 % load', 'Ilr.pk.50', '=CC!E%d' % (C0 + 13), 'A'),
    (78, 'Peak tank current @ 75 % load', 'Ilr.pk.75', '=CC!F%d' % (C0 + 13), 'A'),
    (79, 'Peak tank current @ 100 % load', 'Ilr.pk.100', '=CC!G%d' % (C0 + 13), 'A'),
]


def set_row_height(xml, row, ht):
    return re.sub(r'<row r="%d"(?: [^>]*)?>' % row,
                  '<row r="%d" spans="2:5" ht="%s" customHeight="1">' % (row, ht), xml, count=1)


def main(path):
    parts = X.open_book(path)
    sp = sheet_parts(parts)
    log = parts[sp['CHANGELOG_rev0_6']].decode('utf-8')
    if MARK in log:
        print('already present in', os.path.basename(path))
        return

    # ---- CC: the working block, in the style of the blocks above it
    cc = parts[sp['CC']].decode('utf-8')
    st, stv = X.style_of(cc, 'B27'), X.style_of(cc, 'C21')
    put = lambda xml, ref, cell: X.set_cell(xml, ref, cell)
    cc = X.ensure_row(cc, C0)
    cc = put(cc, 'B%d' % C0, X.cell_t('B%d' % C0, st,
             'Peak tank current vs load @ Vin.min line peak - feeds Res. Tank Design 73-79'))
    cc = X.ensure_row(cc, C0 + 1)
    cc = put(cc, 'B%d' % (C0 + 1), X.cell_t('B%d' % (C0 + 1), st, 'load'))
    for c, ld in zip(COLS, LOADS):
        cc = put(cc, '%s%d' % (c, C0 + 1), X.cell_n('%s%d' % (c, C0 + 1), st, ld))
    for k, label, _ in cc_rows('C'):
        cc = X.ensure_row(cc, C0 + k)
        cc = put(cc, 'B%d' % (C0 + k), X.cell_t('B%d' % (C0 + k), st, label))
        for c in COLS:
            f = dict((kk, ff) for kk, _, ff in cc_rows(c))[k]
            cc = put(cc, '%s%d' % (c, C0 + k), X.cell_f('%s%d' % (c, C0 + k), stv, f))
    r = C0 + 15
    cc = X.ensure_row(cc, r)
    cc = put(cc, 'B%d' % r, X.cell_t('B%d' % r, st, 'Ilm.pk @ line zero crossing (f.Min, any load)'))
    cc = put(cc, 'C%d' % r, X.cell_f('C%d' % r, stv, '0.25*%s*%s/(%s*10^(-6)*MAX(%s,%s)*1000)'
             % (n, Vo, Lm, "'Device Setting'!$D$28", fr)))
    cc = re.sub(r'<dimension ref="[^"]*"/>', '<dimension ref="B3:AM%d"/>' % r, cc, count=1)
    parts[sp['CC']] = cc.encode('utf-8')

    # ---- Res. Tank Design: the result, in the format of rows 62-68
    rt = parts[sp['Res. Tank Design']].decode('utf-8')
    s_title, s_head = X.style_of(rt, 'B62'), X.style_of(rt, 'B64')
    s_lab, s_val, s_unit = X.style_of(rt, 'B65'), X.style_of(rt, 'D65'), X.style_of(rt, 'E65')
    for row, ht in ((69, 14.25), (70, 18), (71, 3), (72, 15.75)):
        rt = X.ensure_row(rt, row)
        rt = set_row_height(rt, row, ht)
    rt = put(rt, 'B70', X.cell_t('B70', s_title, 'Peak tank current vs load (magnetizing + load)'))
    for col, text in zip('BCDE', ('Parameters', 'Name', 'Value', 'Unit')):
        rt = put(rt, '%s72' % col, X.cell_t('%s72' % col, s_head, text))
    for row, label, name, f, unit in RT_ROWS:
        rt = X.ensure_row(rt, row)
        rt = set_row_height(rt, row, 15)
        rt = put(rt, 'B%d' % row, X.cell_t('B%d' % row, s_lab, label))
        rt = put(rt, 'C%d' % row, X.cell_t('C%d' % row, s_lab, name))
        rt = put(rt, 'D%d' % row, X.cell_f('D%d' % row, s_val, f[1:]))
        rt = put(rt, 'E%d' % row, X.cell_t('E%d' % row, s_unit, unit))
    rt = re.sub(r'<dimension ref="[^"]*"/>', '<dimension ref="B4:G79"/>', rt, count=1)
    parts[sp['Res. Tank Design']] = rt.encode('utf-8')

    # ---- CHANGELOG
    rr = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
    why = ('%s - ADDED (user, 2026-10-18/19): below resonance the magnetizing current peaks at the end of '
           'the half cycle and the load current in the middle, so at light load the peak IS the magnetizing '
           'current and only above ld.add does the load raise it ([79], as Device Setting D32 at 100 %%). '
           'Res. Tank Design 73-79 hold the results; CC 59-74 re-solve the frequency at 0/25/50/75/100 %% load '
           '(closed-form cubic of the SMath sheet, section 8) and compute I.trafo, I.lm and the composite '
           'peak. Live formulas on the book inputs; no existing cell changes.' % MARK)
    for sheet, ref, text in ((None, None, why),
                             ('Res. Tank Design', 'D73:D79', 'I.Lm.pk, I.Lm.zc, ld.add, Ilr.pk at 25/50/75/100 %'),
                             ('CC', 'B59:G74', 'working: cubic, fsw, Itrafo.pk, Ilm.pk, r.mix, composite peak')):
        log = X.ensure_row(log, rr)
        for col, t in (('B', sheet), ('C', ref), ('F', text)):
            if t is not None:
                log = X.set_cell(log, col + str(rr), X.cell_t(col + str(rr), '8', t))
        rr += 1
    parts[sp['CHANGELOG_rev0_6']] = log.encode('utf-8')
    X.write_book(path, parts)
    print('written:', path)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(os.path.abspath(sys.argv[1]))
