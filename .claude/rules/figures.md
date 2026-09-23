---
paths:
  - "Design Guide/generators/figs*.py"
  - "Design Guide/generators/schem*.py"
  - "Design Guide/generators/figcheck.py"
  - "Design Guide/generators/figedit.py"
  - "Design Guide/generators/figtrim.py"
  - "Design Guide/generators/pdffig.py"
  - "Design Guide/generators/cores.py"
  - "Design Guide/figures/**"
---
# 그림을 그리거나 고칠 때

- **수치는 전부 `l6790.py` 에서 온다.** 그림 코드에 설계값을 박지 않는다.
- **그림을 고쳤으면 `figcheck.py` 를 돌린다.** 글·선 겹침은 픽셀로 재고(바닥 10 px), 배선 5종(`no-dot` · `open-end` ·
  `crossing` · `off-grid` · `stray-dot`)과 `wrong-panel` · `off-page` · `tiny` 를 본다. 지금 0건이고 0건을 유지한다.
  검사 대상은 `figs.finish(fig)` 뒤의 그림이다. `--crops DIR` 로 겹친 곳의 확대 조각을 저장할 수 있다.
- **접점 점은 세 가닥 이상이 만나는 곳에만.** 모서리에는 찍지 않는다. 일부러 안 찍는 자리는 `schemx.nodot()` 으로
  선언한다(검사기가 보고하되 세지 않는다) — 검사를 느슨하게 하지 말 것.
- **기호는 자기 그림 폭에 비례한다**(`schemx.scale`, `REF_SPAN` 22.45 에 `REF_FIGSPAN` 46.0 바닥). 권선은 턴 반경을 고정하고
  턴 수를 높이에서 뽑는다. 극성점은 리드선 바깥쪽 첫 턴 높이. 바디 다이오드만 0.26(기생 소자), 회로 다이오드는 0.52/0.56.
  **`subplots_adjust` 는 그리기 전에** 부른다(바닥 규칙이 축의 명목 위치를 읽는다).
  `X.xfmr` 의 `gap` 은 *요청*이고 실제 단자는 반환값에서 읽는다 — `x ± gap` 을 가정하지 않는다.
- **글꼴은 본문과 같은 Liberation Sans**, mathtext 도 `fontset=custom` 으로 같은 활자. 한글 폰트는 폴백 목록 **뒤**에.
- **`--plain` 은 제목 없는 판을 `figures/an/` 에 쓴다**(AN 용). `figures/` 와 `figures/an/` 은 같은 집합이 아니다 —
  `figedit.mirror()` 는 자기가 쓴 파일만 민다. 전부 복사하면 AN 이 제목 붙은 판을 읽는다(실제로 13장을 그렇게 덮었다).
- **한글 글꼴이 없는 PC 에서 한글 그림은 건너뛴다**(`_hangul_guard`, exit 2) — 네모로 그려진 파일이 좋은 PNG 를 덮어쓴다.
  이 컨테이너에는 NanumGothic · WenQuanYi 가 있다. 한국어 그림은 WQY 로(`KR_FIGS`).
- **`figedit` 는 그림이 주장하는 바를 바꾸지 않는다.** 유일한 예외가 `fix_freewheel_2nd_half()` 이고 사유가 함수에 있다.
  `_font()` 는 Arial 이 없으면 Liberation Sans, 그것도 없으면 예외 — 비트맵 기본 서체로 떨어지지 않는다.
- 참조 PDF 에서 잘라 온 그림은 `figtrim.py` 로 원문 캡션 조각을 확인한다. **AN 의 그림은 ST 설계 스프레드시트에서 가져온
  도면 세 장(`bom_power_stage` · `bom_pin_config` · `comp_network_st`)을 빼면 전부 우리가 그린 것이다** — 그 세 장은
  캡션과 앞붙이에 출처를 적었다(50차). 가져온 그림을 더하면 캡션과 앞붙이 문장을 같이 고칠 것.
- 코어 기하는 `cores.py` 한 곳(`CORES` 전자기 값 · `MECH` 치수 · `PINMAP` 핀 배정 · `winding()`), 그림·표·벤더 사양서가 같이 읽는다.
  `J_CU` · `K_U` · `K_LITZ` · `T_FOIL` · `MARGIN` 다섯이 가정이다. **핀 번호 방향은 가정**이라 도면으로 확인할 것.
