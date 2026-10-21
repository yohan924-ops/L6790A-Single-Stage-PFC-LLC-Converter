# -*- coding: utf-8 -*-
"""Gate-drive budget at the start-up frequency and in run (2026-10-18, user:
"is 527 kHz manageable with the driver's dead time, rise and fall times; what
happens to the driver when the gate resistor goes down").

Tank numbers come from the x3m3 sheet; driver and MOSFET constants are the
[DS] values of sheet 14c.1 (build_l6790_smath.py).  Three drive networks are
compared with one model:

  gate   = C.g_hi (7.5 nF, the slope of the Qg curve above the plateau - ZVS,
           the drain is already down when the gate rises) behind R.g_int
  driver = source / sink resistance upper bounds R.so / R.si (VCC over the
           short-circuit current minimum, linear output assumed), delay
           mismatch MT between the two channels
  edges  = RC: gate to V.th or V.pl on the way up, to V.pl on the way down

What it answers, per network and frequency
  timing   gate delays, the dead time the IC must give (ADT 40 .. 420 ns), the
           window at f.SU between "incoming channel on after the swing" and
           "on before the tank current reverses"
  power    gate power split between the driver, R.on and the turn-off branch;
           driver junction rise with R.th 120 K/W
  boot     first high-side pulse: what one LOUT pulse puts on C.BOOT through
           R.boot; the steady deficit at f.SU

    python gate_budget.py            the x3m3 tank (sheet)
    python gate_budget.py bench200   the 200 W bench board (its workbook + l6790), 2026-10-21
"""
import math
import os
import sys

import check_trans_spec as CTS

HERE = os.path.dirname(os.path.abspath(__file__))
TANK = sys.argv[1] if len(sys.argv) > 1 else 'x3m3'
_s = CTS.sheet(os.path.join(HERE, '..', '..', 'Smath', 'variants',
                            'L6790A_7p5to1_x3m3.sm'))
g = lambda k: _s[k][0]

if TANK == 'x3m3':
    # ------------------------------------------------------------- tank (sheet)
    fSU, fMAX, fB, fMIN, fR = (g('f.SU') * 1e3, g('f.Max') * 1e3, g('f.sw.b') * 1e3,
                               g('f.Min') * 1e3, g('f.r') * 1e3)
    Lr, Cr = g('L.r') * 1e-6, g('C.r') * 1e-9
    #  c.HB of the sheet already holds the board's 2 x 150 pF drain-source (C.par 400 pF
    #  since 2026-10-18); until then this line added them a second time
    cHB = g('c.HB') * 1e-12
    TT_RUN = g('T.T') * 1e-9                # midpoint swing at I.Lm_pk, run
    LABEL = 'x3m3 tank'
elif TANK == 'bench200':
    # ------------------------------------------------------------- the 200 W bench board
    #  inputs read from its workbook (values typed there, nothing typed here); the oscillator
    #  with the workbook's own formulas (Device Setting D27-D29); the run frequency from
    #  l6790.sweep at the worst line the board is driven from (264 Vac HB = 264 V equivalent)
    import openpyxl
    from l6790 import design, sweep, PRI_FET
    _wb = openpyxl.load_workbook(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet', 'variants',
                                              'BENCH_200W_LGE_workbook_unencrypted.xlsx'))
    _rt, _ds, _sp = _wb['Res. Tank Design'], _wb['Device Setting'], _wb['Design Spec']
    n_, Cr, Lr, Lm_ = (_rt['F9'].value, _rt['F43'].value * 1e-9, _rt['F44'].value * 1e-6,
                       _rt['F45'].value * 1e-6)
    VREF, TIDLE, IEA, IOSC = (_ds['D12'].value, _ds['D13'].value * 1e-9, _ds['D15'].value * 1e-3,
                              _ds['D16'].value * 1e-3)
    CT, RT = _ds['D21'].value * 1e-12, _ds['F24'].value * 1e3
    cHB = _sp['D46'].value * 1e-12
    fMIN = 1 / (2 * (CT * RT + TIDLE))
    fMAX = 1 / (2 * (CT / (IEA / VREF + 1 / RT) + TIDLE))
    fSU = 1 / (2 * (CT / ((IEA + IOSC) / VREF + 1 / RT) + TIDLE))
    fR = 1 / (2 * math.pi * math.sqrt(Lr * Cr))
    _R = design(Vout=25., Pout=_sp['D27'].value, Vo_min=19., dv_out=0.05, Thold=12e-3, Nrect=1,
                fr_t=150e3, fsw_max_spec=225e3, fsw_min_spec=50e3,
                **dict(PRI_FET, C_par=_wb['Power Components']['D72'].value * 1e-12), tD=220e-9,
                n_sel=n_, Cr_sel=Cr, Lr_sel=Lr, Lm_sel=Lm_)
    fB = max(sweep(_R, 264.0, load=ld)[1]['fsw_max'] for ld in (1.0, 0.25, 0.1))
    _ILm = sweep(_R, _R['Vin_min'])[1]['ILm_pk']
    #  run swing: the magnetizing peak carries the node; the slowest bus is 264 Vac HB (373 V)
    TT_RUN = cHB * 373.0 / _ILm
    LABEL = ('200 W bench tank (C.r %.0f nF, L.r %.1f uH, L.m %.1f uH, C.T %.0f pF, R.T %.2f k, '
             'c.HB %.0f pF; run swing at I.Lm %.2f A on 373 V)'
             % (Cr * 1e9, Lr * 1e6, Lm_ * 1e6, CT * 1e12, RT / 1e3, cHB * 1e12, _ILm))
else:
    raise SystemExit('python gate_budget.py [x3m3 | bench200]')
Z0 = math.sqrt(Lr / Cr)
CG = g('C.g_hi') * 1e-9                     # 7.5 nF
RSO, RSI = g('R.so'), g('R.si')             # 10.71 / 9.68 ohm upper bounds
RTH = g('R.th_drv')                         # 120 K/W, SO-14
# [DS] constants of sheet 14c.1 that the parser does not return as rows
VPL, VTH, RGI, MT = 6.3, 4.0, 4.5, 30e-9    # plateau, V.GS(th) typ [ASSUMED 4 V], R.g_int, delay matching
IQ = 480e-6 + 120e-6                        # L6498 quiescent, VCC + floating
VBO_REC = 9.3                               # L6498 floating supply, recommended minimum
PDRV_MAX = 1.0                              # SO-14 at 25 C
ISO, ISI = 1.4, 1.55                        # driver short-circuit currents, min
TA = 70.0                                   # ambient inside the set [ASSUMED]

# ------------------------------------------------------------- networks
#  on:  V -> R.so -> R_on -> R.g_int -> gate
#  off: gate -> R.g_int -> (R_d + diode V_F) || R_p -> R.si -> 0
NETS = [
    dict(name='LGE 18 Oct board   18 V, 47 on, (10 + D) || 47 off, boot 10 ohm x 100 nF',
         V=18.0, Ron=47.0, Rd=10.0, Rp=47.0, Cb=100e-9, Rb=10.0, VFb=1.0, Rpkg=0.1),
    dict(name='design sheet 14c   14.35 V, 4.7 on, (2.2 + D) || 4.7 off, boot ES1J x 470 nF',
         V=14.35, Ron=4.7, Rd=2.2, Rp=4.7, Cb=470e-9, Rb=0.0, VFb=1.3, Rpkg=0.25),
    dict(name='proposal 1206      15 V, 22 on, (4.7 + D) || 22 off, boot 3.3 ohm x 100 nF',
         V=15.0, Ron=22.0, Rd=4.7, Rp=22.0, Cb=100e-9, Rb=3.3, VFb=1.0, Rpkg=0.25),
]
VFD = 0.7                                   # 1N4148W in the turn-off branch


def off_eff(n):
    """Thevenin of the turn-off branch: (R_d + V_F) || R_p -> R_eff, V_eff."""
    Rd, Rp = n['Rd'], n['Rp']
    return Rd * Rp / (Rd + Rp), VFD * Rp / (Rd + Rp)


def i_sw(A, f):
    """Series L-C at V_out ~ 0 driven by a square wave of amplitude A: current at the edge."""
    return A / Z0 * math.tan(math.pi * fR / (2 * f))


def timing(n, f, tD):
    V = n['V']
    tau_on = (RSO + n['Ron'] + RGI) * CG
    Reff, Veff = off_eff(n)
    tau_off = (RSI + Reff + RGI) * CG
    t_th = tau_on * math.log(V / (V - VTH))
    t_pl = tau_on * math.log(V / (V - VPL))
    pulse = 1 / (2 * f) - tD
    Vend = V * (1 - math.exp(-pulse / tau_on))
    t_off = tau_off * math.log((Vend - Veff) / (VPL - Veff))
    t_off_full = tau_off * math.log((V - Veff) / (VPL - Veff))
    return dict(tau_on=tau_on, tau_off=tau_off, t_th=t_th, t_pl=t_pl, pulse=pulse,
                Vend=Vend, t_off=t_off, t_off_full=t_off_full)


def power(n, f, Vend):
    """Per driver (two switches), per cycle energies from a linear gate C."""
    V = n['V']
    Reff, Veff = off_eff(n)
    E_on = CG * Vend * (V - 0.5 * Vend)           # dissipated while charging
    E_off = 0.5 * CG * Vend ** 2                  # dissipated while discharging
    R_on_loop = RSO + n['Ron'] + RGI
    R_off_loop = RSI + Reff + RGI
    s_drv = (RSO / R_on_loop * E_on + RSI / R_off_loop * E_off) / (E_on + E_off)
    P_drv = 2 * (E_on * RSO / R_on_loop + E_off * RSI / R_off_loop) * f + IQ * V
    P_Ron = E_on * n['Ron'] / R_on_loop * f
    # turn-off branch: the current splits R_p : R_d; the diode branch takes R_p/(R_d+R_p)
    kd = n['Rp'] / (n['Rd'] + n['Rp'])
    P_branch = E_off * Reff / R_off_loop * f
    P_Rd = P_branch * (kd ** 2 * n['Rd']) / Reff
    P_Rp = P_branch - P_Rd
    I_d_avg = CG * Vend * f * kd
    I_d_pk = (Vend - VFD) / (RSI + n['Rd'] + RGI) if n['Rp'] > 50 else (Vend - Veff) / R_off_loop * kd
    I_on_pk = V / R_on_loop
    return dict(P_drv=P_drv, s_drv=s_drv, P_Ron=P_Ron, P_Rd=P_Rd, P_Rp=P_Rp,
                I_d_avg=I_d_avg, I_d_pk=I_d_pk, I_on_pk=I_on_pk,
                I_off_pk=(Vend - Veff) / R_off_loop)


def main():
    T = 1 / fSU
    print('%s\n  f.SU %.0f kHz (half period %.0f ns, current reverses T/4 = %.0f ns '
          'after the edge)   f.r %.0f   f.sw,b %.0f   f.Max %.0f   f.Min %.0f kHz'
          % (LABEL, fSU / 1e3, 0.5e9 / fSU, 0.25e9 / fSU, fR / 1e3, fB / 1e3, fMAX / 1e3, fMIN / 1e3))
    print('start-up currents at V.out ~ 0 (L.r-C.r, Z0 %.1f ohm): ' % Z0 +
          '   '.join('%s %.1f A' % (lab, i_sw(A, fSU)) for lab, A in
                     (('FB 155 V', 155.0), ('FB 235 V', 235.0), ('HB 325 V', 325 / 2.0),
                      ('HB 373 V', 373 / 2.0))))
    swing = {}
    for lab, A, Vb in (('FB', 155.0, 155.0), ('HB', 325 / 2.0, 325.0)):
        I = i_sw(A, fSU)
        TT = cHB * Vb / I
        # after the current reverses it grows at V_bus / L.r; the node swings back
        # quadratically: V(t) = (V_bus / L.r) t^2 / (2 c.HB).  Time to 50 V and to V_bus.
        t50 = math.sqrt(2 * cHB * 50.0 * Lr / Vb)
        tfull = math.sqrt(2 * cHB * Vb * Lr / Vb)
        swing[lab] = (TT, t50, tfull)
        print('  %s: swing T.T %.0f ns (c.HB %.2f nF, %.1f A, %.1f V/ns);  after the reversal '
              'the node drifts back 50 V in %.0f ns, fully in %.0f ns' %
              (lab, TT * 1e9, cHB * 1e9, I, I / cHB * 1e-9, t50 * 1e9, tfull * 1e9))
    print('run: T.T %.0f ns at I.Lm_pk;  ADT range 40 .. 420 ns;  driver mismatch %.0f ns;  '
          'V.th %.1f V [assumed], V.pl %.1f V' % (TT_RUN * 1e9, MT * 1e9, VTH, VPL))
    for n in NETS:
        print('\n' + '=' * 100 + '\n' + n['name'] + '\n' + '=' * 100)
        tm = timing(n, fSU, 420e-9)
        tm2 = timing(n, fSU, 220e-9)
        print('gate: tau_on %.0f ns (to V.th %.0f, to V.pl %.0f ns)   tau_off %.0f ns '
              '(V to V.pl %.0f ns)' % (tm['tau_on'] * 1e9, tm['t_th'] * 1e9, tm['t_pl'] * 1e9,
                                       tm['tau_off'] * 1e9, tm['t_off_full'] * 1e9))
        print('      driver peak current: on %.2f A (limit %.1f min), off %.2f A (limit %.2f min)'
              % (power(n, fSU, n['V'])['I_on_pk'], ISO, power(n, fSU, n['V'])['I_off_pk'], ISI))
        print('f.SU pulse: t.D 420 -> on-time %.0f ns, gate reaches %.1f V, off delay to V.pl '
              '%.0f ns;  t.D 220 -> %.0f ns, %.1f V, %.0f ns'
              % (tm['pulse'] * 1e9, tm['Vend'], tm['t_off'] * 1e9,
                 tm2['pulse'] * 1e9, tm2['Vend'], tm2['t_off'] * 1e9))
        # dead time the IC must give: t.D >= t_off + T.T - t_th + MT (incoming channel at
        # V.th after the swing); and the soft upper limit: incoming at V.pl before the
        # current reverses, t.D <= t_off + T/4 - t_pl - MT; the cliff: + drift-back time
        need_run = tm['t_off_full'] + TT_RUN - tm['t_th'] + MT
        print('run:  dead time the IC must give >= %.0f ns  (ADT 40 .. 420: %s)'
              % (need_run * 1e9, 'inside' if 40e-9 <= need_run <= 420e-9 else 'OUTSIDE'))
        for lab in ('FB', 'HB'):
            TT, t50, tfull = swing[lab]
            lo = tm['t_off'] + TT - tm['t_th'] + MT
            hi = tm['t_off'] + T / 4 - tm['t_pl'] - MT
            print('f.SU %s: IC dead time must be %.0f .. %.0f ns for clean ZVS;  420 ns is %s;  '
                  'partial hard switching (50 V) only beyond %.0f ns, full beyond %.0f ns'
                  % (lab, lo * 1e9, hi * 1e9,
                     'inside' if lo <= 420e-9 <= hi else '%+.0f ns outside' % ((420e-9 - hi) * 1e9),
                     (hi + t50) * 1e9, (hi + tfull) * 1e9))
        print('%-10s %6s  %7s %6s %6s  %7s %7s %7s  %6s %6s' %
              ('f', 'gate V', 'P.drv W', 'share', 'dTj K', 'R.on W', 'R.d W', 'R.p W',
               'Id avg', 'Id pk'))
        for lab, f, tD in (('f.SU 1 ms', fSU, 420e-9), ('f.Max', fMAX, 220e-9),
                           ('f.sw,b', fB, 220e-9), ('190 kHz', 190e3, 220e-9),
                           ('f.Min', fMIN, 220e-9)):
            Vend = timing(n, f, tD)['Vend']
            p = power(n, f, Vend)
            print('%-10s %6.1f  %7.2f %6.2f %6.0f  %7.3f %7.3f %7.3f  %5.0fmA %5.2fA' %
                  (lab, Vend, p['P_drv'], p['s_drv'], p['P_drv'] * RTH, p['P_Ron'],
                   p['P_Rd'], p['P_Rp'], p['I_d_avg'] * 1e3, p['I_d_pk']))
        pB = power(n, fB, timing(n, fB, 220e-9)['Vend'])
        print('      at f.sw,b: Tj = %.0f + %.0f = %.0f C;  driver rating %.2f W at 25 C -> '
              '%.2f W at %.0f C ambient (Tj 150)   R.on in a %.2f W package: %.0f %%'
              % (TA, pB['P_drv'] * RTH, TA + pB['P_drv'] * RTH, PDRV_MAX,
                 (150 - TA) / RTH, TA, n['Rpkg'], 100 * pB['P_Ron'] / n['Rpkg']))
        # bootstrap
        Rb = n['Rb'] if n['Rb'] > 0 else 0.5          # a diode alone: its dynamic resistance
        tau_b = Rb * n['Cb']
        Vb = n['V'] - n['VFb']
        first = ['%.0f ns -> %.1f V' % (tp * 1e9, Vb * (1 - math.exp(-tp / tau_b)))
                 for tp in (370e-9, 530e-9, 730e-9)]
        dV = CG * tm['Vend'] / n['Cb']
        k = math.exp(-tm['pulse'] / tau_b)
        deficit = dV * k / (1 - k)
        print('boot: tau %.2f us;  first LOUT pulse charges C.BOOT from 0: %s  (needs >= %.1f V '
              'for the first HOUT);  f.SU steady: %.2f V per HS pulse, deficit %.2f V, '
              'V.BS min %.1f V;  peak charge current into an empty C.BOOT %.1f A'
              % (tau_b * 1e6, ',  '.join(first), VBO_REC, dV, deficit,
                 Vb - deficit - dV, Vb / Rb))
    # R.on sweep: where the gate power goes
    print('\n' + '=' * 100 + '\nR.on sweep at f.sw,b %.0f kHz (continuous worst, line peak), '
          'turn-off branch (R.on/4.7 + D) || R.on, 1206 R.on\n' % (fB / 1e3) + '=' * 100)
    print('%-5s  %-34s  %-34s' % ('R.on', '18 V: P.drv / dTj / R.on W / t.th', '15 V: P.drv / dTj / R.on W / t.th'))
    for Ron in (4.7, 10.0, 15.0, 22.0, 33.0, 47.0):
        cells = []
        for V in (18.0, 15.0):
            n = dict(V=V, Ron=Ron, Rd=max(2.2, round(Ron / 4.7, 1)), Rp=Ron, Cb=100e-9,
                     Rb=3.3, VFb=1.0, Rpkg=0.25)
            tm = timing(n, fB, 220e-9)
            p = power(n, fB, tm['Vend'])
            cells.append('%.2f W / %3.0f K / %.3f W / %3.0f ns' %
                         (p['P_drv'], p['P_drv'] * RTH, p['P_Ron'], tm['t_th'] * 1e9))
        print('%-5.1f  %-34s  %-34s' % (Ron, cells[0], cells[1]))


if __name__ == '__main__':
    main()
