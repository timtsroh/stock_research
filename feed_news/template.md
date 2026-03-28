# Telegram 뉴스 메시지 템플릿

## 메시지 구조

```
📌 등대 포트폴리오 뉴스피드
🕐 YYYY-MM-DD HH:MM KST

1. 회사1
{기사 제목}
{기사 URL}
{언론사 이름} | YYYY-MM-DD HH:MM KST

{기사 제목}
{기사 URL}
{언론사 이름} | YYYY-MM-DD HH:MM KST

{기사 제목}
{기사 URL}
{언론사 이름} | YYYY-MM-DD HH:MM KST


2. 회사2
...
```

---

## 실제 출력 예시

```
📌 등대 포트폴리오 뉴스피드
🕐 2026-03-25 18:00 KST

1. 에스티팜
에스티팜, 올리고 원료의약품 수출 계약 체결
https://www.hankyung.com/article/...
한국경제 | 2026-03-25 14:32 KST

에스티팜 1분기 실적 전망 상향 조정
https://www.mk.co.kr/article/...
매일경제 | 2026-03-25 11:15 KST


2. 올릭스
올릭스, RNAi 치료제 기술 수출 계약
https://www.edaily.co.kr/article/...
이데일리 | 2026-03-25 13:20 KST
```

---

## 규칙

| 항목 | 규칙 |
|---|---|
| 메시지 수 | 피드당 1개 메시지로 통합 전송 |
| 채널 구분 | Light → TELEGRAM_NEWS_ID_Light / Atom → TELEGRAM_NEWS_ID_Atom |
| 회사당 최대 기사 수 | 3건 |
| 정렬 기준 | 최신순 |
| 관련성 필터 | 제목+본문에 회사명 2회 미만 등장 시 제외 |
| 시간 기준 | KST (UTC+9) |
| 뉴스 없는 회사 | 메시지에서 생략 |
| 중복 URL | 동일 실행 내 제거 |
| 언론사 이름 | URL 도메인에서 자동 추출 |
| 회사명 | 볼드(HTML) 처리 |

---

## 템플릿 수정 방법

메시지 형식 변경 → `telegram_sender.py`의 `build_combined_message()` 수정

회사당 기사 수 변경 → `naver_news.py`의 `MAX_PER_COMPANY` 값 수정

피드 채널 추가 → `main.py`의 `FEEDS` 리스트에 항목 추가
