# -*- coding: utf-8 -*-
"""Workbook for the three-core 670 W design (variant 7p5to1_x3m3), 2026-10-18 (user).

Copies the guide workbook (PQ 50/50, 657.5 W) to
    Calculation Excel Sheet/variants/3CORE_670W_workbook_unencrypted.xlsx
and puts in the inputs where the two designs differ - the tank, its effective
turns ratio and the timing resistor, and (2026-10-18, user) the LG board's
feedback parts and output bank:

    Res. Tank Design  F9   n     effective turns ratio = 7.5/sqrt(1 + L.r/L.m)
                      F43  C.r   nF
                      F44  L.r   uH
                      F45  L.m   uH
    Device Setting    F24  R.T   kOhm
    Power Components  D23 D24 D25 D38   n.Cout, Cout.single, ESR.single, Cceramic
    CompensationNet   D14 D28 D29 D31   V.Z, V.Fo, CTR.steady, CTR.max
                      F43 F93 F94 F95   R.B, C.Fo, C.F, R.F    and C25 the optocoupler name
    Design Spec       D46  c.HB 3329 pF (drain-source caps of the LG board; C115/C117 are across the legs)
    Power Components  D72 C132 D136 D138 (C92 D96 D98 before 2026-10-22)   Cpar 400 pF, SR MOSFET TPH3R70APL1 3.7 mOhm k_T 1.9
    CompensationNet   C19 D23 F96       TL431G-AE2-R, I.min 0.5 mA, C.fx 1.6 nF
Primary MOSFET STO60N045DM9 x 1 per position as the guide; SR TPH3R70APL1 x 2 per leg as the board.

Every new value is read from the variant sheet Smath/variants/L6790A_7p5to1_x3m3.sm
(rebuild it first: L6790_VARIANT=7p5to1_x3m3 python build_l6790_smath.py), never
typed here.  The guide workbook itself is not touched.  Cells are edited in the
zip (xlsx_patch) - openpyxl must not save this book.  Dependent formulas keep the
guide's cached values until the copy is opened in Excel once (full_calc is set,
so Excel recalculates on open) or converted with LibreOffice (README section 9).

    python x3m3_xl.py
    check: SM_OVERRIDE=<x3m3 sheet> XL_OVERRIDE=<recalculated copy> python xl_sm_compare.py
"""
import os
import re
import shutil
import xml.etree.ElementTree as ET

import check_trans_spec as CTS
import xlsx_patch as X
from lge200_xl import current, shared_strings

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                                    'GUIDE_PQ50_657W_workbook_rev0_6_unencrypted.xlsx'))
DST = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                                    'variants', '3CORE_670W_workbook_unencrypted.xlsx'))
SM = os.path.normpath(os.path.join(HERE, '..', '..', 'Smath', 'variants',
                                   'L6790A_7p5to1_x3m3.sm'))
LOG = 'xl/worksheets/sheet1.xml'           # CHANGELOG_rev0_6
TANK = 'xl/worksheets/sheet4.xml'          # Res. Tank Design
DEV = 'xl/worksheets/sheet6.xml'           # Device Setting
PWR = 'xl/worksheets/sheet5.xml'           # Power Components
CMP = 'xl/worksheets/sheet7.xml'           # CompensationNet&Check
MARK = '3CORE 670W'


def typed(name):
    """The number typed into input region `name` of the variant sheet (C.r 70.5,
    R.T 7.68 ...), not its displayed result - R.T displays one decimal."""
    raw = open(SM, encoding='utf-8').read()
    root = ET.fromstring(raw.replace(' xmlns="http://smath.info/schemas/worksheet/1.0"', ''))
    for m in root.iter('math'):
        e = list(m.find('input')) if m.find('input') is not None else []
        if e and e[0].get('type') == 'operand' and e[0].text == name:
            for x in e[1:]:
                try:
                    return float(x.text)
                except (TypeError, ValueError):
                    pass
    raise KeyError(name)


def picks():
    s = CTS.sheet(SM)
    v = lambda k: typed(k) if k in ('n', 'C.r', 'L.r', 'L.m', 'R.T') else s[k][0]
    t = typed
    lam = v('L.r') / v('L.m')
    return (('Res. Tank Design', TANK, 'F9', '%.4f' % v('n'),
             'n effective turns ratio = 7.5/sqrt(1 + L.r/L.m), lambda %.3f' % lam),
            ('Res. Tank Design', TANK, 'F43', '%g' % v('C.r'),
             'C.r resonant capacitor, nF - TDK C4532C0G2J473J320KA (47 nF C0G 630 V) 2 in series x 3 in parallel'),
            ('Res. Tank Design', TANK, 'F44', '%g' % v('L.r'),
             'L.r leakage (resonant) inductance, uH - set; 3 units in series, %.2f uH each' % (v('L.r') / 3)),
            ('Res. Tank Design', TANK, 'F45', '%g' % v('L.m'),
             'L.m magnetizing inductance, uH - set; open-circuit %g uH, %.2f uH per unit'
             % (v('L.r') + v('L.m'), (v('L.r') + v('L.m')) / 3)),
            ('Device Setting', DEV, 'F24', '%g' % v('R.T'),
             'R.T timing resistor, kOhm (E96) - f.Min %.1f kHz' % v('f.Min')),
            ('Design Spec', 'xl/worksheets/sheet2.xml', 'D29', '37',
             'h, mm - Rubycon PX 6800 uF / 35 V is 18 x 35.5 mm, L + alpha max 37 mm (PX sheet, Vdc <= 100: alpha 1.5); '
             'read only by the capacitor-suggestion table'),
            ('Power Components', PWR, 'D23', '%g' % t('n.C'),
             'n.Cout - Rubycon PX 6800 uF / 35 V, 18 x 35.5 mm; 11 (user 2026-10-18: 16 do not fit). Ripple current '
             '%.2f A rms each against the PX rating 1.92 A at 120 Hz / 105 C (x 1.15 above 10 kHz = 2.21 A) - '
             'over the rating; check the can temperature on the board' % v('I.Cout_each')),
            ('Power Components', PWR, 'D24', '%g' % t('C.single'), 'Cout.single, uF - Rubycon PX 6800 uF / 35 V'),
            ('Power Components', PWR, 'D25', '%g' % t('ESR.single'),
             'ESR.single, mOhm - tan d 0.26 (35 V: 0.14 + 0.02 per 1000 uF over 1000) / (2 pi 120 Hz 6800 uF); '
             'the PX sheet gives no ESR or impedance at f.sw, so this 120 Hz maximum is an upper bound'),
            ('Power Components', PWR, 'D38', '%g' % t('C.ceramic'),
             'Cceramic, uF - 16 x 10 uF / 50 V X7R, nominal; at 25 V DC bias X7R keeps roughly half '
             '(check the part curve) - R&N at 80 uF is still under 30 mV'),
            ('CompensationNet&Check', CMP, 'D14', '%.5f' % (t('V.R') * (1 + t('R.Z1') / t('R.Z2'))),
             'V.Z, V - LED rail 2.495 x (1 + 100 k / 27 k), as on the LG board (R197 100 k / R204 27 k)'),
            ('CompensationNet&Check', CMP, 'D28', '%g' % t('V.Fo'),
             'V.Fo, V - UPC1008 (UTC UPC10XX datasheet, typ at I.F 50 mA)'),
            ('CompensationNet&Check', CMP, 'D29', '%g' % t('CTR.s'),
             'CTR.steady at I.tr 150 uA - UPC1008 Ic-If curve scaled to the rank minimum 130 %'),
            ('CompensationNet&Check', CMP, 'D31', '%g' % t('CTR.m'),
             'CTR.max at I.tr 300 uA - same curve, rank minimum'),
            ('CompensationNet&Check', CMP, 'F43', '%g' % t('R.B'),
             'R.B, kOhm (E96) - inside the window %.3f-%.3f k over the V.Z band' % (v('R.B_minZ'), v('R.B_maxZ'))),
            ('CompensationNet&Check', CMP, 'F93', '%g' % t('C.Fo'),
             'C.Fo, nF - compensation re-scaled (zero and pole kept) for the UPC1008 CTR and the 11-capacitor plant, '
             'the set picked for a low 3rd harmonic (user 2026-10-18): '
             'f.cross %.1f Hz, phase margin %.1f deg, 3rd harmonic %.2f %%' % (v('f.cross'), v('Φ.act'), v('D.3rd_act'))),
            ('CompensationNet&Check', CMP, 'F94', '%g' % t('C.F'), 'C.F, nF - same scaling'),
            ('CompensationNet&Check', CMP, 'F95', '%g' % t('R.F'), 'R.F, kOhm - same scaling'),
            ('CompensationNet&Check', CMP, 'F96', '%g' % t('C.fx'), 'C.fx, nF - 1.5 nF + 100 pF at the FB pin, as the LG board'),
            ('CompensationNet&Check', CMP, 'D23', '%g' % t('I.min'),
             'I.min, mA - TL431G-AE2-R as on the LG board (UTC: 0.3 typ / 0.5 max)'),
            # the LG board's primary stage - the same numbers as the 200 W book
            ('Design Spec', 'xl/worksheets/sheet2.xml', 'D46', '%g' % v('c.HB'),
             'c.HB, pF - 2 x Coss(tr) 897 pF x 400 / 245 V = 2929 + 100 layout + 2 x 150 drain-source (C127-C130); '
             'C115/C117 2.2 nF are across each leg (VBUS-PGND), not at the midpoint; read by Res. Tank Design D37 (T.T) and D60'),
            ('Power Components', PWR, 'D72', '%g' % t('C.par'),
             'Cpar, pF - 100 layout + 2 x 150 drain-source, feeds D77 for the dv/dt'),
            # SR MOSFET of the LG board (user: same parts as the board)
            ('Power Components', PWR, 'D136', '%g' % (t('R.dson_s25') / 1000),
             'RD, Ohm - TPH3R70APL1 RDSon max at VGS = 10 V, as the 200 W book (Toshiba datasheet not on file)'),
            ('Power Components', PWR, 'D138', '%g' % t('K.Tsec'),
             'kT.sec - ST tool default 1.9 kept for the TPH3R70APL1 (no curve on file); the STL160N10F8 had 1.5'))


TEXT = (('CompensationNet&Check', 'xl/worksheets/sheet7.xml', 'C25', 'UPC1008G-LS04-R',
         'optocoupler part - as on the LG board (U13)'),
        ('CompensationNet&Check', 'xl/worksheets/sheet7.xml', 'C19', 'TL431G-AE2-R',
         'TL431 part - as on the LG board (Q44/Q46)'),
        ('Power Components', PWR, 'C132', 'TPH3R70APL1',
         'SR MOSFET - as on the LG board, 2 per leg under the TEA2095TE'))



def why():
    s = CTS.sheet(SM)
    v = lambda k: s[k][0]
    return ('%s copy, 2026-10-18 (user): variant 7p5to1_x3m3 - three flat transformer units, '
            'primaries in series and secondaries in parallel, 5 : 2+2 per unit (7.5 : 1 set), '
            'A_e 225 mm2 per unit (placeholder, core not specified). f.r %.1f kHz, B.pk %.1f mT. '
            'C.r = TDK C4532C0G2J473J320KA 2S x 3P. Feedback parts and output bank as the LG board '
            '(V.Z 11.74 V, UPC1008G-LS04-R, Rubycon PX 6800 uF / 35 V x 11); primary MOSFET as the guide, SR as the board. '
            'Built from %s by x3m3_xl.py from the variant sheet; every other input is the guide book unchanged.'
            % (MARK, v('f.r'), v('B.pk'), os.path.basename(SRC)))


def main():
    shutil.copyfile(SRC, DST)
    parts = X.open_book(DST)
    rows = []
    for sheet, part, ref, now, what in picks():
        xml = parts[part].decode('utf-8')
        was = re.search(r'<c r="%s"[^>]*><v>([^<]*)</v>' % ref, xml).group(1)
        xml = X.set_cell(xml, ref, X.cell_n(ref, X.style_of(xml, ref), now))
        parts[part] = xml.encode('utf-8')
        rows.append((sheet, ref, was, now, what))
        print('%-21s %-4s %8s -> %s' % (sheet, ref, was, now))
    sst = shared_strings(parts)
    for sheet, part, ref, now, what in TEXT:
        xml = parts[part].decode('utf-8')
        was = current(xml, ref, sst)
        xml = X.set_cell(xml, ref, X.cell_t(ref, X.style_of(xml, ref), now))
        parts[part] = xml.encode('utf-8')
        rows.append((sheet, ref, was, now, what))
        print('%-21s %-4s %8s -> %s' % (sheet, ref, was, now))
    log = parts[LOG].decode('utf-8')
    r = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
    for sheet, ref, was, now, text in [(None, None, None, None, why())] + rows:
        log = X.ensure_row(log, r)
        for col, t in (('B', sheet), ('C', ref), ('D', was), ('E', now), ('F', text)):
            if t is not None:
                log = X.set_cell(log, col + str(r), X.cell_t(col + str(r), '8', t))
        r += 1
    parts[LOG] = log.encode('utf-8')
    X.write_book(DST, parts)
    print('written:', DST)


if __name__ == '__main__':
    main()
