# -*- coding: utf-8 -*-
"""Geometry checker for the generated figures - check_sm.py for matplotlib.

Written after a batch of figures went out with a text label sitting on a
wire, an annotation running out of its own panel into the one below, and
four bridge diodes pointing backwards.  Every one of those is visible at
full size and invisible on a contact sheet, which is how they got through.

What it reports, per figure:

  outside   a text whose box leaves its axes by more than a margin.  An
            annotation placed at y = -1.0 in axis data units lands in the
            next panel down, and nothing in matplotlib complains.
  on-ink    a text box sitting on drawn line work, with no white gap and
            no halo of its own.  Labels are allowed to touch their own
            leader lines, so a line that STARTS or ENDS inside the box is
            not counted.
  text-text two text boxes overlapping each other.
  no-dot / open-end / stub / crossing / off-grid
            the wiring itself, read back off the axes - see topology().
  clipped   a patch drawn past its own axes, so the reader sees its label
            and not the box.

It is a reporter, not a judge: a figure can legitimately put a caption
over a shaded band.  It exists so that a person looking at a list of
twelve figures knows which three to open.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from matplotlib.text import Text
import matplotlib.patheffects as _pe


def _boxes(fig):
    """Every visible text, with the box of the TEXT.

    Annotation.get_window_extent returns the text and its arrow together,
    so a callout whose arrow crossed two component labels was reported as
    overlapping them.  Text.get_window_extent, called on the same object,
    is the text alone - which is what a reader's eye sees as the label.
    """
    r = fig.canvas.get_renderer()
    out = []
    for ax in fig.axes:
        for t in ax.texts:
            if not t.get_visible() or not t.get_text().strip():
                continue
            try:
                out.append((t, ax, Text.get_window_extent(t, r)))
            except Exception:
                pass
    for t in fig.texts:
        if t.get_visible() and t.get_text().strip():
            try:
                out.append((t, None, Text.get_window_extent(t, r)))
            except Exception:
                pass
    return out


def _segments(ax, r):
    """Every drawn line of an axes, in display coordinates.

    Patch outlines count too.  Leaving them out meant a label lying across
    a resistor box was invisible to this check, because a box is a Patch
    and not a Line2D - and that is exactly where a shunt label lands when
    the symbol it names changes size.
    """
    segs = []
    for pa in ax.patches:
        if not pa.get_visible():
            continue
        try:
            v = pa.get_path().transformed(pa.get_patch_transform())
            d = ax.transData.transform(v.vertices)
        except Exception:                                # noqa: BLE001
            continue
        d = d[np.isfinite(d).all(axis=1)]
        if len(d) >= 2:
            segs.append((pa, d))
    for ln in ax.lines:
        if not ln.get_visible():
            continue
        xy = ln.get_xydata()
        if len(xy) < 2:
            continue
        d = ax.transData.transform(np.asarray(xy, float))
        d = d[np.isfinite(d).all(axis=1)]
        if len(d) >= 2:
            segs.append((ln, d))
    return segs


def _hits(box, pts, pad=1.0):
    """Does a polyline pass THROUGH the box rather than end in it?"""
    inside = ((pts[:, 0] > box.x0 - pad) & (pts[:, 0] < box.x1 + pad) &
              (pts[:, 1] > box.y0 - pad) & (pts[:, 1] < box.y1 + pad))
    if not inside.any():
        return False
    # a leader line that ends in the label is fine; a wire crossing is not
    return bool(inside.any() and not inside.all() and inside.sum() > 2
                and inside[0] == inside[-1])


def check(fig, name, margin=3.0):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bad = []
    boxes = _boxes(fig)

    #  Leaving your own axes is normal - a row label is placed to the left
    #  of the frame on purpose.  What is never intended is landing in
    #  SOMEONE ELSE'S panel, or off the paper.  Flagging the first caught
    #  every row label and buried the two real cases.
    fb = fig.bbox
    others = [(a, a.get_window_extent(r)) for a in fig.axes]
    for t, ax, b in boxes:
        if b.x0 < fb.x0 - margin or b.x1 > fb.x1 + margin \
                or b.y0 < fb.y0 - margin or b.y1 > fb.y1 + margin:
            bad.append(('off-page', '%-28s leaves the figure' % _short(t)))
            continue
        for a, ab in others:
            if a is ax:
                continue
            if not b.overlaps(ab):
                continue
            w = min(b.x1, ab.x1) - max(b.x0, ab.x0)
            h = min(b.y1, ab.y1) - max(b.y0, ab.y0)
            if w > 2 and h > 2:
                bad.append(('wrong-panel',
                            '%-28s lands in another panel' % _short(t)))
                break

    for ax in fig.axes:
        segs = _segments(ax, r)
        for t, tax, b in boxes:
            if tax is not ax:
                continue
            if _shielded(t):        # it brings its own background with it
                continue
            bb = Bbox.from_extents(b.x0 + 1, b.y0 + 1, b.x1 - 1, b.y1 - 1)
            for ln, pts in segs:
                if _hits(bb, pts):
                    bad.append(('on-ink', '%-28s sits on drawn line work'
                                % _short(t)))
                    break

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, c = boxes[i][2], boxes[j][2]
            if a.overlaps(c):
                w = min(a.x1, c.x1) - max(a.x0, c.x0)
                h = min(a.y1, c.y1) - max(a.y0, c.y0)
                if w > 2 and h > 2:
                    bad.append(('text-text', '%-28s over %s'
                                % (_short(boxes[i][0]),
                                   _short(boxes[j][0]))))
    bad.extend(topology(fig))
    bad.extend(clipped(fig))
    return bad


def _shielded(t):
    """Is this text already readable over line work?

    Two ways to be: a stroke halo, or an opaque bbox behind it.  The note
    boxes this project has used since the first figures are the second
    kind, and counting them as faults buried the real ones under twenty
    that were fine.
    """
    if t.get_path_effects():
        return True
    bb = t.get_bbox_patch()
    if bb is None:
        return False
    fc = bb.get_facecolor()
    return bool(fc is not None and len(fc) > 3 and fc[3] > 0.55)


def _short(t):
    s = ' '.join(t.get_text().split())
    return (s[:26] + '..') if len(s) > 28 else s


def symbols(fig):
    """Measure every component symbol, with the figure's scale divided out.

    A symbol is the same component wherever it appears, so once the scale
    its axes was drawn at is divided out it has to come back the same size
    - a capacitor 0.60 long, a resistor 1.15, a turn 0.28.  Sized in data
    units it shrank in a dense figure; sized as a fraction of the branch it
    hung on, as the first shunt() did, the same capacitor came out twice
    the size two figures apart.  This reports what was actually drawn.
    """
    fig.canvas.draw()
    out = []
    for ax in fig.axes:
        for rec in getattr(ax, '_syms', []):
            kind, x, y, w, h = rec[:5]
            k = rec[5] if len(rec) > 5 else 1.0
            out.append((kind, w / k, h / k))
    return out


def shield(fig):
    """Give a white halo to any text this figure draws over its own ink.

    Applied at save time rather than at each call site.  The alternative
    was to remember a halo in sixty places, and the twenty texts sitting on
    curves in the older figures are what remembering looks like in
    practice.  Only text that is ALREADY on line work is touched, so
    nothing that reads cleanly gets a stroke it does not need.

    It returns what it had to rescue, and `run` prints that list.  On a
    plot a caption over a curve is fine; on a SCHEMATIC the halo keeps the
    text readable by cutting a white gap in a wire, which is worse than
    the overlap it fixed.  Silently rescuing both hid exactly that - a
    callout eating through a bridge leg - so the rescues are now reported
    even though they are not failures.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    out = []
    for ax in fig.axes:
        segs = _segments(ax, r)
        if not segs:
            continue
        for t, tax, b in _boxes(fig):
            if tax is not ax or _shielded(t):
                continue
            bb = Bbox.from_extents(b.x0 + 1, b.y0 + 1, b.x1 - 1, b.y1 - 1)
            if any(_hits(bb, pts) for _, pts in segs):
                t.set_path_effects([_pe.withStroke(linewidth=3.4,
                                                   foreground='white')])
                t.set_zorder(max(t.get_zorder(), 9))
                out.append(_short(t))
    return out


# ------------------------------------------------------------------ wiring
#  The checks above are about text.  These are about the circuit: they read
#  the wires back off the axes and ask the questions a reviewer asks with a
#  finger on the page.  A wire is a Line2D at zorder 2, which is what
#  schem.wire and schemx.wire draw and nothing else does; symbols are every
#  other line and every patch; a junction dot is a marker-only line.  Only
#  aspect-equal axes are read, because that is what a schematic frame sets
#  and a waveform axis does not - a plotted curve is also a Line2D at
#  zorder 2, and read as wire it would report every trace as dangling.
#
#  Written after a primary winding went out with its return lead ending
#  in open air, a lead drawn 9 degrees off vertical, and a capacitor
#  hanging on a rail with no junction dot - none of which the text checks
#  can see, and all of which are one line each here.
def _pieces(xy):
    """Split a polyline at its NaN breaks (the kit's coils use them), and
    drop a vertex that repeats the one before it - a zero-length segment
    is not a corner, and counted as one it made a plain lead a junction."""
    out, cur = [], []
    for p in np.asarray(xy, float):
        if np.isfinite(p).all():
            if cur and np.hypot(*(p - cur[-1])) < 1e-6:
                continue
            cur.append(p)
        else:
            if len(cur) >= 2:
                out.append(np.array(cur))
            cur = []
    if len(cur) >= 2:
        out.append(np.array(cur))
    return out


def _seg_dist(p, a, b):
    """Distance from p to segment ab, and where along it (0..1) it falls."""
    d = b - a
    L2 = float(d @ d)
    if L2 < 1e-12:
        return float(np.hypot(*(p - a))), 0.0
    t = float(((p - a) @ d) / L2)
    q = a + min(1.0, max(0.0, t)) * d
    return float(np.hypot(*(p - q))), t


def topology(fig, tol=2.0):
    """Wiring faults of every schematic axes, in display pixels.

      no-dot     three or more wires meet, or a wire ends ON another wire,
                 and no junction dot is drawn there
      open-end   a wire ends touching nothing - no wire, no symbol, no dot
      stub       the same, but the wire has a junction elsewhere, so it is
                 a rail drawn past its last connection (reported, not
                 counted: a bus is allowed to run on a little)
      crossing   two wires cross with neither a hop nor a dot
      off-grid   a wire segment more than a degree off the 45-degree grid
    """
    fig.canvas.draw()
    bad = []
    for ax in fig.axes:
        if ax.get_aspect() not in ('equal', 1, 1.0):
            continue
        T = ax.transData.transform
        inv = ax.transData.inverted().transform
        wires, syms, dots = [], [], []
        for ln in ax.lines:
            if not ln.get_visible():
                continue
            xy = np.asarray(ln.get_xydata(), float)
            if ln.get_marker() not in (None, 'None', ''):
                if ln.get_linestyle() in ('None', '', ' ') or len(xy) == 1:
                    for p in xy[np.isfinite(xy).all(axis=1)]:
                        dots.append(T(p))
                continue
            if len(xy) < 2:
                continue
            z = ln.get_zorder()
            if ln.get_gid() == 'symbol':          # a device's own leads
                syms.extend(_pieces(T(xy)))
            elif z == 2:
                wires.extend(_pieces(T(xy)))
            elif z > 2:
                syms.extend(_pieces(T(xy)))
        for pa in ax.patches:
            if not pa.get_visible() or pa.get_zorder() < 2:
                continue
            try:
                v = pa.get_path().transformed(pa.get_patch_transform())
                syms.extend(_pieces(T(np.asarray(v.vertices, float))))
            except Exception:                            # noqa: BLE001
                continue
        if not wires:
            continue

        segs = [(i, pl[k], pl[k + 1])
                for i, pl in enumerate(wires) for k in range(len(pl) - 1)]
        ends = [(i, pl[j]) for i, pl in enumerate(wires) for j in (0, -1)]
        #  a corner of one wire is two arms; a wire ending on it makes three
        corners = [(i, q) for i, pl in enumerate(wires) for q in pl[1:-1]]
        ssegs = [(a, b) for pl in syms for a, b in zip(pl[:-1], pl[1:])]

        def near_dot(p):
            return any(np.hypot(*(p - d)) <= tol for d in dots)

        def on_symbol(p):
            return any(_seg_dist(p, a, b)[0] <= tol for a, b in ssegs)

        def through(p):
            """wire segments p lies strictly inside"""
            n = []
            for i, a, b in segs:
                dist, _ = _seg_dist(p, a, b)
                if dist <= tol and np.hypot(*(p - a)) > tol \
                        and np.hypot(*(p - b)) > tol:
                    n.append(i)
            return n

        def where(p):
            return '(%.2f, %.2f)' % tuple(inv(p))

        def arms(p):
            return (sum(1 for _, q in ends if np.hypot(*(p - q)) <= tol)
                    + 2 * sum(1 for _, q in corners
                              if np.hypot(*(p - q)) <= tol))

        junction_pieces = set()
        junctions = []
        for i, p in ends:
            n_end = arms(p)
            thru = through(p)
            if thru or n_end >= 3:
                junctions.append(p)
                junction_pieces.add(i)
                junction_pieces.update(thru)
                if not near_dot(p) and not any(
                        np.hypot(*(p - q)) <= tol for q in junctions[:-1]):
                    bad.append(('no-dot', 'junction at %s has no dot'
                                % where(p)))
        for i, p in ends:
            if arms(p) >= 2 or through(p) or on_symbol(p) or near_dot(p):
                continue
            kind = 'stub' if i in junction_pieces else 'open-end'
            bad.append((kind, 'wire ends at %s touching nothing' % where(p)))

        for x in range(len(segs)):
            i, a, b = segs[x]
            r = b - a
            L = float(np.hypot(*r))
            if L > tol:
                ang = float(np.degrees(np.arctan2(r[1], r[0]))) % 45.0
                off = min(ang, 45.0 - ang)
                if off > 1.0:
                    bad.append(('off-grid', 'wire %s to %s is %.0f deg off '
                                'the 45-degree grid'
                                % (where(a), where(b), off)))
            for y in range(x + 1, len(segs)):
                j, c, d = segs[y]
                if i == j:
                    continue
                s = d - c
                den = r[0] * s[1] - r[1] * s[0]
                if abs(den) < 1e-9:
                    continue
                q = c - a
                t = (q[0] * s[1] - q[1] * s[0]) / den
                u = (q[0] * r[1] - q[1] * r[0]) / den
                et = tol / max(L, 1e-9)
                eu = tol / max(float(np.hypot(*s)), 1e-9)
                if et < t < 1 - et and eu < u < 1 - eu:
                    p = a + t * r
                    if not near_dot(p):
                        bad.append(('crossing', 'wires cross at %s with no '
                                    'hop and no dot' % where(p)))
    return bad


def clipped(fig, margin=2.0):
    """Patches that leave their own axes - a box drawn past the frame is
    silently cut, and the label inside it survives to say it is there."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bad = []
    for ax in fig.axes:
        ab = ax.get_window_extent(r)
        for pa in ax.patches:
            if not pa.get_visible() or pa.get_zorder() < 2 \
                    or not pa.get_clip_on():
                continue
            try:
                b = pa.get_window_extent(r)
            except Exception:                            # noqa: BLE001
                continue
            if b.x0 < ab.x0 - margin or b.x1 > ab.x1 + margin \
                    or b.y0 < ab.y0 - margin or b.y1 > ab.y1 + margin:
                bad.append(('clipped', '%s at (%.1f, %.1f) leaves its axes'
                            % (type(pa).__name__,
                               *ax.transData.inverted().transform(
                                   ((b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2)))))
    return bad



def run(names=None):
    """Draw every figure through figs.py and report, saving nothing."""
    import figs
    keep = figs.save
    found = {}

    sizes = {}
    rescued = {}

    def spy(fig, nm):
        sizes[nm] = symbols(fig)
        #  save() shields on-ink text before writing the file, so the check
        #  has to run on the same thing the reader gets.  Checking before
        #  the shield reports twenty faults that the saved figure does not
        #  have, which is worse than not checking.
        rescued[nm] = shield(fig)
        found[nm] = check(fig, nm)
        plt.close(fig)

    figs.save = spy
    figs.PLAIN = True
    try:
        for k in (names or sorted(figs.FIGS)):
            try:
                figs.FIGS[k]()
            except Exception as e:                       # noqa: BLE001
                found[k] = [('ERROR', repr(e)[:90])]
        #  The eight-mode sheets are not in figs.FIGS - figs_modes8 writes
        #  them itself - and they are the drawings every other schematic
        #  was matched to, so they are read here by the same rules.
        import figs_modes8
        for k, nums in (('an_modes_1234', (1, 2, 3, 4)),
                        ('an_modes_5678', (5, 6, 7, 8))):
            if names and k not in names:
                continue
            spy(figs_modes8.sheet_fig(nums), k)
    finally:
        figs.save = keep

    total = 0
    for k in sorted(found):
        b = found[k]
        if not b:
            continue
        total += sum(1 for kind, _ in b if kind != 'stub')
        print('%s' % k)
        seen = set()
        for kind, msg in b:
            if (kind, msg) in seen:
                continue
            seen.add((kind, msg))
            print('   %-10s %s' % (kind, msg))
    print('\n%d figure(s) checked · %d finding(s)  (stubs listed, not counted)'
          % (len(found), total))

    hit = {k: v for k, v in rescued.items() if v}
    if hit:
        print('\ntext the shield had to rescue - on a schematic this means '
              'a label is\nlying on a wire and the halo is cutting it:')
        for k in sorted(hit):
            print('  %-20s %s' % (k, ', '.join(hit[k])))

    #  symbol sizes, gathered across every figure
    by = {}
    for nm, lst in sizes.items():
        for kind, w, h in lst:
            by.setdefault(kind, []).append((nm, w, h))
    if by:
        print('\nsymbol size at scale 1 (drawn size / the scale of its axes):')
        for kind in sorted(by):
            rows = by[kind]
            big = max(max(w, h) for _, w, h in rows)
            small = min(max(w, h) for _, w, h in rows)
            #  coil kinds carry integer turn counts, so a few per cent of
            #  rounding is the best they can do
            #  coil kinds carry integer turn counts, and the mode panels
            #  deliberately draw C_oss, C_r and C_o at 0.28, 0.30 and 0.32 -
            #  a 1.14x span that is reviewed and must not be flattened.
            tol = {'turn': 1.22, 'winding': 1.22, 'cap': 1.16}.get(kind, 1.02)
            flag = '' if big <= small * tol + 1e-9 else \
                   '   <-- %.2fx spread' % (big / max(small, 1e-9))
            print('  %-7s %2d drawn · longest side %.3f to %.3f%s'
                  % (kind, len(rows), small, big, flag))
            if flag:
                for nm, w, h in sorted(rows, key=lambda r: -max(r[1], r[2])):
                    print('        %-18s %5.3f x %5.3f' % (nm, w, h))
    return found


if __name__ == '__main__':
    import sys
    run(sys.argv[1:] or None)
