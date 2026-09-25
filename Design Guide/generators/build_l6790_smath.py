# -*- coding: utf-8 -*-
"""Builds  Smath/L6790A_SingleStage_PF_LLC_Design_Guide.sm

Structure follows Reference/EVLHV101SSR50W Design Guide.sm (HVLED101):
numbered sections, one labelled row per quantity, every input highlighted and
editable, every downstream number computed.  Equation tags [n] refer to
AN_L6790A_Design_Guide_rev2_1.md.

Target application: 90-264 Vac in, 25 V / 26.3 A out, TV SMPS for an OLED panel.

Run:  python build_l6790_smath.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smsheet import Sheet                                          # noqa: E402
from l6790 import design, sweep                                    # noqa: E402
import zedsheet as ZS                                              # noqa: E402

# 설계점 3종.  2차가 1턴이냐 2턴이냐로 감을 수 있는 세트 권선비가 갈린다.
#   n.T = N.x*N.p/N.s 이고 N.x = 3 이므로 N.s=1 이면 3의 배수만, N.s=2 면 1.5 의 배수.
#   n = n.T/sqrt(1+lambda) 이고 lambda = L.r/L.m 이므로 L.m 이 n 을 정한다.
# 6:1 은 Z.0 을 낮춰야 산다.  ZVS 를 좌우하는 자화 전류가
#   I.Lm,pk = 39.27 * n.T * lambda / (Z.0 * sqrt(1+lambda))   [V.out = 25 V]
# 로 Z.0 에 반비례하기 때문이다.  n.T 가 작아 불리한 만큼 Z.0 = sqrt(L.r/C.r) 을
# 10.49 -> 6 ohm 으로 내려 덮는다.  대가는 C.r 이 커지는 것과 순환 전류다.
#   N.x 는 세트 안의 트랜스포머 개수다.  세 설계점은 LGE 기존 보드의 3직렬을
#   그대로 쓰므로 3 이고, 8to1 만 2 다 - 코어 하나를 줄이는 대신 유닛당 1차가
#   8턴이 된다.  N.x 가 2 면 N.s=2 에서 감을 수 있는 세트비가 1.0 단위가 된다
#   (N.x=3 · N.s=2 는 1.5 단위라 8 을 못 잡는다).
VARIANTS = {
    #  9 : 1 (Np 3 · Ns 1 · L.m 24 uH) 은 2026-09-23 에 지웠다 - 정본이 7.5:1 이
    #  되면서 쓰는 곳이 없어졌다.  근거와 수치는 docs/HISTORY.md.
    '7p5to1': dict(nT=7.5, Cr=100, Lr=11.0, Lm=20.0, Nx=3, Np=5, Ns=2,
                  kaux=1, RzH=220, CT=470, label='7.5 : 1'),
    '8to1':   dict(nT=8.0, Cr=100, Lr=11.0, Lm=20.0, Nx=2, Np=8, Ns=2,
                  kaux=1, RzH=220, CT=470, label='8 : 1'),
    '6to1':   dict(nT=6.0, Cr=180, Lr=6.4, Lm=14.2, Nx=3, Np=2, Ns=1,
                  kaux=1, RzH=220, CT=330, label='6 : 1',
                  RBZ=680, CVCC=1000),
    #  ONE transformer, 15 : 2 on a single core (2026-09-22, user: the
    #  guide's example is one transformer).  Same tank as 7p5to1; N.aux =
    #  1 * 2 = 2 turns.  The core is cores.CHOSEN (E 60/22/16) - the
    #  PQ 40/40 of the three-unit build has no room for a 15-turn primary.
    '7p5to1_x1': dict(nT=7.5, Cr=100, Lr=11.0, Lm=20.0, Nx=1, Np=15, Ns=2,
                      kaux=1, RzH=220, CT=470, label='7.5 : 1',
                      Ae=211.0),
}
#  2026-09-25: the auxiliary winding supplies VCC (no external rail), n.aux
#  = 1.0 on every design point, so R.ZCD_H is 220 k on all of them.  RBZ and
#  CVCC are the Zener feed resistor and the VCC capacitor of section 14c; only
#  6:1 differs, because its higher f.Max and f.SU draw more gate current.
VAR = os.environ.get('L6790_VARIANT', '7p5to1')    # 정본 = 7.5:1, 3 코어 (2026-09-23)
V = VARIANTS[VAR]
V['n'] = V['nT'] / (1 + V['Lr'] / V['Lm']) ** 0.5

if os.environ.get('L6790_VARIANT'):          # 변형은 variants/ 로
    OUT = os.path.normpath(os.path.join(
        HERE, '..', '..', 'Smath', 'variants', 'L6790A_%s.sm' % VAR))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
else:                                        # 인자가 없으면 정본 자리에
    OUT = os.path.normpath(os.path.join(
        HERE, '..', '..', 'Smath', 'L6790A_SingleStage_PF_LLC_Design_Guide.sm'))
# The compensation network drawing on the CompensationNet&Check sheet of
# Calculation Excel Sheet/L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx, lifted
# out so the equations of section 16 sit next to the topology they describe.
FIG_COMP = os.path.normpath(os.path.join(
    HERE, '..', 'figures', 'comp_network_st.png'))
# BOM&Schematics sheet of the workbook, both drawings
FIG_POWER = os.path.normpath(os.path.join(
    HERE, '..', 'figures', 'bom_power_stage.png'))
FIG_PINS = os.path.normpath(os.path.join(
    HERE, '..', 'figures', 'bom_pin_config.png'))

# --------------------------------------------------------------------------
# This SMath build has NO min(), max(), if(), acos() or tan().  Everything is
# rewritten into the confirmed set  sqrt abs ln exp atan cos sin  (smsheet.py
# enforces this and raises if anything else slips in).
#   min(a,b) = (a + b - |a-b|)/2        max(a,b) = (a + b + |a-b|)/2
#   acos(z)  = 2*atan( sqrt(1-z^2)/(1+z) )          tan(x) = sin(x)/cos(x)
# abs() must only ever see a PURE NUMBER, so for quantities carrying a unit the
# unit is divided out and multiplied back on (SMath pitfall 3 of README.txt).
def MIN(a, b, u=None):
    d = "%s/'%s-%s/'%s" % (a, u, b, u) if u else "%s-%s" % (a, b)
    t = "abs(%s)" % d + ("*'%s" % u if u else "")
    return "(%s+%s-%s)/2" % (a, b, t)


def MAX(a, b, u=None):
    d = "%s/'%s-%s/'%s" % (a, u, b, u) if u else "%s-%s" % (a, b)
    t = "abs(%s)" % d + ("*'%s" % u if u else "")
    return "(%s+%s+%s)/2" % (a, b, t)


def ACOS(z):
    return "2*atan(sqrt(1-(%s)^2)/(1+(%s)))" % (z, z)


def TAN(x):
    return "sin(%s)/cos(%s)" % (x, x)


# The sheet is a design guide for one single-stage PF LLC, and its output
# spec belongs in the title. What does NOT belong is one customer's
# circumstances: which board a core came off, what was decided in a meeting,
# what will be settled on somebody's prototype.
# the output spec, written once. The title, the metadata and the two input
# rows in section 1 all come from here, so the sheet cannot end up named
# after a specification it no longer computes.
VOUT, IOUT = 25.0, 26.3
_SPEC = '%g V / %g A' % (VOUT, IOUT)
_TITLE = 'L6790A Single-Stage PF LLC Converter  -  %s Design Guide' % _SPEC

S = Sheet(_TITLE, 'L6790A', '%s, 90-264 Vac, topology morphing' % _SPEC)

S.h1(_TITLE)
S.note('Yellow cells are INPUTS - change them and press F9. Everything else is computed. '
       'Tags [n] refer to the design guide.')

# ===================================================================== 1
S.h2('1. Design Specifications')
S.const('- Minimum input voltage:', 'V.AC_min', "90*'V", 'V', 0)
S.const('- Maximum input voltage:', 'V.AC_max', "264*'V", 'V', 0)
S.const('- Minimum line frequency:', 'f.line_min', "47*'Hz", 'Hz', 0)
S.const('- Maximum line frequency:', 'f.line_max', "63*'Hz", 'Hz', 0)
S.const('- Regulated output voltage:', 'V.out', "%g*'V" % VOUT, 'V', 1)
S.const('- Maximum output current:', 'I.out', "%g*'A" % IOUT, 'A', 1)
S.row('- Maximum output power:', 'P.out', 'V.out*I.out', 'W', 1)
S.const('- Maximum 2fL output ripple, pk-pk [% of Vout]:', 'ΔV.pc', '5', None, 1)
S.const('- Hold-up time:', 't.holdup', "12*'ms", 'ms', 1)
S.const('- Minimum admitted output voltage in hold-up:', 'V.out_min', "19*'V", 'V', 1)
S.const('- Output rectifier configuration (1 = CT, 2 = FB):', 'N.rect', '1', None, 0)
S.const('- Output rectifier forward drop (0 for SR):', 'V.rect', "0*'V", 'V', 2)

# ===================================================================== 2
S.h2('2. Pre-design Choices')
S.note('[DS] datasheet, fixed by the silicon. [TOOL] the ST spreadsheet default. [PICK] a '
       'choice made here - section 17 lists what each costs if wrong.')
S.const('[PICK] Expected LLC stage efficiency (0..1):', 'η.HB', '0.98', None, 3)
S.const('[PICK] Target series resonant frequency:', 'f.r_t', "150*'kHz", 'kHz', 1)
S.const('[TOOL] Specified maximum switching frequency:', 'f.sw_max_spec', "225*'kHz", 'kHz', 1)
S.const('[TOOL] Specified minimum switching frequency:', 'f.sw_min_spec', "50*'kHz", 'kHz', 1)
S.const('[PICK] Equivalent input for resonant operation:', 'V.eq_ACnom', "225*'V", 'V', 1)
S.const('[TOOL] Above-resonance modulation depth:', 'δ.res', '0.05', None, 3)
S.const('[TOOL] ZVS margin:', 'm.ZVS', '0.15', None, 3)
S.const('[PICK] HB midpoint capacitance (2*Coss + Cpar):', 'c.HB', "800*'pF", 'pF', 0)
S.const('[PICK] Design dead time:', 't.D', "220*'ns", 'ns', 0)
S.const('[TOOL] EMI filter equivalent resistance:', 'R.EMI', "0.15*'ohm", 'ohm', 3)
S.note('   INPUT BRIDGE: s.br = 1 selects the synchronous bridge, 0 the diode bridge. The '
       'selector is a linear blend, so no branching is needed.')
S.const('[PICK] Bridge selector  (1 = synchronous, 0 = diodes):', 's.br', '1', None, 0)
S.const('[TOOL] Synchronous bridge: drop per device:', 'V.f_sync', "0.08*'V", 'V', 3)
S.const('[TOOL] Synchronous bridge: resistance per device:', 'R.d_sync', "0.04*'ohm", 'ohm', 3)
S.const('[PICK] Diode bridge: forward drop per diode:', 'V.f_diode', "0.85*'V", 'V', 3)
S.const('[PICK] Diode bridge: dynamic resistance per diode:', 'R.d_diode', "0.03*'ohm", 'ohm', 3)
S.row('- Selected bridge forward drop:', 'V.f_BR',
      "s.br*V.f_sync+(1-s.br)*V.f_diode", 'V', 3)
S.row('- Selected bridge dynamic resistance:', 'R.d',
      "s.br*R.d_sync+(1-s.br)*R.d_diode", 'ohm', 3)
S.const('[DS] HB -> FB morphing threshold (DS Table 5):', 'V.HVPK_BOH', "235*'V", 'V', 0)
S.const('[DS] FB -> HB morphing threshold (DS Table 5):', 'V.HVPK_BIH', "245*'V", 'V', 0)

# ===================================================================== 3
S.h2('3. Preliminary Calculations   [6] - [17]')
S.row('- Output rectifier efficiency:', 'η.rect', 'V.out/(V.out+N.rect*V.rect)', None, 4)
S.row('- Secondary power:', 'P.sec', 'P.out/η.rect', 'W', 1)
S.row('- Power into the LLC stage:', 'P.in_LLC', 'P.out/(η.rect*η.HB)', 'W', 1)
S.row('- Maximum input current (at Vac min):', 'I.in_max', 'P.in_LLC/V.AC_min', 'A', 3)
S.row('- LLC stage loss:', 'P.d_LLC', 'P.sec*(1-η.HB)/η.HB', 'W', 2)
S.row('- Input bridge loss:', 'P.d_BR',
      "2*(2*sqrt(2)/π*I.in_max*V.f_BR)+2*R.d*I.in_max^2", 'W', 3)
S.row('- Input bridge loss if SYNCHRONOUS:', 'P.dBR_sync',
      "2*(2*sqrt(2)/π*I.in_max*V.f_sync)+2*R.d_sync*I.in_max^2", 'W', 3)
S.row('- Input bridge loss if DIODES:', 'P.dBR_diode',
      "2*(2*sqrt(2)/π*I.in_max*V.f_diode)+2*R.d_diode*I.in_max^2", 'W', 3)
S.row('- EMI filter loss:', 'P.d_EMI', 'R.EMI*I.in_max^2', 'W', 3)
S.row('- AC front-end efficiency:', 'η.ac', 'P.in_LLC/(P.in_LLC+P.d_BR+P.d_EMI)', None, 4)
S.row('- Overall efficiency:', 'η.tot', 'η.HB*η.rect*η.ac', None, 4)
S.row('- Rated input power:', 'P.in', 'P.out/η.tot', 'W', 1)

# The two line voltages every frame carries besides the corners. One place,
# so a legend cannot drift away from the curve it names.
_LINE_A, _LINE_B = 110, 230

# ===================================================================== 4
S.h2('4. Equivalent Design Input Voltage - the effect of topology morphing   [18] - [20]')
S.note('V.AC_* is a LINE voltage. V.eq_* is what the tank sees at that line - '
       'twice it in full bridge, the same in half bridge.')
S.row('- at the minimum line (full bridge):', 'V.eq_ACmin', "2*V.AC_min", 'V', 2)
S.row('- at the HB morphing threshold:', 'V.eq_hbt',
      "V.HVPK_BIH/sqrt(2)", 'V', 2)
S.row('- LOWEST the tank ever sees (the smaller of those two):', 'V.eq_min',
      MIN('V.eq_ACmin', 'V.eq_hbt', 'V'), 'V', 2)
S.row('- at the maximum line (half bridge):', 'V.eq_ACmax', 'V.AC_max', 'V', 1)
S.row('- at the FB morphing threshold - HIGHEST the tank ever sees:',
      'V.eq_FBthr', "2*V.HVPK_BOH/sqrt(2)", 'V', 2)
S.row('- Middle of the morphing band:', 'V.thr',
      "(V.HVPK_BOH+V.HVPK_BIH)/(2*sqrt(2))", 'V', 2)
S.note('The two ordinary lines below are BUILT IN, not picked: every frame legend is '
       'written from them, and F9 does not reach a legend.')
S.const('[BUILD] first ordinary line condition:', 'V.AC_a',
        "%g*'V" % _LINE_A, 'V', 0)
S.row('- bridge mode (1 = half, 0 = full):', 'm.a',
      "(1+(V.AC_a/'V-V.thr/'V)/abs(V.AC_a/'V-V.thr/'V))/2", None, 0)
S.row('- what the tank sees there:', 'V.eq_ACa', "V.AC_a*(2-m.a)", 'V', 2)
S.const('[BUILD] second ordinary line condition:', 'V.AC_b',
        "%g*'V" % _LINE_B, 'V', 0)
S.row('- bridge mode (1 = half, 0 = full):', 'm.b',
      "(1+(V.AC_b/'V-V.thr/'V)/abs(V.AC_b/'V-V.thr/'V))/2", None, 0)
S.row('- what the tank sees there:', 'V.eq_ACb', "V.AC_b*(2-m.b)", 'V', 2)
S.row('- Input voltage imposing resonant operation:', 'V.eq_ACres', 'V.eq_ACnom*(1-δ.res)', 'V', 2)

# ===================================================================== 5
S.h2('5. Turns Ratio and Required Gain   [21] - [25]')
S.row('- Reflected output voltage:', 'V.o_eff', 'V.out+N.rect*V.rect', 'V', 2)
S.row('- Calculated turns ratio:', 'n.calc', "sqrt(2)*V.eq_ACres/(2*V.o_eff)", None, 4)
S.const('- SELECTED equivalent-model turns ratio:', 'n', '%.4f' % V['n'], None, 4,
        note='set by the WOUND ratio n.T = N.x*N.p/N.s, not the other way round.')
S.row('- Reflected voltage on the primary:', 'V.refl', 'n*V.o_eff', 'V', 1)
S.row('- Required gain at minimum equivalent input:', 'M.HBmin',
      "2*n*V.o_eff/(sqrt(2)*V.eq_min)", None, 4)
S.row('- Required gain at maximum equivalent input:', 'M.ACmax',
      "2*n*V.o_eff/(sqrt(2)*V.eq_ACmax)", None, 4)
S.row('- Required gain at the FB morphing threshold:', 'M.FBthr',
      "2*n*V.o_eff/(sqrt(2)*V.eq_FBthr)", None, 4)
S.row('- Required gain at the minimum line:', 'M.ACmin',
      "2*n*V.o_eff/(sqrt(2)*V.eq_ACmin)", None, 4)
S.row('- Required gain at the first plotted line:', 'M.ACa',
      "2*n*V.o_eff/(sqrt(2)*V.eq_ACa)", None, 4)
S.row('- Required gain at the second plotted line:', 'M.ACb',
      "2*n*V.o_eff/(sqrt(2)*V.eq_ACb)", None, 4)
S.row('- Required gain at the nominal equivalent input:', 'M.ACnom',
      "2*n*V.o_eff/(sqrt(2)*V.eq_ACnom)", None, 4)
S.note('Seven line conditions, one demand each, all at the line peak. Divide '
       'any of them by sin(theta) to get the demand at any other phase - that '
       'is the whole of what the input voltage does to this converter. '
       'Section 7.5 draws the two extremes against frequency; section 14c '
       'draws six of them against line phase.')

# ===================================================================== 6
S.h2('6. Resonant Tank Design   [26] - [35], [43] - [45]')
S.area_begin('the four lambda candidates - collapsed, only the largest is used')
S.row('- Minimum gain condition:', 'λ.1', '1/M.FBthr-1', None, 6)
S.row('- Maximum frequency condition:', 'λ.2', "λ.1/(1-(f.r_t/f.sw_max_spec)^2)", None, 6)
S.row('- Maximum frequency with dead time:', 'λ.TD',
      "λ.1/(1-π^2/8*(f.r_t/f.sw_max_spec)^2)", None, 6,
      note='[28]  the pi^2/8 has no stated derivation - indicative only.')
S.row('- Minimum frequency condition:', 'λ.3',
      "(f.sw_min_spec/f.r_t)^2/(1-(f.sw_min_spec/f.r_t)^2)", None, 4)
S.row('- larger of the first two:', 'λ.a', MAX('λ.1', 'λ.2'), None, 4)
S.row('- larger of the last two:', 'λ.b', MAX('λ.TD', 'λ.3'), None, 4)
S.area_end()
S.row('- Design lambda = Lr / Lm:', 'λ', MAX('λ.a', 'λ.b'), None, 4)
S.row('- Equivalent load resistance:', 'R.ac', "4/π^2*n^2*V.o_eff^2/P.in_LLC", 'ohm', 3)
S.area_begin('the two ZVS quality factors - collapsed, the smaller one binds')
S.row('- ZVS quality factor, gain-peak limit:', 'Q.ZVS1',
      "λ/M.HBmin*sqrt(1/λ+M.HBmin^2/(M.HBmin^2-1))", None, 4)
S.row('- ZVS quality factor, dead-time limit:', 'Q.ZVS2', "2/π*λ*t.D/(R.ac*c.HB)", None, 4)
S.row('- Binding ZVS quality factor:', 'Q.mn', MIN('Q.ZVS1', 'Q.ZVS2'), None, 4)
S.area_end()
S.row('- Design quality factor:', 'Q.ZVS', 'Q.mn/(1+m.ZVS)', None, 4)
S.row('- Tank characteristic impedance:', 'Z.0', 'R.ac*Q.ZVS', 'ohm', 3)
S.row('- Calculated resonant capacitor:', 'C.r_calc', "1/(2*π*f.r_t*Z.0)", 'nF', 2)
S.const('- SELECTED resonant capacitor:', 'C.r', "%g*'nF" % V['Cr'], 'nF', 1,
        note='round C.r UP: a larger C.r lowers Q.pk and buys ZVS margin, at the '
             'cost of a higher top frequency.')
S.row('- Resonant inductor for the selected C.r:', 'L.r_calc', "1/(C.r*(2*π*f.r_t)^2)", 'μH', 2)
S.const('- SELECTED resonant inductor:', 'L.r', "%g*'μH" % V['Lr'], 'μH', 2)
S.row('- Calculated magnetizing inductance:', 'L.m_calc', 'L.r/λ', 'μH', 2)
S.const('- SELECTED magnetizing inductance:', 'L.m', "%g*'μH" % V['Lm'], 'μH', 2,
        note='[45]  Normally NEVER round L.m up - it lowers lambda.act and eats '
             'the ZVS margin. Here L.m is not free: the winding fixes n.T = '
             'N.x*N.p/N.s, and the selected n then forces lambda.act = '
             '(n.T/n)^2 - 1, so L.m = L.r/lambda.act exactly. The cost lands on '
             'k.lam, which is a NO-LOAD condition; the loaded corners are '
             'judged by k.ZVS and k.ceil instead.')

# ===================================================================== 7
S.h2('7. Final Tank Check   [46] - [54]')
S.row('- Actual lambda:', 'λ.act', 'L.r/L.m', None, 4)
# 무부하 게인 M(f_n) = f_n^2/(f_n^2*(1+lam) - lam) 을 M.FBthr 로 풀면 코너가 나온다.
# 주석에 숫자를 손으로 적으면 변형 시트에서 조용히 낡는다 - 값에서 문장을 만든다.
_lam_act = V['Lr'] / V['Lm']
_M = S.ns['M__FBthr']
_f_r_py = 1 / (2 * math.pi * math.sqrt(V['Lr'] * 1e-6 * V['Cr'] * 1e-9))
_den = _M * (1 + _lam_act) - 1          # 무부하 점근선 1/(1+lam) 아래면 음수
_f_nl = (_f_r_py * math.sqrt(_M * _lam_act / _den)) if _den > 0 else None
if _f_nl is None:
    _klam_tail = (
        'THIS VARIANT HAS NO SOLUTION AT ALL. The no-load gain of an LLC falls only to '
        'the asymptote [153] 1/(1+lambda.act) = %.4f, and the FB-corner requirement M.FBthr is '
        '%.4f - below it. No frequency, however high, brings the unloaded tank down to '
        'the required gain. Regulation at no load and high line is then handed '
        'to BURST MODE, not to '
        'frequency. Under load the gain falls further and the corner is reached at '
        'f.sw.b in section 8, so the loaded design is unaffected.'
        % (1 / (1 + _lam_act), _M))
else:
    _klam_tail = (
        'At the selected lambda the no-load FB corner needs about %.0f kHz against the '
        '%.0f kHz target - %.0f %% over a design target, not over a limit.'
        % (_f_nl / 1e3, 225.0, 100 * (_f_nl / 225e3 - 1)))
S.row('- lambda against its requirement:', 'k.lam', 'λ.act/λ', None, 3,
      note='NOT A PASS/FAIL - a NO-LOAD requirement. The hardware limit is the VCO '
           'ceiling, checked by k.ceil.')
S.row('- Real (wound) turns ratio if Lr is the leakage:', 'n.T', "n*sqrt(1+λ.act)", None, 4)
S.row('- Series characteristic impedance:', 'Z.0s', "sqrt(L.r/C.r)", 'ohm', 3)
S.row('- Parallel characteristic impedance:', 'Z.0p', "sqrt((L.r+L.m)/C.r)", 'ohm', 3)
S.row('- Series resonant frequency:', 'f.r', "1/(2*π*sqrt(L.r*C.r))", 'kHz', 2)
S.row('- Normalized lower resonance:', 'f.n0', "sqrt(λ.act/(1+λ.act))", None, 4)
S.row('- Lower resonant frequency:', 'f.o', 'f.r*f.n0', 'kHz', 2)
S.row('- Actual quality factor at the line peak:', 'Q.pk', 'Z.0s/R.ac', None, 4)
S.row('- Physical magnetizing inductance:', 'L.mu', "sqrt(L.m*(L.m+L.r))", 'μH', 2)
S.row('- Primary leakage:', 'L.L1', 'L.m+L.r-L.mu', 'μH', 2)
S.row('- Secondary leakage:', 'L.L2', "L.L1/n.T^2", 'nH', 1)
S.row('- Open-circuit inductance to specify:', 'L.open', 'L.m+L.r', 'μH', 2)
S.row('- Short-circuit inductance to specify:', 'L.short', 'L.r', 'μH', 2)

# --------------------------------------------------------------- 7.5
# The gain family indexed by LINE PHASE, which is the one that moves while
# a single stage runs, with the required gain drawn beside it.  Everything
# here is already above: lambda.act and Q.pk from the tank, fn0 from [51],
# M.HBmin and M.FBthr from [24] and [25].
_ZN = 401
_ZXLO, _ZXHI = 0.4, 1.6
_ZTOP = 4.0
# no powers: the first bracket is NEGATIVE below fn0 and the window
# starts well below it. aa.g and bb.g hold the two sub-expressions
# the three curves share, which also computes them once each.
_ZGAIN = ('1/sqrt(el(dd.g,k.gc)'
          '+%s*%s*el(ee.g,k.gc))')
_ZXT = 'normalised frequency   fn = f.sw / f.r'
# the y title is drawn rotated inside the pane, so a long one runs off
# the top and bottom and gets clipped at both ends
_ZYT = 'voltage gain   M'

S.h2('7.5  Can the tank make the gain, at every point of the line cycle?')
S.const('[BUILD] gain plot from f.n =', 'x.gl', '%g' % _ZXLO, None, 2)
S.const('[BUILD] gain plot to   f.n =', 'x.gh', '%g' % _ZXHI, None, 2)
S.const('[PICK] points along the sweep:', 'N.gc', str(_ZN), None, 0)
S.area_begin('Q at the three phases - collapsed, Q(theta) = Q.pk sin(theta) squared')
S.row('- Q at theta = pi/2 (the line peak):', 'Q.h2', 'Q.pk', None, 4)
S.row('- Q at theta = pi/3:', 'Q.h3', 'Q.pk*sin(π/3)^2', None, 4)
S.row('- Q at theta = pi/4:', 'Q.h4', 'Q.pk*sin(π/4)^2', None, 4)
S.area_end()
S.row('- no-load gain floor at infinite frequency:', 'M.inf', '1/(1+λ.act)', None, 4)

S.area_begin('the vectors behind the two frames - collapsed')
S.prog(['k.gc := range(1,N.gc)'], label='- the range variable:', h=54, w=420)
S.prog(['k.2 := range(1,2)'], label='- a two-point range variable:', h=54, w=460)
S.prog(['el(fx.2,k.2) := x.gl+(k.2-1)*(x.gh-x.gl)'],
       label='- the two ends of the f.n axis:', h=54, w=660)
S.prog(['el(fn.g,k.gc) := x.gl+(k.gc-1)*(x.gh-x.gl)/(N.gc-1)'],
       label='- the f.n axis:', h=54, w=700)
S.prog(['el(aa.g,k.gc) := 1+λ.act'
        '-λ.act/(el(fn.g,k.gc)*el(fn.g,k.gc))'],
       label='- the real part, 1+lambda-lambda/fn^2:', h=56, w=880)
S.prog(['el(bb.g,k.gc) := el(fn.g,k.gc)-1/el(fn.g,k.gc)'],
       label='- the reactive part, fn-1/fn:', h=54, w=700)
S.prog(['el(dd.g,k.gc) := el(aa.g,k.gc)*el(aa.g,k.gc)'],
       label='- the real part squared:', h=54, w=640)
S.prog(['el(ee.g,k.gc) := el(bb.g,k.gc)*el(bb.g,k.gc)'],
       label='- the reactive part, fn-1/fn:', h=54, w=700)
S.prog(['el(mo.l,k.gc) := 1/abs(el(aa.g,k.gc))'],
       label='- M.OL, the no-load gain:', h=54, w=560)
for _t, _q in ((2, 'Q.h2'), (3, 'Q.h3'), (4, 'Q.h4')):
    S.prog(['el(mq.%d,k.gc) := %s' % (_t, _ZGAIN % (_q, _q))],
           label='- gain at theta = pi/%d:' % _t, h=62, w=980)
for _t in (2, 3, 4):
    S.prog(['el(ra.%d,k.2) := M.HBmin/sin(π/%d)' % (_t, _t)],
           label='- demanded gain, V.eq_min, pi/%d:' % _t, h=54, w=560)
for _t in (2, 3, 4):
    S.prog(['el(rb.%d,k.2) := M.FBthr/sin(π/%d)' % (_t, _t)],
           label='- demanded gain, FB corner, pi/%d:' % _t, h=54, w=560)
S.prog(['el(mi.f,k.2) := M.inf'], label='- the no-load floor:', h=54, w=420)
S.const('[PICK] points along the boundary:', 'N.mz', '240', None, 0)
S.prog(['k.mz := range(1,N.mz)'], label='- its range variable:', h=54, w=420)
S.prog(['el(fz.g,k.mz) := f.n0*1.002+(k.mz-1)*(0.998-f.n0*1.002)/(N.mz-1)'],
       label='- from just above fn0 to just below fr:', h=56, w=880)
S.prog(['el(z.f2,k.mz) := el(fz.g,k.mz)*el(fz.g,k.mz)'],
       label='- f.n squared:', h=54, w=580)
S.prog(['el(z.a,k.mz) := 1+λ.act'
        '-λ.act/el(z.f2,k.mz)'],
       label='- the real part a:', h=56, w=700)
S.prog(['el(z.b,k.mz) := el(fz.g,k.mz)-1/el(fz.g,k.mz)'],
       label='- the reactive part b:', h=54, w=620)
S.prog(['el(z.a2,k.mz) := el(z.a,k.mz)*el(z.a,k.mz)'],
       label='- a squared:', h=54, w=560)
S.prog(['el(z.b2,k.mz) := el(z.b,k.mz)*el(z.b,k.mz)'],
       label='- the reactive part b:', h=54, w=620)
S.prog(['el(z.q,k.mz) := -2*el(z.a,k.mz)*λ.act'
        '/(el(z.f2,k.mz)*el(fz.g,k.mz)*el(z.b,k.mz)'
        '*(1+1/el(z.f2,k.mz)))'],
       label='- Q squared at that peak:', h=60, w=980)
S.prog(['el(m.z,k.mz) := 1/sqrt(el(z.a2,k.mz)'
        '+el(z.q,k.mz)*el(z.b2,k.mz))'],
       label='- M.Z, the boundary:', h=58, w=860)
for _n, _x, _y in (('Gm.0', 'fn.g', 'mo.l'), ('Gm.2', 'fn.g', 'mq.2'),
                   ('Gm.3', 'fn.g', 'mq.3'), ('Gm.4', 'fn.g', 'mq.4'),
                   ('Ga.2', 'fx.2', 'ra.2'), ('Ga.3', 'fx.2', 'ra.3'),
                   ('Ga.4', 'fx.2', 'ra.4'), ('Gb.2', 'fx.2', 'rb.2'),
                   ('Gb.3', 'fx.2', 'rb.3'), ('Gb.4', 'fx.2', 'rb.4'),
                   ('Gi.1', 'fx.2', 'mi.f'), ('Gz.1', 'fz.g', 'm.z')):
    S.prog(['%s := eval(augment(vectorize(%s),vectorize(%s)))' % (_n, _x, _y)],
           label='- two-column matrix %s:' % _n, h=56, w=780, allow=ZS.VEC)
S.area_end()

# what the tank CAN do, at three points of the line cycle plus no load
_ZC = ['M.OL      no load',
       'M         theta = pi/2   (line peak)',
       'M         theta = pi/3',
       'M         theta = pi/4']
# The panes are harvested with a six-colour palette, so a seventh curve
# comes back the same blue as the first and an eighth the same red as the
# second - two different quantities in one colour on one frame. Each frame
# names its own colours instead.
#
# The gain frames are read as two families: what the tank CAN do at three
# phases, in blues, against what regulation DEMANDS at those same phases,
# in warms. The no-load curve and the boundary locus are neither, so they
# are black and green.
_PAL_GAIN = ['Black', 'Blue', 'DodgerBlue', 'Teal',
             'Red', 'DarkOrange', 'Magenta', 'Green']
# weight tells the two families apart as well as colour does: what the tank
# CAN do is heavy, what regulation DEMANDS is light, and so is the
# capacitive boundary, which is neither.
_W_GAIN = [4, 4, 4, 4, 2, 2, 2, 2]
# the same rule on the line-cycle frames: the line conditions are the data,
# the frequency limits are the frame. P(theta) and M.req(theta) carry
# nothing but data, so every trace on them is heavy.
_W_FSW = [4] * 6 + [2] * 4
_W_ALL = [4] * 6
# a frequency frame is one curve per limit, so the only thing wanted is
# eight colours nobody can confuse with each other in print
_PAL_LIM = ['Blue', 'Red', 'Green', 'DarkOrange', 'Purple', 'Teal',
            'Magenta', 'Black']
# nine, for the frequency frame: four inputs and five limits
# Six input voltages, cool to warm as the input rises, then five limits.
#
# The limits are picked apart from each other rather than off a list: on the
# printed sheet f.o and f.Min are seven kilohertz apart and were black and
# grey, which is two versions of the same line, and f.r and f.sw_max_spec
# were Purple and DarkViolet, which is one colour twice. The two that sit
# closest together now differ most.
_PAL_LIM9 = ['Blue', 'DodgerBlue', 'Teal', 'Green', 'DarkOrange', 'Red',
             'Black',        # f.o             the floor
             'SaddleBrown',  # f.Min           just above it
             'Purple',       # f.r
             'Gray']         # f.sw_max_spec
# a marker line is not data: it is grey so it reads as the frame it is
_PAL_BODE = ['Blue', 'Red', 'Green', 'Gray']
_PAL_PHASE = ['Blue', 'Gray', 'DarkOrange']

_ZPA = ZS.make(8, 'transfer',
               'Can the tank make the gain it needs?  '
               'LOWEST input the tank sees (HB morphing threshold)',
               _ZXT, _ZYT,
               _ZC + ['M.req     theta = pi/2',
                      'M.req     theta = pi/3',
                      'M.req     theta = pi/4',
                      'M.Z       capacitive limit'],
               (_ZXLO, _ZXHI), (0.0, _ZTOP), xlog=False,
               xsteps=(0.1, 0.02), ysteps=(0.5, 0.1), big=True,
               colors=_PAL_GAIN, widths=_W_GAIN, legendsize=10,
               size=(1580, ZS.fit(8)))
_ZPB = ZS.make(8, 'transfer',
               'Can the tank make the gain it needs?  '
               'HIGHEST input the tank sees (FB morphing threshold)',
               _ZXT, _ZYT,
               _ZC + ['M.req     theta = pi/2',
                      'M.req     theta = pi/3',
                      'M.req     theta = pi/4',
                      'M.inf     no-load floor'],
               (_ZXLO, _ZXHI), (0.0, _ZTOP), xlog=False,
               xsteps=(0.1, 0.02), ysteps=(0.5, 0.1), big=True,
               colors=_PAL_GAIN, widths=_W_GAIN, legendsize=10,
               size=(1580, ZS.fit(8)))

ZS.emit(S, ['Gm.0', 'Gm.2', 'Gm.3', 'Gm.4', 'Ga.2', 'Ga.3', 'Ga.4', 'Gz.1'],
        *_ZPA)
ZS.emit(S, ['Gm.0', 'Gm.2', 'Gm.3', 'Gm.4', 'Gb.2', 'Gb.3', 'Gb.4', 'Gi.1'],
        *_ZPB)

# ===================================================================== 8
S.h2('8. Line-Cycle Operating Point - closed form   [55] - [62]')


def cardano(tag, theta_expr, mpk_var, verbose=True, collapse=True):
    """closed-form fn(theta) for one (corner, phase) point.

    The eleven intermediates are packed four to a line: they exist so the sheet
    can be checked by hand, not to be read one by one.
    """
    if collapse:
        S.area_begin('cubic solution, %s - eleven intermediates, collapsed' % tag)
    # the derivation goes INSIDE the fold with the intermediates it explains:
    # it is the answer to "why the middle root", which is a question nobody
    # asks until they have opened the block
    if verbose:
        pass
    S.pack([
        (f'θ{tag}', theta_expr), (f'u{tag}', f"sin(θ{tag})^2"),
        (f'q{tag}', f"Q.pk^2*u{tag}^2"),
        (f'a2{tag}', f"(q{tag}-2*λ.act*(1+λ.act))/λ.act^2"),
        (f'a1{tag}', f"((1+λ.act)^2-2*q{tag}-u{tag}/{mpk_var}^2)/λ.act^2"),
        (f'a0{tag}', f"q{tag}/λ.act^2"),
        (f'p{tag}', f"a1{tag}-a2{tag}^2/3"),
        (f'r{tag}', f"2*a2{tag}^3/27-a2{tag}*a1{tag}/3+a0{tag}"),
        (f'ang{tag}', ACOS(f"3*r{tag}/(2*p{tag})*sqrt(-3/p{tag})") + "/3"),
        (f'w{tag}', f"2*sqrt(-p{tag}/3)"),
        (f'x{tag}', f"w{tag}*cos(ang{tag}-2*π/3)-a2{tag}/3"),
    ])
    if collapse:
        S.area_end()
    # These two are the ANSWER, not an intermediate, so they stay outside the
    # fold and they are labelled - in every corner, verbose or not. The short
    # form used to emit them through pack(), which writes no label and starts
    # six pixels below the fold terminator, so on paper they landed on the
    # grey rule as two bare numbers that read like something that had leaked
    # out of the collapsed block.
    S.row('- Normalized switching frequency:', f'f.n{tag}',
          f"1/sqrt(x{tag})", None, 5)
    S.row('- Switching frequency:', f'f.sw{tag}', f"f.n{tag}*f.r", 'kHz', 2)


def zvs(tag):
    S.row('- Instantaneous quality factor:', f'Q{tag}', f"Q.pk*u{tag}", None, 4)
    S.row('- Tank input impedance phase:', f'ph{tag}',
          f"atan(((λ.act^2+λ.act+(f.n{tag}^2-1)*Q{tag}^2)*f.n{tag}^2-λ.act^2)"
          f"/(Q{tag}*f.n{tag}^3))", None, 5)
    S.row('- Resonant current zero-crossing time:', f'T.ZC{tag}',
          f"ph{tag}/(2*π*f.sw{tag})", 'ns', 1)


S.h2('8.1  Worst corner - HB side of the morphing threshold (gain and ZVS)')
S.row('- Equivalent input voltage:', 'V.eq.a', 'V.eq_min', 'V', 2)
S.row('- Required gain at the line peak:', 'M.pk.a',
      "2*n*V.o_eff/(sqrt(2)*V.eq.a)", None, 4)
cardano('.a', "π/2", 'M.pk.a')
zvs('.a')

S.h2('8.2  Frequency corner - FB side of the morphing threshold')
S.row('- Equivalent input voltage:', 'V.eq.b', 'V.eq_FBthr', 'V', 2)
S.row('- Required gain at the line peak:', 'M.pk.b',
      "2*n*V.o_eff/(sqrt(2)*V.eq.b)", None, 4)
cardano('.b', "π/2", 'M.pk.b')
zvs('.b')

S.h2('8.2b  Nominal input - not a corner, but where the converter lives')
S.row('- Equivalent input voltage:', 'V.eq.c', 'V.eq_ACnom', 'V', 2)
S.row('- Required gain at the line peak:', 'M.pk.c',
      "2*n*V.o_eff/(sqrt(2)*V.eq.c)", None, 4)
cardano('.c', "π/2", 'M.pk.c', verbose=False)

S.h2('8.2e  The two plotted line conditions')
S.row('- Equivalent input voltage:', 'V.eq.pl1', 'V.eq_ACa', 'V', 2)
S.row('- Required gain at the line peak:', 'M.pk.p1',
      "2*n*V.o_eff/(sqrt(2)*V.eq.pl1)", None, 4)
cardano('.p1', "π/2", 'M.pk.p1', verbose=False)
S.row('- Equivalent input voltage:', 'V.eq.pl2', 'V.eq_ACb', 'V', 2)
S.row('- Required gain at the line peak:', 'M.pk.p2',
      "2*n*V.o_eff/(sqrt(2)*V.eq.pl2)", None, 4)
cardano('.p2', "π/2", 'M.pk.p2', verbose=False)

S.h2('8.2d  Minimum line, full bridge')
S.row('- Equivalent input voltage:', 'V.eq.lo', 'V.eq_ACmin', 'V', 2)
S.row('- Required gain at the line peak:', 'M.pk.lo',
      "2*n*V.o_eff/(sqrt(2)*V.eq.lo)", None, 4)
cardano('.lo', "π/2", 'M.pk.lo', verbose=False)

S.h2('8.2c  AC maximum, half bridge')
S.row('- Equivalent input voltage:', 'V.eq.d', 'V.eq_ACmax', 'V', 2)
S.row('- Required gain at the line peak:', 'M.pk.d',
      "2*n*V.o_eff/(sqrt(2)*V.eq.d)", None, 4)
cardano('.d', "π/2", 'M.pk.d', verbose=False)

S.h2('8.3  Frequency and ZVS verdict')
S.row('- Maximum operating switching frequency:', 'f.sw_max_op',
      MAX('f.sw.a', 'f.sw.b', 'Hz'), 'kHz', 2)
S.row('- 1.5 x the maximum operating frequency:', 'f.d1', '1.5*f.sw_max_op', 'kHz', 2)
S.row('- capped by the specified maximum:', 'f.d2',
      MIN('f.sw_max_spec', 'f.d1', 'Hz'), 'kHz', 2)
S.row('- Oscillator design frequency:', 'f.sw_max_des',
      MAX('f.sw_max_op', 'f.d2', 'Hz'), 'kHz', 2)
S.row('- Worst-case zero-crossing time:', 'T.ZC_min',
      MIN('T.ZC.a', 'T.ZC.b', 's'), 'ns', 1)
S.row('- ZVS margin (must be > 1):', 'k.ZVS', 'T.ZC_min/t.D', None, 3)
S.row('- Fundamental tank current at the ZVS corner:', 'I.R1_pk',
      "2*π*P.out/(sqrt(2)*η.HB*V.eq_min*cos(ph.a))", 'A', 3)
S.row('- Current available to charge the midpoint:', 'I.R0',
      'I.R1_pk*sin(ph.a)', 'A', 3, note='[41]')
S.row('- Midpoint transition time:', 'T.T',
      "c.HB*sqrt(2)*V.eq_min/I.R0", 'ns', 1)
S.row('- dead time covers the transition (>1):', 'k.TT', 't.D/T.T', None, 3)

# ===================================================================== 9
# ===================================================================== 9
S.h2('9. Currents and Device Stress at the Worst Corner   [63] - [70]')
S.row('- Instantaneous output current at the line peak:', 'I.o_inst', '2*I.out*u.a', 'A', 2)
S.row('- Clamped switching frequency:', 'f.sw_s', MAX('f.sw.a', 'f.r', 'Hz'), 'kHz', 2)
S.row('- Peak secondary current:', 'I.sec_pk',
      "π*(f.r/f.sw.a)*I.o_inst/(1-cos(π*f.r/f.sw_s))", 'A', 2)
S.row('- Conduction frequency:', 'f.sw_c', MIN('f.sw.a', 'f.r', 'Hz'), 'kHz', 2)
S.row('- Conduction ratio:', 'd', 'f.sw_c/f.r', None, 4)
S.row('- Sine-segment phase span:', 'φ.seg', "π*f.r/f.sw_s", None, 4)
S.row('- Truncation factor [64a]:', 'r.tr',
      "1-sin(2*φ.seg)/(2*φ.seg)", None, 4)
S.row('- Secondary rms per winding (rectifier device):', 'I.sec_rms',
      "I.sec_pk*sqrt(d*r.tr/4)", 'A', 2)
S.row('- Secondary rms into the output node:', 'I.node_rms',
      "I.sec_pk*sqrt(d*r.tr/2)", 'A', 2)
S.row('- Rectifier device rms:', 'I.diode_rms', 'I.sec_rms', 'A', 2)
S.row('- Peak reflected primary current:', 'I.trafo_pk', 'I.sec_pk/n', 'A', 3)
S.row('- Peak magnetizing current:', 'I.Lm_pk', "0.25*n*V.o_eff/(L.m*f.sw_s)", 'A', 3)
S.area_begin('where the composite peak falls - collapsed, three intermediates')
S.row('- Magnetizing-to-load current ratio:', 'r.mix',
      "2*I.Lm_pk/(π*I.trafo_pk)", None, 4)
S.row('- ratio clamped to 1 (peak at the end of the half cycle):', 'r.clamp',
      MIN('r.mix', '0.999999999'), None, 6)
S.row('- Composite peak position:', 'x.pk', ACOS('-r.clamp') + "/π", None, 4)
S.area_end()
S.row('- Composite tank current peak:', 'I.Lr_pk',
      "I.Lm_pk*(2*x.pk-1)+I.trafo_pk*sin(π*x.pk)", 'A', 3)
S.row('- Primary rms over one switching cycle:', 'I.pri_rms',
      "sqrt(I.trafo_pk^2/2+I.Lm_pk^2/3+(I.Lm_pk*f.sw.a*(1/f.sw.a-1/f.r))^2)", 'A', 3)
S.row('- MOSFET rms:', 'I.mos_rms', "I.pri_rms/sqrt(2)", 'A', 3)

# ===================================================================== 10
S.h2('10. Line-Cycle RMS of the Output Capacitor Current   [70a]')
for k, (tg, th) in enumerate([('.a1', "π/8"), ('.a2', "π/4"), ('.a3', "3*π/8")]):
    S.area_begin(f'phase point {k+1} of 3 (theta = {th}) - the whole block. Only S{tg} and '
                 f'P{tg} leave it, and they are used by the Simpson sums below.')
    cardano(tg, th, 'M.pk.a', verbose=False, collapse=False)  # already inside an area
    S.pack([(f'I.oi{tg}', f"2*I.out*u{tg}", 'A', 3),
            (f'f.ss{tg}', MAX(f'f.sw{tg}', 'f.r', 'Hz'), 'kHz', 2),
            (f'f.sc{tg}', MIN(f'f.sw{tg}', 'f.r', 'Hz'), 'kHz', 2),
            (f'I.sp{tg}', f"π*(f.r/f.sw{tg})*I.oi{tg}/(1-cos(π*f.r/f.ss{tg}))", 'A', 3),
            (f'S{tg}', f"f.sc{tg}/f.r/2*I.sp{tg}^2", None, 2),
            (f'I.tr{tg}', f"I.sp{tg}/n", 'A', 3),
            (f'I.lm{tg}', f"0.25*n*V.o_eff/(L.m*f.ss{tg})", 'A', 3),
            (f'P{tg}', f"I.tr{tg}^2/2+I.lm{tg}^2/3"
                       f"+(I.lm{tg}*f.sw{tg}*(1/f.sw{tg}-1/f.r))^2", None, 3)])
    S.area_end()
S.note('The Simpson sums need the two ENDPOINTS as well as the three folded '
       'phase points: S.a and P.a at theta = pi/2 (the line peak, already '
       'computed in section 9) and P.0 at theta -> 0, where the load is gone '
       'and only the magnetizing current is left.')
S.pack([('I.lm.0', "0.25*n*V.o_eff/(L.m*f.r)", 'A', 3),
        ('P.0', "I.lm.0^2/3+(I.lm.0*(1-f.n0))^2", None, 3),
        ('S.a', "d/2*I.sec_pk^2", None, 2),
        ('P.a', "I.pri_rms^2", None, 3)])
S.row('- Mean square secondary node current (Simpson):', 'I.node_ms',
      "(4*S.a1+2*S.a2+4*S.a3+S.a)/12", None, 4)
S.row('- Output capacitor rms current:', 'I.Cout_rms',
      "sqrt(I.node_ms-I.out^2)", 'A', 2)
S.row('- Rectifier device rms over the line cycle:', 'I.diode_lc',
      "sqrt(I.node_ms/2)", 'A', 2,
      note='use this for conduction loss, not the line-peak value.')
S.row('- Mean square primary current (Simpson):', 'I.pri_ms',
      "(P.0+4*P.a1+2*P.a2+4*P.a3+P.a)/12", None, 4)
S.row('- Primary rms over the line cycle:', 'I.pri_lc', "sqrt(I.pri_ms)", 'A', 3)
S.row('- MOSFET rms over the line cycle:', 'I.mos_lc', "I.pri_lc/sqrt(2)", 'A', 3)

# ===================================================================== 11
S.h2('11. Output Capacitor   [101] - [106], at the worst line phase')
S.row('- Capacitance required by the 2fL ripple:', 'C.ripple',
      "I.out/(2*π*f.line_min*V.out*ΔV.pc/100)", 'mF', 2)
S.const('- SELECTED single capacitor:', 'C.single', "470*'μF", 'μF', 0)
S.const('- SELECTED number in parallel:', 'n.C', '160', None, 0)
S.row('- Output capacitance:', 'C.out', 'n.C*C.single', 'mF', 2)
S.row('- Actual 2fL ripple (pk-pk):', 'ΔV.out', "I.out/(2*π*f.line_min*C.out)", 'V', 3)
S.row('- Actual ripple [% of Vout]:', 'ΔV.out_pc', '100*ΔV.out/V.out', None, 2)
S.row('- Hold-up start voltage (worst phase):', 'V.start', 'V.out-ΔV.out/2', 'V', 3)
S.row('- Capacitance required by hold-up:', 'C.hold_req',
      "2*P.out*t.holdup/(V.start^2-V.out_min^2)", 'mF', 2)
S.row('- Achieved hold-up time:', 't.hold_act',
      "C.out*(V.start^2-V.out_min^2)/(2*P.out)", 'ms', 2)
S.row('- Hold-up margin (must be > 1):', 'k.hold', 't.hold_act/t.holdup', None, 3)
S.row('- Ripple current per capacitor:', 'I.Cout_each', 'I.Cout_rms/n.C', 'A', 2)
S.const('[PICK] ESR of ONE output capacitor:', 'ESR.single', "30*'mohm", 'mohm', 1)
S.row('- ESR of the whole bank:', 'ESR.out', 'ESR.single/n.C', 'mohm', 4,
      note='[107]  read the ESR at the SWITCHING frequency, not the 120 Hz tan-delta.')
S.row('- Ripple and noise from the ESR alone:', 'R.N0',
      'ESR.out*I.sec_pk', 'mV', 2)
S.const('[PICK] Allowed ripple and noise at f.sw:', 'R.Nmax', "30*'mV", 'mV', 1)
S.const('[PICK] Ceramic displacement factor [%]:', 'DF', '2.5', None, 2)
S.row('- Ceramic needed to reach the budget:', 'C.cer_raw',
      "(1-R.Nmax/R.N0)*DF/100/(ESR.out*2*π*f.sw.a*R.Nmax/R.N0)", 'μF', 2)
S.row('- clamped at zero:', 'C.cer_min', MAX('C.cer_raw', "0*'μF", 'μF'), 'μF', 2,
      note='[109]  zero means no ceramic is needed.')
S.const('[PICK] SELECTED ceramic capacitor:', 'C.ceramic', "10*'μF", 'μF', 1)
S.row('- Resulting ripple and noise:', 'R.Nact',
      "R.N0/(ESR.out*2*π*f.sw.a*C.ceramic/(DF/100)+1)", 'mV', 2)
S.row('- R&N budget check (>1):', 'k.RN', 'R.Nmax/R.Nact', None, 3)
S.row('- Dissipation in the output bank:', 'P.Cout',
      "I.Cout_rms^2/(2*π*f.sw.a*C.ceramic/(DF/100)+1/ESR.out)", 'W', 3)

# ===================================================================== 12
S.h2('12. Transformer Construction')
S.const('- Number of transformers in the series string:', 'N.x',
        '%d' % V['Nx'], None, 0)
S.const('- Primary turns per transformer:', 'N.p', '%d' % V['Np'], None, 0)
S.const('- Secondary half-winding turns:', 'N.s', '%d' % V['Ns'], None, 0)
S.row('- Wound turns ratio:', 'n.T_act', 'N.x*N.p/N.s', None, 4)
S.row('- Resulting equivalent-model turns ratio:', 'n.act', "n.T_act/sqrt(1+λ.act)", None, 4)
S.row('- Resulting reflected voltage:', 'V.refl_act', 'n.act*V.o_eff', 'V', 2,
      note='compare with V.refl of section 5 and keep the deviation within about 1 %.')
S.const('- Core effective area [mm^2]:', 'A.e_mm', '%g' % V.get('Ae', 113.1), None, 2)
S.row('- Core effective area:', 'A.e', "A.e_mm*'mm*'mm", None, 8)
S.row('- Open-circuit inductance per transformer:', 'L.open_x', 'L.open/N.x', 'μH', 3)
S.row('- Physical magnetizing inductance per transformer:', 'L.mu_x',
      'L.mu/N.x', 'μH', 3,
      note='L.mu, not L.open: only this part of the open-circuit flux linkage '
           'goes round the core. The rest is primary leakage.')
S.row('- Inductance factor required:', 'A.L', "L.open_x/N.p^2", 'nH', 2)
S.row('- Peak flux density in each core:', 'B.pk',
      "n.T_act*V.o_eff/N.x/(2*f.r)/(2*N.p*A.e)", 'mT', 1)
S.const('[PICK] Peak flux density allowed:', 'B.max', "0.2*'T", 'mT', 0,
        note='about half of saturation at Tc 100 C.')
S.row('- Core area this requires:', 'A.e_req',
      "n.T_act*V.o_eff/N.x/(2*f.r)/(2*N.p*B.max)", None, 8)
S.row('- Core area required [mm^2]:', 'A.e_req_mm', "A.e_req/('mm*'mm)", None, 1)
S.row('- Core area margin (>1):', 'k.Ae', 'A.e/A.e_req', None, 3,
      note='below 1 means the core is too small for the flux target.')
S.row('- Flux-equivalent DC test current:', 'I.sat_eq',
      "B.pk*N.p*A.e/L.mu_x", 'A', 2,
      note='the DC current that reproduces B.pk in the OPEN-circuit test. '
           'Divide by L.mu_x, not by L.open_x: the leakage part of the open '
           'flux linkage does not thread the centre leg, so using L.open '
           'puts B.pk at a lower current than it really takes and '
           'UNDER-specifies the test. The answer must come out equal to '
           'I.Lm_pk, because with the secondary open the whole primary '
           'current IS magnetizing current - check_trans_spec tests that.')
#  I.sat_spec is NOT here: it needs V.OVP2_act, which section 14 defines.
#  It is worked out there, right under the OVP thresholds it comes from.
S.row('- Secondary rms current per transformer:', 'I.sec_x', 'I.diode_lc/N.x', 'A', 2)
S.row('- Primary rms current (same in all - series):', 'I.pri_x', 'I.pri_lc', 'A', 3)

# ===================================================================== 13
S.h2('13. Semiconductor Selection   [111] - [121]')
S.const('[PICK] Number of primary switches:', 'N.mos', '4', None, 0)
S.h2('13.1  Primary switch requirement')
S.row('- Minimum drain-source voltage:', 'V.DS_pri', "1.3*sqrt(2)*V.AC_max", 'V', 1,
      note='[114]  30 % over the peak line. 600 V class.')
S.row('- Peak current the device must carry:', 'I.pri_rating', '1.3*I.Lr_pk', 'A', 2)
S.row('- rms in a SWITCHING position:', 'I.D_rms_sw', 'I.mos_lc', 'A', 3)
S.row('- rms in the STATICALLY-ON position (HB mode):', 'I.D_rms_dc', 'I.pri_lc', 'A', 3)
S.const('[PICK] Devices in parallel per switch position:', 'n.par', '1', None, 0)
S.row('- rms current in ONE device (switching):', 'I.mos_dev',
      'I.D_rms_sw/n.par', 'A', 3)
S.row('- rms current in ONE device (statically on):', 'I.dc_dev',
      'I.D_rms_dc/n.par', 'A', 3)
S.row('- peak current in ONE device:', 'I.pk_dev', 'I.Lr_pk/n.par', 'A', 2)
S.const('[PICK] Conduction loss budget per POSITION:', 'P.mos_budget', "3*'W", 'W', 2)
S.row('- Required RDSon per position, switching:', 'R.dson_req_sw',
      "P.mos_budget/I.D_rms_sw^2", 'mohm', 1)
S.row('- Required RDSon per position, static (BINDING):', 'R.dson_req_dc',
      "P.mos_budget/I.D_rms_dc^2", 'mohm', 1)
S.const('[PICK] RDSon rise from 25 C to Tj,max:', 'K.Tpri', '1.8', None, 2)
S.row('- Required RDSon per DEVICE at Tj,max:', 'R.dson_req_dev_p',
      "n.par*R.dson_req_dc", 'mohm', 1)
S.row('- The same as a 25 C datasheet number (SOURCE AGAINST THIS):',
      'R.dson_req_25_p', "R.dson_req_dev_p/K.Tpri", 'mohm', 1)
S.const('[PICK] Layout parasitic at the midpoint:', 'C.par', "100*'pF", 'pF', 0)
S.row('- Largest admissible Coss per device:', 'C.oss_max', "(c.HB-C.par)/2", 'pF', 1,
      note='[116]  c.HB = 2*Coss + Cpar. Above this, put the real Coss into c.HB in section 2 and press F9.')

S.h2('13.1b  Body diode requirement - the parameter that decides survival')
S.row('- Bus voltage across the recovering diode:', 'V.bd_rr', "sqrt(2)*V.AC_max", 'V', 1)
S.row('- Current in the body diode at commutation:', 'I.bd_rr', 'I.Lm_pk', 'A', 2)
S.row('- Recovery energy per event, per unit Qrr:', 'E.rr_perQ', "V.bd_rr", 'V', 1)

S.h2('13.2  Secondary rectifier requirement  (center tap, 2 legs)')
S.row('- Minimum drain-source voltage [118]:', 'V.DS_sec', "1.2*2*V.out/N.rect", 'V', 1)
S.const('[PICK] Ringing allowance over the ideal reflected voltage:', 'K.ring', '1.6', None, 2,
        note='[118] allows only 20 %, which is optimistic. About 1.6x is common '
             'practice - use the row below.')
S.row('- Recommended drain-source voltage:', 'V.DS_sec_rec',
      "K.ring*2*V.out/N.rect", 'V', 1)
S.row('- Peak current per leg:', 'I.sec_rating', '1.2*I.sec_pk', 'A', 1)
S.row('- rms per leg over the line cycle:', 'I.sec_leg', 'I.diode_lc', 'A', 2)
S.const('[PICK] SR devices in parallel per leg:', 'n.SR', '2', None, 0)
S.row('- peak current in ONE device:', 'I.SR_pk_dev', 'I.sec_pk/n.SR', 'A', 1)
S.row('- rms current in ONE device:', 'I.SR_dev', 'I.sec_leg/n.SR', 'A', 2)
S.const('[PICK] Conduction loss budget per leg:', 'P.SR_budget', "3*'W", 'W', 2)
S.row('- Required RDSon per leg:', 'R.dson_req_leg',
      "P.SR_budget/I.sec_leg^2", 'mohm', 2)
S.const('[PICK] RDSon rise from 25 C to Tj,max:', 'K.Tsec', '1.9', None, 2)
S.row('- Required RDSon per DEVICE at Tj,max:', 'R.dson_req_dev',
      "n.SR*R.dson_req_leg", 'mohm', 2)
S.row('- The same as a 25 C datasheet number (SOURCE AGAINST THIS):',
      'R.dson_req_25_s', "R.dson_req_dev/K.Tsec", 'mohm', 2)
S.row('- Primary switch rating on the COMPOSITE tank peak:', 'I.pri_rating2',
      '1.3*I.Lr_pk', 'A', 2)
S.h2('13.3  Losses once the devices are chosen')
S.const('[PICK] Primary RDSon max per device, 25 C at VGS = 10 V:', 'R.dson_p25', "45*'mohm",
        'mohm', 1,
        note='check this against R.dson_req_25_p above whenever it changes.')
S.row('- the same at Tj,max, per device:', 'R.dson_p_hot',
      "R.dson_p25*K.Tpri", 'mohm', 1)
S.row('- effective RDSon per switch POSITION:', 'R.dson_p',
      "R.dson_p_hot/n.par", 'mohm', 1)
S.row('- loss in one SWITCHING position:', 'P.mos_sw', "R.dson_p*I.mos_lc^2", 'W', 2)
S.row('- loss in the STATICALLY-ON position (HB mode):', 'P.mos_dc',
      "R.dson_p*I.pri_lc^2", 'W', 2)
S.row('- loss in ONE device of a SWITCHING position:', 'P.mos_sw_dev',
      "R.dson_p_hot*I.mos_dev^2", 'W', 3)
S.row('- loss in ONE device of the STATIC position (worst):', 'P.mos_dev',
      "R.dson_p_hot*I.dc_dev^2", 'W', 3)
S.row('- Budget margin on the binding device (>1):', 'k.Ploss',
      "P.mos_budget/P.mos_dc", None, 3,
      note='13.1 states the budget, 13.3 spends it; this row is the comparison.')
S.row('- Total primary conduction loss (either mode):', 'P.pri_tot',
      "N.mos/2*R.dson_p*I.pri_lc^2", 'W', 2)
S.const('[PICK] Secondary SR RDSon max per device, 25 C at VGS = 10 V:', 'R.dson_s25', "3.7*'mohm",
        'mohm', 2,
        note='check against R.dson_req_25_s in 13.2 whenever it changes.')
S.row('- the same at Tj,max, per device:', 'R.dson_s',
      "R.dson_s25*K.Tsec", 'mohm', 2)
S.row('- loss in ONE SR device:', 'P.SR_dev', "R.dson_s*I.SR_dev^2", 'W', 3)
S.row('- Secondary conduction loss (total):', 'P.SR',
      "2*N.rect*R.dson_s/n.SR*I.diode_lc^2", 'W', 2)
S.row('- Budget margin per leg (>1):', 'k.PSR',
      "P.SR_budget/(P.SR/(2*N.rect))", None, 3)
S.row('- Input bridge rms current:', 'I.BR_rms', "I.in_max/sqrt(2)", 'A', 3)
S.row('- Input bridge average current:', 'I.BR_avg', "sqrt(2)/π*I.in_max", 'A', 3)
S.row('- Input bridge loss:', 'P.BR', "2*(2*I.BR_avg*V.f_BR)+4*R.d*I.BR_rms^2", 'W', 3)

# ===================================================================== 14
S.h2('14. IC Network   [72] - [100]')
S.const('- Oscillator idle time (DS gives 250 / 350 / 700 ns):', 'T.idle', "250*'ns", 'ns', 0,
        note='DS Table 5 back-solves to 250 ns; DS 5.3.2 says 700 ns. Check both.')
S.const('- CT reference voltage:', 'V.CTref', "1.5*'V", 'V', 2)
S.const('- Maximum E/A current:', 'I.EA_max', "400*'μA", 'μA', 1)
S.const('- Oscillator start-up current:', 'I.OSC_SU', "412.5*'μA", 'μA', 1)
S.area_begin('the oscillator windows - collapsed, C.T and R.T are chosen below')
S.row('- Maximum timing capacitor:', 'C.T_max',
      "I.EA_max/(2*V.CTref)*(1-2*T.idle*f.sw_max_des)*(1-2*T.idle*f.o)"
      "/(f.sw_max_des-f.o)", 'pF', 1)
S.row('- Minimum timing capacitor:', 'C.T_min',
      "1/(30000*'ohm)*(1/(2*f.o)-T.idle)", 'pF', 1)
# 창의 끝은 변형마다 달라진다 - 시트가 방금 계산한 값에서 문장을 만든다.
_ctlo, _cthi = S.ns['C__T_min'] * 1e12, S.ns['C__T_max'] * 1e12       # pF
_lo, _hi = max(_ctlo, 270.0), min(_cthi, 1000.0)                      # 교집합
_geo = math.sqrt(_lo * _hi)
S.const('- SELECTED timing capacitor:', 'C.T', "%g*'pF" % V['CT'], 'pF', 0,
        note='must sit inside BOTH windows - the design window above and the '
             '270..1000 pF datasheet range. Take the geometric middle, not an edge. '
             'C0G/NP0.')
S.row('- C.T under its DESIGN limit (>1):', 'k.CTd', MIN('C.T_max/C.T', 'C.T/C.T_min', None), None, 3,
      note='the 270..1000 pF checks below are the DATASHEET range, a different limit.')
S.row('- R.T that would put f.Min exactly on f.o:', 'R.T_ceil', "1/C.T*(1/(2*f.o)-T.idle)", 'ohm', 0)
S.area_end()
S.const('- SELECTED timing resistor:', 'R.T', "11*'kohm", 'kohm', 1,
        note='DS operating range 5 k to 30 k. A smaller R.T raises the VCO clamp.')
S.row('- R.T under that ceiling (>1):', 'k.RTd', 'R.T_ceil/R.T', None, 3)
S.row('- VCO minimum frequency:', 'f.Min', "1/(2*(C.T*R.T+T.idle))", 'kHz', 2)
S.row('- VCO maximum frequency:', 'f.Max',
      "1/(2*(C.T/(I.EA_max/V.CTref+1/R.T)+T.idle))", 'kHz', 2)
S.row('- Start-up frequency:', 'f.SU',
      "1/(2*(C.T/((I.EA_max+I.OSC_SU)/V.CTref+1/R.T)+T.idle))", 'kHz', 2)
S.row('- VCO clamp above the floor (must be > 1):', 'k.floor', 'f.Min/f.o', None, 3)
S.row('- VCO ceiling margin (must be > 1):', 'k.ceil', 'f.Max/f.sw_max_op', None, 3)
S.row('- R.T*C.T (must be 2.5 .. 12 us):', 'τ.RT', 'R.T*C.T', 'μs', 3)
S.row('- Current sense resistor, max-power limit:', 'R.CS1', "16.8*'ohm*'W/P.in",
      'mohm', 2)
S.row('- Current sense resistor, OCP1 limit:', 'R.CS2', "0.55*'V/I.Lr_pk", 'mohm', 2)
S.row('- Binding limit:', 'R.CS_max', MIN('R.CS1', 'R.CS2', 'ohm'), 'mohm', 2)
S.const('[PICK] Number of sense resistors in parallel:', 'N.RCS', '5', None, 0)
S.row('- Largest admissible SINGLE resistor:', 'R.CS_single_max', "R.CS_max*N.RCS",
      'mohm', 2)
S.const('[PICK] SELECTED single sense resistor:', 'R.CS_single', "120*'mohm", 'mohm', 1)
S.row('- Resulting current sense resistor:', 'R.CS', "R.CS_single/N.RCS", 'mohm', 2,
      note='no filter and no series resistor between R.CS and the ISEN pin: the '
           'maximum-power law and both OCP levels share that one pin.')
S.row('- within the limit (must be > 1):', 'k.RCS', 'R.CS_max/R.CS', None, 3)
S.row('- Actual maximum input power:', 'P.in_max_act', "16.8*'ohm*'W/R.CS", 'W', 1)
S.row('- OCP1 trip current:', 'I.OCP1', "0.55*'V/R.CS", 'A', 2)
S.row('- OCP2 trip current:', 'I.OCP2', "0.75*'V/R.CS", 'A', 2)
S.row('- OCP1 margin over the composite peak (>1):', 'k.OCP', 'I.OCP1/I.Lr_pk', None, 3)
S.row('- Sense resistor dissipation (line cycle):', 'P.RCS',
      "R.CS*I.pri_lc^2", 'W', 2)
S.row('- Sense resistor dissipation (worst switching cycle):', 'P.RCS_pk',
      "R.CS*I.pri_rms^2", 'W', 2)
S.row('- per resistor, line cycle:', 'P.RCS_each', 'P.RCS/N.RCS', 'W', 3)
S.const('[PICK] Power rating of ONE sense resistor:', 'P.RCS_rating', "1*'W", 'W', 1)
S.row('- Sense resistors the dissipation needs:', 'N.RCS_req',
      'P.RCS_pk/P.RCS_rating', None, 2,
      note='[82]  round UP to the next whole part.')
S.row('- rounded UP to whole resistors:', 'N.RCS_min',
      "N.RCS_req+0.5+atan(cos(π*N.RCS_req)/sin(π*N.RCS_req))/π", None, 0)
S.row('- enough resistors fitted (>1):', 'k.NRCS', 'N.RCS/N.RCS_req', None, 3)
S.row('- per resistor, worst switching cycle:', 'P.RCS_each_pk', 'P.RCS_pk/N.RCS', 'W', 3)
S.const('[PICK] Input power at the burst entry point:', 'P.in_BM', "75*'W", 'W', 1)
S.row('- as a fraction of the rated input power:', 'r.BM', 'P.in_BM/P.in', None, 3)
S.row('- Burst-mode resistor:', 'R.BM',
      "16.7*1000*'ohm/('V*'V)*R.CS*P.in_BM", 'kohm', 3,
      note='[85]  valid range 15 k to 140 k.')
S.const('[PICK] SELECTED burst-mode resistor:', 'R.BM_sel', "30*'kohm", 'kohm', 1)
S.row('- Burst-mode FB threshold:', 'V.BM_eq',
      "R.BM_sel/(100000*'ohm)*'V+0.5*'V", 'V', 3,
      note='built from the part actually FITTED, not from the calculated '
           'R.BM above.')
S.const('- Brown-out threshold (rms):', 'V.AC_BO', "85*'V", 'V', 1)
S.row('- CFG resistor:', 'R.CFG', "sqrt(2)*V.AC_BO/(4*'V)*1000*'ohm", 'ohm', 0,
      note='[89]  15 k .. 47 k keeps morphing enabled. Leave LOUT2 open - a pull-down below about 8 k reads as fixed half bridge.')
S.row('- LARGEST admissible CFG resistor:', 'R.CFG_max',
      "sqrt(2)*V.AC_min/(4*'V)*1000*'ohm", 'ohm', 0)
S.const('[PICK] SELECTED CFG resistor:', 'R.CFG_sel', "30*'kohm", 'kohm', 1)
S.row('- CFG above the 15 k morphing floor (>1):', 'k.CFG_lo',
      "R.CFG_sel/(15*'kohm)", None, 3,
      note='DS 5.2.9.')
S.row('- CFG below the 47 k morphing ceiling (>1):', 'k.CFG_hi',
      "47*'kohm/R.CFG_sel", None, 3)
S.row('- Resulting brown-out threshold:', 'V.BO_act',
      "R.CFG_sel*4*'V/(1000*'ohm)/sqrt(2)", 'V', 2)
S.row('- brown-out below the minimum line (must be > 1):', 'k.BO',
      'V.AC_min/V.BO_act', None, 3)
S.const('[PICK] SELECTED input film capacitor:', 'C.in_sel', "2200*'nF", 'nF', 0)
S.row('- Input film capacitor:', 'C.in', "3*'nF/'W*P.in", 'nF', 0,
      note='[100]  3 nF/W. There is no bulk capacitor; too much C.in distorts the line current.')
S.row('- input film capacitor check (>1):', 'k.Cin', 'C.in_sel/C.in', None, 3,
      note='the 3 nF/W guideline is a FLOOR, so the selected part must sit at or above '
           'it.')
S.const('- OVP1 overshoot above Vout:', 'Δ.OVP1', '0.10', None, 3)
S.row('- OVP1 output voltage:', 'V.OVP1_out', 'V.out*(1+Δ.OVP1)', 'V', 2)
S.row('- OVP2 output voltage:', 'V.OVP2_out', "V.OVP1_out*2.5/2.3", 'V', 2)
S.note('The auxiliary winding SUPPLIES VCC (2026-09-25): there is no external '
       'rail. It feeds VCC through a Zener-referenced emitter follower and a '
       'bypass diode (DS 5.1.8), and the ZCD divider below. n.aux_max and '
       'k.auxr are the ST tool\'s test for an auxiliary winding wired straight '
       'to VCC; with the regulator in between, the 25 V limit applies to the '
       'regulator OUTPUT, and k.VCC in section 14c tests that instead. This is '
       'a deliberate difference from the ST workbook.')
S.row('- Maximum auxiliary-to-secondary turns ratio (direct feed only):',
      'n.aux_max', "25*'V/V.OVP2_out", None, 4)
S.const('[PICK] SELECTED auxiliary-to-secondary ratio:', 'n.aux', '%g' % V['kaux'],
        None, 3,
        note='1.0: the lowest whole-turn ratio that keeps the regulator in '
             'regulation at the end of hold-up (k.RBZ, 14c); 0.5 puts VCC below '
             'the HVSU threshold, 1.5 raises everything the regulator burns '
             'by half.')
S.row('- auxiliary ratio under the direct-feed limit (>1 only if wired '
      'straight to VCC):', 'k.auxr', 'n.aux_max/n.aux', None, 3)
S.row('- Auxiliary turns in series (whole number):', 'N.aux',
      'n.aux*N.s', None, 2,
      note='TOTAL, all cores together. It has to be a whole number, and '
           'nothing else here checks that. With N.x > 1, wind one turn on '
           'every unit and series as many as this needs; the rest stay open.')
S.row('- Auxiliary winding nominal voltage:', 'V.aux', 'n.aux*V.out', 'V', 2,
      note='holds only while the winding is coupled to the SECONDARY: wind it '
           'in triple-insulated wire over the secondary (section 14c).')
S.row('- Auxiliary voltage at OVP2:', 'V.aux_OVP2', 'n.aux*V.OVP2_out', 'V', 2)
S.const('- ZCD divider bias current at OVP1:', 'I.bias', "120*'μA", 'μA', 1)
S.row('- Lower ZCD resistor:', 'R.ZCD_L', "2.3*'V/I.bias", 'kohm', 3)
S.const('[PICK] SELECTED lower ZCD resistor:', 'R.ZCD_L_sel', "19*'kohm", 'kohm', 1)
# 분압기는 n.aux 에 정비례한다 - 보조 권선비가 두 배면 상단 저항도 두 배다.
# 이 문장의 숫자를 손으로 적으면 변형 시트에서 곧바로 자기모순이 된다.
_ovp1_t = 27.5
_rzh_calc = 19.0 * (V['kaux'] * _ovp1_t / 2.3 - 1)          # kohm
_ovp1_act = 2.3 * (V['RzH'] / 19.0 + 1) / V['kaux']         # V
_rzh_other = 330.0 if V['kaux'] > 2 else 680.0
_ovp1_other = 2.3 * (_rzh_other / 19.0 + 1) / V['kaux']
S.const('[PICK] SELECTED upper ZCD resistor:', 'R.ZCD_H_sel',
        "%g*'kohm" % V['RzH'], 'kohm', 1,
        note='E24 value ABOVE the calculated one, so OVP1 sits clear of the ripple '
             'peak.')
S.row('- Upper ZCD resistor:', 'R.ZCD_H',
      "R.ZCD_L_sel*(n.aux*V.OVP1_out/(2.3*'V)-1)", 'kohm', 2,
      note='connect the auxiliary winding so ZCD is POSITIVE when LOUT1 is on. The '
           'opposite polarity causes destructive hard switching.')
S.row('- divider ratio actually fitted:', 'r.ZCD', 'R.ZCD_H_sel/R.ZCD_L_sel+1', None, 4)
S.row('- OVP1 the fitted divider really gives:', 'V.OVP1_act',
      "2.3*'V/n.aux*r.ZCD", 'V', 2,
      note='[97]  only the RATIO sets the threshold, so both resistors must be the '
           'selected parts.')
S.row('- OVP2 the fitted divider really gives:', 'V.OVP2_act',
      "2.5*'V/n.aux*r.ZCD", 'V', 2, note='[98]')
#  The saturation test current belongs here and not in section 12, because
#  the number it has to be safe against is this one.  Below resonance the
#  magnetizing conduction window is fixed at T_r/2, so the magnetizing
#  current does NOT depend on f.sw - it is proportional to the OUTPUT
#  VOLTAGE alone.  The worst output the controller ever allows is OVP2, so
#  that is the worst core flux the transformer ever sees, and the test
#  current is simply the magnetizing peak there.  There is no arbitrary
#  margin factor and there must not be one: a round number chosen by hand
#  hides which circuit limit the part is actually being tested against.
#  V.out, not V.o_eff, in the denominator: the exact flux ratio is
#  (V.OVP2_act + N.rect*V.rect)/(V.out + N.rect*V.rect), and V.OVP2_act/V.out
#  is the ratio that sits at or above it.  V.OVP2_act/V.o_eff sat below it
#  whenever V.rect > 0 (equal here, V.rect = 0 with SR).  2026-09-25.
S.row('- Output-voltage overshoot the core must survive:', 'k.OVsat',
      'V.OVP2_act/V.out', None, 4)
S.row('- Test current on the vendor specification:', 'I.sat_spec',
      'I.sat_eq*k.OVsat', 'A', 2,
      note='rounded UP to a whole ampere on the specification sheet. It is '
           'well under the tank peak I.Lr_pk and that is correct - with the '
           'secondary OPEN there is no ampere-turn cancellation, so this '
           'current makes the same core flux that I.Lr_pk makes in service.')
#   V.ZCD_SUend: the draft datasheet's electrical characteristics give 1.36 V
#   (typ); the ST tool carried 1.35 V.  Datasheet value, user 2026-09-24.
S.const('- ZCD voltage at the end of start-up:', 'V.ZCD_SUend', "1.36*'V", 'V', 2)
S.row('- Output voltage where start-up hands over:', 'V.out_SUend',
      "V.ZCD_SUend/(2.3*'V)*V.OVP1_act", 'V', 2)
S.row('- OVP1 against the target (near 1):', 'k.OVP1', 'V.OVP1_act/V.OVP1_out', None, 3)

S.h2('14c. VCC from the auxiliary winding - 2 T and a Zener regulator')
S.note('aux winding -> D.aux -> C.aux -> NPN emitter follower (base held by a '
       'Zener fed through R.BZ from C.aux) -> bypass diode -> VCC pin and '
       'C.VCC. The bypass diode is the one DS 5.1.8 asks for: it keeps the '
       'HVSU charge current out of the regulator. The same winding drives the '
       'ZCD divider above.')
S.const('[DS] VCC turn-on threshold (rising):', 'V.CC_on', "17*'V", 'V', 1)
S.const('[DS] HVSU charge-current turn-on threshold (falling):', 'V.CC_HVSUon',
        "12*'V", 'V', 1)
S.const('[DS] VCC turn-off (UVLO) threshold (falling):', 'V.CC_off', "8*'V", 'V', 1)
S.const('[DS] VCC recommended operating maximum:', 'V.CC_opmax', "25*'V", 'V', 1)
S.const('[DS] IC operating supply current:', 'I.CC', "3*'mA", 'mA', 1)
S.const('[DS] HVSU charge current at 115 Vac:', 'I.HVSU_lo', "13*'mA", 'mA', 1)
S.const('[DS] HVSU charge current at 230 Vac:', 'I.HVSU_hi', "9*'mA", 'mA', 1)
S.const('[DS] HVSU shut-down timeout after VCC passes V.CC_on:', 't.HVSU',
        "120*'ms", 'ms', 0)
S.const('[ASSUMED] Silicon junction drop (D.aux, V.BE, bypass diode):', 'V.F_j',
        "0.7*'V", 'V', 2)
S.row('- C.aux at the nominal output:', 'V.Caux', 'n.aux*V.out-V.F_j', 'V', 2)
S.row('- C.aux at OVP1 (the highest it stays at):', 'V.Caux_OVP1',
      'n.aux*V.OVP1_act-V.F_j', 'V', 2)
S.row('- C.aux at OVP2 (transient; rates C.aux and the pass transistor):',
      'V.Caux_OVP2', 'n.aux*V.OVP2_act-V.F_j', 'V', 2,
      note='plus whatever leakage spike the winding carries - measure it on '
           'the prototype and rate V.CEO and C.aux above both.')
S.row('- C.aux at the end of hold-up:', 'V.Caux_hold', 'n.aux*V.out_min-V.F_j',
      'V', 2)
S.const('[PICK] SELECTED Zener voltage:', 'V.DZ_sel', "15*'V", 'V', 1)
S.const('[PICK] Zener tolerance (the part grade to buy):', 'tol.DZ', '0.05',
        None, 3)
S.row('- Zener, low end:', 'V.DZ_min', 'V.DZ_sel*(1-tol.DZ)', 'V', 2)
S.row('- Zener, high end:', 'V.DZ_max', 'V.DZ_sel*(1+tol.DZ)', 'V', 2)
S.row('- Regulated VCC, nominal:', 'V.CC_reg', 'V.DZ_sel-2*V.F_j', 'V', 2)
S.row('- Regulated VCC, low end:', 'V.CC_reg_min', 'V.DZ_min-2*V.F_j', 'V', 2)
S.row('- Regulated VCC, high end:', 'V.CC_reg_max', 'V.DZ_max-2*V.F_j', 'V', 2)
S.row('- lowest VCC above the HVSU threshold (>1):', 'k.VCClo',
      'V.CC_reg_min/V.CC_HVSUon', None, 3,
      note='the draft datasheet does not say whether the HVSU charge current '
           'comes back below this threshold once it has shut down; kept '
           'above it so the run supply never depends on the answer.')
S.row('- highest VCC under the 25 V operating limit (>1):', 'k.VCC',
      'V.CC_opmax/V.CC_reg_max', None, 3)
S.note('The load on this rail is the IC and the gate drivers. The driver share '
       'is the gate charge of every switch position, once per period.')
S.const('[CANDIDATE] Primary MOSFET gate charge, typ.:', 'Q.g',
        "78.6*10^(-9)*'A*'s", None, 1,
        note='STO60N045DM9, the candidate primary MOSFET, as listed by '
             'DiscoverEE; confirm it on the ST datasheet. 78.6 nC.')
S.const('- Switch positions driven in full bridge:', 'N.sw', '4', None, 0)
S.row('- Supply current in run, bound at f.Max:', 'I.VCC',
      'I.CC+N.sw*n.par*Q.g*f.Max', 'mA', 1,
      note='Q.g holds at the datasheet test condition; a gate driven harder '
           'takes more charge. f.Max is the highest run frequency.')
S.const('[PICK] Pass transistor current gain at I.VCC, min.:', 'β.min',
        '50', None, 0)
S.const('[PICK] Minimum Zener bias current:', 'I.DZ_min', "1*'mA", 'mA', 1)
S.row('- Largest R.BZ that still regulates at the end of hold-up:', 'R.BZ_max',
      '(V.Caux_hold-V.DZ_max)/(I.VCC/β.min+I.DZ_min)', 'ohm', 0)
S.const('[PICK] SELECTED Zener feed resistor R.BZ:', 'R.BZ_sel',
        "%g*'ohm" % V.get('RBZ', 820),
        'ohm', 0)
S.row('- R.BZ margin (>1):', 'k.RBZ', 'R.BZ_max/R.BZ_sel', None, 3)
S.row('- Zener dissipation, no load, C.aux at OVP1 (rating to buy):', 'P.DZ',
      'V.DZ_max*(V.Caux_OVP1-V.DZ_min)/R.BZ_sel', 'mW', 0)
S.row('- Pass transistor dissipation at OVP1 and I.VCC (rating to buy):',
      'P.Qpass', '(V.Caux_OVP1-(V.DZ_min-V.F_j))*I.VCC', 'W', 2,
      note='With n.aux = 1.5 the voltage across it would grow by V.out/2.')
S.row('- the same at the nominal output (goes in the loss account):',
      'P.Qpass_nom', '(V.Caux-(V.DZ_sel-V.F_j))*I.VCC', 'W', 2)
S.note('START-UP. The HVSU charges C.VCC to V.CC_on and switching begins. '
       'Until the output is high enough for the winding to carry VCC, C.VCC '
       'supplies the drivers alone from V.CC_on down to V.CC_HVSUon, and with '
       'the HVSU charge current helping from there down to V.CC_off (DS: the '
       'charge current turns on below V.CC_HVSUon). The worst case is the full '
       'bridge (low line, 13 mA) at the start-up frequency.')
S.row('- Supply current during start-up (full bridge at f.SU):', 'I.VCC_SU',
      'I.CC+N.sw*n.par*Q.g*f.SU', 'mA', 1)
S.row('- Output voltage at which the winding holds VCC at V.CC_off:',
      'V.out_UV', '(V.CC_off+3*V.F_j+I.VCC_SU/β.min*R.BZ_sel)/n.aux', 'V', 2)
S.row('- Time to get there, rated current into C.out and NO load:', 't.hand',
      'C.out*V.out_UV/I.out', 'ms', 1,
      note='[ASSUMED] the load is held off until the rail is up, as a TV '
           'sequences its panel. Any load during start-up stretches this.')
S.row('- hand-over inside the HVSU window (>1):', 'k.thand', 't.HVSU/t.hand',
      None, 3)
S.row('- C.VCC that bridges the hand-over:', 'C.VCC_req',
      't.hand/((V.CC_on-V.CC_HVSUon)/I.VCC_SU'
      '+(V.CC_HVSUon-V.CC_off)/(I.VCC_SU-I.HVSU_lo))', 'μF', 0)
S.const('[PICK] SELECTED C.VCC:', 'C.VCC_sel', "%g*'μF" % V.get('CVCC', 680),
        'μF', 0)
S.row('- C.VCC margin (>1):', 'k.CVCC', 'C.VCC_sel/C.VCC_req', None, 3)
S.row('- Delay before the first switching, 230 Vac:', 't.VCCchg',
      'C.VCC_sel*V.CC_on/I.HVSU_hi', 's', 2,
      note='the price of C.VCC: the HVSU fills it at 9 mA from the line. '
           'Check the HVSU temperature on the prototype (DS: HVSU over-'
           'temperature protection).')

S.h2('14b. Datasheet Operating Limits - every ratio below must be greater than 1')
S.note('DS Table 2 (recommended operating range) and DS section 5.3.2. These are hard silicon '
       'limits, not design preferences.')
S.row('- R.T above the 5 k minimum:', 'k.RT_lo', "R.T/(5000*'ohm)", None, 3)
S.row('- R.T below the 30 k maximum:', 'k.RT_hi', "30000*'ohm/R.T", None, 3)
S.row('- C.T above the 270 pF minimum:', 'k.CT_lo', "C.T/(270*'pF)", None, 3)
S.row('- C.T below the 1000 pF maximum:', 'k.CT_hi', "1000*'pF/C.T", None, 3)
S.row('- R.T*C.T above the 2.5 us minimum:', 'k.tau_lo', "τ.RT/(2.5*'μs)", None, 3)
S.row('- R.T*C.T below the 12 us maximum:', 'k.tau_hi', "12*'μs/τ.RT", None, 3)
S.row('- f.Max below the 675 kHz ceiling:', 'k.675', "675*'kHz/f.Max", None, 3)
S.row('- f.SU below the 675 kHz ceiling:', 'k.SU', "675*'kHz/f.SU", None, 3)
S.row('- dead time above TADT_min 40 ns:', 'k.ADT_lo', "t.D/(40*'ns)", None, 3)
S.row('- dead time below TADT_max 420 ns:', 'k.ADT_hi', "420*'ns/t.D", None, 3)
S.row('- shortest on-pulse:', 't.on_min', "1/(2*f.sw_max_op)-t.D", 'ns', 1)
S.row('- on-pulse above Tpulse_min 370 ns:', 'k.pulse', "t.on_min/(370*'ns)", None, 3,
      note='DS Table 5: below this the adaptive dead time is not enabled.')

# ===================================================================== 15
# -------------------------------------------------------------- 14c
# The half line cycle. Section 8 solves one phase at each corner; this
# sweeps the whole cycle - and it does NOT solve the cubic to do it.
#
# Inverting the gain equation for the PHASE rather than for the frequency
# leaves a quadratic in sin(theta) squared, which is a closed form four
# operations long. The cubic version was seven references deep and SMath
# never finished it.
_TN = 241                       # the theta sweep for the gain and power frames
_TNF = 240                      # the frequency sweep, in fn - EVEN, so
#                                 that the mirror's sign never divides
#                                 by zero in the middle of the sweep
_TLO, _THI = 0.05, math.pi - 0.05
_TXT = ('line phase   theta [rad]     '
        '0 and pi = zero crossings,  pi/2 = line peak')
_TW = (0.0, 3.2)
# The six conditions both line-cycle frames carry, in rising order of what
# the tank sees. The middle four are line voltages a product meets; the two
# thresholds are not, and are here because they are the corners the tank was
# designed against.
_LINES = (('M.ACmin', 'f.n.lo', 'minimum line', 'V.eq_ACmin'),
          ('M.HBmin', 'f.n.a', 'tank minimum', 'V.eq_min'),
          ('M.ACa', 'f.n.p1', '%g Vac' % _LINE_A, 'V.eq_ACa'),
          ('M.ACb', 'f.n.p2', '%g Vac' % _LINE_B, 'V.eq_ACb'),
          ('M.ACmax', 'f.n.d', 'maximum line', 'V.eq_ACmax'),
          ('M.FBthr', 'f.n.b', 'FB threshold', 'V.eq_FBthr'))
_TIN = tuple((i + 1, m, '%s   %s' % (nm, v))
             for i, (m, _f, nm, v) in enumerate(_LINES))
_TFC = tuple((i + 1, m, f, '%s   %s' % (nm, v))
             for i, (m, f, nm, v) in enumerate(_LINES))

S.h2('14c  The half line cycle, against every frequency limit')
S.const('[BUILD] sweep theta from [rad]:', 'th.lo', '%g' % _TLO, None, 3)
S.const('[BUILD] sweep theta to   [rad]:', 'th.hi',
        'π-%g' % _TLO, None, 3,
        note='not from 0 to pi: at the zero crossing the load is zero and the phase is '
             'degenerate, so the sweep starts just inside.')
S.const('[PICK] points along the half cycle:', 'N.th', str(_TN), None, 0)
S.const('[PICK] points along the frequency sweep:', 'N.fs', str(_TNF), None, 0)
S.area_begin('unit stripping - collapsed, nothing here is a design value')
S.row('- series resonance as a plain number [kHz]:', 'q.fr',
      "f.r/\'kHz", None, 2)
S.row('- frequency floor [kHz]:', 'q.fo', "f.o/\'kHz", None, 2)
S.row('- VCO clamp [kHz]:', 'q.fmn', "f.Min/\'kHz", None, 2)
S.row('- design ceiling [kHz]:', 'q.fsp', "f.sw_max_spec/\'kHz", None, 2)
S.row('- rated output power [W]:', 'q.po', "P.out/\'W", None, 1)
S.area_end()

S.area_begin('the vectors behind the three frames - collapsed')
S.prog(['k.th := range(1,N.th)'], label='- the phase range variable:', h=54, w=460)
S.prog(['el(th.g,k.th) := th.lo+(k.th-1)*(th.hi-th.lo)/(N.th-1)'],
       label='- the phase axis:', h=54, w=700)
S.prog(['el(sn.g,k.th) := sin(el(th.g,k.th))'],
       label='- sin(theta), used by both outer frames:', h=54, w=640)
S.prog(['el(tx.2,k.2) := th.lo+(k.2-1)*(th.hi-th.lo)'],
       label='- and its two ends, for the flat lines:', h=54, w=720)
for _i, _mv, _lbl in _TIN:
    S.prog(['el(rq.%d,k.th) := %s/el(sn.g,k.th)' % (_i, _mv)],
           label='- demanded gain at %s:' % _lbl, h=54, w=620)
for _i, _f in ((1, '1'), (2, '0.75'), (3, '0.5'), (4, '0.25')):
    S.prog(['el(pw.%d,k.th) := 2*q.po*%s'
            '*el(sn.g,k.th)*el(sn.g,k.th)' % (_i, _f)],
           label='- output power, %s of full load:' % _f, h=56, w=760)
for _n, _v, _q in (('hz.o', 'f.o', 'q.fo'), ('hz.n', 'f.Min', 'q.fmn'),
                   ('hz.r', 'f.r', 'q.fr'),
                   ('hz.s', 'f.sw_max_spec', 'q.fsp')):
    S.prog(['el(%s,k.2) := %s' % (_n, _q)],
           label='- the %s line:' % _v, h=54, w=480)

S.prog(['k.fs := range(1,N.fs)'],
       label='- the frequency range variable:', h=54, w=500)
S.prog(['el(uu.g,k.fs) := (k.fs-1)/(N.fs-1)'],
       label='- 0 to 1 across the sweep:', h=54, w=560)
S.prog(['el(tt.g,k.fs) := 1-abs(2*el(uu.g,k.fs)-1)'],
       label='- the tent: 0 up to 1 and back:', h=54, w=680)
S.prog(['el(sg.g,k.fs) := (2*el(uu.g,k.fs)-1)/abs(2*el(uu.g,k.fs)-1)'],
       label='- the sign: -1 going up, +1 coming back:', h=56, w=820)
for _i, _mv, _end, _lbl in _TFC:
    S.prog(['el(xn.%d,k.fs) := f.n0*1.0005'
            '+(%s*0.9999-f.n0*1.0005)*el(tt.g,k.fs)' % (_i, _end)],
           label='- f.n from the floor up to %s, at %s:' % (_end, _lbl),
           h=58, w=980)
    S.prog(['el(ga.%d,k.fs) := 1+λ.act'
            '-λ.act/(el(xn.%d,k.fs)*el(xn.%d,k.fs))' % (_i, _i, _i)],
           label='- the real part a:', h=56, w=820)
    S.prog(['el(gb.%d,k.fs) := el(xn.%d,k.fs)-1/el(xn.%d,k.fs)'
            % (_i, _i, _i)],
           label='- the reactive part b:', h=54, w=680)
    S.prog(['el(gd.%d,k.fs) := Q.pk*Q.pk*el(gb.%d,k.fs)*el(gb.%d,k.fs)'
            % (_i, _i, _i)],
           label='- Q.pk squared times b squared:', h=56, w=800)
    S.prog(['el(gn.%d,k.fs) := el(ga.%d,k.fs)*el(ga.%d,k.fs)'
            % (_i, _i, _i)],
           label='- a squared:', h=54, w=620)
    S.prog(['el(gm.%d,k.fs) := 1/(%s*%s)' % (_i, _mv, _mv)],
           label='- one over the required gain squared:', h=54, w=620)
    S.prog(['el(gs.%d,k.fs) := (el(gm.%d,k.fs)'
            '-sqrt(el(gm.%d,k.fs)*el(gm.%d,k.fs)'
            '-4*el(gd.%d,k.fs)*el(gn.%d,k.fs)))/(2*el(gd.%d,k.fs))'
            % (_i, _i, _i, _i, _i, _i, _i)],
           label='- sin(theta) squared, the minus root:', h=60, w=1000)
    S.prog(['el(gt.%d,k.fs) := π/2+el(sg.g,k.fs)*(π/2'
            '-atan(sqrt(el(gs.%d,k.fs))/sqrt(1-el(gs.%d,k.fs))))'
            % (_i, _i, _i)],
           label='- the phase itself:', h=56, w=760)
    S.prog(['el(gf.%d,k.fs) := q.fr*el(xn.%d,k.fs)' % (_i, _i)],
           label='- f.sw [kHz] at that phase:', h=54, w=620)
# derived from _TFC, not written out: a hard-coded (1, 2) here meant the
# third curve was fed to the pane and never built, and it drew as a flat
# zero
_TM = ([('Tf.%d' % i, 'gt.%d' % i, 'gf.%d' % i)
        for i, _m, _e, _l in _TFC]
       + [('Tr.%d' % i, 'th.g', 'rq.%d' % i)
          for i in range(1, len(_LINES) + 1)]
       + [('Tp.%d' % i, 'th.g', 'pw.%d' % i) for i in (1, 2, 3, 4)]
       + [('Th.%s' % k, 'tx.2', 'hz.%s' % k) for k in ('o', 'n', 'r', 'x', 's')])
for _n, _x, _y in _TM:
    S.prog(['%s := eval(augment(vectorize(%s),vectorize(%s)))' % (_n, _x, _y)],
           label='- two-column matrix %s:' % _n, h=56, w=780, allow=ZS.VEC)
S.area_end()

_TA = ZS.make(6, 'transfer',
              'Gain the converter must make, moment by moment through '
              'the line cycle',
              _TXT, 'demanded gain   M.req = M.pk / sin(theta)',
              ['M.req  @ %-14s %s' % (nm, v)
               for _m, _f, nm, v in _LINES],
              _TW, (0.0, 5.0), xlog=False, xsteps=(0.4, 0.1),
              ysteps=(0.5, 0.1), big=True, colors=_PAL_LIM9[:6],
              legendsize=10, widths=_W_ALL, size=(1580, ZS.fit(6)))
# nine traces: four input voltages and five frequency limits. The panes this
# project owns hold eight, so the pane is fed nine and grown by SMath on the
# next save - see harvest_pane.py. _FSWN is the only number to change once
# the nine-curve pane is in panes/.
_FSWLEG = ['f.sw  @ %-14s %s' % (nm, v)
           for _m, _f, nm, v in _LINES] + [
           'f.o           floor',
           'f.Min         VCO clamp',
           'f.r           series resonance',
           'f.sw_max_spec design ceiling']
# f.Max, the VCO ceiling, is deliberately NOT drawn. It sits half again
# above the highest trace and nothing else on the frame comes near it, so
# it alone set the y range and pressed six curves into the bottom of the
# frame. It is not lost: k.ceil reports the margin as a number, and
# f.sw_max_spec - which IS drawn - is the lower of the two ceilings, so
# clearing the drawn one clears the other.
_FSWN = 10
_TB = ZS.make(_FSWN, 'transfer',
              'Where the switching frequency goes through the line cycle, '
              'and what boxes it in',
              _TXT, 'switching frequency   f.sw [kHz]',
              _FSWLEG[:_FSWN],
              _TW, (0.0, 250.0), xlog=False, xsteps=(0.4, 0.1),
              ysteps=(50.0, 10.0), big=True, yauto=True, legendsize=8,
              colors=_PAL_LIM9[:_FSWN], widths=_W_FSW,
              size=(1580, ZS.fit(_FSWN)))
_TC = ZS.make(4, 'transfer',
              'Output power through the line cycle  -  it goes to zero '
              'twice every cycle',
              _TXT, 'output power   P(theta) [W]',
              ['100 % load', '75 %', '50 %', '25 %'],
              _TW, (0.0, 1400.0), xlog=False, xsteps=(0.4, 0.1),
              ysteps=(200.0, 50.0), big=True, colors=_PAL_LIM[:4],
              widths=_W_ALL[:4], size=(1580, ZS.fit(4)))
ZS.emit(S, ['Tr.%d' % (i + 1) for i in range(len(_LINES))], *_TA)
ZS.emit(S, ['Tf.1', 'Tf.2', 'Tf.3', 'Tf.4', 'Tf.5', 'Tf.6',
            'Th.o', 'Th.n', 'Th.r', 'Th.s'], *_TB)
ZS.emit(S, ['Tp.1', 'Tp.2', 'Tp.3', 'Tp.4'], *_TC)

# ==================================================================== 15
S.h2('15. Voltage Loop   [122] - [132]')
S.const('[DS] HV divider gain K.HV  [-]:', 'K.HV', '0.00334', None, 5)
S.const('[DS] Multiplier gain K.M  [1/V^2]:', 'K.M', '0.2', None, 3)
S.const('[DS] Feed-forward gain K.FF  [V^3]:', 'K.FF', '0.2', None, 3)
S.row('- FB power-command coefficient  [V/(ohm*W)]:', 'K.pwr',
      "2*K.HV/(K.M*K.FF)*'V/('ohm*'W)", None, 4)
S.row('- FB voltage at rated power:', 'V.FB',
      "K.pwr*R.CS*P.out/η.HB", 'V', 4)
S.row('- FB set point:', 'V.FB_set', "V.FB+0.5*'V", 'V', 4)
S.row('- Plant integrator gain [rad/s]:', 'G.o', "P.out/V.out/V.FB/C.out", None, 2,
      note='[125]  the unit is rad/s, NOT Hz.')
S.row('- Uncompensated crossover:', 'f.cto', "G.o/(2*π)", 'Hz', 2)
S.row('- Output ripple seen by the loop:', 'ΔV.loop',
      "P.out/V.out/(2*π*f.line_min)/C.out", 'V', 4)
S.const('- Allowed third harmonic [%]:', 'D.3rd', '5', None, 2)
S.row('- Required E/A gain at 2fL:', 'G.EA',
      "4*(V.FB_set-0.5*'V)*D.3rd/100/ΔV.loop", None, 4)
S.const('- Target phase margin [deg]:', 'Φ.M', '50', None, 1)
S.const('- Venable alpha:', 'α.v', '1.2', None, 2)
S.row('- tangent of the target phase margin:', 't.PM', TAN("Φ.M*π/180"), None, 4)
S.row('- K factor:', 'K.v',
      "1/(2*α.v)*((1+α.v^2)*t.PM+sqrt((1+α.v^2*t.PM)^2+4*α.v^2))", None, 4)
S.row('- Target E/A gain constant [rad/s]:', 'EA.o',
      "2*π*2*f.line_min*G.EA/K.v^2", None, 3)
S.row('- Input voltage margin factor:', 'Γ.v', "0.744*V.eq_ACmax/V.eq_min", None, 4)
S.row('- Geometric mean frequency:', 'f.MB',
      "1/(2*π)*sqrt(G.o*K.v*EA.o/Γ.v)", 'Hz', 3)
S.row('- Compensator pole:', 'f.pole', 'K.v*f.MB', 'Hz', 3)
S.row('- Compensator zero:', 'f.zero', 'f.MB/K.v', 'Hz', 3)

# ===================================================================== 16
S.h2('16. Compensation Network and Optocoupler Biasing   [133] - [148]')
_y0 = S.y
S.table(['symbol on the drawing', 'this sheet', 'equation', 'what fixes it'],
        [['R.I / R.O', 'R.I / R.o', '[142] [143]', 'output set point'],
         ['R.B', 'R.B', '[145] [146]', 'FB pin current window'],
         ['R.P', 'R.P', '[144]', 'shunt regulator minimum current'],
         ['C.Fo', 'C.Fo', '[133]', 'E/A gain constant'],
         ['C.f', 'C.F', '[134]', 'pole-to-zero spread'],
         ['R.f', 'R.F', '[135]', 'zero frequency'],
         ['C.fx', 'C.fx', '[136]', 'high-frequency pole, with C.opto'],
         ['TL43X', 'V.R, I.min', '[142] [144]', 'reference voltage and bias current'],
         ['V. REG / SEC AUX', 'V.Z', '[145] [146]', 'feedback supply rail']],
        widths=[145, 85, 85, 260])
_y1, S.y = S.y, _y0          # put the drawing beside the table, not under it
S.pic(FIG_COMP, x=612, w=430)
S.y = max(_y1, S.y)
S.const('[DS] FB pin internal resistance:', 'R.FB', "35*'kohm", 'kohm', 1)
S.const('[DS] FB steady-state current:', 'I.FB_steady', "150*'μA", 'μA', 1)
S.const('[DS] FB maximum current:', 'I.FB_max', "300*'μA", 'μA', 1)
S.const('[PICK] Feedback supply voltage:', 'V.Z', "12*'V", 'V', 1)
S.const('[PICK] Shunt regulator reference (TL431):', 'V.R', "2.495*'V", 'V', 3)
S.const('[PICK] Shunt regulator minimum current:', 'I.min', "0.8*'mA", 'mA', 2)
S.const('[PICK] Optodiode forward drop:', 'V.Fo', "1.15*'V", 'V', 3)
S.const('[PICK] Optocoupler CTR at steady state:', 'CTR.s', '0.37', None, 3)
S.const('[PICK] Optocoupler CTR at maximum current:', 'CTR.m', '0.53', None, 3)
S.const('[PICK] Optocoupler output capacitance:', 'C.opto', "3*'nF", 'nF', 2)
S.const('[PICK] Added high-frequency pole:', 'f.pHF', "1000*'Hz", 'Hz', 0)

S.h2('16.1  Output divider and optocoupler biasing   [142] - [146]')
S.const('[PICK] Upper divider resistor:', 'R.I', "100*'kohm", 'kohm', 1)
S.row('- Lower divider resistor:', 'R.o_calc', "V.R/(V.out-V.R)*R.I", 'kohm', 3)
S.const('[PICK] SELECTED lower divider resistor:', 'R.o', "11*'kohm", 'kohm', 1)
S.row('- Resulting regulated output:', 'V.out_act', "V.R*(R.I+R.o)/R.o", 'V', 3)
S.row('- Maximum photodiode parallel resistor:', 'R.P_max', "V.Fo/I.min", 'kohm', 3,
      note='[144]  R.P must be BELOW this.')
S.const('[PICK] SELECTED photodiode parallel resistor:', 'R.P', "1.3*'kohm", 'kohm', 2)
S.row('- Bias resistor upper bound:', 'R.B_max',
      "(V.Z-(V.R+V.Fo))/(V.Fo/R.P+I.FB_steady/CTR.s)", 'kohm', 3)
S.row('- Bias resistor lower bound:', 'R.B_min',
      "(V.Z-(V.R+V.Fo))/(V.Fo/R.P+I.FB_max/CTR.m)", 'kohm', 3,
      note='[145][146]  the DS 5.2.12 window.')
S.const('[PICK] SELECTED bias resistor:', 'R.B', "6.2*'kohm", 'kohm', 2)
S.row('- photodiode resistor check (>1):', 'k.RP', 'R.P_max/R.P', None, 3,
      note='[144]  a MAXIMUM, so round DOWN.')
S.row('- inside the window, lower check (>1):', 'k.RB_lo', 'R.B/R.B_min', None, 3)
S.row('- inside the window, upper check (>1):', 'k.RB_hi', 'R.B_max/R.B', None, 3)

S.h2('16.2  Compensation components   [133] - [136]')
S.row('- Calculated feedback capacitor C.Fo:', 'C.Fo_calc',
      "f.zero/f.pole*(CTR.s*R.FB)/(R.I*R.B*EA.o)", 'nF', 2)
S.const('[PICK] SELECTED C.Fo:', 'C.Fo', "82*'nF", 'nF', 1)
S.row('- Calculated feedback capacitor C.F:', 'C.F_calc',
      "C.Fo*(f.pole/f.zero-1)", 'nF', 1,
      note='[134]  computed from the SELECTED C.Fo, not from C.Fo_calc.')
S.const('[PICK] SELECTED C.F:', 'C.F', "560*'nF", 'nF', 1)
S.row('- Calculated feedback resistor R.F:', 'R.F_calc',
      "1/(2*π*f.zero*C.F)", 'kohm', 2)
S.const('[PICK] SELECTED R.F:', 'R.F', "47*'kohm", 'kohm', 1)
S.row('- Calculated FB pin capacitor C.fx:', 'C.fx_calc',
      "1/(2*π*f.pHF*R.FB)-C.opto", 'nF', 3)
S.const('[PICK] SELECTED C.fx:', 'C.fx', "1.55*'nF", 'nF', 2)

S.h2('16.3  What the selected parts actually implement   [137] - [140]')
S.area_begin('the compensator algebra - collapsed, the results are below')
S.row('- Implemented E/A gain constant [rad/s]:', 'EA.oi',
      "CTR.s*R.FB/((C.F+C.Fo)*R.I*R.B)", None, 3)
S.row('- Implemented zero:', 'f.zi', "1/(2*π*R.F*C.F)", 'Hz', 3)
S.row('- Series combination of C.F and C.Fo:', 'C.ser', "C.F*C.Fo/(C.F+C.Fo)", 'nF', 2)
S.row('- Implemented pole:', 'f.pi', "1/(2*π*R.F*C.ser)", 'Hz', 3)
S.row('- Implemented high-frequency pole:', 'f.pxi',
      "1/(2*π*R.FB*(C.opto+C.fx))", 'Hz', 1)
S.area_end()
S.show('- zero:', 'f.zi', 'Hz', 3)
S.show('- pole:', 'f.pi', 'Hz', 3)
S.show('- high-frequency pole:', 'f.pxi', 'Hz', 1)
S.show('- E/A gain constant [rad/s]:', 'EA.oi', None, 3)

S.h2('16.4  Loop verification without a solver   [141]')
S.pack([('ω.z', "2*π*f.zi"), ('ω.p', "2*π*f.pi"), ('ω.px', "2*π*f.pxi"),
        ('g.0', "G.o*EA.oi")])
S.area_begin('eight fixed-point steps - collapsed; only the result below matters')
prev = 'w.0'
S.row(None, 'w.0', "sqrt(g.0)", None, 5)
for i in range(1, 9):
    cur = f'w.{i}'
    S.pack([(f'A.{i}',
             f"sqrt(1+({prev}/ω.z)^2)"
             f"/(sqrt(1+({prev}/ω.p)^2)*sqrt(1+({prev}/ω.px)^2))", None, 6),
            (cur, f"sqrt(g.0*A.{i})", None, 5)], per=2)
    prev = cur
S.area_end()
S.area_begin('crossover and phase margin - collapsed, the results are below')
S.row('- Crossover frequency:', 'f.cross', "w.8/(2*π)", 'Hz', 3)
S.row('- Residual |T| at the crossover (must be ~1):', 'T.res',
      "g.0/w.8^2*sqrt(1+(w.8/ω.z)^2)"
      "/(sqrt(1+(w.8/ω.p)^2)*sqrt(1+(w.8/ω.px)^2))", None, 5)
S.row('- Phase margin [deg]:', 'Φ.act',
      "(atan(w.8/ω.z)-atan(w.8/ω.p)-atan(w.8/ω.px))*180/π", None, 2)
S.area_end()
S.show('- crossover frequency:', 'f.cross', 'Hz', 3)
S.show('- phase margin [deg]:', 'Φ.act', None, 2)
S.show('- residual |T| there (must be ~1):', 'T.res', None, 5)
S.row('- phase margin as a fraction of the target:', 'k.PM', 'Φ.act/Φ.M', None, 3,
      note='a value near 1 is the goal; 45 deg or more is acceptable in practice.')

S.h2('16.4b  Gain margin - also without a solver')
S.area_begin('where the phase reaches -180 deg - collapsed, the result is below')
S.row('- Frequency where arg T = -180 deg:', 'f.180',
      'sqrt(f.pi*f.pxi-f.zi*(f.pi+f.pxi))', 'Hz', 2)
S.row('- Angular frequency there:', 'ω.180', '2*π*f.180', None, 3)
S.row('- Loop gain at that frequency:', 'T.180',
      'g.0/ω.180^2*sqrt(1+(ω.180/ω.z)^2)'
      '/(sqrt(1+(ω.180/ω.p)^2)*sqrt(1+(ω.180/ω.px)^2))', None, 5)
S.row('- Gain margin [dB]:', 'GM', '-20*ln(T.180)/ln(10)', None, 2)
S.area_end()
S.show('- frequency where arg T = -180 deg:', 'f.180', 'Hz', 2)
S.show('- gain margin [dB]:', 'GM', None, 2)
S.const('[PICK] Gain margin target [dB]:', 'GM.t', '10', None, 0)
S.row('- gain margin check (>1):', 'k.GM', 'GM/GM.t', None, 3,
      note='6 dB is the usual floor, 10 dB comfortable. Normally very large here - but it '
           'has to be looked at, not assumed.')
S.row('- Angular frequency at 2fL:', 'ω.2fl', "2*π*2*f.line_min", None, 3)
S.row('- Actual E/A gain at 2fL:', 'G.EA_act',
      "EA.oi/ω.2fl*sqrt(1+(ω.2fl/ω.z)^2)"
      "/(sqrt(1+(ω.2fl/ω.p)^2)*sqrt(1+(ω.2fl/ω.px)^2))", None, 4)
S.row('- Actual third-harmonic distortion [%]:', 'D.3rd_act',
      "G.EA_act*ΔV.loop/(4*(V.FB_set-0.5*'V))*100", None, 3)
S.row('- distortion budget check (>1):', 'k.D3rd', 'D.3rd/D.3rd_act', None, 3)

S.h2('16.5  FB ripple against the burst threshold   [147] - [148]')
S.row('- FB ripple at the burst entry point:', 'ΔV.FBBM',
      "P.in_BM/V.out/(2*π*f.line_min)/C.out*G.EA_act", 'mV', 1)
S.row('- Suggested reduction of R.BM:', 'ΔR.BM',
      "ΔV.FBBM/(2*0.01*'V)*1000*'ohm", 'kohm', 3,
      note='[148]  lower R.BM by this much so the 2fL ripple on FB cannot chatter across '
           'the burst threshold.')
S.row('- Recommended R.BM:', 'R.BM_rec', 'R.BM_sel-ΔR.BM', 'kohm', 3)

# ---------------------------------------------------------------- 16.6
# Window ends are rounded outward to whole multiples of the tick step, so
# that every label is a round number and no curve is clipped. Computing them
# from the curve rather than fixing them means a variant with a different
# compensator still gets a frame that fits.
_BXLO, _BXHI, _BN = -1, 3, 241
_bqz = S.ns['f__zi']
_bqp = S.ns['f__pi']
_bqpx = S.ns['f__pxi']
_bqg = S.ns['G__o'] / (2 * math.pi)
_bqa = S.ns['EA__oi'] / (2 * math.pi)


def _bA(f):
    return (math.sqrt(1 + (f / _bqz) ** 2)
            / (math.sqrt(1 + (f / _bqp) ** 2) * math.sqrt(1 + (f / _bqpx) ** 2)))


_bf = [10.0 ** (_BXLO + i * (_BXHI - _BXLO) / 2000.0) for i in range(2001)]
_bgp = [20 * math.log10(_bqg / f) for f in _bf]
_bea = [20 * math.log10(_bqa / f * _bA(f)) for f in _bf]
_btl = [a + b for a, b in zip(_bgp, _bea)]
_bpm = [(math.atan(f / _bqz) - math.atan(f / _bqp) - math.atan(f / _bqpx))
        * 180 / math.pi for f in _bf]
_BDBLO = math.floor(min(_bgp + _bea + _btl) / 20.0) * 20.0
_BDBHI = math.ceil(max(_bgp + _bea + _btl) / 20.0) * 20.0
_BPMLO = math.floor(min(_bpm) / 20.0) * 20.0
_BPMHI = math.ceil(max(_bpm + [S.ns['Φ__M']]) / 20.0) * 20.0

S.h2('16.6  Bode plot of the loop   [141]')
S.const('[BUILD] Plot from log10(f/Hz) =', 'x.lo', '%d' % _BXLO, None, 0)
S.const('[BUILD] Plot to   log10(f/Hz) =', 'x.hi', '%d' % _BXHI, None, 0)
S.const('[PICK] Number of points:', 'N.bp', str(_BN), None, 0)
S.area_begin('unit stripping - collapsed, nothing here is a design value')
S.row('- compensator zero, as a plain number [Hz]:', 'q.z', "f.zi/'Hz", None, 4)
S.row('- compensator pole [Hz]:', 'q.p', "f.pi/'Hz", None, 3)
S.row('- high-frequency pole [Hz]:', 'q.px', "f.pxi/'Hz", None, 2)
S.row('- plant gain, expressed in Hz not rad/s:', 'q.g', "G.o/(2*π*'Hz)", None, 3)
S.row('- E/A gain, expressed in Hz not rad/s:', 'q.ea', "EA.oi/(2*π*'Hz)", None, 3)
S.area_end()

S.area_begin('the vectors behind the two frames - collapsed')
S.prog(['k.bp := range(1,N.bp)'], label='- the range variable:', h=54, w=420)
S.prog(['el(F.bp,k.bp) := 10^(x.lo+(k.bp-1)*(x.hi-x.lo)/(N.bp-1))'],
       label='- frequency [Hz], log spaced:', h=56, w=740)
S.prog(['el(A.bp,k.bp) := sqrt(1+(el(F.bp,k.bp)/q.z)^2)'
        '/(sqrt(1+(el(F.bp,k.bp)/q.p)^2)*sqrt(1+(el(F.bp,k.bp)/q.px)^2))'],
       label='- compensator shape A(f):', h=60, w=980)
S.prog(['el(Gp.bp,k.bp) := 20*ln(q.g/el(F.bp,k.bp))/ln(10)'],
       label='- plant |G.cto| [dB]:', h=56, w=700)
S.prog(['el(Ea.bp,k.bp) := 20*ln(q.ea/el(F.bp,k.bp)*el(A.bp,k.bp))/ln(10)'],
       label='- compensator |EA| [dB]:', h=56, w=820)
S.prog(['el(Tl.bp,k.bp) := el(Gp.bp,k.bp)+el(Ea.bp,k.bp)'],
       label='- loop |T| [dB], the sum of the two:', h=56, w=700)
S.prog(['el(Pm.bp,k.bp) := (atan(el(F.bp,k.bp)/q.z)-atan(el(F.bp,k.bp)/q.p)'
        '-atan(el(F.bp,k.bp)/q.px))*180/π'],
       label='- phase margin [deg]:', h=60, w=980)
S.prog(['el(bx.2,k.2) := 10^(x.lo+(k.2-1)*(x.hi-x.lo))'],
       label='- the two ends of the frequency axis:', h=56, w=760)
S.row('- crossover as a plain number [Hz]:', 'q.fc', "f.cross/\'Hz",
      None, 3)
S.prog(['el(Xc.bp,k.2) := q.fc'],
       label='- the crossover marker, x:', h=54, w=520)
# one marker serves both frames: drawn far past either window and clipped by
# each, so no second vector has to be kept in step with a window
S.prog(['el(Yc.bp,k.2) := -200+400*(k.2-1)'],
       label='- the crossover marker, y:', h=56, w=680)
S.prog(['el(Yt.bp,k.2) := Φ.M'],
       label='- the target-margin marker, y:', h=54, w=480)
for _bn, _bx, _by in (('B.loop', 'F.bp', 'Tl.bp'), ('B.plant', 'F.bp', 'Gp.bp'),
                      ('B.comp', 'F.bp', 'Ea.bp'), ('B.margin', 'F.bp', 'Pm.bp'),
                      ('B.xc', 'Xc.bp', 'Yc.bp'), ('B.tm', 'bx.2', 'Yt.bp')):
    S.prog(['%s := eval(augment(vectorize(%s),vectorize(%s)))' % (_bn, _bx, _by)],
           label='- two-column matrix %s:' % _bn, h=56, w=800, allow=ZS.VEC)
S.area_end()

_BXT = 'frequency   f [Hz]   (logarithmic)'
# Two panes share this row, so each is half as wide, and a frame that is
# taller than it is wide reads as a tower. The full-width frames take the
# whole page band; these take what suits 780 px of width.
_TWOUP = min(ZS.fit(4), 640)

_BB, _BW, _BH = ZS.make(
    4, 'transfer',
    'Voltage loop  -  gain, and where it runs out',
    _BXT, 'gain   [dB]',
    ['|T|       loop',
     '|G.cto|   plant',
     '|EA|      compensator',
     'f.cross   crossover'],
    (10.0 ** _BXLO, 10.0 ** _BXHI), (_BDBLO, _BDBHI),
    xlog=True, logstep=1.0, ysteps=(20.0, 4.0), colors=_PAL_BODE,
    size=(780, _TWOUP))
_MB, _MW, _MH = ZS.make(
    3, 'transfer',
    # ZedGraph centres a pane title and lets it run off both ends, and the
    # pane is 780 wide now - the long form was clipped at both edges. What
    # it used to say is in the note under the frame, where it has room.
    'Voltage loop  -  phase, and how close it is to -180 deg',
    _BXT,
    'distance from -180 deg   [deg]',
    ['180 deg + arg T',
     'f.cross   crossover - read the margin here',
     'Phi.M     target'],
    (10.0 ** _BXLO, 10.0 ** _BXHI), (_BPMLO, _BPMHI),
    xlog=True, logstep=1.0, ysteps=(20.0, 4.0), colors=_PAL_PHASE,
    size=(780, _TWOUP))
ZS.emit(S, ['B.loop', 'B.plant', 'B.comp', 'B.xc'], _BB, _BW, _BH,
        x=20, advance=False)
# second pane of the row: it must not ask for the lead again
ZS.emit(S, ['B.margin', 'B.xc', 'B.tm'], _MB, _MW, _MH,
        x=_BW + 40, advance=True, reserve=4, lead=False)

S.area_begin('five decade anchor points - |T| and phase margin as plain scalars')
for _i, _fq in enumerate(['0.1', '1', '10', '100', '1000'], 1):
    S.pack([(f'wa.{_i}', f"2*π*{_fq}*'Hz", None, 3),
            (f'Aa.{_i}',
             f"sqrt(1+(wa.{_i}/ω.z)^2)"
             f"/(sqrt(1+(wa.{_i}/ω.p)^2)*sqrt(1+(wa.{_i}/ω.px)^2))", None, 5),
            (f'Ta.{_i}', f"20*ln(G.o*EA.oi/wa.{_i}^2*Aa.{_i})/ln(10)", None, 2),
            (f'Ma.{_i}',
             f"(atan(wa.{_i}/ω.z)-atan(wa.{_i}/ω.p)"
             f"-atan(wa.{_i}/ω.px))*180/π", None, 2)], per=4)
S.area_end()

# 16.7 (what this sheet does differently from the ST spreadsheet) and 18
# (what each assumption costs) were commentary on other documents and on
# choices, with computed values quoted in prose. Deleted: the sheet makes
# the design, the guide explains it.
S.h2('17. Design Review')
for lbl, var, un, dp in [
        ('- Rated input power:', 'P.in', 'W', 1),
        ('- Equivalent input range, low:', 'V.eq_min', 'V', 2),
        ('- Equivalent input range, high:', 'V.eq_FBthr', 'V', 2),
        ('- Resonant capacitor:', 'C.r', 'nF', 1),
        ('- Resonant inductor:', 'L.r', 'μH', 2),
        ('- Magnetizing inductance:', 'L.m', 'μH', 2),
        ('- Actual lambda:', 'λ.act', None, 4),
        ('- Wound turns ratio:', 'n.T_act', None, 4),
        ('- Series resonant frequency:', 'f.r', 'kHz', 2),
        ('- Frequency floor:', 'f.o', 'kHz', 2),
        ('- Maximum operating frequency:', 'f.sw_max_op', 'kHz', 2),
        ('- ZVS margin (>1):', 'k.ZVS', None, 3),
        ('- Peak secondary current:', 'I.sec_pk', 'A', 2),
        ('- Composite tank peak:', 'I.Lr_pk', 'A', 3),
        ('- OCP1 margin (>1):', 'k.OCP', None, 3),
        ('- Peak flux density:', 'B.pk', 'mT', 1),
        ('- Core area margin (>1):', 'k.Ae', None, 3),
        ('- Vendor DC-overlap test current:', 'I.sat_spec', 'A', 1),
        ('- Output capacitance:', 'C.out', 'mF', 2),
        ('- Output ripple [% pk-pk]:', 'ΔV.out_pc', None, 2),
        ('- Hold-up margin (>1):', 'k.hold', None, 3),
        ('- Output capacitor rms current:', 'I.Cout_rms', 'A', 2),
        ('- VCO ceiling margin (>1):', 'k.ceil', None, 3),
        ('- VCO floor ratio (>1):', 'k.floor', None, 3)]:
    S.show(lbl, var, un, dp)


S.h2('17.1  Every verdict in one place')
S.note('All of these must be greater than 1. Each line is the ratio itself, '
       'then what to change if it fails.')
S.note('TWO OF THEM CANNOT BE READ THAT WAY. k.auxr asks whether the '
       'auxiliary winding, wired STRAIGHT to VCC, stays under the 25 V rating; '
       'here a Zener regulator sits in between and k.VCC asks the same '
       'question of its output - see section 14. k.lam is a NO-LOAD gain '
       'condition, and the hardware limit it stands in for is k.ceil. Every '
       'other row is a real test, and the text beside it is what to change '
       'when it reads below 1.')

S.h2('       power stage')
for lbl, var in [('T.ZC_min / t.D            raise L.m or lower Q', 'k.ZVS'),
                 ('t.D / T.T                 raise t.D', 'k.TT'),
                 ('I.OCP1 / I.Lr_pk          lower R.CS', 'k.OCP'),
                 ('R.CS_max / R.CS           fewer or smaller resistors', 'k.RCS'),
                 ('N.RCS / N.RCS_req         more sense resistors', 'k.NRCS'),
                 ('t.hold_act / t.holdup     more C.out', 'k.hold'),
                 ('R.Nmax / R.Nact           more ceramic', 'k.RN'),
                 ('C.in_sel / C.in           larger C.in_sel', 'k.Cin'),
                 ('P.mos_budget / P.mos_dc   lower R.dson_p25 or raise n.par',
                  'k.Ploss'),
                 ('P.SR_budget / P.SR_leg    lower R.dson_s25 or raise n.SR',
                  'k.PSR'),
                 ('A.e / A.e_req            bigger core or more N.s',
                  'k.Ae'),
                 ('lambda.act / lambda       NO LOAD only - see the note',
                  'k.lam')]:
    S.show('- ' + lbl, var, None, 3)

S.h2('       oscillator and VCO')
for lbl, var in [('f.Max / f.sw_max_op       lower R.T', 'k.ceil'),
                 ('f.Min / f.o               lower R.T', 'k.floor'),
                 ('R.T_ceil / R.T            lower R.T', 'k.RTd'),
                 ('C.T inside C.T_min..C.T_max', 'k.CTd'),
                 ('R.T / 5 kohm              DS minimum', 'k.RT_lo'),
                 ('30 kohm / R.T             DS maximum', 'k.RT_hi'),
                 ('C.T / 270 pF              DS minimum', 'k.CT_lo'),
                 ('1000 pF / C.T             DS maximum', 'k.CT_hi'),
                 ('R.T*C.T / 2.5 us          DS minimum', 'k.tau_lo'),
                 ('12 us / R.T*C.T           DS maximum', 'k.tau_hi'),
                 ('675 kHz / f.SU            DS ceiling', 'k.SU'),
                 ('675 kHz / f.Max           DS ceiling', 'k.675'),
                 ('t.D / 40 ns               DS minimum dead time', 'k.ADT_lo'),
                 ('420 ns / t.D              DS maximum dead time', 'k.ADT_hi'),
                 ('t.on_min / 370 ns         DS minimum pulse', 'k.pulse')]:
    S.show('- ' + lbl, var, None, 3)

S.h2('       supervision and auxiliary')
for lbl, var in [('V.AC_min / V.BO_act       smaller R.CFG', 'k.BO'),
                 ('R.CFG_sel / 15 kohm       morphing window', 'k.CFG_lo'),
                 ('47 kohm / R.CFG_sel       morphing window', 'k.CFG_hi'),
                 ('n.aux_max / n.aux        DIRECT FEED ONLY - see 14',
                  'k.auxr'),
                 ('25 V / V.CC_reg_max       lower V.DZ_sel', 'k.VCC'),
                 ('V.CC_reg_min / 12 V       raise V.DZ_sel', 'k.VCClo'),
                 ('R.BZ_max / R.BZ_sel       smaller R.BZ_sel', 'k.RBZ'),
                 ('C.VCC_sel / C.VCC_req     larger C.VCC_sel', 'k.CVCC'),
                 ('120 ms / t.hand           hold the load off longer',
                  'k.thand'),
                 ('V.OVP1_act / V.OVP1_out   against target, near 1',
                  'k.OVP1')]:
    S.show('- ' + lbl, var, None, 3)

S.h2('       control loop')
for lbl, var in [('Phi.act / Phi.M           45 deg or more passes', 'k.PM'),
                 ('GM / GM.t                 gain margin', 'k.GM'),
                 ('D.3rd / D.3rd_act         lower EA.o', 'k.D3rd'),
                 ('R.B / R.B_min             DS window', 'k.RB_lo'),
                 ('R.B_max / R.B             DS window', 'k.RB_hi'),
                 ('R.P_max / R.P             a MAXIMUM, round down',
                  'k.RP')]:
    S.show('- ' + lbl, var, None, 3)




S.h2('19. BOM - every line is a LIVE reference')
S.note('Nothing here is typed in - each row echoes the variable that produced it.')

S.h2('19.1  Resonant tank and magnetics')
S.show('- Resonant capacitor:', 'C.r', 'nF', 1)
S.show('- Resonant inductor:', 'L.r', 'μH', 2)
S.show('- Magnetizing inductance:', 'L.m', 'μH', 2)
S.show('- Open-circuit inductance to specify:', 'L.open', 'μH', 2)
S.show('- Short-circuit inductance to specify:', 'L.short', 'μH', 2)
S.show('- Equivalent-model turns ratio:', 'n', None, 3)
S.show('- Wound turns ratio:', 'n.T_act', None, 3)
S.show('- Transformers in the series string:', 'N.x', None, 0)
S.show('- Primary turns per transformer:', 'N.p', None, 0)
S.show('- Secondary half-winding turns:', 'N.s', None, 0)
S.show('- Auxiliary to secondary turns ratio:', 'n.aux', None, 2)
S.show('- Auxiliary turns in series, all cores:', 'N.aux', None, 0)
S.show('- Inductance factor per core:', 'A.L', 'nH', 1)

S.h2('19.2  Input and output capacitors - single, count, TOTAL')
S.show('- Input film capacitor, calculated:', 'C.in', 'nF', 0)
S.show('- Input film capacitor, SELECTED:', 'C.in_sel', 'nF', 0)
S.show('- Output electrolytic, single:', 'C.single', 'μF', 0)
S.show('- Output electrolytic, count:', 'n.C', None, 0)
S.show('- Output electrolytic, TOTAL:', 'C.out', 'mF', 2)
S.show('- Output ceramic, high frequency:', 'C.ceramic', 'μF', 1)
S.show('- ESR of one electrolytic:', 'ESR.single', 'mohm', 1)
S.show('- ESR of the bank:', 'ESR.out', 'mohm', 4)
S.show('- Ripple current in the bank:', 'I.Cout_rms', 'A', 2)
S.show('- Ripple current per capacitor:', 'I.Cout_each', 'A', 3)

S.h2('19.3  Current sense')
S.show('- Single sense resistor:', 'R.CS_single', 'mohm', 1)
S.show('- Number in parallel:', 'N.RCS', None, 0)
S.show('- Resulting sense resistance:', 'R.CS', 'mohm', 2)
S.show('- Dissipation per resistor, worst switching cycle:', 'P.RCS_each_pk', 'W', 3)

S.h2('19.4  Compensation network and output divider')
S.show('- Feedback capacitor C.Fo:', 'C.Fo', 'nF', 1)
S.show('- Feedback capacitor C.F:', 'C.F', 'nF', 1)
S.show('- Feedback resistor R.F:', 'R.F', 'kohm', 1)
S.show('- FB pin capacitor C.fx:', 'C.fx', 'nF', 2)
S.show('- Output divider, upper:', 'R.I', 'kohm', 1)
S.show('- Output divider, lower:', 'R.o', 'kohm', 1)
S.show('- Photodiode parallel resistor:', 'R.P', 'kohm', 2)
S.show('- Optocoupler bias resistor:', 'R.B', 'kohm', 2)
S.show('- Feedback supply rail:', 'V.Z', 'V', 1)

S.h2('19.5  L6790A pin components')
S.show('- Lower ZCD resistor, SELECTED:', 'R.ZCD_L_sel', 'kohm', 1)
S.show('- Upper ZCD resistor, SELECTED:', 'R.ZCD_H_sel', 'kohm', 1)
S.show('- VCO timing capacitor:', 'C.T', 'pF', 0)
S.show('- VCO timing resistor:', 'R.T', 'kohm', 1)
S.show('- Burst-mode resistor, SELECTED:', 'R.BM_sel', 'kohm', 1)
S.show('- CFG resistor, SELECTED:', 'R.CFG_sel', 'kohm', 1)
S.show('- Input film capacitor, SELECTED:', 'C.in_sel', 'nF', 0)
S.show('- VCC regulator Zener, SELECTED:', 'V.DZ_sel', 'V', 1)
S.show('- Zener tolerance grade:', 'tol.DZ', None, 3)
S.show('- Zener feed resistor, SELECTED:', 'R.BZ_sel', 'ohm', 0)
S.show('- Zener power rating, at least:', 'P.DZ', 'mW', 0)
S.show('- VCC capacitor, SELECTED:', 'C.VCC_sel', 'μF', 0)

S.h2('19.6  Semiconductors - the REQUIREMENT each part has to meet')
S.table(['function', 'designator', 'device class and count'],
        [['HVSU connecting diodes', '-', '2 x, 1000 V, low leakage'],
         ['Input bridge rectifier', '-', '1 x, see 19.4 for Vf and rd'],
         ['Primary switches', 'HVG1 HVG2 LVG1 LVG2',
          '4 positions x n.par, superjunction'],
         ['Centre-tap rectifiers', 'D1 D2', '2 legs x n.SR, SR MOSFET'],
         ['VCC rectifier and bypass diodes', 'D.aux D.byp',
          '2 x, rated above V.Caux_OVP2'],
         ['VCC pass transistor', 'Q.VCC',
          '1 x NPN, beta >= beta.min, P >= P.Qpass'],
         ['Feedback optocoupler', '-', '1 x, CTR binned - see 16.5'],
         ['External error amplifier', '-', '1 x, 2.5 V shunt regulator']],
        widths=[430, 260, 230])
S.show('- Primary: devices in parallel per position:', 'n.par', None, 0)
S.show('- Primary: minimum drain-source voltage:', 'V.DS_pri', 'V', 1)
S.show('- Primary: peak current rating per POSITION:', 'I.pri_rating', 'A', 2)
S.show('- Primary: peak current in ONE device:', 'I.pk_dev', 'A', 2)
S.show('- Primary: rms current in ONE device:', 'I.mos_dev', 'A', 3)
S.show('- Primary: required RDSon per DEVICE at Tj,max:', 'R.dson_req_dev_p',
       'mohm', 1)
S.show('- Primary: the same, as a 25 C datasheet number:', 'R.dson_req_25_p',
       'mohm', 1)
S.show('- Primary: largest admissible Coss:', 'C.oss_max', 'pF', 0)
S.show('- Secondary: devices in parallel per leg:', 'n.SR', None, 0)
S.show('- Secondary: recommended drain-source voltage:', 'V.DS_sec_rec', 'V', 1)
S.show('- Secondary: peak current rating per LEG:', 'I.sec_rating', 'A', 1)
S.show('- Secondary: peak current in ONE device:', 'I.SR_pk_dev', 'A', 1)
S.show('- Secondary: rms current in ONE device:', 'I.SR_dev', 'A', 2)
S.show('- Secondary: required RDSon per DEVICE at Tj,max:', 'R.dson_req_dev',
       'mohm', 2)
S.show('- Secondary: the same, as a 25 C datasheet number:', 'R.dson_req_25_s',
       'mohm', 2)
S.show('- VCC pass transistor: power to dissipate:', 'P.Qpass', 'W', 2)
S.show('- VCC pass transistor: V.CE it must block:', 'V.Caux_OVP2', 'V', 1)
S.show('- Optocoupler: CTR at steady state:', 'CTR.s', None, 3)
S.show('- Shunt regulator: reference voltage:', 'V.R', 'V', 3)

S.h2('19.7  Schematics')
S.note('HVSU on the AC side of the bridge. Nothing on CFG, BM, DRV_EN or RT. No filter on ISEN.')
# geometry set by hand in SMath and folded back in, so a rebuild keeps it
S.pic(FIG_POWER, x=81, w=595)
S.pic(FIG_PINS, x=756, w=770, same_row=True)

if S.clashes:
    print('  ** one name, two quantities - the later assignment wins '
          'and the earlier rows keep printing the old value:')
    for nm, a, b in S.clashes:
        print('     %-14s %-14g -> %g' % (nm, a, b))
    raise SystemExit(1)
nbytes, ybottom = S.save(OUT)
# a ZedGraph region needs its assembly in <dependencies> or the file will not
# open at all - SMath throws before it reaches the region
if ZS.declare(OUT):
    nbytes = os.path.getsize(OUT)
print(f'written {OUT}\n  {nbytes} bytes, {ybottom} px tall, '
      f'{ybottom/(S.PAGE_H-2*S.MARGIN):.1f} A3-landscape pages, {len(S.r)} regions')

# ------------------------------------------------------------------ self-check
print('\n--- cross-check against the reference implementation (l6790.py) ---')
R = design(Vout=25., Pout=657.5, Vo_min=19., dv_out=0.05, Thold=12e-3, Nrect=1,
           fr_t=150e3, fsw_max_spec=225e3, fsw_min_spec=50e3,
           c_HB=800e-12, tD=220e-9, n_sel=V['n'],
           Cr_sel=V['Cr'] * 1e-9, Lr_sel=V['Lr'] * 1e-6, Lm_sel=V['Lm'] * 1e-6)
_, Sa = sweep(R, R['Vin_min'])
_, Sb = sweep(R, R['Vin_FBmax'])
checks = [
    ('P.in', R['Pin'], 'W'), ('V.eq_min', R['Vin_min'], 'V'),
    ('M.HBmin', R['MVmin'], '-'), ('λ', R['lam'], '-'), ('R.ac', R['Rac'], 'ohm'),
    ('Q.ZVS', R['Qz'], '-'), ('λ.act', R['lam_a'], '-'), ('n.T', R['nT'], '-'),
    ('f.r', R['fr'], 'Hz'), ('f.o', R['fo'], 'Hz'), ('Q.pk', R['Qpk'], '-'),
    ('f.sw.a', Sa['fsw_max'], 'Hz'), ('f.sw.b', Sb['fsw_max'], 'Hz'),
    ('T.ZC.a', Sa['Tzc_min'], 's'), ('I.sec_pk', Sa['Isec_pk'], 'A'),
    ('I.trafo_pk', Sa['Itr_pk'], 'A'), ('I.Lm_pk', Sa['ILm_pk'], 'A'),
    ('I.Lr_pk', Sa['comp_pk'], 'A'), ('I.pri_rms', Sa['Ipri_pk'], 'A'),
    ('I.Cout_rms', Sa['ICout'], 'A'),
    ('I.diode_lc', Sa['Idio_lc'], 'A'), ('I.pri_lc', Sa['Ipri_lc'], 'A'),
]
bad = 0
for name, ref, unit in checks:
    got = S.ns[name.replace('.', '__')]
    tol = 1.5e-2 if name in ('I.Cout_rms', 'I.diode_lc', 'I.pri_lc') else 2e-4
    ok = abs(got - ref) <= max(abs(ref) * tol, 1e-12)
    bad += 0 if ok else 1
    print(f'  {name:12s} sheet={got:<14.6g} ref={ref:<14.6g} {unit:4s} '
          f'{"OK" if ok else "** DIFF"}')
print(f'  mismatches: {bad}')
