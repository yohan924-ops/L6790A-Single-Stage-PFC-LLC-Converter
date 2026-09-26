# -*- coding: utf-8 -*-
"""Can the drawn winding give the leakage the tank asks for?  A diagnostic.

Written 2026-09-25 (round 65) when the user asked for the transformer example
to be checked again: nothing in the chain had ever computed the leakage of
the side-by-side layout that cores.winding() draws.  The specification asked
L_short = L_r and the note said the separation "sets" it, but no number tied
the two together.

The estimate is the field of the WINDOW CROSS-SECTION, solved exactly for a
rectangle bounded by infinitely permeable core (Roth's method: a double
cosine series, Neumann walls).  The windings are rectangular blocks of
uniform current density at the positions cores.winding() lays out, with
equal and opposite ampere-turns, the secondary taken as NS2 and NS3 both
shorted (the specification's leakage test).  The energy per metre of turn
times the mean turn length gives L_short referred to NP1.

The part of each turn inside the core's depth sees that field.  The part
outside has no outer legs and no yokes, only the centre leg under it; it is
solved as the same blocks in free space over an infinitely permeable plane
(the centre leg), by images and a sum over filaments.  Per metre it comes to
about half the in-core value, and the two are weighted by the share of the
mean turn l_N each covers.  Neither is a measurement; both solvers are
checked against closed forms (self_test: the 1-D formula for windings that
fill the window, and a pair of conductors in free space).

cores.winding() draws a section winding: NP1 in triple-insulated Litz in
one section, NS2 and NS3 in the other, the two sections touching.  This
module says what L_short that gives, how it moves with the looseness of
the winding and with any space between the sections, what each half of
the centre tap sees, and what the leakage field costs in the Litz.

    python leakage.py            L_short of the chosen core's winding, what
                                 moves it, each half of the centre tap on its
                                 own, and the losses the field adds
"""
from math import pi

import numpy as np

MU0 = 4e-7 * pi


def _int_cos(m, x1, x2, a):
    if m == 0:
        return x2 - x1
    k = m * pi / a
    return (np.sin(k * x2) - np.sin(k * x1)) / k


def _coeffs(a, b, blocks, M, N):
    """cosine-series coefficients of A for blocks (x1, x2, y1, y2, NI)"""
    m = np.arange(M)[:, None]
    n = np.arange(N)[None, :]
    S = np.zeros((M, N))
    for x1, x2, y1, y2, NI in blocks:
        J = NI / ((x2 - x1) * (y2 - y1))
        ix = np.array([_int_cos(i, x1, x2, a) for i in range(M)])[:, None]
        iy = np.array([_int_cos(j, y1, y2, b) for j in range(N)])[None, :]
        S += J * ix * iy
    nrm = a * b / (np.where(m == 0, 1, 2) * np.where(n == 0, 1, 2))
    k2 = (m * pi / a) ** 2 + (n * pi / b) ** 2
    k2[0, 0] = np.inf                        # net current is zero
    return S, nrm, k2, m, n


def energy(a, b, blocks, M=400, N=800):
    """Stored energy per metre [J/m] in an a x b window (SI units)."""
    S, nrm, k2, _, _ = _coeffs(a, b, blocks, M, N)
    return 0.5 * MU0 * float(np.sum(S ** 2 / nrm / k2))


def field(a, b, blocks, x, y, M=200, N=600):
    """(B across the window, B along it) [T] at (x, y) - x from the centre
    leg's face, y along the coil axis."""
    S, nrm, k2, m, n = _coeffs(a, b, blocks, M, N)
    C = MU0 * S / nrm / k2
    km, kn = m * pi / a, n * pi / b
    bx = float(np.sum(C * np.cos(km * x) * (-kn * np.sin(kn * y))))
    by = float(np.sum(C * km * np.sin(km * x) * np.cos(kn * y)))
    return bx, by


def energy_open(blocks, n=20):
    """Energy per metre [J/m] of blocks over an infinitely permeable plane
    at x = 0 (the centre leg), in free space: images of the same sign, a
    sum over n x n filaments per block, a filament's own term from the
    geometric mean distance of its cell.  Net current must be zero."""
    X, Y, I, S = [], [], [], []
    for x1, x2, y1, y2, NI in blocks:
        dx, dy = (x2 - x1) / n, (y2 - y1) / n
        gx, gy = np.meshgrid(x1 + dx * (np.arange(n) + 0.5),
                             y1 + dy * (np.arange(n) + 0.5))
        X.extend(gx.ravel())
        Y.extend(gy.ravel())
        I.extend([NI / n / n] * n * n)
        S.extend([0.2235 * (dx + dy)] * n * n)
    X, Y, I, S = (np.array(v) for v in (X, Y, I, S))
    X, Y = np.concatenate([X, -X]), np.concatenate([Y, Y])
    I, S = np.concatenate([I, I]), np.concatenate([S, S])
    d = np.hypot(X[:, None] - X[None, :], Y[:, None] - Y[None, :])
    np.fill_diagonal(d, 1.0)
    L = -MU0 / (2 * pi) * np.log(d)
    np.fill_diagonal(L, -MU0 / (2 * pi) * np.log(S))
    return 0.25 * float(I @ L @ I)           # half of the space, half of LI2


def blocks_of(V, name=None, g=0.0, only=None, turned=True, k=None,
              order=None):
    """The window and the winding blocks of cores.winding(), in metres.

    only=None: NS2 and NS3 both shorted, the secondary group one block (the
    specification's test).  only='NS2' or 'NS3': that winding alone carries
    the secondary ampere-turns, at its bundle positions (one half of the
    switching period in the centre-tapped rectifier)."""
    import cores
    w = cores.winding(V, name, g, k, order)
    M = w['M']
    a = M['r_win_out'] - M['d_centre'] / 2.0         # across the window
    b = M['win_h']                                    # along the axis
    x0 = M['tube_od'] / 2.0 - M['d_centre'] / 2.0    # top of the tube
    fl = (b - w['wind_w']) / 2.0                      # flange, each end
    mm = 1e-3
    bl = [(x0 * mm, (x0 + w['h_A']) * mm, (fl + w['yA'][0]) * mm,
           (fl + w['yA'][1]) * mm, float(w['Np']))]
    y0 = fl + w['yS'][0]
    if only is None:
        bl.append((x0 * mm, (x0 + w['h_S']) * mm, y0 * mm,
                   (y0 + w['w_S']) * mm, -float(w['Np'])))
    else:
        pos = [(k, c) for k, row in enumerate(w['smap'])
               for c, who in enumerate(row) if who == only]
        pc = w['d_sec'] * w['k']                     # pitch along the layer
        pk = pc + w['t_tape']                       # layer pitch, tape in
        for q, c in pos:
            bl.append(((x0 + q * pk) * mm,
                       (x0 + q * pk + w['d_sec']) * mm,
                       (y0 + c * pc) * mm,
                       (y0 + c * pc + w['d_sec']) * mm,
                       -float(w['Np']) / len(pos)))
    return w, a * mm, b * mm, bl


def estimate(V, name=None, g=0.0, only=None, turned=True, k=None,
             order=None):
    """L_short [uH] referred to NP1, and its two parts.  k: the winding
    pitch over the bundle (cores.K_WIND if None; 1.0 = packed tight); g a
    space between the two sections (0: they touch, as designed)."""
    import cores
    name = name or cores.CHOSEN
    w, a, b, bl = blocks_of(V, name, g, only, turned, k, order)
    ln_mm, inside = cores.turn(name)
    l_n = ln_mm * 1e-3
    l_in = 2.0 * energy(a, b, bl, M=200, N=500)       # H/m at 1 A in NP1
    l_out = 2.0 * energy_open(bl)
    L = (l_in * inside + l_out * (1 - inside)) * l_n * 1e6
    return dict(name=name, w=w, L=L, inside=inside, out_ratio=l_out / l_in,
                L_in_only=l_in * l_n * 1e6)


def potential(a, b, blocks, x, y, M=200, N=600):
    """A_z [Wb/m] at (x, y) in the window - the flux linkage per metre of a
    conductor there; differences between two places are what drives current
    around two conductors put in parallel."""
    S, nrm, k2, m, n = _coeffs(a, b, blocks, M, N)
    C = MU0 * S / nrm / k2
    return float(np.sum(C * np.cos(m * pi / a * x) * np.cos(n * pi / b * y)))


def _centres(w):
    """(kind, x, y, strands) of every bundle, mm, window coordinates."""
    M, k, t = w['M'], w['k'], w['t_tape']
    x0 = M['tube_od'] / 2.0 - M['d_centre'] / 2.0
    fl = (M['win_h'] - w['wind_w']) / 2.0
    pa, ps = w['d_pri'] * k, w['d_sec'] * k
    out = []
    for li, n in enumerate(w['rows_A']):
        for q in range(n):                  # a short layer is spread
            out.append(('P', x0 + (pa + t) * li + pa / 2.0,
                        fl + w['yA'][0] + w['w_A'] * (q + 0.5) / n,
                        w['n_strand']))
    for li, row in enumerate(w['smap']):
        for c, who in enumerate(row):
            out.append(('S', x0 + (ps + t) * li + ps / 2.0,
                        fl + w['yS'][0] + ps * (c + 0.5), w['n_strand_s']))
    return out


def proximity(V, f_khz, name=None):
    """Eddy loss [W] in the Litz strands from the leakage field - the term
    the dc resistance leaves out (round 68 audit).

    A strand of diameter d_s well under 2 delta in a field of rms B loses
    pi omega^2 sigma d_s^4 B^2 / 64 per metre.  B is the window field of
    the drawn layout (both secondaries shorted) at each bundle's centre,
    for the line-cycle rms primary current; the part of the turn outside
    the core is taken at the in-core B^2 times the energy ratio out_ratio.
    A first-order estimate for comparing layouts and strands, not a loss
    budget: the tank current is not a sine at f and the field outside the
    core is not solved point by point."""
    import cores
    name = name or cores.CHOSEN
    w, a, b, bl = blocks_of(V, name)
    ln, inside = cores.turn(name)
    ro = estimate(V, name)['out_ratio']
    om = 2 * pi * f_khz * 1e3
    sig = 1.0 / 2.26e-8                              # copper at 100 C
    d = cores.D_STRAND * 1e-3
    l_eff = (inside + (1 - inside) * ro) * ln * 1e-3
    pp = ps = bmax_p = bmax_s = 0.0
    for kind, x, y, n in _centres(w):
        bx, by = field(a, b, bl, x * 1e-3, y * 1e-3)
        B = np.hypot(bx, by) * V['Iprilc']
        p1 = pi * om ** 2 * sig * d ** 4 * B ** 2 / 64.0 * n * l_eff
        if kind == 'P':
            pp += p1
            bmax_p = max(bmax_p, B)
        else:
            ps += p1
            bmax_s = max(bmax_s, B)
    return dict(P_pri=pp, P_sec=ps, B_pri=bmax_p, B_sec=bmax_s)


def dc_loss(V, name=None):
    """I^2 R [W] of NP1 and both secondaries, copper at 100 C."""
    import cores
    w = cores.winding(V, name)
    ln = cores.turn(w['name'])[0] * 1e-3
    a_s = pi * (cores.D_STRAND * 1e-3) ** 2 / 4.0
    rp = 2.26e-8 * V['Np'] * ln / (w['n_strand'] * a_s)
    rs = 2.26e-8 * V['Ns'] * ln / (w['n_strand_s'] * w['sec_par'] * a_s)
    return V['Iprilc'] ** 2 * rp + 2 * V['Idio'] ** 2 * rs


def sharing(V, name=None):
    """Current driven around bundles put in parallel [A rms], first order.

    The bundles of a secondary turn lie side by side along the axis, and
    across the secondary section the leakage field runs radially and falls
    from the primary's side to the far flange: each bundle links a
    different flux.  Summed over the two turns of the winding, the
    difference, at the line-cycle rms primary current, drives a current
    around the loop two bundles make, limited by that loop's inductance
    (in the window the field runs across the depth h_w, outside the core
    the free-space pair).  Returned for NS2 conducting and NS3 idle - the
    worse of the two windings - as laid ('turned': the second turn lays the
    bundles in the reverse order, cores.winding() 'bmap') and as if not
    turned over ('not_turned'), with the current each bundle carries
    ('load')."""
    import cores
    from math import log
    name = name or cores.CHOSEN
    w = cores.winding(V, name)
    ln, inside = cores.turn(name)
    lin, lout = inside * ln * 1e-3, (1 - inside) * ln * 1e-3
    M, k, t = w['M'], w['k'], w['t_tape']
    hw = (M['r_win_out'] - M['d_centre'] / 2.0) * 1e-3
    x0 = M['tube_od'] / 2.0 - M['d_centre'] / 2.0
    fl = (M['win_h'] - w['wind_w']) / 2.0
    ps, ds = w['d_sec'] * k, w['d_sec']
    y0 = fl + w['yS'][0]
    per = w['sec_par']

    def loop(dy_mm):
        dy = dy_mm * 1e-3
        return V['Ns'] * (MU0 * dy / hw * lin + MU0 / pi
                          * (log(dy / (ds * 5e-4)) + 0.25) * lout)
    out = {}
    for turned in (True, False):
        worst = 0.0
        for who in ('NS2', 'NS3'):
            _, a, b, bl = blocks_of(V, name, only=who)
            lay = [q for q, row in enumerate(w['smap']) if row[0] == who]

            def A(l, c):
                return potential(a, b, bl, (x0 + (ps + t) * l + ps / 2.0)
                                 * 1e-3, (y0 + ps * (c + 0.5)) * 1e-3) * lin
            #  bundle c of the winding sits at place c in its first turn and
            #  at place per-1-c in its second when turned over
            L = [sum(A(l, (per - 1 - c) if (turned and j % 2) else c)
                     for j, l in enumerate(lay)) for c in range(per)]
            spread = max(L) - min(L)
            worst = max(worst, spread * V['Iprilc'] / loop((per - 1) * ps))
        out['turned' if turned else 'not_turned'] = worst
    out['load'] = V['Idio'] / w['sec_par']
    return out


def one_d(nA, nB, wA, wS, wB, g1, g2, h_w, l_n):
    """The note's estimate (Equation 'leak'), SI units in, henry out:
    the whole turn inside the core, windings filling the window depth."""
    return MU0 * l_n / h_w * (nA ** 2 * (wA / 3.0 + g1)
                              + (nA ** 2 - nA * nB + nB ** 2) * wS / 3.0
                              + nB ** 2 * (g2 + wB / 3.0))


def one_d_of(V, name=None, g=0.0):
    """one_d() for the layout cores.winding() draws (N_B = 0)."""
    import cores
    w = cores.winding(V, name, g)
    M, C = w['M'], cores.CORES[w['name']]
    mm = 1e-3
    return one_d(w['Np'], 0, w['w_A'] * mm, w['w_S'] * mm, 0.0,
                 w['sep'] * mm, 0.0,
                 (M['r_win_out'] - M['d_centre'] / 2.0) * mm, C['lN'] * mm)


def sweep(V, name=None, step=0.1, gmax=0.5):
    """[(space between the sections, L_short)] - what a space the winder
    leaves between the two sections would add."""
    out, g = [], 0.0
    while g <= gmax + 1e-9:
        out.append((g, estimate(V, name, g)['L']))
        g += step
    return out, gmax


def orders(V, name=None):
    """{order: (L NS2 alone, L NS3 alone)} for the ways the four secondary
    layers can be stacked - what each half of the centre tap sees."""
    import cores
    out = {}
    for o in (('NS2', 'NS2', 'NS3', 'NS3'), ('NS2', 'NS3', 'NS2', 'NS3'),
              ('NS2', 'NS3', 'NS3', 'NS2')):
        out[o] = tuple(estimate(V, name, only=h, order=o)['L']
                       for h in ('NS2', 'NS3'))
    return out


def self_test():
    """Closed forms: the 1-D formula for windings that fill the window
    (concentric, side by side), and two conductors in free space."""
    mm = 1e-3
    a, b = 10 * mm, 30 * mm
    conc = energy(a, b, [(0, 3 * mm, 0, b, 15.0), (5 * mm, 8 * mm, 0, b, -15.0)])
    want = MU0 * 225 * (2 + 6 / 3.0) * mm / b / 2
    side = energy(a, b, [(0, a, 0, 8 * mm, 15.0), (0, a, 12 * mm, 20 * mm, -15.0)])
    want2 = MU0 * 225 * (4 + 16 / 3.0) * mm / a / 2
    #  two 1 mm squares 20 mm apart, 500 mm over the plane: the pair and
    #  its image pair, L' = (mu0/pi)[ln(D/GMD) + 1/2 ln((2X+D)^2/(2X(2X+2D)))]
    s, D, X = 1 * mm, 20 * mm, 500 * mm
    pair = 2 * energy_open([(X, X + s, 0, s, 1.0),
                            (X + D, X + D + s, 0, s, -1.0)])
    want3 = MU0 / pi * (np.log(D / (0.44705 * s)) + 0.5 * np.log(
        (2 * X + D) ** 2 / (2 * X * (2 * X + 2 * D))))
    return abs(conc / want - 1), abs(side / want2 - 1), abs(pair / want3 - 1)


def report(V=None):
    import an_pdf
    import cores
    if V is None:
        V = an_pdf.V
    e1, e2, e3 = self_test()
    out = ['solvers against closed forms: concentric %.0e, side by side %.0e,'
           ' free-space pair %.0e (relative error)' % (e1, e2, e3)]
    r = estimate(V)
    w = r['w']
    out.append('%s, NP1 %d T (one TIW-Litz bundle), NS2/NS3 layers from '
               'the tube %s' % (r['name'], w['Np'], list(w['order'])))
    out.append('  outside the core per metre: %.2f of the in-core value; '
               '%.0f %% of the turn inside the core' %
               (r['out_ratio'], 100 * r['inside']))
    out.append('  L_short, both secondaries shorted: %.2f uH (asked %.1f uH); '
               'in-core-only figure %.2f uH' %
               (r['L'], V['Lshort'], r['L_in_only']))
    sw, gmax = sweep(V)
    out.append('  with a space between the sections: '
               + '  '.join('%.1f mm:%.2f' % t for t in sw))
    out.append('  packed tight (pitch 1.00 instead of %.2f): %.2f uH'
               % (w['k_wind'], estimate(V, k=1.0)['L']))
    for who in ('NS2', 'NS3'):
        h = estimate(V, only=who)
        out.append('  %s alone shorted: %.2f uH' % (who, h['L']))
    out.append('  copper, dc: %.2f W' % dc_loss(V))
    for f in (V['fswA'], V['fr']):
        pr = proximity(V, f)
        out.append('  strand eddy loss at %.0f kHz (first order): NP1 %.2f W, '
                   'NS2+NS3 %.2f W; B up to %.1f / %.1f mT rms'
                   % (f, pr['P_pri'], pr['P_sec'], 1e3 * pr['B_pri'],
                      1e3 * pr['B_sec']))
    for o, (h2, h3) in orders(V).items():
        out.append('  layers %s: NS2 alone %.2f, NS3 alone %.2f uH'
                   % ('-'.join(x[-1] for x in o), h2, h3))
    sh = sharing(V)
    out.append('  current around the %d bundles of a secondary turn: %.1f A '
               'rms as laid, %.1f A not turned over; each bundle carries '
               '%.2f A (first order)'
               % (w['sec_par'], sh['turned'], sh['not_turned'], sh['load']))
    return '\n'.join(out)


if __name__ == '__main__':
    print(report())
