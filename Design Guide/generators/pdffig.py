# -*- coding: utf-8 -*-
"""Lift a labelled figure out of a reference PDF, caption included, nothing else.

Cropping by eyeballed fractions is how you end up with half a caption and the
first line of the next paragraph. This finds the CAPTION as text, then walks
upward to the nearest unrelated text block, and crops the band between them.
The caption is always inside the crop, because the caption is what anchors it.

    python pdffig.py list  onsemi          every "Figure N." it can find
    python pdffig.py show  onsemi 7        crop it, print the box, save a preview
    python pdffig.py get   onsemi 7 f_gain draw it into ../figures/f_gain.png

Always LOOK at the result before using it. The heuristic is good, not perfect:
a figure whose caption sits above the artwork, or two figures sharing a row,
will need the --box override.
"""
import io
import os
import re
import sys
import warnings

warnings.filterwarnings('ignore')
import fitz                                                          # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.normpath(os.path.join(HERE, '..', 'figures'))
REF = os.path.join(ROOT, 'Reference')

# Boxes verified by eye for the figures the application note quotes.  The
# caption anchor puts the bottom edge INSIDE the artwork on these four, so it
# cropped away the lower rail; --nocap made it worse.  Do not re-derive them.
#   onsemi 3  50 557 300 709      onsemi 5  42 115 300 317
#   onsemi 6  40 330 296 527      onsemi 8  42 234 300 452
#   onsemi 4  312 52 558 306      mps2   3  60 236 558 342
#   mps2   8  174 516 442 646
#   tosh   1.3 is not caption-anchored: get tosh 1.1 <name> --page 5
#             --box 126 452 470 732
BOOKS = {
    'onsemi': 'ONsemi LLC Converter Design guide.pdf',
    'infineon': 'Infineon LLC Converter Design guide.pdf',
    'ecce': 'ECCE_Wenbo_A Single Stage 1.65kW AC-DC LLC Converter.pdf',
    'evl': 'EVLHV101SSR50W Design Guide.pdf',
    'mps1': 'MPS_2022-aip-understanding-llc-operation-part-1-switches-and-tank_r1.0_1.pdf',
    'mps2': 'MPS_2022-understanding-llc-operation-part-2-llc-converter-design_r1.0.pdf',
    'icl': 'Infineon－Design＿guide＿Lighting＿ICs＿ACDC＿LED＿Driver＿ICL5102＿ICL5102HV－ApplicationNotes－v01＿00－EN.pdf',
    'tdk': 'TDK_trans_ac_dc-converter_srx_srv_en.pdf',
    'tosh': 'Toshiba_Power Factor Correction (PFC) Circuits AKX00080.pdf',
    'inf2': 'Infineon_Resonant LLC Converter Operation and Design.pdf',
}
# "Figure 7." (onsemi) and "Figure 3.1:" (Infineon) - the number may be dotted,
# so it has to be captured as a string, not an int
CAP = re.compile(r'^\s*Fig(?:ure)?\.?\s*\.?\s*(\d+(?:\.\d+)*)\s*([.:]?)\s', re.I)
DPI = 220


def open_book(key):
    if key not in BOOKS:
        raise SystemExit('unknown book %s  (have: %s)'
                         % (key, ' '.join(BOOKS)))
    return fitz.open(os.path.join(REF, BOOKS[key]))


def captions(doc):
    """every text block that starts like a figure caption"""
    out = []
    for pno in range(doc.page_count):
        page = doc[pno]
        for b in page.get_text('blocks'):
            x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
            m = CAP.match(text)
            if not m:
                continue
            # "Figure 4 shows an LLC converter's gain response..." is a
            # sentence, not a label. A real caption either carries the
            # delimiter or is short. Without this the MPS articles offered
            # every figure twice and the first hit was the prose one.
            rest = ' '.join(text[m.end():].split())
            if not m.group(2) and (len(' '.join(text.split())) >= PROSE
                                   or rest[:1].islower()):
                continue
            out.append(dict(page=pno, num=m.group(1),
                            rect=fitz.Rect(x0, y0, x1, y1),
                            text=' '.join(text.split())[:90]))
    return out


PROSE = 60          # a text block this long is running text, not a figure label
GAP = 34            # vertical clear band that means the figure has ended


def overlaps(a0, a1, b0, b1, frac=0.35):
    """do two horizontal spans share enough width to be the same column?

    A two-column page puts an unrelated figure a few points to the right. A
    loose test ("does it start before x = 331") let the neighbouring column in
    and dragged Figure 12 into Figure 10's crop.
    """
    ov = min(a1, b1) - max(a0, b0)
    return ov > 0 and ov >= frac * min(a1 - a0, b1 - b0)


def column_of(page, cr, near=320, wide=1.6):
    """the page band the caption belongs to

    Only prose that looks like the SAME column counts: comparable width and
    not on the far side of the page. A running header or a copyright line
    spans the full width, and letting one of those in widened the column to
    the whole page, which pulled the neighbouring figure into the crop.
    """
    lo, hi = cr.x0, cr.x1
    w = cr.x1 - cr.x0
    for b in page.get_text('blocks'):
        if not b[4].strip() or len(' '.join(b[4].split())) < PROSE:
            continue
        if (b[2] - b[0]) > wide * w:
            continue                              # header / footer / full width
        if b[3] < cr.y0 - near or b[1] > cr.y1 + near:
            continue
        if overlaps(b[0], b[2], cr.x0, cr.x1, 0.5):
            lo, hi = min(lo, b[0]), max(hi, b[2])
    return lo, hi


def art_above(page, cr, pad=9):
    """the exact box when the artwork is one embedded image over the caption

    The onsemi and Infineon guides draw their figures as vector strokes, so
    the crop has to be inferred by walking up. The MPS articles paste each
    figure as a single raster with the caption directly under it - and there
    the box is not a guess, it is the image rect. Taking the guess anyway
    cropped nothing but the caption, because MPS lets the image bbox reach a
    few points past the caption top and the walk-up rejects anything that
    overlaps the caption.
    """
    best = None
    for info in page.get_image_info():
        r = fitz.Rect(info['bbox'])
        if r.height < 30 or r.width < 40:
            continue
        if r.y0 > cr.y0 - 6 or r.y1 > cr.y1 + 4:
            continue                              # not sitting above it
        if cr.y0 - min(r.y1, cr.y0) > GAP:
            continue                              # too far - another figure
        if not overlaps(r.x0, r.x1, cr.x0, cr.x1, 0.30):
            continue
        if best is None or r.y1 > best.y1:
            best = r
    if best is None:
        return None
    # the padding must not reach into whatever brackets the figure - the
    # running-header banner above (a full-width image) or the paragraph that
    # resumes below. Both got into the first MPS crops.
    top, bot = best.y0 - pad, cr.y1 + pad
    for r in [fitz.Rect(i['bbox']) for i in page.get_image_info()] +              [fitz.Rect(b[:4]) for b in page.get_text('blocks') if b[4].strip()]:
        if r == best or r.height <= 0:
            continue
        if r.y1 <= best.y0 + 1:
            top = max(top, r.y1 + 2)
        elif r.y0 >= cr.y1 - 1:
            bot = min(bot, r.y0 - 2)
    return fitz.Rect(min(best.x0, cr.x0) - pad, top,
                     max(best.x1, cr.x1) + pad, bot)


def drop_caption(doc, cap, box, gap=4):
    """Return the box with the source's own caption cut off the bottom.

    Our document supplies its own numbered caption and the attribution, so
    carrying the original caption in as pixels gives the page two captions.
    The artwork stops just above the caption rectangle.
    """
    cr = fitz.Rect(cap['rect'])
    out = fitz.Rect(box)
    out.y1 = min(out.y1, cr.y0 - gap)
    return out


def crop_for(doc, cap, pad=9, max_h=560):
    """the band between the caption and the last piece of PROSE above it

    The trap: a figure's own labels ("Gain (M)", "fo  fs", "Below resonance")
    are text blocks too, and they sit inside the artwork. Treating them as a
    boundary crops away the whole figure and leaves the caption alone - which
    is exactly what happened first time. Only long blocks bound a figure.
    """
    page = doc[cap['page']]
    cr = fitz.Rect(cap['rect'])
    exact = art_above(page, cr, pad)
    if exact is not None:
        return exact & page.rect
    blocks = [b for b in page.get_text('blocks') if b[4].strip()]
    col0, col1 = column_of(page, cr)

    def mine(x0, x1):
        return overlaps(x0, x1, col0, col1, 0.30)

    def is_prose(b):
        return len(' '.join(b[4].split())) >= PROSE

    # the caption may wrap into short blocks just below it
    bottom = cr.y1
    for b in sorted(blocks, key=lambda b: b[1]):
        if b[1] < cr.y1 - 1 or b[1] > bottom + 12 or not mine(b[0], b[2]):
            continue
        if len(' '.join(b[4].split())) > 110:
            break                                 # the next paragraph
        bottom = max(bottom, b[3])

    # 1. a paragraph in this column is a hard ceiling - and so is ANOTHER
    #    figure's caption, which is what let Figure 5 ride along with Figure 6
    above = [b[3] for b in blocks
             if b[3] < cr.y0 - 2 and mine(b[0], b[2])
             and (is_prose(b) or CAP.match(b[4]))]
    ceiling = (max(above) + pad) if above else max(page.rect.y0,
                                                   cr.y0 - max_h)

    # 2. but the figure itself may stop well short of it. Walk up from the
    #    caption through the artwork, and stop at the first real gap - a column
    #    with no prose (a full-page-wide chart) otherwise runs max_h upward and
    #    swallows the header and the neighbouring figure, which is what
    #    happened to Figure 14.
    # the running header sits a few points above the artwork, so without this
    # the walk-up chains straight into it and takes the whole page
    hdr = page.rect.y0 + 0.075 * page.rect.height
    ftr = page.rect.y1 - 0.055 * page.rect.height

    def body(y0, y1):
        return y1 > hdr and y0 < ftr

    # Two different intruders, two different tests. A running HEADER is text,
    # so the y band catches it. A header RULE is a drawing that spans the page,
    # so width catches it - filtering rules by the y band instead clipped the
    # top tick row off Figure 14.
    wide_lim = 1.35 * (col1 - col0)

    def own(r):
        return mine(r.x0, r.x1) and r.width <= wide_lim

    pieces = []
    for b in blocks:
        if b[3] < cr.y0 + 2 and not is_prose(b) and mine(b[0], b[2]) \
                and body(b[1], b[3]):
            pieces.append((b[1], b[3]))
    for d in page.get_drawings():
        r = d['rect']
        if r.y1 < cr.y0 + 2 and r.width > 3 and own(r):
            pieces.append((r.y0, r.y1))
    for info in page.get_image_info():
        r = fitz.Rect(info['bbox'])
        if r.y1 < cr.y0 + 2 and own(r):
            pieces.append((r.y0, r.y1))

    top = cr.y0
    for y0, y1 in sorted(pieces, key=lambda p: -p[1]):
        if y1 < ceiling:
            break
        if top - y1 > GAP:                    # a clear band: figure ends here
            break
        top = min(top, y0)
    top = max(ceiling, top - pad)

    # widen to the artwork and its labels, but stay inside this column
    xs = [cr.x0, cr.x1]
    for b in blocks:
        if b[1] >= top - 4 and b[3] <= bottom + 2 and not is_prose(b) \
                and mine(b[0], b[2]):
            xs += [b[0], b[2]]
    for d in page.get_drawings():
        r = d['rect']
        if r.y0 >= top - 4 and r.y1 <= bottom + 2 and r.width > 3 and own(r):
            xs += [r.x0, r.x1]
    for info in page.get_image_info():
        r = fitz.Rect(info['bbox'])
        if r.y0 >= top - 4 and r.y1 <= bottom + 2 and own(r):
            xs += [r.x0, r.x1]

    # do not let the bottom padding reach into the paragraph that follows
    below = [b[1] for b in blocks
             if b[1] > bottom + 1 and mine(b[0], b[2])
             and (is_prose(b) or CAP.match(b[4]))]
    floor = (min(below) - 3) if below else page.rect.y1

    return fitz.Rect(max(page.rect.x0, min(xs) - pad),
                     max(page.rect.y0, top - 4),
                     min(page.rect.x1, min(max(xs) + pad, col1 + 3 * pad)),
                     min(page.rect.y1, floor, bottom + pad))


def render(doc, cap, box, path):
    page = doc[cap['page']]
    pix = page.get_pixmap(clip=box, dpi=DPI)
    pix.save(path)
    _trim(path)
    from PIL import Image
    return Image.open(path).size


def _trim(path, pad=10, thr=246):
    """Shave the uniform white margin the caption anchor leaves behind.

    The band between two text blocks is the right BAND, but the artwork
    rarely fills it edge to edge, so the crop comes out with a white gutter
    on one side and looks mis-cut next to a drawn figure.  Trimming is safe:
    it only removes pixels that are white in every row or column.
    """
    from PIL import Image
    im = Image.open(path).convert('RGB')
    a = im.load()
    w, h = im.size

    def blank_col(x):
        return all(min(a[x, y]) >= thr for y in range(0, h, 2))

    def blank_row(y):
        return all(min(a[x, y]) >= thr for x in range(0, w, 2))

    x0 = 0
    while x0 < w - 1 and blank_col(x0):
        x0 += 1
    x1 = w - 1
    while x1 > x0 and blank_col(x1):
        x1 -= 1
    y0 = 0
    while y0 < h - 1 and blank_row(y0):
        y0 += 1
    y1 = h - 1
    while y1 > y0 and blank_row(y1):
        y1 -= 1
    im.crop((max(0, x0 - pad), max(0, y0 - pad),
             min(w, x1 + 1 + pad), min(h, y1 + 1 + pad))).save(path)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    cmd, key = sys.argv[1], sys.argv[2]
    doc = open_book(key)
    caps = captions(doc)

    if cmd == 'list':
        print('%s  —  %d쪽, 캡션 %d개' % (BOOKS[key], doc.page_count, len(caps)))
        for c in caps:
            print('   p%-3d Fig %-5s %s' % (c['page'] + 1, c['num'], c['text']))
        return 0

    num = sys.argv[3]
    hits = [c for c in caps if c['num'] == num]
    if not hits:
        raise SystemExit('Figure %s 를 못 찾았다' % num)
    if len(hits) > 1:
        print('경고: Figure %s 가 %d곳에 있다 —  펶— 붉반대이 열치' % (num, len(hits)))
    cap = hits[0]

    # --box x0 y0 x1 y1  overrides the heuristic. Some pages defeat it: a
    # column with no prose at all, or a caption whose artwork is not directly
    # above it. Look at `show` first, then pin the numbers here.
    box = None
    if '--box' in sys.argv:
        i = sys.argv.index('--box')
        v = [float(x) for x in sys.argv[i + 1:i + 5]]
        box = fitz.Rect(*v)
        print('  수댙 지정 박스 사용')
    NOCAP = '--nocap' in sys.argv
    if '--page' in sys.argv:
        cap = dict(cap)
        cap['page'] = int(sys.argv[sys.argv.index('--page') + 1]) - 1
    if box is None:
        box = crop_for(doc, cap)
    if NOCAP:
        box = drop_caption(doc, cap, box)
        print('  웛본 캡션은 잘라낸다 (--nocap)')

    if cmd == 'show':
        path = os.path.join(
            os.environ.get('TEMP', '.'), 'pdffig_%s_%s.png' % (key, num))
        w, h = render(doc, cap, box, path)
        print('p%d  Fig %s' % (cap['page'] + 1, num))
        print('  캡션 : %s' % cap['text'])
        print('  박스 : x %.0f..%.0f   y %.0f..%.0f   (%.0f x %.0f pt)'
              % (box.x0, box.x1, box.y0, box.y1, box.width, box.height))
        print('  미묭보기 %d x %d px -> %s' % (w, h, path))
        return 0

    if cmd == 'get':
        name = sys.argv[4]
        path = os.path.join(OUT, name + '.png')
        w, h = render(doc, cap, box, path)
        print('  %-26s %4d x %-4d px   <- %s p%d Fig %s'
              % (name + '.png', w, h, key, cap['page'] + 1, num))
        return 0

    raise SystemExit('알 수 없는 명령서 %s' % cmd)


if __name__ == '__main__':
    raise SystemExit(main())
