# -*- coding: utf-8 -*-
"""Text boxes whose content is taller than the box.

None of these shapes has autofit set, so the text really does render past the
bottom edge - into whatever sits below, or off the slide. check_deck.py has been
reporting thirteen of them on slides nobody has touched since the deck was
first built.

Two remedies, in order of preference:

  1. grow the box downward, if the space under it is free. Nothing moves.
  2. otherwise drop the font a point at a time until it fits. Nothing moves
     either, and a point is not visible next to a neighbouring box.

Growing is preferred because shrinking makes one box's text smaller than its
neighbours', which reads as a mistake even when it fits.

    python fix_deck_overflow.py            check only
    python fix_deck_overflow.py --write    apply
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import deckedit as D                                                 # noqa: E402
# both modules wrap sys.stdout for UTF-8 on import. The second wrap takes the
# first one's buffer, and when the first wrapper is garbage collected it closes
# that buffer - taking the second one down with it. Hold on to it.
_keep_alive = sys.stdout
import check_deck as C                                               # noqa: E402
from pptx.util import Emu, Inches, Pt                                # noqa: E402

# check_deck wraps sys.stdout for UTF-8 when it is imported

PAD = 0.04          # keep this much clear under a grown box
FLOOR = 5.30        # the footer band - nothing may grow into it
MIN_PT = 8.0


def box(sh):
    return (Emu(sh.left).inches, Emu(sh.top).inches,
            Emu(sh.width).inches, Emu(sh.height).inches)


def room_below(slide, sh):
    """how far this shape may grow before it touches something"""
    x0, y0, w, h = box(sh)
    limit = FLOOR
    for o in slide.shapes:
        if o is sh:
            continue
        ox0, oy0, ow, oh = box(o)
        if ox0 + ow <= x0 + 0.01 or ox0 >= x0 + w - 0.01:
            continue                                   # different column
        if oy0 + oh <= y0 + h + 0.01:
            continue                                   # entirely above
        # a shape that STARTS above this box and reaches past its bottom - a
        # tall picture beside a short caption - blocks it completely. Testing
        # only for shapes that start below the box let slide 33 grow straight
        # into a 2.2 in^2 overlap with the figure next to it.
        limit = min(limit, max(y0 + h, oy0 - PAD))
    return max(0.0, limit - (y0 + h))


def font_pt(sh):
    for p in sh.text_frame.paragraphs:
        for r in p.runs:
            if r.font.size:
                return r.font.size.pt
    return None


def set_pt(sh, pt):
    for p in sh.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(pt)


def main():
    # the same test check_deck uses, tolerance included - fixing to a stricter
    # rule than the checker applies would rewrite boxes that are already fine
    write = '--write' in sys.argv
    prs = D.open_deck()
    grown = shrunk = stuck = 0
    for i, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                continue
            x0, y0, w, h = box(sh)
            if any(abs(x0 - fx) < .06 and abs(y0 - fy) < .06
                   for fx, fy in ((3.00, 0.16), (0.45, 0.78),
                                  (6.60, 5.33), (1.00, 5.33))):
                continue                                   # shell
            need = C.est_lines(sh)[1]
            if need <= h * 1.22:
                continue
            free = room_below(slide, sh)
            target = need / 1.22 + 0.02
            if free >= target - h:
                if write:
                    sh.height = Inches(target)
                grown += 1
                print('  %2d 확대  %.2f -> %.2f in  (아래 여유 %.2f)  %s'
                      % (i, h, target, free, sh.text_frame.text[:36]))
                continue
            pt = font_pt(sh)
            if pt is None:
                stuck += 1
                print('  %2d 불가  글꼴 크기 미지정  %s'
                      % (i, sh.text_frame.text[:36]))
                continue
            new, ok = pt, False
            while new > MIN_PT:
                new -= 0.5
                set_pt(sh, new)
                if C.est_lines(sh)[1] <= h * 1.22:
                    ok = True
                    break
            if not ok:
                set_pt(sh, pt)
                stuck += 1
                print('  %2d 불가  %.1f pt 까지 줄여도 안 맞는다  %s'
                      % (i, MIN_PT, sh.text_frame.text[:36]))
                continue
            if not write:
                set_pt(sh, pt)
            shrunk += 1
            print('  %2d 축소  %.1f -> %.1f pt  %s'
                  % (i, pt, new, sh.text_frame.text[:36]))
    print()
    print('확대 %d · 축소 %d · 해결 못함 %d' % (grown, shrunk, stuck))
    if write:
        D.save(prs)
    else:
        print('(--write 없이 실행 - 저장하지 않았다)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
