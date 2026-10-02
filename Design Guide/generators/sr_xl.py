# -*- coding: utf-8 -*-
"""One-off, applied 2026-10-02: put the SR MOSFET datasheet into the ST
workbook and log it in CHANGELOG_rev0_6.  The user supplied the STL160N10F8
datasheet (DS14249 Rev 5); the earlier selection was a 3.7 mOhm part with
an assumed temperature factor of 1.9.

    Power Components  C92  part      TPH3R70APL1 -> STL160N10F8
                      D96  RD        0.0037 -> 0.0032 ohm  (Table 3, max.)
                      D98  kT.sec    1.9    -> 1.5         (Fig. 13 at
                           125 C, read from the vector curve: 1.504)

The two values are read from the sheet builder, not typed here.  Cells are
edited in the zip (xlsx_patch) - openpyxl must not save this book.  The
formulas that depend on them keep their old cached values until the book
is opened in Excel once and saved.  The variant workbook is the same file,
so it is copied over afterwards.

    python sr_xl.py
"""
import os
import re
import shutil

import xlsx_patch as X
from an_pdf import _builder_const

HERE = os.path.dirname(os.path.abspath(__file__))
XL = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                                   'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx'))
VAR = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                                    'variants', 'L6790_workbook_7p5to1_x1.xlsx'))
LOG = 'xl/worksheets/sheet1.xml'           # CHANGELOG_rev0_6
PC = 'xl/worksheets/sheet5.xml'            # Power Components

PART = 'STL160N10F8'
RDS = _builder_const('R.dson_s25') / 1e3   # mOhm in the builder -> ohm
KT = _builder_const('K.Tsec')
NUMS = (('D96', '0.0037', '%g' % RDS,
         'RD SR RDSon max 25 C, VGS 10 V - STL160N10F8 Table 3'),
        ('D98', '1.9', '%g' % KT,
         'kT.sec RDSon rise to Tj 125 C - Fig. 13 vector read 1.504'))
MARK = 'STL160N10F8 datasheet'
WHY = ('STL160N10F8 datasheet (DS14249 Rev 5), 2026-10-02 (user): the SR '
       'MOSFET, two per leg. RDSon 3.2 mOhm max and kT 1.5 replace the '
       'earlier 3.7 mOhm and 1.9; the SR conduction loss falls from 5.71 to '
       '3.90 W. 100 V against the 80 V recommended.')


def main():
    parts = X.open_book(XL)
    xml = parts[PC].decode('utf-8')
    for ref, was, now, _ in NUMS:
        cur = re.search(r'<c r="%s"[^>]*><v>([^<]*)</v>' % ref, xml).group(1)
        if abs(float(cur) - float(now)) < 1e-12:
            print('%s already %s' % (ref, now))
            continue
        assert abs(float(cur) - float(was)) < 1e-12, '%s is %s' % (ref, cur)
        xml = X.set_cell(xml, ref, X.cell_n(ref, X.style_of(xml, ref), now))
    if PART not in xml:
        xml = X.set_cell(xml, 'C92', X.cell_t('C92', X.style_of(xml, 'C92'),
                                              PART))
    parts[PC] = xml.encode('utf-8')
    log = parts[LOG].decode('utf-8')
    if MARK not in log:
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
        rows = [(None, None, None, None, WHY),
                ('Power Components', 'C92', 'TPH3R70APL1', PART,
                 'SR part number')] + [
            ('Power Components', ref, was, now, what)
            for ref, was, now, what in NUMS]
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
    print('written:', XL, '\ncopied :', VAR)


if __name__ == '__main__':
    main()
