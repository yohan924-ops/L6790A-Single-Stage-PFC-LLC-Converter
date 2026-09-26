# -*- coding: utf-8 -*-
"""Surface the realised output voltage next to the target it is compared with.

The workbook already computes it - CompensationNet&Check D38,
"Regulated ouput voltage" = D22*(D36+F37)/F37 = 25.177 V from the divider that
was actually selected. But it sits four sheets away from Design Spec D23, the
25 V the designer typed, under a label that reads almost the same. That is how
I ended up comparing the worksheet's realised value against the target and
calling the 0.71 % a difference.

So: mirror it beside the target, and make both labels say which is which.
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

    # --- Design Spec: mirror the realised value beside the target ----------
    p = part_of(parts, 'Design Spec')
    xml = parts[p].decode('utf-8')
    if re.search(r'<c r="G23"', xml):
        print('  건너뜀 Design Spec G23 (이미 있다)')
    else:
        xml = X.set_cell(xml, 'F23', X.cell_t(
            'F23', X.style_of(xml, 'C23'), '실현값 (선정 분압기) ->'))
        xml = X.set_cell(xml, 'G23', X.cell_f(
            'G23', X.style_of(xml, 'D23'), "'CompensationNet&Check+!D38"))
        parts[p] = xml.encode('utf-8')
        print("  Design Spec  F23/G23  <- 'CompensationNet&Check'!D38  (25.177 V)")

    # --- make the two labels distinguishable ------------------------------
    p = part_of(parts, 'Design Spec')
    xml = parts[p].decode('utf-8')
    xml = X.set_cell(xml, 'B23', X.cell_t(
        'B23', X.style_of(xml, 'B23'),
        'Regulated Output Voltage - TARGET (the divider is chosen to hit this)'))
    parts[p] = xml.encode('utf-8')
    print('  Design Spec  B23      라벨에 TARGET 명시')

    p = part_of(parts, 'CompensationNet&Check')
    xml = parts[p].decode('utf-8')
    xml = X.set_cell(xml, 'B38', X.cell_t(
        'B38', X.style_of(xml, 'B38'),
        'Regulated output voltage - ACTUAL, from the selected divider '
        '(target is Design Spec D23)'))
    parts[p] = xml.encode('utf-8')
    print('  CompNet      B38      라벨에 ACTUAL 명시')

    X.write_book(XL, parts)
    print()
    print('Excel 에서 열었다 저장할 것.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
