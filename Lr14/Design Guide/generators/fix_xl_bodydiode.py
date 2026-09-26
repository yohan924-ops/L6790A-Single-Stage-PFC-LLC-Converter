# -*- coding: utf-8 -*-
"""Put the body-diode recovery condition into the workbook too.

The primary-switch block on Power Components asks for voltage rating, current
rating, RDSon, Coss, ambient temperature and thermal resistance. It never asks
about the body diode - and in an LLC that is the parameter that decides whether
an off-resonance excursion costs watts or the device.

The sheet, the guide and the deck now all carry it. Leaving the workbook out
would mean whoever works from the workbook alone never sees the requirement,
which is exactly the kind of split that C.18 was.

Two rows, in the free slot inside the block the designer is already filling in:

    D74   bus voltage across the recovering diode = SQRT(2) * Vac,max
    D75   current it has to recover               = the magnetising peak

No Qrr is assumed. Qrr is a device number and this sheet does not invent device
numbers; the rows state the CONDITION at which the datasheet figure must be
read, which is the part designers usually get wrong (they quote 25 C, low
dI/dt, where the part looks best).
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

# B = Parameter, C = Name, D = Value, E = Unit - the four columns every other
# row of this block uses. The first version filled in only B and D, so the two
# rows printed a bare number with no symbol and no unit.
ROWS = [
    (74, 'Body diode recovery condition - bus voltage', 'Vbd.rr',
     "SQRT(2)*'Design Spec'!D14", 'V'),
    (75, 'Body diode recovery condition - current', 'Ibd.rr',
     'CC!C28', 'A'),
]
LOG = ('Power Components', 'D74 · D75',
       '1차 스위치 선정 항목에 바디 다이오드 역회복 조건이 없다. 정상 ZVS 에서는 바디 '
       '다이오드가 데드타임에만 도통하고 채널이 거의 0 V 에서 전류를 넘겨받으므로 회복이 '
       '일어나지 않지만, 용량성 영역에서는 전류가 앞서므로 반대편 소자가 켜질 때 이 '
       '다이오드가 강제 역회복되고 관통 전류가 버스를 가로지른다. 과부하 · 부하 스텝 · '
       '저입력 · 기동이 모두 몇 사이클씩 그 영역으로 들어가므로 회피가 아니라 생존으로 '
       '설계해야 한다',
       'D74 = SQRT(2)*Vac,max = 373.4 V (용량성 영역에는 소프트 전이가 없어 정류된 라인 '
       '피크 그대로다), D75 = CC!C28 = 자화 전류 피크 12.36 A. Qrr 은 가정하지 않는다 — '
       '소자 값이다. 이 두 조건에서 trr · Qrr 을 규정할 것. 데이터시트 기본값(보통 25 °C, '
       '낮은 dI/dt)이 아니라 — Qrr 은 25 → 125 °C 에서 대략 두 배가 된다')


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
    p = part_of(parts, 'Power Components')
    xml = parts[p].decode('utf-8')

    for row, label, name, formula, unit in ROWS:
        xml = X.ensure_row(xml, row)
        for col, val, txt in (('B', label, True), ('C', name, True),
                              ('D', formula, False), ('E', unit, True)):
            ref = col + str(row)
            st = X.style_of(xml, col + '73')
            cell = (X.cell_t(ref, st, val) if txt else X.cell_f(ref, st, val))
            xml = X.set_cell(xml, ref, cell)
        print('  %-3d B %-42s C %-8s D %-26s E %s'
              % (row, label, name, formula, unit))
    parts[p] = xml.encode('utf-8')

    # and the changelog, so the workbook explains itself
    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    hay = xml + parts.get('xl/sharedStrings.xml', b'').decode('utf-8')
    if LOG[1] in hay:
        print('  CHANGELOG 건너뜀 (이미 기록돼 있다)')
    else:
        r = max(int(x) for x in re.findall(r'<row r="(\d+)"', xml)) + 1
        xml = X.ensure_row(xml, r)
        for col, text, st in (('B', LOG[0], '7'), ('C', LOG[1], '7'),
                              ('D', LOG[2], '8'), ('E', LOG[3], '8')):
            xml = X.set_cell(xml, col + str(r),
                             X.cell_t(col + str(r), st, text))
        parts[cl] = xml.encode('utf-8')
        print('  CHANGELOG_rev0_6 행 %d 에 기록' % r)

    X.write_book(XL, parts)
    print()
    print('예상: D74 = 373.35 V · D75 = 12.36 A')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
