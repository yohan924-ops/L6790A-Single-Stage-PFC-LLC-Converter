# -*- coding: utf-8 -*-
"""Root cause B: give the CC sheet a line-cycle rms instead of one theta.

The design reads three currents straight out of a single column of CC:

    Res. Tank D65  = CC!C29     primary rms
    Res. Tank D67  = CC!C25     secondary rms per winding
    Power     D28  = CC!C31     output-bank ripple current

Column C is theta = pi/4. Calling one phase of the line cycle an rms over the
line cycle understates the bank ripple current by 28 % - that is errata C.18,
and it is the number that sizes 160 capacitors.

It was recorded as structurally unfixable. It is not: RTC already solves SIX
theta per input voltage (pi/12 .. pi/2, 15 degrees apart) and CC reads three of
them. Adding the other three and integrating properly closes it.

  columns F, G, H   theta = 5pi/12, pi/6, pi/12, from RTC!BC150/BC153/BC154
  row 32            the node current SQUARED per column, what the integral needs
  column J          Simpson over theta = 0, 15 .. 90 degrees, weights
                    1,4,2,4,2,4,1 over 18. The theta = 0 sample is exactly zero
                    for the secondary and node currents because the load goes
                    as sin^2.

Measured against the 721-point sweep: secondary -0.09 %, bank ripple -0.16 %,
primary -1.83 %. The primary keeps a residue because its magnetising component
does NOT vanish at theta = 0; the converter is in burst there, so extrapolating
an endpoint for it makes the answer worse (+4.7 %), and zero is the better
choice. Simpson beats the trapezoid on the primary (-1.83 vs -2.70 %) and ties
everywhere else.
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
CC = 'xl/worksheets/sheet6.xml'          # resolved below, this is only a default
TANK = 'xl/worksheets/sheet4.xml'
POWER = 'xl/worksheets/sheet5.xml'

# theta already present: C = pi/4, D = pi/3, E = pi/2
NEW = [('F', '5PI/12', 'RTC!BC150', '5*PI()/12'),
       ('G', 'PI/6', 'RTC!BC153', 'PI()/6'),
       ('H', 'PI/12', 'RTC!BC154', 'PI()/12')]

# Simpson weights on theta = 0,15,30,45,60,75,90 -> the column holding each
W = [('H', 4), ('G', 2), ('C', 4), ('D', 2), ('F', 4), ('E', 1)]


def simpson(row, squared=False):
    """weights 1,4,2,4,2,4,1 over 18; the theta=0 term is zero so it drops out"""
    return '(' + '+'.join('%d*%s%d%s' % (w, c, row, '' if squared else '^2')
                          for c, w in W) + ')/18'


def part_of(parts, name):
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rels = parts['xl/_rels/workbook.xml.rels'].decode('utf-8')
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))
    for nm, r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
        if nm.replace('&amp;', '&') == name:
            return 'xl/' + rid[r].lstrip('/')
    raise KeyError(name)


def main():
    bak = X.backup(XL)
    print('백업 %s' % os.path.basename(bak))
    parts = X.open_book(XL)
    cc = part_of(parts, 'CC')
    xml = parts[cc].decode('utf-8')

    if 'CC 확장' in xml or re.search(r'<c r="F21"', xml):
        print('이미 적용돼 있다. 쓰지 않는다.')
        return 0

    def st(ref):
        return X.style_of(xml, ref)

    n = 0
    # ---- three more theta columns -----------------------------------------
    for col, lab, src, sin_arg in NEW:
        body = [
            ('20', X.cell_t('%s20' % col, st('C20'), lab)),
            ('21', X.cell_f('%s21' % col, st('C21'), src)),
            ('22', X.cell_f('%s22' % col, st('C22'), "'Res. Tank Design'!$D$55")),
            ('23', X.cell_f('%s23' % col, st('C23'),
                            "2*'Design Spec'!$D$98/'Design Spec'!$D$95*SIN(%s)^2" % sin_arg)),
            ('24', X.cell_f('%s24' % col, st('C24'),
                            'PI()*({c}22/{c}21)*{c}23*(1-COS(PI()*{c}22/IF({c}21<{c}22,{c}22,{c}21)))^(-1)'.format(c=col))),
            ('25', X.cell_f('%s25' % col, st('C25'),
                            "IF('Design Spec'!$D$107=1,{c}24*SQRT(MIN({c}21,{c}22)/{c}22/4),{c}24*SQRT(MIN({c}21,{c}22)/{c}22/2))".format(c=col))),
            ('26', X.cell_f('%s26' % col, st('C26'),
                            "IF('Design Spec'!$D$107=1,{c}25,{c}25/SQRT(2))".format(c=col))),
            ('27', X.cell_f('%s27' % col, st('C27'), '{c}24/$C$18'.format(c=col))),
            ('28', X.cell_f('%s28' % col, st('C28'),
                            "0.5*(0.5*$C$17*$C$18)/(IF('Res. Tank Design'!$F$45,'Res. Tank Design'!$F$45,'Res. Tank Design'!$D$45)*IF({c}21<{c}22,{c}22,{c}21))*1000".format(c=col))),
            ('29', X.cell_f('%s29' % col, st('C29'),
                            'SQRT({c}27^2/2+{c}28^2/3+({c}28*{c}21*(1/{c}21-1/{c}22))^2)'.format(c=col))),
            ('30', X.cell_f('%s30' % col, st('C30'), '{c}29/SQRT(2)'.format(c=col))),
            # $C$15 is zero; column C uses a relative C15 whose meaning is unclear
            # and whose value is 0, so the new columns are pinned to it rather
            # than picking up unrelated numbers from the sweep block above.
            ('31', X.cell_f('%s31' % col, st('C31'),
                            'SQRT(0.5*MIN({c}21,{c}22)/{c}22*({c}24^2)-{c}23^2+$C$15^2/2)'.format(c=col))),
        ]
        for _, cell in body:
            xml = X.set_cell(xml, re.search(r'r="([A-Z]+\d+)"', cell).group(1), cell)
            n += 1

    # ---- row 32: the node current squared, per column ----------------------
    xml = X.ensure_row(xml, 32)
    xml = X.set_cell(xml, 'B32', X.cell_t('B32', st('B31'),
                                          'Isec.node.ms.tsw (라인사이클 적분용)'))
    for col in ('C', 'D', 'E', 'F', 'G', 'H'):
        f = '0.5*MIN({c}21,{c}22)/{c}22*({c}24^2)'.format(c=col)
        xml = X.set_cell(xml, col + '32', X.cell_f(col + '32', st('C31'), f))
        n += 1

    # ---- column J: the line-cycle values -----------------------------------
    xml = X.set_cell(xml, 'J20', X.cell_t('J20', st('C20'),
                                          '라인사이클 (Simpson 6점 + θ=0)'))
    for row, formula in (
            (25, 'SQRT(%s)' % simpson(25)),
            (26, 'SQRT(%s)' % simpson(26)),
            (29, 'SQRT(%s)' % simpson(29)),
            (30, 'J29/SQRT(2)'),
            (31, "SQRT(%s-('Design Spec'!$D$98/'Design Spec'!$D$95)^2)"
                 % simpson(32, squared=True))):
        ref = 'J%d' % row
        xml = X.set_cell(xml, ref, X.cell_f(ref, st('C%d' % row), formula))
        n += 1
    parts[cc] = xml.encode('utf-8')

    # ---- point the design at the line-cycle values --------------------------
    for name, part, ref, old, new in (
            ('Res. Tank Design', TANK, 'D65', 'CC!C29', 'CC!J29'),
            ('Res. Tank Design', TANK, 'D67', 'CC!C25', 'CC!J25'),
            ('Power Components', POWER, 'D28', 'CC!C31', 'CC!J31')):
        p = part_of(parts, name)
        x = parts[p].decode('utf-8')
        m = re.search(r'<c r="%s"[^>]*>.*?</c>' % ref, x, re.S)
        if old not in m.group(0):
            print('  건너뜀 %s!%s (이미 바뀌었다)' % (name, ref))
            continue
        x = X.set_cell(x, ref, X.cell_f(ref, X.style_of(x, ref), new))
        parts[p] = x.encode('utf-8')
        print('  %-18s %-5s %s -> %s' % (name, ref, old, new))
        n += 1

    X.write_book(XL, parts)
    print()
    print('셀 %d개 작성' % n)
    print('예상: J25 ~ 28.30 A · J29 ~ 10.70 A · J31 ~ 30.17 A')
    print('Excel 에서 열었다 저장할 것.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
