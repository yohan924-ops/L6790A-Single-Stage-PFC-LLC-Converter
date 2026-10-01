# -*- coding: utf-8 -*-
"""The number a SMath <result> block actually carries.

Every tool here used to read `list(res)[0].text` - the first token - and that
is wrong, because a <result> is RPN like everything else in a .sm file. Four
tools made the same assumption independently, so nothing caught it.

Two things get lost:

    <e>22.26</e><e args="1">-</e>                     -> -22.26, read as 22.26
    <e>3.87</e><e>10</e><e>15</e><e args="1">-</e>
        <e args="2">^</e><e args="2">*</e><e args="1">-</e>
                                                      -> -3.87e-15, read as 3.87

The second one is what surfaced: C.cer_min is MAX(C.cer_raw, 0) with
C.cer_raw = -64.14 uF, so the sheet correctly clamps it to zero - as
-3.87e-15 uF, machine noise around zero. Read as "3.87 uF" it looked like the
design needed 3.87 uF of ceramic, and it disagreed with the workbook, which
had the same guard and honestly returned 0.

Of 525 results in the sheet, 53 are more than one token: 16 carry a sign that
was being dropped, 36 carry a unit that is harmless, and one carried an
exponent.

Unit operands are decoration in a result - the number is already in the
region's display units - so they evaluate as 1.
"""


def value(res):
    """-> float, or None if the block is not a plain arithmetic result"""
    st = []
    for e in list(res):
        kind = e.get('type')
        if kind == 'operand':
            if e.get('style') == 'unit':
                st.append(1.0)                 # already in display units
                continue
            try:
                st.append(float(e.text))
            except (TypeError, ValueError):
                return None
        elif kind == 'operator':
            op, n = e.text, int(e.get('args', 2) or 2)
            if n == 1:
                if not st:
                    return None
                a = st.pop()
                if op == '-':
                    st.append(-a)
                elif op == '+':
                    st.append(a)
                else:
                    return None
            elif n == 2:
                if len(st) < 2:
                    return None
                b, a = st.pop(), st.pop()
                if op == '+':
                    st.append(a + b)
                elif op == '-':
                    st.append(a - b)
                elif op == '*':
                    st.append(a * b)
                elif op == '/':
                    if b == 0:
                        return None
                    st.append(a / b)
                elif op == '^':
                    try:
                        st.append(a ** b)
                    except (OverflowError, ValueError, ZeroDivisionError):
                        return None
                else:
                    return None
            else:
                return None
        else:
            return None
    if not st:
        return None
    # SMath sometimes writes the unit first and leaves the multiply implicit -
    # <e style="unit">nF</e><e>92.21</e> - so more than one item can be left.
    # Unit operands are 1.0, so the product of the remainder is the number.
    out = 1.0
    for x in st:
        out *= x
    return out
