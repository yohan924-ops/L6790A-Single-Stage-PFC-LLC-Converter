# -*- coding: utf-8 -*-
"""zedpane.py  -  edit a serialised ZedGraph pane from the outside.

Everything here is read off the ZedGraph 5.1 source in
Reference/Smath Bode Plot Example/Zedgraph, not guessed.

Scale.GetObjectData writes, in this order:

    schema      int32       = 11
    min         double
    max         double
    majorStep   double
    minorStep   double
    exponent    double
    baseTic     double      double.MaxValue when unset
    minAuto        bool     one byte each, in this order
    maxAuto        bool
    majorStepAuto  bool
    minorStepAuto  bool
    magAuto        bool
    formatAuto     bool
    minGrace    double      0.1 by default
    maxGrace    double      0.1
    ...

so finding the (min, max) pair by value gives the offset of the whole
block, and the six auto flags sit 48 bytes after min.

LinearScale and LogScale both serialise as base.GetObjectData plus
schema2 = 10 - identical layouts, byte for byte. Only the type name in the
stream differs, and BinaryFormatter writes it length-prefixed, so
"\\x11ZedGraph.LogScale" -> "\\x14ZedGraph.LinearScale" is a complete and
safe conversion. Records are read sequentially and referenced by object id,
never by offset, so growing the stream by three bytes breaks nothing.

GraphPane.GetObjectData writes xAxis, x2Axis, yAxisList, y2AxisList,
curveList - so the first scale block in the stream belongs to x.
"""
import struct

LOG = b'\x11ZedGraph.LogScale'
LIN = b'\x14ZedGraph.LinearScale'


def _find_pair(raw, lo, hi):
    pat = struct.pack('<d', lo) + struct.pack('<d', hi)
    n = raw.count(pat)
    if n != 1:
        raise ValueError('the pair (%g, %g) appears %d times, need exactly one'
                         % (lo, hi, n))
    return raw.index(pat)


def set_range(raw, old, new):
    """rewrite one axis's (min, max)"""
    at = _find_pair(raw, *old)
    return (raw[:at] + struct.pack('<d', new[0]) + struct.pack('<d', new[1])
            + raw[at + 16:])


def set_auto(raw, old, on=True):
    """let ZedGraph choose that axis's range and both tick steps"""
    at = _find_pair(raw, *old)
    b = bytearray(raw)
    v = 1 if on else 0
    b[at + 48] = v          # minAuto
    b[at + 49] = v          # maxAuto
    b[at + 50] = v          # majorStepAuto
    b[at + 51] = v          # minorStepAuto
    return bytes(b)


def read_scale(raw, old):
    """what the stream currently says about that axis - for checking"""
    at = _find_pair(raw, *old)
    d = struct.unpack('<6d', raw[at:at + 48])
    f = raw[at + 48:at + 54]
    return dict(zip(('min', 'max', 'majorStep', 'minorStep', 'exponent',
                     'baseTic'), d),
                **dict(zip(('minAuto', 'maxAuto', 'majorStepAuto',
                            'minorStepAuto', 'magAuto', 'formatAuto'), f)))


def to_linear(raw):
    """every logarithmic axis in the pane becomes linear"""
    if LOG not in raw:
        return raw, 0
    n = raw.count(LOG)
    return raw.replace(LOG, LIN), n


def set_text(raw, old, new):
    """rename a label, to text of ANY length

    BinaryFormatter writes a string as a 7-bit-encoded length followed by
    its UTF-8 bytes, so matching the length byte along with the text makes
    the match unambiguous - "Input Impedance" otherwise also matches inside
    "SMPS Input Impedance" - and lets the replacement be a different size.
    Records are read in order and referenced by object id, so the stream
    changing length is not a problem.

    One byte of prefix means text under 128 bytes; longer would need the
    continuation form and nothing here is close.
    """
    a, b = old.encode(), new.encode()
    if len(b) > 127:
        raise ValueError('%r is %d bytes; the one-byte prefix stops at 127'
                         % (new, len(b)))
    pa = bytes([len(a)]) + a
    if raw.count(pa) != 1:
        raise ValueError('label %r appears %d times with its length prefix'
                         % (old, raw.count(pa)))
    return raw.replace(pa, bytes([len(b)]) + b)

# ---------------------------------------------------------------- geometry
def set_size(raw, old, new):
    """Resize the pane. The REGION ATTRIBUTE MUST BE CHANGED WITH IT.

    PaneBase.GetObjectData writes rect first, a RectangleF of four floats,
    and that rect is what ZedGraph lays the chart, the legend and the
    titles out against. The region's width and height attributes are what
    SMath reserves on the page. Change one and not the other and the pane
    comes back as a DEFAULT one - axes named x and y running -5..5, no
    title, no legend - which is how this function got a "do not use" note
    on it for a while.

    Probe P27/P28/P29 settled it. Same pane three ways, printed and the
    frames measured:

        P27  nothing touched                 476 x 217 px
        P28  region attribute doubled only   476 x 217 px   no effect
        P29  region AND this rect doubled    464 x 518 px   correct, and
             the title, both axis names, the legend and every tick label
             came through

    So: call this and set the region to the same numbers. zedsheet.make
    does both from one `size` argument, which is the only way it should be
    reached.
    """
    a = struct.pack('<ffff', 0.0, 0.0, float(old[0]), float(old[1]))
    b = struct.pack('<ffff', 0.0, 0.0, float(new[0]), float(new[1]))
    if raw.count(a) != 1:
        raise ValueError('rect(0,0,%g,%g) appears %d times'
                         % (old[0], old[1], raw.count(a)))
    return raw.replace(a, b)


# ------------------------------------------------------------- trace width
LINEBASE = struct.pack('<i', 12)        # LineBase.schema0


def _offsets(raw, pat):
    out, i = [], raw.find(pat)
    while i >= 0:
        out.append(i)
        i = raw.find(pat, i + 1)
    return out


def set_line_width(raw, width, old=1.0):
    """Thicken every outline: the curves, and the frames around them.

    LineBase.GetObjectData writes schema0 = 12 then the width as a float,
    so each record is found by that pair. Two earlier attempts tried to
    pick out only the curves - by the widest run of records, then by
    splitting on the gaps between them - and both leaned on spacing that
    happens to hold in one pane and is not part of the format.

    Setting all of them is deterministic and does not touch the grid, which
    is a different class: MinorGrid keeps its own penWidth and MajorGrid
    derives from it. So the curves and the frames go to `width` and the
    gridlines stay where they were.
    """
    pat = LINEBASE + struct.pack('<f', float(old))
    n = raw.count(pat)
    if not n:
        # already at the wanted width is success, not failure - a harvested
        # pane comes back widened and gets asked a second time
        if raw.count(LINEBASE + struct.pack('<f', float(width))):
            return raw, 0
        raise ValueError('no LineBase carries width %g, and none carries %g '
                         'either' % (old, width))
    return raw.replace(pat, LINEBASE + struct.pack('<f', float(width))), n


def set_curve_widths(raw, label_offsets, widths):
    """One pen width per curve, instead of set_line_width's all-or-nothing.

    A LineItem writes its label, then its points, then the symbol and the
    line, so the pen lives between one label and the next - the same window
    curve_colors uses for the Color. The LAST LineBase in that window is the
    curve's own line; the earlier ones belong to the symbol, which is not
    drawn here. Read back afterwards, because a silent miss would show up
    only in print.
    """
    if len(widths) != len(label_offsets):
        raise ValueError('%d curves but %d widths'
                         % (len(label_offsets), len(widths)))
    b = bytearray(raw)
    for k, p in enumerate(label_offsets):
        stop = label_offsets[k + 1] if k + 1 < len(label_offsets) else len(raw)
        at, i = -1, raw.find(LINEBASE, p, stop)
        while i >= 0:
            at = i
            i = raw.find(LINEBASE, i + 1, stop)
        if at < 0:
            raise ValueError('curve %d has no LineBase before the next' % (k + 1))
        struct.pack_into('<f', b, at + len(LINEBASE), float(widths[k]))
    got = read_curve_widths(bytes(b), label_offsets)
    if [round(g, 3) for g in got] != [round(float(w), 3) for w in widths]:
        raise ValueError('widths did not take: wanted %s, read back %s'
                         % (list(widths), got))
    return bytes(b)


def read_curve_widths(raw, label_offsets):
    """the pen width of each curve, in order - the inverse of the above"""
    out = []
    for k, p in enumerate(label_offsets):
        stop = label_offsets[k + 1] if k + 1 < len(label_offsets) else len(raw)
        at, i = -1, raw.find(LINEBASE, p, stop)
        while i >= 0:
            at = i
            i = raw.find(LINEBASE, i + 1, stop)
        out.append(None if at < 0 else
                   round(struct.unpack_from('<f', raw, at + len(LINEBASE))[0], 3))
    return out


def set_legend_font_size(raw, size):
    """The legend is the 12 pt FontSpec of a freshly harvested pane.

    ZedGraph's defaults are title 16, axis 14, legend 12, so 12.0 is unique
    until the title is brought down to it. Call this BEFORE
    set_title_font_size, not after.
    """
    return set_title_font_size(raw, size, old=12.0)


def set_title_font_size(raw, size, old=16.0):
    """Shrink the pane title.

    FontSpec.GetObjectData writes, in order, ... angle, stringAlignment,
    size, isDropShadow, dropShadowColor, dropShadowAngle, dropShadowOffset.
    The three after `size` are what makes the record findable without
    walking BinaryFormatter: isDropShadow is one byte, and dropShadowColor
    is a Color written inline as ClassWithId - 0x01, two int32 ids, then
    ObjectNull for the name and eight zero bytes for the value. That run is
    the signature.

    A pane carries ten FontSpecs and ZedGraph's defaults separate them:
    title 16, axis titles and scale labels 14, legend 12. So 16 occurs
    exactly once and needs no further identification - and this checks it,
    because a pane where it does not is not the pane this assumes.
    """
    zero8 = bytes(8)
    hits = []
    for o in range(len(raw) - 30):
        if raw[o + 5] != 1 or raw[o + 4] not in (0, 1):
            continue
        if raw[o + 14] != 0x0a or raw[o + 15:o + 23] != zero8:
            continue
        v, = struct.unpack_from('<f', raw, o)
        if abs(v - old) < 1e-6:
            hits.append(o)
    if len(hits) != 1:
        raise ValueError('%d FontSpec records carry size %g, expected exactly '
                         'one (the title)' % (len(hits), old))
    b = bytearray(raw)
    struct.pack_into('<f', b, hits[0], float(size))
    return bytes(b)


# -------------------------------------------------------------------- grid
def set_minor_grid(raw, on):
    """MinorGrid: schema(int32) = 10, isVisible(bool), dashOn, dashOff,
    penWidth - so the flag is the byte straight after the schema.

    The TI panes leave it on, which puts a second, denser set of dashes
    behind the major grid. On a gain curve that reads as noise.
    """
    pat = struct.pack('<i', 10) + bytes([1 if not on else 0])
    n = 0
    b = bytearray(raw)
    for o in _offsets(raw, pat):
        # only where what follows looks like dashOn, dashOff, penWidth
        try:
            d1, d2, pw = struct.unpack('<3f', raw[o + 5:o + 17])
        except struct.error:
            continue
        if 0 < d1 <= 20 and 0 < d2 <= 20 and 0 < pw <= 5:
            b[o + 4] = 1 if on else 0
            n += 1
    return bytes(b), n

def set_steps(raw, rng, major, minor):
    """Fix the tick steps of one axis, and stop ZedGraph choosing them.

    Scale writes min, max, majorStep, minorStep as consecutive doubles, and
    majorStepAuto and minorStepAuto are the third and fourth of the six
    flag bytes 48 on from min. Both flags have to be cleared or the values
    written here are ignored.

    A log axis steps in decades and does not want this - leave those alone.
    """
    at = _find_pair(raw, *rng)
    b = bytearray(raw)
    b[at + 16:at + 24] = struct.pack('<d', float(major))
    b[at + 24:at + 32] = struct.pack('<d', float(minor))
    b[at + 50] = 0                      # majorStepAuto
    b[at + 51] = 0                      # minorStepAuto
    return bytes(b)


def nice_steps(lo, hi, want=8):
    """a round major step near range/want, with the minor at a fifth of it"""
    import math
    raw_step = (hi - lo) / float(want)
    mag = 10.0 ** math.floor(math.log10(raw_step))
    for k in (1.0, 2.0, 2.5, 5.0, 10.0):
        if k * mag >= raw_step:
            return k * mag, k * mag / 5.0
    return 10.0 * mag, 2.0 * mag

# ------------------------------------------------------------- tick labels
def set_format(raw, rng, fmt):
    """Rewrite one axis's number format, and stop ZedGraph picking its own.

    Scale writes textLabels then format straight after isSkipCrossLabel, so
    both sit at a fixed offset from the (min, max) anchor. format is a
    string, and BinaryFormatter writes a string once and refers to it by
    object id afterwards - so an axis may hold the record itself or a
    reference to the one the previous axis wrote. Patch the record, and
    every axis pointing at it follows.

    Returns (raw, old_format).
    """
    at = _find_pair(raw, *rng)
    p = at + 81
    if raw[p] != 0x0A:                  # textLabels, expected null
        raise ValueError('textLabels at +81 is 0x%02x, not a null record'
                         % raw[p])
    p += 1
    if raw[p] == 0x09:                  # MemberReference to an earlier string
        oid = struct.unpack_from('<i', raw, p + 1)[0]
        rec = raw.find(b'\x06' + struct.pack('<i', oid))
        if rec < 0:
            raise ValueError('format string object %d is not in the pane' % oid)
    elif raw[p] == 0x06:                # BinaryObjectString, written here
        rec = p
    else:
        raise ValueError('0x%02x where the format string should be' % raw[p])

    ln = raw[rec + 5]
    if ln > 127:
        raise ValueError('length-prefixed string spans two bytes')
    old = raw[rec + 6:rec + 6 + ln].decode('utf-8', 'replace')
    new = fmt.encode('utf-8')
    if len(new) > 127:
        raise ValueError('format string too long')
    raw = raw[:rec + 5] + bytes([len(new)]) + new + raw[rec + 6 + ln:]

    b = bytearray(raw)
    b[_find_pair(raw, *rng) + 53] = 0            # formatAuto
    return bytes(b), old

# --------------------------------------------------------------- axis type
# There is no per-axis log/linear switch, and there cannot be one. A pane
# holds six scale records but only two or three type NAMES: those belong to
# class records, and the remaining instances are ClassWithId, which name no
# type of their own. Renaming a class record converts every axis of that
# class at once - which is why to_linear works, and why one axis cannot be
# singled out. So the split comes from the pane you start with:
#
#   impedance panes (1..5 curves)   x, x2, y all LogScale
#   transfer  panes (1..4 curves)   x, x2 LogScale, y LinearScale
#
# log x with linear y therefore means a transfer pane, and those stop at
# four curves. Five curves means every axis linear, through to_linear.

def set_base_tic(raw, rng, value):
    """Where an axis starts counting its major ticks.

    Scale writes baseTic as the sixth double, right after exponent. Left at
    PointPair.Missing (double.MaxValue) it is automatic, and LogScale then
    computes ceil(log10(min)) - the next WHOLE decade at or above the
    minimum. With a major step of a whole decade that is what you want. With
    a fractional step it is not: an axis running 0.5 to 2.5 starts counting
    at 1, so everything below 1 gets no major tick and no label at all, and
    half the frame comes out blank.

    The value is in LOG units for a log axis, so pass log10(min) to make the
    ticks start at the left edge.
    """
    at = _find_pair(raw, *rng)
    b = bytearray(raw)
    b[at + 40:at + 48] = struct.pack('<d', float(value))
    return bytes(b)


# ------------------------------------------------------------------ colour
# System.Drawing.KnownColor, which is what a Color serialises as here: name
# is null, value is zero, and the whole colour is the knownColor short. Only
# the ones this project draws with are listed - a number that is not in the
# table is refused rather than written, because a wrong one is a colour that
# still draws and nobody would look twice at it.
# Read out of System.Drawing on this machine, not counted by hand off a
# list. Teal was written 160 here for a while, which is Tomato - the read-back
# in set_curve_colors uses this same table, so it agreed with itself and
# reported success while one curve drew salmon. The printed page is what
# caught it, and it is the only thing that could have.
#
#     [System.Drawing.Color]::FromKnownColor([System.Drawing.KnownColor]::Teal)
KNOWN = {
    'Black': 35,        # 000000
    'Blue': 37,         # 0000FF
    'Crimson': 47,      # DC143C
    'DarkOrange': 57,   # FF8C00
    'DarkViolet': 65,   # 9400D3
    'DimGray': 68,      # 696969
    'DodgerBlue': 69,   # 1E90FF
    'Fuchsia': 73,      # FF00FF
    'Gray': 78,         # 808080
    'Green': 79,        # 008000
    'Magenta': 107,     # FF00FF
    'Purple': 140,      # 800080
    'Red': 141,         # FF0000
    'SaddleBrown': 144, # 8B4513
    'Teal': 158,        # 008080
}
_KNOWN_R = dict((v, k) for k, v in KNOWN.items())

# name = null, value = 0 (Int64): a colour that is a KnownColor and nothing
# else. knownColor is the short that follows.
_COLOR_HEAD = b'\x0a' + b'\x00' * 8


def _color_at(raw, start, stop):
    """offset of the knownColor short of the first Color after `start`"""
    i = raw.find(_COLOR_HEAD, start, stop)
    return -1 if i < 0 else i + 9


def curve_colors(raw, label_offsets):
    """[(offsets, name_or_number)] - every Color of each curve, in order

    A LineItem writes its label, then its points, then the symbol and the
    line, and ZedGraph gives those two the same colour when it builds the
    curve. Each curve's span holds exactly ONE Color record - checked
    against panes/transfer8.b64, where curves 1 to 7 have one apiece and
    only the last span runs on into the axes and the legend. So the first
    Color after a label is that curve's colour, and the window is the next
    label, which keeps everything else out of reach.
    """
    out = []
    for k, p in enumerate(label_offsets):
        stop = label_offsets[k + 1] if k + 1 < len(label_offsets) else len(raw)
        at = _color_at(raw, p, stop)
        if at < 0:
            raise ValueError('curve %d has no Color record before the next '
                             'curve - this pane is not shaped as expected'
                             % (k + 1))
        kc = struct.unpack_from('<h', raw, at)[0]
        out.append((at, _KNOWN_R.get(kc, kc)))
    return out


def set_curve_colors(raw, label_offsets, names):
    """Give each curve its own colour, and prove it took.

    The panes in the catalogue cycle a six-colour palette, so a seventh and
    an eighth curve come back blue and red again - the same blue and red as
    the first two. That is not a palette running out; it is two different
    quantities drawn in one colour on one frame.
    """
    if len(names) != len(label_offsets):
        raise ValueError('%d curves but %d colours'
                         % (len(label_offsets), len(names)))
    bad = [n for n in names if n not in KNOWN]
    if bad:
        raise ValueError('not in the KnownColor table: %s' % ', '.join(bad))
    b = bytearray(raw)
    for (at, _old), nm in zip(curve_colors(raw, label_offsets), names):
        struct.pack_into('<h', b, at, KNOWN[nm])
    got = [n for _a, n in curve_colors(bytes(b), label_offsets)]
    if got != list(names):
        raise ValueError('colours did not take: wanted %s, read back %s'
                         % (names, got))
    return bytes(b)
