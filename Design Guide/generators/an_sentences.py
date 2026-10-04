#!/usr/bin/env python3
"""Which sentences of the English AN are long?

Reads the built PDF page by page, joins the body text, splits it into
sentences and lists every sentence longer than a word limit (default 40)
with its page.  Headings, captions, table cells and equations are left
out as far as the text layer allows (a run without a full stop is not a
sentence).  A length histogram comes first so the limit can be chosen.

    python an_sentences.py            # limit 40 words
    python an_sentences.py 32         # another limit
    python an_sentences.py 32 --kr    # the Korean edition
"""
import os
import re
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
EN = os.path.join(HERE, '..', 'AN_L6790A_SingleStage_PFC_LLC_ApplicationNote_v1.3.pdf')
KR = os.path.join(HERE, '..', 'AN_L6790A_SingleStage_PFC_LLC_ApplicationNote_KR_v1.3.pdf')

args = [a for a in sys.argv[1:] if not a.startswith('--')]
LIMIT = int(args[0]) if args else 40
PDF = KR if '--kr' in sys.argv else EN
KR = '--kr' in sys.argv

doc = pymupdf.open(PDF)
hist = {}
long_ = []
for pno, page in enumerate(doc, 1):
    blocks = page.get_text('blocks')
    for b in blocks:
        t = ' '.join(b[4].split())
        if len(t) < 60 or re.match(r'^(Figure|Table|Equation|그림|표|식) \d+', t):
            continue
        if re.match(r'^\d+(\.\d+)?\s+[A-Z가-힣]', t) and len(t) < 90:
            continue
        #  split at . ! ? followed by a space and a capital, keeping
        #  decimals (2.5), abbreviations (e.g.) and section numbers whole
        if KR:
            #  Korean: a sentence ends in 다/음/것 + full stop; a following
            #  capital is no clue, so split at every stop followed by space
            parts = re.split(r'(?<=[.!?])\s+(?=[^\d\)])', t)
        else:
            parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"“(])', t)
        for s in parts:
            w = len(s.split())
            if w < 4:
                continue
            k = min(w // 10 * 10, 70)
            hist[k] = hist.get(k, 0) + 1
            if w > LIMIT:
                long_.append((pno, w, s))

tot = sum(hist.values())
print('sentences: %d' % tot)
for k in sorted(hist):
    lab = '%2d-%2d' % (k, k + 9) if k < 70 else '70+  '
    print('  %s words  %4d  %s' % (lab, hist[k], '#' * (hist[k] // 10)))
print('\n%d sentences over %d words:' % (len(long_), LIMIT))
for pno, w, s in long_:
    print('\np%d  (%d words)\n  %s' % (pno, w, s))
