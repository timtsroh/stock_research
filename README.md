# stock_research

개인 투자 포트폴리오 관리를 위한 통합 자동화 플랫폼입니다.
한국 기업 공시 수집, 국내/해외 뉴스 피드, 주식 정보 대시보드, 종목 코드 검색 유틸리티로 구성되어 있습니다.

---

## 디렉토리 구조

```
stock_research/
├── dart/           # DART 전자공시 자동 수집 → Telegram 발송
├── news_kor/       # 국내/해외 뉴스 자동 수집 → Telegram 발송
├── sdb3/           # 주식 정보 웹 대시보드 (FastAPI + React)
└── ticker_finder/  # DART corp_code 및 해외 티커 검색 CLI
```

---

## 모듈별 기능

### dart

금융감독원 DART 전자공시시스템에서 관심 기업의 공시를 자동으로 수집하여 Telegram으로 발송합니다.

- Google Sheets에 등록된 포트폴리오(Light, Atom)를 기준으로 기업 목록을 로드
- DART API를 통해 전날 하루치 공시를 기업당 최대 3건 수집
- 수집된 공시를 Telegram 채널에 HTML 포맷으로 발송
- 발송 내역을 Google Sheets 로그 시트에 기록
- GitHub Actions로 매일 KST 06:00에 자동 실행

**주요 파일**

| 파일 | 역할 |
|---|---|
| `main.py` | 전체 파이프라인 오케스트레이션 |
| `dart_fetcher.py` | DART API 호출 및 공시 데이터 수집 |
| `sheets_reader.py` | Google Sheets에서 기업 목록 로드 |
| `sheets_writer.py` | 수집 결과를 Google Sheets에 기록 |
| `telegram_sender.py` | Telegram 메시지 생성 및 발송 |

**환경 변수**

| 변수명 | 설명 |
|---|---|
| `DART_API_KEY` | DART Open API 인증키 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | GCP 서비스 계정 JSON |
| `GOOGLE_SHEET_ID` | 대상 스프레드시트 ID |
| `TELEGRAM_BOT_TOKEN` | Telegram 봇 토큰 |
| `TELEGRAM_DART_ID_Light` | Light 포트폴리오 채널 ID |
| `TELEGRAM_DART_ID_Atom` | Atom 포트폴리오 채널 ID |

---

### news_kor

Naver 뉴스(국내)와 Marketaux, Finnhub, Alpha Vantage(해외)에서 뉴스를 수집하여 Telegram으로 발송합니다.

- Google Sheets에 등록된 국내 기업은 Naver 검색 API로 뉴스 수집
- 해외 기업은 Marketaux(주) → Finnhub → Alpha Vantage 순서로 수집
- 수집 범위: 발송 시점 기준 최근 12시간 이내 뉴스, 기업당 최대 3건
- 관련성 판단: 뉴스 본문에 회사명이 2회 이상 등장하는 경우만 수집
- GitHub Actions로 매일 KST 08:00에 자동 실행

**주요 파일**

| 파일 | 역할 |
|---|---|
| `main.py` | 국내/해외 뉴스 수집 파이프라인 오케스트레이션 |
| `news_fetcher.py` | Naver, Marketaux, Finnhub, Alpha Vantage API 통합 |
| `sheets_reader.py` | Google Sheets에서 기업 및 티커 목록 로드 |
| `sheets_writer.py` | 수집 결과를 Google Sheets에 기록 |
| `telegram_sender.py` | Telegram 메시지 생성 및 발송 |

**환경 변수**

| 변수명 | 설명 |
|---|---|
| `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` | Naver Open API 인증 |
| `MARKETAUX_API_KEY` | Marketaux API 키 |
| `FINNHUB_API_KEY` | Finnhub API 키 |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API 키 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | GCP 서비스 계정 JSON |
| `GOOGLE_SHEET_ID` | 대상 스프레드시트 ID |
| `TELEGRAM_BOT_TOKEN` | Telegram 봇 토큰 |
| `TELEGRAM_NEWS_ID_Light` | Light 채널 ID |
| `TELEGRAM_NEWS_ID_Atom` | Atom 채널 ID |

---

### sdb3

관심종목, 거시경제 지표, 실적/경제 캘린더를 한 화면에서 관리하는 풀스택 웹 대시보드입니다.
FastAPI 백엔드와 React 프론트엔드로 구성되며, Railway에 배포합니다.

**백엔드 (`sdb3/backend/`)**

| 파일 | 역할 |
|---|---|
| `main.py` | FastAPI 앱 설정, 라우터 등록, 정적 파일 서빙 |
| `database.py` | SQLAlchemy 모델 정의 (WatchlistItem, MacroPanel, EventFilter) |
| `cache_utils.py` | 1시간 TTL 인메모리 캐시 (API 부하 감소) |
| `routers/watchlist.py` | 관심종목 추가/삭제, 시세, 차트, 분기 재무 API |
| `routers/macro.py` | 거시경제 6패널 지표 조회 및 설정 API |
| `routers/calendar_events.py` | 실적 발표 및 경제지표 캘린더 API |

**관심종목 기능**
- yfinance 기반 미국 주식 시세 및 분기 재무(매출, 영업이익, 순이익, FCF) 조회
- FinanceDataReader 기반 한국 주식 시세 조회
- 회사명/티커 자동완성 검색 (KRX, NASDAQ, NYSE, AMEX)
- 1Y/3Y/5Y 주가 차트

**거시경제 패널 기능**
- 6개 슬롯에 원하는 지표 자유 배치
- 기본값: 미국 10Y 금리, S&P 500, 달러 인덱스, WTI 유가, VIX, 나스닥 100
- 기간별(1Y/3Y/5Y) 차트 조회

**캘린더 기능**
- FOMC, CPI, PPI, NFP, PCE, GDP 등 경제지표 발표 일정 (2025~2026 사전 등록)
- 관심종목 실적 발표일 자동 조회 (yfinance)
- 이벤트 종류별 필터 및 색상 구분
- 월간/주간 캘린더 뷰, D-Day 표시

**프론트엔드 (`sdb3/frontend/`)**

| 파일 | 역할 |
|---|---|
| `src/App.jsx` | 탭 네비게이션 (관심종목 / 거시변수 / 캘린더) |
| `src/pages/WatchlistPage.jsx` | 관심종목 목록, 시세 테이블, 차트, 재무 패널 |
| `src/pages/MacroPage.jsx` | 거시경제 6패널 그리드, 지표 편집 |
| `src/pages/CalendarPage.jsx` | 캘린더 뷰, 이벤트 필터, 다가오는 이벤트 목록 |

**환경 변수**

| 변수명 | 설명 |
|---|---|
| `DATABASE_URL` | DB 경로 (기본값: `sqlite:///stock_dashboard.db`) |

**실행 방법**

```bash
# 백엔드
cd sdb3/backend
pip install -r requirements.txt
uvicorn main:app --reload

# 프론트엔드
cd sdb3/frontend
npm install
npm run dev
```

---

### ticker_finder

Google Sheets의 기업 목록에 DART corp_code(국내) 또는 주식 티커(해외)가 비어 있을 때, 이를 대화형으로 검색하여 자동으로 채워주는 CLI 유틸리티입니다.

- 국내 기업: DART API에서 전체 기업 코드 XML을 다운로드하여 로컬 캐시(7일) 후 검색
- 해외 기업: Alpha Vantage `SYMBOL_SEARCH`로 티커 후보 조회
- 검색 결과에서 번호를 선택하거나 직접 입력하여 Google Sheets D열에 기록

**실행 방법**

```bash
cd ticker_finder
pip install -r requirements.txt

python main.py          # Light, Atom, ENG 시트 모두 처리
python main.py Light    # Light 시트(국내)만 처리
python main.py ENG      # ENG 시트(해외)만 처리
```

---

## 데이터 흐름

```
Google Sheets (기업 목록 / 포트폴리오)
        │
        ├── dart/       → DART API → Telegram (공시 알림)
        │                         → Sheets 로그
        │
        ├── news_kor/   → Naver / Marketaux / Finnhub → Telegram (뉴스 알림)
        │                                             → Sheets 로그
        │
        └── ticker_finder/ → DART / Alpha Vantage → Sheets D열 업데이트

yfinance / FinanceDataReader
        │
        └── sdb3/       → REST API → React 대시보드 (실시간 조회)
```

---

## GitHub Actions 스케줄

| 워크플로우 | 실행 시각 (KST) | 대상 모듈 |
|---|---|---|
| `dart.yml` | 매일 06:00 | `dart/` |
| `news_kor.yml` | 매일 08:00 | `news_kor/` |
