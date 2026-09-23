# -*- coding: utf-8 -*-
"""Audit the design guide: equation tags, cross-references, and the worked example.

l6790.py already implements equations [1]..[106] and l6790_validate.py checks
that it reproduces the 240 W example, so the maths of that range has a witness.
What has never been checked is the DOCUMENT: whether every tag exists once,
whether every reference points at something, whether the numbers printed in the
prose agree with the equations above them, and whether the later equations
([107]..) have any witness at all.

    python audit_guide.py
"""
import io
import os
import re
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
GUIDE = os.path.normpath(os.path.join(HERE, '..',
                                      'AN_L6790A_Design_Guide_rev2_1.md'))
SM = os.path.normpath(os.path.join(HERE, 'build_l6790_smath.py'))
REF = os.path.join(HERE, 'l6790.py')

TAG = re.compile(r'\\tag\{\[([0-9]+[a-z]?)\]\}')
CITE = re.compile(r'\\\[([0-9]+[a-z]?)\\\]|\[(?<!\\)([0-9]+[a-z]?)\](?!\()')


def num(t):
    m = re.match(r'(\d+)([a-z]?)', t)
    return (int(m.group(1)), m.group(2))


def main():
    text = io.open(GUIDE, encoding='utf-8').read()
    smath = io.open(SM, encoding='utf-8').read()
    ref = io.open(REF, encoding='utf-8').read()

    tags = TAG.findall(text)
    cnt = Counter(tags)
    print('가이드 %s' % os.path.basename(GUIDE))
    print('  줄 %d · 수식 태그 %d개 (고유 %d)'
          % (text.count('\n') + 1, len(tags), len(cnt)))
    print()

    bad = 0

    dup = sorted([t for t, c in cnt.items() if c > 1], key=num)
    if dup:
        bad += len(dup)
        print('■ 같은 태그가 두 번 이상 -- %d건' % len(dup))
        for t in dup:
            print('   [%s] x%d' % (t, cnt[t]))
        print()

    have = {num(t) for t in cnt}
    plain = sorted({n for n, s in have if s == ''})
    gaps = [i for i in range(min(plain), max(plain) + 1) if i not in plain]
    if gaps:
        print('■ 번호가 비어 있다 -- %d개' % len(gaps))
        print('   %s' % ' '.join('[%d]' % g for g in gaps))
        print('   (부록에서 쓰거나 의도적으로 건너뛴 것일 수 있다)')
        print()

    # every [n] mentioned in prose should be a real tag
    cited = set()
    for a, b in CITE.findall(text):
        t = a or b
        if t:
            cited.add(t)
    dangling = sorted([t for t in cited if t not in cnt], key=num)
    if dangling:
        bad += len(dangling)
        print('■ 본문이 없는 식을 가리킨다 -- %d건' % len(dangling))
        for t in dangling:
            m = re.search(r'[^\n]*\\\[%s\\\][^\n]*' % re.escape(t), text)
            ctx = ' '.join(m.group(0).split())[:74] if m else ''
            print('   [%-4s] %s' % (t, ctx))
        print()

    # which equations have a witness in code
    in_ref = {t for t in cnt if re.search(r'#\s*\[%s\]' % re.escape(t), ref)}
    in_sm = {t for t in cnt if re.search(r'\[%s\]' % re.escape(t), smath)}
    witnessed = in_ref | in_sm
    orphan = sorted([t for t in cnt if t not in witnessed], key=num)
    print('■ 코드에 대응이 있는 식')
    print('   l6790.py %d개 · SMath 빌더 %d개 · 합집합 %d / %d'
          % (len(in_ref), len(in_sm), len(witnessed), len(cnt)))
    if orphan:
        print('   대응 없음 %d개: %s' % (len(orphan),
                                    ' '.join('[%s]' % t for t in orphan)))
        print('   -> 이 식들은 지금까지 아무도 검산한 적이 없다')
    print()
    print('구조 문제 %d건' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
