# -*- coding: utf-8 -*-
"""HVLED101-style SMath worksheet builder.

Layout convention copied from  Reference/EVLHV101SSR50W Design Guide.sm :
  - A4 landscape, header = date/time/filename, footer = page/count
  - one row = a text label on the left + one or more math regions to the right
  - a math region is  <input> ... ':'  +  optional <contract> (display unit)
    +  <result action="numeric">   ->  SMath prints  name := expr = value unit
  - user inputs are highlighted with bgColor #ffff80

Every expression string is parsed twice: once by smgen's parser into SMath RPN,
once by this module into a Python value, so the printed result can never drift
from the formula next to it.
"""
import base64
import html
import math
import re

from smgen import expr_rpn, assign_rpn, rpn_xml, parse

# Functions confirmed to exist in this SMath build, because both worksheets that
# are known to run use only these:
#   Smath/L6790A_Section3_PowerStage_Tank_rev1_1.sm   sqrt abs ln exp atan cos sin
#   Reference/EVLHV101SSR50W Design Guide.sm          sqrt sin cos abs int vectorize solve
# min(), max(), if(), acos() and tan() are NOT available -- SMath reports
# "정의되지 않은 함수입니다" (undefined function).  Use the rewrites in
# build_l6790_smath.py (MIN/MAX/ACOS/TAN) instead.
SAFE_FUNCS = {'sqrt', 'abs', 'ln', 'exp', 'atan', 'cos', 'sin'}


def check_funcs(src):
    """raise before writing the file if an unavailable function slips in"""
    def walk(n):
        if n[0] == 'fun':
            if n[1] not in SAFE_FUNCS:
                raise ValueError(
                    f"function {n[1]!r} is not available in SMath; "
                    f"allowed: {sorted(SAFE_FUNCS)}  --  in: {src}")
            for a in n[2]:
                walk(a)
        elif n[0] == 'op':
            walk(n[2]); walk(n[3])
        elif n[0] == 'neg':
            walk(n[1])
    walk(parse(src))


# ------------------------------------------------------- program blocks
# Everything above is scalar arithmetic that this module also evaluates in
# Python, so a printed number can never drift from the formula beside it.
# A plot needs something else: a loop that fills a matrix.  Those regions are
# NOT evaluated here - they are emitted verbatim - so they get their own,
# wider allow-list.  The extra names are exactly the ones used by the two
# reference sheets in  Reference/Smath Bode Plot Example/ :
#     Bode.sm    for range line el lg numden diff Re Im sqrt
#     MyBode.sm  for range line el mat sys if log10 num2str arg Re Im sqrt
# 'lg' is not included: 20*log10(x) is written as 20*ln(x)/ln(10) so that the
# design sheet needs no logarithm beyond the one already proven to work.
PROG_FUNCS = SAFE_FUNCS | {'el', 'line', 'for', 'range'}


def _check_prog(src, allow=()):
    ok = PROG_FUNCS | set(allow)

    def walk(n):
        if n[0] == 'fun':
            if n[1] not in ok:
                raise ValueError(
                    f"function {n[1]!r} is not allowed in a program block; "
                    f"allowed: {sorted(ok)}  --  in: {src}")
            for a in n[2]:
                walk(a)
        elif n[0] == 'op':
            walk(n[2]); walk(n[3])
        elif n[0] == 'neg':
            walk(n[1])
    walk(parse(src))


def _stmt_rpn(st, allow=()):
    """one statement of a program block -> RPN tokens

    st is either  'lhs := rhs'  (lhs may be el(M,i,j))
    or            ('for', loopvar, 'range(...)', [sub-statements])
    or            'expr'  (evaluated for its value, e.g. the last line)
    """
    if isinstance(st, tuple):
        _, var, rng, body = st
        _check_prog(rng, allow)
        return ([('operand', var, None)] + expr_rpn(rng) + _block_rpn(body, allow)
                + [('function', 'for', 3)])
    if ':=' not in st:
        _check_prog(st, allow)
        return expr_rpn(st)
    lhs, rhs = st.split(':=', 1)
    lhs, rhs = lhs.strip(), rhs.strip()
    _check_prog(lhs, allow); _check_prog(rhs, allow)
    return expr_rpn(lhs) + expr_rpn(rhs) + [('operator', ':', 2)]


def _block_rpn(stmts, allow=()):
    """line(s1, ..., sN, N, 1)  -- the trailing pair is the matrix shape,
    exactly as in the reference sheets, so args = N + 2."""
    toks = []
    for st in stmts:
        toks += _stmt_rpn(st, allow)
    toks += [('operand', str(len(stmts)), None), ('operand', '1', None),
             ('function', 'line', len(stmts) + 2)]
    return toks

# --------------------------------------------------- render size estimate
# The layout bug that produced overlapping regions was a height GUESS
# ("28 + 20 * number of slashes").  SMath lays a formula out as a 2-D tree, so
# the height has to be measured on the tree: a fraction stacks, a radical adds a
# bar, an exponent adds a superscript line.  Units below are text lines.
LINE_PX = 13.5          # one text line at fontSize 8
CHAR_PX = 5.2           # average glyph width at fontSize 8 (measured on the PDF)


def _rh(n):
    """rendered height of a parsed expression, in text lines"""
    t = n[0]
    if t in ('num', 'var', 'unit'):
        return 1.0
    if t == 'neg':
        return _rh(n[1])
    if t == 'fun':
        h = max([_rh(a) for a in n[2]] or [1.0])
        # a radical grows with what is under it, and a function's brackets
        # grow with their content; both were costed as if they did not
        return h * (1.10 if n[1] == 'sqrt' else 1.0) + (
            0.55 if n[1] == 'sqrt' else 0.30)
    if t == 'op':
        o, a, b = n[1], n[2], n[3]
        if o == '/':
            # rule plus a gap above and below, at EVERY level - the old 0.18
            # was about right for one and short by a line by the fourth
            return _rh(a) + _rh(b) + 0.35
        if o == '^':
            return _rh(a) + 0.90 * _rh(b)
        return max(_rh(a), _rh(b))
    return 1.0


def _rwid(n):
    """rendered width in characters (a fraction is as wide as its widest half)"""
    t = n[0]
    if t == 'num' or t == 'var' or t == 'unit':
        return max(1, len(str(n[1])))
    if t == 'neg':
        return _rwid(n[1]) + 1
    if t == 'fun':
        return sum(_rwid(a) for a in n[2]) + len(n[1]) + 2 + len(n[2])
    if t == 'op':
        o, a, b = n[1], n[2], n[3]
        if o == '/':
            return max(_rwid(a), _rwid(b)) + 1
        if o == '^':
            return _rwid(a) + _rwid(b)
        return _rwid(a) + _rwid(b) + 3
    return 1


def est_box(src, lhs=None, unit=None, dp=None):
    """(width_px, height_px) a math region needs, with a little padding"""
    try:
        tree = parse(src)
    except Exception:
        return 240, 40
    lines = _rh(tree)
    chars = _rwid(tree)
    if lhs:
        chars += len(lhs) + 3
    if unit is not None:
        chars += 10 + (dp or 0)
    return int(chars * CHAR_PX) + 24, int(lines * LINE_PX) + 22


# ---------------------------------------------------------------- units
# token -> (SI factor, SMath display name)
UNITS = {
    'V': (1.0, 'V'), 'mV': (1e-3, 'mV'), 'kV': (1e3, 'kV'),
    'A': (1.0, 'A'), 'mA': (1e-3, 'mA'), 'μA': (1e-6, 'μA'),
    'W': (1.0, 'W'), 'mW': (1e-3, 'mW'), 'kW': (1e3, 'kW'),
    'Hz': (1.0, 'Hz'), 'kHz': (1e3, 'kHz'), 'MHz': (1e6, 'MHz'),
    'ohm': (1.0, 'ohm'), 'kohm': (1e3, 'kohm'), 'mohm': (1e-3, 'mohm'),
    'F': (1.0, 'F'), 'mF': (1e-3, 'mF'), 'μF': (1e-6, 'μF'),
    'nF': (1e-9, 'nF'), 'pF': (1e-12, 'pF'),
    'H': (1.0, 'H'), 'mH': (1e-3, 'mH'), 'μH': (1e-6, 'μH'), 'nH': (1e-9, 'nH'),
    's': (1.0, 's'), 'ms': (1e-3, 'ms'), 'μs': (1e-6, 'μs'), 'ns': (1e-9, 'ns'),
    'm': (1.0, 'm'), 'mm': (1e-3, 'mm'), 'cm': (1e-2, 'cm'),
    'T': (1.0, 'T'), 'mT': (1e-3, 'mT'),
    'J': (1.0, 'J'), 'mJ': (1e-3, 'mJ'),
}

_UNIT_TOK = re.compile(r"'([A-Za-zμΩ°]+)")
_DOTTED = re.compile(r"\b([A-Za-zα-ωΑ-Ωπφλδη_][A-Za-zα-ωΑ-Ωπφλδη_0-9]*)((?:\.[A-Za-z0-9_]+)+)")

PYFUN = {
    'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
    'exp': math.exp, 'ln': math.log, 'log': math.log10, 'abs': abs,
    'max': max, 'min': min, 'sign': lambda v: (v > 0) - (v < 0),
    'ceil': math.ceil, 'floor': math.floor, 'π': math.pi, 'pi': math.pi,
}


def pyify(src):
    """SMath expression string -> Python expression string (SI units)."""
    def u(m):
        tok = m.group(1)
        if tok not in UNITS:
            raise KeyError(f"unknown unit {tok!r} in {src!r}")
        return repr(UNITS[tok][0])
    s = _UNIT_TOK.sub(u, src)
    s = _DOTTED.sub(lambda m: m.group(1) + m.group(2).replace('.', '__'), s)
    s = s.replace('^', '**')
    return s


class Sheet:
    """A4-landscape, label-left / math-right worksheet."""

    # A3 LANDSCAPE.  The label column is wide enough that NO row label ever
    # wraps: SMath re-sizes a text region to its content when it saves, so a
    # two-line label ends up taller than the row advance and lands on the next
    # one.  One line per label removes the failure mode instead of estimating
    # around it.  Longest label in this sheet is 58 characters.
    LBL_X, LBL_W = 20, 470
    COLX = (510, 1120, 1400)
    NOTE_W = 1560
    # the paper the user set in SMath by hand; a rebuild must not reset it
    # A3 landscape. SMath lays out at 100 px per inch, which is how the
    # old 1752 x 1268 is known to have been A3 Extra (322 x 445 mm) -
    # a size no ordinary printer has, so it printed as clipped A4.
    PAGE_W, PAGE_H = 1654, 1169
    PAPER_ID = 8
    # What one printed page actually holds, and where the first break is.
    # MEASURED, on a sheet built for the purpose: L6790A_ruler.sm is 20 px
    # markers and nothing else - no folds, no formulas, no panes - so its
    # printed pages say where SMath breaks with nothing else to blame. Nine
    # pages gave first markers 1120 px apart, each page's last marker ending
    # exactly on the next page's first (1104+20 = 1124, 2224+20 = 2244), so
    #
    #     break(N) = N * PAGE_CONTENT + PAGE_ORIGIN
    #
    # This replaces 1117 with no origin, which was reasoned from the paper
    # size and was wrong by 3 px per page plus 4 - about an eighth of a page
    # by page forty. That drift is why the top band landed in a different
    # place on every page.
    PAGE_CONTENT = 1120
    PAGE_ORIGIN = 4
    MARGIN = 19
    # White kept clear at the top and bottom of every page.
    #
    # fit() already refuses to start a region that will not finish on the
    # page, so in principle nothing can straddle. In practice regions kept
    # straddling anyway, because the height fit() is given is an ESTIMATE -
    # est_box() measures a formula tree, and a tree it reads a little short
    # produces a region that starts inside the page and ends past it. There
    # is no warning: SMath just shades the break and the figure prints in
    # two halves.
    #
    # A band absorbs that error, and it is split evenly. The first version
    # put 40 at the bottom and 20 at the top on the reasoning that the
    # bottom seam is where a region overflows - but that only buys room the
    # page below then starts without, so a row pushed to a new page landed
    # 20 px from the seam and printed hard against it. Same total, half
    # each end. The cost is paper and nothing else.
    SAFE_TOP = 60
    SAFE_BOT = 60

    def __init__(self, title, author='', desc=''):
        self.r = []
        self.y = 24
        self.title, self.author, self.desc = title, author, desc
        self.ns = dict(PYFUN)          # python namespace of SI values
        self.gap = 8
        self._hidden = 0
        self.clashes = []
        self._areas = []

    # ------------------------------------------------------------ helpers
    def _emit(self, x, w, h, body, extra=''):
        self.r.append(
            f'    <region left="{x}" top="{self.y}" width="{w}" height="{h}"'
            f'{extra} isBreakable="false">\n{body}\n    </region>')

    # Text is wrapped HERE, into one <p> per line, instead of leaving it to
    # SMath.  A text region in SMath sizes itself to its content, so a long
    # single-<p> cell simply overflowed its column and printed on top of its
    # neighbour - that is what interleaved the section 16.7 table.  Wrapping
    # explicitly also makes the height exact rather than estimated.
    # Measured on the rendered PDF: a 1100 px note at fontSize 9 holds ~208
    # characters -> 5.24 px/char -> 0.58 of the font size.  0.62 leaves ~7 %
    # margin (0.67 leaves 15 %), because SMath silently RE-WRAPS any <p> that
    # does not fit and the extra line lands on top of the next region.
    CH_PER_PX = 0.67

    def _wrap(self, txt, w, size):
        cw = max(1.0, size * self.CH_PER_PX)
        per = max(8, int((w - 10) / cw))
        out, line = [], ''
        for word in str(txt).split(' '):
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= per:
                line += ' ' + word
            else:
                out.append(line)
                line = word
        out.append(line)
        return out or ['']

    # MEASURED on a worksheet SMath itself had saved:
    #   size 8 -> 20 / 47          size 9  -> 21 / 49 / 77 / 105
    #   size 10 -> 23              size 12 -> 26      size 15 -> 30
    # so the FIRST line costs about 1.4*size + 8.7 and every further line
    # about size + 19 - not the "size + 4" this module used to assume, which
    # is why three-line table cells kept landing on the row below.
    @staticmethod
    def text_h(nlines, size):
        return int(round(1.4 * size + 8.7)) + (nlines - 1) * (size + 19) + 2

    def vy(self):
        """y as SMath lays it out - absolute y less what is folded above

        A collapsed area is drawn as a single grey line and everything below
        it moves up, so page breaks do not fall at multiples of anything in
        absolute y. This is the coordinate the paper is divided in.
        """
        return self.y - self._hidden

    def _assign(self, lhs, val):
        """record a value, and notice when a name is being reused

        Two different quantities under one name is not an error SMath can
        report - the later assignment simply wins and the earlier rows go on
        showing what they printed. It happened: a Cardano block tagged .g
        created q.g, which section 16.6 was already using for the plant gain
        per hertz, and only snapshot.py noticed, by comparing against the
        previous run.

        Reassigning the SAME value is fine - that is a helper being rebuilt.
        A different value under a name already used is collected and the
        build reports it.
        """
        k = lhs.replace('.', '__')
        old = self.ns.get(k)
        if old is not None and isinstance(old, float) and isinstance(val, float):
            if old != val and abs(old - val) > 1e-9 * max(1.0, abs(old)):
                self.clashes.append((lhs, old, val))
        self.ns[k] = val

    def fit(self, h):
        """drop to the next page if `h` will not fit on this one

        SMath shades whatever crosses a page break, and that shading is the
        only warning that a region is going to be printed in two halves.
        Nothing here can be centred or scaled to avoid it - the only cure is
        to start the region on the next page.

        A region taller than a page is left where it is: it will cross a
        break wherever it starts, so moving it only wastes paper.

        SAFE_TOP and SAFE_BOT keep it off both seams - see those.
        """
        band = self.PAGE_CONTENT - self.SAFE_TOP - self.SAFE_BOT
        pos = (self.vy() - self.PAGE_ORIGIN) % self.PAGE_CONTENT
        if pos < self.SAFE_TOP:
            self.y += self.SAFE_TOP - pos
            pos = self.SAFE_TOP
        room = self.PAGE_CONTENT - self.SAFE_BOT - pos
        if h > room and h <= band:
            self.y += room + self.SAFE_BOT + self.SAFE_TOP
        return self.y

    def label_h(self, txt, size=10, w=None):
        """what _label would take, without emitting it

        A row and its label share one y, so the decision to move to the next
        page has to be made before either of them is written.
        """
        if txt is None:
            return 0
        return self.text_h(len(self._wrap(txt, w or self.LBL_W, size)), size)

    def _label(self, txt, size=10, bold=False, color='#000000', w=None, x=None,
               nowrap=False, pair=0):
        """pair: the height of the value this label belongs to.

        A label and its value are written at the SAME y, and SMath does not
        draw a region that crosses a page break in two halves - it moves the
        region to the next page. Give the two different heights and a break
        can fall between them: the tall formula moves, the short label stays,
        and the row prints with its label on one page and its value on the
        next. That is what the printed sheet did to the MOSFET-rms row.

        Reserving the same height for both closes the gap a break can land
        in, so either both move or neither does. It does not depend on
        knowing where the break is - which is the point, because the break
        positions could not be recovered from the printed sheet: solving for
        a page height, an origin offset and a per-fold correction against
        eighteen page-start rows and the one row that got cut has no answer.

        The text still draws at the top of its box, so nothing moves.
        """
        if txt is None:
            return 0
        ww = w or self.LBL_W
        st = f'font-weight: {"bold" if bold else "normal"}; font-style: normal; font-size: {size}px;'
        lines = self._wrap(txt, ww, size)
        ps = '\n'.join(f'        <p style="{st}">{html.escape(ln)}</p>' for ln in lines)
        body = ('    <text lang="eng" fontFamily="Arial" fontSize="10">\n      <content>\n'
                f'{ps}\n      </content>\n    </text>')
        h = self.text_h(len(lines), size)
        self._emit(x if x is not None else self.LBL_X, ww, max(h, pair), body,
                   f' color="{color}" fontSize="{size}"')
        return h

    def _math_body(self, rpn, unit, value, dp):
        c = ''
        if unit:
            c = ('\n        <contract>\n          '
                 f'<e type="operand" style="unit">{UNITS[unit][1]}</e>\n        </contract>')
        if value is None:
            res = ''
        else:
            txt = f'{value:.{dp}f}' if dp is not None else f'{value:g}'
            res = ('\n        <result action="numeric">\n          '
                   f'<e type="operand">{txt}</e>\n        </result>')
        dpa = f' decimalPlaces="{dp}"' if dp is not None else ''
        return (f'    <math{dpa}>\n      <input>\n{rpn}\n      </input>'
                f'{c}{res}\n    </math>')

    # ------------------------------------------------------------ blocks
    def h1(self, txt):
        self.y += 6
        # a heading alone at the foot of a page is worse than a gap, so it
        # carries a line of whatever follows it
        self.fit(self.label_h(txt, 15, self.NOTE_W) + 60)
        h = self._label(txt, size=15, bold=True, w=self.NOTE_W, x=self.LBL_X)
        self.y += h + 14

    def h2(self, txt):
        self.y += 16
        self.fit(self.label_h(txt, 12, self.NOTE_W) + 50)
        h = self._label(txt, size=12, bold=True, w=self.NOTE_W, x=self.LBL_X,
                        color='#0f2a44')
        self.y += h + 8

    def note(self, txt, size=9, color='#444444'):
        self.fit(self.label_h(txt, size, self.NOTE_W))
        h = self._label(txt, size=size, w=self.NOTE_W, x=self.LBL_X, color=color)
        self.y += h + self.gap

    def row(self, label, lhs, src, unit=None, dp=2, hi=False, note=None, h=None,
            echo=True, expect=None, allow=()):
        """label + (lhs := src = value unit).  Returns the SI value.

        expect/allow are the escape hatch for expressions this module cannot
        evaluate itself (matrix indexing).  Then the printed value is the one
        given here, so it has to be computed and justified separately.
        """
        if expect is None:
            check_funcs(src)
            val = eval(pyify(src), {'__builtins__': {}}, self.ns)   # noqa: S307
        else:
            _check_prog(src, allow)
            val = expect
        self._assign(lhs, val)
        shown = val / UNITS[unit][0] if unit else val
        rpn = rpn_xml(assign_rpn(lhs, src))
        body = self._math_body(rpn, unit if echo else None,
                               shown if echo else None, dp if echo else None)
        hgt = h or est_box(src, lhs, unit if echo else None, dp)[1]
        # before the label: the two share a y and must not be separated
        self.fit(max(hgt, self.label_h(label, 10)))
        lh = self._label(label, nowrap=True, pair=hgt) if label else 0
        extra = ' bgColor="#ffff80"' if hi else ''
        y0 = self.y
        self._emit(self.COLX[0], 1080, hgt, body,
                   ' color="#000000"' + extra + ' fontSize="8"')
        self.y = y0 + max(lh, hgt) + self.gap
        if note:
            self.note('      ' + note)
        return val

    def const(self, label, lhs, src, unit=None, dp=2, note=None):
        # An input is written in the unit it should be read in, so the literal
        # assignment is the whole story - no <contract>/<result> echo needed.
        return self.row(label, lhs, src, unit, dp, hi=True, note=note, echo=False)

    def show(self, label, src, unit=None, dp=2, h=None):
        check_funcs(src)
        val = eval(pyify(src), {'__builtins__': {}}, self.ns)   # noqa: S307
        shown = val / UNITS[unit][0] if unit else val
        rpn = rpn_xml(expr_rpn(src))
        body = self._math_body(rpn, unit, shown, dp)
        hgt = h or est_box(src, None, unit, dp)[1]
        self.fit(max(hgt, self.label_h(label, 10)))
        lh = self._label(label, pair=hgt) if label else 0
        y0 = self.y
        self._emit(self.COLX[0], 1080, hgt, body, ' color="#000000" fontSize="8"')
        self.y = y0 + max(lh, hgt) + self.gap
        return val

    PACKX = (20, 420, 820, 1220)

    def pack(self, items, per=4, dp=6):
        """lay out intermediate assignments several per line (no labels).

        items: list of (lhs, src) or (lhs, src, unit, dp)

        The number per line is reduced automatically when the measured widths do
        not fit, so a wide expression can never sit on top of its neighbour.
        """
        AVAIL = self.PAGE_W - 2 * self.MARGIN - self.LBL_X
        i = 0
        while i < len(items):
            # how many of the remaining items fit on one line?
            k, total = 0, 0
            while i + k < len(items) and k < per:
                it = items[i + k]
                w = est_box(it[1], it[0],
                            it[2] if len(it) > 2 else None,
                            it[3] if len(it) > 3 else dp)[0]
                if k and total + w > AVAIL:
                    break
                total += w
                k += 1
            k = max(1, k)
            chunk = items[i:i + k]
            widths = [est_box(it[1], it[0],
                              it[2] if len(it) > 2 else None,
                              it[3] if len(it) > 3 else dp)[0] for it in chunk]
            slack = max(0, (AVAIL - sum(widths)) // max(1, len(chunk)))
            x = self.LBL_X
            hmax = max(est_box(it[1], it[0],
                               it[2] if len(it) > 2 else None,
                               it[3] if len(it) > 3 else dp)[1]
                       for it in chunk)
            self.fit(hmax)
            hmax = 0
            for it, w in zip(chunk, widths):
                lhs, src = it[0], it[1]
                unit = it[2] if len(it) > 2 else None
                d = it[3] if len(it) > 3 else dp
                check_funcs(src)
                val = eval(pyify(src), {'__builtins__': {}}, self.ns)   # noqa: S307
                self._assign(lhs, val)
                shown = val / UNITS[unit][0] if unit else val
                body = self._math_body(rpn_xml(assign_rpn(lhs, src)), unit, shown, d)
                hgt = est_box(src, lhs, unit, d)[1]
                hmax = max(hmax, hgt)
                y0 = self.y
                self._emit(x, w, hgt, body, ' color="#000000" fontSize="8"')
                self.y = y0
                x += w + slack
            self.y += hmax + self.gap
            i += k

    # ------------------------------------------------------- collapsible area
    # Structure copied from Reference/Smath Bode Plot Example/MyBode.sm: the
    # opening region CONTAINS the block plus a terminator region.  Collapsed, a
    # block of any height shows as one line, which is how the working parts of
    # this sheet stay readable while the machinery stays available.
    def area_begin(self, title=None, collapsed=True):
        if title:
            # the "[+]" line is all a reader sees of a folded block, so it
            # must not be the thing that lands on the seam
            self.fit(self.label_h('  [+] ' + title, 9, 1100) + 2)
            h = self._label('  [+] ' + title, size=9, color='#6a6a6a', w=1100)
            self.y += h + 2
        if collapsed and any(c for _i, _y, c in self._areas):
            # Section 16.6 lost an area_end() and folded one block inside
            # another. Nothing showed it: the sheet opened, every value was
            # right, and the only symptom was that page breaks below it
            # were three quarters of a page early - which reads as a layout
            # quirk, not a bug. vy() handles it now, but a fold inside a
            # fold is still a missing area_end(), so say so here.
            raise ValueError('a collapsed area inside a collapsed area - '
                             'an area_end() is missing above %r. Use '
                             'collapsed=False for a deliberate inner block.'
                             % title)
        self._areas.append((len(self.r), self.y, collapsed))
        self.y += 2

    def area_end(self):
        NL = chr(10)
        idx, y0, collapsed = self._areas.pop()
        if collapsed and not any(c for _i, _y, c in self._areas):
            # everything between here and there disappears from the printed
            # flow; only the grey line above the block is left, and that was
            # emitted before area_begin so it is already counted.
            #
            # ONLY when nothing collapsed still encloses this one. A block
            # inside an already-folded block is hidden by the outer fold and
            # adding it again subtracts the same paper twice - which it did,
            # for 814 px, and every page break below that point was wrong.
            self._hidden += self.y - y0
        inner = self.r[idx:]
        del self.r[idx:]

        def pad(blk):
            return NL.join('  ' + ln for ln in blk.split(NL))

        body = '      <area%s />' % (' collapsed="true"' if collapsed else '')
        term = ('      <region top="%d" color="#000000">' + NL
                + '        <area terminator="true" />' + NL
                + '      </region>') % self.y
        self.r.append(('    <region top="%d" color="#000000">' + NL
                       + '%s' + NL + '%s' + NL + '%s' + NL + '    </region>')
                      % (y0, body, NL.join(pad(b) for b in inner), term))
        # A COLLAPSED area prints as a rule right across the page at the
        # terminator, and that rule needs room of its own. With 6 px the
        # rule landed on the row below it - ten times in the 42-page print,
        # once straight through the yellow R.T input, which reads as a
        # number crossed out. The rule is about a text line tall, so give
        # it one.
        self.y += 24

    # ------------------------------------------------------------ plots
    def prog(self, stmts, label=None, x=None, w=520, h=None, allow=()):
        """A bare statement block that fills matrices - no <result> echo.

        This is the only region type this module does not evaluate in Python,
        so anything printed from it must be cross-checked separately.
        """
        toks = (_stmt_rpn(stmts[0], allow) if len(stmts) == 1
                else _block_rpn(stmts, allow))
        body = ('    <math>\n      <input>\n'
                + rpn_xml(toks) + '\n      </input>\n    </math>')
        # h is a FLOOR. Every long vector statement carries an h chosen by
        # eye when it was written, and a tall fraction outgrows it silently -
        # nothing downstream can see a region drawn taller than it declares.
        est = max((est_box(st.split(':=')[-1])[1] for st in stmts
                   if ':=' in st), default=0)
        hgt = max(h or 260, est)
        self.fit(max(hgt, self.label_h(label, 10)))
        lh = self._label(label, pair=hgt) if label else 0
        y0 = self.y
        self._emit(x if x is not None else self.COLX[0], w, hgt, body,
                   ' color="#000000" fontSize="8"')
        self.y = y0 + max(lh, hgt) + self.gap

    # view attributes copied verbatim from the magnitude plot of
    # Reference/Smath Bode Plot Example/MyBode.sm, whose data range
    # (x = log10 f over four decades, y in dB) is the same shape as ours.
    # If the initial view is off, the mouse wheel zooms and dragging pans.
    PLOTATTR = ('grid="true" axes="true" type="2d" render="lines" '
                'scale_x="0.157589007083374" scale_y="10.7171895137377" '
                'scale_z="2.34329969537013" rotate_x="0" rotate_y="0" '
                'rotate_z="0" transpose_x="-77" transpose_y="-5" transpose_z="0"')

    PLOT_DIV = 4.0          # px per grid division - measured, see plot_view

    @staticmethod
    def plot_view(w, h, x0, x1, y0, y1, div=None):
        """SMath 2D view attributes for a wanted window.

        scale_* is UNITS PER GRID DIVISION and transpose_* offsets the origin
        in pixels, so pixels-per-unit = div/scale and the window follows.

        div was 20 and is 4. The old value came from reading MyBode.sm
        backwards, which cannot work: those plots carry grid="false"
        axes="false" and draw their own axes from tick tables, so their
        scale_* is wherever the author left the zoom rather than a computed
        window. The number that settles it is P19 of the probe sheet, whose
        intended window this function computed and whose rendering was
        photographed on the SMath this project runs on - x -1.2..1.2 came out
        as roughly -5.5..5.5 and y 0..50 as roughly 0..250. Five times wide on
        both axes, so the division is 4 px.

        With 20 the gain sheet put its x window on 2.5..11.2 while the curves
        lived at 0.55..2.2, and every frame was empty. P19 survived only
        because its transpose_x is 0, which kept the data near the centre.

        Pass div explicitly to draw the same data at several calibrations and
        let the sheet prove the number instead of trusting this note.
        """
        d = Sheet.PLOT_DIV if div is None else float(div)
        sx = d * (x1 - x0) / w
        sy = d * (y1 - y0) / h
        tx = -int(round((x0 + x1) / 2.0 * (d / sx)))
        ty = -int(round((y0 + y1) / 2.0 * (d / sy)))
        return ('grid="true" axes="true" type="2d" render="lines" '
                'scale_x="%.9f" scale_y="%.9f" scale_z="1" '
                'rotate_x="0" rotate_y="0" rotate_z="0" '
                'transpose_x="%d" transpose_y="%d" transpose_z="0"'
                % (sx, sy, tx, ty))

    PLOT_CAPTION = 24

    def plot(self, var, x=None, w=540, h=280, attr=None, advance=True):
        body = ('    <plot ' + (attr or self.PLOTATTR) + '>\n      <input>\n'
                f'        <e type="operand">{html.escape(var)}</e>\n'
                '      </input>\n    </plot>')
        y0 = self.y
        self._emit(x if x is not None else self.LBL_X, w, h, body,
                   ' color="#000000" fontSize="10"')
        # SMath prints the variable name just under the frame; reserve for it
        self.y = y0 + (h + self.PLOT_CAPTION + self.gap if advance else 0)

    _pic_row_y = 0

    def pic(self, path, x=None, w=560, same_row=False):
        """same_row=True places this picture beside the previous one instead of
        under it, and leaves y at the bottom of the taller of the two."""
        from PIL import Image
        with Image.open(path) as im:
            ww, hh = im.size
        h = int(w * hh / ww)
        with open(path, 'rb') as fh:
            b = base64.b64encode(fh.read()).decode()
        body = ('    <picture>\n      <raw format="png" encoding="base64">'
                + b + '</raw>\n    </picture>')
        if same_row:
            self.y = self._pic_row_y
        else:
            self.fit(h)
        y0 = self.y
        self._pic_row_y = y0
        self._emit(x if x is not None else self.LBL_X, w, h, body,
                   ' border="true" color="#000000"')
        self.y = max(self.y, y0 + h + self.gap)

    def set(self, lhs, src):
        """compute silently (helper variables that need not be printed)"""
        val = eval(pyify(src), {'__builtins__': {}}, self.ns)   # noqa: S307
        self._assign(lhs, val)
        return val

    def table(self, headers, rows, widths=None, size=9):
        """simple grid; every cell is wrapped by _wrap, so the row height is
        the real rendered height and columns cannot run into each other"""
        widths = widths or [150] * len(headers)
        GAP = 10                       # gutter between columns

        def emit_row(cells, bold=False):
            # the whole row shares one y, so the tallest cell decides whether
            # the row can stay on this page
            self.fit(max(self.label_h(str(c), size, w - GAP)
                         for w, c in zip(widths, cells)) + 8)
            hs, x, y0 = [], self.LBL_X, self.y
            for w, cell in zip(widths, cells):
                self.y = y0
                hs.append(self._label(str(cell), size=size, bold=bold,
                                      w=w - GAP, x=x))
                x += w
            self.y = y0 + max(hs) + 8

        emit_row(headers, bold=True)
        for r in rows:
            emit_row(r)
        self.y += self.gap

    # ------------------------------------------------------------ save
    def save(self, path):
        xml = (
            '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
            # Solver 1.5.0.9678 / assemblies 1.75.9678.0 - the build
            # installed here, read off the TI application note sheet and
            # off our own sheet after SMath re-saved it. The GUIDs still
            # come from the ST reference file; only the versions moved.
            '<?application progid="SMath Solver" version="1.5.0.9678"?>\n'
            '<worksheet xmlns="http://smath.info/schemas/worksheet/1.0">\n'
            '  <settings ppi="96">\n'
            '    <identity><id>9c1f7a30-4d21-4e6b-9f11-6b2a7c5d3e88</id><revision>1</revision></identity>\n'
            # only <author>: the reference worksheet carries nothing else here and an
            # element outside the schema is a load-time risk
            f'    <metadata lang="eng"><author>{html.escape(self.author)}</author></metadata>\n'
            '    <calculation><precision>4</precision><exponentialThreshold>5</exponentialThreshold>'
            '<trailingZeros>false</trailingZeros><significantDigitsMode>false</significantDigitsMode>'
            '<mixedNumbers>false</mixedNumbers><roundingMode>0</roundingMode>'
            '<approximateEqualAccuracy>3</approximateEqualAccuracy><fractions>decimal</fractions></calculation>\n'
            '    <pageModel active="true" viewMode="2" printGrid="false" printAreas="true" '
            'simpleEqualsOnly="false" printBackgroundImages="true" hideElementsHighlightings="false">\n'
            f'      <paper id="{self.PAPER_ID}" orientation="Landscape" '
            f'width="{self.PAGE_W}" height="{self.PAGE_H}" />\n'
            f'      <margins left="{self.MARGIN}" right="{self.MARGIN}" '
            f'top="{self.MARGIN}" bottom="{self.MARGIN}" />\n'
            '      <header alignment="Center" color="#a9a9a9">&amp;[DATE] &amp;[TIME] - &amp;[FILENAME]</header>\n'
            '      <footer alignment="Center" color="#a9a9a9">&amp;[PAGENUM] / &amp;[COUNT]</footer>\n'
            '      <backgrounds />\n'
            '    </pageModel>\n'
            # every region TYPE used in the sheet must be declared here, otherwise
            # SMath throws "Object reference not set to an instance of an object"
            # while loading and never opens the file.
            '    <dependencies>\n'
            '      <assembly name="SMath Core" version="1.75.9678.0" '
            'guid="a37cba83-b69c-4c71-9992-55ff666763bd" />\n'
            '      <assembly name="MathRegion" version="1.75.9678.0" '
            'guid="02f1ab51-215b-466e-a74d-5d8b1cf85e8d" />\n'
            '      <assembly name="PictureRegion" version="1.75.9678.0" '
            'guid="06b5df04-393e-4be7-9107-305196fcb861" />\n'
            '      <assembly name="PlotRegion" version="1.75.9678.0" '
            'guid="c451c2b5-798b-4f08-b9ec-b90963d1ddaa" />\n'
            '      <assembly name="AreaRegion" version="1.75.9678.0" '
            'guid="4974b228-4974-44cf-8274-bf2936b4a766" />\n'
            '      <assembly name="SpecialFunctions" version="1.75.9678.0" '
            'guid="2814e667-4e12-48b1-8d51-194e480eabc5" />\n'
            '      <assembly name="TextRegion" version="1.75.9678.0" '
            'guid="485d28c5-349a-48b6-93be-12a35a1c1e39" />\n'
            '    </dependencies>\n'
            '  </settings>\n'
            # regions must live inside <regions type="content">, not directly
            # under <worksheet>
            '  <regions type="content">\n'
            + '\n'.join(self.r) +
            '\n  </regions>\n</worksheet>\n')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(xml)
        return len(xml), self.y
