# -*- coding: utf-8 -*-
"""Every number the design guide's worked example prints, for one design point.

    set AN_VARIANT=7p5to1 && python guide_vals.py

The guide (Korean markdown, and the English translation of it) carries its
example values as text. This prints them all from the same sources the
application note uses - an_pdf.V (l6790.py + the variant sheet) - so that the
text can be checked against, or rewritten from, one listing instead of from
memory. Nothing here is typed.
"""
import os
import sys
from math import pi, sqrt, sin, atan

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import an_pdf as A                                                # noqa: E402
import l6790                                                       # noqa: E402

V, R, SH, SA, SB = A.V, A.R, A.SH, A.SA, A.SB
out = []


def sec(t):
    out.append('\n== %s' % t)


def row(k, v, u=''):
    out.append('%-22s %s %s' % (k, v, u))


def f(x, d=2):
    return ('%%.%df' % d) % x


# ---------------------------------------------------------------- tank
sec('tank / ratio (variant %s)' % A.AN_VARIANT)
for k in ('n.calc', 'n', 'n.T', 'N.x', 'N.p', 'N.s', 'V.refl', 'λ.1', 'λ.2',
          'λ.TD', 'λ.3', 'λ', 'λ.act', 'R.ac', 'Q.ZVS1', 'Q.ZVS2', 'Q.ZVS3',
          'Z.0', 'C.r_calc', 'C.r', 'L.r_calc', 'L.r', 'L.m_calc', 'L.m',
          'Z.0s', 'Z.0p', 'f.r', 'f.n0', 'f.o', 'L.mu', 'L.L1', 'L.L2',
          'L.open', 'L.short', 'Q.pk', 'M.HBmin', 'M.ACmax', 'M.FBthr',
          'M.inf', 'k.lam', 'M.ACa', 'M.ACb', 'M.ACnom'):
    row(k, SH.get(k))
row('m = 1+1/lam_act', f(1 + 1 / SH['λ.act'], 2))
row('lam_act/lam', f(SH['λ.act'] / SH['λ'], 3))
row('Q_ZVS3 (tool D20)', f(sqrt(SH['λ'] * (1 + SH['λ'])) / SH['M.HBmin'], 4))
row('Q_pk vs Q_ZVS3', f(100 * (1 - SH['Q.pk'] / (sqrt(SH['λ'] * (1 + SH['λ'])) / SH['M.HBmin'])), 1), '% below')

# peak gain of the selected tank at Q_pk, and at the design Q_ZVS1
lam_a, Qpk = R['lam_a'], R['Qpk']


def peak_gain(Q, lam):
    fn0 = sqrt(lam / (1 + lam))
    best = 0
    fn = fn0 * 1.0001
    while fn < 1.0:
        best = max(best, l6790.M(fn, Q, lam))
        fn += 1e-4
    return best


row('M_peak @Q_pk,lam_act', f(peak_gain(Qpk, lam_a), 4))
row('gain margin %', f(100 * (peak_gain(Qpk, lam_a) / R['MVmin'] - 1), 1))
row('M_peak @Q_ZVS1,lam', f(peak_gain(R['Qz1'], R['lam']), 4),
    'vs MVmin %s' % f(R['MVmin'], 4))
row('no-load corner kHz', V['fnl'])
row('M_FBthr - M_inf', f(SH['M.FBthr'] - SH['M.inf'], 4))

# ---------------------------------------------------------------- ZVS
sec('ZVS')
row('sheet T.ZC.a/.b', (SH['T.ZC.a'], SH['T.ZC.b']))
row('sweep Tzc corner', f(SA['Tzc_min'] * 1e9, 1), 'ns @Vin_min FL')
import an_body
grid = an_body._zvs_grid(A)
for r in grid:
    out.append('   ' + '  '.join('%10s' % c for c in r))
row("worst", an_body.ZVS_WORST)
# corner point detail at theta = pi/2
rowsA, _ = l6790.sweep(R, R['Vin_min'], 1.0)
last = rowsA[-1]
row('corner fn, phi', (f(last['fn'], 4), f(l6790.phase(last['fn'], last['Q'], lam_a), 4)))
row('corner Tzc', f(last['Tzc'] * 1e9, 1))
for k in ('I.R1_pk', 'I.R0', 'T.T'):
    row(k, SH[k])


def closed(lam, Q, Qz1, M, fr):
    fnmin = 1 / sqrt(1 + (1 / lam) * (1 - M ** (-(1 + (Q / Qz1) ** 5))))
    ph = l6790.phase(fnmin, Q, lam)
    return fnmin, ph, ph / (2 * pi * fnmin * fr)


fn_c, ph_c, t_c = closed(R['lam'], R['Qz'], R['Qz1'], R['MVmin'], R['fr'])
row('closed form design lam/Q_ZVS', f(t_c * 1e9, 1), 'ns  fnmin %s' % f(fn_c, 4))
fn_c2, ph_c2, t_c2 = closed(lam_a, Qpk, R['Qz1'], R['MVmin'], R['fr'])
row('closed form lam_act/Q_pk', f(t_c2 * 1e9, 1), 'ns')
row('closed vs sweep %', f(100 * (t_c / SA['Tzc_min'] - 1), 1))

# ---------------------------------------------------------------- hysteresis band
sec('hysteresis band (narrow -> wide)')
for veq_lo, veq_hi, tag in ((R['Vin_min'], 332.34, 'narrow'),
                            (166.17, 346.52, 'wide')):
    _, lo = l6790.sweep(R, veq_lo, 1.0)
    _, hi = l6790.sweep(R, veq_hi, 1.0)
    Mreq = 2 * R['n'] * R['Vo_eff'] / (sqrt(2) * veq_lo)
    row(tag + ' Mreq', f(Mreq, 4))
    row(tag + ' peak margin %', f(100 * (peak_gain(Qpk, lam_a) / Mreq - 1), 1))
    row(tag + ' fsw_max', f(hi['fsw_max'] / 1e3, 1))
    row(tag + ' VCO margin %', f(100 * (SH['f.Max'] / (hi['fsw_max'] / 1e3) - 1), 1))
    row(tag + ' Tzc', f(lo['Tzc_min'] * 1e9, 0))
    row(tag + ' ZVS x', f(lo['Tzc_min'] * 1e9 / V['tD'], 2))

# ---------------------------------------------------------------- fsw(theta)
sec('fsw(theta) kHz, full load')
cols = (R['Vin_min'], 180., 225., 264., 332.34)
rws = {c: l6790.sweep(R, c, 1.0)[0] for c in cols}
for deg in (15, 30, 45, 60, 90):
    i = int(round(deg / 90.0 * 180)) - 1
    out.append('   %3d deg  ' % deg + '  '.join(
        '%7.1f' % (rws[c][i]['fsw'] / 1e3) for c in cols))
row('fsw peaks', [(nm, f(pk, 1), ab) for nm, _v, pk, ab in V['fswPk']])
row('fsw_max_op / design', (SH['f.sw_max_op'], SH['f.sw_max_des']))
row('d at corner', f(SA['fsw_max'] / R['fr'], 3),
    '  sqrt(1/d)-1 = %s %%' % f(100 * (sqrt(R['fr'] / SA['fsw_max']) - 1), 1))

# ---------------------------------------------------------------- currents
sec('currents: corners')
for veq, deg in ((R['Vin_min'], 90), (180., 90), (R['Vin_min'], 45),
                 (264., 90), (332.34, 90)):
    rr = l6790.sweep(R, veq, 1.0)[0]
    r = rr[int(round(deg / 90.0 * 180)) - 1]
    out.append('   %6.1f V %2d deg  fsw %6.1f  Ipk %6.1f  Itr %6.2f  ILm %6.2f'
               '  Ipri %6.2f  Imos %5.2f  comp %6.2f  d %.3f'
               % (veq, deg, r['fsw'] / 1e3, r['Ipk'], r['Itr'], r['ILm'],
                  r['Ipri'], r['Imos'], r['comp'], r['d']))
for k in ('I.sec_pk', 'I.trafo_pk', 'I.Lm_pk', 'I.pri_rms', 'I.mos_rms',
          'I.Lr_pk', 'I.pri_lc', 'I.mos_lc', 'I.diode_lc', 'I.Cout_rms',
          'I.node_ms', 'I.Cout_each', 'I.sec_rms', 'I.sec_leg', 'r.tr'):
    row(k, SH[k])
row('ICout HF part', f(V['ICouthf'], 2), ' 2fl %s' % f(V['ICout2f'], 2))
# pi/4 single point, HF only
r45 = rws[R['Vin_min']][int(round(45 / 90.0 * 180)) - 1]
hf45 = sqrt(max(0, 0.5 * r45['d'] * r45['Ipk'] ** 2 - r45['Ioi'] ** 2))
row('HF @pi/4 only', f(hf45, 1), ' vs %s : %s %% low' % (
    f(SH['I.Cout_rms'], 2), f(100 * (1 - hf45 / SH['I.Cout_rms']), 0)))
row('CT trap: [64] value', f(r45['Isec_w'], 1), 'node %s' % f(r45['Isec_node'], 1))
# line-cycle with the winding value put into [70a] by mistake
ok = [r for r in rws[R['Vin_min']] if r]
wrong = sqrt(max(0, sum(r['Isec_w'] ** 2 for r in ok) / len(ok) - R['Iout'] ** 2))
node = sqrt(sum(r['Isec_node'] ** 2 for r in ok) / len(ok))
row('[70a] with winding rms', f(wrong, 1), ' node rms %s  ratio %s' % (
    f(node, 1), f(SH['I.Cout_rms'] / wrong, 2)))
# exact vs [68] at corner
Itr, ILm, d = last['Itr'], last['ILm'], last['d']
row('[68] exact', f(sqrt(d / 2 * Itr ** 2 + ILm ** 2 * (1 - 2 * d / 3)), 2),
    ' vs [68] %s' % f(last['Ipri'], 2))
# C.18 : pi/4 point vs line cycle
row('C.18 Ipri pi/4 vs lc', (f(r45['Ipri'], 2), f(SH['I.pri_lc'], 2),
                              f(100 * (SH['I.pri_lc'] / r45['Ipri'] - 1), 1)))
row('C.18 Idio pi/4 vs lc', (f(r45['Idio'], 2), f(SH['I.diode_lc'], 2),
                              f(100 * (SH['I.diode_lc'] / r45['Idio'] - 1), 1)))
Rhot = SH['R.dson_s']
p45 = 2 * 2 * Rhot * 1e-3 * (r45['Idio'] / 2) ** 2
plc = SH['P.SR']
row('C.18 SR loss', (f(p45, 2), f(plc, 2), f(plc / p45, 2), 'Rth %s -> %s' % (
    f(100 / p45, 1), f(100 / plc, 1))))
# C.30 : truncation at the FB corner
rB = l6790.sweep(R, 332.34, 1.0)[0]
okB = [r for r in rB if r]
above = sum(1 for r in okB if r['fsw'] > R['fr']) / float(len(okB))
old = sqrt(sum((r['Ipk'] * sqrt(r['d'] / 4)) ** 2 for r in okB) / len(okB))
new = sqrt(sum(r['Isec_w'] ** 2 for r in okB) / len(okB))
row('C.30 FB corner', ('above %s %%' % f(100 * above, 1), f(old, 2), f(new, 2),
                       '+%s %%' % f(100 * (new / old - 1), 1)))

# ---------------------------------------------------------------- IC network
sec('IC network')
for k in ('C.T_max', 'C.T_min', 'C.T', 'R.T_ceil', 'R.T', 'f.Min', 'f.Max',
          'f.SU', 'τ.RT', 'k.floor', 'k.ceil', 'R.CS1', 'R.CS2', 'R.CS',
          'N.RCS_req', 'N.RCS', 'P.RCS_pk', 'P.RCS', 'P.in_max_act',
          'I.OCP1', 'I.OCP2', 'k.OCP', 'R.BM_sel', 'V.BM_eq', 'R.CFG_max',
          'V.BO_act', 'k.BO', 'n.aux', 'n.aux_max', 'V.aux', 'V.aux_OVP2',
          'V.OVP1_out', 'V.OVP2_out', 'R.ZCD_L', 'R.ZCD_L_sel', 'R.ZCD_H',
          'R.ZCD_H_sel', 'V.OVP1_act', 'k.OVP1', 'V.OVP2_act', 'V.out_SUend',
          'ΔV.FBBM', 'ΔR.BM', 'R.BM_rec', 'C.in', 'C.in_sel'):
    row(k, SH.get(k))
RT, CT, Vref, IEA = SH['R.T'] * 1e3, SH['C.T'] * 1e-12, 1.5, 400e-6
for Ti in (250e-9, 350e-9, 700e-9):
    fmin = 1 / (2 * (CT * RT + Ti))
    fmax = 1 / (2 * (CT / (IEA / Vref + 1 / RT) + Ti))
    row('T_idle %d ns' % (Ti * 1e9), 'fMin %s  fMax %s  floor %s  ceil %s'
        % (f(fmin / 1e3, 1), f(fmax / 1e3, 1), f(fmin / 1e3 / SH['f.o'], 3),
           f(fmax / 1e3 / SH['f.sw_max_op'], 3)))
row('swap ZCD', f(2.3 / SH['n.aux'] * (SH['R.ZCD_L_sel'] / SH['R.ZCD_H_sel'] + 1), 2), 'V')
row('R_ZCD_H calc formula', f(SH['R.ZCD_L_sel'] * (SH['n.aux'] * SH['V.OVP1_out'] / 2.3 - 1), 1))

# ---------------------------------------------------------------- output / semis / transformer
sec('output bank, semis, transformer')
for k in ('C.ripple', 'C.hold_req', 'C.out', 'n.C', 'ESR.out', 'ΔV.out',
          'ΔV.out_pc', 't.hold_act', 'k.hold', 'R.N0', 'R.Nact', 'C.cer_min',
          'I.BR_rms', 'I.BR_avg', 'P.BR', 'V.DS_pri', 'I.pri_rating',
          'R.dson_p_hot', 'P.mos_sw', 'P.mos_dc', 'R.dson_req_dev_p',
          'V.bd_rr', 'I.bd_rr', 'V.DS_sec', 'V.DS_sec_rec', 'I.sec_rating',
          'I.SR_dev', 'I.SR_pk_dev', 'R.dson_s', 'P.SR_dev', 'P.SR', 'k.PSR',
          'B.pk', 'A.e_req_mm', 'k.Ae', 'A.L', 'I.sat_eq', 'I.sat_spec',
          'L.open_x', 'n.SR', 'n.par', 'k.Ploss'):
    row(k, SH.get(k))
row('Rth req', f(100 / SH['P.mos_dc'], 1), 'C/W (100 K)')
row('SR leg W', f(SH['P.SR'] / 2, 2), ' with 3 parallel %s' % f(SH['P.SR'] / 2 * 2 / 3, 2))
row('Bpk wrong (Lm,Np)', f(SH['B.pk'] / sqrt(1 + lam_a), 1), 'mT  Ae wrong %s' % f(SH['A.e_req_mm'] / sqrt(1 + lam_a), 0))
row('sqrt(1+lam)-1 %', f(100 * (sqrt(1 + lam_a) - 1), 1))
row('L_short per unit', f(SH['L.short'] / SH['N.x'], 2))
row('Ae 1T secondary', f(SH['A.e_req_mm'] * SH['N.s'], 0))
row('I_eq*1.5', f(1.5 * SH['I.sat_eq'], 1))
row('sat margin %', f(100 * (SH['I.sat_spec'] / SH['I.sat_eq'] - 1), 0))
row('Ldrop %', f(V['Ldrop'], 1))
row('Cratio, Cbulk', (f(V['Cratio'], 0), f(V['Cbulk'], 0)))
row('tholdVo', f(V['tholdVo'], 2))
row('ripLHS/RHS', (f(V['ripLHS'], 3), f(V['ripRHS'], 3), f(V['ripK'], 2)))

print('\n'.join(str(x) for x in out))
