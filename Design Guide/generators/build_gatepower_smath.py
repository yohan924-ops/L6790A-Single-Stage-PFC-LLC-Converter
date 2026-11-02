# -*- coding: utf-8 -*-
"""Builds  Smath/tools/Gate_Driver_Power_Unipolar.sm  -  gate driver dissipation and gate
current for a POSITIVE-ONLY (unipolar, 0 V off) gate drive from a driver with ONE output pin.

History:
  2026-11-02  first version, like the uploaded 21082025_Gate_Driver_Cal.sm (separate R_on /
              R_off as if the driver had two pins).
  2026-11-02  user: "STGAP3SXS, the gate output is a single pin; R_on, and diode + R_off".
              The network is now   OUT --R.g_on-- gate   with   (D.off + R.g_off) across
              R.g_on, cathode toward OUT: turn-on goes through R.g_on alone (diode reverse
              biased), turn-off through R.g_on in parallel with R.g_off + V.F.

Turn-off with the diode (Thevenin of the parallel branch):
    R.eff = R.g_on R.g_off / (R.g_on + R.g_off)        V.eff = V.F R.g_on / (R.g_on + R.g_off)
    I.pk_off = (V.sw - V.eff) / (R.on_L + R.eff + R.g_int)
    voltage across the branch  V.p = V.eff + I.pk_off R.eff,  diode current (V.p - V.F)/R.g_off
The diode stops conducting once the branch voltage falls under V.F; the tail of the turn-off
then runs through R.g_on alone. The fall time below uses the diode path down to 10 %,
which holds while 0.1 V.sw is above V.eff (checked in the sheet).

The STGAP3SXS datasheet could NOT be read when this was built (st.com returned 503); the
driver values in section 2 are placeholders from the first version and are marked so.

Run:  python build_gatepower_smath.py      -> mismatches: 0
      python check_sm.py ../../Smath/tools/Gate_Driver_Power_Unipolar.sm   -> VERDICT OK
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smsheet import Sheet                                          # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'Smath', 'tools', 'Gate_Driver_Power_Unipolar.sm'))
S = Sheet('Gate driver power - single output, unipolar', 'L6790A project',
          'gate driver dissipation and gate current, one output pin, R_on and D + R_off')

S.h1('Gate Driver Calculation  -  one output pin, R.g_on and (D.off + R.g_off), 0 V off')
S.note('Network: driver OUT - R.g_on - gate, and D.off in series with R.g_off across R.g_on, '
       'cathode toward OUT. Turn-on: R.g_on alone. Turn-off: R.g_on in parallel with '
       'R.g_off + V.F. Yellow cells are the inputs. Section 2 holds the driver (written for '
       'STGAP3SXS): its numbers are PLACEHOLDERS - the STGAP3SXS datasheet was not available '
       'when the sheet was built - replace every one of them from the datasheet.')

# ------------------------------------------------------------------ inputs
S.h2('1  Switch and gate network')
S.const('Turn-ON gate resistor R.g_on (series, both edges):', 'R.g_on', "15*'ohm", 'ohm', 2)
S.const('Turn-OFF gate resistor R.g_off (in series with D.off):', 'R.g_off', "7.5*'ohm",
        'ohm', 2)
S.const('Turn-off diode forward voltage V.F at the peak current:', 'V.F', "0.7*'V", 'V', 2,
        note='read at the turn-off peak current computed in section 3, not at 10 mA.')
S.const('Turn-off diode surge current rating I.FSM (short pulse):', 'I.FSM_D', "2*'A", 'A', 2)
S.const('Turn-off diode average forward current rating:', 'I.F_D', "0.15*'A", 'A', 3)
S.const('Switch internal gate resistance (datasheet R.G):', 'R.g_int', "0*'ohm", 'ohm', 2)
S.const('Switch input capacitance C.iss:', 'C.iss', "4307*'pF", 'pF', 0)
S.const('Switch total gate charge Q.g at V.H [10^-9 A s]:', 'Q.g', "210*10^(-9)*'A*'s", None, 0,
        note='read from the gate charge curve at the drive voltage V.H.')
S.const('Switches driven per channel (paralleled):', 'n.par', '1', None, 0)
S.note('Example switch values are those of the uploaded sheet (WG75N65MFW1, 18 V, 85 kHz); '
       'replace them with the switch used.')

S.h2('2  Switching and gate driver (STGAP3SXS - placeholders, replace from its datasheet)')
S.const('Switching frequency:', 'f.sw', "85*'kHz", 'kHz', 1)
S.const('Turn-ON gate voltage V.H (positive supply):', 'V.H', "18*'V", 'V', 1)
S.const('Turn-OFF gate voltage V.L (0 V, unipolar):', 'V.L', "0*'V", 'V', 1)
S.const('[TBD DS] Driver output resistance, source:', 'R.on_H', "1*'ohm", 'ohm', 2)
S.const('[TBD DS] Driver output resistance, sink:', 'R.on_L', "1.5*'ohm", 'ohm', 2)
S.const('[TBD DS] Driver peak source current rating:', 'I.src_max', "6*'A", 'A', 1,
        note='a distributor listing gives 6 A and 10 A without saying which is source and '
             'which is sink - confirm both from the datasheet.')
S.const('[TBD DS] Driver peak sink current rating:', 'I.snk_max', "6*'A", 'A', 1)
S.const('[TBD DS] Driver quiescent current, isolated side, at V.H:', 'I.Q', "0*'mA", 'mA', 2)
S.const('[TBD DS] Thermal resistance junction-ambient [C/W]:', 'R.th_JA', '120', None, 0,
        note='120 is the first version\'s value, not the SO-16W figure of the STGAP3SXS.')
S.const('[TBD DS] Maximum junction temperature [C]:', 'T.j_max', '125', None, 0)

# ------------------------------------------------------------------ results
S.h2('3  Peak currents')
S.row('- Gate swing:', 'V.sw', 'V.H-V.L', 'V', 1)
S.row('- Turn-on path resistance, R.on_H + R.g_on + R.g_int / n.par:', 'R.path_on',
      'R.on_H+R.g_on+R.g_int/n.par', 'ohm', 3)
S.row('- Gate source peak current (turn-on, through R.g_on):', 'I.pk_on', 'V.sw/R.path_on',
      'A', 3)
S.row('- Parallel branch resistance, R.g_on with R.g_off:', 'R.eff',
      'R.g_on*R.g_off/(R.g_on+R.g_off)', 'ohm', 3)
S.row('- Parallel branch offset from the diode:', 'V.eff', 'V.F*R.g_on/(R.g_on+R.g_off)', 'V',
      3)
S.row('- Turn-off path resistance, R.on_L + R.eff + R.g_int / n.par:', 'R.path_off',
      'R.on_L+R.eff+R.g_int/n.par', 'ohm', 3)
S.row('- Gate sink peak current (turn-off, into OUT):', 'I.pk_off',
      '(V.sw-V.eff)/R.path_off', 'A', 3)
S.row('- Voltage across the branch at the turn-off peak:', 'V.p', 'V.eff+I.pk_off*R.eff', 'V',
      3)
S.row('- D.off peak current:', 'I.pk_D', '(V.p-V.F)/R.g_off', 'A', 3)
S.row('- R.g_on peak current at turn-off:', 'I.pk_Ron_off', 'V.p/R.g_on', 'A', 3)
S.row('- driver source current margin (>1):', 'k.src', 'I.src_max/I.pk_on', None, 2)
S.row('- driver sink current margin (>1):', 'k.snk', 'I.snk_max/I.pk_off', None, 2)
S.row('- diode surge margin (>1):', 'k.D_pk', 'I.FSM_D/I.pk_D', None, 2)

S.h2('4  Gate timing')
S.row('- Equivalent gate capacitance from the charge, n.par Q.g / V.sw:', 'C.eq',
      'n.par*Q.g/V.sw', 'nF', 2, note='includes the Miller charge; C.iss alone reads fast.')
S.row('- Gate rising time 10-90 %, 2.2 R.path_on C.eq:', 't.r', '2.2*R.path_on*C.eq', 'ns', 0)
S.row('- Gate falling time 90-10 %, through the diode path:', 't.f',
      "R.path_off*C.eq*ln(((0.9*V.sw-V.eff)/'V)/((0.1*V.sw-V.eff)/'V))", 'ns', 0)
S.row('- 10 % point above the branch offset (>1, else t.f is not valid):', 'k.tf',
      '0.1*V.sw/V.eff', None, 2)
S.row('- the same falling time without the diode (R.g_on alone):', 't.f_noD',
      '2.2*(R.on_L+R.g_on+R.g_int/n.par)*C.eq', 'ns', 0)
S.row('- rising time with C.iss, as in the first version:', 't.r_iss',
      '2.2*R.path_on*n.par*C.iss', 'ns', 0)

S.h2('5  Power')
S.row('- Gate drive power per channel, n.par Q.g V.sw f.sw:', 'P.G', 'n.par*Q.g*V.sw*f.sw',
      'W', 4, note='half at turn-on, half at turn-off.')
S.row('- D.off dissipation, V.F x charge through the diode:', 'P.D_off',
      'V.F*n.par*Q.g*f.sw*R.g_on/(R.g_on+R.g_off)', 'W', 4,
      note='the diode branch carries about R.g_on / (R.g_on + R.g_off) of the turn-off charge.')
S.row('- D.off average current:', 'I.avg_D', 'n.par*Q.g*f.sw*R.g_on/(R.g_on+R.g_off)', 'mA',
      2)
S.row('- diode average current margin (>1):', 'k.D_avg', 'I.F_D/I.avg_D', None, 2)
S.row('- Turn-off energy left for the resistors, per second:', 'P.off_R', 'P.G/2-P.D_off', 'W',
      4)
S.row('- Driver dissipation at turn-on:', 'P.drv_on', 'P.G/2*R.on_H/R.path_on', 'W', 4)
S.row('- Driver dissipation at turn-off:', 'P.drv_off', 'P.off_R*R.on_L/R.path_off', 'W', 4)
S.row('- Driver dissipation per channel:', 'P.drv_ch', 'P.drv_on+P.drv_off', 'W', 4)
S.row('- Driver package dissipation, + quiescent:', 'P.D', 'P.drv_ch+I.Q*V.H', 'W', 4)
S.row('- R.g_on dissipation (each switch):', 'P.Ron',
      '(P.G/2*R.g_on/R.path_on+P.off_R*R.eff/R.path_off*R.g_off/(R.g_on+R.g_off))/n.par',
      'W', 4, note='turn-on share, plus its part of the parallel branch at turn-off '
                   '(split by conductance - an estimate).')
S.row('- R.g_off dissipation (each switch):', 'P.Roff',
      'P.off_R*R.eff/R.path_off*R.g_on/(R.g_on+R.g_off)/n.par', 'W', 4)
S.row('- Internal gate resistance dissipation (in the switch):', 'P.Rgi',
      '(P.G/2*R.g_int/n.par/R.path_on+P.off_R*R.g_int/n.par/R.path_off)', 'W', 4)
S.row('- sum of the parts, equals P.G (check):', 'P.sum',
      'P.drv_on+P.drv_off+n.par*(P.Ron+P.Roff)+P.Rgi+P.D_off', 'W', 4)

S.h2('6  Driver junction temperature')
S.row('- Junction rise [C]:', 'ΔT.j', "P.D/'W*R.th_JA", None, 1)
S.const('Ambient temperature 1 [C]:', 'T.amb1', '25', None, 0)
S.row('- Junction temperature at T.amb1 [C]:', 'T.j1', 'T.amb1+ΔT.j', None, 1)
S.const('Ambient temperature 2 [C]:', 'T.amb2', '45', None, 0)
S.row('- Junction temperature at T.amb2 [C]:', 'T.j2', 'T.amb2+ΔT.j', None, 1)
S.row('- margin to T.j_max at T.amb2 (>1):', 'k.Tj2', '(T.j_max-T.amb2)/ΔT.j', None, 2)
S.row('- Highest ambient the driver allows [C]:', 'T.amb_max', 'T.j_max-ΔT.j', None, 1)

if S.clashes:
    raise SystemExit('name clashes: %s' % S.clashes)
nbytes, ybottom = S.save(OUT)
print(f'written {OUT}\n  {nbytes} bytes, {ybottom} px tall, {len(S.r)} regions')

# ---------------------------------------------------------------- self-check
# independent nodal solution of the turn-off peak (gate at V.sw, OUT at 0 V, diode as V.F)
Vs, RL, Ron, Roff, VF, Rgi = 18.0, 1.5, 15.0, 7.5, 0.7, 0.0
# unknowns: node A (gate side of the branch) and B (OUT side, after R_L) - B is OUT node at
# R_L from 0 V. Currents: I = (Vs - VA)/Rgi (Rgi=0 -> VA = Vs), branch: (VA-VB)/Ron +
# (VA-VB-VF)/Roff = VB/RL
VA = Vs
VB = (VA / Ron + (VA - VF) / Roff) / (1 / Ron + 1 / Roff + 1 / RL)
I_tot = VB / RL
I_d = (VA - VB - VF) / Roff
Qg, f = 210e-9, 85e3
ref = {'I.pk_on': 18 / 16, 'I.pk_off': I_tot, 'I.pk_D': I_d, 'P.G': 0.3213,
       't.r_iss': 152e-9, 'P.sum': 0.3213,
       't.f': (RL + Ron * Roff / (Ron + Roff)) * Qg / Vs *
              math.log((0.9 * Vs - VF * Ron / (Ron + Roff)) / (0.1 * Vs - VF * Ron / (Ron + Roff))),
       'P.D_off': VF * Qg * f * Ron / (Ron + Roff)}
bad = 0
for k, v in ref.items():
    got = S.ns[k.replace('.', '__')]
    tol = 0.005 if k == 't.r_iss' else 1e-6
    ok = abs(got - v) <= abs(v) * tol
    bad += not ok
    print(f'  {k:10s} sheet={got:<12.6g} ref={v:<12.6g} {"OK" if ok else "** DIFF"}')
print(f'  mismatches: {bad}')
if bad:
    raise SystemExit(1)
