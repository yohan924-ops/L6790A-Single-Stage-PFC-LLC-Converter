---
paths:
  - "Design Guide/generators/an_*.py"
  - "Design Guide/generators/tx_*.py"
  - "Design Guide/*.pdf"
---
# Application Note (PDF) 를 고칠 때

- **손으로 적은 수치가 없다.** 전부 `an_pdf.V` 보간 · `eqref` · `calc` · `figs_pf.gain_points()` 같은 계산에서 온다.
  설계 수치는 **7장(설계 예제)에만** 싣고 2~6장은 기호와 IC 상수만. 설계점은 `an_pdf.AN_VARIANT` = `7p5to1_x1`.
- **교차 참조는 이름으로**(`figref/tblref/secref/eqref`, 2-pass). 번호를 손으로 적지 않는다. 안 풀리면 `check_refs()` 가 빌드를 실패시킨다.
- 수식마다 **문장 → `Equation N` → 가운데 수식 → 그것을 쓰는 문장**, 7장은 `eqagain` 으로 되부르고 바로 아래 대입 한 줄(AN4932 방식).
  **기호는 쓰기 전에 정의한다** — `an_symbols.py` 가 MISSING 0 · SILENT 를 보고한다. 빌드 뒤 `an_check.py` 와 함께 돌린다.
- `T()` 는 포맷 안 된 `%%` · `%(…)` 를 거부한다. 캡션에 dict 를 `%s` 로 넣지 말 것(`%(key)s`).
- **mathtext:** `\mathrm{}` 안의 빈칸은 사라진다 → `\mathrm{ripple\ decides}`. `\qquad` 뒤에 빈칸. `\bigl|` 은 없다(`\left|`).
- **본문 서체에 없는 글자:** Liberation Sans 에 U+2272(`≲`)가 없다 → `&le;`. NanumGothic 에 그리스 문자가 없어
  `an_pdf.T()` 가 `_wrap_missing()` 으로 Liberation Sans 에 넘긴다. 새 특수문자를 쓰면 `charToGlyph` 로 확인.
- 그림은 `figs.py --plain` 이 `figures/an/` 에 쓴 제목 없는 판을 읽는다. `FigBlock` 이 쪽 밑 빈 공간을 그림 하나로 메운다 —
  전역 축소는 답이 아니다. 캡션은 **그림의 출처가 아니라 논지의 출처**를 인용한다.
- **레이아웃 코드는 한 벌**(`an_pdf.py`) — 한국어판 `an_kr_pdf.py` · 트랜스포머 `tx_pdf.py` 는 `use_korean()` 과
  `TITLE/COVER/EQWORD/FIGWORD/TBLWORD` 만 바꾼다. 두 판의 본문은 절 단위로 같다(그림·표·수식 호출과 키가 같은 순서).
- **순서:** 영문판 먼저 → 사용자 확인 → 한국어판 이식. PDF 는 직접 전달(ZIP 아님).
- **한국어판 용어**(2026-09-17 사용자 지시): 용량성/유도성 → `capacitive`/`inductive` · 공진 아래/위 → `below`/`above` ·
  첨두 → 피크 · 승압/강압 → `boost`/`buck` · 이득 → 게인, 이득 여유 → `gain margin` · 왜형 → `distortion` ·
  완충기 → 버퍼 · 응력 → `stress`. 천이 · 실효 · 영교차 · 역회복 · 기자력은 그대로. **Q 는 품질계수.**
  **억지 한자어 금지**(2026-09-23 지시) — 현장에서 영어로 부르는 용어는 영어로: 개방/단락 → `Open`/`Short` · 극점/영점 → `pole`/`zero` · 문턱/임계 → `threshold` ·
  위상 여유 → `phase margin` · 교차 주파수 → `crossover 주파수` · 오차 증폭기 → `error amp` · 무/경/전/과부하 → `No/Light/Full load`/`Overload` ·
  표피 깊이 → `skin depth` · 감지 → `sense`/`sensing` · 예산 → `budget` · 명령 → 지령. 전체 목록은 `HISTORY.md` 40차. 영어 낱말 뒤 조사는 한국어 발음의 받침을 따른다.
  **현장 용어**(2026-09-23, 43차): 포일 → 동박 · Litz 가닥 → 소선 · 창 → 권선창 · 창 이용률 → 점적률 · 나란히 감은 권선 → 분할 권선 ·
  반사인파 → 정류 사인파/사인 반파 · 넘기다 → 환산하다 · 산포 → 편차. "만든 대로" 식 직역 제목·"이긴다"·"덮다"·"흔들다" 금지.
- 응용 특정 서술(패널 · TV · 세트)은 넣지 않는다. 의인화(lives / 사는 곳)도. 3분할은 선택지 한 절이지 뼈대가 아니다.
- **문장은 짧고 평이하게** (2026-09-22 사용자 지시 — "비원어민이 이해하기 힘든 단어나 문장구조"). 관용구 · 은유 · "worth doing once" 류의 서술자 개입 금지.
  **기본 개념은 설명하지 않는다** — 피크 전류 · 역회복 · 역률의 정의 같은 것은 독자가 안다. "Section X 가 그것을 다룬다" 식의 예고 문장은 지운다.
  **파란 박스(`note`)는 설계 결정을 바꾸는 경고에만** 쓴다 — 요약 · 예고 · 되풀이는 본문에 녹이거나 지운다. 다른 회사 AN(ST AN4932 · onsemi AN-4151)의 밀도가 기준이다.
