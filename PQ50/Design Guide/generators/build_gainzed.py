# -*- coding: utf-8 -*-
"""Builds  Smath/L6790A_gainzed.sm  -  LLC gain curves in a ZedGraph pane.

Everything here comes from two places and nothing from guesswork: the
ZedGraph 5.1 source in Reference/Smath Bode Plot Example/Zedgraph, and the
TI application note sheet beside it.

How several curves share one frame.  The TI sheet builds its graphs up one
curve at a time and hands each pane a SYSTEM of plot matrices:

    pane #1   plot.transfer_f_LC                                 sys args 3
    pane #5   plot.transfer_f_LC, ..._PDAMP, ..._S_DAMP, 3, 1    sys args 5
    pane #6   plot.input_impedance, plot.LC, plot.P_damp,
              plot.S_damp, 4, 1                                  sys args 6

so the input is sys(p1, ..., pN, N, 1) and each pN is its own two-column
matrix. Pane #6 already carries four curves and four legend entries, which
is exactly the family this sheet draws, so it is lifted whole and every
label rewritten.

Counting LineItem in the blob does NOT tell you how many curves a pane has:
BinaryFormatter writes a class record once and later instances reference it
by object id, so the type name appears once however many curves exist. That
is what made an earlier attempt conclude there was only ever one, and send
this down the augment()-with-more-columns dead end.

How the pane is edited.  zedpane.py works from the source:

  * Scale.GetObjectData fixes the field order, so the (min, max) pair can be
    found by value and the six auto flags sit 48 bytes after min. The TI
    panes have minAuto = maxAuto = 0 - the ranges are pinned - which is why
    a curve at f_n 0.55..2.2 was invisible in a frame running 10 Hz..100 kHz.

  * LinearScale and LogScale serialise identically - base.GetObjectData plus
    schema2 = 10 - so a log axis becomes linear by rewriting the
    length-prefixed type name. Records are referenced by object id, never by
    offset, so the stream changing length is harmless.

  * Strings are length-prefixed too, so titles and legend entries can be
    replaced by text of any length as long as the prefix goes with them.

Do not resize the pane from here. Doubling PaneBase's rect applies
cleanly and produces a pane that will not load: SMath falls back to a
default GraphPane with axes named x and y, because Chart.rect,
Legend.location, Margin and baseDimension are all stored against the old
rectangle and none of them moved with it. Drag the region in SMath
instead. zedpane.set_size carries the same warning.

Run:  python build_gainzed.py
"""
import base64
import io
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import zedpane as Z                                                # noqa: E402
import zedsheet as ZS                                             # noqa: E402
from smsheet import Sheet                                          # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
REF = os.path.join(ROOT, 'Reference', 'Smath Bode Plot Example',
                   'SMPS_Input_Filter_Design_TI_APP_Note.sm')
OUT = os.path.join(ROOT, 'Smath', 'L6790A_gainzed.sm')

ZED_ASM = ('      <assembly name="ZedGraph Region (ZedGraph)" '
           'version="0.1.7806.5613" '
           'guid="b0e7602f-c9d4-4e6c-b6f1-087e4c6e8915" />\n')

LAM = 0.55
QS = [('a', 0.20), ('b', 0.40), ('c', 0.766), ('d', 1.50)]
# One sweep for every pane, spaced logarithmically over Infineon's two
# decades. Log spacing is what makes the curves smooth: 91 evenly spaced
# points put a fifth of themselves below resonance, which is where all the
# structure is, so the peaks came out as three straight segments.
FLO, FHI, NPT = 0.1, 10.0, 1201         # 600 points per decade
VEC = ('eval', 'augment', 'vectorize')
ANCHOR = (0.60, 0.70, 0.80, 1.00, 1.50, 2.00)
LINEW = 2.0      # curves and frames, in px. MinorGrid is a different class
LOGSTEP = 1.0    # major tick every DECADE - 0.1, 1, 10, as Infineon draws it
NUMFMT = '0.###'  # the panes ship with "f0", which rounds 0.63 to 1
XLIN = (0.5, 2.25)                      # the zoomed linear window
XLOG = (FLO, FHI)                       # the Infineon window

# the legend entries those TI panes ship with, in order
LEG1 = ('SMPS Input Impedance',)
LEG4 = ('SMPS Input Imedance', 'LC Choke Impedance',        # sic, TI's typo
        'Parallel Damped', 'Series Damped')
LEG4B = ('LC Choke', 'Parallel Damp', 'Series Damp', '2 Stage Filter')


def M(fn, q, lam=LAM):
    a = 1 + lam - lam / fn ** 2
    return 1.0 / math.sqrt(a * a + q * q * (fn - 1.0 / fn) ** 2)


def dB(x):
    return 20.0 * math.log10(x)


def peak(q):
    return max((M(FLO + i * (FHI - FLO) / 20000.0, q),
                FLO + i * (FHI - FLO) / 20000.0) for i in range(20001))


def panes():
    s = io.open(REF, encoding='utf-8', errors='replace').read()
    got = re.findall(r'<zedgraph([^>]*)>\s*<data encoding="base64">([^<]*)'
                     r'</data>', s, re.S)
    if len(got) < 8:
        raise SystemExit('%s has %d panes, expected at least 8'
                         % (os.path.basename(REF), len(got)))
    return [(int(re.search(r'width="(\d+)"', a).group(1)),
             int(re.search(r'height="(\d+)"', a).group(1)),
             base64.b64decode(b.strip())) for a, b in got]


P = panes()
W1, H1, RAW1 = P[0]                     # one curve,   log x, log y
W4, H4, RAW4 = P[6]                     # FOUR curves, log x, log y
W4B, H4B, RAW4B = P[7]                  # FOUR curves, log x, linear y in dB

# windows sized to the data, with a little air - auto-scale chose 0..9 for a
# family whose tallest curve peaks at 4.67, which wastes half the frame
XWIN = XLIN
_TOP = max(peak(q)[0] for _, q in QS)
# the ends are rounded outwards to whole units, and the dB ends to whole
# tens, so that every tick label is a round number: an axis running to 5.5
# in steps of 1 leaves its last gridline off the frame, and one running
# from -35 labels -35, -25, -15, which reads as noise
YWIN = (0.0, float(math.ceil(_TOP * 1.08)))
YONE = math.ceil(peak(QS[2][1])[0] * 1.15 * 2) / 2.0
DBLO = math.floor(min(dB(M(f, q)) for _, q in QS
                      for f in (FLO, FHI)) / 10.0) * 10.0
DBHI = math.ceil(dB(_TOP) / 10.0) * 10.0

LEGEND = ['Q = %g      peak %.2f at fn = %.2f' % (q, peak(q)[0], peak(q)[1])
          for _, q in QS]


def fit(raw, old, new):
    """set an axis range and give it steps that suit it

    A log axis is left alone: it steps in decades and already draws the
    close mesh the TI panes have. A linear one keeps whatever steps the log
    axis had - majorStep 1, minorStep 1 - and over a range of 1.75 that is
    two lines and nothing between them.
    """
    raw = Z.set_range(raw, old, new)
    mj, mn = Z.nice_steps(*new)
    return Z.set_steps(raw, new, mj, mn)


def logfit(raw, old, new):
    """set a LOG axis range and pin its major step.

    LogScale.CyclesPerStep returns _majorStep unchanged and PickScale only
    overrides it when _majorStepAuto is set, so majorStep is a count of
    DECADES - and it may be fractional, which is how a span narrower than a
    decade can still be labelled. Here the span IS whole decades, so
    LOGSTEP = 1 gives 0.1, 1, 10 and nothing odd in between.

    Minor ticks need nothing: CalcMinorTicValue walks a fixed 1, 2 ... 9
    table, which is the dense mesh the TI panes already show.
    """
    raw = Z.set_range(raw, old, new)
    return Z.set_steps(raw, new, LOGSTEP, 1.0)


def relabel(raw, title, ytitle, legends, old_legends, xnote=''):
    raw = Z.set_text(raw, title[0], title[1])
    raw = Z.set_text(raw, 'Frequency (Hz)',
                     'normalised frequency   fn = fsw / fr' + xnote)
    raw = Z.set_text(raw, ytitle[0], ytitle[1])
    raw = Z.set_text(raw, 'Phase Angle (deg)', 'unused')
    for old, new in zip(old_legends, legends):
        raw = Z.set_text(raw, old, new)
    return raw


# --- one curve, both axes linear and auto-scaled
_p1, NLOG = Z.to_linear(RAW1)
_p1 = fit(_p1, (10.0, 100000.0), XWIN)
_p1 = fit(_p1, (1.0, 100.0), (0.0, YONE))
_p1 = relabel(_p1, ('Input Impedance',
                    'LLC voltage gain   M(fn)      lambda = %g' % LAM),
              ('Impedance (Ohms)', 'voltage gain   M'), [LEGEND[2]], LEG1)

# --- four curves, both axes linear and auto-scaled
_p4, _ = Z.to_linear(RAW4)
_p4 = fit(_p4, (10.0, 100000.0), XWIN)
# pane #6 runs its y from 0.01, not 1 like the single-curve pane
_p4 = fit(_p4, (0.01, 100.0), YWIN)
_p4 = relabel(_p4, ('Input Impedance',
                    'LLC voltage gain   M(fn, Q)      lambda = %g' % LAM),
              ('Impedance (Ohms)', 'voltage gain   M'), LEGEND, LEG4)

# --- four curves in dB, x left logarithmic on purpose
_p4b = fit(RAW4B, (-60.0, 20.0), (DBLO, DBHI))
_p4b = logfit(_p4b, (10.0, 1000000.0), XLOG)
_p4b = relabel(_p4b, ('Transfer Function',
                      'LLC voltage gain in dB      lambda = %g' % LAM),
               ('Gain (dB)', 'voltage gain   20 log10 M   [dB]'),
               LEGEND, LEG4B, xnote='   (log)')

# --- the Infineon picture: linear gain against a logarithmic f_n over two
# full decades, so the major ticks land on 0.1, 1, 10 and each decade
# carries the fixed 1, 2 ... 9 minor mesh
_plog = logfit(RAW4B, (10.0, 1000000.0), XLOG)
_plog = fit(_plog, (-60.0, 20.0), YWIN)
_plog = relabel(_plog, ('Transfer Function',
                        'LLC voltage gain   M(fn, Q)   -   LOG fn'
                        '      lambda = %g' % LAM),
                ('Gain (dB)', 'voltage gain   M'), LEGEND, LEG4B,
                xnote='   (log)')

# --- the panes ship with number format "f0", which rounds every label to a
# whole number: f_n 0.63 printed as 1, and a y axis stepping 0.5 printed
# 0, 1, 1, 2, 2. Each axis carries its own string record, so each is set.
def numfmt(raw, *ranges):
    for r in ranges:
        raw, was = Z.set_format(raw, r, NUMFMT)
    return raw


_p1 = numfmt(_p1, XLIN, (0.0, YONE))
_p4 = numfmt(_p4, XLIN, YWIN)
_p4b = numfmt(_p4b, XLOG, (DBLO, DBHI))
_plog = numfmt(_plog, XLOG, YWIN)

# --- thicker outlines, applied last and on its own. LineBase carries the
# curves and the frame; the grid is MinorGrid, a different class with its
# own penWidth, so the mesh keeps its hairline
_p1, NLINE = Z.set_line_width(_p1, LINEW)
_p4, _ = Z.set_line_width(_p4, LINEW)
_p4b, _ = Z.set_line_width(_p4b, LINEW)
_plog, _ = Z.set_line_width(_plog, LINEW)

PANE_1 = base64.b64encode(_p1).decode()
PANE_4 = base64.b64encode(_p4).decode()
PANE_4B = base64.b64encode(_p4b).decode()
PANE_LOG = base64.b64encode(_plog).decode()


def sys_input(names, indent='        '):
    """sys(p1, ..., pN, N, 1) - how the TI sheet feeds a multi-curve pane"""
    out = ['%s<e type="operand">%s</e>' % (indent, n) for n in names]
    out.append('%s<e type="operand">%d</e>' % (indent, len(names)))
    out.append('%s<e type="operand">1</e>' % indent)
    out.append('%s<e type="function" preserve="true" args="%d">sys</e>'
               % (indent, len(names) + 2))
    return '\n'.join(out)


def one_input(name, indent='        '):
    return '%s<e type="operand">%s</e>' % (indent, name)


def zed(S, inner, blob, w, h, ncurve=1):
    """SMath prints the plot input under the frame, one line per curve and
    a brace around them. One line takes about 24 px and each extra about
    15; reserving 8 put the four-name brace on the next heading.
    """
    body = ('    <zedgraph width="%d" height="%d">\n'
            '      <data encoding="base64">%s</data>\n'
            '      <input>\n%s\n      </input>\n    </zedgraph>'
            % (w, h, blob, inner))
    y0 = S.y
    S._emit(S.LBL_X, w + 10, h + 8, body, ' color="#000000" fontSize="10"')
    S.y = y0 + h + 8 + 24 + 15 * (ncurve - 1) + S.gap


S = Sheet('L6790A gain curves', 'L6790A project',
          'LLC gain curves in a ZedGraph pane')

S.h1('LLC gain curves  -  four traces in one frame, the way the TI sheet does it')
S.note('The linear axes carry their own tick steps. Converting an axis from log to '
       'linear leaves the old ones behind - majorStep 1 and minorStep 1, written for '
       'decades - and over a range of 1.75 that is two lines with nothing between '
       'them. Each range now gets a round step near a tenth of itself and a minor at '
       'a fifth of that, which is the close mesh the TI panes have.')
S.note('A ZedGraph pane takes several curves as sys(p1, ..., pN, N, 1), each pN its own '
       'two-column matrix. The TI sheet builds its graphs up exactly that way - one curve, '
       'then two, then three - and its pane #6 already carries four curves and four legend '
       'entries. Those panes are lifted whole here and every label rewritten. Nothing is '
       'auto-scaled: every range, step and number format below is pinned, because the '
       'panes ship with minAuto = maxAuto = 0 and a format of "f0" that rounds every tick '
       'label to a whole number.')

S.h2('1  the tank')
S.const('[PICK] lambda = L.r / L.m:', 'λ', str(LAM), None, 3)
for tag, q in QS:
    S.const('[PICK] Q for curve %s:' % tag, 'Q.%s' % tag, str(q), None, 3)
S.const('[PICK] sweep from f.n =', 'f.lo', str(FLO), None, 3)
S.const('[PICK] sweep to   f.n =', 'f.hi', str(FHI), None, 3)
S.const('[PICK] points:', 'N.g', str(NPT), None, 0)

S.h2('2  a range variable, then plain assignments      no for loop anywhere')
S.note('The sweep is spaced logarithmically, %d points over the two decades %g to %g - '
       '%d per decade. Even spacing put only a fifth of the points below resonance, which '
       'is where every peak is, so the curves came out of the pane as straight segments.'
       % (NPT, FLO, FHI, round((NPT - 1) / math.log10(FHI / FLO))))
S.prog(['k.g := range(1,N.g)'], label='- the range variable:', h=54, w=420)
S.prog(['el(F.g,k.g) := f.lo*(f.hi/f.lo)^((k.g-1)/(N.g-1))'],
       label='- the frequency axis, log spaced:', h=54, w=760)
for tag, _ in QS:
    S.prog(['el(G.%s,k.g) := 1/sqrt((1+λ-λ/el(F.g,k.g)^2)^2'
            '+Q.%s^2*(el(F.g,k.g)-1/el(F.g,k.g))^2)' % (tag, tag)],
           label='- gain for curve %s:' % tag, h=60, w=900)
for tag, _ in QS:
    S.prog(['el(D.%s,k.g) := 20*ln(el(G.%s,k.g))/ln(10)' % (tag, tag)],
           label='- curve %s in dB:' % tag, h=54, w=620)

S.h2('3  the curve at fixed f_n      numbers to read the picture against')
for fn in ANCHOR:
    S.row('- M at f_n = %.2f, full load:' % fn, 'm.%d' % int(fn * 100),
          '1/sqrt((1+λ-λ/%g^2)^2+Q.c^2*(%g-1/%g)^2)' % (fn, fn, fn),
          None, 4, expect=M(fn, 0.766))
S.row('- and the last point of the swept vector:', 'r.c',
      'el(G.c,N.g)', None, 4, expect=M(FHI, 0.766), allow=())

S.h2('4  one two-column matrix per curve')
for tag, q in QS:
    S.prog(['P.%s := eval(augment(vectorize(F.g),vectorize(G.%s)))' % (tag, tag)],
           label='- curve %s,  Q = %g:' % (tag, q), h=56, w=760, allow=VEC)
for tag, q in QS:
    S.prog(['B.%s := eval(augment(vectorize(F.g),vectorize(D.%s)))' % (tag, tag)],
           label='- curve %s in dB:' % tag, h=56, w=760, allow=VEC)

pk, at = peak(0.766)
S.h2('5  ALL FOUR IN ONE FRAME      sys(P.a, P.b, P.c, P.d, 4, 1)')
S.note('Linear axes zoomed to f_n %g .. %g - the sweep runs wider than that and the pane '
       'clips it - and four legend entries each carrying its own peak. Lighter load is the '
       'taller curve: %s.'
       % (XLIN[0], XLIN[1],
          ', '.join('Q = %g peaks at %.2f' % (q, peak(q)[0]) for _, q in QS)))
zed(S, sys_input(['P.%s' % t for t, _ in QS]), PANE_4, W4, H4,
    len(QS))

S.h2('6  the same four in dB, on a logarithmic f_n axis')
S.note('The other way this family is drawn - dB against a log f_n, both axes as a filter '
       'response would have them. The log axis is labelled the same way as section 7. '
       'Peaks in dB: %s.' % ', '.join('%.1f' % dB(peak(q)[0]) for _, q in QS))
zed(S, sys_input(['B.%s' % t for t, _ in QS]), PANE_4B, W4B, H4B,
    len(QS))

S.h2('7  THE INFINEON PICTURE      linear gain, log f_n, two full decades')
S.note('%g to %g on a logarithmic x, the way the Infineon guide draws this family. Two '
       'whole decades means the major ticks land on %s and each decade carries the fixed '
       '1, 2 ... 9 minor mesh, so the frame reads at a glance without a single odd number '
       'on it - which is the point of choosing the span to be whole decades.'
       % (XLOG[0], XLOG[1],
          ' and '.join('%g' % (10 ** e) for e in
                       range(int(round(math.log10(XLOG[0]))),
                             int(round(math.log10(XLOG[1]))) + 1))))
S.note('Section 5 is the same four curves on a linear x zoomed to %g .. %g. The log frame '
       'spends %d %% of its width below resonance where every peak sits; the linear frame '
       'spends %d %% but shows nothing outside the zoom.'
       % (XLIN[0], XLIN[1],
          round(100 * math.log10(1 / XLOG[0]) / math.log10(XLOG[1] / XLOG[0])),
          round(100 * (1 - XLIN[0]) / (XLIN[1] - XLIN[0]))))
zed(S, sys_input(['P.%s' % t for t, _ in QS]), PANE_LOG, W4B, H4B, len(QS))

S.h2('8  full load alone      the single-curve pane, for comparison')
S.note('Expected: a hump reaching %.2f near f_n %.2f, crossing 1.00 exactly at f_n = 1, '
       'and falling to %.2f at the right edge of the frame, f_n %.2f.'
       % (pk, at, M(XLIN[1], 0.766), XLIN[1]))
zed(S, one_input('P.c'), PANE_1, W1, H1)

# ------------------------------------------------------------------ traces
# How many curves will a pane take?  Straight horizontal lines at 1, 2, 3 ...
# so that the answer is however many are visible.
NT = 8
S.h2('9  HOW MANY TRACES WILL A PANE TAKE      count the horizontal lines')
S.note('Every pane in this project so far was fed exactly as many matrices as it was '
       'lifted with. This asks what happens otherwise, and the gain figure in the design '
       'guide depends on the answer: if a pane builds its curves from the input then six '
       'load curves and two marker lines fit in ONE frame, the way the Infineon guide '
       'draws them. If it only refills the curves it already holds, four is the ceiling '
       'whenever the y axis has to stay linear, and the figure has to be split.')
S.note('Each trace is a horizontal line at its own height, so there is nothing to judge - '
       'count them. T1 gives a FOUR-curve pane EIGHT lines: eight visible means any number '
       'works, four means the pane is the limit, none or red means it refuses. T2 gives a '
       'ONE-curve pane THREE. T3 goes the other way and gives a FOUR-curve pane only TWO, '
       'which matters just as much - a pane that will not draw when under-fed cannot be '
       'used for a small family.')
S.const('[PICK] points per line:', 'N.t', '21', None, 0)
S.prog(['j.t := range(1,N.t)'], label='- the range variable:', h=54, w=420)
S.prog(['el(X.t,j.t) := f.lo*(f.hi/f.lo)^((j.t-1)/(N.t-1))'],
       label='- the shared x axis:', h=56, w=700)
for _k in range(1, NT + 1):
    S.prog(['el(Y.%d,j.t) := %d' % (_k, _k)],
           label='- line %d, a constant:' % _k, h=54, w=420)
for _k in range(1, NT + 1):
    S.prog(['Q.%d := eval(augment(vectorize(X.t),vectorize(Y.%d)))' % (_k, _k)],
           label='- two-column matrix Q.%d:' % _k, h=56, w=760, allow=VEC)

_TX = 'normalised frequency   fn   (log)'
_TY = 'line number'
_T1 = ZS.make(4, 'transfer', 'T1  a FOUR-curve pane given EIGHT matrices', _TX, _TY,
              ['line 1', 'line 2', 'line 3', 'line 4'],
              (FLO, FHI), (0.0, float(NT + 1)), ysteps=(1.0, 0.5))
_T2 = ZS.make(1, 'transfer', 'T2  a ONE-curve pane given THREE', _TX, _TY,
              ['line 1'], (FLO, FHI), (0.0, float(NT + 1)), ysteps=(1.0, 0.5))
_T3 = ZS.make(4, 'transfer', 'T3  a FOUR-curve pane given TWO', _TX, _TY,
              ['line 1', 'line 2', 'line 3', 'line 4'],
              (FLO, FHI), (0.0, float(NT + 1)), ysteps=(1.0, 0.5))
_TP = (S.PAGE_W - 2 * S.MARGIN - (_T1[1] + 10)) // 2
ZS.emit(S, ['Q.%d' % k for k in range(1, NT + 1)], *_T1,
        x=S.MARGIN, advance=False)
ZS.emit(S, ['Q.1', 'Q.2', 'Q.3'], *_T2, x=S.MARGIN + _TP, advance=False)
ZS.emit(S, ['Q.1', 'Q.2'], *_T3, x=S.MARGIN + 2 * _TP, advance=True, reserve=NT)

S.h2('what the answer means')
S.note('T1 shows eight lines  ->  a pane builds its curves from the input, and the design '
       'guide gain figure becomes ONE frame with six loads and both marker lines. '
       'T1 shows four  ->  the pane is the ceiling; with a linear y that is four traces a '
       'frame and the figure stays split. T1 empty or red  ->  the count must match, and '
       'T3 then says whether under-feeding is allowed either.')

nbytes, ybottom = S.save(OUT)

s = io.open(OUT, encoding='utf-8').read()
if 'ZedGraph Region (ZedGraph)' not in s:
    s = s.replace('    </dependencies>', ZED_ASM + '    </dependencies>', 1)
    io.open(OUT, 'w', encoding='utf-8').write(s)

print('written %s\n  %d bytes, %d px, %d regions' % (OUT, len(s), ybottom, len(S.r)))
print('  four-curve pane %dx%d from TI pane #6; %d log axes made linear'
      % (W4, H4, NLOG))
print('  %d outlines at %g px (grid untouched); log axes step %g decade'
      % (NLINE, LINEW, LOGSTEP))
print('  x %s' % {k: v for k, v in Z.read_scale(_p4, XWIN).items()
                  if k in ('min', 'max', 'minAuto', 'maxAuto')})
for (tag, q), lab in zip(QS, LEGEND):
    print('  %-3s %s' % (tag, lab))
