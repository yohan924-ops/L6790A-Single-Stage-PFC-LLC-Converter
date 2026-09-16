# -*- coding: utf-8 -*-
"""트랜스포머 설계 정리 PDF 를 만든다.

an_pdf.py 의 페이지 틀(표지·머리글·번호 붙은 수식·표 스타일)을 그대로 쓰고
폰트만 한국어로 바꾼다. 본문은 tx_body.py 에 있고, 값은 전부 an_pdf.V 에서
보간되므로 시트가 바뀌면 이 문서도 따라온다.

    python tx_pdf.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import an_pdf as A                                               # noqa: E402
from reportlab.platypus import (NextPageTemplate, PageBreak,     # noqa: E402
                                Paragraph, Spacer, Table, TableStyle)

OUT = os.path.join(A.GUIDE, 'L6790A_Transformer_Design_KR_v1.0.pdf')


def front():
    s = [Paragraph('이 문서에 대하여', A.S['h1'])]
    for t in (
        '본 문서는 L6790A 단일단 PF LLC TV SMPS 의 트랜스포머 사양이 어떻게 '
        '나왔는지를 처음부터 끝까지 따라간다. 답하려는 질문은 하나다 — '
        '<b>“왜 1차 5턴에 2차 2턴인가.”</b>',
        '설계 가이드는 식 [1]–[148] 을 다루고 Application Note 는 배포용 '
        '요약이며, 이 문서는 그 둘 사이에서 <b>하나의 사슬</b>만 끝까지 '
        '설명한다. 벤더에게 넘길 사양서의 근거 문서로도 쓸 수 있다.',
        '모든 수치는 SMath 정본 시트와 <i>l6790.py</i> 에서 자동으로 가져온다. '
        '이 문서에 손으로 적은 숫자는 없다.',
    ):
        s.append(Paragraph(A.T(t), A.S['p']))
        s.append(Spacer(1, 3))

    s.append(Spacer(1, 14))
    s.append(Paragraph('개정 이력', A.S['h2']))
    s.append(Table(
        [[Paragraph(A.T(c), A.S['th']) for c in ('버전', '날짜', '내용')],
         [Paragraph('V1.0', A.S['tc']), Paragraph('2026년 9월', A.S['tc']),
          Paragraph(A.T('최초 작성. 3분할 · 1차 %d T : 2차 %d T · 개방 %.2f µH '
                        '· 단락 %.2f µH.' % (5, 2, 31.0/3, 11.0/3)),
                    A.S['tc'])]],
        colWidths=[60, 90, A.CW - 150],
        style=TableStyle([('BACKGROUND', (0, 0), (-1, 0), A.NAVY),
                          ('LINEBELOW', (0, 0), (-1, -1), 0.4, A.LT),
                          ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                          ('TOPPADDING', (0, 0), (-1, -1), 4),
                          ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                          ('LEFTPADDING', (0, 0), (-1, -1), 5)])))

    s.append(Spacer(1, 18))
    s.append(Paragraph('기호', A.S['h2']))
    s.extend(A.bullets([
        '<b>n</b> — 등가모델 권선비. 게인 식에 들어가는 값이며 '
        '<b>감는 턴수의 비가 아니다.</b>',
        '<b>n<sub>T</sub></b> — 실제로 감는 턴수의 비. '
        'n<sub>T</sub> = n·√(1+λ).',
        '<b>λ</b> = L<sub>r</sub>/L<sub>m</sub> — 누설 대 자화. '
        '탱크의 게인 범위를 정한다.',
        '<b>k</b> — 결합계수. k = 1/√(1+λ). 자속 중 2차에 닿는 비율.',
        '<b>등가 입력</b> — 토폴로지 모핑 이후 공진 탱크가 실제로 보는 전압. '
        '상용전원 전압이 아니다.',
    ]))
    return s


def main():
    A.use_korean()
    A.TITLE = '단일단 PF LLC — 트랜스포머 설계'
    A.HEADSIZE = 12.0
    A.FIGWORD, A.TBLWORD = '그림', '표'
    A.DOCID = ['트랜스포머 설계 정리', 'V1.0  2026년 9월']
    A.COVER = {
        'title': ['단일단 PF LLC', '트랜스포머 설계'],
        'sub': '왜 1차 5턴에 2차 2턴인가',
        'boxhead': '이 문서가 다루는 것',
        'box': ['입력 범위에서 λ 가 나오는 과정',
                'λ 와 결합도 k 의 관계, 그리고 왜 턴비가 n 과 다른가',
                '벤더에게 넘길 사양 — 트랜스포머 1개 기준',
                '남은 문제 — 누설과 1차 구리가 같은 창을 다툰다'],
        'foot': ['사내 기술문서. ST 의 간행물이 아니다.',
                 '모든 수치는 SMath 정본 시트에서 자동 생성된다.'],
    }
    import tx_body
    s = [NextPageTemplate('body'), PageBreak()]
    s += front()
    s.append(PageBreak())
    s.append(Paragraph('목차', A.S['h1']))
    s.append(Spacer(1, 8))
    t = __import__('reportlab.platypus.tableofcontents', fromlist=['x'])
    toc = t.TableOfContents()
    toc.levelStyles = [A.S['toc0'], A.S['toc1']]
    toc.dotsMinLevel = 0
    s.append(toc)
    s.append(PageBreak())
    s += tx_body.build(A)
    A.build(s, OUT)


if __name__ == '__main__':
    main()
