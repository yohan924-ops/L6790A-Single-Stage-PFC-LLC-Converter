# -*- coding: utf-8 -*-
"""Small, recorded edits to a figure lifted from a reference document.

Two legitimate reasons to touch a borrowed figure, and no others:

  1. the panel it came from carried its label somewhere the crop cannot
     reach - a table header row, say - so the crop is unusable without it;
  2. the source uses a symbol for the opposite quantity to this document,
     which is worse than useless to a reader;
  3. the panel contradicts itself and the user has said, in so many words, to
     correct it - which has happened exactly once, for the second-half
     freewheeling path, and the caption then says the panel is redrawn.

Anything else that changes what the figure ASSERTS is off limits. Every edit
made here is listed in EDITS below, so what was changed is always readable.

    python figedit.py                 apply every edit, in order
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.normpath(os.path.join(HERE, '..', 'figures'))
WIN = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
NAVY = (3, 35, 75)


def _font(px, bold=True):
    """Arial where it exists, Liberation Sans where it does not.

    The old version fell back to ImageFont.load_default(), which is a fixed
    bitmap face that IGNORES px.  On a machine without Arial - this one -
    every header came out about a fifth of the intended size and nothing
    said so; the figures just looked wrong next to the ones built on
    Windows.  Liberation Sans is metric-compatible with Arial, so the two
    machines now produce the same artwork.  A real fallback is an error.
    """
    cand = [os.path.join(WIN, 'arialbd.ttf' if bold else 'arial.ttf'),
            '/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf'
            % ('Bold' if bold else 'Regular'),
            '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
            % ('-Bold' if bold else '')]
    for f in cand:
        try:
            return ImageFont.truetype(f, px)
        except Exception:
            pass
    raise SystemExit('figedit: no scalable font found, tried:\n  '
                     + '\n  '.join(cand))


def band(src, dst, labels, h=54, size=30, color=NAVY):
    """Add a header band across the top and write one label per column.

    labels: list of (centre as a fraction of width, text)
    """
    im = Image.open(os.path.join(FIGS, src)).convert('RGB')
    w, ih = im.size
    out = Image.new('RGB', (w, ih + h), 'white')
    out.paste(im, (0, h))
    d = ImageDraw.Draw(out)
    f = _font(size)
    for frac, text in labels:
        bb = d.textbbox((0, 0), text, font=f)
        d.text((w * frac - (bb[2] - bb[0]) / 2, (h - (bb[3] - bb[1])) / 2 - 4),
               text, font=f, fill=color)
    out.save(os.path.join(FIGS, dst))
    WROTE.append(dst)
    print('  %-26s %d x %d  (+%d px header: %s)'
          % (dst, out.size[0], out.size[1], h,
             ', '.join(t for _, t in labels)))


def trim(name, margin=12):
    """Cut a caption the crop rectangle reached into.

    The cut is measured, not given: figtrim looks for ink that touches the
    bottom edge, is only a few rows tall, and is separated from the drawing
    by a wide band of white. A panel of a real figure is never sliced at the
    image boundary, so nothing else has that shape.
    """
    import figtrim
    p = os.path.join(FIGS, name)
    _im, w, h, r = figtrim.rows(p)
    got = figtrim.sliver(r, h)
    if not got:
        print('  %-26s nothing to trim' % name)
        return
    last, gap, tail = got
    keep = min(h, last + 1 + margin)
    Image.open(p).crop((0, 0, w, keep)).save(p)
    WROTE.append(name)
    print('  %-26s %d x %d  (cut %d rows: %d blank and %d of a source '
          'caption)' % (name, w, keep, h - keep, gap - margin, tail))


WROTE = []


def mirror():
    """Push the files THIS module wrote into figures/an/, where the AN reads.

    Only those. figures/ and figures/an/ are not two copies of one set: the
    generated figures differ deliberately, because figs.py --plain writes
    the untitled variants the note uses into an/ while the titled ones go to
    figures/. Mirroring everything replaces those with the wrong version -
    which is exactly what a first attempt at this did.

    The reference figures ARE the same in both, and were kept so by hand,
    which is to say not kept so at all: a fix here would have left the note
    reading the old file.
    """
    import shutil
    an = os.path.join(FIGS, 'an')
    n = 0
    for name in WROTE:
        dst = os.path.join(an, name)
        if not os.path.isfile(dst):
            continue
        if open(os.path.join(FIGS, name), 'rb').read() != open(dst, 'rb').read():
            shutil.copyfile(os.path.join(FIGS, name), dst)
            print('  mirrored into figures/an/  %s' % name)
            n += 1
    print('  figures/an/ updated: %d of %d written' % (n, len(WROTE)))


def fix_freewheel_2nd_half(src, dst):
    """Redraw the second-half freewheeling current path.

    The source (Infineon AN 2012-09 Figure 2.8) labels this panel
    "freewheeling, second half" but sends the current BACKWARDS through S1 and
    S4 and out of the + terminal.  S1 and S4 are off in that half and their
    body diodes are reverse biased while S2 and S3 hold the two mid-points at
    0 and Vin, so no current can take that path; and the direction drawn has
    the input absorbing power, where freewheeling still draws it.  What the
    panel actually shows is the dead time at the end of the half, where the
    negative tank current commutates in the S1/S4 body diodes.

    The path drawn here is the one the circuit takes: + rail, S3, the right
    mid-point, Lm, the tank, the left mid-point, S2, - rail - which is the
    source's own Figure 2.6 with the secondary loop open, exactly as its
    Figure 2.7 is Figure 2.5 with the secondary loop open.

    Editing a borrowed figure's arrows is normally forbidden.  This one is
    done on the user's explicit instruction (2026-09-18) and the caption says
    the panel is redrawn.

    Coordinates are measured from the file, not guessed:
        top rail  y  30   bottom rail y 291   tank wire y 125
        left leg  x 818   right leg   x 922   return wire y 207   Lm x 1091
    The red sits beside its wire, at the offsets the source itself uses.
    """
    RED = (255, 0, 0)
    ON, OFF, WIDE = 8, 3, 4              # the source's dash: 8 on, 3 off, 4 thick

    def dash(d, x0, y0, x1, y1):
        step = ON + OFF
        if y0 == y1:
            rng = range(x0, x1, step if x1 > x0 else -step)
            for x in rng:
                xe = x + ON - 1 if x1 > x0 else x - ON + 1
                d.rectangle([min(x, xe), y0 - WIDE // 2,
                             max(x, xe), y0 + WIDE // 2 - 1], fill=RED)
        else:
            rng = range(y0, y1, step if y1 > y0 else -step)
            for y in rng:
                ye = y + ON - 1 if y1 > y0 else y - ON + 1
                d.rectangle([x0 - WIDE // 2, min(y, ye),
                             x0 + WIDE // 2 - 1, max(y, ye)], fill=RED)

    def head(d, x, y, way, L=17, W=9):
        pts = {'R': [(x, y - W), (x, y + W), (x + L, y)],
               'L': [(x, y - W), (x, y + W), (x - L, y)],
               'D': [(x - W, y), (x + W, y), (x, y + L)],
               'U': [(x - W, y), (x + W, y), (x, y - L)]}[way]
        d.polygon(pts, fill=RED)

    im = Image.open(os.path.join(FIGS, src)).convert('RGB')
    a = np.asarray(im).copy()
    q = a.astype(int)                    # uint8 subtraction wraps; the mask needs signed
    xx = np.arange(a.shape[1])[None, :]
    # a loose mask: the anti-aliased edge of a dash is pink, and leaving it
    # behind shows as a ghost of the old path.  Left panel (x < 700) is correct.
    old = ((q[:, :, 0] - q[:, :, 1] > 18) |
           (q[:, :, 0] - q[:, :, 2] > 18)) & (xx >= 700)
    a[old] = (255, 255, 255)
    for y in range(28, 32):              # the old red crossed the top rail
        a[y, 820:842] = a[y, 780]

    im = Image.fromarray(a.astype('uint8'))
    d = ImageDraw.Draw(im)
    TOPY, BOTY, TANKY, RETY = 17, 300, 111, 216      # red levels beside each wire
    LEGL, LEGR, LMX = 830, 929, 1084                 # red columns beside each part
    dash(d, 772, TOPY, LEGR, TOPY);    head(d, 872, TOPY, 'R')    # + rail, in
    dash(d, LEGR, TOPY, LEGR, RETY);   head(d, LEGR, 186, 'D')    # through S3
    dash(d, LEGR, RETY, LMX, RETY);    head(d, 1032, RETY, 'R')   # to the transformer
    dash(d, LMX, RETY, LMX, TANKY);    head(d, LMX, 140, 'U')     # up through Lm
    dash(d, LMX, TANKY, LEGL, TANKY);  head(d, 906, TANKY, 'L')   # back through Lr, Cr
    dash(d, LEGL, TANKY, LEGL, BOTY);  head(d, LEGL, 272, 'D')    # through S2
    dash(d, LEGL, BOTY, 781, BOTY);    head(d, 800, BOTY, 'L')    # - rail, out
    im.save(os.path.join(FIGS, dst))
    print('  %-26s second-half freewheeling path redrawn' % dst)


def mark_modes(name):
    """Bracket the four intervals on the below-resonance panel.

    Readers kept reading the two circuit figures as a four-step sequence. The
    waveform figure already settles it, but the second half's freewheeling
    sits at the very right edge and is easy to miss, so mark all four.

    Every x is MEASURED off the traces - a bracket that drifted off its bump
    would be worse than no bracket. A rectifier is conducting exactly where
    its trace has LEFT its own zero line, which is immune to whatever the
    other traces are doing at that height; the half ends where the gate falls.
    """
    GRN, MAG = (0, 140, 70), (214, 0, 120)
    p = os.path.join(FIGS, name)
    a = np.asarray(Image.open(p).convert('RGB')).astype(int)
    h, w = a.shape[:2]
    navy = (a[:, :, 2] - a[:, :, 0] > 25) & (a.sum(axis=2) < 520)
    X0, X1 = int(w * 0.713), w - 21          # the below-resonance plot area

    def groups(rows):
        out, s, prev = [], None, None
        for y in rows:
            if s is None or y != prev + 1:
                if s is not None:
                    out.append(s)
                s = y
            prev = y
        if s is not None:
            out.append(s)
        return out

    def gaps(base):
        """x runs where the trace has left its zero line"""
        on = navy[base - 2:base + 3, X0:X1].any(axis=0)
        miss = np.where(~on)[0]
        out, s = [], None
        for i, x in enumerate(miss):
            if s is None:
                s = x
            elif x != miss[i - 1] + 1:
                out.append((s + X0, miss[i - 1] + X0)); s = x
        if s is not None:
            out.append((s + X0, miss[-1] + X0))
        return [r for r in out if r[1] - r[0] > 10]

    zeros = groups([y for y in range(h // 2, h)
                    if navy[y, X0:X1].sum() > (X1 - X0) * 0.45])
    lows = groups([y for y in range(h // 4, h // 2)
                   if navy[y, X0:X1].sum() > (X1 - X0) * 0.35])[:2]
    if len(zeros) != 2 or len(lows) != 2:
        raise SystemExit('mark_modes: found %d zero lines and %d gate lines'
                         % (len(zeros), len(lows)))

    src = Image.open(p).convert('RGB')
    im = Image.new('RGB', (src.width, src.height + 46), 'white')
    im.paste(src, (0, 0))                    # room for the lower bracket
    d = ImageDraw.Draw(im)
    f = _font(17)

    def span(xa, xb, y, colour, text):
        d.line([(xa, y), (xb, y)], fill=colour, width=3)
        for x in (xa, xb):
            d.line([(x, y - 6), (x, y + 6)], fill=colour, width=3)
        bb = d.textbbox((0, 0), text, font=f)
        d.text(((xa + xb) / 2 - (bb[2] - bb[0]) / 2, y + 4), text,
               font=f, fill=colour)

    told = []
    step = iter(('1 power delivery', '2 freewheeling',
                 '3 power delivery', '4 freewheeling'))
    for base, low in zip(zeros, lows):
        c = np.where(navy[low - 16:low - 4, X0:X1].any(axis=0))[0] + X0
        gate = (c.min(), c.max())            # this half, gate high
        over = lambda r: min(r[1], gate[1]) - max(r[0], gate[0])
        pd = max(gaps(base), key=over)       # the conducting run inside it
        span(pd[0], pd[1], base + 13, GRN, next(step))
        span(pd[1], gate[1], base + 36, MAG, next(step))
        told.append('%d..%d..%d' % (pd[0], pd[1], gate[1]))
    im.save(p)
    print('  %-26s 4 intervals marked  (%s)' % (name, ' | '.join(told)))


def patch(src, dst, boxes, size=26, color=NAVY, bg='white'):
    """Paint over a region and write replacement text centred in it.

    boxes: list of (x0, y0, x1, y1, text) in pixels. Used ONLY to rename a
    symbol that clashes with this document's notation.
    """
    im = Image.open(os.path.join(FIGS, src)).convert('RGB')
    d = ImageDraw.Draw(im)
    f = _font(size, bold=False)
    for x0, y0, x1, y1, text in boxes:
        d.rectangle([x0, y0, x1, y1], fill=bg)
        bb = d.textbbox((0, 0), text, font=f)
        d.text(((x0 + x1) / 2 - (bb[2] - bb[0]) / 2,
                (y0 + y1) / 2 - (bb[3] - bb[1]) / 2 - bb[1]),
               text, font=f, fill=color)
    im.save(os.path.join(FIGS, dst))
    print('  %-26s %d boxes repainted' % (dst, len(boxes)))


# --------------------------------------------------------------- the edits
def main():
    print('figure edits ->', FIGS)

    # 1. The three-mode waveform row is a table cell in the source, so the
    #    column headings ("At resonance" and so on) live in a header row the
    #    crop cannot include. Put them back.
    band('an_ref_modes_i_raw.png', 'an_ref_modes_i.png',
         [(0.175, 'AT resonance   fsw = fr'),
          (0.505, 'ABOVE resonance   fsw > fr'),
          (0.835, 'BELOW resonance   fsw < fr')])
    #    and bracket the four intervals of the below-resonance panel: readers
    #    kept missing that the second half freewheels too.
    mark_modes('an_ref_modes_i.png')

    # 2. The two operation circuits are captioned only "Figure 2.5" and so on
    #    in the source, which says nothing. Name what each one is.
    #    Name the switch pair as well as the half.  "first half" alone let the
    #    two figures be read as a four-step sequence (power, power, free,
    #    free), which is not the order: freewheeling follows power delivery
    #    INSIDE one half, with the same pair still on.  Infineon's own text,
    #    section 2.2: "Freewheeling operation, which can occur following the
    #    power delivery operation".  The pairs match the gate traces in
    #    an_ref_modes_i.
    band('an_ref_op_power_raw.png', 'an_ref_op_power.png',
         [(0.25, 'STEP 1   POWER DELIVERY,  S1,S4 on'),
          (0.75, 'STEP 3   POWER DELIVERY,  S2,S3 on')], h=48, size=27)
    fix_freewheel_2nd_half('an_ref_op_free_raw.png', 'an_ref_op_free_fix.png')
    band('an_ref_op_free_fix.png', 'an_ref_op_free.png',
         [(0.25, 'STEP 2   FREEWHEELING,  S1,S4 still on'),
          (0.75, 'STEP 4   FREEWHEELING,  S2,S3 still on')], h=48, size=27)

    # 3. The source writes n for the WOUND ratio. In this document n is the
    #    equivalent-model ratio and the wound one is n_T - and this is the
    #    very figure the section about that distinction refers to, so the
    #    clash has to go.
    patch('an_ref_integrated_raw.png', 'an_ref_integrated.png',
          [(403, 194, 444, 220, 'nT : 1')], size=19)

    # 4. The crop rectangle reached one line too far and took the top of the
    #    source's own caption with it - sliced through the letters and
    #    running off the bottom edge. Not this note's caption, and not
    #    legible either way.
    trim('an_ref_integrated.png')

    # 5. The same defect in the Korean guide's power-flow figure: the crop
    #    took the first line of the source's caption. There is no _raw for
    #    this one - it was a one-off crop - so the trim is in place, and
    #    figtrim finds nothing to do on a second run.
    trim('powerflow.png')

    mirror()


if __name__ == '__main__':
    main()
