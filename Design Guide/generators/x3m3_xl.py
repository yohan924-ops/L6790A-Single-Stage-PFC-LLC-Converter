# -*- coding: utf-8 -*-
"""Workbook for the three-core 670 W design (variant 7p5to1_x3m3), 2026-10-18 (user).

Copies the guide workbook (PQ 50/50, 657.5 W) to
    Calculation Excel Sheet/variants/3CORE_670W_workbook_unencrypted.xlsx
and puts in the inputs where the two designs differ.  Specification, devices,
output bank and compensation inputs are the same in both builder variants, so
only the tank, its effective turns ratio and the timing resistor move:

    Res. Tank Design  F9   n     effective turns ratio = 7.5/sqrt(1 + L.r/L.m)
                      F43  C.r   nF
                      F44  L.r   uH
                      F45  L.m   uH
    Device Setting    F24  R.T   kOhm

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
             'R.T timing resistor, kOhm (E96) - f.Min %.1f kHz' % v('f.Min')))


def why():
    s = CTS.sheet(SM)
    v = lambda k: s[k][0]
    return ('%s copy, 2026-10-18 (user): variant 7p5to1_x3m3 - three flat transformer units, '
            'primaries in series and secondaries in parallel, 5 : 2+2 per unit (7.5 : 1 set), '
            'A_e 225 mm2 per unit (placeholder, core not specified). f.r %.1f kHz, B.pk %.1f mT. '
            'Built from %s by x3m3_xl.py; every other input is the guide book unchanged.'
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
        print('%-17s %-4s %8s -> %s' % (sheet, ref, was, now))
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
