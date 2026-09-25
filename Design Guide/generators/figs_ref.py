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
    coming out the wrong shape.  The third panel is a layer-by-layer
    diagram of the secondary and says so: at true scale the twelve foil
    layers are three millimetres and read as a single bar, which is what
    the first version showed and what could not be read.

    Dimensions are from the TDK dimensional drawings of the chosen core
    and coil former (cores.MECH, with provenance per value).  The winding
    is not decoration: cores.winding() lays it out from the design
    current, the chosen current density and the skin depth, and this
    function draws what comes back - Litz bundles as circles of the
    computed bundle diameter at their real radius, foil at its computed
    thickness and width.  If the copper did not fit, it would be seen
    not to fit.

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
    gp = _C.gap(V, R['Ae'])
    d, tp = w['d_litz'], w['t_foil'] + _C.T_FOIL_INS
    NF = w['n_foil']                     # foils in parallel per turn
    NL = w['Ns'] * NF                    # foil layers per secondary winding
    COL = {'NP1': MAG, 'NS2': GRN, 'NS3': CYA}
    EDG = {'NP1': '#9c0055', 'NS2': '#2d7a4c', 'NS3': '#1f7fa6'}

    def fcol(k):
        return 'NS2' if k < NL else 'NS3'

    #  The figure is drawn 15 % smaller than the page column it fills, so
    #  everything on it - core, winding and lettering - prints 15 % larger
    #  (2026-09-22, user: the drawing and its text were too small).
    fig = plt.figure(figsize=(9.3 / 1.15, 5.9 / 1.15))
    S1, S2 = 17.2 * 1.15, 7.7 * 1.15         # mm per inch on the two scaled panels
    ax = _mm_ax(fig, [0.006, 0.033, 0.425, 0.934], 1.5, -3.0, S1)
    ax2 = _mm_ax(fig, [0.440, 0.500, 0.550, 0.470], 17.7, 2.0, S2)
    ax3 = fig.add_axes([0.440, 0.033, 0.550, 0.420])
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 5)
    ax3.axis('off')

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
    FH, WW = M['flange_h'] / 2.0, M['wind_w'] / 2.0
    RF = RW - 0.15
    bob = dict(fc=PLAS, ec='#55606c', lw=0.9, zorder=4)
    for sgn in (-1, 1):
        xt = RB if sgn > 0 else -RT
        ax.add_patch(Rectangle((xt, -FH), RT - RB, 2 * FH, **bob))
        for yy in (WW, -FH):
            xf = RT if sgn > 0 else -RF
            ax.add_patch(Rectangle((xf, yy), RF - RT, FH - WW, **bob))

    yP1 = WW - w['margin']
    yP0 = yP1 - w['w_pri']
    yS1 = yP0 - w['gap']
    yS0 = yS1 - w['w_foil']
    for y0, y1 in ((yP1, WW), (-WW, -WW + w['margin'])):
        for sgn in (-1, 1):
            x0 = RT if sgn > 0 else -RF
            ax.add_patch(Rectangle((x0, y0), RF - RT, y1 - y0, fc=TAPE,
                                   ec='#b9a25e', lw=0.6, zorder=5))
    for li, n in enumerate(w['rows_p']):
        r = RT + d * (li + 0.5)
        y0 = yP1 - d * 0.5 - (w['per_layer'] - n) * d * 0.5
        for k in range(n):
            for sgn in (-1, 1):
                ax.add_patch(Circle((sgn * r, y0 - k * d), d / 2.0,
                                    fc=COL['NP1'], ec=EDG['NP1'], lw=0.7,
                                    alpha=0.45, zorder=6))
    for k in range(2 * NL):
        c = COL[fcol(k)]
        for sgn in (-1, 1):
            x0 = RT + k * tp if sgn > 0 else -(RT + k * tp + w['t_foil'])
            ax.add_patch(Rectangle((x0, yS0), w['t_foil'], w['w_foil'],
                                   fc=c, ec=c, lw=0.4, zorder=6))
    for sgn in (-1, 1):
        x0 = RT if sgn > 0 else -RF
        ax.add_patch(Rectangle((x0, yS1), RF - RT, w['gap'], fc='none',
                               ec=GOLD, lw=1.1, ls=(0, (3.5, 2.5)), zorder=7))

    _dimh(ax, -HW, HW, -HH - 10.5, '%.1f' % M['W'], ext=-HH)
    _dimh(ax, -RC, RC, -HH - 3.2, 'ø%.1f' % M['d_centre'], ext=-WH,
          side=-1)
    _dimv(ax, -HH, HH, HW + 7.6, '%.1f' % M['H'], ext=HW)
    _dimv(ax, -WH, WH, HW + 2.4, '%.1f' % M['win_h'], ext=RW)
    ax.text(0.0, HH + 9.4, '%s in section' % NAME, ha='center', va='bottom',
            fontsize=10.5, color=NAVY, zorder=8)
    ax.text(0.0, -HH - 14.6, 'all dimensions in mm', ha='center', va='top',
            fontsize=8.5, color=GREY, zorder=8)
    #  balloons point into the LEFT window, so no leader crosses the part.
    #  Numbers are the rows of the legend table beside the figure.
    BX = -HW - 5.2
    hs = NL * tp                               # radial build of one winding
    _balloon(ax, 1, -(RT + d * 0.9), yP1 - d * 0.6, BX, yP1 - 0.8, EDG['NP1'])
    _balloon(ax, 2, -(RT + hs * 0.5), yS0 + w['w_foil'] * 0.30, BX,
             yS0 + w['w_foil'] * 0.30, EDG['NS2'])
    _balloon(ax, 3, -(RT + hs * 1.5), yS0 + w['w_foil'] * 0.70, BX,
             yS0 + w['w_foil'] * 0.70, EDG['NS3'])
    _balloon(ax, 4, -(RT + 2.6), yS1 + w['gap'] * 0.5, BX,
             yS1 + w['gap'] * 0.5, GOLD)
    _balloon(ax, 5, -(RT + 2.6), -WW + w['margin'] * 0.5, BX,
             -WW + w['margin'] * 0.5, GREY)
    _balloon(ax, 6, 0.0, gp / 2.0, 0.0, HH + 4.4, GOLD)
    _balloon(ax, 7, 10.5, WH - 2.2, 10.5, HH + 4.4, GREY)

    #  ============================== DETAIL, the winding unrolled
    OX, OY = 2.0, -3.6
    L = M['wind_w']
    fl = (M['flange_h'] - M['wind_w']) / 2.0
    BH = w['build_p'] + 1.1
    ax2.add_patch(Rectangle((OX - fl - 1.6, OY - 1.9), L + 2 * fl + 2.4, 1.9,
                            fc=FERR, ec=FERRE, lw=1.0, hatch='////', zorder=3))
    for x0 in (OX - fl, OX + L):
        ax2.add_patch(Rectangle((x0, OY), fl, BH, **bob))
    for x0 in (OX, OX + L - w['margin']):
        ax2.add_patch(Rectangle((x0, OY), w['margin'], BH, fc=TAPE,
                                ec='#b9a25e', lw=0.6, zorder=4))
    xP = OX + w['margin']
    for li, n in enumerate(w['rows_p']):
        y = OY + d * (li + 0.5)
        x0 = xP + d * 0.5 + (w['per_layer'] - n) * d * 0.5
        for k in range(n):
            ax2.add_patch(Circle((x0 + k * d, y), d / 2.0, fc=COL['NP1'],
                                 ec=EDG['NP1'], lw=0.7, alpha=0.45, zorder=6))
    xG = xP + w['w_pri']
    ax2.add_patch(Rectangle((xG, OY), w['gap'], BH, fc='none', ec=GOLD,
                            lw=1.1, ls=(0, (3.5, 2.5)), zorder=7))
    xS = xG + w['gap']
    for k in range(2 * NL):
        c = COL[fcol(k)]
        ax2.add_patch(Rectangle((xS, OY + k * tp), w['w_foil'], w['t_foil'],
                                fc=c, ec=c, lw=0.4, zorder=6))
    ax2.text(OX + L / 2.0, OY + BH + 5.4,
             'the winding unrolled along the bobbin', ha='center',
             va='bottom', fontsize=10.5, color=NAVY, zorder=8)
    _dimh(ax2, OX, OX + L, OY - 3.5, 'winding width  %.1f' % L,
          ext=OY - 1.9, side=-1)
    for x0, x1, t, c in ((xP, xG, '%.2f' % w['w_pri'], EDG['NP1']),
                         (xG, xS, '%.2f' % w['gap'], GOLD),
                         (xS, xS + w['w_foil'], '%.2f' % w['w_foil'],
                          EDG['NS2'])):
        _dimh(ax2, x0, x1, OY + BH + 1.1, t, color=c)
    for n, xb, c in ((1, (xP + xG) / 2, EDG['NP1']),
                     (4, (xG + xS) / 2, GOLD),
                     (2, xS + w['w_foil'] * 0.30, EDG['NS2']),
                     (3, xS + w['w_foil'] * 0.70, EDG['NS3'])):
        _balloon(ax2, n, 0, 0, xb, OY + BH + 3.1, c, r=0.62, lead=False)
    _balloon(ax2, 5, OX + w['margin'] * 0.5, OY + BH * 0.62,
             OX - 1.5, OY + BH + 3.1, GREY, r=0.62)
    #  which windings the foil layers are, read at the stack itself
    #  (the labels sit in the empty separation box, left of the stack)
    for nm, k0 in (('NS2', 0), ('NS3', NL)):
        yy = OY + (k0 + NL / 2.0) * tp
        ax2.annotate(nm, xy=(xS, yy), xytext=(xS - 0.9, yy), fontsize=8.3,
                     color=EDG[nm], ha='right', va='center', zorder=9,
                     arrowprops=dict(arrowstyle='-', color=EDG[nm], lw=0.6,
                                     shrinkA=1, shrinkB=1))

    #  ===================== SECONDARY, LAYER BY LAYER (not to scale)
    #  Twelve foil layers on the bobbin, grouped into the four turns:
    #  NS2 first, NS3 on top of it.  Each turn is NF foils wound
    #  together and connected in parallel at the pins.
    X0, X1 = 3.6, 5.5                       # foil, left and right edge
    HC, HI = 0.20, 0.07                     # copper and insulation, drawn
    Y0 = 0.70
    ax3.text(0.0, 4.72, 'the secondary, layer by layer  (not to scale)',
             ha='left', va='center', fontsize=10.5, color=NAVY, zorder=8)
    ax3.add_patch(Rectangle((X0 - 0.3, Y0 - 0.40), X1 - X0 + 0.6, 0.30,
                            fc=PLAS, ec='#55606c', lw=0.9, zorder=3))
    ax3.text((X0 + X1) / 2, Y0 - 0.25, 'bobbin', ha='center', va='center',
             fontsize=8.3, color='#55606c', zorder=6)
    for k in range(2 * NL):
        c = COL[fcol(k)]
        y = Y0 + k * (HC + HI)
        ax3.add_patch(Rectangle((X0, y), X1 - X0, HC, fc=c, ec=c, lw=0.4,
                                zorder=6))
        if k < 2 * NL - 1:
            ax3.add_patch(Rectangle((X0, y + HC), X1 - X0, HI, fc='#d9dde2',
                                    ec='#b6bcc4', lw=0.3, zorder=6))
    YT = Y0 + 2 * NL * (HC + HI) - HI          # top of the stack
    #  turn ticks, left of the stack
    for t in range(2 * w['Ns']):
        ya = Y0 + t * NF * (HC + HI)
        yb = ya + NF * (HC + HI) - HI
        nm = 'NS2' if t < w['Ns'] else 'NS3'
        ax3.plot([X0 - 0.15, X0 - 0.15], [ya, yb], color=EDG[nm], lw=1.0,
                 zorder=7)
        ax3.text(X0 - 0.25, (ya + yb) / 2, 'turn %d' % (t % w['Ns'] + 1),
                 ha='right', va='center', fontsize=8.3, color=EDG[nm],
                 zorder=8)
    #  winding brackets with the pins, further left
    for nm, k0 in (('NS2', 0), ('NS3', NL)):
        ya = Y0 + k0 * (HC + HI)
        yb = ya + NL * (HC + HI) - HI
        ax3.plot([X0 - 1.15, X0 - 1.15], [ya, yb], color=EDG[nm], lw=1.3,
                 zorder=7)
        for yy in (ya, yb):
            ax3.plot([X0 - 1.15, X0 - 1.0], [yy, yy], color=EDG[nm], lw=1.3,
                     zorder=7)
        ax3.text(X0 - 1.28, (ya + yb) / 2,
                 '%s  %d T\npins %s' % (nm, w['Ns'], _C.pins(nm, '–')),
                 ha='right', va='center', fontsize=8.3, color=EDG[nm],
                 zorder=8, linespacing=1.3)
    #  what one turn is, said once at the first turn
    ym = Y0 + (NF // 2) * (HC + HI) + HC / 2
    ax3.annotate('one turn = %d foils\n%.2f × %.1f mm, wound together,\n'
                 'connected in parallel' % (NF, w['t_foil'], w['w_foil']),
                 xy=(X1, ym), xytext=(X1 + 0.3, ym + 0.05),
                 fontsize=8.3, color=EDG['NS2'], ha='left', va='center',
                 zorder=9, linespacing=1.3,
                 arrowprops=dict(arrowstyle='-', color=EDG['NS2'], lw=0.6,
                                 shrinkA=1, shrinkB=1))
    yi = Y0 + (NL + 1) * (HC + HI) - HI / 2
    ax3.annotate('%.2f mm insulation between foils' % _C.T_FOIL_INS,
                 xy=(X1, yi), xytext=(X1 + 0.3, yi + 0.55), fontsize=8.3,
                 color=GREY, ha='left', va='center', zorder=9,
                 arrowprops=dict(arrowstyle='-', color=GREY, lw=0.6,
                                 shrinkA=1, shrinkB=1))
    ax3.text(X1 + 0.3, YT + 0.02, 'radial build %.1f mm' % w['build_s'],
             ha='left', va='center', fontsize=8.3, color=GREY, zorder=8)

    foot(fig, 'Drawn to scale from the TDK %s datasheets, core %s and coil '
              'former %s; the third panel is not to scale. The winding is '
              'laid out by cores.winding() at J = %.1f A/mm2, Litz fill '
              '%.2f, %.2f mm foil and %.1f mm margin tape.'
              % (NAME, M['core'], M['former'], _C.J_CU, _C.K_LITZ,
                 _C.T_FOIL, _C.MARGIN))
    save(fig, 'an_core_section')


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
    cap_(axl[3], 'own $\\Phi$ dashed, the sum solid, the gap shaded')

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
    cap_(axr[3], 'own $\\Phi$ dashed, the sum solid, the gap shaded')

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
               u'line-cycle rms at the HB edge: %.1f A \u2192 foil'
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
    c.text(Is / 2, 0.33, 'L at NP1 must\nstay above', ha='center',
           va='center', fontsize=9.4, color=MAG, zorder=4)
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
    Right: the coil former in the mounting-direction view of the TDK
    drawing, every pin at its drawn position, each ringed in the colour
    of the winding it carries.

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
    fig = plt.figure(figsize=(9.35, 6.3))

    # ---------------------------------------------------------- symbol
    ax = fig.add_axes([0.010, 0.060, 0.455, 0.860])
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
    S.dot(ax, 9.1, YT)
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
    S.label(ax, 12.6, YT, 'centre tap:\njoined on the PCB', size=9.6,
            color=NAVY, ha='left')
    S.label(ax, 0.45, 9.2, 'start', size=9.4, color=GREY, ha='right')
    S.label(ax, 0.45, 4.9, 'finish', size=9.4, color=GREY, ha='right')
    S.label(ax, 12.6, 9.2, 'start', size=9.4, color=GREY, ha='left')
    S.label(ax, 12.6, 1.0, 'finish', size=9.4, color=GREY, ha='left')
    S.label(ax, 7.2, 0.05, u'●  start of the winding (the dot end) '
            '= the first pins of the pair', size=9.6, color=GREY)

    # ---------------------------------------------------- coil former
    P = B['plan']
    bx = fig.add_axes([0.485, 0.060, 0.505, 0.860])
    hw, hh = P['w'] / 2.0, P['h'] / 2.0
    S.frame(bx, -hw - 13.0, hw + 13.0, -hh - 17.0, hh + 16.0)
    S.label(bx, 0.0, hh + 14.2, '%s COIL FORMER, VIEW IN MOUNTING DIRECTION'
            % B['former'], size=11.0, color=NAVY, weight='bold')
    bx.add_patch(Rectangle((-hw, -hh), P['w'], P['h'], fc='#f3f4f6',
                           ec=GREY, lw=1.2, zorder=1))
    if P['coil_w']:
        #  the coil between the flanges, seen edge-on from below
        bx.add_patch(Rectangle((-P['coil_w'] / 2.0, -P['coil_h'] / 2.0),
                               P['coil_w'], P['coil_h'], fc='#e4e7ec',
                               ec=GREY, lw=0.8, hatch='////', zorder=1.5))
        bx.text(0, 0, 'coil\n(between the flanges)', fontsize=9.4,
                color=GREY, ha='center', va='center', zorder=2,
                bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='none'))
    if P['mark']:
        mx, my = P['mark']
        bx.add_patch(Polygon([(mx, my), (mx - 2.6, my), (mx, my + 2.6)],
                             closed=True, fc=GREY, ec=GREY, zorder=2))
        bx.annotate('pin 1 marking', xy=(mx - 1.6, my + 0.7),
                    xytext=(-hw - 12.0, -hh - 4.6), fontsize=9.6,
                    color=GREY, ha='left',
                    arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.0),
                    zorder=9)
    by_pin = {}
    for w, (a, b) in C.PINMAP.items():
        for n in a + b:
            by_pin[n] = w
    #  pins run along rows (ETD) or columns (PQ): number them on the side
    #  away from the coil
    for n, (x, y) in C.PIN_XY.items():
        w = by_pin.get(n)
        c = COL[w] if w else '#9aa0a8'
        bx.add_patch(Circle((x, y), 1.85, fc='white', ec=c, lw=1.6,
                            zorder=3))
        bx.add_patch(Circle((x, y), 0.45, fc=c if w else GREY, ec='none',
                            zorder=4))
        if B['pins'] > 12:                              # rows top/bottom
            S.label(bx, x, y + (3.4 if y > 0 else -3.4), str(n), size=9.4,
                    color=c, weight='bold')
        else:
            S.label(bx, x + (3.0 if x < 0 else -3.0), y, str(n), size=9.6,
                    color=c, weight='bold',
                    ha='left' if x < 0 else 'right')
    #  winding name beside its group of pins
    def grp(w):
        a, b = C.PINMAP[w]
        xs = [C.PIN_XY[n][0] for n in a + b]
        ys = [C.PIN_XY[n][1] for n in a + b]
        x, y = sum(xs) / len(xs), sum(ys) / len(ys)
        if B['pins'] > 12:
            S.label(bx, x, (hh + 3.4) if y > 0 else -(hh + 3.4),
                    '%s   %s' % (w, C.pins(w)), size=9.6, color=COL[w],
                    weight='bold')
        else:
            S.label(bx, x + (-3.4 if x < 0 else 3.4), y,
                    '%s\n%s' % (w, C.pins(w)), size=10.0, color=COL[w],
                    weight='bold', ha='right' if x < 0 else 'left')
    for w in ('NP1', 'NAUX', 'NS2', 'NS3'):
        grp(w)
    if B['pins'] > 12:
        S.label(bx, -hw - 3.0, -20.32, 'primary\nside', size=9.4,
                color=NAVY, ha='right')
        S.label(bx, -hw - 3.0, 20.32, 'secondary\nside', size=9.4,
                color=NAVY, ha='right')
        #  the two datasheet numbers that place the pins
        bx.annotate('', xy=(C.PIN_XY[2][0], -hh - 8.0),
                    xytext=(C.PIN_XY[1][0], -hh - 8.0), zorder=1,
                    arrowprops=dict(arrowstyle='<->', color=GREY, lw=0.8,
                                    shrinkA=0, shrinkB=0))
        bx.text((C.PIN_XY[1][0] + C.PIN_XY[2][0]) / 2, -hh - 10.6,
                '%.2f' % B['pitch'], fontsize=9.4, color=GREY, ha='center',
                va='center', zorder=1)
        bx.annotate('', xy=(hw + 5.0, 20.32), xytext=(hw + 5.0, -20.32),
                    zorder=1,
                    arrowprops=dict(arrowstyle='<->', color=GREY, lw=0.8,
                                    shrinkA=0, shrinkB=0))
        bx.text(hw + 7.2, 0.0, '%.2f' % B['rows_apart'], fontsize=9.4,
                color=GREY, ha='center', va='center', rotation=90, zorder=1)
    S.label(bx, 0.0, -hh - 14.6, 'ring = winding on that pin;  grey pins are '
            'free', size=9.4, color=GREY)

    foot(fig, 'The transformer: the schematic symbol with its pin numbers, '
              'and the same pins on the %s coil former. Primary and '
              'auxiliary share one row, the two secondaries the other; the '
              'centre tap is pins %s, joined on the board.'
              % (B['former'], C.tap_text()))
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


FIGS = {'an_rac': an_rac, 'an_integrated': an_integrated,
        'an_pfc_cap': an_pfc_cap, 'an_pfc_boost': an_pfc_boost,
        'an_pfc_ccm': an_pfc_ccm, 'an_two_stage': an_two_stage,
        'an_llc_waves': an_llc_waves, 'an_three_cases': an_three_cases,
        'an_cap_ind': an_cap_ind, 'an_loadshift': an_loadshift,
        'an_peakgain': an_peakgain, 'an_recovery': an_recovery,
        'an_core_section': an_core_section,
        'an_loop_blocks': an_loop_blocks,
        'an_comp_opamp': an_comp_opamp, 'an_loop_example': an_loop_example,
        'an_flyback_llc': an_flyback_llc, 'an_mmf': an_mmf,
        'an_flux_steps': an_flux_steps, 'an_dc_overlap': an_dc_overlap,
        'an_xfmr_read': an_xfmr_read, 'an_xfmr_pins': an_xfmr_pins}
