# -*- coding: utf-8 -*-
"""Check the section 14c and 7.5 vector chains against closed forms.

prog() blocks are the one region type smsheet does not also evaluate in
Python. Every other formula in the sheet is parsed twice - once into SMath
RPN and once into a Python value - so a printed number cannot disagree with
the expression beside it. A vector assignment has no printed number, so a
typo in one would show up nowhere: the sheet would draw a wrong curve and it
would look entirely plausible.

Section 14c reads the phase off the gain equation at a given frequency:

    Q.pk^2 b^2 s^4 - s^2/M.pk^2 + a^2 = 0,   s = sin(theta)
    a = 1+lambda-lambda/fn^2,  b = fn - 1/fn,  physical root is the minus one

Its two ends are quantities section 8 computes by a different route - the
cubic in 1/fn^2, solved trigonometrically - so the check has real force:
the far end must land on f.sw.a and f.sw.b, and the near end on f.o.

Section 7.5 contributes M.OL and M.Z, neither of which has an independent
source anywhere else in the project, so both are checked against the closed
forms they were derived from.

Run:  python check_theta.py
"""
import io
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SRC = os.path.join(HERE, 'build_l6790_smath.py')
src = io.open(SRC, encoding='utf-8').read()
# long expressions are split across adjacent string literals, and a unit is
# written \' , which would end a capture in the wrong place
src = re.sub(r"'\s*\n\s*'", '', src)
src = src.replace("\\'", '~U~')


def grab(lhs):
    m = re.search(re.escape(lhs) + r' := ([^\']+)', src)
    if not m:
        raise SystemExit('%s is not in the builder - the section has been '
                         'renamed or rewritten, and this check is stale' % lhs)
    return m.group(1).strip()


def topy(e, subs):
    e = e.replace('^', '**').replace('λ.act', 'LAM').replace('π', 'PI')
    e = e.replace('Q.pk', 'QPK').replace('f.n0', 'FN0').replace('q.fr', 'FR')
    for a, b in subs:
        e = e.replace(a, b)
    return e


def _run(e, g):
    return eval(e, dict(g, sqrt=math.sqrt, atan=math.atan, sin=math.sin,
                        cos=math.cos, abs=abs))


def freq(ns):
    """the 14c frequency sweep, at both ends of both corners"""
    print('--- section 14c frequency sweep against section 8 ---')
    lam, qpk, fn0 = ns['λ__act'], ns['Q__pk'], ns['f__n0']
    fr = ns['f__r'] / 1000.0
    bad = 0
    # the builder writes these with %d and %s placeholders - the names are
    # supplied by the loop that emits them - so the source text is grabbed in
    # that form and the placeholders resolved here
    VEC = ('xn', 'ga', 'gb', 'gd', 'gn', 'gm', 'gs', 'gt', 'gf')
    sub = [('el(%s.%%d,k.fs)' % v, v) for v in VEC]
    # the mirror's three shared vectors: the sweep runs up and back down and
    # the phase is reflected on the way back
    sub += [('el(%s.g,k.fs)' % v, v) for v in ('uu', 'tt', 'sg')]
    sub += [('k.fs', 'K'), ('N.fs', 'N')]
    for mname, mval, endval, ref in (
            ('M.HBmin', ns['M__HBmin'], ns['f__n__a'], ns['f__sw__a'] / 1000.0),
            ('M.FBthr', ns['M__FBthr'], ns['f__n__b'],
             ns['f__sw__b'] / 1000.0)):
        # Both ends of the sweep and its top. The top is not a sample: N is
        # even so that the sign never divides by zero, which means u never
        # lands on 0.5 exactly and the tent never quite reaches 1. The
        # nearest sample is 0.8 % short of the corner, so comparing it with
        # section 8 would test the sampling and not the algebra. The tent is
        # therefore forced to its top here - the rest of the chain, which is
        # what this check is for, runs untouched.
        for who, K, N in (('first point', 1, 120), ('tent top', None, 120),
                          ('last point', 120, 120)):
            g = dict(LAM=lam, QPK=qpk, FN0=fn0, FR=fr, END=endval, MPK=mval,
                     K=K, N=N, PI=math.pi)
            if K is None:
                g.update(uu=0.5, tt=1.0, sg=-1.0)
            else:
                for v in ('uu', 'tt', 'sg'):
                    g[v] = _run(topy(grab('el(%s.g,k.fs)' % v), sub), g)
            for v in ('xn', 'ga', 'gb', 'gd', 'gn', 'gm', 'gs'):
                e = topy(grab('el(%s.%%d,k.fs)' % v), sub)
                # xn's %s is the sweep end; gm's is the required gain
                # (gs now reads gm rather than spelling M*M out again)
                e = e.replace('%s', 'END' if v == 'xn' else 'MPK')
                g[v] = _run(e, g)
            th = _run(topy(grab('el(gt.%d,k.fs)'), sub), g)
            f = _run(topy(grab('el(gf.%d,k.fs)'), sub), g)
            want = ref if who == 'tent top' else fr * fn0
            ok = abs(f - want) < 0.1
            bad += 0 if ok else 1
            print('  %-8s %-11s theta %7.4f rad  f.sw %8.2f kHz   '
                  'want %8.2f (%s)   %s'
                  % (mname, who, th, f, want,
                     'section 8' if who == 'tent top' else 'f.o',
                     'OK' if ok else '** DIFF'))
    return bad


def gain(ns):
    """the two section 7.5 curves nobody can check by eye"""
    lam = ns['λ__act']
    print('--- section 7.5 vectors against the closed forms ---')
    bad = 0
    sub = [('el(fz.g,k.mz)', 'fz'), ('el(z.f2,k.mz)', 'zf2'),
           ('el(z.a,k.mz)', 'za'), ('el(z.b,k.mz)', 'zb'),
           ('el(z.a2,k.mz)', 'za2'), ('el(z.b2,k.mz)', 'zb2'),
           ('el(z.q,k.mz)', 'zq'),
           ('el(fn.g,k.gc)', 'fn'), ('el(aa.g,k.gc)', 'aa'),
           ('el(bb.g,k.gc)', 'bb')]
    # the longer names have to be replaced before the shorter ones they
    # contain - z.a2 before z.a - or half of each becomes a stray token
    sub.sort(key=lambda p: -len(p[0]))
    # M.Z lives strictly between f.n0 and resonance, and f.n0 = sqrt(lam /
    # (1 + lam)) moves with the variant - so the test points are fractions
    # of that interval, not fixed numbers
    fn0 = math.sqrt(lam / (1 + lam))
    for _r in (0.05, 0.2, 0.5, 0.85):
        fn = fn0 + _r * (1.0 - fn0)
        g = dict(LAM=lam, fz=fn)
        for v, key in (('z.f2', 'zf2'), ('z.a', 'za'), ('z.b', 'zb'),
                       ('z.a2', 'za2'), ('z.b2', 'zb2'), ('z.q', 'zq')):
            g[key] = _run(topy(grab('el(%s,k.mz)' % v), sub), g)
        got = _run(topy(grab('el(m.z,k.mz)'), sub), g)
        a = 1 + lam - lam / fn ** 2
        b = fn - 1 / fn
        q2 = -2 * a * lam / (fn ** 3 * b * (1 + 1 / fn ** 2))
        ref = 1 / math.sqrt(a * a + q2 * b * b)
        ok = abs(got - ref) < 1e-9
        bad += 0 if ok else 1
        print('  M.Z  fn %.2f   sheet %.5f   closed form %.5f   %s'
              % (fn, got, ref, 'OK' if ok else '** DIFF'))
    for fn in (0.52, 0.60, 1.0, 1.5):
        g = dict(LAM=lam, fn=fn)
        g['aa'] = _run(topy(grab('el(aa.g,k.gc)'), sub), g)
        got = _run(topy(grab('el(mo.l,k.gc)'), sub), g)
        ref = 1 / abs(1 + lam - lam / fn ** 2)
        ok = abs(got - ref) < 1e-12
        bad += 0 if ok else 1
        print('  M.OL fn %.2f   sheet %.5f   closed form %.5f   %s'
              % (fn, got, ref, 'OK' if ok else '** DIFF'))
    return bad


def main():
    import build_l6790_smath as B                                # noqa: E402
    ns = B.S.ns
    bad = freq(ns) + gain(ns)
    print('  mismatches: %d' % bad)
    return bad


if __name__ == '__main__':
    raise SystemExit(1 if main() else 0)
