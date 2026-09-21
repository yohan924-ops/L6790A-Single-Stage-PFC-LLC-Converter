# -*- coding: utf-8 -*-
"""The drawing kit the eight-mode panels established.

`schem.py` came first and drew a switch as a labelled box.  When the mode
panels were reviewed the verdict was that a box is not a MOSFET, that the
windings were frayed, and that a current arrow has to land somewhere a
reader can see it - so those panels grew their own symbols.  They were
accepted; this module is where they live so that every figure in the note
can use them instead of each drawing keeping a private copy.

What it settles, and why each one was settled that way:

  * the MOSFET is enhancement mode, so the channel is three separate bars.
    Drawn as one bar it is a depletion device and says the wrong thing.
  * a winding is a stack of half circles with a BREAK between turns.  Butted
    together they meet at a cusp, and a cusp with a line join is a hook at
    every turn - that is what made the first drawings look frayed.
  * the current highlight goes UNDER the schematic, not over it.  On top, a
    wide band swallows the chord of every coil and strikes out the labels.
  * an arrowhead is placed per head as (segment, fraction), because a fixed
    fraction lands on whatever happens to be at that fraction - in the mode
    panels, a wire hop and the inside of a MOSFET.

`schem.py` keeps the composition helpers (frame, shade, arrow, chains) and
now takes its windings and its switch symbol from here, so there is one of
each in the project.
"""
import numpy as np
import matplotlib.pyplot as plt                                  # noqa: F401
import matplotlib.patheffects as pe
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch

#  The ST palette, the same one the rest of the note uses.
NAVY, YEL, MAG = '#03234B', '#FFD200', '#E6007E'
CYA, GRN, PUR = '#3CB4E6', '#49B170', '#8C0078'
GREY, LT = '#464650', '#E8E8E9'
OFF_C = '#C2C5CC'         # a device or branch that is carrying nothing
LW = 1.6


# --------------------------------------------------------------- primitives
def wire(ax, pts, color=NAVY, lw=LW, z=2, **kw):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, zorder=z, solid_capstyle='round', **kw)


def dot(ax, x, y, color=NAVY, ms=5.0, z=6):
    ax.plot([x], [y], 'o', color=color, ms=ms, zorder=z)


def nodot(ax, x, y):
    """Declare a junction that this drawing leaves undotted on purpose.

    Three conductors meeting want a dot, so the wiring check asks for
    one.  When a drawing has a reason to leave it out, the reason has to
    be recorded HERE rather than by loosening the check - otherwise the
    next real missing dot is lost in the same silence.  figcheck lists
    these and does not count them, the way it lists rail stubs.
    """
    ax._nodots = getattr(ax, '_nodots', []) + [(x, y)]


def txt(ax, x, y, t, size=10.5, color=NAVY, ha='center', va='center',
        weight='normal', z=8, halo=False):
    ax.text(x, y, t, ha=ha, va=va, fontsize=size, color=color,
            fontweight=weight, zorder=z,
            path_effects=[pe.withStroke(linewidth=3.4, foreground='white')]
            if halo else None)


#  ---------------------------------------------------------- symbol sizing
#  A component symbol has to come out the SAME PHYSICAL SIZE in every
#  figure.  Sized in data units it shrinks in a dense drawing and grows in
#  a sparse one; sized as a fraction of the branch it hangs on - which is
#  what the old shunt() did - the same capacitor came out 0.73 units long
#  in one figure and 1.38 in another, and that is what "the output cap
#  symbol is far too big" meant the first time it was said.
#
#  REF_UPI is the data-units-per-inch of the eight-mode panels, the scale
#  the symbols below were reviewed at.  `scale(ax)` returns the factor that
#  reproduces that physical size in any other axes, and `_ax()` in the
#  figure modules records each axes' own units-per-inch for it to read.
#  The mode panels' x span - the drawing the symbols were reviewed on.
REF_SPAN = 22.45
#  The mode sheets put 22.45 units across 0.491 of the figure: 45.7 units per
#  figure width.  Rounded UP so the floor never quite reaches them.
REF_FIGSPAN = 46.0
#  Turn radii, at the mode panels' scale.  A transformer winding is drawn
#  with bigger turns than a filter inductor - that is ordinary practice -
#  but the ratio between them is fixed here instead of falling out of
#  whatever height and turn count each drawing happened to pass, which is
#  how one figure ended up with windings five times another's.
#  One half circle of a winding, as a radius.  Raised by half in
#  2026-09-21: at 0.14 and 0.28 a turn printed about a point across
#  on A4 and the coils read as a ripple in the wire rather than as
#  windings.  Turn COUNT falls to suit, which is the intended trade -
#  a schematic winding is a few legible bumps, not a spring.
TURN_R, WIND_R = 0.21, 0.42


def scale(ax):
    """The size factor for every symbol drawn on this axes.

    Two rules, and the larger wins:

      own    the drawing's own width, against the mode panels' (REF_SPAN).
             A schematic that is bigger on the page gets bigger symbols.
      floor  the FIGURE width, in this axes' data units, against the mode
             sheets' (REF_FIGSPAN).  A symbol is never smaller on paper
             than it is on the mode panels - which is what happened to a
             three-panel figure whose panels were each a third of the page:
             sized by their own width the capacitors came out at 60 % of
             the mode panels' and the wires swallowed them.

    The floor reads the axes' nominal position, so a figure that lays out
    with subplots_adjust BEFORE it draws gets the floor it asked for.  The
    mode sheets fall a hair under 1.0 on the floor and exactly 1.0 on their
    own width, so they are governed by the first rule and do not move.
    """
    x0, x1 = ax.get_xlim()
    span = abs(x1 - x0)
    if span < 1e-9:
        return 1.0
    own = span / REF_SPAN
    try:
        w = ax.get_position().width
        floor = (span / w) / REF_FIGSPAN if w > 1e-6 else 0.0
    except Exception:                                    # noqa: BLE001
        floor = 0.0
    return max(own, floor)


def note_symbol(ax, kind, x, y, w, h):
    """Record a drawn symbol so figcheck can measure it: what, where, its
    size, and the scale it was drawn at - dividing the last out is what
    makes symbols in different figures comparable."""
    if not hasattr(ax, '_syms'):
        ax._syms = []
    ax._syms.append((kind, x, y, w, h, scale(ax)))


def _cap_size(ax, s, gap):
    if s is None:
        s = 0.30 * scale(ax)
        return s, (s * (0.11 / 0.30) if gap is None else gap)
    return s, (0.11 if gap is None else gap)


def vcap(ax, x, y, s=None, gap=None, color=NAVY, lw=2.2, z=4):
    """A capacitor across a vertical branch: two horizontal plates.

    s is the plate half-length and gap the half-separation.  Left out, both
    come from the axes' own scale so the symbol is the same size on paper
    as it is on the mode panels.
    """
    #  An explicit s keeps the historical gap: the mode panels pass their
    #  own sizes and must not move.
    s, gap = _cap_size(ax, s, gap)
    for dy in (gap, -gap):
        ax.plot([x - s, x + s], [y + dy] * 2, color=color, lw=lw, zorder=z)
    note_symbol(ax, 'cap', x, y, 2 * s, 2 * gap)


def hcap(ax, x, y, s=None, gap=None, color=NAVY, lw=2.2, z=4):
    """A capacitor in a horizontal run: two vertical plates."""
    s, gap = _cap_size(ax, s, gap)
    for dx in (gap, -gap):
        ax.plot([x + dx] * 2, [y - s, y + s], color=color, lw=lw, zorder=z)
    note_symbol(ax, 'cap', x, y, 2 * gap, 2 * s)


#  A winding is a stack of half circles whose diameters lie on the lead
#  line.  Two of them meet tangent-to-tangent pointing opposite ways, which
#  is a cusp, and a cusp rendered with a join turns into a little hook at
#  every turn - the thing that made these look frayed.  So the arcs are
#  separated by a break: one plot call, no joins, and the round caps close
#  the seam.  The highlight uses the same points and gets the same breaks.
BRK = (np.nan, np.nan)


def coil_pts(x, y0, y1, n=5, side=-1, m=26):
    """A vertical winding, bottom to top, with a break between turns."""
    r = abs(y1 - y0) / (2.0 * n)
    lo = min(y0, y1)
    a = np.linspace(-np.pi / 2, np.pi / 2, m)
    pts = []
    for k in range(n):
        cy = lo + r * (2 * k + 1)
        if pts:
            pts.append(BRK)
        pts += list(zip(x + side * r * np.cos(a), cy + r * np.sin(a)))
    return pts


def hcoil_pts(x, y, s=0.90, n=4, m=26):
    """A horizontal winding, left to right, with a break between turns."""
    r = s / (2.0 * n)
    a = np.linspace(np.pi, 0, m)
    pts = []
    for k in range(n):
        cx = x - s / 2 + r * (2 * k + 1)
        if pts:
            pts.append(BRK)
        pts += list(zip(cx + r * np.cos(a), y + r * np.sin(a)))
    return pts


def coil(ax, x, y0, y1, n=5, side=-1, color=NAVY, lw=2.0, z=4):
    r = abs(y1 - y0) / (2.0 * max(n, 1))
    note_symbol(ax, 'turn', x, (y0 + y1) / 2.0, 2 * r, 2 * r)
    xs, ys = zip(*coil_pts(x, y0, y1, n, side))
    ax.plot(xs, ys, color=color, lw=lw, zorder=z, solid_capstyle='round')


def hcoil(ax, x, y, s=0.90, n=4, color=NAVY, lw=2.0, z=4):
    r = s / (2.0 * max(n, 1))
    note_symbol(ax, 'turn', x, y, 2 * r, 2 * r)
    xs, ys = zip(*hcoil_pts(x, y, s, n))
    ax.plot(xs, ys, color=color, lw=lw, zorder=z, solid_capstyle='round')


def vdiode(ax, x, y, s=0.26, up=True, color=NAVY, lw=2.2, z=4):
    """Triangle and bar on a vertical branch; `up` = conducts upward."""
    d = 1 if up else -1
    tri = [(x - s * 0.72, y - d * s * 0.62), (x + s * 0.72, y - d * s * 0.62),
           (x, y + d * s * 0.62)]
    ax.fill(*zip(*tri), color=color, zorder=z)
    ax.plot([x - s * 0.72, x + s * 0.72], [y + d * s * 0.62] * 2, color=color,
            lw=lw, zorder=z)


def resbox(ax, x, y, w=0.46, h=1.15, color=NAVY, z=4):
    """A resistor as a box.

    The defaults stay literal: the mode panels call this with none, and a
    size derived from their own scale would come out 1.03x and move them.
    `schem.res` passes the scaled size for every other figure.
    """
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc='white', ec=color,
                           lw=1.8, zorder=z))
    note_symbol(ax, 'res', x, y, w, h)


def hop(ax, x, y, r=0.20, color=NAVY, lw=LW, z=5):
    """A horizontal wire crossing a vertical one without joining it."""
    a = np.linspace(0, np.pi, 40)
    ax.plot(x + r * np.cos(a), y + r * np.sin(a), color=color, lw=lw, zorder=z)


def mosfet(ax, x, y, name, state='on', h=1.80, gate=1.00,
           dx_d=0.80, dx_c=1.50, halo=True, body=True, coss=True,
           name_at='gate', size=11.5):
    """One switch: the MOSFET, its body diode and its C_oss, in parallel.

    Enhancement mode, so the channel is THREE separate bars with gaps you
    can see, each with its own lead - drain to the top bar, source to the
    bottom one, bulk to the middle one.  Drawn tight the first time, the
    three merged into one column and the symbol read as a depletion device.
    The gate is a plate standing off the channel across the oxide gap and
    touching nothing.

    state picks which of the three parallel paths is doing the work -
        on          gated on and carrying          (channel)
        diode       gated off, body diode carrying (the ZVS window)
        charge      gated off, C_oss charging,   V_ds rising
        discharge   gated off, C_oss discharging, V_ds falling
        off         nothing
    """
    #  Every dimension inside the symbol is a fraction of the
    #  drain-to-source span, so one call serves a full-page panel and a
    #  switch in a block diagram.  u = 1 is the size the mode panels
    #  were reviewed at, and those numbers are the ones written below.
    u = h / 1.80
    yt, yb = y + h / 2, y - h / 2
    #  'plain' is a switch in a figure that is not about switching states -
    #  drawn in full ink, with no halo, because greying it would say it was
    #  off and that figure is not making that claim.
    live = state == 'on'
    cm = NAVY if state in ('on', 'plain') else OFF_C
    cd = GRN if state == 'diode' else OFF_C
    cc = {'charge': MAG, 'discharge': CYA}.get(state, OFF_C)

    if live and halo:                          # a soft halo, not a filled box
        ax.add_patch(FancyBboxPatch(
            (x - 1.02 * u, yb), 1.16 * u, h,
            boxstyle='round,pad=0.10,rounding_size=0.16', fc=YEL, alpha=0.40,
            ec='none', zorder=1))

    xg, xc = x - 0.62 * u, x - 0.38 * u
    wire(ax, [(x - gate, y), (xg, y)], cm, 1.5, gid='symbol')   # gate lead
    ax.plot([xg, xg], [y - 0.58 * u, y + 0.58 * u], color=cm,
            lw=2.3 * min(u, 1.0) ** 0.4, zorder=4)
    for y0, y1 in ((0.30, 0.58), (-0.14, 0.14), (-0.58, -0.30)):
        ax.plot([xc, xc], [y + y0 * u, y + y1 * u], color=cm,
                lw=2.3 * min(u, 1.0) ** 0.4, zorder=4)     # three bars
    #  gid='symbol': figcheck reads these as part of the device, not as
    #  wiring - the bulk tie lands on the source lead's corner and the
    #  parasitics hang off the drain and source nodes without dots, both
    #  by the convention of the symbol, not of the wiring around it.
    wire(ax, [(xc, y + 0.44 * u), (x, y + 0.44 * u), (x, yt)], cm,
         gid='symbol')                                          # drain
    wire(ax, [(xc, y - 0.44 * u), (x, y - 0.44 * u), (x, yb)], cm,
         gid='symbol')                                          # source
    wire(ax, [(xc, y), (x, y), (x, y - 0.44 * u)], cm, gid='symbol')  # bulk
    ax.add_patch(FancyArrowPatch((x - 0.13 * u, y), (xc + 0.05 * u, y),
                                 arrowstyle='-|>',
                                 mutation_scale=10 * min(u, 1.0) ** 0.5,
                                 color=cm, lw=1.5, zorder=5,
                                 shrinkA=0, shrinkB=0))

    # body diode and C_oss hang off the same two nodes.  A figure that is
    # not about the dead time leaves them out - they are only there to
    # give intervals 3, 4, 7 and 8 somewhere to land.
    far = x
    if body or coss:
        far = x + (dx_c if coss else dx_d)
        wire(ax, [(x, yt), (far, yt)], OFF_C, 1.4, gid='symbol')
        wire(ax, [(x, yb), (far, yb)], OFF_C, 1.4, gid='symbol')
    if body:
        wire(ax, [(x + dx_d, yb), (x + dx_d, yt)], cd,
             2.0 if cd == GRN else 1.4, gid='symbol')
        vdiode(ax, x + dx_d, y, 0.26 * u, up=True, color=cd,
               lw=2.2 if cd == GRN else 1.6)
    if coss:
        wire(ax, [(x + dx_c, yb), (x + dx_c, y - 0.12 * u)], cc, 1.4,
             gid='symbol')
        wire(ax, [(x + dx_c, y + 0.12 * u), (x + dx_c, yt)], cc, 1.4,
             gid='symbol')
        vcap(ax, x + dx_c, y, 0.28 * u, 0.12 * u, color=cc, lw=2.0)
    if name:
        nc = GREY if state == 'off' else NAVY
        if name_at == 'gate':
            txt(ax, x - gate - 0.14, y, name, size=size, weight='bold',
                color=nc, ha='right')
        else:                                   # clear of the whole cluster
            txt(ax, far + 0.22, y, name, size=size, weight='bold',
                color=nc, ha='left')
    return (x, yt), (x, yb)


def xfmr(ax, x, y, hp=1.80, hs=None, np_t=None, ns_t=None, ct=False,
         gap=0.34,
         lp=None, ls=None, dots=True, core=0.13, lead=0.06, size=11,
         s_dot='top', tap_dot=True):
    """A transformer, optionally with a centre-tapped secondary.

    The windings sit CLOSE to the core.  Drawn with a gap wider than their
    own turns they read as two unrelated inductors with a pair of bars
    between them, which is what the first version did.

    But not touching it.  `gap` is a REQUEST, not the answer: the turn
    radius comes from this axes' scale, so the same gap that clears the
    bars in one drawing has the turns lying on them in another, and the
    caller cannot know which.  The gap that gets used is therefore the
    larger of what was asked for and what the turns need, and the caller
    reads the lead lines back out of the returned terminals rather than
    assuming x +- gap.

    Every winding that is drawn as its own symbol gets its own polarity
    dot.  On a centre tap that means two dots, not one: the halves are
    continuous and wound the same way, so the lower half's dot is the tap
    itself - which is exactly what makes one end conduct while the other
    blocks.  Drawing the dot on one half only leaves the second half's
    sense unstated.

    s_dot picks which END of a plain secondary carries the polarity dot.
    'top' is the usual same-sense drawing; 'bot' is the OPPOSITE sense,
    which is the whole difference between a forward converter and a
    flyback and must therefore be drawable.  It has no meaning on a
    centre tap, whose two dots are fixed by the tap itself.

    -> dict of terminal points: p_top p_bot s_top s_bot, and s_tap when
       ct is set.
    """
    hs = hp if hs is None else hs
    #  Turn COUNT follows from the winding height and one turn radius, so
    #  every winding in the document is drawn with the same size turn.
    #  Fixing the count instead makes a tall winding's turns bigger.
    r = WIND_R * scale(ax)
    #  A schematic winding is a few bumps, not a spring.  Filling the whole
    #  core height at a fixed turn radius put ten and more turns on a
    #  transformer drawn as tall as its circuit, and the symbol then
    #  dominated every drawing it appeared in.  Cap the count, keep the
    #  radius, and let straight lead wire take up the rest of the height.
    if np_t is None:
        np_t = min(5, max(3, int(round((hp - 2 * lead) / (2.0 * r)))))
    if ns_t is None:
        hh = (hs / 2.0 if ct else hs) - 2 * lead
        ns_t = min(4, max(2, int(round(hh / (2.0 * r)))))
    mark = len(getattr(ax, '_syms', []))
    rp = min(r, abs(hp - 2 * lead) / (2.0 * max(np_t, 1)))
    rs = min(r, abs((hs / (2.0 if ct else 1.0)) - 2 * lead)
             / (2.0 * max(ns_t, 1)))
    #  The turns bulge TOWARDS the core, so the lead line has to stand off
    #  by the core half-width, the turn radius, and a margin that still
    #  reads as a gap once the page has shrunk the figure.  CLEAR is that
    #  margin in turn radii; at 1.5 every transformer in this document
    #  clears its bars by about two points on A4, where before this the
    #  closest was a quarter of a point and one was a point and a half
    #  INSIDE them.
    CLEAR = 1.5
    gap = max(gap, core + (1.0 + CLEAR) * max(rp, rs))
    xp, xs = x - gap, x + gap
    #  what the page actually gets, for figcheck to convert into points
    ax._xfmr_clear = getattr(ax, '_xfmr_clear', []) + [
        gap - core - rp, gap - core - rs]
    ytp, ybp = y + hp / 2.0, y - hp / 2.0
    yts, ybs = y + hs / 2.0, y - hs / 2.0
    def _wind(xx, y0, y1, n, rr, side):
        """n turns of radius rr, centred in the span, leads for the rest."""
        c = (y0 + y1) / 2.0
        h = min(abs(y1 - y0) - 2 * lead, 2.0 * rr * n)
        a, b = c - h / 2.0, c + h / 2.0
        coil(ax, xx, a, b, n=n, side=side)
        wire(ax, [(xx, y0), (xx, a)])
        wire(ax, [(xx, b), (xx, y1)])
        return a, b

    #  A polarity dot belongs to a WINDING, so it is placed against that
    #  winding's top turn, on the side the turns bulge towards.  Put out
    #  beyond the lead line - which is where it used to be - it sits on
    #  the circuit wire and a reader has to work out which coil it means.
    #  There is room for it beside the coil now that the turns are bigger
    #  and stand further off the core.
    pa, pb = _wind(xp, ybp, ytp, np_t, rp, +1)
    ext = [pa, pb]
    if dots:
        dot(ax, xp + 0.80 * rp, pb + 0.50 * rp, NAVY, 4.8)
    if lp:
        txt(ax, xp - 0.42, y, lp, size=size, ha='right')

    out = dict(p_top=(xp, ytp), p_bot=(xp, ybp),
               s_top=(xs, yts), s_bot=(xs, ybs))
    if ct:
        ua, ub = _wind(xs, y, yts, ns_t, rs, -1)
        la, lb = _wind(xs, ybs, y, ns_t, rs, -1)
        ext += [ua, ub, la, lb]
        if dots:
            dot(ax, xs - 0.80 * rs, ub + 0.50 * rs, NAVY, 4.8)
            dot(ax, xs - 0.80 * rs, lb + 0.50 * rs, NAVY, 4.8)
        if tap_dot:
            dot(ax, xs, y)
        out['s_tap'] = (xs, y)
        if ls:
            txt(ax, xs + 0.42, (y + yts) / 2.0, ls[0], size=size, ha='left')
            txt(ax, xs + 0.42, (y + ybs) / 2.0, ls[1], size=size, ha='left')
    else:
        sa, sb = _wind(xs, ybs, yts, ns_t, rs, -1)
        ext += [sa, sb]
        if dots:
            if s_dot == 'bot':
                dot(ax, xs - 0.80 * rs, sa - 0.50 * rs, NAVY, 4.8)
            else:
                dot(ax, xs - 0.80 * rs, sb + 0.50 * rs, NAVY, 4.8)
        if ls:
            txt(ax, xs + 0.42, y, ls, size=size, ha='left')
    #  The core spans the WINDINGS, not the terminals.  Drawn to the full
    #  terminal height it stood a long way past the coils once those were
    #  capped, and the symbol read as two bars with a small coil beside it.
    #  Overhang from the turn radius, not a constant.  At a fixed 0.30 a
    #  short winding got a core half as long again as itself, and the
    #  symbol read as two long bars with a coil beside them.
    over = 0.45 * max(rp, rs)
    for xx in (x - core, x + core):
        ax.plot([xx, xx], [min(ext) - over, max(ext) + over],
                color=GREY, lw=2.4, zorder=3)

    #  a transformer's turns are their own class, and are checked as one
    syms = getattr(ax, '_syms', [])
    for i in range(mark, len(syms)):
        if syms[i][0] == 'turn':
            syms[i] = ('winding',) + syms[i][1:]
    return out


#  Registries of the things a straight run can meet.  A drawing sets them
#  once with `register()`; the highlight then climbs hops and follows coils
#  without the caller listing those points again.
HOPS, VCOILS, HCOILS = [], [], []


def register(hops=(), vcoils=(), hcoils=()):
    """Declare the wire hops and windings the highlight has to follow."""
    global HOPS, VCOILS, HCOILS
    HOPS, VCOILS, HCOILS = list(hops), list(vcoils), list(hcoils)


def _arc(hx, hy, r, going_right):
    a = np.linspace(np.pi, 0, 24) if going_right else np.linspace(0, np.pi, 24)
    return [(hx + r * np.cos(t), hy + r * np.sin(t)) for t in a]


def _detour(p0, p1, r=0.20):
    """What the highlight does between two points instead of a straight run.

    A run can hold more than one thing to follow - the tank wire crosses the
    right leg AND goes through L_r - so every feature on the segment is
    collected and laid down in travel order.  Returning at the first match
    left L_r flattened under a straight band.
    """
    (x0, y0), (x1, y1) = p0, p1
    segs = []
    if abs(y0 - y1) < 1e-9:                                   # horizontal
        lo, hi = min(x0, x1), max(x0, x1)
        for hx, hy in HOPS:
            if abs(y0 - hy) < 1e-9 and lo < hx - r and hx + r < hi:
                segs.append((hx, [(hx - r, hy)] + _arc(hx, hy, r, True)
                             + [(hx + r, hy)]))
        for cx, cy, span, n in HCOILS:
            if abs(y0 - cy) < 1e-9 and lo <= cx - span / 2.0 \
                    and cx + span / 2.0 <= hi:
                segs.append((cx, hcoil_pts(cx, cy, span, n)))
        flip = x1 < x0
    elif abs(x0 - x1) < 1e-9:                                 # vertical
        lo, hi = min(y0, y1), max(y0, y1)
        for cx, cl, ch, n, side in VCOILS:
            if abs(x0 - cx) < 1e-9 and lo <= cl and ch <= hi:
                segs.append((cl, coil_pts(cx, cl, ch, n, side)))
        flip = y1 < y0
    else:
        return []
    segs.sort(key=lambda t: t[0])
    out = []
    for _, pts in segs:
        out += pts
    return out[::-1] if flip else out


def _with_hops(pts, r=0.20):
    out = [pts[0]]
    for p0, p1 in zip(pts, pts[1:]):
        out += _detour(p0, p1, r)
        out.append(p1)
    return out


def path(ax, pts, load=True, heads=(), lw=3.8, head=18, color=None):
    """The conducting path, laid over the drawing.

    load=True  -> solid magenta, power is being delivered
    load=False -> dashed cyan, only the magnetising current circulates
    heads: (index, fraction) pairs - the segment ENDING at index, and how
    far along it the arrowhead goes.  The fraction is not cosmetic: at the
    default 0.62 the right leg's arrow landed exactly on the wire hop and
    the left leg's inside the MOSFET symbol, because those are where 62 %
    of those particular runs falls.
    """
    #  `color` is for the one case the two-colour convention does not
    #  cover: a fault current, which is neither the load nor the
    #  magnetising current and must not be mistaken for either.
    col = color or (MAG if load else CYA)
    xs, ys = zip(*_with_hops(pts))
    # UNDER the schematic, not over it.  Laid on top, a 3.8-wide highlight
    # swallowed the chord of every coil it ran through and struck out the
    # device names; underneath it reads as a glow round the wire and every
    # symbol stays whole.
    ax.plot(xs, ys, color=col, lw=lw + 1.4, alpha=0.42 if load else 0.60,
            zorder=1.5, solid_capstyle='round',
            ls='-' if load else (0, (3.4, 2.0)))
    #  `head` is in points, so it does NOT shrink with the drawing.  A
    #  scale tuned on a full-page panel swallows a small inductor whole on
    #  a half-width one, which is what it did to the boost reactor.
    for h in heads:
        i, f = h if isinstance(h, tuple) else (h, 0.62)
        p0, p1 = np.array(pts[i - 1], float), np.array(pts[i], float)
        d = p1 - p0
        n = np.hypot(*d)
        if n < 1e-9:
            continue
        m = p0 + f * d
        ax.add_patch(FancyArrowPatch(m - d / n * 0.13, m + d / n * 0.13,
                                     arrowstyle='-|>', mutation_scale=head,
                                     color=col, lw=2.5, zorder=8,
                                     shrinkA=0, shrinkB=0))
