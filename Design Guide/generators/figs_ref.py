# -*- coding: utf-8 -*-
"""The figures that used to be cropped out of other vendors' notes.

Fifteen of the drawings in this document were screenshots from application
notes published by ON Semiconductor, Infineon and Toshiba.  They are good
teaching figures and they are cited, but they are somebody else's artwork
in a document that gets distributed, they are raster at whatever resolution
the crop happened to give, and every one of them is set in a different
typeface from the text around it.

So they are drawn here instead, with the kit in schemx.py - the same
MOSFET, the same windings and the same current highlight the eight-mode
panels use.  The teaching sequence is unchanged and the sources stay cited
in the captions as the source of the argument, not of the picture.

Two of them are not just redrawn but corrected.  The borrowed figures put
the capacitive/inductive boundary at the peak of the gain curve; the
boundary is where the input impedance phase crosses zero, which is a little
ABOVE the peak, so the borrowed version reports a band of hard switching as
inductive.  `l6790.zvs_edge` gives the boundary in closed form and both
figures are drawn from it.

Everything numeric comes from l6790.py.  Nothing in this file is a number
typed in from a picture.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

import schem as S
import schemx as X
from schem import NAVY, MAG, CYA, GRN, PUR, GREY, LT, YEL
from l6790 import M, zvs_edge, phase


# ----------------------------------------------------------------- helpers
#  Anything written over the drawing carries a white halo.  Without one a
#  callout laid across a curve or a wire is unreadable exactly where it
#  matters, and figcheck.py counts that as a fault.
HALO = [pe.withStroke(linewidth=3.6, foreground='white')]


def _call(ax, xy, xytext, t, color=MAG, size=10.5, ha='left', rad=None,
          **kw):
    ap = dict(arrowstyle='-|>', color=color, lw=1.4)
    if rad is not None:
        ap['connectionstyle'] = 'arc3,rad=%s' % rad
    return ax.annotate(t, xy=xy, xytext=xytext, fontsize=size, color=color,
                       ha=ha, arrowprops=ap, path_effects=HALO,
                       zorder=9, **kw)


def _ax(fig, rect, x0, x1, y0, y1):
    ax = fig.add_axes(rect)
    S.frame(ax, x0, x1, y0, y1)
    return ax


def _wave_ax(fig, rect, t0=0.0, t1=1.0, y0=-1.25, y1=1.25, label=None):
    """A bare trace axis: a zero line, no box, a name on the left."""
    ax = fig.add_axes(rect)
    ax.set_xlim(t0, t1)
    ax.set_ylim(y0, y1)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.axhline(0, color=GREY, lw=0.9, zorder=1)
    if label:
        ax.text(-0.012, 0.5, label, transform=ax.transAxes, ha='right',
                va='center', fontsize=10.5, color=NAVY)
    return ax


def _sq(t, duty=0.5, phase_=0.0):
    return np.where(((t + phase_) % 1.0) < duty, 1.0, 0.0)


def _diode_along(ax, a, b, s=0.17, color=NAVY, lw=2.2, z=4):
    """A diode ON the segment a->b, conducting in that direction.

    Built from the direction vector, not from a rotated marker.  The first
    version used matplotlib's rotatable triangle marker and every diode in
    every bridge came out pointing the wrong way - the sort of thing that
    makes a reader stop trusting the rest of the drawing.  The bar also has
    to sit AT the apex, not at the midpoint, or the triangle covers it and
    the symbol stops being a diode at all.
    """
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = b - a
    u = d / np.hypot(*d)                        # along, anode -> cathode
    v = np.array([-u[1], u[0]])                 # across
    m = a + d * 0.5
    tip, base = m + u * s, m - u * s
    ax.fill(*zip(base + v * s * 0.86, base - v * s * 0.86, tip),
            color=color, zorder=z)
    ax.plot([tip[0] + v[0] * s * 0.86, tip[0] - v[0] * s * 0.86],
            [tip[1] + v[1] * s * 0.86, tip[1] - v[1] * s * 0.86],
            color=color, lw=lw, zorder=z, solid_capstyle='butt')
    return tip, base


def _bridge(ax, xm, ym, w=1.55, h=1.35, names=('D$_1$', 'D$_3$',
                                               'D$_2$', 'D$_4$'),
            size=9.5):
    """A diode bridge as a diamond.  -> (ac_left, ac_right, plus, minus)

    Drawn as two columns it needs one of the ac leads to cross the other
    column to reach its node, and a crossing in a four-device figure is a
    crossing too many.  On the diamond every terminal is a corner.

    All four conduct TOWARDS the + corner: that is what a bridge is, and
    it is the one thing in this drawing a reader will check.
    """
    L, Rt, P, Mn = (xm - w, ym), (xm + w, ym), (xm, ym + h), (xm, ym - h)
    for a, b, nm, dx, dy in ((L, P, names[0], -0.48, 0.34),
                             (Rt, P, names[1], 0.48, 0.34),
                             (Mn, L, names[2], -0.48, -0.34),
                             (Mn, Rt, names[3], 0.48, -0.34)):
        S.wire(ax, [a, b])
        _diode_along(ax, a, b)
        mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
        S.label(ax, mx + dx, my + dy, nm, size=size, color=GREY)
    for pt in (L, Rt, P, Mn):
        S.dot(ax, *pt)
    return L, Rt, P, Mn


# ------------------------------------------------------------------ 1  R_ac
def an_rac(save, foot):
    """Why the rectifier and the load collapse into one resistor."""
    fig = plt.figure(figsize=(11.8, 5.6))

    ax = _ax(fig, [0.02, 0.30, 0.62, 0.66], -1.2, 14.6, -2.3, 4.6)
    # the tank, standing in as a current source
    S.acsrc(ax, 0.3, 1.5, None)
    S.label(ax, 0.3, 0.76, 'i$_{ac}$', size=11, color=MAG)
    S.wire(ax, [(0.3, 1.86), (0.3, 3.3), (2.5, 3.3)])
    S.wire(ax, [(0.3, 1.14), (0.3, -0.3), (2.5, -0.3)])
    S.label(ax, 1.45, 1.80, 'v$_{RI}$', size=11.5)
    S.label(ax, 1.45, 3.02, '+', size=12, color=GREY)
    S.label(ax, 1.45, -0.02, '$-$', size=12, color=GREY)

    #  The rectifier is the one this design uses - a centre tap - so the
    #  transformer is in the picture and the n^2 in R_ac has somewhere to
    #  come from.  A bridge would need one of its ac leads to cross the
    #  other, which is a crossing this figure does not have to spend.
    t = X.xfmr(ax, 3.7, 1.5, hp=3.6, hs=3.6, ct=True,
               gap=0.52, ls=('N$_s$', 'N$_s$'))
    S.wire(ax, [(2.5, 3.3), t['p_top']])
    S.wire(ax, [(2.5, -0.3), t['p_bot']])
    S.label(ax, 3.7, -1.05, 'n : 1', size=10.5, color=GREY)

    XJ = 9.3                       # where the two rectifiers join
    S.wire(ax, [t['s_top'], (6.9, 3.3)])
    #  A hop used to sit here, left over from a routing that put the tap's
    #  riser at XT.  The tap leaves on the far side now, so that bump was
    #  a crossing symbol over nothing at all.
    S.wire(ax, [t['s_bot'], (6.9, -0.3)])
    for y, nm, dy in ((3.3, 'D$_1$', 0.56), (-0.3, 'D$_2$', 0.56)):
        di, do = S.diode(ax, 7.6, y, None, s=0.30)
        S.wire(ax, [(6.9, y), di])
        S.wire(ax, [do, (XJ, y)])
        S.label(ax, 7.6, y + dy, nm, size=9.5, color=GREY)
    #  The two rectifiers join on a riser to the LEFT of the load, so the
    #  only crossing in the secondary is the tap hopping that riser.  Join
    #  them through the middle instead and the tap has nowhere to go.
    S.wire(ax, [(XJ, 3.3), (XJ, -1.4)])
    S.dot(ax, XJ, -0.3)
    S.wire(ax, [(XJ, -1.4), (12.5, -1.4)])
    S.wire(ax, [t['s_tap'], (XJ - 0.20, 1.5)])
    S.hop(ax, XJ, 1.5)
    S.wire(ax, [(XJ + 0.20, 1.5), (12.5, 1.5)])
    S.shunt(ax, 11.1, 1.5, -1.4, 'cap', 'C$_o$', frac=0.34)
    S.shunt(ax, 12.5, 1.5, -1.4, 'res', 'R$_o$', frac=0.52)
    S.label(ax, 13.4, 0.30, 'V$_O$', size=11.5, ha='left')
    S.label(ax, 13.4, -0.22, 'stiff', size=10, ha='left', color=GREY)



    ax2 = _ax(fig, [0.655, 0.34, 0.335, 0.56], -6.6, 3.6, -0.6, 4.6)
    S.wire(ax2, [(0.4, 3.6), (2.6, 3.6)])
    S.wire(ax2, [(0.4, 0.4), (2.6, 0.4)])
    S.shunt(ax2, 1.5, 3.6, 0.4, 'res', None, frac=0.46)
    S.label(ax2, 2.0, 2.0, 'R$_{ac}$', size=12, ha='left')
    S.label(ax2, 1.5, 4.15, 'one resistor', size=10.5, color=MAG)
    S.arrow(ax2, (-5.4, 2.0), (-2.6, 2.0), None, color=MAG)
    S.label(ax2, -4.0, 2.70, 'all of it becomes', size=10.5, color=MAG)

    # the two waveforms the argument rests on
    t = np.linspace(0, 2, 600)
    aw = _wave_ax(fig, [0.07, 0.115, 0.36, 0.145], 0, 2, -1.4, 1.4,
                  'i$_{ac}$')
    aw.plot(t, np.sin(np.pi * t), color=MAG, lw=2.0)
    aw.text(0.5, 1.13, 'a sine, because the tank filters everything else',
            transform=aw.transAxes, ha='center', va='bottom', fontsize=9.8,
            color=GREY)

    bw = _wave_ax(fig, [0.55, 0.115, 0.36, 0.145], 0, 2, -1.7, 1.7,
                  'v$_{RI}$')
    sq = np.where(np.sin(np.pi * t) >= 0, 1.0, -1.0)
    bw.plot(t, sq, color=NAVY, lw=2.0)
    bw.plot(t, 4.0 / np.pi * np.sin(np.pi * t), color=CYA, lw=1.8,
            ls=(0, (4, 2.4)))
    bw.text(0.5, 1.13, 'a square, because the output is stiff;  dashed is '
            'its fundamental, 4/$\\pi$ tall',
            transform=bw.transAxes, ha='center', va='bottom', fontsize=9.8,
            color=GREY)

    foot(fig, 'A sine of current against a square of voltage, in phase, is '
              'the same fundamental power as a resistor would take. That is '
              'the whole of the substitution - and it is why R_ac carries '
              'the 8/pi^2, and n^2 for the turns ratio.')
    save(fig, 'an_rac')


# ------------------------------------------------- 2  the integrated magnetic
def an_integrated(save, foot):
    """The same transformer drawn both ways."""
    fig = plt.figure(figsize=(11.6, 7.2))

    # ---- as wound: leakage on both sides of an ideal n_T : 1
    ax = _ax(fig, [0.04, 0.545, 0.92, 0.40], -0.6, 15.0, -0.7, 4.3)
    S.label(ax, 7.2, 4.05, 'as wound:  leakage on both sides', size=11,
            color=GREY)
    S.sqsrc(ax, 0.5, 1.8, None)
    S.label(ax, 0.5, 1.10, 'v$_{in}$', size=11)
    S.wire(ax, [(0.5, 2.18), (0.5, 3.4), (1.7, 3.4)])
    S.wire(ax, [(0.5, 1.42), (0.5, 0.1), (10.4, 0.1)])
    p, q = S.cap(ax, 2.2, 3.4, 'C$_r$', tdy=0.46)
    S.wire(ax, [(1.7, 3.4), p])
    c, d = S.ind(ax, 3.7, 3.4, 'L$_{lkp}$', s=0.95)
    S.wire(ax, [q, c])
    S.wire(ax, [d, (5.1, 3.4)])
    S.shunt(ax, 5.1, 3.4, 0.1, 'ind', None, frac=0.50)
    S.label(ax, 4.62, 1.75, 'L$_m$', size=11, ha='right')
    S.dot(ax, 5.1, 3.4)
    t = X.xfmr(ax, 7.5, 1.75, hp=3.3, hs=3.3, gap=0.52,
               lp=None, ls=None)
    S.wire(ax, [(5.1, 3.4), t['p_top']])
    S.wire(ax, [t['p_bot'], (t['p_bot'][0], 0.1)])
    S.label(ax, 7.5, -0.48, 'n$_T$ : 1', size=10.5, color=GREY)
    #  L_lks starts clear of the secondary's polarity dot.  At 8.6 its
    #  first turn sat on top of the dot, and a dot under a coil is the one
    #  thing a transformer symbol cannot afford to be unclear about.
    e, f = S.ind(ax, 9.3, 3.4, 'L$_{lks}$', s=0.95)
    S.wire(ax, [t['s_top'], e])
    S.wire(ax, [f, (10.4, 3.4)])
    S.wire(ax, [t['s_bot'], (t['s_bot'][0], 0.1)])
    S.wire(ax, [(10.4, 3.4), (12.6, 3.4)])
    S.wire(ax, [(10.4, 0.1), (12.6, 0.1)])
    S.shunt(ax, 11.3, 3.4, 0.1, 'cap', None, frac=0.22)
    S.shunt(ax, 12.6, 3.4, 0.1, 'res', 'R$_o$', frac=0.40)
    S.label(ax, 13.8, 1.75, 'V$_O$', size=11, ha='left')
    S.wire(ax, [(10.70, 3.20), (10.70, 0.30)], GREY, 1.0)
    S.label(ax, 10.52, 1.75, 'v$_{RI}$', size=10.5, color=GREY,
            ha='right')

    S.arrow(ax, (7.2, -0.95), (7.2, -1.9), None, color=MAG)

    # ---- referred: all of it on the primary
    ax2 = _ax(fig, [0.04, 0.085, 0.92, 0.40], -0.6, 15.0, -0.7, 4.3)
    S.label(ax2, 7.2, 4.05, 'referred to the primary:  one L$_r$, one L$_m$, '
            'one ideal 1 : M$_v$', size=11, color=GREY)
    S.sqsrc(ax2, 0.5, 1.8, None)
    S.label(ax2, 0.5, 1.10, 'v$_{in}^F$', size=11)
    S.wire(ax2, [(0.5, 2.18), (0.5, 3.4), (1.7, 3.4)])
    S.wire(ax2, [(0.5, 1.42), (0.5, 0.1), (9.9, 0.1)])
    p, q = S.cap(ax2, 2.2, 3.4, 'C$_r$', tdy=0.46)
    S.wire(ax2, [(1.7, 3.4), p])
    c, d = S.ind(ax2, 4.2, 3.4, 'L$_r$', s=1.05)
    S.wire(ax2, [q, c])
    S.wire(ax2, [d, (5.1, 3.4)])
    S.shunt(ax2, 5.1, 3.4, 0.1, 'ind', None, frac=0.50)
    S.label(ax2, 4.62, 1.75, 'L$_p$ $-$ L$_r$', size=11, ha='right')
    S.dot(ax2, 5.1, 3.4)
    t2 = X.xfmr(ax2, 7.5, 1.75, hp=3.3, hs=3.3, gap=0.52)
    S.wire(ax2, [(5.1, 3.4), t2['p_top']])
    S.wire(ax2, [t2['p_bot'], (t2['p_bot'][0], 0.1)])
    S.label(ax2, 7.5, -0.48, '1 : M$_v$   ideal', size=10.5, color=GREY)
    S.wire(ax2, [t2['s_top'], (9.9, 3.4)])
    S.wire(ax2, [t2['s_bot'], (t2['s_bot'][0], 0.1)])
    S.shunt(ax2, 9.9, 3.4, 0.1, 'res', 'R$_{ac}$', frac=0.44)
    S.label(ax2, 10.9, 1.75, 'V$_{RO}^F$', size=11, ha='left')

    foot(fig, 'L_r is the whole leakage seen from the primary and L_p the '
              'whole open-circuit inductance, so lambda = L_r / (L_p - L_r). '
              'The turns ratio that survives the referral is M_v = '
              'sqrt(L_p / (L_p - L_r)), which is n, not n_T - the difference '
              'between them is the coupling, and confusing the two moves the '
              'whole gain curve.')
    save(fig, 'an_integrated')


def _mains_bridge(ax, xs=0.4, xm=4.1, ym=1.6, ytop=4.0, ybot=-0.6):
    """Mains, a bridge, and the two dc rails leaving it.

    The ac source belongs across the bridge's two AC corners, not across
    its dc rails - which is what the first version of this drawing did, and
    it is the kind of mistake a reader checks a note for.  Reaching the far
    ac corner costs exactly one crossing, and the dc return hops it.

    -> (x of the + rail start, x of the - rail start, x where they are free)
    """
    S.acsrc(ax, xs, ym, None)
    S.label(ax, xs - 0.52, ym, 'mains', size=10.5, color=GREY, ha='right')
    L, Rt, P, Mn = _bridge(ax, xm, ym)
    S.wire(ax, [(xs, ym + 0.36), (xs, ym + 1.9), (L[0] - 0.9, ym + 1.9),
                (L[0] - 0.9, ym), L])
    #  the far ac corner, round the bottom
    yfar = ybot - 0.9
    S.wire(ax, [(xs, ym - 0.36), (xs, yfar), (Rt[0], yfar), (Rt[0], ym)])
    S.wire(ax, [P, (xm, ytop)])
    S.wire(ax, [Mn, (xm, ybot), (Rt[0] - 0.20, ybot)])
    S.hop(ax, Rt[0], ybot)
    S.wire(ax, [(Rt[0] + 0.20, ybot), (xm + 3.0, ybot)])
    S.wire(ax, [(xm, ytop), (xm + 3.0, ytop)])
    return xm + 3.0


# ------------------------------------------------------- 3  the PFC problem
def an_pfc_cap(save, foot):
    """A capacitor-input rectifier, and the current it draws."""
    fig = plt.figure(figsize=(11.4, 6.6))

    ax = _ax(fig, [0.05, 0.50, 0.90, 0.46], -1.4, 13.6, -2.4, 5.0)
    xe = _mains_bridge(ax, 0.4, 4.1, 1.6, 4.0, -0.6)
    S.wire(ax, [(xe, 4.0), (11.6, 4.0)])
    S.wire(ax, [(xe, -0.6), (11.6, -0.6)])
    S.shunt(ax, 9.9, 4.0, -0.6, 'cap', 'C', frac=0.30)
    S.shunt(ax, 11.6, 4.0, -0.6, 'res', None, frac=0.46)
    S.label(ax, 12.35, 1.7, 'load', size=10.5, ha='left')
    S.label(ax, 9.15, 1.7, 'v$_C$', size=11.5, ha='right', color=MAG)

    # what that draws
    aw = fig.add_axes([0.075, 0.10, 0.885, 0.31])
    #  Three line periods are simulated and the last two drawn.  Started
    #  from an empty capacitor the first quarter cycle is one long charge,
    #  and a startup transient drawn as if it were steady state is exactly
    #  the wrong picture for this argument.
    tt = np.linspace(0, 6, 12000)
    vv = np.sin(np.pi * tt)
    vr = np.abs(vv)
    vc = np.empty_like(tt)
    tau, hold = 8.0, 1.0           # tau in half-line-periods: ~12 % droop
    for k in range(len(tt)):
        if k:
            hold *= np.exp(-(tt[k] - tt[k - 1]) / tau)
        hold = max(hold, vr[k])
        vc[k] = hold
    cond = vr >= vc - 1e-12
    ic = np.gradient(vc, tt)                 # the capacitor's own current
    ic = np.clip(np.where(cond, ic, 0.0), 0, None)
    ic = ic / max(ic.max(), 1e-12) * 0.92 * np.sign(vv)

    m = tt >= 2.0
    t = tt[m] - 2.0
    aw.plot(t, vv[m], color=NAVY, lw=1.9, label='line voltage')
    aw.plot(t, vc[m], color=MAG, lw=2.2, label='v$_C$')
    aw.plot(t, -vc[m], color=MAG, lw=2.2)
    aw.fill_between(t, 0, ic[m], color=MAG, alpha=0.34, lw=0,
                    label='line current')
    aw.plot(t, ic[m], color=MAG, lw=1.3)
    aw.set_xlim(0, 4)
    aw.set_ylim(-1.45, 1.45)
    aw.set_xticks([])
    aw.set_yticks([])
    for sp in aw.spines.values():
        sp.set_visible(False)
    aw.axhline(0, color=GREY, lw=0.9)
    aw.legend(loc='lower right', frameon=False, fontsize=10, ncol=3)
    for xc in (0.5, 2.5):
        _call(aw, (xc - 0.02, 0.30), (xc + 0.16, 1.24),
              'conducts only here', size=10)

    foot(fig, 'The capacitor holds the output near the crest, so the diodes '
              'are reverse biased for most of the cycle and the mains is '
              'asked for its whole charge in two narrow spikes. That is a '
              'power factor near 0.6, and it is the thing correction exists '
              'to fix.')
    save(fig, 'an_pfc_cap')


# -------------------------------------------------------- 4  boost corrector
def an_pfc_boost(save, foot):
    """A boost corrector, with the path traced for each half of its period."""
    fig = plt.figure(figsize=(12.0, 6.4))

    for k, (rect, on, ttl) in enumerate((
            ([0.03, 0.10, 0.455, 0.80], True,
             'switch ON - the reactor charges from the line'),
            ([0.525, 0.10, 0.455, 0.80], False,
             'switch OFF - the reactor delivers to C, in series with the '
             'line'))):
        ax = _ax(fig, rect, -1.8, 14.6, -3.0, 6.2)
        S.label(ax, 6.4, 5.80, ttl, size=11, color=MAG if on else GRN)
        xe = _mains_bridge(ax, 0.4, 4.1, 1.6, 4.0, -0.6)

        c, d = S.ind(ax, 8.0, 4.0, 'L', s=1.00, tdy=0.62)
        S.wire(ax, [(xe, 4.0), c])
        S.wire(ax, [d, (9.6, 4.0)])
        S.dot(ax, 9.6, 4.0)
        di, do = S.diode(ax, 10.6, 4.0, 'D', s=0.30)
        S.wire(ax, [(9.6, 4.0), di])
        S.wire(ax, [do, (12.0, 4.0)])
        X.mosfet(ax, 9.6, 2.0, 'Q', 'on' if on else 'off', h=1.40,
                 gate=0.78, body=False, coss=False, name_at='gate', size=10)
        S.wire(ax, [(9.6, 4.0), (9.6, 2.70)])
        S.wire(ax, [(9.6, 1.30), (9.6, -0.6)])
        S.wire(ax, [(xe, -0.6), (13.4, -0.6)])
        S.shunt(ax, 12.0, 4.0, -0.6, 'cap', 'C', frac=0.30)
        S.shunt(ax, 13.4, 4.0, -0.6, 'res', None, frac=0.46)
        S.label(ax, 13.4, -1.15, 'load', size=10.5)
        S.label(ax, 12.0, -1.15, 'V$_{bus}$', size=11)

        #  Only the boost loop is highlighted.  The bridge carries the same
        #  current in both panels, so colouring it would say nothing.
        X.register(hops=[], vcoils=[], hcoils=[(8.0, 4.0, 1.00, 4)])
        #  Heads go on clear stretches, and the head size is in POINTS, so
        #  it does not shrink with a half-width panel: at 18 it swallowed
        #  the reactor's first turn whole.
        if on:
            X.path(ax, [(xe, 4.0), (9.6, 4.0), (9.6, 2.70), (9.6, 1.30),
                        (9.6, -0.6), (xe, -0.6)],
                   load=True, head=13, heads=((1, 0.08), (5, 0.45)))
        else:
            X.path(ax, [(xe, 4.0), (9.6, 4.0), (12.0, 4.0), (12.0, -0.6),
                        (xe, -0.6)],
                   load=True, head=13,
                   heads=((1, 0.08), (2, 0.80), (4, 0.45)))
        X.register()

    foot(fig, 'The switch is modulated so the average reactor current '
              'follows the rectified line, which is what makes the converter '
              'look resistive. Because it is a boost, the bus has to sit '
              'above the line crest - that is where the 400 V comes from, '
              'and it is what a single-stage converter is getting rid of.')
    save(fig, 'an_pfc_boost')


# ------------------------------------------------------------ 5  CCM current
def an_pfc_ccm(save, foot):
    """What that modulation looks like over a line half cycle."""
    fig = plt.figure(figsize=(11.2, 4.6))
    ax = fig.add_axes([0.06, 0.20, 0.90, 0.72])
    t = np.linspace(0, 1, 24000)
    vin = np.sin(np.pi * t)
    avg = vin.copy()
    #  Ripple amplitude falls as the duty approaches 1, which is why the
    #  band is widest at the zero crossings and pinches at the crest.
    nsw = 17
    ph = (t * nsw) % 1.0
    d = 1.0 - 0.72 * vin                      # duty, boost, bus fixed
    tri = np.where(ph < d, ph / np.maximum(d, 1e-6),
                   1.0 - (ph - d) / np.maximum(1 - d, 1e-6))
    #  The average current is drawn below the voltage on purpose: they are
    #  the same shape, which is the point, and laid on top of each other one
    #  of them simply disappears.
    avg = 0.80 * vin
    rip = 0.30 * vin * d
    cur = avg + rip * (tri - 0.5) * 2.0
    ax.plot(t, vin, color=NAVY, lw=2.0, label='line voltage')
    ax.plot(t, cur, color=MAG, lw=1.2, label='reactor current')
    ax.plot(t, avg, color=GRN, lw=2.2, ls=(0, (5, 2.6)),
            label='its average - the line current')
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.22, 1.30)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.axhline(0, color=GREY, lw=0.9)
    ax.legend(loc='upper right', frameon=False, fontsize=10.5)
    _call(ax, (0.30, cur[int(0.30 * len(t))]), (0.10, 1.18),
          'the switching ripple never reaches zero -\ncontinuous conduction',
          size=10)
    foot(fig, 'Continuous conduction mode: the reactor current never falls '
              'to zero inside a switching period, so its average is the '
              'quantity the control loop shapes.')
    save(fig, 'an_pfc_ccm')


# -------------------------------------------------------- 6  the two stages
def an_two_stage(save, foot):
    """The usual two-stage arrangement, with the waveform at every node."""
    fig = plt.figure(figsize=(12.2, 5.2))
    ax = _ax(fig, [0.03, 0.06, 0.94, 0.62], -0.4, 24.6, -1.4, 3.2)

    blocks = [(2.6, 'bridge'), (6.2, 'boost PFC'), (13.4, 'LLC'),
              (17.4, 'transformer'), (20.8, 'rectifier')]
    for x, t in blocks:
        S.box(ax, x, 1.0, 2.9, 1.5, t, fc=LT, ec=GREY, size=10.5)
    S.box(ax, 9.8, 1.0, 2.6, 1.5, '400 V\nbulk C', fc=YEL, ec=MAG, size=10.5)
    S.label(ax, 15.6, 2.35, 'dc / dc converter', size=10, color=GREY)
    S.shade(ax, 11.9, 0.05, 22.4, 1.95, None, color=CYA, alpha=0.07)
    S.label(ax, 0.1, 1.0, 'V$_{in}$', size=11.5, ha='right', weight='bold')
    S.label(ax, 23.0, 1.0, 'V$_{out}$', size=11.5, ha='left', weight='bold')
    xs = [0.1] + [x + 1.45 for x, _ in blocks[:-1]] + [22.4]
    prev = 0.1
    for x, _ in blocks:
        S.wire(ax, [(prev, 1.0), (x - 1.45, 1.0)])
        prev = x + 1.45
    S.wire(ax, [(7.65, 1.0), (8.5, 1.0)])
    S.wire(ax, [(11.1, 1.0), (11.95, 1.0)])
    S.wire(ax, [(22.25, 1.0), (23.0, 1.0)])
    S.label(ax, 9.8, -0.42, 'the buffer sits here', size=10, color=MAG)

    # a strip of node waveforms, each above the wire it belongs to
    t = np.linspace(0, 1, 900)
    nodes = [(0.1, 'mains', np.sin(6 * np.pi * t), NAVY),
             (4.4, 'rectified', np.abs(np.sin(6 * np.pi * t)) * 1.6 - 0.8,
              NAVY),
             (8.0, 'shaped\ncurrent', np.abs(np.sin(6 * np.pi * t)) * 1.6
              - 0.8, GRN),
             (11.5, '400 V dc', 0.20 * np.sin(12 * np.pi * t) + 0.45, MAG),
             (15.6, 'hf square',
              0.80 * np.sign(np.sin(34 * np.pi * t)), CYA),
             (22.4, 'dc out', 0.45 + 0.05 * np.sin(12 * np.pi * t), MAG)]
    for x, nm, y, c in nodes:
        #  Axes fraction from the SAME mapping the schematic uses, or the
        #  thumbnail floats above the wrong block - which it did.
        fx = 0.03 + (x - (-0.4)) / 25.0 * 0.94
        a = fig.add_axes([fx - 0.038, 0.735, 0.076, 0.135])
        a.plot(t, y, color=c, lw=1.5)
        a.set_xlim(0, 1)
        a.set_ylim(-1.15, 1.15)
        a.set_xticks([])
        a.set_yticks([])
        for sp in a.spines.values():
            sp.set_color(GREY)
            sp.set_linewidth(0.7)
        a.set_title(nm, fontsize=9.2, color=GREY, pad=3)

    foot(fig, 'Correction happens in the first block, and the LLC works from '
              'a dc bus that is already regulated. Two controllers, two sets '
              'of switches, and a 400 V electrolytic between them.')
    save(fig, 'an_two_stage')


# ------------------------------------------------------- 7  LLC waveforms
def _cycle(ratio, lam, ilr_pk, ilm_pk, td=0.05, n=2400):
    """One switching period of i_Lm, i_Lr and the rectifier current.

    Below resonance this is the model the eight-mode panels were drawn
    with, imported so the two figures cannot disagree.  That model has no
    meaning at or above resonance: it takes the freewheeling interval to be
    what is left of the half period after T_r/2 and the dead time, and at
    f_sw = f_r that is already negative.  Drawn anyway it produces a
    timeline whose marks are out of order, which is what the first version
    of the three-case figure did.

    So at and above resonance the half sine is TRUNCATED instead.  The
    rectifier is still carrying current when the half period ends and the
    switches commutate it - which is the whole point of that column, and
    the reason reverse recovery belongs to this side of resonance.

    -> t, edges, i_Lm, i_Lr, i_rect, truncated?
    """
    H = 0.5
    tres = ratio / 2.0                   # half of the resonant period
    if tres <= H - td + 1e-9:
        import figs_modes8 as F
        e = F._timeline(ratio, td)
        io_pk = F._solve_io(lam, ratio, e, ilm_pk, ilr_pk)
        t = np.linspace(0.0, 1.0, n)
        h = np.where(t < H, t, t - H)
        ilm, ilr, io = F._halfwave(h, lam, ratio, e, ilm_pk, io_pk)
        sgn = np.where(t < H, 1.0, -1.0)
        return t, e, ilm * sgn, ilr * sgn, io, False

    #  Truncated: the secondary conducts right up to the dead time, so L_m
    #  is clamped for the whole of it and i_Lm is one straight ramp.
    t1 = H - td
    t = np.linspace(0.0, 1.0, n)
    h = np.where(t < H, t, t - H)
    ilm = np.where(h <= t1, -ilm_pk + 2.0 * ilm_pk * h / t1, ilm_pk)
    io_pk = ilr_pk - ilm_pk * 0.0
    io = np.where(h <= t1, np.sin(np.pi * np.clip(h, 0, t1) / tres), 0.0)
    #  scale the load component so the sum peaks at the design tank peak
    tot = ilm + io
    io = io * (ilr_pk - ilm.max()) / max(tot.max() - ilm.max(), 1e-9)
    ilr = ilm + io
    sgn = np.where(t < H, 1.0, -1.0)
    t3 = td * 0.40
    e = [0.0, t1, t1, t1 + t3, H]
    e = e + [x + H for x in e[1:]]
    return t, e, ilm * sgn, ilr * sgn, io, True


def an_llc_waves(save, foot):
    """The waveforms of one switching period, named."""
    import figs_modes8 as F
    fig = plt.figure(figsize=(10.6, 7.4))
    lam, fr = 0.55, 1.0
    t, e, ilm, ilr, io, _ = _cycle(0.70, lam, 18.32, 12.41)

    rows = [('i$_{Lr}$, i$_{Lm}$', 0.0), ('i$_{S1}$', 0.0), ('i$_{D}$', 0.0),
            ('v$_d$', 0.0), ('gates', 0.0)]
    hgt = [0.175, 0.125, 0.125, 0.125, 0.115]
    y = 0.955
    axs = []
    for (nm, _), h in zip(rows, hgt):
        y -= h + 0.021
        a = _wave_ax(fig, [0.105, y, 0.855, h], 0, 1, -1.25, 1.25, nm)
        axs.append(a)

    m = max(abs(ilr).max(), 1e-9)
    axs[0].set_ylim(-1.18, 1.18)
    axs[0].plot(t, ilr / m, color=MAG, lw=2.0)
    axs[0].plot(t, ilm / m, color=CYA, lw=1.8, ls=(0, (4, 2.4)))
    axs[0].text(0.5, 1.10, 'i$_{Lr}$ solid,  i$_{Lm}$ dashed - where they '
                'meet, the secondary stops conducting',
                transform=axs[0].transAxes, va='bottom', ha='center',
                fontsize=9.8, color=GREY)

    #  S1 conducts for as long as it is gated on: intervals 1 and 2.  It
    #  starts NEGATIVE, which is what the annotation is about.
    s1 = np.where(t < e[2], ilr / m, 0.0)
    axs[1].plot(t, s1, color=NAVY, lw=1.9)
    axs[1].fill_between(t, 0, s1, color=NAVY, alpha=0.13, lw=0)

    axs[2].set_ylim(-0.12, 1.25)
    axs[2].plot(t, io / max(io.max(), 1e-9), color=GRN, lw=1.9)

    T = t
    v = F._step(T, e, -1.0, 1.0)
    axs[3].plot(T, v, color=NAVY, lw=2.0)

    g1 = np.where((T >= e[0]) & (T < e[2]), 1.0, 0.0)
    g2 = np.where((T >= e[4]) & (T < e[6]), 1.0, 0.0)
    axs[4].set_ylim(-0.25, 2.5)
    axs[4].fill_between(T, 0.0, g1 * 0.9, color=YEL, lw=0)
    axs[4].plot(T, g1 * 0.9, color=NAVY, lw=1.5)
    axs[4].fill_between(T, 1.3, 1.3 + g2 * 0.9, color=YEL, lw=0)
    axs[4].plot(T, 1.3 + g2 * 0.9, color=NAVY, lw=1.5)
    axs[4].text(0.25, 0.45, 'S$_1$,S$_4$', ha='center', va='center',
                fontsize=9.6, color=NAVY, path_effects=HALO, zorder=9)
    axs[4].text(0.75, 1.75, 'S$_2$,S$_3$', ha='center', va='center',
                fontsize=9.6, color=NAVY, path_effects=HALO, zorder=9)

    for a in axs:
        for x in (e[1], e[2], e[4], e[5], e[6]):
            a.axvline(x, color=GREY, lw=0.7, ls=(0, (2, 3)), zorder=0)

    _call(axs[1], (0.004, s1[2]), (0.13, -0.78),
          'S$_1$ turns on with its own current still negative - that is ZVS',
          size=10)

    foot(fig, 'Below resonance. i_Lr leaves i_Lm while the secondary '
              'conducts and rejoins it when the rectifier current reaches '
              'zero; what is left of the half period circulates. The drive '
              'node swings during the dead time, before the gate that '
              'follows it goes high.')
    save(fig, 'an_llc_waves')


# --------------------------------------------------- 8  below / at / above
def an_three_cases(save, foot):
    """The three cases side by side."""
    import figs_modes8 as F
    fig = plt.figure(figsize=(12.4, 7.0))
    lam = 0.55
    #  The middle column is the boundary case the model itself defines:
    #  the resonant half sine exactly fills the half period less the dead
    #  time, so the freewheeling interval has just closed and nothing is
    #  truncated yet.  With a finite dead time that is a shade below f_r,
    #  and the dead time here is drawn wider than it is.
    td = 0.05
    cases = [(0.70, 'below resonance', 'f$_{sw}$ < f$_r$'),
             (1.0 - 2 * td, 'at resonance', 'f$_{sw}$ = f$_r$'),
             (1.30, 'above resonance', 'f$_{sw}$ > f$_r$')]
    names = ['gates', 'v$_d$', 'i$_{Lr}$, i$_{Lm}$', 'i$_D$']
    hgt = [0.115, 0.145, 0.205, 0.155]
    for c, (ratio, ttl, sub) in enumerate(cases):
        t, e, ilm, ilr, io, trunc = _cycle(ratio, lam, 18.32, 12.41,
                                          td=td)
        x0 = 0.055 + c * 0.323
        fig.text(x0 + 0.128, 0.965, ttl, ha='center', fontsize=12,
                 color=NAVY, fontweight='bold')
        fig.text(x0 + 0.128, 0.936, sub, ha='center', fontsize=10.5,
                 color=GREY)
        y = 0.915
        axs = []
        for nm, h in zip(names, hgt):
            y -= h + 0.028
            a = _wave_ax(fig, [x0, y, 0.256, h], 0, 1, -1.25, 1.25,
                         nm if c == 0 else None)
            axs.append(a)
        T = t
        g1 = np.where((T >= e[0]) & (T < e[2]), 1.0, 0.0)
        g2 = np.where((T >= e[4]) & (T < e[6]), 1.0, 0.0)
        axs[0].set_ylim(-0.25, 2.5)
        for base, g in ((0.0, g1), (1.3, g2)):
            axs[0].fill_between(T, base, base + g * 0.9, color=YEL, lw=0)
            axs[0].plot(T, base + g * 0.9, color=NAVY, lw=1.4)
        axs[1].plot(T, F._step(T, e, -1.0, 1.0), color=NAVY, lw=1.9)
        m = max(abs(ilr).max(), 1e-9)
        axs[2].plot(T, ilr / m, color=MAG, lw=1.9)
        axs[2].plot(T, ilm / m, color=CYA, lw=1.7, ls=(0, (4, 2.4)))
        axs[3].set_ylim(-0.12, 1.25)
        axs[3].plot(T, io / max(io.max(), 1e-9), color=GRN, lw=1.9)
        for a in axs:
            for xv in (e[1], e[2], e[4], e[5], e[6]):
                a.axvline(xv, color=GREY, lw=0.7, ls=(0, (2, 3)), zorder=0)
        #  The interval the freewheeling happens in is what changes across
        #  the three columns, so it is the thing to mark.
        if not trunc and e[2] - e[1] > 0.004:
            axs[3].annotate('', xy=(e[1], 1.12), xytext=(e[2], 1.12),
                            arrowprops=dict(arrowstyle='<->', color=CYA,
                                            lw=1.6))
            axs[3].text((e[1] + e[2]) / 2.0, 1.32, 'freewheeling',
                        ha='center', fontsize=9.4, color=CYA,
                        path_effects=HALO, zorder=9)
        else:
            axs[3].text(0.5, 1.30, 'no freewheeling interval left',
                        ha='center', fontsize=9.4, color=CYA,
                        path_effects=HALO, zorder=9)
        if trunc:
            _call(axs[3], (e[1], io[int(e[1] * len(t)) - 2]
                           / max(io.max(), 1e-9)),
                  (0.04, -0.62),
                  'still conducting when the half\nperiod ends - the '
                  'switches\ncommutate it, so the rectifier\nhas to recover',
                  color=GRN, size=9.0)

    foot(fig, 'Below resonance the rectifier current reaches zero before the '
              'half period does and the rest of it circulates. At resonance '
              'the two coincide. Above resonance the half period ends first, '
              'so the rectifier is commutated by the switches rather than by '
              'its own current reaching zero - which is where the reverse '
              'recovery comes from.')
    save(fig, 'an_three_cases')


# ----------------------------------------------- 9  either side of the edge
def _edge_curves(lam, qs):
    fn = np.linspace(0.30, 2.6, 900)
    return [(q, np.array([M(f, q, lam) for f in fn]), zvs_edge(q, lam))
            for q in qs], fn


def an_cap_ind(save, foot):
    """The same converter either side of the boundary, and how it shows."""
    import figs_modes8 as F
    fig = plt.figure(figsize=(12.0, 8.0))
    lam, q = 0.55, 0.766

    ax = fig.add_axes([0.085, 0.620, 0.855, 0.350])
    fn = np.linspace(0.34, 2.4, 1200)
    g = np.array([M(f, q, lam) for f in fn])
    edge = zvs_edge(q, lam)
    pk = fn[int(np.argmax(g))]
    ax.plot(fn, g, color=NAVY, lw=2.4)
    ax.axvspan(fn[0], edge, color=MAG, alpha=0.10, lw=0)
    ax.axvspan(edge, fn[-1], color=GRN, alpha=0.11, lw=0)
    ax.axvline(edge, color=GREY, lw=1.6, ls=(0, (5, 3)))
    ax.plot([pk], [g.max()], marker='*', ms=15, color=NAVY, zorder=5)
    _call(ax, (pk, g.max()), (pk + 0.40, g.max() - 0.04),
          'gain peak - NOT the boundary', color=NAVY, size=10)
    ax.text(edge + 0.02, ax.get_ylim()[0] + 0.06,
            '  boundary: arg Z$_{in}$ = 0', fontsize=10, color=GREY,
            ha='left')
    ax.text((fn[0] + edge) / 2.0, g.max() * 0.30, 'capacitive\nhard '
            'switching', ha='center', fontsize=11.5, color=MAG,
            path_effects=HALO, zorder=9)
    ax.text(edge + 0.62, g.max() * 0.30, 'inductive\nZVS', ha='center',
            fontsize=11.5, color=GRN, path_effects=HALO, zorder=9)
    ax.set_xlabel('f$_{sw}$ / f$_r$', fontsize=11, color=NAVY)
    ax.set_ylabel('M', fontsize=11, color=NAVY)
    ax.tick_params(labelsize=9.5, colors=GREY)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)

    #  The two cases, drawn from the phase itself.
    #
    #  The first version of this panel built these traces with the same
    #  time-domain model the mode panels use.  That model always produces a
    #  switch current that is negative at turn-on, because it was written
    #  for a converter operating inductively - so the "capacitive" column
    #  was an inductive waveform with a capacitive label on it.  What
    #  actually separates the two cases is the SIGN of arg Z_in, and that is
    #  a number l6790.phase() gives for any f_n, so the traces are drawn
    #  from it and nothing here is invented.
    for c, (fnx, nm, col) in enumerate(((edge * 0.80, 'capacitive', MAG),
                                        (edge * 1.45, 'inductive', GRN))):
        phi = phase(fnx, q, lam)               # arg Z_in, radians
        fig.text(0.085 + c * 0.470 + 0.192, 0.505, nm, ha='center',
                 fontsize=12.5, color=col, fontweight='bold')
        fig.text(0.085 + c * 0.470 + 0.192, 0.482,
                 'f$_{sw}$/f$_r$ = %.2f,   arg Z$_{in}$ = %+.0f$\\degree$'
                 % (fnx, np.degrees(phi)), ha='center', fontsize=10,
                 color=GREY)
        tt = np.linspace(0, 2, 2000)
        vd = np.where((tt % 1.0) < 0.5, 1.0, -1.0)
        cur = np.sin(2 * np.pi * tt - phi)
        y = 0.452
        for nmx, h in (('v$_d$', 0.108), ('i$_{Lr}$', 0.140)):
            y -= h + 0.036
            a = _wave_ax(fig, [0.085 + c * 0.470, y, 0.385, h], 0, 2,
                         -1.35, 1.35, nmx if c == 0 else None)
            if nmx == 'v$_d$':
                a.plot(tt, vd, color=NAVY, lw=1.9)
            else:
                a.plot(tt, cur, color=col, lw=2.1)
                for k in (0.0, 1.0):
                    a.plot([k], [np.sin(-phi)], 'o', color=col, ms=8,
                           zorder=6)
                a.axvline(0.0, color=GREY, lw=0.8, ls=(0, (2, 3)))
                a.axvline(1.0, color=GREY, lw=0.8, ls=(0, (2, 3)))
        tail = ('POSITIVE at turn-on - the current was already\nflowing '
                'the other way, so the body diode of the\nswitch about to '
                'close has to recover.'
                if np.sin(-phi) > 0 else
                'NEGATIVE at turn-on - the current had already\nswung the '
                'node over, so the switch closes\non zero volts.  ZVS.')
        fig.text(0.085 + c * 0.470 + 0.192, 0.112, tail, ha='center',
                 va='top', fontsize=9.6, color=col, linespacing=1.5)

    foot(fig, 'The boundary is where the tank input impedance phase crosses '
              'zero, and that is a little above the peak of the gain curve - '
              'so quoting the peak reports a band of hard switching as '
              'inductive. Both shaded regions here come from '
              'l6790.zvs_edge, which solves the phase for zero in closed '
              'form.')
    save(fig, 'an_cap_ind')


# ------------------------------------------------------- 10  load shifts it
def an_loadshift(save, foot):
    """The boundary is not fixed: loading the converter moves it."""
    fig = plt.figure(figsize=(10.6, 5.8))
    ax = fig.add_axes([0.085, 0.145, 0.885, 0.79])
    lam = 0.55
    fn = np.linspace(0.34, 2.4, 1400)
    #  Q is picked so all three peaks fit one frame.  At Q = 0.2 the peak
    #  is off the top of any sensible axis and the curve tells the reader
    #  nothing except that it is tall.
    qs = [(0.55, 'light load', CYA), (0.85, 'half load', PUR),
          (1.35, 'overload', MAG)]
    edges = []
    for q, nm, col in qs:
        g = np.array([M(f, q, lam) for f in fn])
        ax.plot(fn, g, color=col, lw=2.2, label='%s   Q = %.2f' % (nm, q))
        e = zvs_edge(q, lam)
        edges.append((e, M(e, q, lam), col))
    for e, me, col in edges:
        ax.plot([e], [me], 'o', color=col, ms=8, zorder=6)
    qq = np.linspace(0.30, 1.90, 400)
    ex = np.array([zvs_edge(q, lam) for q in qq])
    ey = np.array([M(zvs_edge(q, lam), q, lam) for q in qq])
    ax.plot(ex, ey, color=GREY, lw=2.0, ls=(0, (5, 3)),
            label='the boundary itself')
    ax.axhline(1.0, color=GREY, lw=1.0, ls=(0, (2, 3)))
    ax.text(2.33, 1.03, 'unity gain', ha='right', fontsize=9.8, color=GREY)
    _call(ax, (edges[-1][0], edges[-1][1]), (edges[0][0] + 0.34, 1.74),
          'loading it moves the boundary UP in frequency', color=NAVY,
          rad=0.22)
    ax.annotate('', xy=(edges[0][0], edges[0][1]),
                xytext=(edges[0][0] + 0.32, 1.72),
                arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=1.4,
                                connectionstyle='arc3,rad=-0.22'))
    ax.set_xlim(0.34, 2.4)
    ax.set_ylim(0, 1.95)
    ax.set_xlabel('f$_{sw}$ / f$_r$', fontsize=11, color=NAVY)
    ax.set_ylabel('M', fontsize=11, color=NAVY)
    ax.tick_params(labelsize=9.5, colors=GREY)
    ax.legend(loc='upper right', frameon=False, fontsize=10)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    foot(fig, 'A frequency that is inductive at light load can be capacitive '
              'at overload, so the minimum frequency has to clear the '
              'boundary at the worst load the converter will see, not at the '
              'one it was drawn for.')
    save(fig, 'an_loadshift')


# --------------------------------------------------------- 11  peak gain
def an_peakgain(save, foot):
    """Why m and Q cannot be chosen separately."""
    fig = plt.figure(figsize=(10.4, 6.0))
    ax = fig.add_axes([0.095, 0.135, 0.875, 0.82])
    fn = np.linspace(0.16, 3.0, 2400)
    qs = np.linspace(0.20, 1.40, 90)
    ms = [2.25, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0]
    cols = plt.cm.viridis(np.linspace(0.08, 0.86, len(ms)))
    #  Every curve is labelled ON itself, at the Q where it is still well
    #  clear of its neighbours.  Stacked at the right-hand end - where they
    #  all converge on a gain of 1 - the labels landed on top of each other.
    #  Each label is put where its own curve crosses a height reserved for
    #  it, so no two can land in the same place and none can land outside
    #  the frame.  Fixed Q anchors did both.
    import matplotlib.patheffects as _pe
    targets = np.linspace(2.16, 1.14, len(ms))
    for mm, col, yt in zip(ms, cols, targets):
        lam = 1.0 / (mm - 1.0)                 # m = L_p / L_r = 1 + 1/lambda
        pk = np.array([max(M(f, q, lam) for f in fn) for q in qs])
        ax.plot(qs, pk, color=col, lw=2.0)
        qa = float(np.interp(-yt, -pk, qs))    # pk falls with Q
        ax.text(qa + 0.022, yt + 0.022, 'm = %g' % mm, fontsize=9.6,
                color=col, va='bottom', ha='left', clip_on=True,
                path_effects=[_pe.withStroke(linewidth=3.2,
                                             foreground='white')])
    ax.set_xlim(0.20, 1.42)
    ax.set_ylim(1.0, 2.3)
    ax.set_xlabel('Q', fontsize=11.5, color=NAVY)
    ax.set_ylabel('peak gain', fontsize=11.5, color=NAVY)
    ax.grid(True, color=LT, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=9.5, colors=GREY)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    _call(ax, (0.62, max(M(f, 0.62, 1.0 / (3.0 - 1.0)) for f in fn)),
          (0.80, 1.66), 'pick a required peak gain and a Q,\n'
          'and m is decided', rad=-0.2)
    foot(fig, 'm = L_p / L_r. A single-stage converter needs a wide gain '
              'range at a Q that is not small, which is what pushes m down '
              'to about 3 - the shape of these curves is the reason the '
              'usual m = 5 to 10 will not start at low line.')
    save(fig, 'an_peakgain')


FIGS = {'an_rac': an_rac, 'an_integrated': an_integrated,
        'an_pfc_cap': an_pfc_cap, 'an_pfc_boost': an_pfc_boost,
        'an_pfc_ccm': an_pfc_ccm, 'an_two_stage': an_two_stage,
        'an_llc_waves': an_llc_waves, 'an_three_cases': an_three_cases,
        'an_cap_ind': an_cap_ind, 'an_loadshift': an_loadshift,
        'an_peakgain': an_peakgain}


# ---------------------------------------- 12  the two conducting intervals
def _pair(save, name, nums, figsize=(17.2, 5.4)):
    """Two mode panels side by side, for the places in the note that need
    only the conducting intervals.

    The full eight-panel sheets carry the dead time as well, which is the
    thing the borrowed figures had no picture of at all.  These two are the
    drop-in pair: same drawing, same colours, the intervals the surrounding
    text is about and nothing else.
    """
    import figs_modes8 as F
    fig, axs = plt.subplots(1, 2, figsize=figsize)
    for ax, n in zip(axs, nums):
        F.panel(ax, F.MODES[n - 1])
    fig.subplots_adjust(left=0.004, right=0.996, top=0.995, bottom=0.075,
                        wspace=0.02)
    F._legend(fig, y=0.012)
    save(fig, name)


def an_op_power(save, foot):
    _pair(save, 'an_op_power', (1, 5))


def an_op_free(save, foot):
    _pair(save, 'an_op_free', (2, 6))


FIGS['an_op_power'] = an_op_power
FIGS['an_op_free'] = an_op_free
