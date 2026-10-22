# -*- coding: utf-8 -*-
"""Start-up conditions and the gate drive in Power Components (2026-10-22, user: "add the
current and frequency expected at start-up, and the gate driver and gate resistor spec so
it can be checked - on and off resistor design, a gate-source capacitor, separate GON/GOFF
by setting the diode V.F to 0, power dissipation, gate current, the bootstrap").

Two blocks under the existing content (rows 121-), each Parameters / Name / Value / Unit
with a Check column F where there is a pass/fail:

  Start-up (rows 121-137)  output near 0 V, so the transformer is a short and the tank is
      the series L.r-C.r driven by the bridge square wave (A = V.bus in FB, V.bus/2 in HB):
      edge current I = A / Z0 tan(pi f.r / (2 f)) (above f.r the edge current is the peak),
      the OCP2 margin at f.SU, the lowest frequency the bridge can run before OCP1
      while V.out is low, the midpoint swing time and dv/dt at f.SU.
  Gate drive (rows 139-)   one model with gate_budget.py: the gate is C.G (Qg slope above
      the plateau) behind R.g,int; the driver is R.so / R.si (15 V over the short-circuit
      current minimum); the turn-off branch is (R.off + diode V.F) || R.on for a one-pin
      output (Conf.DRV 1) or R.off + V.F alone for separate GON/GOFF pins (Conf.DRV 2, set
      V.F 0).  Timing from the IC edge, the dead time the IC must give, the start-up ZVS
      window, gate voltage reached, driver and resistor power, Miller bump, bootstrap.

Inputs differ per book (BOOKS below): the guide and 3-core books take the design sheet's
section 14c.1 network, the bench book the LGE board as fitted.  Every result cell is a live
formula; no existing cell changes.

    python gate_xl.py              all three books, idempotent (CHANGELOG mark)
"""
import os
import re

import xlsx_patch as X
from measured200_xl import sheet_parts

HERE = os.path.dirname(os.path.abspath(__file__))
XL = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet'))
MARK = 'start-up conditions and gate drive (Power Components 121-)'

#  per book: values typed into the yellow input cells
SHEET_NET = dict(DRV='L6498LD (one OUT pin per side)', V=14.35, conf=1, Ron=4.7, Roff=2.2, VF=0.7,
                 Cgs=0, Pon=0.25, Poff=0.25, Cb=470, Rb=0, VFb=1.3,
                 note='design sheet section 14c.1: V.CC_reg_max 14.35 V, R.G 4.7, R.G_off 2.2 ohm '
                      '+ 1N4148W, C.BOOT 470 nF, ES1J (V.F 1.3 V) with no series resistor, 1206')
BOOKS = {
    'GUIDE_PQ50_657W_workbook_rev0_6_unencrypted.xlsx': SHEET_NET,
    os.path.join('variants', '3CORE_670W_workbook_unencrypted.xlsx'): SHEET_NET,
    os.path.join('variants', 'BENCH_200W_LGE_workbook_unencrypted.xlsx'): dict(
        DRV='L6498LD (one OUT pin per side)', V=18.0, conf=1, Ron=47.0, Roff=10.0, VF=0.7,
        Cgs=0, Pon=0.1, Poff=0.1, Cb=100, Rb=3.3, VFb=1.0,
        note='LGE bench board: VCC_GD 18 V, R115 47 ohm on, R114 10 ohm + 1N4148WS off branch '
             '(0603, 0.1 W), C63/C72 100 nF, MURS160 (V.F 1.0 V); boot resistor R113/R155 '
             '10 -> 3.3 ohm (user, 2026-10-21)'),
}

RT, DS, DV = "'Res. Tank Design'!", "'Design Spec'!", "'Device Setting'!"
LR = 'IF(%s$F$44,%s$F$44,%s$D$44)' % (RT, RT, RT)
CR = 'IF(%s$F$43,%s$F$43,%s$D$43)' % (RT, RT, RT)
CHB = DS + '$D$46'
R0 = 121


def rows(net):
    """(key, label, name, kind, value, unit, check) - kind: title / head / in / f / text.
    {key} in a formula becomes the D cell of that row; check is a formula for column F."""
    ok = lambda k: 'IF({%s}>=1,"OK","CHECK")' % k
    return [
        ('t1', 'Start-up conditions - output near 0 V, transformer a short  [ADDED]', None, 'title', None, None, None),
        ('h1', 'Parameters', 'Name', 'head', 'Value', 'Unit', 'Check'),
        ('fSU', 'Start-up switching frequency (Device Setting D29)', 'f.SU', 'f', DV + 'D29', 'kHz', None),
        ('fMax', 'Maximum switching frequency - continuous worst for the gate drive', 'f.Max', 'f', DV + 'D27', 'kHz', None),
        ('fr', 'Series resonance of the selected L.r - C.r: below it the bridge is capacitive while V.out is low',
         'f.r', 'f', '1/(2*PI()*SQRT(%s*%s*10^-15))/1000' % (LR, CR), 'kHz', None),
        ('Z0', 'Characteristic impedance of L.r - C.r', 'Z0', 'f', 'SQRT(%s/%s*1000)' % (LR, CR), 'Ω', None),
        ('VbFB', 'Highest bus in FB - HB/FB morphing threshold (DS V.HVPK_BOH)', 'V.bus.FB', 'in', 235, 'V', None),
        ('VbHB', 'Highest bus in HB - sqrt(2) x VAC.max', 'V.bus.HB', 'f', 'SQRT(2)*%sD14' % DS, 'V', None),
        ('ISUFB', 'Tank current at the edge (= peak) at f.SU, FB, square wave V.bus.FB', 'I.SU.FB', 'f',
         '{VbFB}/{Z0}*TAN(PI()*{fr}/(2*{fSU}))', 'A', None),
        ('ISUHB', 'Tank current at the edge (= peak) at f.SU, HB, square wave V.bus.HB / 2', 'I.SU.HB', 'f',
         '{VbHB}/2/{Z0}*TAN(PI()*{fr}/(2*{fSU}))', 'A', None),
        ('IOCP1', 'OCP1 trip current (Device Setting D49) - raises the frequency', 'I.OCP1', 'f', DV + 'D49', 'A', None),
        ('IOCP2', 'OCP2 trip current (Device Setting G49) - 50 us stop, restart at f.SU', 'I.OCP2', 'f', DV + 'G49', 'A', None),
        ('kSU', 'OCP2 margin at f.SU - target > 1, else start-up restarts', 'k.SU.OCP2', 'f',
         '{IOCP2}/MAX({ISUFB},{ISUHB})', '-', ok('kSU')),
        ('fOCP1', 'Lowest frequency before OCP1 while V.out ~ 0 (start-up stays above it until V.out rises)',
         'f.SU.OCP1', 'f', 'PI()*{fr}/(2*ATAN({IOCP1}*{Z0}/MAX({VbFB},{VbHB}/2)))', 'kHz', None),
        ('TTFB', 'Midpoint swing time at f.SU, FB (c.HB, Design Spec D46)', 'T.T.SU.FB', 'f',
         '%s*{VbFB}/{ISUFB}/1000' % CHB, 'ns', None),
        ('TTHB', 'Midpoint swing time at f.SU, HB', 'T.T.SU.HB', 'f', '%s*{VbHB}/{ISUHB}/1000' % CHB, 'ns', None),
        ('dvdt', 'Midpoint dv/dt at f.SU - driver immunity 50 V/ns', 'dv/dt.SU', 'f',
         'MAX({ISUFB},{ISUHB})/%s*1000' % CHB, 'V/ns', 'IF({dvdt}<=50,"OK","CHECK")'),
        ('gap1', None, None, 'gap', None, None, None),
        ('t2', 'Gate drive - driver, gate network and bootstrap, per switch position  [ADDED]', None, 'title', None, None, None),
        ('h2', 'Parameters (yellow = input)', 'Name', 'head', 'Value', 'Unit', 'Check'),
        ('DRV', 'Gate driver part number', net['DRV'], 'text', None, None, None),
        ('V', 'Driver supply = gate drive voltage (high side ~ V.BS)', 'V.DRV', 'in', net['V'], 'V', None),
        ('conf', 'Driver output: 1 = one OUT pin (R.on also carries turn-off), 2 = separate GON / GOFF pins',
         'Conf.DRV', 'in', net['conf'], '-', None),
        ('Ron', 'Turn-on gate resistor', 'R.on', 'in', net['Ron'], 'Ω', None),
        ('Roff', 'Turn-off resistor: Conf 1 = the diode branch (0 = no branch), Conf 2 = the GOFF resistor',
         'R.off', 'in', net['Roff'], 'Ω', None),
        ('VF', 'Turn-off diode forward voltage - 0 with a separate GOFF pin', 'V.F.off', 'in', net['VF'], 'V', None),
        ('Cgs', 'External gate-source capacitor (0 = none)', 'C.gs.ext', 'in', net['Cgs'], 'nF', None),
        ('Pon', 'Power rating of the R.on package', 'P.R.on.rat', 'in', net['Pon'], 'W', None),
        ('Poff', 'Power rating of the R.off package', 'P.R.off.rat', 'in', net['Poff'], 'W', None),
        ('Rso', 'Driver source resistance - 15 V / I.so min 1.4 A (L6498 full temperature)', 'R.so', 'in', 10.71, 'Ω', None),
        ('Rsi', 'Driver sink resistance - 15 V / I.si min 1.55 A', 'R.si', 'in', 9.68, 'Ω', None),
        ('tpd', 'Driver propagation delay, typ (L6498 85 ns, max 120)', 't.pd', 'in', 85, 'ns', None),
        ('MT', 'Driver delay matching, max (L6498)', 'MT', 'in', 30, 'ns', None),
        ('IQ', 'Driver quiescent current, VCC + floating, max (480 + 120 uA)', 'I.Q.drv', 'in', 0.6, 'mA', None),
        ('Rth', 'Driver thermal resistance j-a (L6498 SO-14)', 'Rth.drv', 'in', 120, '˚C/W', None),
        ('Ta', 'Ambient for the driver check, inside the set [assumed]', 'Ta.drv', 'in', 70, '˚C', None),
        ('Cg', 'MOSFET gate capacitance above the plateau, per device (Qg slope)', 'C.g', 'in', 7.5, 'nF', None),
        ('Cgsd', 'MOSFET gate-source capacitance, per device (C.iss - C.rss)', 'C.gs', 'in', 4.76, 'nF', None),
        ('Rgi', 'MOSFET internal gate resistance, per device', 'R.g.int', 'in', 4.5, 'Ω', None),
        ('Vpl', 'MOSFET Miller plateau', 'V.pl', 'in', 6.3, 'V', None),
        ('Vth', 'MOSFET gate threshold for timing [typ, assumed]', 'V.th', 'in', 4.0, 'V', None),
        ('Vthm', 'MOSFET gate threshold, min (DS, 250 uA)', 'V.th.min', 'in', 3.5, 'V', None),
        ('Qgd', 'Miller charge over the bus swing, per device (C.rss integral 0 .. 163-325 V)', 'Q.gd', 'in', 13, 'nC', None),
        ('Cb', 'Bootstrap capacitor', 'C.BOOT', 'in', net['Cb'], 'nF', None),
        ('Rb', 'Bootstrap series resistor (0 = diode alone, taken as 0.5 ohm)', 'R.BOOT', 'in', net['Rb'], 'Ω', None),
        ('VFb', 'Bootstrap diode forward voltage', 'V.F.BOOT', 'in', net['VFb'], 'V', None),
        ('tDSU', 'Dead time at start-up, before ADT (DS gives none - max ADT assumed)', 't.D.SU', 'in', 420, 'ns', None),
        ('tD', 'Dead time in run (Design Spec D47)', 't.D', 'f', DS + 'D47', 'ns', None),
        ('h3', 'Results', 'Name', 'head', 'Value', 'Unit', 'Check'),
        ('CG', 'Gate capacitance per position: n.par x C.g + C.gs.ext', 'C.G', 'f', '$D$68*{Cg}+{Cgs}', 'nF', None),
        ('RG', 'Internal gate resistance per position', 'R.gi', 'f', '{Rgi}/$D$68', 'Ω', None),
        ('Reff', 'Turn-off path, effective resistance', 'R.off.eff', 'f',
         'IF({conf}=2,{Roff},IF({Roff}>0,{Roff}*{Ron}/({Roff}+{Ron}),{Ron}))', 'Ω', None),
        ('Veff', 'Turn-off path, effective offset (the diode)', 'V.off.eff', 'f',
         'IF({conf}=2,{VF},IF({Roff}>0,{VF}*{Ron}/({Roff}+{Ron}),0))', 'V', None),
        ('ton', 'Turn-on time constant (R.so + R.on + R.gi) C.G', 'τ.on', 'f', '({Rso}+{Ron}+{RG})*{CG}', 'ns', None),
        ('toff', 'Turn-off time constant (R.si + R.off.eff + R.gi) C.G', 'τ.off', 'f', '({Rsi}+{Reff}+{RG})*{CG}', 'ns', None),
        ('Ion', 'Peak gate current, turn-on', 'I.G.on.pk', 'f', '{V}/({Rso}+{Ron}+{RG})', 'A', None),
        ('Ioff', 'Peak gate current, turn-off', 'I.G.off.pk', 'f', '({V}-{Veff})/({Rsi}+{Reff}+{RG})', 'A', None),
        ('tonth', 'IC edge -> channel on (V.th)', 't.on.th', 'f', '{tpd}+{ton}*LN({V}/({V}-{Vth}))', 'ns', None),
        ('tonpl', 'IC edge -> plateau (channel can take the tank current)', 't.on.pl', 'f',
         '{tpd}+{ton}*LN({V}/({V}-{Vpl}))', 'ns', None),
        ('VGSU', 'Gate voltage at the end of the f.SU pulse (T/2 - t.D.SU) - target >= 10 V (RDS(on) spec)',
         'V.G.SU', 'f', '{V}*(1-EXP(-(10^6/(2*{fSU})-{tDSU})/{ton}))', 'V', 'IF({VGSU}>=10,"OK","CHECK")'),
        ('VGMax', 'Gate voltage at the end of the f.Max pulse (T/2 - t.D)', 'V.G.Max', 'f',
         '{V}*(1-EXP(-(10^6/(2*{fMax})-{tD})/{ton}))', 'V', 'IF({VGMax}>=10,"OK","CHECK")'),
        ('toffpl', 'IC edge -> plateau on the way down (from a full gate)', 't.off.pl', 'f',
         '{tpd}+{toff}*LN(({V}-{Veff})/({Vpl}-{Veff}))', 'ns', None),
        ('toffth', 'IC edge -> below V.th.min (channel firmly off)', 't.off.th', 'f',
         'IF({Vthm}>{Veff},{tpd}+{toff}*LN(({V}-{Veff})/({Vthm}-{Veff})),"never")', 'ns', None),
        ('TTrun', 'Run midpoint swing at I.Lm.pk on V.bus.HB (Res. Tank Design D73)', 'T.T.run', 'f',
         "%s*{VbHB}/%sD73/1000" % (CHB, RT), 'ns', None),
        ('tDneed', 'Dead time the IC must give in run: t.off.pl + T.T.run - t.on.th + MT (ADT 40-420 ns)',
         't.D.need', 'f', '({toffpl}-{tpd})+{TTrun}-({tonth}-{tpd})+{MT}', 'ns',
         'IF(AND({tDneed}>=40,{tDneed}<=420),"OK","CHECK")'),
        ('toffSU', 'Turn-off delay to the plateau at f.SU (gate from V.G.SU)', 't.off.SU', 'f',
         '{toff}*LN(({VGSU}-{Veff})/({Vpl}-{Veff}))', 'ns', None),
        ('loFB', 'Start-up ZVS window FB, low end: incoming channel on after the swing', 't.D.SU.lo.FB', 'f',
         '{toffSU}+{TTFB}-({tonth}-{tpd})+{MT}', 'ns', None),
        ('loHB', 'Start-up ZVS window HB, low end', 't.D.SU.lo.HB', 'f', '{toffSU}+{TTHB}-({tonth}-{tpd})+{MT}', 'ns', None),
        ('hiSU', 'Start-up ZVS window, high end: incoming at the plateau before the current reverses (T/4)',
         't.D.SU.hi', 'f', '{toffSU}+10^6/(4*{fSU})-({tonpl}-{tpd})-{MT}', 'ns',
         'IF(AND({tDSU}>=MAX({loFB},{loHB}),{tDSU}<={hiSU}),"OK","CHECK")'),
        ('Eon', 'Energy lost per turn-on at f.Max: C.G V.G (V.DRV - V.G / 2)', 'E.on', 'f',
         '{CG}*{VGMax}*({V}-{VGMax}/2)', 'nJ', None),
        ('Eoff', 'Energy lost per turn-off at f.Max: C.G V.G^2 / 2', 'E.off', 'f', '{CG}*{VGMax}^2/2', 'nJ', None),
        ('Pdrv', 'Driver power at f.Max, both positions of one L6498 + quiescent', 'P.drv', 'f',
         '2*({Eon}*{Rso}/({Rso}+{Ron}+{RG})+{Eoff}*{Rsi}/({Rsi}+{Reff}+{RG}))*{fMax}*10^-6+{IQ}*{V}/1000',
         'W', None),
        ('Tj', 'Driver junction at f.Max: Ta.drv + P.drv Rth - target <= 125 ˚C (DS recommended)', 'Tj.drv', 'f',
         '{Ta}+{Pdrv}*{Rth}', '˚C', 'IF({Tj}<=125,"OK","CHECK")'),
        ('PdrvSU', 'Driver power at f.SU (start-up, a few ms)', 'P.drv.SU', 'f',
         '2*({CG}*{VGSU}*({V}-{VGSU}/2)*{Rso}/({Rso}+{Ron}+{RG})+{CG}*{VGSU}^2/2*{Rsi}/({Rsi}+{Reff}+{RG}))'
         '*{fSU}*10^-6+{IQ}*{V}/1000', 'W', None),
        ('PRon', 'R.on dissipation at f.Max (turn-on share + its turn-off share with Conf 1)', 'P.R.on', 'f',
         '({Eon}*{Ron}/({Rso}+{Ron}+{RG})+IF({conf}=1,{Eoff}*{Reff}/({Rsi}+{Reff}+{RG})*{Reff}/{Ron},0))'
         '*{fMax}*10^-6', 'W', 'IF({PRon}<=0.5*{Pon},"OK","CHECK")'),
        ('PRoff', 'R.off dissipation at f.Max - target <= 50 % of its rating', 'P.R.off', 'f',
         'IF({Roff}>0,{Eoff}*{Reff}/({Rsi}+{Reff}+{RG})*{Reff}/{Roff}*{fMax}*10^-6,0)', 'W',
         'IF({PRoff}<=0.5*{Poff},"OK","CHECK")'),
        ('Id', 'Turn-off diode average current at f.Max', 'I.D.off.avg', 'f',
         'IF({Roff}>0,{CG}*{VGMax}*{fMax}*IF({conf}=2,1,{Ron}/({Roff}+{Ron}))/1000,0)', 'mA', None),
        ('dVM', 'Miller bump on an OFF gate, upper bound (no sink): Q.gd / (C.gs + C.gs.ext)', 'ΔV.GS.Miller', 'f',
         '$D$68*{Qgd}/($D$68*{Cgsd}+{Cgs})', 'V', None),
        ('kM', 'Miller margin V.th.min / ΔV.GS.Miller - target > 1 (ringing adds to it)', 'k.Miller', 'f',
         '{Vthm}/{dVM}', '-', ok('kM')),
        ('taub', 'Bootstrap time constant', 'τ.BOOT', 'f', 'MAX({Rb},0.5)*{Cb}', 'ns', None),
        ('tL1', 'First LOUT pulse at start-up (T/2 - t.D.SU; the IC may lengthen it, DS 5.2.3)', 't.LOUT1', 'f',
         '10^6/(2*{fSU})-{tDSU}', 'ns', None),
        ('VBS1', 'V.BS after the first LOUT pulse from an empty C.BOOT - target >= 9.1 V (VBO_thON max)',
         'V.BS.1', 'f', '({V}-{VFb})*(1-EXP(-{tL1}/{taub}))', 'V', 'IF({VBS1}>=9.1,"OK","CHECK")'),
        ('dVBS', 'V.BS drop per high-side pulse at f.SU: gate charge + 120 uA floating quiescent', 'ΔV.BS', 'f',
         '{CG}*{VGSU}/{Cb}+0.00012*{tL1}/{Cb}', 'V', None),
        ('VBSmin', 'V.BS minimum, steady at f.SU (recharge each LOUT pulse) - target >= 10 V', 'V.BS.min', 'f',
         '{V}-{VFb}-{dVBS}*EXP(-{tL1}/{taub})/(1-EXP(-{tL1}/{taub}))-{dVBS}', 'V', 'IF({VBSmin}>=10,"OK","CHECK")'),
        ('kCb', 'C.BOOT / C.G - target >= 10 (DS: C.BOOT >>> C.EXT)', 'k.CBOOT', 'f', '{Cb}/{CG}', '-',
         'IF({kCb}>=10,"OK","CHECK")'),
        ('Ibpk', 'Peak charging current into an empty C.BOOT (check the diode I.FSM)', 'I.BOOT.pk', 'f',
         '({V}-{VFb})/MAX({Rb},0.5)', 'A', None),
        ('PRb', 'Bootstrap resistor dissipation at f.Max', 'P.R.BOOT', 'f',
         'IF({Rb}>0,{Cb}*({CG}*{VGMax}/{Cb})^2/2*{fMax}*10^-6,0)', 'W', None),
        ('VRRM', 'Bootstrap diode reverse voltage needed: V.bus.HB + V.DRV (+ ringing margin)', 'V.RRM.BOOT',
         'f', '{VbHB}+{V}', 'V', None),
    ]


def main():
    for rel, net in BOOKS.items():
        apply(os.path.join(XL, rel), net)


def apply(path, net):
    parts = X.open_book(path)
    sp = sheet_parts(parts)
    log = parts[sp['CHANGELOG_rev0_6']].decode('utf-8')
    if MARK in log:
        print('already present in', os.path.basename(path))
        return
    pc = parts[sp['Power Components']].decode('utf-8')
    s_title, s_head = X.style_of(pc, 'B57'), X.style_of(pc, 'B59')
    s_lab, s_in, s_val, s_unit = X.style_of(pc, 'B58'), X.style_of(pc, 'D58'), X.style_of(pc, 'D60'), \
        X.style_of(pc, 'E58')
    s_text = X.style_of(pc, 'C67')
    R = rows(net)
    rowof = {k: R0 + i for i, (k, *_r) in enumerate(R)}
    sub = lambda f: re.sub(r'\{(\w+)\}', lambda m: 'D%d' % rowof[m.group(1)], f)
    put = lambda xml, ref, cell: X.set_cell(xml, ref, cell)
    for key, label, name, kind, val, unit, chk in R:
        r = rowof[key]
        pc = X.ensure_row(pc, r)
        if kind == 'gap':
            continue
        if kind == 'title':
            pc = put(pc, 'B%d' % r, X.cell_t('B%d' % r, s_title, label))
            continue
        if kind == 'head':
            for col, t in zip('BCDEF', (label, name, val, unit, chk)):
                pc = put(pc, '%s%d' % (col, r), X.cell_t('%s%d' % (col, r), s_head, t))
            continue
        pc = put(pc, 'B%d' % r, X.cell_t('B%d' % r, s_lab, label))
        if kind == 'text':
            pc = put(pc, 'C%d' % r, X.cell_t('C%d' % r, s_text, name))
            continue
        pc = put(pc, 'C%d' % r, X.cell_t('C%d' % r, s_lab, name))
        if kind == 'in':
            pc = put(pc, 'D%d' % r, X.cell_n('D%d' % r, s_in, val))
        else:
            pc = put(pc, 'D%d' % r, X.cell_f('D%d' % r, s_val, sub(val)))
        pc = put(pc, 'E%d' % r, X.cell_t('E%d' % r, s_unit, unit))
        if chk:
            pc = put(pc, 'F%d' % r, X.cell_f('F%d' % r, s_lab, sub(chk)))
    last = R0 + len(R) - 1
    pc = re.sub(r'<dimension ref="[^"]*"/>', '<dimension ref="B4:N%d"/>' % last, pc, count=1)
    parts[sp['Power Components']] = pc.encode('utf-8')

    rr = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
    why = ('%s - ADDED (user, 2026-10-22): start-up with the output near 0 V (the transformer a short, the '
           'series L.r-C.r on the bridge square wave: edge current at f.SU in FB and HB, OCP margins, the '
           'lowest frequency before OCP1, swing time and dv/dt) and the gate drive (driver, on/off network '
           'with Conf.DRV 1 one OUT pin or 2 separate GON/GOFF with V.F 0, external C.gs, timing from the IC '
           'edge, dead time needed in run and the start-up ZVS window, driver and resistor power, Miller '
           'bump, bootstrap). Same model as gate_budget.py. Inputs: %s.' % (MARK, net['note']))
    for sheet, ref, text in ((None, None, why),
                             ('Power Components', 'B%d:F%d' % (R0, last),
                              'start-up rows %d-%d, gate drive rows %d-%d (yellow = input)'
                              % (R0, rowof['dvdt'], rowof['t2'], last))):
        log = X.ensure_row(log, rr)
        for col, t in (('B', sheet), ('C', ref), ('F', text)):
            if t is not None:
                log = X.set_cell(log, col + str(rr), X.cell_t(col + str(rr), '8', t))
        rr += 1
    parts[sp['CHANGELOG_rev0_6']] = log.encode('utf-8')
    X.write_book(path, parts)
    print('written:', os.path.relpath(path, XL), ' rows %d-%d' % (R0, last))


if __name__ == '__main__':
    main()
