# -*- coding: utf-8 -*-
"""Is the BOM the same in both documents?

The workbook's BOM cells are links, and its cached values are stale until Excel
recalculates, so the Excel side is read from the SOURCE cells the BOM links to.
The SMath side is read out of the generated worksheet.
"""
import io
import os
import sys
import xml.etree.ElementTree as ET

import smresult

import openpyxl


def require_readable(path):
    """Excel takes an exclusive lock while the workbook is open. Say so
    plainly rather than dying inside openpyxl with a bare PermissionError."""
    try:
        open(path, 'rb').close()
    except PermissionError:
        print('워크북이 Excel 에서 열려 있어 읽을 수 없다. 닫고 다시 실행할 것:')
        print('  ' + path)
        raise SystemExit(2)


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# paths are relative to this script, so the toolchain moves with the folder
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')
SM = os.path.join(ROOT, 'Smath', 'L6790A_SingleStage_PF_LLC_Design_Guide.sm')

require_readable(XL)
wv = openpyxl.load_workbook(XL, data_only=True)
RT, PW, DV, CN = (wv['Res. Tank Design'], wv['Power Components'],
                  wv['Device Setting'], wv['CompensationNet&Check'])

raw = open(SM, encoding='utf-8').read()
root = ET.fromstring(raw.replace(' xmlns="http://smath.info/schemas/worksheet/1.0"', ''))
sm = {}
for r in root.iter('region'):
    m = r.find('math')
    if m is None:
        continue
    i, res = m.find('input'), m.find('result')
    if i is None or res is None:
        continue
    e = list(i)
    if e and e[0].get('type') == 'operand':
        c = m.find('contract')
        u = list(c)[0].text if c is not None else ''
        val = smresult.value(res)
        if val is not None:
            sm.setdefault(e[0].text, (val, u))

# (item, unit, excel value, smath variable, tolerance)
ITEMS = [
    ('L.m  magnetizing inductance', 'uH', RT['F45'].value, 'L.m', 1e-6),
    ('L.r  resonant inductor', 'uH', RT['F44'].value, 'L.r', 1e-6),
    ('C.r  resonant capacitor', 'nF', RT['F43'].value, 'C.r', 1e-9),
    ('n    turns ratio', '-', RT['F9'].value, 'n', 1),
    ('n.aux/n.sec', '-', DV['F83'].value, 'n.aux', 1),
    ('C.in input film capacitor', 'nF', PW['F7'].value, 'C.in_sel', 1e-9),
    ('C.out single', 'uF', PW['D24'].value, 'C.single', 1e-6),
    ('n.Cout count', '-', PW['D23'].value, 'n.C', 1),
    ('C.out TOTAL', 'mF', PW['D24'].value * PW['D23'].value / 1000, 'C.out', 1e-3),
    ('C.out ceramic', 'uF', PW['D38'].value, 'C.ceramic', 1e-6),
    ('ESR single', 'mohm', PW['D25'].value, 'ESR.single', 1e-3),
    ('R.CS single', 'mohm', DV['F45'].value, 'R.CS_single', 1e-3),
    ('N.Rcs parallel', '-', DV['D43'].value, 'N.RCS', 1),
    ('R.CS total', 'mohm', DV['D46'].value, 'R.CS', 1e-3),
    ('C.Fo', 'nF', CN['F93'].value, 'C.Fo', 1e-9),
    ('C.F', 'nF', CN['F94'].value, 'C.F', 1e-9),
    ('R.F', 'kohm', CN['F95'].value, 'R.F', 1e3),
    ('C.fx', 'nF', CN['F96'].value, 'C.fx', 1e-9),
    ('R.I  divider upper', 'kohm', CN['D36'].value, 'R.I', 1e3),
    ('R.o  divider lower', 'kohm', CN['F37'].value, 'R.o', 1e3),
    ('R.P  photodiode parallel', 'kohm', CN['F41'].value, 'R.P', 1e3),
    ('R.B  optocoupler bias', 'kohm', CN['F43'].value, 'R.B', 1e3),
    ('V.Z  feedback supply', 'V', CN['D14'].value, 'V.Z', 1),
    ('R.ZCD.L', 'kohm', DV['F90'].value, 'R.ZCD_L_sel', 1e3),
    ('R.ZCD.H', 'kohm', DV['F91'].value, 'R.ZCD_H_sel', 1e3),
    ('C.T  timing capacitor', 'pF', DV['D21'].value, 'C.T', 1e-12),
    ('R.T  timing resistor', 'kohm', DV['F24'].value, 'R.T', 1e3),
    ('R.BM burst-mode', 'kohm', DV['F61'].value, 'R.BM_sel', 1e3),
    ('R.CFG', 'kohm', DV['F108'].value, 'R.CFG_sel', 1e3),
]

print('%-30s %-6s %12s %12s   %s' % ('BOM item', 'unit', 'EXCEL', 'SMath', 'verdict'))
print('-' * 84)
bad = []
for name, unit, xv, var, scale in ITEMS:
    got = sm.get(var)
    if got is None:
        print('%-30s %-6s %12s %12s   MISSING in SMath' % (name, unit, xv, '-'))
        bad.append(name)
        continue
    # the .sm <result> is already in its contract unit: convert to SI, then to
    # the unit this BOM row is quoted in
    U = {'': 1.0, 'V': 1, 'A': 1, 'W': 1, 'ohm': 1, 'kohm': 1e3, 'mohm': 1e-3,
         'F': 1, 'mF': 1e-3, 'uF': 1e-6, 'μF': 1e-6, 'nF': 1e-9, 'pF': 1e-12,
         'H': 1, 'mH': 1e-3, 'uH': 1e-6, 'μH': 1e-6, 'nH': 1e-9, 'Hz': 1, 'kHz': 1e3}
    sv, su = got
    sv_disp = sv * U[su] / scale if scale != 1 else sv
    ok = xv is not None and abs(sv_disp - xv) <= max(abs(xv) * 2e-3, 1e-9)
    print('%-30s %-6s %12.4g %12.4g   %s'
          % (name, unit, xv if xv is not None else float('nan'), sv_disp,
             'same' if ok else '** DIFFERENT'))
    if not ok:
        bad.append(name)
print('-' * 84)
print('items compared: %d   different: %d %s' % (len(ITEMS), len(bad), bad if bad else ''))
