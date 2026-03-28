---
name: naver_research
description: 네이버 금융 산업분석 리포트 자동 수집 스킬. 조선·반도체·에너지 섹터의 전날 보고서를 파싱·다운로드·파일 정리하고 결과를 요약한다.
version: 1.0.0
author: tealeaf
---

# naver_research

## 목적

네이버 금융 산업분석 페이지에서 **어제 날짜** 보고서를 자동으로 수집한다.

- 대상 섹터: 조선 / 반도체 / 에너지
- PDF 보고서 다운로드 → 페이지 수 확인 → 지정 폴더에 규칙적 파일명으로 저장
- PDF 없는 보고서는 빈 `.txt` 파일로 저장

---

## 사용 방법

```
/naver_research
```

인자 없이 실행한다. 어제 날짜는 자동 계산된다.

---

## 입력

| 항목 | 값 |
|------|-----|
| 대상 섹터 | 조선, 반도체, 에너지 |
| 날짜 | 실행일 기준 전날 (yy.mm.dd 자동 계산) |
| 소스 | 네이버 금융 산업분석 페이지 |

---

## 출력

| 항목 | 설명 |
|------|------|
| PDF 파일 | `분류_작성일_증권사_제목_p페이지수.pdf` |
| TXT 파일 | `분류_작성일_증권사_제목.txt` (PDF 없는 보고서) |
| 저장 경로 | `/Users/tealeaf/Library/CloudStorage/GoogleDrive-taeseungg@gmail.com/My Drive/02 주식/02 자료/0 Inbox` |
| 결과 요약 | 섹터별 처리 결과 테이블 |

### 파일명 예시

```
조선_260318_신한투자증권_시황 점검 전쟁통에도 탄탄_p5.pdf
반도체_260318_하나증권_메모리 가격 상승 지속_p12.pdf
에너지_260318_DS투자증권_LNG 발주 본격화.txt
```

---

## 실행 흐름

```
1단계: 네이버 금융 파싱    → 섹터별 어제자 보고서 목록 추출
2단계: PDF 다운로드        → /tmp/ 에 임시 저장
3단계: 페이지 수 확인      → Python으로 PDF 파싱
4단계: 최종 저장           → 파일명 규칙 적용 후 Inbox로 이동
5단계: 결과 요약 출력      → 섹터별 처리 결과 테이블
```

자세한 프롬프트 지시: `prompts/main.md`
스크립트: `scripts/fetch_reports.sh`, `scripts/count_pages.py`
출력 템플릿 참고: `templates/sector_report.md`

---

## 파일 구조

```
naver_research/
├── SKILL.md                 ← 스킬 정의 (이 파일)
├── prompts/
│   └── main.md              ← LLM 실행 프롬프트
├── scripts/
│   ├── fetch_reports.sh     ← 네이버 금융 파싱 스크립트
│   └── count_pages.py       ← PDF 페이지 수 카운터
├── references/
│   └── naver_urls.md        ← 섹터별 네이버 금융 URL
└── templates/
    └── sector_report.md     ← Obsidian 섹터 리서치 요약 템플릿
```
