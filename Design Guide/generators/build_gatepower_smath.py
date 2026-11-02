# -*- coding: utf-8 -*-
"""Builds  Smath/tools/STGAP3SXS_Gate_Driver_Power.sm  -  STGAP3SXS gate driver dissipation
and gate current, +V.H / V.L drive (user: +19 / -4.7 V), one output pin, gate network of
the EVLSTGAP3SXS-H board (22 ohm on, 2.2 ohm + diode off):

    GOUT --R.g_on-- gate,  D.off + R.g_off across R.g_on (cathode at GOUT)

2026-11-02 (user): first like the uploaded 21082025_Gate_Driver_Cal.sm, then the single-pin
network, then STGAP3SXS values from DS14758 Rev 3 (maximum figures, so the dissipation is an
upper estimate) and the EVLSTGAP3SXS-H network (DB5386 Rev 2), then "leave only what is
needed": inputs, peak currents, rise / fall time, power, junction temperature. Then the
user's SiC half-bridge module (1200 V, 1.8 mOhm, Q.g 1377 nC at -5..18 V): Q.g 0->18 V read
from its Fig. 16, and a Miller turn-on check, because 0 V off with V.th min 1.9 V is the
weak point (the module datasheet measured its switching with -5 V and an active clamp). Intermediate
quantities sit in one collapsed block (Sheet.set computes in Python only and would leave them
undefined in SMath).

Turn-off with the diode:  R.eff = R.g_on R.g_off / (R.g_on + R.g_off),
V.eff = V.F R.g_on / (R.g_on + R.g_off); the diode branch carries about
R.g_on / (R.g_on + R.g_off) of the turn-off charge.

Run:  python build_gatepower_smath.py      -> mismatches: 0
      python check_sm.py ../../Smath/tools/Gate_Driver_Power_Unipolar.sm   -> VERDICT OK
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smsheet import Sheet                                          # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'Smath', 'tools', 'STGAP3SXS_Gate_Driver_Power.sm'))
S = Sheet('STGAP3SXS gate driver power', 'L6790A project',
          'STGAP3SXS dissipation and gate current, R_on and D + R_off')

S.h1('STGAP3SXS Gate Driver Calculation  -  GOUT, R.g_on and (D.off + R.g_off), +19 / -4.7 V')

S.h2('1  Inputs')
S.const('Turn-ON gate resistor R.g_on:', 'R.g_on', "22*'ohm", 'ohm', 2)
S.const('Turn-OFF gate resistor R.g_off (in series with D.off):', 'R.g_off', "2.2*'ohm",
        'ohm', 2)
S.const('D.off forward voltage at the peak current:', 'V.F', "0.5*'V", 'V', 2)
S.const('Module internal gate resistance R.G:', 'R.g_int', "0*'ohm", 'ohm', 2)
S.const('Gate charge, V.L -> V.H (Fig. 16) [10^-9 A s]:', 'Q.g', "1419*10^(-9)*'A*'s", None, 0)
S.const('Switching frequency:', 'f.sw', "20*'kHz", 'kHz', 1)
S.const('Gate drive voltage V.H (VH vs GNDISO):', 'V.H', "19*'V", 'V', 1)
S.const('Gate off voltage V.L (VL vs GNDISO):', 'V.L', "-4.7*'V", 'V', 1)
S.const('Logic supply V.DD:', 'V.DD', "5*'V", 'V', 1)
S.const('Input high duty:', 'D.in', '0.5', None, 2)
S.const('Source R.DS_ON, max:', 'R.on_H', "0.80*'ohm", 'ohm', 2)
S.const('Sink R.DS_ON, max:', 'R.on_L', "0.65*'ohm", 'ohm', 2)
S.const('Source / sink current capability, min:', 'I.drv', "7*'A", 'A', 1)
S.const('VH quiescent current, max:', 'I.QH', "6*'mA", 'mA', 1)
S.const('VDD quiescent current, IN+ low, max:', 'I.DD_lo', "2.5*'mA", 'mA', 1)
S.const('VDD quiescent current, IN+ high, max:', 'I.DD_hi', "13*'mA", 'mA', 1)
S.const('Thermal resistance junction-ambient [C/W]:', 'R.th_JA', '65', None, 0)
S.const('Module Q.gd at 800 V [10^-9 A s]:', 'Q.gd', "391*10^(-9)*'A*'s", None, 0)
S.const('Module C.iss - C.rss (800 V):', 'C.gs', "35.8*'nF", 'nF', 1)
S.const('Module gate threshold, min:', 'V.th_min', "1.9*'V", 'V', 1)
S.const('Bus voltage:', 'V.bus', "800*'V", 'V', 0)
S.const('Drain dv/dt at switching [V/ns]:', 'dvdt', '18.6', None, 1)

# intermediates, folded away (Sheet.set would not write them into the file)
S.area_begin('intermediate values - collapsed')
S.pack([('V.sw', 'V.H-V.L', 'V', 1),
        ('R.path_on', 'R.on_H+R.g_on+R.g_int', 'ohm', 3),
        ('R.eff', 'R.g_on*R.g_off/(R.g_on+R.g_off)', 'ohm', 3),
        ('V.eff', 'V.F*R.g_on/(R.g_on+R.g_off)', 'V', 3),
        ('R.path_off', 'R.on_L+R.eff+R.g_int', 'ohm', 3),
        ('C.eq', 'Q.g/V.sw', 'nF', 2),
        ('P.D_off', 'V.F*Q.g*f.sw*R.g_on/(R.g_on+R.g_off)', 'W', 4),
        ('P.off_R', 'Q.g*V.sw*f.sw/2-P.D_off', 'W', 4)], per=3)
S.area_end()

S.h2('2  Peak gate current')
S.row('- Source peak current (turn-on):', 'I.pk_on', 'V.sw/R.path_on', 'A', 2)
S.row('- Sink peak current (turn-off):', 'I.pk_off', '(V.sw-V.eff)/R.path_off', 'A', 2)
S.row('- D.off peak current:', 'I.pk_D', '(V.eff+I.pk_off*R.eff-V.F)/R.g_off', 'A', 2)
S.row('- driver current margin (>1):', 'k.I', 'I.drv/I.pk_off', None, 2)

S.h2('3  Rise and fall time')
S.row('- Gate rising time 10-90 %:', 't.r', 'ln(9)*R.path_on*C.eq', 'ns', 0)
S.row('- Gate falling time 90-10 %:', 't.f',
      "R.path_off*C.eq*ln(((0.9*V.sw-V.eff)/'V)/((0.1*V.sw-V.eff)/'V))", 'ns', 0)

S.h2('4  Power')
S.row('- Gate drive power, Q.g (V.H - V.L) f.sw:', 'P.G', 'Q.g*V.sw*f.sw', 'W', 3)
S.row('- Driver output stage, turn-on + turn-off:', 'P.out',
      'P.G/2*R.on_H/R.path_on+P.off_R*R.on_L/R.path_off', 'W', 3)
S.row('- Driver quiescent, VH and VDD:', 'P.Q',
      'I.QH*V.sw+V.DD*(D.in*I.DD_hi+(1-D.in)*I.DD_lo)', 'W', 3)
S.row('- Driver total dissipation:', 'P.D', 'P.out+P.Q', 'W', 3)
S.row('- R.g_on dissipation:', 'P.Ron',
      'P.G/2*R.g_on/R.path_on+P.off_R*R.eff/R.path_off*R.g_off/(R.g_on+R.g_off)', 'W', 3)
S.row('- R.g_off dissipation:', 'P.Roff', 'P.off_R*R.eff/R.path_off*R.g_on/(R.g_on+R.g_off)',
      'W', 3)

S.h2('5  Miller turn-on of the OFF switch')
S.row('- Drain swing time, V.bus / dv/dt:', 't.sw', "V.bus/dvdt*10^(-9)*'s/'V", 'ns', 0)
S.row('- Miller current into the off gate, Q.gd / t.sw:', 'i.M', 'Q.gd/t.sw', 'A', 2)
S.row('- Gate kick through the hold path (R.path_off, C.gs):', 'ΔV.g',
      "i.M*R.path_off*(1-exp(-(t.sw/'s)/((R.path_off*C.gs)/'s)))", 'V', 2)
S.row('- margin, (V.th_min - V.L) / ΔV.g (>1):', 'k.Miller', '(V.th_min-V.L)/ΔV.g', None, 2)

S.h2('6  Driver junction temperature')
S.const('Ambient temperature 1 [C]:', 'T.amb1', '25', None, 0)
S.row('- Junction temperature at T.amb1 [C]:', 'T.j1', "T.amb1+P.D/'W*R.th_JA", None, 0)
S.const('Ambient temperature 2 [C]:', 'T.amb2', '45', None, 0)
S.row('- Junction temperature at T.amb2 [C]:', 'T.j2', "T.amb2+P.D/'W*R.th_JA", None, 0)

if S.clashes:
    raise SystemExit('name clashes: %s' % S.clashes)
nbytes, ybottom = S.save(OUT)
print(f'written {OUT}\n  {nbytes} bytes, {ybottom} px tall, {len(S.r)} regions')

# ---------------------------------------------------------------- self-check
# independent nodal solution of the turn-off peak (gate at V.H, GOUT through R.on_L to V.L)
VH, VL, RL, RH, Ron, Roff, VF = 19.0, -4.7, 0.65, 0.80, 22.0, 2.2, 0.5
Vs = VH - VL                       # work relative to V.L
VB = (Vs / Ron + (Vs - VF) / Roff) / (1 / Ron + 1 / Roff + 1 / RL)
Qg, f = 1419e-9, 20e3
PG = Qg * Vs * f
PDoff = VF * Qg * f * Ron / (Ron + Roff)
Reff = Ron * Roff / (Ron + Roff)
tsw = 800 / 18.6e9
dV = 391e-9 / tsw * (RL + Reff) * (1 - math.exp(-tsw / ((RL + Reff) * 35.8e-9)))
ref = {'I.pk_on': Vs / (RH + Ron), 'I.pk_off': VB / RL, 'I.pk_D': (Vs - VB - VF) / Roff,
       'P.G': PG, 't.r': math.log(9) * (RH + Ron) * Qg / Vs, 'ΔV.g': dV,
       'k.Miller': (1.9 - VL) / dV,
       'P.D': PG / 2 * RH / (RH + Ron) + (PG / 2 - PDoff) * RL / (RL + Reff)
              + 6e-3 * Vs + 5 * (0.5 * 13e-3 + 0.5 * 2.5e-3)}
bad = 0
for k, v in ref.items():
    got = S.ns[k.replace('.', '__')]
    ok = abs(got - v) <= abs(v) * 1e-6
    bad += not ok
    print(f'  {k:10s} sheet={got:<12.6g} ref={v:<12.6g} {"OK" if ok else "** DIFF"}')
print(f'  mismatches: {bad}')
if bad:
    raise SystemExit(1)
