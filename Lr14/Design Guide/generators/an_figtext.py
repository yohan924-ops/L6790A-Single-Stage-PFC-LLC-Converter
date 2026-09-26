# -*- coding: utf-8 -*-
"""What the AN figures SAY, checked against the rest of the note.

Every other check reads either the prose (an_symbols, an_check) or the
figure's geometry (figcheck).  Nothing read the words and numbers drawn
INSIDE a figure, and that is where the errors of 2026-09-23 were: a
winding named for the wrong half period, a quantity called v_tank in two
figures and v_d everywhere else, a current with no place on any circuit.
So this collects every string each AN figure draws - at save time, the
way figcheck does, nothing is written - and reports:

  UNDEFINED  a symbol drawn in a figure that the symbol table does not
             list, or that neither the prose up to that figure nor the
             figure's own caption has written yet
  LITERAL    a number with a unit drawn in a figure whose digits sit
             inside a string literal of the code that drew it - typed,
             not formatted from l6790 / an_pdf.V.  Only string tokens of
             the functions on the call stack are searched, so a font
             size of 12 does not stand for '12 ms'; until 2026-09-23 the
             whole source was searched and numbers under three digits
             were skipped to keep that quiet, which let '5 %', '12 ms'
             and '25 V' through
  USES       every subscripted symbol and the figures that draw it, so
             two names for one quantity can be seen side by side

    python an_figtext.py            all three
    python an_figtext.py --uses     the cross-figure list only
"""
import inspect
import io
import os
import re
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
import matplotlib                                                    # noqa
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                      # noqa
from matplotlib.text import Text                                     # noqa

import an_symbols as SY                                              # noqa

#  drawn from the ST design spreadsheet, not by us (figures.md)
IMPORTED = {'bom_power_stage', 'bom_pin_config', 'comp_network_st'}
UNIT = r'(?:Vac|Vdc|kHz|MHz|Hz|mT|mF|uF|µF|nF|pF|µH|uH|mH|kΩ|mΩ|Ω|ms|µs|us|ns|W|V|A|%|°)'
_NUM = re.compile(r'(?<![\w.])(\d+(?:\.\d+)?)\s*(' + UNIT + r')(?![A-Za-z])')
_SUB = re.compile(r'(\\[A-Za-z]+|[A-Za-z]+)\$?\s*_\s*(\{[^{}$]*\}|[A-Za-z0-9])')
_GRK = re.compile(r'\\(Phi|mu|lambda|theta|phi|Delta|delta|eta|omega|tau)\b')


_STR_CACHE = {}


def _strings(code):
    """the string literals of one function, comments and numbers left out"""
    if code in _STR_CACHE:
        return _STR_CACHE[code]
    try:
        src = inspect.getsource(code)
    except (OSError, TypeError):
        src = ''
    toks = []
    try:
        for tk in tokenize.generate_tokens(io.StringIO(
                __import__('textwrap').dedent(src)).readline):
            if tk.type == tokenize.STRING or tk.type == getattr(
                    tokenize, 'FSTRING_MIDDLE', -1):
                toks.append(tk.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    _STR_CACHE[code] = '\n'.join(toks)
    return _STR_CACHE[code]


_CALLED = set()


def _prof(frame, event, _arg):
    """remember every figs* function entered while a figure is drawn,
    helpers that return before save() included"""
    #  a module body is the whole file: an import made inside a figure
    #  would lend it every string of that module
    if event == 'call' and frame.f_code.co_name != '<module>' and \
            os.path.basename(frame.f_code.co_filename).startswith('figs'):
        _CALLED.add(frame.f_code)


def _stack_strings():
    """string literals of every figure function called since the last grab"""
    out = [_strings(c) for c in _CALLED]
    _CALLED.clear()
    return '\n'.join(out)


SRCS = {}


def collect():
    """{figure: [every visible string]} for every figure the AN places"""
    sys.argv = ['figs.py']
    import figs
    import figs_modes8
    figs.PLAIN = True
    out = {}

    def grab(fig, name):
        out[name] = [t.get_text().strip() for t in fig.findobj(Text)
                     if t.get_visible() and t.get_text().strip()]
        SRCS[name] = SRCS.get(name, '') + _stack_strings()
        plt.close(fig)
    keep = figs.save
    figs.save = grab
    sys.setprofile(_prof)
    try:
        for k, f in list(figs.FIGS.items()):
            try:
                f()
            except Exception as ex:                          # noqa: BLE001
                print('ERROR drawing %s: %r' % (k, ex))
        for k, nums in (('an_modes_12', (1, 2)), ('an_modes_34', (3, 4)),
                        ('an_modes_56', (5, 6)), ('an_modes_78', (7, 8))):
            grab(figs_modes8.sheet_fig(nums), k)
        #  the strip under the mode sheets, drawn the way build() draws it
        from l6790 import sweep
        _, agg = sweep(figs.R, figs.R['Vin_min'], N=721)
        fig, axes = plt.subplots(4, 1, sharex=True)
        figs_modes8.waveforms(axes, figs.R['lam_a'], 0.70, agg['comp_pk'],
                              agg['ILm_pk'])
        grab(fig, 'an_modes_wave')
    finally:
        sys.setprofile(None)
        figs.save = keep
    return out


def fig_symbols(texts):
    out = set()
    for t in texts:
        s = t.replace('$', '')
        for m in _SUB.finditer(t):
            base, sub = m.group(1), m.group(2).strip('{}')
            if base.startswith('\\') and base[1:] in SY.NOTSYM:
                continue
            #  a subscripted WORD is a label, not a symbol ('rms_x')
            if len(base) > 3 and not base.startswith('\\'):
                base = base[-1]
            out.add(SY.norm(SY._canon(base, sub)))
        for m in _GRK.finditer(s):
            out.add(SY.norm('\\' + m.group(1)))
    return out


class Rec(SY.Rec):
    def fig(self, name, caption, **kw):
        self._add('fig:' + name, caption)


def main():
    only_uses = '--uses' in sys.argv
    import an_pdf as A
    import an_body
    r = Rec()
    r.keys, r.tex = {}, {}
    saved = {}
    for nm in ('p', 'note', 'h1', 'h2', 'bullets', 'fig', 'tbl', 'eq',
               'eqagain', 'calc'):
        saved[nm] = getattr(A, nm)
        setattr(A, nm, getattr(r, nm))
    try:
        an_body.build(A)
    finally:
        for nm, fn in saved.items():
            setattr(A, nm, fn)
    raw = SY.table_symbols(A)
    SY.set_bare(SY.BARE | {k for k in raw if '_' not in k and len(k) > 1
                           and k not in SY.WORDS})
    table = {SY.norm(k) for k in raw}

    texts = collect()
    order, caption, seen_by = [], {}, {}
    known = set()
    for kind, i, payload in r.log:
        if kind.startswith('fig:'):
            nm = kind[4:]
            if nm not in caption:
                order.append(nm)
                caption[nm] = payload
                seen_by[nm] = set(known)
                #  a label drawn on a circuit names that part for every
                #  figure after it - Figure 1 is where L_r is defined
                known |= fig_symbols(texts.get(nm, []))
        if kind in ('text', 'head') or kind.startswith('fig:'):
            known |= {SY.norm(k) for k in SY.prose_symbols(payload)}
        elif kind.startswith('eq') or kind == 'calc':
            known |= {SY.norm(k) for k in SY.tex_symbols(payload)}

    uses = {}
    n_und = n_lit = 0
    for num, nm in enumerate(order, 1):
        if nm in IMPORTED:
            continue
        tx = texts.get(nm)
        if tx is None:
            print('Figure %2d %-22s NOT COLLECTED' % (num, nm))
            continue
        syms = fig_symbols(tx)
        cap = {SY.norm(k) for k in SY.prose_symbols(caption[nm])}
        for k in syms:
            uses.setdefault(k, []).append(num)
        if only_uses:
            continue
        bad = sorted(k for k in syms
                     if k not in SY.DUMMY and
                     (k not in table or k not in (seen_by[nm] | cap)))
        lits = []
        srcs = SRCS.get(nm, '')
        for t in tx:
            for m in _NUM.finditer(t.replace('$', '')):
                digits = m.group(1)
                if re.search(r"(?<![\w.%])" + re.escape(digits)
                             + r"(?![\w.])", srcs):
                    lits.append(m.group(0))
        if bad or lits:
            print('Figure %2d %s' % (num, nm))
        for k in bad:
            why = ('not in the symbol table' if k not in table else
                   'not written before this figure or in its caption')
            print('   UNDEFINED  %-14s %s' % (k, why))
            n_und += 1
        for l_ in sorted(set(lits)):
            print('   LITERAL    %s' % l_)
            n_lit += 1
    print()
    print('USES - each subscripted symbol and the figures drawing it')
    for k in sorted(uses):
        print('   %-16s %s' % (k, ' '.join(str(n) for n in uses[k])))
    if not only_uses:
        print()
        print('%d figures · %d undefined · %d literal numbers to confirm'
              % (len(order), n_und, n_lit))


if __name__ == '__main__':
    main()
