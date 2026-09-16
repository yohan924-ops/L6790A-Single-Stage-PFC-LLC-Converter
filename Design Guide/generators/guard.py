# -*- coding: utf-8 -*-
"""Stop-hook guard: do not let a turn end with the documents out of step.

This exists because of a specific failure. Twice now the two documents drifted
apart right after they had been reported identical - once when the output
capacitor selection changed in the workbook only, once when the builder was
edited but the sheet was never rebuilt. Nothing catches that; the numbers just
quietly disagree until someone runs the comparison by hand.

What it checks, only when one of the tracked files has actually changed:

    1. is the sheet older than the builder that makes it?   -> rebuild needed
    2. check_sm.py    - geometry, overlaps, functions, XML
    3. bom_compare.py - the 29 BOM items, workbook against sheet
    4. snapshot.py    - does CLAUDE.md still describe the sheet it points at?
    5. audit_md.py    - do the documents describe things that exist?

Check 4 is the one that matters across machines. CLAUDE.md is what a session
opening this folder somewhere else reads first, and its design values are
generated from the worksheet. If someone changes a yellow cell and the block is
not regenerated, the next session works from numbers that are quietly wrong.

Silent and instant when nothing changed, or when everything passes. On failure
it exits 2, which blocks the turn from ending and hands the reason back.

It never writes to the worksheet. Rebuilding is a decision, not a side effect -
the sheet may hold layout the user set by hand in SMath.
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SM = os.path.join(ROOT, 'Smath', 'L6790A_SingleStage_PF_LLC_Design_Guide.sm')
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')
BUILDERS = [os.path.join(HERE, n) for n in ('build_l6790_smath.py', 'smsheet.py', 'l6790.py')]
DOC = os.path.join(ROOT, 'CLAUDE.md')
STAMP = os.path.join(HERE, '.guard_stamp.json')

TRACKED = [SM, XL, DOC] + BUILDERS


def mtimes():
    out = {}
    for p in TRACKED:
        try:
            out[os.path.basename(p)] = os.path.getmtime(p)
        except OSError:
            out[os.path.basename(p)] = 0.0
    return out


def run(args):
    try:
        r = subprocess.run([sys.executable] + args, cwd=HERE, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=180)
        return r.returncode, (r.stdout or '') + (r.stderr or '')
    except Exception as e:                      # noqa: BLE001 - report, never raise
        return 1, 'could not run %s: %s' % (' '.join(args), e)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:                           # noqa: BLE001
        payload = {}
    # already re-entered from a previous block - let the turn end
    if payload.get('stop_hook_active'):
        return 0

    now = mtimes()
    try:
        with io.open(STAMP, encoding='utf-8') as fh:
            before = json.load(fh)
    except Exception:                           # noqa: BLE001
        before = None

    if before == now:
        return 0                                # nothing touched, nothing to say

    problems = []

    # 1. sheet older than the code that generates it
    if os.path.exists(SM):
        newest_builder = max((os.path.getmtime(b) for b in BUILDERS
                              if os.path.exists(b)), default=0.0)
        if newest_builder > os.path.getmtime(SM) + 1:
            stale = [os.path.basename(b) for b in BUILDERS
                     if os.path.exists(b) and os.path.getmtime(b) > os.path.getmtime(SM) + 1]
            problems.append(
                'The worksheet is older than %s. Run build_l6790_smath.py - but read the '
                'file first: if the user re-saved it in SMath, fold their layout back into '
                'the builder before overwriting it.' % ' and '.join(stale))

    # 2. geometry and XML
    rc, out = run(['check_sm.py', SM])
    if rc != 0 or 'VERDICT        OK' not in out:
        problems.append('check_sm.py did not pass:\n' + tail(out))

    # 3. the two BOMs
    rc, out = run(['bom_compare.py'])
    if rc == 2 or '열려 있어' in out:
        pass                     # workbook open in Excel; nothing to compare
    elif rc != 0 or '  different: 0' not in out:
        problems.append('The workbook and the worksheet disagree:\n' + tail(out))

    # 4. does CLAUDE.md still describe this sheet?
    rc, out = run(['snapshot.py', '--check'])
    if rc != 0:
        problems.append(
            'CLAUDE.md section 3 no longer matches the worksheet. Run snapshot.py - it '
            'rewrites the block and prints what moved. Do not edit those numbers by hand.\n'
            + tail(out, 4))

    # 5. do the documents still describe things that exist?
    rc, out = run(['audit_md.py'])
    if rc != 0:
        problems.append('CLAUDE.md / HISTORY.md claim something that is not true '
                        '(missing path, dangling section reference, stale count):'
                        + chr(10) + tail(out, 8))

    if problems:
        sys.stderr.write(
            'L6790 guard - the deliverables are out of step:\n\n'
            + '\n\n'.join('  * ' + p for p in problems)
            + '\n\nFix these, or say plainly in your reply that you are leaving them '
              'inconsistent and why.\n')
        return 2                                # blocks the stop, reason goes to Claude

    with io.open(STAMP, 'w', encoding='utf-8') as fh:
        json.dump(now, fh, indent=1)
    return 0


def tail(text, n=14):
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    return '\n'.join('      ' + ln for ln in lines[-n:])


if __name__ == '__main__':
    sys.exit(main())
