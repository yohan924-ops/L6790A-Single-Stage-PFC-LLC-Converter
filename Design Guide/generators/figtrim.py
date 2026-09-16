# -*- coding: utf-8 -*-
"""Find - and cut - the sliver of text a crop left at the bottom of a figure.

A figure lifted out of a reference PDF is cut by a rectangle, and the
rectangle is set from a caption's position. When it reaches a little too
far it takes the first line of the paragraph below with it, and what lands
in the note is the drawing, a band of white, and the tops of some letters
running off the edge of the image.

That has a signature no real drawing has: ink that touches the very bottom
edge, is only a few rows tall, and is separated from everything above it by
a wide band of pure white. A panel of a multi-panel figure is never cut off
at the image boundary; a caption fragment always is.

    python figtrim.py            report every figure that has one
    python figtrim.py --fix      cut them, keeping a small white margin
"""
import glob
import io
import os
import sys

from PIL import Image

# only when run directly: re-wrapping at import time closes the wrapper the
# importing module had already put there, and its next print() fails
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.normpath(os.path.join(HERE, '..', 'figures'))

GAP_MIN = 25        # rows of white that must separate the sliver
TAIL_MAX = 60       # a sliver is thin; a real panel is not
MARGIN = 12         # white left under the drawing after the cut


def rows(path):
    im = Image.open(path).convert('L')
    w, h = im.size
    px = im.load()
    return im, w, h, [sum(1 for x in range(w) if px[x, y] < 128)
                      for y in range(h)]


def sliver(r, h):
    """(cut_at, gap, tail) if the bottom of this image is an orphan band"""
    if not r or r[h - 1] == 0:
        return None                      # nothing touching the bottom edge
    y = h - 1
    while y >= 0 and r[y] > 0:
        y -= 1
    tail = h - 1 - y
    if tail > TAIL_MAX:
        return None                      # too tall to be a caption fragment
    gap_end = y
    while y >= 0 and r[y] == 0:
        y -= 1
    gap = gap_end - y
    if gap < GAP_MIN or y < 0:
        return None                      # not separated from the drawing
    return y, gap, tail


def main(fix=False):
    bad = 0
    for p in sorted(glob.glob(os.path.join(FIGS, '*.png'))
                    + glob.glob(os.path.join(FIGS, 'an', '*.png'))):
        if p.endswith('_raw.png'):
            continue
        try:
            im, w, h, r = rows(p)
        except Exception as e:                                 # noqa: BLE001
            print('  %-30s unreadable: %s' % (os.path.basename(p), e))
            continue
        s = sliver(r, h)
        if not s:
            continue
        bad += 1
        last, gap, tail = s
        keep = min(h, last + 1 + MARGIN)
        print('  %-30s %dx%d   drawing ends at y=%d, %d blank rows, then %d '
              'rows of ink cut off at the edge%s'
              % (os.path.relpath(p, FIGS), w, h, last, gap, tail,
                 '  -> cut to %d' % keep if fix else ''))
        if fix:
            im2 = Image.open(p)
            im2.crop((0, 0, w, keep)).save(p)
    print('  figures with a cropped-in text sliver: %d' % bad)
    return bad


if __name__ == '__main__':
    raise SystemExit(1 if main('--fix' in sys.argv) and '--fix' not in sys.argv
                     else 0)
