# -*- coding: utf-8 -*-
"""Structural audit of the SMath worksheet.

The builder already guarantees that a printed number matches the formula beside
it - smsheet.py parses every expression twice. What it cannot guarantee is that
the SET of expressions is right. So this looks for the shapes of the faults that
survive that guarantee:

  1. dead variables  - computed and then never used, and not shown in the BOM
                       or the summary either. That is how C.12 hid in the ST
                       tool: a pole calculated and referenced by nothing.
  2. forward refs    - a variable used before it is defined. SMath evaluates top
                       to bottom, so this is a red region on the user's screen.
  3. limit pairs     - an X_max / X_min computed next to a selected X, with no
                       k.* ratio anywhere that compares them
  4. orphan checks   - a k.* that nothing explains: not in the summary section
                       and carrying no note
  5. guide coverage  - equation tags [1]..[148] that appear in the guide but in
                       no note in the sheet

    python audit_sm.py
"""
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
BUILDER = os.path.join(HERE, 'build_l6790_smath.py')
GUIDE = os.path.join(ROOT, 'Design Guide', 'AN_L6790A_Design_Guide_rev2_1.md')

# intermediates of the Cardano / fixed-point machinery: consumed positionally
MACHINERY = re.compile(r'^(a[0-2]|w|q|r|p|u|x|ang|ph|θ|λ|Q|M|f\.n|f\.ss|f\.sc|f\.sw|'
                       r'I\.(lm|tr|sp|oi)|A|Aa|Ma|Ta|wa|S|P\.a)[.\d]')
# values whose purpose is to be read by a person, not by another formula
TERMINAL = {'k.', 'GM', 'Φ.act', 'V.out_act', 'B.pk', 'A.L', 'P.', 'R.dson_req',
            'C.oss_max', 'I.pri_rating', 'I.sec_rating', 'V.DS', 'R.N', 'T.res',
            'L.open', 'L.short', 'n.T_act', 'I.OCP', 'ΔV.', 't.hold', 'f.180'}


def sheet_order(path):
    """[(name, [tokens used], y, x)] for every assignment in the .sm

    Regions carry absolute coordinates, so document order is the reading
    order: top to bottom, then left to right. That is the order SMath
    evaluates in.
    """
    raw = io.open(path, encoding='utf-8', errors='replace').read()
    raw = re.sub(r'<raw format="[^"]+" encoding="base64">.*?</raw>',
                 '<raw/>', raw, flags=re.S)
    raw = re.sub(r'<data encoding="base64">[^<]*</data>', '<data/>', raw)
    out = []
    for m in re.finditer(r'<region[^>]*top="(\d+)"[^>]*left="(\d+)"[^>]*>'
                         r'|<region[^>]*left="(\d+)"[^>]*top="(\d+)"[^>]*>',
                         raw):
        pass
    # <math decimalPlaces="4"> as well as a bare <math>: matching only the
    # bare form saw a fraction of the sheet and reported clean
    for m in re.finditer(r'<region ([^>]*)>\s*<math[^>]*>\s*<input>(.*?)</input>',
                         raw, re.S):
        at = m.group(1)
        y = int(re.search(r'top="(\d+)"', at).group(1))
        x = int(re.search(r'left="(\d+)"', at).group(1))
        toks = [(k, v) for k, v in
                re.findall(r'<e type="(\w+)"[^>]*>([^<]*)</e>', m.group(2))]
        if not toks or toks[-1][1] != ':':
            continue                      # not an assignment
        names = [v for k, v in toks if k == 'operand' and v]
        if not names:
            continue
        # the assignment target is the first operand; el(v,k) := ... puts the
        # vector first too, so the same rule reads both
        out.append((names[0], names[1:], y, x))
    out.sort(key=lambda r: (r[2], r[3]))
    return out


def plot_inputs(path):
    """[(name, y)] for every matrix a ZedGraph pane is fed

    The pane names its data in an <input> block. That is not a math region,
    so sheet_order() cannot see it, and a pane fed a name nothing defines
    draws a flat line on zero instead of failing.
    """
    raw = io.open(path, encoding='utf-8', errors='replace').read()
    raw = re.sub(r'<data encoding="base64">[^<]*</data>', '<data/>', raw)
    out = []
    for m in re.finditer(r'<region ([^>]*)>\s*<zedgraph[^>]*>.*?'
                         r'<input>(.*?)</input>', raw, re.S):
        y = int(re.search(r'top="(\d+)"', m.group(1)).group(1))
        for k, v in re.findall(r'<e type="(\w+)"[^>]*>([^<]*)</e>',
                               m.group(2)):
            if k == 'operand' and v and not v.replace('.', '').isdigit():
                out.append((v, y))
    return out


def undefined_plot_inputs(path):
    """plot data the sheet never builds - drawn as a flat zero, not an error"""
    defined = set(name for name, _u, _y, _x in sheet_order(path))
    return sorted(set((n, y) for n, y in plot_inputs(path)
                      if n not in defined))


def forward_refs(path):
    """names used in a region before any region that defines them"""
    rows = sheet_order(path)
    first = {}
    for i, (name, _u, _y, _x) in enumerate(rows):
        first.setdefault(name, i)
    bad = []
    for i, (name, used, _y, _x) in enumerate(rows):
        for t in used:
            if t in first and first[t] > i and t != name:
                bad.append((name, t, i, first[t]))
    return bad


def undefined_refs(path):
    """names a region uses that NO region defines

    The order check cannot see these: a name defined nowhere is never
    defined "later", so it never counts as a forward reference. It is also
    the easier mistake to make - deleting a block while something downstream
    still refers to it - and the harder one to notice, because the builder
    does not evaluate prog blocks and prints nothing.

    A name is only reported if it looks like one of this sheet's variables:
    a dotted name whose base appears elsewhere as a definition. That keeps
    range variables, numbers and function names out of it.
    """
    rows = sheet_order(path)
    defined = set(name for name, _u, _y, _x in rows)
    bases = set(n.split('.')[0] for n in defined)
    bad = {}
    for name, used, _y, _x in rows:
        for t in used:
            if t in defined or t in bad:
                continue
            if '.' not in t or t.split('.')[0] not in bases:
                continue
            bad[t] = name
    return sorted(bad.items())


def main():
    src = io.open(BUILDER, encoding='utf-8').read()

    # (name, expression, note) in the order the sheet defines them
    rows = []
    for m in re.finditer(r"S\.(row|const|set)\(\s*(?:'(?:[^']*)'|\"[^\"]*\")\s*,\s*"
                         r"'([^']+)'\s*,\s*((?:\"[^\"]*\"|'[^']*')(?:\s*(?:\"[^\"]*\"|'[^']*'))*)",
                         src):
        rows.append((m.group(2), m.group(3), m.start()))
    shown = set(re.findall(r"S\.show\(\s*'[^']*'\s*,\s*'([^']+)'", src))
    notes = {}
    for m in re.finditer(r"'([^']+)',[^\n]*\n?[^\n]*note='([^']*)", src):
        notes.setdefault(m.group(1), m.group(2))

    defined = []
    for name, expr, pos in rows:
        defined.append(name)

    seen = set()
    dup = [x for x in defined if x in seen or seen.add(x)]

    # who uses whom
    used = defaultdict(set)
    order = {}
    for i, (name, expr, pos) in enumerate(rows):
        order.setdefault(name, i)
    for i, (name, expr, pos) in enumerate(rows):
        for tok in re.findall(r'[A-Za-zΑ-Ωα-ωΔΦλωθηπ][A-Za-zΑ-Ωα-ωΔΦλωθηπ0-9_]*'
                              r'(?:\.[A-Za-zΑ-Ωα-ω0-9_]+)*', expr):
            if tok in order and tok != name:
                used[tok].add(name)

    hits = defaultdict(list)

    # ------------------------------------------------------- 1. dead variables
    for name in dict.fromkeys(defined):
        if used[name] or name in shown:
            continue
        if MACHINERY.match(name) or any(name.startswith(t) for t in TERMINAL):
            continue
        hits['1 계산만 하고 아무도 안 쓰는 변수'].append(name)

    # --------------------------------------------------------- 2. forward refs
    for i, (name, expr, pos) in enumerate(rows):
        for tok in re.findall(r'[A-Za-zΑ-Ωα-ωΔΦλωθηπ][A-Za-zΑ-Ωα-ω0-9_]*'
                              r'(?:\.[A-Za-zΑ-Ωα-ω0-9_]+)*', expr):
            if tok in order and order[tok] > i:
                hits['2 정의보다 먼저 쓰인다 (SMath 에서 붉은 리전)'].append(
                    '%s (%d번째) 가 %s (%d번째) 를 참조' % (name, i, tok, order[tok]))

    # ------------------------------------------------------- 3. unchecked pairs
    ks = ' '.join(e for _, e, _ in rows if _)
    all_expr = ' '.join(e for _, e, _ in rows)
    for name in dict.fromkeys(defined):
        m = re.match(r'(.+)_(max|min)$', name)
        if not m:
            continue
        base = m.group(1)
        if base not in order:
            continue
        # is there any expression that divides one by the other?
        pair = re.compile(r'%s\s*/\s*%s|%s\s*/\s*%s'
                          % tuple(re.escape(x) for x in (name, base, base, name)))
        if not pair.search(all_expr):
            hits['3 한계와 선정값이 있는데 비교하는 검사가 없다'].append(
                '%s  vs  %s' % (name, base))

    # ------------------------------------------------------ 4. unexplained k.*
    for name in dict.fromkeys(defined):
        if name.startswith('k.') and name not in notes and name not in shown:
            hits['4 설명 없는 판정값'].append(name)

    # ------------------------------------------------------ 5. guide coverage
    guide_tags = set(re.findall(r'\\tag\{\[(\d+[a-z]?)\]\}',
                                io.open(GUIDE, encoding='utf-8').read()))
    sheet_tags = set(re.findall(r'\[(\d+[a-z]?)\]', src))
    missing = sorted(guide_tags - sheet_tags, key=lambda t: (int(re.match(r'\d+', t).group()), t))
    if missing:
        hits['5 가이드에는 있는데 시트 주석에 안 보이는 식'].append(' '.join('[%s]' % t for t in missing))

    if dup:
        hits['0 같은 이름을 두 번 정의'].extend(sorted(set(dup)))

    total = 0
    for cat in sorted(hits):
        print('■ %s — %d건' % (cat, len(hits[cat])))
        for x in hits[cat][:30]:
            print('   ' + str(x))
        if len(hits[cat]) > 30:
            print('   ... 그 외 %d건' % (len(hits[cat]) - 30))
        print()
        total += len(hits[cat])
    print('변수 %d개 · 살펴볼 곳 %d건' % (len(set(defined)), total))



def _order_report():
    import os
    sm = os.environ.get('SM_OVERRIDE') or os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Smath',
        'L6790A_SingleStage_PF_LLC_Design_Guide.sm'))
    if not os.path.isfile(sm):
        print('\n\u25a0 6 \uc21c\uc11c \uac80\uc0ac \u2014 \uc2dc\ud2b8 \ud30c\uc77c\uc774 \uc5c6\uc74c')
        return 0
    miss = undefined_refs(sm)
    print('\n\u25a0 7 \uc4f0\uc774\ub294\ub370 \uc5b4\ub514\uc5d0\ub3c4 \uc815\uc758\uac00 \uc5c6\ub294 \uc774\ub984 \u2014 %d\uac74' % len(miss))
    for t, who in miss[:20]:
        print('   %s \uac00 %s \ub97c \uc4f0\ub294\ub370 \uc815\uc758\uac00 \uc5c6\ub2e4' % (who, t))
    fed = undefined_plot_inputs(sm)
    print('\n[8] plot data that nothing builds (draws as a flat zero) - %d'
          % len(fed))
    for n, y in fed:
        print('   a graph at y=%d is fed %s, which no region assigns' % (y, n))
    bad = forward_refs(sm) + [None] * 0
    print('\n\u25a0 6 \uc815\uc758 \uc804 \uc0ac\uc6a9 (\uc644\uc131\ub41c .sm \uc744 \ub9ac\uc804 \uc21c\uc11c\ub300\ub85c) \u2014 %d\uac74' % len(bad))
    for name, tok, i, j in bad[:20]:
        print('   %s (%d\ubc88\uc9f8) \uac00 %s (%d\ubc88\uc9f8) \ub97c \ucc38\uc870' % (name, i, tok, j))
    if len(bad) > 20:
        print('   ... \uadf8 \uc678 %d\uac74' % (len(bad) - 20))
    return len(bad) + len(miss) + len(fed)


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
    _order_report()
