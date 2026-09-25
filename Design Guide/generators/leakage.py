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

Round 65 found that the side-by-side foil layout leaked about 27 uH and
that its radial field crossed the foil.  The user chose (2026-09-25) to keep
the leakage integrated and make the secondary Litz; this module then
searched the layouts, and cores.winding() now draws the result: NP1 in
triple-insulated Litz, split around the secondary, the gaps free to trim
the leakage.

    python leakage.py            L_short against the gap on the chosen core,
                                 and each half of the centre tap on its own
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


def blocks_of(V, name=None, g=None, only=None, turned=True):
    """The window and the winding blocks of cores.winding(), in metres.

    only=None: NS2 and NS3 both shorted, the secondary group one block (the
    specification's test).  only='NS2' or 'NS3': that winding alone carries
    the secondary ampere-turns, at its bundle positions (one half of the
    switching period in the centre-tapped rectifier).  turned=False puts
    every layer of the group in the order of the first, as if it had not
    been turned over at the layer change."""
    import cores
    w = cores.winding(V, name, g)
    if not turned:
        w = dict(w, smap=[w['smap'][0]] * len(w['smap']))
    M = w['M']
    a = M['r_win_out'] - M['d_centre'] / 2.0         # across the window
    b = M['win_h']                                    # along the axis
    x0 = M['tube_od'] / 2.0 - M['d_centre'] / 2.0    # top of the tube
    fl = (b - M['wind_w']) / 2.0                      # flange, each end
    mm = 1e-3
    bl = [(x0 * mm, (x0 + w['h_A']) * mm, (fl + w['yA'][0]) * mm,
           (fl + w['yA'][1]) * mm, float(w['nA']))]
    if w['nB']:
        bl.append((x0 * mm, (x0 + w['h_B']) * mm, (fl + w['yB'][0]) * mm,
                   (fl + w['yB'][1]) * mm, float(w['nB'])))
    y0 = fl + w['yS'][0]
    if only is None:
        bl.append((x0 * mm, (x0 + w['h_S']) * mm, y0 * mm,
                   (y0 + w['w_S']) * mm, -float(w['Np'])))
    else:
        pos = [(k, c) for k, row in enumerate(w['smap'])
               for c, who in enumerate(row) if who == only]
        pk = w['d_sec'] + w.get('t_tape', 0.0)      # layer pitch, tape in
        for k, c in pos:
            bl.append(((x0 + k * pk) * mm,
                       (x0 + k * pk + w['d_sec']) * mm,
                       (y0 + c * w['d_sec']) * mm,
                       (y0 + (c + 1) * w['d_sec']) * mm,
                       -float(w['Np']) / len(pos)))
    return w, a * mm, b * mm, bl


def estimate(V, name=None, g=None, only=None, turned=True):
    """L_short [uH] referred to NP1, and its two parts."""
    import cores
    name = name or cores.CHOSEN
    w, a, b, bl = blocks_of(V, name, g, only, turned)
    C, M = cores.CORES[name], w['M']
    l_n = C['lN'] * 1e-3
    r_mean = (M['tube_od'] / 2.0 + max(w['h_A'], w['h_S']) / 2.0) * 1e-3
    inside = min(1.0, 2 * M['plan_d'] * 1e-3 / (2 * pi * r_mean))
    l_in = 2.0 * energy(a, b, bl, M=200, N=500)       # H/m at 1 A in NP1
    l_out = 2.0 * energy_open(bl)
    L = (l_in * inside + l_out * (1 - inside)) * l_n * 1e6
    return dict(name=name, w=w, L=L, inside=inside, out_ratio=l_out / l_in,
                L_in_only=l_in * l_n * 1e6)


def one_d(nA, nB, wA, wS, wB, g1, g2, h_w, l_n):
    """The note's estimate (Equation 'leak'), SI units in, henry out:
    the whole turn inside the core, windings filling the window depth."""
    return MU0 * l_n / h_w * (nA ** 2 * (wA / 3.0 + g1)
                              + (nA ** 2 - nA * nB + nB ** 2) * wS / 3.0
                              + nB ** 2 * (g2 + wB / 3.0))


def one_d_of(V, name=None, g=None):
    """one_d() for the layout cores.winding() draws."""
    import cores
    w = cores.winding(V, name, g)
    M, C = w['M'], cores.CORES[w['name']]
    mm = 1e-3
    return one_d(w['nA'], w['nB'], w['w_A'] * mm, w['w_S'] * mm,
                 w['w_B'] * mm, w['gap'] * mm, w['gap'] * mm,
                 (M['r_win_out'] - M['d_centre'] / 2.0) * mm, C['lN'] * mm)


def sweep(V, name=None, step=0.5):
    """[(gap, L_short)] from touching to the widest the bobbin allows."""
    import cores
    w0 = cores.winding(V, name, 0.0)
    gmax = w0['room'] / w0['n_gaps']
    out, g = [], 0.0
    while g <= gmax + 1e-9:
        out.append((g, estimate(V, name, g)['L']))
        g += step
    return out, gmax


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
    out.append('%s, NP1 %d + %d T (TIW-Litz), NS2/NS3 group %s' %
               (r['name'], w['nA'], w['nB'], w['smap']))
    out.append('  outside the core per metre: %.2f of the in-core value; '
               '%.0f %% of the turn inside the core' %
               (r['out_ratio'], 100 * r['inside']))
    sw, gmax = sweep(V)
    out.append('  L_short against each gap (both secondaries shorted), gaps '
               'up to %.2f mm:' % gmax)
    out.append('    ' + '  '.join('%.1f:%.2f' % t for t in sw))
    out.append('  at the nominal gap %.2f mm: %.2f uH (asked %.1f uH); '
               'in-core-only figure %.2f uH' %
               (w['gap'], r['L'], V['Lshort'], r['L_in_only']))
    for who in ('NS2', 'NS3'):
        h = estimate(V, only=who)
        out.append('  %s alone shorted: %.2f uH' % (who, h['L']))
    return '\n'.join(out)


if __name__ == '__main__':
    print(report())
