# -*- coding: utf-8 -*-
"""Gate waveforms of one half-bridge leg through a ZVS transition, in the time domain
(2026-10-21, user: "with the gate resistors, the capacitances and the snubbers - compute
how much the gate pulse slows down").

gate_budget.py treats the gate as one RC.  This solves the leg as circuit equations:

  driver     L6498LD output = ideal source behind R.so / R.si (gate_budget upper bounds),
             propagation delay 85 ns (DS typ) after the IC edge
  network    turn-on  R.on;  turn-off  (R.d + diode 0.7 V) || R.p;  plus R.g,int 4.5 ohm
  MOSFET     STO60N045DM9 from DS14711 Rev 4: C.gs 4.76 nF constant (= C.iss - C.rss, flat
             in Figure 6), C.gd(V.dg) = C.rss of Figure 6 for V.dg > 0.1 V and 2.4 nF below
             (the gate above the drain: that is what the 60 -> 90 nC slope of Figure 5
             needs), C.ds(V.ds) = (C.oss - C.rss) of Figure 6; channel: the saturation
             current is Figure 4 (transfer characteristic, V.DS 20 V, read from the vector
             path - 0.3 A at 5.0 V, 22 A at 6.0 V, 103 A at 7.0 V), joined to the linear
             region by I = I.sat (1 - exp(-V.ds / (R.DS(on) I.sat))), R.DS(on) 45 mohm;
             body diode 0.8 V + 20 S.  'On' below means the channel carries 0.5 A
             (V.GS 5.06 V on Figure 4) - the DS V.GS(th) 3.5-4.5 V is at 250 uA
  C.oss      Figure 6 integrated 0..400 V is 1369 pF of charge, the DS Table 5 'C.oss eq'
             is 897 pF.  k.oss scales C.ds so the charge matches 897 (the default, the
             same number c.HB is built on); k.oss 1 runs the curve as drawn
  midpoint   + snubber C.sn drain-source on each FET + C.par to ground
  tank       start-up: L.r - C.r with the output at 0 V (the transformer a short), the
             current and C.r voltage at the edge from the square-wave steady state;
             full bridge = the other leg the mirror image of this one, half bridge =
             the other leg's low side static and C.r at V.bus / 2.  run: a constant current
             (the magnetizing peak) through the transition

Sequence simulated: the previous edge (HOUT falls, LOUT rises after t.D), the LOUT pulse,
then LOUT falls at t = 0 and HOUT rises at t = t.D.  The high-side gate at the previous
edge starts from the low-side value at t = 0 of the last pass (three passes).

    python gate_wave.py            the 200 W bench board (its workbook), every case
    python gate_wave.py x3m3       the 670 W x3m3 tank (its sheet)
"""
import json
import math
import os
import sys

import numpy as np
from scipy.integrate import solve_ivp

_trapz = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = json.load(open(os.path.join(HERE, 'data', 'STO60N045DM9_caps.json')))


def _curve(name):
    v = np.array([a for a, b in CAP[name]]); c = np.array([b for a, b in CAP[name]])
    return np.log(v), np.log(c * 1e-12)


LV_RSS, LC_RSS = _curve('Crss')
LV_OSS, LC_OSS = _curve('Coss')


def crss(v):
    return math.exp(np.interp(math.log(max(v, 0.1)), LV_RSS, LC_RSS))


def coss(v):
    return math.exp(np.interp(math.log(max(v, 0.1)), LV_OSS, LC_OSS))


C_GS = 4.76e-9
C_GD_NEG = 2.4e-9
TR_V = np.array([a for a, b in CAP['transfer']]); TR_I = np.array([b for a, b in CAP['transfer']])
RDSON = 0.045
VON = float(np.interp(0.5, TR_I, TR_V))         # V.GS where the channel carries 0.5 A
V50 = float(np.interp(50.0, TR_I, TR_V))        # ... and 50 A: fully able to take the tank current
RGI = 4.5
RSO, RSI = 10.71, 9.68
T_PROP = 85e-9
VFD = 0.7
G_BODY, VF_BODY = 20.0, 0.8


def _koss_for(qeq):
    """scale on C.ds so that the 0..400 V charge of C.oss equals qeq x 400 V"""
    vs = np.logspace(-1, math.log10(400), 3000)
    q = _trapz([coss(v) for v in vs], vs) + coss(0.1) * 0.1
    qrss = _trapz([crss(v) for v in vs], vs) + crss(0.1) * 0.1
    return (qeq * 400 - qrss) / (q - qrss)


def cgd(vdg):
    return crss(vdg) if vdg > 0.1 else C_GD_NEG


def cds(vds, koss):
    v = max(vds, 0.1)
    return max(coss(v) - crss(v), 1e-12) * koss


def i_ch(vgs, vds):
    if vds <= 0 or vgs <= TR_V[0]:
        return 0.0
    isat = float(np.interp(vgs, TR_V, TR_I))
    if isat <= 1e-6:
        return 0.0
    return isat * (1 - math.exp(-vds / (RDSON * isat)))


def i_body(vds):
    return G_BODY * (-vds - VF_BODY) if vds < -VF_BODY else 0.0


def i_gate(on, vg_rel, vcc, net):
    """current INTO the gate from the driver network; vg_rel = gate - own source"""
    if on:
        return (vcc - vg_rel) / (RSO + RGI + net['Ron'])
    d = -vg_rel                              # source (0 V) minus gate
    Rs = RSI + RGI
    i = d / (Rs + net['Rp'])                 # diode off
    if -i * net['Rp'] > VFD:                 # gate - V.x > V.F: diode conducts
        G = 1 / net['Rp'] + 1 / net['Rd']
        i = (d * G - VFD / net['Rd']) / (1 + Rs * G)
    return i


def simulate(case, net, tD, koss, csn, cpar, passes=4, record=False):
    Vb, f, mode = case['Vbus'], case['f'], case['mode']
    T = 1 / f
    t_end = tD + 0.25 * T + 150e-9
    t0 = -T / 2 - 20e-9
    Lr, Cr = case.get('Lr'), case.get('Cr')
    vbs = case['VBS']
    # tank state at the edge (t = 0, end of the LS conduction) from the square-wave steady state
    if mode in ('FB', 'HB'):
        A = Vb if mode == 'FB' else Vb / 2
        wr = 1 / math.sqrt(Lr * Cr); Z0 = math.sqrt(Lr / Cr); phi = wr * T / 2
        # drive +A for T/2 starting with i = -I0, vC = -V0; symmetric end i = +I0, vC = +V0
        M = np.array([[1 + math.cos(phi), -math.sin(phi) / Z0],
                      [Z0 * math.sin(phi), 1 + math.cos(phi)]])
        I0, V0 = np.linalg.solve(M, [A * math.sin(phi) / Z0, A * (1 - math.cos(phi))])
    vg_hs0 = case.get('Vend', 14.0)
    d_sw = 0.0                         # IC edge -> midpoint at 50 %: where the tank really switches
    for _ in range(passes):
        # state: gL (abs), gH (abs), v (mid), i (tank current into the mid node), vC
        # at t0 the HS is still on (mid at V.bus) and the tank is in the positive half of its
        # square-wave steady state, which ends where the PREVIOUS edge really switches
        # (-T/2 + d_sw, the same delay as the edge at t = 0 by symmetry)
        if mode in ('FB', 'HB'):
            tp = T / 2 - (-T / 2 + d_sw - t0)          # time into the positive half at t0
            w = 1 / math.sqrt(Lr * Cr)
            i_out = -I0 * math.cos(w * tp) + (A + V0) / Z0 * math.sin(w * tp)
            vC = A - (A + V0) * math.cos(w * tp) - I0 * Z0 * math.sin(w * tp)
            i_in = -i_out
            vC += Vb / 2 if mode == 'HB' else 0.0
        else:
            i_in = -case['I']
            vC = 0.0
        y0 = [0.0, Vb + vg_hs0, Vb, i_in, vC]
        trace = []

        def drv(t):
            # driver outputs = IC commands delayed by T_PROP
            tt = t - T_PROP
            hs = tt < -T / 2 or tt >= tD
            ls = (-T / 2 + tD) <= tt < 0.0
            return hs, ls

        def rhs(t, y):
            gL, gH, v, i_t, vC = y
            if mode == 'CI':                        # magnetizing triangle: -I at the previous edge, +I at t = 0
                i_t = case['I'] * (4 * t / T + 1) if t <= 0 else case['I'] * (1 - 4 * t / T)
            hs, ls = drv(t)
            vgsL, vgsH = gL, gH - v
            vdsL, vdsH = v, Vb - v
            iL = i_gate(ls, vgsL, case['VCC'], net)
            iH = i_gate(hs, vgsH, vbs, net)
            cgdL, cgdH = cgd(v - gL), cgd(Vb - gH)
            cdsL, cdsH = cds(vdsL, koss) + csn, cds(vdsH, koss) + csn
            # node equations, unknowns x = [dgL, dgH, dv]
            A = np.array([[C_GS + cgdL, 0.0, -cgdL],
                          [0.0, C_GS + cgdH, -C_GS],
                          [-cgdL, -C_GS, cdsL + cdsH + cpar + cgdL + C_GS]])
            b = np.array([iL, iH,
                          i_t + i_ch(vgsH, vdsH) - i_body(vdsH) - i_ch(vgsL, vdsL) + i_body(vdsL)])
            dgL, dgH, dv = np.linalg.solve(A, b)
            if mode == 'FB':
                vt = v - (Vb - v) - vC            # tank voltage, the other leg the mirror
            elif mode == 'HB':
                vt = v - vC
            else:
                vt = None
            if vt is None:
                di, dvC = 0.0, 0.0                  # i_t is replaced by the triangle below
            else:
                di = -vt / Lr                       # i_t is INTO the mid node: L d(i_out)/dt = vt, i_out = -i_t
                dvC = -i_t / Cr
            return [dgL, dgH, dv, di, dvC]

        ts = np.linspace(t0, t_end, 6001)
        sol = solve_ivp(rhs, (t0, t_end), y0, method='LSODA', t_eval=ts, max_step=0.5e-9,
                        rtol=1e-6, atol=[1e-4, 1e-4, 1e-3, 1e-4, 1e-3])
        Y = sol.y
        k0 = np.searchsorted(sol.t, 0.0)
        vg_hs0 = Y[0][k0]                     # the LS gate at its turn-off edge = the HS one next time
        k50 = np.where((sol.t > 0) & (Y[2] > 0.5 * Vb))[0]
        if len(k50):
            d_sw = sol.t[k50[0]]
    return sol, Y, k0


def measure(sol, Y, case, tD):
    t = sol.t; gL, gH, v = Y[0], Y[1], Y[2]
    T = 1 / case['f']
    if case['mode'] == 'CI':
        i_in = np.where(t <= 0, case['I'] * (4 * t / T + 1), case['I'] * (1 - 4 * t / T))
    else:
        i_in = Y[3]
    Vb = case['Vbus']
    vgsH = gH - v
    iL = np.array([i_ch(a, b) for a, b in zip(gL, v)])
    iH = np.array([i_ch(a, b) for a, b in zip(vgsH, Vb - v)])
    m = t >= 0
    nan = float('nan')

    def first(cond):
        idx = np.where(cond)[0]
        return t[idx[0]] if len(idx) else nan
    o = dict(Vg_end=float(gL[np.searchsorted(t, 0.0)]))
    o['LS_off'] = first(m & (iL < 0.5) & (gL < VON + 0.5))
    o['mid50'] = first(m & (v > 0.5 * Vb))
    o['mid90'] = first(m & (v > 0.9 * Vb))
    k = np.searchsorted(t, o['mid50']) if not math.isnan(o['mid50']) else 0
    o['i_sw'] = float(i_in[k])
    o['HS_on'] = first(m & (t > tD) & (vgsH > VON))
    o['HS_50'] = first(m & (t > tD) & (vgsH > V50))
    k = np.searchsorted(t, o['HS_on']) if not math.isnan(o['HS_on']) else len(t) - 1
    o['VdsH_on'] = float(Vb - v[k])
    o['i_at_HS_on'] = float(i_in[k])
    rv = np.where(m & (t > (o['mid90'] if not math.isnan(o['mid90']) else 0)) & (i_in < 0))[0]
    o['t_rev'] = t[rv[0]] if len(rv) else nan
    o['E_off'] = float(_trapz(iL[m] * np.maximum(v[m], 0), t[m]))
    o['E_on'] = float(_trapz(iH[m] * np.maximum(Vb - v[m], 0), t[m]))
    o['Vg_HS_end'] = float(vgsH[-1])
    return o


def board_case():
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet', 'variants',
                                             'BENCH_200W_LGE_workbook_unencrypted.xlsx'))
    rt, ds = wb['Res. Tank Design'], wb['Device Setting']
    Cr, Lr = rt['F43'].value * 1e-9, rt['F44'].value * 1e-6
    VREF, TIDLE, IEA, IOSC = ds['D12'].value, ds['D13'].value * 1e-9, ds['D15'].value * 1e-3, ds['D16'].value * 1e-3
    CT, RT = ds['D21'].value * 1e-12, ds['F24'].value * 1e3
    fSU = 1 / (2 * (CT / ((IEA + IOSC) / VREF + 1 / RT) + TIDLE))
    return dict(Lr=Lr, Cr=Cr, fSU=fSU, label='200 W bench (C.r %.0f nF, L.r %.1f uH, f.SU %.0f kHz)'
                % (Cr * 1e9, Lr * 1e6, fSU / 1e3))


NETS = {'board 47 / (10+D)||47': dict(Ron=47.0, Rd=10.0, Rp=47.0),
        '1206 proposal 22 / (4.7+D)||22': dict(Ron=22.0, Rd=4.7, Rp=22.0)}


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else 'bench200'
    if which != 'bench200':
        raise SystemExit('only the bench board is wired in so far: python gate_wave.py')
    B = board_case()
    k897 = _koss_for(897e-12)
    print(B['label'])
    print('MOSFET model: C.gs %.2f nF, C.gd 2.4 nF (V.dg < 0) .. %.0f pF (10 V) .. %.1f pF (100 V); '
          'C.ds scaled x%.3f so 0..400 V charge = 897 pF (k.oss 1: the curve as drawn)'
          % (C_GS * 1e9, crss(10) * 1e12, crss(100) * 1e12, k897))
    cases = [dict(name='start-up 115 Vac FB, line peak', mode='FB', Vbus=163.0, f=B['fSU'], VCC=18.0, VBS=15.7,
                  Lr=B['Lr'], Cr=B['Cr']),
             dict(name='start-up 230 Vac HB, line peak', mode='HB', Vbus=325.0, f=B['fSU'], VCC=18.0, VBS=15.7,
                  Lr=B['Lr'], Cr=B['Cr']),
             dict(name='run 115/230 Vac line peak 180 kHz, I.Lm 8.62 A', mode='CI', Vbus=163.0, f=180e3,
                  VCC=18.0, VBS=17.0, I=8.62)]
    print('channel model: on (0.5 A) at V.GS %.2f V, 50 A at %.2f V (Figure 4)' % (VON, V50))
    hdr = ('%-30s %-5s %-5s %4s | %6s %6s %6s %6s %6s | %6s %6s %6s %6s %6s | %7s %7s'
           % ('network', 'snub', 'koss', 't.D', 'Vg.end', 'LSoff', 'mid50', 'mid90', 'i.sw',
              'HS.on', 'HS50A', 'Vds.on', 'i.on', 'margn', 'E.off', 'E.on'))
    for case in cases:
        print('\n' + '=' * len(hdr) + '\n' + case['name'] + ('  (V.bus %.0f V, f %.0f kHz, half period %.0f ns)'
              % (case['Vbus'], case['f'] / 1e3, 0.5e9 / case['f'])) + '\n' + '=' * len(hdr))
        print('ns from the IC LOUT falling edge (driver delay %.0f ns inside); HOUT rises at t.D;  i: tank '
              'current into the midpoint (+ charges it toward V.bus);  margn: HS channel on -> tank current '
              'reverses (> 0: the body diode still conducts when the HS channel takes over)' % (T_PROP * 1e9))
        print(hdr)
        for nname, net in NETS.items():
            for csn, koss, tD in ((150e-12, k897, 220e-9), (150e-12, k897, 420e-9), (0.0, k897, 420e-9),
                                  (150e-12, 1.0, 420e-9)):
                sol, Y, k0 = simulate(case, net, tD, koss, csn, 100e-12)
                o = measure(sol, Y, case, tD)
                print('%-30s %-5s %-5s %4.0f | %6.1f %6.0f %6.0f %6.0f %6.1f | %6.0f %6.0f %6.1f %6.1f %6.0f | %5.2fuJ %5.2fuJ'
                      % (nname, '%.0fp' % (csn * 1e12), '%.2f' % koss, tD * 1e9, o['Vg_end'], o['LS_off'] * 1e9,
                         o['mid50'] * 1e9, o['mid90'] * 1e9, o['i_sw'], o['HS_on'] * 1e9, o['HS_50'] * 1e9,
                         o['VdsH_on'], o['i_at_HS_on'], (o['t_rev'] - o['HS_on']) * 1e9, o['E_off'] * 1e6,
                         o['E_on'] * 1e6))

if __name__ == '__main__':
    main()
