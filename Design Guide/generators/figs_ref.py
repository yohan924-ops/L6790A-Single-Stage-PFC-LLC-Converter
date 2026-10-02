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
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle
from matplotlib.lines import Line2D
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


def _ihead(ax, x, y, way, name, col, at, ha='center', size=12):
    """A current's reference direction: an arrowhead ON its wire, named.

    Every current a waveform row plots has to be findable on the circuit
    above it, with its positive direction (2026-09-23, user: "which one is
    i_S1?").  The head sits on the conductor itself, so it cannot be read
    as belonging to the wire next to it.  `way` is 'r', 'l', 'u' or 'd'.
    """
    dx, dy = {'r': (1, 0), 'l': (-1, 0), 'u': (0, 1), 'd': (0, -1)}[way]
    ax.add_patch(FancyArrowPatch((x - 0.13 * dx, y - 0.13 * dy),
                                 (x + 0.13 * dx, y + 0.13 * dy),
                                 arrowstyle='-|>', mutation_scale=16,
                                 color=col, lw=2.2, zorder=8, shrinkA=0,
                                 shrinkB=0))
    ax.text(at[0], at[1], name, ha=ha, va='center', fontsize=size,
            color=col, zorder=9, path_effects=HALO)


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
    #  the kit's diode is 0.56 tall at scale 1 and its triangle 0.62 of that
    s = 0.62 * 0.56 * X.scale(ax) if s is None else s
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


def _bridge(ax, xm, ym, w=1.50, h=1.50, names=None, size=9.5):
    """A diode bridge as a diamond.  -> (ac_left, ac_right, plus, minus)

    Drawn as two columns it needs one of the ac leads to cross the other
    column to reach its node, and a crossing in a four-device figure is a
    crossing too many.  On the diamond every terminal is a corner.

    All four conduct TOWARDS the + corner: that is what a bridge is, and
    it is the one thing in this drawing a reader will check.  The diamond
    is square, so its arms are true 45-degree wires: at 1.55 by 1.35 they
    were 4 degrees off, which figcheck's grid test reported.

    No designators by default (2026-09-23): D1-D4 here named the input
    bridge with the names the note gives the two secondary rectifiers, and
    D_3 is also the third-harmonic ratio.  The text never refers to one
    bridge diode on its own, so the bridge carries no names.
    """
    L, Rt, P, Mn = (xm - w, ym), (xm + w, ym), (xm, ym + h), (xm, ym - h)
    #  Offsets grew with the figures: once a drawing is narrower the same
    #  point size covers more data units, and 0.48/0.34 put each name back
    #  on its own arm.
    nms = names or (None,) * 4
    for a, b, nm, dx, dy in ((L, P, nms[0], -0.62, 0.44),
                             (Rt, P, nms[1], 0.62, 0.44),
                             (Mn, L, nms[2], -0.62, -0.44),
                             #  the bottom-right arm has the far ac corner's
                             #  riser just outside it, so this one name goes
                             #  BELOW its arm instead of outboard of it
                             (Mn, Rt, nms[3], 0.22, -0.80)):
        S.wire(ax, [a, b])
        _diode_along(ax, a, b)
        mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
        if names:
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
    S.label(ax, 0.06, 0.76, 'i$_{RI}$', size=11, color=MAG, ha='right')
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
               gap=0.52, ls=('N$_s$', 'N$_s$'), tap_dot=False)
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
    S.shunt(ax, 11.1, 1.5, -1.4, 'cap', 'C$_{out}$', frac=0.34)
    S.dot(ax, 11.1, 1.5)
    S.dot(ax, 11.1, -1.4)
    S.shunt(ax, 12.5, 1.5, -1.4, 'res', 'R$_L$', frac=0.52)
    S.label(ax, 12.98, 1.18, '+', size=12, color=GREY)
    S.label(ax, 12.98, -1.08, '$-$', size=12, color=GREY)
    S.label(ax, 13.4, 0.30, 'V$_{out}$', size=11.5, ha='left')
    S.label(ax, 13.4, -0.22, 'stiff', size=10, ha='left', color=GREY)

    #  What exactly is being replaced.  Without the box the reader has to
    #  guess how far to the right the substitution reaches - and the two
    #  candidate answers (the rectifier alone, or the transformer with it)
    #  differ by the n^2 in R_ac, which is the whole point of the figure.
    S.shade(ax, 2.95, -1.95, 14.15, 4.02,
            'everything the tank drives - transformer, rectifier, '
            'C$_{out}$ and load', color=MAG, alpha=0.07, tdy=0.30)

    ax2 = _ax(fig, [0.655, 0.34, 0.335, 0.56], -6.6, 3.6, -0.6, 4.6)
    #  One resistor, by itself.  The rails the first version ran either
    #  side of it led nowhere and read as a bus with a part hung on it;
    #  the terminal dots that replaced them marked nothing three wires
    #  meet at, which is what a dot is for.
    S.res(ax2, 1.5, 2.0, None, horiz=False)
    S.label(ax2, 2.0, 2.0, 'R$_{ac}$', size=12, ha='left')
    S.label(ax2, 1.5, 4.15, 'one resistor', size=10.5, color=MAG)
    #  The arrow stops at the resistor, not a body-length short of it:
    #  it has to be unambiguous which symbol the box becomes.
    S.arrow(ax2, (-5.2, 2.0), (0.55, 2.0), None, color=MAG)
    S.label(ax2, -2.3, 2.72, 'all of it becomes', size=10.5, color=MAG)

    # the two waveforms the argument rests on
    t = np.linspace(0, 2, 600)
    aw = _wave_ax(fig, [0.07, 0.115, 0.36, 0.145], 0, 2, -1.4, 1.4,
                  'i$_{RI}$')
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
    source(ax, S.sqsrc, 'v$_d$')        # the bridge output of Figure 1
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
    #  v_RI is the rectifier input referred to the primary (Figure an_rac
    #  draws it across the primary); what the secondary itself carries is
    #  v_RI / n.  Both panels said v_RI and R_ac on the SECONDARY side of
    #  an n : 1, one symbol for two values (2026-09-23)
    S.label(ax, 10.45, 1.75, 'v$_{RI}$/n', size=11)

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
    source(ax2, S.acsrc, 'v$_d^F$')
    #  L_m, as the caption and the text call it: 'L_p - L_r' used an L_p
    #  that is the flyback's primary inductance everywhere else (round 63)
    tank(ax2, 4.2, 'L$_r$', 1.05, 'L$_m$')
    t2 = X.xfmr(ax2, 7.5, 1.75, hp=3.3, hs=3.3, gap=0.52)
    S.wire(ax2, [(5.1, YT_), t2['p_top']])
    S.wire(ax2, [t2['p_bot'], (XSRC, YB_)])
    #  The one ideal transformer left after the referral has ratio n : 1,
    #  with n = n_T / M_v.  Written '1 : M_v' it read as a step-up of M_v,
    #  which is neither the wound ratio nor the model one.
    S.label(ax2, 7.5, -0.48, 'n : 1   ideal,   n = n$_T$ / $\\sqrt{1+\\lambda}$',
            size=10.5, color=GREY)
    S.wire(ax2, [t2['s_top'], (9.9, YT_)])
    S.wire(ax2, [t2['s_bot'], (9.9, YB_)])
    S.shunt(ax2, 9.9, YT_, YB_, 'res', 'R$_{ac}$/n$^2$')
    xv = 11.3
    ax2.add_patch(FancyArrowPatch((xv, YB_), (xv, YT_), arrowstyle='<|-|>',
                                  mutation_scale=12, color=GREY, lw=1.4,
                                  zorder=4, shrinkA=0, shrinkB=0))
    S.label(ax2, xv, YT_ + 0.36, '+', size=12, color=GREY)
    S.label(ax2, xv, YB_ - 0.36, '$-$', size=12, color=GREY)
    #  the fundamental of the v_RI above; 'V_RO' was a name used nowhere
    S.label(ax2, xv + 0.25, 1.75, 'v$_{RI}^F$/n', size=11, ha='left')

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
             'switch ON - the inductor charges from the line'),
            ([0.525, 0.10, 0.455, 0.80], False,
             'switch OFF - the inductor delivers to C, in series with the '
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

    foot(fig, 'The switch is modulated so the average inductor current '
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
    ax.plot(t, cur, color=MAG, lw=1.2, label='inductor current')
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
    foot(fig, 'Continuous conduction mode: the inductor current never falls '
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
    S.label(ax, -0.1, YW, 'v$_{ac}$', size=12, ha='right', weight='bold')
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
    ratio = 0.70                       # f_sw / f_r of the drawn period
    t, e, ilm, ilr, io, _ = _cycle(ratio, lam, 18.32, 12.41)

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

    axs[2].set_ylim(-0.12, 1.62)
    axs[2].plot(t, io / max(io.max(), 1e-9), color=GRN, lw=1.9)
    #  which rectifier each hump is - D1 while S1 and S4 are on, D2 in the
    #  other half (Figure 1 marks both)
    for x0, x1, nm in ((e[0], e[1], 'i$_{D1}$'), (e[4], e[5], 'i$_{D2}$')):
        axs[2].text((x0 + x1) / 2.0, 0.40, nm, ha='center', va='center',
                    fontsize=10, color=GRN, path_effects=HALO, zorder=9)

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

    #  Where f_r and f_sw are on the time axis (2026-09-23, user: "which
    #  part is f_r and which is f_sw?").  The secondary conducts for the
    #  resonant half period T_r/2 - from S1 turn-on (e[0]) to where i_Lr
    #  rejoins i_Lm (e[1]); the gate pattern repeats every T_sw, S2 taking
    #  over at T_sw/2 (e[4]).  Below resonance T_r/2 < T_sw/2, and the
    #  difference is the freewheeling interval plus the dead time.
    def _dim(ax, x0, x1, y, txt, col, dy):
        ax.plot([x0, x1], [y, y], color=col, lw=1.3, zorder=6)
        for xv in (x0, x1):
            ax.plot([xv, xv], [y - dy, y + dy], color=col, lw=1.3, zorder=6)
        ax.text((x0 + x1) / 2.0, y + 1.6 * dy, txt, ha='center',
                va='bottom', fontsize=10, color=col, path_effects=HALO,
                zorder=9)

    _dim(axs[2], e[0], e[1], 1.13, 'T$_r$/2 = 1/(2f$_r$): the secondary '
         'conducts', GRN, 0.07)
    dim = fig.add_axes([0.105, 0.035, 0.855, 0.125])
    dim.set_xlim(0, 1)
    dim.set_ylim(0, 1)
    dim.axis('off')
    _dim(dim, e[0], e[4], 0.62, 'T$_{sw}$/2 = 1/(2f$_{sw}$)', NAVY, 0.08)
    _dim(dim, e[0], e[8], 0.12, 'T$_{sw}$ = 1/f$_{sw}$  (one switching '
         'period;  here f$_{sw}$ = %.1f f$_r$)' % ratio, NAVY, 0.08)

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
    #  The waveform block keeps its old proportions; the gain panel under
    #  it answers where each column sits on M(f_n).  Every y below is laid
    #  out on the old 5.28 in canvas and mapped through Y() / H().
    H0, H1 = 5.28, 8.05
    fig = plt.figure(figsize=(9.35, H1))
    def Y(y):
        return 1.0 - (1.0 - y) * H0 / H1
    def H(h):
        return h * H0 / H1
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
    #  i_D gets the tallest row: the callout about reverse recovery
    #  lives above its trace and needs the room.
    hgt = [0.115, 0.145, 0.190, 0.215]
    for c, (ratio, ttl, sub) in enumerate(cases):
        t, e, ilm, ilr, io, trunc = _cycle(ratio, lam, 18.32, 12.41,
                                          td=td)
        x0 = 0.055 + c * 0.323
        fig.text(x0 + 0.128, Y(0.965), ttl, ha='center', fontsize=12,
                 color=NAVY, fontweight='bold')
        fig.text(x0 + 0.128, Y(0.936), sub, ha='center', fontsize=10.5,
                 color=GREY)
        y = 0.915
        axs = []
        for nm, h in zip(names, hgt):
            y -= h + 0.028
            a = _wave_ax(fig, [x0, Y(y), 0.256, H(h)], 0, 1, -1.25, 1.25,
                         nm if c == 0 else None)
            axs.append(a)
        T = t
        g1 = np.where((T >= e[0]) & (T < e[2]), 1.0, 0.0)
        g2 = np.where((T >= e[4]) & (T < e[6]), 1.0, 0.0)
        axs[0].set_ylim(-0.25, 2.5)
        for base, g in ((0.0, g1), (1.3, g2)):
            axs[0].fill_between(T, base, base + g * 0.9, color=YEL, lw=0)
            axs[0].plot(T, base + g * 0.9, color=NAVY, lw=1.4)
        #  which pair each gate row is, as in Figure 2
        axs[0].text(e[2] / 2.0, 0.45, 'S$_1$,S$_4$', ha='center',
                    va='center', fontsize=9.6, color=NAVY, path_effects=HALO,
                    zorder=9)
        axs[0].text((e[4] + e[6]) / 2.0, 1.75, 'S$_2$,S$_3$', ha='center',
                    va='center', fontsize=9.6, color=NAVY, path_effects=HALO,
                    zorder=9)
        axs[1].plot(T, F._step(T, e, -1.0, 1.0), color=NAVY, lw=1.9)
        m = max(abs(ilr).max(), 1e-9)
        axs[2].plot(T, ilr / m, color=MAG, lw=1.9)
        axs[2].plot(T, ilm / m, color=CYA, lw=1.7, ls=(0, (4, 2.4)))
        axs[3].set_ylim(-0.12, 2.15)
        axs[3].plot(T, io / max(io.max(), 1e-9), color=GRN, lw=1.9)
        for a in axs:
            for xv in (e[1], e[2], e[4], e[5], e[6]):
                a.axvline(xv, color=GREY, lw=0.7, ls=(0, (2, 3)), zorder=0)
        #  The interval the freewheeling happens in is what changes across
        #  the three columns, so it is the thing to mark.
        if not trunc and e[2] - e[1] > 0.004:
            #  A bracket, not a double arrow: the interval is short, and a
            #  '<->' with its two heads meeting in the middle printed as a
            #  diamond that meant nothing.
            for xv in (e[1], e[2]):
                axs[3].plot([xv, xv], [1.06, 1.22], color=CYA, lw=1.4)
            axs[3].plot([e[1], e[2]], [1.14, 1.14], color=CYA, lw=1.4)
            axs[3].text((e[1] + e[2]) / 2.0, 1.32, 'freewheeling',
                        ha='center', fontsize=9.4, color=CYA,
                        path_effects=HALO, zorder=9)
        elif not trunc:
            #  The truncated column says this inside its callout instead:
            #  two separate lines up there and the callout's arrow ran
            #  through one of them whatever it was placed.
            axs[3].text(0.5, 1.24, 'no freewheeling interval left',
                        ha='center', fontsize=9.4, color=CYA,
                        path_effects=HALO, zorder=9)
        if trunc:
            #  Above the trace, in the band the taller row leaves free -
            #  set beside the cut it sat on the very half-sine it names.
            _call(axs[3], (e[1] + 0.006, io[int(e[1] * len(t)) - 2]
                           / max(io.max(), 1e-9) + 0.04),
                  (0.98, 2.10),
                  'no freewheeling interval left: still conducting\n'
                  'when the half period ends, so the switches\n'
                  'commutate it - reverse recovery',
                  color=GRN, size=9.4, ha='right', va='top')

    #  Where the three columns sit on the gain curve.  Half load, not full:
    #  at full load (Q = 0.766) f_n = 0.70 is already left of the ZVS edge
    #  (0.726), and a point in the capacitive band would say the left
    #  column is a hard-switching waveform, which it is not.  The full-load
    #  curve is drawn thin to show f_n = 1 is the one point they share.
    qh, qf = 0.766 / 2.0, 0.766
    ax = fig.add_axes([0.085, 0.085, 0.88, 0.235])
    fn = np.linspace(0.45, 1.9, 900)
    gh = np.array([M(f, qh, lam) for f in fn])
    gf = np.array([M(f, qf, lam) for f in fn])
    edge = zvs_edge(qh, lam)
    #  Same colours as the three regions of f04: capacitive, boost, buck.
    ax.axvspan(fn[0], edge, color=MAG, alpha=0.12, lw=0)
    ax.axvspan(edge, 1.0, color=GRN, alpha=0.11, lw=0)
    ax.axvspan(1.0, fn[-1], color=CYA, alpha=0.10, lw=0)
    ax.axhline(1.0, color=GREY, lw=0.8, ls=(0, (2, 3)), zorder=1)
    #  The full-load curve only from its own ZVS edge up: left of it the
    #  point would sit in a band the shading calls inductive.
    kf = fn >= zvs_edge(qf, lam)
    ax.plot(fn[kf], gf[kf], color=GREY, lw=1.3, ls=(0, (5, 3)),
            label='full load')
    ax.plot(fn, gh, color=NAVY, lw=2.3, label='half load')
    ax.set_xlim(fn[0], fn[-1])
    ax.set_ylim(0.55, 2.35)
    pts = [(0.70, 'below: M > 1, boost', (0.80, 2.05), 'left'),
           (1.00, 'at f$_r$: M = 1 at any load', (1.06, 1.62), 'left'),
           (1.30, 'above: M < 1, buck', (1.42, 1.18), 'left')]
    for f0, t, xt, ha in pts:
        m0 = M(f0, qh, lam)
        ax.plot([f0], [m0], 'o', ms=9, color=MAG, mec='white', mew=1.4,
                zorder=6)
        _call(ax, (f0, m0), xt, t, color=MAG, size=10.5, ha=ha)
    ax.text(fn[0] + 0.012, 0.62, 'capacitive at\nhalf load', fontsize=9.6, color=MAG,
            ha='left', path_effects=HALO)
    ax.legend(loc='upper right', fontsize=9.6, frameon=False)
    ax.set_xlabel('f$_{sw}$ / f$_r$', fontsize=11, color=NAVY)
    ax.set_ylabel('M', fontsize=11, color=NAVY)
    ax.tick_params(labelsize=10, colors=GREY)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    fig.text(0.525, 0.345, 'where each column sits on the gain curve',
             ha='center', fontsize=12, color=NAVY, fontweight='bold')

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
    fig = plt.figure(figsize=(9.2, 10.2))
    lam, q = 0.55, 0.766

    ax = fig.add_axes([0.095, 0.838, 0.845, 0.147])
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
        tt = np.linspace(0, 2, 4000)
        vd = np.where((tt % 1.0) < 0.5, 1.0, -1.0)
        cur = np.sin(2 * np.pi * tt - phi)
        on = (tt % 1.0) < 0.5                  # S1 conducting
        hard = np.sin(-phi) > 0
        xc = 0.095 + c * 0.462 + 0.188
        fig.text(xc, 0.795, nm, ha='center',
                 fontsize=13, color=col, fontweight='bold')
        fig.text(xc, 0.776,
                 'arg Z$_{in}$ %s 0' % ('<' if phi < 0 else '>'),
                 ha='center', fontsize=10.5,
                 color=GREY)
        #  THE CIRCUIT, above its own waveforms.  Read on their own the
        #  three traces do not say why one case recovers a diode and the
        #  other closes on a conducting one and is fine (2026-09-22,
        #  user): the answer is which device is carrying the tank current
        #  when the gate rises, and only a circuit shows that.
        cx = _ax(fig, [0.030 + c * 0.492, 0.445, COMM_W, 0.321], *COMM_XY)
        commutation(cx, hard, title=False)
        fig.text(xc, 0.428,
                 ('S1 closes onto S2\u2019s conducting body diode: the rail '
                  'is\nshorted through both until that charge is swept out'
                  if hard else
                  'the node is already over and S1\u2019s own body diode is\n'
                  'conducting, so S1 closes across zero volts'),
                 ha='center', va='top', fontsize=10.2, color=col,
                 linespacing=1.45)
        ids = np.where(on, cur, 0.0)
        if hard:
            #  Reverse recovery of the OPPOSITE body diode, swept out
            #  through the device that is closing. Height and width are
            #  indicative - what is not indicative is that it exists here
            #  and does not exist in the other column.
            for k in (0.0, 1.0):
                ids = ids + np.where(on & (tt >= k),
                                     2.35 * np.exp(-(tt - k) / 0.009), 0.0)
            ids = np.clip(ids, ILOW, IHI)
        y = 0.410
        #  The trace is the leg-1 mid-point to 0, 0 to V_in.  It was
        #  labelled v_d, which the symbol table defines as v_A - v_B and
        #  which swings +-V_in in full bridge - so it is v_A (2026-09-24).
        #  The switch current is S1's, named as in Figure 2.
        rows = (('v$_A$', 0.0735, -0.45, 1.45),
                ('i$_{Lr}$', 0.0735, -1.45, 1.45),
                ('i$_{S1}$', 0.0931, ILOW, IHI))
        for nmx, h, lo, hi in rows:
            y -= h + 0.0245
            a = _wave_ax(fig, [0.095 + c * 0.462, y, 0.376, h], 0, 2,
                         lo, hi, nmx if c == 0 else None)
            if nmx.startswith('v$_A$'):
                a.plot(tt, (vd + 1.0) / 2.0, color=NAVY, lw=1.9)
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
        tail = ('The current was ALREADY flowing the other way, so\n'
                'the diode of the switch about to close conducts and\n'
                'has to be recovered: the spike lands in that device.'
                if hard else
                'The current had already swung the node over, so this\n'
                'switch closes across its own conducting body diode.\n'
                'Zero volts, no recovery, no spike.')
        fig.text(xc, y - 0.020, tail, ha='center',
                 va='top', fontsize=10.2, color=col, linespacing=1.45)

    foot(fig, 'Top: where the boundary sits on the gain curve. Middle: the '
              'leg at the instant S1 is gated on - which device is carrying '
              'the tank current is the whole of the difference. Bottom: what '
              'that costs, in the drain current of S1. The two drain '
              'currents are drawn to one scale.')
    save(fig, 'an_cap_ind')


# ------------------------------------------- 11b  why the diode recovers
def _bd(x, y, h, dx=0.80):
    """The body-diode detour round one device, source node to drain node."""
    return [(x, y - h / 2), (x + dx, y - h / 2), (x + dx, y + h / 2),
            (x, y + h / 2)]


COMM_XY = (-0.6, 9.4, -0.9, 7.0)      # the data box a commutation panel needs
COMM_W = 0.450                        # ... at this width on a 9.2 in figure


def commutation(ax, cap, title=True):
    """One switching instant in one leg, either side of the boundary.

    Drawn here rather than inside a figure because two figures need it:
    the section that introduces capacitive and inductive has to show WHY
    one of them recovers a diode - the waveforms alone do not say it
    (2026-09-22, user) - and the section that goes through the recovery
    in detail draws the same instant.  One drawing, called twice, so the
    two cannot drift apart.

    `ax` must already be framed on COMM_XY.
    """
    RED = '#C21807'
    HI, LO, XL = 6.0, 0.0, 3.0
    YM, HS = 3.0, 1.8
    YS1, YS2 = 4.5, 1.5
    XB0, XB1, XR = 5.3, 7.5, 8.6
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
    #  the node the v_A row is measured at, against 0 (leg-1 mid-point;
    #  v_d is v_A - v_B, 2026-09-24)
    X.txt(ax, XL - 0.30, YM, 'v$_A$', size=11, weight='bold', ha='right')
    ax.add_patch(Rectangle((XB0, YM - 0.70), XB1 - XB0, 1.40, fc=LT,
                           ec=GREY, lw=1.3, zorder=4))
    X.txt(ax, (XB0 + XB1) / 2, YM, 'resonant\ntank', size=10.5, z=5)

    if cap:
        if title:
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
        if title:
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

def an_recovery(save, foot):
    """The two commutations at full size, with the argument written out."""
    fig = plt.figure(figsize=(9.2, 5.3))
    for k, cap in enumerate((True, False)):
        ax = _ax(fig, [0.030 + k * 0.492, 0.300, COMM_W, 0.610], *COMM_XY)
        commutation(ax, cap)

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
    qs = [(0.55, 'light load, Q = 0.55', CYA), (0.85, 'half load, Q = 0.85', PUR),
          (1.35, 'overload, Q = 1.35', MAG)]
    edges = []
    for q, nm, col in qs:
        g = np.array([M(f, q, lam) for f in fn])
        ax.plot(fn, g, color=col, lw=2.2, label=nm)
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
    targets = np.linspace(2.16, 1.14, len(ms))
    for mm, col, yt in zip(ms, cols, targets):
        lam = 1.0 / (mm - 1.0)                 # m = L_p / L_r = 1 + 1/lambda
        pk = np.array([max(M(f, q, lam) for f in fn) for q in qs])
        ax.plot(qs, pk, color=col, lw=2.0)
        qa = float(np.interp(-yt, -pk, qs))    # pk falls with Q
        #  ON the curve, centred, the way a contour is labelled: the line
        #  breaks under its own name.  Set beside the crossing it sat
        #  between its own curve and the next one and read as either
        #  (2026-09-23).
        ax.text(qa, yt, 'm = %g' % mm, fontsize=9.6,
                color=col, va='center', ha='center', clip_on=True,
                zorder=5, bbox=dict(boxstyle='square,pad=0.12', fc='white',
                                    ec='none'))
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
          (0.90, 1.95), 'pick a required peak gain and a Q,\n'
          'and m is decided', rad=-0.2)
    foot(fig, 'm = L_p / L_r. A single-stage converter needs a wide gain '
              'range at a Q that is not small, which is what pushes m down '
              'to about 3 - the shape of these curves is the reason the '
              'usual m = 5 to 10 will not start at low line.')
    save(fig, 'an_peakgain')


# --------------------------------------------- the core, in cross-section
FERR, FERRE, GOLD, TAPE, PLAS = '#dfe4e9', '#6f7883', '#8a6d00', '#f5e6b4', '#eef1f4'


def _mm_ax(fig, rect, cx, cy, mm_per_in):
    """An axes whose data units ARE millimetres, at a stated scale.

    The scale is set from the axes' own size on the page, so the drawing
    cannot be out of scale: there is one number, mm_per_in, and both axes
    of the plot get it.  Panels that quote different scales are detail
    views, exactly as on a real drawing, and each says so.
    """
    ax = fig.add_axes(rect)
    fw, fh = fig.get_size_inches()
    hw = rect[2] * fw * mm_per_in / 2.0
    hh = rect[3] * fh * mm_per_in / 2.0
    ax.set_xlim(cx - hw, cx + hw)
    ax.set_ylim(cy - hh, cy + hh)
    ax.set_aspect('equal')
    ax.axis('off')
    return ax


def _dimh(ax, x0, x1, y, t, ext=None, color=GREY, size=8.3, side=1):
    if ext is not None:
        for x in (x0, x1):
            ax.plot([x, x], [ext, y + 0.35 * (1 if y > ext else -1)],
                    color=color, lw=0.5, zorder=1)
    ax.annotate('', xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.8,
                                mutation_scale=8), zorder=6)
    ax.text((x0 + x1) / 2, y + side * 0.45, t, ha='center',
            va='bottom' if side > 0 else 'top', fontsize=size, color=color,
            zorder=7, path_effects=HALO)


def _dimv(ax, y0, y1, x, t, ext=None, color=GREY, size=8.3):
    if ext is not None:
        for y in (y0, y1):
            ax.plot([ext, x + 0.35 * (1 if x > ext else -1)], [y, y],
                    color=color, lw=0.5, zorder=1)
    ax.annotate('', xy=(x, y0), xytext=(x, y1),
                arrowprops=dict(arrowstyle='<|-|>', color=color, lw=0.8,
                                mutation_scale=8), zorder=6)
    ax.text(x + 0.45, (y0 + y1) / 2, t, ha='left', va='center',
            fontsize=size, color=color, rotation=90, zorder=7,
            path_effects=HALO)


def _balloon(ax, n, x, y, xt, yt, color=GREY, r=1.35, lead=True):
    """A numbered balloon with a short leader - the drawing convention.

    Long prose with a leader across the part is what made the first
    version unreadable: five sentences crossing a core 40 mm wide.  The
    numbers go on the part and the words go in the key beside it.
    """
    if lead:
        ax.annotate('', xy=(x, y), xytext=(xt, yt),
                    arrowprops=dict(arrowstyle='-', color=color, lw=0.8,
                                    shrinkA=r * 2.6, shrinkB=1), zorder=8)
    ax.add_patch(Circle((xt, yt), r, fc='white', ec=color, lw=1.0, zorder=9))
    ax.text(xt, yt - 0.04, '%d' % n, ha='center', va='center', fontsize=8.3,
            color=color, zorder=10)


def an_core_section(save, foot):
    """The chosen core in section, drawn to scale, and the winding in it.

    THE AXES OF THE FIRST TWO PANELS ARE IN MILLIMETRES with equal aspect,
    and the scale comes from each panel's own size on the page (_mm_ax),
    so nothing there can be out of proportion without the core itself
    coming out the wrong shape.  The core seen from above, which the
    leakage needs, is the next figure (an_core_plan).

    Dimensions are from the TDK data sheets of the chosen core and its
    catalogue coil former, with the partition this note adds (cores.MECH,
    with provenance per value).  The winding is not decoration:
    cores.winding() lays it out - NP1, triple-insulated Litz bundles side by
    side a turn, in one section, NS2 and NS3 in the other, the partition
    between - and this function draws what comes back, every bundle a
    circle of its computed diameter at its real radius.  A TIW bundle is
    drawn as its copper inside a ring of its insulation.  Margin tape, when
    there is any, is drawn to the height of the section it flanks.

    Winding colours are the ones of the pin figure (an_xfmr_pins), so
    the two figures read together.
    """
    import cores as _C
    import an_pdf as _A
    V = _A.V
    NAME = _C.CHOSEN
    R = _C.CORES[NAME]
    w = _C.winding(V, NAME)
    M = w['M']
    gp = _C.gap_len(V, NAME)[0]
    dp, dl, ds = w['d_pri'], w['d_litz'], w['d_sec']
    COL = {'NP1': MAG, 'NS2': GRN, 'NS3': CYA}
    EDG = {'NP1': '#9c0055', 'NS2': '#2d7a4c', 'NS3': '#1f7fa6'}
    TIWC = '#f3e3b0'                          # the triple insulation ring

    def pri(ax, x, y):
        ax.add_patch(Circle((x, y), dp / 2.0, fc=TIWC, ec=EDG['NP1'],
                            lw=0.6, zorder=6))
        ax.add_patch(Circle((x, y), dl / 2.0, fc=COL['NP1'], ec=EDG['NP1'],
                            lw=0.4, alpha=0.55, zorder=7))

    def sec(ax, x, y, who):
        ax.add_patch(Circle((x, y), ds / 2.0, fc=COL[who], ec=EDG[who],
                            lw=0.6, alpha=0.75, zorder=6))

    tt = w['t_tape']
    TAPEC = '#e0b000'                         # layer tape, drawn as a line

    def layer_tape(ax, c, a0, a1, vertical=False):
        """one wrap of layer tape: at radius c from a0 to a1 along the axis.
        Its 0.05 mm would not show at scale, so it is drawn as a line."""
        if vertical:
            ax.plot([c, c], [a0, a1], color=TAPEC, lw=1.6, zorder=8,
                    solid_capstyle='butt')
        else:
            ax.plot([a0, a1], [c, c], color=TAPEC, lw=1.6, zorder=8,
                    solid_capstyle='butt')

    def aux(ax, x, y):
        ax.add_patch(Circle((x, y), w['tiw_od'] / 2.0, fc=PUR, ec=PUR,
                            lw=0.5, zorder=7))

    #  The figure is drawn 15 % smaller than the page column it fills, so
    #  everything on it - core, winding and lettering - prints 15 % larger
    #  (2026-09-22, user: the drawing and its text were too small).
    kp = w['k']                               # winding pitch / bundle
    fig = plt.figure(figsize=(9.3 / 1.15, 6.6 / 1.15))
    S1, S2 = 22.5, 9.4                        # mm per inch on the two scaled panels
    ax = _mm_ax(fig, [0.006, 0.030, 0.430, 0.940], 1.6, -2.0, S1)
    #  the unrolled winding: its scale and centre follow the winding width,
    #  so a wider former is not cut off at the panel edge
    S2 = (w['wind_w'] + 2 * w['flange'] + 9.0) / (0.550 * 9.3 / 1.15)
    ax2 = _mm_ax(fig, [0.445, 0.265, 0.550, 0.470],
                 2.0 + w['wind_w'] / 2.0, 4.6, S2)
    #  (the core seen from above is its own figure now, an_core_plan)

    #  =================================================== SECTION, 1:1
    HW, HH = M['W'] / 2.0, M['H'] / 2.0
    WH, RC, RW = M['win_h'] / 2.0, M['d_centre'] / 2.0, M['r_win_out']
    ferr = dict(fc=FERR, ec=FERRE, lw=1.0, hatch='////', zorder=3)
    #  the centre leg is drawn GAPPED, because it is
    for rc in ((-HW, WH, M['W'], HH - WH), (-HW, -HH, M['W'], HH - WH),
               (-RC, gp / 2.0, 2 * RC, WH - gp / 2.0),
               (-RC, -WH, 2 * RC, WH - gp / 2.0),
               (-HW, -WH, HW - RW, M['win_h']),
               (RW, -WH, HW - RW, M['win_h'])):
        ax.add_patch(Rectangle(rc[:2], rc[2], rc[3], **ferr))

    RB, RT = M['bore'] / 2.0, M['tube_od'] / 2.0
    FH, WW = M['flange_h'] / 2.0, w['wind_w'] / 2.0
    RF = M.get('r_room', RW - 0.15)
    bob = dict(fc=PLAS, ec='#55606c', lw=0.9, zorder=4)
    for sgn in (-1, 1):
        xt = RB if sgn > 0 else -RT
        ax.add_patch(Rectangle((xt, -FH), RT - RB, 2 * FH, **bob))
        for yy in (WW, -FH):
            xf = RT if sgn > 0 else -RF
            ax.add_patch(Rectangle((xf, yy), RF - RT, FH - WW, **bob))

    def Y(yax):
        """axial position from the primary flange -> drawing y"""
        return WW - yax
    tape = ((0.0, w['yA'][0], w['h_A']),
            (w['yS'][1], w['wind_w'], w['h_S_aux']))
    tape = tuple(t for t in tape if t[1] - t[0] > 1e-6)
    gaps = [(w['yA'][1], w['yS'][0])] if w.get('sep', 0) > 0 else []
    hmax = max(w['h_A'], w['h_S_aux'])
    ka = w['k_ax']
    pa, ps = dp * kp, ds * kp                 # layer to layer
    qa, qs = dp * ka, ds * ka                 # along a layer
    npp = w['pri_par']
    for sgn in (-1, 1):
        for y0, y1, h in tape:
            x0 = RT if sgn > 0 else -(RT + h)
            ax.add_patch(Rectangle((x0, Y(y1)), h, y1 - y0, fc=TAPE,
                                   ec='#b9a25e', lw=0.6, zorder=5))
        for g0, g1 in gaps:                   # the partition, a wall
            xg = RT if sgn > 0 else -RF
            ax.add_patch(Rectangle((xg, Y(g1)), RF - RT, g1 - g0, **bob))
        y0, y1 = w['yA']
        for li, n in enumerate(w['rows_A']):
            r0 = RT + (pa + tt) * li
            for q in range(n * npp):          # a short layer is spread
                pri(ax, sgn * (r0 + pa / 2.0),
                    Y(y0 + w['w_A'] * (q + 0.5) / (n * npp)))
            layer_tape(ax, sgn * (r0 + pa + tt / 2.0), Y(y0), Y(y1),
                       vertical=True)
        for li, row in enumerate(w['smap']):
            r0 = RT + (ps + tt) * li
            for c, who in enumerate(row):
                sec(ax, sgn * (r0 + ps / 2.0), Y(w['yS'][0] + qs * (c + 0.5)),
                    who)
            layer_tape(ax, sgn * (r0 + ps + tt / 2.0), Y(w['yS'][0]),
                       Y(w['yS'][1]), vertical=True)
        ra = RT + w['h_S'] + w['tiw_od'] * kp / 2.0
        for q in range(w['n_aux']):
            aux(ax, sgn * ra, Y(w['yS'][0] + w['w_S'] * (q + 0.5) / w['n_aux']))
        if w['n_aux']:
            layer_tape(ax, sgn * (RT + w['h_S_aux'] - tt / 2.0),
                       Y(w['yS'][0]), Y(w['yS'][1]), vertical=True)

    _dimh(ax, -HW, HW, -HH - 11.0, '%.1f' % M['W'], ext=-HH)
    _dimh(ax, -RC, RC, -HH - 4.0, ('%.2f' if M.get('shape') == 'E' else
                                   u'ø%.1f') % M['d_centre'], ext=-WH,
          side=-1)
    _dimv(ax, -HH, HH, HW + 8.6, '%.1f' % M['H'], ext=HW)
    _dimv(ax, -WH, WH, HW + 3.0, '%.1f' % M['win_h'], ext=RW)
    ax.text(0.0, HH + 11.5, '%s in section' % NAME, ha='center', va='bottom',
            fontsize=10.5, color=NAVY, zorder=8)
    ax.text(0.0, -HH - 16.5, 'all dimensions in mm', ha='center', va='top',
            fontsize=8.5, color=GREY, zorder=8)
    #  balloons point into the LEFT window, so no leader crosses the part.
    #  Numbers are the rows of the legend table beside the figure.  They are
    #  spaced evenly down the side of the core, in the order of the parts
    #  along the axis.
    BX = -HW - 5.6
    yS0 = w['yS'][0]
    l2 = w['order'].index('NS2')
    l3 = w['order'].index('NS3')
    parts = [
        (1, -(RT + pa * 1.5 + tt), Y(w['yA'][0] + qa * 1.5), EDG['NP1']),
        (7, -(RT + RF) / 2.0, Y((w['yA'][1] + yS0) / 2), '#55606c'),
        (2, -(RT + (ps + tt) * l2 + ps / 2), Y(yS0 + qs * 0.5),
         EDG['NS2']),
        (3, -(RT + (ps + tt) * l3 + ps / 2), Y(yS0 + qs * 1.5),
         EDG['NS3']),
        (4, -(RT + w['h_S'] + w['tiw_od'] * kp / 2),
         Y(yS0 + w['w_S'] * 0.5 / max(w['n_aux'], 1)), PUR),
        (6, -(RT + RF) / 2.0, -(WW + FH) / 2.0, '#55606c')]
    top, bot = WH + 3.0, -WH - 3.0
    for q, (n, x, y, c) in enumerate(parts):
        _balloon(ax, n, x, y, BX, top + (bot - top) * q / (len(parts) - 1), c)
    _balloon(ax, 5, 0.0, gp / 2.0, 0.0, HH + 5.0, GOLD)

    #  ============================== DETAIL, the winding unrolled
    OX, OY = 2.0, -3.6
    L = w['wind_w']
    fl = w['flange']
    BH = hmax + 1.1
    ax2.add_patch(Rectangle((OX - fl - 1.6, OY - 1.9), L + 2 * fl + 3.2, 1.9,
                            fc=FERR, ec=FERRE, lw=1.0, hatch='////', zorder=3))
    for x0 in (OX - fl, OX + L):
        ax2.add_patch(Rectangle((x0, OY), fl, BH, **bob))
    for y0, y1, h in tape:
        ax2.add_patch(Rectangle((OX + y0, OY), y1 - y0, h, fc=TAPE,
                                ec='#b9a25e', lw=0.6, zorder=4))
    for g0, g1 in gaps:
        ax2.add_patch(Rectangle((OX + g0, OY), g1 - g0, BH, **bob))
    y0, y1 = w['yA']
    for li, n in enumerate(w['rows_A']):
        yl = OY + (pa + tt) * li
        for q in range(n * npp):
            pri(ax2, OX + y0 + w['w_A'] * (q + 0.5) / (n * npp), yl + pa / 2.0)
        layer_tape(ax2, yl + pa + tt / 2.0, OX + y0, OX + y1)
    for li, row in enumerate(w['smap']):
        yl = OY + (ps + tt) * li
        for c, who in enumerate(row):
            sec(ax2, OX + yS0 + qs * (c + 0.5), yl + ps / 2.0, who)
        layer_tape(ax2, yl + ps + tt / 2.0, OX + yS0, OX + w['yS'][1])
    for q in range(w['n_aux']):
        aux(ax2, OX + yS0 + w['w_S'] * (q + 0.5) / w['n_aux'],
            OY + w['h_S'] + w['tiw_od'] * kp / 2.0)
    if w['n_aux']:
        layer_tape(ax2, OY + w['h_S_aux'] - tt / 2.0, OX + yS0,
                   OX + w['yS'][1])
    ax2.text(OX + L / 2.0, OY + BH + 5.6,
             'the winding unrolled along the former', ha='center',
             va='bottom', fontsize=10.5, color=NAVY, zorder=8)
    _dimh(ax2, OX, OX + L, OY - 3.5, 'winding width  %.1f' % L,
          ext=OY - 1.9, side=-1)
    dims = [(w['yA'][0], w['yA'][1], '%.2f' % w['w_A'], EDG['NP1'], 1),
            (w['yA'][1], w['yS'][0], '%.2f' % w['sep'], '#55606c', 7),
            (w['yS'][0], w['yS'][1], '%.2f' % w['w_S'], EDG['NS2'], None)]
    for x0, x1, t, c, n in dims:
        _dimh(ax2, OX + x0, OX + x1, OY + BH + 1.1, t, color=c)
        if n:
            _balloon(ax2, n, 0, 0, OX + (x0 + x1) / 2, OY + BH + 3.3, c,
                     r=0.62, lead=False)
    for n, xx, c in ((2, yS0 + qs * 0.5, EDG['NS2']),
                     (3, yS0 + qs * 1.5, EDG['NS3'])):
        _balloon(ax2, n, 0, 0, OX + xx, OY + BH + 3.3, c, r=0.62, lead=False)
    _dimh(ax2, OX + L, OX + L + fl, OY - 3.5, '%.2f' % fl, color=GREY,
          side=-1)

    foot(fig, 'Core %s and coil former %s drawn to scale from the TDK '
              'data sheets, with a %.1f mm partition added to the former. '
              'The winding is laid out by '
              'cores.winding(): %.2f × the conductor layer to layer and %.3f '
              'along the layer, so the width is full (the small gaps of a '
              'real winding, assumed), NP1 one triple-insulated Litz bundle '
              'a turn (%.1f mm of insulation assumed), %.1f mm TIW for NAUX, '
              'and a wrap of %.2f mm layer tape over every layer (the yellow '
              'lines, not to scale).'
              % (NAME, M['former'], w['sep'], kp, w['k_ax'], w['tiw_add'],
                 w['tiw_od'], w['t_tape']))
    save(fig, 'an_core_section')


def an_core_plan(save, foot):
    """The core from above, and how much of one turn the ferrite surrounds.

    Why it is drawn: the tank's L_r IS the leakage of the transformer, and
    the leakage field between NP1 and NS2/NS3 is not the same where the
    ferrite surrounds the winding as where the winding is out in the air.
    leakage_fem.py solves the two cases and adds them in the proportion of
    turn length in each, radius by radius (cores.zones()).  This figure
    shows that proportion for the turn in the middle of NP1.

    Left, to scale (cores.MECH, read from the TDK drawing): the outer legs,
    the bow-tie back plate, the centre leg, the whole winding as a pale
    ring under the plate, and the one turn in three colours.  Right: what
    the colours mean and why the split matters, in words.  The middle
    colour - under the plate but with no outer leg beside it - is counted
    half in each case (cores.YOKE_SHARE, an assumption); it says so.
    """
    import cores as _C
    import an_pdf as _A
    V = _A.V
    NAME = _C.CHOSEN
    w = _C.winding(V, NAME)
    M = w['M']
    fig = plt.figure(figsize=(9.35, 4.75))
    ax = _mm_ax(fig, [0.005, 0.015, 0.500, 0.970], 0.0, -1.0, 15.2)

    (wx0, wy0), (wx1, wy1) = M['wing']
    nx, ny = M['neck']
    hd, hw2, R0 = M['plan_d'] / 2.0, M['W'] / 2.0, M['r_win_out']
    RC, RT = M['d_centre'] / 2.0, M['tube_od'] / 2.0
    top = [(-hw2, hd), (-wx1, hd), (-wx1, wy1), (-wx0, wy0), (-nx, ny)]
    arc = [(RC * np.cos(t), RC * np.sin(t))
           for t in np.linspace(np.arctan2(ny, -nx), np.arctan2(ny, nx), 12)]
    outline = (top + arc + [(nx, ny), (wx0, wy0), (wx1, wy1), (wx1, hd),
                            (hw2, hd)])
    outline = outline + [(x, -y) for x, y in outline[::-1]]

    #  the whole winding, NP1's section, as a pale ring: under the plate it
    #  is seen through the hatching
    rb = RT + w['h_A']
    th = np.linspace(0, 2 * np.pi, 361)
    ring = ([(rb * np.cos(t), rb * np.sin(t)) for t in th] +
            [(RT * np.cos(t), RT * np.sin(t)) for t in th[::-1]])
    ax.add_patch(Polygon(ring, closed=True, fc='#efdcc6', ec='none',
                         zorder=1.2))
    ax.add_patch(Polygon(outline, closed=True, fc=FERR, ec=FERRE, lw=1.0,
                         hatch='////', alpha=0.80, zorder=1.4))
    ax.add_patch(Circle((0, 0), RC, fc=FERR, ec=FERRE, lw=1.0, zorder=1.5))
    for sgn in (-1, 1):                       # the inside of each outer leg
        t = np.linspace(-np.arcsin(M['leg_y'] / R0), np.arcsin(M['leg_y'] / R0),
                        40)
        ax.plot(sgn * R0 * np.cos(t), R0 * np.sin(t), color=FERRE, lw=1.0,
                zorder=1.5)

    box = dict(boxstyle='round,pad=0.18', fc='white', ec='none', alpha=0.9)
    rho = RT + w['h_A'] / 2.0
    th = np.linspace(0, 2 * np.pi, 1441)
    xx, yy = rho * np.cos(th), rho * np.sin(th)
    ax_ = np.abs(xx)
    edge = wy0 + (wy1 - wy0) / (wx1 - wx0) * (ax_ - wx0)
    under = np.where(ax_ >= wx1, np.abs(yy) <= hd, np.abs(yy) <= edge)
    legz = np.abs(np.sin(th)) <= M['leg_y'] / R0
    kind = np.where(legz & under, 0, np.where(under, 1, 2))
    ZC = (MAG, GOLD, '#4a5260')
    for kz in (0, 1, 2):
        ax.plot(xx, np.where(kind == kz, yy, np.nan), color=ZC[kz], lw=3.6,
                zorder=6, solid_capstyle='butt')

    #  names on the drawing
    ax.text(0, 0, 'centre\nleg\n\u00f8%.0f' % M['d_centre'], ha='center',
            va='center', fontsize=9.6, color=NAVY, zorder=8, bbox=box)
    for sgn in (-1, 1):
        ax.text(sgn * (hw2 - 3.0), 0.0, 'outer leg', rotation=90,
                ha='center', va='center', fontsize=9.6, color=NAVY,
                zorder=8, bbox=box)
    ax.annotate('back plate', xy=(-9.5, 12.6), xytext=(-26.0, 25.5),
                fontsize=9.6, color=NAVY, ha='left', va='center', zorder=8,
                arrowprops=dict(arrowstyle='-', color=NAVY, lw=0.8))
    ax.annotate('the whole winding (NP1)', xy=(-9.0, -18.5),
                xytext=(-31.0, -27.0),
                fontsize=9.6, color='#8a5a2b', ha='left', va='center',
                zorder=8, arrowprops=dict(arrowstyle='-', color='#8a5a2b',
                                          lw=0.8))
    ax.text(9.0, 25.5, 'front: no core,\nthe winding is in the open',
            ha='left', va='center', fontsize=9.6, color=GREY, zorder=8)
    ax.text(9.0, -26.5, 'back: the same', ha='left', va='center',
            fontsize=9.6, color=GREY, zorder=8)

    #  what the colours mean
    tx = fig.add_axes([0.520, 0.015, 0.475, 0.970])
    S.frame(tx, 0.0, 100.0, 0.0, 100.0)
    pct = _C.zone_pct(NAME, rho)
    S.label(tx, 0.0, 95.0, 'ONE TURN OF NP1, SEEN FROM ABOVE', size=11.0,
            color=NAVY, weight='bold', ha='left')
    S.label(tx, 0.0, 88.5, 'the turn in the middle of the winding, '
            'r = %.1f mm' % rho, size=9.4, color=GREY, ha='left')
    rows = ((0, '%d %%' % pct[0], 'ferrite all round:',
             'an outer leg beside it'),
            (1, '%d %%' % pct[1], 'the plates above and below,',
             'but no outer leg beside it'),
            (2, '%d %%' % pct[2], 'no ferrite at all:',
             'outside the core, in the air'))
    for q, (kz, p_, t1, t2) in enumerate(rows):
        y = 78.0 - 13.0 * q
        tx.plot([0.0, 7.0], [y, y], color=ZC[kz], lw=3.6,
                solid_capstyle='butt', zorder=3)     # a swatch, not a wire
        S.label(tx, 10.0, y, p_, size=10.5, color=ZC[kz], weight='bold',
                ha='left')
        S.label(tx, 25.0, y + 2.6, t1, size=9.8, color=NAVY, ha='left')
        S.label(tx, 25.0, y - 3.0, t2, size=9.8, color=NAVY, ha='left')
    lines = ('Why it matters. The resonant inductor',
             'is the leakage of this transformer, the',
             'field between NP1 and NS2 / NS3.',
             'Ferrite around the winding holds that',
             'field in; in the air it spreads out. Both',
             'cases are solved and added in these',
             'shares, radius by radius; the middle',
             'share counts half in each (assumed).')
    for i, t in enumerate(lines):
        S.label(tx, 0.0, 38.0 - 4.9 * i, t, size=9.6, color=GREY, ha='left')

    foot(fig, 'Core %s seen from above, to scale from the TDK data sheet: '
              'the outer legs, the bow-tie back plate and the centre leg, '
              'the winding as a pale ring under the plate, and one turn '
              'coloured by what surrounds it.' % NAME)
    save(fig, 'an_core_plan')


# ------------------------------------------------- the voltage loop as blocks
def an_loop_blocks(save, foot):
    """The voltage loop drawn as blocks, so the reader sees what is the
    compensator and what is the plant before either is written as an
    equation.  Plain axes (not aspect-equal): there is no wiring here for
    the topology check to read, only boxes and arrows."""
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(9.3, 3.1))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 32)
    ax.axis('off')
    GRN2 = '#2d7a4c'
    boxes = [(2,  'output\ndivider\nR$_I$, R$_O$', NAVY),
             (16, 'TL431 with\nR$_F$, C$_F$, C$_{Fo}$', NAVY),
             (30, 'optocoupler\nCTR', NAVY),
             (44, 'FB pin\nR$_{FB}$, C$_{fx}$', NAVY),
             (60, 'controller\n(power\ncommand)', GRN2),
             (74, 'converter\nP$_{in}$', GRN2),
             (88, 'C$_{out}$', GRN2)]
    W, H, Y = 11.0, 11.0, 10.0
    for x, t, c in boxes:
        ax.add_patch(FancyBboxPatch((x, Y), W, H, boxstyle='round,pad=0.4',
                                    fc='white', ec=c, lw=1.4, zorder=3))
        ax.text(x + W / 2, Y + H / 2, t, ha='center', va='center',
                fontsize=9.4, color=c, zorder=4, linespacing=1.2)
    for (x0, _, _), (x1, _, _) in zip(boxes[:-1], boxes[1:]):
        ax.annotate('', xy=(x1 - 0.4, Y + H / 2), xytext=(x0 + W + 0.4, Y + H / 2),
                    arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.1),
                    zorder=2)
    #  what travels on each arrow, written above the gap
    for (x0, _, _), t in zip(boxes[:-1], ('v$_{out}$', 'i$_{LED}$', 'i$_{FB}$',
                                          'v$_{FB}$', 'P$_{in}$', 'i$_{out}$')):
        ax.text(x0 + W + 1.5, Y + H + 0.5, t, ha='center', va='bottom',
                fontsize=9.4, color=GREY, zorder=4)
    #  the return path: v_out from C_out back to the divider, drawn as a
    #  polyline under the row so nothing is clipped
    xr, xl, yb = 88 + W / 2, 2 + W / 2, 4.0
    ax.plot([xr, xr, xl], [Y - 0.4, yb, yb], color=GREY, lw=1.1, zorder=2)
    ax.annotate('', xy=(xl, Y - 0.4), xytext=(xl, yb),
                arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.1), zorder=2)
    ax.text(50, yb + 1.3, 'v$_{out}$  is measured and fed back', ha='center',
            va='bottom', fontsize=9.4, color=GREY, zorder=4,
            path_effects=HALO)
    #  the two brackets
    for x0, x1, t, c in ((2, 44 + W, 'compensator  G$_{EA}$(s)  =  $-$v$_{FB}$ / v$_{out}$', NAVY),
                         (60, 88 + W, 'plant  G$_{plant}$(s)  =  v$_{out}$ / v$_{FB}$  =  G$_o$ / s', GRN2)):
        yk = Y + H + 3.2
        ax.plot([x0, x0, x1, x1], [yk - 0.9, yk, yk, yk - 0.9], color=c, lw=1.2,
                zorder=3)
        ax.text((x0 + x1) / 2, yk + 1.0, t, ha='center', va='bottom',
                fontsize=9.6, color=c, zorder=4)
    foot(fig, 'The voltage loop as blocks. The loop gain T(s) is the product '
              'of the two brackets.')
    save(fig, 'an_loop_blocks')


# ------------------------------------- the TL431 compensator as an op-amp
def _pgnd(ax, x, y, s=None, color=NAVY):
    """Primary-side ground: a filled triangle, not the earth symbol.

    The compensator sits on the secondary and the FB pin on the primary,
    with the optocoupler between them, so the two returns are different
    nodes.  Drawing both with the same symbol says they are joined, which
    is exactly what the isolation forbids (2026-09-22, user).
    """
    from matplotlib.patches import Polygon
    s = 0.22 * X.scale(ax) if s is None else s
    ax.add_patch(Polygon([(x - s, y), (x + s, y), (x, y - 1.5 * s)],
                         closed=True, fc=color, ec=color, lw=1.4, zorder=3))


def an_comp_opamp(save, foot):
    """The TL431 network of the ST drawing redrawn as an equivalent circuit.

    Inside the TL431, as its datasheet draws it: REF goes to the
    non-inverting input of an amplifier, the internal 2.495 V reference to
    the inverting one, and the amplifier drives an NPN whose collector is
    the cathode and whose emitter is the anode.  The reference is returned
    to the anode, not to a separate ground.  R_I, R_O and Z_f are external
    and stay outside the outline.  The optocoupler is its small-signal
    model: the LED carries i_LED and the transistor side is a
    current-controlled current source CTR*i_LED sinking from the FB node.
    The optocoupler is also the isolation barrier, so the two sides have
    different returns and different ground symbols.
    """
    from matplotlib.patches import Polygon, Circle, Rectangle
    fig = plt.figure(figsize=(9.6, 7.0))
    ax = _ax(fig, [0.02, 0.03, 0.96, 0.94], -0.6, 15.4, -1.7, 9.9)

    def eqn(x, y, tex, size=12.5, color=NAVY, ha='center'):
        ax.text(x, y, '$%s$' % tex, ha=ha, va='center', fontsize=size,
                color=color, math_fontfamily='stix', zorder=6)

    YR = 5.6                              # the REF / divider line
    XA, XN = 2.0, 6.15                    # REF node, cathode node
    XT_, XB_ = 3.5, 4.95                  # amplifier left edge, apex
    YC = 5.15                             # amplifier centre = base centre
    YK, YA_ = 6.6, 2.6                    # cathode rail, anode rail
    # ------------------------------------------------ inside the TL431
    ax.add_patch(Polygon([(XT_, 4.30), (XT_, 6.00), (XB_, YC)], closed=True,
                         fc='white', ec=NAVY, lw=1.8, zorder=4))
    #  A '+' or a '-' set with va='center' lands about 1.7 pt above its
    #  anchor: matplotlib centres the glyph's layout box, and the ink of
    #  both signs sits above that box's centre.  Measured on this face
    #  at this size, and pushed back down in points so the mark lands on
    #  the input pin whatever the figure's scale (2026-09-22, user).
    for yy, mk, dy in ((YR, '+', -1.6), (4.70, '$-$', -1.8)):
        ax.annotate(mk, (XT_ + 0.26, yy), textcoords='offset points',
                    xytext=(0, dy), ha='center', va='center',
                    fontsize=22, color=NAVY, zorder=6)
    #  the internal reference, returned to the anode
    XR, r = 3.05, 0.36
    S.wire(ax, [(XT_, 4.70), (XR, 4.70), (XR, 4.05)])
    ax.add_patch(Circle((XR, 4.05 - r), r, fc='white', ec=NAVY, lw=1.8,
                        zorder=4))
    S.label(ax, XR, 4.05 - r + 0.42 * r, '+', size=9.8, z=7)
    S.label(ax, XR, 4.05 - r - 0.45 * r, '$-$', size=9.8, z=7)
    S.wire(ax, [(XR, 4.05 - 2 * r), (XR, YA_), (XN, YA_)])
    S.dot(ax, XN, YA_)
    eqn(XR + 0.42, 3.45, r'V_R = 2.495\ \mathrm{V}', size=10.5, ha='left')
    S.label(ax, XR + 0.42, 3.05, '(internal reference)', size=9.8,
            ha='left', color=GREY)
    #  the output transistor: base from the amplifier, collector K, emitter A
    XBB = 5.75
    S.wire(ax, [(XB_, YC), (XBB, YC)])
    ax.plot([XBB, XBB], [YC - 0.40, YC + 0.40], color=NAVY, lw=2.2, zorder=4)
    ax.plot([XBB, XN], [YC + 0.21, YC + 0.61], color=NAVY, lw=1.7, zorder=4)
    ax.plot([XBB, XN], [YC - 0.21, YC - 0.61], color=NAVY, lw=1.7, zorder=4)
    #  the emitter arrowhead at twice the default size: it is what says
    #  NPN rather than PNP, and at the size the rest of the symbol was
    #  shrunk to it had become a speck (2026-09-22, user)
    ax.annotate('', (XN, YC - 0.61), (XBB + 0.13, YC - 0.34),
                arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=1.4,
                                mutation_scale=18), zorder=4)
    S.wire(ax, [(XN, YC + 0.61), (XN, 8.1)])          # collector riser
    S.wire(ax, [(XN, YC - 0.61), (XN, 1.75)])         # emitter riser
    S.gnd(ax, XN, 1.75)
    #  the outline holds only what the part contains
    ax.add_patch(Rectangle((2.75, 2.15), 3.75, 4.05, fc='none', ec=GREY,
                           lw=1.0, ls=(0, (4, 3)), zorder=1))
    S.label(ax, 2.85, 2.38, 'TL431', size=9.8, ha='left', color=GREY)
    S.label(ax, 2.85, YR + 0.28, 'REF', size=9.8, ha='left', color=GREY)
    S.label(ax, 6.60, 6.02, 'K', size=9.8, ha='left', color=GREY)
    S.label(ax, 6.60, 2.02, 'A', size=9.8, ha='left', color=GREY)
    # ------------------------------------------- divider R_I, R_O, REF node
    S.dot(ax, 0.2, YR)
    S.label(ax, 0.2, YR + 0.5, 'v$_{out}$', size=11)
    ra, rb = S.res(ax, 1.10, YR, 'R$_I$', tdy=0.55)
    S.wire(ax, [(0.2, YR), ra])
    S.wire(ax, [rb, (XA, YR), (XT_, YR)])
    S.dot(ax, XA, YR)
    oa, ob = S.res(ax, XA, 4.20, horiz=False)
    S.label(ax, XA - 0.32, 4.20, 'R$_O$', size=10, ha='right')
    S.wire(ax, [(XA, YR), ob])
    S.wire(ax, [oa, (XA, 2.6)])
    S.gnd(ax, XA, 2.6)
    # ----------------------------------- feedback Z_f between REF and K
    S.wire(ax, [(XA, YR), (XA, 8.1)])
    S.dot(ax, XA, 7.2)
    S.dot(ax, XN, 7.2)
    S.dot(ax, XN, YK)
    fa, fb = S.res(ax, 3.6, 7.2, 'R$_F$', tdy=0.50)
    ca, cb = S.cap(ax, 5.1, 7.2, 'C$_F$', tdy=0.50)
    S.wire(ax, [(XA, 7.2), fa])
    S.wire(ax, [fb, ca])
    S.wire(ax, [cb, (XN, 7.2)])
    oa2, ob2 = S.cap(ax, 4.1, 8.1, 'C$_{Fo}$', tdy=0.42)
    S.wire(ax, [(XA, 8.1), oa2])
    S.wire(ax, [ob2, (XN, 8.1)])
    eqn(4.1, 8.95, r'Z_f = C_{Fo} \parallel (R_F + C_F)', size=10.5,
        color=GREY)
    eqn(XN - 0.18, 6.90, r'v_K', size=11, ha='right')
    # ------------------------------------------ LED branch, R_B, R_P
    XK, YLA = 8.0, 7.7
    YB = (YLA + YK) / 2
    S.wire(ax, [(XN, YK), (XK, YK)])
    da, db = S.diode(ax, XK, YB, horiz=False, flip=True)
    S.wire(ax, [(XK, YLA), da])
    S.wire(ax, [db, (XK, YK)])
    S.dot(ax, XK, YLA)
    S.dot(ax, XK, YK)
    ax.annotate('', (XK - 0.42, YB - 0.38), (XK - 0.42, YB + 0.38),
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.6,
                                mutation_scale=11), zorder=6)
    eqn(XK - 0.62, YB + 0.42, r'i_{LED}', size=10.5, color=MAG, ha='right')
    S.label(ax, XK + 0.32, YB + 0.02, 'LED', size=9.8, ha='left',
            color=GREY)
    XP = 9.2
    S.wire(ax, [(XK, YLA), (XP, YLA)])
    pa, pb = S.res(ax, XP, YB, 'R$_P$', horiz=False)
    S.wire(ax, [(XP, YLA), pb])
    S.wire(ax, [pa, (XP, YK), (XK, YK)])
    ba, bb = S.res(ax, XK, 8.50, 'R$_B$', horiz=False)
    S.wire(ax, [(XK, YLA), ba])
    S.wire(ax, [bb, (XK, 9.40)])
    S.dot(ax, XK, 9.40)
    S.label(ax, XK, 9.75, 'V$_Z$ (regulated rail)', size=9.8)
    # -------------------------------------------- the isolation barrier
    XI = 9.95
    ax.plot([XI, XI], [1.6, 9.2], color=GREY, lw=1.0, ls=(0, (5, 4)),
            zorder=1)
    S.label(ax, XI - 0.18, 2.15, 'secondary side', size=9.8, ha='right',
            color=GREY)
    S.label(ax, XI + 0.18, 2.15, 'primary side', size=9.8, ha='left',
            color=GREY)
    # --------------- the transistor side as a controlled current source
    XT, YD, hs = 10.8, 6.60, 0.55
    YFB = 7.7
    ax.add_patch(Polygon([(XT, YD + hs), (XT + 0.42, YD), (XT, YD - hs),
                          (XT - 0.42, YD)], closed=True, fc='white',
                         ec=NAVY, lw=1.8, zorder=4))
    ax.annotate('', (XT, YD - 0.30), (XT, YD + 0.30),
                arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=1.6,
                                mutation_scale=11), zorder=5)
    S.wire(ax, [(XT, YD + hs), (XT, YFB)])
    S.wire(ax, [(XT, YD - hs), (XT, 5.20)])
    _pgnd(ax, XT, 5.20)
    eqn(XT + 0.55, YD + 0.12, r'CTR \cdot i_{LED}', size=10.5, ha='left')
    S.label(ax, XT + 0.55, YD - 0.40, 'optocoupler', size=9.8, ha='left',
            color=GREY)
    # ------------------------------------------------- FB pin network
    XF, XC, XE = 12.4, 13.2, 14.2
    S.wire(ax, [(XT, YFB), (XE, YFB)])
    S.dot(ax, XF, YFB)
    S.dot(ax, XC, YFB)
    S.dot(ax, XE, YFB)
    S.label(ax, XE, YFB + 0.5, 'v$_{FB}$', size=11)
    S.label(ax, XE, YFB - 0.45, 'FB pin', size=9.8, color=GREY)
    pa2, pb2 = S.res(ax, XF, 8.50, 'R$_{FB}$', horiz=False)
    S.wire(ax, [(XF, YFB), pa2])
    S.wire(ax, [pb2, (XF, 9.40)])
    S.dot(ax, XF, 9.40)
    S.label(ax, XF, 9.75, 'pull-up inside the IC', size=9.8)
    qa, qb = S.cap(ax, XC, 6.55, 'C$_{opto}$ + C$_{fx}$', horiz=False)
    S.wire(ax, [(XC, YFB), qb])
    S.wire(ax, [qa, (XC, 5.20)])
    _pgnd(ax, XC, 5.20)
    # ------------------------------------------ the three factors
    eqn(7.4, 0.55, r'\dfrac{v_K}{v_{out}} = -\dfrac{Z_f}{R_I},\qquad '
                   r'i_{LED} = -\dfrac{v_K}{R_B},\qquad '
                   r'v_{FB} = -\,CTR\, i_{LED}\left(R_{FB} \parallel '
                   r'\dfrac{1}{s\,(C_{opto}+C_{fx})}\right)')
    S.label(ax, 7.4, -0.30, 'R$_O$ carries no signal: the REF input is held '
            'at V$_R$', size=9.8, color=GREY)
    #  the three factors above carry three minus signs; G_EA is the loop's
    #  compensator WITHOUT the feedback sign, so it is -v_FB/v_out.  It
    #  read +v_FB/v_out = (a positive product), against its own factors
    eqn(7.4, -1.20, r'G_{EA}(s) = -\dfrac{v_{FB}}{v_{out}} = '
                    r'\dfrac{Z_f}{R_I}\cdot\dfrac{CTR\,R_{FB}}{R_B}\cdot'
                    r'\dfrac{1}{1 + s\,R_{FB}(C_{opto}+C_{fx})}')
    foot(fig, 'The TL431 compensator as an op-amp circuit: an inverting '
              'amplifier, a controlled current source, and one RC pole.')
    save(fig, 'an_comp_opamp')


def _note(ax, x, y, text, color=NAVY, size=9.5, ha='left', va='center'):
    """a boxed annotation, the same look as figs.note (not importable here)"""
    return ax.annotate(text, (x, y), color=color, fontsize=size, ha=ha, va=va,
                       bbox=dict(boxstyle='round,pad=0.35', fc='white',
                                 ec=color, lw=1.1, alpha=0.95), zorder=6)


# ------------------------------------------ an annotated example loop plot
def an_loop_example(save, foot):
    """Where the three loop numbers are read on a Bode plot.

    A generic two-integrator loop with a Type II compensator, drawn in
    units of its own crossover so that no design value appears: the zero
    a factor K below f_c, the pole K above, the extra pole far up.  What
    is marked is what the text computes - crossover, phase margin, gain
    margin, and the compensator gain read at 2f_l.
    """
    K, FPX, F2L = 3.0, 50.0, 5.0
    fz, fp = 1.0 / K, K
    f = np.logspace(-2, 3, 1200)
    A = lambda x: (np.sqrt(1 + (x / fz) ** 2)
                   / (np.sqrt(1 + (x / fp) ** 2) * np.sqrt(1 + (x / FPX) ** 2)))
    T = A(f) / f ** 2 / A(1.0)
    TdB = 20 * np.log10(T)
    ph = -180 + np.degrees(np.arctan(f / fz) - np.arctan(f / fp)
                           - np.arctan(f / FPX))
    pm = 180 + (-180 + np.degrees(np.arctan(1 / fz) - np.arctan(1 / fp)
                                  - np.arctan(1 / FPX)))
    f180 = np.sqrt(fp * FPX - fz * (fp + FPX))
    gm = -20 * np.log10(A(f180) / f180 ** 2 / A(1.0))
    T2l = 20 * np.log10(A(F2L) / F2L ** 2 / A(1.0))

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.4, 6.4), sharex=True,
                                 gridspec_kw={'height_ratios': [1.15, 1]})
    a1.semilogx(f, TdB, color=NAVY, lw=2.4)
    a1.axhline(0, color=GREY, lw=1.0)
    a2.semilogx(f, ph, color=MAG, lw=2.4)
    a2.axhline(-180, color=GREY, lw=1.0)
    for a in (a1, a2):
        a.axvline(1.0, color=YEL, lw=2.0, zorder=1)
        a.axvline(f180, color='#2d7a4c', lw=1.1, ls='-.')
        a.axvline(F2L, color=GREY, lw=1.0, ls=':')
        for x in (fz, fp, FPX):
            a.axvline(x, color=LT, lw=1.0)
        a.set_xlim(0.01, 1000)
    a1.set_ylim(-70, 70)
    a2.set_ylim(-280, -60)
    a1.set_ylabel('|T|  [dB]')
    a2.set_ylabel('arg T  [deg]')
    a2.set_xlabel('f / f$_c$   (log)')
    a2.set_yticks([-270, -225, -180, -135, -90])
    #  crossover
    a1.plot([1.0], [0.0], 'o', color=YEL, ms=8, zorder=5)
    _note(a1, 1.35, 22, 'crossover f$_c$:  |T| = 1  (0 dB)', color=NAVY,
         size=9.5)
    #  phase margin, as the arrow it is
    a2.annotate('', xy=(1.0, -180 + pm), xytext=(1.0, -180),
                arrowprops=dict(arrowstyle='<->', color=MAG, lw=1.6))
    _note(a2, 1.35, -180 + pm / 2, 'phase margin $\\Phi_M$ = 180° + arg T at f$_c$',
         color=MAG, size=9.5)
    #  gain margin
    a1.annotate('', xy=(f180, -gm), xytext=(f180, 0),
                arrowprops=dict(arrowstyle='<->', color='#2d7a4c', lw=1.6))
    _note(a1, f180 * 1.4, -gm / 2, 'gain margin GM = $-$|T| at f$_{180}$',
         color='#2d7a4c', size=9.5)
    a2.plot([f180], [-180], 'o', color='#2d7a4c', ms=7, zorder=5)
    _note(a2, f180 * 1.4, -215, 'f$_{180}$:  arg T = $-$180°', color='#2d7a4c',
         size=9.5)
    #  the gain at 2f_l
    a1.plot([F2L], [T2l], 'o', color=GREY, ms=6, zorder=5)
    _note(a1, 0.012, -45, 'at 2f$_l$ the loop gain is |T(2f$_l$)|;  the '
         'compensator alone has\nG$_{EA}$(2f$_l$) = |T| / |G$_{plant}$|,  the '
         'number the D$_3$ check needs', color=GREY, size=8.6)
    #  slopes and the corner names
    for x, t in ((fz, 'f$_z$ = f$_c$/K'), (fp, 'f$_p$ = K f$_c$'),
                 (FPX, 'f$_{px}$')):
        a1.text(x, 62, t, ha='center', va='top', fontsize=8.6, color=GREY,
                bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none'))
    for x, y, t in ((0.04, 45, '$-$40 dB/dec'), (1.0, -12, '$-$20 dB/dec'),
                    (15, -42, '$-$40 dB/dec'), (200, -66, '$-$60 dB/dec')):
        a1.text(x, y, t, fontsize=8.6, color=GREY, ha='center', va='center',
                rotation=0)
    a2.text(0.02, -190, 'two integrators: $-$180°', fontsize=8.6,
            color=GREY, va='top')
    a2.text(0.02, -95, 'the zero lifts the phase,\nthe poles bring it back down',
            fontsize=8.6, color=GREY, va='top')
    a1.text(F2L, 55, '2f$_l$', ha='center', va='top', fontsize=8.6, color=GREY,
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none'))
    fig.subplots_adjust(left=0.10, right=0.98, top=0.97, bottom=0.10,
                        hspace=0.12)
    foot(fig, 'A two-integrator loop with a Type II compensator, in units of '
              'its own crossover. The three loop numbers and the gain at '
              '2f_l, marked where they are read.')
    save(fig, 'an_loop_example')


# ------------------------------------------- 14  flyback against the LLC
def _batt(ax, x, ytop, ybot, t=None, size=11):
    """A dc source between two nodes, wired to both.  -> (top, bottom)

    Two cells, long plate on the + side.  The plates are drawn at zorder 4
    so the wiring check reads them as a symbol and not as four loose wires.
    """
    s = 0.22 * X.scale(ax)
    yc = (ytop + ybot) / 2.0
    for dy, w in ((1.5, 1.00), (0.5, 0.48), (-0.5, 1.00), (-1.5, 0.48)):
        ax.plot([x - s * w * 1.5, x + s * w * 1.5], [yc + dy * s] * 2,
                color=NAVY, lw=2.2, zorder=4, solid_capstyle='butt')
    S.wire(ax, [(x, ytop), (x, yc + 1.5 * s)])
    S.wire(ax, [(x, yc - 1.5 * s), (x, ybot)])
    if t:
        S.label(ax, x - 1.5 * s - 0.34, yc, t, size=size, ha='right')
    return (x, ytop), (x, ybot)


def _sec(ax, top, bot, ys, xd, xc, xr, yt, size=10.5):
    """rectifier, output capacitor and load, hung on one secondary"""
    di, do = S.diode(ax, xd, yt, None, horiz=True)
    S.wire(ax, [top, di])
    S.label(ax, xd, yt + 0.55 * X.scale(ax) + 0.30, 'D', size=size,
            color=GREY)
    S.wire(ax, [do, (xr, yt)])
    S.wire(ax, [bot, (bot[0], ys), (xr, ys)])
    S.shunt(ax, xc, yt, ys, 'cap', None)
    S.label(ax, xc - 0.34 * X.scale(ax) - 0.20, (yt + ys) / 2.0, 'C$_{out}$',
            size=size, ha='right')
    S.dot(ax, xc, yt)
    S.dot(ax, xc, ys)
    S.shunt(ax, xr, yt, ys, 'res', None)
    S.label(ax, xr + 0.30 * X.scale(ax) + 0.22, (yt + ys) / 2.0, 'R$_L$',
            size=size, ha='left')


def an_flyback_llc(save, foot):
    """The two transformers side by side: circuit, currents and flux.

    This is the question every reader who designed a flyback first asks
    about the LLC transformer: if it stores none of the energy it
    delivers, why does A_e come into it at all, and why is the saturation
    test current so much less than the primary peak?

    Both columns are built from the same four rows, so the difference on
    the page is the circuit and not a choice of what to plot.  The LLC
    column reads its waveforms from the eight-interval model the rest of
    the document uses and its two current levels from the design, so this
    figure cannot disagree with the ones around it.

    The bottom row is the one the figure exists for.  It does NOT plot
    the net flux alone: it plots what each winding's ampere-turns would
    drive on its own, and the sum.  Drawn only as a net, the flyback and
    the LLC look like two shapes with no reason behind them; drawn as
    three, the LLC's two large contributions are visibly cancelling into
    a small one and the flyback's two are visibly taking turns.

    The LLC drive is a HALF BRIDGE, which is the ordinary LLC this
    chapter is about.  A full bridge doubles the drive and changes
    nothing in the argument.
    """
    import an_pdf as _A
    V = _A.V
    fig = plt.figure(figsize=(9.35, 8.40))
    XL, XR, WW = 0.100, 0.590, 0.376

    #  Two lines each.  On one line they ran off both edges of the page
    #  and into each other in the middle.
    fig.text(0.030 + 0.231, 0.992, 'FLYBACK (DCM)\nan inductor with a second '
             'winding', ha='center', va='top', fontsize=11.0, color=NAVY,
             fontweight='bold', linespacing=1.35)
    fig.text(0.508 + 0.231, 0.992, 'LLC\na transformer, and a magnetising '
             'branch', ha='center', va='top', fontsize=11.0, color=NAVY,
             fontweight='bold', linespacing=1.35)

    #  Everything but the transformer at TWICE the kit size, and every
    #  designator at 14 pt: the panels are printed small, and at kit size
    #  the reviewer could not read a capacitor from a resistor or an S
    #  from an S.  The transformers keep their explicit height - they were
    #  the one thing in the panel that was already right.
    MULT, FS = 2.0, 14
    YT, YB, YS = 4.4, -1.7, 0.0
    #  The two circuits get DIFFERENT widths, and that is deliberate.  They
    #  sit in separate columns, so nothing has to line up across the gap,
    #  and sharing one layout cost both of them: the flyback was three
    #  quarters empty loop while the LLC had its tank, its magnetising
    #  branch and its transformer crushed into the same span, with L_m's
    #  name landing on the riser beside it.  The axes limits are shared, so
    #  the scale still is - a symbol is the same size in both panels - but
    #  each circuit is laid out to the width it actually needs.
    LIM = (-2.6, 13.4, -2.9, 5.5)

    # ========================================================= the flyback
    ax = _ax(fig, [0.030, 0.655, 0.462, 0.280], *LIM)
    ax._sym_mult = MULT
    XT_F = 4.30
    #  The secondary polarity dot is at the BOTTOM here and at the top in
    #  the LLC panel.  That one dot is the whole difference: inverted, the
    #  rectifier can only conduct while the switch is OFF, which is what
    #  makes the two winding currents exclusive and the rest of this
    #  figure follow from it.
    t1 = X.xfmr(ax, XT_F, 2.5, hp=3.2, hs=3.2, gap=0.52, s_dot='bot')
    #  Read the lead lines back rather than assuming x +- gap: xfmr widens
    #  the gap when the turns would otherwise lie on the core bars, and
    #  everything hung off the primary lead has to move with it.
    XP_F, XS_F = t1['p_top'][0], t1['s_top'][0]
    S.wire(ax, [t1['p_top'], (XP_F, YT), (0.80, YT)])
    _batt(ax, 0.80, YT, YB, 'V$_{in}$', size=FS)
    S.wire(ax, [(0.80, YB), (XP_F, YB)])
    #  The flyback had no ground at all while the LLC beside it had one,
    #  so the two panels disagreed about what the return rail was.  Same
    #  symbol, same place on both: under the source's negative terminal.
    S.gnd(ax, 0.80, YB, lead=0.45)
    #  The switch sits between the primary's lower terminal and the rail,
    #  so its height is what that gap allows: 0.9 down to -1.7 leaves 2.0
    #  with a short lead each end.
    X.mosfet(ax, XP_F, -0.40, 'S', state='plain', h=2.0, gate=1.5,
             body=False, coss=False, size=FS)
    S.wire(ax, [t1['p_bot'], (XP_F, 0.60)])
    S.wire(ax, [(XP_F, -1.40), (XP_F, YB)])
    _sec(ax, t1['s_top'], t1['s_bot'], YS, 6.80, 8.60, 10.20,
         t1['s_top'][1], size=FS)
    #  Mid-coil, not at the top: the top turn is where the polarity dot is.
    #  On the wires, with their reference directions.  The flyback's i_s
    #  is taken INTO its dot (the dot is at the bottom), so the core sees
    #  N_p i_p + N_s i_s; the LLC's i_s is taken OUT of its dot, so the
    #  core sees N_p i_p - N_s i_s.  Drawn as bare names beside the
    #  windings, the two sign conventions could not be told apart.
    xa = (0.80 + XP_F) / 2.0 + 0.30
    _ihead(ax, xa, YT, 'r', 'i$_p$', MAG, (xa, YT + 0.62), size=FS)
    xa = (XS_F + 6.80) / 2.0 - 0.25
    _ihead(ax, xa, t1['s_top'][1], 'r', 'i$_s$', GRN,
           (xa, t1['s_top'][1] + 0.62), size=FS)
    ax.text(6.0, -2.62, 'switch and rectifier are never on together',
            ha='center', va='center', fontsize=10.2, color=GREY)

    # ============================================================= the LLC
    ax2 = _ax(fig, [0.508, 0.655, 0.462, 0.280], *LIM)
    ax2._sym_mult = MULT
    XT_L = 7.30
    #  A half-bridge LEG, drawn out, because the gate row below has to refer
    #  to something.  With a bare square-wave source on the page the reader
    #  was being shown two gate waveforms and no gates.  The supply is a
    #  labelled rail and a ground rather than a battery: that is how a leg
    #  is normally drawn, and the two units it saves on the left are what
    #  the tank needs on the right.
    XLEG, YM, XRAIL = -0.60, 1.65, -1.90
    t2 = X.xfmr(ax2, XT_L, 2.5, hp=3.2, hs=3.2, gap=0.52)
    XP_L, XS_L = t2['p_top'][0], t2['s_top'][0]
    YPT = t2['p_top'][1]                     # the primary's upper terminal
    S.wire(ax2, [(XRAIL, YT), (XLEG, YT)])
    S.dot(ax2, XRAIL, YT)
    S.label(ax2, XRAIL + 0.45, YT + 0.60, 'V$_{in}$', size=FS, ha='left')
    S.wire(ax2, [(XRAIL, YB), (XP_L, YB)])
    #  Below the rail, not on it.  Drawn at the rail's own height the
    #  widest bar lies along the wire and the symbol reads as a blob.
    S.gnd(ax2, XRAIL, YB, lead=0.45)
    #  Two switches of 2.0 between rails 6.1 apart: 0.1 of lead at each
    #  rail and 0.5 either side of the midpoint node.
    X.mosfet(ax2, XLEG, 3.30, 'S$_1$', state='plain', h=2.0, gate=1.5,
             body=False, coss=False, size=FS)
    X.mosfet(ax2, XLEG, 0.00, 'S$_2$', state='plain', h=2.0, gate=1.5,
             body=False, coss=False, size=FS)
    S.wire(ax2, [(XLEG, YT), (XLEG, 4.30)])
    S.wire(ax2, [(XLEG, 2.30), (XLEG, 1.00)])          # the midpoint leg
    S.wire(ax2, [(XLEG, -1.00), (XLEG, YB)])
    S.dot(ax2, XLEG, YB)

    c, d = S.cap(ax2, 1.30, YM, None)
    S.label(ax2, 1.30, YM - 1.05, 'C$_r$', size=FS - 1, color=GREY)
    a, b = S.ind(ax2, 2.95, YM, None, s=1.35)
    S.label(ax2, 2.95, YM - 1.05, 'L$_r$', size=FS - 1, color=GREY)
    S.wire(ax2, [(XLEG, YM), c])
    S.dot(ax2, XLEG, YM)
    S.wire(ax2, [d, a])
    S.wire(ax2, [b, (4.10, YM), (4.10, YPT), (XP_L, YPT)])

    S.wire(ax2, [t2['p_bot'], (XP_L, YB)])
    #  L_m is drawn as its own shunt because its current is one of the four
    #  rows below; without it on the page i_mu has no branch to be the
    #  current of.  Its name goes beside the COIL, at the coil's own height:
    #  above the coil it landed on the riser corner and on i_p.
    S.shunt(ax2, 5.10, YPT, YB, 'ind', None, frac=0.42)
    #  In the channel between the riser at 4.10 and the coil at 5.10 -
    #  to the right of the coil it sat against the primary's lead line.
    S.label(ax2, 4.60, YM - 0.40, 'L$_m$', size=FS - 1, ha='center')
    S.dot(ax2, 5.10, YPT)
    S.dot(ax2, 5.10, YB)

    #  A BLOCK here, not a diode.  This design rectifies with a centre tap
    #  and its two halves conduct on alternate half periods, so the winding
    #  current below is bipolar; one diode on one winding cannot carry that
    #  and the panel would have contradicted its own waveform.  In the
    #  flyback panel the rectifier is drawn out because its orientation is
    #  the entire mechanism; here any full-wave rectifier does the same
    #  thing to this argument.
    bl, _ = S.box(ax2, 11.20, 2.50, 2.6, 4.2, 'rectifier\n+ load', size=FS - 1)
    S.wire(ax2, [t2['s_top'], (bl[0], t2['s_top'][1])])
    #  straight into the block at the terminal's own height: routed down
    #  to the return line it ended below the block, in the air
    S.wire(ax2, [t2['s_bot'], (bl[0], t2['s_bot'][1])])
    #  i_p is the current BEFORE L_m takes its share - the tank current -
    #  because the row below reads i_mu = i_p - i_s.  Beside the winding,
    #  where it used to be, it named the branch that carries i_s.
    _ihead(ax2, 4.60, YPT, 'r', 'i$_p$', MAG, (4.60, YPT + 0.62), size=FS)
    _ihead(ax2, 5.10, (YPT + 2.55) / 2.0, 'd', 'i$_\\mu$', CYA,
           (5.40, (YPT + 2.55) / 2.0), ha='left', size=FS)
    xa = (XS_L + bl[0]) / 2.0
    _ihead(ax2, xa, t2['s_top'][1], 'r', 'i$_s$', GRN,
           (xa, t2['s_top'][1] + 0.62), size=FS)
    ax2.text(5.4, -2.60, 'both windings conduct at once',
             ha='center', va='center', fontsize=10.2, color=GREY)

    # ======================================================== the four rows
    HS, G, Y0 = (0.072, 0.090, 0.072, 0.125), 0.032, 0.640
    rows = ['gates', 'i$_p$ , i$_s$', 'i$_\\mu$', '$\\Phi$']
    axl, axr, y = [], [], Y0
    for nm, h in zip(rows, HS):
        y -= h + G
        axl.append(_wave_ax(fig, [XL, y, WW, h], 0, 2, -1.25, 1.25, nm))
        axr.append(_wave_ax(fig, [XR, y, WW, h], 0, 2, -1.25, 1.25, nm))

    def cap_(ax, t):
        ax.text(0.5, 1.13, t, transform=ax.transAxes, ha='center',
                va='bottom', fontsize=10.0, color=GREY)

    def flux(ax, t, fp, fs, fn, lo, hi):
        """the two contributions, their sum, and the gap between.

        The band between the primary's own curve and the sum is exactly
        what the secondary's ampere-turns did to the core, drawn as an
        area rather than measured at one instant with an arrow - which is
        what this row first did, and one instant is not a cancellation.
        The same band means two things, and that is the point of the
        figure: in the LLC it is flux the secondary takes away at the
        same moment; in the flyback it is flux the secondary holds up
        after the primary has stopped.
        """
        ax.set_ylim(lo, hi)
        #  Only ONE fill.  A second one under the sum overlapped this band
        #  wherever the primary's own curve is zero - the whole of the
        #  flyback's off-time - and purple under green came out a muddy
        #  grey that read as a third quantity.
        ax.fill_between(t, fn, fp, color=GRN, alpha=0.26, lw=0)
        ax.plot(t, fp, color=MAG, lw=1.5, ls=(0, (5, 2.6)))
        ax.plot(t, fs, color=GRN, lw=1.5, ls=(0, (5, 2.6)))
        ax.plot(t, fn, color=PUR, lw=2.4)

    #  ---- flyback, DISCONTINUOUS conduction, one period drawn twice.
    #  It was continuous here and discontinuous in Figure 18 (an_flux_steps)
    #  beside it, so the two flyback columns disagreed (2026-09-25, user).
    #  DCM is the one the argument needs: the flux starts from zero every
    #  period, all of it is stored and all of it delivered, and B_pk is set
    #  by I_p,pk alone.
    D, DS = 0.40, 0.40                      # on time, secondary conduction
    t = np.linspace(0, 2, 4000)
    ph = t % 1.0
    on = ph < D
    sec = (ph >= D) & (ph < D + DS)
    hi = 1.0
    ip = np.where(on, hi * ph / D, 0.0)
    isr = np.where(sec, hi * (1.0 - (ph - D) / DS), 0.0)
    #  The dots are inverted, so the secondary ampere-turns ADD: they take
    #  over holding the flux up when the primary stops carrying it.
    imu = ip + isr

    axl[0].set_ylim(-0.30, 1.45)
    g = np.where(on, 1.0, 0.0)
    axl[0].fill_between(t, 0.0, g * 0.9, color=YEL, lw=0)
    axl[0].plot(t, g * 0.9, color=NAVY, lw=1.5)
    axl[0].text(0.5 * D, 0.45, 'S', ha='center', va='center',
                fontsize=9.6, color=NAVY, path_effects=HALO, zorder=9)
    cap_(axl[0], 'S on for part of the period, off for the rest')

    axl[1].set_ylim(-0.22, 1.38)
    axl[1].plot(t, ip, color=MAG, lw=2.0)
    axl[1].plot(t, isr, color=GRN, lw=2.0, ls=(0, (4, 2.4)))
    cap_(axl[1], 'i$_p$ solid, i$_s$ dashed and referred - they never '
                 'overlap')

    axl[2].set_ylim(-0.22, 1.38)
    axl[2].plot(t, imu, color=CYA, lw=2.2)
    cap_(axl[2], 'i$_\\mu$ = i$_p$ + i$_s$ - only one is ever flowing')

    flux(axl[3], t, ip, isr, imu, -0.62, 1.42)
    axl[3].annotate('the band is $\\Phi_s$ holding the flux up\n'
                    'after the primary has stopped',
                    xy=(0.60, 0.22), xytext=(1.30, -0.40),
                    fontsize=9.4, color=GREY, ha='center', va='center',
                    arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.2,
                                    connectionstyle='arc3,rad=0.16'),
                    path_effects=HALO, zorder=9)
    cap_(axl[3], 'own $\\Phi$ dashed, the sum solid, the difference shaded')

    #  ---- LLC, the eight-interval model with the design's own currents
    tc, e, ilm, ilr, io, _ = _cycle(0.70, V['lam'], V['Icomp'], V['ILm'])
    T = np.concatenate([tc, tc + 1.0])

    def rep(u):
        return np.concatenate([u, u])

    sg = rep(np.where(tc < 0.5, 1.0, -1.0))
    ILM, ILR, IO = rep(ilm), rep(ilr), rep(io) * sg
    m = max(abs(ILR).max(), 1e-9)

    axr[0].set_ylim(-0.30, 2.75)
    g1 = rep(np.where(tc < e[2], 1.0, 0.0))
    g2 = rep(np.where((tc >= e[4]) & (tc < e[6]), 1.0, 0.0))
    #  S1 on the upper track: it is the high-side switch, and the two
    #  tracks are read the way the leg is drawn.
    axr[0].fill_between(T, 1.35, 1.35 + g1 * 0.85, color=YEL, lw=0)
    axr[0].plot(T, 1.35 + g1 * 0.85, color=NAVY, lw=1.4)
    axr[0].fill_between(T, 0.0, g2 * 0.85, color=YEL, lw=0)
    axr[0].plot(T, g2 * 0.85, color=NAVY, lw=1.4)
    axr[0].text(0.5 * e[1], 1.77, 'S$_1$', ha='center', va='center',
                fontsize=9.6, color=NAVY, path_effects=HALO, zorder=9)
    axr[0].text(0.5 + 0.5 * e[1], 0.42, 'S$_2$', ha='center', va='center',
                fontsize=9.6, color=NAVY, path_effects=HALO, zorder=9)
    cap_(axr[0], 'the two switches, half a period apart')

    axr[1].set_ylim(-1.38, 1.38)
    for k in (0, 1):
        axr[1].axvspan(k + e[0], k + e[1], color=GRN, alpha=0.10, lw=0)
        axr[1].axvspan(k + e[4], k + e[5], color=GRN, alpha=0.10, lw=0)
    axr[1].plot(T, ILR / m, color=MAG, lw=2.0)
    axr[1].plot(T, IO / m, color=GRN, lw=2.0, ls=(0, (4, 2.4)))
    cap_(axr[1], 'shaded: both conducting, and their ampere-turns oppose')

    axr[2].set_ylim(-1.38, 1.38)
    axr[2].plot(T, ILM / m, color=CYA, lw=2.2)
    cap_(axr[2], 'i$_\\mu$ = i$_p$ $-$ i$_s$ - what did not cancel')

    flux(axr[3], T, ILR / m, -IO / m, ILM / m, -1.55, 1.42)
    #  The band is widest where the secondary's contribution is largest,
    #  so the leader is aimed there rather than at a place chosen by eye.
    kx = int(np.argmax(IO[:len(tc)]))
    axr[3].annotate('the band is $\\Phi_s$ cancelling $\\Phi_p$\n'
                    'while both windings conduct',
                    xy=(float(T[kx]), 0.5 * float(ILM[kx] + ILR[kx]) / m),
                    xytext=(1.06, -1.16),
                    fontsize=9.4, color=GREY, ha='center', va='center',
                    arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.2,
                                    connectionstyle='arc3,rad=-0.18'),
                    path_effects=HALO, zorder=9)
    cap_(axr[3], 'own $\\Phi$ dashed, the sum solid, the difference shaded')

    #  Short on purpose.  The document caption under this figure carries
    #  the reading instructions; repeating them here gave the page two
    #  dense grey paragraphs one above the other.
    foot(fig, 'Row three is the answer. In the flyback the magnetising '
              'current IS the winding current, so the flux follows the peak '
              'current. In the LLC the two windings conduct together and '
              'their ampere-turns oppose, so the core carries only the '
              'difference.')
    save(fig, 'an_flyback_llc')


# --------------------------------------- 15  ampere-turns and the dc test
def an_mmf(save, foot):
    """Why the saturation test current is not the primary peak.

    The same core twice - in service and on the vendor's bench with the
    secondary open - and then the three currents the reader has to keep
    apart, drawn to scale against each other.

    The windings are on opposite legs here, and on the real transformer
    they are both on the centre leg.  Separating them changes nothing in
    Ampere's law round the closed path, and it is the only way to show
    two ampere-turns opposing on one drawing.
    """
    import an_pdf as _A
    V = _A.V
    fig = plt.figure(figsize=(9.35, 6.55))

    def core(ax, live):
        S.frame(ax, -3.6, 9.4, -1.7, 8.4)
        ax.add_patch(Rectangle((0.0, 0.0), 5.6, 6.6, fc='#dfe4e9',
                               ec='#6f7883', lw=1.2, zorder=2))
        ax.add_patch(Rectangle((1.2, 1.2), 3.2, 4.2, fc='white',
                               ec='#6f7883', lw=1.0, zorder=3))
        #  The flux path runs along the LEG AND YOKE CENTRELINES, which
        #  means it passes inside both windings.  That is the point: it is
        #  the closed path Ampere's law is taken round, and a loop drawn in
        #  the window instead - which is what this first said - encircles
        #  neither winding and links no current at all.  Drawn under the
        #  coils, which are at zorder 4.
        ax.add_patch(Rectangle((0.6, 0.6), 4.4, 5.4, fc='none', ec=PUR,
                               lw=1.6, ls=(0, (5, 3)), zorder=2.5))
        for x0, x1, yy in ((2.60, 3.06, 6.0), (3.06, 2.60, 0.6)):
            ax.add_patch(FancyArrowPatch((x0, yy), (x1, yy),
                                         arrowstyle='-|>', mutation_scale=14,
                                         color=PUR, lw=1.6, zorder=2.5,
                                         shrinkA=0, shrinkB=0))
        S.label(ax, 2.80, 3.30, '$\\Phi$', size=14, color=PUR)

        #  Eight turns, not four: at four the bumps came out four times
        #  the size every other winding in the document is drawn at.  They
        #  are transformer windings, so they are counted as such.
        mark = len(getattr(ax, '_syms', []))
        X.coil(ax, 0.6, 1.9, 4.7, n=8, side=1, color=MAG)
        X.coil(ax, 5.0, 1.9, 4.7, n=8, side=-1, color=GRN)
        syms = getattr(ax, '_syms', [])
        for i in range(mark, len(syms)):
            if syms[i][0] == 'turn':
                syms[i] = ('winding',) + syms[i][1:]

        #  The leads leave at the height of the winding they belong to.
        #  Taken up over the yoke first, as they were, they ran along the
        #  inside of the core for most of its width.
        S.wire(ax, [(0.6, 4.7), (-2.9, 4.7)], color=MAG)
        S.wire(ax, [(0.6, 1.9), (-2.9, 1.9)], color=MAG)
        S.dot(ax, -2.9, 4.7, color=MAG)
        S.dot(ax, -2.9, 1.9, color=MAG)
        S.label(ax, -0.30, 3.30, 'N$_p$', size=11, color=MAG, ha='right')
        S.label(ax, 5.90, 3.30, 'N$_s$', size=11, color=GRN, ha='left')
        #  The polarity dots ARE the sense convention - a flat drawing of a
        #  winding cannot show handedness, and the equation below the panel
        #  is written against these two dots.
        S.dot(ax, 0.95, 4.42, color=MAG, ms=4.8)
        S.dot(ax, 4.65, 4.42, color=GRN, ms=4.8)

        if live:
            S.wire(ax, [(5.0, 4.7), (8.1, 4.7)], color=GRN)
            S.wire(ax, [(5.0, 1.9), (8.1, 1.9)], color=GRN)
            S.shunt(ax, 8.1, 4.7, 1.9, 'res', None, color=GRN)
            S.label(ax, 8.62, 3.30, 'load', size=10.5, color=GRN, ha='left')
        else:
            #  Open means open: the leads stop at their terminals and
            #  nothing is drawn between them.  Anything across the gap,
            #  dashed or not, would read as a connection, which is the one
            #  thing this panel must not say.
            S.wire(ax, [(5.0, 4.7), (7.4, 4.7)], color=GRN)
            S.wire(ax, [(5.0, 1.9), (7.4, 1.9)], color=GRN)
            S.dot(ax, 7.4, 4.7, color=GRN)
            S.dot(ax, 7.4, 1.9, color=GRN)
            S.label(ax, 8.30, 3.66, 'open', size=11, color=GREY)
            S.label(ax, 8.30, 2.94, 'i$_s$ = 0', size=10.5, color=GRN)

    # --------------------------------------------------------- in service
    ax = fig.add_axes([0.012, 0.400, 0.470, 0.510])
    core(ax, True)
    S.label(ax, 2.8, 7.95, 'IN SERVICE', size=11.5, color=NAVY,
            weight='bold')
    _call(ax, (-1.6, 4.7), (-3.4, 7.10), 'i$_p$ in', color=MAG, size=10.5,
          ha='left')
    _call(ax, (6.6, 4.7), (5.4, 7.10), 'i$_s$ out', color=GRN, size=10.5,
          ha='left')
    ax.text(2.8, -1.25, 'N$_p$ i$_p$  $-$  N$_s$ i$_s$  =  N$_p$ i$_\\mu$',
            ha='center', va='center', fontsize=12.5, color=NAVY,
            bbox=dict(boxstyle='round,pad=0.34', fc='white', ec=NAVY,
                      lw=1.1))

    # ---------------------------------------------- on the bench, open
    ax2 = fig.add_axes([0.512, 0.400, 0.470, 0.510])
    core(ax2, False)
    S.label(ax2, 2.8, 7.95, 'ON THE BENCH, ALL OTHER WINDINGS OPEN', size=11.5,
            color=NAVY, weight='bold')
    _call(ax2, (-1.6, 4.7), (-3.4, 7.10), 'I$_{dc}$ in', color=MAG,
          size=10.5, ha='left')
    ax2.text(2.8, -1.25, 'N$_p$ I$_{dc}$  $-$  0  =  N$_p$ i$_\\mu$',
             ha='center', va='center', fontsize=12.5, color=NAVY,
             bbox=dict(boxstyle='round,pad=0.34', fc='white', ec=NAVY,
                       lw=1.1))

    # ------------------------------------------------- the three currents
    axb = fig.add_axes([0.235, 0.090, 0.700, 0.220])
    vals = [V['Icomp'], V['Isatspec'], V['ILm']]
    cols = [MAG, NAVY, CYA]
    names = ['I$_{Lr,pk}$   tank peak',
             'I$_{sat}$   on the specification',
             'i$_{\\mu,pk}$   magnetising peak']
    notes = ['a flyback habit would specify this',
             'i$_{\\mu,pk}$ raised to the V$_{OVP2}$ ceiling',
             'the only one that sets the flux']
    top = max(vals)
    axb.barh([2, 1, 0], vals, height=0.54, color=cols, alpha=0.85, lw=0)
    axb.set_yticks([2, 1, 0])
    axb.set_yticklabels(names, fontsize=10.2, color=NAVY)
    axb.set_xlim(0, top * 2.95)
    axb.set_ylim(-0.66, 2.66)
    axb.set_xticks([])
    #  The document style has horizontal grid lines on by default, and
    #  here they ran straight through the three labels.
    axb.grid(False)
    axb.tick_params(axis='y', length=0)
    for sp in ('top', 'right', 'bottom', 'left'):
        axb.spines[sp].set_visible(False)
    #  The values sit just past their own bar and the notes in one column
    #  clear of the longest of them, so nothing lands on anything else.
    for yy, vv, cc, nt in zip((2, 1, 0), vals, cols, notes):
        axb.text(vv + top * 0.025, yy, '%.2f A' % vv, va='center',
                 ha='left', fontsize=10.5, color=cc, fontweight='bold')
        axb.text(top * 1.52, yy, nt, va='center', ha='left', fontsize=10.0,
                 color=GREY)

    foot(fig, 'With the secondary open there is nothing to cancel, so the '
              'whole of the test current is magnetising current - which is '
              'exactly the flyback condition. That is why the bench test '
              'reaches the design flux at %.2f A and not at the %.2f A tank '
              'peak: handing the tank peak over would ask the vendor for '
              '%.2f times the flux the core ever sees in service.'
              % (V['ILm'], V['Icomp'], V['Icomp'] / V['ILm']))
    save(fig, 'an_mmf')


# ------------------------------------ 16  the transformer spec, read off the waveforms
def an_xfmr_read(save, foot):
    """Every transformer specification item, and where on the waveform it is.

    Three traces of one switching period at the worst cycle (line peak,
    minimum equivalent input, full load) from the same eight-interval
    model as the mode sheets; under them the two winding rms currents over
    the input half cycle at all six input voltages (the HB edge draws the
    most, which is why the table is read there), and the bench condition
    of the DC-overlap test.  The circled numbers are the rows of the table
    that follows the figure in the note - the figure says WHERE, the
    table says what it sets.

    Every value is from an_pdf.V (the sheet) or from l6790.sweep at the
    design point; the traces are drawn to the model and then labelled
    with the sheet's numbers, as the other waveform figures are.
    """
    import an_pdf as _A
    import l6790 as _L
    V, R = _A.V, _A.R
    ratio = V['fswA'] / V['fr']                 # worst cycle: HB corner, theta = pi/2
    t, e, ilm, ilr, io, _ = _cycle(ratio, V['lam'], V['Icomp'], V['ILm'])
    t1 = e[1]

    fig = plt.figure(figsize=(9.35, 9.9))
    X0, W = 0.115, 0.845
    _pu = '\none unit' if V['nser'] > 1 else ''
    rows = [('i$_p$' + _pu, 0.211), ('i$_{NS3}$, i$_{NS2}$' + _pu, 0.148),
            ('v$_{NS}$', 0.135)]
    y = 0.965
    axs = []
    for nm, h in rows:
        y -= h + 0.022
        axs.append(_wave_ax(fig, [X0, y, W, h], 0, 1, -1.25, 1.25, nm))

    #  interval names once, above the first trace
    for x, nm, c, ha in ((e[1] / 2, 'power delivery', MAG, 'center'),
                         (e[2] - 0.004, 'freewheeling', CYA, 'right'),
                         (e[2] + 0.004, 'dead time', GREY, 'left')):
        #  on a white ground: the interval boundaries are dotted through
        #  this height and ran across 'freewheeling' and 'dead time'
        axs[0].text(x, 1.30, nm, ha=ha, va='bottom', fontsize=9.4, color=c,
                    zorder=5, bbox=dict(boxstyle='square,pad=0.08',
                                        fc='white', ec='none'))
    for a in axs:
        for x in (e[1], e[2], e[4], e[5], e[6]):
            a.axvline(x, color=GREY, lw=0.7, ls=(0, (2, 3)), zorder=0)

    def ring(ax, n, x, y, c, dx=0.0, dy=0.0):
        """a circled number, in axes-data units of the trace axis"""
        ax.annotate('%d' % n, (x, y), xytext=(x + dx, y + dy),
                    textcoords='data', ha='center', va='center',
                    fontsize=9.4, color='white', fontweight='bold', zorder=10,
                    bbox=dict(boxstyle='circle,pad=0.25', fc=c, ec=c, lw=0.8))

    #  ---------------- row 1: primary winding current, the whole current
    a = axs[0]
    m = V['Icomp']
    a.set_ylim(-1.62, 1.45)
    a.plot(t, ilr / m, color=NAVY, lw=2.1, zorder=3)
    a.plot(t, ilm / m, color=PUR, lw=1.7, ls=(0, (4, 2.4)), zorder=3)
    ip = int(np.argmax(ilr[:len(t) // 2]))
    a.plot([t[ip]], [ilr[ip] / m], 'o', color=NAVY, ms=5, zorder=5)
    ring(a, 1, t[ip], 1.0, NAVY, dx=-0.06, dy=0.10)
    #  I_Lr,pk as the text and the tables call it; I_p,pk is the flyback's
    a.text(t[ip] + 0.025, 1.06, 'I$_{Lr,pk}$ = %.1f A' % V['Icomp'], ha='left',
           va='center', fontsize=9.6, color=NAVY, path_effects=HALO, zorder=9)
    #  the magnetising peak is AT the switching instant, on the dashed trace
    a.plot([0.5], [V['ILm'] / m], 'o', color=PUR, ms=5, zorder=5)
    ring(a, 3, 0.5, V['ILm'] / m, PUR, dx=0.065, dy=0.30)
    a.text(0.585, V['ILm'] / m + 0.30, 'I$_{Lm,pk}$ = %.1f A  —  the flux '
           'peaks here' % V['ILm'], ha='left', va='center', fontsize=9.6,
           color=PUR, path_effects=HALO, zorder=9)
    a.text(0.30, -0.42, 'i$_p$ = i$_{Lm}$ + reflected load',
           ha='center', va='center', fontsize=9.4, color=NAVY,
           path_effects=HALO, zorder=9)
    a.text(0.30, -0.70, 'i$_{Lm}$ dashed', ha='center', va='center',
           fontsize=9.4, color=PUR, path_effects=HALO, zorder=9)
    #  the rms window is the WHOLE period, drawn as a bracket under the trace
    for x0, x1 in ((0.0, 1.0),):
        a.plot([x0, x0, x1, x1], [-1.06, -1.16, -1.16, -1.06], color=NAVY,
               lw=1.0, zorder=4)
    ring(a, 2, 0.5, -1.16, NAVY)
    a.text(0.5, -1.27, 'rms over the whole period: %.1f A on this cycle'
           % V['Iprims'], ha='center', va='top', fontsize=9.6, color=NAVY,
           path_effects=HALO, zorder=9)

    #  ---------------- row 2: the two secondary windings of one unit
    a = axs[1]
    a.set_ylim(-0.52, 1.42)
    s = io / max(io.max(), 1e-9)
    s2 = np.where(t < 0.5, s, 0.0)
    s3 = np.where(t >= 0.5, s, 0.0)
    a.plot(t, s2, color=MAG, lw=2.0, zorder=3)
    a.plot(t, s3, color=GRN, lw=2.0, zorder=3)
    a.fill_between(t, 0, s2, color=MAG, alpha=0.10, lw=0)
    a.fill_between(t, 0, s3, color=GRN, alpha=0.10, lw=0)
    #  NS3 first.  i_p > 0 enters the primary dot, and the secondary dot
    #  that current leaves by is NS3's start - the tap (Figure an_xfmr_pins;
    #  the design text: the tap joins the finish of NS2 to the start of
    #  NS3).  So NS3, the lower half, N_s2 of Figure 1, conducts while S1
    #  and S4 are on.  This row had the two names the other way round.
    a.text(t1 / 2, 0.30, 'NS3', ha='center', va='center', fontsize=9.6,
           color=MAG, path_effects=HALO, zorder=9)
    a.text(0.5 + t1 / 2, 0.30, 'NS2', ha='center', va='center', fontsize=9.6,
           color=GRN, path_effects=HALO, zorder=9)
    a.plot([t1 / 2], [1.0], 'o', color=MAG, ms=5, zorder=5)
    ring(a, 4, t1 / 2, 1.0, MAG, dx=-0.055, dy=0.22)
    a.text(t1 / 2 - 0.03, 1.22, ('I$_{sec,pk}$ = %.1f A per unit  (%.0f A per '
           'rectifier leg)' % (V['Isecpkx'], V['Isec'])) if V['nser'] > 1
           else 'I$_{sec,pk}$ = %.1f A, each winding in its half period'
           % V['Isec'], ha='left',
           va='center', fontsize=9.6, color=MAG, path_effects=HALO, zorder=9)
    #  each winding conducts once per period; its rms counts the idle half
    a.plot([0.0, 0.0, 1.0, 1.0], [-0.06, -0.15, -0.15, -0.06], color=MAG,
           lw=1.0, zorder=4)
    ring(a, 5, 0.5, -0.15, MAG)
    a.text(0.5, -0.26, 'one pulse per period per winding: the rms is taken '
           'over the whole period, idle half included', ha='center',
           va='top', fontsize=9.4, color=MAG, path_effects=HALO, zorder=9)

    #  ---------------- row 3: secondary winding voltage and its volt-seconds
    a = axs[2]
    a.set_ylim(-1.66, 1.55)
    dil = np.gradient(ilm, t)
    slope = dil[len(t) // 8]                    # inside the ramp
    v = dil / slope
    a.plot(t, v, color=NAVY, lw=2.0, zorder=3)
    a.fill_between(t, 0, np.where(t <= t1, v, 0.0), color=GOLD, alpha=0.22,
                   lw=0, zorder=2)
    a.fill_between(t, 0, np.where((t >= 0.5) & (t <= 0.5 + t1), v, 0.0),
                   color=GOLD, alpha=0.22, lw=0, zorder=2)
    a.text(-0.012, 1.0, '+V$_{o,eff}$', transform=a.get_yaxis_transform(),
           ha='right', va='center', fontsize=9.4, color=GREY)
    a.text(-0.012, -1.0, '−V$_{o,eff}$', transform=a.get_yaxis_transform(),
           ha='right', va='center', fontsize=9.4, color=GREY)
    ring(a, 6, t1 / 2, 0.5, GOLD)
    a.text(t1 / 2 + 0.035, 0.5, 'V$_{o,eff}$ × T$_r$/2 = 2 N$_s$ A$_e$ B$_{pk}$'
           '  →  B$_{pk}$ = %.0f mT' % V['Bpk'], ha='left', va='center',
           fontsize=9.6, color=GOLD, path_effects=HALO, zorder=9)
    a.text(0.5 + t1 / 2, -0.5, 'the same area, the other way',
           ha='center', va='center', fontsize=9.4, color=GOLD,
           path_effects=HALO, zorder=9)
    _call(a, (e[2] + 0.012, float(np.interp(e[2] + 0.012, t, v))),
          (0.60, 0.30), 'rectifier off: L$_m$ still sees a little',
          color=GREY, size=9.4)
    #  a time scale for the three rows, under the last one
    a.annotate('', xy=(1.0, -1.34), xytext=(0.0, -1.34),
               arrowprops=dict(arrowstyle='<->', color=GREY, lw=0.9))
    a.text(0.5, -1.40, 'one switching period  1/f$_{sw}$', ha='center',
           va='top', fontsize=9.4, color=GREY, path_effects=HALO, zorder=9)
    a.annotate('', xy=(t1, 1.50), xytext=(0.0, 1.50),
               arrowprops=dict(arrowstyle='<->', color=GOLD, lw=0.9))
    a.text(t1 / 2, 1.42, 'T$_r$/2', ha='center', va='top', fontsize=9.4,
           color=GOLD, path_effects=HALO, zorder=9)

    #  ---------------- lower left and centre: the two rms currents over the
    #  input half cycle, at all six input voltages.  Drawn at the HB edge
    #  alone the reader asked why (2026-09-22): the answer is that the HB
    #  edge draws the most current in both windings, so the table is read
    #  there - and the other five are on the picture to show it.  Two
    #  panels, because the two windings' currents are not the same size;
    #  every trace is named in the legend, not on the curves, so nothing
    #  sits on a line.
    COLS = [MAG, '#D97706', CYA, GRN, NAVY, PUR]
    conds = _L.line_conditions(R)
    curves = []
    for (nm, veq, _m), col in zip(conds, COLS):
        rws, _s = _L.sweep(R, veq, 1.0)
        rws = [r for r in rws if r]
        th = np.array([r['th'] for r in rws])
        thd = np.degrees(np.concatenate([th, np.pi - th[::-1]]))
        mir = lambda q: np.concatenate([q, q[::-1]])
        pri = mir(np.array([r['Ipri'] for r in rws]))
        sec = mir(np.array([r['Isec_w'] for r in rws])) / V['nser']
        curves.append((nm, col, thd, pri, sec))
    Y0, H = 0.125, 0.215
    b = fig.add_axes([X0, Y0, 0.245, H])
    b2 = fig.add_axes([0.430, Y0, 0.245, H])
    for ax in (b, b2):
        ax.grid(color='#C4C8CF', lw=0.6, zorder=0)
        ax.set_axisbelow(True)
        ax.set_xlim(0, 180)
        ax.set_xticks([0, 45, 90, 135, 180])
        ax.set_xlabel(u'line phase \u03b8  [deg]', fontsize=9.4)
        ax.set_ylabel('[A]', fontsize=9.4)
        ax.tick_params(labelsize=9.4)
    hs = []
    for nm, col, thd, pri, sec in curves:
        b.plot(thd, pri, color=col, lw=1.7, zorder=3)
        b2.plot(thd, sec, color=col, lw=1.7, zorder=3)
        hs.append((Line2D([], [], color=col, lw=1.7), nm))
    b.axhline(V['Iprilc'], color=NAVY, lw=1.1, ls=(0, (1, 2)), zorder=2)
    b2.axhline(V['Isecx'], color=MAG, lw=1.1, ls=(0, (1, 2)), zorder=2)
    hs.append((Line2D([], [], color=NAVY, lw=1.1, ls=(0, (1, 2))),
               u'line-cycle rms at the HB edge: %.1f A \u2192 primary Cu'
               % V['Iprilc']))
    hs.append((Line2D([], [], color=MAG, lw=1.1, ls=(0, (1, 2))),
               u'line-cycle rms at the HB edge: %.1f A \u2192 secondary Cu'
               % V['Isecx']))
    pmax = max(c[3].max() for c in curves)
    smax = max(c[4].max() for c in curves)
    b.set_ylim(0, 1.32 * pmax)
    b2.set_ylim(0, 1.30 * max(smax, V['Isecx']))
    b.set_title('i$_p$ rms per switching cycle', fontsize=9.6, color=NAVY)
    b2.set_title(('i$_{NS}$ rms per unit, per switching cycle'
                  if V['nser'] > 1 else
                  'i$_{NS}$ rms per switching cycle, each winding'),
                 fontsize=9.6, color=MAG)
    nm0, col0, thd0, pri0, sec0 = curves[0]      # the HB edge: the worst
    ring(b, 2, 90, pri0.max(), NAVY, dx=0, dy=0.12 * pmax)
    ring(b2, 5, 152, float(np.interp(152, thd0, sec0)), MAG, dx=-12,
         dy=0.10 * smax)
    fig.legend([h for h, _n in hs], [n for _h, n in hs], loc='lower center',
               ncol=3, fontsize=9.3, frameon=False,
               bbox_to_anchor=(0.5, 0.002),
               title='over the input half cycle at full load, at the six '
                     'input voltages; the HB edge draws the most',
               title_fontsize=9.4)

    #  ---------------- lower right: the bench, and the one current it wants
    c = fig.add_axes([0.750, Y0, 0.225, H])
    Is = V['Isatspec']
    c.set_xlim(0, 1.45 * max(Is, V['Icomp']))
    c.set_ylim(0, 1.34)
    c.set_xticks([0, 10, 20])
    c.grid(color='#C4C8CF', lw=0.6, zorder=0)
    c.set_axisbelow(True)
    c.set_yticks([0.9, 1.0])
    c.set_yticklabels(['90 %', '100 %'], fontsize=9.4)
    c.set_xlabel('dc current in the primary  [A]', fontsize=9.4)
    c.tick_params(labelsize=9.4)
    c.set_title('DC-overlap test: all other windings open', fontsize=9.6, color=NAVY)
    c.axhline(1.0, color=GREY, lw=1.0)
    c.fill_between([0, Is], 0, 0.9, color='#f3c9c9', lw=0, zorder=1)
    c.plot([0, Is], [0.9, 0.9], color=MAG, lw=1.6, zorder=3)
    c.plot([Is, Is], [0.0, 0.9], color=MAG, lw=1.6, zorder=3)
    #  between the 0 and 10 A grid lines, so no line runs through it
    c.text(5.0, 0.36, 'L at NP1\nmust stay\nabove', ha='center',
           va='center', fontsize=9.4, color=MAG, zorder=4,
           path_effects=HALO)             # it sits on the shaded region
    c.text(0.4, 1.02, 'L$_{open}$ initial', ha='left', va='bottom',
           fontsize=9.4, color=GREY)
    #  the test current is named ABOVE its own line, where nothing else is:
    #  written beside it at 90 % it sat on the ring, on the arrow and on
    #  the "not 18.3 A" label all at once (2026-09-22, user)
    c.text(Is, 1.12, '%.1f A' % Is, ha='center', va='bottom', fontsize=9.6,
           color=MAG, fontweight='bold')
    ring(c, 7, Is, 0.9, MAG, dx=0.0, dy=0.17)
    c.plot([V['ILm']], [0.9], 'o', color=PUR, ms=5, zorder=5)
    c.annotate('', xy=(Is - 0.15, 0.68), xytext=(V['ILm'] + 0.15, 0.68),
               arrowprops=dict(arrowstyle='-|>', color=PUR, lw=1.2))
    c.text(Is - 0.2, 0.71, u'\u00d7 V$_{OVP2}$/V$_{out}$',
           ha='right', va='bottom', fontsize=9.4, color=PUR,
           path_effects=HALO, zorder=9)
    ring(c, 3, V['ILm'], 0.9, PUR, dx=-1.7, dy=0.20)
    c.plot([V['Icomp']], [0.9], 'x', color=NAVY, ms=7, mew=1.8, zorder=5)
    c.annotate('not %.1f A' % V['Icomp'],
               xy=(V['Icomp'], 0.88), xytext=(V['Icomp'] - 0.3, 0.58),
               ha='right', va='top', fontsize=9.4, color=NAVY,
               arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=1.1),
               path_effects=HALO, zorder=9)

    foot(fig, 'Worst switching cycle of the design: line peak at the HB '
              'edge (%.0f Vac, half bridge), full load, f_sw/f_r = %.2f. The traces '
              'are the eight-interval model of the mode figures, labelled '
              'with the sheet values; the lower panels are the design sweep '
              'over the input half cycle at the six input voltages. Circled '
              'numbers are the rows '
              'of the reading table in the text.' % (V['Veqlo'], ratio))
    save(fig, 'an_xfmr_read')



# ------------------------------------ 17  one unit: symbol, windings and bobbin pins
def an_xfmr_pins(save, foot):
    """Which winding comes out on which pin of the chosen coil former.

    Left: the schematic symbol of the transformer with every terminal
    carrying its pin numbers - primary NP1, the ZCD auxiliary NAUX, and
    the two secondary windings NS2 / NS3 that make the centre tap.
    Below: the coil former
    drawn from its data sheet (bobbin_outline.py reads the vector
    drawing), (A) from below, the pin side - the view the data sheet
    numbers its pins in - and (B) from above, which is the PCB footprint
    on the component side.  Every pin at its specified position, ringed in
    the colour of the winding it carries.  (A side view with arrows, then
    a paragraph on how to read A and B, were tried and dropped: the two
    view titles say it - user, 2026-09-30.)

    Numbers, positions and the assignment all come from cores.BOBBIN -
    the same source the vendor specification and the tables in the note
    are written from - so the three cannot disagree.  The numbering
    direction is the assumption recorded in cores.py and repeated in
    the caption.
    """
    import an_pdf as _A
    import cores as C
    V = _A.V
    B = C.BOBBIN
    COL = {'NP1': MAG, 'NAUX': PUR, 'NS2': GRN, 'NS3': CYA}
    fig = plt.figure(figsize=(9.35, 8.1))

    # ---------------------------------------------------------- symbol
    ax = fig.add_axes([0.272, 0.585, 0.455, 0.400])
    S.frame(ax, -0.6, 16.9, -0.3, 10.9)
    S.label(ax, 7.6, 10.45, 'THE TRANSFORMER, SCHEMATIC', size=11.5,
            color=NAVY, weight='bold')
    XP, XS, XC = 5.2, 7.2, 6.2          # winding columns and the core
    for xx in (XC - 0.2, XC + 0.2):
        ax.plot([xx, xx], [1.1, 9.1], color=GREY, lw=2.4, zorder=3)
    mark = len(getattr(ax, '_syms', []))
    #  one turn radius (0.40) for all four windings: span / (2 n)
    X.coil(ax, XP, 5.4, 8.6, n=4, side=1, color=COL['NP1'])
    X.coil(ax, XP, 1.6, 3.2, n=2, side=1, color=COL['NAUX'])
    X.coil(ax, XS, 5.9, 8.3, n=3, side=-1, color=COL['NS2'])
    X.coil(ax, XS, 1.9, 4.3, n=3, side=-1, color=COL['NS3'])
    syms = getattr(ax, '_syms', [])
    for i in range(mark, len(syms)):
        if syms[i][0] == 'turn':
            syms[i] = ('winding',) + syms[i][1:]

    def pin(x, y, pl, w):
        """a terminal: the pin as a marker (a port), its number(s) beside it"""
        c = COL[w]
        ax.plot([x], [y], 'o', ms=3.4, color=c, zorder=6)
        ax.add_patch(Circle((x, y), 0.30, fc='white', ec=c, lw=1.3,
                            zorder=5))
        S.label(ax, x + (-0.75 if x < XC else 0.75), y, C._plus(pl),
                size=9.8, color=c, weight='bold',
                ha='right' if x < XC else 'left', z=7)

    XL, XR = 2.3, 10.1                  # terminal columns
    a, b = C.PINMAP['NP1']
    S.wire(ax, [(XP, 8.6), (XP, 9.2), (XL, 9.2)], color=COL['NP1'])
    S.wire(ax, [(XP, 5.4), (XP, 4.9), (XL, 4.9)], color=COL['NP1'])
    pin(XL, 9.2, a, 'NP1')
    pin(XL, 4.9, b, 'NP1')
    S.dot(ax, XP - 0.42, 8.20, color=COL['NP1'], ms=4.8)
    S.label(ax, 3.55, 7.05, 'NP1\n%d T' % V['Np'], size=10.5,
            color=COL['NP1'], weight='bold')
    a, b = C.PINMAP['NAUX']
    S.wire(ax, [(XP, 3.2), (XP, 3.7), (XL, 3.7)], color=COL['NAUX'])
    S.wire(ax, [(XP, 1.6), (XP, 1.0), (XL, 1.0)], color=COL['NAUX'])
    pin(XL, 3.7, a, 'NAUX')
    pin(XL, 1.0, b, 'NAUX')
    S.dot(ax, XP - 0.42, 2.80, color=COL['NAUX'], ms=4.8)
    S.label(ax, 3.55, 2.30, 'NAUX\n%d T' % V['Naux'], size=10.5,
            color=COL['NAUX'], weight='bold')
    a2, b2 = C.PINMAP['NS2']
    a3, b3 = C.PINMAP['NS3']
    S.wire(ax, [(XS, 8.3), (XS, 9.2), (XR, 9.2)], color=COL['NS2'])
    pin(XR, 9.2, a2, 'NS2')
    S.dot(ax, XS + 0.42, 7.90, color=COL['NS2'], ms=4.8)
    YT = 5.1
    S.wire(ax, [(XS, 5.9), (XS, YT)], color=COL['NS2'])
    S.wire(ax, [(XS, 4.3), (XS, YT)], color=COL['NS3'])
    S.wire(ax, [(XS, YT), (9.1, YT)], color=NAVY)
    S.dot(ax, XS, YT)
    if tuple(b2) != tuple(a3):          # three wires meet at 9.1 only then
        S.dot(ax, 9.1, YT)
    shared = tuple(b2) == tuple(a3)     # the tap made at the pins
    if shared:
        S.wire(ax, [(9.1, YT), (XR, YT)], color=NAVY)
        ax.add_patch(Circle((XR, YT), 0.30, fc='white', ec=NAVY, lw=1.3,
                            zorder=5))
        ax.plot([XR], [YT], 'o', ms=3.4, color=NAVY, zorder=6)
        S.label(ax, XR + 0.75, YT, C._plus(b2), size=9.8, color=NAVY,
                weight='bold', ha='left', z=7)
    else:
        S.wire(ax, [(9.1, YT), (9.1, 5.65), (XR, 5.65)], color=COL['NS2'])
        S.wire(ax, [(9.1, YT), (9.1, 4.55), (XR, 4.55)], color=COL['NS3'])
        pin(XR, 5.65, b2, 'NS2')
        pin(XR, 4.55, a3, 'NS3')
    S.dot(ax, XS + 0.42, 3.90, color=COL['NS3'], ms=4.8)
    S.wire(ax, [(XS, 1.9), (XS, 1.0), (XR, 1.0)], color=COL['NS3'])
    pin(XR, 1.0, b3, 'NS3')
    S.label(ax, 8.75, 7.55, 'NS2\n%d T' % V['Ns'], size=10.5,
            color=COL['NS2'], weight='bold')
    S.label(ax, 8.75, 2.75, 'NS3\n%d T' % V['Ns'], size=10.5,
            color=COL['NS3'], weight='bold')
    if shared:
        S.label(ax, 10.85, 3.55, 'centre tap: NS2 finish\nand NS3 start on '
                'the\nsame pins', size=9.6, color=NAVY, ha='left')
    else:
        S.label(ax, 10.85, 2.95, '%s to %s joined on\nthe PCB: centre tap'
                % (b2[0], a3[-1]), size=9.6, color=NAVY, ha='left')
    S.label(ax, 0.45, 9.2, 'start', size=9.4, color=GREY, ha='right')
    S.label(ax, 0.45, 4.9, 'finish', size=9.4, color=GREY, ha='right')
    S.label(ax, 14.3, 9.2, 'start', size=9.4, color=GREY, ha='left')
    S.label(ax, 14.3, 1.0, 'finish', size=9.4, color=GREY, ha='left')
    S.label(ax, 7.2, 0.05, u'●  start of the winding (the dot end)',
            size=9.6, color=GREY)

    # ---------------------------------------------------- coil former
    #  the outline is the data sheet's own drawing (bobbin_outline.py); the
    #  pins sit at their dimensioned positions (cores.PIN_XY, bottom view)
    import bobbin_outline as BO
    OUT = BO.load()['views']
    by_pin = {}
    for w, (a, b) in C.PINMAP.items():
        for n in a + b:
            by_pin[n] = w
    tap = set(C.PINMAP['NS2'][1]) & set(C.PINMAP['NS3'][0])
    COL['TAP'] = NAVY
    for n in tap:
        by_pin[n] = 'TAP'
    INK = '#3c4350'

    def outline(bx, view, flip=False):
        """the drawing's lines; flip turns the view half a turn (x, y -> -x, -y)"""
        k = -1.0 if flip else 1.0
        for pl in view['outline']:
            xs, ys = zip(*pl)
            #  zorder below 2: a drawing, not wiring (figcheck reads z 2)
            bx.plot([k * x for x in xs], [k * y for y in ys], color=INK,
                    lw=1.1, zorder=1.6, solid_joinstyle='round')
        for pl in view['hidden']:
            xs, ys = zip(*pl)
            bx.plot([k * x for x in xs], [k * y for y in ys], color=INK,
                    lw=0.8, ls=(0, (3, 2)), zorder=1.6)

    def pinview(bx, mirror, title, sub):
        """pins, numbers and winding names; mirror = the top view"""
        hidden = False           # B is read as the footprint: pads, not
                                 # hidden pins
        S.frame(bx, -47.0, 47.0, -41.0, 38.0)
        S.label(bx, 0.0, 35.4, title, size=11.0, color=NAVY, weight='bold')
        S.label(bx, 0.0, 31.4, sub, size=9.4, color=GREY)
        outline(bx, OUT['top'] if mirror else OUT['bottom'], flip=mirror)
        k = -1.0 if mirror else 1.0
        for n, (x, y) in C.PIN_XY.items():
            x = k * x
            w = by_pin.get(n)
            c = COL[w] if w else '#9aa0a8'
            bx.add_patch(Circle((x, y), 1.75, fc='white', ec=c, lw=1.6,
                                ls='--' if hidden else '-', zorder=3))
            bx.add_patch(Circle((x, y), 0.6, fc=c if w else GREY, ec='none',
                                zorder=4))
            out = -1.0 if x < 0 else 1.0            # outside the row
            S.label(bx, x + out * 4.6, y, str(n), size=9.6, color=c,
                    weight='bold', ha='right' if x < 0 else 'left')

        def grp(w, pl=None, text=None, col=None):
            if pl is None:
                a, b = C.PINMAP[w]
                pl = a + b
            xs = [k * C.PIN_XY[n][0] for n in pl]
            ys = [C.PIN_XY[n][1] for n in pl]
            x, y = sum(xs) / len(xs), sum(ys) / len(ys)
            text = text or '%s\n%s' % (w, C.pins(w))
            out = -1.0 if x < 0 else 1.0
            S.label(bx, x + out * 9.4, y, text, size=9.8, color=col or COL[w],
                    weight='bold', ha='right' if x < 0 else 'left')
        for w in ('NP1', 'NAUX', 'NS2', 'NS3'):
            grp(w)
        #  the chamfered corner: bottom left from below, bottom right from above
        cx = 25.0 * (1.0 if mirror else -1.0)
        bx.annotate('pin 1 marking (chamfer)', xy=(cx, -24.4),
                    xytext=(0.0, -35.0), fontsize=9.4, color=GREY,
                    ha='center', va='center', zorder=9,
                    arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.0,
                                    shrinkA=4, shrinkB=1))

    ax_a = fig.add_axes([0.005, 0.025, 0.490, 0.530])
    pinview(ax_a, False, 'A  BOTTOM VIEW (pin side)',
            'as the TDK data sheet draws it')
    ax_b = fig.add_axes([0.505, 0.025, 0.490, 0.530])
    pinview(ax_b, True, 'B  TOP VIEW = PCB FOOTPRINT',
            'component side; left and right swapped against A')

    foot(fig, 'The transformer: the schematic symbol with its pin numbers, '
              'and the %s coil former traced from its data sheet drawing: '
              '(A) from below, the pin side, as the data sheet numbers it '
              '(pin positions and the numbers 1, 6, 7 and 12 from the data '
              'sheet, the others counted), and (B) from above, the PCB '
              'footprint on the component side, left and right exchanged. One '
              'conductor ends on a pin; the centre tap joins pins %s on the '
              'board.' % (B['former'], C.tap_text()))
    save(fig, 'an_xfmr_pins')


# ---------------------------------- 15b  how the flux is built, step by step
def an_flux_steps(save, foot):
    """The flux in each core built in order, one interval at a time.

    Figure an_flyback_llc shows the decomposition; this one shows the
    SEQUENCE - which winding is conducting, what voltage that winding
    holds, and therefore which way the flux is moving and what stops it.
    The point of drawing the two side by side is the two slope labels:
    the flyback's flux ramps at V_in/(N_p A_e) then V_out/(N_s A_e) and
    its peak is wherever the switch turns off, i.e. wherever the load put
    it; the LLC's flux ramps at V_out/(N_s A_e) for exactly T_r/2 and
    stops when the rectifier lets go, so its peak is a number the load
    cannot move.

    The LLC row reads the eight-interval model with the design's own
    currents, like every other current drawing in the document.  The
    flyback row is a generic DCM cycle: nothing in this document designs
    a flyback, so its numbers are shapes only.
    """
    import an_pdf as _A
    V = _A.V
    fig = plt.figure(figsize=(9.35, 8.10))
    XL, XR, WW = 0.075, 0.560, 0.405

    fig.text(XL + WW / 2, 0.985, 'FLYBACK (DCM)', ha='center', va='top',
             fontsize=11.0, color=NAVY, fontweight='bold')
    fig.text(XR + WW / 2, 0.985, 'LLC, below resonance', ha='center',
             va='top', fontsize=11.0, color=NAVY, fontweight='bold')

    HS, G, Y0 = (0.070, 0.120, 0.120, 0.150), 0.040, 0.945
    rows = ['on', 'i$_p$ , i$_s$', 'N$_p$i$_p$ $-$\nN$_s$i$_s$', 'B']
    #  The flyback's i_s is taken into its dot (Figure an_flyback_llc), so
    #  its ampere-turns ADD: this row read N_p i_p - N_s i_s on both sides
    #  and plotted a positive ramp while only i_s > 0 was flowing.
    rows_l = rows[:2] + ['N$_p$i$_p$ +\nN$_s$i$_s$'] + rows[3:]
    axl, axr, y = [], [], Y0
    for nm, nl, h in zip(rows, rows_l, HS):
        y -= h + G
        axl.append(_wave_ax(fig, [XL, y, WW, h], 0, 1, -1.25, 1.25, nl))
        axr.append(_wave_ax(fig, [XR, y, WW, h], 0, 1, -1.25, 1.25, nm))

    def cap_(ax, t):
        ax.text(0.5, 1.10, t, transform=ax.transAxes, ha='center',
                va='bottom', fontsize=9.6, color=GREY)

    def bands(axes, edges, names, ybot=-0.30):
        """numbered step bands, drawn on the top row and dotted through."""
        for ax in axes:
            for e_ in edges[1:-1]:
                ax.axvline(e_, color=GREY, lw=0.8, ls=(0, (2, 2)), zorder=1)
        top = axes[0]
        for k, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
            top.text(0.5 * (a + b), 1.30, names[k], ha='center',
                     va='center', fontsize=9.8 if len(names[k]) < 2 else 9.4,
                     color=NAVY,
                     fontweight='bold', path_effects=HALO, zorder=9)

    # ------------------------------------------------------ flyback, DCM
    D1, D2 = 0.38, 0.40
    t = np.linspace(0, 1, 3000)
    on = t < D1
    sec = (t >= D1) & (t < D1 + D2)
    ip = np.where(on, t / D1, 0.0)
    isr = np.where(sec, 1.0 - (t - D1) / D2, 0.0)
    imu = ip + isr                               # inverted dots: they add
    B = imu                                      # single winding: B ~ N i

    axl[0].set_ylim(-0.30, 1.55)
    g = np.where(on, 1.0, 0.0)
    axl[0].fill_between(t, 0.0, g * 0.9, color=YEL, lw=0)
    axl[0].plot(t, g * 0.9, color=NAVY, lw=1.5)
    axl[0].text(0.5 * D1, 0.45, 'S', ha='center', va='center',
                fontsize=9.6, color=NAVY, path_effects=HALO, zorder=9)
    cap_(axl[0], 'the switch; the rectifier conducts only after it opens')
    bands(axl, [0.0, D1, D1 + D2, 1.0], ['1', '2', '3'])

    axl[1].set_ylim(-0.22, 1.35)
    axl[1].plot(t, ip, color=MAG, lw=2.0)
    axl[1].plot(t, isr, color=GRN, lw=2.0, ls=(0, (4, 2.4)))
    axl[1].text(0.5 * D1, 1.08, 'i$_p$', color=MAG, fontsize=9.6,
                ha='center', path_effects=HALO)
    axl[1].text(D1 + 0.5 * D2, 1.08, 'i$_s$ (referred)', color=GRN,
                fontsize=9.6, ha='center', path_effects=HALO)
    cap_(axl[1], 'one winding at a time')

    axl[2].set_ylim(-0.22, 1.35)
    axl[2].plot(t, imu, color=CYA, lw=2.2)
    cap_(axl[2], 'nothing cancels: the whole current magnetises')

    axl[3].set_ylim(-0.30, 1.80)
    axl[3].plot(t, B, color=PUR, lw=2.4)
    axl[3].annotate('slope V$_{in}$/(N$_p$A$_e$)', xy=(0.19, 0.50),
                    xytext=(0.02, 1.30), fontsize=9.7, color=GREY,
                    ha='left', va='center',
                    arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.0),
                    path_effects=HALO, zorder=9)
    axl[3].annotate('slope $-$V$_{out}$/(N$_s$A$_e$)', xy=(0.62, 0.45),
                    xytext=(0.80, 0.55), fontsize=9.7, color=GREY,
                    ha='left', va='center',
                    arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.0),
                    path_effects=HALO, zorder=9)
    axl[3].plot([D1], [1.0], 'o', color=PUR, ms=5)
    axl[3].annotate('B$_{pk}$ $\\propto$ I$_{p,pk}$: set by the load',
                    xy=(D1, 1.0), xytext=(0.62, 1.55), fontsize=9.7,
                    color=PUR, ha='left', va='center',
                    arrowprops=dict(arrowstyle='-|>', color=PUR, lw=1.0),
                    path_effects=HALO, zorder=9)
    cap_(axl[3], 'B follows the current; the peak is where S turned off')

    # ------------------------------------------- LLC, the eight-interval model
    tc, e, ilm, ilr, io, _ = _cycle(0.70, V['lam'], V['Icomp'], V['ILm'])
    sg = np.where(tc < 0.5, 1.0, -1.0)
    IO = io * sg
    m = max(abs(ilr).max(), 1e-9)

    axr[0].set_ylim(-0.30, 1.55)
    g1 = np.where(tc < e[2], 1.0, 0.0)
    g2 = np.where((tc >= e[4]) & (tc < e[6]), 1.0, 0.0)
    axr[0].fill_between(tc, 0.0, g1 * 0.9, color=YEL, lw=0)
    axr[0].plot(tc, g1 * 0.9, color=NAVY, lw=1.4)
    axr[0].fill_between(tc, 0.0, g2 * 0.9, color=YEL, lw=0)
    axr[0].plot(tc, g2 * 0.9, color=NAVY, lw=1.4)
    axr[0].text(0.5 * e[1], 0.45, 'S$_1$', ha='center', va='center',
                fontsize=9.6, color=NAVY, path_effects=HALO, zorder=9)
    axr[0].text(0.5 + 0.5 * e[1], 0.45, 'S$_2$', ha='center', va='center',
                fontsize=9.6, color=NAVY, path_effects=HALO, zorder=9)
    cap_(axr[0], 'the bridge; the rectifier conducts WHILE a switch is on')
    #  bands, numbered as the eight steps of Figures an_modes_12..an_modes_wave:
    #  1 power transfer (+), 2 freewheel, 3-4 dead time, 5 transfer (-).
    #  They read 1-4 before, so "4" meant the body-diode clamp in one figure
    #  and the other half's power transfer in this one.
    bands(axr, [0.0, e[1], e[2], e[4], e[5], 1.0], ['1', '2', '3,4', '5', ''])

    axr[1].set_ylim(-1.38, 1.38)
    axr[1].axvspan(e[0], e[1], color=GRN, alpha=0.10, lw=0)
    axr[1].axvspan(e[4], e[5], color=GRN, alpha=0.10, lw=0)
    axr[1].plot(tc, ilr / m, color=MAG, lw=2.0)
    axr[1].plot(tc, IO / m, color=GRN, lw=2.0, ls=(0, (4, 2.4)))
    axr[1].text(0.06, 1.05, 'i$_p$', color=MAG, fontsize=9.6,
                path_effects=HALO)
    axr[1].text(0.20, -1.15, 'i$_s$ (referred)', color=GRN, fontsize=9.6,
                path_effects=HALO)
    cap_(axr[1], 'shaded: both conduct, the secondary clamped to V$_{out}$')

    axr[2].set_ylim(-1.38, 1.38)
    axr[2].plot(tc, ilm / m, color=CYA, lw=2.2)
    cap_(axr[2], 'only the difference magnetises: i$_\\mu$, a ramp')

    axr[3].set_ylim(-1.55, 2.30)
    axr[3].plot(tc, ilm / m, color=PUR, lw=2.4)
    k1 = int(np.argmin(abs(tc - e[1])))
    axr[3].plot([tc[k1]], [ilm[k1] / m], 'o', color=PUR, ms=5)
    axr[3].annotate('slope V$_{out}$/(N$_s$A$_e$)\nfor T$_r$/2 exactly',
                    xy=(0.5 * e[1], 0.0), xytext=(0.02, 1.75),
                    fontsize=9.7, color=GREY, ha='left', va='center',
                    arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.0),
                    path_effects=HALO, zorder=9)
    axr[3].annotate('B$_{pk}$ ≈ V$_{out}$T$_r$/(4N$_s$A$_e$):\n'
                    'the rectifier let go; load cannot move it',
                    xy=(tc[k1], ilm[k1] / m), xytext=(0.99, 1.75),
                    fontsize=9.7, color=PUR, ha='right', va='center',
                    arrowprops=dict(arrowstyle='-|>', color=PUR, lw=1.0),
                    path_effects=HALO, zorder=9)
    cap_(axr[3], 'B follows i$_\\mu$; nearly flat once the rectifier turns off')

    foot(fig, 'Steps. Flyback: 1 switch on, V$_{in}$ on the primary, the '
              'flux ramps up with i$_p$; 2 switch off, the secondary takes '
              'the ampere-turns over and V$_{out}$ ramps the flux down; '
              '3 both off. LLC: 1 a switch closes, the rectifier clamps the '
              'secondary to V$_{out}$, the load current passes through and '
              'only i$_\\mu$ ramps the flux; 2 the rectifier turns off at '
              'the end of the resonant half period and the flux holds; '
              '3 dead time, i$_\\mu$ swings the node; 4 the mirror image.')
    save(fig, 'an_flux_steps')


# ----------------------------------------- 15c  the dc-overlap test itself
def an_dc_overlap(save, foot):
    """What the supplier's bench does, and where the design's numbers sit.

    Left: the setup.  An LCR meter reads the primary inductance with a
    small ac signal while a bias source overlaps a dc current on the same
    winding; every other winding is open.  Right: the inductance against
    that dc current.  The curve is a SHAPE, not a measurement - no part
    has been built - but the three currents marked on it are the design's
    own: the operating magnetising peak, the OVP2-scaled test current the
    specification asks for, and the OCP1 trip that would have to be used
    instead if the controller had no voltage ceiling.
    """
    import an_pdf as _A
    V = _A.V
    fig = plt.figure(figsize=(9.35, 4.35))

    # --------------------------------------------------------- the bench
    ax = _ax(fig, [0.030, 0.10, 0.44, 0.84], -0.6, 12.6, -0.4, 7.6)
    t1 = X.xfmr(ax, 7.6, 3.8, hp=3.0, hs=3.0, gap=0.52)
    XP, XS = t1['p_top'][0], t1['s_top'][0]
    _, bm = S.box(ax, 1.7, 5.4, 2.6, 1.7, 'LCR meter\nsmall ac,\ne.g. 100 kHz', size=9.6)
    _, bs = S.box(ax, 1.7, 2.2, 2.6, 1.7, 'dc bias\nsource\nI$_{dc}$ 0 $\\to$ I$_{sat}$', size=9.6)
    S.wire(ax, [t1['p_top'], (XP, 6.4), (3.7, 6.4), (3.7, bm[1]), bm])
    S.wire(ax, [t1['p_bot'], (XP, 1.2), (3.7, 1.2), (3.7, bs[1]), bs])
    #  the two instruments share the winding: series, the meter's ac on top
    #  of the source's dc
    S.wire(ax, [(1.7, 4.55), (1.7, 3.05)])
    S.label(ax, 4.6, 7.05, 'primary: N$_p$, all of I$_{dc}$ magnetises', size=9.6,
            color=MAG, ha='center')
    #  every other winding open, and said so
    S.wire(ax, [t1['s_top'], (XS + 1.1, t1['s_top'][1])], color=GRN)
    S.wire(ax, [t1['s_bot'], (XS + 1.1, t1['s_bot'][1])], color=GRN)
    S.dot(ax, XS + 1.1, t1['s_top'][1], color=GRN)
    S.dot(ax, XS + 1.1, t1['s_bot'][1], color=GRN)
    S.label(ax, XS + 1.3, 3.8, 'open\n(every\nother\nwinding)', size=9.6,
            color=GRN, ha='left')
    ax.text(6.0, -0.05, 'read L against I$_{dc}$; pass if L(I$_{sat}$) '
            '$\\geq$ 0.9 L(0)', ha='center', va='center', fontsize=9.6,
            color=GREY)

    # ------------------------------------------------------ L against I
    a = fig.add_axes([0.575, 0.17, 0.405, 0.74])
    Ieq, Isat = V['Isateq'], V['Isatspec']
    Iocp = float(_A.SH['I.OCP1'])
    Ik = 1.55 * Isat                      # knee: a shape, not a measurement
    I = np.linspace(0, 1.38 * Iocp, 400)
    L = 1.0 / (1.0 + (I / Ik) ** 6) ** 0.5
    a.plot(I, L, color=NAVY, lw=2.2)
    a.axhline(0.9, color=GREY, lw=0.9, ls=(0, (4, 2)))
    a.text(0.3, 0.875, '90 % of L(0)', fontsize=9.6, color=GREY, va='top')
    for x, c, t, ha, dx in ((Ieq, CYA, 'I$_{eq}$ = i$_{\\mu,pk}$\nat V$_{out}$', 'right', -0.3),
                            (Isat, MAG, 'I$_{sat}$\nat V$_{OVP2}$', 'left', 0.3),
                            (Iocp, PUR, 'I$_{OCP1}$\nif no OVP2', 'left', 0.3)):
        a.axvline(x, color=c, lw=1.6, ls=(0, (5, 2.5)))
        a.text(x + dx, 0.12, t, fontsize=9.6, color=c, ha=ha,
               va='bottom', path_effects=HALO, zorder=9)
    a.set_xlim(0, 1.38 * Iocp)
    a.set_ylim(0, 1.12)
    a.set_xlabel('dc current in the primary  I$_{dc}$', fontsize=9.8,
                 color=NAVY)
    a.set_xticks([])                      # chapter 6: where, not how many amps
    a.set_ylabel('L(I$_{dc}$) / L(0)', fontsize=9.6, color=NAVY)
    a.grid(True, axis='y', color='#C4C8CF', lw=0.7)
    a.tick_params(labelsize=9.4, colors=NAVY)
    for sp in a.spines.values():
        sp.set_color(GREY)

    foot(fig, 'The dc current alone sets the flux, so the inductance is '
              'flat until the core approaches saturation and then falls. '
              'The specification names one current and one criterion: '
              'inductance still 90 %% of its initial value at '
              '%.0f A, the magnetising peak scaled from %.1f V to the '
              'OVP2 output of %.2f V.' % (Isat, V['Vout'], V['OVP2']))
    save(fig, 'an_dc_overlap')


# ------------------------------------------------- gate drive and SR (81)
def _ic(ax, x0, y0, x1, y1, part, pins, stub=0.55, size=9.6, psize=8.4,
        ref=None, tsize=10.5, tpad=0.30):
    """An IC as a box with numbered pins.  -> {pin name: wire end point}

    pins: (side, position, number, name).  side is 'L', 'R', 'T' or 'B';
    position is the y of a side pin or the x of a top / bottom pin.  The
    name is written inside the box against its edge, the number outside
    beside the stub, as a datasheet draws it.  The returned point is the
    outer end of the stub, where the wiring attaches.
    """
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc='#F4F5F7', ec=NAVY,
                           lw=1.8, zorder=3))
    cx = (x0 + x1) / 2.0
    S.label(ax, cx, (y0 + y1) / 2.0 if ref is None else ref, part, size=tsize,
            weight='bold')
    k = X.scale(ax)
    st = stub * k
    out = {}
    for side, pos, num, name in pins:
        if side in 'LR':
            xe = x0 if side == 'L' else x1
            d = -1 if side == 'L' else 1
            xo = xe + d * st
            S.wire(ax, [(xe, pos), (xo, pos)])
            S.label(ax, xe - d * 0.16, pos, name, size=size,
                    ha='left' if side == 'L' else 'right')
            S.label(ax, xe + d * st / 2.0, pos + 0.24 * k, str(num),
                    size=psize, color=GREY)
            out[name] = (xo, pos)
        else:
            ye = y1 if side == 'T' else y0
            d = 1 if side == 'T' else -1
            yo = ye + d * st
            S.wire(ax, [(pos, ye), (pos, yo)])
            S.label(ax, pos, ye - d * tpad, name, size=size)
            S.label(ax, pos + 0.24 * k, ye + d * st / 2.0, str(num),
                    size=psize, color=GREY, ha='left')
            out[name] = (pos, yo)
    return out


def _term(ax, x, y):
    """An open terminal: where a net leaves the drawing, or a pin left
    unconnected on purpose.  A marker, so the wiring check reads the wire
    as ending on something."""
    ax.plot([x], [y], 'o', ms=6.5, mfc='white', mec=NAVY, mew=1.5, zorder=5)


def _npn(ax, xb, y, h=1.4, left=False):
    """An NPN transistor, base bar at xb, base lead from the left, collector
    up and emitter down at xb + 0.55 h.  -> base, collector, emitter ends

    The emitter arrow is drawn in data units, pointing out of the device:
    it is the one mark that says NPN.
    """
    #  left=True mirrors it: base lead from the right, collector and
    #  emitter on the left
    xe = xb - 0.55 * h if left else xb + 0.55 * h
    yc, ye = y + 0.5 * h, y - 0.5 * h
    ax.plot([xb, xb], [y - 0.40 * h, y + 0.40 * h], color=NAVY, lw=2.2,
            zorder=4)
    ax.plot([xb, xe], [y + 0.16 * h, yc], color=NAVY, lw=1.7, zorder=4)
    ax.plot([xb, xe], [y - 0.16 * h, ye], color=NAVY, lw=1.7, zorder=4)
    x0, y0 = xb, y - 0.16 * h
    dx, dy = xe - x0, ye - y0
    n = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / n, dy / n
    tx, ty = x0 + 0.92 * dx, y0 + 0.92 * dy
    L, W = 0.30 * h, 0.12 * h
    bx, by = tx - L * ux, ty - L * uy
    ax.fill([tx, bx - W * uy, bx + W * uy], [ty, by + W * ux, by - W * ux],
            color=NAVY, zorder=5, lw=0)
    return (xb, y), (xe, yc), (xe, ye)


def _zener(ax, x, y):
    """A Zener on a vertical branch, cathode up.  -> (anode, cathode)"""
    a, c = S.diode(ax, x, y, horiz=False)
    s = 0.56 * X.scale(ax) * getattr(ax, '_diode_k', 1.0)
    w = 0.72 * s
    yb = c[1]
    ax.plot([x - w, x - w - 0.22 * w], [yb, yb - 0.32 * w], color=NAVY,
            lw=2.2, zorder=3)
    ax.plot([x + w, x + w + 0.22 * w], [yb, yb + 0.32 * w], color=NAVY,
            lw=2.2, zorder=3)
    return a, c


def _sv(key):
    """a value the sheet holds: a printed row, else a builder constant"""
    import an_pdf
    v = an_pdf.SH.get(key)
    return an_pdf._builder_const(key) if v is None else v


def an_gate_drive(save, foot):
    """One bridge leg as built: the L6790A outputs, an L6498LD and two
    STO60N045DM9.  Pin numbers are the datasheets' (L6790A as the ST
    EVL6790_670W control board numbers it; L6498 in SO-14).  Leg 2 is the
    same circuit on HOUT2 / LOUT2 and is drawn as a block.

    The full-bridge return IS the controller ground: the L6790A datasheet
    block diagram puts R_CS between that ground and the input rectifier's
    negative, with ISEN on the rectifier side.  So S2's source, SGND, PGND
    and the controller GND are one node, drawn with the primary-side
    ground symbol, and PGND is wired to S2's driver-source pin.
    """
    fig = plt.figure(figsize=(8.2, 6.23))
    ax = _ax(fig, [0.01, 0.02, 0.98, 0.96], -0.4, 27.6, 1.6, 21.4)
    YV, YB = 18.6, 20.0                     # V_CC rail, rectified bus
    # ------------------------------------------------------- L6790A
    c = _ic(ax, 0.6, 4.6, 4.6, 15.8, 'L6790A',
            [('R', 14.6, 3, 'DRV_EN'),
             ('R', 13.2, 16, 'HOUT1'), ('R', 11.6, 15, 'LOUT1'),
             ('R', 8.2, 14, 'HOUT2'), ('R', 6.9, 13, 'LOUT2'),
             ('T', 2.6, 4, 'VCC'), ('B', 2.6, 5, 'GND')], ref=10.0)
    S.wire(ax, [c['VCC'], (2.6, YV)])
    S.dot(ax, 2.6, YV)
    _pgnd(ax, *c['GND'])
    #  DRV_EN: nothing on it - the L6498 has no enable input
    xe = c['DRV_EN'][0]
    _term(ax, xe, 14.6)
    S.label(ax, xe + 0.35, 14.6, 'open', size=9.4, ha='left', color=GREY)

    # ------------------------------------------------------- L6498LD, leg 1
    XD0, XD1 = 8.0, 13.2
    d = _ic(ax, XD0, 9.6, XD1, 16.4, 'L6498LD',
            [('L', 13.2, 1, 'HIN'), ('L', 11.6, 2, 'LIN'),
             ('T', 9.6, 7, 'VCC'),
             ('B', 9.4, 3, 'SGND'), ('B', 11.6, 5, 'PGND'),
             ('R', 15.6, 13, 'BOOT'), ('R', 14.2, 12, 'HVG'),
             ('R', 12.6, 11, 'OUT'), ('R', 10.6, 6, 'LVG')], ref=12.7)
    S.label(ax, (XD0 + XD1) / 2, 12.0, 'leg 1', size=9.4, color=GREY)
    S.wire(ax, [c['HOUT1'], d['HIN']])
    S.wire(ax, [c['LOUT1'], d['LIN']])
    S.wire(ax, [d['VCC'], (9.6, YV)])
    S.dot(ax, 9.6, YV)
    _pgnd(ax, *d['SGND'])
    # local decoupling at the driver's VCC pin
    XC = 7.4
    ca, cb = S.cap(ax, XC, 17.7, horiz=False)
    S.wire(ax, [(XC, YV), cb])
    S.wire(ax, [ca, (XC, 16.9)])
    _pgnd(ax, XC, 16.9)
    S.dot(ax, XC, YV)
    S.label(ax, XC - 0.45, 17.7, 'local\ndecoupling', size=8.6, ha='right',
            color=GREY)

    # ------------------------------------------------- bootstrap
    XB, R = 14.4, 0.20
    S.wire(ax, [d['BOOT'], (XB, 15.6)])
    S.dot(ax, XB, 15.6)
    da, db = S.diode(ax, XB, 17.1, horiz=False, flip=True)   # VCC -> BOOT
    S.wire(ax, [(XB, YV), da])                     # anode on the rail
    S.wire(ax, [db, (XB, 15.6)])                   # cathode on BOOT
    S.label(ax, XB + 0.55, 17.1, 'D$_{BS}$', size=10, ha='left')
    ca, cb = S.cap(ax, XB, 13.3, horiz=False)
    S.wire(ax, [(XB, 15.6), cb])
    S.wire(ax, [ca, (XB, 12.6)])
    S.dot(ax, XB, 12.6)
    S.label(ax, XB + 0.50, 13.3, 'C$_{BOOT}$', size=10, ha='left')

    # ------------------------------------------------- the two switches
    XS = 20.4                               # drain-source line
    s1d, s1s = X.mosfet(ax, XS, 14.2, None, 'plain', h=1.8, gate=1.4,
                        body=True, coss=False)
    s2d, s2s = X.mosfet(ax, XS, 8.6, None, 'plain', h=1.8, gate=1.4,
                        body=True, coss=False)
    S.label(ax, XS + 1.15, 14.2, 'S1', size=11, weight='bold', ha='left')
    S.label(ax, XS + 1.15, 8.6, 'S2', size=11, weight='bold', ha='left')
    S.label(ax, XS + 1.15, 13.45, 'STO60N045DM9', size=8.6, ha='left',
            color=GREY)
    S.label(ax, XS + 1.15, 7.85, 'STO60N045DM9', size=8.6, ha='left',
            color=GREY)
    # HVG over the C_BOOT lead with a hop, then R_G to the gate
    xh = XS - 1.4
    S.wire(ax, [d['HVG'], (XB - R, 14.2)])
    X.hop(ax, XB, 14.2, r=R)
    ra, rb = S.res(ax, 17.3, 14.2, 'R$_G$', tdy=0.55)
    S.wire(ax, [(XB + R, 14.2), ra])
    S.wire(ax, [rb, (xh, 14.2)])
    S.wire(ax, [d['LVG'], (15.6, 10.6), (15.6, 8.6)])
    ra2, rb2 = S.res(ax, 17.3, 8.6, 'R$_G$', tdy=0.55)
    S.wire(ax, [(15.6, 8.6), ra2])
    S.wire(ax, [rb2, (xh, 8.6)])
    # S1 drain to the bus; S1 source = A = S2 drain
    S.wire(ax, [s1d, (XS, YB)])
    YA = 11.4
    S.wire(ax, [s1s, (XS, YA)])
    S.wire(ax, [(XS, YA), s2d])
    S.dot(ax, XS, YA)
    #  OUT and C_BOOT return to S1's source, at its driver-source pin
    S.wire(ax, [d['OUT'], (XS, 12.6)])
    S.dot(ax, XS, 12.6)
    S.wire(ax, [(XS, YA), (25.2, YA)])
    _term(ax, 25.2, YA)
    S.label(ax, 25.55, YA, 'A: to C$_r$, L$_r$', size=10, ha='left')
    # S2 source: ground.  PGND to its driver-source pin.
    YK, YG = 7.0, 5.6
    S.wire(ax, [s2s, (XS, YG)])
    S.dot(ax, XS, YK)
    S.wire(ax, [d['PGND'], (11.6, YK), (XS, YK)])
    S.dot(ax, XS, YG)
    S.wire(ax, [(XS, YG), (XS, 4.9)])
    _pgnd(ax, XS, 4.9)
    ra3, rb3 = S.res(ax, 22.6, YG, 'R$_{CS}$', tdy=0.55)
    S.wire(ax, [(XS, YG), ra3])
    S.wire(ax, [rb3, (24.6, YG)])
    _term(ax, 24.6, YG)
    S.label(ax, 24.95, YG, 'ISEN and\nrectifier (−)', size=10, ha='left')

    # ------------------------------------------------- rails
    S.wire(ax, [(0.2, YV), (XB, YV)])
    _term(ax, 0.2, YV)
    S.label(ax, 0.2, YV + 0.48, 'V$_{CC}$ from the regulator', size=10,
            ha='left')
    S.wire(ax, [(XS, YB), (25.2, YB)])
    _term(ax, 25.2, YB)
    S.label(ax, 22.8, YB + 0.48, 'V$_{in}$ (C$_{in}$), also leg 2',
            size=10)

    # ------------------------------------------------- leg 2 as a block
    S.box(ax, 10.8, 4.4, 5.6, 2.4, '', fc='#F4F5F7', ec=NAVY)
    S.label(ax, 10.8, 4.9, 'L6498LD + S3, S4', size=10, weight='bold')
    S.label(ax, 10.8, 4.0, 'leg 2, the same circuit', size=9.4, color=GREY)
    S.wire(ax, [c['HOUT2'], (6.6, 8.2), (6.6, 4.9), (8.0, 4.9)])
    S.wire(ax, [c['LOUT2'], (5.9, 6.9), (5.9, 4.0), (8.0, 4.0)])
    S.label(ax, 7.3, 5.22, 'HIN', size=8.6, color=GREY)
    S.label(ax, 7.3, 3.68, 'LIN', size=8.6, color=GREY)
    S.wire(ax, [(13.6, 4.4), (14.6, 4.4)])
    _term(ax, 14.6, 4.4)
    S.label(ax, 14.95, 4.4, 'B: to the transformer', size=10, ha='left')
    foot(fig, 'Leg 1 of the bridge as built. Pin numbers are the '
              'datasheets’.')
    save(fig, 'an_gate_drive')


def _sr_block(ax, full=False):
    """the SR stage of an_sr_ctrl; full=True draws it for the whole-circuit
    sheet: the secondary windings alone, and flags for V_out"""
    R = 0.20
    # ------------------------------------------------- transformer
    if full:
        #  the secondary windings alone; NP1 and NAUX are on sheet 1
        (s7, s9), (s10, s12) = _xf(ax, 1.6, [('R', 13.2, 9.75, 4),
                                             ('R', 9.25, 5.8, 4)])
        xs = s7[0]
        S.wire(ax, [s9, s10])
        t = {'s_top': s7, 's_bot': s12, 's_tap': (xs, 9.5)}
        S.dot(ax, xs, 9.5)
        S.label(ax, xs + 0.55, 11.5, 'NS2\n%.0f T' % _sv('N.s'), size=10,
                ha='left')
        S.label(ax, xs + 0.55, 7.5, 'NS3\n%.0f T' % _sv('N.s'), size=10,
                ha='left')
        S.label(ax, -0.3, 15.0, 'T1\nNP1, NAUX:\nsheet 1', size=8.6,
                color=GREY, ha='left')
    else:
        t = X.xfmr(ax, 2.4, 9.5, hp=5.0, hs=7.4, ct=True, lp='NP1',
                   ls=('NS2', 'NS3'), size=10)
        xs = t['s_top'][0]
        for key, txt_ in (('p_top', '1'), ('p_bot', '3')):
            px, py = t[key]
            S.wire(ax, [(px, py), (0.2, py)])
            _term(ax, 0.2, py)
            S.label(ax, 0.2, py + 0.42, txt_, size=8.6, color=GREY)
        S.label(ax, 0.2, 6.25, 'to the\ntank', size=9.0, color=GREY)
    # ------------------------------------------------- the IC
    XI0, XI1, YI0, YI1 = 8.6, 12.6, 7.0, 14.4
    c = _ic(ax, XI0, YI0, XI1, YI1, 'TEA2095TE',
            [('R', 13.2, 8, 'GDA'), ('R', 11.8, 5, 'SSA'),
             ('T', 11.4, 6, 'DSA'), ('T', 9.6, 7, 'VCC'),
             ('R', 9.6, 4, 'SSB'), ('R', 8.2, 1, 'GDB'),
             ('B', 11.4, 3, 'DSB'), ('B', 9.6, 2, 'GND')], ref=10.7)
    gx, gy = c['GND']
    S.gnd(ax, gx, gy)
    # VCC from a Zener follower on the output (sheet 14c.4), above the
    # leg-A drain bus: R_BSR into the Zener and the base, collector on
    # V_out, emitter down to the pin with C_SR beside it
    vx, vy = c['VCC']
    YR, XRB, YBN = 21.5, 6.4, 19.0
    YDA_ = 16.8                       # the leg-A drain bus, drawn below
    _term(ax, 3.6, YR)
    S.label(ax, 3.25, YR, 'V$_{out}$', size=10, ha='right')
    bq, cq, eq_ = _npn(ax, vx - 0.55 * 1.4, YBN, h=1.4)
    S.wire(ax, [(3.6, YR), (vx, YR), cq])
    S.dot(ax, XRB, YR)
    ra, rb = S.res(ax, XRB, 20.25, horiz=False)
    S.wire(ax, [(XRB, YR), rb])
    S.wire(ax, [ra, (XRB, YBN)])
    S.label(ax, XRB - 0.42, 20.25, 'R$_{BSR}$\n%.0f $\\Omega$'
            % _sv('R.BSR_sel'), size=9.4, ha='right')
    S.dot(ax, XRB, YBN)
    S.wire(ax, [(XRB, YBN), bq])
    za, zc = _zener(ax, XRB, 18.25)
    S.wire(ax, [(XRB, YBN), zc])
    S.wire(ax, [za, (XRB, 17.55)])
    S.gnd(ax, XRB, 17.55)
    S.label(ax, XRB - 0.95, 18.25, 'D$_{ZSR}$\n%.0f V' % _sv('V.DZSR_sel'),
            size=9.4, ha='right')
    S.label(ax, vx + 0.35, YBN + 0.15, 'Q$_{SR}$', size=10, ha='left',
            weight='bold')
    YVC = 15.8
    S.wire(ax, [eq_, (vx, vy)])       # the drain bus hops it, below
    S.label(ax, vx + 0.25, 17.75, 'V$_{CC,SR}$ %.1f V' % _sv('V.SR'),
            size=9.0, ha='left', color=GREY)
    XCD = 7.6
    S.dot(ax, vx, YVC)
    S.wire(ax, [(vx, YVC), (XCD, YVC)])
    ca, cb = S.cap(ax, XCD, 15.0, horiz=False)
    S.wire(ax, [(XCD, YVC), cb])
    S.wire(ax, [ca, (XCD, 14.4)])
    S.gnd(ax, XCD, 14.4)
    S.label(ax, XCD - 0.75, 15.0, 'C$_{SR}$\n%.0f $\\mu$F' % _sv('C.SR'),
            size=9.4, ha='right')
    # ------------------------------------------------- centre tap = V_out
    S.wire(ax, [t['s_tap'], (6.0, 9.5)])
    _term(ax, 6.0, 9.5)
    S.label(ax, 6.0, 10.15, 'V$_{out}$' if full else 'V$_{out}$, C$_{out}$',
            size=10)
    import cores
    _pm = cores.PINMAP
    S.label(ax, xs + 0.15, 9.05, '%d, %d' % (_pm['NS2'][1][0], _pm['NS3'][0][0]),
            size=8.6, color=GREY, ha='left')

    def pair(yc, ydrain, ysrc, gate_pin, leg, hop_y):
        """two MOSFETs, drains on ydrain, sources on ysrc; one gate
        resistor each, from a split at x = 14.2"""
        xa, xb = 18.0, 21.6
        for x in (xa, xb):
            d, s_ = X.mosfet(ax, x, yc, None, 'plain', h=1.8, gate=1.4,
                             body=True, coss=False)
            S.wire(ax, [d, (x, ydrain)])
            S.wire(ax, [s_, (x, ysrc)])
        S.dot(ax, xa, ydrain)
        S.label(ax, xa - 1.3, yc + 0.75, 'Q$_{%s1}$' % leg, size=10,
                weight='bold')
        S.label(ax, xb - 1.3, yc + 0.75, 'Q$_{%s2}$' % leg, size=10,
                weight='bold')
        gpx, gpy = gate_pin
        XS_ = 14.2
        #  one vertical through every branch point; a dot only where a
        #  branch leaves its middle, not at its two corners
        ys_ = sorted((gpy, yc, hop_y))
        S.wire(ax, [(gpx, gpy), (XS_, gpy)])
        S.wire(ax, [(XS_, ys_[0]), (XS_, ys_[2])])
        S.dot(ax, XS_, ys_[1])
        r1a, r1b = S.res(ax, 15.4, yc)
        S.wire(ax, [(XS_, yc), r1a])
        S.wire(ax, [r1b, (xa - 1.4, yc)])
        # to the second, under the first one's source lead
        r2a, r2b = S.res(ax, 15.4, hop_y)
        S.wire(ax, [(XS_, hop_y), r2a])
        S.wire(ax, [r2b, (xa - R, hop_y)])
        X.hop(ax, xa, hop_y, r=R)
        xu = xb - 1.8
        S.wire(ax, [(xa + R, hop_y), (xu, hop_y), (xu, yc), (xb - 1.4, yc)])
        return xa, xb

    # ------------------------------------------------- leg A (NS2, pin 7)
    YDA, YSA = YDA_, 12.6
    xa, xb = pair(14.6, YDA, YSA, c['GDA'], 'A', 13.2)
    #  the drain bus hops the VCC run from the follower
    S.wire(ax, [t['s_top'], (xs, YDA), (vx - R, YDA)])
    X.hop(ax, vx, YDA, r=R)
    S.wire(ax, [(vx + R, YDA), (xb, YDA)])
    S.label(ax, xs + 0.15, t['s_top'][1] + 0.05, str(_pm['NS2'][0][0]),
            size=8.6, color=GREY,
            ha='left')
    S.wire(ax, [(xa, YSA), (24.2, YSA)])
    S.dot(ax, xb, YSA)
    S.wire(ax, [(24.2, YSA), (24.2, 11.9)])
    S.gnd(ax, 24.2, 11.9)
    # sense lines: DSA to the drains, SSA to the sources
    dx_, dy_ = c['DSA']
    S.wire(ax, [(dx_, dy_), (dx_, YDA)])
    S.dot(ax, dx_, YDA)
    sx_, sy_ = c['SSA']
    S.wire(ax, [(sx_, sy_), (23.2, sy_), (23.2, YSA)])
    S.dot(ax, 23.2, YSA)
    S.label(ax, xb, YDA + 0.42, 'leg A: two STL160N10F8 in parallel', size=9.4,
            color=GREY)
    S.label(ax, 14.7, 16.1, 'one gate resistor per MOSFET', size=8.6,
            color=GREY)

    # ------------------------------------------------- leg B (NS3, pin 12)
    YDB, YSB = 5.4, 1.6
    xa, xb = pair(3.6, YDB, YSB, c['GDB'], 'B', 2.4)
    #  the drain bus hops the GDB run, which has to reach the gates
    S.wire(ax, [t['s_bot'], (xs, YDB), (14.2 - R, YDB)])
    X.hop(ax, 14.2, YDB, r=R)
    S.wire(ax, [(14.2 + R, YDB), (xb, YDB)])
    S.label(ax, xs + 0.15, t['s_bot'][1] - 0.05, str(_pm['NS3'][1][0]),
            size=8.6,
            color=GREY, ha='left')
    S.wire(ax, [(xa, YSB), (24.2, YSB)])
    S.dot(ax, xb, YSB)
    S.wire(ax, [(24.2, YSB), (24.2, 0.9)])
    S.gnd(ax, 24.2, 0.9)
    dx_, dy_ = c['DSB']
    S.wire(ax, [(dx_, dy_), (dx_, YDB)])
    S.dot(ax, dx_, YDB)
    sx_, sy_ = c['SSB']
    S.wire(ax, [(sx_, sy_), (23.2, sy_), (23.2, YSB)])
    S.dot(ax, 23.2, YSB)
    S.label(ax, 19.8, 0.95, 'leg B: two STL160N10F8 in parallel', size=9.4, color=GREY)


def an_sr_ctrl(save, foot):
    """The synchronous rectifier as built: one TEA2095TE, two SR MOSFETs
    in parallel per centre-tap leg, the transformer pins as an_xfmr_pins
    numbers them (NS2 7-9, NS3 10-12, 9 and 10 joined as the centre tap).

    Laid out the way ST's EVL6790_670W SR board lays out its TEA2096: one
    gate resistor per MOSFET, DSx and SSx run as separate sense lines to
    the drains and the sources of their pair, VCC decoupled at the pin.
    The second MOSFET of a pair is reached under the first one's source
    lead, so that run crosses it with a hop.
    """
    fig = plt.figure(figsize=(8.2, 7.45))
    ax = _ax(fig, [0.01, 0.02, 0.98, 0.96], -0.4, 27.2, 0.4, 22.4)
    _sr_block(ax)
    foot(fig, 'The synchronous rectifier as built: one TEA2095TE fed by a '
              'Zener follower, two MOSFETs in parallel per leg.')
    save(fig, 'an_sr_ctrl')


# ======================================================== the whole circuit
def _flag(ax, x, y, name, side='r', size=9.4, dy=0.0):
    """A net that continues elsewhere: an open terminal and its name."""
    _term(ax, x, y)
    if side == 'r':
        S.label(ax, x + 0.35, y + dy, name, size=size, ha='left')
    elif side == 'l':
        S.label(ax, x - 0.35, y + dy, name, size=size, ha='right')
    else:
        S.label(ax, x, y + (0.45 if side == 'u' else -0.45) + dy, name,
                size=size)


def _r(v):
    """ohms -> the value in ohm or kilohm, in mathtext"""
    if v >= 1e3:
        t = ('%.1f' % (v / 1e3)).rstrip('0').rstrip('.')
        return t + r' k$\Omega$'
    t = ('%.1f' % v).rstrip('0').rstrip('.')
    return t + r' $\Omega$'


def _c(nf):
    """nF -> the value in pF, nF or uF, whichever reads plainly"""
    if nf < 1:
        return '%.0f pF' % (nf * 1e3)
    if nf < 1e3:
        t = ('%.2f' % nf).rstrip('0').rstrip('.')
        return t + ' nF'
    t = ('%.1f' % (nf / 1e3)).rstrip('0').rstrip('.')
    return t + r' $\mu$F'


def _xf(ax, xc, wind, over=None):
    """Windings beside one core, each its own coil.  wind: (side, ytop,
    ybot, turns); side 'L' or 'R'.  The dot is at the top (the start).
    -> [(top terminal, bottom terminal)] in the order given."""
    r = X.WIND_R * X.scale(ax, xfmr=True) * getattr(ax, '_xf_mult', 1.0)
    core = 0.13
    gap = core + 2.5 * r
    out, ext = [], []
    for side, yt, yb, n in wind:
        xw = xc - gap if side == 'L' else xc + gap
        #  as many turns of the document's radius as the span holds, up to n
        n = max(2, min(n, int((abs(yt - yb) - 0.3) / (2.0 * r))))
        h = 2.0 * r * n
        c = (yt + yb) / 2.0
        a, b = c - h / 2.0, c + h / 2.0
        X.coil(ax, xw, a, b, n=n, side=1 if side == 'L' else -1)
        S.wire(ax, [(xw, yb), (xw, a)])
        S.wire(ax, [(xw, b), (xw, yt)])
        d = -1 if side == 'L' else 1
        X.dot(ax, xw + d * 0.75 * r, b - r, NAVY, 4.8)
        ext += [a, b]
        out.append(((xw, yt), (xw, yb)))
    o = 0.45 * r
    for xx in (xc - core, xc + core):
        ax.plot([xx, xx], [min(ext) - o, max(ext) + o], color=GREY, lw=2.4,
                zorder=3)
    return out


def an_full_pri(save, foot):
    """The whole converter, sheet 1 of 2: the primary side.  Every value
    printed is read from the sheet (_sv); a block without values is a part
    this note does not size.  Pin numbers: L6790A as ST's EVL6790_670W
    control board numbers them, L6498LD in SO-14, T1 as an_xfmr_pins.

    Nets that continue on this sheet away from their source carry a flag
    (HVG1 ... LVG2, A, B, AUX): the drivers sit with the controller, not
    with the switches, and the ZCD divider sits at its pin.
    """
    import an_pdf
    V = an_pdf.V
    fig = plt.figure(figsize=(8.2, 9.7))
    ax = _ax(fig, [0.01, 0.02, 0.98, 0.96], -0.4, 27.6, 0.0, 32.4)
    R = 0.20
    SZ = 9.0                                        # value lettering
    # ------------------------------------------------- mains, EMI, HVSU
    YL, YN = 30.4, 26.4
    for yy, nm in ((YL, 'L'), (YN, 'N')):
        _term(ax, 0.2, yy)
        S.label(ax, 0.2, yy + 0.5, nm, size=10)
        S.wire(ax, [(0.2, yy), (1.0, yy)])
    S.label(ax, 0.0, 31.9, '%.0f–%.0f Vac' % (V['Vacmin'], V['Vacmax']),
            size=SZ, ha='left', color=GREY)
    S.box(ax, 2.3, 28.4, 2.6, 5.4, 'EMI filter\n\nnot sized\nhere', size=9)
    XH1, XH2 = 4.8, 6.0
    S.wire(ax, [(3.6, YL), (6.6, YL)])
    S.dot(ax, XH1, YL)
    S.wire(ax, [(3.6, YN), (XH1 - R, YN)])
    X.hop(ax, XH1, YN, r=R)
    S.wire(ax, [(XH1 + R, YN), (6.6, YN)])
    S.dot(ax, XH2, YN)
    a1, k1 = S.diode(ax, XH1, 24.4, horiz=False, flip=True)
    a2, k2 = S.diode(ax, XH2, 24.4, horiz=False, flip=True)
    S.wire(ax, [(XH1, YL), a1])
    S.wire(ax, [(XH2, YN), a2])
    S.wire(ax, [k2, (XH2, 23.3), (XH1, 23.3)])
    S.label(ax, XH1 - 0.6, 24.4, 'D$_{HV}$', size=SZ, ha='right')
    # ------------------------------------------------- bridge, C_in, R_CS
    S.box(ax, 7.7, 28.4, 2.2, 5.4, 'BR1', size=10, weight='bold')
    S.label(ax, 6.85, YL + 0.35, '~', size=9, color=GREY)
    S.label(ax, 6.85, YN + 0.35, '~', size=9, color=GREY)
    S.label(ax, 8.55, YL + 0.35, '+', size=9, color=GREY)
    S.label(ax, 8.55, YN + 0.35, '−', size=9, color=GREY)
    X1, X2 = 15.6, 20.4                              # bridge legs
    XCI, XM = 9.8, 11.6                              # C_in, rectifier (-)
    YG = 22.6                                        # bridge return
    S.wire(ax, [(8.8, YL), (X2, YL)])
    S.dot(ax, XCI, YL)
    S.dot(ax, X1, YL)
    ca, cb = S.cap(ax, XCI, 28.4, horiz=False)
    S.wire(ax, [(XCI, YL), cb])
    S.wire(ax, [ca, (XCI, YN)])
    S.label(ax, XCI + 0.45, 28.4, 'C$_{in}$\n' + _c(_sv('C.in_sel')),
            size=SZ, ha='left')
    S.wire(ax, [(8.8, YN), (XM, YN), (XM, YG)])
    S.dot(ax, XCI, YN)
    S.dot(ax, XM, YG)
    ra, rb = S.res(ax, 12.8, YG)
    S.wire(ax, [(XM, YG), ra])
    S.wire(ax, [rb, (X2, YG)])
    S.label(ax, 12.8, YG + 1.05, 'R$_{CS}$ %.0f m$\\Omega$' % _sv('R.CS'),
            size=SZ)
    S.label(ax, 12.8, YG - 0.75, '%.0f × %.0f m$\\Omega$'
            % (_sv('N.RCS'), _sv('R.CS_single')), size=8.4, color=GREY)
    XGND = 14.4
    S.dot(ax, XGND, YG)
    S.wire(ax, [(XGND, YG), (XGND, 21.9)])
    _pgnd(ax, XGND, 21.9)
    # ------------------------------------------------- full bridge
    YH, YLO, YA, YB = 29.1, 25.0, 27.0, 26.4
    for x, nm_h, nm_l in ((X1, 'S1', 'S2'), (X2, 'S3', 'S4')):
        d1, s1 = X.mosfet(ax, x, YH, None, 'plain', h=1.8, gate=1.4,
                          body=True, coss=False)
        d2, s2 = X.mosfet(ax, x, YLO, None, 'plain', h=1.8, gate=1.4,
                          body=True, coss=False)
        S.wire(ax, [d1, (x, YL)])
        S.wire(ax, [s1, d2])
        S.wire(ax, [s2, (x, YG)])
        S.label(ax, x + 1.15, YH + 0.55, nm_h, size=10, weight='bold',
                ha='left')
        S.label(ax, x + 1.15, YLO - 0.55, nm_l, size=10, weight='bold',
                ha='left')
    S.dot(ax, X1, YG)
    S.label(ax, 17.9, 31.55, 'S1–S4  STO60N045DM9', size=SZ,
            color=GREY)
    for x, y, nm in ((X1, YH, 'HVG1'), (X1, YLO, 'LVG1'),
                     (X2, YH, 'HVG2'), (X2, YLO, 'LVG2')):
        _flag(ax, x - 1.4, y, nm, side='l', size=SZ)
    # A over leg 2 to C_r, B straight on
    S.dot(ax, X1, YA)
    S.label(ax, X1 - 0.4, YA + 0.4, 'A', size=10, weight='bold')
    S.wire(ax, [(X1, YA), (X2 - R, YA)])
    X.hop(ax, X2, YA, r=R)
    XCR = 21.95
    ra, rb = S.cap(ax, XCR, YA)
    S.wire(ax, [(X2 + R, YA), ra])
    S.label(ax, XCR, YA + 0.75, 'C$_r$ ' + _c(_sv('C.r')), size=SZ)
    S.dot(ax, X2, YB)
    S.label(ax, 21.75, YB - 0.42, 'B', size=10, weight='bold')
    # ------------------------------------------------- T1, primary side
    XC = 25.6
    (p1, p3), (p4, p6) = _xf(ax, XC, [('L', 29.2, 25.4, 5),
                                      ('L', 24.4, 21.6, 3)])
    xw = p1[0]
    S.wire(ax, [rb, (23.1, YA), (23.1, p1[1]), p1])
    S.wire(ax, [(X2, YB), (22.6, YB), (22.6, p3[1]), p3])
    import cores
    _pm = cores.PINMAP
    for (px, py), n_ in ((p1, _pm['NP1'][0][0]), (p3, _pm['NP1'][1][0]),
                         (p4, _pm['NAUX'][0][0]), (p6, _pm['NAUX'][1][0])):
        S.label(ax, px - 0.55, py + 0.3, str(n_), size=8.4, color=GREY)
    S.label(ax, XC + 0.35, 27.3, 'NP1\n%.0f T' % _sv('N.p'), size=SZ,
            ha='left')
    S.label(ax, XC + 0.35, 23.0, 'NAUX\n%.0f T' % _sv('N.aux'), size=SZ,
            ha='left')
    S.label(ax, 24.4, 31.85, 'T1  PQ 50/50, N97', size=SZ, weight='bold')
    S.label(ax, 24.4, 31.15, 'L$_{open}$ %.0f $\\mu$H,  L$_r$ %.0f $\\mu$H'
            % (_sv('L.open'), _sv('L.short')), size=8.6, color=GREY)
    S.label(ax, 24.4, 30.5, 'NS2, NS3: sheet 2', size=8.6, color=GREY)
    S.wire(ax, [p4, (23.1, p4[1]), (23.1, p4[1] - 0.6)])
    _pgnd(ax, 23.1, p4[1] - 0.6)
    # ------------------------------------------------- the controller
    U1 = _ic(ax, 3.8, 3.6, 8.8, 19.2, 'L6790A',
             [('T', XH1, 1, 'HVSU'), ('T', 6.3, 6, 'ISEN'),
              ('T', 7.8, 4, 'VCC'),
              ('R', 17.6, 16, 'HOUT1'), ('R', 16.4, 15, 'LOUT1'),
              ('R', 11.0, 14, 'HOUT2'), ('R', 9.8, 13, 'LOUT2'),
              ('R', 6.4, 12, 'ZCD'), ('R', 5.2, 11, 'CFG'),
              ('R', 4.2, 10, 'BM'),
              ('L', 17.6, 3, 'DRV_EN'), ('L', 15.6, 7, 'RT'),
              ('L', 13.6, 8, 'CT'), ('L', 11.6, 5, 'GND'),
              ('L', 9.0, 9, 'FB')], ref=6.2)
    S.label(ax, 6.3, 5.5, 'U1', size=9, color=GREY)
    S.wire(ax, [k1, U1['HVSU']])
    S.dot(ax, XH1, 23.3)
    YIS = 21.7
    S.wire(ax, [(XM, YG), (XM, YIS), (U1['ISEN'][0], YIS), U1['ISEN']])
    x_, y_ = U1['DRV_EN']
    S.wire(ax, [(x_, y_), (2.0, y_)])
    _term(ax, 2.0, y_)
    S.label(ax, 1.65, y_, 'open', size=8.4, color=GREY, ha='right')
    for pin, kind, val, nm in (('RT', 'res', _r(_sv('R.T') * 1e3), 'R$_T$'),
                               ('CT', 'cap', _c(_sv('C.T') / 1e3), 'C$_T$')):
        x_, y_ = U1[pin]
        if kind == 'res':
            a_, b_ = S.res(ax, 1.8, y_)
        else:
            a_, b_ = S.cap(ax, 1.8, y_)
        S.wire(ax, [(x_, y_), b_])
        S.wire(ax, [a_, (0.4, y_), (0.4, y_ - 0.8)])
        _pgnd(ax, 0.4, y_ - 0.8)
        S.label(ax, 1.8, y_ + 0.75, nm + ' ' + val, size=SZ)
    x_, y_ = U1['GND']
    S.wire(ax, [(x_, y_), (2.0, y_), (2.0, y_ - 0.7)])
    _pgnd(ax, 2.0, y_ - 0.7)
    # FB: the optocoupler transistor and C_fx
    x_, y_ = U1['FB']
    XFX = 2.4
    XOC = 0.3 + 0.77                                 # opto collector
    S.wire(ax, [(x_, y_), (XOC, y_)])
    S.dot(ax, XFX, y_)
    fa, fb_ = S.cap(ax, XFX, y_ - 1.3, horiz=False)
    S.wire(ax, [(XFX, y_), fb_])
    S.wire(ax, [fa, (XFX, y_ - 2.2)])
    _pgnd(ax, XFX, y_ - 2.2)
    S.label(ax, XFX + 0.1, y_ - 3.35, 'C$_{fx}$\n' + _c(_sv('C.fx')),
            size=8.6)
    _, oc, oe = _npn(ax, 0.3, y_ - 1.6, h=1.4)
    S.wire(ax, [oc, (XOC, y_)])
    S.wire(ax, [oe, (XOC, y_ - 2.8)])
    _pgnd(ax, XOC, y_ - 2.8)
    for dy in (0.25, -0.25):
        ax.add_patch(FancyArrowPatch((-0.3, y_ - 1.6 + dy + 0.3),
                                     (0.18, y_ - 1.6 + dy), arrowstyle='-|>',
                                     mutation_scale=9, color=NAVY, lw=1.2,
                                     zorder=5, shrinkA=0, shrinkB=0))
    S.label(ax, -0.3, y_ + 1.05, 'U4, LED on sheet 2', size=8.4,
            color=GREY, ha='left')
    # BM and CFG to ground, ZCD from the auxiliary winding
    for pin, xr_, key, nm in (('BM', 10.2, 'R.BM_sel', 'R$_{BM}$'),
                              ('CFG', 12.0, 'R.CFG_sel', 'R$_{CFG}$')):
        x_, y_ = U1[pin]
        S.wire(ax, [(x_, y_), (xr_, y_)])
        ra, rb = S.res(ax, xr_, y_ - 1.4, horiz=False)
        S.wire(ax, [(xr_, y_), rb])
        S.wire(ax, [ra, (xr_, y_ - 2.6)])
        _pgnd(ax, xr_, y_ - 2.6)
        if pin == 'BM':
            S.label(ax, xr_ - 0.45, y_ - 1.4, nm + '\n'
                    + _r(_sv(key) * 1e3), size=8.6, ha='right')
        else:
            S.label(ax, xr_ + 0.45, y_ - 1.4, nm + '\n'
                    + _r(_sv(key) * 1e3), size=8.6, ha='left')
    x_, y_ = U1['ZCD']
    XZ = 14.4
    S.wire(ax, [(x_, y_), (XZ, y_)])
    S.dot(ax, XZ, y_)
    ra, rb = S.res(ax, XZ, y_ + 1.25, horiz=False)
    S.wire(ax, [(XZ, y_), ra])
    S.wire(ax, [rb, (XZ, y_ + 2.2)])
    _flag(ax, XZ, y_ + 2.2, 'AUX', side='r', size=SZ)
    S.label(ax, XZ + 0.45, y_ + 1.15, 'R$_{ZCD,H}$ '
            + _r(_sv('R.ZCD_H_sel') * 1e3), size=SZ, ha='left')
    ra, rb = S.res(ax, XZ, y_ - 1.4, horiz=False)
    S.wire(ax, [(XZ, y_), rb])
    S.wire(ax, [ra, (XZ, y_ - 2.6)])
    _pgnd(ax, XZ, y_ - 2.6)
    S.label(ax, XZ + 0.45, y_ - 1.4, 'R$_{ZCD,L}$ '
            + _r(_sv('R.ZCD_L_sel') * 1e3), size=SZ, ha='left')
    # ------------------------------------------------- the two drivers
    YV = 20.3                                        # the VCC rail
    W_ = 3.3
    def driver(x0, y0, nm, leg, hin, lin, xvcc):
        """an L6498LD, its bootstrap capacitor and gate resistors"""
        u = _ic(ax, x0, y0, x0 + W_, y0 + 6.0, 'L6498LD',
                [('L', hin, 1, 'HIN'), ('L', lin, 2, 'LIN'),
                 ('T', xvcc, 7, 'VCC'),
                 ('B', x0 + 0.8, 3, 'SGND'), ('B', x0 + 2.5, 5, 'PGND'),
                 ('R', y0 + 5.0, 13, 'BOOT'), ('R', y0 + 3.9, 12, 'HVG'),
                 ('R', y0 + 2.2, 11, 'OUT'), ('R', y0 + 1.1, 6, 'LVG')],
                ref=y0 + 1.75, size=8.6, psize=8.4)
        S.label(ax, x0 + 1.25, y0 + 1.15, nm, size=8.6, color=GREY)
        for pin in ('SGND', 'PGND'):
            gx, gy = u[pin]
            S.wire(ax, [(gx, gy), (gx, gy - 0.3)])
            _pgnd(ax, gx, gy - 0.3)
        xb = x0 + W_ + 1.1                           # bootstrap column
        bx, by = u['BOOT']
        ox, oy = u['OUT']
        hx, hy = u['HVG']
        lx, ly = u['LVG']
        S.wire(ax, [(bx, by), (xb, by)])
        S.dot(ax, xb, by)
        cyc = (by + oy) / 2.0 - 0.45
        ca_, cb_ = S.cap(ax, xb, cyc, horiz=False)
        S.wire(ax, [(xb, by), cb_])
        S.wire(ax, [ca_, (xb, oy)])
        S.dot(ax, xb, oy)
        S.label(ax, xb + 0.4, cyc - 0.05, _c(_sv('C.BOOT')), size=8.4,
                ha='left')
        xr = xb + 1.3
        S.wire(ax, [(hx, hy), (xb - R, hy)])
        X.hop(ax, xb, hy, r=R)
        ra_, rb_ = S.res(ax, xr, hy)
        S.wire(ax, [(xb + R, hy), ra_])
        S.wire(ax, [rb_, (xr + 1.0, hy)])
        _flag(ax, xr + 1.0, hy, 'HVG' + leg, side='r', size=8.6)
        S.wire(ax, [(ox, oy), (xr + 1.0, oy)])
        _flag(ax, xr + 1.0, oy, 'A' if leg == '1' else 'B', side='r',
              size=8.6)
        ra_, rb_ = S.res(ax, xr, ly)
        S.wire(ax, [(lx, ly), ra_])
        S.wire(ax, [rb_, (xr + 1.0, ly)])
        _flag(ax, xr + 1.0, ly, 'LVG' + leg, side='r', size=8.6)
        S.label(ax, xr, hy + 0.55, _r(_sv('R.G')), size=8.4)
        S.label(ax, xr, ly - 0.55, _r(_sv('R.G')), size=8.4)
        return u, xb, by
    u2, xb2, by2 = driver(10.5, 13.3, 'U2', '1', U1['HOUT1'][1],
                          U1['LOUT1'][1], 11.4)
    u3, xb3, by3 = driver(19.3, 6.2, 'U3', '2', U1['HOUT2'][1],
                          U1['LOUT2'][1], 20.2)
    for a_, b_ in ((U1['HOUT1'], u2['HIN']), (U1['LOUT1'], u2['LIN']),
                   (U1['HOUT2'], u3['HIN']), (U1['LOUT2'], u3['LIN'])):
        S.wire(ax, [a_, b_])
    # ------------------------------------------------- V_CC rail
    #  from the controller across to leg 2's driver, which takes it in at
    #  the regulator's output run YO
    XO, YO = 20.2, 14.0
    S.wire(ax, [U1['VCC'], (7.8, YV), (XO, YV), (XO, YO), u3['VCC']])
    S.wire(ax, [u2['VCC'], (11.4, YV)])
    S.dot(ax, 11.4, YV)
    S.label(ax, 17.6, YV + 0.4, 'V$_{CC}$', size=9.0)
    da, dk = S.diode(ax, xb2, (YV + by2) / 2.0 + 0.05, horiz=False,
                     flip=True)
    S.wire(ax, [(xb2, YV), da])
    S.wire(ax, [dk, (xb2, by2)])
    S.dot(ax, xb2, YV)
    S.label(ax, xb2 + 0.45, (YV + by2) / 2.0, 'D$_{BS}$', size=8.6,
            ha='left')
    da, dk = S.diode(ax, xb3, (YO + by3) / 2.0, horiz=False, flip=True)
    S.wire(ax, [(xb3, YO), da])
    S.wire(ax, [dk, (xb3, by3)])
    S.label(ax, xb3 - 0.45, (YO + by3) / 2.0, 'D$_{BS}$', size=8.6,
            ha='right')
    # ------------------------------------------------- V_CC regulator
    N6 = (xw, 20.9)
    S.wire(ax, [p6, N6])
    S.dot(ax, *N6)
    S.wire(ax, [N6, (xw + 0.9, N6[1])])
    _flag(ax, xw + 0.9, N6[1], 'AUX', side='r', size=SZ)
    da, dk = S.diode(ax, xw, 19.95, horiz=False, flip=True)
    S.wire(ax, [N6, da])
    CA = (xw, 19.0)
    S.wire(ax, [dk, CA])
    S.dot(ax, *CA)
    S.label(ax, xw + 0.45, 19.95, 'D$_{aux}$', size=8.6, ha='left')
    XCA = 26.0
    S.wire(ax, [CA, (XCA, CA[1])])
    ca_, cb_ = S.cap(ax, XCA, 18.0, horiz=False)
    S.wire(ax, [(XCA, CA[1]), cb_])
    S.wire(ax, [ca_, (XCA, 17.0)])
    _pgnd(ax, XCA, 17.0)
    S.label(ax, XCA + 0.45, 18.0, 'C$_{aux}$', size=8.6, ha='left')
    XRZ = 23.8
    bq, cq, eq_ = _npn(ax, 22.95, 16.9, h=1.4, left=True)
    S.wire(ax, [CA, (cq[0], CA[1]), cq])
    S.dot(ax, XRZ, CA[1])
    ra_, rb_ = S.res(ax, XRZ, 17.95, horiz=False)
    S.wire(ax, [(XRZ, CA[1]), rb_])
    BN = (XRZ, 16.9)
    S.wire(ax, [ra_, BN])
    S.dot(ax, *BN)
    S.wire(ax, [BN, bq])
    za, zc = _zener(ax, XRZ, 15.9)
    S.wire(ax, [BN, zc])
    S.wire(ax, [za, (XRZ, 15.1)])
    _pgnd(ax, XRZ, 15.1)
    S.label(ax, XRZ + 0.42, 17.95, 'R$_{BZ}$\n' + _r(_sv('R.BZ_sel')),
            size=8.6, ha='left')
    S.label(ax, XRZ + 0.75, 15.9, 'D$_Z$ %.0f V' % _sv('V.DZ_sel'),
            size=8.6, ha='left')
    S.label(ax, cq[0] - 0.3, 17.6, 'Q$_{VCC}$', size=8.6, ha='right')
    ya, yk = S.diode(ax, eq_[0], 15.2, horiz=False, flip=True)
    S.wire(ax, [eq_, ya])
    S.wire(ax, [yk, (eq_[0], YO)])
    S.wire(ax, [(XO, YO), (xb3, YO)])
    S.dot(ax, XO, YO)
    S.dot(ax, eq_[0], YO)
    S.label(ax, eq_[0] - 0.4, 15.2, 'D$_{byp}$', size=8.4, ha='right')
    # C_VCC and the pin ceramic, on the output run
    for xc_ in (25.6, 27.0):
        ca_, cb_ = S.cap(ax, xc_, YO - 1.0, horiz=False)
        S.wire(ax, [(xc_, YO), cb_])
        S.wire(ax, [ca_, (xc_, YO - 1.9)])
        _pgnd(ax, xc_, YO - 1.9)
    S.wire(ax, [(xb3, YO), (27.0, YO)])
    S.dot(ax, xb3, YO)
    S.dot(ax, 25.6, YO)
    S.label(ax, 25.6, YO + 0.45, 'C$_{VCC}$ %s $\\parallel$ %s'
            % (_c(_sv('C.VCC_sel') * 1e3), _c(_sv('C.VCC_hf'))), size=8.4)
    # ------------------------------------------------- legend
    S.label(ax, 27.3, 3.2, 'Sheet 1 of 2:  the primary side', size=10,
            weight='bold', ha='right')
    _pgnd(ax, 18.6, 2.15)
    S.label(ax, 19.1, 2.0, 'primary ground: the bridge return', size=8.6,
            ha='left', color=GREY)
    _term(ax, 18.6, 1.1)
    S.label(ax, 19.1, 1.1, 'net continues at the flag of the same name',
            size=8.6, ha='left', color=GREY)
    save(fig, 'an_full_pri')


def _tl431(ax, x, y):
    """A TL431 as its datasheet draws it: a shunt-regulator triangle, cathode
    up, with REF taken off its left side.  -> (anode, cathode, REF end)"""
    a, c = _zener(ax, x, y)
    s = 0.56 * X.scale(ax) * getattr(ax, '_diode_k', 1.0)
    ax.plot([x - 0.72 * s * 0.5, x - 0.95], [y, y], color=NAVY, lw=1.6,
            zorder=3)
    return a, c, (x - 0.95, y)


def an_full_sec(save, foot):
    """The whole converter, sheet 2 of 2: the secondary side.  The SR stage
    is an_sr_ctrl's own drawing (the secondary windings alone); below it the
    output bank and the voltage loop, joined to it by the V_out flags.
    The LED rail V_Z is a requirement of the loop design and is not sized
    in this note, so it is a block."""
    import an_pdf
    V = an_pdf.V
    fig = plt.figure(figsize=(8.2, 9.7))
    top = _ax(fig, [0.01, 0.335, 0.98, 0.66], -0.4, 27.2, 0.4, 22.4)
    _sr_block(top, full=True)
    ax = _ax(fig, [0.01, 0.005, 0.98, 0.325], -0.4, 27.2, 0.0, 10.4)
    R = 0.20
    YO, YG = 9.6, 0.8                                # V_out, secondary 0 V
    _flag(ax, 0.2, YO, 'V$_{out}$', side='u', size=9.4)
    S.wire(ax, [(0.2, YO), (26.6, YO)])
    _term(ax, 26.6, YO)
    S.label(ax, 26.6, YO + 0.5, '+%.0f V, %.1f A' % (V['Vout'], V['Iout']),
            size=9.4, ha='right')
    S.wire(ax, [(1.2, YG), (26.6, YG)])
    _term(ax, 26.6, YG)
    S.label(ax, 26.6, YG + 0.5, 'output return', size=9.4, ha='right')
    S.gnd(ax, 1.2, YG)
    # the output bank
    for x, txt_ in ((1.8, 'C$_{out}$\n%.0f × %.0f $\\mu$F\n= %.1f mF'
                     % (_sv('n.C'), _sv('C.single'), _sv('C.out'))),
                    (6.4, 'C$_{HF}$\n%.0f $\\mu$F' % _sv('C.ceramic'))):
        ca, cb = S.cap(ax, x, 5.2, horiz=False)
        S.wire(ax, [(x, YO), cb])
        S.wire(ax, [ca, (x, YG)])
        S.dot(ax, x, YO)
        S.dot(ax, x, YG)
        S.label(ax, x + 0.45, 5.2, txt_, size=8.8, ha='left')
    S.label(ax, 1.8 - 0.45, 5.7, '+', size=9, ha='right')
    # the divider and the TL431
    XRI, YREF = 10.6, 3.0
    ra, rb = S.res(ax, XRI, 6.3, horiz=False)
    S.wire(ax, [(XRI, YO), rb])
    S.wire(ax, [ra, (XRI, YREF)])
    S.dot(ax, XRI, YO)
    S.dot(ax, XRI, YREF)
    S.label(ax, XRI - 0.45, 6.3, 'R$_I$\n' + _r(_sv('R.I') * 1e3),
            size=8.8, ha='right')
    ra, rb = S.res(ax, XRI, 1.9, horiz=False)
    S.wire(ax, [(XRI, YREF), rb])
    S.wire(ax, [ra, (XRI, YG)])
    S.dot(ax, XRI, YG)
    S.label(ax, XRI - 0.45, 1.9, 'R$_O$\n' + _r(_sv('R.o') * 1e3),
            size=8.8, ha='right')
    XK = 15.6
    ta, tc, tr = _tl431(ax, XK, YREF)
    S.wire(ax, [(XRI, YREF), tr])
    S.wire(ax, [ta, (XK, YG)])
    S.dot(ax, XK, YG)
    S.label(ax, XK + 0.6, YREF - 0.55, 'U5  TL431', size=8.8, ha='left')
    # compensation between REF and K
    XL_, YF1, YF2 = 11.8, 5.6, 4.4
    S.wire(ax, [(XL_, YREF), (XL_, YF1)])
    S.dot(ax, XL_, YREF)
    S.dot(ax, XL_, YF2)
    ca, cb = S.cap(ax, 13.7, YF1)
    S.wire(ax, [(XL_, YF1), ca])
    S.wire(ax, [cb, (XK, YF1)])
    S.label(ax, 13.7, YF1 + 0.5, 'C$_{Fo}$ ' + _c(_sv('C.Fo')), size=8.6)
    ra, rb = S.res(ax, 13.1, YF2)
    ca, cb = S.cap(ax, 14.7, YF2)
    S.wire(ax, [(XL_, YF2), ra])
    S.wire(ax, [rb, ca])
    S.wire(ax, [cb, (XK, YF2)])
    S.label(ax, 13.1, YF2 - 0.55, 'R$_F$ ' + _r(_sv('R.F') * 1e3), size=8.6)
    S.label(ax, 15.25, YF2 + 0.5, 'C$_F$ ' + _c(_sv('C.F')), size=8.6,
            ha='right')
    # K up to the LED; R_P across it on the left, R_B from the V_Z rail
    YLC, YLA = 6.8, 8.7
    S.wire(ax, [tc, (XK, YLC)])
    S.dot(ax, XK, YF1)
    S.dot(ax, XK, YF2)
    la, lk = S.diode(ax, XK, (YLC + YLA) / 2.0, horiz=False, flip=True)
    S.wire(ax, [(XK, YLA), la])
    S.wire(ax, [lk, (XK, YLC)])
    S.dot(ax, XK, YLC)
    S.dot(ax, XK, YLA)
    ym = (YLC + YLA) / 2.0
    for dy in (0.25, -0.2):
        ax.add_patch(FancyArrowPatch((XK + 0.6, ym + dy),
                                     (XK + 1.05, ym + dy + 0.3),
                                     arrowstyle='-|>', mutation_scale=9,
                                     color=NAVY, lw=1.2, zorder=5,
                                     shrinkA=0, shrinkB=0))
    S.label(ax, XK + 1.25, ym - 0.1, 'U4 LED', size=8.6, ha='left',
            color=GREY)
    XP = XK - 1.7
    S.wire(ax, [(XK, YLA), (XP, YLA)])
    S.wire(ax, [(XK, YLC), (XP, YLC)])
    ra, rb = S.res(ax, XP, ym, horiz=False)
    S.wire(ax, [(XP, YLA), rb])
    S.wire(ax, [ra, (XP, YLC)])
    S.label(ax, XP - 0.45, ym, 'R$_P$\n' + _r(_sv('R.P') * 1e3), size=8.6,
            ha='right')
    XRB_ = 19.6
    ra, rb = S.res(ax, XRB_, YLA)
    S.wire(ax, [(XK, YLA), ra])
    S.label(ax, XRB_, YLA - 0.55, 'R$_B$ ' + _r(_sv('R.B') * 1e3), size=8.6)
    S.box(ax, 23.2, 6.4, 3.0, 2.0,
          'V$_Z$ %.0f V rail\nnot sized here' % _sv('V.Z'), size=8.6)
    S.wire(ax, [rb, (21.0, YLA), (21.0, 6.4), (21.7, 6.4)])
    S.wire(ax, [(23.2, YO), (23.2, 7.4)])
    S.dot(ax, 23.2, YO)
    S.wire(ax, [(23.2, 5.4), (23.2, YG)])
    S.dot(ax, 23.2, YG)
    S.label(top, 27.0, 21.6, 'Sheet 2 of 2:  the secondary side', size=10,
            weight='bold', ha='right')
    S.gnd(top, 21.4, 20.75)
    S.label(top, 21.9, 20.7, 'secondary ground', size=8.6, ha='left',
            color=GREY)
    save(fig, 'an_full_sec')


def an_full(save, foot):
    """The whole converter on one landscape page: primary on the left,
    secondary on the right, T1 between them.  Every value is read from the
    sheet (_sv); a block without a value is a part this note does not size.
    Pin numbers: L6790A as ST's EVL6790_670W control board numbers them,
    L6498LD in SO-14, TEA2095TE in HSO8, T1 as an_xfmr_pins.  The page sets
    it 90 degrees round, so it is drawn at the size it prints: the symbols
    are scaled down (ax._sym_mult) and the diodes a further 20 %.
    """
    import an_pdf
    import cores
    V = an_pdf.V
    _pm = cores.PINMAP
    fig = plt.figure(figsize=(11.0, 8.36))
    W, H = 52.0, 39.5
    ax = _ax(fig, [0.01, 0.01, 0.98, 0.98], 0.0, W, 0.0, H)
    ax._sym_mult = 0.51
    ax._xf_mult = 0.5
    ax._diode_k = 0.8
    R = 0.16
    SZ, SN = 8.6, 8.4                    # value and name lettering
    MH, MG = 1.3, 1.0                    # MOSFET height and gate lead

    def vres(x, ytop, ybot, label=None, side='r', yl=None):
        a_, b_ = S.res(ax, x, (ytop + ybot) / 2.0, horiz=False)
        S.wire(ax, [(x, ytop), b_])
        S.wire(ax, [a_, (x, ybot)])
        if label:
            yy = (ytop + ybot) / 2.0 if yl is None else yl
            S.label(ax, x + (0.4 if side == 'r' else -0.4), yy, label,
                    size=SZ, ha='left' if side == 'r' else 'right')

    def vcap(x, ytop, ybot, label=None, side='r'):
        a_, b_ = S.cap(ax, x, (ytop + ybot) / 2.0, horiz=False)
        S.wire(ax, [(x, ytop), b_])
        S.wire(ax, [a_, (x, ybot)])
        if label:
            S.label(ax, x + (0.45 if side == 'r' else -0.45),
                    (ytop + ybot) / 2.0, label, size=SZ,
                    ha='left' if side == 'r' else 'right')

    def pg(x, y, lead=0.35):              # primary ground on a short lead
        S.wire(ax, [(x, y), (x, y - lead)])
        _pgnd(ax, x, y - lead)

    def sg(x, y, lead=0.3):               # secondary ground
        if lead:
            S.wire(ax, [(x, y), (x, y - lead)])
        y -= lead
        s_ = 0.30
        for k, w in enumerate((1.0, 0.62, 0.28)):
            ax.plot([x - s_ * w, x + s_ * w], [y - k * 0.17] * 2,
                    color=NAVY, lw=1.6, zorder=3)

    # ================================================= primary power band
    YL, YN = 37.4, 33.8
    for yy, nm in ((YL, 'L'), (YN, 'N')):
        _term(ax, 0.35, yy)
        S.label(ax, 0.35, yy + 0.5, nm, size=SN)
        S.wire(ax, [(0.35, yy), (1.1, yy)])
    S.label(ax, 0.1, 39.05, '%.0f–%.0f Vac' % (V['Vacmin'], V['Vacmax']),
            size=SN, ha='left', color=GREY)
    S.box(ax, 2.3, 35.6, 2.4, 5.0, 'EMI\nfilter\n\nnot\nsized', size=SN)
    XH1, XH2 = 4.3, 5.3
    S.wire(ax, [(3.5, YL), (6.2, YL)])
    S.dot(ax, XH1, YL)
    S.wire(ax, [(3.5, YN), (XH1 - R, YN)])
    X.hop(ax, XH1, YN, r=R)
    S.wire(ax, [(XH1 + R, YN), (6.2, YN)])
    S.dot(ax, XH2, YN)
    a1, k1 = S.diode(ax, XH1, 32.2, horiz=False, flip=True)
    a2, k2 = S.diode(ax, XH2, 32.2, horiz=False, flip=True)
    S.wire(ax, [(XH1, YL), a1])
    S.wire(ax, [(XH2, YN), a2])
    YJ = 31.2
    S.wire(ax, [k2, (XH2, YJ), (XH1, YJ)])
    S.label(ax, XH1 - 0.45, 32.2, 'D$_{HV}$\nS1M', size=SN, ha='right')
    S.box(ax, 7.2, 35.6, 2.0, 5.0, 'BR1', size=9.4, weight='bold')
    XCI, XM, YG = 9.0, 10.3, 31.0
    X1, X2 = 14.8, 19.6                   # the two bridge legs
    S.wire(ax, [(8.2, YL), (X2, YL)])
    S.dot(ax, XCI, YL)
    vcap(XCI, YL, YN)
    S.label(ax, XCI + 0.45, 35.6, 'C$_{in}$\n' + _c(_sv('C.in_sel')), size=SZ,
            ha='left')
    S.wire(ax, [(8.2, YN), (XM, YN), (XM, YG)])
    S.dot(ax, XCI, YN)
    S.dot(ax, XM, YG)
    ra, rb = S.res(ax, 11.9, YG)
    S.wire(ax, [(XM, YG), ra])
    S.wire(ax, [rb, (X2, YG)])
    S.label(ax, 11.9, YG - 0.75, 'R$_{CS}$ %.0f m$\\Omega$' % _sv('R.CS'),
            size=SZ)
    S.label(ax, 11.9, YG - 1.35, '%.0f × %.0f m$\\Omega$'
            % (_sv('N.RCS'), _sv('R.CS_single')), size=SN, color=GREY)
    S.dot(ax, 13.6, YG)
    pg(13.6, YG)
    YH, YLO, YA, YB = 36.0, 32.6, 34.3, 33.7
    for x, nh, nl in ((X1, 'S1', 'S2'), (X2, 'S3', 'S4')):
        d1, s1 = X.mosfet(ax, x, YH, None, 'plain', h=MH, gate=MG,
                          body=True, coss=False)
        d2, s2 = X.mosfet(ax, x, YLO, None, 'plain', h=MH, gate=MG,
                          body=True, coss=False)
        S.wire(ax, [d1, (x, YL)])
        S.wire(ax, [s1, d2])
        S.wire(ax, [s2, (x, YG)])
        S.label(ax, x + 1.05, YH + 0.45, nh, size=9.0, weight='bold',
                ha='left')
        S.label(ax, x + 1.05, YLO - 0.45, nl, size=9.0, weight='bold',
                ha='left')
        _flag(ax, x - MG, YH, 'HVG' + ('1' if x == X1 else '2'), side='l',
              size=SN)
        _flag(ax, x - MG, YLO, 'LVG' + ('1' if x == X1 else '2'), side='l',
              size=SN)
    S.dot(ax, X1, YL)
    S.dot(ax, X1, YG)
    S.label(ax, 17.5, 38.05, 'S1–S4  STO60N045DM9', size=SN, color=GREY)
    S.dot(ax, X1, YA)
    S.label(ax, X1 - 0.35, YA + 0.4, 'A', size=9.0, weight='bold')
    S.wire(ax, [(X1, YA), (X2 - R, YA)])
    X.hop(ax, X2, YA, r=R)
    XCR = 21.6
    ca, cb = S.cap(ax, XCR, YA)
    S.wire(ax, [(X2 + R, YA), ca])
    S.label(ax, XCR, YA + 0.6, 'C$_r$ ' + _c(_sv('C.r')), size=SZ)
    S.dot(ax, X2, YB)
    S.label(ax, X2 + 1.4, YB - 0.4, 'B', size=9.0, weight='bold')
    # ================================================= T1, both sides
    XC = 26.4
    (p1, p3), (p4, p6), (s7, s9), (s10, s12) = _xf(
        ax, XC, [('L', 37.0, 33.7, 5), ('L', 32.8, 30.2, 3),
                 ('R', 37.0, 33.8, 5), ('R', 33.4, 30.2, 5)])
    xw, xs = p1[0], s7[0]
    S.wire(ax, [cb, (22.9, YA), (22.9, p1[1]), p1])
    S.wire(ax, [(X2, YB), p3])
    S.wire(ax, [s9, s10])
    S.dot(ax, xs, 33.6)
    for (px, py), n_ in ((p1, _pm['NP1'][0][0]), (p3, _pm['NP1'][1][0]),
                         (p4, _pm['NAUX'][0][0]), (p6, _pm['NAUX'][1][0])):
        S.label(ax, px - 0.35, py + (0.3 if (px, py) != p6 else -0.35),
                str(n_), size=SN, color=GREY, ha='right')
    for (px, py), n_ in ((s7, _pm['NS2'][0][0]), (s12, _pm['NS3'][1][0])):
        S.label(ax, px + 0.35, py + 0.3 if n_ == _pm['NS2'][0][0] else py - 0.3,
                str(n_), size=SN, color=GREY, ha='left')
    S.label(ax, xs + 0.35, 33.25, '%d, %d' % (_pm['NS2'][1][0],
                                              _pm['NS3'][0][0]),
            size=SN, color=GREY, ha='left')
    S.label(ax, 24.6, 39.1, 'T1  PQ 50/50, N97', size=9.0, weight='bold')
    S.label(ax, 24.6, 38.5, 'L$_{open}$ %.0f $\\mu$H, L$_r$ %.0f $\\mu$H'
            % (_sv('L.open'), _sv('L.short')), size=SN, color=GREY)
    S.label(ax, xw - 0.5, 35.4, 'NP1\n%.0f T' % _sv('N.p'), size=SN,
            ha='right')
    S.wire(ax, [p4, (23.4, p4[1]), (23.4, p4[1] - 0.2)])
    _pgnd(ax, 23.4, p4[1] - 0.2)
    S.label(ax, xw - 0.5, 31.4, 'NAUX\n%.0f T' % _sv('N.aux'), size=SN,
            ha='right')
    S.label(ax, xs + 0.5, 35.4, 'NS2\n%.0f T' % _sv('N.s'), size=SN,
            ha='left')
    S.label(ax, xs + 0.5, 31.6, 'NS3\n%.0f T' % _sv('N.s'), size=SN,
            ha='left')

    # ================================================= controller U1
    XU0, XU1, YU0, YU1 = 3.3, 9.6, 10.0, 27.4
    U1 = _ic(ax, XU0, YU0, XU1, YU1, 'L6790A',
             [('T', XH1, 1, 'HVSU'), ('T', 6.3, 6, 'ISEN'),
              ('T', 8.3, 4, 'VCC'),
              ('R', 25.8, 16, 'HOUT1'), ('R', 24.8, 15, 'LOUT1'),
              ('R', 15.8, 14, 'HOUT2'), ('R', 14.8, 13, 'LOUT2'),
              ('B', 4.2, 12, 'ZCD'), ('B', 6.3, 11, 'CFG'),
              ('B', 8.4, 10, 'BM'),
              ('L', 26.0, 3, 'DRV_EN'), ('L', 23.6, 7, 'RT'),
              ('L', 21.2, 8, 'CT'), ('L', 18.8, 5, 'GND'),
              ('L', 15.4, 9, 'FB')], ref=20.6, size=SN, psize=SN,
             tsize=9.4, tpad=0.45)
    S.label(ax, 6.3, 19.8, 'U1', size=SN, color=GREY)
    S.wire(ax, [k1, U1['HVSU']])
    S.dot(ax, XH1, YJ)
    YIS = 29.8
    S.wire(ax, [(XM, YG), (XM, YIS), (U1['ISEN'][0], YIS), U1['ISEN']])
    x_, y_ = U1['DRV_EN']
    S.wire(ax, [(x_, y_), (1.0, y_)])
    _term(ax, 1.0, y_)
    S.label(ax, 1.0, y_ + 0.5, 'open', size=SN, color=GREY)
    for pin, kind, val, nm in (('RT', 'res', _r(_sv('R.T') * 1e3), 'R$_T$'),
                               ('CT', 'cap', _c(_sv('C.T') / 1e3), 'C$_T$')):
        x_, y_ = U1[pin]
        a_, b_ = (S.res if kind == 'res' else S.cap)(ax, 1.6, y_)
        S.wire(ax, [(x_, y_), b_])
        S.wire(ax, [a_, (0.5, y_)])
        pg(0.5, y_, 0.4)
        S.label(ax, 1.6, y_ + 0.85, nm + '\n' + val, size=SZ)
    x_, y_ = U1['GND']
    S.wire(ax, [(x_, y_), (1.8, y_)])
    pg(1.8, y_, 0.4)
    # FB: the optocoupler's transistor and C_fx
    x_, y_ = U1['FB']
    XOC, XFX = 1.15, 2.3
    S.wire(ax, [(x_, y_), (XOC, y_)])
    S.dot(ax, XFX, y_)
    vcap(XFX, y_, y_ - 1.8)
    pg(XFX, y_ - 1.8, 0.3)
    S.label(ax, 0.05, y_ - 3.5, 'C$_{fx}$ ' + _c(_sv('C.fx')), size=SZ,
            ha='left')
    _, oc, oe = _npn(ax, 0.6, y_ - 1.25, h=1.0)
    S.wire(ax, [oc, (XOC, y_)])
    S.wire(ax, [oe, (XOC, y_ - 2.2)])
    pg(XOC, y_ - 2.2, 0.0)
    for dy in (0.2, -0.2):
        ax.add_patch(FancyArrowPatch((0.05, y_ - 1.25 + dy + 0.25),
                                     (0.4, y_ - 1.25 + dy), arrowstyle='-|>',
                                     mutation_scale=7, color=NAVY, lw=1.0,
                                     zorder=5, shrinkA=0, shrinkB=0))
    S.label(ax, 0.1, y_ + 0.55, 'U4', size=SN, ha='left', color=GREY)
    # ZCD from AUX through a divider; CFG and BM to ground
    zx, zy = U1['ZCD']
    YZN = 8.2
    S.wire(ax, [(zx, zy), (zx, YZN)])
    S.dot(ax, zx, YZN)
    ra_, rb_ = S.res(ax, 2.8, YZN)
    S.wire(ax, [(zx, YZN), rb_])
    S.wire(ax, [ra_, (1.4, YZN)])
    _flag(ax, 1.4, YZN, 'AUX', side='l', size=SN)
    S.label(ax, 3.9, YZN + 0.6, 'R$_{ZCD,H}$ ' + _r(_sv('R.ZCD_H_sel') * 1e3),
            size=SZ, ha='right')
    vres(zx, YZN, 4.8, 'R$_{ZCD,L}$\n' + _r(_sv('R.ZCD_L_sel') * 1e3), 'l',
         yl=6.4)
    pg(zx, 4.8)
    for pin, key, nm in (('CFG', 'R.CFG_sel', 'R$_{CFG}$'),
                         ('BM', 'R.BM_sel', 'R$_{BM}$')):
        x_, y_ = U1[pin]
        vres(x_, y_, 6.6, nm + '\n' + _r(_sv(key) * 1e3), yl=8.0)
        pg(x_, 6.6)

    # ================================================= drivers U2, U3
    YV, XO, YO = 28.4, 22.0, 18.4
    W_, H_ = 4.4, 7.0

    def driver(x0, y0, nm, leg):
        u = _ic(ax, x0, y0, x0 + W_, y0 + H_, 'L6498LD',
                [('L', y0 + 5.8, 1, 'HIN'), ('L', y0 + 4.8, 2, 'LIN'),
                 ('T', x0 + 2.2, 7, 'VCC'),
                 ('B', x0 + 0.9, 3, 'SGND'), ('B', x0 + 2.9, 5, 'PGND'),
                 ('R', y0 + 5.8, 13, 'BOOT'), ('R', y0 + 4.8, 12, 'HVG'),
                 ('R', y0 + 3.4, 11, 'OUT'), ('R', y0 + 1.6, 6, 'LVG')],
                ref=y0 + 2.5, size=SN, psize=SN, tsize=9.0,
                tpad=0.45)
        S.label(ax, x0 + 1.4, y0 + 1.6, nm, size=SN, color=GREY)
        for pin in ('SGND', 'PGND'):
            gx, gy = u[pin]
            pg(gx, gy, 0.15)
        xb = x0 + W_ + 1.1
        bx, by = u['BOOT']
        ox, oy = u['OUT']
        hx, hy = u['HVG']
        lx, ly = u['LVG']
        S.wire(ax, [(bx, by), (xb, by)])
        S.dot(ax, xb, by)
        cyc = (by + oy) / 2.0
        ca_, cb_ = S.cap(ax, xb, oy + 0.55, horiz=False)
        S.wire(ax, [(xb, by), cb_])
        S.wire(ax, [ca_, (xb, oy)])
        S.dot(ax, xb, oy)
        xr = xb + 1.3
        S.wire(ax, [(hx, hy), (xb - R, hy)])
        X.hop(ax, xb, hy, r=R)
        ra_, rb_ = S.res(ax, xr, hy)
        S.wire(ax, [(xb + R, hy), ra_])
        S.wire(ax, [rb_, (xr + 1.0, hy)])
        _flag(ax, xr + 1.0, hy, 'HVG' + leg, side='r', size=SN)
        S.wire(ax, [(ox, oy), (xr + 1.0, oy)])
        _flag(ax, xr + 1.0, oy, 'A' if leg == '1' else 'B', side='r',
              size=SN)
        ra_, rb_ = S.res(ax, xr, ly)
        S.wire(ax, [(lx, ly), ra_])
        S.wire(ax, [rb_, (xr + 1.0, ly)])
        _flag(ax, xr + 1.0, ly, 'LVG' + leg, side='r', size=SN)
        return u, xb, by
    XD = 11.6
    u2, xb2, by2 = driver(XD, 20.0, 'U2', '1')
    u3, xb3, by3 = driver(XD, 10.0, 'U3', '2')
    for a_, b_ in ((U1['HOUT1'], u2['HIN']), (U1['LOUT1'], u2['LIN']),
                   (U1['HOUT2'], u3['HIN']), (U1['LOUT2'], u3['LIN'])):
        S.wire(ax, [a_, b_])
    #  V_CC: the controller and leg 1 on YV, leg 2 on the regulator's
    #  output run YO, joined by XO
    S.wire(ax, [U1['VCC'], (U1['VCC'][0], YV), (XO, YV), (XO, YO)])
    S.wire(ax, [u2['VCC'], (u2['VCC'][0], YV)])
    S.dot(ax, u2['VCC'][0], YV)
    S.wire(ax, [u3['VCC'], (u3['VCC'][0], YO), (XO, YO)])
    S.label(ax, 11.0, YV + 0.45, 'V$_{CC}$', size=SZ)
    for xb_, ytop, by_ in ((xb2, YV, by2), (xb3, YO, by3)):
        da, dk = S.diode(ax, xb_, (ytop + by_) / 2.0, horiz=False, flip=True)
        S.wire(ax, [(xb_, ytop), da])
        S.wire(ax, [dk, (xb_, by_)])
        S.dot(ax, xb_, ytop)
        S.label(ax, xb_ + 0.4, (ytop + by_) / 2.0, 'D$_{BS}$', size=SN,
                ha='left')
    S.label(ax, 16.0, 8.4, 'D$_{BS}$ PNU65010ER,  C$_{BOOT}$ %s,  R$_G$ %s'
            % (_c(_sv('C.BOOT')), _r(_sv('R.G'))), size=SN, color=GREY)

    # ================================================= V_CC regulator
    N6 = (xw, 29.3)
    S.wire(ax, [p6, N6])
    S.dot(ax, *N6)
    S.wire(ax, [N6, (xw - 0.9, N6[1])])
    _flag(ax, xw - 0.9, N6[1], 'AUX', side='l', size=SN)
    da, dk = S.diode(ax, xw, 28.45, horiz=False, flip=True)
    S.wire(ax, [N6, da])
    YCA = 27.6
    S.wire(ax, [dk, (xw, YCA)])
    S.label(ax, xw + 0.4, 28.45, 'D$_{aux}$ PMEG10010ELR', size=SN,
            ha='left')
    XRZ, XCA = xw + 1.0, xw + 4.6
    bq, cq, eq_ = _npn(ax, XRZ + 0.6, 24.9, h=1.0)
    S.wire(ax, [(xw, YCA), (XCA, YCA)])
    S.dot(ax, XRZ, YCA)
    S.dot(ax, cq[0], YCA)
    S.wire(ax, [(cq[0], YCA), cq])
    vcap(XCA, YCA, 25.8, 'C$_{aux}$', side='l')
    pg(XCA, 25.8, 0.2)
    vres(XRZ, YCA, 24.9, 'R$_{BZ}$\n' + _r(_sv('R.BZ_sel')), side='l')
    S.dot(ax, XRZ, 24.9)
    S.wire(ax, [(XRZ, 24.9), bq])
    za, zc = _zener(ax, XRZ, 23.9)
    S.wire(ax, [(XRZ, 24.9), zc])
    S.wire(ax, [za, (XRZ, 23.2)])
    _pgnd(ax, XRZ, 23.2)
    S.label(ax, XRZ - 0.45, 23.9, 'D$_Z$\nBZT52H-C15', size=SN, ha='right')
    S.label(ax, cq[0] + 0.35, 24.2, 'Q$_{VCC}$\nPHPT61003NY', size=SN,
            ha='left')
    ya, yk = S.diode(ax, eq_[0], 21.4, horiz=False, flip=True)
    S.wire(ax, [eq_, ya])
    S.wire(ax, [yk, (eq_[0], YO)])
    S.label(ax, eq_[0] - 0.4, 21.4, 'D$_{byp}$\nPMEG10010ELR', size=SN,
            ha='right')
    S.wire(ax, [(XO, YO), (eq_[0], YO)])
    S.dot(ax, XO, YO)
    for xc_ in (22.8, 24.0):
        S.dot(ax, xc_, YO)
        vcap(xc_, YO, YO - 1.3)
        pg(xc_, YO - 1.3, 0.15)
    S.label(ax, 24.45, YO - 0.75, 'C$_{VCC}$ ' + _c(_sv('C.VCC_sel') * 1e3)
            + ' $\\parallel$ ' + _c(_sv('C.VCC_hf')), size=SN, ha='left')

    # ================================================= SR stage
    XV = 32.0                                   # V_out leaves the centre tap
    S.wire(ax, [(xs, 33.6), (XV, 33.6)])
    TX0, TX1, TY0, TY1 = 35.2, 39.6, 30.8, 36.8
    c = _ic(ax, TX0, TY0, TX1, TY1, 'TEA2095TE',
            [('R', 36.0, 8, 'GDA'), ('R', 34.3, 5, 'SSA'),
             ('T', 37.6, 6, 'DSA'), ('L', 36.0, 7, 'VCC'),
             ('R', 33.2, 4, 'SSB'), ('R', 32.1, 1, 'GDB'),
             ('B', 37.6, 3, 'DSB'), ('B', 36.0, 2, 'GND')], ref=35.15,
            size=SN, psize=SN, tsize=8.6, tpad=0.45)
    S.label(ax, 36.6, 34.3, 'U7', size=SN, color=GREY)
    sg(*c['GND'], lead=0.0)
    vx, vy = c['VCC']
    XSR = 34.0
    S.wire(ax, [(vx, vy), (32.9, vy)])
    S.dot(ax, XSR, vy)
    vcap(XSR, vy, 34.4)
    sg(XSR, 34.4, 0.1)
    _flag(ax, 32.9, vy, 'V$_{CC,SR}$', side='u', size=SN)
    S.label(ax, XSR - 0.4, 35.0, 'C$_{SR}$\n' + _c(_sv('C.SR') * 1e3),
            size=SN, ha='right')
    XG, XRG, XQ1, XQ2 = 40.8, 42.0, 44.6, 47.9
    XSA, XSB, XGN = 49.6, 50.2, 51.0

    def pair(yc, ydrain, ysrc, gate_pin, leg, hop_y):
        for x in (XQ1, XQ2):
            d, s_ = X.mosfet(ax, x, yc, None, 'plain', h=MH, gate=MG,
                             body=True, coss=False)
            S.wire(ax, [d, (x, ydrain)])
            S.wire(ax, [s_, (x, ysrc)])
        S.dot(ax, XQ1, ydrain)
        for x, k in ((XQ1, 1), (XQ2, 2)):
            S.label(ax, x + 1.0, yc + 0.55, 'Q$_{%s%d}$' % (leg, k), size=SN,
                    ha='left', weight='bold')
        gpx, gpy = gate_pin
        ys_ = sorted((gpy, yc, hop_y))
        S.wire(ax, [(gpx, gpy), (XG, gpy)])
        S.wire(ax, [(XG, ys_[0]), (XG, ys_[2])])
        S.dot(ax, XG, ys_[1])
        r1a, r1b = S.res(ax, XRG, yc)
        S.wire(ax, [(XG, yc), r1a])
        S.wire(ax, [r1b, (XQ1 - MG, yc)])
        r2a, r2b = S.res(ax, XRG, hop_y)
        S.wire(ax, [(XG, hop_y), r2a])
        S.wire(ax, [r2b, (XQ1 - R, hop_y)])
        X.hop(ax, XQ1, hop_y, r=R)
        xu = XQ2 - MG - 0.6
        S.wire(ax, [(XQ1 + R, hop_y), (xu, hop_y), (xu, yc),
                    (XQ2 - MG, yc)])
        S.wire(ax, [(XQ1, ysrc), (XGN, ysrc)])
        S.dot(ax, XQ2, ysrc)
        sg(XGN, ysrc, 0.2)

    # leg A: NS2 from pin 7, drains on YDA
    YDA, YCA_, YSA = 38.4, 36.9, 34.8
    pair(YCA_, YDA, YSA, c['GDA'], 'A', 35.5)
    S.wire(ax, [s7, (xs, YDA), (XQ2, YDA)])
    dx_, dy_ = c['DSA']
    S.wire(ax, [(dx_, dy_), (dx_, YDA)])
    S.dot(ax, dx_, YDA)
    sx_, sy_ = c['SSA']
    S.wire(ax, [(sx_, sy_), (XSA, sy_), (XSA, YSA)])
    S.dot(ax, XSA, YSA)
    # leg B: NS3 from pin 12, drains on YDB; the bus hops V_out and the
    # gate run
    YDB, YCB, YSB = 29.4, 27.9, 26.0
    pair(YCB, YDB, YSB, c['GDB'], 'B', 26.6)
    S.wire(ax, [s12, (xs, YDB), (XV - R, YDB)])
    X.hop(ax, XV, YDB, r=R)
    S.wire(ax, [(XV + R, YDB), (XG - R, YDB)])
    X.hop(ax, XG, YDB, r=R)
    S.wire(ax, [(XG + R, YDB), (XQ2, YDB)])
    dx_, dy_ = c['DSB']
    S.wire(ax, [(dx_, dy_), (dx_, YDB)])
    S.dot(ax, dx_, YDB)
    sx_, sy_ = c['SSB']
    S.wire(ax, [(sx_, sy_), (XSB, sy_), (XSB, YSB)])
    S.dot(ax, XSB, YSB)
    S.label(ax, 51.8, 39.1, 'Q$_{A1}$–Q$_{B2}$  STL160N10F8, two in parallel '
            'per leg, one R$_G$ each', size=SN, color=GREY, ha='right')

    # ================================================= output bank
    YO2, YT = 23.4, 15.6
    S.wire(ax, [(XV, 33.6), (XV, YT)])
    S.dot(ax, XV, YO2)
    S.wire(ax, [(XV, YO2), (51.4, YO2)])
    _term(ax, 51.4, YO2)
    S.label(ax, 51.6, YO2 + 0.55, '+%.0f V, %.1f A' % (V['Vout'], V['Iout']),
            size=SN, ha='right')
    _term(ax, 51.4, 21.4)
    S.wire(ax, [(51.4, 21.4), (50.6, 21.4)])
    sg(50.6, 21.4, 0.0)
    S.label(ax, 51.6, 20.6, 'return', size=SN, ha='right')
    for x, txt_ in ((33.2, 'C$_{out}$ %.1f mF\n%.0f × %.0f $\\mu$F'
                     % (_sv('C.out'), _sv('n.C'), _sv('C.single'))),
                    (37.8, 'C$_{HF}$\n%.0f $\\mu$F' % _sv('C.ceramic'))):
        S.dot(ax, x, YO2)
        vcap(x, YO2, 20.8)
        sg(x, 20.8, 0.1)
        S.label(ax, x + 0.45, 22.1, txt_, size=SZ, ha='left')
    # the SR supply follower (14c.4)
    XRB, XQB = 43.2, 43.8
    S.dot(ax, XRB, YO2)
    vres(XRB, YO2, 20.6, 'R$_{BSR}$\n' + _r(_sv('R.BSR_sel')), side='l')
    S.dot(ax, XRB, 20.6)
    bq, cq, eq_ = _npn(ax, XQB, 20.6, h=1.0)
    S.wire(ax, [(XRB, 20.6), bq])
    S.wire(ax, [cq, (cq[0], YO2)])
    S.dot(ax, cq[0], YO2)
    za, zc = _zener(ax, XRB, 19.6)
    S.wire(ax, [(XRB, 20.6), zc])
    S.wire(ax, [za, (XRB, 18.9)])
    sg(XRB, 18.9, 0.0)
    S.label(ax, XRB - 0.45, 19.4, 'D$_{ZSR}$\nBZT52H-C15', size=SN,
            ha='right')
    S.wire(ax, [eq_, (eq_[0], 18.8)])
    _flag(ax, eq_[0], 18.8, 'V$_{CC,SR}$', side='r', size=SN)
    S.label(ax, eq_[0] + 0.35, 21.3, 'Q$_{SR}$\nPHPT61003NY', size=SN,
            ha='left')

    # ================================================= voltage loop
    YGR = 1.4
    XRI, YREF = 33.4, 4.6
    S.wire(ax, [(XV, YT), (44.0, YT)])
    vres(XRI, YT, YREF, 'R$_I$\n' + _r(_sv('R.I') * 1e3), side='l')
    S.dot(ax, XRI, YT)
    vres(XRI, YREF, YGR, 'R$_O$\n' + _r(_sv('R.o') * 1e3), side='l')
    S.dot(ax, XRI, YREF)
    XK = 39.4
    ta, tc, tr = _tl431(ax, XK, YREF)
    XL_, YF1, YF2 = 34.6, 8.4, 6.8
    S.wire(ax, [(XRI, YREF), tr])
    S.dot(ax, XL_, YREF)
    S.wire(ax, [ta, (XK, YGR)])
    S.label(ax, XK + 0.45, YREF - 0.6, 'U5\nTL431', size=SN, ha='left')
    S.wire(ax, [(XL_, YREF), (XL_, YF1)])
    S.dot(ax, XL_, YF2)
    ca, cb = S.cap(ax, 37.0, YF1)
    S.wire(ax, [(XL_, YF1), ca])
    S.wire(ax, [cb, (XK, YF1)])
    S.label(ax, 37.0, YF1 + 0.55, 'C$_{Fo}$ ' + _c(_sv('C.Fo')), size=SZ)
    ra, rb = S.res(ax, 35.8, YF2)
    ca, cb = S.cap(ax, 37.9, YF2)
    S.wire(ax, [(XL_, YF2), ra])
    S.wire(ax, [rb, ca])
    S.wire(ax, [cb, (XK, YF2)])
    S.label(ax, 35.8, YF2 - 0.6, 'R$_F$ ' + _r(_sv('R.F') * 1e3), size=SZ)
    S.label(ax, 37.9, YF2 + 0.6, 'C$_F$ ' + _c(_sv('C.F')), size=SZ)
    YLC, YLA = 10.2, 12.4
    S.wire(ax, [tc, (XK, YLC)])
    S.dot(ax, XK, YF1)
    S.dot(ax, XK, YF2)
    la, lk = S.diode(ax, XK, (YLC + YLA) / 2.0, horiz=False, flip=True)
    S.wire(ax, [(XK, YLA), la])
    S.wire(ax, [lk, (XK, YLC)])
    S.dot(ax, XK, YLC)
    S.dot(ax, XK, YLA)
    ym = (YLC + YLA) / 2.0
    for dy in (0.2, -0.2):
        ax.add_patch(FancyArrowPatch((XK + 0.45, ym + dy),
                                     (XK + 0.85, ym + dy + 0.25),
                                     arrowstyle='-|>', mutation_scale=7,
                                     color=NAVY, lw=1.0, zorder=5,
                                     shrinkA=0, shrinkB=0))
    S.label(ax, XK + 1.0, ym - 0.1, 'U4', size=SN, ha='left', color=GREY)
    XP = XK - 1.6
    S.wire(ax, [(XK, YLA), (XP, YLA)])
    S.wire(ax, [(XK, YLC), (XP, YLC)])
    vres(XP, YLA, YLC, 'R$_P$\n' + _r(_sv('R.P') * 1e3), side='l')
    # the LED rail V_Z: R_Z from V_out, U6 as a shunt regulator (16.1b)
    XRB_, XRZ_, XZD, XU6, XCZ = 41.8, 44.0, 46.0, 48.0, 51.0
    ra, rb = S.res(ax, XRB_, YLA)
    S.wire(ax, [(XK, YLA), ra])
    S.wire(ax, [rb, (XCZ, YLA)])
    S.label(ax, XRB_, YLA + 0.55, 'R$_B$ ' + _r(_sv('R.B') * 1e3), size=SZ)
    vres(XRZ_, YT, YLA, 'R$_Z$ ' + _r(_sv('R.Z_sel')))
    for x in (XRZ_, XZD, XU6):
        S.dot(ax, x, YLA)
    S.label(ax, 46.0, YLA + 0.5, 'V$_Z$ %.1f V' % _sv('V.Z'), size=SZ,
            ha='left')
    YRZ = 6.6
    vres(XZD, YLA, YRZ, 'R$_{Z1}$\n' + _r(_sv('R.Z1') * 1e3), side='l')
    vres(XZD, YRZ, YGR, 'R$_{Z2}$\n' + _r(_sv('R.Z2') * 1e3), side='l')
    S.dot(ax, XZD, YRZ)
    ua, uc, ur = _tl431(ax, XU6, YRZ)
    S.wire(ax, [(XZD, YRZ), ur])
    S.wire(ax, [uc, (XU6, YLA)])
    S.wire(ax, [ua, (XU6, YGR)])
    S.label(ax, XU6 + 0.45, YRZ - 0.7, 'U6\nTL431B', size=SN, ha='left')
    vcap(XCZ, YLA, YGR)
    S.label(ax, XCZ - 0.4, 9.4, 'C$_Z$\n' + _c(_sv('C.Z') * 1e3), size=SZ,
            ha='right')
    S.wire(ax, [(XRI, YGR), (XCZ, YGR)])
    for x in (XK, XZD, XU6):
        S.dot(ax, x, YGR)
    sg(42.0, YGR, 0.3)
    S.dot(ax, 42.0, YGR)

    # ================================================= legend
    YLG = 5.6
    _pgnd(ax, 16.2, YLG + 0.25)
    S.label(ax, 16.7, YLG, 'primary ground (bridge return)', size=SN,
            ha='left', color=GREY)
    sg(16.2, YLG - 1.05, 0.0)
    S.label(ax, 16.7, YLG - 1.3, 'secondary ground (output return)',
            size=SN, ha='left', color=GREY)
    _term(ax, 16.2, YLG - 2.4)
    S.label(ax, 16.7, YLG - 2.4, 'net continues at the flag of the same name',
            size=SN, ha='left', color=GREY)
    S.label(ax, 16.0, YLG - 3.6, 'Q$_{VCC}$, Q$_{SR}$: 6 cm$^2$ collector pad;'
            '  D$_Z$, D$_{ZSR}$: 1 cm$^2$ cathode pad', size=SN, ha='left',
            color=GREY)
    S.label(ax, 16.0, YLG - 4.5, 'R$_{BZ}$ ≥ %.2f W, R$_{BSR}$ ≥ %.2f W, '
            'R$_Z$ ≥ %.2f W (at OVP1)' % (_sv('P.RBZ'), _sv('P.RBSR'),
                                        _sv('P.RZ')),
            size=SN, ha='left', color=GREY)
    save(fig, 'an_full')


FIGS = {'an_rac': an_rac, 'an_integrated': an_integrated,
        'an_pfc_cap': an_pfc_cap, 'an_pfc_boost': an_pfc_boost,
        'an_pfc_ccm': an_pfc_ccm, 'an_two_stage': an_two_stage,
        'an_llc_waves': an_llc_waves, 'an_three_cases': an_three_cases,
        'an_cap_ind': an_cap_ind, 'an_loadshift': an_loadshift,
        'an_peakgain': an_peakgain, 'an_recovery': an_recovery,
        'an_core_section': an_core_section,
        'an_core_plan': an_core_plan,
        'an_loop_blocks': an_loop_blocks,
        'an_comp_opamp': an_comp_opamp, 'an_loop_example': an_loop_example,
        'an_flyback_llc': an_flyback_llc, 'an_mmf': an_mmf,
        'an_flux_steps': an_flux_steps, 'an_dc_overlap': an_dc_overlap,
        'an_xfmr_read': an_xfmr_read, 'an_xfmr_pins': an_xfmr_pins,
        'an_gate_drive': an_gate_drive, 'an_sr_ctrl': an_sr_ctrl,
        'an_full_pri': an_full_pri, 'an_full_sec': an_full_sec,
        'an_full': an_full}
