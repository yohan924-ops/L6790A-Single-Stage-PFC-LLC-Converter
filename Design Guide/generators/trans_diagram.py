# -*- coding: utf-8 -*-
"""Schematic diagram of the requirements-only transformer spec (2026-10-18, user).

Drawn the way the approval sheet of the production part 26OP-LM83W draws it
(KH Feelux, "2. SCHEMATIC DIAGRAM"): the primary pins in a row above the core,
the secondary pins in a row below it, each winding a bracket between its two
pins, the dot at its start.  The auxiliary a-b sits between the primary pins 1
and 2, nested inside NP1 - the user's drawing on that sheet.

    python trans_diagram.py      writes trans_diagram_en.png / _kr.png here,
                                 for a look; the spec builder calls draw()
"""
import io
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                 # noqa: E402
from matplotlib import font_manager             # noqa: E402

WQY = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
TXT = {'en': dict(pri='PRIMARY', sec='SECONDARY', dot='winding start (S)'),
       'kr': dict(pri='1차', sec='2차', dot='감기 시작 (S)')}
INK = '#1a1a1a'


def draw(lang, term):
    """PNG bytes.  term: {'NP1': (S, F), 'NAUX': ..., 'NS2': ..., 'NS3': ...}"""
    if lang == 'kr' and os.path.exists(WQY):
        font_manager.fontManager.addfont(WQY)
        family = font_manager.FontProperties(fname=WQY).get_name()
    else:
        family = 'DejaVu Sans'
    t = TXT[lang]
    fig = plt.figure(figsize=(6.4, 2.6), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 38.6)
    ax.axis('off')
    kw = dict(color=INK, lw=1.1, solid_capstyle='butt')

    def pin(x, y, s):
        ax.add_patch(plt.Circle((x, y), 2.2, fill=False, ec=INK, lw=1.1))
        ax.text(x, y - 0.1, s, ha='center', va='center', fontsize=12,
                family=family, color=INK)

    def bracket(x0, x1, y_pins, y_bar):
        top = y_pins - 2.2 if y_bar < y_pins else y_pins + 2.2
        ax.plot([x0, x0, x1, x1], [top, y_bar, y_bar, top], **kw)

    def label(x, y, name, dot_left):
        if dot_left:
            ax.plot([x], [y], 'o', color=INK, ms=5.2)
            ax.text(x + 1.3, y, name, ha='left', va='center', fontsize=11.5,
                    family='DejaVu Sans', color=INK)
        else:
            ax.plot([x], [y], 'o', color=INK, ms=5.2)
            ax.text(x - 1.3, y, name, ha='right', va='center', fontsize=11.5,
                    family='DejaVu Sans', color=INK)

    # core: the double line of the approval sheet
    for y in (19.25, 19.95):
        ax.plot([5, 66], [y, y], color=INK, lw=1.0)

    # primary row: NP1 start, NAUX start, NAUX finish, NP1 finish
    yp = 34.5
    x1, xa, xb, x2 = 19.0, 31.0, 46.0, 58.0
    bracket(x1, x2, yp, 22.0)                     # NP1, the outer bracket
    bracket(xa, xb, yp, 26.6)                     # NAUX inside it
    for x, s in ((x1, term['NP1'][0]), (xa, term['NAUX'][0]),
                 (xb, term['NAUX'][1]), (x2, term['NP1'][1])):
        pin(x, yp, str(s))
    label(x1 + 1.6, 23.7, 'NP1', True)            # dot at the start, pin 1
    label(xa + 1.6, 28.5, 'NAUX', True)           # dot at the start, pin a

    # secondary row: NS3 finish, NS2 finish, NS3 start, NS2 start (6 5 4 3)
    ys = 4.2
    x6, x5, x4, x3 = 12.0, 27.0, 42.0, 57.0
    bracket(x3, x5, ys, 17.4)                     # NS2: 3 -> 5
    bracket(x4, x6, ys, 14.4)                     # NS3: 4 -> 6, crosses NS2
    for x, s in ((x6, term['NS3'][1]), (x5, term['NS2'][1]),
                 (x4, term['NS3'][0]), (x3, term['NS2'][0])):
        pin(x, ys, str(s))
    label(x3 - 1.6, 15.5, 'NS2', False)           # dot at the start, pin 3
    label(x4 - 1.6, 12.4, 'NS3', False)           # dot at the start, pin 4

    ax.text(71, 28.5, t['pri'], ha='left', va='center', fontsize=12,
            family=family, color=INK, fontweight='bold')
    ax.text(71, 10.5, t['sec'], ha='left', va='center', fontsize=12,
            family=family, color=INK, fontweight='bold')
    ax.plot([72], [3.0], 'o', color=INK, ms=5.2)
    ax.text(73.6, 3.0, t['dot'], ha='left', va='center', fontsize=10.5,
            family=family, color='#5A6472')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=220, facecolor='white')
    plt.close(fig)
    return buf.getvalue()


if __name__ == '__main__':
    TERM = {'NP1': (1, 2), 'NAUX': ('a', 'b'), 'NS2': (3, 5), 'NS3': (4, 6)}
    here = os.path.dirname(os.path.abspath(__file__))
    for lang in ('en', 'kr'):
        out = os.path.join(here, 'trans_diagram_%s.png' % lang)
        with open(out, 'wb') as f:
            f.write(draw(lang, TERM))
        print(out)
