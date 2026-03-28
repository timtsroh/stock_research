# PRD: 주식 뉴스 텔레그램 피드 봇

## 1. 개요

Google Sheets에 등록된 기업 목록을 기반으로 국내·해외 뉴스를 수집하고, 매일 2회(오전 6시 / 오후 6시 KST) Telegram 채널로 자동 발송하는 파이프라인.

- **국내 기업**: Naver 뉴스 OpenAPI
- **해외 기업**: Marketaux → Finnhub → Alpha Vantage (순차 보완)

---

## 2. 목표

- 관심 기업 목록의 최신 뉴스를 수동 검색 없이 자동 수집
- Telegram 채널을 통해 팀/개인에게 뉴스 알림 전달
- GitHub Actions로 완전 자동화 (서버 불필요)

---

## 3. 주요 구성 요소

| 구성 요소 | 역할 | 세부 내용 |
|---|---|---|
| Google Sheets | 기업 목록 소스 | Light·Atom 시트 B열(국내), ENG 시트 B열(회사명)·D열(티커) |
| Naver 뉴스 OpenAPI | 국내 뉴스 수집 | 회사명 키워드 검색 |
| Marketaux | 해외 뉴스 수집 (주) | 티커 심볼 검색, 100 req/일 |
| Finnhub | 해외 뉴스 수집 (보조1) | 티커 심볼 검색, 60 req/분 |
| Alpha Vantage | 해외 뉴스 수집 (보조2) | 티커 심볼 검색, 25 req/일 |
| Telegram Bot | 뉴스 발송 | Light/Atom/ENG 각각 채널로 전송 |
| GitHub Actions | 스케줄 실행 | 매일 06:00, 18:00 KST |

---

## 4. 외부 연동 정보

| 항목 | 값 |
|---|---|
| Google Sheets URL | `https://docs.google.com/spreadsheets/d/1sfDjoKbrEbKvA0qwMA1nPdcEu628YgNX0A_JLLOB4WA/edit` |
| Light 시트 | B열: 국내 기업명 |
| Atom 시트 | B열: 국내 기업명 |
| ENG 시트 | B열: 해외 기업명, D열: 티커 심볼 |
| GitHub 레포 | `https://github.com/timtsroh/stock_research` |
| 코드 경로 | `news_kor/` |

---

## 5. 기능 요구사항

### 5.1 Google Sheets 기업 목록 읽기

- gspread 라이브러리 사용
- 국내: Light·Atom 시트 B열에서 회사명 읽기
- 해외: ENG 시트 B열(회사명) + D열(티커) 쌍으로 읽기
- 첫 행(헤더) 항상 스킵, 빈 셀 스킵
- 인증: 서비스 계정(Service Account) JSON → GitHub Secret `GCP_OAUTH_KEYS`

### 5.2 국내 뉴스 수집 — Naver 뉴스 OpenAPI

- 각 회사명으로 Naver 뉴스 OpenAPI 호출
- 파라미터: `display=10`, `sort=date` (최신순)
- 시간 필터: 실행 시점 기준 **12시간 이내** 기사만 수집
- 관련성 필터: 제목+본문 요약에 회사명 **2회 이상** 등장 시만 수집
- 회사당 최대 3건, 중복 URL 제외

### 5.3 해외 뉴스 수집 — Marketaux + Finnhub + Alpha Vantage

- ENG 시트의 티커 심볼로 검색
- 시간 필터: 실행 시점 기준 **12시간 이내** 기사만 수집
- 관련성 필터: 제목+본문 요약에 회사명 **1회 이상** 등장 시만 수집
- 수집 순서: Marketaux → (부족 시) Finnhub → (부족 시) Alpha Vantage
- 회사당 최대 3건, 중복 URL 제외

### 5.4 Telegram 발송

- 피드별 모든 회사 뉴스를 하나의 메시지로 통합 전송
- Light → `TELEGRAM_NEWS_ID_Light` 채널 (국내 + 해외)
- Atom → `TELEGRAM_NEWS_ID_Atom` 채널 (국내)
- HTML parse_mode 사용

### 5.5 실행 로직 흐름

```
main.py 실행
  │
  ├─ [1단계] 국내 기업 뉴스 — Naver
  │     ├─ [Light] Light 시트 B열 회사 목록 로드
  │     │         → Naver 검색 → TELEGRAM_NEWS_ID_Light 전송
  │     └─ [Atom]  Atom 시트 B열 회사 목록 로드
  │                → Naver 검색 → TELEGRAM_NEWS_ID_Atom 전송
  │
  └─ [2단계] 해외 기업 뉴스 — Marketaux + Finnhub + Alpha Vantage
        └─ [ENG] ENG 시트 B열(회사명) + D열(티커) 로드
                 → Marketaux → Finnhub → Alpha Vantage 순 검색
                 → TELEGRAM_NEWS_ID_Light 전송
```

---

## 6. 비기능 요구사항

- **Rate Limiting**: 회사별 API 호출 사이 0.5초 딜레이
- **에러 처리**: API 호출 실패 시 해당 회사 스킵, 로그 출력 후 계속 진행
- **타임존**: 모든 시간 표시는 KST (UTC+9)
- **로그**: 실행 시작/종료, 처리 회사 수, 전송 건수 출력

---

## 7. 파일 구조

```
stock_research/
├── .github/
│   └── workflows/
│       ├── news_kor.yml      # 뉴스 피드 스케줄
│       └── dart.yml          # DART 공시 스케줄
└── news_kor/
    ├── PRD.md
    ├── main.py               # 실행 진입점
    ├── sheets_reader.py      # Google Sheets 읽기
    ├── news_fetcher.py       # Naver / Marketaux / Finnhub / Alpha Vantage 검색
    ├── telegram_sender.py    # Telegram 메시지 전송
    ├── requirements.txt
    └── .gitignore            # .env, gcp-oauth.keys2.json 제외
```

---

## 8. 환경 변수 / GitHub Secrets

| Secret 이름 | 설명 |
|---|---|
| `GCP_OAUTH_KEYS` | Google 서비스 계정 JSON 전체 내용 |
| `GOOGLE_SHEET_ID` | 스프레드시트 ID |
| `NAVER_CLIENT_ID` | Naver OpenAPI Client ID |
| `NAVER_CLIENT_SECRET` | Naver OpenAPI Client Secret |
| `MARKETAUX_API_KEY` | Marketaux API 토큰 (해외 뉴스 주) |
| `FINNHUB_API_KEY` | Finnhub API 키 (해외 뉴스 보조1) |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API 키 (해외 뉴스 보조2) |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_NEWS_ID_LIGHT` | Light 포트폴리오 Telegram 채널 ID |
| `TELEGRAM_NEWS_ID_ATOM` | Atom 포트폴리오 Telegram 채널 ID |

---

## 9. GitHub Actions 스케줄

- `0 21 * * *` → KST 06:00
- `0 9 * * *` → KST 18:00
- `workflow_dispatch` → 수동 트리거 (테스트용)
