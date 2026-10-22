# -*- coding: utf-8 -*-
"""Gate driver selection and start-up in the three workbooks (2026-10-22, user, three rounds:
"too many parameters; start-up into Res. Tank Design, simpler names, no duplicate OCP1/2; the
gate driver in the switch section; recommended value first, mine next; only the checks that
matter; a simple schematic" - "no guarantee the driver is an L6498LD: make it like the MOSFET
selection" - "R.on / R.off have no recommendation, I cannot tell whether the selected values
are right, no verdict on the driver dissipation, the picture is fixed to L6498LD; add the
OCP1 start-up margin, the driver's maximum frequency, drivers with their own dead time").

Power Components, inside the LLC half-bridge switch section (xl_rows.py inserts the rows -
everything below moves down, references follow), in the sheets' own pattern (Device Setting's
CT.max / CT.min / "Select CT between", RT.ceil with its Selected Value on the same row):
  76-83    the switch's gate data, in its own yellow parameter block next to Rdson / Coss:
           C.g (Qg slope above the plateau)  C.gs.dev  R.g  V.pl  V.th  V.th.min  Q.gd  V.gs.max
  89-176   two blank rows, then "LLC Half Bridge Gate Driver Selection" at 91, two blank rows after:
           - the driver part number and its datasheet values (yellow): I.so I.si V.test
             R.o.src R.o.sink (0 = derive from V.test / I.so, I.si) V.cc.min V.cc.max t.pd MT
             t.DT (own dead time, 0 = none) f.max I.Q Rth.drv Tj.max V.bo.min dV/dt.max
             V.hs.max V.IH.max Ta.drv
           - the bootstrap diode part number and V.F V.RRM I.F I.FSM; the turn-off diode part
             number and V.F (0 = no diode: separate GOFF pin) I.F I.FSM
           - the gate network as limit rows and separate Select rows (Value = suggestion,
             Selected Value = the design), no check here: V.drv.max / .min / V.drv;
             R.on.max (gate at 10 V within the shorter pulse) / R.on.min (driver temperature
             AND driver source current) / R.on (E12); R.off.eff.max (min of: overlap - off
             before the other side reaches V.th min; soft turn-off - V.pl -> V.th within the
             run swing; Miller unless the gate's own C.gs holds) / R.off.min (driver sink
             current, D.off surge) / R.off (E12); C.gs.max (10 V within the pulse with the
             selected R.on) / C.gs.min (Miller) / C.gs; C.boot.max / .min / C.boot (E6);
             R.boot.max / R.boot.min (D.boot surge) / R.boot (E12)
           - the final quantities, twelve with a Check: R.so R.si I.G.on.pk I.G.off.pk k.IG(*)
             R.off.eff(*) t.D.need t.D.max k.tD(*) t.D.su.min t.D.su.max k.tD.su(*) V.g.su(*)
             V.bs.1(*) V.bs.min k.Miller(*) dv/dt.su k.drv(*) P.drv.max P.drv(*) Tj.drv f.SU(*)
             P.Ron P.Roff I.boot.pk I.boot.avg V.RRM.need k.D.boot(*) I.off.pk I.off.avg
             k.D.off(*)
           - the schematic (xl_gate_fig.py, no part named) at column G
BOM&Schematics 91-105  "Gate driver and gate network": PN table (U.drv1/2, D.boot, D.off) and a
  value table (V.drv R.on R.off C.gs C.boot R.boot), live links; the frame's bottom row moves down.
  old rows 76-80 -> 84-88, old 81-119 (the secondary section) -> 177-215.
Res. Tank Design 81-87  start-up with the output near 0 V: I.su, k.su.OCP2 and k.su.OCP1 (both
  checked, Device Setting G49 / D49), f.su.OCP1.
CC 77-   the working (the model of gate_budget.py) and the two L6790A assumptions (start-up dead
  time 420 ns, FB bus 235 V).

    python gate_xl.py          all three books, idempotent (CHANGELOG mark)
"""
import os
import re

import xlsx_patch as X
import xl_rows
from measured200_xl import sheet_parts

HERE = os.path.dirname(os.path.abspath(__file__))
XL = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet'))
PNG = os.path.normpath(os.path.join(HERE, '..', 'figures', 'xl_gate_drive.png'))
MARK = 'gate driver selection in the switch section, start-up in Res. Tank Design'
AT1, N1 = 76, 8                     # switch gate data
AT2 = 89                            # gate driver section starts here (after the first insert); N2 below

SHEET = dict(V=15.0, Ron=4.7, Roff=2.2, VF=0.7, Cgs=0, Cb=470, Rb=0, VFb=1.3, IFSMb=30, IFb=1.0, VRRMb=600,
             pboot='ES1J', poff='1N4148W', IFo=0.3, IFSMo=2.0,
             note='design sheet section 14c.1 parts (R.G 4.7, R.G_off 2.2 ohm + 1N4148W, C.BOOT 470 nF, ES1J '
                  'V.F 1.3 V, no series resistor) at V.drv 15 V (user, 2026-10-22; the sheet regulator is 12.85-14.35 V)')
BOOKS = {
    'GUIDE_PQ50_657W_workbook_rev0_6_unencrypted.xlsx': SHEET,
    os.path.join('variants', '3CORE_670W_workbook_unencrypted.xlsx'): SHEET,
    os.path.join('variants', 'BENCH_200W_LGE_workbook_unencrypted.xlsx'): dict(
        V=18.0, Ron=47.0, Roff=10.0, VF=0.7, Cgs=0, Cb=100, Rb=3.3, VFb=1.0, IFSMb=35, IFb=1.0, VRRMb=600,
        pboot='MURS160', poff='1N4148WS', IFo=0.15, IFSMo=2.0,
        note='LGE bench board: VCC_GD 18 V, R115 47 ohm, R114 10 ohm + 1N4148WS, C63/C72 100 nF, '
             'MURS160 (V.F 1.0 V), boot resistor R113/R155 10 -> 3.3 ohm (user, 2026-10-21)'),
}
DV, DS, RT, PCq = "'Device Setting'!", "'Design Spec'!", "'Res. Tank Design'!", "'Power Components'!"


def e12f(x):
    """the E12 value at or below x"""
    y = '(%s)*1.000001' % x
    return ('IF((%s)<=0,0,10^INT(LOG10(%s))*LOOKUP(%s/10^INT(LOG10(%s)),'
            '{1,1.2,1.5,1.8,2.2,2.7,3.3,3.9,4.7,5.6,6.8,8.2}))' % (x, y, y, y))


def e6c(x):
    """the E6 value at or above x"""
    y = '(%s)*0.999999' % x
    return ('IF((%s)<=0,0,-10^INT(LOG10(%s))*LOOKUP(-%s/10^INT(LOG10(%s)),'
            '{-10,-6.8,-4.7,-3.3,-2.2,-1.5,-1}))' % (x, y, y, y))


#  STO60N045DM9 DS14711 Rev 4 (Figures 4-6 read as vectors, gate_wave.py) - one set for all books
MOS_ROWS = [   # key, label, name, value, unit
    ('Cg', 'Gate capacitance above the plateau, Qg slope (per device)', 'C.g', 7.5, 'nF'),
    ('Cgsd', 'Gate-source capacitance C.iss - C.rss (per device)', 'C.gs.dev', 4.76, 'nF'),
    ('Rgi0', 'Internal gate resistance (per device)', 'R.g', 4.5, 'Ω'),
    ('Vpl', 'Miller plateau voltage', 'V.pl', 6.3, 'V'),
    ('Vth', 'Gate threshold, typ (for timing)', 'V.th', 4.0, 'V'),
    ('Vthm', 'Gate threshold, min', 'V.th.min', 3.5, 'V'),
    ('Qgd', 'Miller charge over the bus swing (per device)', 'Q.gd', 13, 'nC'),
    ('Vgsmax', 'Gate-source voltage rating', 'V.gs.max', 20, 'V'),
]

#  gate driver rows from AT2: (key, kind, label, name, D, unit, F, G)
#  kind: title / part / head / data (yellow D) / net (D recommended, F yellow, G range) / res (D, F check)
DRV_ROWS = [
    ('gapA', 'gap', None, None, None, None, None, None),       # two blank rows after the switch section
    ('gapB', 'gap', None, None, None, None, None, None),
    ('t', 'title', 'LLC Half Bridge Gate Driver Selection', None, None, None, None, None),
    ('part', 'part', 'Please Select a dedicated Gate Driver part number ', 'L6498LD', None, None, None, None),
    ('h1', 'head', 'Parameter', 'Name', 'Value', 'Unit', None, None),
    ('Iso', 'data', 'Source current, min (full temperature)', 'I.so', 1.4, 'A', None, None),
    ('Isi', 'data', 'Sink current, min (full temperature)', 'I.si', 1.55, 'A', None, None),
    ('Vt', 'data', 'Supply voltage those currents are given at', 'V.test', 15, 'V', None, None),
    ('Rosrc', 'data', 'Output resistance, source (0 = derive as V.test / I.so)', 'R.o.src', 0, 'Ω', None, None),
    ('Rosnk', 'data', 'Output resistance, sink (0 = derive as V.test / I.si)', 'R.o.sink', 0, 'Ω', None, None),
    ('Vccmin', 'data', 'Supply voltage, recommended min', 'V.cc.min', 10, 'V', None, None),
    ('Vccmax', 'data', 'Supply voltage, recommended max', 'V.cc.max', 20, 'V', None, None),
    ('tpd', 'data', 'Propagation delay, typ', 't.pd', 85, 'ns', None, None),
    ('MT', 'data', 'Delay matching, max', 'MT', 30, 'ns', None, None),
    ('tDT', 'data', 'Internal dead time (0 = none, interlocking only)', 't.DT', 0, 'ns', None, None),
    ('fmax', 'data', 'Maximum switching frequency', 'f.max', 800, 'kHz', None, None),
    ('IQ', 'data', 'Quiescent current, VCC + floating, max', 'I.Q', 0.6, 'mA', None, None),
    ('Rth', 'data', 'Thermal resistance junction-ambient', 'Rth.drv', 120, '˚C/W', None, None),
    ('Tjmax', 'data', 'Junction temperature, recommended max', 'Tj.max', 125, '˚C', None, None),
    ('Vbo', 'data', 'Floating (bootstrap) supply, recommended min', 'V.bo.min', 9.3, 'V', None, None),
    ('dVdt', 'data', 'Output (HS pin) slew rate immunity', 'dV/dt.max', 50, 'V/ns', None, None),
    ('Vhs', 'data', 'HS pin DC voltage rating', 'V.hs.max', 480, 'V', None, None),
    ('VIH', 'data', 'Logic input high threshold, max', 'V.IH.max', 2.5, 'V', None, None),
    ('Ta', 'data', 'Operating ambient temperature of the driver', 'Ta.drv', 25, '˚C', None, None),
    ('pboot', 'part', 'Please Select the bootstrap diode part number ', 'ES1J', None, None, None, None),
    ('h1b', 'head', 'Parameter', 'Name', 'Value', 'Unit', None, None),
    ('VFb', 'data', 'Forward voltage at the charging current', 'V.F.boot', 1.3, 'V', None, None),
    ('VRRMb', 'data', 'Repetitive reverse voltage', 'V.RRM.boot', 600, 'V', None, None),
    ('IFb', 'data', 'Average forward current', 'I.F.boot', 1.0, 'A', None, None),
    ('IFSMb', 'data', 'Non-repetitive surge current (8.3 ms)', 'I.FSM.boot', 30, 'A', None, None),
    ('poff', 'part', 'Please Select the turn-off diode part number (none = separate GOFF pin) ', '1N4148W', None, None,
     None, None),
    ('h1c', 'head', 'Parameter', 'Name', 'Value', 'Unit', None, None),
    ('VF', 'data', 'Forward voltage (0 = no D.off, R.off alone on GOFF)', 'V.F.off', 0.7, 'V', None, None),
    ('IFo', 'data', 'Average forward current', 'I.F.off', 0.3, 'A', None, None),
    ('IFSMo', 'data', 'Non-repetitive surge current (1 us)', 'I.FSM.off', 2.0, 'A', None, None),
    ('h2', 'head', 'Parameters', 'Name', 'Value', 'Unit', 'Selected Value', None),
    ('Vmax', 'max', 'Maximum gate drive voltage (driver supply range)', 'V.drv.max', '{cc:Vmax}', 'V', None, None),
    ('Vmin', 'max', 'Minimum gate drive voltage (10 V at the high-side gate)', 'V.drv.min', '{cc:Vmin}', 'V', None, None),
    ('V', 'net', 'Select V.drv between V.drv.min and V.drv.max', 'V.drv', None, 'V', 'in', None),
    ('Ronmax', 'max', 'Maximum turn-on resistor (gate at 10 V within the start-up pulse)', 'R.on.max', '{cc:Ronmax}', 'Ω',
     None, None),
    ('Ronmin', 'max', 'Minimum turn-on resistor: driver temperature, source current (0 = R.so alone covers them)', 'R.on.min', '{cc:Ronmin}',
     'Ω', None, None),
    ('Ron', 'net', 'Select R.on between R.on.min and R.on.max (Value: E12)', 'R.on', '{cc:Ronrec}', 'Ω', 'in', None),
    ('Reffmax', 'max', 'Maximum turn-off path resistance (off before the swing ends and the other side is on)',
     'R.off.eff.max', '{cc:Reffmax}', 'Ω', None, None),
    ('Roffmin', 'max', 'Minimum turn-off resistor: sink current, D.off surge (0 = R.si alone covers them)', 'R.off.min', '{cc:Roffmin}', 'Ω',
     None, None),
    ('Roff', 'net', 'Select R.off: with D.off || R.on, or alone on GOFF (Value: E12)', 'R.off', '{cc:Roffrec}', 'Ω', 'in',
     None),
    ('Cgsmax', 'max', 'Maximum gate-source capacitor (gate still at 10 V within the start-up pulse with R.on)', 'C.gs.max',
     '{cc:Cgsmax}', 'nF', None, None),
    ('Cgsmin', 'max', 'Minimum gate-source capacitor against the Miller kick (0 = the turn-off path alone holds)', 'C.gs.min',
     '{cc:Cgsmin}', 'nF', None, None),
    ('Cgs', 'net', 'Select C.gs (Value: E6)', 'C.gs', '{cc:Cgsrec}', 'nF', 'in', None),
    ('Cbmax', 'max', 'Maximum bootstrap capacitor (first LOUT pulse charges it to V.bo.min)', 'C.boot.max', '{cc:Cbmax}',
     'nF', None, None),
    ('Cbmin', 'max', 'Minimum bootstrap capacitor (10 x gate capacitance)', 'C.boot.min', '{cc:Cbmin}', 'nF', None, None),
    ('Cb', 'net', 'Select C.boot between C.boot.min and C.boot.max (Value: E6)', 'C.boot', '{cc:Cbrec}', 'nF', 'in', None),
    ('Rbmax', 'max', 'Maximum bootstrap resistor (first LOUT pulse charges C.boot to V.bo.min)', 'R.boot.max',
     '{cc:Rbmax}', 'Ω', None, None),
    ('Rbmin', 'max', 'Minimum bootstrap resistor (D.boot surge into an empty C.boot)', 'R.boot.min', '{cc:Rbmin}', 'Ω',
     None, None),
    ('Rb', 'net', 'Select R.boot between R.boot.min and R.boot.max (Value: E12)', 'R.boot', '{cc:Rbrec}', 'Ω', 'in', None),
    ('h3', 'head', 'Parameters', 'Name', 'Value', 'Unit', 'Check', None),
    ('Rso', 'res', 'Driver output resistance in use, source (in series with R.on)', 'R.so', '{cc:Rso}', 'Ω', None, None),
    ('Rsi', 'res', 'Driver output resistance in use, sink (in series with R.off)', 'R.si', '{cc:Rsi}', 'Ω', None, None),
    ('Ion', 'res', 'Peak gate current, turn-on', 'I.G.on.pk', '{cc:Ion}', 'A', None, None),
    ('Ioff', 'res', 'Peak gate current, turn-off', 'I.G.off.pk', '{cc:Ioff}', 'A', None, None),
    ('kIG', 'res', 'Driver current margin: I.so / I.G.on.pk and I.si / I.G.off.pk (>1)', 'k.IG', '{cc:kIG}', '-',
     'IF({kIG}>=1,"OK","CHECK")', None),
    ('Reff', 'res', 'Turn-off path resistance (<= R.off.eff.max)', 'R.off.eff', '{cc:Reff}', 'Ω',
     'IF({Reff}<={Reffmax},"OK","CHECK")', None),
    ('tD', 'res', 'Dead time needed in run (IC ADT 40-420 ns, or the driver t.DT)', 't.D.need', '{cc:tDneed}', 'ns', None, None),
    ('tDmax', 'res', 'Dead time allowed in run (gate on before the current reverses)', 't.D.max', '{cc:tDmax}', 'ns', None, None),
    ('ktD', 'res', 'Dead time margin in run (>1)', 'k.tD', '{cc:ktD}', '-', 'IF({ktD}>=1,"OK","CHECK")', None),
    ('tDsulo', 'res', 'Start-up dead time needed (gate delays + swing at I.su, FB and HB)', 't.D.su.min', '{cc:tDsulo}', 'ns',
     None, None),
    ('tDsuhi', 'res', 'Start-up dead time allowed (channel on before the current reverses, T/4 at f.SU)', 't.D.su.max',
     '{cc:tDsuhi}', 'ns', None, None),
    ('ktDsu', 'res', 'Start-up dead time margin at the IC 420 ns (CC) or the driver t.DT (>1)', 'k.tD.su', '{cc:ktDsu}', '-',
     'IF({ktDsu}>=1,"OK","CHECK")', None),
    ('Vg', 'res', 'Gate voltage at the end of the start-up pulse (>= 10 V)', 'V.g.su', '{cc:Vgsu}', 'V',
     'IF({Vg}>=10,"OK","CHECK")', None),
    ('Vbs1', 'res', 'V.BS after the first LOUT pulse (>= V.bo.min)', 'V.bs.1', '{cc:Vbs1}', 'V',
     'IF({Vbs1}>={Vbo},"OK","CHECK")', None),
    ('Vbs', 'res', 'V.BS lowest, steady at f.SU', 'V.bs.min', '{cc:Vbsmin}', 'V', None, None),
    ('kM', 'res', 'Gate-off margin against the Miller kick (>1)', 'k.Miller', '{cc:kM}', '-', 'IF({kM}>=1,"OK","CHECK")', None),
    ('dvdt', 'res', 'Midpoint dv/dt at start-up (I.su / c.HB)', 'dv/dt.su', '{cc:dvdt}', 'V/ns', None, None),
    ('kdrv', 'res', 'Driver ratings margin: dV/dt, HS pin voltage, L6790A V.OH 4 V vs V.IH.max (>1)', 'k.drv', '{cc:kdrv}',
     '-', 'IF({kdrv}>=1,"OK","CHECK")', None),
    ('Pallow', 'res', 'Maximum driver dissipation at Ta.drv: (Tj.max - Ta.drv) / Rth', 'P.drv.max', '{cc:Pallow}', 'W', None, None),
    ('Pdrv', 'res', 'Driver dissipation at f.Max, both sides (<= P.drv.max)', 'P.drv', '{cc:Pdrv}', 'W',
     'IF({Pdrv}<={Pallow},"OK","CHECK")', None),
    ('Tj', 'res', 'Driver junction temperature at f.Max and Ta.drv', 'Tj.drv', '{cc:Tj}', '˚C', None, None),
    ('fsw', 'res', 'Start-up frequency f.SU (<= driver f.max and L6790A 675 kHz)', 'f.SU', DV + '$D$29', 'kHz',
     'IF({fsw}<=MIN({fmax},{cc:fIC}),"OK","CHECK")', None),
    ('PRon', 'res', 'R.on dissipation at f.Max (package rating >= 2x)', 'P.Ron', '{cc:PRon}', 'W', None, None),
    ('PRoff', 'res', 'R.off dissipation at f.Max (package rating >= 2x)', 'P.Roff', '{cc:PRoff}', 'W', None, None),
    ('Ibpk', 'res', 'D.boot peak current into an empty C.boot', 'I.boot.pk', '{cc:Ibpk}', 'A', None, None),
    ('Ibavg', 'res', 'D.boot average current at f.Max', 'I.boot.avg', '{cc:Ibavg}', 'mA', None, None),
    ('VRRMn', 'res', 'D.boot reverse voltage seen: V.bus.max + V.drv', 'V.RRM.need', '{cc:VRRMn}', 'V', None, None),
    ('kDb', 'res', 'D.boot margin: V.RRM, I.FSM / I.boot.pk, I.F / I.boot.avg (>1)', 'k.D.boot', '{cc:kDb}', '-',
     'IF({kDb}>=1,"OK","CHECK")', None),
    ('Iopk', 'res', 'D.off peak current (gate at V.drv through R.off)', 'I.off.pk', '{cc:Iopk}', 'A', None, None),
    ('Ioavg', 'res', 'D.off average current at f.Max', 'I.off.avg', '{cc:Ioavg}', 'mA', None, None),
    ('kDo', 'res', 'D.off margin: I.FSM / I.off.pk, I.F / I.off.avg (>1; "-" without D.off)', 'k.D.off', '{cc:kDo}', '-',
     'IF({VF}=0,"-",IF({kDo}>=1,"OK","CHECK"))', None),
]
N2 = len(DRV_ROWS) + 2                    # two blank rows before the secondary section
DRV_ROWS += [('gap%d' % i, 'gap', None, None, None, None, None, None) for i in range(2)]

#  CC working: (key, label, value / formula, unit, is_data). {pc:key} = the Selected Value of a
#  network row, {d:key} = the D cell of a driver or switch data row
CC0 = 77
CC_ROWS = [
    ('title', 'Gate drive working - feeds Power Components 76-82 and 88-177', None, None, False),
    ('tDsu', 'L6790A dead time at start-up, before ADT (DS gives none) [assumed]', 420, 'ns', True),
    ('fIC', 'L6790A maximum operating frequency (DS: upper limited to about 675 kHz)', 675, 'kHz', True),
    ('VbFB', 'L6790A highest FB bus = HB/FB morphing threshold (DS V.HVPK_BOH)', 235, 'V', True),
    ('Rso', 'Driver source resistance: R.o.src, or V.test / I.so', 'IF({d:Rosrc}>0,{d:Rosrc},{d:Vt}/{d:Iso})', 'Ω', False),
    ('Rsi', 'Driver sink resistance: R.o.sink, or V.test / I.si', 'IF({d:Rosnk}>0,{d:Rosnk},{d:Vt}/{d:Isi})', 'Ω', False),
    ('V', 'V.drv (selected)', '{pc:V}', 'V', False),
    ('Vmin', 'V.drv min: driver range, and 10 V at the high-side gate after D.boot', 'MAX({d:Vccmin},10+{d:VFb})', 'V', False),
    ('Vmax', 'V.drv max: driver range and the MOSFET V.gs rating', 'MIN({d:Vccmax},{d:Vgsmax})', 'V', False),
    ('Vbus', 'Highest bus: sqrt(2) x VAC.max', 'SQRT(2)*%s$D$14' % DS, 'V', False),
    ('CG', 'Gate capacitance per position: n.par x C.g + C.gs', PCq + '$D$68*{d:Cg}+{pc:Cgs}', 'nF', False),
    ('Rgi', 'Internal gate resistance per position', '{d:Rgi0}/' + PCq + '$D$68', 'Ω', False),
    ('Reff', 'Turn-off path resistance',
     'IF({d:VF}=0,{pc:Roff},IF({pc:Roff}>0,{pc:Roff}*{pc:Ron}/({pc:Roff}+{pc:Ron}),{pc:Ron}))', 'Ω', False),
    ('Veff', 'Turn-off path offset (D.off)', 'IF(AND({d:VF}>0,{pc:Roff}>0),{d:VF}*{pc:Ron}/({pc:Roff}+{pc:Ron}),0)',
     'V', False),
    ('ton_', 'τ.on = (R.so + R.on + R.gi) C.G', '({Rso}+{pc:Ron}+{Rgi})*{CG}', 'ns', False),
    ('toff_', 'τ.off = (R.si + R.off.eff + R.gi) C.G', '({Rsi}+{Reff}+{Rgi})*{CG}', 'ns', False),
    ('tL1', 'Start-up pulse T/2 - max(t.D.su, t.DT) (also the first LOUT pulse)',
     '10^6/(2*%s$D$29)-MAX({tDsu},{d:tDT})' % DV, 'ns', False),
    ('trun', 'Pulse at f.Max: T/2 - t.D', '10^6/(2*%s$D$27)-MAX(%s$D$47,{d:tDT})' % (DV, DS), 'ns', False),
    ('Vgsu', 'Gate voltage at the end of the start-up pulse', '{V}*(1-EXP(-{tL1}/{ton_}))', 'V', False),
    ('Vgrun', 'Gate voltage at the end of the f.Max pulse', '{V}*(1-EXP(-{trun}/{ton_}))', 'V', False),
    ('Eon', 'Energy per turn-on at f.Max', '{CG}*{Vgrun}*({V}-{Vgrun}/2)', 'nJ', False),
    ('Eoff', 'Energy per turn-off at f.Max', '{CG}*{Vgrun}^2/2', 'nJ', False),
    ('xon', 'Driver share of the turn-on energy', '{Rso}/({Rso}+{pc:Ron}+{Rgi})', '-', False),
    ('xoff', 'Driver share of the turn-off energy', '{Rsi}/({Rsi}+{Reff}+{Rgi})', '-', False),
    ('Pdrv', 'Driver power at f.Max, both positions + quiescent',
     '2*({Eon}*{xon}+{Eoff}*{xoff})*%s$D$27*10^-6+{d:IQ}*{V}/1000' % DV, 'W', False),
    ('Pallow', 'Driver power allowed: (Tj.max - Ta.drv) / Rth', '({d:Tjmax}-{d:Ta})/{d:Rth}', 'W', False),
    ('Pbud', 'Driver gate-power budget: allowed - quiescent', '{Pallow}-{d:IQ}*{V}/1000', 'W', False),
    ('xneed', 'Turn-on share the budget allows',
     '({Pbud}-2*{Eoff}*{xoff}*%s$D$27*10^-6)/(2*{Eon}*%s$D$27*10^-6)' % (DV, DV), '-', False),
    ('RonminT', 'R.on min for the driver temperature',
     'IF({xneed}<=0,"lower V.drv",MAX(0,{Rso}/{xneed}-{Rso}-{Rgi}))', 'Ω', False),
    ('RonminI', 'R.on min for the driver source current: V.drv / I.so - R.so - R.gi', 'MAX(0,{V}/{d:Iso}-{Rso}-{Rgi})', 'Ω', False),
    ('Ronmin', 'R.on min: the larger of the two', 'IF(ISNUMBER({RonminT}),MAX({RonminT},{RonminI}),{RonminT})', 'Ω', False),
    ('Ronmax', 'R.on max: the gate reaches 10 V within the shorter pulse (start-up, f.Max)',
     'IF({V}>10,MIN({tL1},{trun})/({CG}*LN({V}/({V}-10)))-{Rso}-{Rgi},0)', 'Ω', False),
    ('Cgsmax', 'C.gs max: the gate still reaches 10 V within that pulse with the selected R.on',
     'IF({V}>10,MAX(0,MIN({tL1},{trun})/(({Rso}+{pc:Ron}+{Rgi})*LN({V}/({V}-10)))-%s$D$68*{d:Cg}),0)' % PCq, 'nF', False),
    ('Ronrec', 'R.on recommended: the log middle of min .. max, E12 below',
     'IF(ISNUMBER({Ronmin}),' + e12f('SQRT(MAX({Ronmin},1)*MAX({Ronmax},1))') + ',{Ronmin})', 'Ω', False),
    ('TTrun', 'Midpoint swing in run: c.HB V.bus,max / I.Lm.pk',
     '%s$D$46*SQRT(2)*%s$D$14/%s$D$73/1000' % (DS, DS, RT), 'ns', False),
    ('TTsu', 'Midpoint swing at start-up: c.HB V.bus,FB / I.su', '%s$D$46*{VbFB}/%s$D$84/1000' % (DS, RT), 'ns', False),
    ('iM', 'Miller current into an off gate during the faster swing',
     PCq + '$D$68*{d:Qgd}/MIN({TTrun},{TTsu})', 'A', False),
    ('dVr', 'Gate kick, resistive estimate: i.M x sink path', '{iM}*({Rsi}+{Reff}+{Rgi})', 'V', False),
    ('dVc', 'Gate kick, capacitive bound: Q.gd / (C.gs + C.gs option)',
     PCq + '$D$68*{d:Qgd}/(%s$D$68*{d:Cgsd}+{pc:Cgs})' % PCq, 'V', False),
    ('kM', 'k.Miller = V.th min / the smaller kick', '{d:Vthm}/MIN({dVr},{dVc})', '-', False),
    ('Cgsmin', 'C.gs needed (0 if the gate holds without it)',
     'IF(MIN({dVr},{dVc})<={d:Vthm},0,MAX(0,%s$D$68*({d:Qgd}/{d:Vthm}-{d:Cgsd})))' % PCq, 'nF', False),
    ('Cgsrec', 'C.gs suggested: E6 above the need', 'IF({Cgsmin}=0,0,' + e6c('{Cgsmin}') + ')', 'nF', False),
    ('ton', 't.on: IC edge -> V.th', '{d:tpd}+{ton_}*LN({V}/({V}-{d:Vth}))', 'ns', False),
    ('tonpl', 'IC edge -> plateau on the way up', '{d:tpd}+{ton_}*LN({V}/({V}-{d:Vpl}))', 'ns', False),
    ('toff', 't.off: IC edge -> below V.th min',
     'IF({d:Vthm}>{Veff},{d:tpd}+{toff_}*LN(({V}-{Veff})/({d:Vthm}-{Veff})),"never")', 'ns', False),
    ('toffpl', 'IC edge -> plateau on the way down', '{d:tpd}+{toff_}*LN(({V}-{Veff})/({d:Vpl}-{Veff}))', 'ns', False),
    ('tDneed', 't.D.need = (t.off.pl - t.pd) + swing - (t.on - t.pd) + MT', '{toffpl}-{ton}+{TTrun}+{d:MT}', 'ns', False),
    ('tDmax', 't.D.max = T/4 at f.Max + (t.off.pl - t.on.pl) - MT: on at the plateau before the reversal',
     '10^6/(4*%s$D$27)+{toffpl}-{tonpl}-{d:MT}' % DV, 'ns', False),
    ('ktD', 'k.tD = min(max(420, t.DT) / need, t.D.max / max(need, t.DT))',
     'MIN(MAX(420,{d:tDT})/{tDneed},{tDmax}/MAX({tDneed},{d:tDT}))', '-', False),
    ('IsuHB', 'Start-up edge current, HB on V.bus.max / 2', '({Vbus}/2)/%s$D$52*TAN(PI()*%s$D$55/(2*%s$D$29))' % (RT, RT, DV), 'A', False),
    ('TTsuHB', 'Midpoint swing at start-up, HB: c.HB V.bus.max / I.su.HB', '%s$D$46*{Vbus}/{IsuHB}/1000' % DS, 'ns', False),
    ('toffsu', 'Turn-off delay to the plateau from V.g.su (no t.pd)', '{toff_}*LN(({Vgsu}-{Veff})/({d:Vpl}-{Veff}))', 'ns', False),
    ('tDsulo', 't.D.su.min = t.off.su + max(T.T.su FB, HB) - (t.on - t.pd) + MT', '{toffsu}+MAX({TTsu},{TTsuHB})-({ton}-{d:tpd})+{d:MT}', 'ns', False),
    ('tDsuhi', 't.D.su.max = t.off.su + T/4 at f.SU - (t.on.pl - t.pd) - MT', '{toffsu}+10^6/(4*%s$D$29)-({tonpl}-{d:tpd})-{d:MT}' % DV, 'ns', False),
    ('tDsueff', 'Start-up dead time in force: max(IC 420 ns assumed, driver t.DT)', 'MAX({tDsu},{d:tDT})', 'ns', False),
    ('ktDsu', 'k.tD.su = min(t.D.su / t.D.su.min, t.D.su.max / t.D.su)', 'MIN({tDsueff}/{tDsulo},{tDsuhi}/{tDsueff})', '-', False),
    ('dvdt', 'Midpoint dv/dt at start-up: max(I.su FB, HB) / c.HB', 'MAX(%s$D$84,{IsuHB})/%s$D$46*1000' % (RT, DS), 'V/ns', False),
    ('kdrv', 'k.drv = min(dV/dt.max / dv/dt.su, V.hs.max / V.bus.max, 4 V / V.IH.max)', 'MIN({d:dVdt}/{dvdt},{d:Vhs}/{Vbus},4/{d:VIH})', '-', False),
    ('Reffm', 'Turn-off path that holds the gate below V.th min against the Miller current',
     '{d:Vthm}/{iM}-{Rsi}-{Rgi}', 'Ω', False),
    ('Reffo', 'Turn-off path that has the gate below V.th min before the other side reaches V.th min (t.D + its delay)',
     '(MAX(%s$D$47,{d:tDT})+{ton_}*LN({V}/({V}-{d:Vthm})))/(LN(({V}-{Veff})/({d:Vthm}-{Veff}))*{CG})-{Rsi}-{Rgi}' % DS, 'Ω', False),
    ('Reffs', 'Turn-off path that lets the channel go (V.pl -> V.th) within the run swing T.T.run',
     '{TTrun}/(LN(({d:Vpl}-{Veff})/({d:Vth}-{Veff}))*{CG})-{Rsi}-{Rgi}', 'Ω', False),
    ('Reffmax', 'Turn-off path max: overlap and soft turn-off, and Miller unless C.gs alone holds',
     'MIN({Reffo},{Reffs},IF({dVc}<={d:Vthm},1E+9,{Reffm}))', 'Ω', False),
    ('Roffneed', 'R.off that brings the path to half its max (in parallel with R.on unless V.F = 0)',
     'IF({d:VF}=0,{Reffmax}/2,IF({Reffmax}/2>={pc:Ron},1E+9,1/(2/{Reffmax}-1/{pc:Ron})))', 'Ω', False),
    ('Roffrec', 'R.off suggested: GOFF - half the max; with D.off - min(R.on / 2, that need), E12 below',
     'IF({Reffmax}<=0,0,' + e12f('IF({d:VF}=0,{Roffneed},MIN({pc:Ron}/2,{Roffneed}))') + ')', 'Ω', False),
    ('Ion', 'Peak gate current, turn-on: V.drv / (R.so + R.on + R.gi)', '{V}/({Rso}+{pc:Ron}+{Rgi})', 'A', False),
    ('Ioff', 'Peak gate current, turn-off: (V.drv - V.off.eff) / (R.si + R.off.eff + R.gi)', '({V}-{Veff})/({Rsi}+{Reff}+{Rgi})', 'A', False),
    ('kIG', 'k.IG = min(I.so / I.on, I.si / I.off)', 'MIN({d:Iso}/{Ion},{d:Isi}/{Ioff})', '-', False),
    ('Iopk', 'D.off peak current: (V.drv - V.F) / (R.si + R.off + R.gi), upper bound', 'IF({d:VF}=0,0,({V}-{d:VF})/({Rsi}+{pc:Roff}+{Rgi}))', 'A', False),
    ('Ioavg', 'D.off average current at f.Max: C.G V.g f x R.on / (R.on + R.off)',
     'IF({d:VF}=0,0,{CG}*{Vgrun}*%s$D$27*{pc:Ron}/({pc:Ron}+{pc:Roff})/1000)' % DV, 'mA', False),
    ('kDo', 'k.D.off = min(I.FSM / I.off.pk, I.F / I.off.avg)', 'IF({d:VF}=0,"-",MIN({d:IFSMo}/{Iopk},{d:IFo}*1000/{Ioavg}))', '-', False),
    ('Roffmin', 'R.off min: sink current and D.off surge: (V.drv - V.F) / min(I.si, I.FSM) - R.si - R.gi',
     'MAX(0,({V}-{d:VF})/IF({d:VF}=0,{d:Isi},MIN({d:Isi},{d:IFSMo}))-{Rsi}-{Rgi})', 'Ω', False),
    ('Cbmin', 'C.boot min: 10 x C.G', '10*{CG}', 'nF', False),
    ('Cbmax', 'C.boot max: the first LOUT pulse still charges it to V.bo.min (with R.boot)',
     'IF({V}-{d:VFb}>{d:Vbo},{tL1}/(MAX({pc:Rb},0.5)*LN(({V}-{d:VFb})/({V}-{d:VFb}-{d:Vbo}))),0)', 'nF', False),
    ('Cbrec', 'C.boot recommended: E6 above the min', e6c('{Cbmin}'), 'nF', False),
    ('taub', 'τ.boot (a diode alone taken as 0.5 Ω)', 'MAX({pc:Rb},0.5)*{pc:Cb}', 'ns', False),
    ('Rbmax', 'R.boot max: the first LOUT pulse reaches V.bo.min (with C.boot)',
     'IF({V}-{d:VFb}>{d:Vbo},{tL1}/({pc:Cb}*LN(({V}-{d:VFb})/({V}-{d:VFb}-{d:Vbo}))),"V.drv too low")', 'Ω', False),
    ('Rbrec', 'R.boot suggested: half the max, E12 below', 'IF(ISNUMBER({Rbmax}),' + e12f('{Rbmax}/2') + ',0)', 'Ω', False),
    ('Rbmin', 'R.boot min: D.boot surge into an empty C.boot: (V.drv - V.F.boot) / I.FSM', 'MAX(0,({V}-{d:VFb})/{d:IFSMb})', 'Ω', False),
    ('Ibpk', 'D.boot peak current into an empty C.boot', '({V}-{d:VFb})/MAX({pc:Rb},0.5)', 'A', False),
    ('Ibavg', 'D.boot average current at f.Max: C.G V.g f + I.QBO', '({CG}*{Vgrun}*%s$D$27/1000)+0.12' % DV, 'mA', False),
    ('VRRMn', 'D.boot reverse voltage: V.bus.max + V.drv', '{Vbus}+{V}', 'V', False),
    ('kDb', 'k.D.boot = min(V.RRM / need, I.FSM / I.boot.pk, I.F / I.boot.avg)',
     'MIN({d:VRRMb}/{VRRMn},{d:IFSMb}/{Ibpk},{d:IFb}*1000/{Ibavg})', '-', False),
    ('Vbs1', 'V.BS after the first LOUT pulse', '({V}-{d:VFb})*(1-EXP(-{tL1}/{taub}))', 'V', False),
    ('dVbs', 'V.BS drop per high-side pulse at f.SU (gate charge + floating quiescent 120 uA)',
     '{CG}*{Vgsu}/{pc:Cb}+0.00012*{tL1}/{pc:Cb}', 'V', False),
    ('Vbsmin', 'V.BS lowest, steady at f.SU',
     '{V}-{d:VFb}-{dVbs}*EXP(-{tL1}/{taub})/(1-EXP(-{tL1}/{taub}))-{dVbs}', 'V', False),
    ('PRon', 'P.Ron at f.Max',
     '({Eon}*{pc:Ron}/({Rso}+{pc:Ron}+{Rgi})+IF({d:VF}=0,0,{Eoff}*{Reff}/({Rsi}+{Reff}+{Rgi})*{Reff}/{pc:Ron}))'
     '*%s$D$27*10^-6' % DV, 'W', False),
    ('PRoff', 'P.Roff at f.Max',
     'IF({pc:Roff}>0,{Eoff}*{Reff}/({Rsi}+{Reff}+{Rgi})*IF({d:VF}=0,1,{Reff}/{pc:Roff})*%s$D$27*10^-6,0)' % DV,
     'W', False),
    ('Tj', 'Driver junction at f.Max and Ta.drv', '{d:Ta}+{Pdrv}*{d:Rth}', '˚C', False),
]


def rt_rows(cc):
    a = 'MAX(CC!$C$%d,SQRT(2)*%s$D$14/2)' % (cc['VbFB'], DS)
    return [
        ('I.su', 'Tank peak at f.SU, V.out ~0 (FB, 235 V bus)',
         '%s/D52*TAN(PI()*D55/(2*%s$D$29))' % (a, DV), 'A', None),
        ('k.su.OCP2', 'OCP2 margin (> 1, else start-up restarts)', '%s$G$49/D84' % DV, '-',
         'IF(D85>=1,"OK","CHECK")'),
        ('k.su.OCP1', 'OCP1 margin (> 1, else OCP1 acts at once)', '%s$D$49/D84' % DV, '-',
         'IF(D86>=1,"OK","CHECK")'),
        ('f.su.OCP1', 'Start-up floor: lowest f before OCP1 while V.out ~0',
         'PI()*D55/(2*ATAN(%s$D$49*D52/%s))' % (DV, a), 'kHz', None),
    ]


def set_ht(xml, row, ht):
    return re.sub(r'<row r="%d"(?: [^>]*)?>' % row,
                  '<row r="%d" ht="%s" customHeight="1">' % (row, ht), xml, count=1)


def add_merge(xml, ref):
    m = re.search(r'<mergeCells count="(\d+)">', xml)
    return xml.replace(m.group(0), '<mergeCells count="%d"><mergeCell ref="%s"/>' % (int(m.group(1)) + 1, ref), 1)


def add_picture(parts, sp, png, row0, col0=6):
    """anchor the PNG at (col0, row0) of Power Components, about 760 px wide"""
    rels = parts['xl/worksheets/_rels/' + sp['Power Components'].split('/')[-1] + '.rels'].decode()
    dpath = 'xl/' + re.search(r'Target="\.\./(drawings/drawing\d+\.xml)"', rels).group(1)
    drels = dpath.replace('drawings/', 'drawings/_rels/') + '.rels'
    n = max(int(m.group(1)) for k in parts for m in [re.match(r'xl/media/image(\d+)\.\w+$', k)] if m) + 1
    media = 'xl/media/image%d.png' % n
    parts[media] = open(png, 'rb').read()
    parts['__order__'].append(media)            # write_book writes the listed parts only
    r = parts[drels].decode()
    rid = 'rId%d' % (max(int(x) for x in re.findall(r'Id="rId(\d+)"', r)) + 1)
    r = r.replace('</Relationships>', '<Relationship Id="%s" Type="http://schemas.openxmlformats.org/'
                  'officeDocument/2006/relationships/image" Target="../media/image%d.png"/></Relationships>' % (rid, n))
    parts[drels] = r.encode()
    d = parts[dpath].decode()
    cid = max(int(x) for x in re.findall(r'<xdr:cNvPr id="(\d+)"', d)) + 1
    from PIL import Image
    w, h = Image.open(png).size
    cx = 760 * 9525
    cy = int(cx * h / w)
    anchor = ('<xdr:oneCellAnchor><xdr:from><xdr:col>%d</xdr:col><xdr:colOff>76200</xdr:colOff>'
              '<xdr:row>%d</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from><xdr:ext cx="%d" cy="%d"/>'
              '<xdr:pic><xdr:nvPicPr><xdr:cNvPr id="%d" name="Gate drive schematic"/><xdr:cNvPicPr>'
              '<a:picLocks noChangeAspect="1"/></xdr:cNvPicPr></xdr:nvPicPr><xdr:blipFill><a:blip '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="%s"/>'
              '<a:stretch><a:fillRect/></a:stretch></xdr:blipFill><xdr:spPr><a:xfrm><a:off x="0" y="0"/>'
              '<a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></xdr:spPr>'
              '</xdr:pic><xdr:clientData/></xdr:oneCellAnchor>' % (col0, row0 - 1, cx, cy, cid, rid, cx, cy))
    parts[dpath] = d.replace('</xdr:wsDr>', anchor + '</xdr:wsDr>').encode()


def bom_block(parts, sp, drow):
    """Append a 'Gate driver and gate network' block to BOM&Schematics, in the sheet's own
    styles: a PN table (driver, D.boot, D.off) and a value table (V.drv R.on R.off C.gs C.boot
    R.boot), all live links to Power Components; the frame's bottom border row moves down."""
    b = parts[sp['BOM&Schematics']].decode('utf-8')
    last = max(int(x) for x in re.findall(r'<row r="(\d+)"', b))
    bottom = re.search(r'<row r="%d"[^>]*>.*?</row>' % last, b, re.S).group(0)
    b = b.replace(bottom, '')
    r0 = last
    st = lambda ref: X.style_of(b, ref)
    sB, sI, sW = st('B75'), st('I75'), st('W75')
    put = lambda xml, ref, c: X.set_cell(xml, ref, c)

    def frame(xml, r, ht):
        xml = X.ensure_row(xml, r)
        xml = re.sub(r'<row r="%d"(?: [^>]*)?>' % r, '<row r="%d" spans="2:24" ht="%s" customHeight="1">' % (r, ht), xml, count=1)
        xml = put(xml, 'B%d' % r, '<c r="B%d" s="%s"/>' % (r, sB))
        xml = put(xml, 'I%d' % r, '<c r="I%d" s="%s"/>' % (r, sI))
        return put(xml, 'W%d' % r, '<c r="W%d" s="%s"/>' % (r, sW))
    b = frame(b, r0, 18)
    b = put(b, 'C%d' % r0, X.cell_t('C%d' % r0, st('C72'), 'Gate driver and gate network'))
    b = put(b, 'G%d' % r0, '<c r="G%d" s="%s"/>' % (r0, st('G72')))
    b = frame(b, r0 + 1, 14.25)
    r = r0 + 2
    b = frame(b, r, 15.75)
    for col, t in zip('CDE', ('Parameters', 'Name', 'PN')):
        b = put(b, '%s%d' % (col, r), X.cell_t('%s%d' % (col, r), st('%s74' % col), t))
    b = put(b, 'F%d' % r, '<c r="F%d" s="%s"/>' % (r, st('F74')))
    b = put(b, 'G%d' % r, X.cell_f('G%d' % r, st('G74'), 'IF(ISBLANK(E%d),"Please compile on sheet","")' % (r + 1)))
    for label, name, key in (('Gate drivers (one per leg)', 'U.drv1, U.drv2', 'part'),
                             ('Bootstrap diode (one per leg)', 'D.boot', 'pboot'),
                             ('Turn-off gate diode (one per switch)', 'D.off', 'poff')):
        r += 1
        b = frame(b, r, 14.25)
        b = put(b, 'C%d' % r, X.cell_t('C%d' % r, st('C75'), label))
        b = put(b, 'D%d' % r, X.cell_t('D%d' % r, st('D75'), name))
        b = put(b, 'E%d' % r, X.cell_f('E%d' % r, st('E75'), "'Power Components'!$C$%d" % drow[key]))
        b = put(b, 'F%d' % r, '<c r="F%d" s="%s"/>' % (r, st('F75')))
        b = put(b, 'G%d' % r, X.cell_f('G%d' % r, st('G75'), 'IF(ISBLANK(E%d),"Power Components","")' % r))
    r += 1
    b = frame(b, r, 14.25)
    r += 1
    b = frame(b, r, 15.75)
    for col, t in zip('CDEF', ('Parameters', 'Name', 'Value', 'Unit')):
        b = put(b, '%s%d' % (col, r), X.cell_t('%s%d' % (col, r), st('%s54' % col), t))
    b = put(b, 'G%d' % r, '<c r="G%d" s="%s"/>' % (r, st('G72')))
    for label, name, key, unit in (('Gate drive voltage', 'V.drv', 'V', 'V'),
                                   ('Turn-on gate resistor (one per switch)', 'R.on', 'Ron', 'Ω'),
                                   ('Turn-off gate resistor (one per switch)', 'R.off', 'Roff', 'Ω'),
                                   ('Gate-source capacitor, option (one per switch)', 'C.gs', 'Cgs', 'nF'),
                                   ('Bootstrap capacitor (one per leg)', 'C.boot', 'Cb', 'nF'),
                                   ('Bootstrap resistor (one per leg)', 'R.boot', 'Rb', 'Ω')):
        r += 1
        b = frame(b, r, 14.25)
        b = put(b, 'C%d' % r, X.cell_t('C%d' % r, st('C55'), label))
        b = put(b, 'D%d' % r, X.cell_t('D%d' % r, st('D55'), name))
        b = put(b, 'E%d' % r, X.cell_f('E%d' % r, st('E55'), "'Power Components'!$F$%d" % drow[key]))
        b = put(b, 'F%d' % r, X.cell_t('F%d' % r, st('F55'), unit))
        b = put(b, 'G%d' % r, X.cell_f('G%d' % r, st('G55'), 'IF(ISNUMBER(E%d),"","Power Components")' % r))
    r += 1
    b = X.ensure_row(b, r)
    b = b.replace('<row r="%d"></row>' % r, re.sub(r'r="([A-Z]*)%d"' % last, lambda m: 'r="%s%d"' % (m.group(1), r), bottom))
    b = re.sub(r'<dimension ref="([A-Z]+\d+:[A-Z]+)\d+"/>', lambda m: '<dimension ref="%s%d"/>' % (m.group(1), r), b, count=1)
    parts[sp['BOM&Schematics']] = b.encode('utf-8')


def main():
    for rel, sel in BOOKS.items():
        apply(os.path.join(XL, rel), sel)


def apply(path, sel):
    parts = X.open_book(path)
    sp = sheet_parts(parts)
    log = parts[sp['CHANGELOG_rev0_6']].decode('utf-8')
    if MARK in log:
        print('already present in', os.path.basename(path))
        return
    xl_rows.insert_rows(parts, 'Power Components', AT1, N1)
    xl_rows.insert_rows(parts, 'Power Components', AT2, N2)

    drow = {r[0]: AT1 + i for i, r in enumerate(MOS_ROWS)}
    drow.update({r[0]: AT2 + i for i, r in enumerate(DRV_ROWS)})
    ccrow = {r[0]: CC0 + i for i, r in enumerate(CC_ROWS)}

    def sub(f, here):
        def one(m):
            k = m.group(1)
            pre = '' if here == 'pc' else PCq
            if k.startswith('pc:'):
                return '%s$F$%d' % (pre, drow[k[3:]])
            if k.startswith('d:'):
                return '%s$D$%d' % (pre, drow[k[2:]])
            if k.startswith('cc:'):
                return '%s$C$%d' % ('' if here == 'cc' else 'CC!', ccrow[k[3:]])
            return 'D%d' % drow[k] if here == 'pc' else 'C%d' % ccrow[k]
        return re.sub(r'\{([A-Za-z]\w*(?::\w+)?)\}', one, f)

    # ---- Power Components
    pc = parts[sp['Power Components']].decode('utf-8')
    s_title, s_head, s_lab = X.style_of(pc, 'B57'), X.style_of(pc, 'B59'), X.style_of(pc, 'B58')
    s_in, s_val, s_unit = X.style_of(pc, 'D58'), X.style_of(pc, 'D60'), X.style_of(pc, 'E58')
    s_part, s_partb = X.style_of(pc, 'C67'), X.style_of(pc, 'B67')

    def cell(ref, c):
        nonlocal pc
        pc = X.set_cell(pc, ref, c)

    for key, label, name, val, unit in MOS_ROWS:          # the switch's gate data
        r = drow[key]
        pc = X.ensure_row(pc, r)
        cell('B%d' % r, X.cell_t('B%d' % r, s_lab, label))
        cell('C%d' % r, X.cell_t('C%d' % r, s_lab, name))
        cell('D%d' % r, X.cell_n('D%d' % r, s_in, val))
        cell('E%d' % r, X.cell_t('E%d' % r, s_unit, unit))
    for key, kind, label, name, dval, unit, fcol, gcol in DRV_ROWS:
        r = drow[key]
        pc = X.ensure_row(pc, r)
        if kind == 'gap':
            continue
        if kind == 'title':
            cell('B%d' % r, X.cell_t('B%d' % r, s_title, label))
            continue
        if kind == 'part':
            cell('B%d' % r, X.cell_t('B%d' % r, s_partb, label))
            name = sel.get(key, name)
            for col in 'CDE':
                cell('%s%d' % (col, r), X.cell_t('%s%d' % (col, r), s_part, name) if col == 'C'
                     else '<c r="%s%d" s="%s"/>' % (col, r, s_part))
            pc = add_merge(pc, 'C%d:E%d' % (r, r))
            continue
        if kind == 'head':
            for col, t in zip('BCDEFG', (label, name, dval, unit, fcol, gcol)):
                if t:
                    cell('%s%d' % (col, r), X.cell_t('%s%d' % (col, r), s_head, t))
            continue
        cell('B%d' % r, X.cell_t('B%d' % r, s_lab, label))
        cell('C%d' % r, X.cell_t('C%d' % r, s_lab, name))
        if kind == 'data':
            cell('D%d' % r, X.cell_n('D%d' % r, s_in, sel.get(key, dval)))
        elif kind == 'max':
            cell('D%d' % r, X.cell_f('D%d' % r, s_val, sub(dval, 'pc')))
        elif dval:
            cell('D%d' % r, X.cell_f('D%d' % r, s_val, sub(dval, 'pc')))
        else:
            cell('D%d' % r, '<c r="D%d" s="%s"/>' % (r, s_val))
        cell('E%d' % r, X.cell_t('E%d' % r, s_unit, unit))
        if fcol == 'in':
            cell('F%d' % r, X.cell_n('F%d' % r, s_in, sel[key]))
        elif fcol:
            cell('F%d' % r, X.cell_f('F%d' % r, s_lab, sub(fcol, 'pc')))
        if gcol:
            cell('G%d' % r, X.cell_f('G%d' % r, s_lab, sub(gcol, 'pc')))
    parts[sp['Power Components']] = pc.encode('utf-8')
    add_picture(parts, sp, PNG, drow['h2'])

    # ---- CC working
    cc = parts[sp['CC']].decode('utf-8')
    st, stv = X.style_of(cc, 'B27'), X.style_of(cc, 'C21')
    for key, label, val, unit, data in CC_ROWS:
        r = ccrow[key]
        cc = X.ensure_row(cc, r)
        cc = X.set_cell(cc, 'B%d' % r, X.cell_t('B%d' % r, st, label))
        if val is None:
            continue
        cc = X.set_cell(cc, 'C%d' % r, X.cell_n('C%d' % r, s_in, val) if data
                        else X.cell_f('C%d' % r, stv, sub(val, 'cc')))
        cc = X.set_cell(cc, 'D%d' % r, X.cell_t('D%d' % r, st, unit))
    last_cc = CC0 + len(CC_ROWS) - 1
    cc = re.sub(r'<dimension ref="[^"]*"/>', '<dimension ref="B3:AM%d"/>' % last_cc, cc, count=1)
    parts[sp['CC']] = cc.encode('utf-8')

    # ---- BOM&Schematics: gate driver, diodes, gate network (before the frame's bottom row)
    bom_block(parts, sp, drow)

    # ---- Res. Tank Design 81-87 (format of the peak table at 70-79)
    rt = parts[sp['Res. Tank Design']].decode('utf-8')
    s_t, s_h = X.style_of(rt, 'B70'), X.style_of(rt, 'B72')
    s_l, s_v, s_u = X.style_of(rt, 'B73'), X.style_of(rt, 'D73'), X.style_of(rt, 'E73')
    for r, ht in ((80, 14.25), (81, 18), (82, 3), (83, 15.75)):
        rt = X.ensure_row(rt, r)
        rt = set_ht(rt, r, ht)
    rt = X.set_cell(rt, 'B81', X.cell_t('B81', s_t, 'Start-up with the output near 0 V'))
    for col, t in zip('BCDEF', ('Parameters', 'Name', 'Value', 'Unit', 'Check')):
        rt = X.set_cell(rt, '%s83' % col, X.cell_t('%s83' % col, s_h, t))
    rows = rt_rows(ccrow)
    for i, (name, label, f, unit, chk) in enumerate(rows):
        r = 84 + i
        rt = X.ensure_row(rt, r)
        rt = set_ht(rt, r, 15)
        rt = X.set_cell(rt, 'B%d' % r, X.cell_t('B%d' % r, s_l, label))
        rt = X.set_cell(rt, 'C%d' % r, X.cell_t('C%d' % r, s_l, name))
        rt = X.set_cell(rt, 'D%d' % r, X.cell_f('D%d' % r, s_v, f))
        rt = X.set_cell(rt, 'E%d' % r, X.cell_t('E%d' % r, s_u, unit))
        if chk:
            rt = X.set_cell(rt, 'F%d' % r, X.cell_f('F%d' % r, s_l, chk))
    rt_last = 83 + len(rows)
    rt = re.sub(r'<dimension ref="[^"]*"/>', '<dimension ref="B4:G%d"/>' % rt_last, rt, count=1)
    parts[sp['Res. Tank Design']] = rt.encode('utf-8')

    # ---- CHANGELOG
    last = AT2 + N2 - 1
    rr = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
    why = ('%s - ADDED (user, 2026-10-22). Power Components rows inserted (xl_rows.py, every reference '
           'followed): 76-83 the switch gate data (STO60N045DM9: C.g 7.5 nF Qg slope, C.gs 4.76 nF, R.g 4.5, '
           'V.pl 6.3, V.th 4.0 / 3.5, Q.gd 13 nC, V.gs 20 V); 89-%d LLC Half Bridge Gate Driver Selection - part number, '
           'driver datasheet values (L6498LD: 1.4 / 1.55 A at 15 V, 10-20 V, 85 ns, MT 30 ns, no internal dead '
           'time, 800 kHz, 0.6 mA, 120 K/W, 125 C, V.BO 9.3 V), gate network (Value = recommendation, Selected '
           'Value = %s, G = OK / CHECK and the allowed range), results with G = OK / CHECK and the limit, '
           'schematic at column G, two blank rows before and after the section. Old rows 76-80 are now 84-88 and old 81-119 (the secondary section) %d-%d. BOM&Schematics 91-105: gate driver and gate network (PN and values, live links); '
           'CHANGELOG entries above this line name the old rows. Res. Tank Design 81-%d: start-up I.su, '
           'k.su.OCP2, k.su.OCP1, f.su.OCP1. CC 77-%d: the working (gate_budget.py model).'
           % (MARK, last, sel['note'], 81 + N1 + N2, 119 + N1 + N2, rt_last, last_cc))
    for sheet, ref, text in ((None, None, why),
                             ('Power Components', 'B76:E83', 'switch gate data (yellow)'),
                             ('Power Components', 'B%d:G%d' % (AT2, last), 'gate driver selection'),
                             ('Res. Tank Design', 'B81:F%d' % rt_last, 'start-up: I.su, k.su.OCP2, k.su.OCP1, f.su.OCP1'),
                             ('CC', 'B77:D%d' % last_cc, 'gate drive working')):
        log = X.ensure_row(log, rr)
        for col, t in (('B', sheet), ('C', ref), ('F', text)):
            if t is not None:
                log = X.set_cell(log, col + str(rr), X.cell_t(col + str(rr), '8', t))
        rr += 1
    parts[sp['CHANGELOG_rev0_6']] = log.encode('utf-8')
    X.write_book(path, parts)
    print('written:', os.path.relpath(path, XL), ' PC 76-%d, %d-%d' % (AT1 + N1 - 1, AT2, last))


if __name__ == '__main__':
    main()
