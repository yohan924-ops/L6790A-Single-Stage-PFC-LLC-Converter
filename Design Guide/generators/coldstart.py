# -*- coding: utf-8 -*-
"""Can a session that knows nothing pick this project up from CLAUDE.md alone?

Not "does it read well" - that is what I already believed when the document said
80 mF and the sheet said 71.4. This asks whether the specific questions a cold
session must answer are answerable from the text, and whether every instruction
in it actually runs.
"""
import io
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
#  Relative to this script, like every other tool here.  It was an
#  absolute Windows path, so the one check that guards CLAUDE.md's
#  self-sufficiency did not run anywhere else (2026-09-22).
ROOT = os.path.normpath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', '..'))
GEN = os.path.join(ROOT, 'Design Guide', 'generators')
c = io.open(os.path.join(ROOT, 'CLAUDE.md'), encoding='utf-8').read()
h = io.open(os.path.join(ROOT, 'HISTORY.md'), encoding='utf-8').read()

# The questions a cold session has to answer before it can do anything useful,
# and a phrase that only appears if CLAUDE.md answers it.
QUESTIONS = [
    ('이 프로젝트는 무엇을 만드나', ['단일단(Single-Stage) PF LLC']),
    ('출력 사양은', ['25 V / 26.3 A = 657.5 W']),
    ('왜 하는가 (목적)', ['400 V 벌크 커패시터와 승압단']),
    ('그 대가는', ['75 mF']),
    ('산출물이 무엇무엇인가', ['산출물은 넷']),
    ('지금 어디까지 왔나', ['지금 어디까지']),
    ('다음에 뭘 하나', ['다음에 할 일']),
    ('사람이 해야 할 일이 있나', ['사람이 해야 할 일']),
    ('검증은 어떻게 하나', ['python build_l6790_smath.py', 'python xl_sm_compare.py']),
    ('통과 기준이 뭔가', ['mismatches: 0', 'VERDICT OK', 'different: 0']),
    ('설계값은 어디 있나', ['BEGIN GENERATED']),
    ('설계값을 손으로 고쳐도 되나', ['손으로 고치지 마십시오']),
    ('숫자를 헷갈리지 않으려면', ['가장 많이 헷갈리는 것']),
    ('시트를 재빌드해도 안전한가', ['사용자가 SMath에서 손으로 옮긴 것은']),
    ('워크북을 직접 고쳐도 되나', ['xlsx_patch.py']),
    ('SMath에서 쓰면 안 되는 함수는', ['정의되지 않은 함수입니다']),
    ('IC 핀에 하면 안 되는 것', ['커패시터 금지']),
    ('이 토폴로지에서 자주 틀리는 곳', ['반복해서 틀리는 지점']),
    ('근거는 어디서 찾나', ['HISTORY.md']),
    ('무엇이 아직 미확정인가', ['아직 미확정']),
    ('실측으로 뭘 확인해야 하나', ['최우선 실측 항목']),
]

miss = []
for q, needles in QUESTIONS:
    if not all(nd in c for nd in needles):
        miss.append(q)

print('■ 새 세션이 답해야 하는 질문 %d개' % len(QUESTIONS))
if miss:
    print('  CLAUDE.md 에서 답을 못 찾는 것 %d개:' % len(miss))
    for m in miss:
        print('    - ' + m)
else:
    print('  전부 CLAUDE.md 안에서 답이 나온다')

# every command the document tells you to run must actually run
print()
print('■ 문서가 시키는 명령이 실제로 도는가')
cmds = sorted(set(re.findall(r'python ([a-z0-9_]+\.py)(?: (--?[a-z]+))?', c)))
bad = []
for script, flag in cmds:
    args = [sys.executable, script] + ([flag] if flag else [])
    if script == 'check_sm.py':
        args.append(os.path.join(ROOT, 'Smath',
                                 'L6790A_SingleStage_PF_LLC_Design_Guide.sm'))
    r = subprocess.run(args, cwd=GEN, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    locked = '열려 있어' in (r.stdout + r.stderr)
    tag = 'OK  ' if r.returncode == 0 else ('보류' if locked or r.returncode == 2 else 'FAIL')
    if r.returncode and not locked and r.returncode != 2:
        bad.append(script)
    last = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
    print('  %s python %s %s -> %s' % (tag, script, flag or '', last[-1][:70] if last else ''))

# the structure a reader walks
print()
print('■ 구조')
heads = re.findall(r'^## (.+)$', c, re.M)
print('  CLAUDE.md  %d개 절, %d줄, %.0f KB' % (len(heads), c.count(chr(10)) + 1, len(c.encode()) / 1024))
for x in heads:
    print('     ' + x[:66])
print('  HISTORY.md %d개 절, %d줄, %.0f KB'
      % (len(re.findall(r'^## ', h, re.M)), h.count(chr(10)) + 1, len(h.encode()) / 1024))

print()
print('판정:', 'PASS' if not miss and not bad else 'FAIL — %s %s' % (miss, bad))
