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

    upper   the whole mean turn l_N (datasheet) sees the in-core field
    lower   only the part of the turn inside the core's depth does; the
            part outside, with no return path, is counted as nothing

Neither is a measurement.  The solver is checked against the two cases the
one-dimensional formula gets exactly (concentric and side-by-side windings
that fill the window); self_test() runs both.

It also reads the DIRECTION of the field on the secondary: a side-by-side
layout crosses the secondary section with a RADIAL field, which is normal to
the face of a foil.  Foil is a conductor for a field along its face; across
its face the eddy currents run over the whole foil width.  The ratio is
reported, not converted to a loss (that needs a field solver with the foil
in it).

    python leakage.py            the chosen core, and the three-unit build
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


def blocks_of(V, name=None):
    """The window and the winding blocks of cores.winding(), in metres."""
    import cores
    w = cores.winding(V, name)
    M = w['M']
    a = M['r_win_out'] - M['d_centre'] / 2.0         # across the window
    b = M['win_h']                                    # along the axis
    x0 = M['tube_od'] / 2.0 - M['d_centre'] / 2.0    # top of the tube
    fl = (b - M['wind_w']) / 2.0                      # flange, each end
    y1 = fl + w['margin_p']
    s2 = b - fl - w['margin_s']
    top_s = x0 + 2 * V['Ns'] * w['n_foil'] * (w['t_foil'] + cores.T_FOIL_INS)
    mm = 1e-3
    pri = (x0 * mm, (x0 + w['build_p']) * mm, y1 * mm,
           (y1 + w['w_pri']) * mm, float(V['Np']))
    sec = (x0 * mm, top_s * mm, (s2 - w['w_foil']) * mm, s2 * mm,
           -float(V['Np']))
    return w, a * mm, b * mm, [pri, sec]


def estimate(V, name=None):
    import cores
    name = name or cores.CHOSEN
    w, a, b, bl = blocks_of(V, name)
    C, M = cores.CORES[name], w['M']
    per_m = 2.0 * energy(a, b, bl)                   # H/m, at 1 A in NP1
    l_n = C['lN'] * 1e-3
    #  share of the turn inside the core's depth, on both sides
    r_mean = (M['tube_od'] / 2.0 + w['build_p'] / 2.0) * 1e-3
    inside = min(1.0, 2 * M['plan_d'] * 1e-3 / (2 * pi * r_mean))
    pri, sec = bl
    xs = [sec[0] + f * (sec[1] - sec[0]) for f in (0.2, 0.5, 0.8)]
    ys = [sec[2] + f * (sec[3] - sec[2]) for f in (0.1, 0.3, 0.5, 0.7, 0.9)]
    across = along = 0.0
    for x in xs:
        for y in ys:
            bx, by = field(a, b, bl, x, y)
            across += bx * bx
            along += by * by
    n = len(xs) * len(ys)
    return dict(name=name, Np=V['Np'], sep=w['gap'],
                upper=per_m * l_n * 1e6, lower=per_m * l_n * inside * 1e6,
                inside=inside, want=V['Lshort'],
                b_across=(across / n) ** 0.5 * 1e3,
                b_along=(along / n) ** 0.5 * 1e3)


def self_test():
    """The two cases the one-dimensional formula gets exactly."""
    mm = 1e-3
    a, b = 10 * mm, 30 * mm
    conc = energy(a, b, [(0, 3 * mm, 0, b, 15.0), (5 * mm, 8 * mm, 0, b, -15.0)])
    want = MU0 * 225 * (2 + 6 / 3.0) * mm / b / 2
    side = energy(a, b, [(0, a, 0, 8 * mm, 15.0), (0, a, 12 * mm, 20 * mm, -15.0)])
    want2 = MU0 * 225 * (4 + 16 / 3.0) * mm / a / 2
    return abs(conc / want - 1), abs(side / want2 - 1)


def report(V=None):
    import an_pdf
    if V is None:
        V = an_pdf.V
    e1, e2 = self_test()
    out = ['solver against the 1-D formula: concentric %.1e, side-by-side '
           '%.1e (relative error)' % (e1, e2)]
    runs = [(dict(V), None, 1)]
    v3 = dict(V)
    v3['Np'], v3['nser'] = V['Np'] // 3, 3
    runs.append((v3, 'PQ 40/40', 3))
    for v, name, nx in runs:
        r = estimate(v, name)
        out.append('%s x%d, Np %d per unit, separation %.2f mm' %
                   (r['name'], nx, r['Np'], r['sep']))
        out.append('  L_short estimate %.1f .. %.1f uH  (asked %.1f uH; '
                   '%.0f %% of the turn inside the core)'
                   % (nx * r['lower'], nx * r['upper'], V['Lshort'],
                      100 * r['inside']))
        out.append('  field on the secondary, per A in NP1: %.2f mT across '
                   'the foil face, %.2f mT along it'
                   % (r['b_across'], r['b_along']))
    return '\n'.join(out)


if __name__ == '__main__':
    print(report())
