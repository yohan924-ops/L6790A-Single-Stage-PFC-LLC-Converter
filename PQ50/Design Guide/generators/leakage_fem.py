# -*- coding: utf-8 -*-
"""The drawn winding solved as a 2-D field: leakage, gap, strand loss.

Written 2026-09-30 for the PQ 50/50 transformer.  leakage.py solves the
window with the core as an ideal boundary and weights every conductor with
the one mean turn l_N.  On a PQ core that is not good enough, for two
reasons found while the design was checked:

  * the back plate is a bow tie, not a rectangle, so much less of a turn
    is inside the core than the core depth suggests (cores.zones());
  * the winding is deep (9.7 mm on an 11.6 mm tube radius), so an outer
    turn is some 30 % longer than an inner one, and the energy has to be
    weighted by the length of the turn AT ITS RADIUS.  With one l_N the
    two halves of the centre tap come out in the wrong order.

So the section is solved twice with fem2d (finite volumes on a tensor
grid, A = 0 on the axis and on the far walls):

  'core' - through the outer legs: centre leg with its gap, back plates,
           outer legs, ferrite at MU_R;
  'end'  - where the turn leaves the core: the centre leg alone;

and every cell is weighted with the length of turn at its radius that
lies in that kind of section (cores.zones(): the 'leg' zone counts as
core, the 'yoke' zone - under the plate, no outer leg - at
cores.YOKE_SHARE, the rest as end).  The round centre leg is a slab in
2-D; its cells are weighted with pi * r_leg, so that the slab integrates to
the leg's area.  Every conductor is stranded (0.10 mm), so the field is the
static one and the strand eddy loss goes with omega^2.

Results are cached in .fem_cache.json beside this file (a solve is some
seconds); the key holds every number the solve depends on.

    python leakage_fem.py        the report: L_short both halves shorted and
                                 each half alone, the yoke share at 0 / 0.5
                                 / 1, wound tight, the partition trimmed, the
                                 gap for L_open, the strand loss
"""
import hashlib
import json
import math
import os

import numpy as np

import fem2d as F

MU_R = 2000.0            # ferrite, relative permeability - ASSUMED (N97
                         # initial permeability is 2300 +-25 %; the leakage
                         # hardly depends on it, the gap does a little)
RHO_CU = 2.26e-8         # ohm m, copper at 100 C
MM = 1e-3
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     '.fem_cache.json')


def _geo(V, g=None, k=None):
    import cores
    w = cores.winding(V, None, g, k)
    M = w['M']
    leg = M['d_centre'] / 2.0
    G = dict(leg=leg, win_r=M['r_win_out'] - leg,
             out_w=M['W'] / 2.0 - M['r_win_out'], hwin=M['win_h'] / 2.0,
             yoke=(M['H'] - M['win_h']) / 2.0, tube=M['tube_od'] / 2.0 - leg)
    kk, t, ka = w['k'], w['t_tape'], w['k_ax']
    dp, ds = w['d_pri'], w['d_sec']
    y0 = -w['wind_w'] / 2.0
    B = {'P': [], 'S2': [], 'S3': []}
    for li, n in enumerate(w['rows_A']):
        x = G['tube'] + (dp * kk + t) * li + dp * kk / 2.0
        for q in range(n):
            B['P'].append((x, y0 + w['yA'][0] + w['w_A'] * (q + 0.5) / n))
    for li, row in enumerate(w['smap']):
        x = G['tube'] + (ds * kk + t) * li + ds * kk / 2.0
        for c, who in enumerate(row):
            B['S2' if who == 'NS2' else 'S3'].append(
                (x, y0 + w['yS'][0] + ds * ka * (c + 0.5)))
    rad = {'P': w['d_litz'] / 2.0, 'S2': ds / 2.0, 'S3': ds / 2.0}
    return w, G, B, rad


def _build(G, B, rad, kind, gap):
    LEG, WR, OW, HW, YK = G['leg'], G['win_r'], G['out_w'], G['hwin'], G['yoke']
    top = HW + YK
    xs = F.axis([(0, (LEG - 0.6) * MM, 0.5 * MM),
                 ((LEG - 0.6) * MM, LEG * MM, 0.1 * MM),
                 (LEG * MM, (LEG + 1.2) * MM, 0.1 * MM),
                 ((LEG + 1.2) * MM, (LEG + WR) * MM, 0.06 * MM),
                 ((LEG + WR) * MM, (LEG + WR + OW) * MM, 0.5 * MM),
                 ((LEG + WR + OW) * MM, (LEG + WR + OW + 12) * MM, 1.0 * MM)])
    g2 = gap / 2.0
    ys = F.axis([(-(top + 12) * MM, -top * MM, 1.0 * MM),
                 (-top * MM, -HW * MM, 0.5 * MM),
                 (-HW * MM, -g2 * MM, 0.08 * MM), (-g2 * MM, g2 * MM, 0.05 * MM),
                 (g2 * MM, HW * MM, 0.08 * MM), (HW * MM, top * MM, 0.5 * MM),
                 (top * MM, (top + 12) * MM, 1.0 * MM)])

    def cell(xc, yc):
        x, y = xc / MM, yc / MM
        legc = x <= LEG and g2 <= abs(y) <= top
        if kind == 'core':
            yoke = HW <= abs(y) <= top and x <= LEG + WR + OW
            outer = LEG + WR <= x <= LEG + WR + OW and abs(y) <= top
            if legc or yoke or outer:
                return dict(mur=MU_R)
        elif legc:
            return dict(mur=MU_R)
        return {}
    Mo = F.Model(xs, ys, cell, 1.0 / RHO_CU,
                 dirichlet=('xmin', 'xmax', 'ymin', 'ymax'))
    X, Y = Mo.x / MM, Mo.y / MM
    nx, ny = len(X) - 1, len(Y) - 1
    sub = 4
    Mo.src = {}
    for grp, pts in B.items():
        r = rad[grp]
        frac = np.zeros((nx, ny))
        for bx, by in pts:
            bx = bx + LEG
            i0 = max(np.searchsorted(X, bx - r) - 1, 0)
            i1 = min(np.searchsorted(X, bx + r) + 1, nx)
            j0 = max(np.searchsorted(Y, by - r) - 1, 0)
            j1 = min(np.searchsorted(Y, by + r) + 1, ny)
            for a in range(sub):
                for b in range(sub):
                    xx = X[i0:i1, None] + (a + 0.5) / sub * np.diff(X)[i0:i1, None]
                    yy = Y[None, j0:j1] + (b + 0.5) / sub * np.diff(Y)[None, j0:j1]
                    frac[i0:i1, j0:j1] += ((xx - bx) ** 2 + (yy - by) ** 2
                                           <= r * r) / (sub * sub)
        Mo.src[grp] = frac
    Mo.node_src = {kk: Mo._to_nodes(f * Mo.cellA) for kk, f in Mo.src.items()}
    Mo.src_area = {kk: float((f * Mo.cellA).sum()) for kk, f in Mo.src.items()}
    return Mo


def _weights(Mo, G, kind, yoke):
    """per-cell turn length [m] of this kind of section at the cell's radius."""
    import cores
    LEG = G['leg']
    xc = 0.5 * (Mo.x[:-1] + Mo.x[1:]) / MM
    w = np.zeros(len(xc))
    for i, x in enumerate(xc):
        if x < LEG:
            w[i] = math.pi * LEG if kind == 'core' else 0.0
            continue
        l, yk, o = cores.zones(cores.CHOSEN, x)
        w[i] = (l + yoke * yk) if kind == 'core' else (o + (1 - yoke) * yk)
    return (w * MM)[:, None] * np.ones((1, len(Mo.y) - 1))


def _key(*parts):
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str)
                        .encode()).hexdigest()


def _cache_get(k):
    try:
        with open(CACHE) as f:
            return json.load(f).get(k)
    except (OSError, ValueError):
        return None


def _cache_put(k, v):
    try:
        with open(CACHE) as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    d[k] = v
    with open(CACHE, 'w') as f:
        json.dump(d, f)


def _geo_key(V, g, k):
    w, G, B, rad = _geo(V, g, k)
    return [G, B, rad], (w, G, B, rad)


def inductance(V, currents, g=None, k=None, gap=None, yoke=None):
    """[H] for the given group ampere-turns ('P', 'S2', 'S3', per 1 A of
    turn current times the turns): 2 x the stored energy, both kinds of
    section, each cell weighted with its length of turn."""
    import cores
    yoke = cores.YOKE_SHARE if yoke is None else yoke
    gap = gap_len(V) if gap is None else gap
    gk, (w, G, B, rad) = _geo_key(V, g, k)
    key = _key('L', gk, currents, gap, yoke, MU_R)
    hit = _cache_get(key)
    if hit is not None:
        return hit
    E = 0.0
    for kind in ('core', 'end'):
        Mo = _build(G, B, rad, kind, gap)
        a, _ = Mo.solve(2 * math.pi, currents)
        bx, by = Mo.cell_B(a)
        E += float((0.5 * Mo.nu * (np.abs(bx) ** 2 + np.abs(by) ** 2)
                    * Mo.cellA * _weights(Mo, G, kind, yoke)).sum())
    _cache_put(key, 2 * E)
    return 2 * E


def estimate(V, g=None, k=None, only=None, yoke=None, gap=None):
    """L_short [uH] referred to NP1: NS2 and NS3 both shorted (only=None,
    the specification's test) or one of them alone (only='NS2' / 'NS3',
    what each half of the centre tap sees)."""
    Np = float(V['Np'])
    if only is None:
        cur = {'P': Np, 'S2': -Np / 2.0, 'S3': -Np / 2.0}
    else:
        cur = {'P': Np, 'S2' if only == 'NS2' else 'S3': -Np}
    return 1e6 * inductance(V, cur, g, k, gap, yoke)


def gap_len(V):
    """[mm] the centre-leg gap that gives L_open (NP1 alone) = V['Lopen']:
    the field solution, fringing included, of the slab model - the vendor
    grinds to A_L, not to this length."""
    gk, _ = _geo_key(V, None, None)
    import cores
    key = _key('gap', gk, V['Lopen'], cores.YOKE_SHARE, MU_R)
    hit = _cache_get(key)
    if hit is not None:
        return hit
    lo, hi = 0.3, 4.0
    for _ in range(14):
        m = 0.5 * (lo + hi)
        if 1e6 * inductance(V, {'P': float(V['Np'])}, gap=m) > V['Lopen']:
            lo = m
        else:
            hi = m
    g = 0.5 * (lo + hi)
    _cache_put(key, g)
    return g


def proximity(V, f_khz, yoke=None):
    """Strand eddy loss [W] of NP1 and of NS2 + NS3 at f, first order: the
    line-cycle rms primary current as a sine, the secondaries both carrying
    their share (the leakage test's field), plus the magnetising current in
    quadrature (its field, the gap's fringing among it), each strand losing
    pi omega^2 sigma d_s^4 B^2 / 128 per metre at peak B; and the largest rms
    B in each section."""
    import cores
    yoke = cores.YOKE_SHARE if yoke is None else yoke
    gap = gap_len(V)
    gk, (w, G, B, rad) = _geo_key(V, None, None)
    key = _key('prox2', gk, f_khz, V['Iprilc'], V['Isateq'], gap, yoke, MU_R)
    hit = _cache_get(key)
    if hit is not None:
        return hit
    Np = float(V['Np'])
    ipk = math.sqrt(2) * V['Iprilc']
    cur = {'P': Np * ipk, 'S2': -Np / 2.0 * ipk, 'S3': -Np / 2.0 * ipk}
    #  the magnetising current, NP1 alone: a triangle of peak i_mu,pk, rms
    #  i_mu,pk / sqrt(3), taken as a sine of that rms in quadrature with the
    #  load current - its field (the gap's fringing among it) adds in B^2
    impk = math.sqrt(2) * V['Isateq'] / math.sqrt(3)
    cur_m = {'P': Np * impk}
    om = 2 * math.pi * f_khz * 1e3
    ds = cores.D_STRAND * MM
    nstr = {'P': w['n_strand'], 'S2': w['n_strand_s'], 'S3': w['n_strand_s']}
    out = {'P_pri': 0.0, 'P_sec': 0.0, 'B_pri': 0.0, 'B_sec': 0.0}
    for kind in ('core', 'end'):
        Mo = _build(G, B, rad, kind, gap)
        a, _ = Mo.solve(2 * math.pi, cur)
        bx, by = Mo.cell_B(a)
        B2 = np.abs(bx) ** 2 + np.abs(by) ** 2
        am, _ = Mo.solve(2 * math.pi, cur_m)
        mx, my = Mo.cell_B(am)
        B2 = B2 + np.abs(mx) ** 2 + np.abs(my) ** 2
        wt = _weights(Mo, G, kind, yoke)
        for grp in ('P', 'S2', 'S3'):
            dens = nstr[grp] / (math.pi * (rad[grp] * MM) ** 2)
            p = float((Mo.src[grp] * Mo.cellA * wt * dens * math.pi * om ** 2
                       / RHO_CU * ds ** 4 / 128.0 * B2).sum())
            bmax = float(np.sqrt(B2[Mo.src[grp] > 0.5].max() / 2.0)) \
                if np.any(Mo.src[grp] > 0.5) else 0.0
            if grp == 'P':
                out['P_pri'] += p
                out['B_pri'] = max(out['B_pri'], bmax)
            else:
                out['P_sec'] += p
                out['B_sec'] = max(out['B_sec'], bmax)
    _cache_put(key, out)
    return out


def dc_loss(V):
    """I^2 R [W] of NP1 and both secondaries, copper at 100 C, every turn at
    its own radius (2 pi r)."""
    import cores
    w, G, B, rad = _geo(V)
    a_s = math.pi * (cores.D_STRAND * MM) ** 2 / 4.0
    rp = sum(RHO_CU * 2 * math.pi * (G['leg'] + x) * MM for x, _ in B['P']) \
        / (w['n_strand'] * a_s)
    r2 = sum(RHO_CU * 2 * math.pi * (G['leg'] + x) * MM for x, _ in B['S2']) \
        / (w['n_strand_s'] * a_s)
    r3 = sum(RHO_CU * 2 * math.pi * (G['leg'] + x) * MM for x, _ in B['S3']) \
        / (w['n_strand_s'] * a_s)
    return dict(R_p=rp, R_2=r2, R_3=r3,
                P=V['Iprilc'] ** 2 * rp + V['Idio'] ** 2 * (r2 + r3))


def self_test():
    """Two closed forms through fem2d: a side-by-side pair of blocks filling
    the depth of an ungapped window of high permeability (the 1-D formula),
    in a slab section of unit weight."""
    a, b, h = 10.0, 30.0, 1.0
    xs = F.axis([(0, a * MM, 0.1 * MM), (a * MM, (a + 3) * MM, 0.5 * MM)])
    ys = F.axis([(0, b * MM, 0.1 * MM), (b * MM, (b + 3) * MM, 0.5 * MM)])

    def cell(xc, yc):
        return dict(mur=1e5) if (xc / MM > a or yc / MM > b) else {}
    Mo = F.Model(xs, ys, cell, 1.0 / RHO_CU, dirichlet=('xmax', 'ymax'))
    X, Y = Mo.x / MM, Mo.y / MM
    xc = 0.5 * (X[:-1] + X[1:])[:, None]
    yc = 0.5 * (Y[None, :-1] + Y[None, 1:])
    Mo.src = {'A': ((xc < a) & (yc < 8.0)).astype(float),
              'B': ((xc < a) & (yc > 12.0) & (yc < 20.0)).astype(float)}
    Mo.node_src = {kk: Mo._to_nodes(f * Mo.cellA) for kk, f in Mo.src.items()}
    Mo.src_area = {kk: float((f * Mo.cellA).sum()) for kk, f in Mo.src.items()}
    aa, _ = Mo.solve(2 * math.pi, {'A': 15.0, 'B': -15.0})
    L = 2 * Mo.energy(aa) * h
    want = F.MU0 * 225 * (8 / 3.0 + 4 + 8 / 3.0) * MM / (a * MM)
    return abs(L / want - 1)


def report(V=None):
    import an_pdf
    import cores
    V = an_pdf.V if V is None else V
    w = cores.winding(V)
    out = ['fem2d against the 1-D closed form: %.1e' % self_test(),
           '%s, NP1 %d T, partition %.2f mm, secondary layers %s'
           % (w['name'], w['Np'], w['sep'], list(w['order']))]
    gl = gap_len(V)
    out.append('  gap for L_open %.1f uH: %.3f mm (no fringing: %.3f mm)'
               % (V['Lopen'], gl, cores.gap(V, cores.CORES[w['name']]['Ae'])))
    for y in (0.0, cores.YOKE_SHARE, 1.0):
        out.append('  yoke share %.1f: L_short %.2f uH, NS2 alone %.2f, NS3 '
                   'alone %.2f' % (y, estimate(V, yoke=y),
                                   estimate(V, only='NS2', yoke=y),
                                   estimate(V, only='NS3', yoke=y)))
    out.append('  wound tight (k 1.0): %.2f uH' % estimate(V, k=1.0))
    for d in (0.5, 1.0):
        out.append('  partition %.2f mm: %.2f uH'
                   % (w['sep'] - d, estimate(V, g=w['sep'] - d)))
    dc = dc_loss(V)
    out.append('  dc: R NP1 %.2f mOhm, NS2 %.3f, NS3 %.3f mOhm; %.2f W'
               % (dc['R_p'] * 1e3, dc['R_2'] * 1e3, dc['R_3'] * 1e3, dc['P']))
    for f in (V['fswA'], V['fr']):
        pr = proximity(V, f)
        out.append('  strand eddy loss at %.0f kHz: NP1 %.2f W, NS2+NS3 %.2f W;'
                   ' B up to %.1f / %.1f mT rms'
                   % (f, pr['P_pri'], pr['P_sec'], 1e3 * pr['B_pri'],
                      1e3 * pr['B_sec']))
    return '\n'.join(out)


if __name__ == '__main__':
    print(report())
