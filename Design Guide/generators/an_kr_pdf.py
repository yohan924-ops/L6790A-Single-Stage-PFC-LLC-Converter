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
    A.GUIDE, 'AN_L6790A_SingleStage_PFC_LLC_ApplicationNote_KR_v1.3.pdf')


def legal():
    s = [Paragraph('읽기 전에', A.S['h1'])]
    for t in (
        'L6790A 의 동작은 2026년 4월 30일자 <b>DRAFT</b> 데이터시트를 근거로 '
        '적었다. 그 초안에는 TBD 항목이 있고, 스스로 앞뒤가 안 맞는 대목도 '
        '하나 있다. 여기서 가져온 컨트롤러 상수는 양산에 들어가기 전에 정식 '
        '데이터시트로 다시 확인할 것.',
        '본문의 설계 예제는 아직 만들어 보지 않았다. 실측값은 하나도 없고, '
        '모든 값은 계산했거나 부품 데이터시트나 부품 목록에서 읽은 것이다. '
        '안전 절연 값은 규격 원문이 아니라 참고문헌에 적은 세미나 자료와 인증 '
        '성적서에서 가져왔다.',
        '그림은 이 문서를 위해 새로 그렸다. 다만 %s장의 전력단, 컨트롤러, '
        '보상기 도면 세 장은 ST L6790A 설계 스프레드시트에서 가져왔고, 캡션에 '
        '그렇게 적었다. 다른 회사 Application Note 의 설명을 따른 그림도 캡션에 '
        '출처를 적었다.' % A.secref('설계 절차'),
    ):
        s.append(Paragraph(A.T(t), A.S['p']))
        s.append(Spacer(1, 3))

    s.append(Spacer(1, 12))
    s.append(Paragraph('개정 이력', A.S['h2']))
    s.append(Table(
        [[Paragraph(c, A.S['th']) for c in ('버전', '날짜', '내용')],
         [Paragraph('V1.0', A.S['tc']), Paragraph('2026년 9월', A.S['tc']),
          Paragraph(A.T('한국어 초판. 설계 예제 %.0f V / %.1f A, %.1f W.'
                        % (A.V['Vout'], A.V['Iout'], A.V['Pout'])),
                    A.S['tc'])],
         [Paragraph('V1.2', A.S['tc']), Paragraph('2026년 9월', A.S['tc']),
          Paragraph(A.T('명칭을 single-stage PFC LLC 로 통일. 판정 여유의 '
                        '정의 신설. 계산값을 설계 절차에서 설계 예제로 '
                        '옮기고, 값마다 어느 식에서 나왔는지와 넣은 숫자를 '
                        '함께 적었다. 영문판과 판 번호를 맞췄다.'),
                    A.S['tc'])],
         [Paragraph('V1.3', A.S['tc']), Paragraph('2026년 10월', A.S['tc']),
          Paragraph(A.T('설계 예제를 트랜스포머 한 개로 했다: 카탈로그 코일 포머에 '
                        '칸막이를 더한 TDK %s 코어. 권선, 그 누설, 핀을 그렸고, '
                        '탱크를 그 누설에 맞췄다: L<sub>r</sub> %g&nbsp;&micro;H, '
                        'L<sub>m</sub> %g&nbsp;&micro;H, C<sub>r</sub> '
                        '%.0f&nbsp;nF. 보상 회로 장을 루프 수식, TL431 회로의 '
                        'op-amp 등가, 루프 설계 예제와 함께 다시 썼다. '
                        'V<sub>CC</sub> 는 보조 권선에서 제너 레귤레이터로 '
                        '공급한다. 미국, EU, 일본, 한국, 중국의 가정용 AV 기기 '
                        '기준으로 트랜스포머 안전 절연을 정했다. 본문 전체를 '
                        '간결하게 다시 썼다. 영문판 V1.3 과 같은 내용.'
                        % (__import__('cores').CHOSEN, A.V['Lr'], A.V['Lm'],
                           A.V['Cr'])),
                    A.S['tc'])]],
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
        '<b>f<sub>l</sub></b> 이라고 쓴 것만 라인 주파수이고, 나머지 주파수는 '
        '전부 스위칭 주파수다.',
        '<b>f<sub>n</sub></b> = f<sub>sw</sub>/f<sub>r</sub> — 직렬 공진으로 '
        '정규화한 스위칭 주파수. 게인 곡선은 이것에 대해 그린다. 다른 문서는 '
        'f<sub>sw</sub> 를 f<sub>s</sub> 로 쓰기도 한다.',
        '<b>M</b> — 공진 회로의 게인: 1차로 환산한 출력을 구동 전압의 기본파로 '
        '나눈 것. <b>직렬 공진에서는 부하와 무관하게 M = 1</b>.',
        '<b>Z<sub>0</sub></b> = &radic;(L<sub>r</sub>/C<sub>r</sub>), '
        '<b>Q = Z<sub>0</sub>/R<sub>ac</sub></b>: Q = 0 이 No load 이고, Q 가 '
        '클수록 전력이 크고 곡선이 평평하다.',
        '<b>V<sub>o,eff</sub></b> = V<sub>out</sub> + '
        'N<sub>rect</sub>V<sub>f</sub>. <b>N<sub>rect</sub></b> 는 도통 경로의 '
        '정류기 전압 강하 수로, 센터탭은 1, 풀브리지는 2.',
        '<b>n</b> — 게인 모델의 권선비. <b>n<sub>T</sub></b>&nbsp;=&nbsp;'
        'N<sub>p</sub>/N<sub>s</sub> — 실제로 감는 권선비.',
        '&lambda;&nbsp;=&nbsp;L<sub>r</sub>/L<sub>m</sub>. 옛 문헌은 '
        'm&nbsp;=&nbsp;1&nbsp;+&nbsp;1/&lambda; 를 쓴다.',
        '&theta; 는 라인 위상각으로 상용전원 영교차에서 0 이다. '
        '<b>등가 입력</b>은 topology morphing 뒤 탱크가 보는 전압이며 '
        '상용전원 전압이 아니다.',
    ]))
    return s


def main():
    A.use_korean()
    A.TITLE = 'Single-Stage PFC LLC 컨버터 설계'
    A.HEADSIZE = 12.5
    A.FIGWORD, A.TBLWORD = '그림', '표'
    A.EQWORD, A.EQAGAIN = '식', '식 %s, 다시'
    A.DOCID = ['Application Note AN-SS-L6790A-01 KR', 'V1.3  2026년 10월']
    A.COVER = {
        'title': ['Single-Stage PFC LLC', '컨버터 설계'],
        'sub': 'STMicroelectronics L6790A',
        'boxhead': '설계 예제',
        'box': ['90 ~ 264 Vac,  47 ~ 63 Hz',
                '%.0f V / %.1f A = %.1f W'
                % (A.V['Vout'], A.V['Iout'], A.V['Pout'])],
        'foot': [],
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
