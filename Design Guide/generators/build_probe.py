# -*- coding: utf-8 -*-
"""Builds  Smath/L6790A_probe.sm  -  a 2-page diagnostic sheet.

If the full design guide sheet refuses to open or shows red regions, open this
one instead: each numbered probe uses exactly ONE construct, so the first probe
that fails names the cause.  Expected values are in the labels.

This build of SMath does NOT have  min()  max()  if()  acos()  tan()  -- it
reports "정의되지 않은 함수입니다".  The probes below use only the confirmed set
  sqrt  abs  ln  exp  atan  cos  sin
and check the rewrites that replace the missing ones.

Run:  python build_probe.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smsheet import Sheet                                          # noqa: E402


def MIN(a, b, u=None):
    d = "%s/'%s-%s/'%s" % (a, u, b, u) if u else "%s-%s" % (a, b)
    t = "abs(%s)" % d + ("*'%s" % u if u else "")
    return "(%s+%s-%s)/2" % (a, b, t)


def MAX(a, b, u=None):
    d = "%s/'%s-%s/'%s" % (a, u, b, u) if u else "%s-%s" % (a, b)
    t = "abs(%s)" % d + ("*'%s" % u if u else "")
    return "(%s+%s+%s)/2" % (a, b, t)


def ACOS(z):
    return "2*atan(sqrt(1-(%s)^2)/(1+(%s)))" % (z, z)


def TAN(x):
    return "sin(%s)/cos(%s)" % (x, x)


OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'Smath', 'L6790A_probe.sm'))
S = Sheet('L6790A probe', 'L6790A project', 'construct-by-construct diagnostic')

S.h1('L6790A worksheet probes  -  the first red region names the cause')
S.note('Each probe uses one construct only. Compare with the expected value in the label. '
       'Only these functions are used anywhere: sqrt, abs, atan, cos, sin.')

S.h2('P1  plain number, no unit                        expected 3.0000')
S.row('- plain assignment:', 'p.1', '1+2', None, 4)

S.h2('P2  a value carrying a unit                      expected 90.0000 V')
S.const('- unit on an input:', 'p.2', "90*'V", 'V', 4)

S.h2('P3  display unit via <contract>                  expected 150.0000 kHz')
S.row('- contract to kHz:', 'p.3', "150000*'Hz", 'kHz', 4)

S.h2('P4  the resistance unit is lower-case ohm        expected 0.0240 ohm')
S.const('- ohm (NOT Ohm):', 'p.4', "0.024*%ohm", 'ohm', 4)

S.h2('P5  mixed units must cancel                      expected 700.0000 W')
S.row('- ohm*W / ohm:', 'p.5', "16.8*%ohm*'W/p.4", 'W', 4)

S.h2('P6  fractional power on a pure number            expected 1.4142')
S.row('- sqrt:', 'p.6', "sqrt(2)", None, 4)

S.h2('P7  a ratio of two unit-carrying values is unitless      expected 0.6000')
S.row('- V / V:', 'p.7', "p.2/(150*'V)", None, 4)

S.h2('P8  atan   (arctan does NOT exist)               expected 0.7854')
S.row('- atan(1):', 'p.8', "atan(1)", None, 4)

S.h2('P9  abs on a PURE NUMBER  (never on a unit-carrying value)   expected 4.0000')
S.row('- abs:', 'p.9', "abs(3-7)", None, 4)

S.h2('P10  min / max rewritten with abs                expected 3.0000 / 5.0000')
S.note('   min(a,b) = (a+b-|a-b|)/2      max(a,b) = (a+b+|a-b|)/2')
S.row('- min(3,5):', 'p.10a', MIN('3', '5'), None, 4)
S.row('- max(3,5):', 'p.10b', MAX('3', '5'), None, 4)

S.h2('P11  the same on values that carry a unit        expected 180.0000 V / 264.0000 V')
S.const('- a:', 'p.11a', "180*'V", 'V', 4)
S.const('- b:', 'p.11b', "264*'V", 'V', 4)
S.row('- min with the unit divided out:', 'p.11c', MIN('p.11a', 'p.11b', 'V'), 'V', 4)
S.row('- max with the unit divided out:', 'p.11d', MAX('p.11a', 'p.11b', 'V'), 'V', 4)
S.note('   If P11 is right but a later ln() or fractional power fails, the unit tag from '
       'abs() is the cause - SMath pitfall 3 of README.txt.')

S.h2('P12  acos rewritten with atan                    expected 1.0472 / 2.0944')
S.note('   acos(z) = 2*atan( sqrt(1-z^2) / (1+z) )')
S.row('- acos(0.5):', 'p.12a', ACOS('0.5'), None, 4)
S.row('- acos(-0.5):', 'p.12b', ACOS('-0.5'), None, 4)

S.h2('P13  tan rewritten with sin/cos                  expected 1.1918')
S.row('- tan(50 deg):', 'p.13', TAN("50*π/180"), None, 4)

S.h2('P14  pi                                          expected 3.1416')
S.row('- pi:', 'p.14', 'π', None, 4)

S.h2('P15  the full Cardano block of section 8         expected f.n = 0.8356')
S.note('This is what the line-cycle operating point depends on. lambda, Q and M are entered '
       'directly so the probe stands alone. The physical root is ALWAYS the k = 1 branch, so '
       'no root selection is needed.')
S.const('- lambda:', 'q.lam', '0.540284', None, 6)
S.const('- Q at the line peak:', 'q.Q', '0.780512', None, 6)
S.const('- required gain at the line peak:', 'q.M', '1.224745', None, 6)
S.pack([
    ('q.th', "π/2"), ('q.u', "sin(q.th)^2"), ('q.q', "q.Q^2*q.u^2"),
    ('q.a2', "(q.q-2*q.lam*(1+q.lam))/q.lam^2"),
    ('q.a1', "((1+q.lam)^2-2*q.q-q.u/q.M^2)/q.lam^2"),
    ('q.a0', "q.q/q.lam^2"),
    ('q.p', "q.a1-q.a2^2/3"),
    ('q.r', "2*q.a2^3/27-q.a2*q.a1/3+q.a0"),
    ('q.ang', ACOS("3*q.r/(2*q.p)*sqrt(-3/q.p)") + "/3"),
    ('q.w', "2*sqrt(-q.p/3)"),
    ('q.x', "q.w*cos(q.ang-2*π/3)-q.a2/3"),
])
S.row('- normalized switching frequency:', 'q.fn', "1/sqrt(q.x)", None, 5)
S.note('   expected  q.x = 1.43277 ,  q.fn = 0.83543')

S.h2('P16  every unit token the design sheet uses')
S.note('HVLED101 only proves V A W Hz kHz mm cm mA μF μH μs ms nH T J. The rest are used by '
       'the design sheet and are checked here. Each row must show the SAME number it was '
       'written with; if a unit is unknown, that row goes red.')
UNIT_PROBES = [
    ('u.V', "1*'V", 'V'), ('u.A', "1*'A", 'A'), ('u.W', "1*'W", 'W'),
    ('u.Hz', "1*'Hz", 'Hz'), ('u.kHz', "1*'kHz", 'kHz'),
    ('u.ohm', "1*'ohm", 'ohm'),
    ('u.kohm', "1*'kohm", 'kohm'), ('u.mohm', "1*'mohm", 'mohm'),
    ('u.mF', "1*'mF", 'mF'), ('u.uF', "1*'μF", 'μF'),
    ('u.nF', "1*'nF", 'nF'), ('u.pF', "1*'pF", 'pF'),
    ('u.uH', "1*'μH", 'μH'), ('u.nH', "1*'nH", 'nH'),
    ('u.s', "1*'s", 's'), ('u.ms', "1*'ms", 'ms'),
    ('u.us', "1*'μs", 'μs'), ('u.ns', "1*'ns", 'ns'),
    ('u.uA', "1*'μA", 'μA'), ('u.mm', "1*'mm", 'mm'),
    ('u.mT', "1*'mT", 'mT'),
]
S.pack([(n, e, un, 4) for n, e, un in UNIT_PROBES], per=4)
S.note('   All twenty-one must read 1.0000 in their own unit. kohm and mohm are the '
       'two newest - section 19 of the design sheet prints resistors in them so the '
       'BOM is readable, and they are the only units there that HVLED101 does not '
       'already prove.')

S.h2('P17  a unit-carrying quantity through a fractional power')
S.note('   the failure mode of SMath pitfall 3: a stray unit tag blocks ^0.5 and ln()')
S.row('- ratio made explicitly unitless:', 'p.17a', "(264*'V)/(173.24*%V)", None, 4)
S.row('- and then raised to a fractional power:', 'p.17b', "p.17a^0.5", None, 4)
S.note('   expected 1.5239 and 1.2345')

S.h2('P18  the loop that a Bode plot needs  -  for / range / line / el')
S.note('Nothing above this point builds a matrix. A plot needs one. The block below is the '
       'same shape as the one in section 16.6 of the design sheet, cut down to 11 points. '
       'It uses only  for  range  line  el  -  the four names both reference sheets in '
       'Reference/Smath Bode Plot Example/ rely on. If THIS region is red, the design '
       'sheet cannot plot and I will fall back to a printed table.')
S.prog([('for', 'k.p', 'range(1,11)', [
    'x.p := (k.p-1)/5-1',
    "w.p := 2*π*10^x.p*'Hz",
    "g.p := 100*'Hz/w.p",
    'el(T.p,k.p,1) := x.p',
    'el(T.p,k.p,2) := 20*ln(g.p)/ln(10)',
])], label='- eleven points of a pure integrator, x = log10(f/Hz):', h=150)
S.note('   The two traps this checks at once: (a) a matrix element assigned inside a loop, '
       '(b) ln() of a ratio that is only dimensionless because the unit tag was written '
       "explicitly - w.p carries 'Hz so that 100 Hz / w.p is a pure number (pitfall 3).")
S.row('- second point of column 1, must be -0.8000:', 'p.18a',
      'el(T.p,2,1)', None, 4, expect=-0.8000000000, allow=())
S.row('- second point of column 2, must be 40.0364:', 'p.18b',
      'el(T.p,2,2)', None, 4, expect=40.0364026328, allow=())
S.note('   f = 10^-0.8 Hz = 0.1585 Hz, so |100 Hz / (2*pi*0.1585 Hz)| = 100.4 -> 40.04 dB.')

S.h2('P19  the plot region itself                    expected a straight falling line')
S.note('A 2D plot of the N x 2 matrix built by P18. x is log10(f/Hz) from -1 to +1, y is dB '
       'from 44.0 down to 4.0 - one straight falling line of slope -20 dB/decade. '
       'SMath has no logarithmic axis, so the x axis carries log10(f) '
       'and the decade labels are written in the text instead - that is what MyBode.sm does '
       'too. Mouse wheel zooms, dragging pans; if the view opens somewhere empty that is a '
       'view setting, not a broken plot.')
S.plot('T.p', w=520, h=260, attr=S.plot_view(520, 260, -1.2, 1.2, 0.0, 50.0))

S.h2('P20  a collapsed area                        expected ONE grey line, click to open')
S.note('MyBode.sm hides its machinery in a collapsed AreaRegion; sections 8, 10, 16.4 and '
       '16.6 of the design sheet do the same. If this probe shows the three rows below '
       'expanded instead of one collapsed strip, the AreaRegion assembly version in your '
       'build differs and the design sheet will simply look longer - nothing computes wrong.')
S.area_begin('three rows that should be hidden')
S.row('- hidden row 1:', 'p.20a', '1+1', None, 4)
S.row('- hidden row 2:', 'p.20b', 'p.20a*3', None, 4)
S.row('- hidden row 3:', 'p.20c', 'sqrt(p.20b)', None, 4)
S.area_end()
S.row('- visible again, must be 2.4495:', 'p.20d', 'p.20c', None, 4)

# ---------------------------------------------------------------- P21-25
# The section 14c sweep comes up red and its expression is correct - the
# builder string agrees with section 8 to the digit and the RPN reads back
# exactly as intended. So the fault is in a CONSTRUCT, and these take them
# one at a time.
import math as _m                                                # noqa: E402

_LAM = 0.4583333333333333
_QPK = 0.5001479368730567
_MPK = 1.5209591836734695
_FR = 151.7482841316334          # kHz

S.h2('P21  cos of a vector element                  expected 0.5403 then -0.4161')
S.note('Everything else section 14c uses inside a vector - sqrt, atan, ln, division, pi - '
       'is already drawn by section 16.6. cos is the one construct that has only ever been '
       'used on scalars. If this is the one that fails, the sweep has to be rewritten '
       'without it, and there is a way: cos(x) can come from atan and sqrt.')
S.const('- three points:', 'N.p21', '3', None, 0)
S.prog(['k.p21 := range(1,N.p21)'], label='- range variable:', h=54, w=420)
S.prog(['el(v.p21,k.p21) := k.p21-1'], label='- 0, 1, 2:', h=54, w=460)
S.prog(['el(c.p21,k.p21) := cos(el(v.p21,k.p21))'],
       label='- cos of each:', h=54, w=560)
S.row('- cos(1), must be 0.5403:', 'p.21a', 'el(c.p21,2)', None, 4,
      expect=_m.cos(1.0), allow=())
S.row('- cos(2), must be -0.4161:', 'p.21b', 'el(c.p21,3)', None, 4,
      expect=_m.cos(2.0), allow=())

S.h2('P22  unary minus and sqrt of a vector element        expected 2.0000')
S.prog(['el(w.p22,k.p21) := -3*k.p21'], label='- -3, -6, -9:', h=54, w=460)
S.prog(['el(r.p22,k.p21) := 2*sqrt(-el(w.p22,k.p21)/3)'],
       label='- 2*sqrt(-w/3):', h=56, w=620)
S.row('- at k = 1, must be 2:', 'p.22', 'el(r.p22,1)', None, 4,
      expect=2.0, allow=())

S.h2('P23  the arc-cosine identity on a vector             expected 0.3335')
S.prog(['el(z.p23,k.p21) := 0.5*k.p21-0.75'],
       label='- -0.25, 0.25, 0.75:', h=54, w=520)
S.prog(['el(a.p23,k.p21) := 2*atan(sqrt(1-el(z.p23,k.p21)^2)'
        '/(1+el(z.p23,k.p21)))/3'],
       label='- acos(z)/3 written without acos:', h=58, w=880)
S.row('- at z = 0.25, must be 0.4386:', 'p.23', 'el(a.p23,2)', None, 4,
      expect=_m.acos(0.25) / 3, allow=())

S.h2('P24  a scalar over a vector expression               expected 0.5000')
S.const('- a scalar:', 'q.p24', '2', None, 0)
S.prog(['el(d.p24,k.p21) := q.p24/sqrt(4*k.p21^2)'],
       label='- q/sqrt(4k^2):', h=56, w=620)
S.row('- at k = 2, must be 0.5:', 'p.24', 'el(d.p24,2)', None, 4,
      expect=0.5, allow=())

S.h2('P25  the whole f.sw chain, five phases        expected 108.48 kHz at pi/2')
S.note('The same cubic section 8 solves, swept over theta, exactly as section 14c writes '
       'it - the same order, the same intermediates, the same names. The last row is the '
       'line peak, where section 8 of the design sheet gives 108.48 kHz from a completely '
       'different block. If P21 to P24 all pass and this one fails, the fault is in the '
       'combination rather than in any one construct.')
S.const('- lambda:', 'L.p25', '%.10f' % _LAM, None, 6)
S.const('- Q at the line peak:', 'Q.p25', '%.10f' % _QPK, None, 6)
S.const('- required gain at the line peak:', 'M.p25', '%.10f' % _MPK, None, 6)
S.const('- series resonance [kHz]:', 'F.p25', '%.6f' % _FR, None, 4)
S.const('- points:', 'N.p25', '5', None, 0)
S.prog(['k.p25 := range(1,N.p25)'], label='- range variable:', h=54, w=420)
S.prog(['el(t.p25,k.p25) := 0.05+(k.p25-1)*(\u03c0/2-0.05)/(N.p25-1)'],
       label='- theta, 0.05 up to pi/2:', h=56, w=740)
S.prog(['el(s.p25,k.p25) := sin(el(t.p25,k.p25))'],
       label='- sin(theta):', h=54, w=480)
S.prog(['el(q.p25,k.p25) := Q.p25*el(s.p25,k.p25)^2'],
       label='- Q(theta):', h=54, w=520)
S.prog(['el(A2.p25,k.p25) := (el(q.p25,k.p25)^2-2*(1+L.p25)*L.p25)/L.p25^2'],
       label='- cubic a2:', h=56, w=800)
S.prog(['el(A0.p25,k.p25) := el(q.p25,k.p25)^2/L.p25^2'],
       label='- cubic a0:', h=54, w=520)
S.prog(['el(A1.p25,k.p25) := ((1+L.p25)^2-2*el(q.p25,k.p25)^2'
        '-(el(s.p25,k.p25)/M.p25)^2)/L.p25^2'],
       label='- cubic a1:', h=58, w=940)
S.prog(['el(P.p25,k.p25) := el(A1.p25,k.p25)-el(A2.p25,k.p25)^2/3'],
       label='- depressed p:', h=56, w=680)
S.prog(['el(Q2.p25,k.p25) := 2*el(A2.p25,k.p25)^3/27'
        '-el(A2.p25,k.p25)*el(A1.p25,k.p25)/3+el(A0.p25,k.p25)'],
       label='- depressed q:', h=58, w=880)
S.prog(['el(Z.p25,k.p25) := 3*el(Q2.p25,k.p25)/(2*el(P.p25,k.p25))'
        '*sqrt(-3/el(P.p25,k.p25))'],
       label='- the arc-cosine argument:', h=58, w=860)
S.prog(['el(X.p25,k.p25) := 2*sqrt(-el(P.p25,k.p25)/3)'
        '*cos(2*atan(sqrt(1-el(Z.p25,k.p25)^2)/(1+el(Z.p25,k.p25)))/3'
        '-2*\u03c0/3)-el(A2.p25,k.p25)/3'],
       label='- the root x = 1/fn^2:', h=62, w=1180)
S.prog(['el(f.p25,k.p25) := F.p25/sqrt(el(X.p25,k.p25))'],
       label='- f.sw [kHz]:', h=56, w=620)


def _p25(th):
    s_ = _m.sin(th)
    q = _QPK * s_ * s_
    A = 1 + _LAM
    a2 = (q * q - 2 * A * _LAM) / _LAM ** 2
    a1 = (A * A - 2 * q * q - (s_ / _MPK) ** 2) / _LAM ** 2
    a0 = q * q / _LAM ** 2
    pp = a1 - a2 * a2 / 3.0
    qq = 2 * a2 ** 3 / 27.0 - a2 * a1 / 3.0 + a0
    z = 3 * qq / (2 * pp) * _m.sqrt(-3.0 / pp)
    x = (2 * _m.sqrt(-pp / 3)
         * _m.cos(2 * _m.atan(_m.sqrt(1 - z * z) / (1 + z)) / 3
                  - 2 * _m.pi / 3) - a2 / 3)
    return _FR / _m.sqrt(x)


_TH5 = [0.05 + i * (_m.pi / 2 - 0.05) / 4 for i in range(5)]
S.row('- f.sw at theta = 0.05, must be 86.05 kHz:', 'p.25a', 'el(f.p25,1)',
      None, 2, expect=_p25(_TH5[0]), allow=())
S.row('- f.sw at the line peak, must be 108.48 kHz:', 'p.25b', 'el(f.p25,5)',
      None, 2, expect=_p25(_TH5[4]), allow=())

S.h2('P26  every step of P25 at the line peak     the FIRST wrong one is the answer')
S.note('P21 to P24 pass and P25 overflows, so no single construct is at fault and the value goes wrong along the chain. Each row reads ONE element of one intermediate at k = 5, where theta is pi/2, and states what it must be. The first disagreement names the step. If any of them prints a MATRIX instead of a number, then el() on the right-hand side is returning the whole vector rather than one element, and that alone would explain the overflow.')
S.row('- sin(theta), must be 1.000000:', 'p.26a', 'el(s.p25,5)', None, 6,
      expect=1.000000000000, allow=())
S.row('- Q(theta), must be 0.500148:', 'p.26b', 'el(q.p25,5)', None, 6,
      expect=0.500147936873, allow=())
S.row('- cubic a2, must be -5.172849:', 'p.26c', 'el(A2.p25,5)', None, 6,
      expect=-5.172849386406, allow=())
S.row('- cubic a0, must be 1.190787:', 'p.26d', 'el(A0.p25,5)', None, 6,
      expect=1.190786977230, allow=())
S.row('- cubic a1, must be 5.684599:', 'p.26e', 'el(A1.p25,5)', None, 6,
      expect=5.684598525862, allow=())
S.row('- depressed p, must be -3.234858:', 'p.26f', 'el(P.p25,5)', None, 6,
      expect=-3.234858398953, allow=())
S.row('- depressed q, must be 0.739532:', 'p.26g', 'el(Q2.p25,5)', None, 6,
      expect=0.739531580363, allow=())
S.row('- the arc-cosine argument, must be -0.330237:', 'p.26h', 'el(Z.p25,5)', None, 6,
      expect=-0.330236975914, allow=())
S.row('- the root x = 1/fn^2, must be 1.956782:', 'p.26i', 'el(X.p25,5)', None, 6,
      expect=1.956781527838, allow=())

# ----------------------------------------------------------------- P27-P29
# How tall a ZedGraph pane is drawn - the one question that has been answered
# twice with the same answer and never actually asked.
#
# A pane carries its own rect: PaneBase writes a RectangleF(0, 0, w, h) as its
# first field, and it agrees with the region's width and height attributes in
# every pane in this project, because SMath writes both when it saves. What is
# NOT known is which of the two SMath READS. If it resizes the pane to the
# region, the attributes alone are enough and the blob never has to be touched.
# If it draws into the pane's own rect, they have to move together.
#
# zedpane.set_size once changed the rect alone and SMath came back with a
# default pane - axes -5..5, no title. That was read as "the geometry is
# interlocked, do not touch it", and the note in zedpane says so. But that
# experiment moved one of the two and left the other, which is the one
# combination that must fail whichever way the answer goes, so it did not
# separate the cases at all.
#
# Three treatments of ONE pane, same data, drawn one under the other:
#
#   P27  both left alone                       the control - this MUST draw
#   P28  region doubled, pane rect untouched
#   P29  region and pane rect both doubled
#
# Whichever of P28 and P29 comes out twice as tall with the frame, the title
# and the legend all intact is the route. If they BOTH draw, prefer P28: it
# leaves the blob alone. If only P27 draws, the height stays where it is and
# the panes have to be dragged by hand.
import base64                                                     # noqa: E402
import struct                                                     # noqa: E402
import zedsheet as ZS                                             # noqa: E402

S.h1('P27 - P29   how tall a pane is drawn')
S.note('Three copies of one pane, same curve in each. P27 is the control and must look '
       'normal. P28 doubles the height in the region attributes only. P29 doubles it in '
       'the region AND in the pane rect inside the blob. Read them the same way: is the '
       'frame twice as tall, and are the title, the axis names and the legend still there? '
       'A pane that failed to load comes back with axes running -5 to 5, no title and no '
       'legend - that is the failure to look for, not an error message.')
S.prog(['N.pp := 21'], label='- points:', h=52, w=380)
S.prog(['k.pp := range(1,N.pp)'], label='- the range variable:', h=52, w=460)
S.prog(['el(xp.p,k.pp) := (k.pp-1)/(N.pp-1)*100'],
       label='- x, 0 to 100:', h=54, w=620)
S.prog(['el(yp.p,k.pp) := el(xp.p,k.pp)*el(xp.p,k.pp)/100'],
       label='- y, a parabola so a squashed frame is obvious:', h=56, w=760)
S.prog(['P.crv := eval(augment(vectorize(xp.p),vectorize(yp.p)))'],
       label='- the two-column matrix:', h=56, w=760, allow=ZS.VEC)

_pb, _pw, _ph = ZS.make(1, 'transfer', 'P27  control - untouched',
                        'x', 'y = x squared over one hundred', ['the parabola'],
                        (0.0, 100.0), (0.0, 120.0), xlog=False,
                        xsteps=(20.0, 5.0), ysteps=(20.0, 5.0),
                        colors=['Blue'])
S.h2('P27  control                         expected a normal pane, %d x %d'
     % (_pw, _ph))
ZS.emit(S, ['P.crv'], _pb, _pw, _ph)

_b2 = base64.b64decode(_pb)
S.h2('P28  region doubled, blob untouched   expected %d x %d, or a default pane'
     % (_pw, 2 * _ph))
ZS.emit(S, ['P.crv'], _pb, _pw, 2 * _ph)

_old = struct.pack('<ffff', 0.0, 0.0, float(_pw), float(_ph))
_new = struct.pack('<ffff', 0.0, 0.0, float(_pw), float(2 * _ph))
if _b2.count(_old) != 1:
    raise SystemExit('the pane rect is not unique - P29 cannot be built')
_pb3 = base64.b64encode(_b2.replace(_old, _new)).decode()
S.h2('P29  region and pane rect doubled     expected %d x %d, or a default pane'
     % (_pw, 2 * _ph))
ZS.emit(S, ['P.crv'], _pb3, _pw, 2 * _ph)

nbytes, ybottom = S.save(OUT)
print(f'written {OUT}\n  {nbytes} bytes, {ybottom} px, {len(S.r)} regions')

EXPECT = {'p.1': 3, 'p.2': 90, 'p.3': 150000, 'p.4': 0.024, 'p.5': 700,
          'p.6': 2 ** .5, 'p.7': 0.6, 'p.8': 0.7853981634, 'p.9': 4,
          'p.10a': 3, 'p.10b': 5, 'p.11c': 180, 'p.11d': 264,
          'p.12a': 1.0471975512, 'p.12b': 2.0943951024, 'p.13': 1.1917535926,
          'p.14': 3.14159265, 'q.x': 1.43277, 'q.fn': 0.83543,
          'p.20a': 2, 'p.20b': 6, 'p.20c': 6 ** .5, 'p.20d': 6 ** .5,
          'p.17a': 264/173.24, 'p.17b': (264/173.24) ** .5,
          'p.21a': _m.cos(1.0), 'p.21b': _m.cos(2.0), 'p.22': 2.0,
          'p.23': _m.acos(0.25) / 3, 'p.24': 0.5,
          'p.25a': _p25(_TH5[0]), 'p.25b': _p25(_TH5[4]),
          'p.26a': 1.000000000000,
          'p.26b': 0.500147936873,
          'p.26c': -5.172849386406,
          'p.26d': 1.190786977230,
          'p.26e': 5.684598525862,
          'p.26f': -3.234858398953,
          'p.26g': 0.739531580363,
          'p.26h': -0.330236975914,
          'p.26i': 1.956781527838}
bad = 0
for k, want in EXPECT.items():
    got = S.ns[k.replace('.', '__')]
    ok = abs(got - want) <= max(abs(want) * 1e-4, 1e-9)
    bad += 0 if ok else 1
    print(f'  {k:7s} = {got:<16.8g} expected {want:<16.8g} {"OK" if ok else "** DIFF"}')
print(f'  mismatches: {bad}')
