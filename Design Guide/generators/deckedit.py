# -*- coding: utf-8 -*-
"""Edit the training deck in place: swap figures, add slides, keep the styling.

The deck was built by deck2.js, which needs node - and node is not installed on
this machine, so it cannot be regenerated. python-pptx is, so the deck is edited
instead. That is also safer: the errata slide added later by hand survives.

Everything here works by CLONING an existing slide's shell. The title, the navy
kicker bar, the logo and the footer are ordinary shapes with hand-set geometry,
not placeholders (the deck has exactly one empty layout), so copying their XML
is the only way to get a new slide that matches.

    import deckedit as D
    prs = D.open_deck()
    s = D.clone(prs, 12, after=12)        # new slide based on slide 12
    D.set_title(s, 'Three operating regions')
    D.set_kicker(s, 'only the middle one is where you want to be')
    D.clear_content(s)                    # drop everything but the shell
    D.picture(s, 'f04_three_regions', 0.55, 1.20, w=5.6)
    D.text(s, 'why it matters ...', 6.35, 1.30, 3.2, 2.0)
    D.source(s, 'Figure: our own, from l6790.py')
    D.save(prs)
"""
import copy
import io
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
FIGS = os.path.normpath(os.path.join(HERE, '..', 'figures'))
TRAIN = os.path.join(ROOT, 'Training Material')

NAVY = RGBColor(0x03, 0x23, 0x4B)
YEL = RGBColor(0xFF, 0xD2, 0x00)
MAG = RGBColor(0xE6, 0x00, 0x7E)
GREY = RGBColor(0x46, 0x46, 0x50)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = 'Arial'

# the shell geometry, read off the existing slides
TITLE_BOX = (3.00, 0.16, 6.75, 0.50)
KICK_BOX = (0.45, 0.78, 9.10, 0.30)
FOOT_BOX = (6.60, 5.33, 3.15, 0.22)
SRC_BOX = (1.00, 5.33, 5.40, 0.22)
LOGO_BOX = (0.30, 5.00, 0.55, 0.42)


def deck_path():
    return os.path.join(TRAIN, [f for f in os.listdir(TRAIN)
                                if f.lower().endswith('.pptx')][0])


def open_deck(path=None):
    return Presentation(path or deck_path())


def save(prs, path=None):
    p = path or deck_path()
    prs.save(p)
    print('저장 %s   슬라이드 %d장' % (os.path.basename(p), len(prs.slides)))


# ------------------------------------------------------------------ geometry
def _box(sh):
    return (sh.left / 914400.0, sh.top / 914400.0,
            sh.width / 914400.0, sh.height / 914400.0)


def _near(sh, box, tol=0.06):
    b = _box(sh)
    return all(abs(b[i] - box[i]) < tol for i in range(4))


def shell_shapes(slide):
    """the four furniture shapes: logo, title, kicker, footer"""
    out = {}
    for sh in slide.shapes:
        for name, box in (('logo', LOGO_BOX), ('title', TITLE_BOX),
                          ('kicker', KICK_BOX), ('foot', FOOT_BOX),
                          ('source', SRC_BOX)):
            if _near(sh, box):
                out[name] = sh
    return out


# ------------------------------------------------------------------- slide moves
def clone(prs, src_no, after=None):
    """a new slide carrying src's shapes, placed after slide `after` (1-based)"""
    src = prs.slides[src_no - 1]
    dst = prs.slides.add_slide(prs.slide_layouts[0])
    for sh in src.shapes:
        dst.shapes._spTree.append(copy.deepcopy(sh._element))
    if after is not None:
        move_to(prs, len(prs.slides), after + 1)
    return dst


def move_to(prs, frm, to):
    """move slide `frm` (1-based) so it becomes slide `to` (1-based)"""
    lst = prs.slides._sldIdLst
    ids = list(lst)
    el = ids[frm - 1]
    lst.remove(el)
    lst.insert(to - 1, el)


def drop(prs, no):
    lst = prs.slides._sldIdLst
    el = list(lst)[no - 1]
    rId = el.get('{http://schemas.openxmlformats.org/officeDocument/'
                 '2006/relationships}id')
    prs.part.drop_rel(rId)
    lst.remove(el)


# -------------------------------------------------------------------- content
KEEP_BOXES = {'logo': LOGO_BOX, 'title': TITLE_BOX, 'kicker': KICK_BOX,
              'foot': FOOT_BOX, 'source': SRC_BOX}


def clear_content(slide, keep=('logo', 'title', 'kicker', 'foot')):
    """remove everything that is not furniture

    Decide by GEOMETRY, one pass. An earlier version collected the keepers as
    id(shape._element) and compared ids on a second pass - but lxml hands out a
    fresh proxy each time an element is reached, so the ids did not match and
    the title was deleted along with the content.
    """
    boxes = [KEEP_BOXES[k] for k in keep if k in KEEP_BOXES]
    for sh in list(slide.shapes):
        if not any(_near(sh, b) for b in boxes):
            sh._element.getparent().remove(sh._element)


def _set_text(shape, text, size=None, bold=None, color=None, align=None):
    tf = shape.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = text
    r.font.name = FONT
    if size:
        r.font.size = Pt(size)
    if bold is not None:
        r.font.bold = bold
    if color is not None:
        r.font.color.rgb = color
    if align is not None:
        p.alignment = align
    return shape


def set_title(slide, text):
    sh = shell_shapes(slide).get('title')
    if sh is None:
        raise KeyError('이 슬라이드에 제목 상자가 없다')
    return _set_text(sh, text, 20, True, NAVY, PP_ALIGN.RIGHT)


def set_kicker(slide, text, donor=None):
    """set the navy kicker bar, creating it if this slide never had one

    Not every content slide carries one - the rules slide does not - so a
    caller that wants a kicker there has to be given the shape, not an error.
    It is cloned from a slide that has one so the fill and font match exactly.
    """
    sh = shell_shapes(slide).get('kicker')
    if sh is None:
        if donor is None:
            raise KeyError('이 슬라이드에 키커 바가 앆다 (donor 를 주면 뻜듀다)')
        src = shell_shapes(donor).get('kicker')
        if src is None:
            raise KeyError('donor 슼라퍴드에댄 키커 바가 앆다')
        slide.shapes._spTree.append(copy.deepcopy(src._element))
        sh = shell_shapes(slide)['kicker']
    return _set_text(sh, text, 12, True, WHITE, PP_ALIGN.LEFT)


def picture(slide, name, x, y, w=None, h=None):
    """place ../figures/<name>.png, preserving aspect from whichever of w/h given"""
    p = os.path.join(FIGS, name if name.endswith('.png') else name + '.png')
    if not os.path.exists(p):
        raise SystemExit('그림이 없다: %s' % p)
    from PIL import Image
    iw, ih = Image.open(p).size
    if w and not h:
        h = w * ih / iw
    elif h and not w:
        w = h * iw / ih
    elif not w and not h:
        raise ValueError('w 나 h 중 하나늌 필요하다')
    return slide.shapes.add_picture(p, Inches(x), Inches(y),
                                    Inches(w), Inches(h))


def fit(slide, name, bx, by, bw, bh):
    """centre the picture inside a box, preserving aspect"""
    from PIL import Image
    p = os.path.join(FIGS, name if name.endswith('.png') else name + '.png')
    iw, ih = Image.open(p).size
    r, br = iw / ih, bw / bh
    if r > br:
        w, h = bw, bw / r
    else:
        h, w = bh, bh * r
    return slide.shapes.add_picture(p, Inches(bx + (bw - w) / 2),
                                    Inches(by + (bh - h) / 2),
                                    Inches(w), Inches(h))


def text(slide, body, x, y, w, h, size=11, color=NAVY, bold=False,
         align=PP_ALIGN.LEFT, space=6):
    """a plain text block; body may contain newlines"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.04)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    for i, line in enumerate(body.split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space)
        r = p.add_run()
        r.text = line
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
    return tb


def card(slide, x, y, w, h, head, body, colour=NAVY, size=10.5):
    """a titled box, the deck's usual way of putting a point beside a figure"""
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.background()
    sh.line.color.rgb = colour
    sh.line.width = Pt(1.25)
    sh.adjustments[0] = 0.06
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Inches(0.10)
    tf.margin_top = Inches(0.07)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = head
    r.font.name, r.font.size, r.font.bold = FONT, Pt(size + 0.5), True
    r.font.color.rgb = colour
    for line in body.split('\n'):
        q = tf.add_paragraph()
        q.space_before = Pt(3)
        rr = q.add_run()
        rr.text = line
        rr.font.name, rr.font.size = FONT, Pt(size)
        rr.font.color.rgb = NAVY
    return sh


def source(slide, txt):
    """the small grey credit line at the bottom left"""
    sh = shell_shapes(slide).get('source')
    if sh is not None:
        _set_text(sh, txt, 7, False, RGBColor(0xBB, 0xBB, 0xBB), PP_ALIGN.LEFT)
        sh.text_frame.paragraphs[0].runs[0].font.italic = True
        return sh
    tb = text(slide, txt, SRC_BOX[0], SRC_BOX[1], SRC_BOX[2], SRC_BOX[3],
              size=7, color=RGBColor(0xBB, 0xBB, 0xBB))
    tb.text_frame.paragraphs[0].runs[0].font.italic = True
    return tb


def titles(prs):
    out = []
    for i, s in enumerate(prs.slides, 1):
        t = shell_shapes(s).get('title')
        out.append((i, t.text_frame.text if t is not None else '(no title)'))
    return out


if __name__ == '__main__':
    prs = open_deck()
    for i, t in titles(prs):
        print('  %2d  %s' % (i, t[:72]))
