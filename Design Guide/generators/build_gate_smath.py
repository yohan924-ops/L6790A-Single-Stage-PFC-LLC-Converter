# -*- coding: utf-8 -*-
"""Builds  Smath/tools/L6790A_gatedrive.sm  -  the gate-drive and start-up check sheet.

It is the SMath twin of what gate_xl.py put into the workbooks on 2026-10-22 (user: "make a
new SMath sheet to match the new Excel"):

    Power Components   76-83     switch gate data
    Power Components   89-174    LLC Half Bridge Gate Driver Selection (driver, diodes,
                                 network limits and selections, results with checks)
    Res. Tank Design   81-87     start-up tank current and its OCP margins
    CC                 77-167    the working rows behind them

Same formulas, same names (SMath spelling: R.off.eff -> R.eff, dV/dt.max -> dVdt.max), same
order as the workbook except for one thing SMath forces: it evaluates top to bottom, so the
SIX selected values (V.drv, R.on, R.off, C.gs, C.boot, R.boot) are entered first and the
limits that depend on them follow as checks. In the workbook the limit and the selection sit
side by side and Excel resolves the mutual references.

What the sheet cannot do that the workbook does:
  - the E12 / E6 rounding of a recommendation (LOOKUP): the sheet prints the value before
    rounding and says which E-series value the workbook picks;
  - IF branches: the sheet is written for the design as built - a turn-off diode fitted
    (V.F.off > 0, R.off > 0), V.drv above 10 V, V.drv - V.F.boot above V.bo.min, a driver
    whose output resistance is taken from its short-circuit current. The two IF's that
    change a limit (Miller criterion dropped when C.gs alone holds the gate; C.gs needed
    only when the kick exceeds V.th.min) are kept exactly with a step built from abs().
Only sqrt, abs, ln, exp, atan, cos, sin are used (MIN / MAX / TAN rewritten as in the main
sheet builder). Inputs are the guide design point (GUIDE_PQ50_657W workbook).

Run:  python build_gate_smath.py        -> VERDICT at the end must read  mismatches: 0
      python check_sm.py ../../Smath/tools/L6790A_gatedrive.sm   -> VERDICT OK
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smsheet import Sheet                                          # noqa: E402


def MIN(a, b, u=None):
    """(a + b - |a - b|) / 2. Both arguments and the result are bracketed, because the
    arguments here are often sums (R.so/x.need - R.so - R.gi) and the result is divided
    into or by something - the main-sheet form without brackets silently mis-scopes both."""
    a, b = "(%s)" % a, "(%s)" % b
    d = "%s/'%s-%s/'%s" % (a, u, b, u) if u else "%s-%s" % (a, b)
    t = "abs(%s)" % d + ("*'%s" % u if u else "")
    return "((%s+%s-%s)/2)" % (a, b, t)


def MAX(a, b, u=None):
    a, b = "(%s)" % a, "(%s)" % b
    d = "%s/'%s-%s/'%s" % (a, u, b, u) if u else "%s-%s" % (a, b)
    t = "abs(%s)" % d + ("*'%s" % u if u else "")
    return "((%s+%s+%s)/2)" % (a, b, t)


def TAN(x):
    return "sin(%s)/cos(%s)" % (x, x)


def STEP(x):
    """1 when x > 0, 0 when x < 0 (x a plain number, never 0 at the design point)"""
    return "(1+(%s)/abs(%s))/2" % (x, x)


def LNV(num, den):
    """ln of a ratio of two voltages, de-unitised as the rules require"""
    return "ln(((%s)/'V)/((%s)/'V))" % (num, den)


OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'Smath', 'tools', 'L6790A_gatedrive.sm'))
S = Sheet('L6790A gate drive and start-up', 'L6790A project',
          'gate driver selection and start-up check - twin of the workbook rows')

S.h1('L6790A gate drive and start-up check  -  twin of Power Components 76-83, 89-174 '
     'and Res. Tank Design 81-87')
S.note('Every row here is a row of the GUIDE_PQ50_657W workbook (gate_xl.py, 2026-10-22), '
       'same formula and same name. Yellow cells are the inputs; the six selected values '
       'come FIRST because SMath evaluates top to bottom, and their limits follow as checks. '
       'k.* rows are margins and read OK at 1 or above. Functions used: sqrt, abs, ln, exp, '
       'atan, cos, sin - min/max are the abs() forms of the main sheet.')

# ------------------------------------------------------------------ 1. design inputs
S.h2('1  Design inputs (Device Setting D27 D29, Design Spec D14 D46 D47, '
     'Res. Tank Design, Power Components D68)')
S.const('[XL] Maximum input voltage:', 'V.AC_max', "264*'V", 'V', 0)
S.const('[XL] Resonant capacitor C.r:', 'C.r', "180*'nF", 'nF', 0)
S.const('[XL] Resonant inductance L.r:', 'L.r', "25*'μH", 'μH', 1)
S.const('[XL] Current sense resistor R.CS:', 'R.CS', "24*'mohm", 'mohm', 1)
S.const('[XL] Maximum (VCO) switching frequency f.Max:', 'f.Max', "285.5931*'kHz", 'kHz', 2,
        note='Device Setting D27 - set by R.T 21.5 kohm and C.T 470 pF in the main sheet.')
S.const('[XL] Start-up frequency f.SU:', 'f.SU', "476.4035*'kHz", 'kHz', 2,
        note='Device Setting D29.')
S.const('[XL] Half-bridge midpoint capacitance c.HB:', 'c.HB', "3028.98*'pF", 'pF', 1,
        note='Design Spec D46 - two STO60N045DM9 C.oss plus the stray, after fet_xl.py.')
S.const('[XL] Design dead time t.D:', 't.D', "220*'ns", 'ns', 0)
S.const('[XL] Peak magnetizing current I.Lm.pk at f.Max:', 'I.Lm_pk', "11.1320*'A", 'A', 3,
        note='Res. Tank Design D73.')
S.const('[XL] Devices in parallel per switch position n.par:', 'n.par', '1', None, 0)
S.row('- Series resonant frequency:', 'f.r', "1/(2*π*sqrt(L.r*C.r))", 'kHz', 2)
S.row('- Tank characteristic impedance:', 'Z.0', "sqrt(L.r/C.r)", 'ohm', 3)
S.row('- OCP1 trip current:', 'I.OCP1', "0.55*'V/R.CS", 'A', 2)
S.row('- OCP2 trip current:', 'I.OCP2', "0.75*'V/R.CS", 'A', 2)
S.row('- Highest bus, sqrt(2) x VAC.max:', 'V.bus', "sqrt(2)*V.AC_max", 'V', 2)

S.h2('2  L6790A figures the rows assume (CC 78-82)')
S.const('[DS] HOUT / LOUT high level, min (V.OH):', 'V.OH', "4*'V", 'V', 1)
S.const('[ASSUMED] D.boot dynamic resistance at the surge:', 'R.d_boot', "0.5*'ohm", 'ohm', 2)
S.const('[ASSUMED] Dead time at start-up, before ADT acts:', 't.D_su', "420*'ns", 'ns', 0,
        note='the DRAFT datasheet gives none; 420 ns is the value the bench start-up capture '
             'is consistent with. Replace when ST confirms.')
S.const('[DS] Maximum operating frequency (about 675 kHz):', 'f.IC', "675*'kHz", 'kHz', 0)
S.const('[DS] Highest FB bus = HB/FB morphing threshold V.HVPK_BOH:', 'V.bus_FB', "235*'V",
        'V', 0)
S.const('[DS] L6498 floating quiescent current I.QBO:', 'I.QBO', "120*'μA", 'μA', 0)

# ------------------------------------------------------------------ 3. switch gate data
S.h2('3  Switch gate data - STO60N045DM9 (Power Components 76-83)')
S.const('[DS] Gate capacitance above the plateau, Q.g slope:', 'C.g', "7.5*'nF", 'nF', 2)
S.const('[DS] Gate-source capacitance C.iss - C.rss:', 'C.gs_dev', "4.76*'nF", 'nF', 2)
S.const('[DS] Internal gate resistance:', 'R.g', "4.5*'ohm", 'ohm', 1)
S.const('[DS] Miller plateau voltage:', 'V.pl', "6.3*'V", 'V', 1)
S.const('[DS] Gate threshold, typ.:', 'V.th', "4.0*'V", 'V', 1)
S.const('[DS] Gate threshold, min.:', 'V.th_min', "3.5*'V", 'V', 1)
S.const('[DS] Miller charge over the bus swing [nC]:', 'Q.gd', '13', None, 0,
        note='a plain number in nC; the rows below put 10^-9 A*s back on.')
S.const('[DS] Gate-source voltage rating:', 'V.gs_max', "20*'V", 'V', 0)

# ------------------------------------------------------------------ 4. driver and diodes
S.h2('4  Gate driver data - L6498LD (Power Components 92-112)')
S.const('[DS] Source current, min:', 'I.so', "1.4*'A", 'A', 2)
S.const('[DS] Sink current, min:', 'I.si', "1.55*'A", 'A', 2)
S.const('[DS] Test supply voltage for I.so, I.si:', 'V.test', "15*'V", 'V', 0)
S.row('- Source resistance from the short-circuit current:', 'R.so_sc', 'V.test/I.so', 'ohm', 2)
S.row('- Sink resistance from the short-circuit current:', 'R.si_sc', 'V.test/I.si', 'ohm', 2)
S.const('[PICK] Output resistance in use, source:', 'R.so', 'R.so_sc', 'ohm', 2,
        note='the workbook row R.o.src: type the datasheet value here when the driver gives one.')
S.const('[PICK] Output resistance in use, sink:', 'R.si', 'R.si_sc', 'ohm', 2)
S.const('[DS] Supply voltage, min:', 'V.cc_min', "10*'V", 'V', 0)
S.const('[DS] Supply voltage, max:', 'V.cc_max', "20*'V", 'V', 0)
S.const('[DS] Propagation delay:', 't.pd', "85*'ns", 'ns', 0)
S.const('[DS] Delay matching, max:', 'MT', "30*'ns", 'ns', 0)
S.const('[DS] Internal dead time (0 = none):', 't.DT', "0*'ns", 'ns', 0)
S.const('[DS] Maximum switching frequency:', 'f.max_drv', "800*'kHz", 'kHz', 0)
S.const('[DS] Quiescent current, max:', 'I.Q', "0.6*'mA", 'mA', 2)
S.const('[DS] Thermal resistance junction-ambient [C/W]:', 'R.th_drv', '120', None, 0)
S.const('[DS] Junction temperature, max [C]:', 'T.j_max', '125', None, 0)
S.const('[DS] Bootstrap supply, min:', 'V.bo_min', "9.3*'V", 'V', 1)
S.const('[DS] HS pin dV/dt immunity [V/ns]:', 'dVdt.max', '50', None, 0)
S.const('[DS] HS pin voltage rating:', 'V.hs_max', "480*'V", 'V', 0)
S.const('[DS] Logic input high, max:', 'V.IH_max', "2.5*'V", 'V', 1)
S.const('[PICK] Operating ambient temperature of the driver [C]:', 'T.a_drv', '25', None, 0,
        note='set it to the temperature inside the set - 25 is the workbook default.')

S.h2('5  Bootstrap diode ES1J and turn-off diode 1N4148W (Power Components 113-123)')
S.const('[DS] D.boot forward voltage:', 'V.F_boot', "1.3*'V", 'V', 2)
S.const('[DS] D.boot repetitive reverse voltage:', 'V.RRM_boot', "600*'V", 'V', 0)
S.const('[DS] D.boot average forward current:', 'I.F_boot', "1.0*'A", 'A', 2)
S.const('[DS] D.boot surge current, 8.3 ms:', 'I.FSM_boot', "30*'A", 'A', 1)
S.const('[DS] D.off forward voltage (0 = no diode, GOFF pin):', 'V.F_off', "0.7*'V", 'V', 2,
        note='this sheet is written for a diode fitted (V.F.off > 0, R.off > 0) - the '
             'GOFF-pin branch of the workbook IF is not here.')
S.const('[DS] D.off average forward current:', 'I.F_off', "0.3*'A", 'A', 2)
S.const('[DS] D.off surge current, 1 us:', 'I.FSM_off', "2.0*'A", 'A', 1)

# ------------------------------------------------------------------ 6. selections
S.h2('6  Selected values (the Selected Value column, Power Components 127-142)')
S.note('Entered here, checked in section 7. The workbook recommends: V.drv 15 V, R.on 6.8 '
       'ohm (E12 below the log middle of min..max), R.off 2.2, C.gs 0, C.boot 100 nF (E6 '
       'above 10 x C.gate), R.boot 0.33 ohm (E12 below half its max). The design uses the '
       'main-sheet parts of section 14c.1.')
S.const('[PICK] Gate drive voltage V.drv:', 'V.drv', "15*'V", 'V', 1)
S.const('[PICK] Turn-on resistor R.on:', 'R.on', "4.7*'ohm", 'ohm', 2)
S.const('[PICK] Turn-off resistor R.off:', 'R.off', "2.2*'ohm", 'ohm', 2)
S.const('[PICK] Gate-source capacitor C.gs (0 = none):', 'C.gs', "0*'nF", 'nF', 1)
S.const('[PICK] Bootstrap capacitor C.boot:', 'C.boot', "470*'nF", 'nF', 0)
S.const('[PICK] Bootstrap resistor R.boot (0 = none):', 'R.boot', "0*'ohm", 'ohm', 2)

# ------------------------------------------------------------------ 7. working rows
S.h2('7  Working rows (CC 88-167)')
S.row('- Gate capacitance per position, n.par C.g + C.gs:', 'C.G', 'n.par*C.g+C.gs', 'nF', 2)
S.row('- Internal gate resistance per position:', 'R.gi', 'R.g/n.par', 'ohm', 2)
S.row('- Turn-off path resistance, R.off parallel R.on:', 'R.eff',
      'R.off*R.on/(R.off+R.on)', 'ohm', 3)
S.row('- Turn-off path offset from D.off:', 'V.eff', 'V.F_off*R.on/(R.off+R.on)', 'V', 3)
S.row('- tau.on = (R.so + R.on + R.gi) C.G:', 'τ.on', '(R.so+R.on+R.gi)*C.G', 'ns', 1)
S.row('- tau.off = (R.si + R.eff + R.gi) C.G:', 'τ.off', '(R.si+R.eff+R.gi)*C.G', 'ns', 1)
S.row('- Start-up pulse, T/2 - max(t.D.su, t.DT) (first LOUT pulse):', 't.L1',
      '1/(2*f.SU)-' + MAX('t.D_su', 't.DT', 's'), 'ns', 1)
S.row('- Pulse at f.Max, T/2 - max(t.D, t.DT):', 't.run',
      '1/(2*f.Max)-' + MAX('t.D', 't.DT', 's'), 'ns', 1)
S.row('- Gate voltage at the end of the start-up pulse:', 'V.g_su',
      "V.drv*(1-exp(-(t.L1/'s)/(τ.on/'s)))", 'V', 3)
S.row('- Gate voltage at the end of the f.Max pulse:', 'V.g_run',
      "V.drv*(1-exp(-(t.run/'s)/(τ.on/'s)))", 'V', 4)
S.row('- Energy per turn-on at f.Max [nJ]:', 'E.on',
      "C.G*V.g_run*(V.drv-V.g_run/2)/(10^(-9)*'J)", None, 1)
S.row('- Energy per turn-off at f.Max [nJ]:', 'E.off', "C.G*V.g_run^2/2/(10^(-9)*'J)", None, 1)
S.row('- Driver share of the turn-on energy:', 'x.on', 'R.so/(R.so+R.on+R.gi)', None, 4)
S.row('- Driver share of the turn-off energy:', 'x.off', 'R.si/(R.si+R.eff+R.gi)', None, 4)
S.row('- Midpoint swing in run, c.HB V.bus / I.Lm.pk:', 'T.T_run', 'c.HB*V.bus/I.Lm_pk', 'ns', 1)
S.row('- Start-up edge current, HB on V.bus / 2:', 'I.su_HB',
      "(V.bus/2)/Z.0*" + TAN("π*(f.r/'Hz)/(2*f.SU/'Hz)"), 'A', 3)
S.row('- Start-up tank peak, FB bus or half the HB bus, the larger:', 'a.su',
      MAX('V.bus_FB', 'V.bus/2', 'V'), 'V', 1)
S.row('- Start-up tank peak at f.SU (Res. Tank Design D84):', 'I.su',
      "a.su/Z.0*" + TAN("π*(f.r/'Hz)/(2*f.SU/'Hz)"), 'A', 3,
      note='I = A / Z.0 x tan(pi f.r / 2 f.SU): the tank is a short through the transformer '
           'while the output is at 0 V. Valid for f.SU above f.r.')
S.row('- Midpoint swing at start-up, FB: c.HB V.bus.FB / I.su:', 'T.T_su',
      'c.HB*V.bus_FB/I.su', 'ns', 1)
S.row('- Midpoint swing at start-up, HB: c.HB V.bus / I.su.HB:', 'T.T_suHB',
      'c.HB*V.bus/I.su_HB', 'ns', 1)
S.row('- Miller current into an off gate during the faster swing:', 'i.M',
      "n.par*Q.gd*10^(-9)*'A*'s/" + MIN('T.T_run', 'T.T_su', 's'), 'A', 4)
S.row('- Gate kick, resistive estimate, i.M x sink path:', 'dV.r', 'i.M*(R.si+R.eff+R.gi)',
      'V', 3)
S.row('- Gate kick, capacitive bound, Q.gd / (C.gs.dev + C.gs):', 'dV.c',
      "n.par*Q.gd*10^(-9)*'A*'s/(n.par*C.gs_dev+C.gs)", 'V', 3)
S.row('- t.on, IC edge to V.th:', 't.on', 't.pd+τ.on*' + LNV('V.drv', 'V.drv-V.th'), 'ns', 1)
S.row('- IC edge to the plateau on the way up:', 't.on_pl',
      't.pd+τ.on*' + LNV('V.drv', 'V.drv-V.pl'), 'ns', 1)
S.row('- t.off, IC edge to below V.th.min:', 't.off',
      't.pd+τ.off*' + LNV('V.drv-V.eff', 'V.th_min-V.eff'), 'ns', 1)
S.row('- IC edge to the plateau on the way down:', 't.off_pl',
      't.pd+τ.off*' + LNV('V.drv-V.eff', 'V.pl-V.eff'), 'ns', 1)
S.row('- Turn-off delay to the plateau from V.g.su (no t.pd):', 't.off_su',
      'τ.off*' + LNV('V.g_su-V.eff', 'V.pl-V.eff'), 'ns', 1)

# ------------------------------------------------------------------ 8. limits
S.h2('8  Limits of the selected values (Power Components 125-141) and the recommendations')
S.row('- Maximum gate drive voltage, driver range and V.gs rating:', 'V.drv_max',
      MIN('V.cc_max', 'V.gs_max', 'V'), 'V', 1)
S.row('- Minimum gate drive voltage, driver range and 10 V after D.boot:', 'V.drv_min',
      MAX('V.cc_min', "10*'V+V.F_boot", 'V'), 'V', 1)
S.row('- V.drv inside its range (>1):', 'k.Vdrv',
      MIN('V.drv_max/V.drv', 'V.drv/V.drv_min'), None, 3)
S.row('- Driver power allowed at T.a, (T.j.max - T.a) / R.th:', 'P.drv_max',
      "(T.j_max-T.a_drv)/R.th_drv*'W", 'W', 3)
S.row('- Gate-power budget, allowed less quiescent:', 'P.bud', 'P.drv_max-I.Q*V.drv', 'W', 3)
S.row('- Turn-on share the budget allows:', 'x.need',
      "(P.bud-2*E.off*x.off*10^(-9)*'J*f.Max)/(2*E.on*10^(-9)*'J*f.Max)", None, 4)
S.row('- R.on min for the driver temperature:', 'R.on_min_T',
      MAX("0*'ohm", 'R.so/x.need-R.so-R.gi', 'ohm'), 'ohm', 2,
      note='0 when the budget allows the driver to take the whole turn-on energy '
           '(x.need above 1); the workbook says "lower V.drv" when x.need is negative.')
S.row('- R.on min for the driver source current, V.drv / I.so - R.so - R.gi:', 'R.on_min_I',
      MAX("0*'ohm", 'V.drv/I.so-R.so-R.gi', 'ohm'), 'ohm', 2)
S.row('- Minimum turn-on resistor, the larger of the two:', 'R.on_min',
      MAX('R.on_min_T', 'R.on_min_I', 'ohm'), 'ohm', 2)
S.row('- Maximum turn-on resistor, 10 V within the shorter pulse:', 'R.on_max',
      MIN('t.L1', 't.run', 's') + '/(C.G*' + LNV('V.drv', "V.drv-10*'V") + ')-R.so-R.gi',
      'ohm', 2)
S.row('- R.on recommended, log middle of min..max (E12 below -> 6.8):', 'R.on_mid',
      'sqrt(' + MAX('R.on_min', "1*'ohm", 'ohm') + '*' + MAX('R.on_max', "1*'ohm", 'ohm') + ')',
      'ohm', 2)
S.row('- turn-on resistor inside its range (>1):', 'k.Ron',
      MIN('R.on_max/R.on', 'R.on/' + MAX('R.on_min', "0.001*'ohm", 'ohm')), None, 3,
      note='the lower ratio is against 1 mohm when R.on.min is 0, so it is large.')
S.row('- Turn-off path that holds the gate under V.th.min against i.M:', 'R.eff_m',
      'V.th_min/i.M-R.si-R.gi', 'ohm', 2)
S.row('- Turn-off path off before the other side reaches V.th.min:', 'R.eff_o',
      '(' + MAX('t.D', 't.DT', 's') + '+τ.on*' + LNV('V.drv', 'V.drv-V.th_min') + ')/('
      + LNV('V.drv-V.eff', 'V.th_min-V.eff') + '*C.G)-R.si-R.gi', 'ohm', 2)
S.row('- Turn-off path that lets the channel go within T.T.run:', 'R.eff_s',
      'T.T_run/(' + LNV('V.pl-V.eff', 'V.th-V.eff') + '*C.G)-R.si-R.gi', 'ohm', 2)
S.row('- 1 when the capacitive kick exceeds V.th.min (Miller criterion applies):', 's.M',
      STEP("dV.c/'V-V.th_min/'V"), None, 0)
S.row('- Maximum turn-off path resistance:', 'R.eff_max',
      MIN(MIN('R.eff_o', 'R.eff_s', 'ohm'), "R.eff_m+(1-s.M)*10^9*'ohm", 'ohm'), 'ohm', 3,
      note='min of overlap and soft turn-off; the Miller limit joins unless C.gs alone holds '
           'the gate (s.M = 0).')
S.row('- R.off that brings the path to half its max, parallel with R.on:', 'R.off_need',
      '1/(2/R.eff_max-1/R.on)', 'ohm', 2,
      note='valid while R.eff.max / 2 is below R.on - otherwise no R.off is needed (workbook: 1E9).')
S.row('- R.off recommended, min(R.on / 2, that need) (E12 below -> 2.2):', 'R.off_rec',
      MIN('R.on/2', 'R.off_need', 'ohm'), 'ohm', 2)
S.row('- Minimum turn-off resistor, sink current and D.off surge:', 'R.off_min',
      MAX("0*'ohm", '(V.drv-V.F_off)/' + MIN('I.si', 'I.FSM_off', 'A') + '-R.si-R.gi', 'ohm'),
      'ohm', 2)
S.row('- turn-off path inside its range (>1):', 'k.Roff',
      MIN('R.eff_max/R.eff', 'R.off/' + MAX('R.off_min', "0.001*'ohm", 'ohm')), None, 3)
S.row('- Maximum gate-source capacitor, 10 V within the pulse with R.on:', 'C.gs_max',
      MAX("0*'F", MIN('t.L1', 't.run', 's') + '/((R.so+R.on+R.gi)*' + LNV('V.drv', "V.drv-10*'V")
          + ')-n.par*C.g', 'F'), 'nF', 2)
S.row('- 1 when the smaller kick stays under V.th.min (gate holds without C.gs):', 's.hold',
      STEP("V.th_min/'V-" + MIN('dV.r', 'dV.c', 'V') + "/'V"), None, 0)
S.row('- Minimum gate-source capacitor, Miller (0 when the gate holds):', 'C.gs_min',
      '(1-s.hold)*' + MAX("0*'F", 'n.par*(Q.gd*10^(-9)*' + "'A*'s/V.th_min-C.gs_dev)", 'F'),
      'nF', 2, note='the workbook rounds a non-zero need up to E6.')
S.row('- Minimum bootstrap capacitor, 10 x C.G (E6 above -> 100 nF):', 'C.boot_min', '10*C.G',
      'nF', 1)
S.row('- Maximum bootstrap capacitor, first LOUT pulse to V.bo.min:', 'C.boot_max',
      't.L1/((R.boot+R.d_boot)*' + LNV('V.drv-V.F_boot', 'V.drv-V.F_boot-V.bo_min') + ')',
      'nF', 1)
S.row('- bootstrap capacitor inside its range (>1):', 'k.Cboot',
      MIN('C.boot_max/C.boot', 'C.boot/C.boot_min'), None, 3)
S.row('- Maximum bootstrap resistor, first LOUT pulse to V.bo.min:', 'R.boot_max',
      MAX("0*'ohm", 't.L1/(C.boot*' + LNV('V.drv-V.F_boot', 'V.drv-V.F_boot-V.bo_min')
          + ')-R.d_boot', 'ohm'), 'ohm', 3)
S.row('- Minimum bootstrap resistor, D.boot surge into an empty C.boot:', 'R.boot_min',
      MAX("0*'ohm", '(V.drv-V.F_boot)/I.FSM_boot-R.d_boot', 'ohm'), 'ohm', 3)
S.row('- R.boot recommended, half the max (E12 below -> 0.33):', 'R.boot_rec', 'R.boot_max/2',
      'ohm', 3, note='the workbook takes the E6 value above R.boot.min when half the max is '
                     'under the min.')
S.row('- bootstrap resistor under its max (>1):', 'k.Rboot',
      'R.boot_max/' + MAX('R.boot', "0.001*'ohm", 'ohm'), None, 3)

# ------------------------------------------------------------------ 9. results
S.h2('9  Results and checks (Power Components 144-172)')
S.row('- Peak gate current, turn-on:', 'I.g_on', 'V.drv/(R.so+R.on+R.gi)', 'A', 3)
S.row('- Peak gate current, turn-off:', 'I.g_off', '(V.drv-V.eff)/(R.si+R.eff+R.gi)', 'A', 3)
S.row('- Driver current margin (>1):', 'k.IG', MIN('I.so/I.g_on', 'I.si/I.g_off'), None, 3)
S.row('- Dead time needed in run, (t.off.pl - t.on) + T.T.run + MT:', 't.D_need',
      't.off_pl-t.on+T.T_run+MT', 'ns', 1)
S.row('- Dead time allowed in run, T/4 at f.Max + (t.off.pl - t.on.pl) - MT:', 't.D_max',
      '1/(4*f.Max)+t.off_pl-t.on_pl-MT', 'ns', 1)
S.row('- Dead time margin in run (>1):', 'k.tD',
      MIN(MAX('t.D_su', 't.DT', 's') + '/t.D_need', 't.D_max/' + MAX('t.D_need', 't.DT', 's')),
      None, 3, note='the smaller of 420 ns (or the driver dead time) over the need and the '
                    'allowance over the need.')
S.row('- Start-up dead time needed:', 't.D_su_min',
      't.off_su+' + MAX('T.T_su', 'T.T_suHB', 's') + '-(t.on-t.pd)+MT', 'ns', 1)
S.row('- Start-up dead time allowed, T/4 at f.SU:', 't.D_su_max',
      't.off_su+1/(4*f.SU)-(t.on_pl-t.pd)-MT', 'ns', 1)
S.row('- Start-up dead time in force, max(420 ns, t.DT):', 't.D_su_eff',
      MAX('t.D_su', 't.DT', 's'), 'ns', 0)
S.row('- Start-up dead time margin (>1):', 'k.tD_su',
      MIN('t.D_su_eff/t.D_su_min', 't.D_su_max/t.D_su_eff'), None, 3)
S.row('- Gate voltage at the end of the start-up pulse over 10 V (>1):', 'k.Vg_su',
      "V.g_su/(10*'V)", None, 3)
S.row('- tau.boot = (R.boot + diode) C.boot:', 'τ.boot', '(R.boot+R.d_boot)*C.boot', 'ns', 1)
S.row('- V.BS after the first LOUT pulse:', 'V.bs_1',
      "(V.drv-V.F_boot)*(1-exp(-(t.L1/'s)/(τ.boot/'s)))", 'V', 3)
S.row('- V.BS after the first pulse over V.bo.min (>1):', 'k.Vbs1', 'V.bs_1/V.bo_min', None, 3)
S.row('- V.BS drop per high-side pulse at f.SU, gate charge + I.QBO:', 'ΔV.bs',
      'C.G*V.g_su/C.boot+I.QBO*t.L1/C.boot', 'V', 4)
S.row('- V.BS minimum, steady at f.SU:', 'V.bs_min',
      "V.drv-V.F_boot-ΔV.bs*exp(-(t.L1/'s)/(τ.boot/'s))/(1-exp(-(t.L1/'s)/(τ.boot/'s)))-ΔV.bs",
      'V', 3)
S.row('- Miller margin, V.th.min over the smaller kick (>1):', 'k.Miller',
      'V.th_min/' + MIN('dV.r', 'dV.c', 'V'), None, 3)
S.row('- Midpoint dv/dt at start-up, the larger I.su over c.HB [V/ns]:', 'dvdt.su',
      MAX('I.su', 'I.su_HB', 'A') + "/c.HB*10^(-9)*'s/'V", None, 4)
S.row('- Driver ratings margin: dv/dt, HS voltage, logic level (>1):', 'k.drv',
      MIN(MIN('dVdt.max/dvdt.su', 'V.hs_max/V.bus'), 'V.OH/V.IH_max'), None, 3)
S.row('- Driver dissipation at f.Max, both positions + quiescent:', 'P.drv',
      "2*(E.on*x.on+E.off*x.off)*10^(-9)*'J*f.Max+I.Q*V.drv", 'W', 4)
S.row('- driver dissipation under the allowance (>1):', 'k.Pdrv', 'P.drv_max/P.drv', None, 3)
S.row('- Driver junction temperature at f.Max and T.a [C]:', 'T.j_drv',
      "T.a_drv+P.drv/'W*R.th_drv", None, 1)
S.row('- f.SU under the driver maximum and the IC maximum (>1):', 'k.fSU',
      MIN('f.max_drv', 'f.IC', 'Hz') + '/f.SU', None, 3)
S.row('- R.on dissipation at f.Max:', 'P.Ron',
      "(E.on*R.on/(R.so+R.on+R.gi)+E.off*R.eff/(R.si+R.eff+R.gi)*R.eff/R.on)*10^(-9)*'J*f.Max",
      'mW', 1)
S.row('- R.off dissipation at f.Max:', 'P.Roff',
      "E.off*R.eff/(R.si+R.eff+R.gi)*R.eff/R.off*10^(-9)*'J*f.Max", 'mW', 1)
S.row('- D.boot peak current:', 'I.boot_pk', '(V.drv-V.F_boot)/(R.boot+R.d_boot)', 'A', 2)
S.row('- D.boot average current, C.G V.g f.Max + I.QBO:', 'I.boot_avg',
      'C.G*V.g_run*f.Max+I.QBO', 'mA', 2)
S.row('- D.boot reverse voltage, V.bus + V.drv:', 'V.R_boot', 'V.bus+V.drv', 'V', 1)
S.row('- D.boot margin: V.RRM, surge, average (>1):', 'k.D_boot',
      MIN(MIN('V.RRM_boot/V.R_boot', 'I.FSM_boot/I.boot_pk'), 'I.F_boot/I.boot_avg'), None, 3)
S.row('- D.off peak current, upper bound:', 'I.off_pk', '(V.drv-V.F_off)/(R.si+R.off+R.gi)',
      'A', 3)
S.row('- D.off average current, C.G V.g f.Max x R.on / (R.on + R.off):', 'I.off_avg',
      'C.G*V.g_run*f.Max*R.on/(R.on+R.off)', 'mA', 2)
S.row('- D.off margin: surge, average (>1):', 'k.D_off',
      MIN('I.FSM_off/I.off_pk', 'I.F_off/I.off_avg'), None, 3)

# ------------------------------------------------------------------ 10. start-up
S.h2('10  Start-up tank current and OCP margins (Res. Tank Design 83-87)')
S.show('- Start-up tank peak at f.SU (section 7):', 'I.su', 'A', 3)
S.row('- OCP2 margin at start-up (>1):', 'k.su_OCP2', 'I.OCP2/I.su', None, 3)
S.row('- OCP1 margin at start-up (>1):', 'k.su_OCP1', 'I.OCP1/I.su', None, 3)
S.row('- Start-up floor before OCP1, the f.SU at which I.su = I.OCP1:', 'f.su_OCP1',
      "π*f.r/(2*atan((I.OCP1/'A)*(Z.0/'ohm)/(a.su/'V)))", 'kHz', 2,
      note='f.SU must stay above it - the margin rows above say by how much.')

if S.clashes:
    print('** name clashes:')
    for nm, a, b in S.clashes:
        print('     %-14s %-14g -> %g' % (nm, a, b))
    raise SystemExit(1)
nbytes, ybottom = S.save(OUT)
print(f'written {OUT}\n  {nbytes} bytes, {ybottom} px tall, '
      f'{ybottom/(S.PAGE_H-2*S.MARGIN):.1f} A3-landscape pages, {len(S.r)} regions')

# ------------------------------------------------------------------ self-check
# the GUIDE workbook after a LibreOffice recalculation (2026-10-22), SI units
XL = {
    'f.r': 75026.3596797588, 'Z.0': 11.7851130197758, 'I.OCP1': 22.9166666666667,
    'I.OCP2': 31.25, 'V.bus': 373.352380466497,
    'R.so_sc': 10.7142857142857, 'R.si_sc': 9.67741935483871,
    'V.drv_min': 11.3, 'V.drv_max': 20.0,
    'R.on_max': 61.1888333465837, 'R.on_min': 0.0, 'R.eff_max': 7.88442606136035,
    'R.off_min': 0.0, 'C.gs_max': 21.2744888859085e-9, 'C.gs_min': 0.0,
    'C.boot_max': 1108.53207923043e-9, 'C.boot_min': 75e-9,
    'R.boot_max': 0.679289445989819, 'R.boot_min': 0.0,
    'I.g_on': 0.753228120516499, 'I.g_off': 0.926461860552505, 'k.IG': 1.6730316335695,
    'R.eff': 1.49855072463768, 't.D_need': 192.710814707325e-9, 't.D_max': 871.459248789696e-9,
    'k.tD': 2.17943139640536, 't.D_su_min': 372.007371797012e-9,
    't.D_su_max': 519.045488633298e-9, 'k.tD_su': 1.12900988486103,
    'V.g_su': 14.7784006101709, 'V.bs_1': 12.7596071203457, 'V.bs_min': 13.4466213569429,
    'k.Miller': 1.74474464697946, 'dvdt.su': 1.66258617825052, 'k.drv': 1.28564869306645,
    'P.drv_max': 0.833333333333333, 'P.drv': 0.565791770452628, 'T.j_drv': 92.8950124543154,
    'P.Ron': 0.0642156388922573, 'P.Roff': 0.0156897686657003,
    'I.boot_pk': 27.4, 'I.boot_avg': 32.2480865202008e-3, 'V.R_boot': 388.352380466497,
    'k.D_boot': 1.09489051094891, 'I.off_pk': 0.873153437069135,
    'I.off_avg': 21.8843487891223e-3, 'k.D_off': 2.2905481615159,
    'I.su': 5.03594028219725, 'k.su_OCP2': 6.20539526858035, 'k.su_OCP1': 4.55062319695892,
    'f.su_OCP1': 137.880651106336e3,
    # CC working rows
    'V.eff': 0.476811594202899, 'τ.on': 149.357142857143e-9, 'τ.off': 117.569775596073e-9,
    't.L1': 629.530541196329e-9, 't.run': 1530.74257425743e-9, 'V.g_run': 14.9994690400911,
    'E.on': 843.749998942806, 'E.off': 843.690268067442, 'x.on': 0.538020086083214,
    'x.off': 0.617341019775789, 'P.bud': 0.824333333333333, 'x.need': 1.09315656620826,
    'R.on_mid': 7.8223, 'T.T_run': 101.587812420256e-9, 'T.T_su': 141.346056567896e-9,
    'i.M': 0.127968106510854, 'dV.r': 2.0060242087914, 'dV.c': 2.73109243697479,
    't.on': 131.323853934523e-9, 't.on_pl': 166.35889456061e-9, 't.off': 269.518066033611e-9,
    't.off_pl': 192.446856221593e-9, 'I.su_HB': 4.00038360052227,
    'T.T_suHB': 282.692113135793e-9, 't.off_su': 105.639112595743e-9,
    'R.eff_m': 13.1731455275379, 'R.eff_o': 7.88442606136035, 'R.eff_s': 12.7788760322617,
    'R.off_need': 24.4506728069335, 'τ.boot': 235e-9, 'ΔV.bs': 0.235986272853671,
}
print('\n--- cross-check against the recalculated GUIDE workbook ---')
bad = 0
for name, ref in XL.items():
    got = S.ns[name.replace('.', '__')]
    tol = 1e-3 if name == 'R.on_mid' else 2e-4
    ok = abs(got - ref) <= max(abs(ref) * tol, 1e-9)
    bad += 0 if ok else 1
    print(f'  {name:12s} sheet={got:<16.8g} xl={ref:<16.8g} {"OK" if ok else "** DIFF"}')
print(f'  compared: {len(XL)}   mismatches: {bad}')
if bad:
    raise SystemExit(1)
