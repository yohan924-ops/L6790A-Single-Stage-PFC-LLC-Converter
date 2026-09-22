# -*- coding: utf-8 -*-
"""Geometry check on the finished AN PDF - check_sm.py for the PDF side.

Reading forty pages by eye finds the things a person notices and misses the
things a person does not: a caption whose subscript lands on the line below,
a legend painted over the curve it labels, a table cell wider than its
column, a figure that walks past the right margin. Those are all measurable.

    python an_check.py            -> lists problems, exit 1 if any
    python an_check.py <file.pdf> -> check another build

What it looks at, per page:

  outside     any text or image outside the text frame
  overlap     two text blocks sharing space, or an image over text
  gap         trailing white space below the last thing on the page
  thin        an image rendered below 110 dpi - unreadable in print
  stretch     an image whose aspect ratio does not match its source file

Trailing white space is reported, not failed: a tall figure that cannot fit
in what is left of a page has to move, and that is correct behaviour. The
count is there so a change that makes it much worse is visible.
"""
import os
import sys
import warnings

warnings.filterwarnings('ignore')
import pymupdf                                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.normpath(os.path.join(
    HERE, '..', 'AN_L6790A_SingleStage_PFC_LLC_ApplicationNote_v1.3.pdf'))

# the frame an_pdf lays into: A4 with these margins
LM, RM, TM, BM = 62.0, 62.0, 108.0, 62.0
PW, PH = 595.0, 842.0
SLACK = 1.5                    # rounding in the renderer
MIN_DPI = 110.0
GAP_REPORT = 120.0


def boxes(page):
    """text blocks and image rectangles, in page coordinates"""
    tb = [(b[0], b[1], b[2], b[3], (b[4] or '').strip())
          for b in page.get_text('blocks') if (b[4] or '').strip()]
    im = []
    for xref, *_ in page.get_images(full=True):
        for r in page.get_image_rects(xref):
            im.append((r.x0, r.y0, r.x1, r.y1, xref))
    return tb, im


def area(a, b):
    """overlapping area of two rectangles"""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def main(path):
    doc = pymupdf.open(path)
    bad = []

    def say(pg, kind, msg):
        bad.append('  p%-3d %-9s %s' % (pg, kind, msg))

    gaps = []
    for page in doc:
        n = page.number + 1
        tb, im = boxes(page)
        if n == 1:
            continue                       # the cover is laid out by hand

        for x0, y0, x1, y1, txt in tb:
            if x0 < LM - SLACK or x1 > PW - RM + SLACK:
                say(n, 'outside', 'text x %.0f..%.0f outside %.0f..%.0f: %r'
                    % (x0, x1, LM, PW - RM, txt[:40]))
            # the running footer lives below the frame on purpose
            if y1 > PH - BM + SLACK and y0 < PH - 52:
                say(n, 'outside', 'text runs past the bottom: %r' % txt[:40])

        for x0, y0, x1, y1, xref in im:
            if x0 < LM - SLACK or x1 > PW - RM + SLACK:
                say(n, 'outside', 'image x %.0f..%.0f outside the frame'
                    % (x0, x1))
            w = x1 - x0
            src = doc.extract_image(xref)
            px = src['width']
            dpi = px / (w / 72.0)
            if dpi < MIN_DPI:
                say(n, 'thin', 'image %d px over %.0f pt = %.0f dpi'
                    % (px, w, dpi))
            ar_page = w / max(y1 - y0, 1e-6)
            ar_src = src['width'] / float(src['height'])
            if abs(ar_page - ar_src) / ar_src > 0.02:
                say(n, 'stretch', 'aspect %.3f drawn, %.3f in the file'
                    % (ar_page, ar_src))

        # text over text
        for i in range(len(tb)):
            for j in range(i + 1, len(tb)):
                a, b = tb[i], tb[j]
                ov = area(a, b)
                if ov <= 1.0:
                    continue
                small = min((a[2] - a[0]) * (a[3] - a[1]),
                            (b[2] - b[0]) * (b[3] - b[1]))
                if ov / max(small, 1e-6) > 0.06:
                    say(n, 'overlap', '%r over %r (%.0f pt2)'
                        % (a[4][:26], b[4][:26], ov))

        # image over text
        for r in im:
            for t in tb:
                ov = area(r, t)
                if ov > 4.0:
                    say(n, 'overlap', 'image over text %r (%.0f pt2)'
                        % (t[4][:30], ov))

        ys = [t[3] for t in tb if t[3] < PH - BM + SLACK]
        ys += [r[3] for r in im]
        if ys and n < doc.page_count:
            g = (PH - BM) - max(ys)
            if g > GAP_REPORT:
                gaps.append((n, g))

    print('%s   %d pages' % (os.path.basename(path), doc.page_count))
    if gaps:
        print('  trailing white space (reported, not failed):')
        for n, g in gaps:
            print('    p%-3d %.0f pt' % (n, g))
    if bad:
        print('\nproblems: %d' % len(bad))
        print('\n'.join(bad))
        return 1
    print('\nno geometry problems found')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT))
