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
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
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


def _diode_along(ax, a, b, s=None, color=NAVY, lw=2.2, z=4):
    """A diode ON the segment a->b, conducting in that direction.

    Built from the direction vector, not from a rotated marker.  The first
    version used matplotlib's rotatable triangle marker and every diode in
    every bridge came out pointing the wrong way - the sort of thing that
    makes a reader stop trusting the rest of the drawing.  The bar also has
    to sit AT the apex, not at the midpoint, or the triangle covers it and
    the symbol stops being a diode at all.
    """
    #  the kit's diode is 0.28 tall at scale 1 and its triangle 0.62 of that
    s = 0.62 * 0.28 * X.scale(ax) if s is None else s
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


def _bridge(ax, xm, ym, w=1.50, h=1.50, names=('D$_1$', 'D$_3$',
                                               'D$_2$', 'D$_4$'),
            size=9.5):
    """A diode bridge as a diamond.  -> (ac_left, ac_right, plus, minus)

    Drawn as two columns it needs one of the ac leads to cross the other
    column to reach its node, and a crossing in a four-device figure is a
    crossing too many.  On the diamond every terminal is a corner.

    All four conduct TOWARDS the + corner: that is what a bridge is, and
    it is the one thing in this drawing a reader will check.  The diamond
    is square, so its arms are true 45-degree wires: at 1.55 by 1.35 they
    were 4 degrees off, which figcheck's grid test reported.
    """
    L, Rt, P, Mn = (xm - w, ym), (xm + w, ym), (xm, ym + h), (xm, ym - h)
    #  Offsets grew with the figures: once a drawing is narrower the same
    #  point size covers more data units, and 0.48/0.34 put each name back
    #  on its own arm.
    for a, b, nm, dx, dy in ((L, P, names[0], -0.62, 0.44),
                             (Rt, P, names[1], 0.62, 0.44),
                             (Mn, L, names[2], -0.62, -0.44),
                             #  the bottom-right arm has the far ac corner's
                             #  riser just outside it, so this one name goes
                             #  BELOW its arm instead of outboard of it
                             (Mn, Rt, names[3], 0.22, -0.80)):
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
    fig = plt.figure(figsize=(9.35, 4.44))

    ax = _ax(fig, [0.02, 0.30, 0.62, 0.66], -1.2, 14.6, -2.3, 4.6)
    # the tank, standing in as a current source
    S.acsrc(ax, 0.3, 1.5, None)
    S.label(ax, 0.06, 0.76, 'i$_{ac}$', size=11, color=MAG, ha='right')
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
    #  Low-side rectification, as the design has it: each diode sits in
    #  the RETURN of its half, anode on the - rail, cathode at the winding
    #  end, and the tap is V_o+.  Drawn conducting the other way, as the
    #  first version was, the riser became the + rail and the tap the -
    #  rail: the output was upside down and nothing in the picture said so.
    for y, nm, dy in ((3.3, 'D$_1$', 0.60), (-0.3, 'D$_2$', 0.60)):
        di, do = S.diode(ax, 7.6, y, None, flip=True)
        S.wire(ax, [(6.9, y), do])
        S.wire(ax, [di, (XJ, y)])
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
    S.dot(ax, 11.1, 1.5)
    S.dot(ax, 11.1, -1.4)
    S.shunt(ax, 12.5, 1.5, -1.4, 'res', 'R$_o$', frac=0.52)
    S.label(ax, 12.98, 1.18, '+', size=12, color=GREY)
    S.label(ax, 12.98, -1.08, '$-$', size=12, color=GREY)
    S.label(ax, 13.4, 0.30, 'V$_O$', size=11.5, ha='left')
    S.label(ax, 13.4, -0.22, 'stiff', size=10, ha='left', color=GREY)



    ax2 = _ax(fig, [0.655, 0.34, 0.335, 0.56], -6.6, 3.6, -0.6, 4.6)
    #  One resistor, by itself.  The rails the first version ran either
    #  side of it led nowhere and read as a bus with a part hung on it;
    #  the terminal dots that replaced them marked nothing three wires
    #  meet at, which is what a dot is for.
    S.res(ax2, 1.5, 2.0, None, horiz=False)
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
    """The same transformer drawn both ways.

    Isolation is the point of a transformer, so the two sides have their
    own return rails.  The first version ran one rail under both windings
    and tied the secondary's bottom to it, which is a transformer with its
    isolation shorted out - the kind of thing a reader spots at once.
    """
    fig = plt.figure(figsize=(9.35, 5.80))
    XSRC, YT_, YB_ = 0.9, 3.4, 0.1

    def source(ax, f, name):
        """the drive, named on its LEFT: below, the name sat on the
        source's own return wire"""
        left, right = f(ax, XSRC, 1.8, None)
        r = XSRC - left[0]
        S.label(ax, XSRC - r - 0.22, 1.8, name, size=11, ha='right')
        S.wire(ax, [(XSRC, 1.8 + r), (XSRC, YT_)])
        S.wire(ax, [(XSRC, 1.8 - r), (XSRC, YB_)])

    def tank(ax, x_l, l_name, l_len, m_name):
        """C_r, the series inductor, the shunt inductor -> the node x"""
        p, q = S.cap(ax, 2.2, YT_, 'C$_r$', tdy=0.46)
        S.wire(ax, [(XSRC, YT_), p])
        c, d = S.ind(ax, x_l, YT_, l_name, s=l_len)
        S.wire(ax, [q, c])
        S.wire(ax, [d, (5.1, YT_)])
        S.shunt(ax, 5.1, YT_, YB_, 'ind', None, frac=0.50)
        S.label(ax, 4.62, 1.75, m_name, size=11, ha='right')
        S.dot(ax, 5.1, YT_)
        S.dot(ax, 5.1, YB_)

    # ---- as wound: leakage on both sides of an ideal n_T : 1
    ax = _ax(fig, [0.04, 0.545, 0.92, 0.40], -0.6, 15.0, -0.7, 4.9)
    S.label(ax, 7.2, 4.55, 'as wound:  leakage on both sides', size=11,
            color=GREY)
    source(ax, S.sqsrc, 'v$_{in}$')
    #  The shunt of the T model is L_mu, NOT the tank model's L_m.  They
    #  differ by the coupling - L_mu = sqrt(L_m (L_m + L_r)), which on this
    #  design is 24.9 uH against L_m = 20 uH - and the figure said L_m on
    #  both panels, which is the very confusion the caption warns about.
    #  The series elements carry the same names as equation Lmu, too.
    tank(ax, 3.7, 'L$_{L1}$', 0.95, 'L$_\\mu$')
    t = X.xfmr(ax, 7.5, 1.75, hp=3.3, hs=3.3, gap=0.52, lp=None, ls=None)
    S.wire(ax, [(5.1, YT_), t['p_top']])
    #  the primary's return rail ends at the primary
    S.wire(ax, [t['p_bot'], (XSRC, YB_)])          # p_bot is at YB_
    S.label(ax, 7.5, -0.48, 'n$_T$ : 1', size=10.5, color=GREY)
    #  L_lks starts clear of the secondary's polarity dot.  At 8.6 its
    #  first turn sat on top of the dot, and a dot under a coil is the one
    #  thing a transformer symbol cannot afford to be unclear about.
    e, f = S.ind(ax, 9.3, YT_, 'L$_{L2}$', s=0.95)
    S.wire(ax, [t['s_top'], e])
    #  What the secondary drives is the rectifier and the load - one block
    #  here, since this figure is about the magnetics.  v_RI is what it
    #  sees; the first version hung a bare C_o there with no rectifier.
    bl, _ = S.box(ax, 12.0, 1.75, 2.2, 3.9, 'rectifier\n+ load', size=10.5)
    S.wire(ax, [f, (bl[0], YT_)])
    S.wire(ax, [t['s_bot'], (bl[0], YB_)])
    S.label(ax, 10.45, YT_ + 0.36, '+', size=12, color=GREY)
    S.label(ax, 10.45, YB_ - 0.36, '$-$', size=12, color=GREY)
    S.label(ax, 10.45, 1.75, 'v$_{RI}$', size=11)

    #  from this drawing to the next: drawn on the figure, in the gap
    #  between the two panels, where neither axes can clip it
    fig.add_artist(FancyArrowPatch((0.5, 0.538), (0.5, 0.492),
                                   transform=fig.transFigure,
                                   arrowstyle='-|>', mutation_scale=16,
                                   color=MAG, lw=2.0, shrinkA=0, shrinkB=0))

    # ---- referred: all of it on the primary
    ax2 = _ax(fig, [0.04, 0.085, 0.92, 0.40], -0.6, 15.0, -0.7, 4.9)
    S.label(ax2, 7.2, 4.55, 'referred to the primary:  one L$_r$, one L$_m$, '
            'one ideal n : 1', size=11, color=GREY)
    #  a sine, because this is the first-harmonic circuit: the square-wave
    #  symbol the first version used here belongs to the drawing above
    source(ax2, S.acsrc, 'v$_{in}^F$')
    tank(ax2, 4.2, 'L$_r$', 1.05, 'L$_p$ $-$ L$_r$')
    t2 = X.xfmr(ax2, 7.5, 1.75, hp=3.3, hs=3.3, gap=0.52)
    S.wire(ax2, [(5.1, YT_), t2['p_top']])
    S.wire(ax2, [t2['p_bot'], (XSRC, YB_)])
    #  The one ideal transformer left after the referral has ratio n : 1,
    #  with n = n_T / M_v.  Written '1 : M_v' it read as a step-up of M_v,
    #  which is neither the wound ratio nor the model one.
    S.label(ax2, 7.5, -0.48, 'n : 1   ideal,   n = n$_T$ / M$_v$',
            size=10.5, color=GREY)
    S.wire(ax2, [t2['s_top'], (9.9, YT_)])
    S.wire(ax2, [t2['s_bot'], (9.9, YB_)])
    S.shunt(ax2, 9.9, YT_, YB_, 'res', 'R$_{ac}$')
    xv = 11.3
    ax2.add_patch(FancyArrowPatch((xv, YB_), (xv, YT_), arrowstyle='<|-|>',
                                  mutation_scale=12, color=GREY, lw=1.4,
                                  zorder=4, shrinkA=0, shrinkB=0))
    S.label(ax2, xv, YT_ + 0.36, '+', size=12, color=GREY)
    S.label(ax2, xv, YB_ - 0.36, '$-$', size=12, color=GREY)
    S.label(ax2, xv + 0.25, 1.75, 'V$_{RO}^F$', size=11, ha='left')

    foot(fig, 'Only the lower drawing has the tank model in it. Above, the '
              'shunt is the PHYSICAL magnetising inductance L_mu = '
              'sqrt(L_m (L_m + L_r)) and the ideal ratio is the wound one; '
              'below, the shunt is L_m = L_p - L_r and the ratio is n = n_T '
              '/ M_v with M_v = sqrt(L_p / (L_p - L_r)) = sqrt(1 + lambda). '
              'The difference between the two ratios is the coupling, and '
              'confusing them moves the whole gain curve.')
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
    fig = plt.figure(figsize=(9.35, 5.41))

    ax = _ax(fig, [0.05, 0.50, 0.90, 0.46], -1.4, 13.6, -2.4, 5.0)
    xe = _mains_bridge(ax, 0.4, 4.1, 1.6, 4.0, -0.6)
    S.wire(ax, [(xe, 4.0), (11.6, 4.0)])
    S.wire(ax, [(xe, -0.6), (11.6, -0.6)])
    S.shunt(ax, 9.9, 4.0, -0.6, 'cap', 'C', frac=0.30)
    S.dot(ax, 9.9, 4.0)
    S.dot(ax, 9.9, -0.6)
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
    #  v_C is a dc voltage; its mirror is drawn so the negative half cycle's
    #  conduction shows too, and it is named so it does not read as v_C
    aw.plot(t, -vc[m], color=MAG, lw=2.2, label='$-$v$_C$')
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
    aw.legend(loc='lower right', frameon=False, fontsize=10, ncol=4)
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
    fig = plt.figure(figsize=(9.35, 4.99))

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
        di, do = S.diode(ax, 10.6, 4.0, 'D')
        S.wire(ax, [(9.6, 4.0), di])
        #  on past C to the load: stopped at C, the load's top lead ended
        #  in the air, which figcheck was the first to notice
        S.wire(ax, [do, (13.4, 4.0)])
        X.mosfet(ax, 9.6, 2.0, 'Q', 'on' if on else 'off', h=1.40,
                 gate=0.78, body=False, coss=False, name_at='gate', size=10)
        S.wire(ax, [(9.6, 4.0), (9.6, 2.70)])
        S.wire(ax, [(9.6, 1.30), (9.6, -0.6)])
        S.wire(ax, [(xe, -0.6), (13.4, -0.6)])
        S.shunt(ax, 12.0, 4.0, -0.6, 'cap', 'C', frac=0.30)
        S.shunt(ax, 13.4, 4.0, -0.6, 'res', None, frac=0.46)
        for xd, yd in ((9.6, -0.6), (12.0, 4.0), (12.0, -0.6)):
            S.dot(ax, xd, yd)
        S.label(ax, 13.4, -1.15, 'load', size=10.5)
        #  the bus voltage is named on the + rail, where it is - under the
        #  - rail it read as the name of the return
        S.label(ax, 12.7, 4.45, 'V$_{bus}$', size=11)

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
    fig = plt.figure(figsize=(9.35, 3.84))
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
    """The usual two-stage arrangement, with the waveform at every node.

    Each waveform stands directly above the node it is measured at and a
    dotted leader runs down to that node.  The first version floated a
    row of small thumbnails a long way above a row of small blocks, and a
    reader could not tell which belonged to which - nor read either.
    """
    from matplotlib.patches import ConnectionPatch
    fig = plt.figure(figsize=(9.35, 5.48))
    ax = _ax(fig, [0.03, 0.04, 0.94, 0.50], -0.6, 30.4, -1.7, 2.9)

    YW = 1.0                                        # the chain's wire
    blocks = [(3.0, 1.7, 'bridge', LT, GREY),
              (8.2, 1.9, 'boost PFC', LT, GREY),
              (13.2, 1.5, '400 V\nbulk C', YEL, MAG),
              (18.0, 1.7, 'LLC', LT, GREY),
              (22.4, 2.1, 'transformer', LT, GREY),
              (26.8, 1.7, 'rectifier', LT, GREY)]
    for x, hw, t, fc, ec in blocks:
        #  11, not 12: at the narrower figure the longest name no
        #  longer fitted inside its own box
        S.box(ax, x, YW, 2 * hw, 2.2, t, fc=fc, ec=ec, size=11)
    S.shade(ax, 16.0, -0.35, 28.8, 2.35, None, color=CYA, alpha=0.07)
    S.label(ax, 22.4, -0.78, 'dc / dc converter', size=10.5, color=GREY)
    S.label(ax, 13.2, -0.78, 'the buffer sits here', size=10.5, color=MAG)
    S.label(ax, -0.1, YW, 'V$_{in}$', size=12, ha='right', weight='bold')
    S.label(ax, 29.85, YW, 'V$_{out}$', size=12, ha='left', weight='bold')
    edges = [0.4]
    for x, hw, *_ in blocks:
        edges += [x - hw, x + hw]
    edges.append(29.6)
    for x0, x1 in zip(edges[0::2], edges[1::2]):
        S.wire(ax, [(x0, YW), (x1, YW)])
    S.dot(ax, 0.4, YW)
    S.dot(ax, 29.6, YW)

    #  One waveform per node, above it.  The mains node carries voltage
    #  AND current: the current drawn from the mains is what the first
    #  stage shapes, and that is the whole reason the stage is there.
    t = np.linspace(0, 1, 900)
    v = np.sin(6 * np.pi * t)
    #  Every thumbnail carries its zero line, so a rectified or a dc node
    #  reads as one-sided and a mains or square-wave node as two-sided.
    #  Drawn centred, as the first version drew it, the rectified wave
    #  swung below zero.
    #  The bus ripple is a 2f_l SINE, and its sign is not free.  With
    #  v = V sin(theta) the mains delivers P(1 - cos 2theta) while the load
    #  takes P, so the capacitor's stored energy goes as -sin(2theta): the
    #  bus is at its LOWEST at theta = 45 deg, which is the same trough the
    #  power-balance figure marks.  Drawn as +sin it peaked there instead.
    #  Size, from the 274 uF the output-bank figure uses for the two-stage
    #  case: dV_pp = P / (w_l C V) - about a twentieth of the bus, not the
    #  third of it that was drawn.
    import figs as _F
    _FL, _CB, _VB = 47.0, 274e-6, 400.0
    _rip = _F.POUT / (2 * np.pi * _FL * _CB * _VB) / _VB
    DC, _A = 0.62, 0.16            # drawn far larger than life, and said so
    bus = DC - _A * np.sin(12 * np.pi * t)
    out = DC - 0.30 * _A * np.sin(12 * np.pi * t)
    nodes = [(0.85, 'mains\nvoltage  ·  current', [(v, NAVY), (0.72 * v, GRN)]),
             (5.5, 'rectified', [(np.abs(v) * 0.95, NAVY)]),
             (15.5, '400 V dc\n2f$_l$ ripple, %.0f %% pk-pk' % (100 * _rip),
              [(bus, MAG)]),
             (20.2, 'hf square', [(0.82 * np.sign(np.sin(34 * np.pi * t)),
                                   CYA)]),
             (29.05, 'dc out\nregulated, 2f$_l$ residue', [(out, MAG)])]
    x0, x1 = ax.get_xlim()
    for x, nm, traces in nodes:
        fx = 0.03 + (x - x0) / (x1 - x0) * 0.94
        a = fig.add_axes([fx - 0.056, 0.60, 0.112, 0.25])
        a.axhline(0, color=GREY, lw=0.7, zorder=1)
        for y, c in traces:
            #  a dc node gets its mean drawn too: without it the ripple has
            #  nothing to be read against and looks like the whole signal
            if y.min() > 0.05:
                a.axhline(float(np.mean(y)), color=GREY, lw=0.7, ls=(0, (3, 3)),
                          zorder=1)
            a.plot(t, y, color=c, lw=1.7)
        a.set_xlim(0, 1)
        a.set_ylim(-1.15, 1.15)
        a.set_xticks([])
        a.set_yticks([])
        for sp in a.spines.values():
            sp.set_color(GREY)
            sp.set_linewidth(0.8)
        a.set_title(nm, fontsize=10.5, color=GREY, pad=4)
        S.dot(ax, x, YW)
        fig.add_artist(ConnectionPatch(
            xyA=(0.5, 0.0), coordsA='axes fraction', axesA=a,
            xyB=(x, YW), coordsB='data', axesB=ax,
            color=GREY, lw=1.0, ls=(0, (2, 3)), zorder=1))

    foot(fig, 'Correction happens in the first block, and the LLC works from '
              'a dc bus that is already regulated. Two controllers, two sets '
              'of switches, and a 400 V electrolytic between them. The ripple '
              'on the two dc nodes is drawn several times larger than life, '
              'against the dashed mean; its trough sits at \u03b8 = 45\u00b0, '
              'where the mains has delivered one quarter cycle less energy '
              'than the load has taken.')
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
    #  The switches commutate a rectifier that is still conducting, and an
    #  inductor current cannot step: i_D falls to zero across the dead time
    #  (a ramp here; the reverse voltage on L_r sets the real slope) and
    #  i_Lr follows it down onto i_Lm instead of jumping there.
    io_end = np.sin(np.pi * t1 / tres)
    io = np.where(h <= t1, np.sin(np.pi * np.clip(h, 0, t1) / tres),
                  io_end * np.clip((H - h) / (H - t1), 0.0, 1.0))
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
    fig = plt.figure(figsize=(9.35, 6.53))
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
    #  ... and again from the moment its own node has swung back (8): the
    #  body diode takes the current the gate then closes on.  That stretch
    #  is the same negative current the trace starts with, one period
    #  earlier; drawn at zero it contradicted its own first millimetre.
    s1 = np.where((t < e[2]) | (t >= e[7]), ilr / m, 0.0)
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
    fig = plt.figure(figsize=(9.35, 5.28))
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
    """The same converter either side of the boundary, and how it shows.

    The third row is the one that matters to a device: the drain current of
    the switch that is closing.  The gain curve and the tank current say
    WHICH side the converter is on; only the switch current says what that
    costs, and on the capacitive side it is a reverse-recovery spike many
    times the tank current, drawn into a device that is still standing at
    the full rail.  The shape follows ON Semiconductor AN-4151 figure 12.
    """
    fig = plt.figure(figsize=(9.2, 8.4))
    lam, q = 0.55, 0.766

    ax = fig.add_axes([0.095, 0.712, 0.845, 0.252])
    fn = np.linspace(0.34, 2.4, 1200)
    g = np.array([M(f, q, lam) for f in fn])
    edge = zvs_edge(q, lam)
    pk = fn[int(np.argmax(g))]
    ax.plot(fn, g, color=NAVY, lw=2.4)
    ax.axvspan(fn[0], edge, color=MAG, alpha=0.10, lw=0)
    ax.axvspan(edge, fn[-1], color=GRN, alpha=0.11, lw=0)
    ax.axvline(edge, color=GREY, lw=1.6, ls=(0, (5, 3)))
    ax.plot([pk], [g.max()], marker='*', ms=15, color=NAVY, zorder=5)
    _call(ax, (pk, g.max()), (pk + 0.34, g.max() - 0.06),
          'gain peak - NOT the boundary', color=NAVY, size=10.5)
    ax.text(edge + 0.03, ax.get_ylim()[0] + 0.07,
            'boundary: arg Z$_{in}$ = 0', fontsize=10.5, color=GREY,
            ha='left')
    ax.text((fn[0] + edge) / 2.0, g.max() * 0.32, 'capacitive\nhard '
            'switching', ha='center', fontsize=12, color=MAG,
            path_effects=HALO, zorder=9)
    ax.text(edge + 0.62, g.max() * 0.32, 'inductive\nZVS', ha='center',
            fontsize=12, color=GRN, path_effects=HALO, zorder=9)
    ax.set_xlabel('f$_{sw}$ / f$_r$', fontsize=11, color=NAVY)
    ax.set_ylabel('M', fontsize=11, color=NAVY)
    ax.tick_params(labelsize=10, colors=GREY)
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
    IHI, ILOW = 2.75, -1.55            # one scale for BOTH drain currents:
    for c, (fnx, nm, col) in enumerate(((edge * 0.80, 'capacitive', MAG),
                                        (edge * 1.45, 'inductive', GRN))):
        phi = phase(fnx, q, lam)               # arg Z_in, radians
        xc = 0.095 + c * 0.462 + 0.188
        fig.text(xc, 0.648, nm, ha='center',
                 fontsize=13, color=col, fontweight='bold')
        fig.text(xc, 0.626,
                 'f$_{sw}$/f$_r$ = %.2f,   arg Z$_{in}$ = %+.0f$\degree$'
                 % (fnx, np.degrees(phi)), ha='center', fontsize=10.5,
                 color=GREY)
        tt = np.linspace(0, 2, 4000)
        vd = np.where((tt % 1.0) < 0.5, 1.0, -1.0)
        cur = np.sin(2 * np.pi * tt - phi)
        on = (tt % 1.0) < 0.5                  # S1 conducting
        ids = np.where(on, cur, 0.0)
        hard = np.sin(-phi) > 0
        if hard:
            #  Reverse recovery of the OPPOSITE body diode, swept out
            #  through the device that is closing. Height and width are
            #  indicative - what is not indicative is that it exists here
            #  and does not exist in the other column.
            for k in (0.0, 1.0):
                ids = ids + np.where(on & (tt >= k),
                                     2.35 * np.exp(-(tt - k) / 0.009), 0.0)
            ids = np.clip(ids, ILOW, IHI)
        y = 0.600
        rows = (('v$_d$', 0.092, -1.45, 1.45),
                ('i$_{Lr}$', 0.092, -1.45, 1.45),
                ('i$_{DS}$', 0.118, ILOW, IHI))
        for nmx, h, lo, hi in rows:
            y -= h + 0.034
            a = _wave_ax(fig, [0.095 + c * 0.462, y, 0.376, h], 0, 2,
                         lo, hi, nmx if c == 0 else None)
            if nmx.startswith('v$_d$'):
                a.plot(tt, vd, color=NAVY, lw=1.9)
            elif nmx.startswith('i$_{Lr}$'):
                a.plot(tt, cur, color=col, lw=2.1)
                for k in (0.0, 1.0):
                    a.plot([k], [np.sin(-phi)], 'o', color=col, ms=8,
                           zorder=6)
            else:
                a.fill_between(tt, 0, ids, where=(ids < 0), color=GRN,
                               alpha=0.30, lw=0)
                a.plot(tt, ids, color=NAVY, lw=2.0)
                if hard:
                    _call(a, (0.012, 2.30), (0.16, 2.05),
                          'reverse recovery of the other\nbody diode',
                          color=MAG, size=10, ha='left')
                else:
                    _call(a, (0.10, float(np.interp(0.10, tt, ids))),
                          (0.30, 1.45),
                          'negative first: the body diode\nof this very switch',
                          color=GRN, size=10, ha='left')
            for k in (0.0, 1.0):
                a.axvline(k, color=GREY, lw=0.8, ls=(0, (2, 3)))
        tail = ('The current was ALREADY flowing the other way, so the\n'
                'diode of the switch about to close is conducting and\n'
                'has to be recovered. Hard switching, and the spike is\n'
                'dissipated in the closing device.'
                if hard else
                'The current had already swung the node over, so this\n'
                'switch closes across its own conducting body diode.\n'
                'Zero volts, no recovery, no spike.')
        fig.text(xc, y - 0.026, tail, ha='center',
                 va='top', fontsize=10.5, color=col, linespacing=1.5)

    foot(fig, 'The boundary is where the tank input impedance phase crosses '
              'zero, and that is a little above the peak of the gain curve - '
              'so quoting the peak reports a band of hard switching as '
              'inductive. The shaded regions come from l6790.zvs_edge, which '
              'solves the phase for zero in closed form; the two drain '
              'currents are drawn to one scale. i$_{DS}$ is the drain '
              'current of the device that is closing.')
    save(fig, 'an_cap_ind')


# ------------------------------------------- 11b  why the diode recovers
def _bd(x, y, h, dx=0.80):
    """The body-diode detour round one device, source node to drain node."""
    return [(x, y - h / 2), (x + dx, y - h / 2), (x + dx, y + h / 2),
            (x, y + h / 2)]


def an_recovery(save, foot):
    """The two commutations, drawn - why one recovers a diode and one does not.

    The gain curve says which side of the boundary the converter is on and
    the waveforms say what the switch current looks like, but neither says
    WHY the capacitive side destroys devices.  It is one sentence and it
    needs a circuit: on the capacitive side the incoming switch closes onto
    a body diode that is still conducting, and a diode does not block until
    its stored charge has been swept out.  For that moment the rail is
    short-circuited through both devices.
    """
    RED = '#C21807'
    HI, LO, XL = 6.0, 0.0, 3.0
    YM, HS = 3.0, 1.8
    YS1, YS2 = 4.5, 1.5
    XB0, XB1, XR = 5.3, 7.5, 8.6
    fig = plt.figure(figsize=(9.2, 5.3))

    for k, cap in enumerate((True, False)):
        ax = _ax(fig, [0.030 + k * 0.492, 0.300, 0.450, 0.610],
                 -0.6, 9.4, -0.9, 7.0)
        #  rails.  The top one stops at the leg, so it has no loose end;
        #  the bottom one carries the tank return home.
        S.wire(ax, [(0.25, HI), (XL, HI)])
        S.wire(ax, [(0.25, LO), (XR, LO)])
        S.dot(ax, 0.25, HI)
        S.dot(ax, 0.25, LO)
        S.label(ax, 0.25, HI + 0.52, 'V$_{in}$', size=11)
        S.label(ax, 0.25, LO - 0.52, '0', size=11)
        #  the leg
        S.wire(ax, [(XL, HI), (XL, YS1 + HS / 2)])
        S.wire(ax, [(XL, YS1 - HS / 2), (XL, YS2 + HS / 2)])
        S.wire(ax, [(XL, YS2 - HS / 2), (XL, LO)])
        S.dot(ax, XL, LO)
        X.mosfet(ax, XL, YS1, 'S1', 'on' if cap else 'diode', h=HS,
                 gate=0.95, coss=False, size=11)
        X.mosfet(ax, XL, YS2, 'S2', 'diode' if cap else 'off', h=HS,
                 gate=0.95, coss=False, size=11)
        #  the tank, as a block: this figure is about the leg
        S.wire(ax, [(XL, YM), (XB0, YM)])
        S.wire(ax, [(XB1, YM), (XR, YM), (XR, LO)])
        S.dot(ax, XL, YM)
        ax.add_patch(Rectangle((XB0, YM - 0.70), XB1 - XB0, 1.40, fc=LT,
                               ec=GREY, lw=1.3, zorder=4))
        X.txt(ax, (XB0 + XB1) / 2, YM, 'resonant\ntank', size=10.5, z=5)

        if cap:
            ax.set_title('CAPACITIVE — S1 closes onto a conducting diode',
                         fontsize=11.5, color=MAG, pad=6)
            #  vertices at the device edges, so a head can be put on a
            #  clear stretch of leg instead of inside a symbol
            X.path(ax, [(0.25, HI), (XL, HI), (XL, YS1 + HS / 2),
                        (XL, YS1 - HS / 2), (XL, YS2 + HS / 2)]
                   + _bd(XL, YS2, HS)[::-1] + [(XL, LO), (0.25, LO)],
                   heads=((2, 0.50), (4, 0.78), (7, 0.50), (9, 0.50)),
                   color=RED)
            #  the tank current is what put that diode into conduction, so
            #  it is named - but not highlighted, or it would run along the
            #  same leg as the fault current and neither would be readable
            ax.annotate('', xy=(XB0 - 0.25, YM), xytext=(XL + 0.55, YM),
                        arrowprops=dict(arrowstyle='-|>', color=MAG, lw=2.0))
            X.txt(ax, (XL + XB0) / 2 + 0.45, YM + 0.60,
                  'i$_{Lr}$ > 0', size=10.5, color=MAG, halo=True, z=9)
            _call(ax, (XL + 0.80, YS2), (XL + 1.35, YS2 - 1.25),
                  'still carrying,\nstill charged', color=GRN, size=10.5)
        else:
            ax.set_title('INDUCTIVE — the node is already over',
                         fontsize=11.5, color=GRN, pad=6)
            X.path(ax, [(0.25, LO), (XR, LO), (XR, YM), (XB1, YM),
                        (XB0, YM), (XL, YM)]
                   + _bd(XL, YS1, HS) + [(XL, HI), (0.25, HI)],
                   heads=((1, 0.55), (5, 0.55), (8, 0.50), (10, 0.45)))
            X.txt(ax, (XL + XB0) / 2 + 0.45, YM + 0.60,
                  'i$_{Lr}$ < 0', size=10.5, color=MAG, halo=True, z=9)
            _call(ax, (XL + 0.80, YS1), (XL + 1.35, YS1 + 1.15),
                  'the body diode of S1 itself —\nV$_{ds}$ = 0 before the gate rises', color=GRN,
                  size=10.5)

    fig.text(0.255, 0.225,
             'S2 was carrying the tank current in its body diode. A diode\n'
             'cannot block until its stored charge has been swept out, so\n'
             'the moment S1 closes the rail is short-circuited through both\n'
             'devices. Only stray inductance limits the spike, and S1\n'
             'dissipates it at full V$_{ds}$.',
             ha='center', va='top', fontsize=10.5, color=MAG,
             linespacing=1.5)
    fig.text(0.748, 0.225,
             'The tank current ran the other way. Through the dead time it\n'
             'charged the node to V$_{in}$, and it now flows in the body diode\n'
             'of S1 itself. S1 closes across zero volts: nothing to\n'
             'recover, no spike, no turn-on loss. That is the only\n'
             'difference between the two sides of the boundary.',
             ha='center', va='top', fontsize=10.5, color=GRN,
             linespacing=1.5)
    foot(fig, 'The same leg, one switching instant, either side of the '
              'boundary. The mechanism is the reason the capacitive region '
              'is not merely inefficient but destructive, and it is why the '
              'oscillator floor exists (after ON Semiconductor AN-4151).')
    save(fig, 'an_recovery')


# ------------------------------------------------------- 10  load shifts it
def an_loadshift(save, foot):
    """The boundary is not fixed: loading the converter moves it."""
    fig = plt.figure(figsize=(9.35, 5.12))
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
    fig = plt.figure(figsize=(9.35, 5.39))
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


# --------------------------------------------- the core, in cross-section
def an_core_section(save, foot):
    """The chosen core in section, and the winding that has to fit in it.

    Proportions are schematic - the datasheet gives A_e, A_min, A_N and
    l_N but not the window's width and height separately, so nothing here
    is drawn to a dimension that was not published.  Every number written
    on the drawing is either from the datasheet or computed from the
    design by cores.py.

    Stacked, not side by side: five zone names do not fit inside a window
    drawn a third of a panel wide, and putting them there is what made the
    first version unreadable.  Here they sit clear of the core with
    leaders into it.
    """
    import cores as _C
    import an_pdf as _A
    V = _A.V
    NAME = 'PQ 40/40'
    R = _C.CORES[NAME]
    bpk = _C.flux(V, R['Ae'])
    g = _C.gap(V, R['Ae'])
    bare = _C.window(V)
    rows = _C.copper(V)

    CORE, GOLD = '#9aa3ad', '#8a6d00'
    fig = plt.figure(figsize=(9.2, 6.6))

    # ---------------------------------------------------- section
    ax = _ax(fig, [0.035, 0.475, 0.930, 0.455], -8.2, 16.8, -0.9, 9.9)
    ax.set_title('%s in section  —  where each winding goes' % NAME,
                 fontsize=11.5, color=NAVY, pad=6)
    #  Each outer leg carries half the centre leg's flux, so it is half its
    #  width.  Drawn the same width they read as three equal legs, which is
    #  not what the flux does.
    YB, YT, HW = 1.6, 7.4, 1.0          # window floor, ceiling, OUTER leg
    XL, XR, XC0, XC1 = 0.0, 12.0, 5.0, 7.0
    YG0, YG1 = 4.25, 4.75               # the centre-leg gap
    for rc in ((XL, YT, XR - XL, 1.6), (XL, 0.0, XR - XL, YB),
               (XL, YB, HW, YT - YB), (XR - HW, YB, HW, YT - YB),
               (XC0, YG1, XC1 - XC0, YT - YG1),
               (XC0, YB, XC1 - XC0, YG0 - YB)):
        ax.add_patch(Rectangle(rc[:2], rc[2], rc[3], fc=CORE, ec=GREY,
                               lw=1.2, zorder=3))
    ZONES = ((6.85, YT, LT, 'margin tape', GREY),
             (5.25, 6.85, NAVY, 'PRIMARY  %d turns' % V['Np'], NAVY),
             (4.45, 5.25, None, 'separation — sets L$_{short}$',
              GOLD),
             (2.10, 4.45, MAG, 'SECONDARY  %d + %d turns'
              % (V['Ns'], V['Ns']), MAG),
             (YB, 2.10, LT, 'margin tape', GREY))
    for x0, x1 in ((HW, XC0), (XC1, XR - HW)):
        for y0, y1, col, _t, _c in ZONES:
            if col is None:
                continue
            hatch = '///' if col is LT else None
            ax.add_patch(Rectangle((x0 + 0.10, y0), x1 - x0 - 0.20, y1 - y0,
                                   fc=col, ec=GREY, lw=0.9, zorder=4,
                                   alpha=0.9 if hatch else 0.25, hatch=hatch))
    #  names clear of the core, leaders into the left window
    for y0, y1, _col, t, c in ZONES:
        ax.annotate(t, xy=(HW + 0.55, (y0 + y1) / 2),
                    xytext=(-8.0, (y0 + y1) / 2), fontsize=10, color=c,
                    ha='left', va='center', zorder=9,
                    arrowprops=dict(arrowstyle='-', color=c, lw=1.0,
                                    shrinkA=3, shrinkB=2))
    #  clear of the core on the right, like the zone names on the left:
    #  placed inside it they landed on the far window's own windings
    _call(ax, (XC1 - 0.25, 6.6), (12.5, 8.6), 'A$_e$ = %.0f mm$^2$' % R['Ae'],
          color=NAVY, size=10, ha='left')
    _call(ax, (XR - HW - 0.35, 5.95), (12.5, 6.4),
          'window A$_N$ = %.0f mm$^2$' % R['AN'], color=GREY, size=10,
          ha='left')
    _call(ax, (XC1 - 0.25, (YG0 + YG1) / 2), (12.5, 3.3),
          'centre-leg gap:\nground to A$_L$,\nnot to a dimension',
          color=GOLD, size=10, ha='left')

    # ---------------------------------------------- the winding, unrolled
    ax2 = fig.add_axes([0.075, 0.165, 0.855, 0.250])
    ax2.set_title('the same winding, unrolled along the bobbin',
                  fontsize=11.5, color=NAVY, pad=6)
    ax2.set_xlim(-0.3, 10.3)
    ax2.set_ylim(-2.05, 3.60)
    ax2.set_xticks([])
    ax2.set_yticks([])
    for sp in ax2.spines.values():
        sp.set_visible(False)
    #  deep enough that the name clears its own outline: at 0.45 the text
    #  sat on the top and bottom edges of the bar
    ax2.add_patch(Rectangle((0, -0.72), 10, 0.72, fc=CORE, ec=GREY, lw=1.1))
    X.txt(ax2, 5.0, -0.36, 'bobbin', size=10, color='white', z=5)
    for x0, x1 in ((0.0, 1.00), (9.00, 10.0)):
        ax2.add_patch(Rectangle((x0, 0), x1 - x0, 2.4, fc=LT, ec=GREY,
                                lw=0.9, hatch='///'))
    np_, ns_ = V['Np'], V['Ns']
    for k in range(np_):
        cx = 1.32 + 0.60 * (k % 3) + (0.30 if k >= 3 else 0)
        cy = 0.40 + 0.70 * (k // 3)
        ax2.add_patch(Circle((cx, cy), 0.28, fc=NAVY, ec=NAVY, lw=1.0,
                             alpha=0.30))
    #  one text, two lines - two texts one line apart are reported as
    #  overlapping each other, and they are
    X.txt(ax2, 1.92, 1.92, 'primary  %d turns\nLitz, %.2f mm$^2$'
          % (np_, rows[0][3]), size=10, color=NAVY)
    ax2.add_patch(Rectangle((3.55, 0), 1.45, 2.4, fc='none', ec=GOLD,
                            lw=1.6, ls=(0, (4, 3))))
    X.txt(ax2, 4.28, 2.92, 'separation\nsets L$_{short}$', size=10,
          color=GOLD, z=5)
    for k in range(2):
        for j in range(ns_):
            ax2.add_patch(Rectangle((5.35, 0.16 + 0.29 * (j + ns_ * k)), 3.40,
                                    0.19, fc=MAG, ec=MAG, lw=0.8, alpha=0.35))
    X.txt(ax2, 7.05, 1.92, 'secondary  %d + %d turns\nfoil, %.2f mm$^2$ each'
          % (ns_, ns_, rows[1][3]), size=10, color=MAG)
    ax2.annotate('', xy=(0, -1.28), xytext=(10, -1.28),
                 arrowprops=dict(arrowstyle='<->', color=GREY, lw=1.3))
    X.txt(ax2, 5.0, -1.70, 'winding width  —  a margin at each end for '
          'reinforced isolation', size=10, color=GREY)

    foot(fig, 'Schematic section: the datasheet gives A_e, A_min, A_N and '
              'l_N but not the window width and height separately, so no '
              'proportion here is drawn to a published dimension. What is '
              'from the datasheet or computed: A_e %.0f mm2, A_min %.0f '
              'mm2, A_N %.0f mm2, l_N %.0f mm, B_pk %.0f mT (%.0f mT at '
              'A_min), first-estimate gap %.2f mm, bare copper %.1f mm2 per '
              'unit.'
              % (R['Ae'], R['Amin'], R['AN'], R['lN'], bpk,
                 bpk * R['Ae'] / R['Amin'], g, bare))
    save(fig, 'an_core_section')


FIGS = {'an_rac': an_rac, 'an_integrated': an_integrated,
        'an_pfc_cap': an_pfc_cap, 'an_pfc_boost': an_pfc_boost,
        'an_pfc_ccm': an_pfc_ccm, 'an_two_stage': an_two_stage,
        'an_llc_waves': an_llc_waves, 'an_three_cases': an_three_cases,
        'an_cap_ind': an_cap_ind, 'an_loadshift': an_loadshift,
        'an_peakgain': an_peakgain, 'an_recovery': an_recovery,
        'an_core_section': an_core_section}
