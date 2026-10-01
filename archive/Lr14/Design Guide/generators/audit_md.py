# -*- coding: utf-8 -*-
"""Check CLAUDE.md and HISTORY.md against the things they claim.

Re-reading them by eye is how the 80 mF / 71.4 mF error survived for days, so
every checkable claim is checked mechanically here instead:

    - a file or folder named in backticks exists (or is explicitly marked gone)
    - a section cross-reference resolves to a real heading
    - a script named in the tool tables is really in generators/
    - counts quoted in prose (regions, pages, yellow cells, BOM items, paper
      size) match what check_sm.py / bom_compare.py report right now
    - the doc-roles table and the sentence introducing it agree
    - every .sm and .xlsx on disk appears somewhere in CLAUDE.md

    python audit_md.py          -> lists problems, exit 1 if any

A section number belongs to whichever document the words before it name - the
guide, the datasheet, the SMath sheet - so an unqualified "§16.6" is reported:
a reader on another machine cannot tell which document it means.
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SM = os.path.join(ROOT, 'Smath', 'L6790A_SingleStage_PF_LLC_Design_Guide.sm')

# Words that qualify a section number, so "§4.2" is not ambiguous after them
# 'AN ' joined the list when the application note became a deliverable
# with numbered sections of its own - "AN §6.5" is qualified, "§6.5" is not.
QUALIFIERS = ('가이드', '시트', 'DS', '데이터시트', '스프레드시트', '워크북',
              'HISTORY.md', 'CLAUDE.md', 'DESIGN.md', 'README', '부록', '논문', 'AN ', 'AN§')

# Paths the docs mention on purpose while saying they are not here
ABSENT_OK = {
    'L6790A_Section3_Calculation_Sheet_1page.sm',
    'L6790A_Section3_PowerStage_Tank_rev1_1.sm',
    'Smath/L6790A_Section3_PowerStage_Tank_rev1_1.sm',
    'ppt/media/image1.png',          # a path inside a .potx, not on disk
    'ST_Template__16-9_.potx',
    # deleted on purpose 2026-09-23: the AN carries the same material
    'Design Guide/L6790A_Transformer_Design_KR_v1.0.pdf',
    'L6790A_Transformer_Design_KR_v1.0.pdf',
    'tx_pdf.py', 'tx_body.py',
    'Design Guide/generators/tx_pdf.py', 'Design Guide/generators/tx_body.py',
    # the training deck was dropped 2026-09-23, with the tools that only served it
    'Training Material/L6790A_SingleStage_PF_LLC_Design_Training.pptx',
    'L6790A_SingleStage_PF_LLC_Design_Training.pptx',
    'check_deck.py', 'deckedit.py', 'fix_deck_overflow.py',
    # deleted on purpose 2026-09-08: the vendor spec is superseded by the
    # three in variants/, the KH form was already 폐기 예정, and the encrypted
    # original was replaced by the decrypted copy beside it
    'Calculation Excel Sheet/LGE_670W_L6790A_Transformer_Spec_rev1.xlsx',
    'Calculation Excel Sheet/L6790_Trans_20260901.xlsx',
    'Calculation Excel Sheet/04092026_LGE_670W_L6790A_spread sheet.xlsx',
    'L6790_Trans_20260901.xlsx',
    'LGE_670W_L6790A_Transformer_Spec_rev1.xlsx',
    # deleted on purpose 2026-09-23: the canonical sheet and workbook became
    # 7.5:1 and the 9:1 design point was dropped (HISTORY.md 46차)
    'Smath/variants/L6790A_9to1.sm',
    'Transformer_Spec_9to1.xlsx',
    'Calculation Excel Sheet/variants/L6790_workbook_9to1.xlsx',
    'L6790_workbook_9to1.xlsx',
    'Design Guide/AN_L6790A_Design_Guide_rev2_0.md',
    'AN_L6790A_Design_Guide_rev2_0.md',
    # CLAUDE.md 9.1b names this file while saying it is not installed here
    '.claude/settings.json',
}

problems = []


def bad(doc, what):
    problems.append('%-11s %s' % (doc, what))


def find_anywhere(name):
    """the docs cite bare filenames; look for them anywhere under the project"""
    base = os.path.basename(name.rstrip('/'))
    for d, _, files in os.walk(ROOT, followlinks=True):   # Lr14: links
        if base in files or os.path.basename(d) == base:
            return True
    return os.path.exists(os.path.join(ROOT, name))


def main():
    # README.md carries CLAUDE.md's old sections 9 and 11 (moved 2026-09-22).
    # It is read here so the path / script / count checks keep their reach -
    # otherwise moving a section would silently switch its checks off.
    docs = {}
    docs['CLAUDE.md'] = io.open(os.path.join(ROOT, 'CLAUDE.md'), encoding='utf-8').read()
    docs['HISTORY.md'] = io.open(os.path.join(ROOT, 'docs', 'HISTORY.md'), encoding='utf-8').read()
    docs['README.md'] = io.open(os.path.join(HERE, 'README.md'),
                                encoding='utf-8').read()
    # docs/DESIGN.md holds the design sections (old CLAUDE.md 1.3/3/4.2/4.3/5/6/7)
    docs['DESIGN.md'] = io.open(os.path.join(ROOT, 'docs', 'DESIGN.md'),
                                encoding='utf-8').read()

    # ---------------------------------------------------------- paths
    path_re = re.compile(r'`([A-Za-z0-9_./ &\-]+\.'
                         r'(?:md|py|sm|xlsx|pdf|pptx|potx|json|js|png))`')
    dir_re = re.compile(r'`((?:Design Guide|Smath|Reference|Datasheet|EVB Schematic|'
                        r'LGE Material|Training Material|Calculation Excel Sheet)'
                        r'/[A-Za-z0-9_./ &\-]*)`')
    for name, txt in docs.items():
        for p in sorted(set(path_re.findall(txt)) | set(dir_re.findall(txt))):
            if p in ABSENT_OK or ' ' in p and p.startswith('python '):
                continue
            if not find_anywhere(p):
                bad(name, 'path does not exist: %s' % p)

    # ------------------------------------------------- section refs
    def headings(txt):
        out = set()
        for m in re.finditer(r'^#{2,3} (\d+)(?:\.(\d+[a-z]?))?', txt, re.M):
            out.add(m.group(1))
            if m.group(2):
                out.add(m.group(1) + '.' + m.group(2))
        return out

    H = {k: headings(v) for k, v in docs.items()}
    for name, txt in docs.items():
        for m in re.finditer(r'`(?:docs/)?(CLAUDE|HISTORY|DESIGN)\.md`\s*§\s*([\d.]+[a-z]?)', txt):
            sec = m.group(2).rstrip('.')
            if sec not in H[m.group(1) + '.md']:
                bad(name, 'cross-ref %s.md §%s: no such section' % (m.group(1), sec))
        for m in re.finditer(r'(?<![.\w])§\s*(\d+(?:\.\d+[a-z]?)?)', txt):
            sec, before = m.group(1), txt[max(0, m.start() - 24):m.start()]
            if any(q in before for q in QUALIFIERS):
                continue
            if sec not in H[name]:
                bad(name, 'unqualified §%s - which document is it in?' % sec)

    # ----------------------------------------------------- scripts
    for name, txt in docs.items():
        for s in sorted(set(re.findall(r'`([a-z0-9_]+\.py)`', txt))):
            if not os.path.exists(os.path.join(HERE, s)) and s not in ABSENT_OK:
                bad(name, 'script not in generators/: %s' % s)

    # ------------------------------------------- counts vs the tools
    def run(args):
        r = subprocess.run([sys.executable] + args, cwd=HERE, capture_output=True,
                           text=True, encoding='utf-8', errors='replace')
        return r.stdout + r.stderr

    chk, bom = run(['check_sm.py', SM]), run(['bom_compare.py'])
    locked = '열려 있어' in bom          # workbook open in Excel: counts unavailable
    facts = {}
    for pat, key in ((r'regions\s+(\d+)', 'regions'), (r'=\s+([\d.]+) pages', 'pages'),
                     (r'yellow inputs (\d+)', 'yellow'), (r'plots (\d+)', 'plots'),
                     (r'pictures (\d+)', 'pictures'),
                     (r'items compared: (\d+)', 'bom')):
        src = bom if key == 'bom' else chk
        m = re.search(pat, src)
        facts[key] = m.group(1) if m else '?'
    m = re.search(r'(\d+) x (\d+) px', chk)
    facts['paper'] = '%s x %s' % m.groups() if m else '?'

    # counts and the on-disk map may be quoted in either document; keep the
    # name so the report points at the file that actually carries the claim
    QUOTERS = ('CLAUDE.md', 'DESIGN.md', 'README.md')

    def where(pat):
        for n in QUOTERS:
            m = re.search(pat, docs[n])
            if m:
                return n, m
        return QUOTERS[0], None

    c = '\n'.join(docs[n] for n in QUOTERS)
    for phrase, key, expect in (('노란 입력 셀 %s개' % facts['yellow'], 'yellow', None),
                                ('yellow inputs', 'yellow', None),
                                ('regions', 'regions', None),
                                ('items compared:', 'bom', None),
                                ('plots', 'plots', None),
                                ('pictures', 'pictures', None)):
        pass
    for phrase, key in (('regions %s' % facts['regions'], 'regions'),
                        ('yellow inputs %s' % facts['yellow'], 'yellow'),
                        ('items compared: %s' % facts['bom'], 'bom'),
                        ('plots %s' % facts['plots'], 'plots'),
                        ('pictures %s' % facts['pictures'], 'pictures'),
                        ('%s pages' % facts['pages'], 'pages'),
                        (facts['paper'], 'paper')):
        # the phrase built from the CURRENT fact must be the one in the doc;
        # if the doc quotes a different number the stale one shows up here
        stem = phrase.rsplit(' ', 1)[0] if key != 'paper' else 'x'
        if key == 'paper':
            doc, m2 = where(r'(\d+) x (\d+) px')
            if m2 and '%s x %s' % m2.groups() != facts['paper']:
                bad(doc, 'paper claim %s x %s, tool says %s'
                    % (m2.group(1), m2.group(2), facts['paper']))
            continue
        doc, m2 = where(re.escape(stem) + r' ([\d.]+)')
        if key == 'bom' and locked:
            continue                      # cannot read the workbook right now
        if m2 and m2.group(1) != facts[key]:
            bad(doc, 'claims "%s %s" but tool reports %s'
                % (stem, m2.group(1), facts[key]))

    # -------------------------------------------- internal consistency
    rows = len(re.findall(r'^\| \*\*`[\w/ ]+\.md`\*\*', docs['CLAUDE.md'], re.M))
    m = re.search(r'문서는 (\S+?)(?:이고|인데)', docs['CLAUDE.md'])
    if m and {2: '둘', 3: '셋', 4: '넷'}.get(rows) not in (None, m.group(1)):
        bad('CLAUDE.md', 'says 문서는 %s but the table lists %d' % (m.group(1), rows))

    for sub, ext in (('Smath', '.sm'), ('Calculation Excel Sheet', '.xlsx')):
        d = os.path.join(ROOT, sub)
        for f in os.listdir(d) if os.path.isdir(d) else []:
            if f.startswith('BACKUP_'):      # transient by policy, see CLAUDE.md 6.2
                continue
            if f.endswith(ext) and f not in c:
                bad('CLAUDE.md', 'on disk but not in the map: %s/%s' % (sub, f))

    print('tools report:', ' · '.join('%s=%s' % kv for kv in sorted(facts.items())))
    print()
    if problems:
        print('%d problem(s):' % len(problems))
        for p in problems:
            print('  ' + p)
        return 1
    print('no problems found')
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
