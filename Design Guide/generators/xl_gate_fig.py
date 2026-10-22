# -*- coding: utf-8 -*-
"""The gate-drive picture the workbooks carry next to Power Components' gate-drive rows
(2026-10-22, user: "add a simple gate driver schematic with its parts, so I know what is
what while looking at the workbook").

One bridge leg: a half-bridge gate driver (any part - no pin numbers), its bootstrap (R.boot, D.boot, C.boot) and the two switches, each
with R.on, the turn-off branch R.off + D.off and the optional C.gs.  The part names are the
row names of the workbook block (gate_xl.py) - no values are drawn, so one picture serves
all three books.  Drawn with the kit of figs_ref.an_gate_drive.

    python xl_gate_fig.py        -> Design Guide/figures/xl_gate_drive.png
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import figs_ref as F
import schem as S
import schemx as X
from schem import NAVY, GREY

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'figures', 'xl_gate_drive.png'))
GRN = '#1B7F3B'


def draw():
    fig = plt.figure(figsize=(9.0, 5.3))
    ax = F._ax(fig, [0.01, 0.02, 0.98, 0.96], -0.6, 26.4, 3.6, 22.6)
    YV, YB = 20.0, 21.6                      # V.drv rail, bus
    # ------------------------------------------------------------ the driver
    XD0, XD1 = 3.2, 8.4
    d = F._ic(ax, XD0, 8.8, XD1, 16.6, 'Gate driver',
              [('L', 13.2, '', 'IN.H'), ('L', 11.6, '', 'IN.L'),
               ('T', 4.8, '', 'VCC'), ('B', 6.8, '', 'GND'),
               ('R', 15.6, '', 'BOOT'), ('R', 14.2, '', 'HO'),
               ('R', 12.6, '', 'HS'), ('R', 10.6, '', 'LO')], ref=12.4)
    S.label(ax, (XD0 + XD1) / 2, 11.5, 'half bridge', size=8.6, color=GREY)
    S.label(ax, (XD0 + XD1) / 2, 10.0, '(t.DT: internal\ndead time, if any)', size=7.8, color=GREY)
    for y, t in ((13.2, 'HOUT'), (11.6, 'LOUT')):
        pin = d['IN.H'] if y == 13.2 else d['IN.L']
        S.wire(ax, [(0.0, y), pin])
        F._term(ax, 0.0, y)
        S.label(ax, 0.0, y + 0.5, t, size=8.6, ha='left', color=GREY)
    S.label(ax, 0.0, 14.3, 'from L6790A', size=8.6, ha='left', color=GREY)
    S.wire(ax, [d['VCC'], (4.8, YV)])
    S.dot(ax, 4.8, YV)
    S.wire(ax, [(-0.2, YV), (10.2, YV)])
    F._term(ax, -0.2, YV)
    S.label(ax, -0.2, YV + 0.5, 'V.drv', size=10.5, ha='left', weight='bold', color=GRN)

    # ------------------------------------------------------------ bootstrap
    XB, R = 10.2, 0.20
    ra, rb = S.res(ax, XB, 19.0, horiz=False)        # rail -> R.boot -> D.boot -> BOOT
    S.wire(ax, [(XB, YV), rb])
    da, db = S.diode(ax, XB, 17.15, horiz=False, flip=True)
    S.wire(ax, [ra, da])
    S.wire(ax, [db, (XB, 15.6)])
    S.label(ax, XB + 0.5, 19.0, 'R.boot', size=10, ha='left', color=GRN, weight='bold')
    S.label(ax, XB + 0.5, 17.15, 'D.boot', size=10, ha='left', color=GRN, weight='bold')
    S.wire(ax, [d['BOOT'], (XB, 15.6)])
    S.dot(ax, XB, 15.6)
    ca, cb = S.cap(ax, XB, 13.3, horiz=False)
    S.wire(ax, [(XB, 15.6), cb])
    S.wire(ax, [ca, (XB, 12.6)])
    S.dot(ax, XB, 12.6)
    S.label(ax, XB + 0.45, 13.25, 'C.boot', size=10, ha='left', color=GRN, weight='bold')

    # ------------------------------------------------------------ the switches
    XS = 21.6
    xg = XS - 1.4                                    # gate lead
    s1d, s1s = X.mosfet(ax, XS, 14.2, None, 'plain', h=1.8, gate=1.4, **X.MOS_PLAIN)
    s2d, s2s = X.mosfet(ax, XS, 8.6, None, 'plain', h=1.8, gate=1.4, **X.MOS_PLAIN)
    S.label(ax, XS + 1.1, 14.6, 'S1 high side', size=10, weight='bold', ha='left')
    S.label(ax, XS + 1.1, 9.0, 'S2 low side', size=10, weight='bold', ha='left')

    def net(yg, ys, xa):
        """R.on on the gate run, (R.off + D.off) above it, C.gs from the gate node to ys"""
        ra_, rb_ = S.res(ax, 14.6, yg)
        S.wire(ax, [(xa, yg), ra_])
        S.wire(ax, [rb_, (xg, yg)])
        S.label(ax, 14.6, yg - 0.62, 'R.on', size=10, color=GRN, weight='bold')
        x1, x2 = 12.6, 17.0
        yb = yg + 1.7
        for xx in (x1, x2):
            S.dot(ax, xx, yg)
            S.wire(ax, [(xx, yg), (xx, yb)])
        dA, dK = S.diode(ax, 13.7, yb, flip=True)        # cathode toward the driver
        S.wire(ax, [(x1, yb), dK])
        r3a, r3b = S.res(ax, 15.8, yb)
        S.wire(ax, [dA, r3a])
        S.wire(ax, [r3b, (x2, yb)])
        S.label(ax, 13.7, yb + 0.66, 'D.off (V.F)', size=9.6, color=GRN, weight='bold')
        S.label(ax, 15.8, yb + 0.66, 'R.off', size=9.6, color=GRN, weight='bold')
        xc = 18.8                                     # C.gs, optional
        S.dot(ax, xc, yg)
        c1, c2 = S.cap(ax, xc, (yg + ys) / 2, horiz=False, color=GREY)
        S.wire(ax, [(xc, yg), c2], color=GREY)
        S.wire(ax, [c1, (xc, ys)], color=GREY)
        S.dot(ax, xc, ys)
        S.label(ax, xc - 0.42, (yg + ys) / 2, 'C.gs\n(option)', size=8.8, ha='right', color=GREY)

    # high side: HVG crosses the C.boot lead with a hop
    S.wire(ax, [d['HO'], (XB - R, 14.2)])
    X.hop(ax, XB, 14.2, r=R)
    net(14.2, 12.6, XB + R)
    # low side
    S.wire(ax, [d['LO'], (11.4, 10.6), (11.4, 8.6)])
    net(8.6, 7.0, 11.4)
    # drains, midpoint, sources
    S.wire(ax, [s1d, (XS, YB)])
    YA = 11.4
    S.wire(ax, [s1s, (XS, YA)])
    S.wire(ax, [(XS, YA), s2d])
    S.dot(ax, XS, YA)
    S.wire(ax, [d['HS'], (XS, 12.6)])
    S.dot(ax, XS, 12.6)
    S.wire(ax, [(XS, YA), (24.6, YA)])
    F._term(ax, 24.6, YA)
    S.label(ax, 24.6, YA - 0.55, 'midpoint', size=9.4, color=GREY)
    YK = 7.0
    S.wire(ax, [s2s, (XS, 5.6)])
    S.dot(ax, XS, YK)
    S.wire(ax, [d['GND'], (6.8, YK), (XS, YK)])
    F._pgnd(ax, XS, 5.6)
    S.wire(ax, [(XS, YB), (24.6, YB)])
    F._term(ax, 24.6, YB)
    S.label(ax, 23.4, YB + 0.5, 'bus', size=9.4, color=GREY)
    for y, t in ((6.1, 'One output pin per side: R.off + D.off in parallel with R.on.'),
                 (5.3, 'Separate GON / GOFF pins: R.on on GON, R.off on GOFF, V.F = 0.'),
                 (4.5, 'Green names = the rows of Power Components "LLC Half Bridge Gate Driver Selection".')):
        S.label(ax, 0.0, y, t, size=8.8, ha='left', color=GREY)
    return fig


def main():
    fig = draw()
    fig.savefig(OUT, dpi=110, facecolor='white')
    print('written:', OUT)


if __name__ == '__main__':
    main()
