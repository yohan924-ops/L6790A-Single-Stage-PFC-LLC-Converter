# -*- coding: utf-8 -*-
"""The theta = 0 sample the Simpson rule was missing for the primary current.

fix_xl_cc.py added the line-cycle integral and left the theta = 0 term out,
because for the secondary and output-node currents it is exactly zero - the load
goes as sin^2. The PRIMARY current is not zero there: the magnetising current
flows at every phase. Dropping it cost 1.83 %.

The endpoint is a closed form of quantities the sheet already has. Below
resonance I_Lm is clamped at f_r (the sheet writes IF(fsw<fr,fr,fsw)), so as
theta -> 0

    I_Lm(0)  = 0.25*n*Vo_eff/(Lm*f_r)                    = 12.356 A
    I_pri(0) = SQRT( I_Lm^2/3 + (I_Lm*(1 - f_o/f_r))^2 ) =  8.709 A

with f_o/f_r already in Res. Tank Design D54. Verified against the 1441-point
sweep: the primary rms goes from -1.83 % to -0.02 %, and six theta are enough -
adding more does not improve it, because the error was the endpoint, not the
spacing.

My first attempt at this endpoint evaluated I_Lm at f_o instead of f_r and got
20.7 A, which made the answer WORSE (+4.7 %). The clamp is the whole point.
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

LM = ("IF('Res. Tank Design'!$F$45,'Res. Tank Design'!$F$45,"
      "'Res. Tank Design'!$D$45)")


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

    if re.search(r'<c r="I29"', xml):
        print('이미 적용돼 있다.')
        return 0

    st = lambda r: X.style_of(xml, r)                                # noqa: E731
    cells = [
        ('I20', X.cell_t('I20', st('C20'), '0 (θ→0)')),
        # magnetising current at theta = 0: f_sw is below resonance so the
        # sheet's max(fsw,fr) clamp makes this the value at f_r
        ('I28', X.cell_f('I28', st('C28'),
                         '0.5*(0.5*$C$17*$C$18)/(%s*C22)*1000' % LM)),
        ('I29', X.cell_f('I29', st('C29'),
                         "SQRT(I28^2/3+(I28*(1-'Res. Tank Design'!$D$54))^2)")),
    ]
    for ref, cell in cells:
        xml = X.set_cell(xml, ref, cell)
        print('  %-5s %s' % (ref, re.search(r'<f>(.*?)</f>', cell).group(1)[:62]
                             if '<f>' in cell else '(라벨)'))

    # fold the endpoint into the Simpson sum with its weight of 1
    old = '(4*H29^2+2*G29^2+4*C29^2+2*D29^2+4*F29^2+1*E29^2)/18'
    new = '(1*I29^2+4*H29^2+2*G29^2+4*C29^2+2*D29^2+4*F29^2+1*E29^2)/18'
    m = re.search(r'<c r="J29"[^>]*>.*?</c>', xml, re.S)
    if old.replace('^', '^') not in m.group(0):
        raise SystemExit('J29 의 현재 수식이 예상과 다르다:\n  %s' % m.group(0)[:200])
    # 'SQRT%s' % new would put the /18 OUTSIDE the root - new already carries
    # its own brackets, so they would become SQRT's. That shipped once and gave
    # 2.57 A instead of 10.90.
    xml = X.set_cell(xml, 'J29', X.cell_f('J29', X.style_of(xml, 'J29'),
                                          'SQRT(%s)' % new))
    print('  J29   Simpson 합에 θ=0 항(가중치 1) 추가')
    parts[cc] = xml.encode('utf-8')
    X.write_book(XL, parts)
    print()
    print('예상: I29 ~ 8.709 A · J29 ~ 10.898 A (SMath 10.900, 오차 −0.02 %)')
    print('Excel 에서 열었다 저장할 것.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
