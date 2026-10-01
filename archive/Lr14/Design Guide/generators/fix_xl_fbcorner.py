# -*- coding: utf-8 -*-
"""Root cause E, step 2: let the workbook see the FB morphing corner.

With the solutions now coming from the closed form (fix_xl_cardano.py), the
grid is only chart data - but its upper end is still

    CG26  fn.max = SQRT(lambda/(1+lambda-1/M))
    CG25  grid top = 1.5 * fn.max

and that square root goes imaginary the moment M falls below 1/(1+lambda), which
is exactly what happens at the FB corner. So the axis has to be made robust
BEFORE Vin_max can be pointed there, or the 23 charts die with it.

Three terms, each covering a case the others miss - tested over eight specs
(lambda 0.15..0.80, M 0.40..1.23), minimum margin 26 %:

    zero-load limit   SQRT(lambda/(1+lambda-1/M))   when it exists, else 0
    finite-Q asymptote  from 1/M^2 = (1+lambda)^2 + Q^2 (f-1/f)^2
    spec ceiling      f_sw,max,spec / f_r

Then RTC C9 (83 cells, the Vin_max header row) moves from Design Spec D79
(264 Vac, the raw line maximum) to MAX(D79, D81) - D81 = 2*235/SQRT(2) =
332.34 V is the largest equivalent input the tank ever sees, and the workbook
has been computing it all along without reading it anywhere.

That makes Device Setting D2 the real f_sw,max (about 250 kHz instead of 189)
and with it C_T's design ceiling, the last row that still differs.
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

LAM, M, QPK = '$C$23', '$C$18', '$C$41'
SPEC_FN = "'Design Spec'!$D$43/'Res. Tank Design'!$D$55"
# f - 1/f = SQRT(1/M^2-(1+L)^2)/Q  ->  f = (x + SQRT(x^2+4))/2
ASYM_X = "SQRT(MAX(0,1/%s^2-(1+%s)^2))/%s" % (M, LAM, QPK)
FN_MAX = ("MAX(IF(1+{L}-1/{M}>0,SQRT({L}/(1+{L}-1/{M})),0),"
          "({X}+SQRT({X}^2+4))/2,{S})").format(L=LAM, M=M, X=ASYM_X, S=SPEC_FN)


def part_of(parts, name):
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                          parts['xl/_rels/workbook.xml.rels'].decode('utf-8')))
    for nm, r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
        if nm.replace('&amp;', '&') == name:
            return 'xl/' + rid[r].lstrip('/')
    raise KeyError(name)


def colname(i):
    t = ''
    while i:
        i, r = divmod(i - 1, 26)
        t = chr(65 + r) + t
    return t


def main():
    bak = X.backup(XL)
    print('백업 %s' % os.path.basename(bak))
    parts = X.open_book(XL)
    p = part_of(parts, 'RTC')
    xml = parts[p].decode('utf-8')

    # --- 1. make the grid axis robust ---------------------------------------
    m = re.search(r'<c r="CG26"[^>]*(?:/>|>.*?</c>)', xml, re.S)
    if 'MAX(IF' in (m.group(0) if m else ''):
        print('  건너뜀 CG26 (이미 클램프돼 있다)')
    else:
        xml = X.set_cell(xml, 'CG26',
                         X.cell_f('CG26', X.style_of(xml, 'CG26'), FN_MAX))
        print('  CG26  fn.max 에 클램프 + 점근해 + 사양 상한 (3항 MAX)')

    # --- 2. point Vin_max at the largest EQUIVALENT input --------------------
    n = 0
    old = "'Design Spec'!$D$79"
    new = "MAX('Design Spec'!$D$79,'Design Spec'!$D$81)"
    for i in range(3, 3 + 83):                     # C .. CG
        ref = '%s9' % colname(i)
        mm = re.search(r'<c r="%s"[^>]*>(.*?)</c>' % ref, xml, re.S)
        if not mm:
            continue
        f = re.search(r'<f[^>]*>(.*?)</f>', mm.group(1), re.S)
        if not f or old not in f.group(1):
            continue
        xml = X.set_cell(xml, ref, X.cell_f(ref, X.style_of(xml, ref), new))
        n += 1
    print('  행 9  Vin_max 를 MAX(D79, D81) 로 — %d칸' % n)

    # --- 3. say so on the sheet ---------------------------------------------
    xml = X.set_cell(xml, 'B9', X.cell_t(
        'B9', X.style_of(xml, 'B9'),
        'Vin_max (equivalent, = MAX of the AC maximum and the FB morphing corner)'))
    parts[p] = xml.encode('utf-8')
    X.write_book(XL, parts)
    print()
    print('예상: Device Setting D2 189.3 -> 약 249.6 kHz · C_T 상한 839 -> 700 pF')
    print('차트의 "@Vin_max" 곡선은 이제 264 V 가 아니라 332.34 V 를 그린다.')
    print('Excel 에서 열었다 저장한 뒤 rtc_check.py 와 xl_sm_compare.py 를 돌릴 것.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
