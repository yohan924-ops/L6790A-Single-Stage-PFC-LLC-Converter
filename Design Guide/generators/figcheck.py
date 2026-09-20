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

It is a reporter, not a judge: a figure can legitimately put a caption
over a shaded band.  It exists so that a person looking at a list of
twelve figures knows which three to open.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
import matplotlib.patheffects as _pe


def _boxes(fig):
    r = fig.canvas.get_renderer()
    out = []
    for ax in fig.axes:
        for t in ax.texts:
            if not t.get_visible() or not t.get_text().strip():
                continue
            try:
                out.append((t, ax, t.get_window_extent(r)))
            except Exception:
                pass
    for t in fig.texts:
        if t.get_visible() and t.get_text().strip():
            try:
                out.append((t, None, t.get_window_extent(r)))
            except Exception:
                pass
    return out


def _segments(ax, r):
    """Every drawn line segment of an axes, in display coordinates."""
    segs = []
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


def shield(fig):
    """Give a white halo to any text this figure draws over its own ink.

    Applied at save time rather than at each call site.  The alternative
    was to remember a halo in sixty places, and the twenty texts sitting on
    curves in the older figures are what remembering looks like in
    practice.  Only text that is ALREADY on line work is touched, so
    nothing that reads cleanly gets a stroke it does not need.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    n = 0
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
                n += 1
    return n


def run(names=None):
    """Draw every figure through figs.py and report, saving nothing."""
    import figs
    keep = figs.save
    found = {}

    def spy(fig, nm):
        #  save() shields on-ink text before writing the file, so the check
        #  has to run on the same thing the reader gets.  Checking before
        #  the shield reports twenty faults that the saved figure does not
        #  have, which is worse than not checking.
        shield(fig)
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
    finally:
        figs.save = keep

    total = 0
    for k in sorted(found):
        b = found[k]
        if not b:
            continue
        total += len(b)
        print('%s' % k)
        seen = set()
        for kind, msg in b:
            if (kind, msg) in seen:
                continue
            seen.add((kind, msg))
            print('   %-10s %s' % (kind, msg))
    print('\n%d figure(s) checked · %d finding(s)' % (len(found), total))
    return found


if __name__ == '__main__':
    import sys
    run(sys.argv[1:] or None)
