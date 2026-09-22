---
paths:
  - "Smath/**"
  - "Design Guide/generators/smsheet.py"
  - "Design Guide/generators/smgen.py"
  - "Design Guide/generators/build_*.py"
  - "Design Guide/generators/zed*.py"
  - "Design Guide/generators/harvest_pane.py"
  - "Design Guide/generators/check_sm.py"
  - "Design Guide/generators/check_theta.py"
  - "Design Guide/generators/audit_sm.py"
  - "Design Guide/generators/audit_rpn.py"
  - "Design Guide/generators/audit_dim.py"
  - "Design Guide/generators/smresult.py"
  - "Design Guide/generators/snapshot.py"
---
# SMath `.sm` 을 만들거나 고칠 때의 함정

**전부 실제로 한 번씩 겪은 것이다.** 발견 경위와 증거는 `HISTORY.md` 시트 §6.
빌드 후에는 반드시 `check_sm.py` (VERDICT OK) 와 `bom_compare.py` (different: 0) 를 돌린다.
**정본은 빌더다** — SMath 가 저장한 파일을 고쳐 쓰지 말고, 바뀐 것을 빌더에 역이식해 재빌드한다.
판 글자(제목·범례·축이름)에 계산값을 넣지 않는다 — 판은 정적 바이트라 F9 로 안 바뀐다.
벡터 원소 대입(`el(...) :=`) 안에 단위를 넣지 않는다 — 그 자리에서 오류가 난다.
`N.fs` 는 짝수로 유지한다(홀수면 스윕 한가운데서 0 으로 나눈다). 한 판의 최대 높이는 952 px.

**A. 계산이 조용히 틀리는 것**

1. **표시 괄호는 자동 생성되지 않는다.** 부분식 RPN 뒤에 `<e type="bracket">(</e>`.
   없으면 계산은 맞는데 인쇄물이 다르게 보인다.
2. **저항 단위는 소문자 `ohm`.** 대문자 `Ohm`은 독립 차원이 되어 `W + Ohm*A²`가 error 74.
3. **단위 붙은 값에 `abs()` 금지.** 태그가 남아 나중에 `ln`·비정수 거듭제곱이
   "Operation cannot be performed with units"로 죽는다. **값은 정상 표시되므로 증상이 없다.**
   순수 숫자로 계산 후 단위를 다시 붙일 것.
4. `ln` · `exp` · `atan` · 변수 지수의 인자는 **명시적 무단위화** — `(Vo/'V)/(Vin/'V)`.
5. **역탄젠트는 `atan`.** `arctan`은 없다.
6. 표시 리전에 **`<result action="numeric">`** 이 없으면 값이 안 나온다.

**B. 파일이 아예 안 열리는 것**

7. **리전은 `<regions type="content">` 안에** 넣는다. `<worksheet>` 바로 아래면
   NullReferenceException.
8. **`<dependencies>`에 사용한 리전 타입의 어셈블리를 전부 선언한다** — `SMath Core`,
   `MathRegion`, `TextRegion`, `PictureRegion`, `SpecialFunctions`,
   `PlotRegion`(`c451c2b5-798b-4f08-b9ec-b90963d1ddaa`),
   `AreaRegion`(`4974b228-4974-44cf-8274-bf2936b4a766`).
   GUID는 `Reference/EVLHV101SSR50W Design Guide.sm`에서 복사한다 —
   **다만 버전은 거기서 가져오지 말 것.** 그 파일은 ST 것이고 Solver 1.3.0.9126 /
   어셈블리 1.73.9126.0 인데, 여기 깔린 SMath 는 **Solver 1.5.0.9678 / 1.75.9678.0**
   이다(TI 앱노트 시트, 그리고 SMath 가 다시 저장한 우리 시트에서 읽었다).
   2026-09-08 에 빌더를 설치본에 맞췄다. 옛 버전을 적어도 열리기는 한다
   (`MyBode.sm` 은 1.2.9018 이고 잘 그려진다) — 그래도 안 깔린 버전을 적을 이유는 없다.
   `<metadata>`에는 `<author>`만 둔다.

**C. 쓸 수 있는 함수가 제한적이다**

9. **`sqrt · abs · ln · exp · atan · cos · sin`** 뿐이다.
   `min()` · `max()` · `if()` · `acos()` · `tan()`은 "정의되지 않은 함수입니다"로 거부된다.

   | 없는 것 | 대체식 | 오차 |
   | :--- | :--- | ---: |
   | `min(a,b)` | `(a+b−abs(a−b))/2` | 엄밀 |
   | `max(a,b)` | `(a+b+abs(a−b))/2` | 엄밀 |
   | `acos(z)` | `2·atan(sqrt(1−z²)/(1+z))` | 4.4e-16 |
   | `tan(x)` | `sin(x)/cos(x)` | 1.8e-15 |

   **단위가 붙은 값의 min/max는 단위를 나눠 빼고 다시 곱한다** — `(a+b−abs(a/'V−b/'V)*'V)/2`.
   그래프에는 **`for` · `range` · `line` · `el`** 4개가 추가로 필요하다.

   **가드가 있다.** `smsheet.py`의 `SAFE_FUNCS`/`PROG_FUNCS`와 `check_funcs()`가 파일을 쓰기
   전에 모든 수식을 파싱해 허용 밖 함수가 있으면 예외를 던진다. 이 실수는 다시 나올 수 없다.

10. **Cardano 근 선택에 min/max가 아예 필요 없다.** 물리적 근은 **항상 k = 1 분기**
    `w·cos(ang − 2π/3) − a₂/3` 이다 (6,089건 전수 확인).

**D. 레이아웃 — 겹침의 원인 전부**

11. **입력 셀은 대입식만 쓴다.** `V.AC_min := 90 V` 로 끝내고 `<contract>`·`<result>` 에코를
    붙이지 않는다. 계산 결과 행에는 당연히 `<result>`가 필요하다.
12. **리전 높이를 "슬래시 개수"로 추정하면 안 된다 — 수식 트리로 잰다.**
    `smsheet.py`의 `_rh()`/`_rwid()`/`est_box()`. 기준: `LINE_PX 13.5`, `CHAR_PX 5.2`.
13. **텍스트 줄바꿈을 SMath에 맡기면 안 된다.** TextRegion은 폭에 안 맞는 `<p>`를 말없이 다시
    줄바꿈하고, 늘어난 줄이 다음 리전 위에 찍힌다. `_wrap()`이 직접 나눈다.
    글자폭 상수 **`CH_PER_PX = 0.67`** (PDF 실측 0.58에 15 % 여유).
14. **텍스트 리전 높이는 실측표를 쓴다** — 첫 줄 ≈ 1.4·size + 8.7, 이후 한 줄당 ≈ size + 19.
    `Sheet.text_h()`.
15. **SMath는 저장할 때 텍스트 리전을 내용 크기로 다시 맞춘다.** 그래서 **좌측 라벨은 무조건
    한 줄**이어야 한다. `_label(nowrap=True)`가 두 줄이 되려 하면 **빌드를 실패시킨다.**
16. **그래프에는 로그 축도 자동 스케일도 없다.** x축에 `log10(f/Hz)`를 넣고 눈금은 글로 적는다.
    `20·log10(x)`는 `20·ln(x)/ln(10)`으로 쓴다. `scale_*`가 창을 고정하고 **창 밖 데이터는 빈
    그래프로 보인다.** `Sheet.plot_view(w,h,x0,x1,y0,y1)`가 계산해 준다
    (격자 한 칸 20 px, `scale_*` = 칸당 단위수, `transpose_*` = −(창 중심 × px/단위)).
17. **그래프 리전은 프레임 아래에 변수 이름을 한 줄 더 그린다** — `PLOT_CAPTION = 24 px`.
18. **접기(`AreaRegion`)로 기계 부분을 숨긴다.** 여는 리전이 내용과 종료 리전을 **품는다.**
    현재 8곳. **중첩 금지** — 시트 §10은 안쪽 Cardano 접기를 `collapse=False`로 꺼서 depth 2 유지.
    접힌 리전도 절대 좌표를 그대로 가지므로 `check_sm.py`는 펼친 상태로 검사한다.
19. **`range(a,b,c)`의 셋째 인자는 증분이 아니라 *두 번째 값*이다** (Mathcad 방식).
    `line(s1,…,sN, N, 1)`은 `args = N+2`, `for(변수, range(…), 본문)`은 `args=3`.
26. **접힌 블록은 가로줄을 하나 그리고, 그 줄도 자리를 차지한다.** `area_end()` 가
    6 px 만 띄우던 탓에 **그 줄이 바로 아래 행을 관통**했다 — 13:22 인쇄물에서 열 군데,
    그중 20쪽은 노란 입력 `R.T := 11 kohm` 을 그어 놓아 **지운 숫자처럼 읽혔다.** 노란 셀은
    사람이 고치는 자리이므로 가장 나쁜 자리다. 24 px 으로 올렸다(쪽수 42 → 43).
    **SMath 는 접힘·종료 리전에 `height` 를 안 적으므로(전부 `None`) 파일에서는 잴 수 없다** —
    인쇄물의 부족분이 6 px 이었다는 것만 근거이므로 다음 인쇄에서 확인할 것.
25. **SMath 로 저장하면 레이아웃이 무너진다 — 빌더가 잡은 여백은 저장 한 번을 못 견딘다.**
    2026-09-09 에 사용자가 열어 저장한 파일과 같은 빌드를 리전 1908개 전수 대조했다.
    **내용은 한 글자도 다르지 않은데** 좌표는 거의 전부 달라져 있었다 — top 1837개 ·
    left 1851개 · height 1849개. 크기 변화는 대부분 무해하지만(SMath 가 라벨을
    실제 한 줄 높이로 줄인다: 138 → 23 px) **±1~4 px 짜리 위치 흔들림이 아래로 누적**되고,
    여러 줄 주석의 높이 재측정이 ±100~350 px 계단을 만든다. 결과: 재빌드 직후
    **겹침 0 · 걸침 0** 이던 시트가 저장 한 번에 **겹침 3 · 걸침 14 · seam −30 px** 이 됐다.
    이건 사용자가 무엇을 잘못해서가 아니라 **저장 자체의 효과**다 — 손으로 끌어 옮긴
    것(그때는 접힘 헤더 4개와 판 2장)을 전부 제자리로 돌려 놓고 다시 재도 18건이 남았다.
    **그러므로 `.sm` 의 정본은 언제나 빌더이고, 인쇄는 저장 없이 한다**(시트 §9.3b).
    저장된 파일이 생기면 그것을 고쳐 쓰려 하지 말고 **무엇을 바꿨는지 확인해 빌더에
    역이식한 뒤 재빌드**한다.
20. **용지 설정은 `smsheet.py`의 `PAGE_W/PAGE_H/PAPER_ID`에 있다.** 사용자가 SMath에서 바꾼
    용지를 빌더에 반영해 두었으므로(A3 1654×1169, id 8) 재빌드해도 되돌아가지 않는다.
    그림 위치도 마찬가지로 빌더에 반영되어 있다 — **사용자가 SMath에서 손으로 옮긴 것은
    반드시 빌더에 역이식할 것.** 안 그러면 다음 재빌드에서 사라진다.

**E. `.sm`을 손으로 읽거나 쓸 때**

21. 단위는 `<e type="operand" style="unit">V</e>` 를 값과 `*` 로 결합한다.
    표시 단위는 `<input>`과 `<result>` 사이의 `<contract>` 블록이다.
22. **파싱 전에 base64 이미지를 지운다** — 안 그러면 XML 파서가 몇 MB를 문자열로 물고 늘어진다:
    `re.sub(r'<raw format="[^"]+" encoding="base64">.*?</raw>', '<raw/>', s, flags=re.S)`
23. 수식은 **RPN**이다. 중위로 덤프할 때 연산자 우선순위 괄호를 넣지 않으면 오독한다
    (`smgen.py`의 역변환이 참고가 된다).
24. **`<result>`는 표시 단위(contract) 값이다.** SI가 아니다.
