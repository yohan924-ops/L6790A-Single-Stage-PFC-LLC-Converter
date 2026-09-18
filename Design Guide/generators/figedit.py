# -*- coding: utf-8 -*-
"""Small, recorded edits to a figure lifted from a reference document.

Two legitimate reasons to touch a borrowed figure, and no others:

  1. the panel it came from carried its label somewhere the crop cannot
     reach - a table header row, say - so the crop is unusable without it;
  2. the source uses a symbol for the opposite quantity to this document,
     which is worse than useless to a reader.

Anything that changes what the figure ASSERTS is off limits. Every edit made
here is listed in EDITS below, so what was changed is always readable.

    python figedit.py                 apply every edit, in order
"""
import io
import os
import sys

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
         [(0.25, 'POWER DELIVERY   1st half:  S1,S4 on'),
          (0.75, 'POWER DELIVERY   2nd half:  S2,S3 on')], h=48, size=27)
    #    The right panel is NOT labelled with a switch pair, because the
    #    source draws its arrows through S1 and S4 in reverse - the dead-time
    #    path, not freewheeling with S2,S3 on.  Traced at high zoom against
    #    the source PDF; the caption carries the finding.  Do not "fix" the
    #    arrows: this is a borrowed figure and it may not be made to say
    #    something it does not say.
    band('an_ref_op_free_raw.png', 'an_ref_op_free.png',
         [(0.25, 'FREEWHEELING   1st half:  S1,S4 still on'),
          (0.75, 'FREEWHEELING   2nd half:  see the caption')], h=48, size=27)

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
