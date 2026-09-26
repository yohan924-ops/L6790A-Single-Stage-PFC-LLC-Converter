# -*- coding: utf-8 -*-
"""Schematic primitives for the figures.

The application note is distributed, so the circuit drawings in it have to be
ours. Reference application notes from other vendors are excellent teaching
material and are cited, but their figures are not redrawn here and not lifted
into the document.

Everything is drawn in axis units on a plain axes with no ticks. Call
`frame(ax, x0, x1, y0, y1)` first; every symbol returns the two terminal
points so a chain can be wired without arithmetic in the caller.
"""
import numpy as np
from matplotlib.patches import Rectangle, FancyArrowPatch

#  The symbols themselves come from schemx, which is the kit the eight-mode
#  panels established and the reader has already been shown.  This module
#  keeps only the composition helpers - frames, shading, block chains.
import schemx as X
from schemx import hop, coil, hcoil, mosfet, path, register   # noqa: F401

NAVY, YEL, MAG = '#03234B', '#FFD200', '#E6007E'
CYA, GRN, PUR = '#3CB4E6', '#49B170', '#8C0078'
GREY, LT = '#464650', '#E8E8E9'

LW = 1.5


def frame(ax, x0, x1, y0, y1, title=None):
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    if title:
        ax.set_title(title, fontsize=11.5, color=NAVY, pad=6)


def wire(ax, pts, color=NAVY, lw=LW, z=2, **kw):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, zorder=z, solid_capstyle='round', **kw)
    return pts[-1]


def dot(ax, x, y, color=NAVY, ms=5.2, z=5):
    ax.plot([x], [y], 'o', color=color, ms=ms, zorder=z)


def label(ax, x, y, t, size=10, color=NAVY, ha='center', va='center',
          weight='normal', z=6):
    ax.text(x, y, t, ha=ha, va=va, fontsize=size, color=color,
            fontweight=weight, zorder=z)


# --------------------------------------------------------------- components
def cap(ax, x, y, t=None, horiz=True, s=None, color=NAVY, tdy=None):
    """A capacitor, drawn by the kit.  -> (left, right) or (bottom, top)

    `s` is the plate half-length.  Left out it comes from the axes' scale,
    so the same capacitor is the same size on paper in every figure.  The
    old version derived the plate from whatever length the caller happened
    to pass, and shunt() passed a fraction of the branch - so the plates
    grew with the branch and no two matched.
    """
    s = 0.30 * X.scale(ax) if s is None else s
    g = s * (0.11 / 0.30)
    #  The terminals are the PLATES, at +-g along the run - not +-s, which
    #  is the plate half-LENGTH, across it.  Returned as +-s, every
    #  capacitor wired through this function stopped short of its plates
    #  by s - g, a gap figcheck's open-end test was the first to notice.
    if horiz:
        X.hcap(ax, x, y, s=s, gap=g, color=color)
        if t:
            label(ax, x, y + (tdy if tdy is not None else s * 1.35), t)
        return (x - g, y), (x + g, y)
    X.vcap(ax, x, y, s=s, gap=g, color=color)
    if t:
        label(ax, x + s * 1.45, y, t, ha='left')
    return (x, y - g), (x, y + g)


def ind(ax, x, y, t=None, horiz=True, s=0.66, n=None, color=NAVY, tdy=None):
    """An inductor.  -> (left, right) or (bottom, top)

    The TURN SIZE is fixed and the number of turns fills the length, which
    is the way a real winding works and the way the mode panels draw one.
    Fixing n instead made a long inductor's turns three times the size of a
    short one's in the same document.
    """
    r = X.TURN_R * X.scale(ax)
    #  Capped at four bumps.  Uncapped, a long inductor came out as a
    #  spring of ten turns and the symbol swamped the wire it was in; the
    #  extra length is drawn as lead, which is what it is.
    n = min(4, max(2, int(round(s / (2.0 * r))))) if n is None else n
    w = min(s, 2.0 * r * n)
    #  A lead shorter than a couple of percent of the symbol is a wire
    #  whose two ends land on the same pixel, and the wiring check then
    #  counts three arms at one point and asks for a junction dot that
    #  means nothing.  Below that, the coil's own ends ARE the terminals.
    #
    #  Measured against the TURN RADIUS, not against s.  A fraction of s
    #  scales with the inductor and the pixel does not: raising the turn
    #  radius by half left a 0.042 lead on a 1.35 inductor, which is four
    #  hundredths of s - over the old threshold - and one pixel on paper.
    #  Half a turn radius is the shortest lead that is visibly a lead.
    if (s - w) / 2.0 < 0.5 * r:
        w = s
    if horiz:
        X.hcoil(ax, x, y, s=w, n=n, color=color)
        if w < s - 1e-9:
            wire(ax, [(x - s / 2, y), (x - w / 2, y)], color=color)
            wire(ax, [(x + w / 2, y), (x + s / 2, y)], color=color)
        if t:
            label(ax, x, y + (tdy if tdy is not None else w / (2.0 * n)
                              + 0.20), t)
        return (x - s / 2, y), (x + s / 2, y)
    X.coil(ax, x, y - w / 2, y + w / 2, n=n, side=+1, color=color)
    if w < s - 1e-9:
        wire(ax, [(x, y - s / 2), (x, y - w / 2)], color=color)
        wire(ax, [(x, y + w / 2), (x, y + s / 2)], color=color)
    if t:
        label(ax, x + w / (2.0 * n) + 0.16, y, t, ha='left')
    return (x, y - s / 2), (x, y + s / 2)


def res(ax, x, y, t=None, horiz=True, s=None, color=NAVY, tdy=None):
    """A resistor as a box, at the kit's size.  -> two terminals"""
    k = X.scale(ax)
    long_, short = (1.15 * k, 0.46 * k)
    w, h = (long_, short) if horiz else (short, long_)
    X.resbox(ax, x, y, w=w, h=h, color=color)
    if t:
        if horiz:
            label(ax, x, y + (tdy if tdy is not None else h * 0.5 + 0.20), t)
        else:
            label(ax, x + w * 0.5 + 0.16, y, t, ha='left')
    return ((x - w / 2, y), (x + w / 2, y)) if horiz else \
           ((x, y - h / 2), (x, y + h / 2))


def sw(ax, x, y, t, on=False, w=0.62, h=1.30, gate=0.56, side='gate'):
    """A switch: the MOSFET symbol, not a box with a name in it.

    The box was the first thing a reviewer rejected, and rightly - a block
    diagram may use boxes but a schematic may not.  `w` is accepted and
    ignored so the older call sites still read; the span that matters is h,
    drain node to source node.
    """
    X.mosfet(ax, x, y, t, 'on' if on else 'plain', h=h, gate=gate,
             body=False, coss=False,
             name_at='right' if side == 'right' else 'gate', size=10)
    return (x, y - h / 2), (x, y + h / 2)


def diode(ax, x, y, t=None, horiz=True, s=None, flip=False, color=NAVY):
    """triangle + bar, centred on (x, y).  -> (in, out) along conduction

    Same proportions as the kit's vdiode: the triangle runs from -0.62 s
    to +0.62 s along the branch and the bar stands at its tip, so the two
    terminals are the triangle's base and the bar.  The first version put
    the base at x - s and the bar at x and then returned x + s as the far
    terminal, which left every wire on that side hanging s short of the
    bar - visible once figcheck read the wires back.  `s` defaults to the
    kit's size at this axes' scale.
    """
    #  0.56: doubled 2026-09-21 with the kit's vdiode - see there
    s = 0.56 * X.scale(ax) if s is None else s
    d = -1 if flip else 1
    a, w = 0.62 * s, 0.72 * s                     # half-length, half-width
    if horiz:
        tri = [(x - d * a, y - w), (x - d * a, y + w), (x + d * a, y)]
        ax.fill(*zip(*tri), color=color, zorder=3)
        ax.plot([x + d * a] * 2, [y - w, y + w], color=color, lw=2.2,
                zorder=3)
        if t:
            label(ax, x, y + w + 0.26 * X.scale(ax) + 0.12, t)
        return (x - d * a, y), (x + d * a, y)
    tri = [(x - w, y - d * a), (x + w, y - d * a), (x, y + d * a)]
    ax.fill(*zip(*tri), color=color, zorder=3)
    ax.plot([x - w, x + w], [y + d * a] * 2, color=color, lw=2.2, zorder=3)
    if t:
        label(ax, x + w + 0.16, y, t, ha='left')
    return (x, y - d * a), (x, y + d * a)


def acsrc(ax, x, y, t=None, r=0.36, color=NAVY, tdy=None):
    """a circle with a sine in it -> (left, right)"""
    a = np.linspace(0, 2 * np.pi, 120)
    ax.plot(x + r * np.cos(a), y + r * np.sin(a), color=color, lw=1.7, zorder=3)
    u = np.linspace(-1, 1, 60)
    ax.plot(x + u * r * 0.62, y + 0.42 * r * np.sin(np.pi * u), color=color,
            lw=1.7, zorder=4)
    if t:
        #  Below by default, but a source that is wired out of its BOTTOM
        #  puts its own return wire through that label - which is where
        #  the three source names in the FHA figure were sitting.
        label(ax, x, y + (tdy if tdy is not None else -(r + 0.24)), t)
    return (x - r, y), (x + r, y)


def sqsrc(ax, x, y, t=None, r=0.38, color=NAVY, tdy=None):
    """a circle with a square wave in it -> (left, right)"""
    a = np.linspace(0, 2 * np.pi, 120)
    ax.plot(x + r * np.cos(a), y + r * np.sin(a), color=color, lw=1.7, zorder=3)
    q = r * 0.55
    ax.plot([x - q, x - q, x, x, x + q, x + q],
            [y - q * 0.6, y + q * 0.6, y + q * 0.6, y - q * 0.6,
             y - q * 0.6, y + q * 0.6], color=color, lw=1.7, zorder=4)
    if t:
        label(ax, x, y + (tdy if tdy is not None else -(r + 0.24)), t)
    return (x - r, y), (x + r, y)


def xfmr(ax, x, y, hp=1.15, hs=1.15, gap=0.30, lp=None, ls=None, dots=True,
         ct=False, np_t=None, ns_t=None, s_dot='top', tap_dot=True):
    """Two windings and a core; the kit draws it.  -> dict of terminals."""
    return X.xfmr(ax, x, y, hp=hp, hs=hs, np_t=np_t, ns_t=ns_t, ct=ct,
                  gap=gap, lp=lp, ls=ls, dots=dots, size=10, s_dot=s_dot,
                  tap_dot=tap_dot)


def _coil(ax, x, y, h, side, n=4):
    """One winding, drawn by the kit so it matches the mode panels."""
    X.coil(ax, x, y - h / 2, y + h / 2, n=n, side=side)


def gnd(ax, x, y, s=None, color=NAVY, lead=0.0):
    """Ground.  (x, y) is the point it CONNECTS to, not the first bar.

    With lead 0 the widest bar lands on that point, so a ground hung on a
    rail is drawn straight across the rail and reads as a blob on the
    wire.  Give it a lead and the bars stand clear.  The lead is drawn at
    the symbol's own zorder, so the wiring check reads it as part of the
    symbol rather than as a wire ending at nothing.
    """
    #  Sized like every other symbol, so a ground is the same size on
    #  paper wherever it is drawn - it was the one symbol still fixed in
    #  data units, and in a wide panel it came out as three short ticks.
    s = 0.22 * X.scale(ax) if s is None else s
    if lead:
        ax.plot([x, x], [y, y - lead], color=color, lw=1.8, zorder=3)
    y -= lead
    for k, w in enumerate((1.0, 0.62, 0.28)):
        ax.plot([x - s * w, x + s * w], [y - k * s * 0.34] * 2, color=color,
                lw=1.8, zorder=3)


def box(ax, x, y, w, h, t, fc=LT, ec=GREY, size=10.5, weight='normal', z=3):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=fc, ec=ec, lw=1.4,
                           zorder=z))
    label(ax, x, y, t, size=size, weight=weight, z=z + 1)
    return (x - w / 2, y), (x + w / 2, y)


def shade(ax, x0, y0, x1, y1, t=None, color=CYA, alpha=0.13, tdy=0.18):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=color, alpha=alpha,
                           ec=color, lw=1.2, ls=(0, (5, 3)), zorder=1))
    if t:
        label(ax, (x0 + x1) / 2, y1 + tdy, t, size=10.5, color=color,
              weight='bold')


def arrow(ax, p0, p1, t=None, color=MAG, lw=2.0, size=11, dy=0.22):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>',
                                 mutation_scale=15, color=color, lw=lw,
                                 zorder=6, shrinkA=0, shrinkB=0))
    if t:
        label(ax, (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + dy, t,
              color=color, size=size, weight='bold')


def shunt(ax, x, ytop, ybot, kind, t=None, frac=None, tdx=None, **kw):
    """A component hanging between two nodes, wired to both.

    Placing a vertical symbol centred ON the node - the obvious thing to
    write - puts the wire in the middle of the coil and the junction dot
    inside the resistor box.  This places the symbol and wires the
    leftovers.

    It used to size the symbol to `frac` of the span, which is why the same
    capacitor came out half again as large in a figure whose output rail
    happened to sit further from its return.  The symbol is now a fixed
    physical size; `frac` is kept only for the inductor, whose LENGTH is a
    real choice, and is ignored for the other two.
    """
    span = abs(ytop - ybot)
    yc = min(ytop, ybot) + span / 2.0
    if kind == 'ind':
        out = ind(ax, x, yc, None, horiz=False,
                  s=span * (0.55 if frac is None else frac), **kw)
    elif kind == 'cap':
        out = cap(ax, x, yc, None, horiz=False, **kw)
    else:
        out = res(ax, x, yc, None, horiz=False, **kw)
    b, tp = out
    #  The leftover wire carries the SYMBOL's colour.  Left at the default
    #  it came out navy on a branch drawn in another colour, and the two
    #  halves of one net then read as two nets.
    lc = kw.get('color', NAVY)
    wire(ax, [(x, ytop), tp if ytop > ybot else b], color=lc)
    wire(ax, [b if ytop > ybot else tp, (x, ybot)], color=lc)
    if t:
        #  clear of the symbol that was actually drawn, not a fixed guess:
        #  the symbols shrank when they became physically sized and the old
        #  0.34 put every label on top of its own component.
        half = 0.30 * X.scale(ax)
        for rec in getattr(ax, '_syms', [])[-1:]:
            half = rec[3] / 2.0
        dx = (half + 0.34 * X.scale(ax)) if tdx is None else tdx
        label(ax, x + dx, yc, t, ha='left')
    return (x, ytop), (x, ybot)
