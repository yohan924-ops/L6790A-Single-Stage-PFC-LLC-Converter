# -*- coding: utf-8 -*-
"""Builds  Smath/L6790A_gainplot.sm  -  can SMath draw an LLC gain curve?

A separate, small sheet on purpose. The design guide sheet is already 31.8
A3+ pages and this question does not belong in it until the answer is known.

The question has three parts and they are not equally settled:

  G3  ONE curve in ONE frame.  Certain - it is exactly what section 16.6 of
      the design sheet already does four times over, and the gain function
      needs nothing outside the confirmed set (sqrt and arithmetic).

  G4  FOUR curves in FOUR frames.  Certain for the same reason.

  G5  FOUR curves in ONE frame.  This is the actual question. The mechanism
      is sys(c1..cN, N, 1), seen in Reference/Smath Bode Plot Example/
      Project Admittance Copy.sm where S1(x) and S2(x) share a frame. Two
      things about it are unproven here: sys and mat are outside
      smsheet.SAFE_FUNCS and check_sm.ALLOWED, and nothing in this project
      has ever emitted them - so this build is the first time this PC's
      SMath is asked.

If G5 comes up empty or red while G4 is fine, the answer is "four frames",
and that costs nothing.

Everything is plotted against f_n = f_sw/f_r on a LINEAR axis, so unlike the
Bode plots there is no log10 substitution and no hand-written decade labels.

Run:  python build_gainplot.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smsheet import Sheet                                          # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'Smath',
                                    'L6790A_gainplot.sm'))

# the 7.5:1 design point, so the curves are the ones the AN prints
LAM = 0.55
QS = [('a', 0.20), ('b', 0.40), ('c', 0.766), ('d', 1.50)]
FLO, FHI, NPT = 0.55, 2.20, 91


def M(fn, q, lam=LAM):
    a = 1 + lam - lam / fn ** 2
    return 1.0 / math.sqrt(a * a + q * q * (fn - 1.0 / fn) ** 2)


def sys_input(names, indent='        '):
    """The <input> of a plot that carries several curves.

    sys(c1, ..., cN, N, 1) stacks N matrices into one plot. args is N+2
    because the row and column counts are arguments too, and preserve="true"
    is what the reference file carries on sys and mat - the generic emitter
    in smgen does not write it, so this is built by hand.
    """
    out = ['%s<e type="operand">%s</e>' % (indent, n) for n in names]
    out.append('%s<e type="operand">%d</e>' % (indent, len(names)))
    out.append('%s<e type="operand">1</e>' % indent)
    out.append('%s<e type="function" preserve="true" args="%d">sys</e>'
               % (indent, len(names) + 2))
    return '\n'.join(out)


def plot_xml(S, inner, x=None, w=540, h=280, attr=None, advance=True):
    """A plot whose input is given as XML rather than one variable name."""
    body = ('    <plot ' + (attr or S.PLOTATTR) + '>\n      <input>\n'
            + inner + '\n      </input>\n    </plot>')
    y0 = S.y
    S._emit(x if x is not None else S.LBL_X, w, h, body,
            ' color="#000000" fontSize="10"')
    S.y = y0 + (h + S.PLOT_CAPTION + S.gap if advance else 0)


S = Sheet('L6790A gain plot', 'L6790A project',
          'can SMath draw the LLC gain curve family?')

S.h1('Can SMath draw an LLC gain curve?  -  a standalone check')
S.note('Separate from the design sheet on purpose: this only answers whether the '
       'plotting works, and the design sheet is large enough already. '
       'Everything below uses only sqrt and arithmetic, which this build of SMath '
       'is known to have. The one construct that has never been tried here is '
       'sys() in G5.')

# ------------------------------------------------------------------ inputs
S.h2('G1  the gain function and two checks that need no plot at all')
S.note('M(f_n, Q, lambda) = 1 / sqrt( (1 + lambda - lambda/f_n^2)^2 '
       '+ Q^2 (f_n - 1/f_n)^2 ).   Two things are true whatever the tank, and if '
       'either fails here nothing below is worth looking at.')
S.const('[PICK] lambda = L.r / L.m:', 'λ', str(LAM), None, 3)
for tag, q in QS:
    S.const('[PICK] Q for curve %s:' % tag, 'Q.%s' % tag, str(q), None, 3)

def DEN(q, fn):
    return 'sqrt((1+λ-λ/%s^2)^2+%s^2*(%s-1/%s)^2)' % (fn, q, fn, fn)
S.const('- first test frequency, at resonance:', 'f.na', '1', None, 3)
S.row('- M at f.n = 1 with the LIGHTEST load, must be 1.0000:',
      'g.1a', '1/' + DEN('Q.a', 'f.na'), None, 4, expect=1.0)
S.row('- M at f.n = 1 with the HEAVIEST load, must be 1.0000 too:',
      'g.1b', '1/' + DEN('Q.d', 'f.na'), None, 4, expect=1.0)
S.note('That is the series resonance: the second term under the root vanishes and the '
       'first becomes 1, so every gain curve passes through the same point. '
       'It is also why f_n = 1 is a poor place to check a gain formula - a wrong one '
       'can still give 1 there.')
S.const('- second test frequency, above resonance:', 'f.nb', '2', None, 3)
S.note('A SEPARATE name, not f.na reassigned. SMath would evaluate a reassignment in row order and get it right, but a reader - and any tool that re-reads the file - has to know that to follow it. Two names cost nothing.')
S.row('- M at f.n = 2, no-load asymptote is 1/(1+lambda) = %.4f:'
      % (1 / (1 + LAM)), 'g.1c', '1/' + DEN('0', 'f.nb'), None, 4,
      expect=M(2.0, 0.0))
S.row('- M at f.n = 2 at full load:', 'g.1d', '1/' + DEN('Q.c', 'f.nb'), None, 4,
      expect=M(2.0, 0.766))

# ------------------------------------------------------------------ sweep
S.h2('G2  fill the curves  -  one pass, four matrices')
S.const('[PICK] sweep from f.n =', 'f.lo', str(FLO), None, 3)
S.const('[PICK] sweep to   f.n =', 'f.hi', str(FHI), None, 3)
S.const('[PICK] points per curve:', 'N.g', str(NPT), None, 0)
S.note('Each G.x is an N x 2 matrix: column 1 is f_n, column 2 is the gain. That is the '
       'shape section 16.6 of the design sheet builds for its Bode curves, and the only '
       'shape a 2D plot reads directly.')
body = ['x.g := f.lo+(k.g-1)*(f.hi-f.lo)/(N.g-1)']
for tag, _ in QS:
    body += ['el(G.%s,k.g,1) := x.g' % tag,
             'el(G.%s,k.g,2) := 1/sqrt((1+λ-λ/x.g^2)^2+Q.%s^2*(x.g-1/x.g)^2)'
             % (tag, tag)]
S.prog([('for', 'k.g', 'range(1,N.g)', body)],
       label='- fill all four curves in one pass:', h=300, w=720)
S.row('- spot check, G.c at the last point:', 'g.2a',
      'el(G.c,N.g,2)', None, 4, expect=M(FHI, 0.766), allow=())
S.row('- and its f_n, must be %.2f:' % FHI, 'g.2b',
      'el(G.c,N.g,1)', None, 4, expect=FHI, allow=())

# ------------------------------------------------------------------ plots
# 0..5, not 0..3: the lightest curve peaks at 4.67 and a curve that leaves
# the window is the classic way to get a plot that looks empty
YTOP = 5.0
XLO, XHI = FLO - 0.05, FHI + 0.05
VIEW = Sheet.plot_view(540, 300, XLO, XHI, 0.0, YTOP)

S.h2('G2b  which grid division does this SMath use?   pick the frame that fits')
S.note('All four frames below ask for the SAME window - f_n %.2f to %.2f, gain 0 to %.0f - '
       'and differ only in the pixels-per-division constant used to compute it. Exactly '
       'one of them should show the full-load curve filling the frame, rising to about '
       '%.2f near f_n %.2f and falling to about %.2f at the right edge. The others will '
       'show it squeezed into a corner or not at all.'
       % (XLO, XHI, YTOP, max(M(FLO + i * (FHI - FLO) / 2000.0, 0.766)
                              for i in range(2001)),
          max(((M(FLO + i * (FHI - FLO) / 2000.0, 0.766),
                FLO + i * (FHI - FLO) / 2000.0) for i in range(2001)))[1],
          M(FHI, 0.766)))
S.note('This block exists because the constant was wrong once and a comment in the code '
       'claimed it was right. A picture settles it; a comment does not.')
for i, d in enumerate((20.0, 8.0, 4.0, 2.0)):
    S.plot('G.c', x=20 + (i % 2) * 560, w=540, h=260,
           attr=Sheet.plot_view(540, 260, XLO, XHI, 0.0, YTOP, div=d),
           advance=(i % 2 == 1))
S.note('- left to right, top row then bottom:  division = 20 px,  8 px,  4 px,  2 px. '
       'The sheet below is drawn with %g px, which is what P19 of the probe sheet '
       'measured. If a different frame above is the right one, that number is what '
       'smsheet.Sheet.PLOT_DIV should become.' % Sheet.PLOT_DIV)

S.h2('G3  ONE curve in ONE frame        expected: full-load curve, peak about %.2f'
     % max(M(FLO + i * (FHI - FLO) / 400.0, 0.766) for i in range(401)))
S.note('x is f_n from %.2f to %.2f, y is gain from 0 to 5, both fixed - SMath has no '
       'auto-scale, and a curve outside the window looks like an empty plot rather '
       'than an error. Mouse wheel zooms, dragging pans.' % (FLO, FHI))
S.plot('G.c', w=540, h=300, attr=VIEW)

S.h2('G4  FOUR curves in FOUR frames                  expected: four separate curves')
S.note('Q = %s, left to right, top row then bottom. Lighter load gives the taller, '
       'more peaked curve. This is the fallback if G5 comes up empty, and it costs '
       'nothing but page area.' % ', '.join('%.3g' % q for _, q in QS))
S.plot('G.a', x=20, w=540, h=300, attr=VIEW, advance=False)
S.plot('G.b', x=580, w=540, h=300, attr=VIEW)
S.plot('G.c', x=20, w=540, h=300, attr=VIEW, advance=False)
S.plot('G.d', x=580, w=540, h=300, attr=VIEW)

S.h2('G5  FOUR curves in ONE frame                    THIS IS THE QUESTION')
S.note('sys(G.a, G.b, G.c, G.d, 4, 1) stacks the four matrices into one plot input. '
       'The construct is taken from Project Admittance Copy.sm, which puts S1(x) and '
       'S2(x) in one frame the same way. If the frame below shows four curves the '
       'family plot is available; if it is empty or red, use G4 instead. '
       'SMath prints no legend, so the curves would have to be named in text - '
       'lighter load is the taller curve.')
plot_xml(S, sys_input(['G.%s' % t for t, _ in QS]),
         w=1100, h=380,
         attr=Sheet.plot_view(1100, 380, FLO - 0.05, FHI + 0.05, 0.0, YTOP))

S.note('What to report back: which of G3, G4, G5 drew, and whether any region is red.')

nbytes, ybottom = S.save(OUT)
print('written %s\n  %d bytes, %d px, %d regions' % (OUT, nbytes, ybottom, len(S.r)))
print('  expected: M(1)=1.0000 · M(2,Q=0)=%.4f · M(2,Q=0.766)=%.4f'
      % (M(2.0, 0.0), M(2.0, 0.766)))
for tag, q in QS:
    pk = max((M(FLO + i * (FHI - FLO) / 2000.0, q), FLO + i * (FHI - FLO) / 2000.0)
             for i in range(2001))
    print('  curve %s  Q=%-6.3g peak %.3f at f_n %.3f' % (tag, q, pk[0], pk[1]))
