# -*- coding: utf-8 -*-
"""Temperature factors, and the one input that split the two feedback windows.

1  kT.pri and kT.sec were set to 1. The R_DS(on) figures entered are the
   datasheet MAXIMUM, which covers process spread at T_j = 25 C - not
   temperature. The same part at 125 C is about twice that for a superjunction
   device and about 1.5x for a low-voltage trench SR FET. Those are the numbers
   the multiplier is for.

2  V.Fo, the optocoupler LED forward drop, was 1.45 V here and 1.15 V in the
   SMath sheet. That single input feeds both R.P_max and the R.B window, and it
   pushed them 20 % apart - far enough that the two R.B windows did not overlap
   at all and no value could satisfy both documents:

       V.Fo 1.45  ->  R.B 5.873 .. 6.652 k   R.P_max 1.813 k
       V.Fo 1.15  ->  R.B 6.934 .. 8.001 k   R.P_max 1.438 k

   1.15 V is the right one. This loop drives the LED at I.FB/CTR = about
   0.55 mA, where an SFH617A sits near 1.1 V; 1.45 V is its drop at tens of
   milliamps, which the loop never reaches. It is also the conservative choice
   for R.P, whose limit must be rounded DOWN (appendix C.23).

3  With the windows agreed, R.P and R.B move inside them: 1.8 k exceeded the
   1.438 k ceiling and 5.6 k sat below the window floor.

    python fix_xl_comp.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx_patch as X                                               # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')

# sheet -> {ref: (value, what, was)}
EDIT = {
    'Power Components': {
        'D80': (2, 'kT.pri  RDSon rise to Tj,max, superjunction', 1),
        'D98': (1.5, 'kT.sec  RDSon rise to Tj,max, trench SR', 1),
    },
    'CompensationNet&Check': {
        'D28': (1.15, 'V.Fo  optodiode drop at the current this loop runs', 1.45),
        'F41': (1.3, 'R.P   selected - under the 1.438 k ceiling', 1.8),
        # the R.B window itself moves with R.P - V.Fo/R.P sits in its
        # denominator - so lowering R.P to 1.3 k pulled the window down to
        # 5.759..6.477 k. 6.2 k is its geometric middle.
        'F43': (6.2, 'R.B   selected - inside the 5.759..6.477 k window', 5.6),
    },
}

LOG = [
    ('Power Components', 'D80 · D98',
     'Both temperature multipliers were set to 1 while D70 and D96 hold the '
     'datasheet MAXIMUM R_DS(on). A datasheet maximum covers process spread at '
     'T_j = 25 C; it says nothing about temperature.',
     'kT.pri = 2 and kT.sec = 1.5, the usual rise to T_j = 125 C for a 600 V '
     'superjunction part and a low-voltage trench SR FET. Read the exact factor '
     'off the part\'s normalized R_DS(on) vs T_j curve and correct these.',
     'With STO60N045DM9 at 45 mOhm max: switching device 2.67 -> 5.35 W, '
     'statically-on device 5.34 -> 10.69 W, required Rth 18.7 -> 9.36 C/W. The '
     'statically-on device is the one that conducts continuously in half-bridge '
     'morphing mode, which is the normal mode on a 220 V mains.'),
    ('CompensationNet&Check', 'D28 · F41 · F43',
     'V.Fo was 1.45 V here and 1.15 V in the SMath sheet. It feeds R.P_max and '
     'both ends of the R.B window, and the 20 % it put between them left the two '
     'R.B windows DISJOINT - 5.873..6.652 k here against 6.934..8.001 k there - '
     'so no resistor value could satisfy both documents. R.P was selected at '
     '1.8 k and R.B at 5.6 k, which violate the SMath limits.',
     'V.Fo = 1.15 V on both. R.P = 1.3 k, below the 1.438 k ceiling. R.B = '
     '6.2 k. NOTE that the R.B window MOVES WITH R.P - V.Fo/R.P sits in its '
     'denominator - so bringing R.P down to 1.3 k pulled the window from '
     '6.934..8.001 k to 5.759..6.477 k. 6.2 k is the geometric middle of the '
     'window that actually applies.',
     'The loop drives the LED at I.FB/CTR of about 0.55 mA, where an SFH617A '
     'sits near 1.1 V; 1.45 V is its drop at tens of milliamps, which this loop '
     'never reaches. 1.15 V is also the conservative choice for R.P, whose '
     'limit is a MAXIMUM and must be rounded down - at 1.8 k the shunt '
     'regulator cathode current falls under its 0.8 mA minimum and it stops '
     'regulating (appendix C.23). C.Fo, C.F and R.F depend on R.B and are '
     're-selected in the SMath sheet against the new calculated values.'),
]


def part_of(parts, name):
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                          parts['xl/_rels/workbook.xml.rels'].decode('utf-8')))
    for nm, r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
        if nm.replace('&amp;', '&') == name:
            return 'xl/' + rid[r].lstrip('/')
    raise KeyError(name)


def main():
    print('백업 %s' % os.path.basename(X.backup(XL)))
    parts = X.open_book(XL)
    for sheet, cells in EDIT.items():
        p = part_of(parts, sheet)
        xml = parts[p].decode('utf-8')
        for ref, (val, what, was) in cells.items():
            xml = X.set_cell(xml, ref, X.cell_n(ref, X.style_of(xml, ref), val))
            print('  %-22s %-5s %-6s -> %-6s %s' % (sheet, ref, was, val, what))
        parts[p] = xml.encode('utf-8')

    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    r = max(int(x) for x in re.findall(r'<row r="(\d+)"', xml))
    for sheet, cells, was, now, why in LOG:
        m = re.search(r'<c r="C(\d+)"[^>]*><is><t[^>]*>%s<' % re.escape(cells), xml)
        rr = int(m.group(1)) if m else (r + 1)
        if not m:
            r = rr
        xml = X.ensure_row(xml, rr)
        for col, text, st in (('B', sheet, '7'), ('C', cells, '7'),
                              ('D', was, '8'), ('E', now, '8'), ('F', why, '8')):
            xml = X.set_cell(xml, col + str(rr), X.cell_t(col + str(rr), st, text))
        print('  CHANGELOG 행 %d  %s' % (rr, cells))
    parts[cl] = xml.encode('utf-8')

    X.write_book(XL, parts)
    print()
    print('예상: R.P.Max 1.438 k · R.B 창 5.759~6.477 k · Pdiss 5.35/10.69 W')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
