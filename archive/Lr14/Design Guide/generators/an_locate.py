# -*- coding: utf-8 -*-
u"""Put every figure finding back on the printed page.

figcheck.py reports faults in the figures it draws.  That report names a
figure and quotes a label, which is everything a person needs who has the
generator source open, and nothing at all for a person holding the PDF:
the figure has a number there, not a name, and it is on one page out of
seventy.  Saying "an_pfc_idea has four labels under 6.5 pt" is not a
statement the reader can check.

So this walks the finished PDF, finds where each figure actually landed,
and reports the finding against that place.  Three outputs:

    python an_locate.py
        a table - finding, figure name, Figure N, page P, and what is
        wrong with it.  Figures the note does not use are said so.

    python an_locate.py --mark
        a copy of the PDF with every offender ringed in red and carrying
        a popup note.  Any viewer lists those annotations in a sidebar,
        so the reader clicks down the list instead of hunting.

    python an_locate.py --crops DIR
        the same places as PNGs, rendered at print size and then blown
        up, so the size of a 5 pt label is visible as a size and not as
        a number.

Figure name to page is resolved by CONTENT: the images the PDF carries
are re-encoded copies of figures/an/*.png, so the bytes differ, but the
pixels do not.  Matching on pixels needs no build, no bookkeeping, and
cannot drift out of step with either side.  The figure's NUMBER is then
read off the caption sitting under that image on that page, which is the
number the reader sees.
"""
import io
import os
import re
import sys
import warnings

warnings.filterwarnings('ignore')

import numpy as np                                            # noqa: E402
import pymupdf                                                # noqa: E402
from PIL import Image                                         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.normpath(os.path.join(
    HERE, '..', 'AN_L6790A_SingleStage_PFC_LLC_ApplicationNote_v1.3.pdf'))
FIGDIR = os.path.normpath(os.path.join(HERE, '..', 'figures', 'an'))

THUMB = (48, 48)           # what the pixel match compares
CAP_BAND = 60.0            # how far under an image its caption may sit


# ------------------------------------------------------------------ pixels
def _thumb(im):
    """a small grey signature that survives re-encoding"""
    return np.asarray(im.convert('L').resize(THUMB, Image.BILINEAR),
                      dtype=float)


def _catalogue():
    out = {}
    for f in sorted(os.listdir(FIGDIR)):
        if f.endswith('.png'):
            out[f[:-4]] = _thumb(Image.open(os.path.join(FIGDIR, f)))
    return out


def placements(path):
    """{figure name: (page number, rect, figure number)} for the whole PDF

    Every embedded image is signed and matched against the figure files.
    The equation PNGs match nothing and drop out, which is the test that
    the matching is doing anything at all.
    """
    cat = _catalogue()
    doc = pymupdf.open(path)
    out, seen = {}, {}
    for page in doc:
        n = page.number + 1
        for xref, *_ in page.get_images(full=True):
            src = doc.extract_image(xref)
            try:
                sig = _thumb(Image.open(io.BytesIO(src['image'])))
            except Exception:                                # noqa: BLE001
                continue
            best, err = None, 1e30
            for name, ref in cat.items():
                if ref.shape != sig.shape:
                    continue
                e = float(np.abs(ref - sig).mean())
                if e < err:
                    best, err = name, e
            #  A figure and its own re-encoding differ by a fraction of a
            #  grey level.  An equation against the nearest figure differs
            #  by tens.  There is no middle ground to tune.
            if best is None or err > 6.0:
                continue
            for r in page.get_image_rects(xref):
                if best in seen and seen[best][0] <= n:
                    continue
                seen[best] = (n, r)
    for name, (n, r) in seen.items():
        out[name] = (n, r, _capnum(doc[n - 1], r))
    doc.close()
    return out


def _capnum(page, rect):
    """the number the caption under this image gives it"""
    for b in page.get_text('blocks'):
        x0, y0, x1, y1, txt = b[0], b[1], b[2], b[3], (b[4] or '')
        if y0 < rect.y1 - 2 or y0 > rect.y1 + CAP_BAND:
            continue
        m = re.match(r'\s*(Figure|그림)\s*(\d+)', txt)
        if m:
            return int(m.group(2))
    return None


# ----------------------------------------------------------------- figures
def findings(names=None):
    """draw every figure through figcheck and keep the per-item records

    figcheck's own report goes to the bin here.  It is the right report
    for somebody with the source open and the wrong one for somebody
    with the PDF open, and printing both would only invite the reader to
    reconcile two lists that say the same thing in different names.
    """
    import contextlib
    import figcheck
    figcheck.ITEMS = []
    with contextlib.redirect_stdout(io.StringIO()):
        figcheck.run(names)
    return figcheck.ITEMS


# -------------------------------------------------------------------- page
def _on_page(rect, box):
    """a figure-fraction box, placed on the page the figure is printed at"""
    fx0, fy0, fx1, fy1 = box
    w, h = rect.x1 - rect.x0, rect.y1 - rect.y0
    return pymupdf.Rect(rect.x0 + fx0 * w, rect.y0 + fy0 * h,
                        rect.x0 + fx1 * w, rect.y0 + fy1 * h)


def _group(items, place):
    """findings gathered per figure, in page order"""
    g = {}
    for it in items:
        g.setdefault(it['fig'], []).append(it)
    return sorted(g.items(), key=lambda kv: place[kv[0]][0])


def _summary(kind, lst):
    worst = min(lst, key=lambda i: _pt(i['note']))
    return '%s: %d place(s), worst %s' % (kind, len(lst), worst['note'])


def _pt(note):
    m = re.match(r'([0-9.]+) pt', note)
    return float(m.group(1)) if m else 0.0


def mark(path, items, place, out):
    """a copy of the PDF with each offender ringed and annotated

    One ring per offender, because the ring is what the eye follows, and
    one sticky note per figure, because seventy-eight popups on a page
    is a sidebar nobody reads.
    """
    doc = pymupdf.open(path)
    n = 0
    for name, lst in _group(items, place):
        pg, rect, num = place[name]
        page = doc[pg - 1]
        for it in lst:
            a = page.add_rect_annot(_on_page(rect, it['box'])
                                    + (-1.5, -1.5, 1.5, 1.5))
            a.set_colors(stroke=(0.85, 0.05, 0.05))
            a.set_border(width=0.8)
            a.update()
            n += 1
        kinds = sorted({i['kind'] for i in lst})
        body = '\n'.join(_summary(k, [i for i in lst if i['kind'] == k])
                          for k in kinds)
        note = page.add_text_annot(
            pymupdf.Point(rect.x1 - 6, rect.y0 - 2),
            'Figure %s  (%s)\n%s' % (num, name, body), icon='Comment')
        note.set_info(title='figcheck')
        note.update()
    doc.save(out)
    doc.close()
    return n


def crop(path, items, place, outdir, zoom=4.0, pad=6.0):
    """each figure as a PNG, rendered at the size the page prints it and
    then magnified, with every offender ringed

    Per FIGURE, not per offender: the reader has to see the label in the
    drawing it belongs to, at the size it is actually printed, to judge
    whether it is readable.  A crop of the label alone answers a
    different question.
    """
    os.makedirs(outdir, exist_ok=True)
    doc = pymupdf.open(path)
    made = []
    for name, lst in _group(items, place):
        pg, rect, num = place[name]
        page = doc[pg - 1]
        clip = pymupdf.Rect(max(rect.x0 - pad, 0), max(rect.y0 - pad, 0),
                            min(rect.x1 + pad, page.rect.x1),
                            min(rect.y1 + pad, page.rect.y1))
        pm = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
        im = Image.open(io.BytesIO(pm.tobytes('png'))).convert('RGB')
        d = _draw(im)
        for it in lst:
            r = _on_page(rect, it['box'])
            d.rectangle([((r.x0 - clip.x0) * zoom, (r.y0 - clip.y0) * zoom),
                         ((r.x1 - clip.x0) * zoom, (r.y1 - clip.y0) * zoom)],
                        outline=(217, 13, 13), width=2)
        f = os.path.join(outdir, 'p%03d_Figure%s_%s.png'
                         % (pg, num if num else '_', name))
        im.save(f)
        made.append((f, pg, num, name, lst))
    doc.close()
    return made


def _draw(im):
    from PIL import ImageDraw
    return ImageDraw.Draw(im)


# -------------------------------------------------------------------- main
def main(argv):
    path, outdir, domark = DEFAULT, None, False
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--crops':
            outdir = argv[i + 1]
            i += 1
        elif a == '--mark':
            domark = True
        elif a.lower().endswith('.pdf'):
            path = a
        else:
            rest.append(a)
        i += 1

    place = placements(path)
    print('%s   %d figures located by pixel content'
          % (os.path.basename(path), len(place)))
    items = findings(rest or None)
    print()

    if not items:
        print('no findings')
        return 0

    used, unused = [], []
    for it in items:
        (used if it['fig'] in place else unused).append(it)

    print('%-24s %-8s %-6s %s'
          % ('figure', 'Figure', 'page', 'what to look at'))
    print('-' * 96)
    for name, lst in _group(used, place):
        pg, _, num = place[name]
        for kind in sorted({i['kind'] for i in lst}):
            sub = [i for i in lst if i['kind'] == kind]
            print('%-24s %-8s p%-5d %s' % (name, num, pg, _summary(kind, sub)))

    if unused:
        print('\nnot in this PDF - these belong to the other edition or to '
              'the training deck,\nso nothing here is wrong with the document '
              'you are holding:')
        byfig = {}
        for it in unused:
            byfig.setdefault(it['fig'], []).append(it)
        for name in sorted(byfig):
            for kind in sorted({i['kind'] for i in byfig[name]}):
                sub = [i for i in byfig[name] if i['kind'] == kind]
                print('  %-24s %s' % (name, _summary(kind, sub)))

    if domark:
        out = path[:-4] + '_marked.pdf'
        n = mark(path, used, place, out)
        print('\n%d place(s) ringed in %s' % (n, os.path.basename(out)))
    if outdir:
        made = crop(path, used, place, outdir)
        print('\n%d crop(s) in %s' % (len(made), outdir))
        for f, pg, num, name, lst in made:
            print('  %-46s %d place(s) ringed' % (os.path.basename(f),
                                                  len(lst)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
