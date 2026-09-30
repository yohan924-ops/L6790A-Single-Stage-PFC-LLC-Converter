# -*- coding: utf-8 -*-
"""Record two things the SMath revision established, in the workbook's own log.

Neither changes a cell. Both are the kind of fact that gets re-derived from
scratch by the next person because nothing in the file says it.

1. THE COARSE QUADRATURE IS JUSTIFIED. C.18 put a Simpson integral in `CC`
   column J - seven points across the half cycle, weights 1,4,2,4,2,4,1 over
   18 - and the SMath sheet does the same thing with five. Neither had ever
   been checked against a fine grid, so both looked like the sort of
   approximation someone would later "improve" or distrust. Swept at 2000
   intervals: the seven-point rule is 0.0011 % low and the five-point rule
   0.0013 % low. Nothing downstream can see that.

2. fsw.max IS UPSTREAM OF THE TANK. `Design Spec` D43 is labelled "Maximum
   Switching Frequency (1.5*f.R1 sugg)", which reads as a limit to check
   against afterwards. It is not: `Res. Tank Design` D13 and D14 - the
   lambda candidates lambda.min.2 and lambda.min.TD - both DIVIDE by a term
   built from it,

       D13 = D12 / (1 - (fr/fsw.max)^2)
       D14 = D12 / (1 - (pi^2/8)(fr/fsw.max)^2)

   and D16 takes the largest of the four. So the number typed into D43
   computes lambda, and lambda computes L.m. Here fr/fsw.max = 150/225, the
   squared ratio is 44.4 %, and the two denominators lift the requirement
   from D12 to roughly twice it. Push D43 toward fr and they go to zero.

   That is a different kind of quantity from f.sw.max.design on `Device
   Setting`, which is the oscillator ceiling fixed by R.T, C.T and the idle
   time - a real limit, checked after the fact.

    python log_xl_findings.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx_patch as X                                                # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')

ROWS = [
    ('CC', 'J25 – J31',
     'The Simpson integral C.18 installed in column J - seven points over the '
     'half cycle, weights 1,4,2,4,2,4,1 over 18 - had never been checked '
     'against a fine grid, so there was no way to tell a justified '
     'approximation from a rough one.',
     'Swept at 2000 intervals: the seven-point rule reads 0.0011 % low and '
     'the five-point rule the SMath sheet uses reads 0.0013 % low. Both are '
     'far inside every margin downstream. No cell changed - this is a record '
     'so the rule is not "improved" or distrusted later.'),
    ('Design Spec', 'D43',
     'D43 is labelled "Maximum Switching Frequency (1.5*f.R1 sugg)", which '
     'reads as a limit to be checked afterwards. It is not. Res. Tank Design '
     'D13 and D14 - the lambda candidates lambda.min.2 and lambda.min.TD - '
     'both divide by a term built from it: D13 = D12/(1-(fr/fsw.max)^2) and '
     'D14 = D12/(1-(pi^2/8)(fr/fsw.max)^2), and D16 takes the largest of the '
     'four.',
     'So D43 COMPUTES lambda, and lambda computes L.m. At fr/fsw.max = '
     '150/225 the squared ratio is 44.4 % and the two denominators lift the '
     'requirement to roughly twice D12; push D43 toward fr and they go to '
     'zero. Not to be confused with f.sw.max.design on Device Setting, which '
     'is the oscillator ceiling set by R.T, C.T and the idle time - a real '
     'limit, checked after the fact. No cell changed.'),
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
    bak = X.backup(XL)
    print('백업 %s' % os.path.basename(bak))
    parts = X.open_book(XL)
    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    hay = xml + parts.get('xl/sharedStrings.xml', b'').decode('utf-8')
    n = 0
    for sheet, cells, why, what in ROWS:
        if why[:48] in hay:
            print('  건너뜀 (이미 기록돼 있다): %s %s' % (sheet, cells))
            continue
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', xml)) + 1
        xml = X.ensure_row(xml, r)
        for col, text, st in (('B', sheet, '7'), ('C', cells, '7'),
                              ('D', why, '8'), ('E', what, '8')):
            xml = X.set_cell(xml, col + str(r),
                             X.cell_t(col + str(r), st, text))
        print('  CHANGELOG_rev0_6 행 %d: %s %s' % (r, sheet, cells))
        n += 1
    if not n:
        print('바뀐 것이 없다')
        return 0
    parts[cl] = xml.encode('utf-8')
    X.write_book(XL, parts)
    print()
    print('수식도 값도 손대지 않았다 - 기록 %d 줄뿐이다.' % n)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
