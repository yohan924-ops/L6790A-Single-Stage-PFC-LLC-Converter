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
        '본문의 설계 예제는 아직 만들어 보지 않았다. 실측이라고 적은 값만 '
        '실측이고 나머지는 계산값이다.',
        '그림은 전부 이 문서를 위해 그린 것이다. 발표된 Application Note 의 '
        '논지를 따른 그림은 캡션에 그렇게 적었다.',
    ):
        s.append(Paragraph(A.T(t), A.S['p']))
        s.append(Spacer(1, 3))

    s.append(Spacer(1, 12))
    s.append(Paragraph('개정 이력', A.S['h2']))
    s.append(Table(
        [[Paragraph(c, A.S['th']) for c in ('버전', '날짜', '내용')],
         [Paragraph('V1.0', A.S['tc']), Paragraph('2026년 9월', A.S['tc']),
          Paragraph(A.T('한국어 초판. 설계 예제 %.0f V / %.1f A, %.1f W, '
                        '권선비 %d : %d.'
                        % (A.V['Vout'], A.V['Iout'], A.V['Pout'],
                           A.V['NpSet'], A.V['Ns'])), A.S['tc'])],
         [Paragraph('V1.2', A.S['tc']), Paragraph('2026년 9월', A.S['tc']),
          Paragraph(A.T('명칭을 single-stage PFC LLC 로 통일. 판정 여유의 '
                        '정의 신설. 계산값을 설계 절차에서 설계 예제로 '
                        '옮기고, 값마다 어느 식에서 나왔는지와 넣은 숫자를 '
                        '함께 적었다. 영문판과 판 번호를 맞췄다.'),
                    A.S['tc'])],
         [Paragraph('V1.3', A.S['tc']), Paragraph('2026년 9월', A.S['tc']),
          Paragraph(A.T('설계 예제를 트랜스포머 한 개(ETD 49/25/16DG)로 하고 '
                        '권선과 핀 배정을 그렸다. 보상망 장을 루프 수식, TL431 '
                        '회로의 OPAMP 등가, 루프 설계 예제와 함께 다시 썼다. '
                        '전문을 짧게 다시 썼고, 입력 전압 여섯 조건에서 보고한다. '
                        '영문판 V1.3 과 같은 내용.'),
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
    A.TITLE = 'Single-Stage PFC LLC 컨버터 설계'
    A.HEADSIZE = 12.5
    A.FIGWORD, A.TBLWORD = '그림', '표'
    A.EQWORD, A.EQAGAIN = '식', '식 %s, 다시'
    A.DOCID = ['Application Note AN-SS-L6790A-01 KR', 'V1.3  2026년 9월']
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
