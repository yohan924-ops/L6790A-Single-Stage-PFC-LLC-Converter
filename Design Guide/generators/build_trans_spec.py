# -*- coding: utf-8 -*-
"""벤더에 보낼 트랜스포머 요구사양서를 만든다.  변형을 인자로 받는다.

이것은 우리가 보내는 '사양서' 이지 벤더가 채워 오는 '검사성적서' 가 아니다.
그래서 빈 칸을 하나도 두지 않는다 - 벤더는 자기 양식으로 승인원을 낸다.

값은 변형 시트의 세트 값을 유닛으로 환산한 것이다: 1차가 직렬이라
인덕턴스는 /N.x, 2차가 병렬이라 전류는 /N.x, 권선비는 /N.x.  N.x 는
시트에서 읽는다 - 이 설계는 트랜스포머 한 개라 1 이다.
L.L2(2차 누설)는 지그 부유 인덕턴스 수준이라 주지 않는다 - 개방·단락 두
인덕턴스와 권선비가 있으면 T-모델이 완전히 결정된다.

권선비는 적어야 한다. 저턴수 2차의 자기 인덕턴스에는 전선 고리 성분이 섞여
권선비를 담지 못하고(기존품 26OP-LM83W: 계산 2.12 uH, 사양 2.80 uH, 벤더가
+-50 % 를 걸어 놨다), 벤더의 표준 측정 항목 어디에도 권선비 정보가 없다.

핀 배정은 승인원 방식이다 - NS2 = 3->5, NS3 = 4->6 (엇갈림).  1턴 동판은
보빈 한쪽으로 들어가 반대쪽으로 나오므로 두 끝이 반대편 핀 뱅크에 떨어진다.
인접핀(3-4, 5-6)으로 적었던 판이 있었는데 전기적으로는 같지만 - 어느 쪽이든
4+5 를 이으면 끝이 3·6 인 같은 센터탭 권선이 된다 - 보빈에 자연스럽지 않다.
센터탭(4+5)은 PCB 에서 만든다.

결선도는 넣지 않는다 - 사용자가 직접 그린 것을 쓴다.
이 파일을 실행하면 사양서가 통째로 덮어써진다. 사용자가 손으로 색·배치를
고쳤을 수 있으므로 **요청받았을 때만 실행할 것.**
"""
import math
import os
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# 시트에서 읽는 값(인덕턴스·전류·A.e·주파수)은 여기 적지 않는다.  손으로 적으면
# 시트를 고칠 때마다 조용히 낡는다 - 6:1 사양서가 실제로 그렇게 f.Min 을 90 kHz
# 로 달고 있었다(참값 110 kHz).  아래에는 시트에서 나오지 않는 것만 둔다.
VARIANTS = {
    '7p5to1_x1': dict(label='7.5 : 1'),        # ONE transformer, cores.CHOSEN
    # 2026-10-18 (user: "코어를 특정하지 말고 사양만"): the third three-core option,
    # written as REQUIREMENTS ONLY.  No core, coil former or pin layout is named -
    # the sheet gives what the core must do (A.e for the flux ceiling B_FLAT,
    # the material class, the copper that must fit) and the supplier chooses.
    # Terminals follow the production part 26OP-LM83W, as the frozen 7p5to1 spec.
    # LR_BAND: 3 uH at 5 T is hard to hit.  Trial builds (THREE_CORE_BOARD.md,
    # 2026-10-18, re-checked at 70.5 nF / 10 uH): L.r 8 .. 11 uH passes 71/75
    # like the design point once C.r is re-centred; -15 % leakage at the design C.r fails k.CTd / k.ceil, -10 %
    # passes - so the tolerance stays the uniform +-10 %.  J_CU: the copper of
    # the design's winding example (3.0 / 2.5 mm2, 1.0 W a transformer at MLT
    # 0.1 m) - flat cores have long turns, so not the general 4.5 A/mm2.
    #  AUX_WIRE (2026-10-18, winding table): NAUX is 1 T carrying the VCC load
    #  (I.VCC, about 0.2 A dc) in pulses - its copper loss is negligible at any
    #  rms the pulses can have (18 mW at 1 A rms, MLT 0.1 m, 100 C), so the diameter is a
    #  mechanical choice: the bench part's auxiliary wire (LGE slide, 2026-10-16).
    '7p5to1_x3m3': dict(label='7.5 : 1', nocore=True, B_FLAT=0.075,
                        LR_BAND=(8.0, 11.0), J_CU=3.75, AUX_WIRE=0.40),
}
if len(sys.argv) < 2 or sys.argv[1] not in VARIANTS:
    raise SystemExit('변형을 인자로 주십시오: %s   '
                     '인자 없이 실행해서 정본 사양서를 덮어쓰는 사고가 두 번 났습니다.'
                     % ' / '.join(VARIANTS))
VAR = sys.argv[1]
V = VARIANTS[VAR]
#  --kr: Korean edition of the requirements-only spec (2026-10-18, user).  The
#  one-transformer spec stays English.
LANG = 'kr' if '--kr' in sys.argv[2:] else 'en'
FONT = 'Malgun Gothic' if LANG == 'kr' else 'Calibri'

# ---------------------------------------------------- 시트에서 읽어 온다
import check_trans_spec as CTS
import cores as CORES          # 핀 배정의 유일한 출처 - AN 의 그림·표와 같은 곳

_sm = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', '..', 'Smath', 'variants', 'L6790A_%s.sm' % VAR)
if not os.path.exists(_sm):
    raise SystemExit('변형 시트가 없다.  먼저 만들 것:  '
                     'set L6790_VARIANT=%s && python build_l6790_smath.py' % VAR)
_d = CTS.derive(CTS.sheet(_sm))

V.update(
    Np=_d['Np'], Ns=_d['Ns'], Nx=_d['Nx'], Naux=_d['Naux'],
    Naux_set=_d['Naux_set'], Ivcc=_d['Ivcc'],
    Lopen=_d['Lopen'], Lshort=_d['Lshort'],
    Ae=int(round(_d['Ae'])),
    Ipri='%.1f A   /   %.1f A' % (_d['Ipri_rms'], _d['Ipri_pk']),
    Isec='%.1f A   /   %.1f A' % (_d['Isec_rms'], _d['Isec_pk']),
    # 개방 시험은 2차 기자력 상쇄가 없으므로 같은 전류로도 자속이 훨씬 크다.
    # 동작 자속을 개방 시험에서 재현하는 전류에 여유를 곱한 값이 시험 전류다.
    Isat=int(math.ceil(_d['Isat_spec'])),
    fsw='%d  to  %d kHz' % (round(_d['fmin']), round(_d['fmax'])),
)

# 공차는 개방·단락 모두 +-10 % 로 통일한다.  버틸 수 있는 개방 인덕턴스 저하는
# 1 - 1/k.floor^2 이고 변형마다 다르지만(9:1 14.9 % · 7.5:1 4.1 % · 6:1 58.9 %),
# 비대칭 공차는 양산 공정이 맞추지 못한다 - 2026-09-07 사용자 결정.
# 7.5:1 을 채택한다면 R.T 를 10 kohm 으로 내려 k.floor 를 1.117 로 올려야 한다.
V['tol_open'] = '±10 %'
V['tol_short'] = V.get('tol_short', '±10 %')

# 보빈과 핀 배정: cores.CHOSEN(PQ 50/50, 카탈로그 보빈 B65982E 12핀 + 칸막이 3.0 mm),
# cores.BOBBINS 한 곳에서 읽는다.
NOCORE = bool(V.get('nocore'))
if NOCORE:
    #  26OP-LM83W approval sheet (KH Feelux): NP1 1-2, NS2 3-5, NS3 4-6, NAUX a-b.
    #  The tap 4+5 is made on the PCB.  Pin layout is the supplier's.
    BOB_NAME, BOB = None, None
    _MAP = {'NP1': ((1,), (2,)), 'NS2': ((3,), (5,)), 'NS3': ((4,), (6,)),
            'NAUX': (('a',), ('b',))}
else:
    BOB_NAME = CORES.CHOSEN
    BOB = CORES.BOBBINS[BOB_NAME]
    _MAP = BOB['map']

# --------------------------------------- requirements-only spec: what the core must do
if NOCORE:
    _s = CTS.sheet(_sm)
    _g = lambda k: _s[k][0]
    _Vo, _fr, _Cr = _g('V.o_eff'), _g('f.r'), _g('C.r')          # V, kHz, nF
    _Lr_set, _Lm_set = _g('L.r'), _g('L.m')                     # uH, the set
    _fsu = _g('f.SU')                                           # kHz
    # A.e that keeps B.pk = V.o / (4 f.r N.s A.e) at or below B_FLAT - rounded UP to 10 mm2
    _Ae_flat = _Vo / (4.0 * _fr * 1e3 * V['Ns'] * V['B_FLAT']) * 1e6
    V['Ae_flat'] = int(math.ceil(_Ae_flat / 10.0) * 10)
    # copper: the design's current density (cores.J_CU), rounded UP to 0.1 mm2
    _up = lambda x: math.ceil(x * 10.0 - 1e-9) / 10.0
    V['J'] = V.get('J_CU', CORES.J_CU)
    V['Acu_pri'] = _up(_d['Ipri_rms'] / V['J'])
    V['Acu_sec'] = _up(_d['Isec_rms'] / V['J'])
    # skin depth at f.r, copper at 100 C (rho 1.72e-8 * (1 + 0.00393 * 80))
    _rho = 1.72e-8 * (1.0 + 0.00393 * 80.0)
    _delta = lambda f_khz: math.sqrt(_rho / (math.pi * f_khz * 1e3 * 4e-7 * math.pi)) * 1e3
    V['delta_mm'], V['delta_hi_mm'] = _delta(_fr), _delta(_d['fmax'])
    V['strand_mm'] = 0.10                       # <= 0.6 delta, nearest standard gauge
    #  the winding table names a wire: Litz of strand_mm with the fewest strands
    #  (rounded UP to 10) that holds the copper above; the auxiliary is one wire
    _a1 = math.pi / 4.0 * V['strand_mm'] ** 2
    _count = lambda a: int(math.ceil(a / _a1 / 10.0 - 1e-9) * 10)
    V['n_pri'], V['n_sec'] = _count(V['Acu_pri']), _count(V['Acu_sec'])
    V['Cu_pri'], V['Cu_sec'] = V['n_pri'] * _a1, V['n_sec'] * _a1
    V['Cu_aux'] = math.pi / 4.0 * V['AUX_WIRE'] ** 2
    V['foil_mm'] = CORES.T_FOIL
    V['fr'], V['Cr'], V['fsu'] = _fr, _Cr, _fsu
    V['Lopen_set'], V['Lshort_set'] = _Lr_set + _Lm_set, _Lr_set
    V['Lshort_lo'], V['Lshort_hi'] = (x / V['Nx'] for x in V['LR_BAND'])


def pins(w, dash='\u2013'):
    a, b = _MAP[w]
    return '%s %s %s' % (CORES._plus(a), dash, CORES._plus(b))


def tap_text():
    t = [str(n) for n in sorted(set(_MAP['NS2'][1] + _MAP['NS3'][0]))]
    return ', '.join(t[:-1]) + ' and ' + t[-1]


NWORD = {1: 'one', 2: 'two', 3: 'three', 4: 'four'}

TXT = {
    'en': dict(
        title='TRANSFORMER  SPECIFICATION',
        subtitle='Turns   NP1 : NS2 : NS3 : NAUX   =   %d : %d : %d : %d',
        s1='1.    CONSTRUCTION',
        construction='Flat (low-profile) construction as the production part '
                     '26OP-LM83W.   Core and coil former are the supplier’s choice; '
                     'the windings are as section 2.   The overall height is agreed '
                     'before the first samples.',
        s2='2.    WINDING  SPEC',
        h_no='No', h_wdg='Winding', h_term='Terminal', h_turns='Turns',
        h_sf='S  →  F', h_wire='Wire   (copper)', h_loc='Location',
        w_np1='NP1   Primary', w_ns2='NS2   Secondary A',
        w_ns3='NS3   Secondary B', w_aux='NAUX  Auxiliary',
        turns='%d T', aux_cur='%.0f mA dc',
        litz='Litz  ø%.2f × %d   (%.2f mm²)', solid='Solid  ø%.2f   (%.2f mm²)',
        loc_np1='Primary section', loc_ns2='Secondary section, with NS3 (bifilar)',
        loc_ns3='Secondary section, with NS2 (bifilar)',
        loc_aux='Secondary section, beside NS2 · NS3',
        direction='Winding direction: all windings in the same direction.   S = start, '
                  'F = finish; the starts (%s) are the dots (●) of the schematic diagram.',
        sections='Primary section and secondary section side by side, as 26OP-LM83W; '
                 'the spacing between them sets item 3-2.   NAUX is in the secondary '
                 'section so that its voltage follows the secondaries.',
        tap='Centre tap is made on the PCB by joining pins %s — do NOT join them '
            'inside the transformer.   One conductor per pin; a secondary pin '
            'carries its whole winding current (%.1f A rms): confirm the pin '
            'current rating, or bring the secondary ends straight out.',
        equiv='Another wire is acceptable with at least the same copper and strands '
              '≤ ø%.2f (skin depth %.2f mm at %.0f kHz); NS2 and NS3 may also be '
              'copper foil ≤ %.2f mm thick.',
        terminals='Terminal numbers follow the production part 26OP-LM83W (approval '
                  'sheet, KH Feelux); the pin layout is the supplier’s choice.',
        s3='3.    ELECTRICAL  REQUIREMENTS',
        s3_tail='Measured with an LCR meter at 100 kHz / 1 V.',
        h_item='Item', h_req='Requirement', h_cond='Condition',
        r_ind='INDUCTANCE',
        c_ind='All other windings OPEN.   L.mag + L.leak, not L.mag alone.',
        r_lk='LEAKAGE INDUCTANCE',
        c_lk='EACH HALF: NS2 short alone, then NS3 short alone; the other half and '
             'NAUX open.   Both must pass.   A target, not a maximum.',
        r_sat='D.C OVERLAP', req_sat='≥ 90 % of initial inductance',
        c_sat='Test current %d A, normal temperature',
        req_L='%.2f µH    %s',
        band='Item 2 is a target, not a maximum: if the construction cannot reach '
             'it, state the value it reaches BEFORE samples — %.2f to %.2f µH is '
             'acceptable, the %s then applying around the stated value.',
        allshort='With NS2 and NS3 both shorted the reading is lower: record it, do '
                 'not hold it to item 2.   The auxiliary is NOT shorted.',
        s4='4.    OPERATING  CONDITIONS',
        f_item='Winding frequency', f_val='%d  to  %d kHz',
        f_tail='of the winding current and voltage at full load; up to %.0f kHz '
               'briefly at start-up',
        i_item='Winding current   %s', i_val='%.1f A rms   /   %.1f A peak',
        i_tail_pri='at full load — the wire of section 2 carries it at ≤ %.2f A/mm²',
        i_tail_sec='each, at full load', i_tail_aux='dc load',
        ae_item='Core effective area', ae_val='Ae  ≥  %d mm²',
        ae_tail='keeps B.pk ≤ %.0f mT with %d T at %.0f kHz.   Ae of the whole flux '
                'path: yoke-limited in a flat core; two core sets (pairs) placed side '
                'by side in one former add.',
    ),
    'kr': dict(
        title='트랜스포머  요구사양서',
        subtitle='권선비   NP1 : NS2 : NS3 : NAUX   =   %d : %d : %d : %d',
        s1='1.    구조',
        construction='양산품 26OP-LM83W 와 같은 납작한(저배) 구조.   코어 · 보빈은 '
                     '제작사가 정하고 권선은 2절대로 한다.   전체 높이는 첫 샘플 전에 '
                     '협의한다.',
        s2='2.    권선 사양',
        h_no='번호', h_wdg='권선', h_term='단자', h_turns='턴수',
        h_sf='S  →  F', h_wire='선재   (구리 단면)', h_loc='위치',
        w_np1='NP1   1차', w_ns2='NS2   2차 A', w_ns3='NS3   2차 B',
        w_aux='NAUX  보조',
        turns='%d T', aux_cur='%.0f mA dc',
        litz='리츠선  ø%.2f × %d   (%.2f mm²)', solid='단선  ø%.2f   (%.2f mm²)',
        loc_np1='1차 구역', loc_ns2='2차 구역, NS3 와 함께(바이파일러)',
        loc_ns3='2차 구역, NS2 와 함께(바이파일러)', loc_aux='2차 구역, NS2 · NS3 옆',
        direction='감는 방향: 모든 권선을 같은 방향으로 감는다.   S = 감기 시작, F = 끝; '
                  '감기 시작(%s)이 결선도의 점(●)이다.',
        sections='1차 구역과 2차 구역을 26OP-LM83W 처럼 나란히 둔다; 두 구역 사이 간격이 '
                 '3절 항목 2(누설)를 정한다.   NAUX 는 전압이 2차를 따라가도록 2차 구역에 둔다.',
        tap='센터탭은 PCB 에서 핀 %s 를 이어 만든다 — 트랜스포머 안에서 잇지 말 것.   '
            '핀마다 도체 하나; 2차 핀 하나가 권선 전류 전체(%.1f A rms)를 흘리므로 핀 '
            '전류 정격을 확인하거나 2차 끝을 바로 뽑아낼 것.',
        equiv='구리 단면이 같거나 크고 소선이 ø%.2f 이하이면 다른 선재도 된다(표피 깊이 '
              '%.2f mm, %.0f kHz).   NS2 · NS3 는 두께 %.2f mm 이하 동박도 된다.',
        terminals='단자 번호는 양산품 26OP-LM83W(KH필룩스 승인원) 방식.   핀 배치는 '
                  '제작사가 정한다.',
        s3='3.    전기 요구사양',
        s3_tail='측정: LCR 미터, 100 kHz / 1 V.',
        h_item='항목', h_req='요구값', h_cond='조건',
        r_ind='인덕턴스',
        c_ind='다른 권선 전부 개방.   자화 + 누설 인덕턴스(자화만이 아님).',
        r_lk='누설 인덕턴스',
        c_lk='반쪽씩: NS2 만 단락, 이어서 NS3 만 단락; 나머지 반쪽과 NAUX 는 개방.   '
             '둘 다 만족할 것.   목표값이며 최대값이 아님.',
        r_sat='DC 중첩(포화)', req_sat='초기 인덕턴스의 90 % 이상',
        c_sat='시험 전류 %d A, 상온',
        req_L='%.2f µH    %s',
        band='항목 2 는 목표값이며 최대값이 아니다: 구조상 못 맞추면 샘플 전에 도달값을 '
             '알릴 것 — %.2f–%.2f µH 까지 받아들이며, 그때는 알린 값에 %s 를 적용한다.',
        allshort='NS2 · NS3 를 함께 단락하면 더 낮게 읽힌다: 기록만 하고 항목 2 의 판정에는 '
                 '쓰지 말 것.   보조 권선은 단락하지 않는다.',
        s4='4.    동작 조건',
        f_item='권선 주파수', f_val='%d – %d kHz',
        f_tail='정격 부하에서 권선 전류 · 전압의 주파수; 기동 시 잠깐 %.0f kHz 까지',
        i_item='권선 전류   %s', i_val='%.1f A rms   /   %.1f A 피크',
        i_tail_pri='정격 부하 — 2절의 선재로 %.2f A/mm² 이하',
        i_tail_sec='각각, 정격 부하', i_tail_aux='직류 부하',
        ae_item='코어 유효 단면적', ae_val='Ae  ≥  %d mm²',
        ae_tail='B.pk ≤ %.0f mT(%d T · %.0f kHz)가 되는 값.   자속 경로 전체의 유효 단면: '
                '납작한 코어는 요크가 정하고, 한 보빈에 코어 세트(반쪽 두 개 한 쌍) 둘을 '
                '나란히 넣으면 합산.',
    ),
}
T = TXT[LANG]
NAVY, BAND, LINE, MUTED = '1F3864', 'EDF0F7', 'B4B4B4', '5A6472'
thin = Side(style='thin', color=LINE)
box = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()
ws = wb.active
ws.title = 'Transformer Spec'
ws.sheet_view.showGridLines = False

#  The requirements-only spec has six columns - its winding table follows the
#  approval sheet (terminal S -> F, turns, wire, location) - the one-transformer
#  spec keeps its five.  Both add up to the same printed width.
if NOCORE:
    WIDTHS = {'A': 2.2, 'B': 4.5, 'C': 16, 'D': 11, 'E': 8, 'F': 33, 'G': 36,
              'H': 2.2}
else:
    WIDTHS = {'A': 2.2, 'B': 4.5, 'C': 22, 'D': 16, 'E': 24, 'F': 42, 'G': 2.2}
for k, v in WIDTHS.items():
    ws.column_dimensions[k].width = v

LAST = 'G' if NOCORE else 'F'
COLS = 'BCDEFG' if NOCORE else 'BCDEF'


def put(ref, val, bold=False, size=10, color='000000', fill=None,
        align='left', wrap=False, border=False, italic=False):
    c = ws[ref]
    if val is not None:                 # None 이면 셀에 아무것도 쓰지 않는다
        c.value = val                   # (빈 문자열은 숫자 서식 칸에서 0.00 이 된다)
    c.font = Font(name=FONT, size=size, bold=bold, italic=italic, color=color)
    c.alignment = Alignment(horizontal=align, vertical='center', wrap_text=wrap)
    if fill:
        c.fill = PatternFill('solid', fgColor=fill)
    if border:
        c.border = box
    return c


def span(row):
    ws.merge_cells('B%d:%s%d' % (row, LAST, row))


def section(row, text, tail=None):
    span(row)
    put('B%d' % row, text, bold=True, size=11, color='FFFFFF', fill=NAVY)
    for c in COLS[1:]:
        ws['%s%d' % (c, row)].fill = PatternFill('solid', fgColor=NAVY)
    ws.row_dimensions[row].height = 19
    if tail:
        span(row + 1)
        put('B%d' % (row + 1), tail, size=9, italic=True, color=MUTED)
        ws.row_dimensions[row + 1].height = 14


def head(row, cells):
    for col, t in cells:
        put('%s%d' % (col, row), t, bold=True, size=9, fill=BAND,
            align='center', border=True)
    ws.row_dimensions[row].height = 20


#  Characters a cell holds on one line (Calibri 10 pt in column widths above;
#  9 pt italic in a note merged B..F).  Estimates on the safe side: a row too
#  tall shows white space, a row too short clips the text in print.
CHARS = {'C': 28, 'D': 17, 'E': 26, 'F': 44, 'note': 115, 'cond_tail': 48}
CHARS['val'] = CHARS['E']
if NOCORE:
    CHARS = {'C': 17, 'D': 11, 'E': 8, 'F': 34, 'G': 37, 'note': 115,
             'cond_tail': 42, 'val': 43}


def nlines(text, chars):
    #  Korean edition (Malgun Gothic): a Hangul syllable takes about two Calibri
    #  characters, Latin letters and digits about 1.25, a space half of one
    if LANG == 'kr':
        n = sum(2.0 if ord(ch) >= 0x1100 else 0.5 if ch == ' ' else 1.25
                for ch in text)
        return max(1, int(-(-n // chars)))
    return max(1, -(-len(text) // chars))


def line(row, cells, h=18):
    lines = 1
    for col, t, al in cells:
        put('%s%d' % (col, row), t, size=10, align=al, border=True,
            wrap=(al == 'left'))
        if al == 'left' and col in CHARS:
            lines = max(lines, nlines(t, CHARS[col]))
    ws.row_dimensions[row].height = max(h, 13 * lines + 5)


def note(row, text, lines=None):
    span(row)
    lines = lines or nlines(text, CHARS['note'])
    put('B%d' % row, text, size=9, italic=True, color=MUTED, wrap=(lines > 1))
    ws.row_dimensions[row].height = 14 if lines == 1 else 12 * lines + 2


# ------------------------------------------------------------------ 표제
span(2)
put('B2', T['title'] if NOCORE else 'TRANSFORMER  SPECIFICATION',
    bold=True, size=18, color=NAVY)
ws.row_dimensions[2].height = 26
span(3)
put('B3', (T['subtitle'] % (V['Np'], V['Ns'], V['Ns'], V['Naux'])) if NOCORE else
          ('L6790A single-stage PF LLC converter      25 V / 26.3 A output'
           '      —      turns ratio %s' % V['label']), size=11, color=MUTED)
ws.row_dimensions[3].height = 17
for c in COLS:
    ws['%s4' % c].border = Border(bottom=Side(style='medium', color=NAVY))
ws.row_dimensions[4].height = 4


def cond(row, item, val, tail, lines=None):
    """One operating-condition line; lines > 1 wraps the value and the tail."""
    lines = lines or max(nlines(val, CHARS['val']), nlines(tail or '', CHARS['cond_tail']))
    put('B%d' % row, '•', size=10, align='center', color=MUTED)
    ws.merge_cells('C%d:D%d' % (row, row))
    put('C%d' % row, item, size=10)
    if NOCORE:
        ws.merge_cells('E%d:F%d' % (row, row))
    put('E%d' % row, val, size=10, bold=True, wrap=(lines > 1))
    if tail:
        put('%s%d' % (LAST, row), tail, size=9, italic=True, color=MUTED,
            wrap=(lines > 1))
    ws.row_dimensions[row].height = 16 if lines == 1 else 13 * lines


#  Row numbers are not fixed: the requirements-only spec has more lines.  The
#  cursor reproduces the one-transformer layout exactly (rows 6 .. 45, print area
#  to 47) - check_trans_spec reads the file by its labels, not by row.
r = 6

# ------------------------------------------------------------- 1. 구성
section(r, T['s1'] if NOCORE else '1.    CONFIGURATION')
r += 1
if NOCORE:
    BULLETS = [(T['construction'], False)]
else:
    BULLETS = [
        ('One transformer per set on %s %s (core %s, %s coil former, %d pins).'
         % (CORES.CORES[BOB_NAME].get('vendor', 'TDK'), BOB_NAME,
            CORES.CORES[BOB_NAME]['core'], BOB['former'], BOB['pins']), False),
        ('EVERY VALUE BELOW IS PER TRANSFORMER.', True),
    ]
for t, red in BULLETS:
    span(r)
    _nl = nlines(t, CHARS['note'])
    put('B%d' % r, '•   ' + t, size=10, bold=red,
        color=('C00000' if red else '000000'), wrap=(_nl > 1))
    ws.row_dimensions[r].height = 15 if _nl == 1 else 13 * _nl + 4
    r += 1
r += 1

# ---------------------------------------------------------- 2. 권선
section(r, T['s2'] if NOCORE else '2.    WINDING')
r += 1
if NOCORE:
    #  The approval sheet's WINDING SPEC: terminal S -> F, turns, wire, location.
    #  The currents behind the wire are in section 4.
    head(r, [('B', T['h_no']), ('C', T['h_wdg']), ('D', T['h_sf']),
             ('E', T['h_turns']), ('F', T['h_wire']), ('G', T['h_loc'])])
    r += 1
    _litz = lambda n, cu: T['litz'] % (V['strand_mm'], n, cu)
    for n, des, w, turns, wire, loc in [
            ('1', T['w_np1'], 'NP1', V['Np'], _litz(V['n_pri'], V['Cu_pri']),
             T['loc_np1']),
            ('2', T['w_ns2'], 'NS2', V['Ns'], _litz(V['n_sec'], V['Cu_sec']),
             T['loc_ns2']),
            ('3', T['w_ns3'], 'NS3', V['Ns'], _litz(V['n_sec'], V['Cu_sec']),
             T['loc_ns3']),
            ('4', T['w_aux'], 'NAUX', V['Naux'],
             T['solid'] % (V['AUX_WIRE'], V['Cu_aux']), T['loc_aux'])]:
        line(r, [('B', n, 'center'), ('C', des, 'left'),
                 ('D', pins(w, '\u2192'), 'center'), ('E', T['turns'] % turns, 'center'),
                 ('F', wire, 'left'), ('G', loc, 'left')])
        ws['E%d' % r].font = Font(name=FONT, size=10, bold=True)
        r += 1
    WIND = []
else:
  head(r, [('B', 'No'), ('C', 'Winding'), ('D', 'Terminal'), ('E', 'Turns'),
           ('F', 'Winding current           rms   /   peak')])
  r += 1
  WIND = [
    ('1', 'NP1     Primary', pins('NP1'), '%d T' % V['Np'], V['Ipri']),
    ('2', 'NS2     Secondary A', pins('NS2'), '%d T' % V['Ns'], V['Isec']),
    ('3', 'NS3     Secondary B', pins('NS3'), '%d T' % V['Ns'], V['Isec']),
    ('4', 'NAUX   Auxiliary (VCC, ZCD)', pins('NAUX'), '%d T' % V['Naux'],
     '%.0f mA dc load (VCC)' % V['Ivcc']),
  ]
for n, des, term, turns, cur in WIND:
    line(r, [('B', n, 'center'), ('C', des, 'left'), ('D', term, 'center'),
             ('E', turns, 'center'), ('F', cur, 'center')])
    ws['E%d' % r].font = Font(name=FONT, size=10, bold=True)
    r += 1
r += 1

_shared = set(_MAP['NS2'][1]) == set(_MAP['NS3'][0])
if NOCORE:
    note(r, T['direction'] % ', '.join(
        str(_MAP[w][0][0]) for w in ('NP1', 'NS2', 'NS3', 'NAUX')))
    r += 1
    note(r, T['sections'])
    r += 1
    _tap = tap_text() if LANG == 'en' else ' · '.join(
        str(n) for n in sorted(set(_MAP['NS2'][1] + _MAP['NS3'][0])))
    note(r, T['tap'] % (_tap, _d['Isec_rms']))
elif _shared:
    note(r, 'Centre tap: NS2 finish and NS3 start share pins %s, one Litz '
            'bundle of each on a pin.   At most two bundles on a pin: confirm '
            'the pin current rating.   NP1: the %d bundles of a turn are '
            'turned over as a group at each layer.'
            % (tap_text(), CORES.PRI_PAR))
else:
    note(r, 'Centre tap is made on the PCB by joining pins %s — do NOT join '
            'them inside the transformer.%s'
            % (tap_text(), '   One conductor per pin; a secondary pin '
               'carries its whole winding current%s: confirm the pin current '
               'rating, or bring the secondary ends straight out.'
               % (' (%.1f A rms)' % _d['Isec_rms'] if NOCORE else '')))
r += 1
if NOCORE:
    note(r, T['equiv'] % (V['strand_mm'], V['delta_hi_mm'], _d['fmax'], V['foil_mm']))
    r += 1
    note(r, T['terminals'])
    r += 2
else:
    note(r, ('Custom coil former for %s, %d pins, made to this '
             'specification.   ' % (BOB_NAME, BOB['pins'])
             if CORES.MECH.get(BOB_NAME, {}).get('custom') else
             'Coil former TDK %s (%s), %d pins%s.   '
             % (BOB['former'], BOB_NAME, BOB['pins'],
                ', with a %.1f mm partition added between the two sections'
                % CORES.PARTITION
                if CORES.MECH.get(BOB_NAME, {}).get('partition') else '')) +
            (CORES.PIN_NOTE if BOB_NAME == CORES.CHOSEN else
             'Pin numbers count along one row from pin 1 and back along the '
             'other — confirm on the bobbin drawing before winding.'))
    r += 1

# ------------------------------------------------- 3. 전기 요구사양
section(r, T['s3'] if NOCORE else '3.    ELECTRICAL  REQUIREMENTS',
        T['s3_tail'] if NOCORE else 'Measured with an LCR meter at 100 kHz / 1 V.')
r += 2
if NOCORE:
    head(r, [('B', T['h_no']), ('C', T['h_item']), ('D', T['h_term']),
             ('E', T['h_req']), ('F', None), ('G', T['h_cond'])])
    ws.merge_cells('E%d:F%d' % (r, r))
else:
    head(r, [('B', 'No'), ('C', 'Item'), ('D', 'Terminal'), ('E', 'Requirement'),
             ('F', 'Condition')])
r += 1
REQ = [
    ('1', T['r_ind'], pins('NP1'), T['req_L'] % (V['Lopen'], V['tol_open']),
     T['c_ind'], 18),
    ('2', T['r_lk'], pins('NP1'), T['req_L'] % (V['Lshort'], V['tol_short']),
     T['c_lk'], 30),
    ('3', T['r_sat'], pins('NP1'), T['req_sat'], T['c_sat'] % V['Isat'], 18),
] if NOCORE else [
    ('1', 'INDUCTANCE', pins('NP1'), '%.2f µH    %s' % (V['Lopen'], V['tol_open']),
     'All other windings OPEN.   L.mag + L.leak, not L.mag alone.', 18),
    ('2', 'LEAKAGE INDUCTANCE', pins('NP1'), '%.2f µH    %s' % (V['Lshort'], V['tol_short']),
     ('EACH HALF: NS2 short alone, then NS3 short alone; the other half and '
      'NAUX open.   Both must pass.   Resonant inductor — a target, not a '
      'maximum.'), 30),
    ('3', 'D.C OVERLAP', pins('NP1'), '≥ 90 % of initial inductance',
     'Test current %d A, normal temperature' % V['Isat'], 18),
]
for n, item, term, req, cnd, h in REQ:
    if NOCORE:                      # requirement E:F, condition G
        line(r, [('B', n, 'center'), ('C', item, 'left'), ('D', term, 'center'),
                 ('E', req, 'center'), ('F', None, 'center'), ('G', cnd, 'left')],
             h=h)
        ws.merge_cells('E%d:F%d' % (r, r))
    else:
        line(r, [('B', n, 'center'), ('C', item, 'left'), ('D', term, 'center'),
                 ('E', req, 'center'), ('F', cnd, 'left')], h=h)
    ws['E%d' % r].font = Font(name=FONT, size=10, bold=True)
    ws['C%d' % r].alignment = Alignment(horizontal='left', vertical='center',
                                        wrap_text=True)
    r += 1

if NOCORE:
    note(r, T['band'] % (V['Lshort_lo'], V['Lshort_hi'], V['tol_short']))
    r += 1
    note(r, T['allshort'])
    r += 2
else:
    note(r, 'Both measured at %s of ONE transformer.   ' % pins('NP1') +
            ('Item 2 is set by the winding and the partition between the two '
             'sections: measure it, and each half alone, on the first samples; '
             'a thinner partition lowers it.'))
    r += 1
    note(r, ('Item 2, each half: in service only one half conducts at a time, '
             'and the two halves lie in different layers.   With NS2 and NS3 '
             'both shorted the reading is lower (about %.1f µH estimated): '
             'record it, do not hold it to item 2.   The auxiliary is NOT shorted.'
             % __import__('leakage_fem').estimate(__import__('an_pdf').V)))
    r += 2

# ------------------------------------------------------- 4. 동작 조건
section(r, T['s4'] if NOCORE else '4.    OPERATING  CONDITIONS')
r += 1
if NOCORE:
    COND = [
        (T['f_item'], T['f_val'] % (round(_d['fmin']), round(_d['fmax'])),
         T['f_tail'] % V['fsu']),
        (T['i_item'] % 'NP1', T['i_val'] % (_d['Ipri_rms'], _d['Ipri_pk']),
         T['i_tail_pri'] % (_d['Ipri_rms'] / V['Cu_pri'])),
        (T['i_item'] % 'NS2, NS3', T['i_val'] % (_d['Isec_rms'], _d['Isec_pk']),
         T['i_tail_sec']),
        (T['i_item'] % 'NAUX', T['aux_cur'] % V['Ivcc'], T['i_tail_aux']),
        (T['ae_item'], T['ae_val'] % V['Ae_flat'],
         T['ae_tail'] % (V['B_FLAT'] * 1e3, V['Ns'], V['fr'])),
    ]
else:
    COND = [
        ('Switching frequency', V['fsw'], 'at full load'),
        ('Core effective area', 'Ae  ≥  %d mm²' % V['Ae'],
         'holds the peak flux density at or below 0.20 T'),
    ]
for item, val, tail in COND:
    cond(r, item, val, tail)
    r += 1
if NOCORE:
    r += 1
else:
    r += 1
    note(r, 'The core, coil former and winding arrangement of the reference design '
            'set item 3-2. Another construction is acceptable only when sections 3 '
            'and 5 are met and the first samples are approved.')
    r += 2

# --------------------------------------------------- 5. 안전 절연 (insulation.py)
#  Not in the requirements-only spec (2026-10-18, user): the customer's safety
#  engineering writes the insulation system; the transformer maker gets the
#  electrical and winding requirements only.
import insulation as INS                                        # noqa: E402
_R = INS.req()
if NOCORE:
    LAST_ROW = r - 2
else:
  section(r, '5.    SAFETY  INSULATION',
          ('IEC 62368-1 (household AV), GB 4943.1-2022 for China; 5000 m.'
           if NOCORE else
           'Household AV (TV) for the US, EU, Japan, Korea and China: IEC 62368-1 '
           'as adopted there, GB 4943.1-2022 in China (5000 m).'))
  r += 2
  head(r, [('B', 'No'), ('C', 'Item'), ('D', 'Between'), ('E', 'Requirement'),
           ('F', 'Condition')])
  r += 1
  PRI, SEC = 'primary', 'secondary'
  if NOCORE:
      _np1 = ('Triple-insulated Litz approved as reinforced insulation to IEC '
              '62368-1, one wire from pin to pin.')
      _naux = ('Triple-insulated wire approved as reinforced insulation to IEC '
               '62368-1; leads stay insulated up to the primary pins. Its approved '
               'frequency must cover the start-up frequency, %.0f kHz.' % V['fsu'])
  else:
      _np1 = ('Triple-insulated Litz approved as reinforced insulation to IEC '
              '62368-1, one wire from pin to pin. The partition between the '
              'sections carries NO insulation; it sets item 3-2.')
      _naux = ('Triple-insulated wire approved as reinforced insulation to IEC 62368-1, '
               'wound OVER the secondary; leads stay insulated up to the primary-row '
               'pins. Its approved frequency must cover the start-up frequency.')
  SAFE = [
      ('1', 'Insulation grade', '%s  |  %s' % (PRI, SEC), 'REINFORCED',
       'Primary = NP1, NAUX; secondary = NS2, NS3 and the CORE.   PD 2, OVC II, '
       'material group IIIb.', 18),
      ('2', 'Creepage', '%s  |  %s' % (PRI, SEC), '≥ %.1f mm' % _R['creep'],
       'where the triple insulation ends (pins, stripped ends) to the secondary '
       'and the core', 18),
      ('3', 'Clearance', '%s  |  %s' % (PRI, SEC), '≥ %.1f mm' % _R['clearance'],
       'at 5000 m (%.1f mm × %.2f)' % (_R['cl_2000'], INS.K_ALT), 18),
      ('4', 'NP1, NAUX wire', '%s  |  %s' % (PRI, SEC), 'TIW, reinforced',
       'triple-insulated (NP1: TIW-Litz), approved to IEC 62368-1 up to '
       '%.0f kHz; one wire pin to pin' % V['fsu'], 18),
      ('5', 'Solid insulation', '%s  |  %s' % (PRI, SEC),
       'DTI ≥ %.1f mm  or  ≥ %d tape layers' % (_R['dti'], _R['layers']),
       'where tape or sleeving carries it', 18),
      ('6', 'Electric strength', '%s  |  %s' % (PRI, SEC),
       '%d V ac 60 s  (%d V dc)' % (_R['hipot_ac'], _R['hipot_dc']),
       'NP1 + NAUX against NS2 + NS3 + core; type test, no breakdown', 18),
  ] if NOCORE else [
      ('1', 'Insulation grade', '%s  |  %s' % (PRI, SEC), 'REINFORCED',
       'Primary = NP1, NAUX; secondary = NS2, NS3 and the CORE. Pollution '
       'degree 2, overvoltage category II, material group IIIb, 5000 m.', 30),
      ('2', 'Creepage', '%s  |  %s' % (PRI, SEC), '≥ %.1f mm' % _R['creep'],
       'Wherever the triple insulation ends: primary pins and stripped wire '
       'ends to the core and to secondary leads and pins (%d V rms row, '
       'reinforced = 2 × basic).' % _R['row'], 30),
      ('3', 'Clearance', '%s  |  %s' % (PRI, SEC), '≥ %.1f mm' % _R['clearance'],
       '%.1f mm at 2000 m × %.2f for 5000 m, rounded up.'
       % (_R['cl_2000'], INS.K_ALT), 22),
      ('4', 'NP1 wire', 'NP1  |  %s' % SEC, 'TIW-Litz, reinforced', _np1, 30),
      ('5', 'NAUX wire', 'NAUX  |  %s' % SEC, 'TIW, reinforced', _naux, 30),
      ('6', 'Solid insulation', '%s  |  %s' % (PRI, SEC),
       'DTI ≥ %.1f mm  or  ≥ %d tape layers' % (_R['dti'], _R['layers']),
       'Where tape or sleeving carries it: each tape layer passes the '
       'reinforced test. Sleeve primary leads that leave the triple '
       'insulation near the core.', 30),
      ('7', 'Electric strength', '%s  |  %s' % (PRI, SEC),
       '%d V ac 60 s  (%d V dc)' % (_R['hipot_ac'], _R['hipot_dc']),
       'NP1 + NAUX joined against NS2 + NS3 + core joined. Type test, no '
       'breakdown. Routine test voltage and time as agreed with the certifier.',
       30),
  ]
  for n, item, betw, req, cnd, h in SAFE:
      line(r, [('B', n, 'center'), ('C', item, 'left'), ('D', betw, 'center'),
               ('E', req, 'center'), ('F', cnd, 'left')], h=h)
      ws['E%d' % r].font = Font(name=FONT, size=10, bold=True)
      ws['D%d' % r].alignment = Alignment(horizontal='center',
                                          vertical='center', wrap_text=True)
      ws.row_dimensions[r].height = max(ws.row_dimensions[r].height,
                                        13 * nlines(betw, CHARS['D']) + 5)
      r += 1
  r += 1
  note(r, ('Working voltage: design estimate %.0f V rms / %.0f V peak at %g Vac; '
           'the certifying body measures it.' if NOCORE else
           'The working voltage behind item 2 is an estimate from the design '
           '(%.0f V rms, %.0f V peak at %g Vac); the certifying body measures it.')
          % (_R['u_rms'], _R['u_pk'], INS.V_MAINS_DESIGN))
  LAST_ROW = r

# ------------------------------------------------------------- 인쇄
ws.page_setup.orientation = 'portrait'
ws.page_setup.paperSize = ws.PAPERSIZE_A4
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 1
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.print_area = 'A1:%s%d' % ('H' if NOCORE else 'G', LAST_ROW + 2)
ws.page_margins.left = ws.page_margins.right = 0.3
ws.page_margins.top = ws.page_margins.bottom = 0.4

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', '..', 'Calculation Excel Sheet',
                   'variants', 'Transformer_Spec_%s%s.xlsx'
                   % (VAR, '_KR' if LANG == 'kr' else ''))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
try:
    wb.save(OUT)
except PermissionError:
    raise SystemExit('사양서가 Excel 에서 열려 있어 쓸 수 없다.  닫고 다시 실행할 것:  '
                     + os.path.normpath(OUT))
print('생성:', os.path.normpath(OUT))
