# -*- coding: utf-8 -*-
"""Write the three fixes into the workbook's own CHANGELOG sheet.

The workbook has to explain itself to whoever opens it next, without this
folder. fix_xl_causes.py changed six cells; those are three causes, and this
records them the way rows 1..75 are already written: sheet, cells, what was
wrong, what it is now.
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
PART = 'xl/worksheets/sheet1.xml'                # CHANGELOG_rev0_6
STYLE = {'B': '7', 'C': '7', 'D': '8', 'E': '8'}

ROWS = [
    ('Res. Tank Design', 'D28 · D29 · D30',
     'ZVS 검사가 탱크를 고른 뒤 다시 계산되지 않는다. D28 은 근사식 [36] 으로 f.n 을 '
     '0.82111 로 다시 구하고(지수 5 는 ST 문서에 근거가 없다), D29 는 실제 동작 Q 가 아니라 '
     '설계 상한 Q_ZVS = 0.8466 에서 위상을 낸다. D30 은 다시 실제 공진주파수가 아니라 목표치 '
     "'Design Spec'!D102 = 150 kHz 로 나눈다. 결과 T_ZC = 303 ns 로 실제보다 34 % 낮다",
     '실현값은 이미 워크북 안에 있다 — 격자가 푼 RTC!$BB$149 = 0.84006 과 RTC!$C$41 = '
     '0.7717. D28 = RTC!$BB$149, D29 의 Q 두 곳을 RTC!$C$41 로, D30 의 분모를 D55(실제 '
     'f.r 151.748 kHz)로 바꿨다. T_ZC 303 -> 457 ns. 탱크 선정 경로(D26->D27->D43..D45)는 '
     '건드리지 않았다'),

    ('CompensationNet&Check', 'D110',
     '검증 블록이 자체 라인주파수 입력 D110 = 50 Hz 를 갖고 있다. 설계 블록은 최악값 47 Hz '
     '로 설계한다(D7 · D68 · D73 · D83). 즉 47 Hz 로 설계해 놓고 50 Hz 로 검증한다 — '
     'D116 · AV122 · D125 · D126 · D128 · D129 가 전부 낙관적으로 나온다',
     'D110 = 47 (사양 47~63 Hz 의 최악값, Design Spec!D17 과 같다). 3차 고조파 3.86 -> '
     '4.31 % · 버스트 FB 리플 47.3 -> 52.9 mV · R_BM 조정폭 2.37 -> 2.65 kohm'),

    ('CC · Res. Tank Design · Power Components',
     'CC F~H 20:31 · CC 32 · CC J · Res.Tank D65 D67 · Power D28',
     'C.18 — 설계가 라인사이클 실효값이라고 부르는 세 전류가 실은 θ=π/4 한 점이다. '
     "Res.Tank D65 = CC!C29, D67 = CC!C25, Power D28 = CC!C31 로 CC 의 한 칸을 그대로 "
     '읽는다. 출력 뱅크 리플전류가 21.77 A 로 나오지만 라인사이클 실효는 30.19 A — '
     '28 % 과소이고, 이 값이 출력 커패시터 개수를 정한다',
     'RTC 는 이미 θ 를 6점 푼다(π/12 ~ π/2, 15° 간격). CC 가 3점만 읽고 있었을 뿐이다. '
     '열 F·G·H 에 나머지 세 θ 를 RTC!BC150 · BC153 · BC154 에서 받아 추가하고, 행 32 에 '
     '노드 전류의 제곱을, 열 J 에 Simpson 적분(가중치 1,4,2,4,2,4,1 ÷ 18)을 넣었다. '
     'θ=0 표본은 부하가 sinB�θ 이므로 정확히 0 이다. D65 → CC!J29 · D67 → CC!J25 · '
     'Power D28 → CC!J31 로 연결했다. 721점 스윕 대비 2차 −0.04 % · 뱅크 리플 −0.08 % · '
     '1차 −1.83 %. 1차만 잔차가 남는 것은 자화 전류가 θ=0 에서도 사라지지 않기 때문이고, '
     '끝점을 외삽하면 +4.7 % 로 오히려 나빠진다(θ→0 은 버스트 영역이라 도달하지 않는다)'),

    ('Power Components', 'D22 · D33',
     '홀드업이 공칭 출력 25 V(D14)에서 방전을 시작한다고 본다. 실제 출력은 2f_L 리플로 '
     '24.41 ~ 25.59 V 를 오가고 AC 는 아무 위상에서나 끊기므로 최악은 리플 골이다. '
     '에너지가 V^2 이라 12.5 % 낙관적이 된다. 실제 리플은 바로 아래 D31 에 이미 있다',
     '두 수식의 D14^2 을 (D14-D31/2)^2 으로 바꿨다. 요구 용량 59.77 -> 67.22 mF · '
     '달성 홀드업 15.10 -> 13.42 ms. D22 -> D31 -> D26 -> D23/D24(수동 선정) 이므로 '
     '순환 참조가 아니다'),
]


def main():
    bak = X.backup(XL)
    print('백업 %s' % os.path.basename(bak))
    parts = X.open_book(XL)
    xml = parts[PART].decode('utf-8')

    # Excel rewrites inline strings into sharedStrings.xml when it saves, so a
    # row written by an earlier run is no longer visible in the sheet part.
    # Looking only there duplicated three rows once already.
    haystack = xml + parts.get('xl/sharedStrings.xml', b'').decode('utf-8')

    used = [int(r) for r in re.findall(r'<row r="(\d+)"', xml)]
    nxt = max(used) + 1
    for sheet, cells, problem, fix in ROWS:
        if cells in haystack:
            print('  건너뜀 %-22s %s (이미 기록돼 있다)' % (sheet, cells[:40]))
            continue
        r = nxt
        nxt += 1
        xml = X.ensure_row(xml, r)
        for col, text in (('B', sheet), ('C', cells), ('D', problem), ('E', fix)):
            xml = X.set_cell(xml, col + str(r), X.cell_t(col + str(r), STYLE[col], text))
        print('  행 %d  %-22s %s' % (r, sheet, cells))
    parts[PART] = xml.encode('utf-8')
    X.write_book(XL, parts)
    print()
    print("CHANGELOG_rev0_6 갱신 완료")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
