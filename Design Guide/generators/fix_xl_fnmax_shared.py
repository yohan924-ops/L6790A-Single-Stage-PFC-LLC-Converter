# -*- coding: utf-8 -*-
"""fn.max is a SHARED formula across row 26 - clamping only CG26 left 82 #NUM!.

Row 26 carries three shared masters, not 83 independent cells:

    si=22  ref C26:AH26   (C23/(1+C23-(1/C18)))^0.5
    si=23  ref AI26:BN26  (AI23/(1+AI23-(1/AI18)))^0.5
    si=24  ref BO26:CF26  (BO23/(1+BO23-(1/BO18)))^0.5

Once Vin_max moved to the FB corner every one of them went imaginary. Patching
the masters' TEXT in place - keeping t="shared", ref and si - makes all 83
columns follow, which is the same mechanism C.12 used for f_px.

The clamp is written with column-RELATIVE references so the shared children
shift correctly: each column reads its own 23/18/41, and those rows hold the
same value in every column anyway.
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

SPEC = "'Design Spec'!$D$43/'Res. Tank Design'!$D$55"


def clamped(c):
    """the three-term ceiling, in column-relative form for shared use"""
    lam, m, q = '%s23' % c, '%s18' % c, '%s41' % c
    x = 'SQRT(MAX(0,1/{M}^2-(1+{L})^2))/{Q}'.format(M=m, L=lam, Q=q)
    return ('MAX(IF(1+{L}-1/{M}>0,SQRT({L}/(1+{L}-1/{M})),0),'
            '(({X})+SQRT(({X})^2+4))/2,{S})'
            .format(L=lam, M=m, X=x, S=SPEC))


MASTERS = [('C', '22'), ('AI', '23'), ('BO', '24')]


def part_of(parts, name):
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                          parts['xl/_rels/workbook.xml.rels'].decode('utf-8')))
    for nm, r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
        if nm.replace('&amp;', '&') == name:
            return 'xl/' + rid[r].lstrip('/')
    raise KeyError(name)


def main():
    bak = X.backup(XL)
    print('백업 %s' % os.path.basename(bak))
    parts = X.open_book(XL)
    p = part_of(parts, 'RTC')
    xml = parts[p].decode('utf-8')

    n = 0
    for col, si in MASTERS:
        old = '(%s23/(1+%s23-(1/%s18)))^0.5' % (col, col, col)
        pat = (r'(<f t="shared" ref="%s26:[A-Z]+26" si="%s">)%s(</f>)'
               % (col, si, re.escape(X.esc(old))))
        m = re.search(pat, xml)
        if not m:
            if X.esc(clamped(col)) in xml:
                print('  건너뜀 %s26 (이미 클램프돼 있다)' % col)
                continue
            raise SystemExit('%s26 의 공유 마스터를 찾지 못했다' % col)
        xml = xml[:m.start()] + m.group(1) + X.esc(clamped(col)) + m.group(2) \
            + xml[m.end():]
        print('  %s26 (si=%s) 마스터 교체 -> 그 밴드의 열 전체가 따라온다' % (col, si))
        n += 1

    # drop the stale #NUM! caches on rows 26/27 so nothing reads them before
    # Excel recalculates
    before = xml.count('t="e"')
    for row in (26, 27):
        xml = re.sub(r'(<c r="[A-Z]+%d"[^>]*?) t="e"' % row, r'\1', xml)
        xml = re.sub(r'(<c r="[A-Z]+%d"[^>]*>(?:<f[^>]*(?:/>|>.*?</f>))?)'
                     r'<v>#NUM!</v>' % row, r'\1', xml)
    print('  행 26·27 의 낡은 #NUM! 캐시 %d개 제거' % (before - xml.count('t="e"')))

    parts[p] = xml.encode('utf-8')
    X.write_book(XL, parts)
    print()
    print('예상: fn.max = 1.4827 (사양 상한 항이 이긴다) · 격자 상한 2.2241 · #NUM! 0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
