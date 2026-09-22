# -*- coding: utf-8 -*-
"""Every symbol the note uses, and whether the reader was ever told what it is.

Written because one got through: the design example divided by `a_s`
before anything had said what a strand was or what `a_s` meant, and it
was found by a reader rather than by a check (2026-09-22, user).  Eyes
will not do this job - the note has sixty-seven numbered equations and
several hundred subscripted names in the prose, and the ones that go
unexplained are exactly the ones nobody notices.

What it does:

  1. Replays an_body.build() with the layout calls swapped for recorders,
     so it sees the finished text in document order - after the % dict()
     interpolation, which is where half the symbols actually appear - and
     without rendering a single equation PNG.
  2. Pulls symbol names out of two languages: TeX, from the equations
     and the substitution lines, and the note's own `X<sub>y</sub>` from
     the running text, tables, captions and notes.
  3. Compares that against the symbol table at the back.

Two failures are reported and they are different:

  MISSING   the symbol is used but the table does not list it
  UNDEFINED the symbol appears in an equation before any prose in the
            document has written it - the `a_s` failure exactly

A third listing, UNUSED, catches the table drifting the other way.

    python an_symbols.py            the three reports
    python an_symbols.py --all      plus every symbol with its first use
"""
import re
import sys


# TeX control words that are not symbols.  Everything else beginning with
# a backslash is treated as a name, so a new Greek letter cannot slip in.
NOTSYM = set("""
frac dfrac sqrt left right cdot times quad qquad , ; ! : > < mathrm mathbf
text sum int max min lceil rceil lfloor rfloor langle rangle infty pi
Longrightarrow Rightarrow rightarrow leftarrow to approx simeq neq geq leq
ge le log ln sin cos tan arg deg bigl bigr Bigl Bigr lvert rvert vert
ldots cdots dots pm mp cup cap partial nabla equiv propto sim ast star
begin end hline over atop choice space thinspace hspace vspace
arctan arcsin arccos circ lim leftarrow Leftarrow
""".split())

#  Names that are words, not symbols: they appear in TeX as \mathrm{...}
#  or as bare letters inside one, and listing them as undefined symbols is
#  noise.  Kept explicit so the list can be argued with.
#  A unit or a word only counts as noise when it stands ALONE.  Filtering
#  on the base letter instead threw away V_out, A_e and every other real
#  symbol whose initial happens to be a unit.
WORDS = set("""
mm cm m kHz Hz W V A F H s ns us ms uH nF pF uF mF kohm ohm mohm T
per unit across the assembly started at ripple decides rounded down
strands parallel device in out max min pk rms dt
\Omega \mu
""".split())

#  Dummies of general calculus and algebra.  They are not design symbols
#  and a symbol table that lists them is harder to use, not easier.
DUMMY = {'t', 'v', 'i', 's', 'w', 'x', 'u', 'q', 'z', 'j',
         '\\omega', '\\pi', '\\varphi_1'}


def _canon(base, sub):
    """one name for the same symbol, however it was written"""
    sub = re.sub(r'\\mathrm\{([^{}]*)\}', r'\1', sub or '')
    sub = re.sub(r'[\\{}$\s]', '', sub)
    sub = sub.replace('&minus;', '-')
    base = base.strip()
    return base + ('_' + sub if sub else '')


# --------------------------------------------------------------- TeX
#  A run of letters is ONE name: CTR, GM, THD, PF, EA.  Taking them a
#  letter at a time invented symbols C, T, R, G and M that the note
#  never uses, and those drowned the real finds.
_TEX_TOK = re.compile(r'(\\[A-Za-z]+|[A-Za-z]+)\s*(_\{[^{}]*\}|_[A-Za-z0-9])?')


def tex_symbols(tex):
    """the symbol names in one TeX string"""
    out = set()
    #  \mathrm{...} is a word, never a symbol - drop those spans whole
    body = re.sub(r'\\math(rm|bf|it|sf)\s*\{[^{}]*\}', ' ', tex)
    for m in _TEX_TOK.finditer(body):
        base, sub = m.group(1), m.group(2) or ''
        if base.startswith('\\'):
            if base[1:] in NOTSYM:
                continue
            name = base
        else:
            name = base
        sub = sub[1:] if sub else ''
        out.add(_canon(name, sub))
    return out


# -------------------------------------------------------------- prose
_HTML_TOK = re.compile(r'(&[A-Za-z]+;|[A-Za-z]+)<sub>(.*?)</sub>')
_GREEK = re.compile(r'&(lambda|theta|delta|eta|mu|rho|pi|alpha|beta|gamma|'
                    r'Gamma|Phi|Delta|Omega|omega|tau|phi|sigma|epsilon);')
#  Single letters and short words used as symbols in the prose.  Scanning
#  every capital in English prose reports the first word of every
#  sentence, so the list is explicit - and it is SEEDED FROM THE TABLE, so
#  a bare symbol the table lists is one the prose is then searched for.
#  Otherwise the check says a symbol is never written when the sentence
#  under its own equation writes it.
BARE = {'CTR', 'GM', 'THD', 'ESR', 'PF', 'Q', 'J', 'M', 'd', 'k', 'm', 'n'}
_BARE = [re.compile(r'(?<![A-Za-z])(CTR|GM|THD|ESR|Q|J|M|d|k|m|n)(?![A-Za-z<])')]


def set_bare(names):
    names = sorted({n for n in names if re.fullmatch(r'[A-Za-z]{1,4}', n)},
                   key=len, reverse=True)
    _BARE[0] = re.compile(r'(?<![A-Za-z])(%s)(?![A-Za-z<])'
                          % '|'.join(names)) if names else _BARE[0]


def _strip(t):
    return re.sub(r'<[^>]+>', '', t)


def prose_symbols(text):
    out = set()
    for m in _HTML_TOK.finditer(text):
        out.add(_canon(_strip(m.group(1)), _strip(m.group(2))))
    for m in _GREEK.finditer(text):
        out.add('\\' + m.group(1))
    for m in _BARE[0].finditer(_strip(text)):
        out.add(m.group(1))
    return out


#  the two alphabets write the same symbol differently
ALIAS = {'\\lambda': '\\lambda', '\\theta': '\\theta', '\\delta': '\\delta',
         '\\mu': '\\mu', '\\eta': '\\eta', '\\rho': '\\rho',
         '\\Phi': '\\Phi', '\\Gamma': '\\Gamma', '\\alpha': '\\alpha',
         '\\Delta': '\\Delta', '\\infty': '\\infty'}


def norm(k):
    """fold the spellings that mean one symbol"""
    k = k.replace('\\,', '').replace('\\', '\\')
    b, _, s = k.partition('_')
    if b.startswith('&') and b.endswith(';'):
        b = '\\' + b[1:-1]
    b = ALIAS.get(b, b)
    #  The same subscript reaches here in three alphabets: TeX (\\mu, with
    #  the backslash already stripped), an HTML entity (&mu;) and a plain
    #  word.  Fold them, or L_mu and L_&mu; look like two symbols and the
    #  table appears to be missing one that is in it.
    for ent, word in (('&mu;', 'mu'), ('&infin;', 'infty'),
                      ('&lambda;', 'lambda'), ('&theta;', 'theta'),
                      ('&delta;', 'delta'), ('&Phi;', 'phi'),
                      ('&Delta;', 'delta'), ('&alpha;', 'alpha'),
                      ('&Gamma;', 'gamma'), ('&eta;', 'eta')):
        s = s.replace(ent, word)
    s = s.replace('\\', '').replace(';', '').replace(' ', '')
    #  o and out, min and Min, and so on are the same subscript to a reader
    s = s.lower().replace('(', '').replace(')', '')
    return b + ('_' + s if s else '')


# ------------------------------------------------------------- replay
class Rec(object):
    """records what an_body asks the layout to print, in order"""

    def __init__(self):
        self.log = []          # (kind, index, payload)
        self.eqn = 0

    def _add(self, kind, payload):
        self.log.append((kind, len(self.log), payload))

    # -- the calls an_body makes
    def p(self, t):
        self._add('text', t)

    def note(self, t):
        self._add('text', t)

    def h1(self, t):
        self._add('head', t)

    def h2(self, t):
        self._add('head', t)

    def bullets(self, items):
        for it in items:
            self._add('text', it)
        return []

    def fig(self, name, caption, **kw):
        self._add('text', caption)

    def tbl(self, caption, rows, **kw):
        self._add('text', caption)
        for r in rows:
            for c in r:
                self._add('table', str(c))
        return []

    def eq(self, tex, size=None, number=True, key=None, again=False):
        lines = list(tex) if isinstance(tex, (list, tuple)) else [tex]
        if not number:
            self._add('calc', '  '.join(lines))
            return None
        if again:
            n = self.keys.get(key)
        else:
            self.eqn += 1
            n = self.eqn
            if key:
                self.keys[key] = n
                self.tex[key] = lines
        self._add('eq%d' % (n or 0), '  '.join(lines))
        return None

    def eqagain(self, key):
        return self.eq(self.tex[key], key=key, again=True)

    def calc(self, tex):
        return self.eq(tex, number=False)


def replay():
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
    return r, A


# -------------------------------------------------------------- table
def table_symbols(A):
    """what the symbol table at the back actually lists"""
    import an_body
    src = open(an_body.__file__, encoding='utf-8').read()
    blk = src[src.index('    _SYM = ['):src.index('    s.extend(tbl(')]
    out = set()
    for m in re.finditer(r"\(\s*('(?:[^'\\]|\\.)*')\s*,", blk):
        col = eval(m.group(1))
        if col.startswith('<b>'):        # a group heading, not a symbol
            continue
        out |= prose_symbols(col)
        #  and the bare names in the same cell - 'E, C, V, V<sub>min</sub>'
        #  lists three symbols that carry no subscript at all, and taking
        #  only the subscripted one left them looking unlisted
        for c in _strip(col).split(','):
            c = c.strip().split('(')[0].strip()
            if c and re.fullmatch(r'[A-Za-z&;]{1,4}', c):
                out.add(c.replace('&ndash;', ''))
    return out


def main():
    r, A = replay()
    raw = table_symbols(A)
    set_bare(BARE | {k for k in raw if '_' not in k})
    table = {norm(k) for k in raw}

    first_eq, first_text, where = {}, {}, {}
    for kind, i, payload in r.log:
        if kind.startswith('eq') or kind == 'calc':
            syms = tex_symbols(payload)
            for k in syms:
                k = norm(k)
                if k not in first_eq:
                    first_eq[k] = (i, kind)
        else:
            for k in prose_symbols(payload):
                k = norm(k)
                first_text.setdefault(k, i)
        for k in (tex_symbols(payload) if kind.startswith('eq')
                  or kind == 'calc' else prose_symbols(payload)):
            where.setdefault(norm(k), payload[:90])

    used = set(first_eq) | set(first_text)
    used = {k for k in used
            if k and k not in WORDS and k not in DUMMY
            and not re.fullmatch(r'\d+', k)}

    missing = sorted(k for k in used if k not in table)
    #  Two different faults.  A symbol the prose never writes at all is the
    #  `a_s` case: the reader meets it inside an equation and has nowhere
    #  to look.  A symbol the prose writes only AFTER the equation is a
    #  weaker complaint - the sentence under the equation usually does the
    #  job - so it is listed separately rather than mixed in.
    silent = sorted(k for k in used if k in first_eq and k not in first_text)
    late = sorted(k for k in used
                  if k in first_eq and k in first_text
                  and first_text[k] > first_eq[k][0])
    unused = sorted(k for k in table if k not in used)

    def show(title, keys, note=''):
        print('\n%s  (%d)%s' % (title, len(keys), note))
        for k in keys:
            e = first_eq.get(k)
            t = first_text.get(k)
            print('  %-16s %-14s %-14s %s'
                  % (k,
                     'eq %s' % e[1][2:] if e and e[1].startswith('eq')
                     else ('calc' if e else '-'),
                     'text @%d' % t if t is not None else 'NEVER in text',
                     where.get(k, '')[:60]))

    show('MISSING from the symbol table', missing)
    show('SILENT: used in an equation, never written in the prose at all',
         silent)
    show('LATE: the prose writes it only after the equation', late)
    print('\nIN THE TABLE BUT NEVER USED  (%d)' % len(unused))
    for k in unused:
        print('  %s' % k)
    print('\n%d symbols used - %d missing from the table, %d never written '
          'in the prose, %d written only afterwards'
          % (len(used), len(missing), len(silent), len(late)))
    if '--all' in sys.argv:
        print('\nEVERY SYMBOL')
        for k in sorted(used):
            print('  %-18s %s' % (k, 'listed' if k in table else '** not listed'))


if __name__ == '__main__':
    main()
