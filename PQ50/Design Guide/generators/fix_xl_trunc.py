# -*- coding: utf-8 -*-
"""CC rows 25, 31 and 32: [64] squares a waveform [63] does not describe.

[63] computes the secondary peak from a sine that is TRUNCATED once fsw > fr -
that is precisely what its 1-cos(PI*fr/fsw) denominator means: the half period
ends before the resonant half sine does, so the current never comes back to
zero. [64] then takes the rms as Ipk*SQRT(d/4) with d = MIN(fsw,fr)/fr, which
clamps to Ipk/2 above resonance - the rms of a FULL half sine, which is a
different waveform.

For the segment [63] itself assumes, spanning phase Dphi = PI*fr/fsw,

    mean square = (Ipk^2/4) * d * [1 - SIN(2*Dphi)/(2*Dphi)]

Below resonance Dphi = PI, SIN(2*PI) = 0, the bracket is exactly 1 and this
collapses to what the sheet already had. So NO NUMBER IN THIS WORKBOOK MOVES:
CC evaluates at Vin,min, where fsw runs 90.4 to 127.5 kHz and never reaches
fr = 151.7 kHz. At the FB morphing corner, where 56 % of the line cycle IS
above resonance, the old expression is 8 % low.

Both this design and the guide's 240 W example have their worst secondary rms
at LOW line, so the sizing is unaffected either way. The correction matters
when a re-spec moves the worst corner to high line - and it removes an
inconsistency that would otherwise have to be re-derived by whoever noticed it
next.

    python fix_xl_trunc.py
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

COLS = 'CDEFGH'          # the six theta columns of the 100 % load block


def ktr(c):
    """1 - SIN(2*Dphi)/(2*Dphi), with Dphi = PI*fr/MAX(fsw,fr)"""
    p = '2*PI()*{c}22/MAX({c}21,{c}22)'.format(c=c)
    return '(1-SIN({p})/({p}))'.format(p=p)


def formulas(c):
    k = ktr(c)
    d = 'MIN({c}21,{c}22)/{c}22'.format(c=c)
    return {
        # per winding: CT keeps the whole leg current, FB splits the path
        '%s25' % c: ("IF('Design Spec'!$D$107=1,"
                     "{c}24*SQRT({d}/4*{k}),"
                     "{c}24*SQRT({d}/2*{k}))").format(c=c, d=d, k=k),
        # the output node sees the sum of both legs
        '%s31' % c: ('SQRT(0.5*{d}*{k}*({c}24^2)-{c}23^2+{c}15^2/2)'
                     ).format(c=c, d=d, k=k),
        '%s32' % c: '0.5*{d}*{k}*({c}24^2)'.format(c=c, d=d, k=k),
    }


LOG = ('CC', 'C25:H25 · C31:H31 · C32:H32',
       '[64] takes the secondary rms as Ipk*SQRT(d/4) with d = MIN(fsw,fr)/fr, '
       'which clamps to Ipk/2 above resonance - the rms of a FULL half sine. '
       'But [63], one row above, computes the peak from a TRUNCATED sine: its '
       '1-COS(PI*fr/fsw) denominator is exactly that truncation. Above '
       'resonance the switching half period ends before the resonant half sine '
       'does and the current never returns to zero, so the two rows describe '
       'different waveforms.',
       'Multiplied the mean square by the truncation factor '
       '1-SIN(2*Dphi)/(2*Dphi), Dphi = PI*fr/MAX(fsw,fr), in rows 25, 31 and '
       '32. Below resonance Dphi = PI and the factor is exactly 1.',
       'NO VALUE IN THIS WORKBOOK CHANGES. CC evaluates at Vin,min, where fsw '
       'runs 90.4 to 127.5 kHz and never reaches fr = 151.7 kHz, so the factor '
       'is 1 at every theta. At the FB morphing corner, where 56 % of the line '
       'cycle is above resonance, the old expression is 8.0 % low on the '
       'per-leg rms (23.04 vs 24.89 A) - and 8.4 % low on the guide\'s 240 W '
       'example. Both designs still have their worst secondary rms at LOW '
       'line (28.33 A here), so no sizing moves. It matters if a re-spec makes '
       'high line the worst corner. The same correction is in l6790.py, the '
       'SMath sheet (r.tr) and guide [64a].')


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
    p = part_of(parts, 'CC')
    xml = parts[p].decode('utf-8')

    n = 0
    for c in COLS:
        for ref, f in formulas(c).items():
            xml = X.set_cell(xml, ref, X.cell_f(ref, X.style_of(xml, ref), f))
            n += 1
    print('  %d칸 갱신  (%s 열 x 25/31/32행)' % (n, COLS))
    for row in (25, 31, 32):
        body = re.search(r'<row r="%d"[^>]*>(.*?)</row>' % row, xml, re.S).group(1)
        left = len(re.findall(r't="shared"', body))
        print('    행 %d 남은 shared 속성 %d' % (row, left))
    parts[p] = xml.encode('utf-8')

    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    m = re.search(r'<c r="C(\d+)"[^>]*><is><t[^>]*>C25:H25', xml)
    r = int(m.group(1)) if m else \
        max(int(x) for x in re.findall(r'<row r="(\d+)"', xml)) + 1
    xml = X.ensure_row(xml, r)
    for col, text, st in (('B', LOG[0], '7'), ('C', LOG[1], '7'),
                          ('D', LOG[2], '8'), ('E', LOG[3], '8'),
                          ('F', LOG[4], '8')):
        xml = X.set_cell(xml, col + str(r), X.cell_t(col + str(r), st, text))
    print('  CHANGELOG 행 %d' % r)
    parts[cl] = xml.encode('utf-8')

    X.write_book(XL, parts)
    print()
    print('예상: 저입력에서 인수 = 1 이므로 값은 하나도 안 바뀐다')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
