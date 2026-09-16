# -*- coding: utf-8 -*-
"""L6790A single-stage PF LLC - design guide rev1.1 equations [1]..[106], faithfully."""
from math import pi, sqrt, sin, cos, atan


def M(fn, Q, lam):
    A = 1 + lam - lam / fn ** 2
    return 1.0 / sqrt(A * A + Q * Q * (fn - 1.0 / fn) ** 2)


def solve_fn(Mreq, Q, lam, fn0):
    """[59] inductive-side root: scan down from 3.0, then bisect."""
    lo = hi = None
    fn = 3.0
    prev = M(fn, Q, lam)
    while fn > fn0 * 1.0000001:
        fn2 = fn - 1e-4
        cur = M(fn2, Q, lam)
        if (prev - Mreq) * (cur - Mreq) <= 0:
            lo, hi = fn2, fn
            break
        prev, fn = cur, fn2
    if lo is None:
        return None                       # burst region (no inductive solution)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if (M(lo, Q, lam) - Mreq) * (M(mid, Q, lam) - Mreq) <= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def phase(fn, Q, lam):
    """[37] tank input impedance phase."""
    num = (lam ** 2 + lam + (fn ** 2 - 1) * Q ** 2) * fn ** 2 - lam ** 2
    return atan(num / (Q * fn ** 3))


def design(Vac_min=90., Vac_max=264., fl=50., fl_min=47.,
           Vout=60., Pout=240., Vo_min=50., dv_out=0.10, Thold=10e-3,
           eta_HB=0.98, fr_t=150e3, fsw_max_spec=225e3, fsw_min_spec=50e3,
           Nrect=2, Vrect=0.0, c_HB=500e-12, tD=220e-9, m_ZVS=0.15,
           d_res=0.05, Vin_nom=225., R_EMI=0.15, Vf_BR=0.08, Rd=0.04,
           Cr_sel=None, Lr_sel=None, Lm_sel=None, n_sel=None, label=""):
    V_BOH, V_BIH = 235., 245.
    # --- 3.2 power budget [6]-[17]
    Iout = Pout / Vout                                                   # [6]
    eta_rect = Vout / (Vout + Nrect * Vrect)                             # [7]
    Psec = Pout / eta_rect                                               # [8]
    Pin_LLC = Pout / (eta_rect * eta_HB)                                 # [9]
    Iin_max = Pin_LLC / Vac_min                                          # [10]
    Pd_LLC = Psec * (1 - eta_HB) / eta_HB                                # [12]
    Pd_BR = 2 * (2 * sqrt(2) / pi * Iin_max * Vf_BR) + 2 * Rd * Iin_max ** 2   # [13]
    Pd_EMI = R_EMI * Iin_max ** 2                                        # [14]
    eta_ac = Pin_LLC / (Pin_LLC + Pd_BR + Pd_EMI)                        # [15]
    eta_tot = eta_HB * eta_rect * eta_ac                                 # [16]
    Pin = Pout / eta_tot                                                 # [17]
    # --- 3.3 equivalent input [18]-[20]
    Vin_min = min(2 * Vac_min, V_BIH / sqrt(2))                          # [18]
    Vin_max = Vac_max
    Vin_FBmax = 2 * V_BOH / sqrt(2)                                      # [19]
    Vin_res = Vin_nom * (1 - d_res)                                      # [20]
    # --- 3.4 turns ratio [21]-[22]
    Vo_eff = Vout + Nrect * Vrect                                        # [21]
    n_calc = sqrt(2) * Vin_res / (2 * Vo_eff)                            # [22]
    n = n_sel if n_sel else n_calc
    # --- 3.5 gain [23]-[24]
    MVmin = 2 * n * Vo_eff / (sqrt(2) * Vin_min)                         # [23]
    MVmax = 2 * n * Vo_eff / (sqrt(2) * Vin_max)                         # [24]
    MFBmax = 2 * n * Vo_eff / (sqrt(2) * Vin_FBmax)                      # [24a]
    # --- 3.6 lambda [26]-[30]
    # [26] asks that the tank can reach the LOWEST required gain, and that
    # happens at the HIGHEST equivalent input.  After morphing that is the FB
    # side of the threshold (332 Vac), not the AC maximum (264 Vac) - the same
    # corner RTC was re-pointed to (guide C.8 / cause E).  Using Vac_max here
    # understates the bound by more than a hundred times.
    l1 = 1 / MFBmax - 1                                                  # [26]
    l2 = l1 / (1 - (fr_t / fsw_max_spec) ** 2)                           # [27]
    lTD = l1 / (1 - (pi ** 2 / 8) * (fr_t / fsw_max_spec) ** 2)          # [28]
    l3 = (fsw_min_spec / fr_t) ** 2 / (1 - (fsw_min_spec / fr_t) ** 2)   # [29]
    lam = max(l1, l2, lTD, l3)                                           # [30]
    # --- 3.7 Rac, Q [31]-[35]
    Rac = 4 / pi ** 2 * n ** 2 * Vo_eff ** 2 / Pin_LLC                   # [31]
    Qz1 = (lam / MVmin * sqrt(1 / lam + MVmin ** 2 / (MVmin ** 2 - 1))
           if MVmin > 1 else float('inf'))                               # [32]
    Qz2 = 2 / pi * lam * tD / (Rac * c_HB)                               # [33]
    Qz = min(Qz1, Qz2) / (1 + m_ZVS)                                     # [34]
    Z0 = Rac * Qz                                                        # [35]
    # --- 3.9 tank [43]-[45]
    Cr_c = 1 / (2 * pi * fr_t * Z0)
    Cr = Cr_sel or Cr_c                                                  # [43]
    Lr_c = 1 / (Cr * (2 * pi * fr_t) ** 2)
    Lr = Lr_sel or Lr_c                                                  # [44]
    Lm_c = Lr / lam
    Lm = Lm_sel or Lm_c                                                  # [45]
    # --- 3.10 final check [46]-[54]
    lam_a = Lr / Lm                                                      # [46]
    nT = n * sqrt(1 + lam_a)                                             # [47]
    Z0s = sqrt(Lr / Cr)                                                  # [48]
    Z0p = sqrt((Lr + Lm) / Cr)                                           # [49]
    fr = 1 / (2 * pi * sqrt(Lr * Cr))                                    # [50]
    fn0 = sqrt(lam_a / (1 + lam_a))
    fo = fr * fn0                                                        # [51]
    Lmu = sqrt(Lm * (Lm + Lr))                                           # [52]
    LL1 = Lm + Lr - Lmu                                                  # [53]
    LL2 = LL1 / nT ** 2                                                  # [54]
    Qpk = Z0s / Rac                                                      # [58]
    # --- 6.2 output capacitor [101]-[106]
    Cout_ripple = Iout / (2 * pi * fl_min * Vout * dv_out)               # [101]
    Cout_hold = 2 * Pout * Thold / (Vout ** 2 - Vo_min ** 2)             # [102]
    Cout_req = max(Cout_ripple, Cout_hold)                               # [103]
    R = dict(locals())
    R.pop('R', None)
    return R


def sweep(R, Vac_eq, load=1.0, N=181):
    """[55]-[70a] line-cycle sweep at one equivalent input voltage."""
    n, Vo_eff, lam_a = R['n'], R['Vo_eff'], R['lam_a']
    fr, fn0, Lm, Qpk = R['fr'], R['fn0'], R['Lm'], R['Qpk']
    Iout, Nrect = R['Iout'] * load, R['Nrect']
    rows = []
    for i in range(1, N):
        th = pi / 2 * i / (N - 1)
        Mreq = 2 * n * Vo_eff / (sqrt(2) * Vac_eq * sin(th))             # [57]
        Q = Qpk * load * sin(th) ** 2                                    # [58]
        fn = solve_fn(Mreq, Q, lam_a, fn0)
        if fn is None:
            rows.append(None)
            continue
        fsw = fn * fr                                                    # [60]
        fsw_s = max(fsw, fr)
        Ioi = 2 * Iout * sin(th) ** 2                                    # [56]
        Ipk = pi * (fr / fsw) * Ioi / (1 - cos(pi * fr / fsw_s))         # [63]
        d = min(fsw, fr) / fr                                            # [64]
        # [63] takes the sine as TRUNCATED when fsw > fr - that is exactly what
        # its 1-cos(pi*fr/fsw) denominator is. [64] then squared it as though it
        # were a full half sine, which drops the part of the waveform that never
        # comes back to zero: 8 % of the rms at the FB corner. Below resonance
        # dphi = pi and this factor is exactly 1, so nothing moves there - and
        # both worked designs have their worst secondary rms at LOW line.
        dphi = pi * fr / fsw_s                                           # [64a]
        k_tr = 1.0 - sin(2 * dphi) / (2 * dphi)                          # [64a]
        Isec_w = (Ipk * sqrt(d * k_tr / 4) if Nrect == 1
                  else Ipk * sqrt(d * k_tr / 2))                         # [64] per winding / path
        Isec_node = Ipk * sqrt(d * k_tr / 2)                             # into the output node (both cases)
        Idio = Isec_w if Nrect == 1 else Isec_w / sqrt(2)                # [65]
        Itr = Ipk / n                                                    # [66]
        ILm = 0.25 * n * Vo_eff / (Lm * fsw_s)                           # [67]
        Ipri = sqrt(Itr ** 2 / 2 + ILm ** 2 / 3
                    + (ILm * fsw * (1 / fsw - 1 / fr)) ** 2)             # [68]
        Imos = Ipri / sqrt(2)                                            # [69]
        comp = max(ILm * (2 * x / 1000 - 1) + Itr * sin(pi * x / 1000)
                   for x in range(0, 1001))                              # [79] composite tank peak
        Tzc = phase(fn, Q, lam_a) / (2 * pi * fsw)                       # [38a]
        rows.append(dict(th=th, fsw=fsw, fn=fn, Q=Q, Mreq=Mreq, Ioi=Ioi, Ipk=Ipk, d=d,
                         Isec_w=Isec_w, Isec_node=Isec_node, Idio=Idio, Itr=Itr, ILm=ILm,
                         Ipri=Ipri, Imos=Imos, comp=comp, Tzc=Tzc))
    ok = [r for r in rows if r]
    ms = lambda k: sqrt(sum(r[k] ** 2 for r in ok) / len(ok))
    return rows, dict(
        fsw_max=max(r['fsw'] for r in ok), Tzc_min=min(r['Tzc'] for r in ok),
        Isec_pk=max(r['Ipk'] for r in ok), Itr_pk=max(r['Itr'] for r in ok),
        ILm_pk=max(r['ILm'] for r in ok), comp_pk=max(r['comp'] for r in ok),
        Ipri_pk=max(r['Ipri'] for r in ok), Imos_pk=max(r['Imos'] for r in ok),
        Ipri_lc=ms('Ipri'), Imos_lc=ms('Imos'), Isec_lc=ms('Isec_w'), Idio_lc=ms('Idio'),
        ICout=sqrt(max(0.0, sum(r['Isec_node'] ** 2 for r in ok) / len(ok)
                       - R['Iout'] ** 2 * load ** 2)))
