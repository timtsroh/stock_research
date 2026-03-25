# PRD: 한국 주식 뉴스 텔레그램 피드 봇

## 1. 개요

Google Sheets에 등록된 한국 기업 목록을 기반으로 네이버 뉴스 OpenAPI를 통해 관련 뉴스를 수집하고, 매일 2회(오전 6시 / 오후 6시) Telegram 채널로 자동 발송하는 파이프라인.

---

## 2. 목표

- 관심 기업 목록의 최신 뉴스를 수동 검색 없이 자동 수집
- Telegram 채널을 통해 팀/개인에게 뉴스 알림 전달
- GitHub Actions로 완전 자동화 (서버 불필요)

---

## 3. 주요 구성 요소

| 구성 요소 | 역할 | 세부 내용 |
|---|---|---|
| Google Sheets | 기업 목록 소스 | Light 시트 B열, Atom 시트 B열 |
| Naver 뉴스 OpenAPI | 뉴스 수집 | `https://openapi.naver.com/v1/search/news.json` |
| Telegram Bot | 뉴스 발송 | Light/Atom 각각 별도 채널로 전송 |
| GitHub Actions | 스케줄 실행 | 매일 06:00, 18:00 KST |

---

## 4. 외부 연동 정보

| 항목 | 값 |
|---|---|
| Google Sheets URL | `https://docs.google.com/spreadsheets/d/1sfDjoKbrEbKvA0qwMA1nPdcEu628YgNX0A_JLLOB4WA/edit` |
| Light 시트 | B열에서 기업명 읽기 |
| Atom 시트 | B열에서 기업명 읽기 |
| Naver OpenAPI 엔드포인트 | `https://openapi.naver.com/v1/search/news.json` |
| GitHub 레포 | `https://github.com/timtsroh/stock_research` |
| 코드 경로 | `news_kor/` |

---

## 5. 기능 요구사항

### 5.1 Google Sheets 기업 목록 읽기

- gspread 라이브러리 사용
- Light 시트 B열, Atom 시트 B열에서 각각 회사명 목록 읽기
- 첫 행(헤더) 항상 스킵
- 빈 셀 스킵
- 인증 방식: 서비스 계정(Service Account) JSON 키 → GitHub Secret에 저장

### 5.2 네이버 뉴스 검색

- 각 회사명에 대해 Naver 뉴스 OpenAPI 호출
- 파라미터: `display`: 10, `sort`: `date` (최신순)
- 관련성 필터: 제목+본문에 회사명 2회 미만 등장 시 제외
- 회사당 최대 3건
- 중복 URL 필터링 (동일 실행 내)
- 인증: `X-Naver-Client-Id` / `X-Naver-Client-Secret` 헤더

### 5.3 Telegram 발송

- 한 피드(Light 또는 Atom)의 모든 회사 뉴스를 하나의 메시지로 통합 전송
- Light → TELEGRAM_CHAT_ID_Light 채널
- Atom → TELEGRAM_CHAT_ID_Atom 채널
- HTML parse_mode 사용 (볼드 처리)

### 5.4 실행 로직 흐름

```
main.py 실행
  │
  ├─ [Light 피드]
  │     ├─ Light 시트 B열에서 회사 목록 로드
  │     ├─ 각 회사 Naver 뉴스 검색 (최대 3건)
  │     └─ 통합 메시지 → TELEGRAM_CHAT_ID_Light 전송
  │
  └─ [Atom 피드]
        ├─ Atom 시트 B열에서 회사 목록 로드
        ├─ 각 회사 Naver 뉴스 검색 (최대 3건)
        └─ 통합 메시지 → TELEGRAM_CHAT_ID_Atom 전송
```

---

## 6. 비기능 요구사항

- **Rate Limiting**: 회사별 API 호출 사이 0.5초 딜레이
- **에러 처리**: API 호출 실패 시 해당 회사 스킵, 로그 출력 후 계속 진행
- **타임존**: 모든 시간 표시는 KST (UTC+9)
- **로그**: 실행 시작/종료, 처리 회사 수, 전송 메시지 수 출력

---

## 7. 파일 구조

```
stock_research/
├── .gitignore
├── .github/
│   └── workflows/
│       └── news_feed.yml
└── news_kor/
    ├── PRD.md
    ├── template.md
    ├── main.py
    ├── sheets_reader.py
    ├── naver_news.py
    ├── telegram_sender.py
    ├── requirements.txt
    └── .env.example
```

---

## 8. 환경 변수 / GitHub Secrets

| Secret 이름 | 설명 |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google 서비스 계정 JSON 전체 내용 |
| `GOOGLE_SHEET_ID` | 스프레드시트 ID |
| `NAVER_CLIENT_ID` | Naver OpenAPI Client ID |
| `NAVER_CLIENT_SECRET` | Naver OpenAPI Client Secret |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID_Light` | Light 포트폴리오 Telegram 채널 ID |
| `TELEGRAM_CHAT_ID_Atom` | Atom 포트폴리오 Telegram 채널 ID |

---

## 9. GitHub Actions 스케줄

- `0 21 * * *` → KST 06:00
- `0 9 * * *` → KST 18:00
- `workflow_dispatch` → 수동 트리거 (테스트용)
