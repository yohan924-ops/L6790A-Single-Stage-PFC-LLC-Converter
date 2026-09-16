# -*- coding: utf-8 -*-
"""Does the RPN in the .sm file compute what the sheet prints?

smsheet.py parses every expression twice - once into SMath RPN, once into a
Python value - and the printed number comes from the second parse. That
guarantees the number matches the SOURCE STRING. It does not guarantee the RPN
matches it: a bug in the RPN emitter would leave a sheet whose printed values
are right and whose SMath-computed values are wrong, and nobody would see it
until SMath was opened.

This closes that hole from the other side. It reads the RPN back out of the
finished file, rebuilds an expression from it, evaluates that in Python, and
compares against the <result> the file carries.

    python audit_rpn.py            differences only
    python audit_rpn.py -v         every region
"""
import io
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

import smresult

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SM = os.path.join(ROOT, 'Smath', 'L6790A_SingleStage_PF_LLC_Design_Guide.sm')
if os.environ.get('SM_OVERRIDE'):          # a variant instead of the canonical sheet
    SM = os.environ['SM_OVERRIDE']

UNIT = {'V': 1., 'A': 1., 'W': 1., 'ohm': 1., 'kohm': 1e3, 'mohm': 1e-3,
        'F': 1., 'mF': 1e-3, 'μF': 1e-6, 'uF': 1e-6, 'nF': 1e-9, 'pF': 1e-12,
        'H': 1., 'mH': 1e-3, 'μH': 1e-6, 'uH': 1e-6, 'nH': 1e-9,
        'Hz': 1., 'kHz': 1e3, 'MHz': 1e6,
        's': 1., 'ms': 1e-3, 'μs': 1e-6, 'us': 1e-6, 'ns': 1e-9,
        'mV': 1e-3, 'mA': 1e-3, 'μA': 1e-6, 'uA': 1e-6,
        'T': 1., 'mT': 1e-3, 'K': 1., 'm': 1., 'mm': 1e-3, 'cm': 1e-2}

FUNCS = {'sqrt': math.sqrt, 'abs': abs, 'ln': math.log, 'exp': math.exp,
         'atan': math.atan, 'cos': math.cos, 'sin': math.sin}

OPS = {'+': lambda a, b: a + b, '-': lambda a, b: a - b,
       '*': lambda a, b: a * b, '/': lambda a, b: a / b,
       '^': lambda a, b: a ** b}


def evaluate(elems, env):
    """run the RPN the way SMath would, on plain floats"""
    st = []
    for e in elems:
        t, txt = e.get('type'), (e.text or '')
        if t == 'bracket':
            continue
        if t == 'operand':
            if e.get('style') == 'unit':
                st.append(UNIT[txt])
            elif re.fullmatch(r'-?\d+(\.\d+)?([eE][-+]?\d+)?', txt):
                st.append(float(txt))
            elif txt in env:
                st.append(env[txt])
            elif txt == 'π':
                st.append(math.pi)
            else:
                raise KeyError(txt)
        elif t == 'operator':
            n = int(e.get('args', 2))
            if txt == '-' and n == 1:
                st.append(-st.pop())
            elif txt == '/' and n == 1:
                st.append(1.0 / st.pop())
            else:
                b, a = st.pop(), st.pop()
                st.append(OPS[txt](a, b))
        elif t == 'function':
            n = int(e.get('args', 1))
            args = [st.pop() for _ in range(n)][::-1]
            if txt not in FUNCS:
                raise NotImplementedError(txt)
            st.append(FUNCS[txt](*args))
        else:
            raise NotImplementedError(t)
    if len(st) != 1:
        raise ValueError('스택에 %d개 남음' % len(st))
    return st[0]


def main():
    verbose = '-v' in sys.argv
    raw = io.open(SM, encoding='utf-8').read()
    raw = re.sub(r'<raw format="[^"]+" encoding="base64">.*?</raw>', '<raw/>', raw, flags=re.S)
    root = ET.fromstring(raw.replace(' xmlns="http://smath.info/schemas/worksheet/1.0"', ''))

    env = {}
    checked = skipped = bad = 0
    problems = []
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
        name = elems[0].text
        # assignment: name := expression   (the ':' operator is last)
        if not (elems[-1].get('type') == 'operator' and (elems[-1].text or '') == ':'):
            continue
        try:
            val = evaluate(elems[1:-1], env)
        except Exception as e:                                     # noqa: BLE001
            skipped += 1
            if verbose:
                print('  skip %-14s %s' % (name, e))
            continue
        env.setdefault(name, val)
        checked += 1

        res = m.find('result')
        if res is None or not len(list(res)):
            continue
        c = m.find('contract')
        unit = list(c)[0].text if c is not None and len(list(c)) else ''
        txt = list(res)[0].text
        shown = smresult.value(res)          # NOT val - val is the RPN answer
        try:
            printed = shown * UNIT.get(unit, 1.0)
        except (TypeError, ValueError):
            continue
        if abs(val) < 1e-30 and abs(printed) < 1e-30:
            continue
        # <result> is the DISPLAYED number, already rounded to the region's
        # decimal places, so the only fair tolerance is half of the last digit
        mant = txt.lstrip('-')
        dec = len(mant.split('.')[1]) if '.' in mant else 0
        if 'e' in txt.lower():
            dec = 12
        half = 0.5 * 10 ** (-dec) * UNIT.get(unit, 1.0)
        rel = abs(val - printed) / max(abs(printed), 1e-30)
        if abs(val - printed) > half * 1.001:
            bad += 1
            problems.append('%-16s RPN %-14.7g  인쇄 %-14.7g  %.3g %% (표시 %d자리)'
                            % (name, val, printed, rel * 100, dec))
        elif verbose:
            print('  ok   %-14s %.7g' % (name, val))

    for p in problems:
        print('  ** ' + p)
    print()
    print('RPN 을 되읽어 계산한 값 vs 시트에 인쇄된 값')
    print('  검사 %d개 · 불일치 %d개 · 평가 불가 %d개 (루프·행렬 등)' % (checked, bad, skipped))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
