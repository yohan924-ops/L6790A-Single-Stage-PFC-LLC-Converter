# -*- coding: utf-8 -*-
"""Replace whole statements of an_body.build() (or an_kr_body) by a key.

Written for the 2026-09-22 concision pass, when 373 of the 706 statements
in build() were rewritten.  Editing a 300 KB file by exact-match replacement
means retyping the long original of every paragraph, and one wrong character
silently matches nothing; this keys each edit on a short substring instead
and replaces the whole statement it lands in.

    from an_patch import apply
    apply([('first few words of the paragraph', "    add(p('new text'))"),
           ('a note to delete entirely', '')])

The key must occur in exactly one top-level statement of build(); an empty
replacement deletes the statement.  Edits are applied bottom-up so the line
numbers stay valid, the result is parsed before it is written, and if any
key matches zero or several statements nothing at all is written.
"""
import ast, io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)) + os.sep

def apply(edits, path=HERE + 'an_body.py'):
    src = io.open(path, encoding='utf-8').read()
    lines = src.split('\n')
    tree = ast.parse(src)
    build = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build')
    spans = [(s.lineno, s.end_lineno) for s in build.body]
    text = {sp: '\n'.join(lines[sp[0]-1:sp[1]]) for sp in spans}
    todo, bad = [], []
    for key, new in edits:
        hits = [sp for sp in spans if key in text[sp]]
        if len(hits) != 1:
            bad.append((key, len(hits))); continue
        todo.append((hits[0], new))
    if bad:
        for k, n in bad: print('KEY %s -> %d hits' % (k[:60], n))
        sys.exit('no edits applied')
    seen = set()
    for sp, _ in todo:
        assert sp not in seen, 'two edits hit statement at line %d' % sp[0]; seen.add(sp)
    todo.sort(reverse=True)
    before = len(src)
    for (a, b), new in todo:
        lines[a-1:b] = new.rstrip('\n').split('\n') if new.strip() else []
    out = '\n'.join(lines)
    io.open(path, 'w', encoding='utf-8').write(out)
    ast.parse(out)   # syntax check
    print('applied %d edits · %d -> %d chars' % (len(todo), before, len(out)))
