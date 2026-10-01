# -*- coding: utf-8 -*-
"""ZedGraph panes for SMath sheets - the TI pane catalogue and one call to
build one.

SMath cannot draw a logarithmic axis, and its native plot region has no
legend, no title and no way to put several named curves in one frame. The
ZedGraph region does all of that, but it has no editor here: a pane is a
BinaryFormatter blob, so the only way to get one is to take a pane that
already exists and rewrite it. The TI application note sheet in
Reference/Smath Bode Plot Example ships nine, and between them they cover
one to five curves:

    curves   transfer pane            impedance pane
             log x, LINEAR y          log x, log y
      1      index 1                  index 0
      2      index 3                  index 2
      3      index 5                  index 4
      4      index 7                  index 6
      5      -                        index 8

The log/linear split is a property of the pane and cannot be changed one
axis at a time - see the note in zedpane.py. So a log x with a linear y
means a transfer pane, and those stop at four curves; five curves means
to_linear and a linear x as well.

What a caller has to supply is a window, a title, axis names and one legend
entry per curve. Everything else - tick steps that suit the range, a number
format that does not round 0.63 to 1, and a visible line width - is set
here, because every one of those was wrong in the panes as shipped.

The plot input is sys(p1, ..., pN, N, 1), each pN a two-column matrix. Build
those the way the TI sheet does, with a range variable and el() assignments
fed to eval(augment(vectorize(x), vectorize(y))). A matrix filled inside a
for() program block does not draw.
"""
import base64
import io
import math
import os
import re
import struct

import harvest_pane as HP
import zedpane as Z

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
REF = os.path.join(ROOT, 'Reference', 'Smath Bode Plot Example',
                   'SMPS_Input_Filter_Design_TI_APP_Note.sm')

VEC = ('eval', 'augment', 'vectorize')   # what a plot matrix needs
LINEW = 2.0             # curves and frames. The grid is MinorGrid, untouched
NUMFMT = '0.###'        # the panes ship with "f0", which rounds 0.63 to 1

# Panes this project owns, grown by SMath from a smaller one and lifted
# back out with harvest_pane.py: (curves, kind) -> (file, xrange, yrange).
# SMath makes a pane's curve list match the input, so a four-curve pane fed
# eight matrices becomes an eight-curve pane the moment the sheet is saved.
# Feeding extra matrices works without this, but the extra curves come out
# in a default colour, one pixel wide and with no legend entry - which is
# the whole reason to keep the grown pane.
LOCAL = {
    # ranges are those of the STORED pane, which make() converts from. Change
    # them whenever the pane is re-harvested from a sheet with a different
    # window - _find_pair fails loudly if they are wrong, which is how this
    # was caught after the pane was harvested a second time.
    (8, 'transfer'): ('transfer8', (0.1, 10.0), (0.0, 4.0)),
    # grown from transfer8: it was fed nine matrices and SMath rewrote
    # the pane on save. Its stored window is the frequency frame's, so
    # that is what make() converts from.
    (9, 'transfer'): ('transfer9', (0.0, 3.2), (0.0, 350.0)),
    # grown again, from transfer9, for the eleven traces of the
    # frequency frame: six line conditions and five limits
    (11, 'transfer'): ('transfer11', (0.0, 3.2), (0.0, 350.0)),
}
STORE = os.path.join(HERE, 'panes')

# (curves, kind) -> index in the TI sheet
CATALOG = {
    (1, 'transfer'): 1, (2, 'transfer'): 3,
    (3, 'transfer'): 5, (4, 'transfer'): 7,
    (1, 'impedance'): 0, (2, 'impedance'): 2, (3, 'impedance'): 4,
    (4, 'impedance'): 6, (5, 'impedance'): 8,
}

ZED_ASM = ('      <assembly name="ZedGraph Region (ZedGraph)" '
           'version="0.1.7806.5613" '
           'guid="b0e7602f-c9d4-4e6c-b6f1-087e4c6e8915" />\n')

_CACHE = []


def _panes():
    if _CACHE:
        return _CACHE
    s = io.open(REF, encoding='utf-8', errors='replace').read()
    got = re.findall(r'<zedgraph([^>]*)>(.*?)</zedgraph>', s, re.S)
    if len(got) < 9:
        raise SystemExit('%s has %d ZedGraph panes, expected 9'
                         % (os.path.basename(REF), len(got)))
    for attr, body in got:
        raw = base64.b64decode(re.search(
            r'<data encoding="base64">([^<]*)</data>', body, re.S
        ).group(1).strip())
        m = re.search(r'args="(\d+)">sys<', body)
        _CACHE.append({
            'w': int(re.search(r'width="(\d+)"', attr).group(1)),
            'h': int(re.search(r'height="(\d+)"', attr).group(1)),
            'raw': raw,
            'n': (int(m.group(1)) - 2) if m else 1,
        })
    return _CACHE


def _strings(raw):
    """every BinaryObjectString in the blob, in stream order"""
    out, i = [], 0
    while True:
        i = raw.find(b'\x06', i)
        if i < 0:
            return out
        ln = raw[i + 5] if i + 5 < len(raw) else 0
        if 0 < ln < 128 and i + 6 + ln <= len(raw):
            try:
                t = raw[i + 6:i + 6 + ln].decode('utf-8')
            except UnicodeDecodeError:
                t = None
            if t and all(32 <= ord(c) < 127 for c in t) \
                    and not t.startswith(('ZedGraph', 'System', 'mscorlib')):
                out.append(t)
        i += 1


def shipped(index):
    """(title, xtitle, ytitle, [legend, ...]) as the TI pane carries them"""
    st = _strings(_panes()[index]['raw'])
    try:
        k = st.index('Phase Angle (deg)')
    except ValueError:
        raise SystemExit('pane %d has no phase-axis title; the layout of the '
                         'TI panes is not what this module assumes' % index)
    return st[0], st[2], st[5], st[k + 2:]


# ZedGraph's default title is 16 pt against 14 pt axis titles and 12 pt
# legend entries, and these titles are sentences - at 16 they were the
# loudest thing on the page and wrapped to two lines. 12 puts them level
# with the legend, which is where a caption belongs.
TITLESIZE = 12.0


def make(curves, kind, title, xtitle, ytitle, legends, xwin, ywin,
         xlog=True, ylog=None, logstep=1.0, ylogstep=1.0,
         ysteps=None, xsteps=None, big=False, colors=None, size=None,
         widths=None, legendsize=None, yauto=False):
    """Rewrite a pane into ours. Returns (base64, width, height).

    `curves` is how many matrices will be FED. If no pane holds exactly
    that many, a larger one is used and the surplus curves are left
    unlabelled - SMath prunes them on the first recalculation. `big` forces
    that path even when a TI pane would fit, because every TI pane is
    552x317 and some figures need the room.

    xwin and ywin are the wanted windows. xlog keeps the pane's logarithmic
    x - only a transfer pane can then still have a linear y - and logstep is
    the major tick spacing on it, counted in DECADES (0.1 puts seven labels
    across two thirds of a decade; 1 labels 0.1, 1, 10).

    size is (width, height) in sheet pixels. It rewrites the pane's own
    rect AND is returned as the region size, because those two have to
    agree - see zedpane.set_size.

    colors names one KnownColor per curve (zedpane.KNOWN). Left out, the
    pane keeps the palette it was harvested with - and that palette has six
    entries, so a seventh curve comes back the same blue as the first.

    widths gives one pen width per curve, for a frame that carries two
    families - what the tank CAN do against what regulation DEMANDS - and
    wants them told apart by weight as well as by colour. Left out, every
    curve gets LINEW.

    legendsize overrides the legend font. A frame with eleven entries needs
    a smaller one than a frame with four.

    yauto hands the y range and both tick steps to ZedGraph, so the frame
    follows the data instead of a window fixed at build time. Use it only
    where the data is BOUNDED: on the gain frames M.OL has a pole inside the
    plotted range, and auto-scaling to that would flatten everything else
    into the axis.

    ysteps and xsteps override the automatic (major, minor) choice. The
    automatic one rounds a step near a tenth of the range, which lands on an
    odd number whenever the range is not a round multiple of it: -100..100
    wants 25 and reads -100, -75, -50, where 20 reads -100, -80, -60.
    """
    if len(legends) != curves:
        raise ValueError('%d curves but %d legend entries'
                         % (curves, len(legends)))
    if colors is not None and len(colors) != curves:
        raise ValueError('%d curves but %d colours' % (curves, len(colors)))
    curves_fed = curves
    for t in (title, xtitle, ytitle) + tuple(legends):
        _no_values(t)
    key = (curves, kind)
    if big:
        # ignore the TI panes: they are all 552x317, and a figure that has
        # to be read against a scope trace wants the room
        if key not in LOCAL:
            key = None
    if key is None or (key not in CATALOG and key not in LOCAL):
        # a bigger pane will do: SMath prunes the curves it is not fed. Take
        # the smallest one that fits, and leave the surplus unlabelled so
        # they are out of the legend even before the first recalculation.
        bigger = sorted(k for k in LOCAL if k[1] == kind and k[0] > curves)
        if not bigger:
            raise ValueError('no pane with %d curves and a %s layout, and '
                             'none bigger to prune - see the tables in this '
                             'module' % (curves, kind))
        key = bigger[0]
        legends = list(legends) + [''] * (key[0] - curves)
        if colors is not None:
            # the surplus curves are never fed, so they never draw; they
            # still need a colour each for the count to match
            colors = list(colors) + ['Black'] * (key[0] - curves)
    if ylog is None:
        ylog = (kind == 'impedance') and xlog
    if kind == 'transfer' and ylog:
        raise ValueError('a transfer pane has a LINEAR y and it cannot be made '
                         'logarithmic on its own - x, x2 and y2 would go with '
                         'it (zedpane)')
    if kind == 'impedance' and xlog != ylog:
        raise ValueError('an impedance pane has x, x2 and y in ONE LogScale '
                         'class record, so they convert together: xlog and '
                         'ylog must match (zedpane)')
    if key in LOCAL:
        name, xr, yr = LOCAL[key]
        raw, w, h = _local(name)
        t0, x0, y0, leg0 = shipped_raw(raw)
    else:
        p = _panes()[CATALOG[key]]
        raw, w, h = p['raw'], p['w'], p['h']
        t0, x0, y0, leg0 = shipped(CATALOG[key])
        if len(leg0) != curves:
            raise SystemExit('pane %d ships %d legend entries for %d curves'
                             % (CATALOG[key], len(leg0), curves))
        xr = (10.0, 1000000.0) if kind == 'transfer' else (10.0, 100000.0)
        yr = (-60.0, 20.0) if kind == 'transfer' else \
             ((1.0, 100.0) if curves == 1 else (0.01, 100.0))

    if not xlog:
        raw, _ = Z.to_linear(raw)
    raw = (_logfit(raw, xr, xwin, logstep) if xlog
           else _fit(raw, xr, xwin, xsteps))
    raw = (_logfit(raw, yr, ywin, ylogstep) if ylog
           else _fit(raw, yr, ywin, ysteps))

    raw = Z.set_text(raw, t0, title)
    raw = Z.set_text(raw, x0, xtitle)
    raw = Z.set_text(raw, y0, ytitle)
    if key not in LOCAL:
        raw = Z.set_text(raw, 'Phase Angle (deg)', 'unused')
    if key in LOCAL:
        # every curve owns a Label here, including the ones SMath added, so
        # the legend is set through the Label records rather than by
        # rewriting shipped strings that only exist for some of them
        raw = HP.set_curve_labels(raw, list(legends))
    else:
        for old, new in zip(leg0, legends):
            raw = Z.set_text(raw, old, new)

    if colors is not None:
        # after every string rewrite: the label offsets move when a title or
        # a legend entry changes length
        raw = Z.set_curve_colors(
            raw, [p for p, _k, _t in HP.curve_labels(raw)], list(colors))

    if widths is not None:
        if len(widths) != curves:
            raise ValueError('%d curves but %d widths' % (curves, len(widths)))
        offs = [p for p, _k, _t in HP.curve_labels(raw)]
        # the pane may carry more curves than are fed; the surplus keeps the
        # default pen, the same one it already has
        raw = Z.set_curve_widths(
            raw, offs, list(widths) + [LINEW] * (len(offs) - len(widths)))

    raw, _ = Z.set_format(raw, xwin, NUMFMT)
    raw, _ = Z.set_format(raw, ywin, NUMFMT)
    raw, _ = Z.set_line_width(raw, LINEW)
    # the legend is the pane's other 12 pt FontSpec, so it has to be set
    # while 12.0 is still unique - before the title comes down to it
    if legendsize is not None:
        raw = Z.set_legend_font_size(raw, legendsize)
    raw = Z.set_title_font_size(raw, TITLESIZE)
    if yauto:
        raw = Z.set_auto(raw, ywin, True)
    if size is not None:
        raw = Z.set_size(raw, (w, h), size)
        w, h = size
    return base64.b64encode(raw).decode(), w, h


_VALUE = re.compile(r'\d+\.\d')


def _no_values(t):
    """Refuse a computed number in pane text.

    A pane is a static blob. The builder fills it from the sheet, so it is
    right the moment it is written - and then someone edits a yellow cell,
    presses F9, and the curves move while the title still reads 17.57 Hz.
    Nothing warns them: the number looks like part of the picture.

    This is the same rule the BOM already lives under. Say what a trace IS,
    and name the variable that sets it; the value belongs in a row above the
    frame, where F9 reaches it. It also makes the panes worth reusing - a
    title carrying this project's crossover is no use to the next one.
    """
    if _VALUE.search(t):
        raise ValueError(
            'pane text carries what looks like a computed value: %r. A pane '
            'is static and F9 does not reach it, so name the variable '
            'instead of printing its value.' % t)


def _local(name):
    """a pane kept in panes/ - first line is width and height"""
    p = os.path.join(STORE, name + '.b64')
    if not os.path.isfile(p):
        raise SystemExit('%s is missing. It is produced by harvest_pane.py '
                         'from a sheet SMath has saved; see that module.' % p)
    head, body = io.open(p, encoding='ascii').read().split('\n', 1)
    w, h = (int(v) for v in head.split())
    return base64.b64decode(body.strip()), w, h


def shipped_raw(raw):
    """(title, xtitle, ytitle, [curve label, ...]) of a pane already loaded

    A harvested pane has been through make() once already, so its unused
    phase-axis title is 'unused' rather than the name the TI panes carry.
    The strings are still in the same order: title, the font name, the x
    title, two number formats, then the y title.
    """
    st = _strings(raw)
    return st[0], st[2], st[5], [x[2] for x in HP.curve_labels(raw)
                                 if x[1] == 'string']


def _logfit(raw, old, new, step):
    """A log axis: range, step in DECADES, and where it starts counting.

    baseTic left automatic is ceil(log10(min)) - the next whole decade at or
    above the minimum. With a whole-decade step that is right; with a
    fractional one it is not, and an axis running 0.5 to 2.5 starts its
    ticks at 1 and leaves everything below unlabelled.
    """
    raw = Z.set_range(raw, old, new)
    raw = Z.set_steps(raw, new, step, 1.0)
    return Z.set_base_tic(raw, new, math.log10(new[0]))


def _fit(raw, old, new, steps=None):
    raw = Z.set_range(raw, old, new)
    mj, mn = steps if steps else Z.nice_steps(*new)
    return Z.set_steps(raw, new, mj, mn)


def sys_input(names, indent='        '):
    """sys(p1, ..., pN, N, 1) - how a multi-curve pane is fed"""
    if len(names) == 1:
        return '%s<e type="operand">%s</e>' % (indent, names[0])
    out = ['%s<e type="operand">%s</e>' % (indent, n) for n in names]
    out.append('%s<e type="operand">%d</e>' % (indent, len(names)))
    out.append('%s<e type="operand">1</e>' % indent)
    out.append('%s<e type="function" preserve="true" args="%d">sys</e>'
               % (indent, len(names) + 2))
    return '\n'.join(out)


# SMath prints the plot input under the frame - one line per matrix, in a
# brace - and draws it OUTSIDE the region, so nothing in the file describes
# it and check_sm cannot see it. These reserve for it.
#
# Measured on the rendered PDF: the first name sits about 12 px below the
# frame and the rows step about 19. That alone would be 40 and 22; these are
# half again as much, because the measurement is of ONE rendering and the
# thing being measured is not in the file - nothing downstream can catch it
# if it is short, and a gap that is too big only costs paper. The first
# values, 24 and 15, were fitted when a pane took one or two matrices: at
# four the section 16.6 note landed on the last entry of the brace, and at
# eight the list ran through the next section heading.
# Measured on the printed page, not guessed: SMath draws the input names
# one per line, 23.1 px apart, starting a little under the frame.
# The list is now SUPPRESSED - emit() writes showInputData="false" on the
# region, which is the attribute SMath itself sets when you untick "show
# input data" on a plot. Nothing is drawn below the frame any more, so
# nothing has to be reserved for it, and every pane gets that height back:
# an eleven-curve frame was giving up 300 px to a list of matrix names that
# said Tf.1 .. Tf.6, Th.o .. Th.s and told a reader nothing the legend does
# not say better.
CAPTION = 0
PER_CURVE = 0
# A pane now starts at the top of a page (emit pads to the boundary), so
# these are no longer holding a frame away from a page break - they are only
# the air a reader wants around a figure.
LEAD = 20               # white above the frame
TRAIL = 20              # white below the name list

# LEAD and TRAIL are not measurements of anything - they are room. A pane
# that lands across a page break gets a shaded band from SMath and the
# figure is read in two halves; the fix is space, and space costs paper and
# nothing else. Together with CAPTION and PER_CURVE they put about three
# times the previous band around every frame.


# Sheet.gap in smsheet - emit() adds it after the figure, like every other
# emitter, and it has to come out of the budget or the block is a hair too
# tall for its page.
GAP = 8


def fit(curves, page_h=None, lead=True, top=None, bot=None):
    """the tallest a pane with this many curves can be on one page

    SMath draws the input matrix names below the frame, one per line, and
    they belong to the pane as much as the frame does - a pane that fits but
    whose names spill over still crosses the break. So the budget is the
    page less everything else the figure needs. page_h is the PRINTABLE
    height, not the paper - see Sheet.PAGE_CONTENT.

    Every term matters, including the trailing gap. Leaving GAP out made the
    block exactly one page tall and then advanced eight pixels past the
    boundary, so the next region started a page it could not fit on and was
    pushed off it - and the page in between came out BLANK. Five of them.
    """
    from smsheet import Sheet
    # measured on L6790A_ruler.sm; the old 1117 default was reasoned from
    # the paper size and was three pixels a page wrong
    page_h = Sheet.PAGE_CONTENT if page_h is None else page_h
    top = Sheet.SAFE_TOP if top is None else top
    bot = Sheet.SAFE_BOT if bot is None else bot
    return (page_h - top - bot - (LEAD if lead else 0) - 8
            - CAPTION - PER_CURVE * (curves - 1) - TRAIL - GAP)


# How much of a frame is worth keeping rather than moving to a fresh page.
#
# 0.6 let a frame shrink to about 600 px, which kept the page count down and
# produced panes of three different heights in one family - the user
# enlarged two of them by hand rather than read them at that size. 0.8
# refuses anything below about 760, which in this sheet means every large
# frame comes out at the full 952 and they are all the same height. It costs
# two pages. Frames are the reason this document exists, so they get the
# room and the paper pays.
KEEP = 0.8


def _resize(blob, w, h, new_h):
    """shrink a pane to fit the room left, region attribute and rect together

    Both have to move or the pane comes back as a default one - see
    zedpane.set_size, which is where that was measured.
    """
    raw = base64.b64decode(blob)
    raw = Z.set_size(raw, (w, h), (w, int(new_h)))
    return base64.b64encode(raw).decode(), int(new_h)


def emit(S, names, blob, w, h, x=None, advance=True, reserve=None,
         lead=True):
    """Place a pane. Reserves room for the input names SMath draws below it.

    reserve overrides that count, for a pane placed beside a taller one: two
    panes on one row advance once, by whichever has the longer input. lead
    is the white above the frame, and the SECOND pane of a row must not ask
    for it again.
    """
    # A pane must not cross a page break - SMath draws a grey band through
    # whatever does, and the figure reads as two broken pictures. But
    # pushing it to the next page leaves the rest of this one empty, and a
    # frame is the one thing on the page that can be made smaller without
    # losing anything. So it gives way first, and only moves when giving
    # way would leave it too small to read.
    below = 8 + CAPTION + PER_CURVE * (
        (len(names) if reserve is None else reserve) - 1) + TRAIL
    # the same coordinate smsheet breaks pages in: absolute y less what
    # is folded away above it, against the printable height
    pos = (S.vy() - S.PAGE_ORIGIN) % S.PAGE_CONTENT
    if lead and pos < S.SAFE_TOP:
        S.y += S.SAFE_TOP - pos
        pos = S.SAFE_TOP
    room = S.PAGE_CONTENT - S.SAFE_BOT - pos - (LEAD if lead else 0)
    if h + below > room:
        give = room - below
        if give >= KEEP * h:
            blob, h = _resize(blob, w, h, give)
        elif lead:
            # start the next page, inside its top band
            S.y += room + S.SAFE_BOT + S.SAFE_TOP
        elif give > 0:
            # the second pane of a row cannot move on its own - the first one
            # has already settled which page they are both on - so it takes
            # whatever height is left rather than crossing the break
            blob, h = _resize(blob, w, h, give)
    if lead:
        S.y += LEAD
    body = ('    <zedgraph width="%d" height="%d">\n'
            '      <data encoding="base64">%s</data>\n'
            '      <input>\n%s\n      </input>\n    </zedgraph>'
            % (w, h, blob, sys_input(names)))
    y0 = S.y
    S._emit(x if x is not None else S.LBL_X, w + 10, h + 8, body,
            ' color="#000000" fontSize="10" showInputData="false"')
    if advance:
        n = len(names) if reserve is None else reserve
        S.y = y0 + h + 8 + CAPTION + PER_CURVE * (n - 1) + TRAIL + S.gap


def declare(path):
    """Add the ZedGraph assembly to a finished .sm if it is not there yet."""
    s = io.open(path, encoding='utf-8').read()
    if 'ZedGraph Region (ZedGraph)' in s:
        return False
    s = s.replace('    </dependencies>', ZED_ASM + '    </dependencies>', 1)
    io.open(path, 'w', encoding='utf-8').write(s)
    return True
