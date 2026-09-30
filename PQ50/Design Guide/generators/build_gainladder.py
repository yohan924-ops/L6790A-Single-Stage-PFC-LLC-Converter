# -*- coding: utf-8 -*-
"""Builds  Smath/L6790A_gainladder.sm  -  why does P19 draw and the gain sheet not?

P19 of the probe sheet draws a line. The gain sheet draws nothing, at any
of four calibrations. Both are built by the same code and their token
streams have the same shape - range args=2, el args=3, line args=N+2,
for args=3 - so the difference is in what the loop is asked to do, not in
how it is written.

Four things differ, and this sheet changes them ONE AT A TIME:

    P18 (draws)          gain sheet (does not)
    range(1, 11)         range(1, N.g)      - literal bound vs variable
    5 statements         9 statements       - line args 7 vs 11
    1 matrix             4 matrices
    11 points            91 points

Every rung prints a number BEFORE its plot. That matters: an empty frame
means either "no data" or "data off-screen", and only the number tells them
apart. If the readout is right and the frame is empty, the window is wrong;
if the readout is missing or red, the loop is.

L1  literal bound, 3 statements, 1 matrix, 11 points   <- closest to P18
L2  variable bound
L3  4 matrices, 9 statements
L4  91 points

The first rung that stops drawing names the cause.

Run:  python build_gainladder.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smsheet import Sheet                                          # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'Smath',
                                    'L6790A_gainladder.sm'))

LAM = 0.55
QC = 0.766
FLO, FHI = 0.55, 2.20
XLO, XHI, YTOP = FLO - 0.05, FHI + 0.05, 2.0
W, H = 520, 260


def M(fn, q=QC, lam=LAM):
    a = 1 + lam - lam / fn ** 2
    return 1.0 / math.sqrt(a * a + q * q * (fn - 1.0 / fn) ** 2)


def pts(n):
    return [FLO + i * (FHI - FLO) / (n - 1) for i in range(n)]


GAIN = '1/sqrt((1+λ-λ/{x}^2)^2+Q.c^2*({x}-1/{x})^2)'


def plot_xml(S, inner, x=None, w=520, h=260, attr=None, advance=True):
    """A plot whose input is XML rather than one variable name."""
    body = ('    <plot ' + (attr or S.PLOTATTR) + '>\n      <input>\n'
            + inner + '\n      </input>\n    </plot>')
    y0 = S.y
    S._emit(x if x is not None else S.LBL_X, w, h, body,
            ' color="#000000" fontSize="10"')
    S.y = y0 + (h + S.PLOT_CAPTION + S.gap if advance else 0)


def math_xml(S, inner, x=None, w=700, h=60, label=None):
    """A math region whose RPN is given as XML - bypasses the allow-list.

    Used only for constructs proven in the reference sheets but absent from
    smsheet.SAFE_FUNCS: eval, augment, vectorize, and a function definition
    on the left of the assignment.
    """
    # the label needs its own line: _emit does not advance y, so a label and
    # a region asked for at the same y land on top of each other
    if label:
        S.y += S._label(label)
    y0 = S.y
    body = ('    <math decimalPlaces="4" exponentialThreshold="5">\n'
            '      <input>\n' + inner + '\n      </input>\n    </math>')
    S._emit(x if x is not None else S.LBL_X, w, h, body)
    S.y = y0 + h + S.gap


def op(name):
    return '        <e type="operand">%s</e>' % name


def fn(name, n):
    return '        <e type="function" args="%d">%s</e>' % (n, name)


def opr(sym, n=2):
    return '        <e type="operator" args="%d">%s</e>' % (n, sym)


S = Sheet('L6790A gain ladder', 'L6790A project',
          'which construct stops the plot drawing?')

S.h1('Why does P19 draw and the gain sheet not?  -  one change per rung')
S.note('Every rung below prints a number and then plots the same curve. The number says '
       'whether the matrix exists; the frame says whether the window found it. '
       'Read them in order and stop at the first rung that goes wrong - that rung names '
       'the cause. Expected shape every time: a hump rising to about %.3f near f_n 0.69 '
       'and falling to %.3f at the right edge.' % (max(M(x) for x in pts(2001)), M(FHI)))
S.const('[PICK] lambda:', 'λ', str(LAM), None, 3)
S.const('[PICK] Q of the drawn curve:', 'Q.c', str(QC), None, 3)

S.note('WHAT IS ALREADY KNOWN. In the gain sheet SMath wrote back '
       'el(G.c,91,1) = 2.2 and el(G.c,91,2) = 0.5096, both correct, so the loop, the '
       'formula and el() are all working and the matrices are real. Whatever is wrong '
       'is in the plotting alone.')
S.note('THE ONE THING WORTH DOING IF NOTHING BELOW DRAWS. SMath re-saves this file '
       'keeping every plot attribute, so it can be asked directly. Take any one frame, '
       'drag it and roll the mouse wheel until the curve is visible, then save the file '
       'and say so. The window you reached is then written into the file as scale_x, '
       'scale_y, transpose_x and transpose_y, and the correct calibration can be read '
       'off it exactly - no more arithmetic about what a grid division is.')

VIEW = Sheet.plot_view(W, H, XLO, XHI, 0.0, YTOP)

# ----------------------------------------------------------------- rung 1
S.h2('L1  literal bound, 3 statements, 1 matrix, 11 points     closest to P18')
S.note('P18 fills its matrix with range(1,11) and five statements, and P19 plots it. '
       'This is the same shape with the gain formula in place of the dB line.')
S.prog([('for', 'k.1', 'range(1,11)', [
    'x.1 := %g+(k.1-1)*%g/10' % (FLO, FHI - FLO),
    'el(T.1,k.1,1) := x.1',
    'el(T.1,k.1,2) := ' + GAIN.format(x='x.1'),
])], label='- fill T.1:', h=200, w=700)
S.row('- T.1 last point, f_n must be %.2f:' % FHI, 'r.1a',
      'el(T.1,11,1)', None, 4, expect=FHI, allow=())
S.row('- T.1 last point, gain must be %.4f:' % M(FHI), 'r.1b',
      'el(T.1,11,2)', None, 4, expect=M(FHI), allow=())
S.plot('T.1', w=W, h=H, attr=VIEW)

# ----------------------------------------------------------------- rung 2
S.h2('L2  the only change is a VARIABLE bound in range()')
S.const('- point count as a variable:', 'N.2', '11', None, 0)
S.prog([('for', 'k.2', 'range(1,N.2)', [
    'x.2 := %g+(k.2-1)*%g/(N.2-1)' % (FLO, FHI - FLO),
    'el(T.2,k.2,1) := x.2',
    'el(T.2,k.2,2) := ' + GAIN.format(x='x.2'),
])], label='- fill T.2:', h=200, w=700)
S.row('- T.2 last point, gain must be %.4f:' % M(FHI), 'r.2b',
      'el(T.2,N.2,2)', None, 4, expect=M(FHI), allow=())
S.plot('T.2', w=W, h=H, attr=VIEW)

# ----------------------------------------------------------------- rung 3
S.h2('L3  the only change is FOUR matrices and nine statements')
S.note('line() carries 11 arguments here instead of 5. Section 16.6 of the design sheet '
       'uses 14 and MyBode.sm never goes past 8, so this is the widest untested case.')
body = ['x.3 := %g+(k.3-1)*%g/(N.2-1)' % (FLO, FHI - FLO)]
for t in 'abcd':
    body += ['el(T.3%s,k.3,1) := x.3' % t,
             'el(T.3%s,k.3,2) := ' % t + GAIN.format(x='x.3')]
S.prog([('for', 'k.3', 'range(1,N.2)', body)],
       label='- fill T.3a .. T.3d:', h=320, w=900)
S.row('- T.3c last point, gain must be %.4f:' % M(FHI), 'r.3b',
      'el(T.3c,N.2,2)', None, 4, expect=M(FHI), allow=())
S.plot('T.3c', w=W, h=H, attr=VIEW)

# ----------------------------------------------------------------- rung 4
S.h2('L4  the only change is 91 points instead of 11')
S.const('- point count:', 'N.4', '91', None, 0)
S.prog([('for', 'k.4', 'range(1,N.4)', [
    'x.4 := %g+(k.4-1)*%g/(N.4-1)' % (FLO, FHI - FLO),
    'el(T.4,k.4,1) := x.4',
    'el(T.4,k.4,2) := ' + GAIN.format(x='x.4'),
])], label='- fill T.4:', h=200, w=700)
S.row('- T.4 last point, gain must be %.4f:' % M(FHI), 'r.4b',
      'el(T.4,N.4,2)', None, 4, expect=M(FHI), allow=())
S.plot('T.4', w=W, h=H, attr=VIEW)

# ----------------------------------------------------------------- rung 6
S.h2('L6  the TI app note idiom      one index, augment(), eval()')
S.note('SMPS_Input_Filter_Design_TI_APP_Note.sm fills COLUMN VECTORS with a single '
       'index - el(f, j), not el(f, j, 1) - and then glues them with '
       'eval(augment(vectorize(x), vectorize(y))). Three differences from L1 at once, '
       'but every one of them is taken from a sheet that renders here. It also proves '
       'eval, augment and vectorize exist, which this project had assumed they did not.')
S.prog([('for', 'k.6', 'range(1,N.2)', [
    'el(X.6,k.6) := %g+(k.6-1)*%g/(N.2-1)' % (FLO, FHI - FLO),
    'el(Y.6,k.6) := ' + GAIN.format(x='el(X.6,k.6)'),
])], label='- fill two column vectors:', h=200, w=760)
S.row('- Y.6 last point, gain must be %.4f:' % M(FHI), 'r.6b',
      'el(Y.6,N.2)', None, 4, expect=M(FHI), allow=())
math_xml(S, '\n'.join([
    op('P.6'),
    op('X.6'), fn('vectorize', 1),
    op('Y.6'), fn('vectorize', 1),
    fn('augment', 2), fn('eval', 1),
    opr(':'),
]), label='- glue them the way the TI sheet does:', w=760, h=64)
S.plot('P.6', w=W, h=H, attr=VIEW)

# ----------------------------------------------------------------- rung 7
S.h2('L7  no matrix at all      plot a FUNCTION of the plot variable')
S.note('Project Admittance Copy.sm puts S1(x) and S2(x) straight into a plot. For a '
       'closed-form gain curve that is the obvious thing to do - no loop, no matrix, '
       'nothing to fill - and it was never tried here. If this rung draws and the '
       'others do not, the whole matrix approach can be dropped.')
math_xml(S, '\n'.join([
    op('x'), fn('M.f', 1),
    op('1'),
    op('1'), op('λ'), opr('+'),
    op('λ'), op('x'), op('2'), opr('^'), opr('/'), opr('-'),
    '        <e type="bracket">(</e>',
    op('2'), opr('^'),
    op('Q.c'), op('2'), opr('^'),
    op('x'), op('1'), op('x'), opr('/'), opr('-'),
    '        <e type="bracket">(</e>',
    op('2'), opr('^'), opr('*'), opr('+'),
    fn('sqrt', 1), opr('/'),
    opr(':'),
]), label='- define the gain as a function of x:', w=760, h=64)
S.note('- M.f(1) must be 1.0000 whatever Q, and M.f(%.2f) must be %.4f.'
       % (FHI, M(FHI)))
plot_fx = '\n'.join([op('x'), fn('M.f', 1)])
plot_xml(S, plot_fx, w=W, h=H, attr=VIEW)

S.h2('L5  the same T.1 at four grid divisions      only one window can be right')
S.note('If L1 printed its numbers but drew nothing, the matrix is fine and the window is '
       'not. These four ask for the identical window and differ only in the pixels per '
       'grid division: 20, 8, 4, 2 - left to right, top row then bottom.')
for i, d in enumerate((20.0, 8.0, 4.0, 2.0)):
    S.plot('T.1', x=20 + (i % 2) * 560, w=W, h=H,
           attr=Sheet.plot_view(W, H, XLO, XHI, 0.0, YTOP, div=d),
           advance=(i % 2 == 1))
S.note('- what to report: for each of L1..L4, did the number print and did the frame draw; '
       'and in L5, which of the four frames holds the curve.')

nbytes, ybottom = S.save(OUT)
print('written %s\n  %d bytes, %d px, %d regions' % (OUT, nbytes, ybottom, len(S.r)))
print('  every rung must print  f_n %.2f  and  gain %.4f' % (FHI, M(FHI)))
print('  curve peaks at %.4f near f_n %.3f'
      % max((M(x), x) for x in pts(2001)))
