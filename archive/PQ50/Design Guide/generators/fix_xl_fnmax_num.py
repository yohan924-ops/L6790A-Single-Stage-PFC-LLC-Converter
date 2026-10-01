# -*- coding: utf-8 -*-
"""RTC rows 26-27: 164 cells reading #NUM!, and the reason is worth knowing.

fn.max asks at what normalised frequency the NO-LOAD gain curve falls to the
required gain:

    fn.max = sqrt( lambda / (1 + lambda - 1/M) )

The no-load gain falls monotonically from 1 at resonance towards its asymptote
1/(1+lambda) - here 1/1.55 = 0.6452 - and never below it. Cause E moved Vin_max
from 264 Vac to the FB morphing corner, 332.34 Vac equivalent, which dropped the
required gain to M = 0.6383. That is BELOW the asymptote, so the equation has no
root, the radicand goes negative, and every cell in the row returns #NUM!.

Nothing is broken by it. The grid axis is built from CG25 = 1.5 * CG26, and
CG26 already carries a three-way guard; the row-25 axis is a linear
interpolation from it, and the answers the design reads (BB149..BB154) come from
the Cardano block. Rows 26 and 27 are read by nothing at all. But 164 error
cells in a delivered workbook read as a broken file and they bury real errors in
the audit output, so the per-column expression gets the same guard CG26 has.

The guard is not a fudge: below the asymptote there is genuinely no no-load
crossing, and the frequency ceiling then comes from the loaded curve and from
the design's own f_sw,max, which are the other two terms of the CG26 MAX.

Every cell in row 26 is part of one of three shared-formula groups, all three
confined to that row. They are rewritten as plain formulas, so no master is left
pointing at followers that no longer match - that mismatch is what corrupted
this workbook once before.

    python fix_xl_fnmax_num.py
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

LABEL = ('fn.max  (no-load crossing; falls back to the CG26 ceiling when the '
         'required gain is below the 1/(1+lambda) asymptote)')
LOG = ('RTC', 'C26:CF26 (82 cells + row 27)',
       'Every cell of row 26 returned #NUM!, and row 27 with it - 164 error '
       'cells. fn.max = SQRT(lambda/(1+lambda-1/M)) has no root once M falls '
       'below the no-load asymptote 1/(1+lambda) = 0.6452, and cause E moved '
       'Vin_max to the FB morphing corner (332.34 Vac equivalent), which took '
       'the required gain down to M = 0.6383.',
       'The per-column expression now carries the same guard CG26 already had: '
       'IF(1+lambda-1/M>0, SQRT(...), $CG$26). All three shared-formula groups '
       'in the row were rewritten as plain formulas so that no master is left '
       'pointing at followers with different text.',
       'Nothing read rows 26 or 27 - the grid axis comes from CG25 = 1.5*CG26 '
       'by linear interpolation and the answers come from the Cardano block, '
       'so no number moves. But 164 visible errors read as a broken workbook '
       'and they bury real findings in the audit output. The guard is not a '
       'fudge: below the asymptote there is genuinely no no-load crossing, and '
       'the ceiling then comes from the loaded curve and from the design '
       'f_sw,max, which are the other two terms of the CG26 MAX. Grid top is '
       'now f_n = 2.2241 = 337.5 kHz, and f_sw,max 249.6 kHz sits inside it.')


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
    p = part_of(parts, 'RTC')
    xml = parts[p].decode('utf-8')

    body = re.search(r'<row r="26"[^>]*>(.*?)</row>', xml, re.S).group(1)
    cols = [m.group(1) for m in
            re.finditer(r'<c r="([A-Z]+)26"[^>]*>\s*<f', body)]
    cols = [c for c in cols if c != 'CG']
    print('  대상 %d열  %s .. %s' % (len(cols), cols[0], cols[-1]))

    for c in cols:
        ref = '%s26' % c
        f = ('IF(1+{c}23-1/{c}18>0,SQRT({c}23/(1+{c}23-1/{c}18)),$CG$26)'
             .format(c=c))
        xml = X.set_cell(xml, ref, X.cell_f(ref, X.style_of(xml, ref), f))
    xml = X.set_cell(xml, 'B26', X.cell_t('B26', X.style_of(xml, 'B26'), LABEL))

    left = len(re.findall(r't="shared"',
                          re.search(r'<row r="26"[^>]*>(.*?)</row>',
                                    xml, re.S).group(1)))
    print('  남은 shared 속성 %d개 (0이어야 한다)' % left)
    assert left == 0
    parts[p] = xml.encode('utf-8')

    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    hay = xml + parts.get('xl/sharedStrings.xml', b'').decode('utf-8')
    m = re.search(r'<c r="C(\d+)"[^>]*><is><t[^>]*>C26:CF26', xml)
    if m:
        r = int(m.group(1))
        print('  CHANGELOG 행 %d 갱신' % r)
    else:
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', xml)) + 1
    xml = X.ensure_row(xml, r)
    for col, text, st in (('B', LOG[0], '7'), ('C', LOG[1], '7'),
                          ('D', LOG[2], '8'), ('E', LOG[3], '8'),
                          ('F', LOG[4], '8')):
        xml = X.set_cell(xml, col + str(r), X.cell_t(col + str(r), st, text))
    parts[cl] = xml.encode('utf-8')

    X.write_book(XL, parts)
    print()
    print('예상: 행 26 전 열 = 1.4827 · 행 27 전 열 = 225.0 kHz · #NUM! 0개')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
