# L6790A 단일단 PF LLC — 25 V / 26.3 A TV(OLED) SMPS

ST **L6790A** 로 **단일단(Single-Stage) PF LLC** 를 설계한다. 90–264 Vac → **25 V / 26.3 A = 657.5 W**.
2단(Boost PFC + LLC)의 400 V 벌크 커패시터와 승압단을 없애고, 그 대가로 출력에 **75 mF 뱅크**가 붙는다.
설계 수치는 **닫혔다** — 시트 · 워크북 · `l6790.py` 세 곳이 일치하고 판정 지표 40개 중 34개 통과
(미달 6개의 사유는 `docs/DESIGN.md` §3). 남은 것은 문서 작업과 결정 두 개다(아래 "다음 할 일").

**응답은 한국어.** 모르는 것은 모른다고 하고, 근거 없는 값을 만들지 않는다. 추측으로 고치지 말고
진단 수단(프로브 · 검사기)을 먼저 심는다. 요청하지 않은 workflow · agent · deep-research 는 쓰지 않는다.

## 문서는 넷이고 답하는 질문이 다르다

| 파일 | 답하는 질문 | 언제 읽나 |
| :--- | :--- | :--- |
| **`CLAUDE.md`** (이 파일) | 무엇을 만들고, 지금 어디이고, 뭘 하면 되나 | 매 세션 자동 |
| **`docs/DESIGN.md`** | 설계 판단 · **현재 설계값(정본)** · 미확정 · 동작 원리 · 반복 실수 · 핀 규칙 | **설계 수치·설계 서술을 쓰거나 고치기 전에** |
| **`Design Guide/generators/README.md`** | 스크립트 50여 개가 각각 뭘 하나 · 표준 절차와 기대값 · 시트 구조 | 도구를 돌리기 전에 |
| **`docs/HISTORY.md`** | 왜 그렇게 정했나 — 근거 · 정오표 · 사고 기록 · 날짜별 타임라인 | 근거가 필요할 때 |

`.claude/rules/` 의 규칙 4개(`smath` · `xlsx` · `figures` · `an`)는 **해당 파일을 건드릴 때 로드**된다 —
`.sm` 과 `.xlsx` 를 깨뜨리는 함정 목록이 거기 있다. **경로 조건이 안 먹는 버전이면 항상 로드된다.**

## 세 설계가 떠다닌다 — 숫자를 볼 때마다 어느 것인지 확인할 것

| | 가이드 옛 예제 · PPT · ST 툴 원본 | ST EVL6790_670W | **본 프로젝트** |
| :--- | ---: | ---: | ---: |
| 출력 | 240 W / 60 V / 4 A | 670 W / 48 V / 14 A | **657.5 W / 25 V / 26.3 A** |
| 2차 정류 · 권선비 n · C_out | FB · 2.5 · 4.08 mF | CT · 3.2 · 18.8 mF | **CT · 6.0 · 75.2 mF** |

탱크와 1차측은 EVL 보드와 거의 같고(반사 전압 150 vs 154 V), 달라지는 것은 2차측 전부와 출력 뱅크다.

**권선비는 미결정이다** — 정본 시트와 빌더 기본은 **9:1**, 배포용 AN(`an_pdf.AN_VARIANT`)과 벤더 사양서는
**7.5:1**(단일 트랜스포머 `7p5to1_x1`). **사용자 결정 대기.** 상세와 다른 확정값은 `docs/DESIGN.md` §1.3.

## 산출물과 파일 지도

산출물은 넷 — ① 설계 가이드(배포용) ② SMath 시트(정확한 수학 모델) ③ 교육자료(초보자용) ④ 수정된 ST 스프레드시트.
데이터시트 · 회로도 · 논문은 **입력 자료**이고 고치지 않는다.

| 경로 | 무엇 | 상태 |
| :--- | :--- | :--- |
| `Smath/L6790A_SingleStage_PF_LLC_Design_Guide.sm` | **정본 시트** — 19절 · 노란 입력 셀 113개 · ZedGraph 판 7장 · A3 가로 44쪽 | rev 1 · F9 확인됨 |
| `Smath/variants/L6790A_{9to1,7p5to1,7p5to1_x1,8to1,6to1}.sm` | 설계점 5종. `L6790_VARIANT` 로 `build_l6790_smath.py` 가 만든다 | 전부 검사 통과 |
| `Smath/L6790A_probe.sm` · `L6790A_ruler.sm` | 진단 프로브 P1–P29 · 쪽 경계 자 | 큰 시트가 안 열리면 프로브부터 |
| `Smath/L6790A_gainzed.sm` · `L6790A_gainladder.sm` · `L6790A_gainplot.sm` | 게인 곡선을 SMath 로 그릴 수 있는가 — 확인용 3종 | **아직 아무도 안 열었다** |
| `Calculation Excel Sheet/L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx` | ST 툴 수정본. `CHANGELOG_rev0_6` 에 변경 이력 | rev 0.6 |
| `Calculation Excel Sheet/Uncryped_04092026_LGE_670W_L6790A_spread sheet.xlsx` | ST 원본(디크립트본, openpyxl 로 열림). 원본 `sheetN` ↔ 우리 `sheetN+1` | 읽기 전용 |
| `Calculation Excel Sheet/variants/` | 워크북 3종(`9to1,7p5to1,6to1`) · 벤더 사양서 5종(`+7p5to1_x1,8to1`) | 8:1 · `_x1` 은 워크북 없음 |
| `Design Guide/AN_L6790A_SingleStage_PFC_LLC_ApplicationNote_v1.3.pdf` · `…_KR_v1.3.pdf` | **배포용 AN** 영문 93쪽 · 한국어 92쪽. `an_pdf.py`+`an_body.py` / `an_kr_pdf.py`+`an_kr_body.py`, 수치 전부 `l6790.py`·시트 | v1.3 · **한국어판이 29·30·35차만큼 뒤처짐** |
| `Design Guide/AN_L6790A_Design_Guide_rev2_0.md` · `AN_L6790A_Design_Guide_rev2_1.md` | 한국어 본체 문서 — rev 2.0 은 9:1, rev 2.1 은 7.5:1. **둘 다 살아 있는 설계점, 지우지 말 것** | rev 2.0/2.1 |
| `Design Guide/L6790A_Transformer_Design_KR_v1.0.pdf` | 트랜스포머 설계 정리 9쪽(`tx_pdf.py`+`tx_body.py`) | v1.0 |
| `Design Guide/generators/` | 도구 체인 전부 — README 참조 | |
| `Training Material/…Design_Training.pptx` | 영문 교육자료 61장 | 한국어판 남음 |
| `Datasheet/` · `EVB Schematic/` · `LGE Material/` · `Reference/` | 입력 자료. DS 는 **DRAFT**(TBD · 내부 모순 있음). `Reference/Visio-LLC drawing.pdf` 가 본 설계 회로도(벡터) | 원본 |

## 지금 상태와 다음 할 일

| 남은 일 | 무엇을 | 상태 |
| :-- | :--- | :--- |
| **한국어판 AN** | 영문 v1.3 의 29·30차(PF 설명 · 게인 비교 절 · 기호표 130행)를 `an_kr_body.py` 에 이식. 한글 글꼴(NanumGothic · WQY)은 이 컨테이너에 있다 | **다음 차례** |
| **권선비 결정** | 9:1(정본) 대 7.5:1(AN) | 사용자 대기 |
| 스프레드시트 rev 0.7 | 정리만 남았다 — `CHANGELOG_rev0_7` 시트 분리, 그때 **CHANGELOG 에 없는 설계 셀 48개**를 채운다 | 대기 |
| 교육자료 한국어판 | 영문 61장 끝, 한국어판 | 대기 |
| 열린 설계 항목 3 | 코어 미선정(`k.Ae`) · `n.SR` 2→3(`k.PSR`) · `R.T` 11→10 kΩ(7.5:1 채택 시) — `docs/DESIGN.md` §4.2 | 대기 |
| 시제품 실측 | `docs/DESIGN.md` §4.3 의 11항목 | 보드 |

**사람이 PC 에서 해야 할 일** (기계가 대신 못 한다): ① 6:1 워크북을 한 번 열었다 저장(`calcChain` 없음, `f.Min` 캐시가 옛 390 pF 값)
② 정본 워크북도 한 번 열었다 저장(신설 셀 9개 값 생성) ③ 프로브 P27·P28·P29 중 어느 것이 세로 2배로 그려지는지 확인
④ 프로브 P16·P18·P19·P20 이 이 PC 의 SMath 에서 도는지. 근거는 `HISTORY.md` 2026-08-24 · 09-08.

## 절대 규칙 — 어기면 파일이 깨지거나 값이 조용히 틀린다

- **`.sm` 의 정본은 언제나 빌더다.** SMath 로 저장하면 레이아웃이 무너진다 — 인쇄는 열기 → F9 → 인쇄 → **저장 없이 닫기**.
  사용자가 SMath 에서 손으로 옮긴 것은 **빌더에 역이식**하고 재빌드한다. 저장된 파일을 고쳐 쓰지 않는다.
- **워크북은 openpyxl 로 저장하지 않는다**(차트 30개가 날아간다). XML 편집은 `xlsx_patch.py` 로만.
- **BOM 과 설계값은 손으로 적지 않는다** — 살아 있는 참조 · `snapshot.py` · `an_pdf.V` 로만. 판 글자에 계산값 금지.
- **`l6790.py` 가 수치 정본.** 새 수치는 거기서 내고 시트 · 워크북과 삼중 대조. 계산값과 **선정값**을 구분 기록한다.
- **`l6790_validate.py` 를 절대 지우지 말 것** — 240 W 예제가 `l6790.py` 의 유일한 독립 검증이고 코드 안에 값 29개가 있다.
- **`build_trans_spec.py` 는 변형 인자 필수** — 인자 없이 돌려 정본을 덮어쓴 사고가 두 번 났다.
- **한국어판 AN 은 영문판을 사용자가 확인한 뒤에** 이식한다. 한국어판의 억지 한자어는 영어로(`.claude/rules/an.md`).
- **PDF 는 직접 전달**(ZIP 아님 — 2026-09-22 사용자 지시). 그 밖의 파일 묶음은 ZIP 하나로.
- 커밋 · 코드 · 산출물에 모델 식별자를 넣지 않는다.

## 검증 — 새 세션은 이 세 줄로 시작한다

```
cd "Design Guide/generators"
python build_l6790_smath.py        # -> mismatches: 0
python check_sm.py "../../Smath/L6790A_SingleStage_PF_LLC_Design_Guide.sm"   # -> VERDICT OK
python bom_compare.py              # -> items compared: 29   different: 0
python snapshot.py                 # docs/DESIGN.md §3 갱신 + 지난번 이후 무엇이 움직였는지
```

전량 검증 12종과 기대값은 README §9.1. 문서를 고쳤으면 `python audit_md.py`, AN 을 고쳤으면 `an_check.py` + `an_symbols.py`.
**Stop hook(`.claude/settings.json` → `guard.py`)이 추적 파일이 바뀐 턴 끝에 이것들을 돌리고, 실패하면 턴을 막는다.**
Python 3.12 + `openpyxl` · `Pillow` · `numpy` · `matplotlib` · `reportlab`. 경로는 전부 스크립트 기준 상대경로.

## 환경 메모

- 이 컨테이너에서 정본 `.sm` 을 재빌드하면 **줄바꿈만 CRLF → LF 로 바뀌어 23,732줄 diff** 로 보인다. 내용은 같다 — `git checkout` 으로 되돌린다.
- TDK CDN 은 기본 UA 를 403 으로 막는다(브라우저 UA 필요). wikidocs.net 은 Cloudflare 챌린지라 자동으로 못 읽는다.
- 워크북이 Excel 에서 열려 있으면 `bom_compare` 가 비교를 건너뛴다.
