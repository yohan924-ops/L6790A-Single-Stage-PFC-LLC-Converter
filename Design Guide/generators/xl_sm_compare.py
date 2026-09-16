# -*- coding: utf-8 -*-
"""Excel workbook vs SMath worksheet: same inputs, same numbers?

bom_compare.py only checks the 29 parts that end up on a bill of materials. This
walks the whole design - spec, power budget, tank, currents, output bank, IC
network, control loop, compensation - and puts the workbook's cached result next
to the worksheet's computed one.

Three verdicts:

    same        agrees within tolerance
    INTENDED    differs on purpose; the reason is printed. These are places
                where the ST tool is knowingly wrong or looks at a different
                operating point, and the worksheet is the conservative one.
                See HISTORY.md 3.6.
    ** DIFF     nobody meant this. Fix it.

The workbook side is read from the sheet's own cached values, so Excel must have
recalculated at least once since the last edit (the file carries
fullCalcOnLoad="1", so opening it is enough).

    python xl_sm_compare.py            summary plus every difference
    python xl_sm_compare.py -v         every row
"""
import io
import os
import re
import sys

import openpyxl


def require_readable(path):
    """Excel takes an exclusive lock while the workbook is open. Say so
    plainly rather than dying inside openpyxl with a bare PermissionError."""
    try:
        open(path, 'rb').close()
    except PermissionError:
        print('워크북이 Excel 에서 열려 있어 읽을 수 없다. 닫고 다시 실행할 것:')
        print('  ' + path)
        raise SystemExit(2)


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')
SM = os.path.join(ROOT, 'Smath', 'L6790A_SingleStage_PF_LLC_Design_Guide.sm')
if os.environ.get('SM_OVERRIDE'):          # a variant instead of the canonical sheet
    SM = os.environ['SM_OVERRIDE']
if os.environ.get('XL_OVERRIDE'):
    XL = os.environ['XL_OVERRIDE']

U = {'': 1.0, 'V': 1, 'A': 1, 'W': 1, 'ohm': 1, 'kohm': 1e3, 'mohm': 1e-3,
     'F': 1, 'mF': 1e-3, 'uF': 1e-6, 'μF': 1e-6, 'nF': 1e-9, 'pF': 1e-12,
     'H': 1, 'mH': 1e-3, 'uH': 1e-6, 'μH': 1e-6, 'nH': 1e-9,
     'Hz': 1, 'kHz': 1e3, 's': 1, 'ms': 1e-3, 'us': 1e-6, 'μs': 1e-6, 'ns': 1e-9,
     'mV': 1e-3, 'mA': 1e-3, 'uA': 1e-6, 'μA': 1e-6, 'T': 1, 'mT': 1e-3,
     'deg': 1, '%': 1}

# (excel sheet, cell, scale-to-SI, smath var, label, reason-if-intended)
# scale converts the workbook's number into SI so it can meet the worksheet's.
M = [
    # ---------------------------------------------------------- 1. 사양
    ('Design Spec', 'D13', 1, 'V.eq_min', None, ''),          # placeholder, fixed below
]
M = []


def row(sheet, cell, scale, var, label, why=''):
    M.append((sheet, cell, scale, var, label, why))


# ---------------------------------------------------------------- root causes
# Reading the two formulas side by side (2026-08-23) showed the differences are
# not independent: inside each group the equations are character-for-character
# the same and one input differs, and the later rows are simply downstream of
# the first. Counting rows overstates how many problems there are - count these.
CAUSES = {
    'A': ('ZVS 를 선정 후 재검산하지 않는다  [2026-08-23 수정 완료]',
          'D28 은 근사식 [36](f.n 0.82111), D29 는 선정 Q(0.8466). 실제 동작점은 '
          'f.n 0.84006 · Q 0.7717 이고 툴 자신의 RTC!BB149 · RTC!C41 에 있다. '
          '고치려면 그 둘을 가리키게 하면 된다'),
    'B': ('C.18 — CC 시트가 θ 를 3점만 봤다  [2026-08-23 수정 완료, 1차 전류만 −1.8 % 잔차]',
          '설계가 D65 = CC!C29 · D67 = CC!C25 · Power D28 = CC!C31 로 θ=π/4 한 칸을 '
          '읽고 그것을 라인사이클 실효값이라 불렀다. RTC 가 이미 θ 6점을 풀어 두었으므로 '
          'CC 에 열 F·G·H(5π/12 · π/6 · π/12)와 행 32(노드 전류 제곱), 열 J(Simpson 적분, '
          '가중치 1,4,2,4,2,4,1 ÷ 18)를 넣고 설계를 CC!J.. 로 연결했다. 뱅크 리플전류 '
          '21.77 → 30.17 A(SMath 30.19). 1차 전류만 잔차가 남는다 — 자화 전류가 θ=0 에서 '
          '0 이 아니기 때문이고, 끝점을 외삽하면 +4.7 % 로 더 나빠진다'),
    'C': '검증 블록의 입력 D110 = 50 Hz  [2026-08-23 47 Hz 로 수정 완료]',
    'D': '홀드업 시작 전압이 공칭 D14 = 25 V  [2026-08-23 리플 골로 수정 완료]',
    'E': ('RTC!C9 가 264 V(AC 최대)를 가리킨다. 탱크가 보는 최대 등가입력은 '
          'Design Spec!D81 = 332.34 V 이고 그 셀은 아무도 읽지 않는다',
          '**링크만 바꾸면 워크북이 깨진다.** 332.34 V 에서 M_req = 0.6383 이고 이것은 '
          '탱크의 무부하 게인 하한 1/(1+λ) = 0.6452 보다 낮다. 그러면 RTC 행 26 의 '
          'fn.max = √(λ/(1+λ−1/M)) 이 음수의 제곱근이 되어 #NUM! 이 되고, 격자 상한 '
          'CG25 = 1.5·CG26 이 따라 죽어 f_n 격자 전체와 차트 23장이 무너진다. '
          '물리적으로 옳은 결과다 — FB 코너 경부하에서는 어떤 주파수로도 게인을 그만큼 '
          '낮출 수 없고 버스트로 가야 한다. 고치려면 격자 범위 설계를 다시 해야 한다 '
          '(2026-08-23 확인, 적용하지 않음)'),
    'F': '정의가 서로 다르고 양쪽 다 맞다 — 2026-08-23 전부 같은 양끼리 대조하도록 고쳤다',
}
ROOT = {
    ('Res. Tank Design', 'D30'): 'A', ('Res. Tank Design', 'D35'): 'A',
    ('Res. Tank Design', 'D36'): 'A', ('Res. Tank Design', 'D37'): 'A',
    ('Res. Tank Design', 'D65'): 'B', ('Res. Tank Design', 'D67'): 'B',
    ('Power Components', 'D28'): 'B', ('Power Components', 'D40'): 'B',
    ('CompensationNet&Check', 'D125'): 'C',
    ('CompensationNet&Check', 'D126'): 'C',
    ('CompensationNet&Check', 'D128'): 'C',
    ('CompensationNet&Check', 'D129'): 'C',
    ('Power Components', 'D22'): 'D', ('Power Components', 'D33'): 'D',
    ('Device Setting', 'D19'): 'E',
    ('Device Setting', 'D42'): 'F',
    ('Device Setting', 'D108'): 'F',
}


# 1. specification and equivalent input
row('Design Spec', 'D20', 1, 'V.eq_min', 'HB 코너 등가입력')
row('Design Spec', 'D81', 1, 'V.eq_FBthr', 'FB 코너 등가입력')
# Design Spec D86 (Vin.nom) 은 SMath 에서 노란 입력 셀이라 <result> 가 없다 (규칙 6.1-11)
row('Design Spec', 'D89', 1, 'V.eq_ACres', '공진 운전 등가입력')
# 2. power budget
row('Preliminary Calculation', 'D9', 1, 'P.sec', '2차 전력')
row('Preliminary Calculation', 'D10', 1, 'P.in_LLC', 'LLC단 입력 전력')
row('Preliminary Calculation', 'D11', 1, 'I.in_max', '최대 입력 전류')
row('Preliminary Calculation', 'D13', 1, 'P.d_LLC', 'LLC단 손실')
row('Preliminary Calculation', 'D14', 1, 'P.d_BR', '브리지 손실')
row('Preliminary Calculation', 'D15', 1, 'P.d_EMI', 'EMI 필터 손실')
row('Preliminary Calculation', 'D18', 0.01, 'η.ac', 'AC단 효율')
row('Preliminary Calculation', 'D19', 0.01, 'η.tot', '전체 효율')
row('Preliminary Calculation', 'D20', 1, 'P.in', '입력 전력')
# 3. tank
row('Res. Tank Design', 'D9', 1, 'n.calc', '권선비 계산값')
row('Res. Tank Design', 'D10', 1, 'M.HBmin', '최대 요구 게인')
row('Res. Tank Design', 'D11', 1, 'M.ACmax', '최소 요구 게인')
row('Res. Tank Design', 'D14', 1, 'λ.TD', 'λ 상한 (지연시간)')
row('Res. Tank Design', 'D16', 1, 'λ', 'λ 계산값')
row('Res. Tank Design', 'D17', 1, 'R.ac', '등가 부하 저항')
row('Res. Tank Design', 'D18', 1, 'Q.ZVS1', 'Q 상한 1')
row('Res. Tank Design', 'D26', 1, 'Q.ZVS', 'Q 상한 (마진 포함)')
row('Res. Tank Design', 'D27', 1, 'Z.0', '특성 임피던스')
row('Res. Tank Design', 'D30', 1e-9, 'T.ZC.a', 'ZVS 여유 시간',
    '2026-08-23 A 수정 적용·확인됨 — D28 을 RTC!$BB$149, D29 의 Q 를 RTC!$C$41, λ 를 D50, D30 의 분모를 D55 로. 이 행은 이제 차이가 없다')
row('Res. Tank Design', 'D50', 1, 'λ.act', 'λ 실현값')
row('Res. Tank Design', 'D51', 1, 'n.T', '권선 턴비')
row('Res. Tank Design', 'D55', 1e3, 'f.r', '직렬 공진')
row('Res. Tank Design', 'D56', 1e3, 'f.o', '병렬 공진')
row('Res. Tank Design', 'D57', 1e-6, 'L.mu', '개방 인덕턴스')
row('Res. Tank Design', 'D58', 1e-6, 'L.L1', '1차 누설')
row('Res. Tank Design', 'D59', 1e-6, 'L.L2', '2차 누설')
row('Res. Tank Design', 'D66', 1, 'I.trafo_pk', '트랜스 피크 전류')
row('Res. Tank Design', 'D68', 1, 'I.sec_pk', '2차 피크 전류')
row('Res. Tank Design', 'D65', 1, 'I.pri_lc', '1차 실효 (라인사이클)',
    'B 수정 후 남은 잔차. CC!J29 는 Simpson 적분이지만 1차 전류는 θ=0 에서 0 이 '
    '아니다 — 자화 전류가 남는다. 끝점을 외삽하면 +4.7 % 로 더 나빠지므로(θ→0 은 '
    '버스트 영역이라 도달하지 않는다) 0 으로 둔다. 10.30 → 10.70 A, 오차 −11.2 → −1.8 %')
row('Res. Tank Design', 'D67', 1, 'I.diode_lc', '2차 실효 (권선당, 라인사이클)',
    '2026-08-23 B 수정 적용·확인됨 — CC 에 θ 3열(F·G·H)과 Simpson 적분(열 J)을 넣고 여기를 CC!J.. 로 연결했다. 이 행은 이제 차이가 없다')
# 4. output bank
row('Power Components', 'D7', 1e-9, 'C.in', '입력 필름 커패시터 계산값')
row('Power Components', 'D21', 1e-6, 'C.ripple', '리플 요구 용량')
row('Power Components', 'D22', 1e-6, 'C.hold_req', '홀드업 요구 용량',
    '2026-08-23 D 수정 적용·확인됨 — 방전 시작을 (D14−D31/2) 로. 이 행은 이제 차이가 없다')
row('Power Components', 'D26', 1e-6, 'C.out', '출력 총용량')
row('Power Components', 'D27', 1e-3, 'ESR.out', '뱅크 ESR')
row('Power Components', 'D28', 1, 'I.Cout_rms', '뱅크 리플 전류',
    '2026-08-23 B 수정 적용·확인됨 — CC 에 θ 3열(F·G·H)과 Simpson 적분(열 J)을 넣고 여기를 CC!J.. 로 연결했다. 이 행은 이제 차이가 없다')
row('Power Components', 'D31', 1, 'ΔV.out', '2fL 리플 pk-pk')
row('Power Components', 'D32', 1, 'ΔV.out_pc', '리플 [%]')
row('Power Components', 'D33', 1e-3, 't.hold_act', '홀드업 시간',
    '2026-08-23 D 수정 적용·확인됨 — 방전 시작을 (D14−D31/2) 로. 이 행은 이제 차이가 없다')
row('Power Components', 'D34', 1e-3, 'R.N0', 'ESR만의 R&N')
row('Power Components', 'D39', 1e-3, 'R.Nact', '세라믹 포함 R&N')
row('Power Components', 'D64', 1, 'V.DS_pri', '1차 소자 내압')
row('Power Components', 'D86', 1, 'I.sec_pk', '2차 피크 (재확인)')
# 5. IC network
row('Device Setting', 'D4', 1e3, 'f.r', 'f_r (재확인)')
row('Device Setting', 'D19', 1e-12, 'C.T_max', 'C_T 상한',
    '같은 식에 다른 주파수를 넣은 것이다. SMath 의 f.sw_max_des 는 FB morphing 코너의 '
    '249.6 kHz, 워크북 D3 은 사양 상한 225 kHz — D2 가 RTC 에서 오는 189.3 kHz'
    '(V_in,max=264 Vac)라 MAX/MIN 이 225 를 고른다. 699.6 pF 를 만드는 주파수를 '
    '역산하면 249.65 kHz 로 정확히 맞는다. 선정 C.T 470 pF 는 양쪽 상한을 모두 통과')
row('Device Setting', 'D24', 1e3, 'R.T_ceil', 'R_T 상한 (f.Min=f.o 지점)',
    '같은 이유 (T_idle 250 ns 통일)')
row('Device Setting', 'D27', 1e3, 'f.Max', 'VCO 상한',
    '같은 이유')
row('Device Setting', 'D28', 1e3, 'f.Min', 'VCO 하한', '같은 이유')
row('Device Setting', 'D29', 1e3, 'f.SU', '기동 주파수',
    '같은 이유')
row('Device Setting', 'D31', 1, 'P.in', 'P_in (재확인)')
row('Device Setting', 'D32', 1, 'I.Lr_pk', '합성 탱크 피크')
row('Device Setting', 'D33', 1, 'I.pri_rms', 'R_CS 실효 전류')
row('Device Setting', 'D38', 1e-3, 'R.CS1', 'R_CS 상한 1')
row('Device Setting', 'D39', 1e-3, 'R.CS2', 'R_CS 상한 2')
row('Device Setting', 'D46', 1e-3, 'R.CS', 'R_CS 실현값')
row('Device Setting', 'D48', 1, 'P.in_max_act', '최대 입력 전력 한계')
row('Device Setting', 'D49', 1, 'I.OCP1', 'OCP1 트립 전류')
row('Device Setting', 'D50', 1, 'k.OCP', 'OCP 여유')
row('Device Setting', 'D61', 1e3, 'R.BM', 'R_BM 상한')
row('Device Setting', 'D78', 1, 'V.OVP1_out', 'OVP1 출력 환산')
row('Device Setting', 'D79', 1, 'V.OVP2_out', 'OVP2 출력 환산')
row('Device Setting', 'D83', 1, 'n.aux_max', 'n_aux/n_sec 상한')
row('Device Setting', 'D90', 1e3, 'R.ZCD_L', 'ZCD 하단 저항 하한')
row('Device Setting', 'D91', 1e3, 'R.ZCD_H', 'ZCD 상단 저항 상한')
# D108 is the hard ceiling from V_AC,min. The worksheet now carries the same
# quantity as R.CFG_max; its R.CFG is the design value for the V.AC_BO target,
# which the workbook has no counterpart for.
row('Device Setting', 'D108', 1e3, 'R.CFG_max', 'R_CFG 상한')
row('Device Setting', 'D109', 1, 'V.BO_act', '브라운아웃 전압')
# 6. loop and compensation
row('CompensationNet&Check', 'D5', 1, 'C.out', 'C_out (재확인)')
row('CompensationNet&Check', 'D36', 1e3, 'R.I', '분압기 상단')
row('CompensationNet&Check', 'D37', 1e3, 'R.o_calc', '분압기 하단 계산값')
# Design Spec D23 is the TARGET; this is what the selected divider actually
# gives. Design Spec G23 now mirrors it beside the target so the two cannot
# be confused again.
row('CompensationNet&Check', 'D38', 1, 'V.out_act', '출력 전압 실현값')
row('CompensationNet&Check', 'D41', 1e3, 'R.P_max', 'R_P 상한')
row('CompensationNet&Check', 'D42', 1e3, 'R.B_max', 'R_B 상한')
row('CompensationNet&Check', 'D43', 1e3, 'R.B_min', 'R_B 하한')
row('CompensationNet&Check', 'D52', 1, 'R.CS', 'R_CS (재확인)')
row('CompensationNet&Check', 'D64', 1, 'V.FB', 'FB 전압 @ Po')
row('CompensationNet&Check', 'D66', 1, 'G.o', '플랜트 이득')
row('CompensationNet&Check', 'D67', 1, 'V.FB_set', 'FB 설정점')
row('CompensationNet&Check', 'D68', 1, 'ΔV.out', '출력 리플 (재확인)')
row('CompensationNet&Check', 'D72', 1, 'f.cto', '무보상 교차주파수')
row('CompensationNet&Check', 'D73', 1, 'G.EA', '요구 EA 이득 @ 2fl',
    'C.13 수정이 실제로 동작함을 확인 — 2026-08-23 재계산 후 일치. 이 행은 이제 차이가 없다')
row('CompensationNet&Check', 'D74', 1, 'Γ.v', 'Γ_v')
row('CompensationNet&Check', 'D78', 1, 'K.v', 'K_v')
row('CompensationNet&Check', 'D84', 1, 'f.MB', '버스트 변조 주파수',
    'C.13 수정이 실제로 동작함을 확인 — 2026-08-23 재계산 후 일치. 이 행은 이제 차이가 없다')
row('CompensationNet&Check', 'D86', 1, 'f.zero', '목표 영점',
    'C.13 수정이 실제로 동작함을 확인 — 2026-08-23 재계산 후 일치. 이 행은 이제 차이가 없다')
row('CompensationNet&Check', 'D93', 1e-9, 'C.Fo_calc', 'C_Fo 계산값',
    'C.13 수정이 실제로 동작함을 확인 — 2026-08-23 재계산 후 일치. 이 행은 이제 차이가 없다')
row('CompensationNet&Check', 'D94', 1e-9, 'C.F_calc', 'C_F 계산값')
row('CompensationNet&Check', 'D95', 1e3, 'R.F_calc', 'R_F 계산값',
    'C.13 수정이 실제로 동작함을 확인 — 2026-08-23 재계산 후 일치. 이 행은 이제 차이가 없다')
row('CompensationNet&Check', 'D96', 1e-9, 'C.fx_calc', 'C_fx 계산값')
row('CompensationNet&Check', 'D101', 1, 'EA.oi', 'EA 이득 실현값')
row('CompensationNet&Check', 'D102', 1, 'f.zi', '영점 실현값')
row('CompensationNet&Check', 'D103', 1, 'f.pi', '극점 실현값')
row('CompensationNet&Check', 'D104', 1, 'f.pxi', '고주파 극점')
row('CompensationNet&Check', 'D123', 1, 'f.cross', '루프 교차주파수')
row('CompensationNet&Check', 'D124', 1, 'Φ.act', '위상 여유',
    'C.12 수정이 실제로 동작함을 확인 — 196셀에 f_px 항을 넣고 2026-08-23 재계산 후 일치. 이 행은 이제 차이가 없다')
row('CompensationNet&Check', 'D126', 1, 'D.3rd_act', '3차 고조파',
    'C.13 기준 차이의 하류 — 영구적이다. ΔV 비 1.0638(=50/47) × EA 이득 비 1.0512 '
    '= 1.1183 으로 정확히 설명된다(D65 · D125 참조)')
row('CompensationNet&Check', 'D128', 1e-3, 'ΔV.FBBM', '버스트 FB 리플',
    '같은 이유 — C.13 기준 차이의 하류, 비 1.1183')
row('CompensationNet&Check', 'D129', 1e3, 'ΔR.BM', 'R_BM 조정폭',
    '같은 이유 — C.13 기준 차이의 하류, 비 1.1183')



# ---------------------------------------------------------- 7. 2026-08-23 확장
# 위 101개 외에, 설계 시트에서 수치를 내면서 대조되지 않고 있던 것들.
row('Res. Tank Design', 'D12', 1, 'λ.1', 'λ 하한 1 (게인)')
row('Res. Tank Design', 'D13', 1, 'λ.2', 'λ 하한 2 (주파수)')
row('Res. Tank Design', 'D15', 1, 'λ.3', 'λ 하한 3 (f.sw,min)')
row('Res. Tank Design', 'D19', 1, 'Q.ZVS2', 'Q 상한 2 (전하)',
    'c.HB 800 pF · t.D 220 ns 로 2026-08-23 재계산 후 일치 확인')
row('Res. Tank Design', 'D35', 1, 'I.R1_pk', 'ZVS 코너 기본파 전류',
    '2026-08-23 A 수정 적용·확인됨 — D28 을 RTC!$BB$149, D29 의 Q 를 RTC!$C$41, λ 를 D50, D30 의 분모를 D55 로. 이 행은 이제 차이가 없다')
row('Res. Tank Design', 'D36', 1, 'I.R0', '중점 충전 전류',
    '2026-08-23 A 수정 적용·확인됨 — D28 을 RTC!$BB$149, D29 의 Q 를 RTC!$C$41, λ 를 D50, D30 의 분모를 D55 로. 이 행은 이제 차이가 없다')
row('Res. Tank Design', 'D37', 1e-9, 'T.T', '중점 천이 시간',
    '2026-08-23 A 수정 적용·확인됨 — D28 을 RTC!$BB$149, D29 의 Q 를 RTC!$C$41, λ 를 D50, D30 의 분모를 D55 로. 이 행은 이제 차이가 없다')
row('Res. Tank Design', 'D43', 1e-9, 'C.r_calc', 'C_r 계산값')
row('Res. Tank Design', 'D44', 1e-6, 'L.r_calc', 'L_r 계산값')
row('Res. Tank Design', 'D45', 1e-6, 'L.m_calc', 'L_m 계산값')
row('Res. Tank Design', 'D52', 1, 'Z.0s', '직렬 특성 임피던스')
row('Res. Tank Design', 'D53', 1, 'Z.0p', '병렬 특성 임피던스')
row('Res. Tank Design', 'D54', 1, 'f.n0', '정규화 하측 공진')
row('Power Components', 'D37', 1e-6, 'C.cer_min', '필요 세라믹 용량')
row('Power Components', 'D40', 1, 'P.Cout', '출력 뱅크 손실',
    '2026-08-23 B 수정 적용·확인됨 — CC 에 θ 3열(F·G·H)과 Simpson 적분(열 J)을 넣고 여기를 CC!J.. 로 연결했다. 이 행은 이제 차이가 없다')
row('Power Components', 'D45', 1, 'I.in_max', '최대 입력 전류')
row('Power Components', 'D53', 1, 'I.BR_rms', '브리지 실효 전류')
row('Power Components', 'D54', 1, 'I.BR_avg', '브리지 평균 전류')
row('Power Components', 'D55', 1, 'P.BR', '브리지 손실')
row('Power Components', 'D89', 1, 'V.DS_sec', '2차 소자 내압')
row('Power Components', 'D90', 1, 'I.sec_rating', '2차 소자 전류 정격')
# the switch blocks, which no comparison ever reached until now
row('Power Components', 'D65', 1, 'I.pri_rating', '1차 소자 전류 정격 (합성 피크)')
row('Power Components', 'D68', 1, 'n.par', '1차 병렬 소자 수')
row('Power Components', 'D62', 1, 'I.mos_dev', '1차 소자 1개 실효')
row('Power Components', 'D66', 1, 'I.pk_dev', '1차 소자 1개 피크')
row('Power Components', 'D78', 1, 'P.mos_sw_dev', '1차 스위칭 소자 1개 손실')
row('Power Components', 'D79', 1, 'P.mos_dev', '1차 정적 도통 소자 손실 (최악)')
row('Power Components', 'D103', 1, 'n.SR', '2차 병렬 소자 수')
row('Power Components', 'D87', 1, 'I.SR_dev', '2차 소자 1개 실효')
row('Power Components', 'D91', 1, 'I.SR_pk_dev', '2차 소자 1개 피크')
row('Power Components', 'D100', 1, 'P.SR_dev', '2차 소자 1개 손실')
row('Power Components', 'D102', 1, 'P.SR', '2차 정류 총손실')
row('Device Setting', 'D1', 1e3, 'f.o', 'f.sw,min = f_o')
row('Device Setting', 'D20', 1e-12, 'C.T_min', 'C_T 설계 하한')
# both round up now; the worksheet keeps the raw ratio alongside for the margin
row('Device Setting', 'D42', 1, 'N.RCS_min', '필요한 저항 개수 (올림)')
row('Device Setting', 'D44', 1e-3, 'R.CS_single_max', '단일 저항 상한')
row('Device Setting', 'D47', 1, 'P.RCS_pk', 'R_CS 손실 (최악 스위칭주기)')
row('Device Setting', 'D94', 1, 'V.OVP1_act', 'OVP1 실현값')
row('Device Setting', 'D95', 1, 'V.OVP2_act', 'OVP2 실현값')
row('Device Setting', 'D99', 1, 'V.out_SUend', '기동 종료 출력 전압')
# D65 is the reference row labelled "@2fL" (nominal). The DESIGN uses D68,
# "@2fLmin", and that is the one to compare - pointing at D65 manufactured a
# difference that is not there.
row('CompensationNet&Check', 'D68', 1, 'ΔV.loop', '루프가 보는 출력 리플')
row('CompensationNet&Check', 'D83', 1, 'EA.o', '목표 EA 이득',
    'C.13 의 하류')
row('CompensationNet&Check', 'D85', 1, 'f.pole', '목표 극점',
    'C.13 의 하류')
row('CompensationNet&Check', 'D118', 1, 'f.cto', '무보상 교차 (재확인)')
row('CompensationNet&Check', 'D125', 1, 'G.EA_act', '실현 EA 이득 @ 2fl',
    'C.13 의 하류')



import smresult

def read_sm():
    import xml.etree.ElementTree as ET
    raw = io.open(SM, encoding='utf-8').read()
    raw = re.sub(r'<raw format="[^"]+" encoding="base64">.*?</raw>', '<raw/>', raw, flags=re.S)
    root = ET.fromstring(raw.replace(' xmlns="http://smath.info/schemas/worksheet/1.0"', ''))
    out = {}
    for r in root.iter('region'):
        m = r.find('math')
        if m is None:
            continue
        i, res = m.find('input'), m.find('result')
        if i is None or res is None:
            continue
        e = list(i)
        if e and e[0].get('type') == 'operand':
            c = m.find('contract')
            u = list(c)[0].text if c is not None and len(list(c)) else ''
            val = smresult.value(res)
            if val is not None and u in U:
                out.setdefault(e[0].text, val * U[u])
            elif val is not None and not u:
                out.setdefault(e[0].text, val)
    return out


def stale_cache():
    """Has Excel recalculated since the last edit?

    xlsx_patch deletes xl/calcChain.xml whenever a formula changes, and Excel
    rebuilds it the first time it saves. So a missing chain means the cached
    values still describe the formulas as they were BEFORE the edit, and every
    number on the workbook side of this comparison is provisional.
    """
    import zipfile
    with zipfile.ZipFile(XL) as z:
        return 'xl/calcChain.xml' not in z.namelist()


def main():
    verbose = '-v' in sys.argv
    sm = read_sm()
    require_readable(XL)
    wv = openpyxl.load_workbook(XL, data_only=True)
    wf = openpyxl.load_workbook(XL)

    same = intended = diff = missing = stale_hits = 0
    is_stale = stale_cache()
    seen_cause = {}
    lines = []
    for sheet, cell, scale, var, label, why in M:
        xv = wv[sheet][cell].value
        sv = sm.get(var)
        if not isinstance(xv, (int, float)) or sv is None:
            missing += 1
            lines.append(('MISS', '%-26s %-22s %s' % (label, '%s!%s' % (sheet, cell),
                                                      'excel=%r smath=%r' % (xv, sv))))
            continue
        x_si = xv * scale
        # A purely relative test explodes when the right answer is ZERO. That is
        # not hypothetical: C.cer_min is MAX(C.cer_raw, 0) and the sheet clamps
        # it to -3.9e-21 F, machine noise, while the workbook's own IF returns a
        # clean 0. Both are right and they differed by "387000000000 %".
        # 1e-15 SI is far below anything real here - the smallest genuine
        # quantity in either document is a 100 pF parasitic, 1e-10 F.
        rel = abs(sv - x_si) / max(abs(x_si), 1e-30)
        ok = rel < 3e-3 or abs(sv - x_si) < 1e-15
        if ok:
            same += 1
            tag = 'same'
        elif why and not is_stale:
            intended += 1
            seen_cause.setdefault(ROOT.get((sheet, cell), '?'), []).append(label)
            tag = 'INTENDED'
        elif why:
            # the book has not been recalculated, so its cached value is not
            # the result of its own formula - a registered reason explains
            # nothing in that state
            stale_hits += 1
            tag = 'STALE?'
        else:
            diff += 1
            tag = '** DIFF'
        if verbose or not ok:
            lines.append((tag, '%-26s %-22s excel %-12.6g smath %-12.6g  %+7.2f %%%s'
                          % (label, '%s!%s' % (sheet, cell), x_si, sv, rel * 100,
                             '' if ok else '')))
            if why and not ok:
                c = ROOT.get((sheet, cell))
                lines.append(('', '    ↳ [%s] %s' % (c or '?', why)))
            if tag == '** DIFF':
                f = wf[sheet][cell].value
                lines.append(('', '    ↳ 엑셀 수식: %s' % f))

    for tag, text in lines:
        print('%-9s %s' % (tag, text))
    print()
    print('대조 %d항목 — 일치 %d · 의도된 차이 %d · **불일치 %d** · 읽기 실패 %d'
          % (len(M), same, intended, diff, missing))
    if seen_cause:
        print()
        print('의도된 차이 %d건의 근본 원인은 %d개다 — 같은 글자의 식에 값 하나가 다른 것이고,'
              % (intended, len(seen_cause)))
        print('그 그룹의 나머지는 첫 행의 하류다. 행을 세면 문제가 실제보다 많아 보인다.')
        for k in sorted(seen_cause):
            d = CAUSES.get(k, '?')
            head, detail = d if isinstance(d, tuple) else (d, '')
            print()
            print('  [%s] %s   (%d행: %s)'
                  % (k, head, len(seen_cause[k]), ' · '.join(seen_cause[k])))
            if detail:
                print('       %s' % detail)
    if is_stale:
        print()
        print('⚠ 워크북이 수식 변경 이후 아직 재계산되지 않았다 (calcChain 없음).')
        print('  캐시값이 옛 수식의 결과이므로 위 비교는 잠정이다.')
        if stale_hits:
            print('  STALE? %d건 — 등록된 사유가 있더라도 이 상태에서는 사유가'
                  ' 아니라 낡은 캐시가 원인일 수 있다.' % stale_hits)
        print('  Excel 에서 한 번 열었다 저장하면(fullCalcOnLoad=1) 갱신된다.')
        return 1
    return 1 if (diff or missing) else 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
