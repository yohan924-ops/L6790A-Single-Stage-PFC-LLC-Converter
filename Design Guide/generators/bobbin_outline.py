"""The B65982E coil former outline, read from the vector drawing of its data sheet.

    python bobbin_outline.py            # writes data/B65982E_outline.json
    python bobbin_outline.py --check    # the numbers the drawing must give back

Source: data/TDK_B65982E_coil_former.pdf, page 287 of the TDK ferrite
databook 04/13 (drawing FPK0433-H), saved as one page.  The drawing is
vector and at 1:2, so every line is read, not traced by eye.

WHICH VIEW IS WHICH.  The page carries no view names.  The front view is in
the middle (pins pointing down).  Above it is the view that shows the pin
ends as circles and carries the numbers 1, 6, 7, 12 and the pin-1 marking;
below it is a view with the same outline but no pins.  Seen from the
winding side the pins are hidden inside the pin blocks (section A-A shows
them entering the base from below), so the view WITH pins is the view from
the pin side - the BOTTOM view - and the one without is the TOP view.  That
is first-angle projection, the European drawing convention: the view from
below is placed above the front view.  Both views have the chamfered
(pin-1) corner on the left, as the two views of first-angle projection
must.

What is kept: the outline (0.57 pt lines), the hidden edges (short-dashed
0.29 pt), the pins (0.38 pt).  What is dropped: dimension lines, arrows,
lettering (all filled or thin), the centre lines (long dash-dot).

Coordinates in the json are millimetres, x to the right and y up as the
views stand on the page, origin on the centre lines of each view (the front
view: x on its centre line, y = 0 at the seating plane - the underside of
the stand-offs, 1 mm below the pin blocks, where the 7.6 mm pin length is
measured from).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, 'data', 'TDK_B65982E_coil_former.pdf')
OUT = os.path.join(HERE, 'data', 'B65982E_outline.json')

MM = 72.0 / 25.4 / 2.0          # pt per mm on the page: 1:2
#  the views on the page, in pt: (x0, y0, x1, y1) and the origin
VIEWS = {
    'bottom': ((95.0, 240.0, 176.0, 320.0), (135.7, 279.8)),
    'front': ((95.0, 330.0, 176.0, 426.0), (135.7, 412.0)),
    'top': ((95.0, 450.0, 176.0, 530.0), (135.7, 491.2)),
}


def _bez(p0, p1, p2, p3, n=10):
    out = []
    for i in range(1, n + 1):
        t = i / float(n)
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0.x + b * p1.x + c * p2.x + d * p3.x,
                    a * p0.y + b * p1.y + c * p2.y + d * p3.y))
    return out


def _polylines(path):
    """one drawing path -> list of polylines (a new one wherever it jumps)"""
    lines, cur, last = [], [], None
    for it in path['items']:
        if it[0] == 're':
            r = it[1]
            lines.append([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1),
                          (r.x0, r.y1), (r.x0, r.y0)])
            continue
        p0 = it[1]
        if last is None or abs(p0.x - last[0]) > 0.05 or abs(p0.y - last[1]) > 0.05:
            if len(cur) > 1:
                lines.append(cur)
            cur = [(p0.x, p0.y)]
        if it[0] == 'l':
            cur.append((it[2].x, it[2].y))
        elif it[0] == 'c':
            cur.extend(_bez(it[1], it[2], it[3], it[4]))
        last = cur[-1]
    if len(cur) > 1:
        lines.append(cur)
    return lines


def _kind(path):
    w = round(path.get('width') or 0.0, 3)
    dash = (path.get('dashes') or '').strip()
    if path.get('fill') is not None and not w:
        return None                               # lettering, arrow heads
    if w == 0.571:
        return 'outline'
    if w == 0.381:
        return 'pin'
    if w == 0.286 and dash.startswith('[ 2.857'):
        return 'hidden'
    return None                                   # dimensions, centre lines


def extract():
    import pymupdf
    page = pymupdf.open(PDF)[0]
    out = {'source': 'TDK ferrite databook 04/13 p. 287, drawing FPK0433-H '
                     '(data/TDK_B65982E_coil_former.pdf), read by '
                     'bobbin_outline.py',
           'scale_pt_per_mm': MM,
           'views': {}}
    paths = page.get_drawings()
    for name, ((x0, y0, x1, y1), (ox, oy)) in VIEWS.items():
        v = {'outline': [], 'hidden': [], 'pin': []}
        for p in paths:
            k = _kind(p)
            r = p['rect']
            if k is None or r.x0 < x0 or r.x1 > x1 or r.y0 < y0 or r.y1 > y1:
                continue
            for pl in _polylines(p):
                v[k].append([(round((x - ox) / MM, 3), round((oy - y) / MM, 3))
                             for x, y in pl])
        out['views'][name] = v
    return out


def load():
    with open(OUT) as f:
        return json.load(f)


def _span(lines):
    xs = [x for pl in lines for x, _ in pl]
    ys = [y for pl in lines for _, y in pl]
    return min(xs), max(xs), min(ys), max(ys)


def check(d):
    """the dimensions printed on the drawing, read back from the lines"""
    b, t, f = d['views']['bottom'], d['views']['top'], d['views']['front']
    pins = [((min(x for x, _ in pl) + max(x for x, _ in pl)) / 2,
             (min(y for _, y in pl) + max(y for _, y in pl)) / 2)
            for pl in b['pin'] if len(pl) > 8]
    xs = sorted({round(x, 1) for x, _ in pins})
    ys = sorted({round(y, 1) for _, y in pins})
    bx = _span(b['outline'])
    tx = _span(t['outline'])
    fx = _span(f['outline'])
    rows = [('pins found', len(pins), 12),
            ('pin rows apart', xs[-1] - xs[0], 45.72),
            ('pin pitch in a group', ys[1] - ys[0], 7.62),
            ('gap between the groups', ys[3] - ys[2], 12.70),
            ('bottom view, outline height', bx[3] - bx[2], 51.0),
            ('top view, width', tx[1] - tx[0], 51.6),
            ('front view, height above the seating plane', fx[3], 52.5)]
    bad = 0
    for what, got, want in rows:
        ok = abs(got - want) <= max(0.3, 0.01 * want)
        bad += not ok
        print('  %-44s %8.2f   drawing %6.2f   %s'
              % (what, got, want, 'ok' if ok else 'OFF'))
    return bad


if __name__ == '__main__':
    if '--check' in sys.argv:
        sys.exit(1 if check(load()) else 0)
    d = extract()
    with open(OUT, 'w') as f:
        json.dump(d, f, separators=(',', ':'))
    print('%s: %s' % (os.path.relpath(OUT, HERE),
                      ', '.join('%s %d/%d/%d' % (k, len(v['outline']),
                                                 len(v['hidden']), len(v['pin']))
                                for k, v in d['views'].items())))
    sys.exit(1 if check(d) else 0)
