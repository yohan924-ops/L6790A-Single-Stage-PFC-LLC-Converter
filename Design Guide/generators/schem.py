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
def cap(ax, x, y, t=None, horiz=True, s=0.30, color=NAVY, tdy=None):
    """capacitor: two plates.  -> (left, right) or (bottom, top)"""
    g, h = s * 0.30, s
    if horiz:
        for dx in (-g, g):
            ax.plot([x + dx, x + dx], [y - h / 2, y + h / 2], color=color,
                    lw=2.1, zorder=3)
        if t:
            label(ax, x, y + (tdy if tdy is not None else h * 0.85), t)
        return (x - s, y), (x + s, y)
    for dy in (-g, g):
        ax.plot([x - h / 2, x + h / 2], [y + dy, y + dy], color=color, lw=2.1,
                zorder=3)
    if t:
        label(ax, x + h * 0.95, y, t, ha='left')
    return (x, y - s), (x, y + s)


def ind(ax, x, y, t=None, horiz=True, s=0.66, n=4, color=NAVY, tdy=None):
    """inductor: n half-loops.  -> (left, right) or (bottom, top)"""
    r = s / (2.0 * n)
    a = np.linspace(np.pi, 0, 40)
    for k in range(n):
        c = x - s / 2 + r * (2 * k + 1) if horiz else x
        if horiz:
            ax.plot(c + r * np.cos(a), y + r * np.sin(a), color=color, lw=2.0,
                    zorder=3)
        else:
            cy = y - s / 2 + r * (2 * k + 1)
            ax.plot(x + r * np.sin(a), cy + r * np.cos(a), color=color,
                    lw=2.0, zorder=3)
    if t:
        if horiz:
            label(ax, x, y + (tdy if tdy is not None else r + 0.20), t)
        else:
            label(ax, x + r + 0.16, y, t, ha='left')
    return ((x - s / 2, y), (x + s / 2, y)) if horiz else \
           ((x, y - s / 2), (x, y + s / 2))


def res(ax, x, y, t=None, horiz=True, s=0.70, color=NAVY, tdy=None):
    """resistor: a box.  -> (left, right) or (bottom, top)"""
    w, h = (s, s * 0.42) if horiz else (s * 0.42, s)
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc='white',
                           ec=color, lw=1.8, zorder=3))
    if t:
        if horiz:
            label(ax, x, y + (tdy if tdy is not None else h * 0.5 + 0.20), t)
        else:
            label(ax, x + w * 0.5 + 0.16, y, t, ha='left')
    return ((x - w / 2, y), (x + w / 2, y)) if horiz else \
           ((x, y - h / 2), (x, y + h / 2))


def sw(ax, x, y, t, on=False, w=0.62, h=0.52):
    """a switch drawn as a labelled box"""
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h,
                           fc=(YEL if on else 'white'),
                           ec=(MAG if on else GREY), lw=(2.2 if on else 1.4),
                           zorder=3))
    label(ax, x, y, t, size=9.5, weight='bold', z=4)
    return (x, y - h / 2), (x, y + h / 2)


def diode(ax, x, y, t=None, horiz=True, s=0.30, flip=False, color=NAVY):
    """triangle + bar.  -> (in, out) along the conduction direction"""
    d = -1 if flip else 1
    if horiz:
        tri = [(x - d * s, y - s * 0.62), (x - d * s, y + s * 0.62), (x, y)]
        ax.fill(*zip(*tri), color=color, zorder=3)
        ax.plot([x, x], [y - s * 0.62, y + s * 0.62], color=color, lw=2.2,
                zorder=3)
        if t:
            label(ax, x, y + s * 1.1, t)
        return (x - d * s, y), (x + d * s, y)
    tri = [(x - s * 0.62, y - d * s), (x + s * 0.62, y - d * s), (x, y)]
    ax.fill(*zip(*tri), color=color, zorder=3)
    ax.plot([x - s * 0.62, x + s * 0.62], [y, y], color=color, lw=2.2, zorder=3)
    if t:
        label(ax, x + s * 0.95, y, t, ha='left')
    return (x, y - d * s), (x, y + d * s)


def acsrc(ax, x, y, t=None, r=0.36, color=NAVY):
    """a circle with a sine in it -> (left, right)"""
    a = np.linspace(0, 2 * np.pi, 120)
    ax.plot(x + r * np.cos(a), y + r * np.sin(a), color=color, lw=1.7, zorder=3)
    u = np.linspace(-1, 1, 60)
    ax.plot(x + u * r * 0.62, y + 0.42 * r * np.sin(np.pi * u), color=color,
            lw=1.7, zorder=4)
    if t:
        label(ax, x, y - r - 0.24, t)
    return (x - r, y), (x + r, y)


def sqsrc(ax, x, y, t=None, r=0.38, color=NAVY):
    """a circle with a square wave in it -> (left, right)"""
    a = np.linspace(0, 2 * np.pi, 120)
    ax.plot(x + r * np.cos(a), y + r * np.sin(a), color=color, lw=1.7, zorder=3)
    q = r * 0.55
    ax.plot([x - q, x - q, x, x, x + q, x + q],
            [y - q * 0.6, y + q * 0.6, y + q * 0.6, y - q * 0.6,
             y - q * 0.6, y + q * 0.6], color=color, lw=1.7, zorder=4)
    if t:
        label(ax, x, y - r - 0.24, t)
    return (x - r, y), (x + r, y)


def xfmr(ax, x, y, hp=1.15, hs=1.15, gap=0.30, lp=None, ls=None, dots=True):
    """two windings and a core.

    -> dict with p_top p_bot s_top s_bot, all terminal points
    """
    xl, xr = x - gap, x + gap
    for xx in (x - 0.09, x + 0.09):
        ax.plot([xx, xx], [y - max(hp, hs) / 2 - 0.10,
                           y + max(hp, hs) / 2 + 0.10],
                color=GREY, lw=2.0, zorder=2)
    _coil(ax, xl, y, hp, side=-1)
    _coil(ax, xr, y, hs, side=+1)
    if dots:
        dot(ax, xl - 0.20, y + hp / 2 - 0.10, NAVY, 4.4)
        dot(ax, xr + 0.20, y + hs / 2 - 0.10, NAVY, 4.4)
    if lp:
        label(ax, xl - 0.34, y, lp, ha='right')
    if ls:
        label(ax, xr + 0.34, y, ls, ha='left')
    return dict(p_top=(xl, y + hp / 2), p_bot=(xl, y - hp / 2),
                s_top=(xr, y + hs / 2), s_bot=(xr, y - hs / 2))


def _coil(ax, x, y, h, side, n=4):
    r = h / (2.0 * n)
    a = np.linspace(-np.pi / 2, np.pi / 2, 40)
    for k in range(n):
        cy = y - h / 2 + r * (2 * k + 1)
        ax.plot(x + side * r * np.cos(a), cy + r * np.sin(a), color=NAVY,
                lw=2.0, zorder=3)


def gnd(ax, x, y, s=0.22, color=NAVY):
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


def shunt(ax, x, ytop, ybot, kind, t=None, frac=0.55, tdx=0.34, **kw):
    """A component hanging between two nodes, wired to both.

    Placing a vertical symbol centred ON the node - which is the obvious
    thing to write - puts the wire in the middle of the coil and the junction
    dot inside the resistor box.  This sizes the symbol to a fraction of the
    span and wires the leftovers.
    """
    fn = {'ind': ind, 'cap': cap, 'res': res}[kind]
    span = ytop - ybot
    s = span * frac
    yc = ybot + span / 2.0
    (b, tp) = fn(ax, x, yc, None, horiz=False, s=s, **kw)
    wire(ax, [(x, ytop), tp])
    wire(ax, [b, (x, ybot)])
    if t:
        label(ax, x + tdx, yc, t, ha='left')
    return (x, ytop), (x, ybot)
