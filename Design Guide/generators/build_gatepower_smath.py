# -*- coding: utf-8 -*-
"""Builds  Smath/tools/Gate_Driver_Power_Unipolar.sm  -  gate driver dissipation and gate
current for a POSITIVE-ONLY (unipolar, 0 V off) gate drive from STGAP3SXS (one output pin).

History (2026-11-02, user):
  1. like the uploaded 21082025_Gate_Driver_Cal.sm (separate R_on / R_off);
  2. "STGAP3SXS - the gate output is a single pin; R_on, and diode + R_off";
  3. "refer to" DS_stgap3s6i (DS14758 Rev 3, October 2026) and DB_evlstgap3sxs-h (DB5386
     Rev 2, January 2025): driver numbers now from the datasheet, gate network values from
     the evaluation board, logic-side supply, Miller-clamp pre-driver, VH UVLO and the
     frequency limit added.

Network (same as the EVLSTGAP3SXS-H gate driver stage, Fig. 1 of the data brief):
    GOUT --R.g_on (R15 22 ohm)-- gate,   D.off (D1 STPS2L40ZFY) + R.g_off (R18 2.2 ohm)
    across R.g_on, cathode at GOUT;  SOFTOFF --R19 10 ohm-- gate;  CLAMPdrv --2.2 ohm--
    STL7N6F7 (gate to VL).
Turn-on: R.g_on alone. Turn-off: R.g_on in parallel with R.g_off + V.F (Thevenin
R.eff, V.eff). Driver losses use the MAXIMUM datasheet R.DON / R.DOFF and supply currents,
so the dissipation is an upper estimate.

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
S = Sheet('STGAP3SXS gate driver power - unipolar', 'L6790A project',
          'STGAP3SXS dissipation and gate current, one output pin, R_on and D + R_off')

S.h1('STGAP3SXS Gate Driver Calculation  -  GOUT, R.g_on and (D.off + R.g_off), 0 V off')
S.note('Network as on the EVLSTGAP3SXS-H board: GOUT - R.g_on - gate, and D.off in series with '
       'R.g_off across R.g_on, cathode at GOUT. Turn-on through R.g_on alone; turn-off through '
       'R.g_on in parallel with R.g_off + V.F. Driver values: STGAP3SXS datasheet DS14758 Rev 3, '
       'Table 5 (T.J = 25 C, VH = 15 V unless noted); the maximum figures are used for losses. '
       'Yellow cells are the inputs.')

# ------------------------------------------------------------------ inputs
S.h2('1  Switch and gate network')
S.const('Turn-ON gate resistor R.g_on (EVL board R15):', 'R.g_on', "22*'ohm", 'ohm', 2)
S.const('Turn-OFF gate resistor R.g_off (EVL board R18):', 'R.g_off', "2.2*'ohm", 'ohm', 2)
S.const('[TBD DS] D.off forward voltage at the peak current:', 'V.F', "0.5*'V", 'V', 2,
        note='EVL board D1 is STPS2L40ZFY (Schottky); its datasheet was not available - '
             'read V.F at the D.off peak current of section 3.')
S.const('[TBD DS] D.off surge current rating (0 = not entered):', 'I.FSM_D', "0*'A", 'A', 2)
S.const('[TBD DS] D.off average forward current rating:', 'I.F_D', "2*'A", 'A', 2,
        note='2 A is what the part name STPS2L40 implies - confirm from its datasheet.')
S.const('Switch internal gate resistance (datasheet R.G):', 'R.g_int', "0*'ohm", 'ohm', 2)
S.const('Switch total gate charge Q.g at V.H [10^-9 A s]:', 'Q.g', "210*10^(-9)*'A*'s", None, 0,
        note='example value of the first version (WG75N65MFW1); use the gate charge curve of '
             'the switch at the drive voltage V.H.')
S.const('Switches driven per channel (paralleled):', 'n.par', '1', None, 0)
S.const('Switching frequency:', 'f.sw', "85*'kHz", 'kHz', 1)
S.const('Turn-ON gate voltage V.H (VH vs GNDISO):', 'V.H', "18*'V", 'V', 1)
S.const('Turn-OFF gate voltage V.L (VL tied to GNDISO, unipolar):', 'V.L', "0*'V", 'V', 1,
        note='DS 6.x: for unipolar drive connect GNDISO and VL with short traces.')
S.const('Miller-clamp FET gate charge at V.CLAMP [10^-9 A s]:', 'Q.g_clamp', "0*10^(-9)*'A*'s",
        None, 1, note='EVL board uses STL7N6F7 on CLAMPdrv; 0 = clamp not fitted. Its gate '
                      'is charged to V.CLAMPdrv_H once per cycle.')

S.h2('2  STGAP3SXS (DS14758 Rev 3)')
S.const('[DS] Source R.DS_ON, max (IGON 100 mA):', 'R.on_H', "0.80*'ohm", 'ohm', 2,
        note='typ 0.65, min 0.50 ohm.')
S.const('[DS] Sink R.DS_ON, max (IGOFF 100 mA):', 'R.on_L', "0.65*'ohm", 'ohm', 2,
        note='typ 0.50, min 0.35 ohm.')
S.const('[DS] Source short-circuit current, min over -40..125 C:', 'I.src_max', "7*'A", 'A', 1,
        note='8 / 10 / 11.5 A min / typ / max at 25 C; 7 A is the characterization minimum.')
S.const('[DS] Sink short-circuit current, min over -40..125 C:', 'I.snk_max', "7*'A", 'A', 1)
S.const('[DS] VH quiescent current, max (IN+ = GND):', 'I.QH', "6*'mA", 'mA', 1,
        note='typ 5 mA. The datasheet gives it only with the output low.')
S.const('Logic supply VDD:', 'V.DD', "5*'V", 'V', 1)
S.const('[DS] VDD quiescent current, IN+ low, max:', 'I.DD_lo', "2.5*'mA", 'mA', 1)
S.const('[DS] VDD quiescent current, IN+ high, max:', 'I.DD_hi', "13*'mA", 'mA', 1,
        note='typ 2.0 / 11 mA. The logic side draws far more while the input is high.')
S.const('Input high duty (fraction of the period):', 'D.in', '0.5', None, 2)
S.const('[DS] CLAMPdrv high level vs VL, max (VHL >= 11.5 V):', 'V.clamp', "13*'V", 'V', 1)
S.const('[DS] VH UVLO turn-on threshold, max (STGAP3SxSx):', 'V.H_on', "14.3*'V", 'V', 1,
        note='turn-off 12.2 - 13.4 V. The S variant is the SiC threshold.')
S.const('[DS] Maximum switching frequency (Table 4):', 'f.max', "1000*'kHz", 'kHz', 0)
S.const('[DS] Thermal resistance junction-ambient, SO-16W [C/W]:', 'R.th_JA', '65', None, 0,
        note='2s2p JEDEC board; a real board differs.')
S.const('[DS] Operating junction temperature, max [C]:', 'T.j_max', '125', None, 0)

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
S.row('- Gate sink peak current (turn-off, into GOUT):', 'I.pk_off',
      '(V.sw-V.eff)/R.path_off', 'A', 3)
S.row('- Voltage across the branch at the turn-off peak:', 'V.p', 'V.eff+I.pk_off*R.eff', 'V',
      3)
S.row('- D.off peak current:', 'I.pk_D', '(V.p-V.F)/R.g_off', 'A', 3)
S.row('- R.g_on peak current at turn-off:', 'I.pk_Ron_off', 'V.p/R.g_on', 'A', 3)
S.row('- driver source current margin (>1):', 'k.src', 'I.src_max/I.pk_on', None, 2)
S.row('- driver sink current margin (>1):', 'k.snk', 'I.snk_max/I.pk_off', None, 2,
      note='I.GON / I.GOFF are what the output stage can deliver, not an absolute maximum: '
           'below 1 the driver itself caps the current and the edge is slower than computed.')
S.row('- diode surge margin (>1; 0 until I.FSM_D is entered):', 'k.D_pk', 'I.FSM_D/I.pk_D',
      None, 2)

S.h2('4  Gate timing')
S.row('- Equivalent gate capacitance from the charge, n.par Q.g / V.sw:', 'C.eq',
      'n.par*Q.g/V.sw', 'nF', 2, note='includes the Miller charge.')
S.row('- Gate rising time 10-90 %, ln(9) R.path_on C.eq:', 't.r', 'ln(9)*R.path_on*C.eq',
      'ns', 0, note='ln(9) = 2.197 is the 10 % to 90 % time of an RC charge in time constants.')
S.row('- Gate falling time 90-10 %, through the diode path:', 't.f',
      "R.path_off*C.eq*ln(((0.9*V.sw-V.eff)/'V)/((0.1*V.sw-V.eff)/'V))", 'ns', 0)
S.row('- 10 % point above the branch offset (>1, else t.f is not valid):', 'k.tf',
      '0.1*V.sw/V.eff', None, 2)

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
S.row('- Driver output dissipation at turn-on:', 'P.drv_on', 'P.G/2*R.on_H/R.path_on', 'W', 4)
S.row('- Driver output dissipation at turn-off:', 'P.drv_off', 'P.off_R*R.on_L/R.path_off',
      'W', 4)
S.row('- Miller-clamp pre-driver, Q.g_clamp V.clamp f.sw:', 'P.clamp',
      'Q.g_clamp*V.clamp*f.sw', 'W', 4, note='all of it counted in the driver - an upper bound.')
S.row('- Isolated-side quiescent, I.QH V.H:', 'P.QH', 'I.QH*V.H', 'W', 4)
S.row('- Logic-side supply, V.DD (D.in I.DD_hi + (1 - D.in) I.DD_lo):', 'P.DD',
      'V.DD*(D.in*I.DD_hi+(1-D.in)*I.DD_lo)', 'W', 4)
S.row('- STGAP3SXS package dissipation, total:', 'P.D',
      'P.drv_on+P.drv_off+P.clamp+P.QH+P.DD', 'W', 4)
S.row('- R.g_on dissipation (each switch):', 'P.Ron',
      '(P.G/2*R.g_on/R.path_on+P.off_R*R.eff/R.path_off*R.g_off/(R.g_on+R.g_off))/n.par',
      'W', 4, note='turn-on share, plus its part of the parallel branch at turn-off '
                   '(split by conductance - an estimate).')
S.row('- R.g_off dissipation (each switch):', 'P.Roff',
      'P.off_R*R.eff/R.path_off*R.g_on/(R.g_on+R.g_off)/n.par', 'W', 4)
S.row('- Internal gate resistance dissipation (in the switch):', 'P.Rgi',
      '(P.G/2*R.g_int/n.par/R.path_on+P.off_R*R.g_int/n.par/R.path_off)', 'W', 4)
S.row('- gate power parts sum to P.G (check):', 'P.sum',
      'P.drv_on+P.drv_off+n.par*(P.Ron+P.Roff)+P.Rgi+P.D_off', 'W', 4)

S.h2('6  Driver limits and junction temperature')
S.row('- V.H above the VH UVLO turn-on threshold (>1):', 'k.UVLO', 'V.H/V.H_on', None, 3)
S.row('- f.sw under the driver maximum (>1):', 'k.fsw', 'f.max/f.sw', None, 2)
S.row('- Junction rise [C]:', 'ΔT.j', "P.D/'W*R.th_JA", None, 1)
S.const('Ambient temperature 1 [C]:', 'T.amb1', '25', None, 0)
S.row('- Junction temperature at T.amb1 [C]:', 'T.j1', 'T.amb1+ΔT.j', None, 1)
S.const('Ambient temperature 2 [C]:', 'T.amb2', '45', None, 0)
S.row('- Junction temperature at T.amb2 [C]:', 'T.j2', 'T.amb2+ΔT.j', None, 1)
S.row('- margin to T.j_max at T.amb2 (>1):', 'k.Tj2', '(T.j_max-T.amb2)/ΔT.j', None, 2)
S.row('- Highest ambient the driver allows [C]:', 'T.amb_max', 'T.j_max-ΔT.j', None, 1)
S.note('Unused functions (DS Table 8): without desaturation protection connect DESAT to '
       'GNDISO and leave DIAG floating; without the Miller clamp leave CLAMPdrv floating. '
       'SOFTOFF goes to VL only if BOTH are unused - with the Miller clamp it must go to the '
       'gate through a resistor of at least 10 ohm (EVL board R19 10 ohm).')

if S.clashes:
    raise SystemExit('name clashes: %s' % S.clashes)
nbytes, ybottom = S.save(OUT)
print(f'written {OUT}\n  {nbytes} bytes, {ybottom} px tall, {len(S.r)} regions')

# ---------------------------------------------------------------- self-check
# independent nodal solution of the turn-off peak (gate at V.sw, GOUT through R.on_L to 0 V)
Vs, RL, RH, Ron, Roff, VF = 18.0, 0.65, 0.80, 22.0, 2.2, 0.5
VB = (Vs / Ron + (Vs - VF) / Roff) / (1 / Ron + 1 / Roff + 1 / RL)
Qg, f = 210e-9, 85e3
PG = Qg * Vs * f
PDoff = VF * Qg * f * Ron / (Ron + Roff)
Reff = Ron * Roff / (Ron + Roff)
ref = {'I.pk_on': Vs / (RH + Ron), 'I.pk_off': VB / RL, 'I.pk_D': (Vs - VB - VF) / Roff,
       'P.G': PG, 'P.sum': PG, 't.r': math.log(9) * (RH + Ron) * Qg / Vs,
       'P.D': PG / 2 * RH / (RH + Ron) + (PG / 2 - PDoff) * RL / (RL + Reff)
              + 6e-3 * 18 + 5 * (0.5 * 13e-3 + 0.5 * 2.5e-3)}
bad = 0
for k, v in ref.items():
    got = S.ns[k.replace('.', '__')]
    ok = abs(got - v) <= abs(v) * 1e-6
    bad += not ok
    print(f'  {k:10s} sheet={got:<12.6g} ref={v:<12.6g} {"OK" if ok else "** DIFF"}')
print(f'  mismatches: {bad}')
if bad:
    raise SystemExit(1)
