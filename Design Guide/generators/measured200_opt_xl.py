# -*- coding: utf-8 -*-
"""Second copy of the measured-transformer 200 W workbook with the re-reviewed
controller values of 2026-10-14 (docs/THREE_CORE_BOARD.md): C.r 47 nF so that
f.o (132 kHz) sits just under the f.Min the bench needs (154 kHz), C.T 330 pF /
R.T 9.1 kOhm for that f.Min with f.Max 444 kHz, ZCD 270 kOhm, R.CFG 27 kOhm,
R.BM 15 kOhm, and the 34 mF compensation (C.Fo 220 nF, C.F 2.2 uF, R.F 22 k).

Built from the bench copy that measured200_xl.py writes, so every bench value
not listed here (L.r, L.m, n, R.CS, C.in, C.out) is inherited.

    python measured200_opt_xl.py
"""
import os
import re

import xlsx_patch as X
from measured200_xl import DST as SRC, sheet_parts

DST = SRC.replace('_200W.xlsx', '_200W_opt.xlsx')

PICKS = (('Res. Tank Design', 'F43', '100', '47', 'C.r, nF - f.o 132 kHz under the f.Min the bench needs'),
         ('Device Setting', 'D21', '470', '330', 'C.T, pF - f.Max 444 kHz for 264 Vac HB (FHA 400-409 kHz); '
          'the oscillator formulas read D21, F21 only echoes it'),
         ('Device Setting', 'F21', '470', '330', 'C.T, pF - echo of D21'),
         ('Device Setting', 'F24', '6.8', '9.1', 'R.T, kOhm - f.Min 154 kHz = 1.16 x f.o'),
         ('Device Setting', 'F91', '360', '270', 'R.ZCD.H, kOhm - OVP1 35 V, OVP2 38 V, start-up end 20.7 V; 22 pF on ZCD'),
         ('Device Setting', 'F108', '13', '27', 'R.CFG, kOhm - brownout 76 Vac, brown-in 83 Vac (production)'),
         ('Device Setting', 'F61', '16', '15', 'R.BM, kOhm - burst entry 37 W input at R.CS 24 mOhm'),
         ('CompensationNet&Check', 'F93', '82', '220', 'C.Fo, nF - 34 mF output bank'),
         ('CompensationNet&Check', 'F94', '560', '2200', 'C.F, nF - 34 mF output bank'),
         ('CompensationNet&Check', 'F95', '47', '22', 'R.F, kOhm - 34 mF output bank'))
MARK = 'reviewed 200 W copy'
WHY = ('%s, 2026-10-14: controller values re-reviewed for the measured transformer at 200 W. '
       'f.Min has to stay about 1.5 x f.o or the valley circulating current (series resonance of '
       'L.r + L.m with C.r) saturates the small cores; PF needs f.Min near f.o. Only C.r moves f.o, '
       'so C.r 100 -> 47 nF and the oscillator follows.' % MARK)


def main():
    parts = X.open_book(SRC)
    where = sheet_parts(parts)
    for sheet, ref, was, now, _ in PICKS:
        part = where[sheet]
        xml = parts[part].decode('utf-8')
        cur = re.search(r'<c r="%s"[^>]*><v>([^<]*)</v>' % ref, xml).group(1)
        assert abs(float(cur) - float(was)) < 1e-9, '%s!%s is %s, expected %s' % (sheet, ref, cur, was)
        xml = X.set_cell(xml, ref, X.cell_n(ref, X.style_of(xml, ref), now))
        parts[part] = xml.encode('utf-8')
    log_part = where['CHANGELOG_rev0_6']
    log = parts[log_part].decode('utf-8')
    if MARK not in log:
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
        for sheet, ref, was, now, why in [(None, None, None, None, WHY)] + list(PICKS):
            log = X.ensure_row(log, r)
            for col, text in (('B', sheet), ('C', ref), ('D', was), ('E', now), ('F', why)):
                if text is not None:
                    log = X.set_cell(log, col + str(r), X.cell_t(col + str(r), '8', text))
            r += 1
        parts[log_part] = log.encode('utf-8')
    X.write_book(DST, parts)
    print('written:', DST)


if __name__ == '__main__':
    main()
