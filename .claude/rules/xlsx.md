---
paths:
  - "Calculation Excel Sheet/**"
  - "Design Guide/generators/fix_xl_*.py"
  - "Design Guide/generators/log_xl_*.py"
  - "Design Guide/generators/xlsx_patch.py"
  - "Design Guide/generators/xl_sm_compare.py"
  - "Design Guide/generators/rtc_check.py"
  - "Design Guide/generators/audit_xl.py"
  - "Design Guide/generators/audit_fet.py"
  - "Design Guide/generators/bom_compare.py"
  - "Design Guide/generators/build_trans_spec.py"
  - "Design Guide/generators/check_trans_spec.py"
---
# 워크북 `.xlsx` 를 고칠 때의 함정

**스프레드시트는 정본이 아니다** — 구조적 한계가 있다(`HISTORY.md` 시트 §3.2). 수치 정본은 `l6790.py`,
설계값 정본은 SMath 시트다. 워크북을 손댔으면 `xl_sm_compare.py` (불일치 0) 와 `bom_compare.py` 를 돌린다.
`build_trans_spec.py` 는 **변형 인자 필수**이고 `variants/` 에만 쓴다.

## XML 로 직접 고칠 때

이 워크북은 **차트 30 · 이미지 11 · 코멘트 7**을 갖고 있고 **openpyxl은 차트를 라운드트립하지
못한다.** 그래서 zip 안의 XML을 직접 고친다. **openpyxl로 저장하지 말 것.**

1. **한 `<row>` 안에 같은 `r=` 셀이 두 번 있으면 안 된다.**
2. **`<row>` 안의 셀은 열 번호 오름차순이어야 한다.**
3. **수식을 추가/삭제하면 `xl/calcChain.xml`을 삭제한다** — `[Content_Types].xml`의 Override와
   `xl/_rels/workbook.xml.rels`의 Relationship도 함께. Excel이 다시 만든다.
4. `workbook.xml`의 `<calcPr>`에 `fullCalcOnLoad="1"`.
5. **쓰기 전에 전 시트를 훑어 "행 안의 셀이 중복 없이 오름차순인가"를 검사한다.**
   통과 못 하면 설치하지 않는다. → **`xlsx_patch.py`가 1–5를 전부 대신한다.**
   손으로 zip을 뜯지 말고 이것을 쓸 것: `set_cell()` · `cell_t/f/n()` · `style_of()` ·
   `open_book()` / `write_book()`(검사 실패 시 쓰기 거부) · `backup()`.
6. **`BOM&Schematics`의 G열은 비어 있지 않다** — 모든 행이 `=IF(E.., "", "<출처 시트>")`
   힌트를 갖고 있다. **H·I열은 그림이 앵커되어 있어 그림 밑에 깔린다.**
7. **수정 전 백업을 남긴다** — `xlsx_patch.backup()`. 작업이 검증되면 지운다 (중간 상태 백업 4개는 2026-08-23에 정리했다).

## BOM 대조가 읽는 셀 — 엑셀 BOM 시트가 아니다

BOM 셀은 링크이고 캐시값은 Excel 이 재계산하기 전까지 낡아 있으므로 **링크가 가리키는 원본 셀**을 읽는다:

```
Res. Tank Design       F9 F43 F44 F45
Power Components       F7 D23 D24 D25 D38
Device Setting         F24 F45 D43 D46 F61 F83 F90 F91 F108 D21
CompensationNet&Check  D14 D36 F37 F41 F43 F93~F96
```

SMath 쪽은 `<result>` 와 `<contract>` 표시 단위를 함께 읽어 환산한다. **`<result>` 는 이미 표시 단위 값이다** —
SI 로 착각해 또 나누면 전부 불일치로 보인다. `C.T` 는 `Device Setting D21` 직접 입력이지 F열 선정 셀이 아니다.

## 사양을 바꿀 때 함께 바꿔야 하는 셀

**입력 셀만 바꾸면 탱크까지는 정확하게 따라오지만, "선정값(F열)"은 하나도 따라오지 않는다.**

| # | 셀 | 안 고치면 |
| :-- | :--- | :--- |
| 1 | `Power Components` D23 · D24 · D25 | 출력 커패시터가 요구값과 무관하게 남는다. **D31·D32(리플 %)와 D33(홀드업 ms) 두 줄을 반드시 볼 것** |
| 2 | `Device Setting` F45 | D46이 D38을 넘으면 **D48 최대 입력 전력이 잘린다.** OCP1도 같은 저항 |
| 3 | `Device Setting` F83 | D83을 넘으면 OVP2에서 VCC가 25 V를 넘는다. **정수 턴 구현 가능성도 확인** |
| 4 | `Device Setting` F108 | D108을 넘으면 V_BO가 VAC_min 위로 올라가 최저 입력에서 브라운아웃 |
| 5 | `Device Setting` D57 | 절대값이므로 P_in 대비 비율이 통째로 바뀐다 |
| 6 | `CompensationNet&Check` F37 · F41 · F43 · F93~F96 | **1·2를 먼저 고치고 마지막에 다시 계산할 것** |
| 7 | `Design Spec` D46 · D47 · `Device Setting` D13 | ✅ 2026-08-23에 800 pF / 220 ns / T_idle 250 ns로 맞췄다. **사양을 바꾸면 다시 볼 것** |

---

