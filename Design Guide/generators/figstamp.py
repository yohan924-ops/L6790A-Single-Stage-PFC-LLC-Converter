# -*- coding: utf-8 -*-
"""Is every drawn figure of the note still drawn from the current design?

Written because two rounds shipped stale figures and nothing noticed
(2026-09-25, round 65): round 64 moved n.aux, R.ZCD_H and the saturation test
current in the sheet but redrew only the one figure it was editing, so the
note printed "NAUX 3 T" in the pin figure and 15.19 A in the ampere-turn
figure next to text that said 2 T and 15.6 A.  Round 63 had changed "2 x" to
"2 ×" in f13_morphing's source and never redrawn it.

figs.save() writes two stamps into every PNG it draws:

    l6790-data   hash of the design values the figures draw from - an_pdf.V,
                 an_pdf.SH (the sheet) and the winding cores.winding() lays
                 out on the chosen core
    l6790-code   module:function that drew it, and the hash of its source

This script recomputes both WITHOUT drawing anything and lists every figure
whose stamp no longer matches.  A figure without stamps is one drawn before
this existed, or a reference crop that figs.save() did not write - listed
separately, not failed.

    python figstamp.py            report; exit 1 if any figure is stale
"""
import hashlib
import importlib
import inspect
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AN_DIR = os.path.normpath(os.path.join(HERE, '..', 'figures', 'an'))


def _norm(v):
    if isinstance(v, float):
        return float('%.10g' % v)
    if isinstance(v, (list, tuple)):
        return [_norm(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _norm(x) for k, x in v.items()}
    if isinstance(v, (int, str, bool)) or v is None:
        return v
    return repr(type(v))            # functions, arrays: not design values


_DATA = None


def data_hash():
    global _DATA
    if _DATA is None:
        import an_pdf
        import cores
        w = cores.winding(an_pdf.V)
        w = {k: v for k, v in w.items() if k != 'M'}
        blob = json.dumps([_norm(dict(an_pdf.V)), _norm(dict(an_pdf.SH)),
                           _norm(w)], sort_keys=True)
        _DATA = hashlib.md5(blob.encode('utf-8')).hexdigest()[:16]
    return _DATA


def code_stamp(code):
    """'module:function:hash' for the code object that called figs.save()"""
    mod = inspect.getmodule(code)
    src = inspect.getsource(code)
    return '%s:%s:%s' % (mod.__name__ if mod else '?', code.co_name,
                         hashlib.md5(src.encode('utf-8')).hexdigest()[:16])


def read(path):
    from PIL import Image
    info = Image.open(path).info
    return info.get('l6790-data'), info.get('l6790-code')


def main():
    stale, unstamped, ok = [], [], 0
    for fn in sorted(os.listdir(AN_DIR)):
        if not fn.endswith('.png'):
            continue
        d, c = read(os.path.join(AN_DIR, fn))
        if not d or not c:
            unstamped.append(fn)
            continue
        why = []
        if d != data_hash():
            why.append('design values changed')
        mod, func, h = c.split(':')
        try:
            f = getattr(importlib.import_module(mod), func)
            now = code_stamp(f.__code__)
            if now.split(':')[2] != h:
                why.append('drawing code %s.%s changed' % (mod, func))
        except (ImportError, AttributeError) as e:
            why.append('drawing function not found (%s)' % e)
        if why:
            stale.append((fn, why))
        else:
            ok += 1
    for fn, why in stale:
        print('STALE  %-30s %s' % (fn, '; '.join(why)))
    print('%d current · %d stale · %d without a stamp (drawn before '
          'figstamp, or not drawn by figs.save)' % (ok, len(stale),
                                                    len(unstamped)))
    if stale:
        print('redraw them:  python figs.py --plain   (every figure; the '
              'FIGS keys are not the file names)')
    return 1 if stale else 0


if __name__ == '__main__':
    sys.exit(main())
