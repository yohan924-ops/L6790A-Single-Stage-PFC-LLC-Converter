# -*- coding: utf-8 -*-
"""Third copy of the measured-transformer 200 W workbook: the inputs LGE typed into
their copy of the OLD ST tool (sheet-protected '16102026_LGE_200W_L6790A_Single_Stage
_PFC_LLC_TV_Power.xlsx', received 2026-10-16 with the schematic and the test deck)
ported into our rev0_6 book.

Their file is the ST original layout cell for cell (same 10 sheets, same cell count,
no formula edited); 36 constants differ from the ST original.  Most of them the bench
copy (measured200_xl.py) already carries - Pout 200, Vo_min 19, dv 5 %, Thold 12 ms,
n 6.773, L.r 5.7, L.m 25.2 uH, C.in 660 nF, 5 x 6800 uF, R.T 9.1 k, R.ZCD.H 360 k,
R.CFG 13 k, Coss 897 pF, STO60N045DM9.  This copy adds the rest, checked against the
schematic of the same date (LG L6790A Single Stage PFC LLC, sheet 3 of 3):

    C.r 117 nF                 C106.. 47 nF 630 V X7R, 2S x 5P (board 117.5 nF)
    BM grounded                R211 0 ohm to ground -> P.in.BM 0, R.BM 0
    n.aux/n.sec 1.5            aux 3 T (pins 8-7) over 2 T; ZCD 360 k / (18 k + 1 k = 19 k) + 20 pF
    dead time 270 ns           their value (the IC's dead time is adaptive)
    c.HB 5229 pF               NOT their 500 pF: C115/C117 2.2 nF 2 kV sit at both half-bridge
                               midpoints (user, 2026-10-14), so c.HB = 2 x Coss(tr) 897 pF x
                               400 V / 245 V (l6790 [116], 2929 pF) + 100 pF stray + 2200 pF.
                               The book reads c.HB in two places only: Res. Tank Design D60
                               I.R0.crit = sqrt(2 c.HB / (L.r + L.m)) x sqrt2 Vin.min (1.39 ->
                               4.51 A against the 8.62 A magnetizing peak) and D37 T.T.
    ceramic 50 uF              C61/C66/C84/C85/C92 10 uF x 5 beside the 5 x 6800 uF
    compensation               C95 220 nF, R187 22 k + C98 2.2 uF (C99 0.1 uF parallel),
                               C.fx 1.5 nF + 100 pF at the FB pin = 1.6 nF, line 50 Hz
    TL431 (TL431G-AE2-R, I.min 0.5 mA) and opto UPC1008G-LS04-R (V.Fo 1.45 V as typed)

NOT ported, on purpose:
    Design Spec F20 Vin.min 180 Vac   our F20 is a formula (245 V / sqrt 2 = 173.2 Vac,
                               the morphing threshold); 180 is inside the tool's own
                               "165-180" hint but less conservative.
    Design Spec D58 Vrect 0.395 V + Power Components C92 STPS30M60S
                               the old tool has no SR option, so they modelled the
                               rectifier as a Schottky drop with RD 3.7 mohm; the board
                               runs TPH3R70APL1 x 2 per leg under a TEA2095TE and the
                               test was taken with SR on.  rev0_6 models exactly that:
                               Conf.SR = 2, TPH3R70APL1, RD 3.7 mohm, Vrect 0.

Built from the bench copy that measured200_xl.py writes, so every bench value not
listed here is inherited.  Cells are edited in the zip (xlsx_patch) - openpyxl must
not save this book.  Dependent formulas keep their old cached values until the copy is
opened in Excel once (or converted with LibreOffice and OOXMLRecalcMode 0).

    python lge200_xl.py
"""
import re

import xlsx_patch as X
from measured200_xl import DST as SRC, sheet_parts

DST = SRC.replace('_200W.xlsx', '_LGE_200W.xlsx')

PICKS = (('Design Spec', 'D29', '25', '30', 'h, mm - max output capacitor height (LGE workbook)'),
         ('Design Spec', 'D46', '800', '5229', 'c.HB, pF - 2 x Coss(tr) 897 pF x 400 V / 245 V = 2929 pF (l6790 [116]) + 100 pF stray '
          '+ C115/C117 2.2 nF/2 kV at the midpoint = 5229 pF; LGE typed 500 pF, which leaves out the 2.2 nF'),
         ('Design Spec', 'D47', '220', '270', 't.D, ns - dead time as typed by LGE'),
         ('Res. Tank Design', 'F43', '100', '117', 'C.r, nF - board 47 nF 630 V X7R 2S x 5P = 117.5 nF (C106..C116)'),
         ('Power Components', 'D38', '10', '50', 'Cceramic, uF - 5 x 10 uF/50 V beside the 5 x 6800 uF'),
         ('Device Setting', 'D57', '75', '0', 'P.in.BM, W - burst mode not used: BM pin grounded through R211 0 ohm'),
         ('Device Setting', 'F61', '16', '0', 'R.BM, kOhm - R211 0 ohm, BM grounded'),
         ('Device Setting', 'F83', '1.0', '1.5', 'n.aux/n.sec - aux 3 T (pins 8-7) over the 2 T secondary; matches the '
          'ZCD 2.0 V peak measured at 360 k; lower ZCD resistor R208 18 k + R213 1 k = 19 k (F90)'),
         ('CompensationNet&Check', 'C19', 'TL431AIT', 'TL431G-AE2-R', 'TL431 part as on the board (Q44/Q46)'),
         ('CompensationNet&Check', 'D23', '0.8', '0.5', 'I.min, mA - TL431G-AE2-R as typed by LGE'),
         ('CompensationNet&Check', 'C25', 'SFH617A', 'UPC1008G-LS04-R', 'optocoupler as on the board (U13)'),
         ('CompensationNet&Check', 'D28', '1.15', '1.45', 'V.Fo, V - UPC1008G-LS04-R as typed by LGE (CTR 0.37/0.53 and '
          'C.opto 3 nF left at the SFH617A values - the UPC1008 datasheet gives rank 130-260 % at 5 mA, no 150/300 uA data)'),
         ('CompensationNet&Check', 'F93', '82', '220', 'C.Fo, nF - C95 220 nF (34 mF output bank)'),
         ('CompensationNet&Check', 'F94', '560', '2200', 'C.F, nF - C98 2.2 uF (C99 0.1 uF in parallel)'),
         ('CompensationNet&Check', 'F95', '47', '22', 'R.F, kOhm - R187 22 k'),
         ('CompensationNet&Check', 'F96', '1.55', '1.6', 'C.fx, nF - 1.5 nF + 100 pF at the FB pin'),
         ('CompensationNet&Check', 'D110', '47', '50', 'fl, Hz - line frequency of the test (50 Hz)'))
MARK = 'LGE 200 W workbook copy'
WHY = ('%s, 2026-10-16: inputs LGE typed into their sheet-protected copy of the old ST tool, ported here '
       'and checked against the schematic of the same date (L6790A board, sheet 3 of 3). Not ported: '
       'Vin.min 180 Vac (F20 stays the 173.2 Vac morphing formula), Vrect 0.395 V and the STPS30M60S '
       'entry (the old tool has no SR option; this book models the TPH3R70APL1 SR of the board with '
       'Conf.SR = 2, RD 3.7 mOhm, Vrect 0).' % MARK)


def shared_strings(parts):
    xml = parts.get('xl/sharedStrings.xml', b'').decode('utf-8')
    out = []
    for si in re.findall(r'<si>(.*?)</si>', xml, re.S):
        out.append(''.join(re.findall(r'<t[^>]*>([^<]*)</t>', si)))
    return out


def current(xml, ref, sst):
    m = re.search(r'<c r="%s"([^>]*)>(.*?)</c>' % ref, xml, re.S)
    assert m, 'cell %s not found' % ref
    attrs, body = m.group(1), m.group(2)
    if 'inlineStr' in attrs:
        return ''.join(re.findall(r'<t[^>]*>([^<]*)</t>', body))
    v = re.search(r'<v>([^<]*)</v>', body)
    if not v:
        return None
    return sst[int(v.group(1))] if 't="s"' in attrs else v.group(1)


def is_num(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def main():
    parts = X.open_book(SRC)
    where = sheet_parts(parts)
    sst = shared_strings(parts)
    for sheet, ref, was, now, _ in PICKS:
        part = where[sheet]
        xml = parts[part].decode('utf-8')
        cur = current(xml, ref, sst)
        if is_num(was):
            assert abs(float(cur) - float(was)) < 1e-9, '%s!%s is %s, expected %s' % (sheet, ref, cur, was)
            new = X.cell_n(ref, X.style_of(xml, ref), now)
        else:
            assert cur == was, '%s!%s is %r, expected %r' % (sheet, ref, cur, was)
            new = X.cell_t(ref, X.style_of(xml, ref), now)
        xml = X.set_cell(xml, ref, new)
        parts[part] = xml.encode('utf-8')
    log_part = where['CHANGELOG_rev0_6']
    log = parts[log_part].decode('utf-8')
    if MARK not in log:
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
        rows = [(None, None, None, None, WHY)] + list(PICKS)
        for sheet, ref, was, now, why in rows:
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
