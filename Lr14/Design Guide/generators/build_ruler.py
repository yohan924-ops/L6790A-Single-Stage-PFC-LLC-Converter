# -*- coding: utf-8 -*-
"""A ruler down the sheet, so the page break can be READ instead of solved.

Every attempt to recover SMath's page break from the design sheet failed,
and the reason is now clear: the rows I was using as landmarks are rows
fit() had already pushed to what IT thinks is a page boundary, so they sit
at exact multiples of the number being tested. The model was checking
itself. The one independent datum - a row whose label printed on page 12
and whose formula printed on page 13 - contradicts every page height that
fits the rest, with or without an origin offset or a per-fold correction.

So measure it. This sheet is nothing but numbered markers, 20 px apart and
20 px tall, running down eight pages:

    no formulas   - so nothing has to be recalculated and F9 is irrelevant
    no folds      - so visible y and absolute y are the same number
    no graphs     - so nothing can be pushed for a reason of its own

Print it. The first marker on each page names the break to within 20 px,
and a marker that vanishes from the bottom of one page and reappears at the
top of the next names it to within its own height. Eight pages give seven
independent readings, which settles the page height and whether the first
page is offset from the rest.

    python build_ruler.py          -> Smath/L6790A_ruler.sm
"""
import io
import os

import smsheet as SM

STEP = 20
HEIGHT = 20
PAGES = 8

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', '..', 'Smath', 'L6790A_ruler.sm')

S = SM.Sheet('L6790A page-break ruler', author='', desc='')

# One marker every STEP px. The text is its own y, so a printed page can be
# read straight off the paper with no counting.
top = 0
n = int(PAGES * S.PAGE_H / STEP)
for i in range(n):
    y = 24 + i * STEP
    S.y = y
    S._emit(20, 300, HEIGHT,
            '    <text lang="eng" fontFamily="Arial" fontSize="9">\n'
            '      <content>\n'
            '        <p style="font-weight: normal; font-style: normal; '
            'font-size: 9px;">y = %d</p>\n'
            '      </content>\n    </text>' % y,
            ' color="#000000" fontSize="9"')
    # every fifth marker also on the right, so a page cannot be mistaken
    if i % 5 == 0:
        S._emit(1200, 300, HEIGHT,
                '    <text lang="eng" fontFamily="Arial" fontSize="9">\n'
                '      <content>\n'
                '        <p style="font-weight: normal; font-style: normal; '
                'font-size: 9px;">---- y = %d ----</p>\n'
                '      </content>\n    </text>' % y,
                ' color="#c00000" fontSize="9"')

S.y = 24 + n * STEP
S.save(OUT)
print('wrote %s' % os.path.normpath(OUT))
print('  %d markers, %d px apart, %d px tall, %d px of sheet'
      % (n, STEP, HEIGHT, n * STEP))
print('  paper %d x %d, the same as the design sheet' % (S.PAGE_W, S.PAGE_H))
print()
print('Print it with the usual settings and read off, for each page, the')
print('first "y =" that appears and the last one before it. The break is')
print('between those two numbers.')
