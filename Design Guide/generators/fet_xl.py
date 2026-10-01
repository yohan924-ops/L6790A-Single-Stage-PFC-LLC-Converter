# -*- coding: utf-8 -*-
"""One-off, applied 2026-10-01: put the primary MOSFET datasheet into the ST
workbook and log it in CHANGELOG_rev0_6.  The user supplied the STO60N045DM9
datasheet (DS14711 Rev 4) with the L6498LD gate driver and the TEA2095TE SR
controller.

    Design Spec       D46  c.HB    800  -> 3028.98 pF  (built as in l6790.py:
                           2 x C_oss eq. 897 pF x 400 V / (sqrt(2) V.eq_min)
                           + 100 pF layout - the charge of two devices over
                           the corner bus, an upper bound)
    Power Components  D58  kT.pri  1.8  -> 1.9         (Fig. 10 at 125 C, read
                           from the vector curve: 1.898)
    Power Components  D72  Cpar    10   -> 100 pF      (the layout parasitic
                           the SMath sheet uses; D77 is the only reader)

c.HB is computed here from l6790.py, not typed.  Cells are edited in the zip
(xlsx_patch) - openpyxl must not save this book.  The formulas that depend on
them keep their old cached values until the book is opened in Excel once and
saved.  The variant workbook is the same file, so it is copied over afterwards.

    python fet_xl.py
"""
import os
import re
import shutil
from math import sqrt

import l6790
import xlsx_patch as X

HERE = os.path.dirname(os.path.abspath(__file__))
XL = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                                   'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx'))
VAR = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                                    'variants', 'L6790_workbook_7p5to1_x1.xlsx'))
LOG = 'xl/worksheets/sheet1.xml'           # CHANGELOG_rev0_6

_F = l6790.PRI_FET
_VEQ = 245. / sqrt(2)                      # V.eq_min = V_BIH / sqrt(2) here
CHB = round((2 * _F['Coss_tr'] * _F['V_oss_tr'] / (sqrt(2) * _VEQ)
             + _F['C_par']) * 1e12, 2)

PICKS = (('Design Spec', 'xl/worksheets/sheet2.xml', 'D46', '800', '%.2f' % CHB,
          'c.HB midpoint capacitance, pF - from C_oss eq. 897 pF (0..400 V)'),
         ('Power Components', 'xl/worksheets/sheet5.xml', 'D58', '1.8', '1.9',
          'kT.pri RDSon rise to Tj 125 C - Fig. 10 vector read 1.898'),
         ('Power Components', 'xl/worksheets/sheet5.xml', 'D72', '10', '100',
          'Cpar midpoint layout parasitic, pF - as the SMath sheet'))
MARK = 'STO60N045DM9 datasheet'
WHY = ('STO60N045DM9 datasheet (DS14711 Rev 4), 2026-10-01 (user): c.HB is '
       'now the charge of two devices, 2 x 897 pF x 400 V over the corner '
       'bus sqrt(2) x V.eq_min, plus 100 pF layout (was an 800 pF pick); '
       'kT.pri from Fig. 10. Q.ZVS2 falls to 4.22 but Q.ZVS1 1.97 still '
       'binds, so the tank is unchanged; T.T rises to 170 ns (t.D 220 ns).')


def main():
    # the cell must be what l6790.py says the sheet uses
    R = l6790.design(Vout=25., Pout=657.5, Vo_min=19., dv_out=0.05,
                     Thold=12e-3, Nrect=1, **l6790.PRI_FET, tD=220e-9)
    assert abs(R['c_HB'] * 1e12 - CHB) < 0.01, (R['c_HB'], CHB)
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
    print('c.HB = %.2f pF' % CHB)
    print('written:', XL, '\ncopied :', VAR)


if __name__ == '__main__':
    main()
