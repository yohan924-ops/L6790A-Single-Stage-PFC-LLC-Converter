# L6790A 단일단 PF LLC — 25 V / 26.3 A TV(OLED) SMPS — PQ50 복사본(TDK PQ 50/50 한 개 · 15:2 · L_r 25 µH)

> **이 폴더(`PQ50/`)는 `Lr14/` 를 그대로 복사해 트랜스포머를 TDK PQ 50/50 한 개로 바꾼 복사본이다**(2026-09-30 사용자: "엑셀시트와 Smath 사본 만들어서 설계부터 다시 검증해"). 원본(저장소 최상위)과 `Lr14/` 는 건드리지 않는다. `Reference/` 등 입력 폴더는 원본 폴더로의 심볼릭 링크. 도구는 이 폴더 안에서 돌린다. Stop hook(`guard.py`)은 원본만 검사하므로 이 폴더의 검사는 손으로 돌린다.
>
> **AN(영문) · 그림 · 벤더 사양서 · `cores.py` · `insulation.py` 도 PQ 50/50 판이다(73차).** 옛 코어(ETD 54 · E 60/22/16 · PC47)는 AN 에서 지웠다. 누설의 기준은 **`leakage_fem.py`(2D FEM, `fem2d.py` 풀이기 · scipy 필요)** 이고, `leakage.py`(1D 해석식)는 PQ 에서 반쪽 순서를 거꾸로 내므로 기준이 아니다. **한국어판 AN 은 이 복사본에서 뺐다** — ETD 54 판이었고, 영문판을 사용자가 확인한 뒤에 이식한다.

ST **L6790A** 로 **단일단(Single-Stage) PF LLC** 를 설계한다. 90–264 Vac → **25 V / 26.3 A = 657.5 W**.
2단(Boost PFC + LLC)의 400 V 벌크 커패시터와 승압단을 없애고, 그 대가로 출력에 **75 mF 뱅크**가 붙는다.

**설계점(2026-09-30).** 트랜스포머는 **TDK PQ 50/50(N97, B65981A) 한 개 + 카탈로그 보빈 B65982E(12핀) + 칸막이 3.0 mm**, 15:2.
1차 NP1 15 T = **3층 × 5 T, TIW-Litz ø2.9**(Elektrisola EFOLIT 급, 강화절연 · 500 kHz) · 칸막이 · 2차 **NS2 2 T 한 층 → NS3 2 T 한 층, Litz ø4.0** · NAUX 2 T TIW 맨 위.
턴당 한 다발, 층마다 권선 하나, 뒤집기 없음. 반경 9.72 mm(플랜지 끝 반경 21.3–21.6 · 바깥다리 원호 ø44 — TDK 도면 벡터로 읽음).
2D FEM 누설 **23.3–26.4 µH**(반쪽 NS2 24.5 · NS3 25.1, 요크 나비넥타이 모양 반영) → **L_r 25 µH · L_m 45 µH · C_r 180 nF(E12) · R.T 21.5 kΩ(E96) · C.T 470 pF**.
f_r 75.0 kHz · f_o 44.8 kHz · B_pk 125.5 mT(A_e 332) · A_L 311 nH · n 6.013(λ 0.556).
**검증**(이 폴더에서 손으로): 빌더 대조 4변형 `mismatches 0` · `check_sm` OK(정본 · `_x1`) · `bom_compare` 29/0 · `rtc_check` OK · **`xl_sm_compare` 145/145**(LibreOffice 재계산 사본) · `check_theta` 0 · `audit_dim` 0 · `audit_rpn` 불일치 1(P.DZ 의 W↔mW 표시, 오탐 · Lr14 와 같음).
판정 지표 44개 중 **PQ 50/50 한 개(`_x1`) 41개**, **정본(3코어 자리표시자) 40개**(`k.Ae` 미달 — PQ 40/40 × 3 의 B_pk 368 mT, 3코어 구성은 이 탱크로 다시 검토하지 않았다). 탱크는 C_r · L_m · R.T 를 고정하고 **L_r 22.3–28.6 µH** 에서 41/44.
워크북은 `pq50_xl.py` 가 `Res. Tank Design` F43 · F44 · F45 · **F9(n 6.0241 → 6.0134)** 와 `Device Setting` F24 를 바꿨다 — **F9 를 빠뜨리면 11칸이 0.4–0.9 % 어긋난다**(λ 가 0.55 → 0.556 이 돼 n 이 움직인다). 의존 수식의 캐시는 Excel 에서 한 번 열었다 저장해야 맞는다.

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

**권선비는 7.5:1 로 확정**(2026-09-21). 정본 시트 · 정본 워크북 · 빌더 기본은 **코어 3개(유닛 5:2, `7p5to1`)** —
실제 설계용이고 SMath 에만 해당한다. 배포용 AN(`an_pdf.AN_VARIANT`)은 같은 탱크를 **트랜스포머 1개(15:2, `7p5to1_x1`)**로 설명한다.
9:1 은 2026-09-23 에 지웠다. 상세와 다른 확정값은 `docs/DESIGN.md` §1.3.

## 산출물과 파일 지도

산출물은 셋 — ① 설계 가이드(배포용 AN) ② SMath 시트(정확한 수학 모델) ③ 수정된 ST 스프레드시트.
교육자료(PPT)와 트랜스포머 설계 정리 PDF 는 지웠다 — 교육자료는 중단, 트랜스포머 정리는 AN 에 같은 내용이 있다(2026-09-23 사용자).
데이터시트 · 회로도 · 논문은 **입력 자료**이고 고치지 않는다.

| 경로 | 무엇 | 상태 |
| :--- | :--- | :--- |
| `Smath/L6790A_SingleStage_PF_LLC_Design_Guide.sm` | **정본 시트** — 19절 · 노란 입력 셀 130개 · ZedGraph 판 7장 · A3 가로 47쪽 | rev 1 · F9 확인됨 — **시트 §14c(2026-09-25 신설)는 아직 F9 미확인** |
| `Smath/variants/L6790A_{7p5to1,7p5to1_x1,8to1,6to1}.sm` | 설계점 4종(`7p5to1` 은 정본과 같은 바이트). `L6790_VARIANT` 로 `build_l6790_smath.py` 가 만든다 | 전부 검사 통과 |
| `Smath/L6790A_probe.sm` · `L6790A_ruler.sm` | 진단 프로브 P1–P29 · 쪽 경계 자 | 큰 시트가 안 열리면 프로브부터 |
| `Smath/L6790A_gainzed.sm` · `L6790A_gainladder.sm` · `L6790A_gainplot.sm` | 게인 곡선을 SMath 로 그릴 수 있는가 — 확인용 3종 | **아직 아무도 안 열었다** |
| `Calculation Excel Sheet/L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx` | ST 툴 수정본, 7.5:1(`variants/…_7p5to1.xlsx` 와 같은 파일). `CHANGELOG_rev0_6` 에 변경 이력. **이 복사본은 `Res. Tank Design` F43 · F44 · F45 · F9 와 `Device Setting` F24 를 180 · 25 · 45 · 6.0134 · 21.5 로(`pq50_xl.py`) — 의존 수식의 캐시는 Excel 에서 한 번 열었다 저장해야 맞는다** | rev 0.6 + PQ 50/50 탱크 |
| `Calculation Excel Sheet/Uncryped_04092026_LGE_670W_L6790A_spread sheet.xlsx` | ST 원본(디크립트본, openpyxl 로 열림). 원본 `sheetN` ↔ 우리 `sheetN+1` | 읽기 전용 |
| `Calculation Excel Sheet/variants/` | 워크북 2종(`7p5to1,6to1`) · 벤더 사양서 4종(`+7p5to1_x1,8to1`) | 8:1 · `_x1` 은 워크북 없음 |
| `Design Guide/AN_L6790A_SingleStage_PFC_LLC_ApplicationNote_v1.3.pdf` | **배포용 AN** 영문 110쪽, 7장 예제 트랜스포머는 PQ 50/50 · 목차 링크·북마크. `an_pdf.py`+`an_body.py`, 수치 전부 `l6790.py`·시트·`cores.py`·`leakage_fem.py`. **한국어판 PDF 는 이 복사본에 없다**(`an_kr_body.py` 는 옛 판 그대로, 영문 확인 뒤 이식) | v1.3 · PQ 50/50 판(73차) |
| `Design Guide/AN_L6790A_Design_Guide_rev2_1.md` | 한국어 본체 문서(7.5:1). **시트의 식 번호 [n] 의 출처** — `audit_sm` · `audit_guide` 가 읽는다. 9:1 판 rev 2.0 은 2026-09-23 삭제 | rev 2.0/2.1 |
| `Design Guide/generators/` | 도구 체인 전부 — README 참조 | |
| `Design Guide/generators/data/` | TDK B65982E 보빈 데이터시트 한 쪽(databook 04/13 p. 287)과 거기서 벡터로 읽은 윤곽 `B65982E_outline.json`(`bobbin_outline.py`). **핀 번호가 적힌 뷰는 밑면도(핀 쪽)** — 핀 끝이 보이는 뷰가 정면도 위에 있다(제1각법). `cores.PIN_XY` 도 밑면도 좌표 | 입력 자료 사본 |
| `Datasheet/` · `EVB Schematic/` · `LGE Material/` · `Reference/` | 입력 자료. DS 는 **DRAFT**(TBD · 내부 모순 있음). `Reference/Visio-LLC drawing.pdf` 가 본 설계 회로도(벡터) | 원본 |

## 지금 상태와 다음 할 일

| 남은 일 | 무엇을 | 상태 |
| :-- | :--- | :--- |
| 스프레드시트 기록 | **끝** — ST 원본과 전량 대조해 CHANGELOG 에 빠진 17셀(옛 메모의 "48"은 그 뒤 채워진 줄을 세지 않은 수)을 `CHANGELOG_rev0_6` 96행부터 기록(`log_xl_unlogged.py`, 정본·6:1). 남은 것은 `RTC` 격자를 FB 경계 기준으로 바꾸는 설계 변경 하나(`HISTORY.md` "E 는 적용하지 않았다" 단락) — 값에는 영향 없음 | 필요하면 |
| **절연 · VCC 의 확인 항목** | 규격 원문 미확인 값 · 작업전압 실측 · `Q.g` 확인 · TIW-Litz 공급 · 누설 첫 샘플 — `docs/DESIGN.md` §4.2 10–13 | 인증기관 · 벤더 · 설계자 |
| **`R.T` — 21.5 kΩ** | PQ50 탱크로 다시 골랐다(E96). `R.T_ceil` 23.2 kΩ · `k.floor` 1.077 · `k.RTd` 1.079 · f.SU 477 kHz(TIW 500 kHz 안). C_r · L_m · R.T 를 고정하고 L_r 22.3–28.6 µH 에서 41/44 — 21.0–22.1 kΩ 어디서나 같다. 실측 누설로 다시 확인 | 시제품 |
| 시제품 실측 | `docs/DESIGN.md` §4.3 의 14항목 | 보드 |

**사람이 PC 에서 해야 할 일** (기계가 대신 못 한다): ① 7.5:1 · 6:1 워크북을 한 번 열었다 저장(`calcChain` 없음 — 6:1 은 `f.Min` 캐시가 옛 390 pF 값, 둘 다 D71 1.36 V 변경분은 캐시를 손으로 맞춰 두었다)
② 프로브 P27·P28·P29 중 어느 것이 세로 2배로 그려지는지 확인
③ 프로브 P16·P18·P19·P20 이 이 PC 의 SMath 에서 도는지. 근거는 `HISTORY.md` 2026-08-24 · 09-08.
④ 정본 시트를 열고 F9 — 시트 §14c(보조권선 VCC 레귤레이터)가 기계 계산과 같은지. 워크북 F83 · F91 변경분(2026-09-25)도 ① 의 열었다 저장으로 캐시가 맞춰진다.

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

전량 검증 12종과 기대값은 README §9.1. 문서를 고쳤으면 `python audit_md.py`, AN 을 고쳤으면 `an_check.py` + `an_symbols.py`, 그림을 고쳤으면 **`figcheck.py` 를 인자 없이 전량** + `an_figtext.py`(그림 속 기호·손 입력 숫자, 53차).
**설계값(시트)이 움직였으면 `figs.py --plain` 전량 재생성** — `figstamp.py` 가 낡은 그림을 찾는다(65차, Stop hook 6번째 검사).
**Stop hook(`.claude/settings.json` → `guard.py`)이 추적 파일이 바뀐 턴 끝에 이것들을 돌리고, 실패하면 턴을 막는다.**
Python 3.12 + `openpyxl` · `Pillow` · `numpy` · `matplotlib` · `reportlab` · **`scipy`(`fem2d.py`)**. `leakage_fem.py` 는 풀이 결과를 `generators/.fem_cache.json`(무시 파일)에 저장한다. 경로는 전부 스크립트 기준 상대경로.

## 환경 메모

- 이 컨테이너에서 정본 `.sm` 을 재빌드하면 **줄바꿈만 CRLF → LF 로 바뀌어 23,732줄 diff** 로 보인다. 내용은 같다 — `git checkout` 으로 되돌린다.
- TDK CDN 은 기본 UA 를 403 으로 막는다(브라우저 UA 필요). wikidocs.net 은 Cloudflare 챌린지라 자동으로 못 읽는다.
- 워크북이 Excel 에서 열려 있으면 `bom_compare` 가 비교를 건너뛴다.
