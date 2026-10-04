#!/usr/bin/env python3
"""How big does every circuit diode print, figure by figure?

Draws each AN figure the way figcheck does (figs.save intercepted, nothing
written) and converts every recorded 'diode' symbol to its size on the
printed page, in points, with figcheck's own page-scale arithmetic.  The
body diode inside the MOSFET symbol is not a recorded symbol and is left
out on purpose (it is drawn small by design).

    python diode_survey.py              # every figure
    python diode_survey.py an_full f04  # a few
    python diode_survey.py --kind mosfet   # the switches instead

One line per figure: how many diodes, the smallest and the largest in
points on the page, and the drawn size at scale 1 behind them.
"""
import sys

import matplotlib

KIND = 'diode'
if '--kind' in sys.argv:
    i = sys.argv.index('--kind')
    KIND = sys.argv[i + 1]
    del sys.argv[i:i + 2]
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                  # noqa: E402

import figcheck                                                  # noqa: E402
import figs                                                      # noqa: E402

figs.PLAIN = True
rows = {}


def spy(fig, nm):
    fig.canvas.draw()
    out = []
    for ax in fig.axes:
        recs = [r for r in getattr(ax, '_syms', []) if r[0] == KIND]
        if not recs:
            continue
        ppd = figcheck._page_pt(fig, nm, ax)
        for kind, x, y, w, h, *rest in recs:
            k = rest[0] if rest else 1.0
            out.append((max(w, h) * ppd, max(w, h) / k))
    rows[nm] = out
    plt.close(fig)


figs.save = spy
want = sys.argv[1:] or sorted(figs.FIGS)
for key in want:
    try:
        figs.FIGS[key]()
    except Exception as e:                                       # noqa: BLE001
        print('%-22s ERROR %r' % (key, e))
import figs_modes8                                               # noqa: E402
for k, nums in (('an_modes_12', (1, 2)), ('an_modes_34', (3, 4)),
                ('an_modes_56', (5, 6)), ('an_modes_78', (7, 8))):
    if sys.argv[1:] and k not in sys.argv[1:]:
        continue
    spy(figs_modes8.sheet_fig(nums), k)

print('%-22s %3s  %7s %7s   %s' % ('figure', 'n', 'min pt', 'max pt',
                                   'drawn at scale 1 (min..max)'))
allpt = []
for nm in sorted(rows):
    r = rows[nm]
    if not r:
        continue
    pts = [p for p, _ in r]
    sc = [s for _, s in r]
    allpt += pts
    print('%-22s %3d  %7.1f %7.1f   %.3f..%.3f' % (nm, len(r), min(pts),
                                                  max(pts), min(sc), max(sc)))
if allpt:
    print('\nall figures: %d %ss, %.1f to %.1f pt on the page'
          % (len(allpt), KIND, min(allpt), max(allpt)))
