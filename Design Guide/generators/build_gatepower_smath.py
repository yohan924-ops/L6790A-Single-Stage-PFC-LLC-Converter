# -*- coding: utf-8 -*-
"""Builds  Smath/tools/Gate_Driver_Power_Unipolar.sm  -  gate driver dissipation and gate
current for a POSITIVE-ONLY (unipolar, 0 V off) gate drive (2026-11-02, user: "make a SMath
sheet that computes gate driver power dissipation / current for positive-voltage gate
driving, like this one" - the uploaded 21082025_Gate_Driver_Cal.sm).

Same inputs and the same results as that sheet (rise / fall time, peak source / sink current,
gate drive power, junction temperature at 25 and 45 C), plus what it left out:
  - the gate drive power splits over the driver output, the external resistor and the
    switch's internal gate resistor; only the driver's share heats the driver. The old sheet
    put ALL of Q.g V f.sw on the driver, which over-states its junction rise;
  - the driver's own quiescent power, the number of channels per package, the external
    resistor power, and checks against the driver's junction limit;
  - rise / fall time from the gate charge (C.eq = Q.g / V.H, Miller included) next to the
    old C.iss estimate.
With R.g_int = 0, I.Q = 0 and the share set aside, the example values reproduce the uploaded
sheet: t.r 152 ns, t.f 85 ns, 1.125 A / 2 A, 0.3213 W, +39 C.

Only + - * / ^ sqrt are used. Temperatures are plain numbers in C (SMath's degree units are
not used, they do not mix with the rest of this tool chain).

Run:  python build_gatepower_smath.py      -> mismatches: 0
      python check_sm.py ../../Smath/tools/Gate_Driver_Power_Unipolar.sm   -> VERDICT OK
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smsheet import Sheet                                          # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'Smath', 'tools', 'Gate_Driver_Power_Unipolar.sm'))
S = Sheet('Gate driver power - unipolar drive', 'L6790A project',
          'gate driver dissipation and gate current, positive-only gate drive')

S.h1('Gate Driver Calculation  -  positive-only gate drive (V.L = 0 V)')
S.note('Yellow cells are the inputs. The example values are those of the uploaded sheet '
       '(WG75N65MFW1, 18 V, 85 kHz) so the two can be compared; replace them with the switch '
       'and driver datasheet values. The driver dissipates only its share of the gate power - '
       'the rest goes into the external and internal gate resistors.')

# ------------------------------------------------------------------ inputs
S.h2('1  Transistor spec and circuitry value')
S.const('Turn-ON gate resistor (external):', 'R.g_on', "15*'ohm", 'ohm', 2)
S.const('Turn-OFF gate resistor (external):', 'R.g_off', "7.5*'ohm", 'ohm', 2)
S.const('Switch internal gate resistance (datasheet R.G):', 'R.g_int', "0*'ohm", 'ohm', 2,
        note='0 reproduces the uploaded sheet; the datasheet value moves part of the gate '
             'power from the driver and the external resistor into the switch.')
S.const('Switch input capacitance C.iss:', 'C.iss', "4307*'pF", 'pF', 0)
S.const('Switch total gate charge Q.g at V.H [nC x 10^-9 A s]:', 'Q.g', "210*10^(-9)*'A*'s", None, 0,
        note='Q.g must be read at the drive voltage V.H (gate charge curve), not at the '
             'datasheet test voltage.')
S.const('Switches driven per channel (paralleled):', 'n.par', '1', None, 0)

S.h2('2  Switching and gate driver spec')
S.const('Switching frequency:', 'f.sw', "85*'kHz", 'kHz', 1)
S.const('Turn-ON gate voltage V.H (driver supply):', 'V.H', "18*'V", 'V', 1)
S.const('Turn-OFF gate voltage V.L (unipolar drive):', 'V.L', "0*'V", 'V', 1,
        note='this sheet is for 0 V turn-off; V.H - V.L is the swing in every formula, '
             'so a negative V.L still computes, but then Q.g must be the charge over that swing.')
S.const('Driver internal high-side FET R.on (source):', 'R.on_H', "1*'ohm", 'ohm', 2)
S.const('Driver internal low-side FET R.on (sink):', 'R.on_L', "1.5*'ohm", 'ohm', 2)
S.const('Driver quiescent supply current I.Q:', 'I.Q', "0*'mA", 'mA', 2,
        note='0 reproduces the uploaded sheet; take the datasheet I.Q (all supplies) at V.H.')
S.const('Driven channels in the package (2 for a half-bridge driver):', 'N.ch', '1', None, 0)
S.const('Driver thermal resistance junction-ambient [C/W]:', 'R.th_JA', '120', None, 0)
S.const('Driver maximum junction temperature [C]:', 'T.j_max', '125', None, 0)

# ------------------------------------------------------------------ results
S.h2('3  Gate timing and peak current')
S.row('- Gate swing:', 'V.sw', 'V.H-V.L', 'V', 1)
S.row('- Equivalent gate capacitance from the charge, Q.g / swing:', 'C.eq',
      'n.par*Q.g/V.sw', 'nF', 2,
      note='includes the Miller charge, so it is larger than C.iss and gives the real timing.')
S.row('- Gate rising time 10-90 %, 2.2 (R.on_H + R.g_on + R.g_int) C.iss:', 't.r_iss',
      '2.2*(R.on_H+R.g_on+R.g_int)*n.par*C.iss', 'ns', 0)
S.row('- Gate falling time 90-10 %, 2.2 (R.on_L + R.g_off + R.g_int) C.iss:', 't.f_iss',
      '2.2*(R.on_L+R.g_off+R.g_int)*n.par*C.iss', 'ns', 0)
S.row('- Gate rising time 10-90 %, with C.eq:', 't.r', '2.2*(R.on_H+R.g_on+R.g_int)*C.eq',
      'ns', 0)
S.row('- Gate falling time 90-10 %, with C.eq:', 't.f', '2.2*(R.on_L+R.g_off+R.g_int)*C.eq',
      'ns', 0)
S.row('- Gate source peak current at rising:', 'I.pk_on',
      'V.sw/(R.on_H+R.g_on+R.g_int/n.par)', 'A', 3,
      note='compare with the driver\'s source current rating.')
S.row('- Gate sink peak current at falling:', 'I.pk_off',
      'V.sw/(R.on_L+R.g_off+R.g_int/n.par)', 'A', 3,
      note='flows into the driver; compare with its sink current rating.')

S.h2('4  Power')
S.row('- Gate drive power per channel, Q.g V.sw f.sw:', 'P.G', 'n.par*Q.g*V.sw*f.sw', 'W', 4,
      note='half is lost at turn-on, half at turn-off, independent of the resistors.')
S.row('- Driver share at turn-on, R.on_H / (R.on_H + R.g_on + R.g_int):', 'x.on',
      'R.on_H/(R.on_H+R.g_on+R.g_int/n.par)', None, 4)
S.row('- Driver share at turn-off, R.on_L / (R.on_L + R.g_off + R.g_int):', 'x.off',
      'R.on_L/(R.on_L+R.g_off+R.g_int/n.par)', None, 4)
S.row('- Driver dissipation per channel:', 'P.drv_ch', 'P.G/2*(x.on+x.off)', 'W', 4)
S.row('- Turn-ON resistor dissipation (each switch):', 'P.Rg_on',
      'P.G/2*R.g_on/(R.on_H+R.g_on+R.g_int/n.par)/n.par', 'W', 4,
      note='with n.par > 1 each switch has its own R.g_on of this value.')
S.row('- Turn-OFF resistor dissipation (each switch):', 'P.Rg_off',
      'P.G/2*R.g_off/(R.on_L+R.g_off+R.g_int/n.par)/n.par', 'W', 4)
S.row('- Driver package dissipation, all channels + quiescent:', 'P.D',
      'N.ch*P.drv_ch+I.Q*V.H', 'W', 4)
S.row('- The uploaded sheet\'s "PD" for comparison, N.ch P.G:', 'P.D_old', 'N.ch*P.G', 'W', 4,
      note='all gate power counted in the driver - an upper bound, reached only with no '
           'external or internal gate resistance.')

S.h2('5  Driver junction temperature')
S.row('- Junction rise [C]:', 'ΔT.j', "P.D/'W*R.th_JA", None, 1)
S.const('Ambient temperature 1 [C]:', 'T.amb1', '25', None, 0)
S.row('- Junction temperature at T.amb1 [C]:', 'T.j1', 'T.amb1+ΔT.j', None, 1)
S.row('- margin to T.j_max at T.amb1 (>1):', 'k.Tj1', '(T.j_max-T.amb1)/ΔT.j', None, 2)
S.const('Ambient temperature 2 [C]:', 'T.amb2', '45', None, 0)
S.row('- Junction temperature at T.amb2 [C]:', 'T.j2', 'T.amb2+ΔT.j', None, 1)
S.row('- margin to T.j_max at T.amb2 (>1):', 'k.Tj2', '(T.j_max-T.amb2)/ΔT.j', None, 2)
S.row('- Highest ambient the driver allows [C]:', 'T.amb_max', 'T.j_max-ΔT.j', None, 1)
S.row('- The uploaded sheet\'s junction rise for comparison [C]:', 'ΔT.j_old',
      "P.D_old/'W*R.th_JA", None, 1)

if S.clashes:
    raise SystemExit('name clashes: %s' % S.clashes)
nbytes, ybottom = S.save(OUT)
print(f'written {OUT}\n  {nbytes} bytes, {ybottom} px tall, {len(S.r)} regions')

# ---------------------------------------------------------------- self-check
# the uploaded sheet's printed results, and the split computed by hand
ref = {'t.r_iss': 152e-9, 't.f_iss': 85e-9, 'I.pk_on': 1.125, 'I.pk_off': 2.0,
       'P.G': 0.3213, 'ΔT.j_old': 38.556,
       'P.drv_ch': 0.3213 / 2 * (1 / 16 + 1.5 / 9), 'C.eq': 210e-9 / 18}
bad = 0
for k, v in ref.items():
    got = S.ns[k.replace('.', '__')]
    tol = 0.005 if k in ('t.r_iss', 't.f_iss') else 1e-4
    ok = abs(got - v) <= abs(v) * tol
    bad += not ok
    print(f'  {k:10s} sheet={got:<12.6g} ref={v:<12.6g} {"OK" if ok else "** DIFF"}')
print(f'  mismatches: {bad}')
if bad:
    raise SystemExit(1)
