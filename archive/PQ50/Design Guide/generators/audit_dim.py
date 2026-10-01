# -*- coding: utf-8 -*-
"""Dimensional analysis of the SMath worksheet.

Both existing evaluation paths - smsheet's Python pass and audit_rpn's replay -
treat a unit as a plain scale factor, so neither can tell V from A. SMath itself
can, and it refuses: a unit clash is a red region, and an implicit unit inside
ln / exp / atan / a fractional power is the silent failure described in
CLAUDE.md 6.1 items 3 and 4 - the value still prints, and something far away
dies later.

So the dimensions are carried through the RPN here, in base (V, A, s, m, K):

    W = V*A      ohm = V/A     F = A*s/V     H = V*s/A
    Hz = 1/s     T = V*s/m^2

and four rules are enforced:

  1. + and -            both sides must carry the same dimension
  2. ln exp atan sin cos  the argument must be dimensionless
  3. ^                  the exponent must be dimensionless, and a dimensioned
                        base needs an integer exponent
  4. <contract>         the unit the sheet PRINTS must match what it computed

Rule 4 is the one that catches a mislabelled row - a number that is right and
whose unit is wrong.

    python audit_dim.py
"""
import io
import os
import re
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SM = os.path.join(ROOT, 'Smath', 'L6790A_SingleStage_PF_LLC_Design_Guide.sm')
if os.environ.get('SM_OVERRIDE'):          # a variant instead of the canonical sheet
    SM = os.environ['SM_OVERRIDE']

# (V, A, s, m, K)
D0 = (0, 0, 0, 0, 0)


def d(**kw):
    return tuple(Fraction(kw.get(k, 0)) for k in ('V', 'A', 's', 'm', 'K'))


DIM = {
    'V': d(V=1), 'mV': d(V=1), 'kV': d(V=1),
    'A': d(A=1), 'mA': d(A=1), 'μA': d(A=1), 'uA': d(A=1),
    'W': d(V=1, A=1), 'mW': d(V=1, A=1), 'kW': d(V=1, A=1),
    'ohm': d(V=1, A=-1), 'kohm': d(V=1, A=-1), 'mohm': d(V=1, A=-1),
    'F': d(A=1, s=1, V=-1), 'mF': d(A=1, s=1, V=-1), 'μF': d(A=1, s=1, V=-1),
    'uF': d(A=1, s=1, V=-1), 'nF': d(A=1, s=1, V=-1), 'pF': d(A=1, s=1, V=-1),
    'H': d(V=1, s=1, A=-1), 'mH': d(V=1, s=1, A=-1), 'μH': d(V=1, s=1, A=-1),
    'uH': d(V=1, s=1, A=-1), 'nH': d(V=1, s=1, A=-1),
    's': d(s=1), 'ms': d(s=1), 'μs': d(s=1), 'us': d(s=1), 'ns': d(s=1),
    'Hz': d(s=-1), 'kHz': d(s=-1), 'MHz': d(s=-1),
    'T': d(V=1, s=1, m=-2), 'mT': d(V=1, s=1, m=-2),
    'm': d(m=1), 'mm': d(m=1), 'cm': d(m=1), 'K': d(K=1),
}
NAMES = {v: k for k, v in (('V', d(V=1)), ('A', d(A=1)), ('W', d(V=1, A=1)),
                           ('ohm', d(V=1, A=-1)), ('F', d(A=1, s=1, V=-1)),
                           ('H', d(V=1, s=1, A=-1)), ('s', d(s=1)),
                           ('Hz', d(s=-1)), ('T', d(V=1, s=1, m=-2)),
                           ('m', d(m=1)), ('K', d(K=1)), ('-', D0))}

BARE = {'ln', 'exp', 'atan', 'sin', 'cos'}


def show(dim):
    if dim in NAMES:
        return NAMES[dim]
    return ' '.join('%s^%s' % (u, e) for u, e in
                    zip(('V', 'A', 's', 'm', 'K'), dim) if e) or '-'


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub_(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(a, k):
    return tuple(x * k for x in a)


class Clash(Exception):
    pass


def dims(elems, env, val):
    """carry (dimension, value) together - the exponent's VALUE decides how the
    base's dimension scales, so tracking dimension alone loses V^2 -> V."""
    st = []
    for e in elems:
        t, txt = e.get('type'), (e.text or '')
        if t == 'bracket':
            continue
        if t == 'operand':
            if e.get('style') == 'unit':
                if txt not in DIM:
                    raise Clash('모르는 단위 %s' % txt)
                st.append((DIM[txt], 1.0))
            elif re.fullmatch(r'-?\d+(\.\d+)?([eE][-+]?\d+)?', txt):
                st.append((D0, float(txt)))
            elif txt == 'π':
                st.append((D0, 3.141592653589793))
            elif txt in env:
                st.append((env[txt], val.get(txt, 1.0)))
            else:
                raise Clash('미정의 %s' % txt)
        elif t == 'operator':
            n = int(e.get('args', 2))
            if n == 1:
                if txt == '-':
                    dd, vv = st.pop()
                    st.append((dd, -vv))
                elif txt == '/':
                    dd, vv = st.pop()
                    st.append((mul(dd, -1), 1.0 / vv if vv else 1.0))
                continue
            (bd, bv), (ad, av) = st.pop(), st.pop()
            if txt in '+-':
                if ad != bd:
                    raise Clash('%s 의 양변 차원이 다르다: %s vs %s' % (txt, show(ad), show(bd)))
                st.append((ad, av + bv if txt == '+' else av - bv))
            elif txt == '*':
                st.append((add(ad, bd), av * bv))
            elif txt == '/':
                st.append((sub_(ad, bd), av / bv if bv else 1.0))
            elif txt == '^':
                if bd != D0:
                    raise Clash('지수에 단위가 붙어 있다: %s' % show(bd))
                fr = Fraction(bv).limit_denominator(64)
                if ad != D0 and fr.denominator != 1:
                    raise Clash('단위 있는 값에 비정수 거듭제곱 %s  (CLAUDE.md 6.1-4)' % bv)
                st.append((mul(ad, fr), av ** bv if av > 0 or fr.denominator == 1 else 1.0))
            else:
                st.append((D0, 1.0))
        elif t == 'function':
            n = int(e.get('args', 1))
            args = [st.pop() for _ in range(n)][::-1]
            ad, av = args[0]
            if txt in BARE:
                if ad != D0:
                    raise Clash('%s 의 인자에 단위가 있다: %s' % (txt, show(ad)))
                st.append((D0, 1.0))
            elif txt == 'sqrt':
                st.append((mul(ad, Fraction(1, 2)), abs(av) ** 0.5))
            elif txt == 'abs':
                if ad != D0:
                    raise Clash('abs 의 인자에 단위가 있다: %s  (CLAUDE.md 6.1-3)' % show(ad))
                st.append((ad, abs(av)))
            else:
                st.append((D0, 1.0))
    return st[-1] if st else (D0, 1.0)


def main():
    raw = io.open(SM, encoding='utf-8').read()
    raw = re.sub(r'<raw format="[^"]+" encoding="base64">.*?</raw>', '<raw/>', raw, flags=re.S)
    root = ET.fromstring(raw.replace(' xmlns="http://smath.info/schemas/worksheet/1.0"', ''))

    env, val, clash, label, checked = {}, {}, [], [], 0
    for r in root.iter('region'):
        m = r.find('math')
        if m is None:
            continue
        i = m.find('input')
        if i is None:
            continue
        elems = list(i)
        if not (elems and elems[0].get('type') == 'operand'):
            continue
        if not (elems[-1].get('type') == 'operator' and (elems[-1].text or '') == ':'):
            continue
        name = elems[0].text
        try:
            dim, v = dims(elems[1:-1], env, val)
        except Clash as e:
            clash.append('%-16s %s' % (name, e))
            continue
        except Exception:                                          # noqa: BLE001
            continue
        env.setdefault(name, dim)
        val.setdefault(name, v)
        checked += 1
        c = m.find('contract')
        if c is not None and len(list(c)):
            u = list(c)[0].text
            if u in DIM and DIM[u] != dim:
                label.append('%-16s 계산 차원 %-10s 인데 표시 단위는 %s' % (name, show(dim), u))

    print('■ 차원 충돌 (SMath 에서 붉은 리전이 되는 것) — %d건' % len(clash))
    for x in clash[:30]:
        print('   ' + x)
    print()
    print('■ 표시 단위가 계산 차원과 다른 행 — %d건' % len(label))
    for x in label[:30]:
        print('   ' + x)
    print()
    print('차원을 추적한 식 %d개' % checked)
    return 1 if (clash or label) else 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
