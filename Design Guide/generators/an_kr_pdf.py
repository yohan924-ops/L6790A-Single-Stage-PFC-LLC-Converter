# -*- coding: utf-8 -*-
"""한국어판 Application Note 를 만든다.

an_pdf.py 의 페이지 틀(표지·법적 고지·점선 목차·번호 붙은 수식·그림 캡션)을
그대로 쓰고 서체만 한국어로 바꾼다.  본문은 an_kr_body.py 에 있고 구조는
영문판 an_body.py 와 절 단위로 같다 — 한쪽을 고치면 다른 쪽도 같이 고친다.

값은 전부 an_pdf.V 보간이므로 시트가 바뀌면 이 문서도 따라온다.  손으로 적은
숫자가 하나도 없어야 한다.

    python an_kr_pdf.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import an_pdf as A                                                # noqa: E402
from reportlab.platypus import (NextPageTemplate, PageBreak,      # noqa: E402
                                Paragraph, Spacer, Table, TableStyle)

OUT = os.path.join(
    A.GUIDE, 'AN_L6790A_SingleStage_PF_LLC_ApplicationNote_KR_v1.0.pdf')


def legal():
    s = [Paragraph('이 문서에 대하여', A.S['h1'])]
    for t in (
        '이 Application Note 는 사내 설계 과제를 위해 작성한 것이다. '
        'STMicroelectronics 나 다른 반도체 회사의 간행물이 <b>아니며</b> '
        '그들의 보증을 받지 않았다. L6790A 의 동작을 설명한 부분은 '
        '2026년 4월 30일자 <b>DRAFT</b> 데이터시트를 근거로 한 것이고, '
        '그 문서에는 TBD 항목과 내부 모순이 남아 있다. 여기서 가져온 '
        '컨트롤러 상수는 양산 확정 전에 정식 데이터시트로 전부 다시 '
        '확인해야 한다.',
        '본문의 설계 예제는 실제 설계이고 앞뒤가 맞지만 <b>아직 만들어 보지 '
        '않았다.</b> 실측값은 실측이라고 밝혀 적었고 나머지는 전부 계산값이다. '
        '예산을 지키지 못한 채로 결정한 항목은 예산을 슬쩍 고치지 않고 '
        '그대로 적었다.',
        '이 설계의 수치를 담은 그림은 설계값을 만드는 것과 같은 참조 구현에서 '
        '생성되므로, 그림과 본문이 어긋날 수 없다. 일반 LLC 이론 그림 몇 장은 '
        '참고문헌의 Application Note 에서 가져온 것이고 출처를 캡션에 적었다. '
        '그 그림들의 권리는 각 저자에게 있다.',
    ):
        s.append(Paragraph(A.T(t), A.S['p']))
        s.append(Spacer(1, 3))

    s.append(Spacer(1, 12))
    s.append(Paragraph('개정 이력', A.S['h2']))
    s.append(Table(
        [[Paragraph(c, A.S['th']) for c in ('버전', '날짜', '내용')],
         [Paragraph('V1.0', A.S['tc']), Paragraph('2026년 9월', A.S['tc']),
          Paragraph(A.T('영문판 V1.1 을 바탕으로 한 한국어 초판. 설계 예제 '
                        '%.0f V / %.1f A, %.1f W, 권선비 %d : %d.'
                        % (A.V['Vout'], A.V['Iout'], A.V['Pout'],
                           A.V['NpSet'], A.V['Ns'])), A.S['tc'])]],
        colWidths=[70, 90, A.CW - 160],
        style=TableStyle([('BACKGROUND', (0, 0), (-1, 0), A.NAVY),
                          ('LINEBELOW', (0, 0), (-1, -1), 0.4, A.LT),
                          ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                          ('TOPPADDING', (0, 0), (-1, -1), 4),
                          ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                          ('LEFTPADDING', (0, 0), (-1, -1), 5)])))

    s.append(Spacer(1, 16))
    s.append(Paragraph('표기', A.S['h2']))
    s.extend(A.bullets([
        '<b>줄임말은 영어 그대로 쓴다</b> — ZVS, ZCS, PFC, THD, FHA, SR, '
        'OCP, OVP, VCO, BM. 억지로 우리말로 옮기면 오히려 읽기 어렵다.',
        '<b>n</b> — 등가모델 권선비. 게인 식에 들어가는 값이며 감는 턴수의 '
        '비가 아니다.',
        '<b>n<sub>T</sub></b> — 실제로 감는 턴수의 비. '
        'n<sub>T</sub> = n&radic;(1+&lambda;).',
        '<b>&lambda;</b> = L<sub>r</sub>/L<sub>m</sub> — 누설 대 자화. '
        '탱크가 낼 수 있는 게인 범위를 정한다.',
        '<b>f<sub>n</sub></b> = f<sub>sw</sub>/f<sub>r</sub> — 정규화 주파수.',
        '<b>M</b> — 탱크 전압 게인, <b>Q</b> = Z<sub>0</sub>/R<sub>ac</sub> '
        '— 부하가 탱크를 얼마나 무겁게 하는가.',
        '<b>등가 입력</b> — topology morphing 이후 공진 탱크가 실제로 보는 '
        '전압. 상용전원 전압이 아니다.',
        '<b>&theta;</b> — 라인 위상. 0 과 &pi; 가 영교차, &pi;/2 가 라인 '
        '피크다.',
    ]))
    return s


def main():
    A.use_korean()
    A.TITLE = '단일단 PF LLC 컨버터 설계'
    A.HEADSIZE = 12.5
    A.FIGWORD, A.TBLWORD = '그림', '표'
    A.DOCID = ['Application Note AN-SS-L6790A-01 KR', 'V1.0  2026년 9월']
    A.COVER = {
        'title': ['단일단 PF LLC', '컨버터 설계'],
        'sub': 'STMicroelectronics L6790A',
        'boxhead': '이 문서가 끝까지 따라가는 설계',
        'box': ['90 ~ 264 Vac 유니버설 입력,  47 ~ 63 Hz',
                '%.0f V / %.1f A = %.1f W 설계 예제'
                % (A.V['Vout'], A.V['Iout'], A.V['Pout']),
                '벌크 커패시터도 승압단도 없다',
                '모든 설계값이 참조 구현까지 추적된다'],
        'foot': ['사내 기술문서. ST 의 간행물이 아니다.',
                 '근거로 삼은 L6790A 데이터시트는 DRAFT (2026-04-30) 다.'],
    }
    import an_kr_body
    A._pass1()
    an_kr_body.build(A)
    A._pass2()
    s = [NextPageTemplate('body'), PageBreak()]
    s += legal()
    s.append(PageBreak())
    s += A.toc('목차')
    s.append(PageBreak())
    s += an_kr_body.build(A)
    A.build(s, OUT, toc_title='목차')


if __name__ == '__main__':
    main()
