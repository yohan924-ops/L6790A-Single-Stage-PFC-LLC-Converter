# -*- coding: utf-8 -*-
"""Audit the comments SMath actually prints, by reading the .sm.

WHY THIS READS THE ARTIFACT AND NOT THE BUILDER

The first version walked the builder's AST and read every comment with
ast.literal_eval. That found the comments the builder writes as plain
strings, and nothing else:

  - seven comments are built with %, so they are expressions, not literals.
    literal_eval failed on them and they were skipped - and they were the
    worst ones, because interpolating a computed value into prose is exactly
    what this check exists to catch. It reported ZERO while six of them were
    doing it.

  - about a hundred more are TABLE CELLS, emitted through S.table(), which
    the check was not looking at at all.

A checker that reads the SOURCE can only see what the source shapes it knows
about produce. Reading the .sm has no such blind spot: whatever SMath will
print is in there as text, whichever builder call put it there. That is the
rule this file exists to hold - CHECK THE ARTIFACT.

WHAT IT REPORTS

  1. every text region that is prose - not a heading, not a row label - so
     the count, the total and the longest are visible;
  2. prose that quotes a number the sheet computes. A comment must not: the
     number goes stale the moment a yellow cell moves and nothing downstream
     can see that it has. It matches values, so it finds candidates rather
     than verdicts - a datasheet limit that happens to equal a computed value
     looks the same from here - and it does not fail a build.

Run:  python audit_notes.py
"""
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SM = os.environ.get('SM_OVERRIDE') or os.path.join(
    HERE, '..', '..', 'Smath', 'L6790A_SingleStage_PF_LLC_Design_Guide.sm')

MUL = {'%': 0.01, 'W': 1.0, 'A': 1.0, 'V': 1.0, 'F': 1.0, 'H': 1.0,
       'ohm': 1.0, 'mohm': 1e-3, 'kohm': 1e3, 'Hz': 1.0, 'kHz': 1e3,
       'nF': 1e-9, 'pF': 1e-12, 'uF': 1e-6, 'mF': 1e-3, 'ns': 1e-9,
       'us': 1e-6, 'ms': 1e-3, 'mT': 1e-3, 'k': 1e3}
NUM = re.compile(r'(\d+(?:\.\d+)?)\s*(%|mohm|kohm|ohm|kHz|Hz|nF|pF|uF|mF|'
                 r'ns|us|ms|mT|[WAVFH]|k)\b')

# numbers that come from outside the sheet: datasheet windows, gate drive,
# junction temperatures, standard practice
KEEP = {25.0, 125.0, 100.0, 10.0, 4.0, 4.5, 250.0, 350.0, 700.0, 370.0,
        15.0, 30.0, 47.0, 140.0, 270.0, 1000.0, 5.0, 3.0, 120.0, 1.5, 2.0,
        6.0, 20.0, 45.0, 50.0, 60.0, 180.0, 9.0}


def prose(path):
    """[(chars, text)] for every text region that is neither heading nor label"""
    raw = io.open(path, encoding='utf-8', errors='replace').read()
    raw = re.sub(r'<raw format="[^"]+" encoding="base64">.*?</raw>',
                 '<raw/>', raw, flags=re.S)
    root = ET.fromstring(
        raw.replace(' xmlns="http://smath.info/schemas/worksheet/1.0"', ''))
    out = []
    for r in root.iter('region'):
        if r.get('left') is None or r.find('text') is None:
            continue
        t = ' '.join(''.join(e.itertext()) for e in r.iter('p')).strip()
        if not t:
            continue
        if float(r.get('fontSize') or 10) >= 11:          # a heading
            continue
        x = int(r.get('left'))
        if x < 500 and (t.startswith('-') or t.startswith('[')):
            continue                                      # a row label
        out.append((len(t), t))
    return out


def values():
    """{name: value} for everything the sheet computes"""
    import build_l6790_smath as B                                # noqa: E402
    return dict((k.replace('__', '.'), v) for k, v in B.S.ns.items()
                if isinstance(v, (int, float)))


def main():
    items = prose(SM)
    tot = sum(n for n, _t in items)
    print('[audit_notes] prose printed by the sheet: %d regions, %d chars'
          % (len(items), tot))
    if items:
        med = sorted(n for n, _t in items)[len(items) // 2]
        print('              median %d, longest %d'
              % (med, max(n for n, _t in items)))

    ns = values()
    hits = []
    for _n, txt in items:
        for m in NUM.finditer(txt):
            val, unit = float(m.group(1)), m.group(2)
            if val in KEEP:
                continue
            si = val * MUL[unit]
            same = [k for k, v in ns.items()
                    if v and abs(abs(v) - si) <= 0.005 * abs(si)]
            if same:
                hits.append((m.group(0), sorted(same)[:3], txt))
    print('              quoting a value the sheet computes: %d' % len(hits))
    for what, who, txt in hits[:20]:
        print('   %-12s matches %s' % (what, ', '.join(who)))
        print('        %s' % txt[:110])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
