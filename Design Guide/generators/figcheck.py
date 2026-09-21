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
  no-dot / nodot / open-end / stub / crossing / off-grid
            the wiring itself, read back off the axes - see topology().
  clipped   a patch drawn past its own axes, so the reader sees its label
            and not the box.
  tiny      text that lands under 6.5 pt once the page scales the figure
            down to the column width it is actually printed at.  The floor
            is there to catch the 3 and 4 pt disasters, not to police the
            last half point: a 9.5 pt label on a full-column figure prints
            at 6.65 and reads perfectly well.

It is a reporter, not a judge: a figure can legitimately put a caption
over a shaded band.  It exists so that a person looking at a list of
twelve figures knows which three to open.
"""
import re
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
        if getattr(t, '_is_foot', False):
            continue               # the caption, laid out by save() itself
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


def ink(fig, floor=10):
    """Where a text's GLYPHS actually land on drawn ink, in pixels.

    The geometric test this replaces asked whether a line passed through
    the text's bounding BOX.  A box is bigger than the letters in it - it
    carries the font's ascent, descent and side bearings - so a label
    correctly placed a hair off a wire was reported as lying on it, and
    tuning the box smaller to silence those would have been fitting the
    checker to the answer.

    So it is measured instead.  The figure is rendered twice: once as it
    is, and once with every text string emptied.  The pixels that differ
    ARE the glyphs; anything non-white in the second render is the drawing.
    Where those two masks meet, a letter is sitting on ink, and the count
    of such pixels says how badly.

    Emptying the string rather than hiding the artist matters: a note box
    and an annotation's arrow are drawn in both passes, so neither is
    mistaken for a letter.

    -> [(text, axes, overlapping pixel count), ...], worst first
    """
    fig.canvas.draw()
    A = np.asarray(fig.canvas.buffer_rgba()).astype(np.int16)
    boxes = _boxes(fig)
    #  Hidden by alpha, not by emptying the string.  An annotation's arrow
    #  is clipped at its own text box, so an emptied text let the arrow
    #  grow into the space the letters had been, and that extra piece of
    #  arrow was then read as letters lying on ink - a phantom overlap on
    #  every callout in the document.
    saved = [(t, t.get_alpha()) for t, _, _ in boxes]
    for t, _ in saved:
        t.set_alpha(0.0)
    #  A label INSIDE a filled box is not lying on anything - the fill is
    #  its background.  So the second pass also blanks the face of every
    #  large patch (a block, a shaded band, a switch's halo) and keeps its
    #  edge, which IS line work.  Small filled shapes - a diode's triangle,
    #  an arrowhead - stay, because a label on one of those is a fault.
    r = fig.canvas.get_renderer()
    faces = []
    for ax in fig.axes:
        for pa in ax.patches:
            try:
                bb = pa.get_window_extent(r)
            except Exception:                            # noqa: BLE001
                continue
            if bb.width * bb.height > 1500 and pa.get_visible():
                faces.append((pa, pa.get_facecolor()))
                pa.set_facecolor('none')
    #  The current highlight (zorder 1.5, under the drawing) is a
    #  background band too: a label brushing its glow is not lying on a
    #  wire.  Anything drawn below the wiring is hidden in this pass.
    glows = []
    for ax in fig.axes:
        if ax.get_aspect() not in ('equal', 1, 1.0):
            continue
        for ln in ax.lines:
            if ln.get_zorder() < 2 and ln.get_visible():
                glows.append((ln, ln.get_alpha()))
                ln.set_alpha(0.0)
    try:
        fig.canvas.draw()
        B = np.asarray(fig.canvas.buffer_rgba()).astype(np.int16)
    finally:
        for t, al in saved:
            t.set_alpha(al)
        for pa, fc in faces:
            pa.set_facecolor(fc)
        for ln, al in glows:
            ln.set_alpha(al)
        fig.canvas.draw()

    H = A.shape[0]
    glyph = (np.abs(A[:, :, :3] - B[:, :, :3]).max(axis=2) > 12)
    drawn = (B[:, :, :3].min(axis=2) < 235)
    both = glyph & drawn
    out = []
    for t, ax, b in boxes:
        c0, c1 = int(np.floor(b.x0)), int(np.ceil(b.x1))
        r0, r1 = int(np.floor(H - b.y1)), int(np.ceil(H - b.y0))
        c0, r0 = max(c0, 0), max(r0, 0)
        n = int(both[r0:r1, c0:c1].sum())
        if n >= floor:
            out.append((t, ax, n))
    out.sort(key=lambda r: -r[2])
    return out


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

    for t, ax, n in ink(fig):
        #  White glyphs are drawn on a dark fill on purpose, and the second
        #  render blanks that fill - so what is measured under them is the
        #  fill's own outline and the gridlines behind it, not something a
        #  reader can see.  shield() skips them for the same reason.
        if _shielded(t) or _white(t):
            continue
        bad.append(('on-ink', '%-28s %4d px of it are on drawn line work'
                    % (_short(t), n)))

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
    bad.extend(tiny(fig, name))
    bad.extend(windings(fig, name))
    return bad


#  ------------------------------------------------------------------ size
#  A4 text column, the same arithmetic an_pdf.py does.
_CW_PT = 595.276 - 62 - 62
_HCAP_PT = 560.0                 # an_pdf keeps one figure to a page
_PLACE = None


def _placement(name):
    """How wide the application note actually prints this figure, in points.

    Read out of an_body.py rather than assumed, because half the figures
    ask for a fraction of the column and that fraction is the whole
    reason their text lands at 3 pt on paper.
    """
    global _PLACE
    if _PLACE is None:
        import os
        out = {}
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'an_body.py')
        try:
            s = open(f, encoding='utf-8').read()
        except OSError:
            return _CW_PT
        for m in re.finditer(r"fig\('([a-z0-9_]+)'", s):
            i, d = m.end(), 1          # balance the call's own brackets
            while i < len(s) and d:
                d += (s[i] == '(') - (s[i] == ')')
                i += 1
            w = re.search(r"width=CW \* ([0-9.]+)", s[m.end():i])
            out[m.group(1)] = _CW_PT * float(w.group(1)) if w else _CW_PT
        _PLACE = out
    return _PLACE.get(name, _CW_PT)


def _page_pt(fig, name, ax):
    """page points per data unit on this axes, once A4 has shrunk the figure"""
    fw, fh = fig.get_size_inches()
    w = _placement(name)
    h = w * fh / fw
    if h > _HCAP_PT:
        w *= _HCAP_PT / h
    sc = w / (fw * 72.0)
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    p = ax.get_position()
    inch = min(p.width * fw / max(abs(x1 - x0), 1e-9),
               p.height * fh / max(abs(y1 - y0), 1e-9))
    return inch * 72.0 * sc


def windings(fig, name, floor=1.5):
    """Transformer turns resting on their own core bars.

    schemx.xfmr records what standoff it actually used; this converts it
    to page points and subtracts the two stroke half-widths, because what
    a reader sees is ink against ink, not centre line against centre line.

    Nothing here shows up in the PNG at screen size, which is how it hid:
    the worst case in this document was a turn a point and a half INSIDE
    the bars, and the eye only caught it at four times magnification on a
    figure that had already been checked and shipped.
    """
    bad = []
    for ax in fig.axes:
        cl = getattr(ax, '_xfmr_clear', None)
        if not cl:
            continue
        upt = _page_pt(fig, name, ax)
        for c in cl:
            edge = c * upt - 1.2 - 1.0      # core lw 2.4, coil lw 2.0
            if edge < floor:
                bad.append(('winding', 'turns clear the core bars by only '
                            '%.2f pt on the page (floor %.1f)'
                            % (edge, floor)))
    return bad


#  ---------------------------------------------------------------- where
#  A finding printed as one line tells the reader a figure is wrong and
#  not where to look.  ITEMS carries, for every individual offender, the
#  box it occupies as a fraction of its own figure, so an_locate.py can
#  put that box back on the printed page and ring it.  Fractions, because
#  the figure is a PNG by the time the page has it and the only thing
#  that survives the trip is relative position.
ITEMS = []


def _frac(fig, b):
    """a display-pixel box as fractions of the SAVED image, y from the top

    Of the saved image and not of the figure canvas, because savefig
    crops to the tight box: the two differ by an inch at the top of a
    tall figure, and a ring drawn an inch out is worse than no ring.
    """
    import figs
    #  Cached on the figure: saved_box draws the whole canvas, and one
    #  figure here has seventy-eight offenders.  Measuring it once per
    #  text turned a four minute sweep into a ten minute one.
    box = getattr(fig, '_saved_box', None)
    if box is None:
        box = fig._saved_box = figs.saved_box(fig)
    x0, y0, x1, y1 = box
    W, H = max(x1 - x0, 1e-9), max(y1 - y0, 1e-9)
    return ((b.x0 - x0) / W, (y1 - b.y1) / H,
            (b.x1 - x0) / W, (y1 - b.y0) / H)


def _item(kind, name, fig, b, note):
    ITEMS.append({'kind': kind, 'fig': name, 'box': _frac(fig, b),
                  'note': note})


def tiny(fig, name, floor=6.5):
    """Text that will be unreadable once the page shrinks the figure.

    Nothing here is wrong in the PNG - it is wrong at A4.  A figure 14 in
    wide printed 6.5 in wide divides every point size by 2.2, so a 10 pt
    annotation arrives at 4.5 pt and the reader gives up.  Ten figures
    went out like that before anyone put a number on it.

    What matters is fontsize / figure-width-in-inches: the dpi cancels.
    """
    fw, fh = fig.get_size_inches()
    w = _placement(name)
    h = w * fh / fw
    if h > _HCAP_PT:                 # an_pdf shrinks it again to fit a page
        w *= _HCAP_PT / h
    sc = w / (fw * 72.0)
    small = []
    for t, ax, b in _boxes(fig):
        try:
            s = float(t.get_fontsize()) * sc
        except Exception:                                # noqa: BLE001
            continue
        if s < floor:
            small.append((s, _short(t)))
            _item('tiny', name, fig, b,
                  '%.1f pt on the page: %s' % (s, _short(t)))
    if not small:
        return []
    small.sort()
    return [('tiny', 'page scale %.2f - %d text(s) under %.1f pt, '
             'smallest %.1f pt  %s'
             % (sc, len(small), floor, small[0][0], small[0][1]))]


def _white(t):
    """A white halo on white glyphs erases them - the bar labels of the
    output-bank figure came out as white blobs.  Such text is drawn on a
    dark fill on purpose, so it is left alone."""
    from matplotlib.colors import to_rgb
    try:
        r, g, b = to_rgb(t.get_color())
    except ValueError:
        return False
    return min(r, g, b) > 0.9


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
    """Give a white halo to any PLOT text that sits on drawn ink.

    Applied at save time rather than at each call site.  The alternative
    was to remember a halo in sixty places, and the twenty texts sitting on
    curves in the older figures are what remembering looks like in
    practice.  Only text that is measured to be on ink is touched, so
    nothing that reads cleanly gets a stroke it does not need.

    Schematic axes (aspect equal) are left alone: there a halo cuts a
    white gap in the wire the label is lying on, which is worse than the
    overlap.  check() reports those and they get moved.

    It returns what it had to rescue, and `run` prints that list.
    """
    sch = {ax for ax in fig.axes if ax.get_aspect() in ('equal', 1, 1.0)}
    out = []
    for t, ax, n in ink(fig):
        if ax in sch or _shielded(t) or _white(t):
            continue
        t.set_path_effects([_pe.withStroke(linewidth=3.4,
                                           foreground='white')])
        t.set_zorder(max(t.get_zorder(), 9))
        out.append(_short(t))
    return out


def crops(fig, name, outdir, zoom=3, pad=60):
    """A magnified crop round every text that is on ink, its box in red.

    So that a finding is judged by looking, not by arguing about it: the
    first pass of the on-ink test flagged twenty labels that turned out to
    be a hair off their wires, and the only way to know was to see them.
    """
    import os
    from PIL import Image, ImageDraw
    hits = ink(fig)
    if not hits:
        return []
    fig.canvas.draw()
    A = np.asarray(fig.canvas.buffer_rgba())
    im = Image.fromarray(A[:, :, :3].copy())
    H = im.height
    out = []
    for k, (t, ax, n) in enumerate(hits):
        b = Text.get_window_extent(t, fig.canvas.get_renderer())
        x0, x1 = int(b.x0), int(b.x1)
        y0, y1 = int(H - b.y1), int(H - b.y0)
        box = (max(0, x0 - pad), max(0, y0 - pad),
               min(im.width, x1 + pad), min(im.height, y1 + pad))
        c = im.crop(box)
        d = ImageDraw.Draw(c)
        d.rectangle((x0 - box[0], y0 - box[1], x1 - box[0], y1 - box[1]),
                    outline=(255, 0, 0), width=1)
        c = c.resize((c.width * zoom, c.height * zoom), Image.LANCZOS)
        f = os.path.join(outdir, '%s_%02d.png' % (name, k))
        c.save(f)
        out.append((f, _short(t), n))
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
      stray-dot  a junction dot where exactly two wire arms meet - a plain
                 corner.  A dot means "these wires are connected, they do
                 not merely cross"; on a corner there is nothing to say,
                 and it looks exactly like the dots that do say something.
                 A dot on ONE arm is a port marker and is left alone, as
                 is a dot on no wire at all (a transformer's polarity dot).
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

        #  Junctions the drawing declares undotted on purpose - see
        #  schemx.nodot.  Listed below, never counted.
        declared = [np.asarray(T(np.array([q]))[0], float)
                    for q in getattr(ax, '_nodots', [])]

        def near_dot(p):
            return any(np.hypot(*(p - d)) <= tol for d in dots)

        def declared_nodot(p):
            return any(np.hypot(*(p - d)) <= tol * 3 for d in declared)

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
                    bad.append(('nodot' if declared_nodot(p) else 'no-dot',
                                'junction at %s has no dot' % where(p)))
        for i, p in ends:
            if arms(p) >= 2 or through(p) or on_symbol(p) or near_dot(p):
                continue
            kind = 'stub' if i in junction_pieces else 'open-end'
            bad.append((kind, 'wire ends at %s touching nothing' % where(p)))

        for d in dots:
            if arms(d) == 2 and not through(d):
                bad.append(('stray-dot', 'dot at %s marks a corner, not a '
                            'junction' % where(d)))

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
                sv = d - c
                den = r[0] * sv[1] - r[1] * sv[0]
                if abs(den) < 1e-9:
                    continue
                q = c - a
                t = (q[0] * sv[1] - q[1] * sv[0]) / den
                u = (q[0] * r[1] - q[1] * r[0]) / den
                et = tol / max(L, 1e-9)
                eu = tol / max(float(np.hypot(*sv)), 1e-9)
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



def run(names=None, cropdir=None):
    """Draw every figure through figs.py and report, saving nothing.

    With `cropdir`, every on-ink finding is also saved there as a
    magnified crop with the text's box drawn in red.
    """
    import figs
    figs.PLAIN = True          # check the AN's figures: no footer, as saved to figures/an
    keep = figs.save
    found = {}

    sizes = {}
    rescued = {}

    def spy(fig, nm):
        sizes[nm] = symbols(fig)
        if cropdir:
            for f, lbl, n in crops(fig, nm, cropdir):
                print('  crop %-40s %-28s %4d px' % (f.split('/')[-1], lbl, n))
        #  save() shields on-ink text before writing the file, so the check
        #  has to run on the same thing the reader gets.  Checking before
        #  the shield reports twenty faults that the saved figure does not
        #  have, which is worse than not checking.
        #  finish() is what save() does to a figure before writing it:
        #  halos, and the footer caption.  Checking anything else reports
        #  faults the reader's copy does not have, and measures positions
        #  against a canvas the reader's copy was cropped out of.
        rescued[nm] = figs.finish(fig)
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
        for k, nums in (('an_modes_12', (1, 2)), ('an_modes_34', (3, 4)),
                        ('an_modes_56', (5, 6)), ('an_modes_78', (7, 8))):
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
        total += sum(1 for kind, _ in b if kind not in ('stub', 'nodot'))
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
    argv = sys.argv[1:]
    cd = None
    if '--crops' in argv:
        k = argv.index('--crops')
        cd = argv[k + 1]
        del argv[k:k + 2]
    run(argv or None, cropdir=cd)
