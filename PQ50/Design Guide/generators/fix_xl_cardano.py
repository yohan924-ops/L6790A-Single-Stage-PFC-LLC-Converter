# -*- coding: utf-8 -*-
"""Root cause E, step 1: solve f_n in closed form instead of searching a grid.

RTC answers the central question of this topology - at each line phase, what
switching frequency delivers the gain the boundary condition demands - by laying
out an 83-column grid of normalised frequencies, evaluating the gain across it,
and interpolating where the curve crosses the requirement. 10,008 formulas, and
its upper end is anchored to

    fn.max = SQRT(lambda/(1+lambda-1/M))

which is imaginary whenever M < 1/(1+lambda). At a morphing FB corner it is, so
the grid cannot be pointed there without taking the whole sheet down with it.

But M(f_n) = M_req is a CUBIC in x = 1/f_n^2, and the physical (inductive) root
is always the k = 1 Cardano branch - 6,089 cases checked, HISTORY 2. Excel has
ACOS and COS natively, so it is thirteen rows:

    a2 = (Q^2 - 2L(1+L))/L^2        p = a1 - a2^2/3
    a1 = ((1+L)^2 - 2Q^2 - 1/M^2)/L^2   q = 2a2^3/27 - a2 a1/3 + a0
    a0 = Q^2/L^2                    w = 2 SQRT(-p/3)
    f_n = 1 / SQRT( w cos( acos(3q/(pw))/3 - 2pi/3 ) - a2/3 )

with NA() where no real inductive root exists - the same answer the grid gives
by finding no crossing.

This writes the 18 points (6 theta x 3 input voltages) into the free rows below
218 and points BB149..BB202 at them. The grid rows 60..93 are LEFT IN PLACE and
echoed beside each result, so the two methods can be read against each other
before anything is deleted. The charts are untouched: no chart plots rows 60..93
(checked - they draw rows 25/28/29/31/47/49/50/53/55/56/67/69/70 and beyond).
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx_patch as X                                               # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')

R0 = 220                     # first row of the new block
LAM = '$C$23'                # lambda, already on the sheet
THETA = ['pi/2', '5pi/12', 'pi/3', 'pi/4', 'pi/6', 'pi/12']
# (label, first Mreq row, first grid-solution row, first BB cell row)
BANDS = [('Vin.min', 53, 60, 149), ('Vin.max', 67, 74, 197),
         ('Vin.nom', 81, 88, 173)]
QROW = 41                    # Q(Po, theta) rows 41..46, same theta order

ROWS = ['설명', 'M.req', 'Q', 'a2', 'a1', 'a0', 'p', 'q', 'w', 'z', 'ang',
        'x', 'f.n (닫힌형)', 'f.n (격자)', '차이 [%]']


def colname(i):
    t = ''
    while i:
        i, r = divmod(i - 1, 26)
        t = chr(65 + r) + t
    return t


def part_of(parts, name):
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                          parts['xl/_rels/workbook.xml.rels'].decode('utf-8')))
    for nm, r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
        if nm.replace('&amp;', '&') == name:
            return 'xl/' + rid[r].lstrip('/')
    raise KeyError(name)


def block(c, mrow, qrow, grow):
    """the thirteen formulas for one (band, theta) column"""
    def r(k):
        return '%s%d' % (c, R0 + k)
    return {
        R0 + 1: '$C$%d' % mrow,
        R0 + 2: '$C$%d' % qrow,
        R0 + 3: '(%s^2-2*%s*(1+%s))/%s^2' % (r(2), LAM, LAM, LAM),
        R0 + 4: '((1+%s)^2-2*%s^2-1/%s^2)/%s^2' % (LAM, r(2), r(1), LAM),
        R0 + 5: '%s^2/%s^2' % (r(2), LAM),
        R0 + 6: '%s-%s^2/3' % (r(4), r(3)),
        R0 + 7: '2*%s^3/27-%s*%s/3+%s' % (r(3), r(3), r(4), r(5)),
        R0 + 8: 'IF(%s<0,2*SQRT(-%s/3),NA())' % (r(6), r(6)),
        R0 + 9: 'IF(ISNA(%s),NA(),3*%s/(%s*%s))' % (r(8), r(7), r(6), r(8)),
        R0 + 10: 'IF(OR(ISNA(%s),ABS(%s)>1),NA(),ACOS(%s)/3)' % (r(9), r(9), r(9)),
        R0 + 11: 'IF(ISNA(%s),NA(),%s*COS(%s-2*PI()/3)-%s/3)'
                 % (r(10), r(8), r(10), r(3)),
        R0 + 12: 'IF(OR(ISNA(%s),%s<=0),NA(),1/SQRT(%s))' % (r(11), r(11), r(11)),
        R0 + 13: 'IF(MAX(C%d:CH%d)>0,MAX(C%d:CH%d),NA())' % (grow, grow, grow, grow),
        R0 + 14: 'IF(OR(ISNA(%s),ISNA(%s)),NA(),(%s/%s-1)*100)'
                 % (r(12), r(13), r(12), r(13)),
    }


def main():
    bak = X.backup(XL)
    print('백업 %s' % os.path.basename(bak))
    parts = X.open_book(XL)
    p = part_of(parts, 'RTC')
    xml = parts[p].decode('utf-8')
    if re.search(r'<c r="C%d"' % (R0 + 12), xml):
        print('이미 적용돼 있다.')
        return 0

    for k in range(len(ROWS)):
        xml = X.ensure_row(xml, R0 + k)
    st_txt = X.style_of(xml, 'B41')
    st_num = X.style_of(xml, 'C41')

    # row labels down column B
    for k, name in enumerate(ROWS):
        ref = 'B%d' % (R0 + k)
        xml = X.set_cell(xml, ref, X.cell_t(ref, st_txt, name))

    n = 0
    col = 3                                     # start at C
    repoint = []
    for bname, mrow0, grow0, bb0 in BANDS:
        for k, th in enumerate(THETA):
            c = colname(col)
            xml = X.set_cell(xml, '%s%d' % (c, R0),
                             X.cell_t('%s%d' % (c, R0), st_txt,
                                      '%s @ %s' % (bname, th)))
            for row, f in block(c, mrow0 + k, QROW + k, grow0 + k).items():
                ref = '%s%d' % (c, row)
                xml = X.set_cell(ref and xml, ref, X.cell_f(ref, st_num, f))
                n += 1
            repoint.append(('BB%d' % (bb0 + k), '%s%d' % (c, R0 + 12)))
            col += 1

    # BB149..BB202 now read the closed form
    for bb, src in repoint:
        xml = X.set_cell(xml, bb, X.cell_f(bb, X.style_of(xml, bb), src))
    parts[p] = xml.encode('utf-8')
    X.write_book(XL, parts)
    print('  Cardano 블록 18개 · 수식 %d개  (RTC 행 %d~%d, 열 C~%s)'
          % (n, R0, R0 + len(ROWS) - 1, colname(col - 1)))
    print('  BB149..BB202 %d개를 닫힌형으로 연결' % len(repoint))
    print('  격자 행 60~93 은 그대로 두고 행 %d 에 나란히 인쇄한다' % (R0 + 13))
    print()
    print('Excel 에서 열었다 저장한 뒤 rtc_check.py 로 18점을 확인할 것.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
