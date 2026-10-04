# -*- coding: utf-8 -*-
"""한국어판 Application Note 본문.

구조는 영문판 an_body.py 와 절 단위로 같다 — 그림·표·수식 호출이 같은
순서로 같은 키를 쓰고, 글만 한국어다.  레이아웃은 an_pdf.py 가 갖고 있고
이 파일은 글만 갖는다.  숫자는 전부 an_pdf.V 보간이며 손으로 적은 상수가
하나도 없어야 한다 — 그것이 이 문서가 시트와 어긋나지 않는 이유다.

말투 규칙:
  * 줄임말은 영어 그대로 (ZVS, ZCS, PFC, THD, FHA, SR, OCP, OVP, VCO)
  * 억지로 한자어를 쓰지 않는다.  capacitive/inductive, below/above,
    boost/buck, 게인, gain margin, distortion, 버퍼, stress 는 영어로
  * 짧은 평서문.  번역투("~에 있어서", "~되어진다")와 예고문("X 절이 그것을
    다룬다")은 쓰지 않는다 (2026-09-23 사용자 지시)
  * 마이너스는 &minus; — NanumGothic 에 없는 글자라 an_pdf 가 라틴 서체로
    그린다 (50차: 그 전에는 하이픈으로 바꿔 넣고 있었다)
  * 번호·계산값 뒤의 조사는 _josa() 로 — 번호가 바뀌면 손으로 적은 조사가
    틀린다
"""


def _kc(name):
    """l6790.line_conditions() 의 영어 조건 이름을 한국어로.

    값은 그쪽에서 계산한 것을 그대로 쓰고 이름만 옮긴다 — 숫자를 다시
    적지 않는다.
    """
    return (name.replace('HB edge', 'HB 경계').replace('FB edge', 'FB 경계')
                .replace(', half bridge', ', 하프브리지')
                .replace(', full bridge', ', 풀브리지'))


def _kr_row(text):
    """cores.py 의 보빈 줄 이름(영어)을 한국어로."""
    return (text.replace('pin-1 row', '1번 핀 열').replace('other row', '반대쪽 열')
                .replace('front row', '앞 열').replace('back row', '뒤 열')
                .replace('both rows', '양쪽 열'))


_INS_KR = [
    # insulation.checks() 의 영어 문장을 한국어로.  숫자는 그쪽 계산값을
    # 그대로 쓰고 문장만 옮긴다 - 표에 손으로 적은 값이 없다.
    (r'^NP1 to NS2, NS3 and the core$', 'NP1 ↔ NS2, NS3, 코어'),
    (r'^NAUX to NS2, NS3 and the core$', 'NAUX ↔ NS2, NS3, 코어'),
    (r'^the triple insulation of the NP1 Litz, one wire from pin to pin$',
     'NP1 Litz 의 삼중 절연, 핀에서 핀까지 한 가닥'),
    (r'^the triple insulation of NAUX, from pin to pin$',
     'NAUX 의 삼중 절연, 핀에서 핀까지'),
    (r'^reinforced: triple-insulated wire, rated ([\d.]+) V rms against a '
     r'working voltage of ([\d.]+) V rms$',
     r'강화 절연: 삼중 절연선, 정격 \1 V rms 대 작업 전압 \2 V rms'),
    (r'^the partition between the sections \(([\d.]+) mm\)$',
     r'칸 사이 칸막이(\1 mm)'),
    (r'^nothing: it sets the leakage only; the wire carries the insulation$',
     '없음: 누설만 정한다. 절연은 전선이 맡는다'),
    (r'^none$', '없음'),
    (r'^NS2, NS3 to the core$', 'NS2, NS3 ↔ 코어'),
    (r'^the same side of the barrier: the core is secondary here$',
     '절연 경계의 같은 쪽: 여기서 코어는 2차 쪽이다'),
    (r'^functional$', '기능 절연'),
    (r'^primary pin row to secondary pin row, across the coil former$',
     '1차 핀 열 ↔ 2차 핀 열, 코일 포머를 가로질러'),
    (r'^([\d.]+) mm between the rows \(([\d.]+) apart, less one pin\)$',
     r'열 사이 \1 mm(\2 mm 간격에서 핀 하나를 뺀 값)'),
    (r'^primary pin to the core, through the air$', '1차 핀 ↔ 코어, 공기 중'),
    (r'^([\d.]+) mm: rows ([\d.]+) mm apart, core ([\d.]+) mm deep at most, '
     r'pin ([\d.]+) mm$',
     r'\1 mm: 열 사이 \2 mm, 코어 깊이 최대 \3 mm, 핀 \4 mm'),
    (r'^primary pins and the stripped TIW ends to the core yoke and to '
     r'secondary leads$', '1차 핀과 피복을 벗긴 TIW 끝 ↔ 코어 요크, 2차 리드'),
    (r'^the coil former and the lead dress, not this drawing$',
     '코일 포머와 리드 처리. 이 도면이 정하지 않는다'),
    (r', or sleeving qualified as reinforced$',
     ', 또는 강화 절연으로 인정된 슬리브'),
    (r'^the TIW approval against the frequencies it sees$',
     'TIW 인증 주파수 대 실제 스위칭 주파수'),
    (r'^approved to ([\d.]+) kHz$', r'\1 kHz 까지 인증'),
    (r'^every switching frequency, start-up included \(([\d.]+) kHz\)$',
     r'기동을 포함한 모든 스위칭 주파수(\1 kHz)'),
    (r'^ok$', '통과'), (r'^open$', '미결'), (r'^FAIL$', '미달'),
]


def _kr_ins(text):
    """insulation.checks() 한 칸을 한국어로.  맞는 문형이 없으면 영어 그대로
    남긴다 - 빌드 뒤 an_check 가 아니라 읽어서 찾는다."""
    import re
    for a, b in _INS_KR:
        text = re.sub(a, b, text)
    return text


# 숫자 끝자리를 한국어로 읽었을 때의 받침: 1 일 · 7 칠 · 8 팔 은 ㄹ, 3 삼 ·
# 6 육 · 0(십·백·영) 은 그 밖의 받침, 2 이 · 4 사 · 5 오 · 9 구 는 받침 없음
_FINAL = {'0': 'C', '1': 'L', '2': '', '3': 'C', '4': '', '5': '', '6': 'C',
          '7': 'L', '8': 'L', '9': ''}


def _josa(x, a, b):
    """숫자 x 뒤의 조사: 받침이 있으면 a, 없으면 b.

    그림·표·식 번호와 계산값은 빌드마다 바뀔 수 있어 조사를 손으로 적으면
    틀린다(50차: '그림 24 은').  '으로/로' 는 ㄹ 받침 뒤에서도 '로'다.
    숫자가 아닌 값(첫 패스의 '?')은 받침 있는 쪽으로 둔다.
    """
    s = str(x).strip()
    fin = _FINAL.get(s[-1:], 'C')
    if a == '으로':
        return b if fin in ('', 'L') else a
    return a if fin else b


def _nj(x, a, b):
    """숫자와 그 조사를 함께: '24 는', '1.021 은'"""
    return '%s %s' % (x, _josa(x, a, b))


def _edge_numbers(A):
    """Full load 에서의 capacitive 경계와, 사람들이 그 대신 말하는 게인 피크.

    서로 다른 주파수다.  같다고 적어 두는 대신 나란히 인쇄해서 얼마나 떨어져
    있는지 보이게 한다.
    """
    import l6790
    from math import degrees
    lam, Q, fr = A.V['lam'], A.V['Qpk'], A.V['fr']
    edge = l6790.zvs_edge(Q, lam)
    fn = [0.30 + 0.7e-5 * i for i in range(100001)]
    pk = max(fn, key=lambda x: l6790.M(x, Q, lam))
    return {'fnEdge': edge * fr, 'fnPk': pk * fr,
            'phPk': abs(degrees(l6790.phase(pk, Q, lam)))}



def _d_overstate(A):
    """how much dropping the conduction ratio d overstates the secondary loss

    Line-cycle loss at the low equivalent corner with d left out, over the
    same with d in: the sweep's own rows, not a typed "about 26 %".
    """
    import l6790
    rows, _ = l6790.sweep(A.R, A.R['Vin_min'], 1.0, N=721)
    ok = [r for r in rows if r]
    return 100 * (sum(r['Isec_w'] ** 2 / r['d'] for r in ok)
                  / sum(r['Isec_w'] ** 2 for r in ok) - 1)

def build(A):
    """A 는 an_pdf 모듈이다 — 여기서 import 하면 an_pdf 가 __main__ 으로
    돌 때 사본이 하나 더 생긴다."""
    import cores as _CORE          # 데이터시트 값은 한 곳에
    import insulation as _INS      # 안전 요구치와 그 출처
    _INS_ALT = _INS.ALTITUDE_M
    import figs_pf as _GAIN        # 게인 차트가 표시하는 교차점
    h1, h2, p, eq, fig, tbl, note = A.h1, A.h2, A.p, A.eq, A.fig, A.tbl, A.note
    bullets, V, CW = A.bullets, A.V, A.CW
    FR, TR, SR = A.figref, A.tblref, A.secref
    ER = A.eqref
    eqagain, calc = A.eqagain, A.calc
    s = []
    add = s.append
    ext = s.extend

    # =============================================================== 1
    add(h1('들어가며'))
    add(p('유니버설 입력 LLC 전원은 보통 two-stage 다. 400&nbsp;V 버스를 만드는 '
          'boost PFC 단과, 그 버스를 내리는 LLC 단. 버스 커패시터는 역률 1 에서 라인 주파수 2배로 변하는 입력 전력의 변동분을 저장하고, LLC 에는 거의 일정한 전압을 공급한다. 그래서 탱크는 좁은 게인 범위만 커버하면 된다.'))
    add(p('<b>single-stage PFC LLC</b> 는 boost 단과 버스 커패시터를 없앤다. '
          '정류된 상용전원이 공진 탱크로 바로 들어간다. 입력은 100/120&nbsp;Hz '
          '정류 사인파가 된다. 탱크가 내야 하는 게인은 라인 주기 동안 입력을 '
          '따라 바뀐다. 버스 커패시터가 하던 일은 출력 커패시터가 맡는다. two-stage 설계 습관은 '
          '대부분 여기에 맞지 않는다.'))
    add(p('이 문서는 이 컨버터가 어떻게 동작하는지, 그리고 STMicroelectronics '
          '<b>L6790A</b> 로 어떻게 설계하는지를 다룬다. 설계 예제 하나를 문서 전체에서 쓴다: <b>90 ~ 264&nbsp;Vac 입력, %(Vout).0f&nbsp;V / '
          '%(Iout).1f&nbsp;A = %(Pout).1f&nbsp;W 출력</b>.' % V))
    add(note('<b>다루는 범위.</b> 전력단, 공진 탱크, 트랜스포머, 출력 뱅크, '
             '컨트롤러 주변 회로, V<sub>CC</sub> 공급, 전압 루프, 트랜스포머가 '
             '갖춰야 할 절연. 다루지 않는 것: EMI 필터, 레이아웃, 안전 인증 '
             '절차 자체.'))

    # =============================================================== 2
    add(h1('기초: LLC 컨버터와 PFC'))
    add(p('이 장은 일반 LLC 와 일반 PFC 를 다룬다. 둘 다 아는 독자는 '
          '%s 장으로 건너뛰어도 된다.'
          % SR('왜 single-stage 인가, 그 대가는 무엇인가')))
    add(h2('LLC 컨버터란 무엇인가'))
    add(p('LLC 컨버터는 사각파 발생기가 공진 회로를 구동하고, 그 회로가 '
          '트랜스포머와 정류기를 구동하는 구조다. 스위치는 주파수만 정한다. '
          '듀티 제어도, 인덕터 전류 제어도 없다.'))
    add(fig('an_llc_stage',
            'LLC 단. 스위치는 주파수를, 탱크는 전력을, 트랜스포머는 전압을 '
            '정한다. 브리지 출력 v<sub>d</sub> = v<sub>A</sub> &minus; '
            'v<sub>B</sub> 가 탱크를 구동한다. 화살표는 그림&nbsp;%s 에 그린 '
            '각 전류의 양의 방향이다.' % FR('an_llc_waves')))
    add(p('탱크 소자는 셋이다. 직렬 인덕턴스 L<sub>r</sub>, 트랜스포머의 자화 '
          '인덕턴스 L<sub>m</sub>, 직렬 커패시턴스 C<sub>r</sub>. '
          'L<sub>m</sub> 은 트랜스포머가 원래 갖고 있는 인덕턴스이고 L<sub>r</sub> 도 보통 그 누설 인덕턴스이므로, 반드시 별도 부품이 필요한 것은 C<sub>r</sub> 뿐이다.'))
    add(h2('왜 더 간단한 토폴로지 대신 LLC 인가'))
    add(p('포워드나 플라이백과 비교하면 LLC 의 장점은 다음과 같다.'))
    ext(bullets([
        '<b>모든 부하에서 소프트 스위칭.</b> 1차 스위치는 전압 0 에서 켜지고, '
        'below 에서는 정류기가 전류 0 에서 꺼진다. 중점을 방전시키는 자화 전류는 '
        '부하와 무관하게 흐르므로 Light load 에서도 ZVS 를 잃지 않는다.',
        '<b>더 높은 주파수.</b> 스위칭 손실이 주파수를 제한하지 않으므로 자성 '
        '부품과 필터가 작아진다.',
        '<b>누설 인덕턴스를 스너버로 억제하는 대신 L<sub>r</sub> 로 쓰고</b>, '
        '출력 인덕터가 없다.']))
    add(p('대가도 있다. 주파수가 입력과 부하에 따라 움직인다. 자화 전류가 '
          '부하와 무관하게 순환하므로 Light load 효율이 떨어진다. 설계는 듀티 '
          '식이 아니라 게인 곡선에서 나온다.'))
    add(h2('공진으로 무엇을 얻나'))
    add(p('하드 스위칭 컨버터에서는 스위치 출력 커패시턴스의 에너지가 매 '
          '턴온마다 버려지고, 그 손실이 주파수를 제한한다.'))
    add(p('LLC 를 <b>inductive 영역에서</b> 돌리면 브리지가 inductive 부하를 '
          '보고, 탱크 전류가 구동 전압보다 뒤처진다. 데드타임 동안 그 뒤처진 '
          '전류가 중점을 스스로 방전시키고, 다음 스위치는 0 V 에서 켜진다. '
          '<b>이것이 ZVS 다.</b> 조건은 %s 절에 있다.'
          % SR('ZVS 와 ZCS 는 다른 것이다')))
    add(fig('an_llc_waves',
            'below 에서의 한 스위칭 주기. i<sub>Lr</sub> 과 i<sub>Lm</sub> 의 '
            '차이가 2차로 넘어간다. 스위치는 자기 전류가 아직 음일 때 켜지고, '
            '그 전류가 이미 중점을 방전시켜 놓았다. 2차는 공진 반주기 '
            'T<sub>r</sub>/2 = 1/(2f<sub>r</sub>) 동안 도통하고, 브리지는 '
            'T<sub>sw</sub>/2 = 1/(2f<sub>sw</sub>) 마다 바뀐다. below 에서는 '
            '뒤쪽이 더 길다.'))
    add(note('ZVS 의 조건은 특정 주파수가 아니라 <i>inductive 동작</i>이다. '
             'capacitive 경계 아래에서는 전류가 앞서고, 브리지가 낮은 '
             '임피던스로 하드 스위칭하며, 부품이 뜨거워지는 정도가 아니라 파손된다. '
             '경계는 부하에 따라 움직인다(%s 절).'
             % SR('두 경계는 같은 경계가 아니다')))
    add(h2('회로가 어떻게 M(f<sub>n</sub>, Q) 가 되는가'))
    add(p('게인 곡선은 세 번의 단순화로 얻고, 단계마다 무시하는 것이 있다.'))
    add(fig('an_rac',
            '정류기와 부하가 왜 저항 하나가 되는가. 출력 전압이 일정하므로 탱크가 '
            '보는 전압 v<sub>RI</sub> 는 사각파이고, 탱크가 기본파만 통과시키므로 전류 '
            'i<sub>RI</sub> 는 사인파다. 기본파만 보면 이 둘은 저항과 같은 전력을 소비한다.'))
    add(fig('an_fha_steps',
            '등가 회로를 만드는 세 단계: 실제 회로, 2차를 1차로 환산한 것, 기본파만 남긴 것. 결과는 게인 M 과 품질계수 Q 를 가진 AC 회로 하나다.'))
    ext(bullets([
        '<b>2차를 1차로 환산한다.</b> 부하 저항에 n&sup2; 이 곱해진다.',
        '<b>정류기와 출력 필터를 저항 하나로 바꾼다.</b> 기본파에서는 저항 '
        '하나로 보인다.',
        '<b>구동 사각파의 기본파만 남긴다.</b> 이것이 <i>기본파 근사(FHA)</i>'
        '이고, LLC 설계가 식이 아니라 시뮬레이션이나 실측으로 끝나는 '
        '이유다.']))
    add(p('남은 회로는 숫자 둘로 설명된다.'))
    ext(bullets([
        '<b>게인 M</b>: R<sub>ac</sub> 양단 전압을 그것을 구동하는 기본파로 '
        '나눈 값. 직렬 공진 f<sub>r</sub> 에서 C<sub>r</sub> 과 L<sub>r</sub> '
        '이 상쇄되므로 <b>거기서는 부하와 무관하게 M = 1</b> 이다. '
        'f<sub>r</sub> 아래에서는 boost 할 수 있고, 위에서는 buck 만 된다.',
        '<b>품질계수 Q = Z<sub>0</sub>/R<sub>ac</sub></b>, '
        'Z<sub>0</sub> = &radic;(L<sub>r</sub>/C<sub>r</sub>). <b>Q 는 출력 '
        '전력과 함께 커진다.</b> Q = 0 이면 곡선이 높고 뾰족하고, 부하가 커지면 낮고 완만해진다.']))
    add(p('f<sub>n</sub> 을 직렬 공진 주파수로 정규화하고, &lambda; 를 두 인덕턴스의 비로 두면 다음과 같다.'))
    add(eq(r'f_{n}=\frac{f_{sw}}{f_{r}}\,,\qquad '
           r'Z_{0}=\sqrt{\frac{L_{r}}{C_{r}}}\,,\qquad '
           r'Q=\frac{Z_{0}}{R_{ac}}\,,\qquad '
           r'\lambda=\frac{L_{r}}{L_{m}}', key='Qdef'))
    add(p('M(f<sub>n</sub>, Q) 라고 쓴 것은 언제나 이 등가 회로의 게인이다.'))
    add(h2('두 개의 공진'))
    add(p('2차가 도통하는 동안에는 반사된 출력 전압이 L<sub>m</sub> 을 '
          '클램프하므로 직렬 공진만 남는다.'))
    add(eq(r'f_r=\frac{1}{2\pi\sqrt{L_rC_r}}', key='fr'))
    add(p('2차가 꺼지면 두 인덕턴스가 함께 공진한다.'))
    add(eq(r'f_o=\frac{1}{2\pi\sqrt{(L_r+L_m)\,C_r}}', key='fo'))
    add(p('f<sub>r</sub> 에서는 부하가 무엇이든 게인이 1 이다. f<sub>o</sub> '
          '에서는 No load 게인이 발산한다. 둘 사이에서 탱크는 boost 할 수 있고, '
          'f<sub>r</sub> 위에서는 못 한다.'))
    add(fig('f02_two_resonances',
            '두 개의 공진과 그 사이의 boost 가능 구간. 색칠한 가장자리는 '
            'capacitive 경계의 No load 위치이고, 부하가 걸리면 위로 올라간다.'))

    add(p('below 에서는 반주기마다 두 구간이 있고, 그동안 켜진 스위치 쌍은 '
          '같다: 전력 전달, 그다음 프리휠링. 공진에서는 반주기가 전력 '
          '전달뿐이고, above 에서는 전력 전달이 중간에 잘린다.'))
    add(fig('an_modes_12',
            '<b>앞 반주기, STEP 1 과 2.</b> <b>1</b>&nbsp;전력 전달: '
            'S<sub>1</sub>·S<sub>4</sub> 가 켜져 있고, 공진 전류가 자화 전류를 '
            '넘어서며 그 차이가 D<sub>1</sub> 으로 흐른다. L<sub>m</sub> 이 '
            '클램프돼 있으므로 이 구간은 f<sub>r</sub> 로 공진한다. '
            '<b>2</b>&nbsp;프리휠링: 공진 전류가 자화 전류까지 떨어져 정류기가 '
            '꺼지고, L<sub>m</sub> 이 공진에 들어와 f<sub>o</sub> 로 공진한다. '
            '같은 스위치가 그대로 켜져 있다. 회색 바디 다이오드와 C<sub>oss</sub> 는 그 STEP 에서 동작하지 않는다.'))
    add(fig('an_modes_34',
            '<b>STEP 3 과 4, 데드타임.</b> <b>3</b>&nbsp;스위치가 전부 꺼져 '
            '있으므로 자화 전류는 네 개의 C<sub>oss</sub> 로만 흐를 수 있고, '
            'A 를 끌어내리며 B 를 밀어올린다. <b>4</b>&nbsp;스윙이 끝나고 '
            'S<sub>2</sub>·S<sub>3</sub> 의 바디 다이오드가 V<sub>ds</sub> 를 '
            '0 에 클램프한다. 다음 게이트 신호는 이 구간 안에 들어와야 한다.'))
    add(fig('an_modes_56',
            '<b>뒤 반주기, STEP 5 와 6</b>: S<sub>2</sub>·S<sub>3</sub> 와 '
            'D<sub>2</sub> 로 이루어지는 1·2 의 대칭 동작.'))
    add(fig('an_modes_78',
            '<b>STEP 7 과 8</b>, 두 번째 데드타임. 중점이 되돌아가고(<b>7</b>), '
            'S<sub>1</sub>·S<sub>4</sub> 의 바디 다이오드가 클램프하며(<b>8</b>), '
            'STEP 1 이 0 V 에서 시작된다. ZVS 는 STEP 4 와 8 에서만 일어난다.'))
    add(fig('an_modes_wave',
            '<b>각 STEP 이 파형의 어느 구간인가.</b> 번호가 붙은 띠가 위 여덟 칸을 '
            '시간 순으로 늘어놓은 것이다. below 에서 '
            'f<sub>sw</sub>/f<sub>r</sub> = 0.70 으로 그렸고, STEP 3·4·7·8 이 '
            '보이도록 데드타임을 넓혔다. 전류 크기는 이 설계에서 탱크가 보는 '
            '가장 낮은 전압에서의 I<sub>Lr,pk</sub> 와 I<sub>Lm,pk</sub> 다. 정류기 전류는 '
            '1차로 환산해 그렸다: i<sub>D</sub>/n = i<sub>Lr</sub> &minus; '
            'i<sub>Lm</sub>.', width=CW))
    add(note('<b>"프리휠링" 은 문헌에서 서로 다른 두 구간을 가리킨다.</b> '
             '여기서는 STEP 2·6 이다: 정류기가 꺼지고, L<sub>m</sub> 이 공진에 '
             '들어오며, 같은 스위치가 켜져 있는 구간. Toshiba 의 <i>Resonant '
             'Circuits and Soft Switching</i>(2019) 은 같은 말을 바디 '
             '다이오드가 도통하는 데드타임에 쓴다. 데드타임은 어느 주파수에나 '
             '있고, STEP 2·6 은 below 에서만 있다.'))
    add(fig('an_three_cases',
            'below, 공진, above. <b>위:</b> 게이트, 브리지 전압, 자화 전류를 '
            '점선으로 겹친 공진 전류, 정류기 전류. <b>아래:</b> 같은 세 스위칭 '
            '주파수를 Half load 게인 곡선 위의 점으로 찍었다. Full load 에서는 '
            'f<sub>sw</sub>/f<sub>r</sub> = 0.70 이 이미 capacitive 이므로 '
            'Full load 곡선은 ZVS 경계부터만 그렸다.', width=CW))
    add(p('아래 패널은 %s 절의 게인 M 이다. f<sub>r</sub> 의 어느 쪽에서 '
          '도는지가 탱크가 boost 할지 buck 할지를 정한다.'
          % SR('게인 곡선과 세 영역')))
    ext(bullets([
        '<b>f<sub>r</sub> 아래: M&nbsp;&gt;&nbsp;1, boost.</b> 공진 전류의 '
        '사인 반파가 일찍 끝나고 <b>i<sub>Lr</sub> 이 i<sub>Lm</sub> 과 '
        '같아진다.</b> 그때부터 2차로 넘어가는 전력이 없다: 프리휠링.',
        '<b>f<sub>r</sub> 에서: 부하와 무관하게 M&nbsp;=&nbsp;1.</b> 브리지가 '
        '바뀌는 순간 i<sub>Lr</sub> 이 i<sub>Lm</sub> 을 만나고, 정류기 '
        '전류도 같은 순간 0 이 된다. 가장 효율이 좋은 점이다.',
        '<b>f<sub>r</sub> 위: M&nbsp;&lt;&nbsp;1, buck.</b> 스위칭 반주기가 '
        '먼저 끝나 공진 전류의 사인 반파가 <b>잘린다</b>. 스위치는 더 큰 '
        '전류를 끊고, 정류기는 도통 중에 끊긴다.']))
    add(p('<b>프리휠링 구간의 공진 주파수가 f<sub>o</sub> 다.</b> L<sub>m</sub> 을 '
          '클램프하는 것이 없으므로 L<sub>r</sub>&nbsp;+&nbsp;L<sub>m</sub> 이 '
          'C<sub>r</sub> 과 공진한다. 거의 평평해 보이는 것은 이 구간이 '
          'f<sub>o</sub> 의 주기에 비해 짧고, 그 공진의 꼭대기 근처에 있기 '
          '때문이다. f<sub>sw</sub> 가 낮을수록 반주기에서 이 구간이 차지하는 '
          '몫이 커진다. 쓸모 있는 동작은 모두 두 주파수 사이에서 일어난다.'))
    add(note('<b>이 기호는 업계 표준이 아니다.</b> 널리 쓰이는 자료 중 적어도 하나는 '
             '<i>직렬</i> 공진을 f<sub>o</sub> 라고 부른다. 여기와 정반대다. '
             '비교하기 전에 확인할 것.'))
    add(p('일반 LLC 는 공칭 입력에서 순환 전류가 가장 작은 f<sub>r</sub> 근처에서 '
          '돌고, hold-up 때만 그 아래로 내려간다. 이 컨버터는 입력 전압과 라인 '
          '위상에 따라 양쪽을 다 오간다(%s 절).'
          % SR('이 컨버터는 공진의 어느 쪽에서 도는가')))
    add(h2('게인 곡선과 세 영역'))
    add(p('기본파 근사로 탱크 게인은 다음과 같다.'))
    add(eq(r'M(f_n,Q,\lambda)=\frac{1}'
           r'{\sqrt{\left(1+\lambda-\frac{\lambda}{f_n^{2}}\right)^{2}'
           r'+Q^{2}\left(f_n-\frac{1}{f_n}\right)^{2}}}', key='M'))
    add(p('간단한 검산 두 가지. f<sub>n</sub>&nbsp;=&nbsp;1 에서는 Q 항이 '
          '사라져 <b>Q 가 무엇이든 M&nbsp;=&nbsp;1</b> 이므로 모든 곡선이 그 '
          '점을 지난다. No load(Q&nbsp;=&nbsp;0)에서는 f<sub>n</sub> 을 올려도 '
          'M 이 1/(1+&lambda;) 까지만 내려간다. 그 하한은 %s 절에서 문제가 '
          '된다.' % SR('&lambda; 의 반대쪽 한계, 그리고 해가 없는 경우')))
    add(p('곡선에는 세 영역이 있다. capacitive/inductive 경계 아래에서는 '
          '브리지가 하드 스위칭한다: 허용되지 않는다. 경계와 f<sub>r</sub> '
          '사이에서는 inductive 이고 boost 하며, f<sub>r</sub> 위에서는 '
          'inductive 이고 buck 한다. 경계는 Full load 곡선 기준으로 그렸다. '
          'No load 에서는 f<sub>o</sub> 에 있고, 부하가 걸릴수록 위로 올라간다.'))
    add(fig('f04_three_regions',
            '세 영역. Full load 곡선 기준으로 색칠했다. 쓸 수 있는 것은 '
            'inductive 두 영역뿐이다. 영역 구분은 ROHM TechWeb 을 따랐다.'))
    add(p('<b>어느 쪽에서 도는지는 파형 없이 차트로 읽는다.</b> 요구 게인을 '
          '수평선으로 긋고 현재 부하의 곡선과 만나는 점을 찾는다. 요구 게인이 '
          '1 보다 크면 교차점은 f<sub>n</sub>&nbsp;=&nbsp;1 의 왼쪽이다(below, '
          '그림&nbsp;%s 의 왼쪽 열). 1 이면 부하와 무관하게 f<sub>r</sub> 이다. '
          '1 보다 작으면 오른쪽이다(above).' % FR('an_three_cases')))
    add(p('따라서 어느 쪽인지는 부하가 아니라 입력 전압이 정한다. 요구 게인은 '
          '반사된 출력 전압을 탱크가 보는 입력으로 나눈 값이고, 부하는 곡선만 '
          '고른다. 입력이 높아지면 수평선이 내려가고 교차점은 오른쪽으로 간다. '
          '부하가 정하는 것은 교차점이 아직 capacitive 경계의 오른쪽에 '
          '있는지다(%s 절).' % SR('두 경계는 같은 경계가 아니다')))
    add(h2('capacitive 와 inductive: 이름의 뜻'))
    add(p('이 이름은 <b>브리지에서 본 부하의 성격</b>을 가리킨다: 구동 사각파에 대한 '
          '탱크 전류의 위상이다. 낮은 주파수에서는 C<sub>r</sub> 이 지배해 '
          '전류가 <i>앞서고</i>, 높은 주파수에서는 인덕턴스가 지배해 '
          '<i>뒤처진다</i>. 그 위상이 스위칭이 소프트인지 하드인지를 정한다.'))
    add(fig('an_cap_ind',
            '경계 양쪽. <b>위:</b> 경계는 게인 피크보다 조금 위에 있다. '
            '<b>가운데:</b> S<sub>1</sub> 에 게이트가 들어오는 순간의 레그. '
            '왼쪽은 탱크 전류가 이미 양이라 S<sub>2</sub> 의 바디 다이오드로 '
            '흐르고 있고, S<sub>1</sub> 이 도통 중인 다이오드 위에서 켜진다. '
            '오른쪽은 음이라 데드타임 동안 중점을 올려놓았고, S<sub>1</sub> 은 '
            '자기 바디 다이오드가 0 V 에서 도통하는 상태에서 켜진다. '
            '<b>아래:</b> 중점 전압 v<sub>A</sub>(0 기준), 탱크 전류, 켜지는 '
            '스위치의 드레인 전류 i<sub>S1</sub>. 같은 축척이다.', width=CW))
    ext(bullets([
        '<b>inductive: 전류가 뒤처진다.</b> 턴오프 때 전류가 아직 브리지 '
        '노드를 반대쪽 레일로 밀고 있다. 데드타임 동안 이 전류가 노드를 옮기므로 다음 '
        '소자가 0 V 에서 켜진다. <b>ZVS.</b>',
        '<b>capacitive: 전류가 앞선다.</b> 이미 뒤집혀 있어서 노드를 반대로 민다. '
        '다음 소자는 레일 전압을 다 받은 채 켜지고, 반대쪽 바디 다이오드는 '
        '낮은 임피던스로 강제 역회복된다. <b>하드 스위칭이고, 부품을 파손시키는 고장이다.</b> 설계는 이 영역에 들어가지 않고, 들어갔을 때를 위해 컨트롤러에 보호 기능이 있다.']))
    add(h2('다이오드가 한쪽에서만 역회복하는 이유'))
    add(p('레그 하나를 보자. 하이사이드 스위치, 로우사이드 스위치, 중점에 연결된 탱크. 어느 소자가 꺼지든 <b>탱크 전류는 멈추지 않는다</b>. '
          '데드타임 동안 어느 소자가 그 전류를 흘리느냐가 결과를 결정한다. '
          '그림&nbsp;%s 의 가운데 행이 두 경우다. onsemi AN-4151 을 '
          '따랐다.' % FR('an_cap_ind')))
    ext(bullets([
        '<b>inductive.</b> 전류가 두 C<sub>oss</sub> 를 통해 중점을 '
        '<i>반대쪽</i> 레일로 옮기고, 켜질 소자의 바디 다이오드가 이어받으며, '
        '그 소자는 0 V 에서 게이트를 받는다. 채널이 전류를 넘겨받을 때 자기 바디 '
        '다이오드에는 역전압이 걸리지 않는다: <b>회복할 것이 없다</b>.',
        '<b>capacitive.</b> 전류가 이미 뒤집혀 있다. 방금 꺼진 소자의 바디 '
        '다이오드를 통해 중점을 원래 레일에 붙잡아 둔다. 켜질 소자는 레일 '
        '전압을 다 받은 채, 도통 중인 다이오드 위에서 게이트를 받는다.']))
    add(p('그 다이오드는 저장 전하가 다 빠질 때까지 역전압을 차단하지 못하므로, 그동안 '
          '두 소자가 함께 도통하고 레일이 그 둘을 통해 Short 된다. 전류는 루프 '
          '인덕턴스만이 제한하는 스파이크이고, 레일 전압을 다 받은 채 켜지는 소자에서 열로 소모된다. 다이오드가 끊길 때는 루프 인덕턴스의 di/dt 가 '
          '소자 양단에 오버슈트로 나타난다.'))
    add(note('<b>1차 소자에 fast-recovery 바디 다이오드를 요구하는 이유가 '
             '이것이다</b>(%(ref)s 절). capacitive 영역에 한 번이라도 들어가면 '
             '소자가 반대쪽 소자의 도통 중인 바디 다이오드 위에서 켜진다. '
             'f<sub>Min</sub> 을 f<sub>o</sub> 위에 두는 이유, anti-capacitive '
             '보호가 있는 이유도 같다.'
             % dict(ref=SR('이 설계의 반도체 요구조건'))))
    add(h2('두 경계는 같은 경계가 아니다'))
    add(p('두 쌍의 용어는 모두 주파수 축 위의 위치를 가리키지만, 서로 다른 선이다.'))
    ext(tbl('두 가지 분류, 두 개의 경계, 두 가지 결과.',
            [['', 'capacitive / inductive', 'below / above'],
             ['경계', '<b>arg Z<sub>in</sub> = 0</b> 인 곳',
              '<b>f<sub>r</sub></b>, 직렬 공진'],
             ['움직이나?', '<b>그렇다 &mdash; 부하에 따라</b>',
              '아니다. L<sub>r</sub> 과 C<sub>r</sub> 이 고정한다'],
             ['정하는 것',
              '<b>1차</b>의 ZVS 냐 하드 스위칭이냐',
              'boost 냐 buck 이냐, 그리고 <b>2차</b>의 ZCS 여부'],
             ['어느 쪽이 허용되나', 'inductive 만, 언제나', '양쪽 다 정상 동작']],
            widths=[CW * 0.19, CW * 0.40, CW * 0.41], key='capind', split=True))
    add(p('capacitive 경계는 <b>부하와 함께 올라간다</b>. No load 에서는 '
          'f<sub>o</sub> 에 있고, 부하가 커질수록 f<sub>r</sub> 쪽으로 올라간다. '
          '그래서 Light load 에서 inductive 이던 주파수가 Overload 에서는 '
          'capacitive 일 수 있다.'))
    add(note('<b>경계는 게인 피크가 아니다.</b> <b>arg Z<sub>in</sub> = 0</b> '
             '인 곳이고, 피크보다 조금 <i>위</i>다. 피크를 쓰면 위험한 쪽으로 낙관적인 판정이 된다. 이 설계의 두 주파수는 %(ref)s 절에 있고, 판정은 '
             '%(zvsref)s 절의 ZVS 검사에서 온다.'
             % dict(ref=SR('운전 영역 전체의 ZVS'), zvsref=SR('ZVS 검증'))))
    add(fig('an_loadshift',
            '경계는 부하와 함께 올라간다. 점선은 Q 를 바꿔 가며 그린 경계의 궤적이다.'))
    ext(bullets([
        '<b>below 이면서 inductive</b>: 일반적인 boost 영역이다.',
        '<b>below 이면서 capacitive</b>: 고장이다. f<sub>r</sub> 아래로 가는 '
        '것이 위험한 게 아니라 경계 아래로 가는 것이 위험하다.',
        '<b>above</b>: 어느 부하에서도 inductive 다.']))
    add(note('<b>설계 규칙.</b> f<sub>Min</sub> 을 f<sub>o</sub> 위에 둔다. '
             '그것은 No load 경계일 뿐이라 필요조건이지 충분조건이 아니다. 실제 검사는 %s 절의 ZVS 스윕이고, 부하를 걸고 라인 위상 전체에서 '
             '돌린다.' % SR('ZVS 검증')))
    add(h2('ZVS 와 ZCS 는 다른 것이다'))
    add(p('둘 다 소자의 전압이나 전류가 0 일 때 스위칭한다. 적용되는 소자가 '
          '다르고, 보장되는 것은 하나뿐이다.'))
    add(fig('an_zvs_zcs',
            '1차의 ZVS 와 2차의 ZCS: 소자도, 원리도, 조건도 다르다.',
            width=CW))
    ext(bullets([
        '<b>1차 스위치의 ZVS</b> 는 inductive 동작이 조건이고, 그것은 '
        'f<sub>r</sub> 양쪽 어디서나 가능하다. 어디서나 필수이며, 여유는 %s 절에 '
        '있다.' % SR('ZVS 검증'),
        '<b>2차 정류기의 ZCS</b> 는 공진 전류가 스스로 0 에 닿을 때 일어나고, '
        '그것은 <b>f<sub>r</sub> 아래에서만</b> 그렇다. f<sub>r</sub> 위에서는 '
        '정류기가 도통 중에 끊기고 역회복이 다시 생긴다.']))
    add(note('입력이 f<sub>r</sub> 을 넘나드는 컨버터는 양쪽을 다 검사해야 '
             '한다. f<sub>r</sub> 위에서 도는 동안에는 정류기의 바디 다이오드와 '
             'SR 데드타임이 문제가 된다.'))
    add(h2('ZVS 가 실제로 일어나게 데드타임을 잡는 법'))
    add(p('ZVS 는 전하 문제다. 데드타임 동안 자화 전류가 브리지 노드를 반대쪽 '
          '레일까지 옮길 만큼의 전하를 공급해야 한다. 설계 변수는 게이트가 꺼진 뒤 '
          '탱크 전류가 0 에 닿기까지 걸리는 시간 T<sub>ZC</sub> 이고, 그것이 '
          '데드타임보다 길어야 한다.'))
    add(eq(r'T_{ZC}\;>\;t_D', key='zvs'))
    add(fig('f05_zvs_mechanism',
            '데드타임 동안 브리지 노드를 방전시키는 것은 자화 전류다. 조건은 '
            '둘이다: 데드타임이 끝나기 전에 전류가 0 이 되면 안 되고'
            '(T<sub>ZC</sub> &gt; t<sub>D</sub>), 스윙 T<sub>T</sub> 가 '
            '데드타임 안에 끝나야 한다.'))
    add(note('<b>C<sub>o(tr)</sub></b>(즉 Q<sub>oss</sub>)를 쓸 것. 데이터시트 첫 쪽의 C<sub>oss</sub> 가 아니다. 데이터시트의 세 값은 3 ~ 5 배 다르고, '
             'ZVS 는 전하 문제다.'))
    add(h2('플라이백이 아니다, 그래서 코어가 달라진다'))
    add(p('플라이백 습관 두 가지가 여기서는 틀리고 비용도 든다: 전류로 코어를 '
          '정하는 것, 그리고 권선 피크 전류에서 포화 시험을 요구하는 것. 둘 다 '
          '두 권선이 언제 도통하느냐에서 나온다.'))
    add(p('<b>플라이백에서는 두 권선이 같이 도통하지 않으므로</b> 매 순간 권선 '
          '전류 전부가 자화 전류다. 전달되는 에너지는 전부 먼저 코어에 '
          '저장됐던 것이고, 자속은 <i>전류</i>를 따라가며, A<sub>e</sub> 는 '
          '피크 전류에서 정한다.'))
    add(p('<b>LLC 에서는 두 권선이 같이 도통한다.</b> 암페어턴이 서로 상쇄되고, '
          '그 차이만 코어를 자화시킨다.'))
    add(eq(r'N_{p}\,i_{p}\;-\;N_{s}\,i_{s}\;=\;N_{p}\,i_{\mu}', key='mmf'))
    add(p('부하 전류는 트랜스포머 작용으로 통과할 뿐 코어에 들어가지 않는다. '
          '코어에 저장되는 것은 자화 에너지 &frac12;L<sub>&mu;</sub>i<sub>&mu;</sub>'
          '&sup2; 이다. L<sub>&mu;</sub> 는 실제 트랜스포머의 자화 인덕턴스로, '
          '탱크 모델의 L<sub>m</sub> 과 꼭 같지는 않다(%s 절). 이 에너지는 '
          '부산물이 아니다. i<sub>&mu;</sub> 가 데드타임 동안 브리지 노드 '
          '전압을 스윙시키는 전류다. 갭은 L<sub>&mu;</sub> 를, 그리고 그것을 '
          '통해 L<sub>m</sub> 을 맞추려고 있는 것이지 부하 에너지를 저장하려고 '
          '있는 것이 아니다.' % SR('두 개의 비, 두 개의 인덕턴스')))
    add(fig('an_flyback_llc',
            '왼쪽: 불연속 도통(DCM)의 플라이백으로 그림&nbsp;%s 같다. 스위치와 '
            '정류기가 같이 켜지는 일이 없으므로 도통하는 권선이 '
            '자화 전류 전부를 흘리고 자속은 그것을 따라 오른다. 오른쪽: 둘이 '
            '동시에 도통하고 i<sub>&mu;</sub> = i<sub>p</sub> &minus; '
            'i<sub>s</sub> 만 코어를 자화시킨다. 2차 전류는 1차로 환산해 '
            '그렸다. 화살표는 기준 방향이다. 플라이백의 i<sub>s</sub> 는 점으로 '
            '들어가는 방향, LLC 의 i<sub>s</sub> 는 점에서 나오는 방향이라 '
            '플라이백에서는 기자력이 더해진다. 맨 아래 행: 점선은 각 권선이 혼자 만들 자속, 실선은 그 '
            '합, 색칠한 띠는 2차가 만드는 차이.'
            % _nj(FR('an_flux_steps'), '과', '와')))
    add(p('그림&nbsp;%s 두 컨버터의 한 주기를 구간별로 따라간다. 어느 '
          '권선이 도통하는가. 그 권선에 어떤 전압이 걸리는가. 그래서 자속이 어느 '
          '쪽으로 움직이고, 무엇이 그것을 멈추는가.'
          % _nj(FR('an_flux_steps'), '은', '는')))
    add(fig('an_flux_steps',
            '자속이 만들어지는 과정. 왼쪽은 불연속 도통의 플라이백, 오른쪽은 '
            'below 의 LLC 로, 8구간 모델에 이 설계의 전류를 넣어 그렸고 번호는 '
            '그림&nbsp;%s STEP 번호다. 맨 아래 행의 자속을 비교할 것.'
            % _nj(FR('an_modes_wave'), '의', '의')))
    ext(bullets([
        '<b>플라이백 1.</b> 스위치가 켜진다. 1차에 V<sub>in</sub> 이 걸리고 '
        'i<sub>p</sub> 가 V<sub>in</sub>/L<sub>p</sub> 로 올라간다. 다른 권선은 '
        '도통하지 않으므로 암페어턴 전부가 코어를 자화시킨다: B 는 '
        'V<sub>in</sub>/(N<sub>p</sub>A<sub>e</sub>) 로 오른다. 에너지는 갭에 저장된다.',
        '<b>플라이백 2.</b> 스위치가 꺼진다. 자속은 불연속으로 변할 수 없으므로 암페어턴이 '
        '그 순간 2차로 넘어간다: N<sub>s</sub>i<sub>s</sub> = '
        'N<sub>p</sub>I<sub>p,pk</sub>. 정류기가 도통하고 2차에 '
        'V<sub>out</sub> 이 걸리며, 갭의 에너지가 출력으로 빠져나가는 동안 B '
        '는 V<sub>out</sub>/(N<sub>s</sub>A<sub>e</sub>) 로 내려간다.',
        '<b>플라이백 3.</b> 2차 전류가 0 에 닿는다. 두 권선 다 꺼져 있고 '
        '자속은 다음 주기까지 0 근처에 머문다. 피크 자속은 스위치가 꺼지는 '
        '순간 I<sub>p,pk</sub> 가 정했고, 그 값은 부하와 입력이 요구한 '
        '만큼이다.',
        '<b>LLC 1.</b> 브리지 스위치 하나가 켜진다. 2차 전압이 '
        'V<sub>out</sub> 에 닿는 순간 정류기가 도통하므로 2차는 '
        'V<sub>out</sub> 에 클램프되고 자화 브랜치에는 n&thinsp;V<sub>out</sub> '
        '이 걸린다. 부하 전류는 두 권선에 동시에 흐르고 그 암페어턴은 '
        '상쇄되며, i<sub>&mu;</sub> 만 올라간다: B 는 '
        'V<sub>out</sub>/(N<sub>s</sub>A<sub>e</sub>) 로 오른다.',
        '<b>LLC 2.</b> 공진 반주기가 끝난다: i<sub>s</sub> 가 0 에 닿고 '
        '정류기가 꺼지며 클램프가 사라진다. L<sub>m</sub> 이 C<sub>r</sub> 과의 '
        '공진에 들어오고, i<sub>&mu;</sub> 는 거의 평평하며, B 는 피크에 '
        '머문다. 그 피크는 V<sub>out</sub> 과 T<sub>r</sub>/2 만이 정했다.',
        '<b>LLC 3·4.</b> 데드타임. i<sub>&mu;</sub> 가 브리지 노드를 반대쪽 '
        '레일로 옮긴다. 자속은 거의 움직이지 않는다.',
        '<b>LLC 5.</b> 반대쪽 스위치가 켜지고 반대쪽 정류기가 2차를 '
        '&minus;V<sub>out</sub> 에 클램프한다. B 는 같은 기울기로 '
        '&minus;B<sub>pk</sub> 까지 내려간다.']))
    ext(tbl('같은 코어 둘, 나란히 비교.',
            [['', '플라이백', 'LLC'],
             ['자속을 정하는 권선',
              '도통하는 쪽; B 는 그 전류를 따라간다',
              '클램프된 2차; B 는 그 볼트-초를 따라간다'],
             ['피크 자속을 정하는 것',
              'I<sub>p,pk</sub>: 부하, 입력 전압, 도통 모드',
              'V<sub>out</sub>, T<sub>r</sub>, N<sub>s</sub> 뿐'],
             ['부하에 따른 자속', '부하와 함께 오른다', '움직이지 않는다'],
             ['스위칭 주파수에 따른 자속',
              '주파수가 오르면 내려간다(온 시간이 짧아지므로)',
              'below 에서는 일정, above 에서는 내려간다'],
             ['갭이 하는 일',
              '부하 에너지를 저장한다; 갭과 A<sub>e</sub> 가 함께 전력을 '
              '정한다',
              'L<sub>m</sub>, 곧 자화 전류와 ZVS 를 정한다; 자화 에너지만 저장한다'],
             ['코어를 위협하는 것', 'Overload, 과전류', '출력 과전압'],
             ['코어를 지키는 보호', '전류 제한',
              '출력 OVP; 전류 제한은 OVP 가 없을 때만(%s 절)'
              % SR('포화 시험은 권선 피크 전류가 아니다')],
             ['포화 시험 전류',
              '권선 피크 전류에 여유를 더한 것',
              'i<sub>&mu;,pk</sub> 를 OVP 상한으로 환산한 것; 권선 피크보다 '
              '작다'],
             ['A<sub>e</sub> 를 정하는 것',
              '피크 전류와 L<sub>p</sub>: 에너지',
              'f<sub>r</sub> 에서의 출력 볼트-초: 패러데이']],
            widths=[CW * 0.26, CW * 0.37, CW * 0.37], key='flyllc',
            split=True))
    add(note('"LLC 트랜스포머는 에너지를 저장하지 않는다" 는 흔히 하는 말이다. 자화 '
             '에너지를 주기마다 두 번 저장한다. 저장하지 않는 것은 부하 '
             '에너지다.'))
    add(p('그래도 A<sub>e</sub> 가 문제가 되는 것은 패러데이 법칙이 에너지 '
          '저장 여부를 묻지 않기 때문이다.'))
    add(eq(r'B(t)\;=\;\frac{1}{N\,A_{e}}\int v\,dt', key='faraday'))
    add(p('v 는 권선 전압, N 은 턴수, A<sub>e</sub> 는 코어 면적이다. '
          '<b>달라지는 것은 식에 넣는 값뿐이다.</b> 플라이백의 볼트-초는 입력 전압 '
          '곱하기 온 시간이다. LLC 에서는 도통하는 2차가 권선을 공진 반주기 '
          '동안 출력에 클램프하므로 자속은 <b>출력 전압만으로</b> 정해진다'
          '(%s 절).' % SR('자속은 1차가 아니라 2차가 정한다')))
    add(p('세 가지 결과가 따라온다.'))
    ext(bullets([
        '<b>자속은 부하와 함께 오르지 않는다.</b> 부하가 늘면 i<sub>s</sub> '
        '와 i<sub>p</sub> 의 반사 성분이 같이 오르고, 그 차이 i<sub>&mu;</sub> '
        '는 움직이지 않는다. Overload 가 위협하는 것은 동선과 반도체이지 코어가 '
        '아니다.',
        '<b>자속은 출력 전압과 함께 오른다.</b> 그래서 포화 사양은 공칭 '
        '출력이 아니라 과전압 threshold 에서 정한다(%s 절).'
        % SR('포화 시험은 권선 피크 전류가 아니다'),
        '<b>below 에서는 자속이 스위칭 주파수와 함께 줄지 않는다.</b> f<sub>sw</sub> 가 무엇이든 정류기가 권선을 T<sub>r</sub>/2 '
        '동안 클램프하므로, 자속 식에 f<sub>r</sub> 이 나온다.']))
    add(p('<b>설계할 때 염두에 둘 것.</b>'))
    ext(bullets([
        '<b>A<sub>e</sub> 는 전류가 아니라 볼트-초로 정한다.</b> 입력은 '
        'V<sub>out</sub>, N<sub>s</sub>, f<sub>r</sub> 이고(%s 절), 권선 '
        '전류는 들어가지 않는다.'
        % SR('자속은 1차가 아니라 2차가 정한다'),
        '<b>여유를 준다고 갭을 더 두지 말 것.</b> 플라이백에서는 갭이 크면 '
        '저장 에너지가 는다. 여기서는 갭이 크면 L<sub>m</sub> 이 작아진다: '
        '자화 전류와 순환 손실이 늘고 &lambda; 가 달라지며, 자속은 전혀 '
        '변하지 않는다. 갭은 L<sub>m</sub> 이 정하고 L<sub>open</sub> 으로 '
        '확인하며, 자속 여유는 OVP 상한이 정하고 DC overlap 시험으로 '
        '확인한다.',
        '<b>시험 전류는 L<sub>&mu;</sub> 를 따라가고, 자속은 따라가지 '
        '않는다.</b> 갭이 작으면 L<sub>&mu;</sub> 가 오르고 같은 자속에서 '
        'i<sub>&mu;,pk</sub> 가 내려간다. 갭이 바뀌면 I<sub>eq</sub> 를 실제 '
        'L<sub>&mu;</sub> 로 다시 계산한다. 이전 값을 가져다 쓰지 않는다.',
        '<b>B<sub>pk</sub> 가 고정이므로 코어 손실은 주파수를 따라간다.</b> '
        'below 에서는 라인 사이클의 어느 점에서나 자속이 같고, 그 자속에서의 '
        '코어 손실은 f<sub>sw</sub> 와 함께 오른다. above 에서는 자속이 1/f<sub>sw</sub> 로 줄고 '
        '손실도 따라 줄므로, 최악 코어 손실은 f<sub>r</sub> 근처다.',
        '<b>비용이 가장 큰 플라이백 습관</b>은 탱크 피크 전류에서 포화하지 말라고 '
        '벤더에 요구하는 것이다. 컨버터가 만들 수 없는 자속을 위해 필요 '
        '이상으로 큰 코어를 요구하는 셈이다.']))
    add(p('DC overlap 시험은 나머지 권선을 모두 Open 으로 두고 하므로 상쇄가 없다: 시험 전류 전부가 '
          '자화 전류다. %s 절에서 숫자로 확인한다.'
          % SR('포화 시험은 권선 피크 전류가 아니다')))
    add(h2('LLC 는 보통 어떻게 설계하나'))
    add(p('표준 순서다. %s 장이 이 순서를 따르되 두 곳에서 벗어난다.'
          % SR('설계 절차')))
    ext(bullets([
        '<b>1  권선비.</b> 공칭 입력에서 M&nbsp;=&nbsp;1 근처, 순환 전류가 가장 '
        '작은 곳에서 돌도록.',
        '<b>2  게인 범위</b> M<sub>min</sub>&hellip;M<sub>max</sub>. 입력 '
        '범위와 출력 허용 오차에서.',
        '<b>3  1차로 환산한 부하 저항</b> R<sub>ac</sub>.',
        '<b>4  m = (L<sub>r</sub>+L<sub>m</sub>)/L<sub>r</sub> (또는 &lambda;) 과 Q 를 함께</b> 피크 게인 차트에서. m 마다 '
        'Q 에 대한 도달 가능 피크 게인 곡선이 있고, 설계는 그 아래에 여유를 '
        '두고 있어야 한다. m 이 크면 순환 전류가 작고 피크 게인도 작다.',
        '<b>5  부품값.</b> Q 와 R<sub>ac</sub> 에서 Z<sub>0</sub>, '
        'Z<sub>0</sub> 와 f<sub>r</sub> 에서 C<sub>r</sub> 과 L<sub>r</sub>, '
        'm 에서 L<sub>m</sub>.',
        '<b>6  검증.</b> 최악 코너의 게인 여유, 최악점의 ZVS, 실제 부품에 대한 '
        '전류와 자속.']))
    add(fig('an_peakgain',
            'STEP 4: 피크 게인은 m 과 Q 둘 다에 달렸으므로, 요구 게인과 Q 를 '
            '정하면 쓸 수 있는 m 은 좁은 범위로 한정된다.'))
    add(h2('역률 보정이란 무엇인가'))
    add(p('커패시터 부하가 걸린 브리지 정류기는 버스 전압을 상용전원 피크 근처에 '
          '유지한다. 그래서 다이오드는 상용전원이 커패시터 전압보다 높은 짧은 '
          '구간에서만 도통한다. 한 주기의 전하가 전부 그 구간에 몰린다.'))
    add(fig('an_pfc_cap',
            '커패시터 입력 정류기: v<sub>C</sub> 는 피크 근처에 머물고, '
            '다이오드는 좁은 구간에서만 도통하며, 그 안의 전류는 높다.'))
    add(p('피크 전류는 같은 전력의 저항 부하에 흐를 전류의 몇 배이고, 그렇게 좁은 펄스 전류는 고조파 성분이 대부분이다.'))
    add(h2('역률과 distortion 은 다르다'))
    add(p('<b>역률</b>은 유효 전력과 피상 전력의 비다. V<sub>ac</sub> 와 I<sub>ac</sub> 는 입력 전압과 전류의 실효값이다.'))
    add(eq(r'PF=\frac{P}{V_{ac}I_{ac}}\;=\;\cos\varphi_{1}\;\times\;\frac{I_{1,rms}}{I_{ac}}'))
    add(p('P 는 평균 전력, I<sub>1,rms</sub> 는 기본파만의 실효값, '
          '&phi;<sub>1</sub> 은 전압에 대한 기본파의 위상이다. <b>변위</b>'
          '(위상)는 모터 부하에서 나빠지고, <b>distortion</b>(실효값 중 고조파의 몫)은 정류기 부하에서 나빠진다. 위의 전류는 위상이 거의 같은데도 역률이 0.6 정도밖에 안 된다.'))
    add(p('THD(total harmonic distortion)는 기본파에 대한 고조파의 비다.'))
    add(eq(r'THD=\frac{\sqrt{I_{ac}^{2}-I_{1,rms}^{2}}}{I_{1,rms}}'
           r'\,,\qquad \frac{I_{1,rms}}{I_{ac}}=\frac{1}{\sqrt{1+THD^{2}}}'))
    add(note('PF 가 0.99 를 넘어도 IEC&nbsp;61000-3-2 를 통과하지 못할 수 있다. 이 규격은 <i>개별</i> 고조파를 A 단위로 제한한다. Class&nbsp;D 는 '
             '규격이 열거한 제품군에만 600&nbsp;W 이하에서 적용되고, 그 위는 Class&nbsp;A 의 '
             '절대 한도다. 등급부터 정할 것.'))
    add(h2('PFC 회로는 어떻게 동작하나'))
    add(p('입력 전류가 입력 전압을 따라가게 하면 컨버터는 상용전원에 저항으로 '
          '보인다. 표준 구현은 <b>브리지 뒤의 boost 컨버터</b>이고, 한 스위칭 '
          '주기 안에서는 상용전원이 일정하다고 볼 만큼 빠르게 스위칭한다.'))
    add(fig('an_pfc_boost',
            'boost PFC: 스위치가 켜진 동안 인덕터에 에너지가 쌓이고, 꺼진 동안 입력과 직렬로 버스에 에너지를 전달한다.'))
    ext(bullets([
        '<b>왜 boost 인가.</b> 영교차 근처에서는 무한한 비로 boost 해야 하는데 '
        'boost 는 그럴 수 있고, 입력 전류가 연속이라 전류 파형을 제어할 수 있다.',
        '<b>안쪽 루프</b>는 인덕터 전류를 빠르게 조절한다.',
        '<b>바깥 루프</b>는 버스 전압을 조절하고 <b>2f<sub>l</sub> 보다 훨씬 느리게</b> 설계한다. 빠른 전압 루프는 버스 리플에 반응해 PFC 가 만들려는 '
        '전류 파형을 망가뜨린다.',
        '<b>multiplier</b> 가 둘을 잇는다: 모양은 상용전원에서, 크기는 출력에서.']))
    add(fig('an_pfc_ccm',
            '연속 도통에서의 결과: 인덕터 전류에 스위칭 리플이 실리고, 그 '
            '평균이 입력 전압을 따라간다.'))
    add(p('전류가 전압을 따라간다는 것은 입력 전력이 sin&sup2;&thinsp;&theta; '
          '를 따라간다는 뜻이다: 주기마다 두 번 0, 피크에서 평균의 두 배. '
          '부하는 일정한 전력을 요구하므로 <b>무언가가 그 차이를 저장해야 '
          '한다</b>.'))
    add(h2('왜 보통 two-stage 인가'))
    add(fig('an_two_stage',
            'two-stage 구성과 각 노드의 파형. 라인 주파수 2배의 리플을 흡수하는 '
            '버퍼는 두 단 사이 400&nbsp;V 에 있다. DC 노드의 리플은 과장했다. '
            'v<sub>ac</sub> 는 순시 상용전원 전압이다.',
            width=CW))
    add(p('버스 커패시터는 두 가지 일을 한다.'))
    ext(bullets([
        '맥동하는 입력 전력과 일정한 출력 전력의 차이를 <b>버퍼</b>한다.',
        'LLC 를 상용전원 파형에서 <b>분리한다</b>. 탱크는 거의 일정한 '
        '입력을 보고 좁은 게인 범위만 커버하면 된다.']))
    add(p('boost 단을 없애면 둘 다 없어진다. 에너지 버퍼는 다른 곳에 두어야 하고, '
          '탱크는 1초에 100 번이나 120 번 0 으로 떨어지는 정류 사인파에서 '
          '동작해야 한다.'))
    add(h1('왜 single-stage 인가, 그 대가는 무엇인가'))
    add(p('%s 절의 표준 설계 순서 중 두 단계는 여기서 쓸 수 없다. 입력이 정류 사인파를 따라 움직이므로 공칭점이 없고, 탱크 하나로 게인 범위를 커버하지 못하므로 '
          '브리지 구성 자체가 바뀐다(%s 절과 %s 장).'
          % (SR('LLC 는 보통 어떻게 설계하나'),
             SR('게인은 제어 변수가 아니라 경계 조건이다'),
             SR('Topology morphing'))))
    add(h2('역률 1 에서 고르지 않게 들어오는 에너지'))
    add(p('역률 1 에서 순시 입력 전력은 sin&sup2;&thinsp;&theta; 를 따라, '
          '라인 주파수의 2배로 0 과 평균의 2배 사이를 오간다.'))
    add(eq(r'p_{in}(t)=V_{ac}I_{ac}\,\left[\,1-\cos(2\omega_l t)\,\right]'))
    add(p('V<sub>ac</sub> 와 I<sub>ac</sub> 는 상용전원 전압과 전류의 실효값, '
          '&omega;<sub>l</sub> = 2&pi;f<sub>l</sub> 이다. '
          '부하는 일정한 전력을 요구하므로, 토폴로지가 무엇이든 그 차이를 '
          '저장했다가 몇 ms 뒤에 되돌려 줘야 한다.'))
    add(p('그림&nbsp;%s 의 패널 2 가 그것이다. 평평한 부하 위로 남는 에너지와 '
          '아래로 모자라는 에너지가 같다. 어딘가의 커패시터가 남는 것을 '
          '흡수했다가 모자랄 때 되돌려 줘야 한다.' % FR('an_pf_chain')))
    add(h2('버퍼를 400 V 에서 출력으로 옮기기'))
    add(p('two-stage 에서는 버퍼가 400&nbsp;V 버스 커패시터다. 여기는 버스가 '
          '없으므로 버퍼가 출력으로 간다. <b>저장할 에너지(J)는 같고 전압만 바뀌는데</b>, 커패시터가 내놓을 수 있는 에너지는 시작 전압과 부하가 허용하는 최저 전압 사이의 몫뿐이다.'))
    add(eq(r'E=\frac{1}{2}C\left(V^{2}-V_{min}^{2}\right)'))
    add(p('hold-up 을 계산해 보면 그 대가가 보인다. 두 구조 모두 같은 T<sub>hold</sub> '
          '동안 같은 에너지를 저장해야 한다. 320&nbsp;V 까지 내려가도 되는 '
          '400&nbsp;V 버스에서는 쓸 수 있는 전압 구간이 400&sup2;&nbsp;&minus;&nbsp;320&sup2; 이다. '
          '수십 V 출력에서는 V<sub>out</sub>&sup2;&nbsp;&minus;&nbsp;'
          'V<sub>o,min</sub>&sup2; 으로 수백 배 작다. 그래서 커패시턴스가 그만큼 '
          '커진다. 이것부터 확인할 것: 뱅크가 제품 케이스에 들어가지 않으면 출력 전압을 '
          '바꿔야 한다. %(ref)s 절이 이 설계의 뱅크를 정하는데, 거기서는 '
          'hold-up 이 아니라 리플이 결정한다.'
          % dict(ref=SR('출력 뱅크 설계 결과'))))
    add(note('<b>맞바꾸는 것.</b> 없어지는 것: 스위치, 인덕터, 다이오드, '
             '400&nbsp;V 전해 커패시터와 그 손실. 새로 생기는 것: 아주 큰 저전압 '
             '커패시터 뱅크, 출력의 2f<sub>l</sub> 리플, 훨씬 넓은 범위를 커버해야 하는 탱크. 좋은 trade-off 인지는 부하가 출력 리플을 얼마나 허용하느냐에 달렸다.'))
    add(h2('부하가 견뎌야 하는 것'))
    add(p('출력에 2f<sub>l</sub> 리플이 그대로 실린다. 루프가 아니라 뱅크와 '
          '부하가 정하는 값이고, 루프로 없앨 수 없다: 없애려 하면 그 '
          'distortion 이 입력 전류로 옮겨 간다(%s 절). <b>허용 리플은 부하가 정하는 값</b>이고 사양에 있어야 한다. 이 설계는 피크-피크 몇 %% 를 '
          '허용한다.'
          % SR('crossover 주파수가 낮아야 하는 이유: 2f<sub>l</sub> 리플')))

    # =============================================================== 3
    add(h1('동작 원리'))
    add(h2('게인은 제어 변수가 아니라 경계 조건이다'))
    add(p('two-stage LLC 에서는 컨트롤러가 게인을 지령한다. 여기서는 그럴 수 '
          '없다. <b>입력과 출력이 모두 전압원</b>이기 때문이다: 출력은 mF 급 '
          '커패시터 뱅크이고 입력은 정류된 상용전원이다. 순시 게인은 외부에서 정해진다.'))
    add(eq(r'M(\theta)=\frac{n\,V_{o,eff}}{V_{drive}(\theta)}'
           r'=\frac{2\,n\,V_{o,eff}}{\sqrt{2}\,V_{ac,eq}\,\sin\theta}', key='Mreq'))
    add(p('&theta; 는 라인 위상, V<sub>drive</sub> 는 브리지가 탱크에 인가하는 진폭이다: 풀브리지에서는 정류된 상용전원, 하프브리지에서는 그 '
          '절반. V<sub>ac,eq</sub> 는 같은 구동을 하프브리지로 얻는 데 필요한 상용전원 전압으로, '
          '풀브리지에서는 상용전원의 2 배, 하프브리지에서는 상용전원 그대로다. '
          'V<sub>o,eff</sub> 는 출력에 정류기 강하를 더한 것이다(식&nbsp;%s). '
          '두 전압 모두 외부에서 고정되므로 그 비는 순간마다 정해져 '
          '있다.' % ER('Vrefl')))
    add(p('따라서 주파수를 바꾸면 달라지는 것은 <b>Q</b>, 즉 전력이다. '
          '<b>주파수는 전압 지령이 아니라 전력 지령이다.</b>'))
    add(h2('서로 상쇄하는 두 발산'))
    add(p('영교차 근처에서 요구 게인은 1/sin&thinsp;&theta; 로 한없이 오른다. '
          '그래도 컨버터가 동작하는 이유는 같은 순간 부하가 사라지기 때문이다.'))
    add(eq(r'Q(\theta)=Q_{pk}\,\sin^{2}\theta', key='Qtheta'))
    add(p('Q<sub>pk</sub> 는 라인 피크에서의 값이다. 그리고 No load LLC 는 f<sub>o</sub> 에서 무한한 게인을 갖는다. 두 '
          '무한대가 상쇄하고, 상용전원이 0 으로 가는 동안 동작점은 '
          'f<sub>o</sub> 쪽으로 내려간다(%s 절). <b>f<sub>o</sub> 가 설계 '
          '전체의 주파수 하한이다.</b> 오실레이터 클램프가 그 아래에 있으면 '
          '하드웨어가 파손된다.'
          % SR('이 설계는 공진의 어느 쪽에서 도는가')))
    add(h2('주파수 변조가 곧 역률 보정이다'))
    add(p('그림&nbsp;%s 라인 반주기 동안의 제어 법칙을 단계별로 보여 준다. 앞의 세 '
          '단계는 두 전압원이 강제하는 것이고, 컨트롤러가 하는 일은 넷째뿐이다.'
          % _nj(FR('an_pf_chain'), '은', '는')))
    add(fig('an_pf_chain',
            '라인 반주기에 걸쳐 역률이 보정되는 과정. <b>1</b>&nbsp;역률 1: '
            '전류가 정류된 상용전원과 같은 모양이다. <b>2</b>&nbsp;입력 전력은 sin&sup2; 형태이고 부하는 일정한 P<sub>out</sub> 을 소비한다. '
            '색칠한 면적이 뱅크가 버퍼하는 몫이다. <b>3</b>&nbsp;탱크에 요구되는 게인과 부하가 정해지고, 둘 다 영교차에서 발산한다. <b>4</b>&nbsp;스위칭 '
            '주파수가 유일한 자유 변수이고, 이 프로파일이 1~3 을 만족시킨다. '
            '정규화한 그림이고, 숫자는 %s 절에 있다.'
            % SR('이 설계는 공진의 어느 쪽에서 도는가'), width=CW))
    add(p('역률 1 '
          '은 순시 전력을 2&nbsp;P<sub>in</sub>&thinsp;sin&sup2;&thinsp;&theta; '
          '로 고정하고, 그것이 매 순간 게인(식&nbsp;%(m)s)과 부하'
          '(식&nbsp;%(q)s)를 함께 고정한다. 컨트롤러가 손댈 수 있는 변수는 하나뿐이다. 전류 루프도, 정류 기준파에 대한 multiplier 도 없다: <b>주파수 '
          '프로파일 f<sub>sw</sub>(&theta;) 가 곧 역률 보정이다.</b>'
          % dict(m=ER('Mreq'), q=ER('Qtheta'))))
    ext(tbl('반주기의 여섯 순간. 그림&nbsp;%s 같이 정규화했다. 삼각함수뿐이고 '
            '부품값은 하나도 안 들어간다.' % _nj(FR('an_pf_chain'), '과', '와'),
            [['라인 위상', 'sin&thinsp;&theta;',
              '순시 전력 p/P<sub>in</sub>',
              '요구 게인 M<sub>req</sub>/M<sub>pk</sub>',
              '부하 Q/Q<sub>pk</sub>'],
             ['&theta; = 90&deg;, 피크', '1.000', '2.000', '1.000',
              '1.000'],
             ['&theta; = 60&deg;', '0.866', '1.500', '1.155', '0.750'],
             ['&theta; = 45&deg;', '0.707', '1.000', '1.414', '0.500'],
             ['&theta; = 30&deg;', '0.500', '0.500', '2.000', '0.250'],
             ['&theta; = 10&deg;', '0.174', '0.060', '5.759', '0.030'],
             ['&theta; &rarr; 0', '0', '0', '&infin;', '0']],
            widths=[CW * 0.22, CW * 0.13, CW * 0.22, CW * 0.23, CW * 0.20],
            key='pfwalk', split=True))
    add(p('마지막 두 행에서 게인 요구는 발산하지만, 탱크가 낼 수 있는 게인도 함께 발산한다: No load 탱크는 f<sub>o</sub> 에서 무한한 게인을 갖는다. '
          '주파수는 f<sub>o</sub> 쪽으로 내려가고 전류는 전압과 함께 0 으로 '
          '간다.'))
    add(p('컨트롤러에는 시간 척도가 다른 신호가 둘 있다.'))
    ext(bullets([
        '<b>FB 는 크기를 정한다.</b> error amp 출력을 옵토커플러로 '
        '받아 입력 <i>전력</i>을 지령한다(%s 절). 이 루프의 crossover 는 라인 주파수보다 훨씬 낮으므로 한 반주기 안에서는 상수다: 패널 '
        '4 프로파일의 <i>높이</i>.' % SR('피드백 핀은 전력 지령이다'),
        '<b>HVSU 는 라인 위상을 알려 준다.</b> 기동 핀이 입력 전압 sensing 도 '
        '겸하므로 컨트롤러는 분압기 없이 순시 정류 전압을 안다. 이것이 빠른 신호이고 프로파일의 <i>모양</i>을 정한다.',
        '<b>내부의 PFC·THD 블록이 둘을 합쳐</b> 오실레이터를 제어하는 유일한 전류 I<sub>EA</sub> 를 만든다(식&nbsp;%s).' % ER('Tsw')]))
    add(note('<b>초안 데이터시트는 그 블록의 제어 법칙을 공개하지 않는다.</b> 그래서 이 문서는 입력 전류가 전압을 따라가기 위해 <i>필요한</i> 프로파일을 탱크 특성에서 계산한다. 첫 보드에서 f<sub>sw</sub>(&theta;) '
             '를 측정해 이 블록의 실제 동작을 확인한다.'))

    add(note('<b>영교차 dead zone.</b> &theta;&nbsp;= 0 바로 근처에서 프로파일은 '
             'f<sub>Min</sub> 아래의 주파수를 요구하고, 컨버터는 상용전원 전압이 다시 올라올 때까지 전류를 끌지 않는다. 이것은 구조적인 현상이고 '
             '3차 고조파 distortion 으로 나타난다. 다른 THD 원인은 전압 '
             '루프다(%s 절).' % SR('crossover 주파수가 낮아야 하는 이유: 2f<sub>l</sub> 리플')))
    add(h2('근 탐색 없이 프로파일 풀기'))
    add(p('프로파일에 수치 근 탐색은 필요 없다. M<sub>req</sub> = '
          'M<sub>pk</sub>/sin&thinsp;&theta;, Q = Q<sub>pk</sub>sin&sup2;'
          '&thinsp;&theta;, x = 1/f<sub>n</sub>&sup2; 으로 두면 게인 식은 x 의 '
          '3차식이다.'))
    add(eq(r'\lambda^{2}x^{3}+(q-2\lambda(1+\lambda))x^{2}'
           r'+((1+\lambda)^{2}-2q-\frac{u}{M_{pk}^{2}})x+q=0,'
           r'\qquad u=\sin^{2}\theta,\;\; q=Q_{pk}^{2}u^{2}', key='cubic'))
    add(p('근 하나는 음수다(3차식은 x&nbsp;= 0 에서 +q 이고, '
          'x&nbsp;&rarr;&nbsp;&minus;&infin; 에서 &minus;&infin; 로 간다). '
          '나머지 둘은 같은 곡선의 capacitive 교차와 inductive '
          '교차이고, inductive 쪽이 <b>가운데</b> 근이다. 주파수가 오르면 x 가 '
          '내려가기 때문이다. Cardano 의 삼각함수 형에서는 언제나 k&nbsp;= 1 인 근이다. 양의 근이 없으면 수치 실패가 아니라 %s 절의 해 없음이다. '
          '격자 탐색을 하려면 f<sub>n</sub> 의 상한도 필요한데, 모핑 코너 대신 '
          'AC 최대 전압에서 잡은 상한은 실제 동작점을 놓친다.'
          % SR('&lambda; 의 반대쪽 한계, 그리고 해가 없는 경우')))
    add(h2('single-stage 컨버터의 게인 차트 읽는 법'))
    add(p('그림&nbsp;%(f)s 의 차트가 표준 그림이다: 곡선군 하나, 요구 게인 선 하나, 교차점 하나. single-stage 컨버터는 같은 방식으로 그리되 '
          '<b>다르게 읽는다</b>. 그림&nbsp;%(c)s 에 둘을 나란히 놓았다.'
          % dict(f=FR('f02_two_resonances'), c=FR('an_gain_compare'))))
    add(fig('an_gain_compare',
            '일반 LLC 차트와 single-stage 차트: 같은 축, 같은 식, 읽는 법은 다르다. '
            '왼쪽은 곡선군의 매개변수가 <b>부하</b>이고 컨버터는 교차점 하나에 있다. '
            '오른쪽은 곡선군의 매개변수가 <b>라인 위상</b>이고, 곡선마다 같은 색의 요구 '
            '게인 선이 있으며, 컨버터는 라인 주기마다 두 번 이 곡선군을 오간다. '
            '오른쪽 패널은 라인 피크에서 M&nbsp;=&nbsp;1 이 필요한 입력(M<sub>pk</sub> = 1)으로 그렸다. 입력이 낮으면 점선이 모두 같은 비율로 올라간다.', width=CW))
    add(p('여섯 가지가 다르다.'))
    ext(bullets([
        '<b>곡선군의 매개변수는 부하가 아니라 라인 위상이다.</b> 부하는 '
        'Full load 로 고정이고 곡선은 &theta;&nbsp;= 90&deg;, 60&deg;, '
        '45&deg;&thinsp;&hellip; 다. Q&nbsp;= Q<sub>pk</sub>sin&sup2;'
        '&thinsp;&theta; 가 상용전원과 함께 내려가기 때문이다.',
        '<b>동작점이 1초에 100 또는 120 번 움직인다.</b> 검사할 동작점이 하나가 아니다. 경로 전체를 검사한다.',
        '<b>요구 게인 선이 여러 개다.</b> M<sub>req</sub>(&theta;) = '
        'M<sub>pk</sub>/sin&thinsp;&theta;, 위상마다 선 하나, 영교차 쪽으로 '
        '한없이 오른다. <b>각 곡선은 자기 선과만 비교한다.</b>',
        '<b>선이 오를수록 곡선도 높아진다.</b> sin&thinsp;&theta; 가 반이 되면 '
        '요구는 두 배가 되지만 Q 는 1/4 이 되어 곡선은 두 배보다 훨씬 높아진다. '
        '여유는 영교차 쪽으로 갈수록 커진다.',
        '<b>capacitive 경계 M<sub>Z</sub> 를 그린다.</b> arg Z<sub>in</sub> = 0 '
        '인 곳(%(b)s 절)으로, 각 곡선의 피크보다 조금 오른쪽에 있고, 모든 '
        '교차점은 그보다 <b>오른쪽</b>에 있어야 한다. 모든 위상에서 지켜야 '
        '하므로 한 곡선으로 그린다.'
        % dict(b=SR('두 경계는 같은 경계가 아니다')),
        '<b>M<sub>&infin;</sub> = 1/(1+&lambda;) 가 차트에 있다.</b> 일반 LLC 는 그렇게 작은 게인이 필요 없지만, 높은 입력 전압의 single-stage '
        '컨버터는 필요하다. 이 선 아래에는 <b>No load 에서 어느 주파수에도 해가 '
        '없고</b> '
        '버스트 모드로 넘어간다(%(l)s 절).'
        % dict(l=SR('&lambda; 의 반대쪽 한계, 그리고 해가 없는 경우'))]))
    add(note('<b>이 차트에서 흔히 하는 실수:</b> 가장 높은 곡선을 가장 낮은 선과 '
             '비교하는 것. 그런 동작점은 없다. &theta; 가 곡선<i>과</i> 선을 '
             '함께 정하므로 같은 색끼리 비교해야 뜻이 있다.'))
    add(p('최저 등가 입력에서 차트가 답하는 질문은 "탱크가 그 게인을 내면서 '
          'inductive 로 남는가" 이다. 최고 등가 입력에서는 "주파수가 얼마나 '
          '올라가고, Light load 에 해가 있는가" 이다. 그래서 %s 절은 여섯 입력 '
          '전압 전부에서 그린다.' % SR('이 설계의 게인 차트')))
    add(h2('피드백 핀은 전력 지령이다'))
    add(p('버스트 모드 식과 블록도의 multiplier 를 합치면 피드백 전압 V<sub>FB</sub> 의 의미가 나온다.'))
    add(eq(r'V_{FB}\;=\;V_{os}+\frac{2K_{HV}}{K_{M}K_{FF}}\,R_{CS}\,P_{in,LLC}'
           r'\;=\;0.5\,\mathrm{V}+0.167\,'
           r'\frac{\mathrm{V}}{\Omega\cdot\mathrm{W}}\,R_{CS}\,P_{in,LLC}', key='VFB'))
    add(p('P<sub>in,LLC</sub> 는 브리지가 끌어가는 전력이다. R<sub>CS</sub> 가 브리지 귀환 경로에 있으므로 '
          '컨트롤러가 검출하는 것이 이 전력이다. V<sub>os</sub> 는 전력 지령이 없을 때 핀이 머무는 0.5&nbsp;V 다. '
          'K<sub>HV</sub>, K<sub>M</sub>, K<sub>FF</sub> 는 블록도의 입력 전압 sensing, multiplier, 피드포워드 게인이다. 피드백 폭 2.8&nbsp;V 에서 '
          '2.8/0.167 = 16.8&nbsp;&Omega;&middot;W, 데이터시트의 최대 전력 '
          '규칙이 나온다. <b>최대 전력, 버스트 진입, Overload 검출이 전부 '
          'R<sub>CS</sub> 하나로 정해진다.</b> 옵토커플러 루프는 입력 '
          '전력을 지령하고, 내부 루프가 그것을 라인 주기에 걸쳐 '
          'sin&sup2;&thinsp;&theta; 로 분배한다.'))
    add(note('전류 sense 핀에 필터도 직렬 저항도 허용되지 않는 이유가 이것이다: '
             '전력 법칙과 과전류 threshold 가 같은 핀을 읽는다.'))
    add(h2('이 컨버터는 공진의 어느 쪽에서 도는가'))
    add(p('single-stage 컨버터는 한쪽을 고르지 않는다. 등가 입력이 정류 사인파를 따르고 요구 게인도 그것을 따르므로, 동작점은 한 라인 주기 안에서 '
          'f<sub>r</sub> 을 넘었다가 돌아올 수 있다. 넘는지, 얼마나 오래 넘는지는 '
          '상용전원 전압에 달렸고, 입력이 낮으면 주기 내내 f<sub>r</sub> 아래에 머물 수도 있다. %s 절이 여섯 입력 전압에서의 프로파일을 '
          '보인다.' % SR('이 설계는 공진의 어느 쪽에서 도는가')))
    add(note('<b>양쪽을 모두 고려해 설계해야 한다.</b> boost 쪽이 게인 요구와 ZVS 여유를 '
             '정한다. buck 쪽이 최고 주파수를 정하고 2차가 ZCS 를 잃으므로, 정류기의 바디 다이오드와 SR 데드타임이 여기서 문제가 '
             '된다.'))
    add(h2('&lambda; 가 0.5 근처여야 하는 이유'))
    add(p('고전적인 LLC 는 m&nbsp;=&nbsp;(L<sub>r</sub>+L<sub>m</sub>)/L<sub>r</sub> 을 5 ~ 10, '
          '즉 &lambda; 를 0.11 ~ 0.25 로 쓴다. single-stage 컨버터는 영교차 '
          '근처에서 아주 높은 게인이 필요한데, 피크 게인은 &lambda; 가 '
          '작아질수록 떨어진다. ST 의 평가 보드는 &lambda;&nbsp;=&nbsp;0.500 '
          '으로 동작하고 이 설계도 그 근처로 나온다(%s 절): 이 값은 토폴로지 특성에서 나온다.' % SR('단계별 계산')))
    add(p('대가는 순환 전류다. L<sub>m</sub> 이 작으면 자화 전류가 크고, 그 '
          '도통 손실은 부하와 무관하다. <b>single-stage PFC LLC 는 two-stage '
          'LLC 보다 효율이 낮다. 구조상 그렇다.</b>'))
    add(h2('f<sub>sw,max</sub> 는 검사값이 아니라 설계 입력이다'))
    add(p('&lambda; 후보 넷 중 둘은 사양의 최대 스위칭 주파수를 분모에 '
          '갖는다.'))
    add(eq(r'\lambda_{2}=\frac{\lambda_{1}}'
           r'{1-\left(\frac{f_r}{f_{sw,max}}\right)^{2}}'
           r'\qquad\qquad'
           r'\lambda_{TD}=\frac{\lambda_{1}}'
           r'{1-\frac{\pi^{2}}{8}\left(\frac{f_r}{f_{sw,max}}\right)^{2}}', key='lam'))
    add(p('&lambda;<sub>1</sub> 은 단순한 최소 게인 조건이다. '
          '&lambda;<sub>2</sub> 와 &lambda;<sub>TD</sub> 는 주파수 상한을 반영한다: 탱크는 주파수 상한에 닿기 <i>전에</i> 최저 요구 게인에 '
          '닿아야 한다. 흔히 쓰는 f<sub>sw,max</sub> = 1.5&nbsp;f<sub>r</sub> '
          '이면 제곱비가 0.44 라 <b>f<sub>sw,max</sub> 로 넣은 값이 요구 '
          '&lambda; 를 대략 두 배로 만든다</b>. f<sub>r</sub> 근처로 잡으면 '
          '요구 &lambda; 는 무한대로 간다. 네 번째 후보 &lambda;<sub>3</sub> 은 '
          '사양의 최소 스위칭 주파수에서 나온다. 이 컨버터에서는 작아서 결정에 관여하지 않는다.'))
    add(note('흔히 쓰는 1.5&nbsp;&times;&nbsp;f<sub>r</sub> 은 물리적 한계가 아니라 설계자의 <b>선택</b>이고, 탱크 계산의 입력이다: 여기에 넣은 어림값이 '
             'L<sub>m</sub> 을 바꾼다.'))
    add(p('오실레이터 상한 f<sub>Max</sub> 는 다르다. 그것은 R<sub>T</sub>, '
          'C<sub>T</sub>, I<sub>EA,max</sub>, idle 시간이 고정하는 진짜 한계이고, 사후에 '
          'k<sub>ceil</sub> 로 검사한다(%s 절). 하나는 탱크를 정하고, 다른 '
          '하나는 오실레이터가 그 탱크를 감당하는지 확인한다.'
          % SR('판정 여유란 무엇인가')))
    add(h2('&lambda; 의 반대쪽 한계, 그리고 해가 없는 경우'))
    add(p('&lambda; 의 상한은 최고 등가 입력·No load 에서의 최저 요구 게인에서 '
          '온다. No load 게인은 한없이 떨어지지 않는다. 주파수를 올려도 '
          '점근선까지만 내려간다.'))
    add(eq(r'M_{\infty}\;=\;\lim_{f\to\infty}M_{OL}'
           r'\;=\;\frac{1}{1+\lambda}', key='Minf'))
    add(p('M<sub>OL</sub> 은 No load(Q = 0, 출력 Open)의 게인 곡선이다.'))
    add(p('<b>요구 최소 게인이 M<sub>&infin;</sub> 아래이면 어느 주파수도 '
          '만족시키지 못한다.</b> 그 주파수를 구하는 스프레드시트는 오류를 내는데, 수식이 깨진 것처럼 보이지만 실제로는 해가 없는 것이다. 탱크가 점근선 위인지 아래인지는 1 %% 차이이고, Full load '
          '검사로는 보이지 않는다. %s 절에 이 설계의 결과가 있다.'
          % SR('단계별 계산')))
    add(note('해가 없는 것이 실패는 아니다: 높은 입력 전압의 No load 는 '
             '<b>버스트 모드</b>의 몫이다. 하지만 어느 후보 권선비가 No load 에서 '
             '주파수만으로 조절할 수 있는지를 이것이 판별한다.'))

    # =============================================================== 4
    add(h1('Topology morphing'))
    add(p('공진 탱크의 실용적인 게인 범위는 Full load 에서 대략 1.5:1 이다. '
          '유니버설 상용전원은 %(rm).2f:1 을 요구한다. 탱크 하나로는 ZVS 를 지키며 '
          '그 범위를 커버하지 못하므로, L6790A 는 브리지 구성을 바꾼다.' % dict(V, rm=V['Vacmax'] / V['Vacmin'], rt=V['Veqhi'] / V['Veqlo'], rt2=V['Veqhi2'] / V['Veqlo2'])))
    add(p('상용전원 피크가 235&nbsp;V 아래이면 <b>풀브리지</b>로 돌고, 탱크를 '
          '레일의 두 배로 구동한다. 245&nbsp;V<sub>pk</sub> 위에서는 '
          '<b>하프브리지</b>다. 그래서 탱크가 보는 것은 등가 %(Veqlo).1f ~ '
          '%(Veqhi).1f&nbsp;Vac, %(rt).2f:1 이고, 탱크 하나로 커버할 수 있다.' % dict(V, rm=V['Vacmax'] / V['Vacmin'], rt=V['Veqhi'] / V['Veqlo'], rt2=V['Veqhi2'] / V['Veqlo2'])))
    add(fig('f13_morphing',
            '모핑이 %.2f:1 의 상용전원 범위를 탱크에서 %.2f:1 로 줄인다. 최악 '
            '코너는 상용전원 범위의 양 끝이 아니라 모핑 경계다. 상용전원이 내려가는 '
            '경우를 그렸고, 방향에 따라 모드가 달라지는 띠는 그림&nbsp;%s 에 있다.'
            % (V['Vacmax'] / V['Vacmin'], V['Veqhi'] / V['Veqlo'],
               FR('f18_morph_levels'))))
    add(h2('풀브리지'))
    add(p('대각선 쌍이 함께 도통하므로 구동은 진폭 V<sub>in</sub>, 기본파 '
          '(4/&pi;)&thinsp;V<sub>in</sub> 의 사각파다. 네 소자가 모두 '
          '스위칭한다.'))
    add(fig('f15_bridge_fb',
            '풀브리지: 반주기마다의 도통 경로와 그 결과인 탱크 구동.'))
    add(h2('하프브리지'))
    add(p('LOUT2 가 high 로 고정된다: S3 는 켜지지 않고 S4 는 꺼지지 않으므로 '
          '브리지 출력은 0 과 V<sub>in</sub> 사이를 오간다. C<sub>r</sub> 이 '
          'DC 성분 V<sub>in</sub>/2 를 막고, 탱크는 &plusmn;V<sub>in</sub>/2, '
          '기본파 (2/&pi;)&thinsp;V<sub>in</sub> 을 본다. 추가 부품은 필요 없다.'))
    add(fig('f16_bridge_hb',
            '하프브리지: 레그 2 가 스위칭을 멈추고, C<sub>r</sub> 이 비대칭 '
            '구동이 만드는 DC 를 없앤다.'))
    add(note('<b>고정된 소자가 가장 뜨겁다.</b> S4 는 스위칭하지 않지만 탱크 '
             '전류 전부를 계속 흘리고, 이 설계에서 가장 뜨거운 단일 소자다'
             '(%s 절).' % SR('손실 분배')))
    add(h2('컨트롤러는 무엇을 하나'))
    add(p('모드 사이에 바뀌는 것은 2번 레그뿐이다: HOUT2 는 멈춰 low 로, LOUT2 는 멈춰 high 로 '
          '고정된다. threshold 는 <b>IC 안에 '
          '고정</b>돼 있다. R<sub>CFG</sub> 는 모핑을 활성화하고 브라운아웃 threshold 를 '
          '정할 뿐이다.'))
    add(fig('f17_morph_gates',
            '두 모드에서의 브리지 구동 신호 넷. LOUT2 를 high, HOUT2 를 low 로 고정하는 것이 전부다.'))
    add(h2('히스테리시스 띠와 실제 동작 범위'))
    add(p('올라갈 때는 245&nbsp;V<sub>pk</sub> 에서 하프브리지로 전환하고, '
          '내려올 때는 235&nbsp;V<sub>pk</sub> 에서 풀브리지로 돌아온다. '
          '히스테리시스가 잦은 모드 전환은 막지만, <b>둘 사이에서는 모드가 전압이 아니라 이전 상태에 따라 달라진다</b>.'))
    add(p('각 threshold 를 그 모드가 보장되는 쪽에서 잡으면 %(Veqlo).1f ~ '
          '%(Veqhi).1f&nbsp;Vac (%(rt).2f:1) 이다. 히스테리시스 띠까지 포함하면 <b>%(Veqlo2).1f ~ '
          '%(Veqhi2).1f&nbsp;Vac (%(rt2).2f:1)</b> 이다. 이 설계는 넓은 범위에서도 '
          '통과한다. 사양을 조일 때 좁은 쪽 숫자를 쓰지 말 것.' % dict(V, rm=V['Vacmax'] / V['Vacmin'], rt=V['Veqhi'] / V['Veqlo'], rt2=V['Veqhi2'] / V['Veqlo2'])))
    add(fig('f18_morph_levels',
            '각 모드가 적용되는 곳. 띠 안에서는 입력 전압이 올라가는 중인지 내려가는 중인지에 따라 모드가 달라진다. '
            'V<sub>BO</sub> 는 R<sub>CFG</sub> 가 정하는 브라운아웃 threshold 다(%s 절).'
            % SR('브라운아웃과 브리지 구성: CFG 핀')))
    add(note('공칭 상용전원 전압 중 166 ~ 173&nbsp;Vrms 에 드는 것은 없다. 이 구간은 sag 가 왔을 때, 그리고 프로그래머블 AC 소스를 쓴 시험이나 dip·surge 시험에서 나타난다. 램프가 아니라 '
             'threshold 를 가로지르는 <b>스텝</b>으로 시험할 것.'))
    add(note('<b>전환 시 과도 응답.</b> threshold 를 넘으면 한 라인 주기 안에 구동이 2:1 로 '
             '바뀐다. 루프는 수십 Hz 에서 교차하므로 바로 따라가지 못한다. 루프가 '
             '회복할 때까지 출력이 내려가거나(상용전원이 올라갈 때) '
             '오버슈트한다(내려올 때). '
             '내려가는 쪽은 이미 만족한 hold-up 보다 덜 심하므로 '
             'C<sub>out</sub> 을 키울 이유는 아니다. 둘 다 시간 영역에서 '
             '검사하지는 않았다.'))

    # =============================================================== 5
    # 스윕이 ZVS_WORST 를 채운다 - 설계 예제의 요약표가 격자보다 먼저 읽는다
    _zvs_grid(A, head=('부하', '경계'))
    add(h1('설계 절차'))
    add(fig('bom_power_stage',
            '전력단. 브리지 정류기가 레그 쌍에 바로 이어진다: 벌크 커패시터도 '
            'boost 단도 없다. 2차는 센터탭(Solution&nbsp;1)과 풀브리지'
            '(Solution&nbsp;2)로 그렸다. ST L6790A 설계 스프레드시트의 '
            '도면이다.', width=CW))
    add(p('2차 정류 방식부터 정한다. 그것이 N<sub>rect</sub> 를 정하고, N<sub>rect</sub> '
          '가 반사 전압을 정한다. 센터탭은 도통 경로에 소자가 하나, '
          '풀브리지는 둘이므로, 낮은 출력 전압에서 센터탭은 소자당 역전압 두 '
          '배를 대가로 정류기 도통 손실을 반으로 줄인다. 이 설계는 센터탭이다. '
          '아래 단계는 서로 의존하므로 순서대로 간다.'))
    add(h2('사양'))
    add(p('사양 전체는 %(ref)s 절에 있다. 모든 단계에 조건 둘이 붙는다: '
          '<b>최악의 라인 주파수는 최저치</b>이고, <b>hold-up 은 리플 골에서 '
          '규정</b>한다.' % dict(V, ref=SR('사양과 값의 종류'))))
    add(h2('등가 입력 범위'))
    add(p('모핑이 있으므로 탱크는 90 ~ %(Vacmax).0f&nbsp;Vac 를 보지 않는다. '
          '브리지 모드가 정하는 <b>등가</b> 입력을 본다.' % V))
    # matplotlib mathtext 에는 cases 환경도 \text 도 없다
    add(eq(r'V_{ac,eq}=2\,V_{ac}\;\;\mathrm{(full\;bridge)}'
           r'\;\;\;\;\;\;\;\;V_{ac,eq}=V_{ac}\;\;\mathrm{(half\;bridge)}', key='Veq'))
    add(p('하프브리지 경계(245&nbsp;V<sub>pk</sub>)에서 탱크는 '
          '%(Veqlo).1f&nbsp;Vac 를 보고, 풀브리지 경계(235&nbsp;V<sub>pk</sub>)'
          '에서는 %(Veqhi).1f&nbsp;Vac 를 본다. <b>이 두 경계가 설계 코너다</b>: '
          '낮은 쪽은 게인과 ZVS, 높은 쪽은 스위칭 주파수. 실제 상용전원 전압도 같은 축에 놓인다. 풀브리지의 90 과 110&nbsp;Vac 는 '
          '등가 180 과 220&nbsp;Vac 가 된다. 하프브리지의 230 과 264&nbsp;Vac '
          '는 230 과 264 그대로다. 넷 다 두 경계 안에 있다. 이 문서는 여섯 조건 전부의 결과를 제시한다.' % V))
    add(h2('권선비와 반사 전압'))
    add(p('권선비는 언제나 유효 출력 전압에 곱해진 꼴로만 나오므로, 중요한 '
          '것은 <b>반사 전압</b> V<sub>refl</sub> 이다.'))
    add(eq(r'V_{refl}=n\,V_{o,eff}=n\left(V_{out}+N_{rect}V_{f}\right)', key='Vrefl'))
    add(p('V<sub>f</sub> 는 정류기 하나의 순방향 전압 강하, N<sub>rect</sub> 는 도통 경로의 정류기 수다. '
          '<b>n</b> 은 게인 식의 모델 비이고, <b>n<sub>T</sub></b> 는 누설을 '
          'L<sub>r</sub> 에 포함시킨 실제 감는 비다. &lambda;&nbsp;&asymp;'
          '&nbsp;0.5 에서 둘은 20&nbsp;%% 넘게 다르므로(%(ref)s 절) 도면에는 '
          '턴수와 함께 Open·Short 인덕턴스를 적어야 한다.'
          % dict(ref=SR('두 개의 비, 두 개의 인덕턴스'))))
    add(h2('공진 탱크'))
    add(p('센터탭 2차의 등가 AC 부하 저항을 라인 피크에서 평가하면 다음과 '
          '같다.'))
    add(eq(r'R_{ac}=\frac{4}{\pi^{2}}\,'
           r'\frac{n^{2}V_{o,eff}^{2}}{P_{in,LLC}}', key='Rac'))
    add(p('P<sub>in,LLC</sub> 는 공진단으로 들어가는 전력이다. 일반적인 LLC 식은 8/&pi;&sup2; 계수와 two-stage 컨버터의 출력 전력을 쓴다. 여기서 입력 전력은 2P&thinsp;sin&sup2;&thinsp;&theta; 다. 그래서 '
          'R<sub>ac</sub> 는 p = 2P 인 라인 피크에 고정하고, 8 은 4 가 된다. '
          'Q 는 피크에서의 품질계수다. 다른 위상에서는 Q(&theta;) = '
          'Q<sub>pk</sub>sin&sup2;&thinsp;&theta; 다. two-stage 값을 쓰면 부하를 '
          '절반으로 잘못 본다.'))
    add(p('낮은 코너의 게인 요구와 ZVS 요구가 품질계수를 Q<sub>ZVS</sub> 로 '
          '제한한다. R<sub>ac</sub>Q<sub>ZVS</sub> 가 탱크를 정하는 '
          '임피던스다: 식&nbsp;%(q)s %(e)s C<sub>r</sub> 을 고정하고, '
          'C<sub>r</sub> 과 f<sub>r</sub> 이 L<sub>r</sub> 을 고정한다. 계산보다 다음 규칙 셋이 중요하다.'
          % dict(q=_nj(ER('Qdef'), '과', '와'), e=_nj(ER('fr'), '으로', '로'))))
    ext(bullets([
        '계산된 세 값이 하나의 탱크를 이루는 것은 아니다. L<sub>r</sub> 은 계산값이 아니라 '
        '<b>선정한</b> C<sub>r</sub> 에서 나온다. 계산된 L<sub>m</sub> 은 <i>높은 코너의 '
        'No load</i> 가 요구하는 &lambda; 로 L<sub>r</sub> 을 나눈 값이다. 설계는 그 '
        '조건을 알고도 만족시키지 않을 수 있으므로(%s 절) 그 L<sub>m</sub> 에 맞춰 반올림하지 않는다.'
        % SR('&lambda; 의 반대쪽 한계, 그리고 해가 없는 경우'),
        '<b>L<sub>m</sub> 을 크게 잡으면 ZVS 여유가 준다.</b> &lambda; 와, '
        '노드를 스윙시키는 자화 전류가 함께 줄기 때문이다. 반대로 C<sub>r</sub> 을 계산값보다 크게, L<sub>m</sub> 을 작게 잡으면 여유가 는다.',
        '<b>Q<sub>ZVS</sub> 한도 아래에 머물 것.</b> 그 간격이 ZVS 여유의 '
        '대부분이다. L<sub>m</sub> 은 n 과 함께 골라 n<sub>T</sub>&nbsp;=&nbsp;'
        'n&radic;(1+&lambda;<sub>act</sub>) 가 감을 수 있는 비가 되게 한다.']))
    add(h2('ZVS 검증'))
    add(p('대부분의 가이드에 있는 ZVS 닫힌 식은 설계 Q<sub>ZVS</sub> 에서 피팅한 근사식이지, 컨버터가 실제로 도는 Q 에서의 값이 아니다. 전체 스윕과 '
          '비교하면 수십 % 틀리고, 어느 쪽으로 틀릴지 보장하는 것이 없다. 낙관적인 쪽이 위험한 쪽이다.'))
    add(note('그 근사식은 &lambda; 를 첨자 없이 쓰고 <i>설계</i> &lambda; 를 '
             '뜻한다. &lambda;<sub>act</sub> 로 읽으면 inductive 영역 한가운데의 '
             '탱크에서도 위상이 <b>음수</b>로 나올 수 있다. 스윕에는 그런 '
             '모호함이 없다.'))
    add(p('<b>선정한</b> 탱크로 &theta;, 입력 전압, 부하를 스윕해 최솟값을 '
          '잡는다. %(ref)s 절이 이 설계에 대해 그렇게 했고, 최악점은 예상 밖의 곳에 있다.' % dict(ref=SR('운전 영역 전체의 ZVS'))))
    add(h2('컨버터는 공진의 어느 쪽에서 도는가'))
    add(p('f<sub>r</sub> 아래에서 2차 전류는 온전한 공진 사인 반파 뒤에 프리휠링 '
          '구간이 오고, 도통비 d = f<sub>sw</sub>/f<sub>r</sub> 은 1 보다 '
          '작다. f<sub>r</sub> 위에서는 사인 반파가 중간에 잘리고 d 가 1 에 '
          '고정된다. 정격과 손실의 바탕이 되는 실효값에는 d 가 들어 있다.'))
    add(p('<b>어느 쪽인지는 권선비가 정한다.</b> M<sub>req</sub> = '
          '2n&thinsp;V<sub>o,eff</sub>/(&radic;2&nbsp;V<sub>ac,eq</sub>) 이므로 n '
          '이 크면 더 큰 게인을 요구하고 공진 주파수보다 더 아래에서 동작한다. 같은 탱크의 '
          '두 후보 트랜스포머가 같은 상용전원 전압에서 f<sub>r</sub> 의 반대쪽에 '
          '있을 수 있다.'))
    add(note('트랜스포머를 발주하기 전에 이것부터 정할 것: below 에서는 '
             '정류기가 전류 0 에서 꺼지고, above 에서는 그렇지 않다.'))
    add(h2('라인 사이클에 걸친 전류'))
    add(p('정격은 최악의 스위칭 사이클에서, 손실은 라인 사이클 실효값에서 '
          '온다. 규칙 둘이 더 있다.'))
    ext(bullets([
        '1차 소자와 sense 저항은 <b>합성</b> 탱크 전류를 본다: 반사 부하 전류와 자화 전류의 합. 그 피크는 두 피크의 합도, 큰 쪽도 아니다. 두 피크가 '
        '다른 순간에 오기 때문이다.',
        'below 에서 2차는 반주기마다 d 만큼만 도통한다. 실효값은 &radic;d 에 '
        '비례하므로, d 를 빠뜨리면 실효값을 과대평가하고 손실은 그 제곱으로 과대평가한다. %s 절이 이 설계의 합성 '
        '전류를 그린다.' % SR('이 설계가 흘려야 하는 전류')]))
    add(h2('트랜스포머'))
    add(p('탱크는 L<sub>r</sub>, L<sub>m</sub>, 그리고 비 하나를 고정했다. '
          '트랜스포머에는 턴수, Open 인덕턴스, 누설이 있다. <b>권선비 둘과 '
          '인덕턴스 둘이 거의 같은 이름을 갖고</b>, 오류는 대부분 거기서 '
          '난다. 이 절은 %s 절의 내용을 벤더가 측정할 수 있는 값으로 옮긴다.'
          % SR('플라이백이 아니다, 그래서 코어가 달라진다')))
    add(p('도면의 숫자는 전부 1차 전류, 2차 각 권선의 전류, 2차 권선 전압, '
          '또는 벤치 시험 하나에서 읽는다. 그림&nbsp;%(f)s 에 각 값을 파형의 어디에서 읽는지 표시했고, 표&nbsp;%(t)s 에 각 표시가 무엇을 정하는지 적었다.' % dict(f=FR('an_xfmr_read'), t=TR('xfmr-read'))))
    _J = _CORE.J_CU
    ext(tbl('그림의 각 표시가 무엇을 정하나. 전류는 유닛 하나의 값이다. '
            '트랜스포머가 하나이면 그 트랜스포머 전체이고, N<sub>x</sub> 개 '
            '유닛으로 나누면(%s 절) 1차는 직렬, 2차는 병렬이다.' % SR('트랜스포머 한 개로 안 될 때'),
            [['표시', '항목', '읽는 위치와 구간',
              '정하는 것'],
             ['<b>1</b>', '1차 피크 전류',
              'i<sub>p</sub> 의 피크: 자화 램프에 부하 전류의 사인 반파를 더한 것. 최악 스위칭 사이클: 라인 피크, 최저 등가 입력, '
              'Full load.',
              '1차 스위치와 OCP1 여유. 포화 시험이 <b>아니다</b>.'],
             ['<b>2</b>', '1차 실효 전류',
              'i<sub>p</sub>&sup2; 을 스위칭 주기 전체로, 그다음 라인 반주기로 '
              '평균. N<sub>x</sub> 개 유닛으로 나누면 각 유닛이 이 전류를 '
              '전부 흘린다: 1차는 직렬.',
              '1차 동선: 유닛당 A<sub>cu</sub> = I<sub>rms</sub>/J'],
             ['<b>3</b>', '자화 피크',
              '스위칭 순간의 점선 i<sub>Lm</sub>. below 에서는 f<sub>sw</sub> '
              '에도 부하에도 무관하고 V<sub>o,eff</sub> 만으로 정해지므로 어느 '
              '사이클에서나 같다.',
              '피크 자속. 그리고 V<sub>OVP2</sub> 로 환산해 DC overlap 시험 '
              '전류(표시 7)'],
             ['<b>4</b>', '2차 피크 전류',
              '어느 2차 권선이든 펄스의 피크, 같은 최악 사이클. N<sub>x</sub> '
              '개 유닛으로 나누면 유닛마다 정류기 레그 값의 1/N<sub>x</sub>: '
              '2차는 병렬.',
              '정류기 피크 정격, 2차 단자'],
             ['<b>5</b>', '2차 실효 전류, 권선마다',
              '권선마다 주기당 펄스 하나이므로 도통하지 않는 반주기를 포함한 주기 '
              '전체로 실효값을 잡고, 그다음 라인 반주기로 평균.',
              '2차 동선: A<sub>cu</sub> = I<sub>rms</sub>/J, 권선당·유닛당'],
             ['<b>6</b>', '권선 볼트-초',
              '정류기가 도통하는 공진 반주기 T<sub>r</sub>/2 동안 2차 권선 '
              '전압은 V<sub>o,eff</sub> 이다. 그 면적이 자속 스윙 '
              '2&thinsp;N<sub>s</sub>A<sub>e</sub>B<sub>pk</sub> 이고, 구간이 '
              'T<sub>r</sub>/2 보다 길어지는 일은 없으므로 f<sub>r</sub> 이 '
              '최악이다.',
              '코어 면적과 N<sub>s</sub>: A<sub>e</sub> &ge; '
              'V<sub>o,eff</sub>/(4 f<sub>r</sub> N<sub>s</sub> B<sub>max</sub>)'],
             ['<b>7</b>', 'DC overlap(포화) 시험',
              '파형이 아니다. LCR 미터를 1차 NP1 에 걸고 나머지 권선(2차 NS2·NS3, 보조 NAUX)은 '
              '모두 Open, 1차에 DC 전류를 겹쳐 흘리며 1차 인덕턴스를 전류에 따라 '
              '읽는다. 시험 전류는 표시 3 을 컨트롤러가 허용하는 최고 '
              '출력 V<sub>OVP2</sub>/V<sub>out</sub> 으로 환산한 것.',
              '코어 포화 여유. 벤더가 시험하는 값'],
             ['&mdash;', 'L<sub>open</sub>, L<sub>short</sub>',
              'LCR 미터(100&nbsp;kHz, 1&nbsp;V)를 NP1 에 걸고 잰다. L<sub>open</sub>: '
              '나머지 권선 모두 Open. L<sub>short</sub>: 2차 반쪽 하나를 Short, 다른 '
              '반쪽과 NAUX 는 Open 으로 재고, 그다음 다른 반쪽을 같은 식으로 잰다. '
              '탱크가 보는 것은 도통하는 반쪽이다. 두 반쪽이 같은 자리에 있지 않으면 '
              '둘 다 Short 한 값은 더 낮게 나온다. 단자에서 재는 값이라 벤더가 '
              '시험할 수 있다.',
              'L<sub>m</sub> + L<sub>r</sub> 과 L<sub>r</sub>: 탱크 소자 그 자체']],
            widths=[CW * 0.07, CW * 0.17, CW * 0.48, CW * 0.28],
            key='xfmr-read', split=True))
    add(h2('두 개의 비, 두 개의 인덕턴스'))
    add(p('누설을 전부 1차로 환산하면 탱크는 비 n 의 이상 트랜스포머, 직렬 '
          'L<sub>r</sub>, 병렬 L<sub>m</sub> 을 본다. 그 n 은 감는 비가 '
          '<b>아니다</b>. 결합 계수를 k 라 하면'))
    add(eq(r'n \;=\; k\,n_{T},\qquad k \;=\; \sqrt{\frac{L_{m}}{L_{m}+L_{r}}}'
           r'\;=\;\frac{1}{\sqrt{1+\lambda}}', key='nnT'))
    add(p('이므로 n<sub>T</sub> = n&radic;(1+&lambda;) 이다. &lambda; &asymp; '
          '0.5 에서 20&nbsp;%% 넘게 차이 나고, 어떤 게인 여유보다 훨씬 크다.'
          % {}))
    add(p('인덕턴스도 같은 식으로 둘로 나뉜다. 탱크 모델은 L<sub>r</sub> 과 '
          'L<sub>m</sub> 을 쓰고, 실제 트랜스포머는 양쪽에 누설이 있는 자화 '
          '인덕턴스 L<sub>&mu;</sub> 를 갖는다.'))
    add(eq(r'L_{\mu}=\sqrt{L_{m}\,(L_{m}+L_{r})}\,,\qquad '
           r'L_{L1}=L_{m}+L_{r}-L_{\mu}\,,\qquad '
           r'L_{L2}=\frac{L_{L1}}{n_{T}^{2}}', key='Lmu'))
    add(p('L<sub>L1</sub> 은 1차 누설, L<sub>L2</sub> 는 2차 누설로, 각각 비의 '
          '자기 쪽에 있다.'))
    add(fig('an_integrated',
            '같은 트랜스포머를 두 가지로 그린 것. 위는 실제 구조: 양쪽 누설, '
            '병렬의 실제 L<sub>&mu;</sub>, 비 n<sub>T</sub>&nbsp;:&nbsp;1. '
            '구동은 v<sub>d</sub>. 아래는 1차로 환산하고 v<sub>d</sub> 의 기본파로 구동한 것: L<sub>r</sub> 하나, L<sub>m</sub> 하나, 비 '
            'n&nbsp;:&nbsp;1. 병렬 소자도 비도 같은 숫자가 아니다.'))
    add(note('실제 구조로 그린 모델(L<sub>L1</sub>, L<sub>&mu;</sub>, L<sub>L2</sub>)은 누설이 양쪽에 고르게 나뉜다고 가정한다. 실제 '
             '분배는 상관없다: 탱크는 LCR 미터로 읽는 두 값만 본다.'))
    add(h2('트랜스포머 사양서에 꼭 적을 것'))
    add(p('단자에서 잴 수 있는 인덕턴스는 둘뿐이고, 그 둘이 탱크에 필요한 '
          '둘이다.'))
    add(eq(r'L_{open}=L_{\mu}+L_{L1}=L_{m}+L_{r},\qquad '
           r'L_{short}=L_{L1}+\frac{L_{\mu}\,n_{T}^{2}L_{L2}}'
           r'{L_{\mu}+n_{T}^{2}L_{L2}}=L_{r}', key='Lopen'))
    add(p('둘 다 1차 단자에서 읽는다. L<sub>open</sub> 은 나머지 권선을 모두 Open 으로 '
          '두고, L<sub>short</sub> 는 2차를 Short, 보조 권선을 Open 으로 둔다. 센터탭이면 '
          '<b>반쪽씩 하나만</b> Short 한다. 실제 동작에서는 반쪽 하나만 도통하므로 탱크가 '
          '보는 것은 반쪽마다의 값이다. 두 반쪽이 같은 자리에 있지 않으면 둘 다 Short 한 '
          '값은 더 낮게 나온다. 그 값은 기록만 하고 L<sub>r</sub> 기준으로 판정하지 않는다. '
          '<b>이 둘과 턴수를 적고, L<sub>&mu;</sub> '
          '는 적지 말 것</b>: 그것을 잴 수 있는 단자 쌍은 없다. 턴수는 숫자로 '
          '적는다. 2차가 한두 턴이면 리드선 루프가 그 권선의 인덕턴스를 '
          '지배한다. 그래서 1차와 2차 한 권선에서 각각 잰 Open 인덕턴스의 비의 제곱근 '
          '&radic;(L<sub>1</sub>/L<sub>2</sub>) 로는 권선비가 안 나온다.'))
    add(h2('자속은 1차가 아니라 2차가 정한다'))
    add(p('그림&nbsp;%(f)s 의 표시 <b>6</b>: 2차 권선 전압은 높이 '
          'V<sub>o,eff</sub>, 폭 T<sub>r</sub>/2 의 직사각형이고 그동안 자속은 '
          '&plusmn;B<sub>pk</sub> 를 오간다. above 에서는 2차가 더 짧은 스위칭 '
          '반주기 동안만 도통하므로, 라인 사이클 어디서나 f<sub>r</sub> 이 '
          '최악이다.' % dict(f=FR('an_xfmr_read'))))
    add(eq(r'B_{pk}=\frac{V_{o,eff}}{4\,f_{r}\,N_{s}\,A_{e}}'
           r'\qquad\Longrightarrow\qquad '
           r'A_{e}\;\geq\;\frac{V_{o,eff}}{4\,f_{r}\,N_{s}\,B_{max}}', key='Bpk'))
    add(p('<b>N<sub>p</sub> 는 나오지 않는다.</b> 자속을 줄이는 것은 2차 '
          '턴수뿐이다. 2차를 한 턴으로 하고 싶은 저전압 대전류 출력에서는 '
          'N<sub>s</sub> 를 반으로 줄이면 코어 면적이 두 배가 된다.'))
    add(note('인덕턴스에서 같은 자속을 구하면 B<sub>pk</sub> = '
             'L<sub>&mu;</sub>i<sub>&mu;,pk</sub>/(N<sub>p</sub>A<sub>e</sub>) '
             '이고, <b>실제</b> L<sub>&mu;</sub> 를 써야 한다. 탱크 '
             'L<sub>m</sub> 을 쓰면 &radic;(1+&lambda;) 만큼 작게 나온다.'))
    add(h2('코어 고르기: 두 면적, 그리고 실제로 결정하는 셋째 조건'))
    add(p('코어는 독립된 조건 둘을 만족해야 한다. 정한 턴수에서 자속을 감당할 단면적 A<sub>e</sub>, 그리고 권선이 들어갈 권선창 A<sub>N</sub>. 둘의 '
          '곱이 <b>area product</b> 이고, 어느 쪽이든 제약이 될 수 있다.'))
    add(note('<b>자속은 A<sub>e</sub> 가 아니라 A<sub>min</sub> 에 대해 검사할 '
             '것.</b> 가장 좁은 단면이 먼저 포화한다: 실제 피크는 '
             'B<sub>pk</sub>&thinsp;A<sub>e</sub>/A<sub>min</sub> 이다.'))
    add(p('single-stage PFC LLC 에서는 <b>보통 셋째 조건이 결정한다</b>: '
          '누설이 L<sub>r</sub> 로 나와야 한다. LCR 미터로 읽는 값의 비로 쓰면'))
    add(eq(r'\frac{L_{short}}{L_{open}}=\frac{L_{r}}{L_{m}+L_{r}}'
           r'=\frac{\lambda}{1+\lambda}', key='lkfrac'))
    add(p('&lambda;&nbsp;&asymp;&nbsp;0.5 에서 <b>약 1/3</b> 이다. 일반 트랜스포머는 누설이 몇 % 인데, 여기서는 일부러 그 열 배의 누설을 만들어야 한다. 그만한 누설은 권선 <b>배치</b>로 만들고, 그 배치가 권선창 면적을 차지한다. '
          'A<sub>e</sub> 와 권선 면적 조건을 통과한 코어가 이 조건에서 탈락할 수 있다.'))
    add(h2('권선 배치가 곧 누설이다'))
    add(p('누설은 두 권선을 어떻게 배치하고 얼마나 떨어뜨리느냐가 정한다.'))
    ext(bullets([
        '<b>샌드위치</b>(1차, 2차, 1차): 1 ~ 2 %. 포워드나 플라이백 '
        '트랜스포머가 원하는 것이고, 여기 필요한 것과 정반대다.',
        '<b>동심 권선(샌드위치 아님)</b>: 몇 %. 아직 모자란다.',
        '<b>분할 권선</b>(나란히 배치): 폭의 절반에 1차, 나머지 절반에 2차: 수십 %, 둘 사이 '
        '간격으로 조절 가능. <b>single-stage 탱크가 요구하는 것이 이것</b>이고, '
        '권선창이 넉넉해야 하는 이유다.',
        '<b>1차 분리</b>: 1차를 둘로 나눠 2차 양쪽에 둔다. 간격마다 자기 쪽 '
        '1차의 암페어턴만 지나가므로 누설은 나란히 배치한 값의 일부가 되고, '
        '간격으로 여전히 조절할 수 있다. 두 부분의 턴수 비가 간격으로 닿을 수 '
        '있는 범위 안에서 목표값의 위치를 정한다.',
        '권선창 안의 <b>자기 션트</b>: 권선 폭 없이 누설을 얻되, 부품 하나와 더 '
        '까다로운 공차가 대가다.']))
    add(p('여러 칸으로 나눠 감은 권선의 누설은 감기 전에 어림할 수 있다. 보빈 '
          '축을 따라 가면 암페어턴은 1차 A 부분에서 오르고, 첫 간격에서 평평하며, '
          '2차를 지나며 내려가고, 1차 B 부분에서 다시 0 으로 돌아온다. 자계는 '
          '권선창 깊이 h<sub>w</sub> 를 가로지르고, 그 에너지에서 다음 식이 나온다.'))
    add(eq(r'L_{short}\approx\frac{\mu_{0}\,l_{N}}{h_{w}}\left[N_{A}^{2}'
           r'\left(\frac{w_{A}}{3}+g_{1}\right)+\left(N_{A}^{2}-N_{A}N_{B}'
           r'+N_{B}^{2}\right)\frac{w_{S}}{3}+N_{B}^{2}\left(g_{2}'
           r'+\frac{w_{B}}{3}\right)\right]', key='leak'))
    add(p('N<sub>A</sub> + N<sub>B</sub> = N<sub>p</sub> 는 1차 두 '
          '부분의 턴수, w<sub>A</sub>, w<sub>S</sub>, w<sub>B</sub> 는 A 부분, '
          '2차, B 부분의 축 방향 폭, g<sub>1</sub> 과 g<sub>2</sub> 는 간격, '
          'l<sub>N</sub> 은 평균 턴 길이다. N<sub>B</sub>&nbsp;=&nbsp;0 이면 나란히 '
          '배치한 권선이다. 이 식은 상한 추정이다: 턴 전체가 코어 안에 있다고 '
          '보는데, 코어 밖 부분은 자계를 되돌려 줄 바깥다리가 없어 누설이 '
          '적다. 실제 배치로 자계를 풀면 범위가 좁아지고, 판정은 첫 샘플이 한다.'))
    add(note('트랜스포머는 보통 샌드위치로 감으라고 권한다. 여기서 '
             'L<sub>r</sub> 은 설계값이고, 결합을 "개선" 하는 벤더는 컨버터를 '
             '망가뜨린다. 도면의 L<sub>short</sub> 옆에 그렇게 적을 것.'))
    add(h2('갭, 그리고 도면에 갭을 적으면 안 되는 이유'))
    add(p('L<sub>m</sub> 은 갭 없는 코어가 주는 값보다 훨씬 작으므로 코어에 '
          '갭을 둔다.'))
    add(eq(r'A_{L}=\frac{L_{open}/N_{x}}{N_{p}^{2}}'
           r'\qquad\qquad '
           r'g\;\approx\;\frac{\mu_{0}\,A_{e}}{A_{L}}', key='ALgap'))
    add(p('N<sub>x</sub> 는 유닛 수(트랜스포머 하나면 1, %s 절), g 는 중앙 다리의 총 갭, &mu;<sub>0</sub> 는 진공 투자율이다. 갭 '
          '식은 프린징을 무시하므로 실제로 필요한 갭은 더 크다. '
          '<b>A<sub>L</sub>, 아니면 더 좋게 L<sub>open</sub> 을 적고 갭은 벤더에게 '
          '맡길 것</b>: 벤더가 그 값에 맞춰 갭을 연마하고, LCR 미터로 확인할 수 있다.'
          % SR('트랜스포머 한 개로 안 될 때')))
    add(h2('권선창: 도선과 전류 밀도'))
    add(p('그림&nbsp;%(f)s 의 표시 <b>2</b> 와 <b>5</b>. 동선은 <b>라인 '
          '사이클</b> 실효값으로 정한다: 스위칭 주기마다의 실효값을 라인 '
          '반주기에 걸쳐 I&sup2; 으로 평균한 것. 2차 값은 권선당·유닛당이고, '
          '도통하지 않는 반주기도 평균에 들어 있다.' % dict(f=FR('an_xfmr_read'))))
    add(p('권선마다 실효 전류와 방열이 허용하는 전류 밀도가 정하는 동선 '
          '면적이 필요하다.'))
    add(eq(r'A_{cu}=\frac{I_{rms}}{J}\qquad\qquad '
           r'\sum_{w} N_{w}A_{cu,w}\;\leq\;k_{u}A_{N}', key='window'))
    add(p('N<sub>w</sub> 는 권선 w 의 턴수, A<sub>cu,w</sub> 는 그 동선 '
          '면적이다. J 는 가정이다: 자연 대류에서 4 ~ 5&nbsp;A/mm&sup2;, '
          '밀폐되면 그보다 낮게. 권선창 점적률 k<sub>u</sub> 는 절연, 보빈 벽, '
          '마진, 테이프까지 세면 Litz 선에서 <b>0.3 이하</b>다. 순수 동선 면적만으로 계산하면 들어가는 양을 세 배 과대평가한다.'))
    add(note('N<sub>x</sub> 개 유닛으로 나누면(%s 절) 1차가 직렬이므로 모든 '
             '유닛이 1차 전류 전부를 흘린다. 나누는 것은 2차뿐이다. 그래서 '
             '유닛을 나누는 것이 저전압 대전류 출력에 도움이 된다.' % SR('트랜스포머 한 개로 안 될 때')))
    add(h2('skin depth, 그리고 권선을 단선으로 만들지 않는 이유'))
    add(p('스위칭 주파수에서 전류는 다음 깊이의 표면층으로 몰린다.'))
    add(eq(r'\delta=\sqrt{\frac{\rho}{\pi f\mu_{0}}}', key='skin'))
    add(p('&rho; 는 권선 온도에서의 구리 비저항, f 는 그 도선이 흘리는 '
          '주파수로 여기서는 f<sub>r</sub> 이다. 표면에서 &delta; 보다 깊은 구리에는 전류가 거의 흐르지 않으므로, 2&delta; 보다 굵은 도체는 굵기를 늘려도 얻는 것이 적다. 다른 턴의 자계도 각 도체에 순환 전류를 만드는데(proximity effect), '
          '분할 권선에서는 이 효과가 더 클 수 있다.'))
    add(p('따라서 권선을 굵은 단선 하나로 만들지 않는다. 방법은 둘이다.'))
    ext(bullets([
        '<b>Litz 선</b>: 에나멜 절연한 가는 소선 여러 가닥을 꼬아, 각 소선이 단면의 모든 위치를 고르게 지나게 한 것. 가는 선 하나가 <b>소선(strand)</b>이고, d<sub>s</sub> 는 소선 지름, a<sub>s</sub> 는 소선 하나의 동선 단면적이다. 규칙은 <b>소선마다</b> d<sub>s</sub>&nbsp;&le;'
        '&nbsp;2&delta;.',
        '저전압 대전류 2차에 <b>동박</b>: 두께 t<sub>f</sub> 는 &delta; 근처로 잡고, 전류는 폭으로 감당한다. 센터탭 단자를 내기도 쉽다. 단 <b>동심 권선에서만</b> 그렇다. 동심 권선에서는 누설 자계가 동박을 따라 흐른다. 분할 권선이나 1차 분리 배치에서는 칸 사이의 자계가 권선창을 가로질러 동박 면을 그대로 뚫고 지나가며, 폭 전체에 와전류를 일으킨다. 그런 배치에서는 2차도 Litz 로 감는다.']))
    add(p('어느 쪽이든 권선 발열을 정하는 것은 AC 저항이다. DC 저항은 하한일 뿐 답이 아니다.'))
    add(p('<b>Litz.</b> 2&delta; 이하의 표준 소선을 고른다. 소선 수는 필요한 동선 면적을 소선 하나의 면적으로 나눈 것이다.'))
    add(eq(r'a_{s}=\frac{\pi d_{s}^{2}}{4}\,,\qquad '
           r'n_{s}=\left\lceil\frac{A_{cu}}{a_{s}}\right\rceil',
           key='astrand'))
    add(p('A<sub>cu</sub> 는 식&nbsp;%s 에서 온다. 완성된 Litz 선은 동선 면적보다 굵다. 소선 사이의 틈, 에나멜, 서빙을 점적률 k<sub>litz</sub> 약 0.5 ~ '
          '0.6 으로 반영하면 외경은' % ER('window')))
    add(eq(r'd_{litz}=\sqrt{\frac{4A_{cu}}{\pi k_{litz}}}', key='litz'))
    add(p('<b>동박.</b> 두께는 skin depth 와 벤더가 보유한 규격에서 고르고, 폭은 그에 따라 정해진다. 보빈 폭을 넘으면 좁은 동박 여러 장을 병렬로 겹쳐 쌓는다.'))
    add(eq(r'w_{f}=\frac{A_{cu}}{t_{f}}\,,\qquad '
           r'n_{f}=\left\lceil\frac{w_{f}}{w_{f,max}}\right\rceil',
           key='foil'))
    add(h2('안전 절연: 권선이 갖춰야 할 것'))
    add(p('트랜스포머가 절연 경계다. 여러 시장에 파는 제품이라면 모든 시장을 '
          '통과하는 구조 하나가 필요하다. 그래서 요구 조건마다 가장 엄격한 '
          '시장을 기준으로 잡는다. 절연 등급은 Class&nbsp;II 제품 기준으로, 상용전원 쪽 '
          '전부와 2차 사이를 <b>강화 절연</b>한다(Class&nbsp;I 도 이것으로 충족된다). '
          '고도는 어느 시장이 가정하는 가장 높은 값이다. clearance 가 고도와 함께 '
          '커지기 때문이다. 작업 전압은 입력 범위의 최고값이다.'))
    ext(bullets([
        '<b>Clearance</b> 는 과전압 범주 II 의 상용전원 서지로 정한다. 강화 '
        '절연은 내전압 등급을 한 단계 올려 잡고, 2000&nbsp;m 를 넘으면 그 '
        '값에 고도 계수를 곱한다.',
        '<b>Creepage</b> 는 작업 전압 실효값, 오염도, 표면 재료의 재료군으로 '
        '정하고, 강화 절연은 기본 절연의 두 배다. 보빈의 tracking index 를 '
        '모르면 가장 낮은 재료군으로 잡는다.',
        '<b>고체 절연</b>(테이프, 보빈 벽, 튜브)은 최소 두께를 갖추거나, '
        '여러 층으로 하되 층마다 강화 절연 내전압 시험을 통과해야 한다.',
        '<b>칸 사이의 강화 절연은 거리나 전선 중 하나가 맡는다.</b> 거리로 '
        '맡기면 1차 칸과 2차 칸 사이 간격이 튜브를 따라가는 creepage 이자 '
        '튜브 위를 건너는 clearance 다. 그래서 강화 절연 creepage 보다 좁을 수 '
        '없다. 그 간격은 누설이기도 하므로 절연이 L<sub>short</sub> 의 하한을 '
        '정하게 된다: 결정하기 전에 식&nbsp;%s 그 하한을 확인한다. '
        '전선으로 맡기면 삼중 절연선(TIW, Litz 로도 만든다)이 강화 절연을 '
        '스스로 갖추므로, 간격은 누설이 요구하는 대로 정하면 된다.'
        % _nj(ER('leak'), '으로', '로'),
        '<b>코어는 가장 가까이 붙은 쪽에 속한다고 본다.</b> 일반 전선이면 1차가 '
        '권선창을 바깥다리 근처까지 채우므로 코어는 1차 쪽이다. 그러면 2차는 '
        '코어까지 강화 절연 거리가 필요하다: 튜브 벽을 지나, 플랜지를 넘어, '
        '바깥다리까지, 그리고 리드에서. 1차가 삼중 절연선이면 코어는 2차 쪽이 '
        '된다. 남는 확인 대상은 절연이 끝나는 곳이다: 1차 핀에서 피복을 벗긴 선 '
        '끝과 코어, 2차 리드 사이.',
        '<b>V<sub>CC</sub> 를 공급하고 출력을 sense 하는 보조 권선은 2차 위에 '
        '감는다.</b> 그래야 출력을 따라간다. 보조 권선은 상용전원 쪽 회로이므로 '
        '그 자리에서 스스로 강화 절연을 갖춰야 하고, 삼중 절연선이면 테이프 '
        '없이 된다.']))
    add(note('권선을 층으로 쌓는 구조라면 양쪽 플랜지의 마진 테이프로 creepage 를 '
             '얻고, 그만큼 권선 폭을 잃는다. 삼중 절연선은 마진이 필요 없지만 '
             '같은 동선 면적에 더 굵고 더 비싸다.'))
    add(h2('손실과 온도 상승'))
    ext(bullets([
        '<b>코어 손실</b>은 대표값이 아니라, 동작 자속과 주파수에서 재료 곡선을 읽어 구한다. below 에서는 자속이 고정이므로 f<sub>sw</sub> 와 함께 오르고, above 에서는 자속이 1/f<sub>sw</sub> 로 줄므로 최악 손실은 f<sub>r</sub> 근처다.',
        '<b>동손</b>은 두 권선 모두 I&sup2;R<sub>ac</sub> 이고, 분할 권선이면 proximity effect 항이 작지 않다.',
        '설계를 제한하는 것은 <b>온도 상승</b>이고, 그것은 표면적과 기류에 '
        '달렸다. 계산한 손실은 열 측정의 입력이지 답이 아니다.']))
    add(h2('포화 시험은 권선 피크 전류가 아니다'))
    add(p('<b>사양서의 DC overlap 항목.</b> 트랜스포머 사양서에는 보통 "DC '
          'overlap: 초기 인덕턴스의 90&nbsp;% 이상, 시험 전류 I<sub>sat</sub>, '
          '상온" 형식의 항목이 있다. 이름이 곧 측정 방법이다. LCR 미터가 작은 AC '
          '신호로 1차 인덕턴스를 읽는다(100&nbsp;kHz, 1&nbsp;V 가 흔한 설정이고 '
          '누설 시험과 같다). 그동안 바이어스 전원이 같은 권선에 DC 전류를 '
          '겹쳐(overlap) 흘린다. 다른 권선은 전부 Open 이다. DC 전류를 단계로 '
          '올리며 단계마다 인덕턴스를 읽는다. 같은 시험을 DC bias, DC '
          'superposition 이라고도 부른다.'))
    add(fig('an_dc_overlap',
            'DC overlap 시험. 왼쪽: 벤치. 오른쪽: DC 전류에 대한 인덕턴스로, '
            '곡선 모양은 예시이고 그 위의 세 전류는 이 설계의 값이다: 동작 '
            '중의 자화 피크, 사양서가 요구하는 시험 전류, 그리고 컨트롤러에 '
            '전압 상한이 없었다면 써야 했을 전류.'))
    add(p('<b>이 시험이 드러내는 것.</b> 다른 권선이 Open 이면 DC 전류 하나가 '
          '자속을 정하므로, 코어가 선형인 동안 인덕턴스는 평평하고 포화에 '
          '다가가면 떨어진다. 90&nbsp;% 점이 knee 점이다. 단자에서 자속 '
          '여유를 읽는 시험은 이것뿐이다. 턴수와 A<sub>L</sub> 은 그것을 '
          '말해 주지 않는다. 같은 A<sub>L</sub> 이 다른 갭, 다른 '
          'A<sub>min</sub>, 다른 재료에서도 나온다. L<sub>open</sub> 은 '
          '인덕턴스를 확인할 뿐 여유를 확인하지 않는다. L<sub>open</sub> 은 '
          '맞는데 코어가 틀린 부품은 여기서만 잡힌다.'))
    add(p('<b>어떤 전류를 적어야 하나.</b> 그림&nbsp;%(f)s 의 표시 <b>3</b> 과 '
          '벤치 패널. 요구할 전류는 자화 전류 피크를 과전압 상한으로 환산한 '
          '것이지, 표시&nbsp;1 의 권선 피크 전류가 아니다.'
          % dict(f=FR('an_xfmr_read'))))
    add(p('시험에서는 1차 암페어턴을 상쇄하는 것이 없으므로 같은 전류가 동작 '
          '중보다 훨씬 큰 자속을 만든다. 그 시험에서 동작 자속을 재현하는 '
          '전류를 요구한다:'))
    add(eq(r'I_{eq}=\frac{B_{pk}\,N_{p}\,A_{e}}{L_{\mu}}', key='Isat'))
    add(note('<b>분모는 L<sub>open</sub> 이 아니라 L<sub>&mu;</sub> 다</b>: 1차 '
             '누설은 코어와 쇄교하지 않는다. L<sub>open</sub> 으로 나누면 '
             '전류가 &radic;(1+&lambda;) 배 작게 나온다. 간단한 검산: 답은 '
             'i<sub>&mu;,pk</sub> 와 <b>같아야</b> 한다.'))
    add(p('탱크 피크 전류로 시험하면 컨버터가 만들지 않는 자속을 요구하게 된다. '
          'I<sub>eq</sub> 에 임의의 여유를 더할 필요도 없다: 자속 상한은 이미 '
          '컨트롤러가 멈추기 전에 허용하는 최고 출력으로 정해져 있다.'))
    add(p('<b>상한이 OVP2 인 이유.</b> 같은 피크 자속을 두 가지로 쓴다: 클램프된 '
          '2차가 거는 볼트-초로(식&nbsp;%(b)s), 그리고 코어를 자화시키는 전류로'
          '(식&nbsp;%(i)s). A<sub>e</sub> 는 약분된다:'
          % dict(b=ER('Bpk'), i=ER('Isat'))))
    add(eq(r'B_{pk}=\frac{V_{o,eff}}{4\,f_{r}\,N_{s}\,A_{e}}'
           r'=\frac{L_{\mu}\,i_{\mu,pk}}{N_{p}\,A_{e}}'
           r'\qquad\Longrightarrow\qquad '
           r'i_{\mu,pk}=\frac{n_{T}\,V_{o,eff}}{4\,f_{r}\,L_{\mu}}',
           key='imuVo'))
    add(p('n<sub>T</sub> = N<sub>p</sub>/N<sub>s</sub> 다. 부하나 입력이 정하는 '
          '것은 하나도 남지 않는다. below 에서는 f<sub>sw</sub> 가 무엇이든 2차가 '
          'T<sub>r</sub>/2 동안 클램프되고, above 에서는 그보다 짧으므로 자속이 더 '
          '작다. <b>자화 피크와 자속은 동작 중에 출력 전압에만 비례한다.</b> 따라서 '
          '최악은 브리지가 아직 스위칭하는 가장 높은 출력 전압이다.'))
    add(p('L6790A 는 ZCD 핀에 두 단계를 갖는다. OVP1(핀 '
          '2.3&nbsp;V)에서는 전력을 줄인 채 스위칭을 계속하므로, 출력이 OVP1 과 '
          'OVP2 사이에 머무는 동안에도 트랜스포머는 구동된다. OVP2(2.5&nbsp;V)에서는 '
          '스위칭을 100&nbsp;ms 멈췄다가 소프트 스타트로 다시 시작한다. 따라서 코어가 '
          '구동되는 동안 출력은 V<sub>OVP2</sub> 이하이고, 식&nbsp;%(m)s 코어가 겪는 '
          '가장 큰 자화 피크를 준다.'
          % dict(m=_nj(ER('imuVo'), '이', '가'))))
    add(p('벤치에서는 나머지 권선이 모두 Open 이므로 DC 전류가 코어의 유일한 '
          '암페어턴이고, B&nbsp;=&nbsp;L<sub>&mu;</sub>&thinsp;I<sub>dc</sub>/'
          '(N<sub>p</sub>A<sub>e</sub>) 로 동작 중과 같은 관계다. OVP2 에서의 '
          '자속을 재현하는 시험 전류는 자화 피크를 전압비로 환산한 것이고, 두 '
          '전압의 비가 여유의 전부다. 그 위에 임의의 계수를 더 곱하지 않는다:'))
    add(eq(r'I_{sat}\;=\;I_{eq}\;\frac{V_{OVP2}}{V_{out}}',
           key='Isatspec'))
    add(p('V<sub>f</sub> = 0 이면 이것이 정확한 자속비다. 정류기 전압 강하가 있으면 '
          '자속비는 (V<sub>OVP2</sub> + N<sub>rect</sub>V<sub>f</sub>)/(V<sub>out</sub> + '
          'N<sub>rect</sub>V<sub>f</sub>) 로 조금 작으므로, 식&nbsp;%s 안전한 쪽으로 '
          '틀린다.' % _nj(ER('Isatspec'), '은', '는')))
    add(p('Overload, 기동, 버스트 모드, 스위칭 주파수는 자속을 올리지 '
          '않는다(%s 절). 출력 과전압은 자속을 올리고, 온도는 상한을 낮춘다. MnZn 파워 페라이트의 B<sub>s</sub> 는 25 &deg;C 에서 '
          '100&nbsp;&deg;C 사이에 약 1/5 떨어진다. 그래서 상온에서 한 시험은 '
          '재료의 고온 B<sub>s</sub> 에 대해 읽는다. OVP2 에서의 설계 자속은 그 '
          '아래에 여유를 두고 있어야 한다. 90&nbsp;%% 기준이 그 여유다.'
          % SR('플라이백이 아니다, 그래서 코어가 달라진다')))
    add(p('<b>컨트롤러에 OVP2 같은 상한이 없으면.</b> 그때는 다른 무언가가 '
          '출력 전압을 제한해야 하고, 사양은 실제로 존재하는 그 한계를 '
          '따른다.'))
    ext(bullets([
        '<b>구동을 멈추는 보호</b>가 절연 어느 쪽에든 있으면: 2차측 crowbar 나 '
        '래치, SR 컨트롤러의 OVP, 래치되는 1차측 OVP. 그 threshold 를 '
        'V<sub>OVP2</sub> 자리에 쓴다.',
        '<b>전력만 줄이는 보호</b>는 OVP1 처럼 상한이 아니다: 코어가 구동되는 '
        '채로 출력이 거기 머물 수 있다. 쓰지 않는다.',
        '<b>전압 상한이 아예 없으면.</b> 출력을 제한하는 것은 오실레이터 하한에서 '
        '가장 가벼운 부하로 탱크가 낼 수 있는 값뿐인데, 하한이 f<sub>o</sub> '
        '근처이면 그 한계는 쓸모가 없다. 남는 것은 전류 제한이다. 2차를 '
        '클램프하는 것이 없으면 1차 전류가 곧 자화 전류다. 그러므로 컨트롤러가 '
        '1차에 허용하는 가장 큰 전류에서 코어가 포화하지 않아야 한다: '
        'I<sub>sat</sub>&nbsp;=&nbsp;I<sub>OCP1</sub>. 안전하지만 비싸다. '
        '%s 절에 이 설계의 비가 있다.' % SR('자속 확인과 사양서'),
        '<b>관행값</b>, 즉 상온에서 i<sub>&mu;,pk</sub> 나 권선 피크의 1.2 ~ '
        '1.5 배는 근거를 따지지 않고 사양서에 넣는 값이다. 특정 동작 조건에 근거하지 않으므로 안전하지도 경제적이지도 않다. 위 '
        '셋 중 하나로 바꾼다.']))
    add(h2('사양서에서 빠뜨리면 안 되는 것'))
    add(note('<b>Open 인덕턴스 공차는 주파수 하한과 맞춰 볼 것.</b> '
             'f<sub>o</sub> 가 1/&radic;L<sub>open</sub> 으로 가므로 값이 낮은 부품은 f<sub>o</sub> 를 오실레이터 하한 f<sub>Min</sub> 쪽으로 밀어 올린다. '
             '하한 여유가 그 하락을 덮지 못하면 &plusmn;10&nbsp;%% 를 만족하는 부품도 하드 스위칭할 수 있다. '
             '검사 방법은 %s 절에 있다.' % SR('컨트롤러 주변 회로')))
    add(p('L<sub>open</sub>, L<sub>short</sub>, 그리고 %s 절의 절연을 만족하면 '
          '코어, 보빈, 도선, 권선 순서는 벤더에게 맡길 수 있다. 그것들은 모두 '
          '단자에서 잴 수 있기 때문이다. 설계 예제는 그래도 그것들을 정한다: '
          '예제의 L<sub>r</sub> 이 특정한 권선 하나의 누설이기 때문이다.'
          % SR('안전 절연: 권선이 갖춰야 할 것')))
    add(h2('트랜스포머 한 개로 안 될 때'))
    add(p('저전압 대전류에서는 2차가 굵은 한 턴이 되고 코어가 커진다. 그러면 '
          '트랜스포머를 <b>1차 직렬, 2차 병렬</b>의 같은 유닛 N<sub>x</sub> '
          '개로 만들 수 있다. 직렬 1차는 같은 전류를 흘리므로 2차 전류는 밸런스 저항 없이 고르게 나뉜다.'))
    ext(bullets([
        'Open 인덕턴스와 누설 인덕턴스가 N<sub>x</sub> 로 나뉘고, 2차 전류도 '
        '그렇다. <b>1차 전류는 안 나뉜다.</b>',
        'DC overlap 시험 전류는 바뀌지 않는다.',
        '감는 비는 N<sub>x</sub>N<sub>p</sub>/N<sub>s</sub> 가 되므로 <b>가능한 '
        '비는 N<sub>x</sub>/N<sub>s</sub> 단위로 양자화된다</b>. 탱크 설계 때 고려할 것.']))
    add(h2('입력 커패시터'))
    add(p('C<sub>in</sub> 은 스위칭 리플만 흡수하는 필름 커패시터다. 하한은 ST 의 '
          '경험식이고 평가 보드도 이것을 따른다:'))
    add(eq(r'C_{in}\;=\;3\,\frac{\mathrm{nF}}{\mathrm{W}}\times P_{in}', key='Cin'))
    add(p('이것은 <b>하한</b>이다. 다음 표준값으로 올리고, 입력 전압 전체에 '
          '대해 정격을 잡는다. 이보다 훨씬 크게 잡지는 않는다: 값이 크면 영교차 '
          '부근에서 전하를 유지해 입력 전류 파형을 왜곡하므로 THD 에 영향을 준다.'))
    add(h2('출력 커패시터 뱅크'))
    add(p('조건이 둘이고 큰 쪽으로 정한다. 리플 조건은'))
    add(eq(r'C_{out}\;\geq\;\frac{P_{out}}'
           r'{2\pi f_{l,min}\,\Delta v\,V_{out}^{2}}', key='Crip'))
    add(p('이고 hold-up 조건은'))
    add(eq(r'C_{out}\;\geq\;\frac{2P_{out}T_{hold}}'
           r'{\left(V_{out}-\frac{1}{2}\Delta v_{pp}\right)^{2}'
           r'-V_{o,min}^{2}}', key='Chold'))
    add(note('<b>hold-up 은 최악의 라인 위상에서 시작한다.</b> 리플 골에서 '
             '정전이 나면 뱅크는 이미 리플의 절반만큼 내려가 있다. 그래서 '
             '&minus;&frac12;&Delta;v<sub>pp</sub> 항이 있고, 그만큼 유지 시간이 줄어든다. &Delta;v<sub>pp</sub> 는 허용값이 아니라 뱅크가 실제로 '
             '만드는 리플이므로, 뱅크를 정한 뒤에 검사한다.'))
    add(p('두 조건 모두 1/V<sub>out</sub>&sup2; 으로 가므로 어느 조건이 결정하는지는 사양에 달렸다. k&nbsp;=&nbsp;V<sub>o,min</sub>/V<sub>out</sub> 으로 두면 리플 조건이 결정하는 경우는'))
    add(eq(r'\left(1-\frac{\Delta v}{2}\right)^{2}-k^{2}'
           r'\;>\;4\pi f_{l}\,\Delta v\,T_{hold}', key='ripscreen'))
    add(p('뱅크를 정하기 전에 판단하므로 <i>허용</i> &Delta;v 를 쓴다. 이 설계의 값은 %s 절에 있다.' % SR('출력 뱅크 설계 결과')))
    ext(bullets([
        '리플 전류에 <b>2f<sub>l</sub> 성분</b>을 넣을 것. 스위칭 성분과 '
        '비슷한 크기이고 제곱합으로 더해진다.',
        '센터탭 2차에서는 커패시터 리플 전류를 권선당이 아니라 <b>출력 '
        '노드</b>에서 판단할 것.',
        'ESR 은 전류 성분마다 그 주파수의 값을 쓸 것: 스위칭 성분에는 '
        '<b>스위칭 주파수</b> ESR, 2f<sub>l</sub> 성분에는 tan&thinsp;&delta; '
        '에서 구한 <b>120&nbsp;Hz</b> ESR. 여기서는 두 성분의 크기가 비슷하다.']))
    add(note('컨트롤러의 기동 허용 시간은 정해져 있고, 이 뱅크는 일반 설계보다 훨씬 큰 기동 부하다. 뱅크를 모두 단 상태의 cold start 를 초기에 확인할 것.'))
    add(h2('반도체 요구조건'))
    add(p('부품을 고르지 말고 요구조건을 적는다. 규칙 넷.'))
    ext(bullets([
        '1차 스위치 정격은 <b>합성 탱크 피크</b>로 잡는다. 부하 성분만으로 '
        '잡으면 부족하다.',
        '병렬 소자 수로 나눈다. 표의 전류는 1차는 <b>스위치 한 개당</b>, 2차는 '
        '<b>레그당</b>이다. 센터탭 레그는 2차 전류 전부를 흘린다.',
        '손실은 <b>T<sub>j,max</sub></b> 에서의 R<sub>DS(on)</sub> 으로 계산한다. '
        '데이터시트 최대값은 25&nbsp;&deg;C 공정 편차만 반영하고, 온도 영향은 별도 계수로 슈퍼정션 소자에서 약 2 배다.',
        'T<sub>a</sub> 에 대한 곡선을 T<sub>j</sub> 로 읽어도 되는 것은 '
        '<b>펄스 시험일 때뿐</b>이다.']))
    add(note('하프브리지 모핑에서 고정된 소자(%s 절)는 스위칭하지 않으면서 '
             '탱크 전류 전부를 흘린다. 여기서 그 대가가 얼마인지는 %s 절에 '
             '있다.' % (SR('하프브리지'), SR('손실 분배'))))
    add(h2('브리지 구동: 외부 게이트 드라이버'))
    add(p('컨트롤러의 HOUTx 와 LOUTx 는 로직 출력이다. 레그마다 하프브리지 '
          '드라이버가 필요하고, 그 드라이버가 검사 항목 넷을 더한다.'))
    add(p('<b>하이사이드는 부트스트랩으로 산다.</b> 그 커패시터 C<sub>BOOT</sub> '
          '는 같은 레그의 로우사이드가 켜져 있는 T<sub>charge</sub> 동안 '
          'V<sub>CC</sub> 에서 다시 충전된다. 저항 R<sub>BS</sub> 의 내장 스위치로 '
          '충전하는 드라이버는'))
    add(eq(r'V_{drop}=\frac{Q_{g}\,R_{BS}}{T_{charge}}', key='bsdrop'))
    add(p('만큼 잃는다. 이 값은 주파수와 함께 커진다. V<sub>CC</sub> 의 큰 몫이 '
          '되면 V<sub>CC</sub> 에서 BOOT 로 외부 고속 다이오드를 단다. 그러면 '
          '하이사이드 전원은 레일보다 다이오드 전압 V<sub>F</sub> 와 주기마다의 '
          '리플만큼 낮다. 리플은 게이트 전하에, 플로팅부가 가장 긴 하이사이드 펄스 '
          'T<sub>on,max</sub> 동안 끄는 I<sub>QBO</sub> 를 더한 것이다:'))
    add(eq([r'\Delta V_{boot}=\frac{Q_{g}+I_{QBO}\,T_{on,max}}{C_{BOOT}}',
            r'V_{BO}=V_{CC}-V_{F}-\Delta V_{boot}'], key='vbo'))
    add(p('<b>드라이버가 V<sub>CC</sub> 의 하한을 정한다.</b> 드라이버 자체 전원과 '
          '플로팅 전원에는 권장 최소값이 있다. 그 아래에서도 스위칭은 할 수 있지만 '
          '데이터시트가 보증하는 것은 없다. 그래서 기동 설계는 이 값을 쓴다:'))
    add(eq(r'V_{CC,floor}=\max\left(V_{CCoff},\;V_{CC,drv,min},\;'
           r'V_{BO,min}+V_{F}+\Delta V_{boot}\right)', key='vccfloor'))
    add(p('<b>게이트 전력은 나눠 갖는다.</b> 드라이버 하나가 주기마다 스위치 둘의 '
          '전하를 옮긴다. 전력 Q<sub>g</sub>V<sub>CC</sub>f 는 드라이버 출력 '
          'R<sub>drv</sub>, 게이트 저항 R<sub>G</sub>, MOSFET 내부 R<sub>g,int</sub> '
          '에 나뉘므로 드라이버 몫은'))
    add(eq([r's_{drv}=\frac{1}{2}\left(\frac{R_{so}}{R_{so}+R_{G}+R_{g,int}}'
            r'+\frac{R_{si}}{R_{si}+R_{G}+R_{g,int}}\right)',
            r'P_{drv}=2\,Q_{g}V_{CC}f_{sw}\,s_{drv}+(I_{QCC}+I_{QBO})\,V_{CC}'],
           key='pdrv'))
    add(p('R<sub>so</sub> 와 R<sub>si</sub> 는 출력의 소스·싱크 저항이다. '
          '데이터시트에 더 나은 값이 없으면 V<sub>CC</sub> 를 단락 전류로 나눠 쓴다. '
          'I<sub>QCC</sub> 와 I<sub>QBO</sub> 는 로우사이드부와 플로팅부의 대기 '
          '전류다. 턴오프 경로를 따로 두면(아래) 싱크 항의 R<sub>G</sub> 는 '
          'R<sub>G,off</sub> 다.'))
    add(p('<b>타이밍.</b> 데드타임은 드라이버의 지연 편차 MT 만큼 줄어서 게이트에 '
          '닿는다. 그래서 (t<sub>D</sub> &minus; MT) 가 스윙 T<sub>T</sub> 를 '
          '덮어야 한다. 스윙 중의 중점 기울기 S<sub>mid</sub> 도 검사한다. 스윙 '
          '꼭대기에서 전류 전환 전류가 출력 커패시턴스에 흐르며 만드는 기울기이고, '
          '드라이버가 허용하는 OUT 슬루율 S<sub>OUT,max</sub> 아래여야 한다.'))
    add(p('<b>턴오프 경로는 따로 둔다.</b> 게이트 저항 하나가 두 에지를 다 정한다. '
          'R<sub>G</sub> 에 역병렬로 다이오드를 달고 더 작은 R<sub>G,off</sub> 를 '
          '직렬로 두면 게이트가 충전보다 빨리 방전된다. 같은 레그의 다른 스위치가 '
          '켜질 때 그 dv/dt 가 Miller 커패시턴스로 전하를 밀어 넣는다. 그때 게이트를 '
          '붙잡아 두는 것이 이 경로다. 검사는 셋이다. 피크 방전 전류 '
          '(V<sub>CC</sub> &minus; V<sub>F</sub>)/(R<sub>G,off</sub> + '
          'R<sub>si</sub> + R<sub>g,int</sub>) 는 드라이버 싱크 정격과 다이오드 '
          '서지 정격 아래여야 한다. 평균 Q<sub>g</sub>f<sub>sw</sub> 는 다이오드의 '
          '연속 정격 아래여야 한다. 그리고 레일에서 Miller 평탄부까지의 하강 시간에는 '
          '하한이 있다. R<sub>G,off</sub> 를 아무리 작게 해도 내부 저항과 싱크 '
          '저항이 그 하한을 정한다.'))

    add(h2('컨트롤러 주변 회로'))
    add(fig('bom_pin_config',
            '컨트롤러와 주변 수동 소자. HVSU 는 브리지의 AC 쪽에서 받고, 보조 '
            '권선이 분압기를 거쳐 ZCD 를 구동하며, R<sub>T</sub> 와 '
            'C<sub>T</sub> 가 오실레이터 한계를 정하고, R<sub>CFG</sub> 와 '
            'R<sub>BM</sub> 은 전원 인가 시 읽힌다. 도면은 보조 권선에서 다이오드 '
            '하나만 거쳐 V<sub>CC</sub> 를 공급하는데, 설계 예제는 그 사이에 제너 '
            '기준 레귤레이터를 둔다(%s 절). ST L6790A 설계 스프레드시트의 '
            '도면이다.' % SR('보조 권선 V<sub>CC</sub> 설계 결과'), width=CW))
    add(p('보조 권선의 용도부터 정한다. V<sub>CC</sub> 에 바로 연결하면 OVP2 에서의 '
          '전압이 V<sub>CC</sub> 정격 아래여야 하므로 권선비에 상한이 생긴다. '
          '사이에 레귤레이터를 두면 그 상한은 레귤레이터 출력으로 옮겨 가고, '
          '권선비는 다른 두 조건이 정한다(%s 절).'
          % SR('보조 권선으로 V<sub>CC</sub> 공급하기')))
    add(p('%s 절이 부품을 순서대로 정한다. 가장 신경 쓸 것은 R<sub>T</sub> '
          '다: 오실레이터 하한을 정하고, 그 하한은 f<sub>o</sub> 위에 있어야 '
          '한다.' % SR('컨트롤러 주변 부품')))
    add(note('<b>이 하한 여유가 보통 설계에서 가장 작다.</b> 오실레이터 idle 시간에도 '
             '달렸는데, 초안 데이터시트가 그 값을 일관되지 않게 적고 있으므로 '
             '하드웨어에서 f<sub>sw</sub>(&theta;) 를 재서 확인해야 한다.'))
    add(p('트랜스포머 공차도 같은 여유 안에 들어가야 한다. L<sub>open</sub> 이 '
          '<b>낮으면</b> f<sub>o</sub> 가 오른다. 허용되는 인덕턴스 감소는'))
    add(eq(r'\frac{\Delta L}{L}\;=\;1-\frac{1}{k_{floor}^{2}}', key='Ldrop'))
    add(p('k<sub>floor</sub> = f<sub>Min</sub>/f<sub>o</sub> 는 하한 여유다. 하한 여유가 몇 %% 뿐이면 허용 하락도 몇 %% 뿐이다. 그러면 흔한 '
          '&plusmn;10&nbsp;%% 는 <b>안 들어간다</b>. 공차 아래쪽 끝에서 '
          'f<sub>o</sub> 가 f<sub>Min</sub> 위로 올라가, 영교차 근처에서 하드 '
          '스위칭할 수 있다. 아래쪽 공차를 조이거나 R<sub>T</sub> 를 낮춰 '
          'f<sub>Min</sub> 을 올린다. 하한을 올리면 영교차 dead zone 이 '
          '넓어진다(%s 절). <b>트랜스포머를 발주하기 전에 확인할 것.</b>'
          % SR('주파수 변조가 곧 역률 보정이다')))
    add(h2('보조 권선으로 V<sub>CC</sub> 공급하기'))
    add(p('권선이 다이오드를 거쳐 커패시터를 충전한다. 베이스를 제너로 잡은 NPN '
          '이미터 팔로워가 그 전압을 핀으로 넘긴다. 둘 사이에는 데이터시트가 '
          '요구하는 바이패스 다이오드가 있어, 기동 전류가 레귤레이터로 들어가지 '
          '않게 한다. 핀 전압 V<sub>CC,reg</sub> 는 제너 전압 V<sub>DZ</sub> 에서 '
          '베이스-이미터 전압 V<sub>BE</sub> 와 다이오드 전압 V<sub>D</sub> 를 '
          '뺀 값이다:'))
    add(eq(r'V_{CC,reg}=V_{DZ}-V_{BE}-V_{D}', key='vccreg'))
    add(p('제너 공차 때문에 이 값은 범위를 갖는다. 범위의 아래쪽 끝은 '
          'V<sub>CC,HVSUon</sub> 보다 높게 둔다. 그 아래로 내려가면 기동 회로가 '
          '충전 전류를 다시 켜는데, 초안 데이터시트는 기동 timeout 이 지난 '
          '뒤에도 그런지 적지 않았다. 그 레벨 위에 있으면 이 문제는 생기지 '
          '않는다. 위쪽 끝은 핀의 동작 한계 아래여야 한다. 부하 I<sub>VCC</sub> '
          '는 셋의 합이다: 컨트롤러 자체의 I<sub>CC</sub>, 게이트 드라이버의 대기 '
          '전류 I<sub>drv,q</sub>, 그리고 스위치 자리 N<sub>sw</sub> 개 각각의 '
          '게이트 전하 Q<sub>g</sub> 를 주기마다 한 번씩 채우는 전류:'))
    add(eq(r'I_{VCC}=I_{CC}+I_{drv,q}+N_{sw}\,Q_{g}\,f_{sw}', key='ivcc'))
    add(p('Q<sub>g</sub> 는 드라이버가 실제로 거는 전압, 곧 레일 전압에서의 '
          '전하다. 데이터시트 표제의 10&nbsp;V 값이 아니다. Miller 평탄부를 지나면 '
          '드레인은 이미 내려와 있고 게이트는 고정 커패시턴스로 보인다. 거기서 '
          '게이트 전하 곡선은 직선이다. 그 위의 두 점이면 어느 구동 전압의 전하든 '
          '나온다:'))
    add(eq(r'Q_{g}(V)=Q_{g,10}+C_{g}\,(V-10\;\mathrm{V})', key='qgv'))
    add(p('<b>권선비에는 하한과 비용이 있다.</b> hold-up 끝에서 출력이 '
          'V<sub>o,min</sub> 일 때도 권선은 베이스를 가장 높은 제너 전압 '
          'V<sub>DZ,max</sub> 위로 올려야 한다. 그러고도 베이스 전류 '
          'I<sub>VCC</sub>/&beta;<sub>min</sub> 과 제너 바이어스 '
          'I<sub>Z,min</sub> 을 댈 전류가 남아 있어야 한다. 이것이 공급 저항 '
          'R<sub>BZ</sub> 의 상한을 정한다:'))
    add(eq(r'R_{BZ}\leq\frac{n_{aux}V_{o,min}-V_{D}-V_{DZ,max}}'
           r'{I_{VCC}/\beta_{min}+I_{Z,min}}', key='rbz'))
    add(p('OVP1 에서는 패스 트랜지스터가 커패시터와 핀 사이의 전압 차에 '
          'I<sub>VCC</sub> 를 곱한 만큼을 소모한다. 그러므로 하한을 만족하는 '
          '가장 작은 정수 턴의 권선비가 비용도 가장 작다.'))
    add(p('<b>기동이 또 하나의 크기 결정 조건이다.</b> 기동 회로가 C<sub>VCC</sub> '
          '를 V<sub>CCon</sub> 까지 채우면 스위칭이 시작된다. 출력이 올라와 권선이 '
          '핀을 유지할 수 있을 때까지는 C<sub>VCC</sub> 가 컨트롤러와 드라이버를 '
          '먹인다. V<sub>CC,HVSUon</sub> 까지는 혼자, 그 아래 V<sub>CC,floor</sub> '
          '까지는 기동 충전 전류 I<sub>HVSU</sub> 의 도움을 받는다. 하한은 '
          '컨트롤러의 V<sub>CCoff</sub> 가 아니다. 그것과 게이트 드라이버의 최저 '
          '보증 전원 중 높은 쪽이다(식&nbsp;' + ER('vccfloor') + '). 이 시간이 '
          't<sub>hand</sub> 를 버텨야 한다. t<sub>hand</sub> 는 출력이 '
          'V<sub>out,UV</sub>, 곧 권선이 핀을 하한에 붙잡아 둘 수 있는 레벨에 '
          '닿을 때까지의 시간이다. 구동 전류는 레일과 함께 떨어진다: '
          'I<sub>VCC</sub>(V) = I<sub>VCC,SU</sub> &minus; B(V<sub>CCon</sub> '
          '&minus; V), B = N<sub>sw</sub>C<sub>g</sub>f<sub>sw</sub>(식&nbsp;'
          + ER('qgv') + '). 동작 범위 위에서 기동하는 오실레이터는 처음에 전하 '
          '&Delta;Q<sub>OSC</sub> 를 더 쓴다. 출력 뱅크를 정격 전류로, No load 로 '
          '충전한다고 보고 C<sub>VCC</sub>dV/dt = &minus;I<sub>VCC</sub>(V) 를 두 '
          '구간에서 적분하면'))
    add(eq([r't_{hand}=\frac{C_{out}V_{out,UV}}{I_{out}}',
            r'C_{VCC}\geq\frac{B\left(t_{hand}+\Delta Q_{OSC}/I_{VCC,SU}'
            r'\right)}{\ln\dfrac{I_{VCC}(V_{CCon})}{I_{VCC}(V_{CC,HVSUon})}'
            r'+\ln\dfrac{I_{VCC}(V_{CC,HVSUon})-I_{HVSU}}'
            r'{I_{VCC}(V_{CC,floor})-I_{HVSU}}}'],
           key='cvcc'))
    add(p('C<sub>VCC</sub> 를 크게 잡은 대가는 첫 펄스까지의 지연 '
          'C<sub>VCC</sub>V<sub>CCon</sub>/I<sub>HVSU</sub> 이다.'))
    add(h2('전압 루프와 보상'))
    add(p('루프는 그림&nbsp;%(f)s 처럼 이어진다. 분압기가 출력을 검출한다. TL431 이 '
          '기준과 비교해 옵토커플러 LED 를 구동한다. 옵토커플러 트랜지스터가 '
          'FB 핀을 끌어내린다. FB 전압이 전력을 지령하고(%(s)s 절), 그 전력이 '
          '출력 커패시터로 들어간다.'
          % dict(f=FR('an_loop_blocks'), s=SR('피드백 핀은 전력 지령이다'))))
    add(fig('an_loop_blocks',
            '전압 루프의 블록도. FB 핀 왼쪽이 전부 보상기 G<sub>EA</sub>(s), '
            '오른쪽이 전부 플랜트 G<sub>plant</sub>(s) 다. 루프 게인은 T(s) = '
            'G<sub>plant</sub>(s)&nbsp;G<sub>EA</sub>(s).'))
    add(p('<b>플랜트.</b> FB 전압이 전력을 정하고, 전력을 출력 전압으로 나눈 '
          '것이 C<sub>out</sub> 으로 들어가는 전류이며, 커패시터로 들어가는 '
          '전류는 적분된다. 소신호로, v<sub>out</sub> 과 v<sub>FB</sub> 는 '
          'V<sub>out</sub> 과 V<sub>FB</sub> 의 변화분이다.'))
    add(eq(r'G_{plant}(s)=\frac{v_{out}(s)}{v_{FB}(s)}=\frac{G_{o}}{s},'
           r'\qquad G_{o}=\frac{P_{out}}{V_{out}\,V_{FB}\,C_{out}}'
           r'\quad[\mathrm{rad/s}]', key='Gplant'))
    add(p('V<sub>FB</sub> 는 정격 전력에서 0.5&nbsp;V 오프셋 위의 피드백 '
          '전압이다(식&nbsp;%(e)s). 적분기는 어디서나 &minus;90&deg; 로 '
          'decade 당 20&nbsp;dB 씩 떨어지고, f<sub>cto</sub> = G<sub>o</sub>/2&pi; '
          '에서 0&nbsp;dB 를 지난다. 둘째 pole 도 RHP zero 도 없으므로 '
          '루프는 안정시키기 쉽다. crossover 주파수 선정을 어렵게 하는 것은 출력 리플이다'
          '(%(r)s 절).'
          % dict(e=ER('VFB'),
                 r=SR('crossover 주파수가 낮아야 하는 이유: 2f<sub>l</sub> 리플'))))
    add(p('적분기는 출력이 움직여도 일정한 전력을 끄는 부하를 가정한다. 뒷단 '
          '컨버터가 그런 부하다. 저항 부하 R<sub>L</sub> 은 출력이 내려가면 덜 '
          '끌므로, 소신호에서 적분기가 1/(&pi;R<sub>L</sub>C<sub>out</sub>) 의 '
          'pole 로 바뀐다. 그 pole 위에서는 플랜트가 같고, 아래에서는 루프 게인이 '
          '낮으며, crossover 에서 위상이 최대 90&deg; 덜 음수다. 그러므로 적분기가 '
          'phase margin 의 최악 조건이다.'))
    add(h2('루프 설계 목표와 벗어났을 때의 결과'))
    add(p('T(s) 의 Bode plot 에서 숫자 셋을 읽는다. |T| = 1 인 <b>crossover 주파수</b> f<sub>c</sub>. f<sub>c</sub> 에서의 <b>phase margin</b> '
          '180&deg; + arg&nbsp;T. 그리고 <b>gain margin</b>: arg&nbsp;T = &minus;180&deg; 인 '
          'f<sub>180</sub> 에서 |T| 가 0&nbsp;dB 아래로 얼마나 있는가. 목표는 표&nbsp;%(t)s 에 있다.'
          % dict(t=TR('loop-aims'))))
    ext(tbl('루프가 이뤄야 할 것.',
            [['항목', '목표', '너무 낮으면', '너무 높으면'],
             ['crossover 주파수 f<sub>c</sub>',
              '이 컨버터에서는 15 ~ 20 Hz (%s 절). 일반 규칙은 '
              'f<sub>sw</sub>/5 아래, 그리고 루프가 따라가면 안 되는 리플 '
              '주파수 아래.'
              % SR('crossover 주파수가 낮아야 하는 이유: 2f<sub>l</sub> 리플'),
              '루프가 느리다. 부하 스텝이나 모핑 전환 뒤 출력이 더 많이 내려가고 더 늦게 돌아온다.',
              '루프가 2f<sub>l</sub> 출력 리플을 따라간다. 전력 지령이, 따라서 '
              '입력 전류가 2f<sub>l</sub> 로 변조된다: 입력 전류의 3차 고조파, '
              '버스트 threshold 를 넘나드는 채터링.'],
             ['phase margin &Phi;<sub>M</sub>',
              '45&deg; 가 하한, 50 ~ 60&deg; 가 목표. 76&deg; 에서는 스텝 '
              '응답에 오버슈트가 없고, 45&deg; 에서는 링잉한다(Q &asymp; 1.2) '
              '[onsemi TND381].',
              '외란마다 링잉. 0&deg; 에서는 루프가 f<sub>c</sub> 로 발진한다.',
              '응답이 과감쇠되어 느리다. 문제는 아니지만 대가가 있다: phase margin 을 늘리려면 crossover 주파수를 낮춰야 한다.'],
             ['gain margin GM',
              '6 dB 가 하한, 10 dB 면 여유 있다.',
              '부품 편차로 |T| 가 커진다. 옵토커플러 CTR 만으로도 랭크·전류·온도에 '
              '따라 2:1 편차가 있다. gain margin 이 작은 루프는 온도가 높은 보드에 '
              'CTR 높은 부품이 들어가면 f<sub>180</sub> 에서 발진한다.',
              '&mdash;'],
             ['2f<sub>l</sub> 에서의 G<sub>EA</sub>',
              '3차 고조파를 허용치 안에 두는 값 이하(식&nbsp;%s).' % ER('GEAreq'),
              '루프에는 문제없다. crossover 주파수가 필요 이상으로 낮을 뿐이다.',
              '3차 고조파가 허용치를 넘고, 버스트 채터링.']],
            widths=[CW * 0.16, CW * 0.30, CW * 0.27, CW * 0.27],
            key='loop-aims', split=True))
    add(h2('crossover 주파수가 낮아야 하는 이유: 2f<sub>l</sub> 리플'))
    add(p('2f<sub>l</sub> 출력 리플(%(s)s 절)의 피크-피크 값은'
          % dict(s=SR('역률 1 에서 고르지 않게 들어오는 에너지'))))
    add(eq(r'\Delta V_{loop}=\frac{P_{out}}{V_{out}}\,\frac{1}{2\pi f_{l}\,C_{out}}',
           key='dVloop'))
    add(p('보상기가 그 중 G<sub>EA</sub>(2f<sub>l</sub>) 만큼을 FB 핀으로 '
          '넘기는데, FB 는 전력 지령이므로 입력 전류가 2f<sub>l</sub> 로 '
          '변조된다. 사인파를 그 주파수의 두 배로 변조하면 3차 고조파가 '
          '생긴다. 지령을 m 만큼 변조하면 3차 고조파로 m/2 가 나타나고, 리플 진폭은 '
          '피크-피크의 절반이므로'))
    add(eq(r'D_{3}=\frac{G_{EA}(2f_{l})\,\Delta V_{loop}}{4\,V_{FB}}',
           key='D3'))
    add(p('거꾸로, 3차 고조파 허용치가 2f<sub>l</sub> 에서의 최대 보상기 '
          '게인을 정한다.'))
    add(eq(r'G_{EA}(2f_{l})\;\leq\;\frac{4\,V_{FB}\,D_{3}}{\Delta V_{loop}}',
           key='GEAreq'))
    add(p('2f<sub>l</sub> 에서 게인이 작다는 것은 crossover 주파수가 그보다 훨씬 '
          '아래라는 뜻이다. 3차 고조파 5&nbsp;% 허용이면 15 ~ 20&nbsp;Hz. 더 '
          '빠른 루프는 출력 리플을 줄이고 부하 스텝 응답을 빠르게 하지만 입력 '
          'distortion 을 키운다. distortion 한도가 우선한다. onsemi TND381 은 '
          '이 현상을 "tail chasing" 이라 부른다.'))
    add(h2('보상기: TL431, 옵토커플러, FB 핀'))
    add(fig('comp_network_st',
            '2차측의 보상기. R<sub>I</sub> 와 R<sub>O</sub> 가 출력 전압 설정값을 정하고, TL431 이 error amp 이며, R<sub>F</sub>, C<sub>F</sub>, '
            'C<sub>Fo</sub>(도면의 Rf, Cf, Cfo)가 그 게인을 만들고, R<sub>B</sub> 가 안정화된 '
            'V<sub>Z</sub> 레일에서 옵토커플러 LED 에 전류를 주며, R<sub>P</sub> 가 TL431 의 최소 동작 전류를 확보하고, C<sub>fx</sub> 는 FB 핀 커패시터다. '
            'ST L6790A 설계 스프레드시트의 도면이다.'))
    add(p('분압기 R<sub>I</sub>, R<sub>O</sub> 가 출력을 분압해 TL431 기준 전압 V<sub>R</sub>&nbsp;=&nbsp;2.495&nbsp;V 와 비교한다.'))
    add(eq(r'V_{out}=V_{R}\left(1+\frac{R_{I}}{R_{O}}\right)', key='RoVout'))
    add(p('출력이 오르면 TL431 이 LED 를 통해 더 많은 캐소드 전류를 흘린다. '
          'R<sub>B</sub> 는 안정화 레일 V<sub>Z</sub> 에서 LED 에 전류를 준다. '
          '이 레일은 제너가 아니라 shunt 레귤레이터다. 아래의 R<sub>B</sub> 허용 '
          '범위가 제너 공차에 비해 너무 좁기 때문이고, %s 절에서 둘째 TL431 로 '
          '만든다. 옵토커플러 트랜지스터가 내부 풀업 R<sub>FB</sub> 에 맞서 FB 를 '
          '끌어내려 전력 지령이 떨어진다. LED 에 병렬인 R<sub>P</sub> 는 TL431 '
          '이 필요로 하는 최소 캐소드 전류를 흘리므로 상한이 있다.'
          % SR('전압 루프 설계 결과')))
    add(eq(r'R_{P}\leq\frac{V_{Fo}}{I_{min}}', key='RPmax'))
    add(p('V<sub>Fo</sub> 는 LED 순방향 전압, I<sub>min</sub> 은 TL431 에 필요한 최소 캐소드 전류다. '
          'LED 를 V<sub>Z</sub> 에서 공급하므로 출력 리플은 TL431 을 통해서만 '
          'LED 에 닿는다: 둘째 경로(TND381 의 "fast lane")가 없다.'))
    add(p('<b>같은 회로를 op-amp 로.</b> 그림&nbsp;%(f)s 에 다시 그렸다. '
          'TL431 안에서는 증폭기가 REF 를 내부 V<sub>R</sub> 과 비교해 NPN 을 '
          '구동하고, 그 컬렉터가 캐소드다. 트랜지스터가 반전하므로 REF 에서 '
          '캐소드까지 이 부품은 REF 를 V<sub>R</sub> 로 유지하는 고게인 반전 '
          '증폭기다. R<sub>I</sub> 가 입력 저항이고 R<sub>F</sub> + '
          'C<sub>F</sub> 에 병렬인 C<sub>Fo</sub> 가 피드백 임피던스 '
          'Z<sub>f</sub> 이므로, 캐소드는 출력 변화의 '
          '&minus;Z<sub>f</sub>/R<sub>I</sub> 배만큼 움직인다. R<sub>O</sub> 는 DC 동작점만 정한다. 캐소드 전류가 LED 전류다. 옵토커플러 '
          '트랜지스터는 FB 노드에서 CTR&thinsp;i<sub>LED</sub> 를 흘리는 전류 제어 전류원이고, R<sub>FB</sub> 와 C<sub>opto</sub> + '
          'C<sub>fx</sub> 의 pole 을 갖는다. 세 블록을 곱하면 음의 게인이 되고, 그것이 '
          '음귀환이다. G<sub>EA</sub> 는 그 부호를 뺀 값으로 쓴다: G<sub>EA</sub> = '
          '&minus;v<sub>FB</sub>/v<sub>out</sub>.' % dict(f=FR('an_comp_opamp'))))
    add(fig('an_comp_opamp',
            'TL431 보상기를 op-amp 회로로: R<sub>I</sub> 와 Z<sub>f</sub> 가 '
            '반전 증폭기를 이루고, R<sub>B</sub>, R<sub>P</sub>, LED 가 캐소드 '
            '전압을 i<sub>LED</sub> 로 바꾸며, 옵토커플러는 R<sub>FB</sub> 와 '
            'C<sub>opto</sub> + C<sub>fx</sub> 로 전류를 흘리는 전류원 '
            'CTR&thinsp;i<sub>LED</sub> 다. 1차측과 2차측은 절연되어 있고 접지도 따로다.'))
    add(p('출력에서 FB 핀까지의 전달함수는 pole 이 하나 더 있는 Type&nbsp;II 회로다.'))
    add(eq(r'G_{EA}(s)=\frac{EA_{o}}{s}\cdot'
           r'\frac{1+s/\omega_{z}}{(1+s/\omega_{p})(1+s/\omega_{px})}',
           key='GEAtf'))
    add(eq([r'EA_{o}=\frac{CTR\;R_{FB}}{(C_{F}+C_{Fo})\,R_{I}\,R_{B}}\quad[\mathrm{rad/s}],'
            r'\qquad f_{z}=\frac{1}{2\pi R_{F}C_{F}}',
            r'f_{p}=\frac{1}{2\pi R_{F}C_{ser}},\quad C_{ser}=\frac{C_{F}C_{Fo}}{C_{F}+C_{Fo}},'
            r'\qquad f_{px}=\frac{1}{2\pi R_{FB}\,(C_{opto}+C_{fx})}'],
           key='fzp'))
    add(p('전체에서 &omega; = 2&pi;f 이고, C<sub>ser</sub> 는 C<sub>F</sub> 와 '
          'C<sub>Fo</sub> 의 직렬이다. C<sub>F</sub> + C<sub>Fo</sub> 가 원점 pole 을 만든다(정상 상태 오차 0). R<sub>F</sub>C<sub>F</sub> 가 위상을 회복시키는 zero f<sub>z</sub> 를 만든다. R<sub>F</sub> 와 C<sub>Fo</sub> 가 '
          '2f<sub>l</sub> 에서 게인을 낮추는 pole f<sub>p</sub> 를 만든다. '
          'C<sub>opto</sub> + C<sub>fx</sub> 와 R<sub>FB</sub> 가 kHz 근처의 셋째 pole f<sub>px</sub> 를 만들어 스위칭 노이즈를 거른다. CTR 이 게인 전체에 '
          '곱해지므로 그 편차가 중요하다.'))
    add(p('<b>바이어스 허용 범위.</b> LED 는 CTR 이 가장 낮을 때도 FB 핀을 정상 상태 '
          '전류로 구동해야 한다(상한). TL431 이 완전히 켜졌을 때 CTR 이 가장 '
          '높아도 핀의 최대 전류를 넘지 않아야 한다(하한). I<sub>FB,steady</sub> 와 '
          'I<sub>FB,max</sub> 가 그 두 FB 핀 전류다.'))
    add(eq([r'R_{B,max}=\frac{V_{Z}-(V_{R}+V_{Fo})}'
            r'{V_{Fo}/R_{P}+I_{FB,steady}/CTR_{s}}',
            r'R_{B,min}=\frac{V_{Z}-(V_{R}+V_{Fo})}'
            r'{V_{Fo}/R_{P}+I_{FB,max}/CTR_{m}}'], key='RBwin'))
    add(note('EA<sub>o</sub> 는 정상 상태 LED 전류에서의 CTR, CTR<sub>s</sub> '
             '를 쓴다. R<sub>B</sub> 의 하한은 최대 LED 전류에서의 CTR, '
             'CTR<sub>m</sub> 을 쓴다. 둘 다 실제로 실장할 랭크에서 가져온다. '
             '랭크의 위쪽 끝에서 루프를 다시 검사할 것. 그 근처에서 루프는 decade 당 '
             '20&nbsp;dB 에 가깝게 떨어진다. 그래서 crossover 주파수는 CTR 에 거의 '
             '비례해 오르고, phase margin 은 떨어진다.'))
    add(h2('zero 와 pole 배치: K-factor 법'))
    add(p('Venable 의 K-factor 법은 목표 둘에서 EA<sub>o</sub>, zero, pole 을 '
          '정한다. 목표는 phase margin &Phi;<sub>M</sub> 과 2f<sub>l</sub> 에서 '
          '허용되는 게인이다. phase margin 에서 K factor K<sub>v</sub> 가 나오고, '
          '&alpha;<sub>v</sub> 는 가중 상수다(ST 툴에서 1.2).'))
    add(eq(r'K_{v}=\frac{1}{2\alpha_{v}}\left[(1+\alpha_{v}^{2})\tan\Phi_{M}'
           r'+\sqrt{(1+\alpha_{v}^{2}\tan\Phi_{M})^{2}'
           r'+4\alpha_{v}^{2}}\;\right]', key='Kv'))
    add(p('zero 는 crossover 주파수의 K<sub>v</sub> 분의 1, pole 은 K<sub>v</sub> 배에 '
          '둔다. pole 위에서 게인은 EA<sub>o</sub>K<sub>v</sub>&sup2;/&omega; '
          '이므로, 2f<sub>l</sub> 의 한도가 EA<sub>o</sub> 를 정한다.'))
    add(eq(r'EA_{o}=\frac{2\pi\,(2f_{l})\,G_{EA}(2f_{l})}{K_{v}^{2}}',
           key='EAotarget'))
    add(p('중심 주파수는 플랜트 게인에서 정해진다. &Gamma;<sub>v</sub> = 0.744 '
          'V<sub>eq,max</sub>/V<sub>eq,min</sub> 은 ST 툴의 입력 전압 여유 '
          '계수다(부록&nbsp;%(a)s). 툴은 V<sub>eq,min</sub> 을 가장 낮은 등가 입력으로, '
          'V<sub>eq,max</sub> 를 가장 높은 등가 입력이 아니라 상용전원 최대값으로 잡는다:'
          % dict(a=SR('근거 없이 쓰인 상수'))))
    add(eq(r'f_{MB}=\frac{1}{2\pi}\sqrt{\frac{G_{o}K_{v}EA_{o}}{\Gamma_{v}}},'
           r'\qquad f_{p}=K_{v}f_{MB},\qquad f_{z}=\frac{f_{MB}}{K_{v}}', key='fMB'))
    add(p('부품은 식&nbsp;%(e)s 에서 따라 나온다. 고주파 pole 은 정한 '
          'f<sub>pHF</sub> 에 두고, C<sub>fx</sub> 는 옵토커플러 커패시턴스를 '
          '뺀 나머지다.' % dict(e=ER('fzp'))))
    add(eq([r'C_{Fo}=\frac{f_{z}}{f_{p}}\cdot\frac{CTR_{s}\,R_{FB}}{R_{I}R_{B}\,EA_{o}},'
            r'\qquad C_{F}=C_{Fo}\left(\frac{f_{p}}{f_{z}}-1\right)',
            r'R_{F}=\frac{1}{2\pi f_{z}C_{F}},'
            r'\qquad C_{fx}=\frac{1}{2\pi f_{pHF}\,R_{FB}}-C_{opto}'],
           key='Ccomp'))
    add(p('값마다 표준 부품으로 반올림한 뒤, 그 표준 부품이 주는 zero·pole·'
          '게인을 다시 계산해 그 값으로 루프를 검사한다.'))
    add(h2('루프 검사: crossover 주파수, phase margin, gain margin'))
    add(p('루프 게인(식&nbsp;%(a)s, %(b)s)은 적분기 둘, zero 하나, pole '
          '둘이다.' % dict(a=ER('Gplant'), b=ER('GEAtf'))))
    add(eq([r'|T(\omega)|=\frac{G_{o}\,EA_{o}}{\omega^{2}}\cdot'
            r'\frac{\sqrt{1+(\omega/\omega_{z})^{2}}}'
            r'{\sqrt{1+(\omega/\omega_{p})^{2}}\;\sqrt{1+(\omega/\omega_{px})^{2}}}',
            r'\arg T(\omega)=-180^{\circ}+\arctan\frac{\omega}{\omega_{z}}'
            r'-\arctan\frac{\omega}{\omega_{p}}-\arctan\frac{\omega}{\omega_{px}}'],
           key='Tloop'))
    add(p('&minus;180&deg; 는 적분기 둘의 몫이므로 <b>phase margin 은 crossover 주파수에서의 보상기 위상</b>이다. 식&nbsp;%(t)s 의 분수를 '
          'A(&omega;) 라 하면 교차 조건(&omega;<sub>c</sub>&sup2; = '
          'G<sub>o</sub>EA<sub>o</sub>A(&omega;<sub>c</sub>))은 다음 식을 몇 번 반복해 푼다.' % dict(t=ER('Tloop'))))
    add(eq(r'\omega_{c}\leftarrow\sqrt{G_{o}\,EA_{o}\,A(\omega_{c})},'
           r'\qquad\mathrm{starting\ from}\ \ \omega_{c}=\sqrt{G_{o}\,EA_{o}}',
           key='wc'))
    add(p('제곱근이 A 의 변화를 절반으로 줄이므로 반복할 때마다 오차가 절반 넘게 '
          '줄고, 수치 해석 도구는 필요 없다. 그다음'))
    add(eq(r'\Phi_{M}=\arctan\frac{\omega_{c}}{\omega_{z}}'
           r'-\arctan\frac{\omega_{c}}{\omega_{p}}'
           r'-\arctan\frac{\omega_{c}}{\omega_{px}}', key='PMeq'))
    add(p('그림&nbsp;%(f)s 에 세 숫자를 어디서 읽는지 보였다. 주파수를 루프의 crossover 주파수로 정규화했으므로 이런 루프 전부에 같은 모양이다. %(s)s 절이 이 설계의 값으로 같은 그림을 그린다.'
          % dict(f=FR('an_loop_example'), s=SR('전압 루프 설계 결과'))))
    add(fig('an_loop_example',
            '적분기 두 개와 Type II 보상기로 된 루프, crossover 주파수 단위. phase margin 은 '
            'f<sub>c</sub> 에서 &minus;180&deg; 까지의 거리, gain margin 은 '
            'f<sub>180</sub> 에서 0&nbsp;dB 아래의 |T| 다. 2f<sub>l</sub> 의 '
            '점이 3차 고조파 검사가 읽는 게인이다.'))
    add(h2('gain margin, 그리고 검사가 필요한 이유'))
    add(p('f<sub>px</sub> 위에서는 zero 하나에 pole 이 둘이므로 위상이 '
          '계속 떨어지고 <b>유한한 주파수에서 &minus;180&deg; 를 지난다</b>. '
          '이것도 반복 계산 없이 구한다.'))
    add(eq(r'f_{180}=\sqrt{\,f_{p}f_{px}-f_{z}(f_{p}+f_{px})\,}'
           r'\,,\qquad GM=-20\log_{10}|T(f_{180})|', key='f180'))
    add(p('zero 가 두 pole 보다 충분히 아래에 있으면 근은 실수이고, K-factor '
          '배치가 그렇게 만든다. 근호 안이 음수라면 위상이 모든 주파수에서 '
          '&minus;180&deg; 아래에 있으므로 어느 crossover 주파수에서도 phase margin 이 '
          '음이다. 6&nbsp;dB 를 하한으로, 10&nbsp;dB 를 여유 있는 값으로 판정한다. '
          'crossover 주파수가 수십 Hz 이면 여유는 보통 크다. 그래도 가정하지 말고 계산할 것.'))
    add(p('같은 식을 2f<sub>l</sub> 에서 계산해 식&nbsp;%(d)s 에 넣으면 3차 고조파가 나오고, 검사가 완결된다.' % dict(d=ER('D3'))))
    add(h2('버스트 threshold 에 대한 피드백 리플'))
    add(p('crossover 주파수가 이렇게 낮으면 FB 핀에 2f<sub>l</sub> 리플이 남고, '
          '그것이 반주기마다 지령 전력을 움직인다. 버스트 진입 threshold 를 넘으면 '
          '컨버터가 채터링한다. 버스트 점에서의 리플은'))
    add(eq(r'\Delta V_{FB}\;=\;\frac{P_{in,BM}}{V_{out}}\,'
           r'\frac{1}{2\pi f_{l}\,C_{out}}\;G_{EA}(2f_{l})', key='dVFB'))
    add(p('P<sub>in,BM</sub> 은 버스트 진입점의 입력 전력이다. R<sub>BM</sub> 을 낮추면 버스트 진입이 k&Omega; 당 0.01&nbsp;V 씩 '
          '그 리플 아래로 내려가고, 리플이 그 threshold 를 넘나들지 않아야 한다.'))
    add(eq(r'\Delta R_{BM}=\frac{\Delta V_{FB}}{2\times 0.01\ \mathrm{V/k\Omega}}',
           key='dRBM'))
    add(p('crossover 주파수를 올리면 리플은 줄지만 distortion 이 나빠지므로, '
          'R<sub>BM</sub> 이 현실적인 답이다.'))
    add(note('이렇게 느린 루프는 큰 부하 스텝에서 스스로 회복하지 못한다. '
             'anti-saturation 회로가 회복시키는데, 그러려면 FB 핀이 전류 범위 '
             '전체를 쓸 수 있어야 한다. R<sub>B</sub> 가 바이어스 범위 안에 있어야 하는 이유가 이것이다(식&nbsp;%(e)s).' % dict(e=ER('RBwin'))))

    # =============================================================== 6
    add(h1('설계 예제'))
    add(p('사양에서 부품값까지 하나의 설계를 따라간다. 계산값마다 계산 과정을 보인다. '
          '<b>90 ~ %(Vacmax).0f&nbsp;Vac 입력, %(Vout).0f&nbsp;V / '
          '%(Iout).1f&nbsp;A = %(Pout).1f&nbsp;W 출력</b>, 센터탭 동기 정류, '
          '벌크 커패시터 없음, boost 단 없음.' % V))
    add(h2('사양과 값의 종류'))
    add(p('각 값은 넷 중 하나다: 부하와 상용전원이 <b>주는</b> 값, 설계자가 '
          '<b>고르는</b> 값, 부품 <b>데이터시트</b>에서 읽은 값, 측정 전이라 '
          '<b>가정한</b> 값.'))
    ext(tbl('사양. 이 장의 나머지는 전부 여기서 계산한다.',
            [['항목', '기호', '값', '종류', '비고'],
             ['상용전원 입력', 'V<sub>ac</sub>, f<sub>l</sub>',
              '90 ~ %(Vacmax).0f Vac, %(flmin).0f ~ %(flmax).0f Hz' % V,
              '주어짐',
              '최악의 라인 주파수는 최저치이므로 모든 f<sub>l</sub> 항에 '
              '%(flmin).0f Hz 를 쓴다' % V],
             ['출력', 'V<sub>out</sub>, I<sub>out</sub>',
              '%(Vout).0f V, %(Iout).1f A  (%(Pout).1f W)' % V, '주어짐',
              'V<sub>o,eff</sub> = V<sub>out</sub> + N<sub>rect</sub>'
              'V<sub>f</sub> = %(Vout).1f V, V<sub>f</sub> = 0' % V],
             ['출력 리플, 2f<sub>l</sub> pk-pk', '&Delta;v',
              'V<sub>out</sub> 의 %(dv).0f %% 이하 (%(dVpp).2f V)'
              % dict(V, dVpp=V['Vout'] * V['dv'] / 100), '주어짐',
              '컨버터가 아니라 부하가 정하는 값'],
             ['hold-up', 'T<sub>hold</sub>, V<sub>o,min</sub>',
              '100 Vac 에서 %(Thold).0f ms, %(Vomin).0f V 까지' % V, '주어짐',
              '최악의 라인 위상인 리플 골에서 시작'],
             ['2차 정류기', 'N<sub>rect</sub>', '1 (센터탭, SR)',
              '선택',
              '정류기 도통 손실 절반, 소자 역전압 두 배'],
             ['목표 직렬 공진', 'f<sub>r</sub>', '%(frt).0f kHz' % V,
              '선택', '출발점. 최종 f<sub>r</sub> 은 트랜스포머의 누설이 정한다: '
              '%(fr).1f kHz(%(s)s 절)' % dict(V, s=SR('단계별 계산'))],
             ['사양 최대 f<sub>sw</sub>', 'f<sub>sw,max</sub>',
              '%(fswspec).0f kHz (%(fx).1f f<sub>r</sub>)' % dict(V, fx=V['fswspec'] / V['frt']), '선택',
              '&lambda; 의 입력, %s 절'
              % SR('f<sub>sw,max</sub> 는 검사값이 아니라 설계 입력이다')],
             ['브리지 데드타임', 't<sub>D</sub>', '%(tD).0f ns' % V, '선택',
              'ZVS 스윕이 넘어야 할 값'],
             ['V<sub>CC</sub> 공급', '&mdash;',
              '보조 권선 %(Naux)d T, 제너 레귤레이터 경유' % V,
              '선택', '외부 레일 없음. 핀을 정격 아래로 지키는 것은 권선비가 '
              '아니라 레귤레이터다'],
             ['LLC 단 효율', '&eta;<sub>HB</sub>',
              '%(etaHB).0f %%' % V, '가정',
              '95 %% 가 나와도 R<sub>ac</sub> 와 R<sub>CS</sub> 가 약 %.0f %% '
              '움직일 뿐, 이후 계산에 크게 영향을 주는 것은 없다' % (100 * (V['etaHB'] / 95.0 - 1))],
             ['오실레이터 idle 시간', 'T<sub>idle</sub>',
              '%(Tidle).0f ns' % V, '가정',
              '초안 데이터시트에서는 350 ns 와 700 ns 도 나온다. %s '
              '&mdash; 가장 먼저 잴 것' % _idle700_kr(V)],
             ['R<sub>DS(on)</sub> 온도 계수', 'k<sub>T</sub>',
              '%(Rdpk).1f / %(Rdsk).1f' % V, '데이터시트',
              '1차 / 2차, T<sub>j</sub> = 125&nbsp;&deg;C. 둘 다 데이터시트 '
              '곡선을 벡터로 읽음'],
             ['버스트 진입점', 'r<sub>BM</sub>',
              'P<sub>in</sub> 의 %(rBM).0f %% (%(PinBM).0f W)'
              % dict(V, rBM=A.SH['r.BM'] * 100), '가정',
              'R<sub>BM</sub> 을 정하고, 피드백 리플에 대해 검사'],
             ['1차 스위치', '&mdash;',
              'STO60N045DM9, 자리마다 1개, 모두 4개', '선택',
              '고속 회복 바디 다이오드를 가진 600&nbsp;V 슈퍼정션(%s 절)'
              % SR('1차 스위치: STO60N045DM9')],
             ['1차 게이트 전하와 출력 전하', 'Q<sub>g,10</sub>, '
              'C<sub>o(tr)</sub>',
              '%(Qg10).0f nC (0&ndash;10 V), %(Cosstr).0f pF (0&ndash;%(Vosstr).0f V)'
              % V, '데이터시트',
              'Q<sub>g</sub> 는 V<sub>CC</sub> 부하를, C<sub>o(tr)</sub> 는 '
              '데드타임이 덮어야 할 스윙을 정한다'],
             ['게이트 드라이버', '&mdash;',
              'L6498LD(SO-14) 2개, 레그당 1개, ES1J 부트스트랩 다이오드, '
              '게이트마다 1N4148W 턴오프 다이오드', '선택',
              '컨트롤러에는 드라이버가 없다(%s 절)'
              % SR('게이트 드라이버: L6498LD 2개')],
             ['SR MOSFET', '&mdash;',
              'STL160N10F8, 레그당 %(nSR).0f개, 모두 4개' % V, '선택',
              '100&nbsp;V STripFET F8(%s 절)'
              % SR('SR MOSFET: STL160N10F8')],
             ['동기 정류기', '&mdash;',
              'TEA2095TE', '선택',
              '연결과 한계만(%s 절)'
              % SR('동기 정류: TEA2095TE')],
             ['레귤레이터 부품', 'V<sub>BE</sub>, V<sub>D</sub>, '
              '&beta;<sub>min</sub>, I<sub>Z,min</sub>',
              '%(VFj).1f V, %(VFj).1f V, %(bmin).0f, %(IDZmin).0f mA' % V,
              '가정', '접합 전압은 가정값. 게인과 바이어스는 부품에 거는 '
              '요구 조건이고, 실장한 FZT651 과 BZT52H-C15 가 만족한다(%s 절)'
              % SR('보조 권선 V<sub>CC</sub> 설계 결과')],
             ['안전 조건', '&mdash;',
              '미국, EU, 일본, 한국, 중국; 가정용 AV; %d m'
              % _INS_ALT, '주어짐',
              '트랜스포머 절연을 정한다(%s 절)'
              % SR('이 트랜스포머의 안전 절연')],
             ['트랜스포머 구조', '&mdash;',
              '카탈로그 코일 포머에 칸막이를 더한 칸 권선: 한 칸에 삼중 절연 '
              'Litz 의 NP1, 다른 칸에 Litz 2차, 층마다 테이프',
              '선택', '절연은 전선이 맡는다. 권선창 모양과 칸막이가 '
              'L<sub>short</sub> 를 정한다(%s 절)'
              % SR('코어 고르기')],
             ['권선 계수', 'J, k<sub>litz</sub>, k<sub>w</sub>',
              '%.1f A/mm&sup2;, %.2f, %.2f; 삼중 절연 두께 %.1f mm'
              % (_CORE.J_CU, _CORE.K_LITZ, _CORE.K_WIND,
                 _CORE.TIW_LITZ_ADD), '가정',
              '트랜스포머의 동선 면적과 지름. k<sub>w</sub> 는 다발 지름에 대한 '
              '권선 피치로 첫 샘플에서 확인한다. 절연 두께는 전선 벤더 값']],
            widths=[CW * 0.20, CW * 0.12, CW * 0.21, CW * 0.11, CW * 0.36],
            key='spec-given', split=True))
    add(note('<b>고조파 등급.</b> IEC&nbsp;61000-3-2 Class&nbsp;D 는 '
             '600&nbsp;W 까지다. 이 설계는 입력 전력이 %(Pin).0f&nbsp;W 이므로 Class&nbsp;A 의 절대 한도가 적용된다.' % V))
    add(h2('주요 설계 값'))
    ext(tbl('주요 값. 각 값의 계산 과정은 이 장의 뒤에 있다.',
            [['블록', '값'],
             ['탱크', 'C<sub>r</sub> %(Cr).0f nF, L<sub>r</sub> %(Lr)g '
              '&micro;H, L<sub>m</sub> %(Lm)g &micro;H, '
              '&lambda; %(lam).3f, f<sub>r</sub> %(fr).1f kHz, '
              'f<sub>o</sub> %(fo).1f kHz' % V],
             ['트랜스포머', 'N<sub>p</sub>:N<sub>s</sub> '
              '%(NpSet)d:%(Ns)d, n %(n).3f, n<sub>T</sub> %(nT).2f, '
              'L<sub>open</sub> %(Lopen).1f &micro;H, '
              'L<sub>short</sub> %(Lshort).1f &micro;H, '
              'A<sub>e</sub> &ge; %(Aereq).0f mm&sup2; (B<sub>pk</sub> '
              '%(Bmx).2f T)' % dict(V, Bmx=_CORE.B_MAX)],
             ['주파수', '라인 피크, Full load 의 f<sub>sw</sub>: 낮은 코너에서 %(fswA).1f kHz, '
              '높은 코너에서 %(fswB).1f kHz' % V],
             ['출력', '%(Cout1).0f &micro;F &times; %(nC).0f = '
              '%(Cout).1f mF, 리플 %(dVo).2f V (%(dVopc).2f %%), '
              'hold-up %(thold).2f ms' % V],
             ['컨트롤러', 'R<sub>T</sub> %(RT)g k&Omega;, '
              'C<sub>T</sub> %(CT).0f pF, R<sub>CS</sub> %(RCS).1f m&Omega;, '
              'R<sub>CFG</sub> %(RCFG).0f k&Omega;, '
              'R<sub>BM</sub> %(RBM).0f k&Omega;' % V],
             ['루프', 'f<sub>c</sub> %(fcross).2f Hz, '
              '&Phi;<sub>M</sub> %(PM).1f&deg;, '
              '3차 고조파 %(D3).2f %%' % V],
             ['스위치', 'STO60N045DM9 &times; 4; L6498LD 2개, 턴온 '
              'R<sub>G</sub> %(RG).1f &Omega;, 턴오프 1N4148W + R<sub>G,off</sub> '
              '%(RGo).1f &Omega;, C<sub>BOOT</sub> %(CBOOT).0f nF 와 ES1J; '
              'TEA2095TE, 레그당 STL160N10F8 %(nSR).0f개'
              % dict(V, RGo=A._builder_const('R.G_off'))],
             ['V<sub>CC</sub>', 'N<sub>aux</sub> %d T, 제너 %.0f V, '
              'R<sub>BZ</sub> %.0f &Omega;, C<sub>VCC</sub> %.0f &micro;F, '
              'V<sub>CC,reg</sub> %.2f V'
              % (V['Naux'], V['DZ'], V['RBZ'], V['CVCC'], A.SH['V.CC_reg'])],
             ['V<sub>CC,SR</sub>', '출력에서 FZT651 팔로워로, 제너 %.0f V, '
              'R<sub>BSR</sub> %.0f &Omega;, R<sub>SR</sub> %.0f &Omega; 과 핀의 '
              '%.0f nF + %.1f &micro;F 병렬, V<sub>CC,SR</sub> %.1f V'
              % (A._builder_const('V.DZSR_sel'), A._builder_const('R.BSR_sel'),
                 A._builder_const('R.SR'), A._builder_const('C.SR'),
                 A._builder_const('C.SRb'), A.SH['V.SR'])],
             ['V<sub>Z</sub>', 'TL431B shunt 레귤레이터 Q6, R<sub>Z</sub> '
              '%.1f k&Omega; 로 공급, 분압기 %.1f / %.0f k&Omega;, %.2f V'
              % (A._builder_const('R.Z_sel') / 1e3,
                 A._builder_const('R.Z1'), A._builder_const('R.Z2'),
                 A.SH['V.Z'])],
             ['절연', '1차와 2차 사이 강화 절연, 삼중 절연선 NP1 과 NAUX 가 '
              '맡는다. 핀에서 clearance %.1f mm, creepage %.1f mm, '
              '%d V ac 60 s'
              % (_INS.req()['clearance'], _INS.req()['creep'],
                 _INS.req()['hipot_ac'])]],
            widths=[CW * 0.18, CW * 0.82], split=True))

    # ------------------------------------------------ 판정 여유란
    add(h2('판정 여유란 무엇인가'))
    add(p('모든 검사는 설계가 가진 값을 요구되는 값으로 나눈 비다.'))
    add(eq(r'k\;=\;\frac{X_{\mathrm{act}}}{X_{\mathrm{req}}}\qquad\Longrightarrow\qquad \mathrm{pass\;when}\;k>1', key='margin'))
    add(p('k&nbsp;=&nbsp;1.05 는 5 % 의 여유다. 가장 작은 k 가 설계의 가장 약한 곳이다.'))
    _kb = V['kPloss'] * A.SH['P.mos_dc']          # budget 을 되찾는다
    _ks = V['kPSR'] * A.SH['P.SR'] / 2.0
    ext(tbl('판정 여유.',
            [['검사', 'k = 실제값 / 요구값', '대입', 'k'],
             ['스윕 최악점의 ZVS',
              'T<sub>ZC,min</sub> / t<sub>D</sub>',
              '%(zTzc).0f ns / %(tD).0f ns' % dict(V, **ZVS_WORST),
              '%(zk).3f' % dict(V, **ZVS_WORST)],
             ['오실레이터 하한이 아래쪽 공진을 넘는가',
              'f<sub>Min</sub> / f<sub>o</sub>',
              '%(fMin).2f kHz / %(fo).2f kHz' % V, '<b>%(kfloor).3f</b>' % V],
             ['오실레이터 상한이 최고 동작 주파수를 넘는가',
              'f<sub>Max</sub> / f<sub>sw</sub>(FB 경계, 라인 피크)',
              '%(fMax).2f kHz / %(fswmaxop).2f kHz' % V, '%(kceil).3f' % V],
             ['과전류 threshold 가 탱크 피크를 넘는가',
              'I<sub>OCP1</sub> / I<sub>Lr,pk</sub>',
              '%(I).2f A / %(Icomp).2f A' % dict(V, I=A.SH['I.OCP1']),
              '%(kOCP).3f' % V],
             ['달성 hold-up 대 요구 hold-up',
              't<sub>hold</sub> / T<sub>hold</sub>',
              '%(thold).2f ms / %(Thold).0f ms' % V, '%(khold).3f' % V],
             ['정류 레그당 2차 손실 대 budget',
              'P<sub>budget</sub> / P<sub>SR,leg</sub>',
              '%(b).2f W / %(a).2f W' % dict(b=_ks, a=A.SH['P.SR'] / 2.0),
              '%(kPSR).3f' % V],
             ['고정 1차 소자의 손실 대 budget',
              'P<sub>budget</sub> / P<sub>mos,dc</sub>',
              '%(b).2f W / %(a).2f W' % dict(b=_kb, a=A.SH['P.mos_dc']),
              '<b>%(kPloss).3f</b>' % V],
             ['V<sub>CC</sub> 가 기동 threshold 위에 머무는가',
              'V<sub>CC,reg,min</sub> / V<sub>CC,HVSUon</sub>',
              '%.2f V / %.0f V' % (A.SH['V.CC_reg_min'], V['VCCHV']),
              '%.3f' % A.SH['k.VCClo']],
             ['hold-up 끝에서도 제너 공급이 레귤레이션하는가',
              'R<sub>BZ,max</sub> / R<sub>BZ</sub>',
              '%.0f &Omega; / %.0f &Omega;' % (A.SH['R.BZ_max'], V['RBZ']),
              '%.3f' % A.SH['k.RBZ']],
             ['C<sub>VCC</sub> 가 기동 인계 구간을 버티는가',
              'C<sub>VCC</sub> / C<sub>VCC,req</sub>',
              '%.0f &micro;F / %.0f &micro;F' % (V['CVCC'], A.SH['C.VCC_req']),
              '<b>%.3f</b>' % A.SH['k.CVCC']],
             ['하이사이드 드라이버 전원이 범위 안에 머무는가',
              'V<sub>BO</sub> / V<sub>BO,min</sub>',
              '%.2f V / %.1f V' % (A.SH['V.BO_run'], V['VBOrec']),
              '%.3f' % A.SH['k.VBO']],
             ['게이트에 남는 데드타임이 스윙을 덮는가',
              '(t<sub>D</sub> &minus; MT) / T<sub>T</sub>',
              '%.0f ns / %.0f ns' % (V['tD'] - V['MT'], A.SH['T.T']),
              '%.3f' % A.SH['k.TTd']],
             ['중점 기울기가 드라이버 한계 아래인가',
              'S<sub>OUT,max</sub> / S<sub>mid</sub>',
              '%.0f V/ns / %.1f V/ns' % (V['dvmax'], A.SH['dv.dt']),
              '%.3f' % A.SH['k.dvdt']],
             ['게이트 드라이버 손실이 정격 안인가',
              'P<sub>drv,max</sub> / P<sub>drv</sub>',
              '%.0f W / %.3f W' % (V['Pdrvmax'], A.SH['P.drv']),
              '%.3f' % A.SH['k.Pdrv']],
             ['SR 게이트 구동이 R<sub>DS(on)</sub> 시험 전압에 닿는가',
              'V<sub>G,SR</sub> / 10 V',
              '%.1f V / 10 V' % V['VGSR'],
              '<b>%.3f</b>' % A.SH['k.VGSR']]],
            widths=[CW * 0.34, CW * 0.18, CW * 0.26, CW * 0.10],
            key='margins', split=True))
    add(note('k<sub>Ploss</sub> = %(kPl)s 계산 실패가 아니라 결과다. '
             '고정된 1차 소자가 %(b).0f&nbsp;W budget 에 대해 %(a).2f&nbsp;W 를 '
             '소모한다. 고정 소자 위치에서 그 budget 을 만족하는 단일 600&nbsp;V '
             '소자는 없다. 그래서 설계는 히트싱크를 전제로 진행하고(%(hs)s 절), '
             '나머지는 실측으로 정한다(%(ref)s 절). %(thin)s SR 게이트 구동의 '
             'k = %(kvg)s 구조상 작다. SR 컨트롤러가 게이트 구동을 '
             '%(vg).1f&nbsp;V 에 클램프하고 SR R<sub>DS(on)</sub> 은 10&nbsp;V '
             '에서 주어지므로, 클램프가 시험 전압만 넘으면 된다. '
             'k<sub>floor</sub> = %(kfl)s 모르는 값에 기대고 있다. 트랜스포머 '
             '공차와 idle 시간이 둘 다 이 값을 움직이는데, 어느 쪽도 아직 재지 '
             '않았다.'
             % dict(V, a=A.SH['P.mos_dc'], b=_kb, vg=V['VGSR'],
                    kvg=_nj('%.3f' % A.SH['k.VGSR'], '은', '는'),
                    hs=SR('1차 스위치: STO60N045DM9'),
                    thin=_thinnest_kr(V, A),
                    ref=SR('하드웨어에서 먼저 잴 것'),
                    kPl=_nj('%.3f' % V['kPloss'], '은', '는'),
                    kfl=_nj('%.3f' % V['kfloor'], '은', '는'))))

    # ------------------------------------------------ 사슬, 단계별로
    add(h2('단계별 계산'))
    add(p('계산 순서대로 정리한 설계. 단계마다 식과 대입한 값을 보인다. '
          '결과는 표&nbsp;%s 에 모았다.' % TR('chain')))
    _SH = A.SH
    _rt = (1 + V['lam']) ** 0.5
    # -- 전력
    add(p('<b>STEP 1 &mdash; 탱크에 들어가는 전력.</b> 브리지, EMI 필터, '
          'LLC 단에 각각 손실 budget 을 할당하고, LLC 단의 budget 은 '
          '&eta;<sub>HB</sub> 로 정한다.'))
    add(calc(r'P_{in}=P_{out}+P_{LLC}+P_{EMI}+P_{BR}'
             r'=%.1f+%.2f+%.2f+%.2f=\mathbf{%.1f\ W}'
             % (V['Pout'], _SH['P.d_LLC'], _SH['P.d_EMI'], _SH['P.d_BR'],
                V['Pin'])))
    add(calc(r'P_{in,LLC}=P_{in}-P_{BR}-P_{EMI}=%.1f-%.2f-%.2f'
             r'=\mathbf{%.1f\ W}'
             % (V['Pin'], _SH['P.d_BR'], _SH['P.d_EMI'], _SH['P.in_LLC'])))
    # -- 코너
    add(p('<b>STEP 2 &mdash; 등가 입력의 두 코너.</b> 상용전원의 한계가 아니라 '
          '모핑 threshold 다.'))
    add(eqagain('Veq'))
    add(calc(r'V_{ac,eq,low}=\frac{245\ \mathrm{V_{pk}}}{\sqrt{2}}'
             r'=\mathbf{%.1f\ V_{ac}}\qquad '
             r'V_{ac,eq,high}=\frac{2\times 235\ \mathrm{V_{pk}}}{\sqrt{2}}'
             r'=\mathbf{%.1f\ V_{ac}}' % (V['Veqlo'], V['Veqhi'])))
    # -- 권선비
    add(p('<b>STEP 3 &mdash; 권선비.</b> 입력은 실제 턴수 비 %(NpSet)d:%(Ns)d%(j)s. 실제로 감을 수 있는 비이기 때문이다(계산값은 '
          'n = %(ncalc).3f). 모델 비 n 은 그 결과로 얻는 &lambda; 와 함께 정해진다(STEP 8).'
          % dict(V, ncalc=_SH['n.calc'], j=' ' + _josa(V['Ns'], '이다', '다'))))
    add(eqagain('nnT'))
    add(calc(r'n=\frac{n_{T}}{\sqrt{1+\lambda_{act}}}=\frac{%.3f}{%.4f}'
             r'=\mathbf{%.3f}' % (V['nT'], _rt, V['n'])))
    add(eqagain('Vrefl'))
    add(calc(r'V_{refl}=n\,V_{o,eff}=%.3f\times %.1f=\mathbf{%.1f\ V}'
             % (V['n'], V['Vout'], V['Vrefl'])))
    # -- 요구 게인
    add(p('<b>STEP 4 &mdash; 탱크에 요구되는 게인</b>, 각 코너의 라인 피크'
          '(&theta; = 90&deg;)에서: 낮은 코너의 M<sub>low</sub>, 높은 코너의 M<sub>high</sub>.'))
    add(eqagain('Mreq'))
    add(calc(r'M_{low}=\frac{2\times %.3f\times %.1f}{\sqrt{2}\times %.2f}'
             r'=\mathbf{%.4f}\qquad '
             r'M_{high}=\frac{2\times %.3f\times %.1f}{\sqrt{2}\times %.2f}'
             r'=\mathbf{%.4f}'
             % (V['n'], V['Vout'], V['Veqlo'], _SH['M.HBmin'],
                V['n'], V['Vout'], V['Veqhi'], _SH['M.FBthr'])))
    # -- 부하
    add(p('<b>STEP 5 &mdash; 탱크가 보는 부하.</b> 교과서의 8 이 아니라 4 다. '
          'P<sub>in,LLC</sub> 가 라인 피크 전력이기 때문이다(%s 절).'
          % SR('공진 탱크')))
    add(eqagain('Rac'))
    add(calc(r'R_{ac}=\frac{4}{\pi^{2}}\,\frac{%.3f^{2}\times %.1f^{2}}{%.1f}'
             r'=\mathbf{%.2f\ \Omega}'
             % (V['n'], V['Vout'], _SH['P.in_LLC'], V['Rac'])))
    # -- Q 한도와 임피던스
    add(p('<b>STEP 6 &mdash; Q 한도와 설계 임피던스.</b> 낮은 코너에서, 탱크가 M<sub>low</sub> 를 낼 수 있는 최대 Q 와, ZVS 가 t<sub>D</sub> 안에 끝나는 최대 Q 중 작은 쪽을 쓴다(식&nbsp;%s). 설계 임피던스 Z<sub>0,design</sub> 이 거기서 나온다.' % ER('Qdef')))
    add(calc(r'Q_{ZVS}=\mathbf{%.4f}\qquad '
             r'Z_{0,design}=R_{ac}\,Q_{ZVS}=%.2f\times %.4f'
             r'=\mathbf{%.2f\ \Omega}'
             % (V['QZVS'], V['Rac'], V['QZVS'], V['Z0'])))
    # -- Cr, Lr
    add(p('<b>STEP 7 &mdash; C<sub>r</sub> 과 L<sub>r</sub>.</b> C<sub>r</sub> '
          '은 Q 여유를 위해 일부러 <b>크게</b> 잡는다. 목표 f<sub>r</sub> 에서 '
          '<i>선정한</i> C<sub>r</sub> 과 짝이 되는 L<sub>r</sub> 을 아래에서 계산한다. '
          '실제로 쓰는 L<sub>r</sub> 은 트랜스포머의 누설이고(%s 절), f<sub>r</sub> 은 '
          '그것을 따른다:' % SR('코어 고르기')))
    add(eqagain('fr'))
    add(calc(r'C_{r}=\frac{1}{2\pi f_{r}Z_{0,design}}'
             r'=\frac{1}{2\pi\times %.0f\ \mathrm{kHz}\times %.2f\ \Omega}'
             r'=%.2f\ \mathrm{nF}\ \rightarrow\ \mathbf{%.0f\ nF}'
             % (V['frt'], V['Z0'], V['Crc'], V['Cr'])))
    add(calc(r'L_{r}=\frac{1}{(2\pi f_{r})^{2}C_{r}}'
             r'=\frac{1}{(2\pi\times %.0f\ \mathrm{kHz})^{2}\times %.0f\ \mathrm{nF}}'
             r'=%.2f\ \mu\mathrm{H}\ \rightarrow\ \mathbf{%g\ \mu H}'
             % (V['frt'], V['Cr'], V['Lrc'], V['Lr'])))
    # -- λ 와 Lm
    add(p('<b>STEP 8 &mdash; &lambda; 와 L<sub>m</sub>.</b> &lambda; 후보 넷 '
          '중 가장 큰 것이 결정한다.'))
    add(eqagain('lam'))
    add(calc(r'\lambda_{1}=%.3f\,,\quad \lambda_{2}=%.3f\,,\quad '
             r'\lambda_{3}=%.3f\,,\quad '
             r'\lambda_{TD}=\mathbf{%.3f}\quad\Longrightarrow\quad '
             r'L_{m}=\frac{L_{r}}{\lambda_{TD}}=\frac{%g}{%.3f}'
             r'=%.2f\ \mu\mathrm{H}'
             % (_SH['λ.1'], _SH['λ.2'], _SH['λ.3'], _SH['λ.TD'], V['Lr'], _SH['λ.TD'],
                V['Lmc'])))
    add(p('그 %(Lmc).1f&nbsp;&micro;H 는 높은 코너의 No load 조건인데, 이 '
          '설계는 그것을 알고도 만족시키지 않으므로(%(ref)s 절) 그 값에 맞추지 않는다. L<sub>m</sub> 은 n 과 함께 n<sub>T</sub> 가 실제로 감을 수 있는 비가 되도록 고른다.'
          % dict(V, ref=SR('&lambda; 의 반대쪽 한계, 그리고 해가 없는 경우'))))
    add(calc(r'L_{m}=\mathbf{%g\ \mu H}\qquad '
             r'\lambda_{act}=\frac{L_{r}}{L_{m}}=\frac{%g}{%g}'
             r'=\mathbf{%.3f}' % (V['Lm'], V['Lr'], V['Lm'], V['lam'])))
    # -- 실현값
    add(p('<b>STEP 9 &mdash; 선정한 부품으로 얻는 값.</b> 이후 모든 검사는 이 값을 쓴다.'))
    add(eqagain('fo'))
    add(calc(r'f_{r}=\frac{1}{2\pi\sqrt{%g\ \mu\mathrm{H}\times %.0f\ \mathrm{nF}}}'
             r'=\mathbf{%.1f\ kHz}\qquad '
             r'f_{o}=\frac{1}{2\pi\sqrt{%g\ \mu\mathrm{H}\times %.0f\ \mathrm{nF}}}'
             r'=\mathbf{%.1f\ kHz}'
             % (V['Lr'], V['Cr'], V['fr'], V['Lr'] + V['Lm'], V['Cr'], V['fo'])))
    add(calc(r'Z_{0}=\sqrt{\frac{%g\ \mu\mathrm{H}}{%.0f\ \mathrm{nF}}}'
             r'=%.2f\ \Omega\qquad '
             r'Q_{pk}=\frac{Z_{0}}{R_{ac}}=\frac{%.2f}{%.2f}=\mathbf{%.3f}'
             % (V['Lr'], V['Cr'], V['Z0s'], V['Z0s'], V['Rac'], V['Qpk'])))
    add(calc((r'n_{T}=n\sqrt{1+\lambda_{act}}=%.3f\times %.4f=\mathbf{%.3f}'
              % (V['n'], _rt, V['nT']))
             + (r'\ =\ %d:%d' % (V['NpSet'], V['Ns']) if V['nser'] == 1 else
                r'\ =\ %d:%d\ \mathrm{across\ the\ assembly},\ %d:%d\ \mathrm{per\ unit}'
                % (V['NpSet'], V['Ns'], V['Np'], V['Ns']))))
    ext(tbl('단계별 설계 결과. a &rarr; b 에서 a 는 계산값, b 는 선정한 부품값이다.',
            [['단계', '항목', '식', '결과'],
             ['1', 'P<sub>in</sub>, P<sub>in,LLC</sub>', '&mdash;',
              '%(Pin).1f W, %(PL).1f W' % dict(V, PL=_SH['P.in_LLC'])],
             ['2', 'V<sub>ac,eq</sub>, 낮은·높은 코너', ER('Veq'),
              '%(Veqlo).1f, %(Veqhi).1f Vac' % V],
             ['3', 'n, V<sub>refl</sub>', ER('nnT') + ', ' + ER('Vrefl'),
              '%(n).3f, %(Vrefl).1f V' % V],
             ['4', 'M<sub>low</sub>, M<sub>high</sub>', ER('Mreq'),
              '%(a).4f, %(b).4f' % dict(a=_SH['M.HBmin'], b=_SH['M.FBthr'])],
             ['5', 'R<sub>ac</sub>', ER('Rac'), '%(Rac).2f &Omega;' % V],
             ['6', 'Q<sub>ZVS</sub>, Z<sub>0,design</sub>', ER('Qdef'),
              '%(QZVS).4f, %(Z0).2f &Omega;' % V],
             ['7', 'C<sub>r</sub>, L<sub>r</sub>', ER('fr'),
              '%(Crc).1f &rarr; %(Cr).0f nF, %(Lrc).2f &rarr; %(Lr)g '
              '&micro;H' % V],
             ['8', '&lambda;<sub>req</sub>, L<sub>m</sub>, '
              '&lambda;<sub>act</sub>', ER('lam'),
              '%(lTD).3f, %(Lm)g &micro;H, %(lam).3f'
              % dict(V, lTD=_SH['λ.TD'])],
             ['9', 'f<sub>r</sub>, f<sub>o</sub>, Q<sub>pk</sub>, '
              'n<sub>T</sub>', ER('fr') + ', ' + ER('fo') + ', ' + ER('Qdef'),
              '%(fr).1f kHz, %(fo).1f kHz, %(Qpk).3f, %(nT).3f' % V]],
            widths=[CW * 0.07, CW * 0.36, CW * 0.14, CW * 0.43],
            key='chain', split=True))
    add(note('<b>STEP 7 과 8 에서 설계자의 판단이 들어간다.</b> C<sub>r</sub> 은 '
             '계산값 %(Crc).1f 대신 %(Cr).0f&nbsp;nF 을 골랐다: 커패시터가 크면 '
             'Q<sub>pk</sub> 가 낮아지고, ZVS 여유가 여기서 나온다. '
             'L<sub>m</sub> 은 %(Lmc).1f 대신 %(Lm)g&nbsp;&micro;H 를 골랐다: '
             '감는 비 %(NpSet)d:%(nsj)s 탱크에 필요한 n 이 나오게 하는 값이고, '
             '그 대신 No load 해를 포기한다(다음 주석).'
             % dict(V, nsj=_nj(V['Ns'], '으로', '로'))
             + ('' if abs(V['Lr'] / V['Lrc'] - 1) < 0.10 else
                ' L<sub>r</sub> 은 %(Lrc).2f 대신 %(Lr)g&nbsp;&micro;H 다: 채워진 '
                '트랜스포머 권선창의 누설이 그 값이다(%(ref)s 절). 그래서 '
                'f<sub>r</sub> 은 목표 %(frt).0f&nbsp;kHz 에서 %(fr).1f&nbsp;kHz 로 '
                '내려가고, L<sub>m</sub> 은 &lambda; 를 그에 맞춰 유지한다.'
                % dict(V, ref=SR('코어 고르기')))))
    if V['fnl'] is not None:
        add(note('<b>No load 해.</b> 이 탱크의 No load 게인은 M<sub>&infin;</sub> = %(mi)s 하한이고, 높은 코너의 요구는 %(MFBmax).4f '
                 '이므로 약 %(fnl).0f&nbsp;kHz 에 해가 있다(%(ref)s 절).'
                 % dict(V, ref=SR('&lambda; 의 반대쪽 한계, 그리고 해가 없는 '
                                  '경우'),
                        mi=_nj('%.4f' % V['Minf'], '이', '가'))))
    else:
        add(note('<b>No load 해: 없음.</b> 이 탱크의 No load 게인은 '
                 'M<sub>&infin;</sub> = %(mi)s 하한인데, 높은 코너의 '
                 '요구는 그보다 낮은 %(MFBmax).4f 이다. No load 에서 그 게인에 '
                 '닿는 주파수는 없고, 차이가 1 %% 미만이라 Full load 검사로는 '
                 '보이지 않는다. 그 영역은 버스트 모드의 몫이다(%(ref)s 절).'
                 % dict(V, ref=SR('&lambda; 의 반대쪽 한계, 그리고 해가 없는 '
                                  '경우'),
                        mi=_nj('%.4f' % V['Minf'], '이', '가'))))
    add(h2('운전 영역 전체의 ZVS'))
    add(p('%(zref)s 절의 닫힌 식은 이 탱크에서 %(TzcCF).0f&nbsp;ns 를 주는데, 스윕은 '
          '%(Tzc).0f&nbsp;ns 다(%(mag).0f&nbsp;%% 보수적). 이 프로젝트에서 계산한 다른 '
          '탱크에서도 수십 %% 낮게 나왔지만, 그것이 다른 탱크를 보증하지는 않는다. 설계 &lambda; = %(lamreq).3f 대신 '
          '&lambda;<sub>act</sub> = %(la)s 읽으면 %(act)s'
          '&nbsp;ns, inductive 탱크를 capacitive 로 판정한다. 이 설계는 '
          '스윕으로 판정한다.'
          % dict(V, zref=SR('ZVS 검증'), mag=abs(V['TzcCFpc']),
                 lamreq=A.SH['λ'], act=_minus(V['TzcCFact'], '%.0f'),
                 la=_nj('%.3f' % V['lam'], '으로', '로'))))
    add(p('Full load 곡선의 capacitive 경계(arg Z<sub>in</sub> = 0)는 '
          '%(fnEdge).1f&nbsp;kHz 다. 게인 피크는 그보다 낮은 '
          '%(fnPk).1f&nbsp;kHz 이고, 거기에는 아직 %(phPk).1f&deg; 의 capacitive '
          '위상이 남아 있다(%(ref)s 절). 어느 쪽도 판정에는 쓰지 않는다.'
          % dict(V, ref=SR('두 경계는 같은 경계가 아니다'),
                 **_edge_numbers(A))))
    add(tbl('부하와 입력 전압마다 라인 반주기에서 가장 작은 '
            'T<sub>ZC,min</sub>, 단위 ns. FB 는 풀브리지(탱크에는 상용전원의 '
            '두 배), HB 는 하프브리지. t<sub>D</sub>&nbsp;=&nbsp;'
            '%(tD).0f&nbsp;ns.' % V,
            ZVS_WORST['rows'], widths=[CW * 0.10] + [CW * 0.15] * 6,
            key='zvsgrid'))
    _z = dict(V, t=TR('zvsgrid'), **ZVS_WORST)
    _z.update(zk_j=' ' + _josa('%.2f' % _z['zk'], '이다', '다'),
              ck_j=' ' + _josa('%.2f' % _z['ck'], '이다', '다'))
    if ZVS_WORST['same']:
        add(p('표&nbsp;%(t)s 의 최악점은 HB 경계의 Full load, '
              '<b>T<sub>ZC</sub>&nbsp;=&nbsp;%(zTzc).0f&nbsp;ns 대 '
              't<sub>D</sub>&nbsp;=&nbsp;%(tD).0f&nbsp;ns</b>, 여유 %(zk).2f 배다 '
              '&mdash; 탱크를 설계한 바로 그 코너다.' % _z))
    else:
        add(p('<b>최악점은 탱크를 설계한 코너가 아니다.</b> HB 경계의 '
              'Full load 는 <i>게인</i> 요구가 정해지는 곳이고, 거기서는 '
              'T<sub>ZC</sub>&nbsp;=&nbsp;%(cTzc).0f&nbsp;ns, 여유 %(ck).2f%(ck_j)s. '
              '표&nbsp;%(t)s 에서 가장 작은 숫자는 <b>%(zAt)s 의 %(zLoad).0f&nbsp;%% '
              '부하, %(zTzc).0f&nbsp;ns</b>, '
              't<sub>D</sub>&nbsp;=&nbsp;%(tD).0f&nbsp;ns 에 대해 여유 %(zk).2f'
              '%(zk_j)s. 이 설계의 ZVS 판정은 이 값으로 한다.'
              % dict(_z, zAt=_where(ZVS_WORST['zVin'], A.R, fb='FB 경계(풀브리지 %.0f&nbsp;Vac, 탱크에는 %.0f&nbsp;Vac)', hb='HB 경계(하프브리지 %.0f&nbsp;Vac)', other='%.0f&nbsp;Vac'))))
        add(note('<b>높은 입력 전압의 Light load 가 ZVS 코너가 될 수 있는 이유.</b> '
                 '브리지 노드 전압을 스윙시키는 전하는 자화 전류가 옮기고, 그 피크는 '
                 'n&thinsp;V<sub>o,eff</sub>/(4f<sub>sw</sub>L<sub>m</sub>) 에 비례한다(이 코너가 도는 above 영역에서). '
                 '부하가 줄면 컨트롤러가 게인을 줄이려고 f<sub>sw</sub> 를 '
                 '올리므로, 충방전할 커패시턴스는 그대로인데 그 '
                 '전류가 줄어든다. 설계 코너만 보면 실제로 없는 여유를 있다고 판단하게 된다.'))
    add(h2('이 설계의 게인 차트'))
    add(p('그림&nbsp;%(f)s 에 %(s)s 절의 차트를 이 탱크'
          '(&lambda;<sub>act</sub>&nbsp;=&nbsp;%(lam).3f, Q<sub>pk</sub>&nbsp;='
          '&nbsp;%(Qpk).3f)로 그렸고, 입력 전압마다 패널 하나다: 모핑 '
          '경계 둘과 실제 상용전원 전압 넷. 패널마다 상용전원 전압과 브리지 '
          '구성을 적었고, 풀브리지에서는 탱크에 상용전원의 두 배가 걸리므로 '
          '탱크가 보는 전압도 함께 적었다. 곡선은 모든 '
          '패널에서 같고 요구 게인 선만 움직인다. 표시한 교차점이 스윕에 쓴 동작점이다.'
          % dict(V, s=SR('single-stage 컨버터의 게인 차트 읽는 법'),
                 f=FR('an_gain_design'))))
    add(fig('an_gain_design',
            '이 설계의 게인 차트, 여섯 입력 전압을 탱크가 보는 전압이 낮은 것부터. '
            '왼쪽 위는 HB 경계(하프브리지 %(lo).0f&nbsp;Vac): 요구 게인이 가장 '
            '높고 교차점은 f<sub>r</sub> 아래. 오른쪽 아래는 FB 경계(풀브리지 '
            '%(fb).0f&nbsp;Vac, 탱크에는 %(hi).0f&nbsp;Vac): 요구 게인이 가장 '
            '낮고 교차점은 f<sub>r</sub> 위. 위상마다 같은 색의 점선과만 비교한다.'
            % dict(lo=V['Veqlo'], hi=V['Veqhi'], fb=V['Veqhi'] / 2), width=CW))
    _gp = _GAIN.gain_points(A.R)
    import l6790 as _L
    _cn = {veq: _kc(nm) for nm, veq, _m in _L.line_conditions(A.R)}
    _byv = [[g for g in _gp if abs(g[0] - veq) < 1e-6]
            for _nm, veq, _m in _L.line_conditions(A.R)]
    _lo = [g for g in _gp if abs(g[0] - A.R['Vin_min']) < 1e-6]
    _hi = [g for g in _gp if abs(g[0] - A.R['Vin_FBmax']) < 1e-6]
    ext(tbl('그림&nbsp;%(s)s 에 표시한 교차점, 모든 입력 전압에서. '
            'Q&nbsp;=&nbsp;Q<sub>pk</sub>&thinsp;sin&sup2;&thinsp;&theta;, '
            'M<sub>req</sub>&nbsp;=&nbsp;M<sub>pk</sub>/sin&thinsp;&theta; 이고, '
            'M<sub>pk</sub> 는 1/V<sub>ac,eq</sub> 로 HB 경계의 %(a).3f 에서 FB '
            '경계의 %(b).3f 까지 내려간다.'
            % dict(a=V['MVmin'], b=V['MFBmax'], s=FR('an_gain_design')),
            [['입력 전압', '&theta;', 'Q(&theta;)',
              'M<sub>req</sub>(&theta;)', 'f<sub>sw</sub>/f<sub>r</sub>',
              'f<sub>sw</sub>']]
            + [[_cn[v] if i == 0 else '',
                '%.0f&deg;' % (th * 180.0 / 3.141592653589793),
                '%.3f' % q, '%.3f' % mr,
                '&mdash;' if fn is None else '%.3f' % fn,
                '&mdash;' if fs is None else '%.1f kHz' % fs]
               for rows in _byv
               for i, (v, th, q, mr, fn, fs) in enumerate(rows)],
            widths=[CW * 0.26, CW * 0.09, CW * 0.13, CW * 0.18, CW * 0.17,
                    CW * 0.17],
            key='gainpts', split=True))
    add(p('읽을 점은 넷이다.'))
    ext(bullets([
        '<b>HB 경계가 탱크를 정한다.</b> 하프브리지 %(lo).0f&nbsp;Vac 는 탱크가 '
        '보는 가장 낮은 전압이므로 그 라인 피크 요구 게인 M<sub>pk</sub>&nbsp;=&nbsp;%(m)s '
        '여섯 조건 중 가장 크다. f<sub>sw</sub>/f<sub>r</sub>&nbsp;='
        '&nbsp;%(fn).3f 에서 만족되고, M<sub>Z</sub> 오른쪽으로 여유가 충분하다: '
        'inductive.' % dict(lo=V['Veqlo'], fn=_lo[0][4],
                            m=_nj('%.3f' % V['MVmin'], '이', '가')),
        '<b>FB 경계가 주파수를 정한다.</b> 풀브리지 %(fb).0f&nbsp;Vac 에서는 '
        '탱크에 %(hi).0f&nbsp;Vac 가 걸린다. 탱크가 보는 가장 높은 전압이고, 라인 '
        '피크 교차점은 %(f).0f&nbsp;kHz 이고, 상용전원 최대가 아니라 이것이 '
        '오실레이터 상한이 넘어야 할 값이다(%(o)s 절).'
        % dict(hi=V['Veqhi'], fb=V['Veqhi'] / 2, f=_hi[0][5] or 0.0,
               o=SR('오실레이터: C<sub>T</sub> 먼저, 그다음 R<sub>T</sub>')),
        '<b>상용전원 전압 넷은 두 경계 사이에 있다.</b> 풀브리지의 90&nbsp;Vac'
        '는 탱크에 2 &times; 90 = 180&nbsp;Vac 를 걸고, HB 경계보다 '
        '%(p90).0f&nbsp;%% 위일 뿐이다. 그래서 90&nbsp;Vac 쪽은 게인 최악 조건 가까이에서 '
        '돈다. 풀브리지의 110&nbsp;Vac(탱크에는 220&nbsp;Vac)와 하프브리지의 '
        '230&nbsp;Vac(탱크에도 230&nbsp;Vac)는 %(p23).0f&nbsp;%% 차이다. 모핑 '
        '덕분에 두 상용전원 계통이 탱크에는 거의 같게 보인다. 하프브리지의 '
        '264&nbsp;Vac 는 FB 경계에서 탱크가 보는 전압보다 아직 %(p264).0f&nbsp;%% '
        '아래다.'
        % dict(p90=100 * (180.0 / V['Veqlo'] - 1),
               p23=100 * (230.0 / 220.0 - 1),
               p264=100 * (1 - 264.0 / V['Veqhi'])),
        '<b>FB 경계는 &lambda; 도 판정한다.</b> 거기서 라인 피크 요구는 '
        '%(mm).3f 이고 No load 하한은 M<sub>&infin;</sub>&nbsp;=&nbsp;%(mi).3f '
        '이다. 그보다 낮으므로 No load 해가 없고 버스트 모드가 맡는다'
        '(%(l)s 절).'
        % dict(mm=V['MFBmax'], mi=V['Minf'],
               l=SR('&lambda; 의 반대쪽 한계, 그리고 해가 없는 경우'))]))
    add(note('여섯 패널은 여섯 설계가 아니라 한 축 위의 여섯 지점이다. 곡선은 '
             '입력 전압에 무관하다: M(f<sub>n</sub>,&nbsp;Q) 는 '
             '&lambda;<sub>act</sub> 와 Q<sub>pk</sub> 가 고정한다. <b>입력 전압은 M<sub>req</sub> 를 통해서만 반영된다.</b>'))
    add(h2('이 설계는 공진의 어느 쪽에서 도는가'))
    add(p('n<sub>T</sub> = %(nT).2f 에서는 입력 전압 %(nc)d 개 중 %(nAbove)d 개에서 '
          '탱크가 라인 주기의 일부 구간에서 f<sub>r</sub> 위로 동작한다. 거기서는 '
          '2차 정류기가 ZCS 를 잃으므로, 정류기의 바디 다이오드와 SR '
          '데드타임을 검사해야 한다. 그림&nbsp;%(f)s 와 표&nbsp;%(t)s 는 Full '
          'load 에서 그렸다. <b>어디서 넘어가는지는 부하와 무관하다.</b> Q 가 '
          '무엇이든 f<sub>sw</sub> = f<sub>r</sub> 에서 M = 1 이다(식&nbsp;%(e)s). '
          '그러므로 컨버터는 M<sub>req</sub>(&theta;) = M<sub>pk</sub>/sin&theta; '
          '= 1 인 곳, 곧 sin&theta; = M<sub>pk</sub> 인 곳에서 f<sub>r</sub> 을 '
          '지난다. M<sub>pk</sub> 가 1 보다 작은 입력은 &theta;<sub>0</sub> = '
          'arcsin M<sub>pk</sub> 와 180&deg; &minus; &theta;<sub>0</sub> 사이에서 '
          'buck 하고, 그 창 밖에서 boost 한다. M<sub>pk</sub> 가 1 보다 큰 입력은 '
          '반주기 내내 boost 한다. 부하는 창 안에서 주파수가 f<sub>r</sub> 위로 '
          '얼마나 올라가는지만 정한다.'
          % dict(V, nc=len(V['fswPk']), f=FR('an_above_below'),
                 t=TR('fswside'), e=ER('M'))))
    add(fig('an_above_below',
            '라인 반주기에 걸쳐 컨버터가 f<sub>r</sub> 의 어느 쪽에 있는가, '
            '여섯 입력 전압에서. 모든 곡선이 영교차에서 f<sub>o</sub> 로 '
            '모인다. 범례의 백분율은 반주기 중 f<sub>r</sub> 위에서, 즉 정류기 ZCS 없이 동작하는 시간의 비율이다.', width=CW))
    ext(tbl('Full load 에서 반주기 동안의 피크 f<sub>sw</sub>, f<sub>r</sub> = '
            '%(fr).1f kHz 에 대해, 그리고 sin&theta; = M<sub>pk</sub> 로 구한 창, '
            '곧 컨버터가 f<sub>r</sub> 위에서(buck) 도는 라인 위상 구간. 여섯 입력 '
            '전압 중 %(nAbove)d 개가 주기의 일부에서 above 로 넘어간다.'
            % dict(V, nc=len(V['fswPk'])),
            [['입력 전압과 브리지', '탱크가 보는 전압 (Vac rms)',
              'M<sub>pk</sub>', '피크 f<sub>sw</sub>',
              'f<sub>r</sub> 위(buck)인 &theta;', '반주기의 비율']]
            + [[_kc(nm), '%.0f Vac' % veq, '%.3f' % mpk, '%.1f kHz' % pk,
                ('<b>%.0f&deg; ~ %.0f&deg;</b>' % (th0, 180 - th0))
                if th0 is not None else '없음: 내내 boost',
                '%.0f %%' % sh]
               for (nm, veq, pk, ab), (_n, _v, mpk, th0, sh)
               in zip(V['fswPk'], V['fswCross'])],
            widths=[CW * 0.27, CW * 0.13, CW * 0.10, CW * 0.14, CW * 0.22,
                    CW * 0.14], key='fswside', split=True))
    add(p('<b>부하가 바꾸는 것.</b> 부하를 줄이면 모든 위상에서 Q 가 내려가지만 '
          'M<sub>req</sub>(&theta;) 는 그대로다. 그래서 표&nbsp;%(t)s 의 창은 '
          '움직이지 않는다. 그림&nbsp;%(f)s 의 곡선은 창 안에서만 올라간다. '
          '%(l).0f&nbsp;%% 부하에서 가장 높은 피크는 FB 경계의 %(pk).0f&nbsp;kHz '
          '다. Full load 의 %(pk1).1f&nbsp;kHz 보다 높지만, 지정 최대 '
          '%(spec).0f&nbsp;kHz 아래다. No load 에서도 창은 같다. '
          'M<sub>&infin;</sub> 아래에서는 해가 아예 없다(%(s)s 절). 가장 낮은 '
          '입력 둘은 어느 부하에서도 buck 하지 않는다.'
          % dict(t=TR('fswside'), f=FR('an_above_below'),
                 l=100 * V['loadLight'], pk=V['fswPkLight'],
                 pk1=max(p for _n, _v, p, _a in V['fswPk']),
                 spec=V['fswspec'],
                 s=SR('&lambda; 의 반대쪽 한계, 그리고 해가 없는 경우'))))
    add(fig('f12_two_divergences',
            '영교차 근처에서 요구 게인이 발산하고 부하가 사라지는 일이 함께 '
            '일어나므로, 동작점은 f<sub>o</sub> = %(fo).1f&nbsp;kHz 로 모인다'
            '(%(ref)s 절).' % dict(V, ref=SR('서로 상쇄하는 두 발산'))))
    add(h2('이 설계가 흘려야 하는 전류'))
    add(p('정격은 최악의 스위칭 사이클에서, 손실은 라인 사이클 실효값에서 '
          '오므로 둘 다 적는다. 피크는 HB 경계의 라인 피크'
          '(표&nbsp;%(t)s 의 &theta;&nbsp;=&nbsp;90&deg;)에서 한 사이클을 읽은 '
          '것이다. 합성 피크는 두 성분을 더한 파형의 피크다. 두 성분의 피크가 다른 순간에 오기 '
          '때문이다.' % dict(t=TR('gainpts'))))
    add(calc(r'I_{Lr,pk}=\max_{t}\left|i_{Lm}(t)+i_{trafo}(t)\right|'
             r'=%(Icomp).2f\;\mathrm{A}\;<\;'
             r'%(ILm).2f+%(Itr).2f=%(sum).2f\;\mathrm{A}'
             % dict(V, sum=V['ILm'] + V['Itr'])))
    add(p('실효값은 한 스위칭 주기의 실효값을 라인 반주기에 걸쳐 5점 Simpson '
          '법으로 I&sup2; 평균한 것이다.'))
    add(calc(r'I_{lc}=\sqrt{\frac{2}{\pi}\int_{0}^{\pi/2}'
             r'I_{rms}^{2}(\theta)\,d\theta}'
             r'\;\simeq\;\sqrt{\frac{1}{12}\sum_{k}w_{k}'
             r'I_{rms}^{2}(\theta_{k})}\,,\qquad '
             r'w=\{1,4,2,4,1\}'))
    add(p('그래서 라인 사이클 1차 실효값 %(Iprilc).2f&nbsp;A 는 최악 '
          '사이클의 %(Iprims).2f&nbsp;A 보다 작다.' % V))
    add(fig('an_tank_current',
            'HB 경계, Full load 의 합성 탱크 전류. 그 피크가 두 성분 피크의 '
            '합이 아닌 이유: 두 피크가 다른 순간에 온다. 계산 모델 그대로 그렸다: '
            '반사 부하 전류는 스위칭 반주기 전체에 걸친 사인 반파, 자화 전류는 '
            '직선 램프.'))
    ext(tbl('HB 경계(하프브리지 %.0f&nbsp;Vac), Full load 의 전류. ' % V['Veqlo'] +
            '피크와 최악 사이클 실효값은 '
            '라인 피크(&theta; = 90&deg;)의 스위칭 사이클에서, 라인 사이클 실효값은 '
            '라인 반주기 전체에서 구했다.',
            [['항목', '값', '쓰이는 곳'],
             ['f<sub>sw</sub>', '%(fswA).1f kHz' % V,
              '아래 피크 값들을 읽은 스위칭 사이클'],
             ['I<sub>sec,pk</sub>', '%(Isec).1f A' % V,
              '2차 정류기 피크'],
             ['I<sub>trafo,pk</sub>', '%(Itr).2f A' % V,
              '반사 부하 성분'],
             ['I<sub>Lm,pk</sub>', '%(ILm).2f A' % V,
              '자화 성분'],
             ['<b>합성 탱크 피크</b>', '<b>%(Icomp).2f A</b>' % V,
              '<b>1차 소자 정격, OCP 여유</b>'],
             ['I<sub>pri,rms</sub> (최악 사이클)', '%(Iprims).2f A' % V,
              '1차 실효 정격'],
             ['I<sub>pri</sub> (라인 사이클 실효값)', '%(Iprilc).2f A' % V,
              '1차 도통 손실'],
             ['I<sub>rect</sub> 레그당 (라인 사이클 실효값)',
              '%(Idio).2f A' % V, '2차 도통 손실'],
             ['I<sub>Cout</sub> (라인 사이클 실효값)', '%(ICout).2f A' % V,
              '출력 뱅크 리플 전류']],
            widths=[CW * 0.36, CW * 0.20, CW * 0.44], key='currents',
            split=True))
    add(h2('트랜스포머가 갖춰야 할 값'))
    add(p('탱크가 요구하는 것은 L<sub>r</sub> = %(Lr)g&nbsp;&micro;H, '
          'L<sub>m</sub> = %(Lm)g&nbsp;&micro;H, n<sub>T</sub> = %(nTj)s. '
          '트랜스포머는 부품 하나다: 1차 %(Np)d 턴, 그리고 센터탭에서 만나는 '
          '%(Ns)d 턴 2차 둘, NS2 와 NS3. NS2 는 그림&nbsp;%(f1)s N<sub>s1</sub>, '
          'NS3 은 N<sub>s2</sub> 이므로 S1·S4 가 켜져 있는 동안 NS3 이 도통한다. '
          '여러 유닛을 직렬로 쓸 필요(%(ref2)s 절)는 여기서는 없다.'
          % dict(V, ref2=SR('트랜스포머 한 개로 안 될 때'),
                 nTj=_nj('%.2f' % V['nT'], '이다', '다').replace(' 이다', '이다')
                 .replace(' 다', '다'),
                 f1=_nj(FR('an_llc_stage'), '의', '의'))))
    add(fig('an_xfmr_read',
            '각 값을 읽는 위치. 위: 최악 사이클(HB 경계 %(Veqlo).0f&nbsp;Vac '
            '하프브리지, 라인 피크, Full load)의 한 스위칭 주기 동안의 1차 전류, '
            '2차 권선 전류 둘, 2차 권선 전압. 왼쪽 아래와 가운데: 여섯 입력 '
            '전압에서 입력 반주기에 걸친 두 권선 전류의 실효값. HB 경계가 두 '
            '권선 모두에서 가장 크므로 표를 거기서 읽는다. 오른쪽 아래: DC '
            'overlap 벤치 시험. 동그라미 번호는 표&nbsp;%(t)s 행 번호다.'
            % dict(V, t=_nj(TR('xfmr-read'), '의', '의'))))
    ext(tbl('탱크가 트랜스포머에 요구하는 값.',
            [['항목', '값', '비고'],
             ['턴수', 'N<sub>p</sub> %(Np)d T; NS2 %(Ns)d T, NS3 %(Ns)d T; '
              'NAUX %(Naux)d T' % V,
              'n<sub>T</sub> = %(Np)d / %(Ns)d = %(nT).1f. 보조 권선은 '
              'V<sub>CC</sub> 와 ZCD 에 쓴다' % V],
             ['Open 인덕턴스', '%(Lopen).1f &micro;H' % V,
              'L<sub>r</sub> + L<sub>m</sub>. NP1 에서, 나머지 권선 모두 Open'],
             ['Short 인덕턴스', '%(Lshort).1f &micro;H' % V,
              '이것이 L<sub>r</sub> 이고 공진 인덕터를 따로 두지 않는다. NP1 에서, '
              'NS2 하나만 Short 한 뒤 NS3 하나만 Short. 다른 반쪽과 NAUX 는 Open'],
             ['A<sub>L</sub>', '%(AL).0f nH' % V,
              'Open 인덕턴스 / N<sub>p</sub>&sup2;. 코어 갭을 이 값에 맞춘다'
              '(%s 절)' % SR('코어 고르기')]],
            widths=[CW * 0.24, CW * 0.30, CW * 0.46],
            key='trafo-built', split=True))
    add(h2('코어 고르기'))
    _w = _CORE.winding(V)
    _R = _CORE.CORES[_CORE.CHOSEN]
    _cw = _CORE.window(V) / _CORE.K_U
    add(p('코어를 고르기 전에 정해지는 요구 조건이 셋 있다: 자속이 코어 면적을, '
          '동선이 권선창을, 누설이 권선 폭을 정한다.'))
    add(p('<b>코어 면적.</b> f<sub>r</sub> 에서의 자속으로, B<sub>pk</sub> 를 '
          '%.2f&nbsp;T 이하로 둔다:' % _CORE.B_MAX))
    add(eqagain('Bpk'))
    add(calc(r'A_{e}\geq\frac{%.1f\ \mathrm{V}}{4\times %.2f\ \mathrm{kHz}\times %d'
             r'\times %.2f\ \mathrm{T}}=\mathbf{%.0f\ mm^{2}}'
             % (V['Vout'], V['fr'], V['Ns'], _CORE.B_MAX, V['Aereq'])))
    add(p('<b>동선.</b> 각 권선은 라인 사이클 실효 전류(표&nbsp;%(t)s)를 '
          'J&nbsp;=&nbsp;%(j).1f&nbsp;A/mm&sup2; 로 흘린다. 권선 전부를 더한 '
          '것이 권선창이 담아야 할 동선 면적이다:'
          % dict(t=TR('currents'), j=_CORE.J_CU)))
    add(eqagain('window'))
    _cp, _cs = _CORE.copper(V)[0], _CORE.copper(V)[1]
    add(calc([r'\mathrm{NP1:}\ A_{cu}=\frac{%.2f\ \mathrm{A}}{%.1f\ \mathrm{A/mm^{2}}}'
              r'=%.2f\;\mathrm{mm^{2}}\,,\qquad '
              r'\mathrm{NS2:}\ A_{cu}=\frac{%.2f\ \mathrm{A}}{%.1f\ \mathrm{A/mm^{2}}}'
              r'=%.2f\;\mathrm{mm^{2}}'
              % (_cp[2], _CORE.J_CU, _cp[3], _cs[2], _CORE.J_CU, _cs[3]),
              r'\sum_{w} N_{w}A_{cu,w}=%d\times %.2f+%d\times %.2f'
              r'=%.1f\;\mathrm{mm^{2}}\;\leq\;%.2f\,A_{N}'
              r'\;\Rightarrow\;A_{N}\geq\mathbf{%.0f\ mm^{2}}'
              % (V['Np'], _cp[3], 2 * V['Ns'], _cs[3], _CORE.window(V),
                 _CORE.K_U, _CORE.window(V) / _CORE.K_U)]))
    add(p('각 권선의 도체는 skin depth 에서 정해진다.'))
    _rows = _CORE.copper(V)
    _rp, _rs = _rows[0], _rows[1]
    add(p('100&nbsp;&deg;C 구리(&rho;&nbsp;=&nbsp;2.26&nbsp;&times;'
          '&thinsp;10<sup>&minus;8</sup>&nbsp;&Omega;m), f<sub>r</sub> 에서의 '
          '<b>skin depth</b>:'))
    add(eqagain('skin'))
    add(calc(r'\delta=\sqrt{\frac{2.26\times10^{-8}}'
             r'{\pi\cdot%(fr).1f\times10^{3}\cdot4\pi\times10^{-7}}}'
             r'=%(d).3f\;\mathrm{mm}'
             % dict(fr=V['fr'], d=V['delta'])))
    add(p('2&delta;&nbsp;=&nbsp;%(d2).2f&nbsp;mm 보다 굵은 도체는 얻는 것이 '
          '적으므로 <b>두 권선 모두 Litz 로 감는다</b>. 그 안에 넉넉히 드는 '
          '표준 소선은 <b>d<sub>s</sub> = &oslash;%(ds).2f&nbsp;mm</b> 로, '
          '2&delta; 의 1/%(rat).1f 이다. 1차의 소선 면적과 소선 수는 '
          '식&nbsp;%(e)s:'
          % dict(d2=2 * V['delta'], ds=_CORE.D_STRAND,
                 rat=2 * V['delta'] / _CORE.D_STRAND, e=ER('astrand'))))
    add(eqagain('astrand'))
    _asn = 3.141592653589793 * _CORE.D_STRAND ** 2 / 4
    _np1 = int(_rp[3] / _asn + 0.9999)
    _ns1 = int(_rs[3] / _asn + 0.9999)
    _dp1 = _CORE.litz(_rp[3])[0]
    _ds1 = _CORE.litz(_rs[3])[0]
    add(calc(r'a_{s}=\frac{\pi\cdot(%(ds).2f)^{2}}{4}'
             r'=%(a).5f\;\mathrm{mm^{2}}\,,\qquad '
             r'n_{s}=\left\lceil\frac{%(ap).2f}{%(a).5f}\right\rceil'
             r'=%(n)d'
             % dict(ds=_CORE.D_STRAND, ap=_rp[3], n=_np1, a=_asn)))
    add(p('서빙한 다발 하나로 만들면 k<sub>litz</sub>&nbsp;=&nbsp;%(kl).2f 에서 '
          '외경은:'
          % dict(kl=_CORE.K_LITZ)))
    add(eqagain('litz'))
    add(calc(r'd_{litz}=\sqrt{\frac{4\cdot%(ap).2f}{\pi\cdot%(kl).2f}}'
             r'=%(dl).2f\;\mathrm{mm}'
             % dict(ap=_rp[3], kl=_CORE.K_LITZ, dl=_dp1)))
    add(p('<b>2차도 Litz 다.</b> 아래에서 고르는 권선의 두 칸 사이에서는 자계가 '
          '2차를 가로지르므로(%(ref)s 절) 동박이면 폭 전체에 와전류가 흐른다. '
          'NS2 나 NS3 한 턴에 필요한 면적은 %(a).2f&nbsp;mm&sup2; 다:'
          % dict(ref=SR('skin depth, 그리고 권선을 단선으로 만들지 않는 이유'),
                 a=_rs[3])))
    add(calc(r'n_{s}=\left\lceil\frac{%(a2).2f}{%(a).5f}\right\rceil=%(n)d'
             r'\,,\qquad d_{litz}=\sqrt{\frac{4\cdot%(a2).2f}{\pi\cdot'
             r'%(kl).2f}}=%(d).2f\;\mathrm{mm}'
             % dict(a2=_rs[3], a=_asn, n=_ns1, kl=_CORE.K_LITZ, d=_ds1)))
    add(p('<b>권선마다 턴당 도체 하나다</b>: 다발을 병렬로 쓰지 않으므로 전류가 '
          '고르지 않게 나뉠 일이 없고, 끝마다 도체 하나가 핀 하나에 간다. 크기는 '
          '반올림했다: NS2 와 NS3 은 <b>&oslash;%(ds).1f&nbsp;mm Litz</b> 로 동선이 '
          '요구하는 %(d2).2f&nbsp;mm 보다 굵다. NP1 은 <b>삼중 절연 포함 '
          '&oslash;%(dp).1f&nbsp;mm</b> 로 동선이 요구하는 %(d1).2f&nbsp;mm'
          '(%(d1b).2f&nbsp;mm 에 절연 %(ta).1f&nbsp;mm)보다 굵다. 그래야 1차 층이 '
          '2차와 같은 반경 방향 공간을 채운다(아래).'
          % dict(ds=_CORE.D_SEC, d2=_ds1, dp=_CORE.D_PRI,
                 d1=_dp1 + _CORE.TIW_LITZ_ADD, d1b=_dp1,
                 ta=_CORE.TIW_LITZ_ADD)))

    #  배치는 누설에서 정한다 (1D 식은 leakage.py, 그린 배치의 자계 풀이는
    #  leakage_fem.py)
    import leakage as _LK
    import leakage_fem as _LF
    import insulation as _INS
    _M, _mm = _w['M'], 1e-3
    _hw = _M['r_win_out'] - _M['d_centre'] / 2.0
    _sep = _INS.separation_min()
    _wsb = (-(-V['Np'] // 3)) * _dp1             # plain Litz, 3 layers
    _L1 = _LK.one_d(V['Np'], 0, _wsb * _mm, _w['w_S'] * _mm, 0.0, _sep * _mm,
                    0.0, _hw * _mm, _R['lN'] * _mm) * 1e6
    _L2 = _LK.one_d_of(V) * 1e6
    _ef = _LF.estimate(V)                        # both halves shorted
    _ef0 = _LF.estimate(V, yoke=0.0)
    _ef1 = _LF.estimate(V, yoke=1.0)
    _h2 = _LF.estimate(V, only='NS2')
    _h3 = _LF.estimate(V, only='NS3')
    _h2a, _h3a = (_LF.estimate(V, only='NS2', yoke=0.0),
                  _LF.estimate(V, only='NS3', yoke=1.0))
    _hm = 0.5 * (_h2 + _h3)
    _hmax = max(_h2, _h3)
    _Lmax = V['Lshort'] * 1.10
    _et = _LF.estimate(V, k=1.0)
    _g05 = _LF.estimate(V, g=_w['sep'] - 0.5)
    _pa = _LF.proximity(V, V['fswA'])
    _pb = _LF.proximity(V, V['fr'])
    _dcl = _LF.dc_loss(V)
    _pdc = _dcl['P']
    _gl = _LF.gap_len(V)
    _g0 = _CORE.gap(V, _R['Ae'])
    _zp = _CORE.zone_pct(_CORE.CHOSEN, _w['r_tube'] + _w['h_A'] / 2.0)
    _rin = _w['r_tube'] + _w['d_sec'] * _w['k'] / 2.0
    _rout = _rin + _w['d_sec'] * _w['k'] + _w['t_tape']
    _wall = (_M['tube_od'] - _M['d_centre']) / 2.0
    _mid = _w['wind_w'] / 2.0                    # the gap, from the NP1 flange
    add(p('<b>배치.</b> L<sub>short</sub> 는 %(Ls).1f&nbsp;&micro;H 가 나와야 한다. '
          '먼저 일반 전선으로 나란히 배치하고 칸 사이 간격이 강화 절연을 맡는 '
          '경우를 본다: 그러면 간격은 적어도 creepage %(sep).1f&nbsp;mm 다'
          '(%(ins)s 절). 식&nbsp;%(e)s N<sub>B</sub>&nbsp;=&nbsp;0 으로 쓴다. '
          '넣는 값은 아래에서 고르는 권선창(깊이 h<sub>w</sub> = '
          '%(hw).2f&nbsp;mm, 평균 턴 길이 l<sub>N</sub> = %(ln).1f&nbsp;mm), '
          '세 층으로 감은 일반 Litz 다발 하나의 1차(w<sub>A</sub> = '
          '%(wa).2f&nbsp;mm), 그리고 2차 묶음(w<sub>S</sub> = %(ws).2f&nbsp;mm)이다:'
          % dict(Ls=V['Lshort'], sep=_sep, e=_nj(ER('leak'), '을', '를'), wa=_wsb,
                 ws=_w['w_S'], hw=_hw, ln=_R['lN'],
                 ins=SR('이 트랜스포머의 안전 절연'))))
    add(calc(r'L_{short}\approx\frac{4\pi\times10^{-7}\times %(ln).1f\ '
             r'\mathrm{mm}}{%(hw).2f\ \mathrm{mm}}\times %(np)d^{2}\left('
             r'\frac{%(wa).2f}{3}+%(g).1f+\frac{%(ws).2f}{3}\right)\ \mathrm{mm}'
             r'=\mathbf{%(L).0f\ \mu H}'
             % dict(ln=_R['lN'], hw=_hw, np=V['Np'], wa=_wsb, g=_sep,
                    ws=_w['w_S'], L=_L1)))
    add(p('목표의 %(r).1f 배다. 그래서 <b>절연을 전선에 넣는다</b>: NP1 은 삼중 '
          '절연 Litz, NAUX 는 삼중 절연선이다. 그러면 권선은 흔한 LLC 레퍼런스 '
          '트랜스포머의 <b>칸 권선</b>이 된다. 두 칸짜리 코일 포머의 한 칸에 '
          'NP1, 다른 칸에 2차 묶음을 감는다. 그 사이에 <b>칸막이</b>, 층마다 '
          '테이프 한 겹.'
          % dict(r=_L1 / V['Lshort'])))
    add(p('<b>이 권선에 필요한 권선창.</b> 칸마다 권선창 깊이를 채우면 그 폭은 '
          '동선 면적을 깊이로 나눈 값이므로, 식&nbsp;%(e)s l<sub>N</sub> 곱하기 '
          '동선 면적 나누기 h<sub>w</sub>&sup2; 로 간다. 즉 채워진 칸 권선의 누설은 '
          '권선창의 <b>모양</b>이 정한다: 깊고 짧은 권선창은 누설이 적고, 얕고 긴 '
          '권선창은 많다. 여기서는 카탈로그 코일 포머의 권선창을 빈 곳 없이 '
          '채우고, 탱크의 L<sub>r</sub> 을 그 권선창이 주는 값에 맞춘다.'
          % dict(e=_nj(ER('leak'), '은', '는'))))
    add(p('<b>권선 구성.</b> 실제 권선은 빈틈없이 감기지 않는다: 한 층의 턴끼리, '
          '층과 층끼리 조금씩 떨어져 있다. 그래서 층 사이 피치를 도체 지름의 '
          'k<sub>w</sub>&nbsp;=&nbsp;%(k).2f 배로, 층마다 테이프 %(t).2f&nbsp;mm 를 '
          '넣어 쌓는다. k<sub>w</sub> 는 가정값이고 첫 샘플의 실측 구성으로 바꾼다. '
          'NP1 은 %(per)d 턴씩 %(lp)d 층, NS2 는 %(sp)d 턴을 나란히 한 층, NS3 은 '
          '그다음 층, NAUX(&oslash;%(tiw).1f&nbsp;mm TIW)가 마지막이다. 두 칸의 '
          '깊이는 거의 같다(NP1 은 h<sub>A</sub>, NAUX 를 포함한 2차 칸은 '
          'h<sub>S</sub>). 튜브에서 바깥다리 원호까지의 반경 공간 h<sub>r</sub> '
          '는 %(hr).2f&nbsp;mm 다. 공차 끝(원호는 가장 작게, 튜브는 가장 크게)에서는 '
          '%(hm).2f&nbsp;mm 다. 층을 따라서는 피치 k<sub>ax</sub> 로 두 칸을 '
          '권선 폭에서 칸막이 %(g).1f&nbsp;mm 를 뺀 만큼에 펼쳐, 빈 곳을 남기지 '
          '않는다:'
          % dict(k=_w['k_wind'], t=_w['t_tape'], lp=_w['layers_A'],
                 per=_w['per_A'], sp=_w['sec_per'], tiw=_w['tiw_od'],
                 hr=_w['r_free'], hm=_w['room_min'], g=_w['sep'])))
    add(calc([r'h_{A}=%(lp)d\times(%(dp).2f\times %(k).2f+%(t).2f)=%(ha).2f\;'
              r'\mathrm{mm}'
              % dict(lp=_w['layers_A'], dp=_w['d_pri'], k=_w['k_wind'],
                     t=_w['t_tape'], ha=_w['h_A']),
              r'h_{S}=%(ls)d\times(%(ds).2f\times %(k).2f'
              r'+%(t).2f)+(%(ta).1f\times %(k).2f+%(t).2f)=%(hs).2f\;\mathrm{mm}'
              % dict(lp=_w['layers_A'], dp=_w['d_pri'], k=_w['k_wind'],
                     t=_w['t_tape'], ha=_w['h_A'], ls=_w['sec_layers'],
                     ds=_w['d_sec'], ta=_w['tiw_od'], hs=_w['h_S_aux']),
              r'J_{p}=\frac{%(ip).2f\ \mathrm{A}}{%(ap).2f\ \mathrm{mm^{2}}}'
              r'=\mathbf{%(jp).2f\ A/mm^{2}}\,,\qquad '
              r'J_{s}=\frac{%(isec).2f\ \mathrm{A}}{%(asec).2f\ \mathrm{mm^{2}}}'
              r'=\mathbf{%(js).2f\ A/mm^{2}}'
              % dict(ip=_rp[2], ap=_w['area_p'], jp=_w['j_p'], isec=_rs[2],
                     asec=_w['area_s'], js=_w['j_s']),
              r'k_{ax}=\frac{%(W).1f-%(g).1f\ \mathrm{mm}}{%(np)d\times '
              r'%(dp).2f+%(ns)d\times %(ds).2f\ \mathrm{mm}}=\mathbf{%(ka).3f}'
              % dict(W=_w['wind_w'], g=_w['sep'], np=_w['per_A'],
                     dp=_w['d_pri'], ns=_w['sec_per'], ds=_w['d_sec'],
                     ka=_w['k_ax'])]))
    add(p('권선 구성의 깊이는 %(b).2f&nbsp;mm 다: 다리 원호까지 %(cn).2f&nbsp;mm, '
          '공차 끝에서 %(cm).2f&nbsp;mm 남고, 플랜지 끝(치수 없음)과 거의 같은 '
          '높이다. 1차 다발은 동선이 요구하는 %(n1)d 가닥 대신 %(np)d 가닥, 2차는 '
          '%(n2)d 대신 %(ns)d 가닥이고, 둘 다 이 문서의 %(jc).1f&nbsp;A/mm&sup2; '
          '아래다.'
          % dict(b=_w['build'], cn=_w['clear_nom'], cm=_w['clear_min'],
                 np=_w['n_strand'], n1=_np1, ns=_w['n_strand_s'], n2=_ns1,
                 jc=_CORE.J_CU)))
    add(p('<b>누설.</b> 표&nbsp;%(t)s 폭과 칸막이 %(g).2f&nbsp;mm 를 넣고 턴 '
          '전체가 코어 안에 있다고 보면 식&nbsp;%(e)s 상한 추정을 준다'
          % dict(e=_nj(ER('leak'), '이', '가'), t=_nj(TR('winding'), '의', '의'),
                 g=_w['sep'])))
    add(calc(r'L_{short}\approx\frac{4\pi\times10^{-7}\times %(ln).1f\ '
             r'\mathrm{mm}}{%(hw).2f\ \mathrm{mm}}\times %(np)d^{2}\left('
             r'\frac{%(wa).2f}{3}+%(g).2f+\frac{%(ws).2f}{3}\right)\ \mathrm{mm}'
             r'=\mathbf{%(L).1f\ \mu H}'
             % dict(ln=_R['lN'], hw=_hw, np=V['Np'], wa=_w['w_A'],
                    g=_w['sep'], ws=_w['w_S'], L=_L2)))
    add(p('이 값을 낮추는 것이 둘 있다. PQ 코어의 뒤판은 직사각형이 아니라 '
          '중앙다리 쪽이 좁은 나비넥타이 모양이다(그림&nbsp;%(f)s). 권선 '
          '가운데에서 한 턴 중 바깥다리가 옆에 있는 것은 %(zl).0f&nbsp;%% 뿐이다. '
          '%(zy).0f&nbsp;%% 는 바깥다리 없이 뒤판 아래에 있고, %(zo).0f&nbsp;%% '
          '는 코어 밖에 있다. 또 권선이 깊다: 2차 바깥 층의 한 턴은 안쪽 층보다 '
          '%(rr).0f&nbsp;%% 길다. 그린 배치의 자계 풀이는 둘 다 반영한다. 단면을 '
          '두 경우로 푼다: 바깥다리를 지나는 경우(페라이트, 갭, 뒤판)와 턴이 '
          '코어를 벗어나는 경우(중앙다리만). 그리고 각 부분에 그 반경에서 각 '
          '경우에 해당하는 턴 길이를 가중치로 준다. 뒤판 아래만 있는 부분은 '
          '양쪽에 절반씩 넣는다.'
          % dict(f=FR('an_core_plan'), zl=_zp[0], zy=_zp[1], zo=_zp[2],
                 rr=100 * (_rout / _rin - 1))))
    add(fig('an_core_plan',
            '위에서 본 코어, 실제 비율: 바깥다리, 나비넥타이 모양의 뒤판, '
            '중앙다리, 뒤판 아래의 옅은 고리로 그린 NP1 전체, 그리고 그 가운데 '
            '턴 하나를 둘레에 무엇이 있느냐에 따라 색칠했다. 누설은 페라이트로 '
            '둘러싸인 경우와 열린 경우를 각각 풀고, 반경마다 이 비율로 더한다.'))
    add(p('<b>탱크가 보는 값.</b> 실제 동작에서는 센터탭의 반쪽 하나만 도통한다. '
          'NS2 하나만 Short 하면 자계 풀이는 <b>%(h2).2f&nbsp;&micro;H</b>, NS3 '
          '하나만이면 <b>%(h3).2f&nbsp;&micro;H</b> 를 준다: NS3 이 더 바깥에 '
          '있어 턴이 길다. 둘의 평균 %(hm).2f&nbsp;&micro;H 는 탱크의 '
          'L<sub>r</sub> %(Ls).1f&nbsp;&micro;H 와 %(dm).0f&nbsp;%% 안에서 '
          '맞는다. 뒤판 아래 부분을 전부 밖으로 또는 전부 안으로 세면 반쪽 '
          '값은 극단에서 %(h2aj)s %(h3a).2f&nbsp;&micro;H 로 움직인다. 높은 '
          '쪽 반쪽은 L<sub>r</sub> 보다 %(hp).1f&nbsp;%% 높아, 사양서가 반쪽마다 '
          '거는 &plusmn;10&nbsp;%% %(inout)s, 그 공진 주파수는 다른 반쪽보다 '
          '%(df).1f&nbsp;%% 낮다: 누설이 적은 반쪽이 부하를 조금 더 맡는다. '
          '사양서의 다른 측정인 두 반쪽 모두 Short 값은 더 낮은 '
          '%(Lf).2f&nbsp;&micro;H(%(L0).2f&ndash;%(L1).2f)다. 그때는 두 층이 2차 '
          '암페어턴을 나눠 갖기 때문이다. 이 값은 기록만 하고 L<sub>r</sub> '
          '기준으로 판정하지 않는다.'
          % dict(h2=_h2, h3=_h3, hm=_hm, Ls=V['Lshort'], h2a=_h2a, h3a=_h3a,
                 dm=max(1.0, -(-100 * abs(_hm / V['Lshort'] - 1) // 1)),
                 h2aj=_nj('%.2f' % _h2a, '과', '와'),
                 hp=100 * (_hmax / V['Lshort'] - 1),
                 inout='안에 들고' if _hmax <= _Lmax else '밖에 있고',
                 df=100 * (1 - (min(_h2, _h3) / _hmax) ** 0.5),
                 Lf=_ef, L0=_ef0, L1=_ef1)))
    add(p('<b>첫 샘플 뒤에 손댈 수 있는 것은 칸막이이고, 한 방향으로만이다.</b> '
          '%(g).1f&nbsp;mm 벽은 더 얇게 성형할 수 있고 그러면 누설이 낮아지지만, '
          '더 두껍게 하는 것은 쓸모가 없다. %(g5).1f&nbsp;mm 이면 두 반쪽 모두 '
          'Short 값이 %(l5).2f&nbsp;&micro;H 로 내려가고, 줄어든 폭은 층 방향 '
          '피치가 흡수한다. 빈틈없이(k<sub>w</sub>&nbsp;=&nbsp;1) 감으면 같은 '
          '권선이 %(Lt).2f&nbsp;&micro;H 가 된다: 권선의 느슨함이 값을 '
          '%(dl).1f&nbsp;%% 움직인다. 모두 추정값이고 판정은 첫 샘플이 한다.'
          % dict(g=_w['sep'], g5=_w['sep'] - 0.5, l5=_g05, Lt=_et,
                 dl=100 * abs(1 - _et / _ef))))
    add(p('<b>AC 손실.</b> DC 저항은 하한이다: 라인 사이클 실효 전류에서, '
          '턴마다 제 반경으로 계산해 %(dc).2f&nbsp;W. 소선은 모두 누설 자계 '
          '안에 있고, 그 자계는 1차 칸에서 최대 %(bp).1f&nbsp;mT rms, 2차 칸에서 '
          '%(bs).1f mT rms 다. 피크 B 의 자계 안에 있는 지름 d<sub>s</sub> 의 '
          '소선은 미터당 &pi;&omega;&sup2;&sigma;d<sub>s</sub>&#8308;B&sup2;/128 '
          '을 잃는다. 그린 배치의 소선 전부에 대해 더한다. 라인 사이클 실효 '
          '전류는 사인파로 본다. 그러면 %(fa).0f&nbsp;kHz(하프브리지 경계의 라인 '
          '피크)와 f<sub>r</sub> 사이에서 NP1 %(pa).1f ~ %(pb).1f&nbsp;W, NS2·NS3 '
          '%(sa).1f ~ %(sb).1f&nbsp;W 다. 1차 근사로 <b>DC 손실의 %(ra).1f ~ '
          '%(rb).1f 배</b>다. 누설 자계를 공진 인덕터로 쓰는 대가이고, 소선이 '
          '그 크기를 정한다: 같은 동선 면적이면 d<sub>s</sub>&sup2; 에 비례한다. '
          '소선은 첫 샘플의 발열 측정으로 정한다.'
          % dict(dc=_pdc, bp=1e3 * _pa['B_pri'], bs=1e3 * _pa['B_sec'],
                 pa=_pa['P_pri'], pb=_pb['P_pri'], sa=_pa['P_sec'],
                 sb=_pb['P_sec'], fa=V['fswA'],
                 ra=(_pa['P_pri'] + _pa['P_sec']) / _pdc,
                 rb=(_pb['P_pri'] + _pb['P_sec']) / _pdc)))
    _built = (V['Np'] * _w['pri_par'] * _w['area_p']
              + 2 * V['Ns'] * _w['sec_par'] * _w['area_s'])
    add(p('<b>코어가 갖춰야 할 것.</b> A<sub>e</sub> %(ae).0f&nbsp;mm&sup2; '
          '이상. k<sub>u</sub>&nbsp;=&nbsp;%(ku).2f 에서 NP1, NS2, NS3 의 동선을 '
          '담을 권선창 %(cu).1f/%(ku).2f = %(win).0f&nbsp;mm&sup2; 이상(NAUX 는 '
          'V<sub>CC</sub> 부하, 평균 %(ivcc).0f&nbsp;mA 만 흘리므로 뺐다). 그리고 '
          '누설을 위해, 채워진 칸 권선이 L<sub>r</sub> 이 되도록 충분히 깊고 '
          '짧은 권선창.'
          % dict(ae=V['Aereq'], cu=_CORE.window(V), ku=_CORE.K_U, win=_cw,
                 ivcc=A.SH['I.VCC'])))
    _pc = _R['P_core_max']
    add(p('<b>코어.</b> TDK <b>%(core)s</b>, %(mat)s 페라이트의 %(chosen)s: '
          'A<sub>e</sub> = %(ae).0f&nbsp;mm&sup2; 로 자속이 요구하는 값의 '
          '%(rae).1f 배이고, B<sub>pk</sub> 는 %(bpk).0f&nbsp;mT 다. 권선창은 '
          '&oslash;%(f).0f&nbsp;mm 원형 중앙다리에서 각 바깥다리 안쪽을 이루는 '
          '원호(&oslash;%(arc).0f&nbsp;mm)까지 깊이 %(hw).1f&nbsp;mm, 높이 '
          '%(wh).1f&nbsp;mm 다. 코일 포머는 카탈로그 부품 <b>%(former)s</b> 로 한 '
          '칸에 핀 %(pins)d 개이고, 보빈 제조사에 요구하는 변경은 %(g).1f&nbsp;mm '
          '칸막이 하나뿐이다. 권선은 칸막이를 포함해 플랜지 사이 '
          '%(ww).1f&nbsp;mm 를 차지한다. A<sub>N</sub> 은 %(an).0f&nbsp;mm&sup2;, '
          '실제 동선은 %(bu).1f&nbsp;mm&sup2; 다. 카탈로그는 코어 손실을 한 점에서만 '
          '준다: %(pf).0f&nbsp;kHz, %(pb).0f&nbsp;mT, %(pt).0f&nbsp;&deg;C 에서 '
          '최대 %(p0).2f&nbsp;W. 동작 자속에서의 손실은 %(mat)s 재료 곡선에서 '
          '읽는다. 계산은 표&nbsp;%(t2)s 있다.'
          % dict(chosen=_CORE.CHOSEN, mat=_R['material'], core=_R['core'],
                 ae=_R['Ae'], rae=_R['Ae'] / V['Aereq'],
                 bpk=_CORE.flux(V, _R['Ae']), hw=_hw, wh=_M['win_h'],
                 f=_M['d_centre'], arc=2 * _M['r_win_out'], ww=_w['wind_w'],
                 former=_R['former'], pins=_CORE.BOBBIN['pins'], g=_w['sep'],
                 an=_R['AN'], bu=_built, p0=_pc[0], pf=_pc[1], pb=_pc[2],
                 pt=_pc[3], t2=_nj(TR('winding'), '에', '에'))))
    add(p('<b>갭은 한 군데이고, 권선이 갭에 가깝다.</b> 데이터시트는 이 코어의 '
          'A<sub>L</sub> 과 갭의 관계를 주지 않는다. 갭 코어는 주문 생산으로 '
          'A<sub>L</sub> 에 맞춰 연마한다. 프린징을 빼면 &mu;<sub>0</sub>A<sub>e</sub>/'
          'A<sub>L</sub> 에서 A<sub>L</sub>&nbsp;=&nbsp;%(AL).0f&nbsp;nH 에 '
          '%(g0).2f&nbsp;mm 가 나오고, 프린징을 포함한 자계 풀이로는 <b>약 '
          '%(gl).2f&nbsp;mm</b> 다. 갭은 중앙다리 가운데, 1차 칸 플랜지에서 '
          '%(ud).1f&nbsp;mm 에 있고, %(pd)s, NP1 첫 층과는 튜브를 사이에 두고 '
          '%(wall).2f&nbsp;mm 떨어져 있다. 그 프린징 자계가 안쪽 층까지 닿으며, '
          '위의 소선 손실에 자계 풀이가 이미 포함했다.'
          % dict(AL=V['AL'], g0=_g0, gl=_gl, ud=_mid,
                 pd=('1차 칸 아래로 칸막이에서 %.1f&nbsp;mm 못 미친 곳이며'
                     % (_w['yA'][1] - _mid))
                 if _mid < _w['yA'][1] else '2차 칸 아래이며',
                 wall=_wall)))
    ext(tbl('전류에서 동선까지의 권선. NS3 은 NS2 와 같고 한 층 바깥에 있다.',
            [['단계', '1차 NP1', '2차 NS2'],
             ['라인 사이클 실효 전류', '%.2f A' % _rp[2], '%.2f A' % _rs[2]],
             ['J = %.1f A/mm&sup2; 에서 필요한 동선' % _CORE.J_CU,
              '%.2f / %.1f = <b>%.2f mm&sup2;</b>, 소선 %d 가닥'
              % (_rp[2], _CORE.J_CU, _rp[3], _np1),
              '%.2f / %.1f = <b>%.2f mm&sup2;</b>, 소선 %d 가닥'
              % (_rs[2], _CORE.J_CU, _rs[3], _ns1)],
             ['실제 도체',
              '턴당 삼중 절연 Litz 다발 하나, %d &times; '
              '&oslash;%.2f mm: &oslash;%.2f + %.1f = <b>&oslash;%.2f mm</b>'
              % (_w['n_strand'], _CORE.D_STRAND, _w['d_litz'], _w['tiw_add'],
                 _w['d_pri']),
              '턴당 Litz 다발 하나, %d &times; &oslash;%.2f mm: '
              '<b>&oslash;%.2f mm</b>'
              % (_w['n_strand_s'], _CORE.D_STRAND, _w['d_sec'])],
             ['실제 전류 밀도',
              '%.2f / %.2f = <b>%.2f A/mm&sup2;</b>'
              % (_rp[2], _w['area_p'], _w['j_p']),
              '%.2f / %.2f = <b>%.2f A/mm&sup2;</b>'
              % (_rs[2], _w['area_s'], _w['j_s'])],
             ['턴과 층',
              '%d T, %d 층, 층마다 %s 턴'
              % (V['Np'], _w['layers_A'],
                 ', '.join(str(n) for n in _w['rows_A'])),
              '%d T 를 한 층에 나란히. NS3 은 다음 층(튜브부터: %s)'
              % (V['Ns'], ', '.join(_w['order']))],
             ['피치',
              '층 사이 k<sub>w</sub> = %.2f(가정), 층 방향 k<sub>ax</sub> '
              '= %.3f, 층마다 테이프 %.2f mm'
              % (_w['k_wind'], _w['k_ax'], _w['t_tape']),
              '같음. 맨 위에 NAUX %.1f &times; %.2f + %.2f mm'
              % (_w['tiw_od'], _w['k_wind'], _w['t_tape'])],
             ['코일 포머 위의 폭',
              '%d &times; %.2f &times; %.3f = <b>%.2f mm</b>'
              % (_w['per_A'], _w['d_pri'], _w['k_ax'], _w['w_A']),
              '%d &times; %.2f &times; %.3f = <b>%.2f mm</b>'
              % (_w['sec_per'], _w['d_sec'], _w['k_ax'], _w['w_S'])],
             ['반경 방향 두께, 테이프 포함',
              '%d &times; (%.2f &times; %.2f + %.2f) = <b>%.2f mm</b>'
              % (_w['layers_A'], _w['d_pri'], _w['k_wind'], _w['t_tape'],
                 _w['h_A']),
              '%d &times; (%.2f &times; %.2f + %.2f) = %.2f mm, + NAUX = '
              '<b>%.2f mm</b>'
              % (_w['sec_layers'], _w['d_sec'], _w['k_wind'], _w['t_tape'],
                 _w['h_S'], _w['h_S_aux'])],
             ['반경 공간, 튜브에서 다리 원호까지',
              '공칭 %.2f mm, 공차 끝에서 %.2f mm. 공차 끝에서 %.2f mm '
              '남는다'
              % (_w['r_free'], _w['room_min'], _w['clear_min']), ''],
             ['코일 포머, %s' % _R['former'],
              '%.2f + 칸막이 %.2f + %.2f = <b>%.2f mm</b>, 플랜지 사이 폭. '
              '남는 곳 없음'
              % (_w['w_A'], _w['sep'], _w['w_S'], _w['wind_w']), ''],
             ['권선창 안의 동선',
              '요구: %d &times; %.2f + %d &times; %.2f = %.1f mm&sup2;, '
              'k<sub>u</sub> = %.2f 에서 권선창 %.0f mm&sup2; 필요. '
              '실제 %.1f mm&sup2;. A<sub>N</sub> = %.0f mm&sup2;'
              % (V['Np'], _rp[3], 2 * V['Ns'], _rs[3], _CORE.window(V),
                 _CORE.K_U, _cw, _built, _R['AN']),
              '']],
            widths=[CW * 0.20, CW * 0.42, CW * 0.38],
            key='winding', split=True))
    add(h2('권선과 핀'))
    add(p('그림&nbsp;%(f)s 단면과 권선을 보이고, 표&nbsp;%(t)s 각 항목의 '
          '이름을 적었다.'
          % dict(f=_nj(FR('an_core_section'), '이', '가'),
                 t=_nj(TR('legend42'), '에', '에'))))
    add(fig('an_core_section',
            '코어 단면(왼쪽, 실제 비율)과 코일 포머를 따라 펼친 권선(오른쪽, '
            '실제 비율). 한 칸에 NP1, 다른 칸에 NS2 와 NS3, 그 사이에 '
            '%(g).2f&nbsp;mm 칸막이. 노란 선은 층 테이프다. 동그라미 번호는 '
            '표&nbsp;%(t)s 행 번호다.'
            % dict(t=_nj(TR('legend42'), '의', '의'), g=_w['sep']), shrink=False))
    ext(tbl('그림의 항목.',
            [['표시', '항목', '턴수', '도체, 위치'],
             ['1', 'NP1 1차, 핀 %s' % _CORE.pins('NP1', '&ndash;'),
              '%d T' % V['Np'],
              '턴당 삼중 절연 Litz 다발 하나, %d &times; &oslash;%.2f mm '
              '(&oslash;%.2f mm), 1차 칸에 %d 층(층마다 %s 턴). 층마다 테이프'
              % (_w['n_strand'], _CORE.D_STRAND, _w['d_pri'],
                 _w['layers_A'], ', '.join(str(n) for n in _w['rows_A']))],
             ['2', 'NS2 2차, 핀 %s' % _CORE.pins('NS2', '&ndash;'),
              '%d T' % V['Ns'],
              '턴당 Litz 다발 하나, %d &times; &oslash;%.2f mm '
              '(&oslash;%.2f mm), 두 턴을 2차 첫 층에 나란히. 그 위에 테이프'
              % (_w['n_strand_s'], _CORE.D_STRAND, _w['d_sec'])],
             ['3', 'NS3 2차, 핀 %s' % _CORE.pins('NS3', '&ndash;'),
              '%d T' % V['Ns'], '같은 구성으로 한 층 바깥에, NS2 와 같은 '
              '방향으로 감는다'],
             ['4', 'NAUX 보조, 핀 %s'
              % _CORE.pins('NAUX', '&ndash;'), '%d T' % V['Naux'],
              '삼중 절연선, &oslash;%.1f mm 가정, 2차 위에 한 층. '
              'V<sub>CC</sub> 와 ZCD 에 쓴다'
              % _w['tiw_od']],
             ['5', '중앙다리 갭', '&mdash;',
              '한 군데, 자계 풀이로 약 %.2f mm, A<sub>L</sub> = %.0f nH 에 '
              '맞춰 연마' % (_gl, V['AL'])],
             ['6', '코일 포머', '&mdash;',
              'TDK %s: 튜브 &oslash;%.1f mm, 튜브에서 플랜지 %.2f mm. 절연 '
              '역할 없음' % (_R['former'], _M['tube_od'], _w['flange'])],
             ['7', '칸막이', '&mdash;',
              '%.2f mm, 카탈로그 코일 포머에 더한 것. 칸 사이 벽으로 권선과 함께 '
              'L<sub>short</sub> 를 정한다. 절연 역할 없음' % _w['sep']]],
            widths=[CW * 0.07, CW * 0.30, CW * 0.09, CW * 0.54],
            key='legend42', split=True))
    _B = _CORE.BOBBIN
    add(p('<b>핀.</b> 코일 포머 %(former)s 는 핀 %(pins)d 개가 %(half)d 개씩 두 '
          '열로 있고, 열 사이는 %(rows).2f&nbsp;mm 다. 한 열은 세 개씩 두 묶음으로, '
          '묶음 안에서는 %(pitch).2f&nbsp;mm, 묶음 사이는 %(pb).1f&nbsp;mm 다. '
          '데이터시트는 핀 1, 6, 7, 12 의 번호를 <b>아래에서 본</b> 그림, 곧 핀 '
          '쪽에서 본 그림에 적었다. 도면에 그렇게 적혀 있지는 않다. 그러나 핀 '
          '끝이 보이는 것은 그 그림이고, 위에서 본 그림에는 핀이 보이지 않는다. '
          '풋프린트를 그리는 보드 부품면에서 보면 좌우가 바뀐다: '
          '그림&nbsp;%(fig)s 둘 다 그렸다. NP1 과 보조 권선 NAUX 는 1번 핀 열, '
          'NS2 와 NS3 은 반대쪽 열을 쓴다. 권선마다 도체 하나이고 끝 하나가 핀 '
          '하나다. <b>센터탭은 보드에서 만든다</b>: NS2 끝(핀 %(t2)d)과 NS3 시작'
          '(핀 %(t3)d)을 보드에서 이어, 반쪽마다 따로 잴 수 있게 한다. 2차 핀은 '
          '그 권선의 전류 전부, 라인 사이클 실효값 %(ip).1f&nbsp;A 를 흘린다: '
          '보빈 제조사가 그 정격을 확인하거나, 2차 끝을 핀을 거치지 않고 보드로 '
          '바로 뽑는다. NAUX 와 2차 리드는 핀으로 가는 길에 1차 칸을 지나는데, '
          '거기서는 NP1 이 절연을 맡는다.'
          % dict(former=_B['former'], pins=_B['pins'], half=_B['pins'] // 2,
                 fig=_nj(FR('an_xfmr_pins'), '에', '에'),
                 pitch=_B['pitch'], pb=_B['pitch_b'], rows=_B['rows_apart'],
                 t2=_CORE.PINMAP['NS2'][1][0], t3=_CORE.PINMAP['NS3'][0][0],
                 ip=V['Idio'])))
    add(fig('an_xfmr_pins',
            '핀 번호를 단 회로 기호와, 같은 핀을 %(former)s 코일 포머(핀 '
            '%(pins)d 개, 열 사이 %(rows).2f&nbsp;mm) 위에 그린 것. 윤곽은 '
            '데이터시트 도면에서 따왔다: (A) 데이터시트처럼 아래, 곧 핀 쪽에서 본 '
            '그림, (B) 위에서 본 그림으로 부품면의 PCB 풋프린트. 권선 색의 '
            '고리가 그 권선의 핀이다. 점이 찍힌 쪽이 각 권선의 시작이다. '
            '%(note)s'
            % dict(former=_B['former'], pins=_B['pins'],
                   rows=_B['rows_apart'], note=_CORE.PIN_NOTE_KR)))
    _PM = _CORE.PINMAP

    def PIN_ROW0(n):
        return _CORE.PIN_XY[n][0] < 0
    ext(tbl('권선과 핀 배정.',
            [['권선', '핀(시작 &ndash; 끝)', '턴수', '도체',
              '열'],
             ['NP1 1차', _CORE.pins('NP1', '&ndash;'), '%d T' % V['Np'],
              '삼중 절연 Litz, %d &times; &oslash;%.2f mm'
              % (_w['n_strand'], _CORE.D_STRAND), _kr_row(_B['rows'][0])],
             ['NAUX 보조(V<sub>CC</sub>, ZCD)',
              _CORE.pins('NAUX', '&ndash;'), '%d T' % V['Naux'],
              '2차 위의 삼중 절연선', _kr_row(_B['rows'][0])],
             ['NS2 2차', _CORE.pins('NS2', '&ndash;'), '%d T' % V['Ns'],
              'Litz, %d &times; &oslash;%.2f mm'
              % (_w['n_strand_s'], _CORE.D_STRAND), _kr_row(_B['rows'][1])],
             ['NS3 2차', _CORE.pins('NS3', '&ndash;'), '%d T' % V['Ns'],
              '같은 구성, 다음 층', _kr_row(_B['rows'][1])],
             ['센터탭', _CORE.tap_text().replace(' and ', '·'),
              '&mdash;', 'NS2 끝과 NS3 시작, 보드에서 연결',
              _kr_row(_B['rows'][1])],
             ['빈 핀', ', '.join(str(n) for n in _CORE.free_pins()),
              '&mdash;', '연결 없음',
              _kr_row(_B['rows'][0]) if all(PIN_ROW0(n) for n in _CORE.free_pins())
              else '양쪽 열']],
            widths=[CW * 0.20, CW * 0.26, CW * 0.09, CW * 0.27, CW * 0.18],
            key='pins', split=True))
    add(p('<b>극성.</b> 데이터시트는 레그 1 의 low-side 스위치(LOUT1)가 켜져 '
          '있는 동안 ZCD 가 양이어야 한다고 한다. 그때 1차 점 쪽이 음이므로, '
          '점이 찍힌 보조 권선의 시작, 핀 %(aj)s 접지에, 끝인 핀 %(bj)s '
          'R<sub>ZCD,H</sub> 와 V<sub>CC</sub> 정류기에 잇는다. NS2 와 NS3 은 같은 '
          '방향으로 감고, 탭은 NS2 의 끝과 NS3 의 시작을 잇는다.'
          % dict(aj=_nj(_PM['NAUX'][0][0], '을', '를'),
                 bj=_nj(_PM['NAUX'][1][0], '을', '를'))))
    add(h2('이 트랜스포머의 안전 절연'))
    _IR = _INS.req()
    _ck, _cw2 = _INS.checks(V)
    add(p('미국, EU, 일본, 한국, 중국에 파는 TV 이므로 요구 조건마다 가장 엄격한 '
          '쪽을 잡는다. <b>강화 절연</b>: Class&nbsp;II 제품에 필요하고 Class&nbsp;I '
          '도 충족한다. <b>%(alt)d&nbsp;m</b>: GB&nbsp;4943.1-2022 는 제조사가 따로 '
          '정하지 않으면 이 고도를 가정한다 [GB]. 작업 전압: 설계 범위의 최고값인 '
          '<b>%(vm).0f&nbsp;Vac</b> 에서. 1차는 NP1 과 NAUX, 2차는 '
          'NS2, NS3, 그리고 코어다. 1차가 스스로 절연을 갖추므로 코어는 2차 쪽에 '
          '속한다(%(s)s 절).'
          % dict(alt=_INS.ALTITUDE_M, vm=_INS.V_MAINS_DESIGN,
                 s=SR('안전 절연: 권선이 갖춰야 할 것'))))
    add(p('1차 권선과 2차 사이의 <b>작업 전압</b>은 설계에서 추정한다. 상용전원 '
          '중성선과 2차는 접지 전위에 있다. 브리지는 반주기마다 1차 접지를 라인 '
          '쪽으로 옮긴다. 여기에 라인 주기의 모든 점에서 스윕한 레그 전압과 '
          'C<sub>r</sub> 스윙이 더해진다. %(vm).0f&nbsp;Vac 에서 %(ur).0f&nbsp;V '
          'rms, %(up).0f&nbsp;V 피크다. 상용전원 자체보다 낮으므로 creepage 행은 '
          '상용전원이 정한다. 인증 기관이 실측하며, 고른 행은 %(row)d&nbsp;V 까지 '
          '덮는다.'
          % dict(vm=_INS.V_MAINS_DESIGN, ur=_IR['u_rms'], up=_IR['u_pk'],
                 row=_IR['row'])))
    ext(tbl('절연 요구 조건과 각 숫자의 출처. 출처는 참고문헌에 있다.',
            [['항목', '요구', '근거'],
             ['등급', '1차와 2차 사이 강화 절연',
              'Class II 제품 [TUV]'],
             ['조건', '오염도 2, 과전압 범주 II, 재료군 IIIb, %d m'
              % _INS.ALTITUDE_M,
              '보빈의 tracking index 를 모르므로 IIIb. 고도 [GB]'],
             ['Clearance', '%.1f &times; %.2f = %.2f &rarr; <b>%.1f mm</b>'
              % (_IR['cl_2000'], _INS.K_ALT, _IR['cl_2000'] * _INS.K_ALT,
                 _IR['clearance']),
              '상용전원 서지 %.0f V. 강화 절연은 한 단계 위 4000 V 로 '
              '%.1f mm [ATIS, TUV]. 일시 과전압 경로로는 %.2f mm 뿐 [PI]. '
              '%d m 에 &times;%.2f 하고 올림 [PI]'
              % (_INS.V_TRANSIENT, _INS.CL_TABLE14_R,
                 _INS.CL_TABLE10_R, _INS.ALTITUDE_M, _INS.K_ALT)],
             ['Creepage', '2 &times; %.1f = <b>%.1f mm</b>'
              % (_IR['creep_basic'], _IR['creep']),
              '%d V 행의 기본 절연 [PI]. 강화 절연은 기본의 두 배 [TI]. CB '
              '성적서가 적용하는 행과 같다 [TUV]' % _IR['row']],
             ['고체 절연', '두께 &ge; %.1f mm, 또는 테이프 &ge; %d 층'
              % (_IR['dti'], _IR['layers']),
              '층마다 강화 절연 내전압 시험을 통과해야 한다 [TUV]'],
             ['내전압', '%d V ac 60 s, 또는 %d V dc'
              % (_IR['hipot_ac'], _IR['hipot_dc']),
              '형식 시험, NP1 + NAUX 대 NS2 + NS3 와 코어. CB 성적서가 '
              'Class II 100&ndash;240 V 제품에 %d m 에서 적용하는 값 [TUV]. '
              '습도 처리 뒤 1 분 [PI]' % _INS.ALTITUDE_M],
             ['NP1 과 NAUX 전선', '강화 절연으로 인증된 삼중 절연선. NP1 은 '
              'Litz',
              'EN IEC 62368-1 과 IEC 62368-1:2018 Annex&nbsp;J 인증이 '
              '%d V rms, %d kHz, 절연 Class %s 로 있고, Litz 형도 같은 인증 '
              '[TIW]'
              % (_INS.TIW_VRMS, _INS.TIW_FMAX / 1e3, _INS.TIW_CLASS)]],
            widths=[CW * 0.16, CW * 0.30, CW * 0.54], key='insreq',
            split=True))
    add(p('표&nbsp;%(t)s 두 쪽 사이의 경로를 모두 들고, 각 경로를 무엇이 맡는지 '
          '적었다. 권선 안에서는 전선이 모든 경로를 맡고, 칸막이는 아무것도 '
          '맡지 않는다.' % dict(t=_nj(TR('inscheck'), '는', '는'))))
    ext(tbl('경로마다 절연을 맡는 것(%s).'
            % _cw2['name'],
            [['경로', '맡는 것', '요구', '판정']]
            + [[_kr_ins(pth), _kr_ins(by), _kr_ins(need), _kr_ins(st)]
               for pth, by, need, st in _ck],
            widths=[CW * 0.26, CW * 0.34, CW * 0.30, CW * 0.10],
            key='inscheck', split=True))
    add(p('NP1 과 NAUX 는 교차하는 곳까지 포함해 핀에서 핀까지 삼중 절연 안에 '
          '있다. 피복을 벗기는 것은 핀의 끝뿐이고, 도면이 정할 수 있는 것은 '
          '거기까지다. 도면이 정하지 못하는 것은 인증 기관과 벤더에게 넘어간다:'))
    ext(bullets([
        '1차 핀과 피복을 벗긴 선 끝 ↔ 코어 요크, 2차 리드: 코일 포머와 리드 '
        '처리가 정한다. 강화 절연 거리를 두거나, 강화 절연으로 인정된 슬리브를 '
        '쓴다.',
        '삼중 절연 Litz 자체: %d &times; &oslash;%.2f mm 다발 하나, 절연 포함 '
        '&oslash;%.1f mm 가 이 설계가 요구하는 크기다. 절연 두께 %.1f mm 는 '
        '가정이고, 크기와 인증은 전선 벤더에게서 받는다.'
        % (_w['n_strand'], _CORE.D_STRAND, _w['d_pri'], _w['tiw_add']),
        '인증서가 인용할 판의 내전압 값, 그리고 양산 시험 전압과 시간.',
        '작업 전압의 고주파 성분에 대한 clearance: 인용한 자료에 그 표가 없다. '
        '한 CB 성적서는 133 kHz, 588 V 피크에서 보통 값을 적용했다 [UL].',
        ('인용한 TIW 인증은 %d kHz 까지다. 가장 높은 스위칭 주파수인 기동 '
         '주파수는 %.0f kHz 로 %s. Class %s 정격은 권선 hot spot 온도의 상한도 '
         '정하므로 발열 측정으로 확인해야 한다.'
         % (_INS.TIW_FMAX / 1e3, A.SH['f.SU'],
            '그 안에 든다' if A.SH['f.SU'] * 1e3 <= _INS.TIW_FMAX
            else '세이프 스타트 처음 몇 ms 동안은 그 위다: 전선 벤더에게 '
                 '확인한다', _INS.TIW_CLASS)),
        'L<sub>short</sub> 는 자계 풀이 추정값이다. 칸막이 %.2f&nbsp;mm, 가정한 '
        '권선 피치에서 두 반쪽이 %s %.2f&nbsp;&micro;H 다. 판정은 첫 샘플이 '
        '한다.'
        % (_w['sep'], _nj('%.2f' % _h2, '과', '와'), _h3)]))
    add(h2('자속 확인과 사양서'))
    add(p('고른 코어에서 f<sub>r</sub> 의 <b>피크 자속 밀도</b>(식&nbsp;%s):'
          % ER('Bpk')))
    add(calc(r'B_{pk}=\frac{%.1f\ \mathrm{V}}{4\times %.2f\ \mathrm{kHz}'
             r'\times %d\times %.1f\ \mathrm{mm^{2}}}=\mathbf{%.0f\ mT}'
             % (V['Vout'], V['fr'], V['Ns'], V['Aemm'], V['Bpk'])))
    add(p('L<sub>&mu;</sub> 로 계산한 <b>자화 피크</b>(i<sub>&mu;,pk</sub> 와 '
          '같다):'))
    add(eqagain('Isat'))
    add(calc(r'I_{eq}=\frac{%.4f\ \mathrm{T}\times %d\times %.1f\ \mathrm{mm^{2}}}'
             r'{%.2f\ \mu\mathrm{H}}=\mathbf{%.2f\ A}\ =\ i_{\mu,pk}'
             % (V['Bpk'] / 1e3, V['Np'], V['Aemm'], V['Lmu'] / V['nser'],
                V['Isateq'])))
    add(p('같은 전류를 코어 데이터 없이 출력 전압만으로 계산하면'
          '(식&nbsp;%s):' % ER('imuVo')))
    add(calc(r'i_{\mu,pk}=\frac{%.2f\times %.1f\ \mathrm{V}}'
             r'{4\times %.2f\ \mathrm{kHz}\times %.2f\ \mu\mathrm{H}}'
             r'=\mathbf{%.2f\ A}'
             % (V['nT'], _SH['V.o_eff'], V['fr'], V['Lmu'] / V['nser'],
                V['nT'] * _SH['V.o_eff'] / (4 * V['fr'] * 1e3
                                       * V['Lmu'] / V['nser'] * 1e-6))))
    add(p('<b>포화 시험 전류</b>, 곧 OVP2 출력 전압에서의 자화 피크:'))
    add(eqagain('Isatspec'))
    add(calc(r'I_{sat}=%.2f\ \mathrm{A}\times\frac{%.2f\ \mathrm{V}}{%.1f\ \mathrm{V}}'
             r'=%.2f\times %.4f=\mathbf{%.1f\ A}'
             % (V['Isateq'], V['OVP2'], V['Vout'], V['Isateq'],
                V['OVP2'] / V['Vout'], V['Isatspec'])))
    add(fig('an_mmf',
            '동작 중에는 2차가 1차 암페어턴의 대부분을 상쇄한다. 나머지 권선을 '
            '모두 Open 으로 두면 시험 전류 전부가 코어를 자화시킨다. 그래서 벤치에서는 '
            '설계 자속에 탱크 피크 %(Icomp).2f&nbsp;A 가 아니라 '
            '%(ILm).2f&nbsp;A 에서 닿는다.' % V))
    _r1, _r2 = V['OVP1'] / V['Vout'], V['OVP2'] / V['Vout']
    _iocp = float(A.SH['I.OCP1'])
    add(p('<b>이 설계의 숫자로 본 OVP2 의 이유.</b> OVP1 은 출력의 %(r1).3f 배인 '
          '%(o1).2f&nbsp;V, OVP2 는 %(r2).3f 배인 %(o2).2f&nbsp;V 다. OVP1 에서는 '
          '컨트롤러가 스위칭을 계속하므로 코어가 구동되는 채로 자속이 '
          '%(b1).0f&nbsp;mT 까지 갈 수 있다. OVP2 에서는 멈추므로 %(b2).0f&nbsp;mT '
          '가 이 코어가 겪는 가장 큰 자속이다. 이 숫자를 재료 데이터의 %(mat)s '
          '고온 B<sub>s</sub> 와 비교한다. 사양서의 항목은 이렇다: DC overlap, '
          '%(isat).0f&nbsp;A%(rnd)s에서 초기 인덕턴스의 '
          '90&nbsp;%% 이상, 상온(표&nbsp;%(t)s).'
          % dict(o1=V['OVP1'], r1=_r1, o2=V['OVP2'], r2=_r2,
                 b1=V['Bpk'] * _r1, b2=V['Bpk'] * _r2,
                 mat=_CORE.CORES[_CORE.CHOSEN]['material'],
                 isat=V['IsatTest'],
                 rnd=('(%.1f&nbsp;A 를 올림)' % V['Isatspec']
                      if V['IsatTest'] - V['Isatspec'] >= 0.05 else ''),
                 t=TR('spec-out'))))
    add(p('<b>이 부품에서 시험하는 법.</b> LCR 미터를 1차(NP1, 표&nbsp;%(t)s '
          '핀)에 걸고, 2차 둘과 센터탭과 보조 권선은 모두 Open. 소신호는 누설 '
          '시험과 같은 100&nbsp;kHz, 1&nbsp;V. 바이어스 전류를 0 에서 '
          '%(isat).0f&nbsp;A 넘게까지 단계로 올리며 단계마다 인덕턴스를 기록한다. '
          '%(isat).0f&nbsp;A 에서의 L 이 0 에서의 L(L<sub>open</sub> &asymp; '
          '%(lo).1f&nbsp;&micro;H)의 0.9 이상이면 합격. 단계는 짧게: DC 가 권선 '
          '저항으로 권선을 데우고, 데워진 코어는 더 일찍 포화한다. '
          '%(isat).0f&nbsp;A 아래에서 곡선이 꺾이는 부품은 L<sub>open</sub> 이 '
          '맞더라도 갭이 모자라거나 코어가 틀린 것이다. 고온 코어에 대한 여유는 '
          '시험이 아니라 B<sub>pk</sub> 에 들어 있다.'
          % dict(t=_nj(TR('pins'), '의', '의'), isat=V['IsatTest'],
                 lo=V['Lopen'])))
    add(p('<b>OVP2 가 없다면.</b> 전류 제한이 유일한 상한이 된다: OCP1 은 '
          '%(io).2f&nbsp;A 에서 동작하고, OVP2 기준 %(isat).1f&nbsp;A 의 '
          '%(rr).2f 배다. 같은 L<sub>&mu;</sub> 에서 이 코어(자속 목표가 요구하는 '
          '면적의 %(ra).1f 배)로는 %(bo).0f&nbsp;mT 다. %(bt).2f&nbsp;T 목표에 '
          '맞춘 코어라면 %(bt2).0f&nbsp;mT 가 되고, OVP2 가 허용하는 '
          '%(bt3).0f&nbsp;mT 로 묶으려면 코어 면적이나 N<sub>s</sub> 가 %(rr).2f '
          '배 필요하다. 관행인 i<sub>&mu;,pk</sub> 의 1.3 배는 %(rule).1f&nbsp;A '
          '로, 우연히 OVP2 값 근처일 뿐 근거가 되는 동작 조건이 없다.'
          % dict(io=_iocp, rr=_iocp / V['Isatspec'], isat=V['Isatspec'],
                 bo=V['Bpk'] * _iocp / V['Isateq'], bt=_CORE.B_MAX,
                 bt2=1e3 * _CORE.B_MAX * _iocp / V['Isateq'],
                 bt3=1e3 * _CORE.B_MAX * _r2,
                 rule=1.3 * V['Isateq'], ra=V['Aemm'] / V['Aereq'])))
    add(p('벤더가 잴 수 있는 것으로 줄이면 이것이 사양서다. L<sub>&mu;</sub> 는 '
          '일부러 넣지 않았다(%s 절).'
          % SR('트랜스포머 사양서에 꼭 적을 것')))
    ext(tbl('설계 예제의 트랜스포머 사양서.',
            [['항목', '값', '조건'],
             ['코어', '%s, %s, A<sub>L</sub> %.0f nH' % (
                 _CORE.CHOSEN, _R['material'], V['AL']),
              'TDK %s. 코일 포머 %s 에 %.1f mm 칸막이 추가. 중앙다리 갭 한 군데, '
              'A<sub>L</sub> 에 맞춰 연마'
              % (_R['core'], _R['former'], _w['sep'])],
             ['턴수', 'N<sub>p</sub> %(Np)d T; NS2 %(Ns)d T, NS3 %(Ns)d T; '
              'NAUX %(Naux)d T' % V,
              '칸 권선: 한 칸에 NP1(턴당 삼중 절연 Litz 다발 하나, %d 턴씩 %d 층). '
              '다른 칸에 NS2 와 NS3(턴당 Litz 다발 하나, NS2 의 %d 턴은 첫 층에 '
              '나란히, NS3 은 둘째 층, 같은 방향). 칸 사이 %.2f mm 칸막이. 층마다 '
              '테이프. 핀 하나에 도체 하나. 센터탭(핀 %s)은 보드에서 연결. NAUX '
              '는 삼중 절연선으로 2차 위에'
              % (_w['per_A'], _w['layers_A'], _w['sec_per'], _w['sep'],
                 _CORE.tap_text().replace(' and ', '·'))],
             ['Open 인덕턴스',
              '%(Lopen).1f &micro;H, 낮은 쪽 %(Ldrop).1f %% 이내 '
              '(식&nbsp;%(e)s)' % dict(V, e=ER('Ldrop')),
              'NP1 에서 측정. 나머지 권선(NS2, NS3, NAUX) 모두 Open. LCR 미터 '
              '100 kHz, 1 V'],
             ['누설 인덕턴스, 반쪽마다',
              '%(Lshort).1f &micro;H &plusmn;10 %%' % V,
              'NP1 에서 측정. NS2 만 Short, NS3 과 NAUX 는 Open. 그다음 NS3 만 '
              'Short, NS2 와 NAUX 는 Open. LCR 미터 100 kHz, 1 V. 추정 %s '
              '%.2f &micro;H(%s 절). 두 반쪽 모두 합격해야 한다: 탱크가 보는 것은 '
              '도통하는 반쪽이다'
              % (_nj('%.2f' % _h2, '과', '와'), _h3, SR('코어 고르기'))],
             ['누설 인덕턴스, 두 반쪽 모두 Short', '기록',
              '위와 같되 NS2 와 NS3 을 함께 Short. 추정 %.2f &micro;H 로 반쪽 '
              '하나씩보다 낮다' % _ef],
             ['DC overlap', '초기 인덕턴스의 &ge; 90 %%' % V,
              'NP1 에서 측정, 나머지 권선 모두 Open. DC %(IsatTest).0f A 를 '
              '100 kHz, 1 V 신호에 겹침. 상온(표시 7)' % V],
             ['1차 전류', '%(Iprilc).1f A rms / %(Icomp).1f A pk' % V,
              '라인 사이클 실효값(표시 2)과 합성 피크(표시 1), 둘 다 HB 경계'
              '(하프브리지 %(Veqlo).0f Vac), Full load' % V],
             ['2차 전류, 권선마다',
              '%(Idio).1f A rms / %(Isec).0f A pk' % V,
              '라인 사이클 실효값(표시 5)과 피크(표시 4), 둘 다 HB 경계, '
              'Full load'],
             ['코어 면적', 'A<sub>e</sub> &ge; %(Aereq).0f mm&sup2;' % V,
              'f<sub>r</sub> 에서 B<sub>pk</sub> 를 %.2f T 이하로(표시 6)'
              % _CORE.B_MAX],
             ['스위칭 주파수', '%(fswA).0f ~ %(fswB).0f kHz' % V,
              '라인 피크, Full load, HB 경계에서 FB 경계까지. 영교차 근처에서는 '
              'f<sub>o</sub> = %(fo).1f kHz 쪽으로 내려간다' % V],
             ['절연', '강화 절연, NP1 + NAUX 대 NS2 + NS3 와 코어: 삼중 절연선이 '
              '맡는다. 핀에서 clearance &ge; %.1f mm, creepage &ge; %.1f mm'
              % (_INS.req()['clearance'], _INS.req()['creep']),
              '표&nbsp;%s. 칸막이는 절연을 맡지 않는다'
              % TR('inscheck')],
             ['내전압', '%d V ac 60 s (%d V dc)'
              % (_INS.req()['hipot_ac'], _INS.req()['hipot_dc']),
              'NP1 + NAUX 대 NS2 + NS3 와 코어. 형식 시험, 절연 파괴 없을 것']],
            widths=[CW * 0.28, CW * 0.34, CW * 0.38], key='spec-out', split=True))
    add(h2('출력 뱅크 설계 결과'))
    add(p('%(ref)s 절의 두 조건 중 큰 쪽으로 정한다. <b>리플 조건</b>, &Delta;v 는 비율로:' % dict(V, ref=SR('출력 커패시터 뱅크'))))
    add(eqagain('Crip'))
    add(calc(r'C_{out}\geq\frac{%.1f\ \mathrm{W}}{2\pi\times %.0f\ \mathrm{Hz}'
             r'\times %.2f\times %.0f\ \mathrm{V^{2}}}=\mathbf{%.2f\ mF}'
             % (V['Pout'], V['flmin'], V['dv'] / 100.0, V['Vout'] ** 2,
                V['Crip'])))
    add(p('<b>hold-up</b>, V<sub>out</sub> 보다 리플 절반만큼 낮은 점에서 시작:'))
    add(eqagain('Chold'))
    add(calc(r'C_{out}\geq\frac{2\times %.1f\ \mathrm{W}\times %.3f\ \mathrm{s}}'
             r'{%.3f^{2}-%.0f^{2}}=\mathbf{%.2f\ mF}'
             r'\qquad(\mathrm{started\ at\ }V_{out}:\ %.2f\ \mathrm{mF})'
             % (V['Pout'], V['Thold'] / 1e3, V['Vout'] - V['dVo'] / 2,
                V['Vomin'], V['Chold'],
                2 * V['Pout'] * V['Thold'] / 1e3
                / (V['Vout'] ** 2 - V['Vomin'] ** 2) * 1e3)))
    add(p('<b>어느 조건이 결정하나</b>, k = V<sub>o,min</sub>/V<sub>out</sub> = '
          '%(k).3f 에서:' % dict(k=V['Vomin'] / V['Vout'])))
    add(eqagain('ripscreen'))
    add(calc(r'%.3f\ >\ %.3f\quad\Longrightarrow\quad\mathrm{ripple\ decides}'
             % (V['ripLHS'], V['ripRHS'])))
    add(p('좌변이 우변보다 %(pks).1f&nbsp;%% 클 뿐이다. 허용 리플이 %(swap).1f&nbsp;%% 를 넘으면 홀드업이 결정한다. '
          '실장한 뱅크는 %(Crip).1f&nbsp;mF 이상인 가장 가까운 조합이다: '
          '<b>%(Cout1).0f&nbsp;&micro;F &times; %(nC).0f = '
          '%(Cout).1f&nbsp;mF</b>.' % dict(V, pks=100 * (V['ripKs'] - 1), swap=V['ripSwap'])))
    add(fig('f19_cout_criterion',
            '왼쪽: 두 조건 모두 1/V<sub>out</sub>&sup2; 으로 내려간다. '
            '%(Vout).0f&nbsp;V 에서 리플은 %(Crip).1f&nbsp;mF, hold-up 은 '
            '%(Chold).1f&nbsp;mF 을 요구한다. 오른쪽: 같은 hold-up 에너지 %(Ehold).1f&nbsp;J 을 저장하는 데 400&nbsp;V 버스에서는 %(Cbulk).0f&nbsp;&micro;F 한 개면 되고, 여기서는 %(Chold).1f&nbsp;mF, %(Cratio).0f 배가 든다. 그 비가 이 구조의 대가다.' % V))
    ext(tbl('선정한 뱅크의 실제 성능과 부담.',
            [['항목', '값', '기준'],
             ['달성 리플', '%(dVo).2f V (%(dVopc).2f %%)' % V,
              '허용 %(dv).0f %%' % V],
             ['달성 hold-up', '%(thold).2f ms' % V,
              '요구 %(Thold).0f ms(100 Vac, 리플 골에서 %(Vomin).0f V 까지) &mdash; 골이 '
              '아니라 V<sub>out</sub> 에서 시작하면 %(tholdVo).2f ms' % V],
             ['리플 전류, 스위칭 성분',
              '%(ICouthf).1f A rms' % V, '&mdash;'],
             ['리플 전류, 2f<sub>l</sub> 성분',
              '%(ICout2f).1f A rms' % V, '스위칭 성분과 직교(제곱합)'],
             ['리플 전류, 합계', '<b>%(ICout).2f A rms</b>' % V,
              '%(nC).0f 개 각각에 %(each).2f A'
              % dict(V, each=A.SH['I.Cout_each'])],
             ['뱅크 ESR', '%(esr).4f m&Omega;'
              % dict(V, esr=A.SH['ESR.out']),
              '개당 %(esr1).0f m&Omega;, %(nC).0f 개 병렬'
              % dict(V, esr1=A.SH['ESR.single'])],
             ['리플과 노이즈', '%(RN).1f mV' % V,
              '%(Ccer).0f &micro;F 세라믹 바이패스 포함' % V]],
            widths=[CW * 0.30, CW * 0.22, CW * 0.48], key='bank-built', split=True))

    # ------------------------------------------------ 손실 budget
    add(h2('손실 분배'))
    add(p('사양은 손실 %(diff).1f&nbsp;W 를 허용했고, 부품을 고르기 전에 셋으로 나눴다. 나중에 계산한 소자 손실이 그 분배와 맞을 이유는 '
          '없고, 여기서도 맞지 않는다.' % dict(V, diff=V['Pin'] - V['Pout'])))
    ext(tbl('가정한 budget 과 계산한 소자 손실. 아래 항목들은 위 budget 의 세부 내역이 아니다.',
            [['항목', '값', '비고'],
             ['<b>budget</b> &mdash; 입력 브리지', '%(a).2f W'
              % dict(a=A.SH['P.d_BR']), '동기 브리지 가정'],
             ['<b>budget</b> &mdash; EMI 필터', '%(a).2f W'
              % dict(a=A.SH['P.d_EMI']), '&mdash;'],
             ['<b>budget</b> &mdash; LLC 단', '%(a).2f W'
              % dict(a=A.SH['P.d_LLC']),
              'P<sub>in,LLC</sub> 의 &eta;<sub>HB</sub> = %(etaHB).0f %%' % V],
             ['1차 도통, 고정 소자', '%(Ploss).2f W' % V,
              '스위칭하지 않는 하프브리지 레그 &mdash; 가장 뜨거운 단일 소자'],
             ['1차 도통, 스위칭하는 두 자리',
              '%(a).2f W' % dict(a=A.SH['P.pri_tot'] - A.SH['P.mos_dc']),
              '하프브리지의 S1 과 S2, 각 %(b).2f W. 도통 손실만이고 스위칭 '
              '손실은 들어 있지 않다' % dict(b=A.SH['P.mos_sw'])],
             ['2차 정류기', '%(a).2f W'
              % dict(a=A.SH['P.SR']),
              '소자당 %(PSR).3f W, 레그당 %(nSR).0f 개 병렬' % V],
             ['전류 sense 저항', '%(a).2f W'
              % dict(a=A.SH['P.RCS']),
              '라인 사이클 평균; 최악 스위칭 사이클에서는 %(b).2f W'
              % dict(b=A.SH['P.RCS_pk'])],
             ['출력 커패시터 ESR', '%(a).3f W'
              % dict(a=A.SH['P.Cout']),
              '리플 전류 전부를 스위칭 주파수 ESR 로 계산. 더 큰 120&nbsp;Hz '
              'ESR 에 흐르는 2f<sub>l</sub> 성분은 빠져 있다(실장 부품의 '
              'tan&thinsp;&delta; 모름)'],
             ['V<sub>CC</sub> 패스 트랜지스터', '%(a).2f W'
              % dict(a=A.SH['P.Qpass_nom']),
              '공칭 출력에서. 게이트 구동 자체는 f<sub>Max</sub> 에서 최대 '
              'I<sub>VCC</sub>V<sub>CC,reg</sub> = %(g).2f W 로, 드라이버와 게이트 '
              '저항에서 소모되며 합계에 넣지 않았다'
              % dict(g=A.SH['I.VCC'] * 1e-3 * A.SH['V.CC_reg'])],
             ['V<sub>CC,SR</sub> 패스 트랜지스터와 SR 컨트롤러',
              '%(a).2f W' % dict(a=A.SH['P.QSR_run'] + A.SH['P.SR_run']),
              '공칭 출력에서 Q<sub>SR</sub> 에 %(q).2f W, TEA2095TE 에 %(c).3f W. '
              'SR 게이트 전하 자체가 이 안에 들어 있다'
              % dict(q=A.SH['P.QSR_run'], c=A.SH['P.SR_run'])],
             ['<b>항목 합계</b>', '<b>%(t).2f W</b>'
              % dict(t=A.SH['P.pri_tot'] + A.SH['P.SR']
                     + A.SH['P.RCS'] + A.SH['P.Cout'] + A.SH['P.Qpass_nom']
                     + A.SH['P.QSR_run'] + A.SH['P.SR_run']),
              '소자만이다: 트랜스포머 권선이 %.1f ~ %.1f W 를 더한다(DC 와 소선 '
              '손실, %s 절). 코어 손실은 여기서 계산하지 않았다'
              % (_pdc + _pa['P_pri'] + _pa['P_sec'],
                 _pdc + _pb['P_pri'] + _pb['P_sec'],
                 SR('코어 고르기'))]],
            widths=[CW * 0.34, CW * 0.14, CW * 0.52], key='loss', split=True))
    add(p('<b>고정된 1차 소자</b>는 하프브리지 모핑에서 스위칭하지 않는 레그의 로우사이드 '
          '스위치다. 라인 사이클 실효 전류 전부를 계속 흘린다. R<sub>DS(on)</sub> 은 25&nbsp;&deg;C 값 %(R25).0f&nbsp;m&Omega; 에 '
          'k<sub>T</sub>&nbsp;=&nbsp;%(kT)s 곱한 <b>고온</b> 값이다(%(ref)s 절).'
          % dict(V, kT=_nj('%.1f' % V['Rdpk'], '을', '를'), R25=V['Rdp'],
                 ref=SR('반도체 요구조건'))))
    add(calc(r'P_{mos,dc}=I_{pri}^{2}\,k_{T}R_{DS(on),25}'
             r'=(%(I).3f)^{2}\cdot%(kT).1f\cdot%(R).0f\times10^{-3}'
             r'=%(P).2f\;\mathrm{W}'
             % dict(I=A.SH['I.pri_lc'], kT=V['Rdpk'], R=V['Rdp'],
                    P=A.SH['P.mos_dc'])))
    add(p('<b>2차 정류기</b> 각각은 병렬 %(nSR).0f 개로 레그 전류를 나눠 '
          '흘리고, %(Rs).1f&nbsp;m&Omega; 에 k<sub>T</sub>&nbsp;=&nbsp;%(kTs).1f '
          '이다(STL160N10F8, %(ref)s 절).'
          % dict(V, kTs=V['Rdsk'], Rs=V['Rds'],
                 ref=SR('SR MOSFET: STL160N10F8'))))
    add(calc(r'P_{SR}=\left(\frac{%(I).2f}{%(n).0f}\right)^{2}'
             r'\cdot%(kT).1f\cdot%(R).1f\times10^{-3}'
             r'=%(P).3f\;\mathrm{W\;per\;device}'
             % dict(I=V['Idio'], n=V['nSR'], kT=V['Rdsk'], R=V['Rds'],
                    P=A.SH['P.SR_dev'])))
    add(note('<b>효율 가정은 낙관적이다.</b> 항목별 소자 손실은 %(t).1f&nbsp;W 로, '
             '&eta;<sub>HB</sub> = %(etaHB).0f&nbsp;%% 가 허용하는 '
             '%(b).1f&nbsp;W 를 트랜스포머 전에 이미 넘는다. 전기적 설계는 이 차이에 영향받지 않는다. 열 설계는 영향을 받으며, 실측으로 정한다.'
             % dict(V, t=A.SH['P.pri_tot'] + A.SH['P.SR']
                    + A.SH['P.RCS'] + A.SH['P.Cout'] + A.SH['P.Qpass_nom']
                    + A.SH['P.QSR_run'] + A.SH['P.SR_run'],
                    b=A.SH['P.d_LLC'])))

    # ------------------------------------------------ 만든 루프
    add(h2('이 설계의 반도체 요구조건'))
    add(p('%s 절의 요구조건을 이 설계의 숫자로 적는다. 이어지는 절들이 실장 '
          '부품을 이 요구조건에 대조한다.' % SR('반도체 요구조건')))
    ext(tbl('설계 예제의 반도체 요구조건.',
            [['항목', '요구조건'],
             ['1차 드레인-소스 전압',
              '&ge; %(VDS).0f V, 그래서 600 V 급' % V],
             ['1차 바디 다이오드',
              'fast recovery: capacitive 영역에 들어가면 소자가 반대쪽 소자의 '
              '도통 중인 바디 다이오드 위에서 켜진다(%s 절)'
              % SR('다이오드가 한쪽에서만 역회복하는 이유')],
             ['1차 소자당 R<sub>DS(on)</sub>',
              '손실 budget 을 맞추려면 <b>고온</b>에서 &le; %(Rdreq).1f m&Omega;'
              % V],
             ['1차 C<sub>o(tr)</sub>',
              '탱크가 %(tD).0f ns 에서 드라이버 지연 편차를 뺀 시간 안에 노드 '
              '전압을 스윙시킬 수 있을 만큼 작게' % V],
             ['게이트 드라이버',
              '레그당 하프브리지 드라이버 하나, 플로팅부는 버스 피크 위까지. '
              '부트스트랩 다이오드는 1차 스위치와 같은 정격. 게이트마다 싱크 '
              '피크를 견디는 턴오프 다이오드'],
             ['2차 드레인-소스 전압',
              '센터탭의 두 배를 포함해 &ge; %(VDSs).0f V' % V],
             ['2차 정류기 전류',
              '레그당 %(Idio).2f A rms, 피크 %(Isec).1f A' % V],
             ['2차 패키지',
              '다이만이 아니라 리드와 클립 정격을 확인할 것'],
             ['V<sub>CC</sub> 패스 트랜지스터(NPN)',
              '%.0f mA 에서 &beta; &ge; %.0f. OVP1 에서 %.2f W 소모. %.1f V 에 '
              '권선 스파이크를 더한 전압을 견딜 것'
              % (A.SH['I.VCC'], V['bmin'], A.SH['P.Qpass'],
                 A.SH['V.Caux_OVP2'])],
             ['V<sub>CC</sub> 제너',
              '%.0f V &plusmn;%.0f %%, 정격 %.0f mW 이상'
              % (V['DZ'], 100 * V['tolDZ'], A.SH['P.DZ'])],
             ['V<sub>CC</sub> 정류 다이오드와 바이패스 다이오드',
              '역전압 정격이 %.1f V 에 권선 스파이크를 더한 값 이상'
              % A.SH['V.Caux_OVP2']]],
            widths=[CW * 0.36, CW * 0.64], split=True))
    # ------------------------------------------------ 실장 부품
    _sh = A.SH
    _Pdc = _sh['P.mos_dc']
    add(h2('1차 스위치: STO60N045DM9'))
    add(p('자리마다 ST STO60N045DM9 하나, 풀브리지에 넷이다. 600&nbsp;V, '
          '25&nbsp;&deg;C 와 V<sub>GS</sub> = 10&nbsp;V 에서 최대 '
          '%(Rdp).0f&nbsp;m&Omega;, 고속 회복 바디 다이오드, 그리고 드라이버 소스 '
          '핀이 따로 있는 TO-LL 패키지 [STO]. 그 핀 덕에 게이트 루프가 전력 소스 '
          '리드 밖으로 나온다. 데이터시트의 세 줄이 설계에 들어간다.' % V))
    add(p('<b>고온 R<sub>DS(on)</sub>.</b> 데이터시트 벡터 도면에서 읽은 정규화 '
          '곡선은 125&nbsp;&deg;C 에서 k<sub>T</sub> = %(Rdpk).1f 를 준다. 고정 '
          '소자는 %(P).2f&nbsp;W 를 소모한다(%(ref)s 절). 이것은 히트싱크 '
          '문제다. 접합-케이스는 %(rjc).1f&nbsp;&deg;C/W 이지만, 같은 부품을 '
          '2&nbsp;oz 동박 40&nbsp;&times;&nbsp;40&nbsp;mm 에 올리면 '
          '%(rja).0f&nbsp;&deg;C/W 로 적혀 있다. 이 손실에서 %(dT).0f&nbsp;&deg;C '
          '상승이다. 워크북처럼 접합 125&nbsp;&deg;C, 주위 %(ta).0f&nbsp;&deg;C '
          '로 잡으면 케이스-주위 경로에 허용되는 값은 %(rca).1f&nbsp;&deg;C/W 다. '
          '실제 주위 온도가 10&nbsp;&deg;C 오를 때마다 %(d10).2f&nbsp;&deg;C/W 씩 '
          '줄어든다. 노출 패드가 히트싱크에 닿아야 한다.'
          % dict(V, P=_Pdc, rjc=V['RthJC'], rja=V['RthJApcb'],
                 dT=_sh['ΔT.pcb'], ta=V['Tamb'], rca=_sh['R.thCA_max'],
                 d10=10.0 / _Pdc, ref=SR('손실 분배'))))
    add(p('<b>출력 전하.</b> C<sub>o(tr)</sub> = %(C).0f&nbsp;pF 는 0 에서 '
          '%(Vt).0f&nbsp;V 까지 C<sub>oss</sub> 와 같은 시간에 충전되는 고정 '
          '커패시턴스다. 그러므로 소자당 %(Q).0f&nbsp;nC 의 전하를 뜻한다. ZVS '
          '경계에서 스윙은 %(Vb).0f&nbsp;V 뿐이지만, 그 위에서 C<sub>oss</sub> 는 '
          '적어도 %(C4).0f&nbsp;pF 다. 그래서 전체 전하는 경계를 몇 %% '
          '과대평가하고, 그대로 쓴다. 소자 둘이 함께 스윙하므로 중점이 보는 값은'
          % dict(C=V['Cosstr'], Vt=V['Vosstr'], Q=V['Cosstr'] * V['Vosstr'] / 1e3,
                 Vb=2 ** 0.5 * V['Veqlo'], C4=V['Coss400'])))
    add(calc(r'c_{HB}=\frac{2\cdot%(C).0f\,\mathrm{pF}\cdot%(Vt).0f}'
             r'{\sqrt{2}\cdot%(Vm).2f}+%(Cp).0f\,\mathrm{pF}'
             r'=%(c).0f\;\mathrm{pF}'
             % dict(C=V['Cosstr'], Vt=V['Vosstr'], Vm=V['Veqlo'],
                    Cp=V['Cpar'], c=_sh['c.HB'])))
    add(p('이다. 부품을 고르기 전에 가정한 %(old).0f&nbsp;pF 대신이다. Q 의 '
          '데드타임 한계는 Q<sub>ZVS2</sub> = %(q2).2f 로 옮겨 가는데, 게인 '
          '피크 한계 %(q1).3f 보다 여전히 위이므로 탱크는 바뀌지 않는다. 스윙은 '
          '%(tD).0f&nbsp;ns 데드타임 중 T<sub>T</sub> = %(tt).0f&nbsp;ns 를 '
          '쓴다.'
          % dict(V, old=800, q2=_sh['Q.ZVS2'], q1=_sh['Q.ZVS1'],
                 tt=_sh['T.T'])))
    add(p('<b>게이트 전하.</b> 데이터시트는 0 에서 10&nbsp;V 까지 '
          '%(q10).0f&nbsp;nC 를, 그 곡선은 12&nbsp;V 에서 %(q12).0f&nbsp;nC 를 '
          '준다. 둘 사이는 식&nbsp;%(e)s 의 직선이고 C<sub>g</sub> = '
          '%(cg).1f&nbsp;nF 다. 가장 높은 레귤레이션 레일에서, 그리고 기동이 '
          '시작되는 V<sub>CCon</sub> 에서 전하 Q<sub>g,run</sub> 과 '
          'Q<sub>g,SU</sub> 는'
          % dict(q10=V['Qg10'], q12=V['Qg12'], cg=_sh['C.g_hi'],
                 e=ER('qgv'))))
    add(calc(r'Q_{g,run}=%(q10).0f+%(cg).1f\,(%(vm).2f-10)=%(qr).1f\;\mathrm{nC}'
             r'\,,\qquad Q_{g,SU}=%(q10).0f+%(cg).1f\,(%(von).0f-10)'
             r'=%(qs).1f\;\mathrm{nC}'
             % dict(q10=V['Qg10'], cg=_sh['C.g_hi'], vm=_sh['V.CC_reg_max'],
                    von=V['VCCon'], qr=_sh['Q.g_run'], qs=_sh['Q.g_SU'])))
    add(note('두 값 모두 V<sub>DD</sub> = 400&nbsp;V 하드 스위칭에서 잰 것이다. '
             'ZVS 에서는 Miller 몫(33&nbsp;nC)이 흐르지 않으므로 운전 전류를 '
             '과대평가한다. 그래도 그대로 둔다. 기동의 첫 펄스들은 하드 '
             '스위칭이기 때문이다.'))

    add(h2('게이트 드라이버: L6498LD 2개'))
    add(p('L6790A 는 게이트를 직접 구동하지 않는다. 레그마다 L6498LD 하나를 둔다. '
          'ST L6498 고전압 하프브리지 게이트 드라이버의 SO-14 판이고 [L6498], '
          '레귤레이션된 V<sub>CC</sub> 에서 전원을 받는다(그림&nbsp;%s).'
          % FR('an_gate_drive')))
    add(fig('an_gate_drive',
            '실장한 레그 하나. 핀 번호는 L6790A 는 ST EVL6790_670W 제어 보드의 '
            '번호, L6498LD 는 SO-14 의 번호다. 레그 2(S3, S4)는 HOUT2 와 LOUT2 에 '
            '같은 회로다. 브리지 귀환은 컨트롤러 접지다. R<sub>CS</sub> 는 그 '
            '접지와 입력 정류기 음극 사이에 있고 ISEN 이 거기서 읽는다(L6790A '
            '데이터시트 블록도). D<sub>BS</sub> 는 외부 부트스트랩 다이오드다. '
            '각 R<sub>G</sub> 에 역병렬인 D<sub>G,off</sub> 와 R<sub>G,off</sub> '
            '가 턴오프를 맡는다.'))
    add(tbl('L6498LD 연결, 레그마다 하나(x = 1, 2).',
            [['핀', '이름', '연결'],
             ['1', 'HIN', 'L6790A 의 HOUTx'],
             ['2', 'LIN', 'L6790A 의 LOUTx'],
             ['3', 'SGND', '컨트롤러 접지'],
             ['5', 'PGND', '로우사이드 스위치의 드라이버 소스 핀. SGND 에서 '
              '&plusmn;5&nbsp;V 까지 허용되므로 sense 저항 전압 강하를 덮는다'],
             ['6', 'LVG', '로우사이드 게이트, R<sub>G</sub> 경유. 역병렬인 '
              'D<sub>G,off</sub> 와 R<sub>G,off</sub> 가 턴오프를 맡는다'],
             ['7', 'VCC', '레귤레이션된 V<sub>CC</sub>. C<sub>BOOT</sub> 의 몇 '
              '배인 세라믹 커패시터를 바로 옆에. 부트스트랩 재충전은 매번 '
              '여기서 끌어간다'],
             ['11', 'OUT', '레그 중점, 하이사이드 스위치의 드라이버 소스 핀'],
             ['12', 'HVG', '하이사이드 게이트, R<sub>G</sub> 와 같은 턴오프 경로 '
              '경유'],
             ['13', 'BOOT', 'C<sub>BOOT</sub> 를 OUT 으로. VCC 에서 외부 고속 '
              '다이오드'],
             ['4, 8, 9, 10, 14', 'NC', '연결하지 않음']],
            widths=[CW * 0.16, CW * 0.12, CW * 0.72], key='l6498pins'))
    add(p('<b>로직.</b> 컨트롤러 출력은 high 에서 적어도 %(oh).0f&nbsp;V, low '
          '에서 많아야 %(ol).1f&nbsp;V 다. 드라이버는 %(ih).1f&nbsp;V 위를 high, '
          '%(il).2f&nbsp;V 아래를 low 로 읽는다(k = %(k1).2f 과 %(k2).2f). 두 '
          '입력이 다 high 이면 두 출력이 다 low 다. L6498 에는 enable 입력이 '
          '없으므로 DRV_EN 은 비워 둔다. 연결 하나는 다시 봐야 한다. 기동 때 '
          'L6790A 는 LOUT2 로 %(i).0f&nbsp;&micro;A 를 흘려 보내고 '
          '%(vt).1f&nbsp;V 와 비교해, 고정 하프브리지인지 모핑인지 가린다. LIN '
          '풀다운은 적어도 %(r).0f&nbsp;k&Omega; 이고 %(vx).1f&nbsp;V 가 걸리므로 '
          'LOUT2 는 여전히 Open 으로 읽힌다(k<sub>LOUT2</sub> = %(k3).2f).'
          % dict(oh=V['VOH'], ol=V['VOL'], ih=V['Vih'], il=V['Vil'],
                 k1=_sh['k.VIH'], k2=_sh['k.VIL'], i=V['IHBFB'],
                 vt=V['VHBFB'], r=V['RPD'], vx=V['RPD'] * V['IHBFB'] / 1e3,
                 k3=_sh['k.LOUT2'])))
    add(p('<b>플로팅부.</b> OUT 정격은 %(vo).0f&nbsp;V dc(1&nbsp;ms 미만은 '
          '600&nbsp;V)이고 버스 피크는 %(vb).0f&nbsp;V 다(k = %(k).3f).'
          % dict(vo=V['VOUTdrv'], vb=_sh['V.bd_rr'], k=_sh['k.OUTdrv'])))
    add(p('<b>전원.</b> 드라이버는 %(lo).0f ~ %(hi).0f&nbsp;V 에서 보증된다. '
          '레귤레이션 범위 %(a).2f ~ %(b).2f&nbsp;V 는 그 안에 있다. 기동 회로가 '
          '레일을 가장 높이 올리는 V<sub>CCon</sub> = %(on).0f&nbsp;V 도 안이다'
          '(k = %(k).3f). 드라이버 둘의 대기 전류는 %(iq).2f&nbsp;mA 다. '
          '플로팅부는 부트스트랩을 거쳐 V<sub>CC</sub> 에서 전원을 받으므로 그 '
          '몫도 들어 있다.'
          % dict(lo=V['VCCdlo'], hi=V['VCCdhi'], a=_sh['V.CC_reg_min'],
                 b=_sh['V.CC_reg_max'], on=V['VCCon'], k=_sh['k.VCCdrv'],
                 iq=_sh['I.drv_q'])))
    add(p('<b>부트스트랩.</b> L6498 은 부트스트랩 다이오드 대신 약 '
          '%(r).0f&nbsp;&Omega; 의 내장 스위치를 쓴다. f<sub>Max</sub> 에서 '
          '로우사이드는 T<sub>charge</sub> = 1/(2f<sub>Max</sub>) &minus; '
          't<sub>D</sub> = %(tc).0f&nbsp;ns 동안 켜져 있고, 식&nbsp;%(e)s 은'
          % dict(r=V['RBS'], tc=_sh['T.chg'], e=ER('bsdrop'))))
    add(calc(r'V_{drop}=\frac{%(q).1f\,\mathrm{nC}\cdot%(r).0f\,\Omega}'
             r'{%(tc).0f\,\mathrm{ns}}=%(vd).1f\;\mathrm{V}'
             % dict(q=_sh['Q.g_run'], r=V['RBS'], tc=_sh['T.chg'],
                    vd=_sh['V.drop_int'])))
    add(p('를 준다. 레일 거의 전부다. 그래서 드라이버 데이터시트가 허용하는 대로 '
          'VCC 에서 BOOT 로 외부 고속 다이오드가 충전을 맡는다. 이 다이오드는 '
          '버스를 막으므로 1차 스위치와 같은 정격이다: ES1J, 600&nbsp;V, '
          '1&nbsp;A. 전압 강하를 데이터시트의 1&nbsp;A 최대값 %(vf).2f&nbsp;V 로, '
          'C<sub>BOOT</sub> = %(cb).0f&nbsp;nF, 가장 긴 하이사이드 펄스를 '
          '1/(2f<sub>Min</sub>) = %(ton).2f&nbsp;&micro;s 로 잡으면 '
          '식&nbsp;%(e)s 은'
          % dict(vf=V['VFbs'], cb=V['CBOOT'], ton=_sh['T.on_max'],
                 e=ER('vbo'))))
    add(calc(r'\Delta V_{boot}=\frac{%(q).1f\,\mathrm{nC}+%(i).0f\,\mathrm{\mu A}'
             r'\cdot%(ton).2f\,\mathrm{\mu s}}{%(cb).0f\,\mathrm{nF}}'
             r'=%(dv).2f\;\mathrm{V}\,,\qquad V_{BO}=%(vl).2f-%(vf).1f-%(dv).2f'
             r'=%(vbo).2f\;\mathrm{V}'
             % dict(q=_sh['Q.g_SU'], i=V['IQBO'], ton=_sh['T.on_max'],
                    cb=V['CBOOT'], dv=_sh['ΔV.boot'], vl=_sh['V.CC_reg_min'],
                    vf=V['VFbs'], vbo=_sh['V.BO_run'])))
    add(p('를 준다. 권장 최소 %(m).1f&nbsp;V 에 대해 k = %(k).3f 이다. '
          '하프브리지 모핑에서 쉬는 레그는 로우사이드를 켜 두므로 그 부트스트랩은 '
          '충전된 채다. 버스트 휴지 뒤에는 컨트롤러가 둘 다 재충전하는 패턴으로 '
          '다시 시작한다.'
          % dict(m=V['VBOrec'], k=_sh['k.VBO'])))
    add(p('<b>드라이버가 V<sub>CC</sub> 아래에 두는 하한</b>은 식&nbsp;%(e)s 에서 '
          '나온다:' % dict(e=ER('vccfloor'))))
    add(calc(r'V_{CC,floor}=\max\left(%(off).0f,\;%(lo).0f,\;%(bo).1f+%(vf).1f'
             r'+%(dv).2f\right)=%(fl).2f\;\mathrm{V}'
             % dict(off=V['VCCoff'], lo=V['VCCdlo'], bo=V['VBOrec'],
                    vf=V['VFbs'], dv=_sh['ΔV.boot'], fl=_sh['V.CC_floor'])))
    add(p('기동 때 C<sub>VCC</sub> 가 어디까지 내려가도 되는지는 컨트롤러의 '
          '%(off).0f&nbsp;V lockout 이 아니라 하이사이드 전원이 정한다'
          '(%(ref)s 절).'
          % dict(off=V['VCCoff'],
                 ref=SR('보조 권선 V<sub>CC</sub> 설계 결과'))))
    _rso, _rsi = _sh['R.so'], _sh['R.si']
    add(p('<b>손실.</b> 데이터시트는 출력을 단락 전류로만 준다. 15&nbsp;V 에서 '
          '전 온도에 걸쳐 소스 적어도 %(so).1f&nbsp;A, 싱크 적어도 '
          '%(si).2f&nbsp;A 다. 그래서 출력을 %(rso).1f 과 %(rsi).1f&nbsp;&Omega; '
          '로 잡는다. 들어갈 때는 R<sub>G</sub> = %(rg).1f&nbsp;&Omega;, 나올 '
          '때는 R<sub>G,off</sub> = %(rgo).1f&nbsp;&Omega; 이고(아래), MOSFET '
          '자체의 %(rgi).1f&nbsp;&Omega; 은 양쪽에 다 있다. 그러므로 드라이버는 '
          '게이트 전력의 s<sub>drv</sub> = %(sh).3f 을 갖는다. f<sub>Max</sub> '
          '와 레일 위쪽 끝에서(식&nbsp;%(e)s)'
          % dict(so=V['Iso'], si=V['Isi'], rso=_rso, rsi=_rsi, rg=V['RG'],
                 rgo=A._builder_const('R.G_off'),
                 rgi=V['Rgint'], sh=_sh['s.drv'], e=ER('pdrv'))))
    add(calc(r'P_{drv}=2\cdot%(q).1f\,\mathrm{nC}\cdot%(v).2f\cdot%(f).1f'
             r'\,\mathrm{kHz}\cdot%(sh).3f+%(iq).0f\,\mathrm{\mu A}\cdot%(v).2f'
             r'=%(p).3f\;\mathrm{W}'
             % dict(q=_sh['Q.g_run'], v=_sh['V.CC_reg_max'], f=_sh['f.Max'],
                    sh=_sh['s.drv'], iq=V['IQCC'] + V['IQBO'],
                    p=_sh['P.drv'])))
    add(p('드라이버 하나당이고, SO-14 의 %(pm).0f&nbsp;W 에 대해 k = %(k).3f '
          '이다. %(rth).0f&nbsp;&deg;C/W 에서 %(dt).0f&nbsp;&deg;C 상승이다. '
          'f<sub>Max</sub> 는 Light load 에서만 닿으므로 이 상한은 일부러 높게 '
          '잡은 것이다.'
          % dict(pm=V['Pdrvmax'], k=_sh['k.Pdrv'], dt=_sh['ΔT.drv'],
                 rth=V['Rthdrv'])))
    _g = dict(_sh)
    for _k in ('R.G_off', 'I.FSM_Goff', 'I.FM_Goff', 'V.pl'):
        if _k not in _g:
            _g[_k] = A._builder_const(_k)
    add(p('<b>턴오프 경로.</b> 게이트마다 R<sub>G</sub> 에 역병렬인 1N4148W, '
          'D<sub>G,off</sub> 와 직렬 R<sub>G,off</sub> = %(rgo).1f&nbsp;&Omega; '
          '로 방전한다. 그래서 off 에지는 R<sub>G</sub> 가 아니라 '
          'R<sub>G,off</sub>, 드라이버 싱크, R<sub>g,int</sub> 에 달려 있다. '
          '레일 위쪽 끝에서 피크는 (%(vm).2f &minus; %(vf).1f)/(%(rgo).1f + '
          '%(rsi).1f + %(rgi).1f) = %(ip).2f&nbsp;A 다. 드라이버 싱크 전류 '
          '아래이고(k = %(ks).2f), 다이오드의 1&nbsp;&micro;s 서지 정격 '
          '%(fsm).0f&nbsp;A 아래다(k = %(kd).2f). 평균 '
          'Q<sub>g,run</sub>f<sub>Max</sub> = %(ia).0f&nbsp;mA 는 다이오드의 '
          '%(fm).0f&nbsp;mA 아래다(k = %(ka).1f). Miller 평탄부는 V<sub>pl</sub> '
          '= %(vpl).1f&nbsp;V 다. 거기서 채널이 꺼지고 중점이 스윙을 시작한다. '
          '게이트는 다이오드 경로로 레일에서 평탄부까지 t<sub>off,pl</sub> = '
          '%(tp).0f&nbsp;ns 에 떨어진다. R<sub>G</sub> 만으로는 %(tr).0f&nbsp;ns '
          '이므로 %(kt).2f 배 빠르다. 이 시간의 대부분은 R<sub>G</sub> 가 아니라 '
          '내부 저항과 싱크 저항이 정한다. 컨트롤러의 적응 데드타임은 중점이 '
          '스윙을 마치면 끝난다. 그러므로 느린 하강은 shoot-through 가 아니라 '
          '잃어버린 데드타임이 된다. 낮은 턴오프 임피던스는 다른 스위치의 dv/dt '
          '에 맞서 게이트를 붙잡아 두는 것이기도 하다.'
          % dict(rgo=_g['R.G_off'], vm=_sh['V.CC_reg_max'], vf=V['VFj'],
                 rsi=_rsi, rgi=V['Rgint'], ip=_g['I.Goff_pk'],
                 ks=_g['k.Goff_si'], fsm=_g['I.FSM_Goff'], kd=_g['k.Goff_D'],
                 ia=_g['I.Goff_avg'], fm=_g['I.FM_Goff'], ka=_g['k.Goff_avg'],
                 vpl=_g['V.pl'], tp=_g['t.off_pl'], tr=_g['t.off_RG'],
                 kt=_g['k.Goff_t'])))
    add(p('<b>타이밍.</b> 드라이버의 지연 편차는 많아야 %(mt).0f&nbsp;ns 다. '
          '그래서 게이트에 남는 데드타임은 (t<sub>D</sub> &minus; MT)/T<sub>T</sub> '
          '= %(k).3f 로 스윙을 덮는다. 이 비는 L<sub>r</sub> 과 함께 떨어진다. '
          'C<sub>r</sub>, L<sub>m</sub>, R<sub>T</sub> 를 고정하면 L<sub>r</sub> '
          '&asymp; %(lr).1f&nbsp;&micro;H 에서 1 이 된다. 자계 풀이가 허용하는 '
          '누설 하한 바로 위다(%(ref)s 절). c<sub>HB</sub> 는 상한값이고, '
          '컨트롤러는 데드타임을 40 ~ 420&nbsp;ns 사이에서 맞춘다. 그래도 첫 '
          '샘플이 낮게 나오면 t<sub>D</sub> 를 먼저 올린다. MOSFET 자체의 '
          '턴오프·턴온 지연(%(toff).0f, %(ton).0f&nbsp;ns)은 28&nbsp;A 하드 '
          '스위칭 값이라 ZVS 에는 맞지 않는다. 게이트-중점 타이밍을 잰다.'
          % dict(mt=V['MT'], k=_sh['k.TTd'], lr=_ttd_lr_edge(V, A),
                 toff=109, ton=38, ref=SR('코어 고르기'))))
    add(p('<b>기울기.</b> 드라이버의 OUT 은 많아야 %(dm).0f&nbsp;V/ns 로 '
          '움직여도 된다. 스윙 꼭대기 근처에서 C<sub>oss</sub> 는 '
          '%(c4).0f&nbsp;pF 뿐이므로, 전류 전환 전류 I<sub>Lm,pk</sub> = '
          '%(il).2f&nbsp;A 가 만드는 기울기는'
          % dict(dm=V['dvmax'], c4=V['Coss400'], il=_sh['I.Lm_pk'])))
    add(calc(r'S_{mid}=\frac{%(il).2f\,\mathrm{A}}{2\cdot%(c4).0f'
             r'+%(cp).0f\,\mathrm{pF}}=%(dv).1f\;\mathrm{V/ns}'
             % dict(il=_sh['I.Lm_pk'], c4=V['Coss400'], cp=V['Cpar'],
                    dv=_sh['dv.dt'])))
    add(p('(k = %(k).3f). 공진 위에서는 스위칭되는 전류가 I<sub>Lm,pk</sub> 를 '
          '넘을 수 있다. 실측이 요구하면 스위치마다 작은 커패시터를 병렬로 '
          '다는 것이 대책이고, 대가는 T<sub>T</sub> 다.'
          % dict(k=_sh['k.dvdt'])))
    add(note('<b>ST EVL6790_670W 가 다르게 한 것.</b> 그 회로도에서 세 가지는 '
             '맞는 곳에 가져다 쓸 만하다. 드라이버 전원을 DRV_EN 으로 P-MOSFET'
             '(BSS84, 2N7002 로 레벨 시프트)을 거쳐 끊어, idle 에서 드라이버가 '
             '전류를 쓰지 않게 한다. 하프브리지 보드는 부트스트랩을 다이오드'
             '(STTH1R06)와 직렬 3.3&nbsp;&Omega; 으로 충전해 첫 충전 전류를 '
             '제한한다. 그리고 게이트마다 소스로 10&nbsp;k&Omega; 을 둔다. L6498 '
             '은 자체 V<sub>CC</sub> 가 3&nbsp;V 를 넘어야 출력을 low 로 '
             '붙잡으므로, 그 전까지를 저항이 덮는다.'))

    add(h2('SR MOSFET: STL160N10F8'))
    _f = dict(A.SH)
    for _k in ('V.DS_SR', 'R.thJA_SR', 'Q.g_sync', 'C.g_SR', 'V.G_SRmax',
               'C.iss_SR', 'P.SR_budget'):
        if _k not in _f:
            _f[_k] = A._builder_const(_k)
    add(p('센터탭 레그마다 STMicroelectronics STL160N10F8 %(n).0f개를 병렬로 '
          '둔다 [STL]. PowerFLAT 5&times;6 의 100&nbsp;V STripFET F8 이고, '
          '드레인은 핀 5&ndash;8, 게이트는 4, 소스는 1&ndash;3 이다. %(s)s 절이 '
          '요구하는 것과 대조하면:'
          % dict(n=V['nSR'], s=SR('이 설계의 반도체 요구조건'))))
    add(tbl('STL160N10F8 과 2차 요구조건(DS14249 Rev 5).',
            [['항목', '데이터시트', '요구', '여유'],
             ['V<sub>DS</sub>', '%.0f V' % _f['V.DS_SR'],
              '%.0f V' % _f['V.DS_sec_rec'], '%.3f' % _f['k.VDSsec']],
             ['R<sub>DS(on)</sub> 최대, 25&nbsp;&deg;C, V<sub>GS</sub> = 10 V',
              '%.1f m&Omega;' % V['Rds'],
              '%.2f m&Omega;' % _f['R.dson_req_25_s'], '%.3f' % _f['k.RDSsec']],
             ['k<sub>T</sub>, 25 ~ 125&nbsp;&deg;C (Fig.&nbsp;13)',
              '%.1f' % V['Rdsk'], '&mdash;', '&mdash;'],
             ['소자당 손실, 레그당 budget',
              '%.3f W' % _f['P.SR_dev'],
              '레그당 %.1f W' % _f['P.SR_budget'], '%.3f' % _f['k.PSR']],
             ['최고 구동 전압에서의 게이트 전하',
              '%.1f nC' % _f['Q.g_SR'], '%.1f nC' % _f['Q.g_SR_max'],
              '%.3f' % _f['k.QgSR']]],
            widths=[CW * 0.42, CW * 0.18, CW * 0.22, CW * 0.18],
            key='stl160'))
    add(p('k<sub>T</sub> 는 Fig.&nbsp;13 의 벡터 곡선에서 읽었다'
          '(125&nbsp;&deg;C 에서 1.504, typical). 그러므로 고온 R<sub>DS(on)</sub> '
          '은 %(rh).1f&nbsp;m&Omega; 이고 소자 넷이 함께 %(p).2f&nbsp;W 를 '
          '잃는다. 데이터시트의 2s2p 보드 %(rt).0f&nbsp;&deg;C/W 에서 소자 하나는 '
          '%(dt).0f&nbsp;&deg;C 오른다. 실제 보드가 정한다.'
          % dict(rh=_f['R.dson_s'], p=_f['P.SR'], rt=_f['R.thJA_SR'],
                 dt=_f['ΔT.SR_dev'])))
    add(p('SR MOSFET 에서 중요한 게이트 전하는 드레인이 이미 바디 다이오드 전압에 '
          '있는 채로 켜질 때의 값이다: Q<sub>g,sync</sub> = %(q).0f&nbsp;nC, '
          '10&nbsp;V, typical. 컨트롤러는 %(vg).1f&nbsp;V 까지 구동하고, 평탄부를 '
          '지난 게이트 전하 곡선(Fig.&nbsp;8, 벡터로 읽음)은 V 당 '
          'C<sub>g,SR</sub> = %(cg).2f&nbsp;nC 씩 오르므로'
          % dict(q=_f['Q.g_sync'], vg=_f['V.G_SRmax'], cg=_f['C.g_SR'])))
    add(calc(r'Q_{g,SR}=%(q).0f+%(cg).2f\cdot(%(vg).1f-10)=%(r).1f\;\mathrm{nC}'
             % dict(q=_f['Q.g_sync'], cg=_f['C.g_SR'], vg=_f['V.G_SRmax'],
                    r=_f['Q.g_SR'])))
    add(p('소자당이다. 게이트 핀 하나에 둘이 달리므로 C<sub>iss</sub> = '
          '%(n).0f &times; %(c).1f = %(cp).1f&nbsp;nF(50&nbsp;V, typical)다. '
          'TEA2095TE 데이터시트가 드라이버를 특성화한 10&nbsp;nF 정도다. 바디 '
          '다이오드는 60&nbsp;A 에서 V<sub>SD</sub> 최대 1.2&nbsp;V, Q<sub>rr</sub> '
          '160&nbsp;nC typical 이고, 컨트롤러가 남기는 데드타임에만 도통한다.'
          % dict(n=V['nSR'], c=_f['C.iss_SR'], cp=_f['C.iss_pin'])))

    add(h2('동기 정류: TEA2095TE'))
    add(p('NXP TEA2095TE 하나가 센터탭 두 레그를 구동하고, 레그마다 MOSFET '
          '%(nSR).0f개가 병렬이다 [TEA](그림&nbsp;%(f)s). 여기서 설계할 것은 '
          '연결과 한계뿐이다. 게이트 구동, 조절, 타이밍은 이 부품 자체의 몫이다.'
          % dict(V, f=FR('an_sr_ctrl'))))
    add(fig('an_sr_ctrl',
            '실장한 동기 정류기: 레그 A 의 Q<sub>A1</sub>, Q<sub>A2</sub> 와 레그 '
            'B 의 Q<sub>B1</sub>, Q<sub>B2</sub>. V<sub>CC,SR</sub> 은 제너 '
            '팔로워 R<sub>BSR</sub>, D<sub>ZSR</sub>, Q<sub>SR</sub> 에서 핀의 '
            'R<sub>SR</sub>&ndash;C<sub>SR</sub> 필터를 거쳐 오고, 크기는 아래에서 '
            '정한다. MOSFET 마다 게이트 저항이 따로 있다. DSx 와 SSx 는 짝의 '
            '드레인과 소스로 가는 별도의 sense 선이고, 전력 접지를 따라가지 '
            '않는다. 트랜스포머 핀은 그림&nbsp;%s 와 같다. 센터탭이 출력이다.'
            % FR('an_xfmr_pins')))
    add(tbl('TEA2095TE 연결(HSO8).',
            [['핀', '이름', '연결'],
             ['1, 8', 'GDB, GDA', '레그 B 와 레그 A 짝의 게이트'],
             ['2', 'GND', 'SR 소스의 2차 접지'],
             ['3, 6', 'DSB, DSA', '드레인 sense, 각 짝의 드레인으로 별도 배선'],
             ['4, 5', 'SSB, SSA', '소스 sense, 각 짝의 소스로 별도 배선, 전력 '
              '접지를 따라가지 않는다'],
             ['7', 'VCC', '아래의 12&nbsp;V 급 팔로워, 핀의 '
              'R<sub>SR</sub>&ndash;C<sub>SR</sub> 필터 경유']],
            widths=[CW * 0.12, CW * 0.18, CW * 0.70], key='tea2095pins'))
    _q = dict(A.SH)
    for _k in ('V.SR_char', 'I.SR_max', 'I.SR_q', 'I.SR_dch', 'R.thSR',
               'V.DZSR_sel', 'R.BSR_sel', 'C.SR', 'C.SRb', 'R.SR', 'ΔV.RSR',
               'ΔV.CSR', 'k.SRpin'):
        if _k not in _q:
            _q[_k] = A._builder_const(_k)
    add(p('<b>전원.</b> %(vo).0f&nbsp;V 출력에서 바로 받으면 컨트롤러가 자체 '
          '게이트 구동 전원까지의 차이를 떨어뜨려야 한다. 그 전압 강하에 SR '
          '게이트 전류를 곱한 만큼이 HSO8 안의 열이다. 12&nbsp;V 급 제너 팔로워, '
          '곧 식&nbsp;%(e)s 의 회로에서 바이패스 다이오드를 뺀 것이 그 전압 '
          '강하를 밖으로 꺼낸다. R<sub>BSR</sub> 은 출력에서 베이스의 제너 '
          'D<sub>ZSR</sub> 로 간다. 컬렉터는 출력에 있다. 이미터는 R<sub>SR</sub> '
          '= %(rs).0f&nbsp;&Omega; 을 거쳐 VCC 를 먹이고, 핀에는 C<sub>SR</sub> = '
          '%(c).0f&nbsp;nF 와 %(cb).1f&nbsp;&micro;F 벌크가 있다. RC 필터다'
          '(ST 보드는 거기에 10&nbsp;&micro;F 를 둔다). 저항은 f<sub>Max</sub> '
          '전류에서 %(dr).2f&nbsp;V 를 떨어뜨리고, 한 레그의 짝이 충전될 때 핀은 '
          '%(dc).2f&nbsp;V 꺼진다. 특성화된 12&nbsp;V 에 대해 k = %(kp).3f 이다. '
          '데이터시트는 게이트 구동을 V<sub>CC</sub> = %(ch).0f&nbsp;V 에서 '
          '주므로, 범위의 가운데가 아니라 아래쪽 끝을 거기에 둔다. '
          '&plusmn;%(tp).0f&nbsp;%% 의 %(z).0f&nbsp;V 제너와 V<sub>BE</sub> = '
          '%(VFj).1f&nbsp;V 로'
          % dict(V, vo=V['Vout'], e=ER('vccreg'), c=_q['C.SR'],
                 rs=_q['R.SR'], cb=_q['C.SRb'], dr=_q['ΔV.RSR'],
                 dc=_q['ΔV.CSR'], kp=_q['k.SRpin'],
                 ch=_q['V.SR_char'], z=_q['V.DZSR_sel'],
                 tp=100 * V['tolDZ'])))
    add(calc(r'V_{CC,SR}=%(z).0f-%(VFj).1f=%(r).2f\;\mathrm{V}'
             r'\,,\qquad %(lo).2f\ldots%(hi).2f\;\mathrm{V}'
             % dict(V, z=_q['V.DZSR_sel'], r=_q['V.SR'], lo=_q['V.SR_min'],
                    hi=_q['V.SR_max'])))
    add(p('%(ch).0f&nbsp;V 에 대해 k = %(k).3f 이다. 13&nbsp;V 제너라면 범위의 '
          '가운데가 12&nbsp;V 근처가 되지만 아래쪽 끝은 %(l13).2f&nbsp;V 가 된다. '
          '거기서는 게이트 구동이 보증되지 않는다. 팔로워는 전류 I<sub>SR,max</sub> '
          '= %(im).0f&nbsp;mA 에 맞춰 설계한다. 이 값이 SR MOSFET 이 가져와도 '
          '되는 최대 게이트 전하를 정한다. 주기마다 MOSFET %(n).0f개가 스위칭하고 '
          '운전 주파수 상한을 1차와 같이 f<sub>Max</sub> 로 잡으면'
          % dict(k=_q['k.SRlo'], ch=_q['V.SR_char'], im=_q['I.SR_max'],
                 n=_q['N.SRsw'],
                 l13=13 * (1 - V['tolDZ']) - V['VFj'])))
    add(calc(r'Q_{g,SR}\leq\frac{%(im).0f\,\mathrm{mA}-%(iq).2f\,\mathrm{mA}}'
             r'{%(n).0f\cdot%(fk).1f\,\mathrm{kHz}}=%(q).1f\;\mathrm{nC}'
             % dict(im=_q['I.SR_max'], iq=_q['I.SR_q'], n=_q['N.SRsw'],
                    fk=_q['f.Max'], q=_q['Q.g_SR_max'])))
    add(p('MOSFET 당이다. STL160N10F8 의 %(qg).1f&nbsp;nC 에 대해 k = %(kq).3f '
          '이다. 그러면 f<sub>Max</sub> 에서 팔로워가 흘리는 전류는'
          % dict(qg=_q['Q.g_SR'], kq=_q['k.QgSR'])))
    add(calc(r'I_{SR}=%(iq).2f+%(n).0f\cdot%(qg).1f\,\mathrm{nC}\cdot'
             r'%(fk).1f\,\mathrm{kHz}=%(i).1f\;\mathrm{mA}'
             % dict(iq=_q['I.SR_q'], n=_q['N.SRsw'], qg=_q['Q.g_SR'],
                    fk=_q['f.Max'], i=_q['I.SR'])))
    add(p('이고, I<sub>SR,q</sub> = %(iq).2f&nbsp;mA 는 컨트롤러 자체의 전류다. '
          '방전 모드 전류는 12&nbsp;V 에서 많아야 %(id).0f&nbsp;mA, 그 위에서는 '
          '더 작으므로 넉넉히 안이다(k = %(kd).3f). R<sub>BSR</sub> 은 '
          '식&nbsp;%(e)s 에서 나온다. 출력은 hold-up 끝의 값이고, '
          '&beta;<sub>min</sub> 과 I<sub>Z,min</sub> 은 같다:'
          % dict(iq=_q['I.SR_q'], id=_q['I.SR_dch'], kd=_q['k.SRdch'],
                 e=ER('rbz'))))
    add(calc(r'R_{BSR}\leq\frac{%(vm).0f-%(zm).2f}{%(im).0f/%(b).0f+%(iz).0f}'
             r'=%(r).0f\;\Omega\;\rightarrow\;%(rs).0f\;\Omega'
             % dict(vm=V['Vomin'], zm=_q['V.DZSR_sel'] * (1 + V['tolDZ']),
                    im=_q['I.SR_max'], b=V['bmin'], iz=V['IDZmin'],
                    r=_q['R.BSR_max'], rs=_q['R.BSR_sel'])))
    add(p('살 때의 정격은 OVP1(%(o1).2f&nbsp;V)에서 정한다. 제너는 No load 에서 '
          '%(pz).0f&nbsp;mW, R<sub>BSR</sub> 은 %(pr).3f&nbsp;W, 패스 '
          '트랜지스터는 I<sub>SR,max</sub> 에서 %(pq).2f&nbsp;W(공칭 출력에서 '
          '%(pn).2f&nbsp;W)다. 트랜지스터 몫은 실제 게이트 전류 '
          '%(n).0f&nbsp;&middot;&nbsp;Q<sub>g</sub>&nbsp;&middot;&nbsp;f<sub>sw</sub> '
          '에 비례한다. OVP2 출력 %(o2).2f&nbsp;V 를 막아야 한다. 이 회로가 사 '
          '주는 것: I<sub>SR,max</sub> 에서 컨트롤러 자체의 전압 강하는 '
          '(%(sx).2f &minus; %(vg).1f)&nbsp;V &times; %(ig).0f&nbsp;mA = '
          '%(pi).3f&nbsp;W 다. 데이터시트가 4층 보드에서 주는 '
          '%(rt).0f&nbsp;&deg;C/W 로 %(ti).0f&nbsp;&deg;C 상승이다. 출력에서 바로 '
          '받으면 OVP1 에서 %(pd).2f&nbsp;W, %(td).0f&nbsp;&deg;C 가 된다. 실제 '
          'I<sub>SR</sub> 에서 두 값은 공칭 출력의 패스 트랜지스터 '
          '%(prun).2f&nbsp;W 와 컨트롤러 %(ir).3f&nbsp;W 다.'
          % dict(o1=_sh['V.OVP1_act'], prun=_q['P.QSR_run'],
                 ir=_q['P.SR_run'], pz=_q['P.DZSR'], pr=_q['P.RBSR'],
                 pq=_q['P.QSR'], pn=_q['P.QSR_nom'], n=_q['N.SRsw'],
                 o2=_sh['V.OVP2_act'], sx=_q['V.SR_max'], vg=V['VGSR'],
                 ig=_q['I.SR_max'] - _q['I.SR_q'], pi=_q['P.SR_int'],
                 ti=_q['ΔT.SR'], rt=_q['R.thSR'], pd=_q['P.SR_dir'],
                 td=_q['ΔT.SR_dir'])))
    for _k in ('R.thQ', 'T.jQ', 'R.thDZ'):
        if _k not in _q:
            _q[_k] = A._builder_const(_k)
    add(p('Q<sub>SR</sub> 은 Q<sub>VCC</sub> 와 같은 FZT651 이고, 같은 '
          '50&nbsp;&times;&nbsp;50&nbsp;mm 컬렉터 패드에 있다'
          '(%(rth).1f&nbsp;&deg;C/W, T<sub>j,max</sub> %(tj).0f&nbsp;&deg;C). '
          '설계 전류 I<sub>SR,max</sub> 에서 주위 온도 %(ta).0f&nbsp;&deg;C 까지 '
          '허용한다. OVP1 에서 STL160N10F8 의 전하로는 %(po).2f&nbsp;W 를 '
          '소모하고 %(tar).0f&nbsp;&deg;C 까지 허용한다. D<sub>ZSR</sub> 은 같은 '
          'BZT52H-C15 이고, 1&nbsp;cm&sup2; 패드에서 P<sub>DZSR</sub> 로 '
          '%(tad).0f&nbsp;&deg;C 까지다.'
          % dict(rth=_q['R.thQ'], tj=_q['T.jQ'], ta=_q['T.aQSR'],
                 po=_q['P.QSR_ovp'], tar=_q['T.aQSR_run'],
                 tad=_q['T.aDZSR'])))
    add(p('그 밖의 한계. V<sub>CC</sub> 는 최대 %(m).0f&nbsp;V 다. OVP2 출력 '
          '%(o2).2f&nbsp;V 는 패스 트랜지스터가 단락됐을 때만 본다'
          '(k = %(k1).3f). 드레인 sense 입력은 %(ds).0f&nbsp;V 까지 받고, SR '
          'MOSFET 에 요구한 %(vr).0f&nbsp;V 위다(k = %(k2).2f). 게이트 구동은 '
          '전원이 12&nbsp;V 이상이면 %(vg).1f ~ 11.2&nbsp;V 사이에 유지되므로, '
          'SR R<sub>DS(on)</sub> 을 주는 10&nbsp;V 를 넘는다(k = %(k3).3f). 전원 '
          '%(st).2f&nbsp;V 아래에서는 꺼지고 바디 다이오드가 정류한다.'
          % dict(o2=_sh['V.OVP2_act'], m=V['SRcc'], k1=_sh['k.SRVCC'],
                 ds=V['DSsense'], vr=V['VDSs'], k2=_sh['k.DSsense'],
                 vg=V['VGSR'], k3=_sh['k.VGSR'], st=V['SRstart'])))
    _pd = 0.4 * V['Vout'] / _q['V.SR']
    add(p('이 부품의 기능 둘이 이 설계와 만난다. 게이트 핀마다 MOSFET 둘을 '
          '구동하므로 전하가 하나의 두 배인데, 데이터시트는 드라이버를 '
          '10&nbsp;nF 로 특성화했다. 시제품에서 턴온·턴오프 시간을 확인한다. '
          '그리고 정류 동작이 1.4&nbsp;s(적어도 1.1&nbsp;s) 없으면 출력을 '
          '방전하려고 0.4&nbsp;W / V<sub>CC</sub> 를 끈다. 팔로워를 거치므로 그 '
          '전류는 출력에서 오고, 출력은 %(vo).0f/%(vs).1f &times; 0.4 = '
          '%(pd).2f&nbsp;W 를 내놓는다. 상용전원이 끊긴 뒤 %(co).1f&nbsp;mF '
          '뱅크, %(vo).0f&nbsp;V 에서 %(e).1f&nbsp;J 은 약 %(t).0f&nbsp;s 에 '
          '비워진다. 그러나 No load 에서 1.1&nbsp;s 보다 긴 깊은 버스트 휴지도 '
          '이 기능을 켜고, 대기 전력에 %(pd).2f&nbsp;W 를 더한다. No load 의 가장 '
          '긴 burst-off 시간을 잰다.'
          % dict(V, co=V['Cout'], e=0.5 * V['Cout'] * 1e-3 * V['Vout'] ** 2,
                 vo=V['Vout'], vs=_q['V.SR'], pd=_pd,
                 t=0.5 * V['Cout'] * 1e-3 * V['Vout'] ** 2 / _pd)))
    add(note('<b>ST EVL6790_670W 의 SR 보드</b>는 같은 핀 배치의 TEA2096 을 '
             '쓰고, 레그당 ISC079N15NM6 둘이다. 게이트마다 0&nbsp;&Omega; 자리를, '
             '드레인 sense 선마다 직렬 220&nbsp;&Omega; 을 둔다. V<sub>CC</sub> 는 '
             '보조 레일에서 10&nbsp;&Omega; 을 거쳐 오고 핀에 10&nbsp;&micro;F 가 '
             '있다.'))

    add(h2('전압 루프 설계 결과'))
    from math import atan, degrees, sqrt, pi
    _at = lambda w, w0: degrees(atan(w / w0))
    _A = lambda w: (sqrt(1 + (w / V['wz']) ** 2)
                    / (sqrt(1 + (w / V['wp']) ** 2) * sqrt(1 + (w / V['wpx']) ** 2)))
    add(p('%(a)s 절부터 %(b)s 절까지의 방법을 이 설계 값으로 계산 순서대로 적용한다.'
          % dict(a=SR('전압 루프와 보상'),
                 b=SR('버스트 threshold 에 대한 피드백 리플'))))
    add(p('<b>STEP 1 &mdash; 출력 분압기</b>, R<sub>I</sub> = '
          '%(RI).0f&nbsp;k&Omega; 으로 정하고:' % V))
    add(eqagain('RoVout'))
    add(calc(r'R_{O}=\frac{V_{R}\,R_{I}}{V_{out}-V_{R}}'
             r'=\frac{%.3f\ \mathrm{V}\times %.0f\ \mathrm{k\Omega}}'
             r'{%.1f\ \mathrm{V}-%.3f\ \mathrm{V}}=%.2f\ \mathrm{k\Omega}'
             r'\;\rightarrow\;\mathbf{%.0f\ k\Omega}'
             % (V['VR'], V['RI'], V['Vout'], V['VR'], V['Roc'], V['Ro'])))
    add(calc(r'V_{out}=%.3f\ \mathrm{V}\times\left(1+\frac{%.0f}{%.0f}\right)'
             r'=\mathbf{%.2f\ V}' % (V['VR'], V['RI'], V['Ro'], V['VoutAct'])))
    add(p('<b>STEP 2 &mdash; 플랜트.</b> 식&nbsp;%(e)s 기울기 K<sub>pwr</sub> = '
          '2K<sub>HV</sub>/(K<sub>M</sub>K<sub>FF</sub>) 로 V<sub>FB</sub> = K<sub>pwr</sub> '
          'R<sub>CS</sub> P<sub>in,LLC</sub> = %(Kpwr).3f &times; '
          '%(RCS).0f&nbsp;m&Omega; &times; %(PinLLC).1f&nbsp;W = '
          '%(VFBv).3f&nbsp;V. 그다음'
          % dict(V, PinLLC=V['Pout'] / (V['etaHB'] / 100.0), e=ER('VFB'))))
    add(eqagain('Gplant'))
    add(calc(r'G_{o}=\frac{%.1f\ \mathrm{W}}{%.1f\ \mathrm{V}\times %.3f\ \mathrm{V}'
             r'\times %.1f\ \mathrm{mF}}=\mathbf{%.1f\ rad/s},\qquad '
             r'f_{cto}=\frac{%.1f}{2\pi}=%.1f\ \mathrm{Hz}'
             % (V['Pout'], V['Vout'], V['VFBv'], V['Cout'], V['Go'], V['Go'],
                V['fcto'])))
    add(p('<b>STEP 3 &mdash; 2f<sub>l</sub> 에서 허용되는 게인</b>, 3차 고조파 '
          '%(D3set).0f&nbsp;%% 에 대해:' % V))
    add(eqagain('dVloop'))
    add(calc(r'\Delta V_{loop}=\frac{%.1f\ \mathrm{W}}{%.1f\ \mathrm{V}}\cdot'
             r'\frac{1}{2\pi\times %.0f\ \mathrm{Hz}\times %.1f\ \mathrm{mF}}'
             r'=\mathbf{%.3f\ V}' % (V['Pout'], V['Vout'], V['flmin'], V['Cout'],
                                     V['dVloop'])))
    add(eqagain('GEAreq'))
    add(calc(r'G_{EA}(2f_{l})\leq\frac{4\times %.3f\ \mathrm{V}\times %.2f}'
             r'{%.3f\ \mathrm{V}}=\mathbf{%.4f}'
             % (V['VFBv'], V['D3set'] / 100.0, V['dVloop'], V['GEAreq'])))
    add(p('<b>STEP 4 &mdash; K factor</b>, 목표 phase margin %(PhiM).0f&deg;'
          '(tan&nbsp;%(PhiM).0f&deg; = %(tPM).4f), &alpha;<sub>v</sub> = '
          '%(alphav).1f 에 대해:' % V))
    add(eqagain('Kv'))
    add(calc(r'K_{v}=\frac{1}{2\times %.1f}\left[(1+%.1f^{2})\times %.4f'
             r'+\sqrt{(1+%.1f^{2}\times %.4f)^{2}+4\times %.1f^{2}}\right]'
             r'=\mathbf{%.4f}'
             % (V['alphav'], V['alphav'], V['tPM'], V['alphav'], V['tPM'],
                V['alphav'], V['Kv'])))
    add(p('<b>STEP 5 &mdash; 보상기 게인 상수:</b>'))
    add(eqagain('EAotarget'))
    add(calc(r'EA_{o}=\frac{2\pi\times %.0f\ \mathrm{Hz}\times %.4f}{%.4f^{2}}'
             r'=\mathbf{%.2f\ rad/s}'
             % (2 * V['flmin'], V['GEAreq'], V['Kv'], V['EAo'])))
    add(p('<b>STEP 6 &mdash; zero 와 pole</b>, &Gamma;<sub>v</sub> = 0.744 &times; '
          '%(Veqhi).1f / %(Veqlo).2f = %(gv)s:'
          % dict(V, Veqhi=V['Vacmax'],
                 gv=_nj('%.4f' % V['Gammav'], '으로', '로'))))
    add(eqagain('fMB'))
    add(calc([r'f_{MB}=\frac{1}{2\pi}\sqrt{\frac{%.2f\times %.4f\times %.2f}{%.4f}}'
              r'=\mathbf{%.2f\ Hz}'
              % (V['Go'], V['Kv'], V['EAo'], V['Gammav'], V['fMB']),
              r'f_{p}=%.4f\times %.2f=\mathbf{%.2f\ Hz},'
              r'\qquad f_{z}=\frac{%.2f}{%.4f}=\mathbf{%.3f\ Hz}'
              % (V['Kv'], V['fMB'], V['fp'], V['fMB'], V['Kv'], V['fz'])]))
    add(p('<b>STEP 7 &mdash; 바이어스 부품</b>, TL431 최소 전류 %(Imin).1f&nbsp;mA, '
          'V<sub>Z</sub> = %(VZ).0f&nbsp;V, V<sub>Fo</sub> = %(VFo).2f&nbsp;V, '
          'I<sub>FB,steady</sub> = %(IFBs).0f&nbsp;&micro;A, I<sub>FB,max</sub> = '
          '%(IFBm).0f&nbsp;&micro;A, CTR<sub>s</sub> = %(CTRs).2f, '
          'CTR<sub>m</sub> = %(cm)s:'
          % dict(V, cm=_nj('%.2f' % V['CTRm'], '으로', '로'))))
    add(eqagain('RPmax'))
    add(calc(r'R_{P}\leq\frac{%.2f\ \mathrm{V}}{%.1f\ \mathrm{mA}}=%.3f\ \mathrm{k\Omega}'
             r'\;\rightarrow\;\mathbf{%.1f\ k\Omega}\ (\mathrm{rounded\ down})'
             % (V['VFo'], V['Imin'], V['RPmax'], V['RP'])))
    add(eqagain('RBwin'))
    _hd = V['VZ'] - V['VR'] - V['VFo']
    add(calc(r'R_{B,max}=\frac{%.0f-(%.3f+%.2f)\ \mathrm{V}}'
             r'{%.2f/%.1f\ \mathrm{mA}+%.0f\,\mu\mathrm{A}/%.2f}'
             r'=\frac{%.3f\ \mathrm{V}}{%.3f\ \mathrm{mA}+%.3f\ \mathrm{mA}}'
             r'=\mathbf{%.2f\ k\Omega}'
             % (V['VZ'], V['VR'], V['VFo'], V['VFo'], V['RP'], V['IFBs'],
                V['CTRs'], _hd, V['VFo'] / V['RP'], V['IFBs'] / V['CTRs'] / 1e3,
                V['RBmax'])))
    add(calc(r'R_{B,min}=\frac{%.3f\ \mathrm{V}}{%.3f\ \mathrm{mA}+'
             r'%.0f\,\mu\mathrm{A}/%.2f}=\mathbf{%.2f\ k\Omega}'
             r'\qquad\rightarrow\ R_{B}=\mathbf{%.1f\ k\Omega}'
             % (_hd, V['VFo'] / V['RP'], V['IFBm'], V['CTRm'], V['RBmin'],
                V['RB'])))
    add(p('<b>STEP 8 &mdash; 보상 부품</b>, R<sub>FB</sub> = %(RFB).0f&nbsp;k&Omega;, '
          'C<sub>opto</sub> = %(Copto).0f&nbsp;nF, 고주파 pole %(fpHF).0f&nbsp;Hz '
          '로:' % V))
    add(eqagain('Ccomp'))
    add(calc(r'C_{Fo}=\frac{%.3f}{%.2f}\cdot\frac{%.2f\times %.0f\ \mathrm{k\Omega}}'
             r'{%.0f\ \mathrm{k\Omega}\times %.1f\ \mathrm{k\Omega}\times %.2f}'
             r'=%.1f\ \mathrm{nF}\;\rightarrow\;\mathbf{%.0f\ nF}'
             % (V['fz'], V['fp'], V['CTRs'], V['RFB'], V['RI'], V['RB'],
                V['EAo'], V['CFoc'], V['CFo'])))
    add(calc([r'C_{F}=%.0f\ \mathrm{nF}\times\left(\frac{%.2f}{%.3f}-1\right)'
              r'=%.0f\ \mathrm{nF}\;\rightarrow\;\mathbf{%.0f\ nF}'
              % (V['CFo'], V['fp'], V['fz'], V['CFc'], V['CF']),
              r'R_{F}=\frac{1}{2\pi\times %.3f\ \mathrm{Hz}\times %.0f\ \mathrm{nF}}'
              r'=%.1f\ \mathrm{k\Omega}\;\rightarrow\;\mathbf{%.0f\ k\Omega}'
              % (V['fz'], V['CF'], V['RFc'], V['RF'])]))
    add(calc(r'C_{fx}=\frac{1}{2\pi\times %.0f\ \mathrm{Hz}\times %.0f\ \mathrm{k\Omega}}'
             r'-%.0f\ \mathrm{nF}=%.3f\ \mathrm{nF}\;\rightarrow\;\mathbf{%.2f\ nF}'
             % (V['fpHF'], V['RFB'], V['Copto'], V['Cfxc'], V['Cfx'])))
    add(p('<b>STEP 9 &mdash; 표준 부품이 주는 값:</b>'))
    add(eqagain('fzp'))
    add(calc([r'EA_{o}=\frac{%.2f\times %.0f\ \mathrm{k\Omega}}'
              r'{(%.0f+%.0f)\ \mathrm{nF}\times %.0f\ \mathrm{k\Omega}\times %.1f\ \mathrm{k\Omega}}'
              r'=\mathbf{%.2f\ rad/s}'
              % (V['CTRs'], V['RFB'], V['CF'], V['CFo'], V['RI'], V['RB'],
                 V['EAoi']),
              r'f_{z}=\frac{1}{2\pi\times %.0f\ \mathrm{k\Omega}\times %.0f\ \mathrm{nF}}'
              r'=\mathbf{%.3f\ Hz}' % (V['RF'], V['CF'], V['fzi'])]))
    add(calc([r'C_{ser}=\frac{%.0f\times %.0f}{%.0f+%.0f}\ \mathrm{nF}=%.1f\ \mathrm{nF},'
              r'\qquad f_{p}=\frac{1}{2\pi\times %.0f\ \mathrm{k\Omega}\times %.1f\ \mathrm{nF}}'
              r'=\mathbf{%.2f\ Hz}'
              % (V['CF'], V['CFo'], V['CF'], V['CFo'], V['Cser'], V['RF'],
                 V['Cser'], V['fpi']),
              r'f_{px}=\frac{1}{2\pi\times %.0f\ \mathrm{k\Omega}\times(%.0f+%.2f)\ \mathrm{nF}}'
              r'=\mathbf{%.0f\ Hz}' % (V['RFB'], V['Copto'], V['Cfx'], V['fpx'])]))
    add(p('<b>STEP 10 &mdash; crossover 주파수와 phase margin.</b> '
          'G<sub>o</sub>EA<sub>o</sub> = %(g0).0f 이므로 반복은 '
          '&omega;<sub>c</sub> = %(w0).1f&nbsp;rad/s 에서 시작해 다음에 '
          '수렴한다.' % dict(V, f0=V['w0'] / (2 * pi))))
    add(eqagain('wc'))
    add(calc(r'\omega_{c}=\mathbf{%.1f\ rad/s},\qquad f_{c}=\frac{%.1f}{2\pi}'
             r'=\mathbf{%.2f\ Hz},\qquad |T(\omega_{c})|=%.4f\ \ (\mathrm{check:}\ 1)'
             % (V['wc'], V['wc'], V['fcross'], V['Tres'])))
    add(eqagain('PMeq'))
    add(calc(r'\Phi_{M}=\arctan\frac{%.1f}{%.1f}-\arctan\frac{%.1f}{%.1f}'
             r'-\arctan\frac{%.1f}{%.0f}=%.1f^{\circ}-%.1f^{\circ}-%.1f^{\circ}'
             r'=\mathbf{%.1f^{\circ}}'
             % (V['wc'], V['wz'], V['wc'], V['wp'], V['wc'], V['wpx'],
                _at(V['wc'], V['wz']), _at(V['wc'], V['wp']),
                _at(V['wc'], V['wpx']), V['PM'])))
    add(p('<b>STEP 11 &mdash; gain margin:</b>'))
    add(eqagain('f180'))
    add(calc([r'f_{180}=\sqrt{%.2f\times %.0f-%.3f\times(%.2f+%.0f)}\ \mathrm{Hz}'
              r'=\mathbf{%.0f\ Hz}'
              % (V['fpi'], V['fpx'], V['fzi'], V['fpi'], V['fpx'], V['f180']),
              r'|T(f_{180})|=%.4f,\qquad GM=-20\log_{10}%.4f=\mathbf{%.1f\ dB}'
              % (V['T180'], V['T180'], V['GM'])]))
    add(p('<b>STEP 12 &mdash; 설계한 루프의 3차 고조파</b>, 2f<sub>l</sub> = '
          '%(f2).0f&nbsp;Hz (&omega; = %(w2fl).1f&nbsp;rad/s) 에서:'
          % dict(V, f2=2 * V['flmin'])))
    add(calc(r'G_{EA}(2f_{l})=\frac{%.2f}{%.1f}\cdot'
             r'\frac{\sqrt{1+(%.1f/%.1f)^{2}}}'
             r'{\sqrt{1+(%.1f/%.1f)^{2}}\,\sqrt{1+(%.1f/%.0f)^{2}}}'
             r'=\mathbf{%.4f}\ \ (\leq %.4f)'
             % (V['EAoi'], V['w2fl'], V['w2fl'], V['wz'], V['w2fl'], V['wp'],
                V['w2fl'], V['wpx'], V['GEAact'], V['GEAreq'])))
    add(eqagain('D3'))
    add(calc(r'D_{3}=\frac{%.4f\times %.3f\ \mathrm{V}}{4\times %.3f\ \mathrm{V}}'
             r'=\mathbf{%.2f\ \%%}\ \ (\mathrm{budget}\ %.0f\ \%%)'
             % (V['GEAact'], V['dVloop'], V['VFBv'], V['D3'], V['D3set'])))
    add(p('<b>STEP 13 &mdash; 버스트 점의 피드백 리플</b>, 버스트 진입 '
          '%(PinBM).0f&nbsp;W 에서:' % V))
    add(eqagain('dVFB'))
    add(calc(r'\Delta V_{FB}=\frac{%.0f\ \mathrm{W}}{%.1f\ \mathrm{V}}\cdot'
             r'\frac{1}{2\pi\times %.0f\ \mathrm{Hz}\times %.1f\ \mathrm{mF}}'
             r'\times %.4f=\mathbf{%.1f\ mV}'
             % (V['PinBM'], V['Vout'], V['flmin'], V['Cout'], V['GEAact'],
                V['dVFBBM'])))
    add(eqagain('dRBM'))
    add(calc(r'\Delta R_{BM}=\frac{%.1f\ \mathrm{mV}}{2\times 0.01\ \mathrm{V/k\Omega}}'
             r'=\mathbf{%.2f\ k\Omega},\qquad R_{BM}=%.0f-%.2f'
             r'=\mathbf{%.1f\ k\Omega}'
             % (V['dVFBBM'], V['dRBM'], V['RBMsel'], V['dRBM'], V['RBMrec'])))
    add(p('지금은 선정값 %(RBMsel).0f&nbsp;k&Omega; 을 그대로 둔다. 기준이 된 '
          '버스트 진입점이 가정값이기 때문이다(표&nbsp;%(t)s). 대기 전력을 '
          '실측한 뒤 이 리플과 맞바꿔 R<sub>BM</sub> 을 정한다(부록&nbsp;%(a)s).'
          % dict(V, t=TR('spec-given'), a=SR('이 설계의 미결 항목'))))
    add(fig('an_loop_bode',
            '설계한 루프의 |T| 와 180&deg; + arg&nbsp;T. 둘째 곡선은 crossover 주파수에서만 phase margin 이고, gain margin 은 f<sub>180</sub> 에서 '
            '읽는다.'))
    ext(tbl('전압 루프 설계 결과.',
            [['항목', '값', '기준'],
             ['분압기 R<sub>I</sub> / R<sub>O</sub>',
              '%(RI).0f / %(Ro).0f k&Omega;' % V,
              '%(VoutAct).2f V 로 조절' % V],
             ['바이어스 R<sub>P</sub>, R<sub>B</sub>',
              '%(RP).1f k&Omega;, %(RB).1f k&Omega;' % V,
              'R<sub>P</sub> &le; %(RPmax).2f k&Omega;; R<sub>B</sub> 는 '
              '%(RBmin).2f ~ %(RBmax).2f k&Omega; 안' % V],
             ['보상 C<sub>Fo</sub>, C<sub>F</sub>, R<sub>F</sub>, '
              'C<sub>fx</sub>',
              '%(CFo).0f nF, %(CF).0f nF, %(RF).0f k&Omega;, %(Cfx).2f nF' % V,
              'zero %(fzi).2f Hz, pole %(fpi).1f Hz, pole %(fpx).0f Hz' % V],
             ['crossover 주파수 f<sub>c</sub>', '%(fcross).2f Hz' % V,
              '이 토폴로지의 일반 범위 15 ~ 20 Hz'],
             ['phase margin', '%(PM).1f&deg;' % V,
              '목표 %(PhiM).0f&deg;, 하한 45&deg;' % V],
             ['gain margin', '%(f180).0f Hz 에서 %(GM).1f dB' % V,
              '하한 6 dB, %(GMt).0f dB 면 여유' % V],
             ['입력 전류의 3차 고조파', '%(D3).2f %%' % V,
              '허용치 %(D3set).0f %%' % V],
             ['버스트 점의 피드백 리플',
              '%(dVFBBM).0f mV' % V,
              'R<sub>BM</sub> 을 선정값 %(RBMsel).0f k&Omega; 에서 %(RBMrec).1f k&Omega; 으로 '
              '낮추면 리플이 버스트 threshold 를 넘나들지 않는다' % V]],
            widths=[CW * 0.34, CW * 0.28, CW * 0.38], key='loop-result', split=True))

    # ------------------------------------------------ 컨트롤러 주변 회로
    add(h2('컨트롤러 주변 부품'))
    add(p('결과는 아래 표와 같다. 이어지는 절에서 값을 정하는 순서대로 하나씩 구한다.'))
    ext(tbl('설계 예제의 컨트롤러 주변 회로.',
            [['부품', '값', '결과'],
             ['C<sub>T</sub> / R<sub>T</sub>',
              '%(CT).0f pF / %(RT)g k&Omega;' % V,
              'f<sub>Min</sub> %(fMin).1f kHz, f<sub>Max</sub> %(fMax).1f kHz'
              % V],
             ['R<sub>CS</sub>', '%(RCS).1f m&Omega; (%(RCS1).0f m&Omega; '
              '&times; %(nR).0f 병렬)' % dict(V, nR=A.SH['N.RCS']),
              '합성 피크의 %(kOCP).3f 배에서 OCP1' % V],
             ['R<sub>CFG</sub>', '%(RCFG).0f k&Omega;' % V,
              'V<sub>BO</sub> 피크 %(pk).0f V(%(VBO).1f Vac rms), 모핑 사용' % dict(V, pk=V['VBO'] * 2 ** 0.5)],
             ['R<sub>BM</sub>', '%(RBM).0f k&Omega;' % V,
              '버스트 모드 진입점'],
             ['ZCD 분압기', '%(RZH).0f k&Omega; / %(RZL).0f k&Omega;' % V,
              'OVP1 %(OVP1).2f V, OVP2 %(OVP2).2f V' % V],
             ['C<sub>in</sub>', '%(Cin).0f nF 필름' % V,
              '약 %.1f nF/W &mdash; 벌크 커패시터가 없다'
              % (V['Cin'] / V['Pin'])],
             ['V<sub>CC</sub> 레귤레이터',
              '제너 %.0f V, R<sub>BZ</sub> %.0f &Omega;, C<sub>VCC</sub> '
              '%.0f &micro;F' % (V['DZ'], V['RBZ'], V['CVCC']),
              'N<sub>aux</sub> %d T 에서 V<sub>CC</sub> %.2f V(%.2f ~ %.2f V)'
              % (V['Naux'], A.SH['V.CC_reg'], A.SH['V.CC_reg_min'],
                 A.SH['V.CC_reg_max'])],
             ['보상',
              '%(CFo).0f nF / %(CF).0f nF / %(RF).0f k&Omega; / %(Cfx).2f nF'
              % V,
              'f<sub>c</sub> %(fcross).2f Hz, &Phi;<sub>M</sub> '
              '%(PM).1f&deg;' % V]],
            widths=[CW * 0.20, CW * 0.34, CW * 0.46], split=True))
    add(h2('오실레이터: C<sub>T</sub> 먼저, 그다음 R<sub>T</sub>'))
    add(p('VCO 는 V<sub>ref</sub>/R<sub>T</sub> 에 error amp 전류 '
          'I<sub>EA</sub> 를 더한 전류로 C<sub>T</sub> 를 V<sub>ref</sub>&nbsp;='
          '&nbsp;1.5&nbsp;V 까지 충전하고, 고정된 idle 시간을 더한다.'))
    add(eq(r'\frac{T_{sw}}{2}=\frac{C_{T}V_{ref}}'
           r'{\frac{V_{ref}}{R_{T}}+I_{EA}}+T_{idle}', key='Tsw'))
    add(p('<b>I<sub>EA</sub> 가 유일한 제어 입력이다.</b> 전류가 크면 주파수가 '
          '높고 전력이 작다. C<sub>T</sub> 가 주파수 범위의 <i>폭</i>을, '
          'R<sub>T</sub> 가 <i>하한</i>을 정하므로 그 순서로 고른다.'))
    add(eq(r'C_{T,max}=\frac{I_{EA,max}}{2V_{ref}}\cdot'
           r'\frac{(1-2T_{idle}f_{sw,des})(1-2T_{idle}f_{sw,min})}'
           r'{f_{sw,des}-f_{sw,min}}\,,\qquad '
           r'C_{T,min}=\frac{1}{R_{T,max}}'
           r'\left(\frac{1}{2f_{sw,min}}-T_{idle}\right)', key='CT'))
    add(eq(r'R_{T,ceil}=\frac{1}{C_{T}}'
           r'\left(\frac{1}{2f_{sw,min}}-T_{idle}\right)', key='RTceil'))
    add(p('f<sub>sw,des</sub> 는 오실레이터 범위를 설계하는 주파수다. 컨버터가 '
          '실제로 도는 최고 주파수 %(fmx).1f&nbsp;kHz(라인 피크의 풀브리지 경계)의 '
          '1.5 배이되, 사양 %(fswspec).0f&nbsp;kHz 를 넘지 않는다. 넣는 값은 '
          'f<sub>sw,min</sub> = f<sub>o</sub>&nbsp;=&nbsp;%(fo).1f&nbsp;kHz, '
          'f<sub>sw,des</sub>&nbsp;=&nbsp;%(fop).1f&nbsp;kHz, '
          'I<sub>EA,max</sub>&nbsp;=&nbsp;400&nbsp;&micro;A, V<sub>ref</sub>'
          '&nbsp;=&nbsp;1.5&nbsp;V, T<sub>idle</sub>&nbsp;=&nbsp;%(Tidle).0f'
          '&nbsp;ns 다:' % dict(V, fop=A.SH['f.sw_max_des'], fmx=V['fswmaxop'])))
    add(calc(r'C_{T,max}=\frac{400\times10^{-6}}{2\cdot1.5}\cdot'
             r'\frac{(1-2\cdot%(t).0f\!\times\!10^{-9}\cdot'
             r'%(fmx).1f\!\times\!10^{3})'
             r'(1-2\cdot%(t).0f\!\times\!10^{-9}\cdot'
             r'%(fmn).1f\!\times\!10^{3})}'
             r'{(%(fmx).1f-%(fmn).1f)\times10^{3}}'
             r'=%(CTmax).0f\;\mathrm{pF}'
             % dict(t=V['Tidle'], fmx=A.SH['f.sw_max_des'], fmn=V['fo'],
                    CTmax=A.SH['C.T_max'])))
    add(p('하한 조건, 곧 R<sub>T</sub> 최대 30&nbsp;k&Omega; 에서 '
          'f<sub>Min</sub> 을 f<sub>o</sub> 까지 내리는 조건은 C<sub>T,min</sub>'
          '&nbsp;=&nbsp;%(CTmin).0f&nbsp;pF 을 준다. 데이터시트 허용 범위는 '
          '270 ~ 1000&nbsp;pF 이므로 선택 범위는 %(lo).0f ~ %(CTmax).0f&nbsp;pF 이고, 그 중간 값을 고른다: <b>C<sub>T</sub> = %(CT).0f&nbsp;pF</b>, C0G. '
          '그다음'
          % dict(V, CTmin=A.SH['C.T_min'], CTmax=A.SH['C.T_max'],
                 lo=max(270.0, A.SH['C.T_min']))))
    add(calc(r'R_{T,ceil}=\frac{1}{%(CT).0f\times10^{-12}}'
             r'\left(\frac{1}{2\cdot%(fo).1f\times10^{3}}'
             r'-%(t).0f\times10^{-9}\right)'
             r'=%(RTceil).2f\;\mathrm{k\Omega}\;\rightarrow\;'
             r'%(RT)g\;\mathrm{k\Omega}'
             % dict(V, t=V['Tidle'], RTceil=A.SH['R.T_ceil'] / 1e3)))
    add(note('<b>R<sub>T,ceil</sub> 은 최대값이다.</b> R<sub>T</sub> 가 '
             '커질수록 f<sub>Min</sub> 이 <i>내려가므로</i> 올려 잡으면 클램프가 '
             'f<sub>o</sub> 아래로 떨어진다. <b>내려서</b> 잡을 것.'))
    add(p('선정한 두 부품으로 얻는 값은'))
    add(eq(r'f_{Min}=\frac{1}{2(C_{T}R_{T}+T_{idle})}\,,\qquad '
           r'f_{Max}=\frac{1}{2\left(\frac{C_{T}}'
           r'{\frac{I_{EA,max}}{V_{ref}}+\frac{1}{R_{T}}}+T_{idle}\right)}', key='fMinMax'))
    add(p('f<sub>Min</sub>&nbsp;=&nbsp;1/[2(%(CT).0f&nbsp;pF&times;%(RT)g'
          '&nbsp;k&Omega; + %(Ts).2f&nbsp;&micro;s)] = '
          '<b>%(fMin).2f&nbsp;kHz</b>, 이것이 f<sub>o</sub> 를 넘어야 한다.'
          % dict(V, Ts=V['Tidle'] / 1e3)))
    ext(tbl('오실레이터: 두 부품으로 얻는 값과 각 한계.',
            [['항목', '값', '한계', '여유'],
             ['f<sub>Min</sub>', '%(fMin).1f kHz' % V,
              'f<sub>o</sub> = %(fo).1f kHz 위' % V,
              '%(kfloor).3f' % V],
             ['f<sub>Max</sub>', '%(fMax).1f kHz' % V,
              '최고 동작 f<sub>sw</sub> = %(fswmaxop).1f kHz(FB 경계, 라인 피크) 위' % V,
              '%(kceil).3f' % V],
             ['f<sub>SU</sub>', '%(fSU).1f kHz' % dict(V, fSU=A.SH['f.SU']),
              '실리콘 상한 675 kHz 아래', '%(kSU).3f'
              % dict(V, kSU=A.SH['k.SU'])],
             ['R<sub>T</sub>C<sub>T</sub>',
              '%(tau).2f &micro;s' % dict(V, tau=A.SH['τ.RT']),
              '2.5 ~ 12 &micro;s', '%(a).3f / %(b).3f'
              % dict(a=A.SH['k.tau_lo'], b=A.SH['k.tau_hi'])],
             ['R<sub>T</sub>', '%(RT)g k&Omega;' % V, '5 ~ 30 k&Omega;',
              '%(a).3f / %(b).3f'
              % dict(a=A.SH['k.RT_lo'], b=A.SH['k.RT_hi'])],
             ['C<sub>T</sub>', '%(CT).0f pF' % V, '270 ~ 1000 pF',
              '%(a).3f / %(b).3f'
              % dict(a=A.SH['k.CT_lo'], b=A.SH['k.CT_hi'])]],
            widths=[CW * 0.18, CW * 0.20, CW * 0.44, CW * 0.18], split=True))
    add(note('<b>T<sub>idle</sub> 은 이 장에서 가장 불확실한 값이다.</b> 초안 '
             '데이터시트의 주파수 식은 700&nbsp;ns, C<sub>T,max</sub> 식은 '
             '350&nbsp;ns 를 뜻하고, Table&nbsp;2 를 역산하면 약 250&nbsp;ns 가 '
             '나온다. 이 설계는 %(Tidle).0f&nbsp;ns 를 쓴다. '
             '700&nbsp;ns 이면 f<sub>Min</sub> 은 %(a).1f&nbsp;kHz 로 '
             'f<sub>o</sub> = %(fo).1f&nbsp;kHz %(side)s, f<sub>Max</sub> 는 '
             '%(b).1f&nbsp;kHz 로 FB 경계에 필요한 %(c).1f&nbsp;kHz %(top)s. '
             '가장 먼저 잴 것.'
             % dict(V, a=_f_idle(V, 700.0)[0], b=_f_idle(V, 700.0)[1],
                    c=V['fswmaxop'],
                    side='아래가 되고' if _f_idle(V, 700.0)[0] < V['fo'] else
                    '보다 겨우 높고',
                    top='에 못 미친다' if _f_idle(V, 700.0)[1] < V['fswmaxop']
                    else '를 넘는다')))
    add(h2('전류 sense 저항: 저항 하나가 세 가지를 정한다'))
    add(p('조건이 둘이고 작은 쪽으로 정한다.'))
    add(eq(r'R_{CS,max1}=\frac{16.8\,\Omega\!\cdot\!\mathrm{W}}{P_{in}}'
           r'\qquad\qquad '
           r'R_{CS,max2}=\frac{0.55\,\mathrm{V}}{I_{Lr,pk}}', key='RCS'))
    add(p('첫째는 최대 전력 법칙(%s 절), 둘째는 OCP1 트립점이다. 첫째는 데이터시트처럼 '
          'P<sub>in</sub> 으로 쓰고, 핀이 실제로 검출하는 P<sub>in,LLC</sub> 로 쓰지 않는다. 그만큼 '
          '%.0f&nbsp;%% 보수적이다.'
          % (SR('피드백 핀은 전력 지령이다'), 100 * (V['Pin'] / _SH['P.in_LLC'] - 1))))
    add(calc(r'R_{CS,max1}=\frac{16.8}{%(Pin).1f}=%(a1).5f\;\Omega'
             r'=%(a).2f\;\mathrm{m\Omega}\,,\qquad '
             r'R_{CS,max2}=\frac{0.55}{%(Ipk).2f}=%(b1).5f\;\Omega'
             r'=%(b).2f\;\mathrm{m\Omega}'
             % dict(Pin=V['Pin'], a1=A.SH['R.CS1'] / 1e3, a=A.SH['R.CS1'],
                    Ipk=V['Icomp'], b1=A.SH['R.CS2'] / 1e3,
                    b=A.SH['R.CS2'])))
    add(p('따라서 전력 법칙이 제한한다. 최악 스위칭 사이클의 손실을 저항 몇 '
          '개로 나눌지를 정한다.'))
    add(calc(r'P_{CS}=I_{pri,rms}^{2}R_{CS}=(%(I).2f)^{2}\cdot%(R).1f'
             r'\times10^{-3}=%(P).2f\;\mathrm{W}'
             r'\;\Rightarrow\;N=%(N).0f\;\mathrm{in\;parallel}'
             % dict(I=V['Iprims'], R=V['RCS'], P=A.SH['P.RCS_pk'],
                    N=A.SH['N.RCS'])))
    add(p('%(R1).0f&nbsp;m&Omega; %(N).0f 개 병렬로 <b>R<sub>CS</sub> = '
          '%(RCS).1f&nbsp;m&Omega;</b>.'
          % dict(V, N=A.SH['N.RCS'], R1=A.SH['R.CS_single'])))
    add(note('R<sub>CS</sub> 는 브리지 리턴 경로에 있으므로 R<sub>CS,max2</sub> '
             '는 합성 피크를 쓴다. I<sub>Lr,pk</sub> = %(Icomp).2f&nbsp;A 대신 '
             'I<sub>trafo,pk</sub> = %(Itr).2f&nbsp;A 를 쓰면 과전류 보호가 약 '
             '%(pc).0f&nbsp;%% 느슨해진다.' % dict(V, pc=100 * (V['Icomp'] / V['Itr'] - 1))))
    ext(tbl('선정한 R<sub>CS</sub> 가 정하는 것.',
            [['결과', '값', '기준'],
             ['최대 입력 전력', '%(P).1f W'
              % dict(P=A.SH['P.in_max_act']),
              'P<sub>in</sub> = %(Pin).1f W' % V],
             ['OCP1 트립', '%(I).2f A' % dict(I=A.SH['I.OCP1']),
              '합성 피크 %(Icomp).2f A, 여유 %(kOCP).3f' % V],
             ['OCP2 트립', '%(I).2f A' % dict(I=A.SH['I.OCP2']),
              '즉시 스위칭 정지, 50 &micro;s 뒤 f<sub>SU</sub> 에서 재기동'],
             ['sense 저항 손실, 최악 스위칭 사이클', '합계 %(P).2f W, 개당 %(Pe).3f W'
              % dict(P=A.SH['P.RCS_pk'], Pe=A.SH['P.RCS_each_pk']),
              '1 W 부품, 여유 %(k).3f' % dict(k=A.SH['k.NRCS'])]],
            widths=[CW * 0.26, CW * 0.26, CW * 0.48], split=True))
    add(h2('버스트 모드: 전원 인가 시 한 번 읽는 저항'))
    add(eq(r'R_{BM}=16.7\,\frac{\mathrm{k}\Omega}{\mathrm{V}^{2}}'
           r'\,R_{CS}\,P_{in,BM}\,,\qquad '
           r'V_{BM,eq}=0.01\,\frac{\mathrm{V}}{\mathrm{k}\Omega}\,R_{BM}+0.5\,\mathrm{V}', key='RBM'))
    add(p('버스트는 P<sub>in,BM</sub> = %(rBM).0f&nbsp;%% &times; '
          '%(Pin).1f&nbsp;W = %(PinBM).1f&nbsp;W 에서 시작한다.'
          % dict(V, rBM=100 * A.SH['r.BM'],
                 PinBM=A.SH['r.BM'] * V['Pin'])))
    add(calc(r'R_{BM}=16.7\cdot%(R).1f\times10^{-3}\cdot%(P).1f'
             r'=%(RB).1f\;\mathrm{k\Omega}\;\rightarrow\;'
             r'%(sel).0f\;\mathrm{k\Omega}\,,\qquad '
             r'V_{BM,eq}=0.01\times %(sel).0f+0.5=%(V).3f\;\mathrm{V}'
             % dict(R=V['RCS'], P=A.SH['r.BM'] * V['Pin'], RB=A.SH['R.BM'],
                    sel=A.SH['R.BM_sel'], V=A.SH['V.BM_eq'])))
    add(p('유효 범위는 15 ~ 140&nbsp;k&Omega; 이고, 접지에 연결하면 버스트 모드가 '
          '꺼진다. 이 threshold 를 피드백 리플에 대해 검사할 것(%s 절). 그렇지 않으면 컨버터가 버스트를 넘나들며 채터링한다.'
          % SR('버스트 threshold 에 대한 피드백 리플')))
    add(h2('브라운아웃과 브리지 구성: CFG 핀'))
    add(p('저항 하나가 두 가지 기능을 정하고, 둘 다 전원 인가 시 읽는다.'))
    add(eq(r'V_{BO,pk}=R_{CFG}\times 4\,\frac{\mathrm{V}}{\mathrm{k}\Omega}'
           r'\,,\qquad V_{BO,rms}=\frac{V_{BO,pk}}{\sqrt{2}}', key='VBO'))
    add(p('브라운아웃은 상용전원의 <i>피크</i>와 비교하므로 &radic;2 를 빠뜨리기 '
          '쉽다. 브라운아웃을 최저 입력 전압 바로 아래에:'))
    add(calc(r'R_{CFG,max}=\frac{\sqrt{2}\cdot%(Vac).0f}{4}'
             r'=%(max).2f\;\mathrm{k\Omega}\;\rightarrow\;'
             r'%(sel).0f\;\mathrm{k\Omega}'
             % dict(Vac=V['Vacmin'], max=A.SH['R.CFG_max'] / 1e3,
                    sel=V['RCFG'])))
    add(p('최대값이므로 내려서 잡는다. 선정한 부품이 정하는 값은'))
    add(calc(r'V_{BO,rms}=\frac{%(R).0f\cdot4}{\sqrt{2}}'
             r'=%(V).2f\;\mathrm{Vac}'
             % dict(R=V['RCFG'], V=V['VBO'])))
    add(p('최저 %(Vacmin).0f&nbsp;Vac 에 대해 여유 %(k).3f 이다. 올려 잡으면 '
          '컨버터가 최저 입력 전압에서 기동하지 못한다.'
          % dict(V, k=A.SH['k.BO'])))
    ext(tbl('R<sub>CFG</sub> 와 LOUT2 가 함께 고르는 것. 235 V 와 245 V threshold 는 '
            'IC 안에 고정돼 있어 옮길 수 없다.',
            [['R<sub>CFG</sub>', 'LOUT2', '구성'],
             ['15 k&Omega;', 'Open',
              '모핑, 고정 브라운아웃: 피크 60 V 아래에서 정지, 70 V 위에서 동작'],
             ['15 ~ 47 k&Omega;', 'Open',
              '<b>모핑, 조절 브라운아웃 &mdash; 이 설계</b>'],
             ['47 ~ 100 k&Omega;', 'Open', '고정 풀브리지'],
             ['15 k&Omega;', 'GND 로',
              '고정 하프브리지, 분할 C<sub>r</sub>, 고정 브라운아웃'],
             ['15 ~ 100 k&Omega;', 'GND 로',
              '고정 하프브리지, 분할 C<sub>r</sub>, 조절 브라운아웃']],
            widths=[CW * 0.20, CW * 0.14, CW * 0.66], split=True))
    add(note('유니버설 입력이면 선택 범위는 15&nbsp;k&Omega; ~ %(max).1f&nbsp;k&Omega; '
             '이고, 모핑 한계 47&nbsp;k&Omega; 에는 이를 일이 없다. LOUT2 에는 아무 부품도 연결하지 말 것: 약 8&nbsp;k&Omega; 아래의 풀다운은 고정 '
             '하프브리지로 읽힌다.' % dict(max=A.SH['R.CFG_max'] / 1e3)))

    _z = dict(A.SH)
    for _k in ('R.Z_sel', 'R.Z1', 'R.Z2', 'C.Z', 'tol.VR', 'tol.RZ', 'R.thQ6',
               'I.KA_min'):
        if _k not in _z:
            _z[_k] = A._builder_const(_k)
    add(p('<b>LED 레일 V<sub>Z</sub>.</b> STEP 7 은 V<sub>Z</sub> 를 주어진 '
          '값으로 썼다. 이 레일은 둘째 TL431, Q6 를 shunt 레귤레이터로 써서 '
          '만든다. R<sub>Z</sub> 는 출력에서 V<sub>Z</sub> 노드로 가고, 노드는 '
          'C<sub>Z</sub> 가 붙잡는다. 캐소드가 노드에 있고 기준은 R<sub>Z1</sub> '
          '과 R<sub>Z2</sub> 의 분압에서 받으므로 V<sub>Z</sub> = '
          'V<sub>R</sub>(1 + %(r1).1f/%(r2).0f) = %(vz).2f&nbsp;V 다. STEP 7 의 '
          'R<sub>B</sub> 허용 범위가 좁으므로 레일은 값을 지켜야 한다. B 등급'
          '(기준 &plusmn;%(tv).1f&nbsp;%%, Q5 도 같은 등급으로 산다)과 1&nbsp;%% '
          '저항으로 %(lo).2f ~ %(hi).2f&nbsp;V 이고, 허용 범위는 여전히 '
          'R<sub>B</sub> 를 품는다(위로 k = %(kh).3f, 아래로 %(kl).3f). 그 자리에 '
          '&plusmn;5&nbsp;%% 12&nbsp;V 제너를 쓰면 상한이 %(z5).2f R<sub>B</sub> '
          '가 되어 범위 밖이다. R<sub>Z</sub> 는 R<sub>B</sub> 가 끌 수 있는 최대 '
          '%(ib).2f&nbsp;mA(Q5 가 기준에 있을 때)에 Q6 의 %(ik).0f&nbsp;mA 와 '
          '분압기의 %(id).2f&nbsp;mA 를 더한 전류를 hold-up 끝에서 대야 한다. '
          '그래서 최대 %(rm).0f&nbsp;&Omega; 이고 %(rz).0f&nbsp;&Omega; 을 '
          '실장한다(k = %(kr).3f). LED 가 꺼진 OVP1 에서 R<sub>Z</sub> 는 '
          '%(prz).2f&nbsp;W, Q6 는 %(pq).0f&nbsp;mW 를 소모한다. SOT-23 에서 '
          '%(dt).0f&nbsp;&deg;C 상승이다. C<sub>Z</sub> = %(cz).0f&nbsp;&micro;F '
          '는 TL431 이 커패시터 부하에 불안정한 띠(이 캐소드 전압에서 약 0.01 ~ '
          '2&nbsp;&micro;F) 위에 있고, 바이어스로 줄어드는 용량까지 여유가 있다. '
          '옵토커플러 Q4 는 ST 툴과 보드의 SFH617A-2 다. STEP 7 의 CTR 값은 이 '
          '설계의 선택값이고, 쓰는 LED 전류에서 그 곡선과 대조해야 한다.'
          % dict(r1=_z['R.Z1'], r2=_z['R.Z2'], vz=_z['V.Z'],
                 tv=100 * _z['tol.VR'], lo=_z['V.Z_min'], hi=_z['V.Z_max'],
                 kh=_z['k.RBZ_hi'], kl=_z['k.RBZ_lo'], z5=_z['r.RB_zener5'],
                 ib=_z['I.RB_max'], ik=_z['I.KA_min'], id=_z['I.Zdiv'],
                 rm=_z['R.Z_max'], rz=_z['R.Z_sel'], kr=_z['k.RZ'],
                 prz=_z['P.RZ'], pq=_z['P.Q6'], dt=_z['ΔT.Q6'],
                 cz=_z['C.Z'])))

    add(h2('출력 sensing 과 과전압: ZCD 분압기'))
    add(p('분압비만으로 두 과전압 threshold 가 정해진다. 저항의 절대값은 바이어스 전류로 정한다.'))
    add(eq(r'R_{ZCD,L}=\frac{2.3\,\mathrm{V}}{I_{bias}}\,,\qquad '
           r'R_{ZCD,H}=R_{ZCD,L}\left('
           r'\frac{n_{aux}}{n_{sec}}\frac{V_{OVP1,out}}{2.3\,\mathrm{V}}'
           r'-1\right)', key='RZCD'))
    add(eq(r'V_{OVP1}=\frac{2.3\,\mathrm{V}}{n_{aux}/n_{sec}}'
           r'\left(\frac{R_{ZCD,H}}{R_{ZCD,L}}+1\right)\,,\qquad '
           r'V_{OVP2}=\frac{2.5}{2.3}\,V_{OVP1}', key='OVP'))
    add(p('출력보다 %(pc).0f&nbsp;%% 높은 OVP1 은 %(t).2f&nbsp;V 다. 아래 '
          '저항은 바이어스 전류 %(ib).0f&nbsp;&micro;A 에서, 위 저항은 비에서 '
          'n<sub>aux</sub>/n<sub>sec</sub> = %(nx)s:'
          % dict(V, pc=100 * (A.SH['V.OVP1_out'] / V['Vout'] - 1),
                 nx=_nj('%.1f' % A.SH['n.aux'], '으로', '로'),
                 t=A.SH['V.OVP1_out'], naux=A.SH['n.aux'],
                 ib=2.3 / A.SH['R.ZCD_L'] * 1e3)))
    add(calc(r'R_{ZCD,L}=\frac{2.3}{%(ib).0f\times10^{-6}}'
             r'=%(rl).2f\;\mathrm{k\Omega}\;\rightarrow\;'
             r'%(RZL).0f\;\mathrm{k\Omega}'
             % dict(V, ib=2.3 / A.SH['R.ZCD_L'] * 1e3,
                    rl=A.SH['R.ZCD_L'])))
    add(calc(r'R_{ZCD,H}=%(RZL).0f\left(\frac{%(naux).1f\cdot%(t).1f}'
             r'{2.3}-1\right)=%(rh).1f\;\mathrm{k\Omega}'
             r'\;\rightarrow\;%(RZH).0f\;\mathrm{k\Omega}'
             % dict(V, naux=A.SH['n.aux'], t=A.SH['V.OVP1_out'],
                    rh=A.SH['R.ZCD_H'])))
    add(p('위 저항은 계산값 <i>바로 위의 E24 값</i>이라 OVP1 이 리플 피크보다 확실히 위에 온다. 실장한 쌍이 주는 값은'))
    add(calc(r'V_{OVP1}=\frac{2.3}{%(naux).1f}'
             r'\left(\frac{%(RZH).0f}{%(RZL).0f}+1\right)'
             r'=%(OVP1).2f\;\mathrm{V}\,,\qquad '
             r'V_{OVP2}=\frac{2.5}{2.3}\cdot%(OVP1).2f'
             r'=%(OVP2).2f\;\mathrm{V}'
             % dict(V, naux=A.SH['n.aux'])))
    add(p('기동 제어는 ZCD 핀이 데이터시트의 기동 종료 threshold '
          '%(zs).2f&nbsp;V 에 닿을 때 루프로 넘어간다. 같은 분압기를 거치므로 '
          'OVP1 출력 전압의 %(zs).2f/2.3 배, 곧 출력 %(su).2f&nbsp;V 다.'
          % dict(V, su=A.SH['V.out_SUend'], zs=A._builder_const('V.ZCD_SUend'))))
    add(note('두 저항을 바꿔 끼우면 OVP1 이 출력 1 V 아래에서 트립해 컨버터가 '
             '기동하지 못한다. 권선 극성이 뒤집히면 첫 펄스부터 브리지가 하드 '
             '스위칭한다.'))
    add(note('이 권선을 V<sub>CC</sub> 에 바로 이으면 OVP2 에서 핀에 '
             '%(vo).2f&nbsp;V 가 걸려 25&nbsp;V 정격을 넘는다. ST 툴의 권선비 검사도 '
             '%(kj)s 나온다. 여기서 그것이 문제가 되지 않는 것은 다음 절의 '
             '레귤레이터 때문이다.'
             % dict(vo=A.SH['n.aux'] * A.SH['V.OVP2_act'],
                    kj=_nj('%.3f' % A.SH['k.auxr'], '으로', '로'))))
    add(h2('보조 권선 V<sub>CC</sub> 설계 결과'))
    add(p('외부 레일은 없다. 보조 권선은 2차 위에 감은 삼중 절연선 %(Naux)d 턴으로 '
          'n<sub>aux</sub> = %(na).1f 이므로 출력 전압을 따라간다: 권선에 '
          '%(va).1f&nbsp;V, 다이오드 뒤 커패시터에 %(vc).1f&nbsp;V. %(DZ).0f&nbsp;V '
          '&plusmn;%(tp).0f&nbsp;%% 제너와 V<sub>BE</sub> = V<sub>D</sub> = '
          '%(VFj).1f&nbsp;V 가정으로 식&nbsp;%(e)s'
          % dict(V, na=A.SH['n.aux'], va=A.SH['V.aux'], vc=A.SH['V.Caux'],
                 tp=100 * V['tolDZ'], e=_nj(ER('vccreg'), '은', '는'))))
    add(calc(r'V_{CC,reg}=%(DZ).0f-%(VFj).1f-%(VFj).1f=%(r).2f\;\mathrm{V}'
             r'\,,\qquad %(lo).2f\ldots%(hi).2f\;\mathrm{V}'
             % dict(V, r=A.SH['V.CC_reg'], lo=A.SH['V.CC_reg_min'],
                    hi=A.SH['V.CC_reg_max'])))
    add(p('범위의 아래쪽 끝은 V<sub>CC,HVSUon</sub> = %(hv).0f&nbsp;V 를 '
          '%(k1).3f 배로 넘고, 위쪽 끝은 동작 한계 %(mx).0f&nbsp;V 아래에 %(k2).3f '
          '배 여유로 머문다. 부하는 컨트롤러 %(ICC).0f&nbsp;mA, 드라이버 둘 '
          '%(iq).2f&nbsp;mA, 그리고 Q<sub>g,run</sub> = %(qr).1f&nbsp;nC 의 '
          '스위치 자리 %(Nsw).0f 개다(%(s)s 절). f<sub>Max</sub> 에서 상한을 '
          '잡는다(식&nbsp;%(e)s):'
          % dict(V, hv=V['VCCHV'], mx=V['VCCmax'], k1=A.SH['k.VCClo'],
                 k2=A.SH['k.VCC'], e=ER('ivcc'), iq=A.SH['I.drv_q'],
                 qr=A.SH['Q.g_run'],
                 s=SR('1차 스위치: STO60N045DM9'))))
    add(calc(r'I_{VCC}=%(ICC).0f\,\mathrm{mA}+%(iq).2f\,\mathrm{mA}'
             r'+%(Nsw).0f\cdot%(qr).1f'
             r'\,\mathrm{nC}\cdot%(fk).1f\,\mathrm{kHz}'
             r'=%(I).1f\;\mathrm{mA}'
             % dict(V, fk=A.SH['f.Max'], I=A.SH['I.VCC'],
                    iq=A.SH['I.drv_q'], qr=A.SH['Q.g_run'])))
    add(p('공급 저항은 hold-up 끝에서 식&nbsp;%(e)s 정한다. &beta;<sub>min</sub> '
          '= %(bj)s I<sub>Z,min</sub> = %(iz).0f&nbsp;mA 는 부품에 거는 요구 '
          '조건이다:' % dict(e=_nj(ER('rbz'), '으로', '로'),
                         bj=_nj('%.0f' % V['bmin'], '과', '와'),
                         iz=V['IDZmin'])))
    add(calc(r'R_{BZ}\leq\frac{%(na).1f\cdot%(vm).0f-%(VFj).1f-%(zm).2f}'
             r'{%(I).1f/%(b).0f+%(iz).0f}=%(r).3f\;\mathrm{k\Omega}'
             r'\;\rightarrow\;%(RBZ).0f\;\Omega'
             % dict(V, na=A.SH['n.aux'], vm=V['Vomin'], zm=A.SH['V.DZ_max'],
                    I=A.SH['I.VCC'], b=V['bmin'], iz=V['IDZmin'],
                    r=A.SH['R.BZ_max'] / 1e3)))
    add(p('두 부품의 소모는 커패시터 전압이 가장 높게 머무는 OVP1, '
          '%(c1).2f&nbsp;V 에서 정해진다. 제너는 공급 전류를 나눠 줄 부하가 없을 '
          '때 %(pz).0f&nbsp;mW 를 소모한다. 패스 트랜지스터는 I<sub>VCC</sub> 에서 '
          '%(pq).2f&nbsp;W 다(공칭 출력에서는 %(pn).2f&nbsp;W 로, 손실표에 들어가는 '
          '값). 둘 다 여유가 아니라 부품을 살 때의 정격이다. 트랜지스터는 OVP2 '
          '에서 %(c2).2f&nbsp;V 에 권선 스파이크를 더한 전압도 견뎌야 한다. '
          '스파이크는 실측으로만 알 수 있다.'
          % dict(c1=A.SH['V.Caux_OVP1'], pz=A.SH['P.DZ'],
                 pq=A.SH['P.Qpass'], c2=A.SH['V.Caux_OVP2'],
                 pn=A.SH['P.Qpass_nom'])))
    _t = dict(A.SH)
    for _k in ('R.thQ', 'R.thQ_std', 'T.jQ', 'V.CEO_Q', 'R.thDZ', 'T.jDZ'):
        if _k not in _t:
            _t[_k] = A._builder_const(_k)
    add(p('<b>부품.</b> Q<sub>VCC</sub> 는 FZT651 이다. SOT-223 의 NPN 으로 '
          '%(vceo).0f&nbsp;V, 3&nbsp;A 정격이고, 데이터시트 최소 h<sub>FE</sub> '
          '70 이 &beta;<sub>min</sub> = %(b).0f 을 덮는다. %(vceo).0f&nbsp;V 는 '
          'OVP2 커패시터 전압의 %(kv).2f 배다. 정격은 P<sub>Qpass</sub> 에서 '
          '허용하는 주위 온도로 본다: T<sub>a</sub> = T<sub>j,max</sub> &minus; '
          'R<sub>th(j-a)</sub>P. 컬렉터 탭을 2&nbsp;oz 동박 '
          '50&nbsp;&times;&nbsp;50&nbsp;mm, %(rth).1f&nbsp;&deg;C/W 에 올리면 '
          '%(ta).0f&nbsp;&deg;C 다. 25&nbsp;&times;&nbsp;25&nbsp;mm 패드'
          '(%(rts).1f&nbsp;&deg;C/W)에서는 %(tas).0f&nbsp;&deg;C 뿐이다. 그래서 '
          '패드는 큰 쪽이다. D<sub>Z</sub> 는 BZT52H-C15(%(DZ).0f&nbsp;V '
          '&plusmn;%(tp).0f&nbsp;%%, SOD-123F)다. 1&nbsp;cm&sup2; 캐소드 패드, '
          '%(rtd).0f&nbsp;&deg;C/W 에서 P<sub>DZ</sub> 로 %(tad).0f&nbsp;&deg;C '
          '까지 허용한다. D<sub>aux</sub> 와 D<sub>byp</sub> 는 1N4148W 다. '
          'D<sub>aux</sub> 는 I<sub>VCC</sub> 와 제너 공급 전류를 펄스로 '
          '흘리므로 손실은 V<sub>F</sub> 에 평균을 곱한 것보다 크고, 실측할 '
          '값이다. 두 OVP 값은 이중 최악이다: OVP1 의 레귤레이터에 f<sub>Max</sub> '
          '의 게이트 전류. 공칭 출력과 스위칭 주파수에서 트랜지스터는 '
          '%(pn).2f&nbsp;W 를 소모한다.'
          % dict(vceo=_t['V.CEO_Q'], b=V['bmin'], kv=_t['k.VCEOQ'],
                 rth=_t['R.thQ'], ta=_t['T.aQVCC'], rts=_t['R.thQ_std'],
                 tas=_t['T.aQVCC_std'], DZ=V['DZ'], tp=100 * V['tolDZ'],
                 rtd=_t['R.thDZ'], tad=_t['T.aDZ'], pn=A.SH['P.Qpass_nom'])))
    add(p('<b>기동.</b> 풀브리지에서 오실레이터는 처음 %(to).0f&nbsp;ms 동안만 '
          'f<sub>SU</sub> = %(fs).1f&nbsp;kHz 로 돌고, 그 뒤에는 f<sub>Max</sub> '
          '아래에 머문다. V<sub>CCon</sub> 에서의 게이트 전하로 드라이버가 끄는 '
          '전류, 그리고 C<sub>VCC</sub> 가 내려갈 때 V 당 잃는 B 는'
          % dict(fs=A.SH['f.SU'], to=V['TOSC'])))
    add(calc(r'I_{VCC,SU}=%(ICC).0f+%(iq).2f+%(Nsw).0f\cdot%(qs).1f'
             r'\,\mathrm{nC}\cdot%(fk).1f\,\mathrm{kHz}'
             r'=%(I).1f\;\mathrm{mA}'
             % dict(V, fk=A.SH['f.Max'], I=A.SH['I.VCC_SU'],
                    iq=A.SH['I.drv_q'], qs=A.SH['Q.g_SU'])))
    add(calc(r'B=%(Nsw).0f\cdot%(cg).1f\,\mathrm{nF}\cdot%(fk).1f'
             r'\,\mathrm{kHz}=%(b).2f\;\mathrm{mA/V}'
             % dict(V, fk=A.SH['f.Max'], cg=A.SH['C.g_hi'], b=A.SH['B.SU'])))
    add(p('이다. 그러므로 V<sub>CC,HVSUon</sub> 에서 %(ih).1f&nbsp;mA, 하한 '
          'V<sub>CC,floor</sub> = %(fl).2f&nbsp;V 에서 %(if).1f&nbsp;mA 다. 이 '
          '하한은 하이사이드 드라이버 전원이 정한다(%(s)s 절). f<sub>SU</sub> 의 '
          '첫 1&nbsp;ms 는 &Delta;Q<sub>OSC</sub> = %(to).0f&nbsp;ms &middot; '
          '%(Nsw).0f &middot; %(qs).1f&nbsp;nC &middot; (%(fs).1f &minus; '
          '%(fk).1f)&nbsp;kHz = %(dq).1f&nbsp;&micro;C 를 더 쓴다. 출력이 '
          '(V<sub>CC,floor</sub> + 3V<sub>D</sub> + '
          'I<sub>VCC,SU</sub>R<sub>BZ</sub>/&beta;<sub>min</sub>)/'
          'n<sub>aux</sub> = %(uv).2f&nbsp;V 에 닿으면 권선이 핀을 하한에 붙잡아 '
          '둔다. 그러면 식&nbsp;%(e)s'
          % dict(V, ih=A.SH['I.VCC_hv'], fl=A.SH['V.CC_floor'],
                 to=V['TOSC'], qs=A.SH['Q.g_SU'], fs=A.SH['f.SU'],
                 fk=A.SH['f.Max'], dq=A.SH['ΔQ.OSC'],
                 uv=A.SH['V.out_UV'], e=_nj(ER('cvcc'), '은', '는'),
                 s=SR('게이트 드라이버: L6498LD 2개'),
                 **{'if': A.SH['I.VCC_fl']})))
    add(calc(r't_{hand}=\frac{%(co).1f\cdot%(uv).2f}{%(Iout).1f}'
             r'=%(th).1f\;\mathrm{ms}'
             % dict(V, co=A.SH['C.out'], uv=A.SH['V.out_UV'],
                    th=A.SH['t.hand'])))
    add(calc(r'C_{VCC}\geq\frac{%(b).2f\cdot(%(th).1f+%(dq).1f/%(I).1f)}'
             r'{\ln\dfrac{%(I).1f}{%(ih).1f}'
             r'+\ln\dfrac{%(ih).1f-%(IHVlo).0f}{%(if).1f-%(IHVlo).0f}}'
             r'=%(cr).0f\;\mathrm{\mu F}\;\rightarrow\;%(CVCC).0f\;'
             r'\mathrm{\mu F}'
             % dict(V, th=A.SH['t.hand'], I=A.SH['I.VCC_SU'],
                    b=A.SH['B.SU'], dq=A.SH['ΔQ.OSC'], ih=A.SH['I.VCC_hv'],
                    cr=A.SH['C.VCC_req'], **{'if': A.SH['I.VCC_fl']})))
    add(note('단위: mA/V 에 ms 를 곱하고 순수한 수로 나누면 &micro;F 다. '
             '&micro;C 를 mA 로 나누면 ms 다.'))
    add(p('인계는 기동 회로가 살아 있는 %(t).0f&nbsp;ms 안에 넉넉히 끝난다. '
          '대가는 첫 펄스까지의 지연으로 230&nbsp;Vac 에서 %(d).2f&nbsp;s 이고, '
          '그동안 충전 전부를 기동 회로가 맡는다. 시제품에서 그 온도를 확인한다.'
          % dict(t=V['tHVSU'], d=A.SH['t.VCCchg'])))
    add(note('t<sub>hand</sub> 는 TV 가 패널을 순서대로 켜듯, 레일이 올라올 때까지 '
             '세트가 부하를 걸지 않는다고 가정한다. 기동 중에 부하가 걸리면 '
             't<sub>hand</sub> 가 길어지고 C<sub>VCC</sub> 도 그만큼 커져야 한다.'))
    add(p('기동 경로의 배선 규칙 두 가지:'))
    ext(bullets([
        '<b>HVSU 는 브리지 앞</b>, AC 쪽에 라인마다 1000&nbsp;V 다이오드 하나로 '
        '연결한다. 브리지 뒤에 달면 X 커패시터 방전과 브라운아웃 검출이 둘 다 '
        '동작하지 않는다.',
        '<b>V<sub>CC</sub> 핀에 100&nbsp;nF</b>, C<sub>VCC</sub> 옆에.']))

    # =============================================================== 7
    add(h2('컨트롤러 핀 규칙'))
    ext(tbl('어기면 안 되는 핀 규칙.',
            [['핀', '규칙'],
             ['ISEN', '필터도 직렬 저항도 없이. 최대 전력 법칙과 과전류 threshold 가 '
              '이 핀을 같이 읽는다.'],
             ['CFG, BM', '커패시터 없이. 둘 다 전원 인가 시 읽힌다. 범위 밖의 '
              'CFG 저항은 컨트롤러를 래치 오프시킨다.'],
             ['DRV_EN, RT', '커패시터 없이. 둘 다 몇 ms 마다 잠깐 샘플되고, '
              '커패시터가 있으면 고장으로 읽힌다.'],
             ['LOUT2', '모핑을 쓰면 풀다운 없이. 접지로 몇 k&Omega; 이면 고정 '
              '하프브리지로 읽힌다.'],
             ['HVSU', '입력 브리지 앞 AC 쪽에 연결. 브리지 뒤에 달면 X 커패시터 '
              '방전과 브라운아웃 검출이 둘 다 멈춘다.'],
             ['ZCD', '보조 권선 극성은 레그 1 의 로우사이드가 켜졌을 때 ZCD 가 '
              '양이 되게. 뒤집히면 브리지가 하드 스위칭한다.'],
             ['HOUTx, LOUTx', '게이트 드라이버가 아니라 로직 레벨 출력이다. '
              '외부 하프브리지 드라이버가 필요하다.']],
            widths=[CW * 0.16, CW * 0.84], split=True))
    add(h2('보호 기능과 각 threshold 를 정하는 부품'))
    add(p('각 threshold 는 이미 고른 저항으로 정해지므로, 한 목적으로 바꾼 저항이 다른 threshold 를 움직일 수 있다.'))
    ext(tbl('보호와 각각을 정하는 부품.',
            [['보호', '정하는 것', '이 설계'],
             ['브라운아웃, 정류 전압에서',
              'R<sub>CFG</sub>, 전원 인가 시 읽음',
              'V<sub>BO</sub> 피크 %(pk).0f V = %(VBO).1f Vac rms, 최저 %(Vacmin).0f Vac 에 대해 '
              '여유 %(kBO).3f' % dict(V, kBO=A.SH['k.BO'], pk=V['VBO'] * 2 ** 0.5)],
             ['1단계 과전류, OCP1: 스위칭 주파수를 올린다',
              'R<sub>CS</sub> &mdash; 최대 전력 법칙과 같은 저항',
              '합성 피크 %(Icomp).2f A 에 대해 %(IOCP1).2f A, 여유 %(kOCP).3f'
              % dict(V, IOCP1=A.SH['I.OCP1'])],
             ['2단계 과전류, OCP2',
              'R<sub>CS</sub>, OCP1 과 고정 비율',
              '%(IOCP2).2f A' % dict(V, IOCP2=A.SH['I.OCP2'])],
             ['출력 과전압, OVP1',
              '보조 권선의 ZCD 분압기',
              '%(OVP1).2f V, 리플 피크 위, OVP2 아래' % V],
             ['2단계 과전압, OVP2',
              '같은 분압기',
              '%(OVP2).2f V' % V],
             ['capacitive 모드 보호',
              '내부, ISEN 핀: ACP-soft 는 주파수를 올리고, ACP-hard 는 '
              '50&nbsp;&micro;s 멈춘 뒤 최대 주파수로 재시작',
              '최후의 보호일 뿐 &mdash; 첫째는 주파수 하한 f<sub>Min</sub>'],
             ['Light load 버스트 모드',
              'R<sub>BM</sub>, 전원 인가 시 읽음',
              '%(RBM).0f k&Omega;; 2f<sub>l</sub> 피드백 리플이 %(dVFBBM).0f mV '
              '이므로 %%s 절 참조' % V
              % SR('버스트 threshold 에 대한 피드백 리플')],
             ['최악 코너의 ZVS 상실',
              '보호가 아니라 설계 여유',
              '추정이 아니라 스윕; %s 절' % SR('ZVS 검증')]],
            widths=[CW * 0.24, CW * 0.30, CW * 0.46], split=True))
    add(h2('시스템 설계 규칙'))
    add(p('앞의 내용을 체크리스트로 정리한다.'))
    ext(bullets([
        '<b>탱크는 상용전원 범위가 아니라 등가 범위 %(Veqlo).1f ~ '
        '%(Veqhi).1f&nbsp;Vac 에서 설계한다.</b>' % V,
        '<b>&lambda; 는 0.5 근처를 예상할 것.</b> two-stage 의 인덕턴스 비로는 '
        '최저 입력 전압에서 필요한 게인이 나오지 않는다.',
        '<b>f<sub>Min</sub> 을 f<sub>o</sub> 위에.</b> anti-capacitive 보호는 '
        '첫째가 아니라 최후의 보호다.',
        '<b>출력 뱅크는 리플과 hold-up 에서 정하고</b> 큰 쪽을 잡은 뒤, 실효 '
        '리플 전류를 따로 검사한다.',
        '<b>crossover 주파수는 수십 Hz.</b> 남는 피드백 리플은 더 빠른 루프가 '
        '아니라 R<sub>BM</sub> 으로 처리한다.',
        '<b>모핑 경계 둘을 Full load 와 Light load 에서 잰다.</b>',
        '<b>권선비는 턴수 비 그 자체가 아니라 n&thinsp;V<sub>o,eff</sub> 로 검사한다.</b>',
        '<b>과전류는 합성 탱크 피크로 판단한다.</b>',
        '<b>커패시터 리플 전류에 2f<sub>l</sub> 성분을 넣고</b>, 센터탭은 출력 '
        '노드에서 판단한다.',
        '<b>2차 실효값에 &radic;d 를 넣는다.</b> 빼면 여기서는 손실을 약 '
        '%.0f&nbsp;%% 과대평가한다.' % _d_overstate(A),
        '<b>트랜스포머 도면에 턴수 옆에 L<sub>open</sub> 과 L<sub>short</sub> '
        '를 적는다.</b>',
        '<b>ESR 은 전류 성분마다 그 주파수의 값</b>: 스위칭과 2f<sub>l</sub>.',
        '<b>L<sub>m</sub> 을 올렸으면 ZVS 를 다시 검사한다.</b>',
        '<b>ZVS 는 선정한 탱크를 스윕해 검증한다.</b> 닫힌 식은 오차 부호가 '
        '정해져 있지 않다.',
        '<b>계산값과 선정값을 따로 기록하고</b>, 이후의 모든 검사가 선정값을 쓰게 한다.',
        '<b>절연을 배치하기 전에 누설부터 어림한다.</b> 간격이 강화 절연을 맡으면 '
        'creepage 보다 좁을 수 없고, 그러면 식&nbsp;%s L<sub>short</sub> 의 '
        '하한을 정한다. 그 하한이 L<sub>r</sub> 보다 높으면 절연을 전선에 넣고, '
        '탱크를 확정하기 전에 칸 권선을 L<sub>r</sub> 에 대해 다시 확인한다.'
        % _nj(ER('leak'), '이', '가'),
        '<b>동박은 동심 권선에서만.</b> 칸 사이에서는 누설 자계가 권선창과 동박 '
        '면을 가로지른다.',
        '<b>V<sub>CC</sub> 를 공급하는 보조 권선</b>: hold-up 끝에서도 레귤레이션되는 '
        '가장 작은 정수 턴의 권선비를 잡고, C<sub>VCC</sub> 는 정상 상태가 아니라 '
        '기동 인계 구간에 맞춰 정한다.']))

    add(p('<b>실장 부품이 요구하는 배치 규칙.</b> 각각 데이터시트의 지시이거나 '
          '전류가 흐르는 길에서 따라 나온다:'))
    ext(bullets([
        '<b>R<sub>CS</sub>:</b> ISEN 과 컨트롤러 접지는 각각 제 배선으로 sense '
        '저항 양 끝까지. 직렬 소자도 필터도 없이. 브리지 귀환 전류가 ISEN 배선을 '
        '같이 쓰면 안 된다.',
        '<b>게이트 루프:</b> R<sub>G</sub>, 턴오프 다이오드, R<sub>G,off</sub> 를 '
        '게이트 옆에 두고 STO60N045DM9 의 드라이버 소스 핀으로 돌려보낸다. '
        '거기서 PGND(로우사이드) 또는 OUT(하이사이드)으로. 전력 소스 전류는 '
        '게이트 루프를 지나지 않는다.',
        '<b>드라이버 디커플링:</b> C<sub>BOOT</sub> 는 BOOT 와 OUT 핀 바로 옆에, '
        '세라믹은 VCC 와 PGND 핀 바로 옆에, D<sub>BS</sub> 는 C<sub>BOOT</sub> '
        '옆에.',
        '<b>L6790A 전원:</b> VCC 와 GND 핀 사이에 100&nbsp;nF, 그 옆에 '
        'C<sub>VCC</sub>. HVSU 는 브리지의 AC 쪽에서.',
        '<b>SR sense:</b> DSA/DSB 와 SSA/SSB 는 짝의 드레인과 소스로 가는 별도 '
        '배선, 전력 접지를 따라가지 않는다. 컨트롤러 GND 는 두 소스 버스가 '
        '만나는 SR 소스에. R<sub>SR</sub>, C<sub>SR</sub>, %(cb).1f&nbsp;'
        '&micro;F 는 VCC 핀에.' % dict(cb=A._builder_const('C.SRb')),
        '<b>패스 트랜지스터:</b> FZT651 마다 컬렉터 탭을 정격이 가정하는 '
        '50&nbsp;&times;&nbsp;50&nbsp;mm 동박에. 제너 캐소드는 1&nbsp;cm&sup2; 에.',
        '<b>피드백:</b> TL431 회로와 R<sub>I</sub>, R<sub>O</sub> 는 출력 단자 '
        '근처 한 점에서 2차 접지로, SR 소스 버스에서 떨어뜨려. C<sub>fx</sub> 는 '
        'FB 핀에.']))

    add(h2('하드웨어에서 먼저 잴 것'))
    add(p('순서대로. 앞의 네 항목이 설계의 성립 여부를 판단한다.'))
    ext(bullets([
        '<b>라인 반주기에 걸친 f<sub>sw</sub>(&theta;).</b> 두 오실레이터 '
        '클램프 뒤에 있는 미지수 T<sub>idle</sub> 을 확정한다.',
        '<b>%(Cout).1f&nbsp;mF 뱅크를 모두 단 상태의 cold start.</b> 기동 허용 시간은 정해져 있고, 이 위험은 이 구조에서 새로 생긴다.' % V,
        ('<b>하프브리지 경계(245&nbsp;V<sub>pk</sub>, Full load)의 ZVS</b>. 여기가 '
         '스윕의 최악점이기도 하다: 계산 %(zTzc).0f&nbsp;ns 대 %(tD).0f&nbsp;ns.'
         % dict(V, **ZVS_WORST)
         if round(ZVS_WORST['cTzc']) == round(ZVS_WORST['zTzc']) else
         '<b>하프브리지 경계(245&nbsp;V<sub>pk</sub>, Full load)의 ZVS</b>: 계산 '
         '%(cTzc).0f&nbsp;ns 대 %(tD).0f&nbsp;ns. 그다음 스윕의 최악점, '
         '%(zAt)s 의 %(zLoad).0f&nbsp;%% 부하, %(zTzc).0f&nbsp;ns. '
         '이 설계를 판정하는 숫자다.'
         % dict(V, zAt=_where(ZVS_WORST['zVin'], A.R, fb='FB 경계(풀브리지 %.0f&nbsp;Vac, 탱크에는 %.0f&nbsp;Vac)', hb='HB 경계(하프브리지 %.0f&nbsp;Vac)', other='%.0f&nbsp;Vac'), **ZVS_WORST)),
        '<b>풀브리지 경계(235&nbsp;V<sub>pk</sub>, Full load)의 스위칭 주파수</b>: '
        '계산 %(fswB).1f&nbsp;kHz. VCO 상한에 닿으면 안 된다.' % V,
        '<b>%(Vacmin).0f&nbsp;Vac Full load 의 입력 전류와 THD</b>: 영교차 '
        'dead zone.' % V,
        '<b>부하가 견디는 값에 대한 출력 리플.</b>',
        '<b>뱅크의 리플 전류와 온도 상승</b>: 계산 %(ICout).2f&nbsp;A rms, '
        '개당 %(Icout1).2f&nbsp;A.' % V,
        '<b>소자 온도</b>, 245&nbsp;V<sub>pk</sub> 위 <b>하프브리지 모핑</b>에서. '
        '고정 소자의 손실이 가장 큰 곳이다. 손실 budget 초과를 감수한 결정이 맞는지 이것으로 판정한다.',
        '<b>Light load 에서 버스트 threshold 에 대한 피드백 리플.</b>',
        '<b>리플 골에서의 AC 정전</b>: %(Thold).0f&nbsp;ms 뒤에도 출력이 '
        '%(Vomin).0f&nbsp;V 위.' % V,
        '<b>모핑 띠를 가로지르는 스텝</b>, 양방향.',
        '<b>출력에 대한 V<sub>CC</sub> 와 보조 권선 전압</b>: No load, Full load, '
        'cold start 에서. 권선이 출력을 따라가는지, 언제 C<sub>VCC</sub> 에게서 '
        '공급을 넘겨받는지.',
        '<b>두 레그의 게이트와 중점 타이밍</b>: 게이트에 남는 데드타임, cold start '
        '동안의 V<sub>BO</sub>(%(VBOrec).1f&nbsp;V 위에 머물러야 한다), 그리고 '
        '%(dvmax).0f&nbsp;V/ns 에 대한 중점 dv/dt.' % V,
        '<b>SR 게이트 파형</b>: 게이트 핀당 MOSFET 둘로, No load 의 가장 긴 '
        'burst-off 시간, 그리고 Full load 에서 V<sub>CC,SR</sub> 과 '
        'Q<sub>SR</sub>·TEA2095TE 의 온도.',
        '<b>트랜스포머의 작업 전압과 내전압 시험</b>: 첫 샘플로, 인증 기관에 '
        '보내기 전에.']))

    add(h2('전체 회로와 이 설계의 값'))
    add(p('그림&nbsp;%(f)s 는 이 장의 부품을 한 쪽에 모아 옆으로 눕혀 그렸다. '
          '왼쪽이 1차, 오른쪽이 2차이고, 둘 사이의 선을 넘는 것은 트랜스포머뿐이다. '
          '다른 곳으로 이어지는 net 은 이름표를 단다. 적힌 값은 전부 시트의 '
          '선정값이다. 여기서 처음 이름을 붙인 부품은 AC 라인에서 HVSU 로 가는 '
          '기동 다이오드 D<sub>HV</sub>, 부트스트랩 다이오드 D<sub>BS</sub>, 출력 '
          '뱅크 옆의 세라믹 C<sub>HF</sub> 다. 나머지는 %(s1)s 절부터 %(s2)s 절까지의 '
          '부품과 %(s3)s 절의 레귤레이터다: 보조 권선의 D<sub>aux</sub> 와 '
          'C<sub>aux</sub>, 베이스에 D<sub>Z</sub> 를, 이미터에 D<sub>byp</sub> 를 '
          '단 Q<sub>VCC</sub>.'
          % dict(f=FR('an_full'),
                 s1=SR('1차 스위치: STO60N045DM9'),
                 s2=SR('전압 루프 설계 결과'),
                 s3=SR('보조 권선 V<sub>CC</sub> 설계 결과'))))
    add(p('이 문서가 크기를 정하지 않은 것은 블록으로, 또는 값 없이 그렸다: EMI '
          '필터와 입력 브리지 BR1. SR 게이트 저항은 ST 보드의 0&nbsp;&Omega; '
          '자리이고, C<sub>aux</sub> 는 임의로 고른 값이다. DRV_EN 과 RT 의 '
          '풀다운 스위치는 실장하지 않는다. 컨트롤러를 끄는 방법을 보일 뿐이다.'))
    add(A.figpage('an_full',
                  '전체 회로. 핀 번호는 L6790A 는 ST EVL6790_670W 제어 보드의 '
                  '번호, L6498LD 는 SO-14, TEA2095TE 는 HSO8, 트랜스포머는 '
                  '그림&nbsp;%s 의 번호다. 브리지 귀환은 1차 접지이고, '
                  'R<sub>CS</sub> 는 그 접지와 정류기 음극 사이에 있어 ISEN 이 '
                  '거기서 읽는다. SR 소스 버스는 하나의 2차 접지에서 만난다.'
                  % FR('an_xfmr_pins')))
    _k = A._builder_const

    def _ohm(v):
        if v >= 1e3:
            return ('%.1f' % (v / 1e3)).rstrip('0').rstrip('.') + ' k&Omega;'
        return ('%.1f' % v).rstrip('0').rstrip('.') + ' &Omega;'

    def _nf(v):
        if v < 1:
            return '%.0f pF' % (v * 1e3)
        if v < 1e3:
            return ('%.2f' % v).rstrip('0').rstrip('.') + ' nF'
        return ('%.1f' % (v / 1e3)).rstrip('0').rstrip('.') + ' &micro;F'
    add(p('표&nbsp;%s 는 같은 부품을 기호별로, 크기를 정한 절과 함께 적었다. '
          '부품이 견뎌야 할 것(전압, 전력, 온도)은 그 절에 있다. 표는 값과 '
          '부품만 준다.' % TR('bom')))
    ext(tbl('그림&nbsp;%s 의 부품. 값은 시트의 선정값이다. 이 문서가 크기를 정하지 '
            '않은 부품은 그렇게 적었다.' % FR('an_full'),
            [['기호', '부품', '정한 절'],
             ['EMI 필터, BR1', '여기서 정하지 않음. BR1 은 %.0f Vac 에서 %.1f A rms '
              '를 흘리고 상용전원 피크를 막는다' % (V['Vacmin'], A.SH['I.in_max']),
              '&mdash;'],
             ['D<sub>HV</sub> &times; 2', 'S1M, 1000 V, 1 A, 각 AC 라인에서 HVSU '
              '로', '%s' % SR('보조 권선 V<sub>CC</sub> 설계 결과')],
             ['C<sub>in</sub>', '%s 필름, 입력 전압 전체 정격'
              % _nf(A.SH['C.in_sel']), '%s' % SR('입력 커패시터')],
             ['R<sub>CS</sub>', '%.0f m&Omega; &times; %.0f 병렬 = %.1f m&Omega;, '
              '%.0f W 부품' % (A.SH['R.CS_single'], A.SH['N.RCS'],
                             A.SH['R.CS'], 1),
              '%s' % SR('전류 sense 저항: 저항 하나가 세 가지를 정한다')],
             ['S1&ndash;S4', 'STO60N045DM9, 자리마다 1개', '%s'
              % SR('1차 스위치: STO60N045DM9')],
             ['U1 과 주변 회로', 'L6790A; R<sub>T</sub> %s, C<sub>T</sub> %s C0G, '
              'R<sub>CFG</sub> %s, R<sub>BM</sub> %s, R<sub>ZCD,H</sub> %s, '
              'R<sub>ZCD,L</sub> %s, C<sub>fx</sub> %s, VCC 에 100 nF'
              % (_ohm(A.SH['R.T'] * 1e3), _nf(A.SH['C.T'] / 1e3),
                 _ohm(A.SH['R.CFG_sel'] * 1e3), _ohm(A.SH['R.BM_sel'] * 1e3),
                 _ohm(A.SH['R.ZCD_H_sel'] * 1e3), _ohm(A.SH['R.ZCD_L_sel'] * 1e3),
                 _nf(A.SH['C.fx'])),
              '%s ~ %s' % (SR('컨트롤러 주변 부품'),
                           SR('출력 sensing 과 과전압: ZCD 분압기'))],
             ['U2, U3 과 게이트 회로', 'L6498LD(SO-14); 드라이버마다 C<sub>BOOT</sub> '
              '%s 와 D<sub>BS</sub> ES1J(600 V, 1 A); 게이트마다 R<sub>G</sub> %s, '
              'D<sub>G,off</sub> 1N4148W, R<sub>G,off</sub> %s'
              % (_nf(_k('C.BOOT')), _ohm(_k('R.G')), _ohm(_k('R.G_off'))),
              '%s' % SR('게이트 드라이버: L6498LD 2개')],
             ['C<sub>r</sub>', '%s. 전압·전류 정격은 탱크 피크에서 따라 나오고 '
              '여기서 정하지 않았다' % _nf(A.SH['C.r']),
              '%s' % SR('단계별 계산')],
             ['T1', 'TDK PQ 50/50, N97, 코일 포머 B65982E 에 3.0 mm 칸막이; '
              '표&nbsp;%s' % TR('spec-out'),
              '%s' % SR('자속 확인과 사양서')],
             ['D<sub>aux</sub>, D<sub>byp</sub>, C<sub>aux</sub>, '
              'R<sub>BZ</sub>, D<sub>Z</sub>, Q<sub>VCC</sub>, C<sub>VCC</sub>',
              '1N4148W &times; 2; %s; %s; BZT52H-C15(%.0f V); FZT651, 동박 '
              '50 &times; 50 mm; %.0f &micro;F + 100 nF'
              % (_nf(_k('C.aux') * 1e3), _ohm(V['RBZ']), V['DZ'],
                 V['CVCC']),
              '%s' % SR('보조 권선 V<sub>CC</sub> 설계 결과')],
             ['Q<sub>A1</sub>&ndash;Q<sub>B2</sub>, R<sub>G,SR</sub>',
              'STL160N10F8, 레그당 %.0f개; 게이트 저항은 ST 보드처럼 %s 자리'
              % (V['nSR'], _ohm(_k('R.G_SR'))),
              '%s' % SR('SR MOSFET: STL160N10F8')],
             ['U7, R<sub>SR</sub>, C<sub>SR</sub>', 'TEA2095TE(HSO8); %s; VCC 핀에 '
              '%s 와 %s 병렬'
              % (_ohm(_k('R.SR')), _nf(_k('C.SR')), _nf(_k('C.SRb') * 1e3)),
              '%s' % SR('동기 정류: TEA2095TE')],
             ['R<sub>BSR</sub>, D<sub>ZSR</sub>, Q<sub>SR</sub>', '%s; '
              'BZT52H-C15(%.0f V); FZT651, 동박 50 &times; 50 mm'
              % (_ohm(_k('R.BSR_sel')), _k('V.DZSR_sel')),
              '%s' % SR('동기 정류: TEA2095TE')],
             ['C<sub>out</sub>, C<sub>HF</sub>', '%.0f &micro;F &times; %.0f = '
              '%.1f mF; 세라믹 %.0f &micro;F'
              % (A.SH['C.single'], A.SH['n.C'], A.SH['C.out'],
                 A.SH['C.ceramic']),
              '%s' % SR('출력 뱅크 설계 결과')],
             ['R<sub>I</sub>, R<sub>O</sub>, Q5, C<sub>Fo</sub>, R<sub>F</sub>, '
              'C<sub>F</sub>, R<sub>P</sub>, R<sub>B</sub>, Q4',
              '%s, %s; TL431B; %s, %s, %s; %s, %s; SFH617A-2'
              % (_ohm(V['RI'] * 1e3), _ohm(V['Ro'] * 1e3), _nf(V['CFo']),
                 _ohm(V['RF'] * 1e3), _nf(V['CF']), _ohm(V['RP'] * 1e3),
                 _ohm(V['RB'] * 1e3)),
              '%s' % SR('전압 루프 설계 결과')],
             ['R<sub>Z</sub>, R<sub>Z1</sub>, R<sub>Z2</sub>, Q6, C<sub>Z</sub>',
              '%s; %s, %s; TL431B; %s'
              % (_ohm(_k('R.Z_sel')), _ohm(_k('R.Z1') * 1e3),
                 _ohm(_k('R.Z2') * 1e3), _nf(_k('C.Z') * 1e3)),
              '%s' % SR('전압 루프 설계 결과')]],
            widths=[CW * 0.24, CW * 0.58, CW * 0.18], key='bom', split=True))

    # =============================================================== 8
    add(h1('기호표'))
    add(p('이 문서에서 쓴 기호. 컨트롤러 자체의 전기 파라미터는 데이터시트에 '
          '있다.'))
    _SYM = [
        ('<b>탱크와 게인</b>', ''),
        ('C<sub>r</sub>, L<sub>r</sub>, L<sub>m</sub>', '탱크 모델의 공진 커패시터, 직렬 인덕턴스, 자화 인덕턴스'),
        ('Z<sub>0</sub>, Z<sub>0,design</sub>', '특성 임피던스 &radic;(L<sub>r</sub>/C<sub>r</sub>); 탱크를 설계하는 기준값 R<sub>ac</sub>Q<sub>ZVS</sub>'),
        ('Z<sub>in</sub>', '브리지가 구동하는 입력 임피던스; arg Z<sub>in</sub> = 0 이 capacitive 경계'),
        ('f<sub>r</sub>, f<sub>o</sub>', '직렬 공진, 그리고 L<sub>m</sub> 을 포함한 아래쪽 공진'),
        ('f<sub>sw</sub>, f<sub>n</sub>', '스위칭 주파수, 그리고 f<sub>r</sub> 로 정규화한 값'),
        ('f<sub>sw,max</sub>, f<sub>sw,min</sub>', '사양의 최대 스위칭 주파수(&lambda; 의 입력); 그리고 오실레이터가 도달해야 할 최저 주파수(이 설계에서는 f<sub>o</sub>)'),
        ('f<sub>sw,des</sub>', '오실레이터 범위를 설계하는 주파수: 컨버터가 실제로 도는 최고 스위칭 주파수의 1.5 배, 사양 최대값 이하'),
        ('T<sub>sw</sub>, T<sub>r</sub>', '스위칭 주기 1/f<sub>sw</sub>, 공진 주기 1/f<sub>r</sub>'),
        ('&lambda;, m', 'L<sub>r</sub>/L<sub>m</sub>, 그리고 (L<sub>r</sub>+L<sub>m</sub>)/L<sub>r</sub> = 1 + 1/&lambda;'),
        ('&lambda;<sub>act</sub>, &lambda;<sub>req</sub>', '선정한 부품의 &lambda;, 그리고 설계가 요구한 &lambda;'),
        ('&lambda;<sub>1</sub>, &lambda;<sub>2</sub>, &lambda;<sub>TD</sub>, &lambda;<sub>3</sub>', '&lambda; 후보 넷: 최소 게인, 여기에 주파수 상한을 더한 것, 데드타임 조건, 최소 주파수 조건; 가장 큰 것이 결정한다'),
        ('Q, Q<sub>pk</sub>, Q<sub>ZVS</sub>', '품질계수 Z<sub>0</sub>/R<sub>ac</sub>; 라인 피크에서의 값; ZVS 조건이 두는 한도'),
        ('R<sub>ac</sub>', '기본파에서 정류기와 부하를 저항 하나로 본 것'),
        ('v<sub>RI</sub>, v<sub>RI</sub><sup>F</sup>, i<sub>RI</sub>', '1차로 환산한 정류기 입력의 구형파 전압, 그 기본파, 그리고 탱크가 정류기로 보내는 사인 전류'),
        ('M', '탱크 게인, n V<sub>o,eff</sub> 를 구동 진폭으로 나눈 것'),
        ('M<sub>req</sub>, M<sub>pk</sub>', '동작점이 요구하는 게인, 그리고 라인 피크에서의 값'),
        ('M<sub>min</sub>, M<sub>max</sub>', '고전적인 LLC 설계 절차에서: 입력 범위와 출력 허용 오차로 정해지는, 탱크가 커버해야 하는 게인 범위'),
        ('M<sub>low</sub>, M<sub>high</sub>', '낮은·높은 등가 코너의 요구 게인'),
        ('M<sub>OL</sub>, M<sub>&infin;</sub>', 'No load(Q = 0, 출력 Open)의 게인 곡선, 그리고 그것이 수렴하는 하한 1/(1+&lambda;)'),
        ('M<sub>Z</sub>', 'capacitive/inductive 경계(arg Z<sub>in</sub> = 0)에서의 게인을 Q 를 바꿔 가며 이은 곡선. 게인 피크보다 조금 오른쪽'),
        ('x, u, q', '게인 식을 3차식으로 만드는 치환: 1/f<sub>n</sub>&sup2;, sin&sup2;&thinsp;&theta;, Q<sub>pk</sub>&sup2;u&sup2;'),
        ('d', '2차의 도통비 f<sub>sw</sub>/f<sub>r</sub>, above 에서는 1'),
        ('n, n<sub>T</sub>', '등가 모델 권선비, 그리고 실제(감는) 권선비'),
        ('N<sub>rect</sub>', '2차 도통 경로의 소자 수: 센터탭 1, 풀브리지 2'),
        ('V<sub>drive</sub>', '브리지가 탱크에 거는 진폭: 풀브리지에서는 정류 전압, 하프브리지에서는 그 절반'),
        ('V<sub>refl</sub>', '반사 출력 전압 n V<sub>o,eff</sub>'),
        ('V<sub>o,eff</sub>', 'V<sub>out</sub> + N<sub>rect</sub> V<sub>f</sub>'),
        ('V<sub>f</sub>', '2차 정류기 하나의 순방향 전압 강하'),

        ('<b>상용전원과 역률</b>', ''),
        ('&theta;', '라인 위상각'),
        ('&theta;<sub>0</sub>', '컨버터가 f<sub>r</sub> 을 지나는 라인 위상: sin&theta;<sub>0</sub> = M<sub>pk</sub>. &theta;<sub>0</sub> 와 180&deg; &minus; &theta;<sub>0</sub> 사이에서 buck 한다'),
        ('f<sub>l</sub>, f<sub>l,min</sub>, &omega;<sub>l</sub>', '라인 주파수, 그 최저 규정값, 그리고 2&pi;f<sub>l</sub>'),
        ('v<sub>ac</sub>, V<sub>ac</sub>, I<sub>ac</sub>', '순시 상용전원 전압, 그리고 입력 실효 전압과 전류'),
        ('I<sub>1,rms</sub>', '입력 전류 기본파만의 실효값'),
        ('p<sub>in</sub>(t), P', '순시·평균 입력 전력'),
        ('v<sub>in</sub>(&theta;), i<sub>in</sub>(&theta;)', '라인 반주기 동안의 정류된 상용전원 전압과 거기서 끌어오는 전류'),
        ('PF, THD', '역률, 그리고 입력 전류의 THD'),
        ('&phi;<sub>1</sub>, D', '기본파의 변위각, 그리고 distortion 계수 I<sub>1,rms</sub>/I<sub>ac</sub>'),
        ('D<sub>3</sub>', '입력 전류의 3차 고조파, 기본파에 대한 비'),
        ('V<sub>in</sub>, V<sub>pk</sub>', '브리지 레일 전압, 그리고 상용전원 피크'),
        ('V<sub>bus</sub>', 'two-stage 컨버터의 두 단 사이에 있는 정전압 DC 버스'),
        ('V<sub>ac,eq</sub>, V<sub>ac,eq,low</sub>, V<sub>ac,eq,high</sub>', '모핑 뒤 탱크가 보는 등가 입력 전압, 그리고 두 모핑 threshold 에서의 값'),
        ('V<sub>eq,min</sub>, V<sub>eq,max</sub>', '최저 등가 입력(HB 경계)과 상용전원 최대, ST 툴의 여유 계수 &Gamma;<sub>v</sub> 에서 쓰는 값'),

        ('<b>전력과 손실</b>', ''),
        ('P<sub>in</sub>, P<sub>out</sub>', '입력 전력, 출력 전력'),
        ('P<sub>LLC</sub>, P<sub>EMI</sub>, P<sub>BR</sub>', 'budget 으로 잡은 손실 셋: LLC 단, EMI 필터, 입력 브리지'),
        ('P<sub>in,LLC</sub>', '탱크로 들어가는 전력, P<sub>out</sub>/&eta;<sub>HB</sub>'),
        ('&eta;<sub>HB</sub>', 'LLC 단의 가정 효율'),
        ('P<sub>mos,dc</sub>', '하프브리지 모핑에서 켜진 채 고정되는 1차 소자의 도통 손실'),
        ('P<sub>SR</sub>, P<sub>SR,leg</sub>', '2차 정류기 손실, 소자당과 정류 레그당'),
        ('P<sub>CS</sub>', '전류 sense 저항의 손실'),
        ('P<sub>budget</sub>', '부품을 고르기 전에 소자 한 개에 허용한 손실'),
        ('E, C, V, V<sub>min</sub>', 'hold-up 식에서 커패시턴스 C 가 두 전압 사이에서 방출하는 에너지'),

        ('<b>한 스위칭 주기의 전류와 시간</b>', ''),
        ('i<sub>Lr</sub>, I<sub>Lr,pk</sub>', '탱크 전류, 그리고 그 피크: 반사 부하 더하기 자화'),
        ('i<sub>trafo</sub>, I<sub>trafo,pk</sub>', '반사 부하 전류만, 그리고 그 피크'),
        ('i<sub>Lm</sub>, I<sub>Lm,pk</sub>', '탱크 모델의 자화 전류, 그리고 그 피크'),
        ('i<sub>&mu;</sub>, i<sub>&mu;,pk</sub>', '실제 트랜스포머의 자화 전류, 그리고 그 피크'),
        ('i<sub>p</sub>, i<sub>s</sub>', '순시 1차·2차 권선 전류'),
        ('I<sub>sec,pk</sub>', '정류 레그당 2차 피크 전류'),
        ('I<sub>pri,rms</sub>', '최악 스위칭 사이클의 1차 실효값'),
        ('I<sub>lc</sub>, I<sub>pri</sub>, I<sub>rect</sub>', '라인 사이클 실효값: 스위칭 주기마다의 실효값을 라인 반주기에 걸쳐 I&sup2; 평균한 것; 1차와 정류 레그 하나에 대해'),
        ('I<sub>Cout</sub>, I<sub>out</sub>', '출력 뱅크의 리플 전류, 그리고 부하 전류'),
        ('t<sub>D</sub>, T<sub>ZC</sub>, T<sub>ZC,min</sub>', '브리지 데드타임; 게이트가 꺼진 뒤 탱크 전류가 0 에 닿기까지의 시간, 그리고 운전 영역 전체에서의 최솟값'),
        ('T<sub>T</sub>', '스윙 시간: 데드타임 동안 브리지 노드가 레일을 건너가는 데 걸리는 시간'),
        ('v<sub>d</sub>, v<sub>d</sub><sup>F</sup>, V<sub>ds</sub>', '브리지 중점 전압, 그 기본파, 그리고 소자의 드레인-소스 전압'),
        ('v<sub>A</sub>, v<sub>B</sub>', '브리지의 두 중점 A, B 의 0 기준 전압. v<sub>d</sub> = v<sub>A</sub> &minus; v<sub>B</sub>'),
        ('i<sub>S1</sub>', 'S1 의 드레인 전류, 드레인에서 소스로 흐르는 방향이 양'),
        ('S<sub>1</sub>, S<sub>2</sub>, S<sub>3</sub>, S<sub>4</sub>, D<sub>1</sub>, D<sub>2</sub>', '브리지 스위치 넷, 그리고 2차 정류기 둘'),
        ('i<sub>D1</sub>, i<sub>D2</sub>, i<sub>D</sub>', '각 2차 정류기의 순방향 전류; i<sub>D</sub> 는 그 중 하나'),

        ('<b>트랜스포머와 코어</b>', ''),
        ('B(t), B<sub>pk</sub>, B<sub>max</sub>', '자속 밀도, 그 피크, 그리고 설계가 지키는 상한'),
        ('N', '패러데이 법칙에서 전압이 걸린 권선의 턴수'),
        ('A<sub>e</sub>, A<sub>min</sub>', '코어 유효 단면적, 그리고 가장 좁은 단면'),
        ('A<sub>N</sub>', '보빈의 권선창 면적'),
        ('A<sub>L</sub>, g, &mu;<sub>0</sub>', '갭을 둔 코어의 인덕턴스 계수, 중앙 다리 총 갭, 진공 투자율'),
        ('N<sub>p</sub>, N<sub>s</sub>, N<sub>x</sub>', '1차 턴수, 권선당 2차 턴수, 유닛 수'),
        ('N<sub>s1</sub>, N<sub>s2</sub>', '센터탭 2차의 위쪽 반과 아래쪽 반(설계 예제의 NS2, NS3)'),
        ('i<sub>NS</sub>, i<sub>NS2</sub>, i<sub>NS3</sub>, v<sub>NS</sub>', '설계 예제에서: 권선 이름으로 부른 2차 권선 전류, 그리고 한 권선의 전압'),
        ('N<sub>aux</sub>, n<sub>aux</sub>/n<sub>sec</sub>', '보조 권선 턴수, 그리고 2차 하나에 대한 그 권선비'),
        ('L<sub>open</sub>, L<sub>short</sub>', '1차 단자에서 잰 인덕턴스: 나머지 권선을 모두 Open 한 값, 그리고 2차를 Short(센터탭이면 반쪽씩)하고 보조 권선은 Open 한 값'),
        ('I<sub>dc</sub>', 'DC overlap 시험에서 LCR 신호에 겹쳐 흘리는 DC 전류'),
        ('I<sub>p,pk</sub>, L<sub>p</sub>', '플라이백 비교에서만: 플라이백의 1차 피크 전류와 1차 인덕턴스'),
        ('&Phi;, &Phi;<sub>p</sub>, &Phi;<sub>s</sub>', '플라이백 비교에서: 코어 자속, 그리고 1차와 2차의 암페어-턴이 각각 혼자 만들 자속'),
        ('B<sub>s</sub>', '코어 재료의 포화 자속 밀도, 온도별 재료 데이터에서'),
        ('L<sub>&mu;</sub>, L<sub>L1</sub>, L<sub>L2</sub>', '실제 자화 인덕턴스와 두 누설 인덕턴스'),
        ('L<sub>1</sub>, L<sub>2</sub>', '1차와 2차 하나에서 잰 Open 인덕턴스'),
        ('L, &Delta;L', '인덕턴스와 공차가 허용하는 그 변화'),
        ('I<sub>eq</sub>, I<sub>sat</sub>', '동작 자속을 재현하는 Open 전류; DC overlap 시험 전류'),

        ('<b>동선</b>', ''),
        ('A<sub>cu</sub>, J, I<sub>rms</sub>', '권선 하나에 필요한 동선 단면적, 그 기준 전류 밀도, 그리고 그 권선의 실효 전류. I<sub>rms</sub>(&theta;) 는 라인 위상 &theta; 에서 스위칭 한 주기에 걸친 실효값'),
        ('N<sub>w</sub>, A<sub>cu,w</sub>', '모든 권선에 대한 합에서 권선 w 의 턴수와 동선 면적'),
        ('k<sub>u</sub>', '권선창 점적률: A<sub>N</sub> 중 동선이 되는 몫'),
        ('&delta;, &rho;, f', 'skin depth, 동작 온도에서의 구리 비저항, 그리고 깊이를 평가하는 주파수'),
        ('&sigma;', '구리의 도전율 1/&rho;, 소선 와전류 손실 식에 쓴다'),
        ('d<sub>s</sub>, a<sub>s</sub>, n<sub>s</sub>', 'Litz 소선 지름, 소선 하나의 동선 단면적, 권선에 필요한 소선 수'),
        ('d<sub>litz</sub>, k<sub>litz</sub>', '서빙까지 한 Litz 선의 외경, 그리고 그 점적률'),
        ('t<sub>f</sub>, w<sub>f</sub>, w<sub>f,max</sub>, n<sub>f</sub>', '동박 두께, 한 턴에 필요한 폭, 가정한 동박 한 장의 최대 폭, 병렬 동박 수'),
        ('N<sub>A</sub>, N<sub>B</sub>', '둘로 나눈 1차의 두 부분의 턴수'),
        ('w<sub>A</sub>, w<sub>S</sub>, w<sub>B</sub>', '1차 A 부분, 2차, 1차 B 부분의 축 방향 폭'),
        ('g<sub>1</sub>, g<sub>2</sub>', '권선 칸 사이의 간격'),
        ('h<sub>w</sub>, l<sub>N</sub>', '누설 자계가 가로지르는 권선창의 깊이, 그리고 평균 턴 길이'),
        ('h<sub>r</sub>, k<sub>w</sub>', '코일 포머 튜브에서 플랜지 끝(또는 바깥다리 중 가까운 쪽)까지의 반경 공간, 그리고 다발 지름에 대한 층 사이 피치(실제 권선의 느슨함)'),
        ('h<sub>A</sub>, h<sub>S</sub>', '1차 칸, 그리고 NAUX 를 포함한 2차 칸의 반경 방향 두께'),
        ('k<sub>ax</sub>', '다발 지름에 대한 층 방향 피치. 두 칸과 칸막이가 권선 폭을 채우도록 펼친 값'),
        ('J<sub>p</sub>, J<sub>s</sub>', '실제 권선의 1차, 2차 권선마다의 전류 밀도'),

        ('<b>반도체</b>', ''),
        ('R<sub>DS(on)</sub>, R<sub>DS(on),25</sub>, k<sub>T</sub>', '온저항, 그 25&nbsp;&deg;C 대표값, 그리고 25&nbsp;&deg;C 에서 T<sub>j,max</sub> 까지의 배율'),
        ('T<sub>j</sub>, T<sub>j,max</sub>, T<sub>a</sub>', 'junction 온도, 그 정격, 주위 온도'),
        ('C<sub>oss</sub>, C<sub>o(tr)</sub>, Q<sub>oss</sub>', 'MOSFET 의 소신호·시간 등가 출력 커패시턴스, 그리고 시간 등가값이 뜻하는 전하'),

        ('<b>컨트롤러와 주변 회로</b>', ''),
        ('V<sub>FB</sub>, v<sub>FB</sub>', '정격 전력에서 0.5&nbsp;V 오프셋 위의 피드백 전압, 그리고 그 소신호 성분'),
        ('V<sub>os</sub>, K<sub>HV</sub>, K<sub>M</sub>, K<sub>FF</sub>', '피드백 법칙의 오프셋과 내부 게인 셋, 데이터시트 블록도에서 인용'),
        ('K<sub>pwr</sub>', '전력 법칙의 게인, V<sub>FB</sub> = K<sub>pwr</sub>R<sub>CS</sub>P<sub>in,LLC</sub>'),
        ('R<sub>CS</sub>, R<sub>CS,max1</sub>, R<sub>CS,max2</sub>', '전류 sense 저항, 그리고 그것을 제한하는 두 조건: 최대 전력 법칙과 OCP1 트립'),
        ('I<sub>OCP1</sub>, I<sub>OCP2</sub>', 'R<sub>CS</sub> 가 정하는 과전류 threshold'),
        ('C<sub>T</sub>, R<sub>T</sub>', '오실레이터 타이밍 커패시터와 저항'),
        ('C<sub>T,min</sub>, C<sub>T,max</sub>, R<sub>T,ceil</sub>, R<sub>T,max</sub>', '그 둘의 선택 범위'),
        ('V<sub>ref</sub>, I<sub>EA</sub>, I<sub>EA,max</sub>', '오실레이터 기준, 유일한 제어 입력인 error amp 전류, 그리고 그 최대'),
        ('f<sub>Min</sub>, f<sub>Max</sub>, f<sub>SU</sub>', 'R<sub>T</sub>, C<sub>T</sub>, T<sub>idle</sub> 이 정하는 오실레이터 하한·상한·기동 주파수'),
        ('T<sub>idle</sub>', '오실레이터 idle 시간'),
        ('R<sub>BM</sub>, r<sub>BM</sub>, V<sub>BM,eq</sub>, P<sub>in,BM</sub>', '버스트 모드 저항, 버스트가 시작되는 전력의 정격 입력 전력 P<sub>in</sub> 에 대한 비, 등가 FB threshold, 그리고 그에 해당하는 입력 전력'),
        ('R<sub>CFG</sub>, R<sub>CFG,max</sub>', '구성 저항, 그리고 최저 입력 전압이 허용하는 최대값'),
        ('V<sub>BO</sub>, V<sub>BO,pk</sub>, V<sub>BO,rms</sub>', '브라운아웃 threshold, 그리고 그것을 상용전원 피크와 실효값으로 나타낸 값'),
        ('R<sub>ZCD,H</sub>, R<sub>ZCD,L</sub>, I<sub>bias</sub>', 'ZCD 분압기, 그리고 그 분압기에 흐르도록 설계한 전류'),
        ('V<sub>OVP1</sub>, V<sub>OVP2</sub>, V<sub>OVP1,out</sub>', '과전압 threshold 둘, 그리고 OVP1 이 겨냥하는 출력 전압'),
        ('V<sub>CC</sub>, V<sub>CCon</sub>, V<sub>CCoff</sub>', 'IC 전원, 그리고 UVLO 의 두 threshold'),
        ('V<sub>CC,reg</sub>, V<sub>CC,reg,min</sub>, C<sub>VCC</sub>, C<sub>VCC,req</sub>', '레귤레이터가 V<sub>CC</sub> 핀을 유지하는 전압과 그 범위의 아래쪽 끝; 핀의 커패시터와 기동에 필요한 값'),
        ('V<sub>CC,HVSUon</sub>', '그 아래로 내려가면 기동 회로가 충전 전류를 켜는 V<sub>CC</sub> 레벨'),
        ('V<sub>DZ</sub>, V<sub>DZ,max</sub>, V<sub>BE</sub>, V<sub>D</sub>', '레귤레이터 제너 전압과 그 공차 위쪽 끝, 패스 트랜지스터의 베이스-이미터 전압, 실리콘 다이오드 순방향 전압'),
        ('R<sub>BZ</sub>, R<sub>BZ,max</sub>, &beta;<sub>min</sub>, I<sub>Z,min</sub>', '제너 공급 저항과 레귤레이션이 유지되는 최대값, 패스 트랜지스터의 최소 전류 게인, 최소 제너 바이어스'),
        ('I<sub>VCC</sub>, I<sub>VCC,SU</sub>, I<sub>CC</sub>, I<sub>drv,q</sub>', 'V<sub>CC</sub> 레일이 정상 동작과 스위칭 시작 때 공급하는 전류, 컨트롤러 자체의 몫, 그리고 게이트 드라이버의 대기 전류'),
        ('N<sub>sw</sub>, Q<sub>g</sub>, Q<sub>g,10</sub>, C<sub>g</sub>', '구동하는 스위치 자리 수; 1차 MOSFET 하나의 게이트 전하, 구동 전압에서와 10&nbsp;V 에서, 그리고 Miller 평탄부를 지난 곡선의 기울기'),
        ('B, &Delta;Q<sub>OSC</sub>, V<sub>CC,floor</sub>, I<sub>VCC</sub>(V)', 'V<sub>CC</sub> 1 V 당 줄어드는 구동 전류; 기동 오실레이터 구간의 추가 전하; 컨트롤러와 드라이버가 보증되는 최저 V<sub>CC</sub>; 레일 전압 V 에서의 공급 전류'),
        ('C<sub>BOOT</sub>, V<sub>BO</sub>, &Delta;V<sub>boot</sub>, V<sub>drop</sub>, R<sub>BS</sub>', '부트스트랩 커패시터, 하이사이드 드라이버 전원과 주기마다의 리플, 저항 R<sub>BS</sub> 의 내장 부트스트랩 스위치에 걸리는 전압 강하'),
        ('T<sub>charge</sub>, T<sub>on,max</sub>, I<sub>QCC</sub>, I<sub>QBO</sub>', '부트스트랩을 재충전하는 로우사이드 on 시간, 가장 긴 하이사이드 on 시간, 로우사이드부와 플로팅부의 대기 전류'),
        ('R<sub>G</sub>, R<sub>g,int</sub>, R<sub>so</sub>, R<sub>si</sub>, s<sub>drv</sub>, P<sub>drv</sub>', '외부·내부 게이트 저항, 드라이버 소스·싱크 저항, 게이트 전력 중 드라이버 몫, 그리고 드라이버 손실'),
        ('D<sub>G,off</sub>, R<sub>G,off</sub>, V<sub>pl</sub>, t<sub>off,pl</sub>', 'R<sub>G</sub> 에 역병렬인 턴오프 다이오드와 저항, 1차 MOSFET 의 Miller 평탄부, 레일에서 거기까지의 게이트 하강 시간'),
        ('MT', '게이트 드라이버의 채널 사이 지연 편차'),
        ('D<sub>BS</sub>, Q<sub>A1</sub>, Q<sub>A2</sub>, Q<sub>B1</sub>, Q<sub>B2</sub>, R<sub>G,SR</sub>', '외부 부트스트랩 다이오드; SR MOSFET, 센터탭 레그당 둘; 그 게이트 저항'),
        ('D<sub>HV</sub>, D<sub>aux</sub>, C<sub>aux</sub>, Q<sub>VCC</sub>, D<sub>Z</sub>, D<sub>byp</sub>', 'HVSU 로 가는 기동 다이오드; 보조 권선의 정류 다이오드와 커패시터; V<sub>CC</sub> 패스 트랜지스터, 그 베이스 제너, 이미터의 바이패스 다이오드'),
        ('C<sub>HF</sub>', '출력 뱅크 옆의 세라믹 커패시터'),
        ('V<sub>CC,SR</sub>, R<sub>BSR</sub>, D<sub>ZSR</sub>, Q<sub>SR</sub>, R<sub>SR</sub>, C<sub>SR</sub>', 'SR 컨트롤러 전원, 그리고 그것을 만드는 팔로워의 공급 저항, 제너, 패스 트랜지스터, 직렬 저항, 핀 커패시터'),
        ('P<sub>Qpass</sub>, P<sub>DZ</sub>, P<sub>DZSR</sub>', 'OVP1 에서 V<sub>CC</sub> 패스 트랜지스터, 그 제너, SR 팔로워 제너의 손실'),
        ('T<sub>j,max</sub>, T<sub>a</sub>, R<sub>th(j-a)</sub>, h<sub>FE</sub>', '부품의 접합 한계, 그 손실에서 허용하는 주위 온도, 데이터시트가 주는 동박에서의 접합-주위 열저항, 트랜지스터의 전류 게인'),
        ('I<sub>SR,max</sub>, I<sub>SR</sub>, I<sub>SR,q</sub>', 'SR 전원 팔로워의 설계 전류, 고른 MOSFET 으로 실제 흐르는 전류, SR 컨트롤러 자체의 전류'),
        ('C<sub>iss</sub>, V<sub>SD</sub>, Q<sub>rr</sub>', 'MOSFET 입력 커패시턴스, 바디 다이오드의 순방향 전압과 역회복 전하'),
        ('Q<sub>g,SR</sub>, Q<sub>g,sync</sub>, C<sub>g,SR</sub>', '최고 구동 전압에서 SR MOSFET 하나의 게이트 전하, 데이터시트의 10&nbsp;V 동기 정류 게이트 전하, 평탄부를 지난 게이트 전하 곡선의 기울기'),
        ('Q<sub>g,run</sub>, Q<sub>g,SU</sub>', '가장 높은 레귤레이션 V<sub>CC</sub> 에서의 게이트 전하, 그리고 기동이 시작되는 V<sub>CCon</sub> 에서의 값'),
        ('V<sub>BO,min</sub>, V<sub>CC,drv,min</sub>, P<sub>drv,max</sub>, R<sub>drv</sub>', '플로팅·로우사이드 드라이버 전원의 권장 최소값, 드라이버 패키지가 허용하는 손실, 그 출력 저항'),
        ('S<sub>mid</sub>, S<sub>OUT,max</sub>', '스윙 중 브리지 중점의 기울기, 드라이버 OUT 핀이 허용하는 슬루율'),
        ('c<sub>HB</sub>, Q<sub>ZVS2</sub>', '브리지 중점이 스윙시키는 커패시턴스(소자 둘과 배선), 그것이 정하는 Q 의 데드타임 한계'),
        ('V<sub>GS</sub>, V<sub>DD</sub>, V<sub>G,SR</sub>', '게이트-소스 전압; 데이터시트 시험 회로의 드레인 전원; SR 컨트롤러의 게이트 구동 전압'),
        ('k<sub>LOUT2</sub>', '드라이버 입력 풀다운이 LOUT2 를 고정 하프브리지로 읽히는 레벨에서 얼마나 위에 두는가'),
        ('I<sub>HVSU</sub>, t<sub>hand</sub>, V<sub>out,UV</sub>', '기동 회로 충전 전류; 첫 펄스부터 보조 권선이 V<sub>CC</sub> 를 붙잡을 때까지의 시간, 그리고 그때의 출력 전압'),

        ('<b>전압 루프</b>', ''),
        ('G<sub>plant</sub>(s), G<sub>EA</sub>(s), T(s)', '플랜트 v<sub>out</sub>/v<sub>FB</sub>, 보상기 &minus;v<sub>FB</sub>/v<sub>out</sub>(귀환 부호를 뺀 값), 루프 게인 T = G<sub>plant</sub>G<sub>EA</sub>'),
        ('G<sub>o</sub>, EA<sub>o</sub>', '플랜트 적분기와 보상기의 게인 상수, rad/s'),
        ('&omega;<sub>z</sub>, &omega;<sub>p</sub>, &omega;<sub>px</sub>, &omega;<sub>c</sub>', '보상기 zero, pole, 고주파 pole, 그리고 crossover 주파수, rad/s'),
        ('f<sub>z</sub>, f<sub>p</sub>, f<sub>px</sub>, f<sub>180</sub>', '같은 zero 와 pole 을 Hz 로, 그리고 arg T = &minus;180&deg; 인 주파수'),
        ('f<sub>c</sub>, &Phi;<sub>M</sub>, GM', '루프 crossover 주파수, phase margin, gain margin'),
        ('f<sub>cto</sub>', '플랜트 적분기 단독으로 0&nbsp;dB 를 지나는 곳, G<sub>o</sub>/2&pi;'),
        ('f<sub>pHF</sub>, f<sub>MB</sub>', 'C<sub>fx</sub> 를 정하려고 고른 고주파 pole, 그리고 K-factor 법이 zero 와 pole 을 그 양쪽에 두는 중심 주파수'),
        ('K<sub>v</sub>, &Gamma;<sub>v</sub>, &alpha;<sub>v</sub>', 'Type II 보상기의 K factor, 그리고 그것을 만드는 입력 전압 여유 계수와 가중 상수'),
        ('Z<sub>f</sub>', '보상기의 피드백 임피던스, R<sub>F</sub>+C<sub>F</sub> 에 병렬인 C<sub>Fo</sub>'),
        ('v<sub>K</sub>', 'TL431 캐소드의 소신호 전압'),
        ('R<sub>I</sub>, R<sub>O</sub>', '보상기의 출력 분압기'),
        ('C<sub>Fo</sub>, C<sub>F</sub>, R<sub>F</sub>, C<sub>fx</sub>', '보상 부품: TL431 회로의 커패시터 둘과 저항, 그리고 FB 핀 커패시터'),
        ('C<sub>opto</sub>, C<sub>ser</sub>', '옵토커플러 자체의 출력 커패시턴스, 그리고 C<sub>F</sub>+C<sub>Fo</sub> 의 직렬'),
        ('R<sub>B</sub>, R<sub>B,max</sub>, R<sub>B,min</sub>, R<sub>P</sub>, R<sub>FB</sub>', '옵토커플러 LED 저항과 그 허용 범위, TL431 바이어스 저항, FB 핀 내부 풀업'),
        ('CTR, CTR<sub>s</sub>, CTR<sub>m</sub>, i<sub>LED</sub>', '옵토커플러 전류 전달비, 정상 상태와 최대 LED 전류에서의 값, 그리고 LED 전류'),
        ('i<sub>FB</sub>', '옵토커플러가 FB 핀에서 끌어내는 소신호 전류, CTR&thinsp;i<sub>LED</sub>'),
        ('I<sub>FB,steady</sub>, I<sub>FB,max</sub>, I<sub>min</sub>', '정상 상태와 최대의 FB 핀 전류, 그리고 TL431 이 조절을 유지하는 데 필요한 최소 전류'),
        ('V<sub>R</sub>, V<sub>Z</sub>, V<sub>Fo</sub>', 'TL431 기준, LED 에 전류를 주는 안정화 레일, LED 순방향 전압'),
        ('R<sub>Z</sub>, R<sub>Z1</sub>, R<sub>Z2</sub>, C<sub>Z</sub>', 'V<sub>Z</sub> shunt 레귤레이터의 공급 저항, 분압기, 커패시터'),
        ('Q4, Q5, Q6', '옵토커플러(Q4A 는 LED, Q4B 는 트랜지스터), 루프의 TL431, V<sub>Z</sub> 의 TL431'),
        ('v<sub>out</sub>, i<sub>out</sub>, v<sub>C</sub>', '소신호 출력 전압과 컨버터가 뱅크로 보내는 전류, 그리고 파형에서 커패시터의 전압'),
        ('&Delta;V<sub>loop</sub>, &Delta;V<sub>FB</sub>', '루프가 보는 2f<sub>l</sub> 출력 리플, 그리고 그것이 FB 핀에 남기는 리플'),

        ('<b>출력과 hold-up</b>', ''),
        ('C<sub>out</sub>, C<sub>in</sub>', '출력 커패시터 뱅크, 입력 필름 커패시터'),
        ('V<sub>out</sub>, I<sub>out</sub>, R<sub>L</sub>', '출력 전압과 부하 전류; 부하를 저항으로 본 것'),
        ('&Delta;v, &Delta;v<sub>pp</sub>', '허용·달성 2f<sub>l</sub> 출력 리플'),
        ('T<sub>hold</sub>, t<sub>hold</sub>, V<sub>o,min</sub>', '요구·달성 hold-up 시간, 그리고 그 끝에서 허용되는 최저 출력'),
        ('ESR', '뱅크의 등가 직렬 저항, 스위칭 주파수에서의 값'),

        ('<b>판정 여유</b>', ''),
        ('k, X, X<sub>act</sub>, X<sub>req</sub>', '판정 여유 X<sub>act</sub>/X<sub>req</sub>, X 는 그 행의 양; 이 문서의 모든 k 는 설계가 통과하면 &ge; 1'),
        ('k<sub>floor</sub>, k<sub>ceil</sub>', 'f<sub>Min</sub> 이 f<sub>o</sub> 를 얼마나 넘는가, f<sub>Max</sub> 가 최고 동작 주파수를 얼마나 넘는가'),
        ('k<sub>Ploss</sub>', '소자 한 개의 손실 budget 을 계산한 손실로 나눈 것'),
        ('k<sub>RBZ</sub>', 'R<sub>BZ,max</sub>/R<sub>BZ</sub>: 제너 공급 저항이 hold-up 끝에서도 레귤레이션되는 최대값보다 얼마나 아래인가'),
        ('w<sub>k</sub>, &theta;<sub>k</sub>', '라인 사이클 실효값을 적분하는 5점 Simpson 법의 가중치와 샘플 점'),
    ]
    s.extend(tbl('기호.', [['기호', '뜻']] + [list(r) for r in _SYM],
             widths=[CW * 0.26, CW * 0.74], split=True))

    # =============================================================== 9
    add(h1('참고문헌'))
    ext(bullets([
        'STMicroelectronics, <i>L6790A LLC-PFC controller</i>, preliminary '
        'datasheet, 2026년 4월 30일. <b>Draft.</b>',
        'STMicroelectronics, <i>EVL6790_670W</i> 평가 보드 회로도.',
        'Infineon Technologies, <i>LLC Converter Design Note</i>, AN 2013-03, '
        'V1.0, 2013년 3월.',
        'Infineon Technologies, <i>Resonant LLC converter: operation and '
        'design</i>, AN 2012-09, V1.0, 2012년 9월.',
        'onsemi (formerly Fairchild), <i>Half-bridge LLC resonant converter '
        'design using FSFR-series Fairchild power switch</i>, AN-4151.',
        'Monolithic Power Systems, <i>Understanding LLC operation</i>, '
        'part&nbsp;2.',
        'Toshiba Electronic Devices &amp; Storage, <i>Power factor '
        'correction (PFC) circuits</i>, application note.',
        'Toshiba Electronic Devices &amp; Storage, <i>Resonant circuits and '
        'soft switching</i>, application note, 2019년 11월 12일.',
        'ROHM Semiconductor, TechWeb, <i>LLC operating regions</i> '
        '(그림&nbsp;' + FR('f04_three_regions') + ' 의 영역 구분).',
        'W. Wenbo et al., <i>A single-stage 1.65 kW ac-dc LLC converter</i>, '
        'IEEE ECCE.',
        'onsemi, <i>The TL431 in the control of switching power supplies</i>, '
        'TND381-D (TL431 과 옵토커플러의 보상기 설계).',
        '[PI] Power Integrations, <i>If your power converter is not safe, '
        'you may have an expensive recall</i>, PSMA IS293, 2020 '
        '(IEC 62368-1 creepage·clearance 표, 고도 계수).',
        '[ATIS] M. Maytum, <i>IEC 62368-1 and pluggable mains powered '
        'equipment surge protection</i>, ATIS PEG, 2019 (상용전원 서지, '
        'Table 14 clearance).',
        '[TUV] TUV Rheinland, CB test report 60431427 001, IEC 62368-1, '
        'Class II AV/ICT 어댑터, 5000 m 평가.',
        '[UL] UL, CB test report E135803-A6002-CB-1, IEC 62368-1, '
        'Advanced Energy GB130Q, 5000 m 평가.',
        '[TI] Texas Instruments, <i>Demystifying clearance and creepage '
        'distance for high-voltage end equipment</i>, SLUP419, 2024.',
        '[GB] GB 4943.1-2022, <i>Audio/video, information and communication '
        'technology equipment &mdash; Part 1: Safety requirements</i> '
        '(서문과 적용 범위).',
        '[TIW] Furukawa Electric, <i>TEX-E triple-insulated wire, safety '
        'approvals</i>.',
        '[STO] STMicroelectronics, <i>STO60N045DM9, N-channel 600 V, '
        '35 m&Omega; typ., 56 A MDmesh DM9 Power MOSFET in a TO-LL '
        'package</i>, DS14711 Rev&nbsp;4, 2026년 6월.',
        '[L6498] STMicroelectronics, <i>L6498, high voltage high and '
        'low-side 2 A gate driver</i>, DocID030318 Rev&nbsp;3, 2017년 9월.',
        '[STL] STMicroelectronics, <i>STL160N10F8, N-channel 100 V, '
        '3.2 m&Omega; max., 158 A STripFET F8 Power MOSFET in a PowerFLAT '
        '5x6 package</i>, DS14249 Rev&nbsp;5, 2024년 7월.',
        '[TEA] NXP Semiconductors, <i>TEA2095TE, GreenChip dual synchronous '
        'rectifier controller</i>, product data sheet Rev.&nbsp;1.3, '
        '2025년 10월 20일.',
        '[FZT] Diodes Incorporated, <i>FZT651, NPN silicon planar medium '
        'power transistor</i>, DS33149 Rev.&nbsp;7-2, 2022년 3월(동박 '
        '25 &times; 25 와 50 &times; 50 mm 에서의 열저항).',
        '[1N4148W] Diodes Incorporated, <i>1N4148W, surface mount fast '
        'switching diode</i>, DS30086 Rev.&nbsp;31.',
        '[ES1J] Diodes Incorporated, <i>ES1A&ndash;ES1J, 1.0 A surface mount '
        'super-fast rectifier</i>, DS39406 Rev.&nbsp;2.',
        '[BZT] Nexperia, <i>BZT52H series, 375 mW Zener diodes in SOD123F</i>, '
        'product data sheet.',
        '[TL431] Texas Instruments, <i>TL431 / TL432 precision programmable '
        'reference</i>, SLVS543(등급, 캐소드 전류, 안정성 값).',
        '[SFH] Vishay Semiconductors, <i>SFH617A, optocoupler, phototransistor '
        'output, with base connection</i>, data sheet(CTR 랭크).']))

    # =============================================================== 10
    add(h1('정오표와 미결 항목'))
    add(p('여기 적은 항목은 해결된 것이 아니라 임시로 처리한 것이고, 대부분은 정식 '
          '데이터시트나 시제품만이 확정할 수 있다. 양산 전에 다시 읽을 것.'))
    add(h2('데이터시트: 초안은 앞뒤가 안 맞는다'))
    ext(tbl('초안 데이터시트가 스스로 모순되거나 값을 비워 둔 곳. 전부 정식 '
            '문서로 다시 확인해야 한다.',
            [['항목', '초안이 말하는 것', '여기서 쓴 것, 그리고 이유'],
             ['오실레이터 idle 시간 T<sub>idle</sub>',
              '5.3.2 절의 주파수 식은 700 ns, 같은 절의 C<sub>T,max</sub> 식은 '
              '350 ns 를 뜻한다. 표 2(권장 동작 범위)를 역산하면 약 250 ns',
              '<b>%(Tidle).0f ns.</b> 250 ns 에서는 두 클램프가 동작 범위를 감싼다. %(t7)s. 그러므로 추정이 아니라 측정해야 할 값' % dict(V, t7=_idle700_kr(V))],
             ['브라운아웃 식',
              'V<sub>BO</sub> = min(60 V, R<sub>CFG</sub>&middot;4 V/k&Omega;) '
              '&mdash; 글자 그대로 읽으면 어느 저항에서나 60 V 라 구성표와 '
              '모순',
              '15 k&Omega; 을 하한으로 하는 R<sub>CFG</sub>&middot;4 V/k&Omega; '
              '으로 읽는다. 표와 일치하는 유일한 해석'],
             ['브라운아웃 단위',
              'threshold 는 <i>피크</i> 전압인데 보드 노트와 설계 툴은 실효값을 '
              '적는다',
              '비교하는 곳마다 명시적으로 변환(&radic;2 = 1.414)'],
             ['열저항', 'TBD',
              '데이터시트만으로는 junction 온도를 예측할 수 없다. 손실 budget 은 대신 '
              '실측 온도 상승으로 검사'],
             ['ZCD 절대 최대', '하한이 TBD',
              '분압기는 OVP threshold 만으로 정한다'],
             ['5.3.1 절의 드라이버 이름',
              '한 문장에서 LOUT1 과 LOUT2 가 블록도·구성표와 뒤바뀌어 있다',
              '블록도와 표를 따른다: 하프브리지에서 high 로 고정되는 핀이 LOUT2 다'],
             ['timeout 뒤의 기동 회로',
              'V<sub>CC,HVSUon</sub> = 12 V 아래에서 충전 전류가 켜지고, 발생기는 '
              'V<sub>CCon</sub> 뒤 120 ms 에 멈춘다. 그 뒤 12 V 아래로 내려가면 충전 '
              '전류가 다시 켜지는지는 적혀 있지 않다',
              'V<sub>CC,reg</sub> 범위의 아래쪽 끝을 12 V 위에 두므로, 정상 동작 '
              '전원은 그 답에 기대지 않는다']],
            widths=[CW * 0.22, CW * 0.40, CW * 0.38], split=True))
    add(h2('설계 시트를 단순하게 만들 때 빠지기 쉬운 함정'))
    add(p('설계 시트를 단순하게 만들면 그럴듯하지만 틀린 값이 나오고, 시트가 경고하지도 않는 곳.'))
    ext(tbl('그럴듯하지만 틀린 값을 만드는 함정.',
            [['항목', '함정', '결과'],
             ['등가 입력 범위',
              '최대를 풀브리지 모핑 경계가 아니라 AC 최대 전압에서 잡는 것',
              '주파수 코너를 아예 평가하지 않는다. 여기서는 등가 %(Vacmax).0f '
              'Vac 와 %(Veqhi).1f Vac 의 차이이고, &lambda; 도 함께 정한다' % V],
             ['최소 게인 조건의 &lambda;',
              '같은 코너 조건을 앞 단계에서 한 번 더 적용하는 것',
              '요구 &lambda; 가 터무니없이 작게 나오고(한 경우 100배 넘게), '
              'L<sub>m</sub> 은 그만큼 터무니없이 크게 나온다'],
             ['라인 사이클 실효 전류',
              '위상 하나, 보통 &theta; = &pi;/4 만 평가하고 라인 사이클 값이라 '
              '부르는 것',
              '출력 뱅크 리플 전류와 정류기 손실을 둘 다 작게 본다. 반주기에 '
              '걸친 Simpson 법은 계산 부담이 없고 충분히 정확하다'],
             ['above 의 2차 실효값',
              '전류가 잘렸는데 잘리지 않은 사인 반파로 계산하는 것',
              '높은 코너에서 최대 8 %. below 에서는 계수가 정확히 1 이라 오류가 오래 드러나지 않을 수 있다'],
             ['1차 소자 정격',
              '반사 부하 전류 I<sub>trafo,pk</sub> 로 정격을 잡는 것',
              '약 %.0f %% 부족 &mdash; 스위치는 <i>합성</i> 탱크 전류를 흘린다' % (100 * (V['Icomp'] / V['Itr'] - 1))],
             ['손실과 열저항',
              '25 &deg;C R<sub>DS(on)</sub> 으로 손실을 계산하고 125 &deg;C 를 '
              '지키는 히트싱크를 요구하는 것',
              '요구 열저항이 실제 필요한 값보다 두 배 가까이 느슨하게 나온다'],
             ['ZVS 검사',
              '설계 Q 와 설계 &lambda; 로 닫힌 식 근사를 쓰는 것',
              '수십 %% 오차이고 부호를 정해 주는 것이 없다. 이 탱크에서는 %(pc).0f %% 보수적. '
              '낙관적인 쪽이 위험한 쪽'
              % dict(pc=abs(V['TzcCFpc']))],
             ['선정값 대 계산값',
              '보드에는 선정값이 실렸는데 검사가 계산값을 읽는 것',
              '이후의 모든 여유가 실제로 만들지 않은 설계를 기준으로 계산된다']],
            widths=[CW * 0.20, CW * 0.38, CW * 0.42], split=True))
    add(h2('근거 없이 쓰인 상수'))
    _TPM = A.SH['t.PM']
    _PMT = __import__('math').degrees(__import__('math').atan(_TPM))
    ext(bullets([
        '&lambda; 조건의 데드타임 형에 있는 <b>&pi;&sup2;/8</b>. 사각파의 '
        '기본파 성분 보정처럼 보이지만 출처가 없다. 참고값이고, 실제 판정은 ZVS 스윕으로 한다.',
        'ZVS 닫힌 식 근사의 <b>지수 5</b>. 피팅한 숫자이고, 근사가 경계 근처에서 '
        '예측할 수 없게 틀리는 주된 이유다.',
        '보상기 설계의 입력 전압 여유 계수에 있는 <b>0.744</b>. crossover 주파수 '
        '목표에 비례 계수로 들어갈 뿐이고, 결과가 % 단위로 달라지는 곳은 없다.',
        '<b>K<sub>v</sub> 식</b>(식&nbsp;%(e)s)은 ST 툴의 식을 그대로 옮긴 것이다. '
        '&alpha;<sub>v</sub> = 1 이면 %(pm).0f&deg; 목표에서 %(k1j)s 나와, '
        'Venable 의 tan(45&deg; + &Phi;<sub>M</sub>/2) = %(kvj)s 다르다. 툴은 '
        '&alpha;<sub>v</sub> 가 무엇의 가중치인지 밝히지 않는다. 그래서 phase '
        'margin 은 K<sub>v</sub> 가 아니라 실장 부품으로(식&nbsp;%(m)s) 계산한다.'
        % dict(e=ER('Kv'), m=ER('PMeq'), pm=_PMT,
               k1j=_nj('%.3f' % ((2 * _TPM + ((1 + _TPM) ** 2 + 4) ** 0.5) / 2),
                       '이', '가'),
               kvj=_nj('%.3f' % __import__('math').tan(
                   __import__('math').radians(45 + _PMT / 2)), '과', '와')),
        '최대 전력 상수 <b>16.8 &Omega;&middot;W</b> 는 피드백 폭과 '
        'multiplier 게인에서 나온다(2.8&nbsp;V / 0.167). 여기 적는 것은 그 '
        '게인이 초안값이기 때문이다.',
        '<b>게이트 드라이버 출력 저항</b>은 15&nbsp;V 를 전 온도 최소 단락 '
        '전류로 나눈 값이다. L6498 데이터시트는 출력 저항을 주지 않는다. 실제 '
        '출력은 저항이 아니고, 이 선택은 게이트 전력의 큰 몫을 드라이버에 '
        '둔다.']))
    add(h2('이 설계의 미결 항목'))
    ext(tbl('미결 항목과 확정 방법.',
            [['항목', '상태', '확정 방법'],
             ['T<sub>idle</sub>', '값 셋, 250 · 350 · 700 ns',
              '첫 보드에서 f<sub>sw</sub>(&theta;) 측정'],
             ['1차 도통 손실',
              'budget 대비 %(kPloss).3f &mdash; <b>미달, 그리고 수용</b>' % V,
              '고정 소자 위치에서 %.0f W budget 을 만족하는 단일 600 V 소자는 없다. '
              '보드 동박만으로는 %.0f&nbsp;&deg;C 오르므로, %.0f&nbsp;&deg;C 주위에서 '
              '케이스-주위 %.1f&nbsp;&deg;C/W 이하의 히트싱크가 필요하다(%s 절). '
              '나머지는 열 측정'
              % (_kb, A.SH['ΔT.pcb'], V['Tamb'], A.SH['R.thCA_max'],
                 SR('1차 스위치: STO60N045DM9'))],
             ['2차 손실 budget',
              '%(kPSR).3f &mdash; 여유가 거의 없다' % V,
              '레그당 소자 하나 더 병렬이면 회복된다. 실측 온도를 보고 결정한다'],
             (['트랜스포머 인덕턴스 공차',
               '탱크는 Open 인덕턴스 %(Ldrop).1f %% 하락까지 견디므로 흔한 '
               '&plusmn;10 %% 가 들어간다' % V,
               'R<sub>T</sub> 는 첫 보드까지 %(RT)g k&Omega; 으로 둔다. '
               'R<sub>T</sub> 를 높이면 영교차 dead zone 이 좁아지지만 이 여유를 '
               '쓴다. f<sub>sw</sub>(&theta;) 와 90·230 Vac 의 입력 전류 THD 를 '
               '재고 정한다' % V] if V['Ldrop'] >= 10.0 else
              ['트랜스포머 인덕턴스 공차',
               '탱크는 Open 인덕턴스 %(Ldrop).1f %% 하락까지 견디는데 흔한 사양은 '
               '&plusmn;10 %% 를 요구한다' % V,
               'R<sub>T</sub> 는 첫 보드까지 %(RT)g k&Omega; 으로 둔다. '
               'R<sub>T</sub> 를 낮추면 &plusmn;10 %% 를 덮지만 영교차 dead zone '
               '이 넓어지므로, f<sub>sw</sub>(&theta;) 와 90·230 Vac 의 입력 '
               '전류 THD 를 재고 정한다' % V]),
             ['출력 뱅크 부피와 높이',
              '%(Cout).1f mF, %(nC).0f 개' % V,
              '전기가 아니라 기구 문제이고, 출력 전압 선정까지 되돌아가게 할 수 있다'],
             ['대기 전력', '버스트 진입을 %(PinBM).0f W 로 가정' % V,
              '측정하고, R<sub>BM</sub> 을 피드백 리플과 절충해 정한다'],
             ['효율 가정',
              '&eta;<sub>HB</sub> = %(etaHB).0f %% 가정' % V,
              '낙관적이다. 95 %% 로 잡으면 R<sub>CS</sub> 와 R<sub>ac</sub> 가 약 %.0f %% '
              '움직일 뿐 이후 계산에 크게 영향을 주는 것은 없다 &mdash; 그래도 실측값으로 바꿔야 한다' % (100 * (V['etaHB'] / 95.0 - 1))],
             ['SR MOSFET 게이트 전하',
              'typical 값뿐: STL160N10F8 의 Q<sub>g,sync</sub> 와 Fig.&nbsp;8 '
              '기울기',
              'Full load 에서 SR 전원 전류를 잰다. 팔로워는 소자당 %.1f&nbsp;nC '
              '까지 허용한다. 게이트 핀당 둘이 SR 스위칭 시간을 정한다'
              % A.SH['Q.g_SR_max']],
             ['부트스트랩 다이오드',
              'ES1J, V<sub>F</sub> = %(VFbs).2f V, 데이터시트의 1 A 최대값' % V,
              '시제품에서 충전 전류와 전압 강하를 잰다. V<sub>CC,floor</sub> 와 '
              'C<sub>VCC</sub> 가 그 전압 강하를 따라간다'],
             ['게이트 턴오프 다이오드',
              '1N4148W: 피크 %.2f A, 1 &micro;s 비반복 서지 정격 %.0f A 에 대해 '
              'k = %.2f. 데이터시트에 반복 피크 정격은 없다'
              % (A.SH['I.Goff_pk'], A._builder_const('I.FSM_Goff'),
                 A.SH['k.Goff_D']),
              '게이트 전류와 다이오드 온도를 잰다. 같은 footprint 의 1 A '
              'Schottky 가 대안이다'],
             ['패스 트랜지스터',
              'FZT651: 2 oz 동박 50 &times; 50 mm 에서 허용 주위 온도 '
              '%.0f &deg;C(Q<sub>VCC</sub>), %.0f &deg;C(Q<sub>SR</sub>). '
              'h<sub>FE</sub> &ge; 70 은 표에서 읽은 값이고 시험 전류가 '
              'I<sub>VCC</sub> 와 다르다'
              % (A.SH['T.aQVCC'], A.SH['T.aQSR']),
              '실제 동박에서 탭 온도를, I<sub>VCC</sub> 에서 베이스 전류를 잰다'],
             ['SR 게이트 저항',
              'ST 보드처럼 %.0f &Omega; 자리' % A._builder_const('R.G_SR'),
              '시제품의 SR 게이트 링잉을 보고 몇 &Omega; 을 넣을지 정한다'],
             ['옵토커플러 CTR',
              'CTR<sub>s</sub> %.2f, CTR<sub>m</sub> %.2f 는 SFH617A-2 에 대한 '
              '설계 선택값' % (V['CTRs'], V['CTRm']),
              '쓰는 LED 전류에서 랭크의 곡선을 읽고, 랭크 양 끝에서 '
              'R<sub>B</sub> 허용 범위와 crossover 주파수를 다시 검사한다'],
             ['게이트에 남는 데드타임',
              '(t<sub>D</sub> &minus; MT)/T<sub>T</sub> = %.3f. L<sub>r</sub> '
              '&asymp; %.1f &micro;H 에서 1'
              % (A.SH['k.TTd'], _ttd_lr_edge(V, A)),
              '첫 샘플에서 L<sub>r</sub> 을, 시제품에서 게이트-중점 타이밍을 '
              '잰다. L<sub>r</sub> 이 낮게 나오면 t<sub>D</sub> 를 올린다'],
             ['공진 위의 중점 기울기',
              'I<sub>Lm,pk</sub> 에서 %.1f V/ns. 스위칭되는 전류는 더 클 수 있다'
              % A.SH['dv.dt'],
              'OUT 핀의 dv/dt 를 드라이버의 %(dvmax).0f V/ns 에 대해 잰다' % V],
             ['SR 방전 기능과 버스트',
              '정류 동작이 1.1 ~ 1.7 s 없으면 동작',
              'No load 의 가장 긴 burst-off 시간을 잰다. 더 긴 휴지는 대기 '
              '전력에 0.4 W 를 더한다'],
             ['기동 인계',
              't<sub>hand</sub> %.1f ms 는 레일이 올라올 때까지 부하가 없다고 가정'
              % A.SH['t.hand'],
              '실제 부하 순서로 cold start 하며 V<sub>CC</sub> 와 기동 회로 온도를 잰다'],
             ['트랜스포머 작업 전압',
              '%.0f V rms 추정. creepage 는 %d V 행'
              % (_INS.req()['u_rms'], _INS.req()['row']),
              '인증 기관이 첫 샘플에서 잰다'],
             ['규격 원문에서 읽지 않은 절연 값',
              '세미나 자료와 인증 성적서에서 가져옴(%s 절)'
              % SR('이 트랜스포머의 안전 절연'),
              '인증서가 인용할 판으로 인증 기관과 확인: 내전압, 고주파 clearance '
              '표, 양산 시험'],
             ['TIW 인증',
              '%d kHz, Class %s; f<sub>SU</sub> %.0f kHz'
              % (_INS.TIW_FMAX / 1e3, _INS.TIW_CLASS, A.SH['f.SU']),
              '쓰는 전선 크기에 대한 인증을 확인하고, 권선을 130 &deg;C 아래로 '
              '유지한다'],
             ['반쪽마다의 누설',
              'NS2 만 %.2f, NS3 만 %.2f &micro;H(칸막이 %.2f mm, k<sub>w</sub> = '
              '%.2f, 자계 풀이 추정). 뒤판 몫의 극단에서 %.2f&ndash;%.2f'
              % (_h2, _h3, _w['sep'], _w['k_wind'], _h2a, _h3a),
              '첫 샘플에서 두 반쪽을 재고, 그 값으로 탱크와 R<sub>T</sub> 를 '
              '판정한다. 칸막이를 얇게 하면 값이 내려간다. %.1f mm 보다 두껍게 '
              '하지는 않는다' % _w['sep']],
             ['누설, 두 반쪽 모두 Short',
              '추정 %.2f &micro;H, 빈틈없이 감으면 %.2f' % (_ef, _et),
              '샘플에서 기록만 한다. 탱크가 보는 값이 아니다'],
             ['권선 피치 k<sub>w</sub>',
              '%.2f, 가정' % _w['k_wind'],
              '첫 샘플의 권선 구성을 잰다. 공차 끝에서 권선과 다리 원호 사이는 '
              '%.2f mm' % _w['clear_min']],
             ['코일 포머의 칸막이',
              '카탈로그 %s(한 칸, 핀 %d 개)에 %.1f mm 추가'
              % (_R['former'], _CORE.BOBBIN['pins'], _w['sep']),
              '보빈 제조사가 칸막이를 코일 포머에 성형할 수 있는지, 핀 주변 거리를 '
              '확인한다'],
             ['2차 핀',
              '&oslash;%s 핀 하나에 라인 사이클 실효값 %.1f A'
              % (_CORE.BOBBIN['pin'].split()[-2], V['Idio']),
              '보빈 제조사가 핀 정격을 준다. 안 되면 2차 끝을 보드로 바로 뽑는다'],
             ['중앙다리 갭',
              '한 군데, 약 %.2f mm(자계 풀이. 프린징을 빼면 %.2f mm)' % (_gl, _g0),
              'NP1 첫 층이 갭에서 %.2f mm 떨어져 있다: 그 근처의 권선 온도를 잰다'
              % _wall],
             ['코어 손실',
              '%s, %.0f mT, f<sub>r</sub>: 계산하지 않음. 카탈로그 값은 %.0f kHz, '
              '%.0f mT, %.0f &deg;C 에서 최대 %.2f W'
              % (_R['material'], _CORE.flux(V, _R['Ae']), _pc[1], _pc[2],
                 _pc[3], _pc[0]),
              '%s 재료 곡선을 코어 온도에서 읽고(100 &deg;C 아래에서는 손실이 '
              '오른다) 실측한다' % _R['material']],
             ['Litz 의 AC 손실',
              'DC %.1f W 에 누설 자계로 %.1f ~ %.1f W, 1차 근사, 소선 '
              '&oslash;%.2f mm'
              % (_pdc, _pa['P_pri'] + _pa['P_sec'], _pb['P_pri'] + _pb['P_sec'],
                 _CORE.D_STRAND),
              '권선 온도를 잰다. 대책은 더 가는 소선(손실은 d<sub>s</sub>&sup2; 에 '
              '비례)이고, 점적률은 벤더 값'],
             ['전선 크기',
              'NP1 삼중 절연 Litz &oslash;%.1f mm(%d &times; &oslash;%.2f, 절연 '
              '%.1f mm 가정). NS2, NS3 Litz &oslash;%.1f mm(%d &times; '
              '&oslash;%.2f)'
              % (_w['d_pri'], _w['n_strand'], _CORE.D_STRAND, _w['tiw_add'],
                 _w['d_sec'], _w['n_strand_s'], _CORE.D_STRAND),
              '전선 벤더가 크기, 절연, 인증을 확인하고, &oslash;%.1f mm Litz 를 '
              '&oslash;%.1f mm 튜브에 감을 때의 굽힘도 확인한다'
              % (_w['d_sec'], _M['tube_od'])]],
            widths=[CW * 0.22, CW * 0.34, CW * 0.44], key='openitems',
            split=True))
    add(note('<b>이 문서의 모든 대조는 일관성 검사이지 정확성 검증이 아니다.</b> 세 가지 구현이 일치한다는 것은 같은 식을 구현했다는 뜻이지, 그 식이 '
             '하드웨어를 기술한다는 뜻이 아니다. 정확성 검증은 첫 시제품으로 한다.'))

    return s


# ZVS 스윕과 그 결과 사전은 영문판과 한 벌이다 - 숫자를 두 번 계산하지 않는다.
from an_body import (ZVS_WORST, _zvs_grid, _minus, _f_idle, _where,     # noqa: E402
                     _ttd_lr_edge)


def _idle700_kr(V):
    """T_idle 이 700 ns 일 때 두 클램프가 어떻게 되는지 - 숫자를 보고 문장을
    고른다(영문판 _idle700_text 와 같은 판정)."""
    fmin, fmax = _f_idle(V, 700.0)
    if fmin < V['fo'] or fmax < V['fswmaxop']:
        return '700 ns 이면 두 클램프가 더는 동작 범위를 감싸지 못한다'
    return ('700 ns 에서도 감싸지만 하한 여유가 %s 줄어든다'
            % _nj('%.3f' % (fmin / V['fo']), '으로', '로'))


def _thinnest_kr(V, A):
    """통과한 판정 여유 중 가장 작은 것을, 그 행의 이름으로."""
    rows = [('스윕 최악점의 ZVS', ZVS_WORST['zk']),
            ('오실레이터 하한', V['kfloor']),
            ('오실레이터 상한', V['kceil']),
            ('과전류 threshold', V['kOCP']),
            ('hold-up', V['khold']),
            ('정류 레그당 2차 손실', V['kPSR']),
            ('기동 threshold 위의 V<sub>CC</sub>', A.SH['k.VCClo']),
            ('제너 공급', A.SH['k.RBZ']),
            ('기동 인계의 C<sub>VCC</sub>', A.SH['k.CVCC']),
            ('하이사이드 드라이버 전원', A.SH['k.VBO']),
            ('게이트에 남는 데드타임', A.SH['k.TTd']),
            ('중점 기울기', A.SH['k.dvdt']),
            ('게이트 드라이버 손실', A.SH['k.Pdrv']),
            ('SR 게이트 구동', A.SH['k.VGSR'])]
    name, k = min(((n, k) for n, k in rows if k > 1.0), key=lambda r: r[1])
    return ('통과한 여유 중 가장 작은 것은 %s, k = %s.'
            % (name, _nj('%.3f' % k, '이다', '다').replace(' 이다', '이다')
               .replace(' 다', '다')))
