# PRD: 주식 리서치 대시보드

## 1. 개요

### 제품 목적
관심종목 주가·재무 정보, 거시경제 변수, 주요 이벤트 일정을 한 화면에서 빠르게 파악할 수 있는 개인용 주식 리서치 대시보드.

### 대상 사용자
개인 투자자 (주식 리서치 목적)

### 기술 스택

#### Frontend
- React 18 + Vite
- TailwindCSS (다크 테마)
- Recharts (차트)
- react-big-calendar (캘린더)
- axios (API 통신)

#### Backend
- FastAPI (Python)
- SQLAlchemy + SQLite (로컬 DB)
- yfinance (미국 주가·재무·캘린더)
- FinanceDataReader (한국 주가)
- uvicorn (ASGI 서버)

#### 배포
- Railway (PaaS)
- Nixpacks 빌드 (Python + Node.js)
- 단일 FastAPI 서버가 API + React 빌드 정적 파일 동시 서빙

---

## 2. 배포 아키텍처 (Railway)

### 구조
```
Railway 컨테이너
├── Build Phase
│   ├── npm --prefix frontend install
│   ├── npm --prefix frontend run build  →  frontend/dist/
│   └── pip install -r backend/requirements.txt
└── Run Phase
    └── uvicorn main:app (backend/)
        ├── /api/*          → FastAPI 라우터
        ├── /assets/*       → StaticFiles (frontend/dist/assets)
        └── /*              → SPA fallback (index.html)
```

### 설정 파일

#### `railway.toml`
```toml
[build]
buildCommand = "npm --prefix frontend install && npm --prefix frontend run build && pip install -r backend/requirements.txt"

[deploy]
startCommand = "bash start.sh"
healthcheckPath = "/health"
```

#### `nixpacks.toml`
```toml
providers = ["python", "node"]
```
> Nixpacks가 루트에 `package.json`이 없을 경우 Node.js를 자동 감지하지 못하므로 명시 필요.

#### `start.sh`
```bash
#!/bin/bash
cd "$(dirname "$0")/backend" && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```
> Railway가 주입하는 `$PORT` 환경변수를 사용. 미설정 시 기본 8000.

### Railway 프로젝트 설정 (UI)
| 항목 | 값 |
|------|-----|
| Root Directory | `stock_dashboard` |
| Health Check Path | `/health` |

### 제약 사항
| 항목 | 내용 |
|------|------|
| 파일시스템 | 재배포 시 초기화됨 (SQLite DB 유실). 영구 저장 필요 시 Railway PostgreSQL 플러그인 사용 |
| 포트 | Railway가 `$PORT`로 자동 할당. 고정 포트 사용 불가 |
| 환경변수 | Railway 대시보드 Variables 탭에서 설정 |
| 빌드 시간 | FinanceDataReader, yfinance 등 의존성 설치로 약 2~3분 소요 |

---

## 3. 화면 구조

상단 네비게이션 바에서 아래 3개 메뉴를 탭으로 선택:

```
[ 관심종목 ]  [ 거시변수 ]  [ 캘린더 ]
```

---

## 4. 메뉴별 요구사항

### 4-1. 관심종목

#### 목적
등록된 관심종목의 주가, 시가총액, 주요 재무지표를 한눈에 볼 수 있는 대시보드.

#### 기능 요구사항

| ID | 기능 | 설명 |
|----|------|------|
| W-01 | 종목 등록/삭제 | 티커 심볼 + 시장(US/KR) 선택으로 관심종목 추가·제거 |
| W-02 | 주가 요약 | 현재가, 등락률, 52주 고/저 표시 |
| W-03 | 시가총액 표시 | 종목별 시총 (단위: 조/억) |
| W-04 | 재무제표 요약 | 매출액, 영업이익, 순이익, PER, PBR (최근 8분기) |
| W-05 | 주가 차트 | 종목별 1Y/3Y/5Y 주가 라인차트 |
| W-06 | 정렬/필터 | 시총, 등락률, PER 기준 정렬 |

#### 데이터 소스
| 데이터 | 소스 | 비고 |
|--------|------|------|
| 미국 주가·재무 | `yfinance` | `yf.Ticker(ticker).info` |
| 한국 주가 | `FinanceDataReader` | `fdr.DataReader(ticker)` |
| 한국 기업 정보 | `yfinance` | `yf.Ticker(f"{ticker}.KS").info` |
| 분기 재무제표 | `yfinance` | `yf.Ticker(sym).quarterly_income_stmt` |

#### API 엔드포인트
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/watchlist/` | 전체 관심종목 목록 + 실시간 주가 |
| POST | `/api/watchlist/` | 종목 추가 |
| DELETE | `/api/watchlist/{ticker}` | 종목 삭제 |
| GET | `/api/watchlist/{ticker}/financials` | 분기 재무제표 |
| GET | `/api/watchlist/{ticker}/chart?period=1y` | 주가 차트 데이터 |

#### 화면 레이아웃
```
┌─────────────────────────────────────────────┐
│  + 종목 추가      정렬: [시총 ▼]            │
├──────┬────────┬────────┬────────┬────────────┤
│ 종목 │ 현재가 │ 등락률 │  시총  │ PER / PBR  │
├──────┼────────┼────────┼────────┼────────────┤
│ AAPL │ $189  │ +1.2%  │ 2.9조$ │ 28x / 8.2x │
│ TSLA │ $245  │ -0.8%  │ 0.8조$ │ 65x / 12x  │
│  ... │  ...  │  ...   │  ...   │    ...     │
└──────┴────────┴────────┴────────┴────────────┘

[ 선택 종목 재무제표 상세 패널 ]
매출액 | 영업이익 | 순이익  (최근 8분기 바차트, 단위: 십억)
```

---

### 4-2. 거시변수

#### 목적
주요 거시경제 지표와 시장 인덱스를 최근 5년 차트로 한눈에 확인.

#### 화면 레이아웃
3열 × 2행 = **6개 차트 패널** (각 패널: 지표명 + 라인차트)

```
┌──────────────┬──────────────┬──────────────┐
│ 미국 10Y 금리 │   S&P 500   │  달러 인덱스  │
│  [차트]      │  [차트]      │  [차트]      │
├──────────────┼──────────────┼──────────────┤
│  WTI 유가    │  VIX 지수   │  나스닥 100  │
│  [차트]      │  [차트]      │  [차트]      │
└──────────────┴──────────────┴──────────────┘
```

#### 기본 6개 지표 (yfinance 티커)

| 패널 | 지표명 | 티커 |
|------|--------|------|
| 1 | 미국 10년물 국채금리 | `^TNX` |
| 2 | S&P 500 | `^GSPC` |
| 3 | 달러 인덱스 (DXY) | `DX-Y.NYB` |
| 4 | WTI 원유 | `CL=F` |
| 5 | VIX (공포지수) | `^VIX` |
| 6 | 나스닥 100 | `^NDX` |

#### 교체 가능 프리셋 티커
`^KS11` (KOSPI), `^KQ11` (KOSDAQ), `GC=F` (금), `^IXIC` (나스닥 종합), `^DJI` (다우존스)

#### 기능 요구사항

| ID | 기능 | 설명 |
|----|------|------|
| M-01 | 라인차트 | 각 패널에 일별 데이터 표시 (주간 다운샘플링) |
| M-02 | 기간 선택 | 1Y / 3Y / 5Y 버튼으로 기간 변경 |
| M-03 | 현재값 표시 | 각 패널 상단에 현재 수치 및 전일 대비 등락 표시 |
| M-04 | 지표 교체 | 6개 패널 각각 프리셋 목록에서 원하는 지표로 변경 |
| M-05 | 데이터 갱신 | 페이지 로드 시 자동 갱신 |

#### API 엔드포인트
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/macro/panels` | 현재 6개 패널 설정 조회 |
| PUT | `/api/macro/panels/{slot}` | 패널 지표 변경 |
| GET | `/api/macro/presets` | 교체 가능 지표 목록 |
| GET | `/api/macro/chart/{ticker}?period=5y` | 차트 데이터 |

---

### 4-3. 캘린더

#### 목적
관심종목 실적 발표, Fed 회의, 주요 경제지표 발표 일정을 달력에서 한눈에 확인.

#### 화면 레이아웃
```
┌─────────────────────────┬──────────────────────┐
│                         │  이벤트 필터         │
│   월간 캘린더           │  ☑ Earnings Call     │
│                         │  ☑ Fed Meeting       │
│   (이벤트 아이콘 표시)  │  ☑ CPI 발표          │
│                         │  ☑ PPI 발표          │
│                         │  ☑ 고용보고서        │
│                         │  ☑ PCE 발표          │
│                         │  ☑ GDP 발표          │
│                         │  ☑ FOMC 의사록       │
│                         │  ☑ ISM 제조업PMI     │
│                         │  ☑ 소비자신뢰지수    │
└─────────────────────────┴──────────────────────┘
```

#### 이벤트 10종

| # | 이벤트 | 색상 | key |
|---|--------|------|-----|
| 1 | Earnings Call (관심종목) | 🔵 파랑 `#3b82f6` | `earnings` |
| 2 | Fed Meeting (FOMC) | 🔴 빨강 `#ef4444` | `fed` |
| 3 | CPI 발표 | 🟠 주황 `#f97316` | `cpi` |
| 4 | PPI 발표 | 🟡 노랑 `#eab308` | `ppi` |
| 5 | 고용보고서 (Non-Farm Payroll) | 🟢 초록 `#22c55e` | `nfp` |
| 6 | PCE 발표 | 🟣 보라 `#a855f7` | `pce` |
| 7 | GDP 발표 | 🟤 갈색 `#a16207` | `gdp` |
| 8 | FOMC 의사록 공개 | 연빨강 `#f87171` | `fomc_minutes` |
| 9 | ISM 제조업 PMI | ⚫ 회색 `#6b7280` | `ism` |
| 10 | 소비자신뢰지수 | 🩵 하늘 `#38bdf8` | `consumer` |

#### 기능 요구사항

| ID | 기능 | 설명 |
|----|------|------|
| C-01 | 월간 캘린더 뷰 | react-big-calendar 기반, 기본 월간 보기 |
| C-02 | 이벤트 필터 | 우측 체크박스로 이벤트 종류별 표시/숨김 (DB 저장) |
| C-03 | 이벤트 클릭 | 클릭 시 상세 정보 카드 표시 |
| C-04 | 관심종목 연동 | 관심종목 탭 종목의 실적 일정 자동 반영 |
| C-05 | D-day 표시 | 다가오는 이벤트까지 남은 일수 표시 |

#### 데이터 소스
| 데이터 | 소스 |
|--------|------|
| Earnings 날짜 | `yf.Ticker(sym).calendar` |
| Fed/경제지표 | 코드 내 하드코딩 (2025~2026 일정) |

#### API 엔드포인트
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/calendar/events` | 전체 이벤트 목록 (필터 적용) |
| GET | `/api/calendar/filters` | 필터 설정 목록 |
| PUT | `/api/calendar/filters/{key}` | 필터 ON/OFF |

---

## 5. DB 스키마 (SQLite)

| 테이블 | 주요 컬럼 | 용도 |
|--------|-----------|------|
| `watchlist` | ticker, name, market(US/KR), added_at | 관심종목 목록 |
| `macro_panels` | slot(0~5), ticker, label | 거시변수 패널 설정 |
| `event_filters` | key, label, enabled, color | 캘린더 필터 상태 |

> Railway 배포 시 SQLite 파일은 컨테이너 재시작/재배포 시 초기화됨.
> 데이터 영속성이 필요한 경우 Railway PostgreSQL 플러그인 + SQLAlchemy URL 환경변수(`DATABASE_URL`) 방식으로 전환.

---

## 6. 공통 요구사항

| ID | 항목 | 설명 |
|----|------|------|
| G-01 | 반응형 레이아웃 | 데스크탑 기준 (최소 1280px), 모바일 768px 지원 |
| G-02 | 다크 모드 | 기본값 다크 테마 (TailwindCSS `dark` 클래스) |
| G-03 | 로딩 상태 | 데이터 로딩 중 스켈레톤 UI 표시 |
| G-04 | 에러 처리 | API 실패 시 에러 메시지 표시 |
| G-05 | SPA 라우팅 | 모든 비-API 경로는 `index.html` fallback 처리 |

---

## 7. 개발 우선순위

| Phase | 범위 | 목표 |
|-------|------|------|
| Phase 1 | 거시변수 (6개 차트) | 데이터 파이프라인 검증 |
| Phase 2 | 관심종목 테이블 + 재무요약 | 핵심 기능 구현 |
| Phase 3 | 캘린더 + 이벤트 필터 | 일정 관리 완성 |

---

## 8. 확정 사항

| 항목 | 결정 내용 |
|------|----------|
| 배포 플랫폼 | Railway (nixpacks 빌드, 단일 컨테이너) |
| 서빙 방식 | FastAPI가 React 빌드 + API 동시 서빙 (별도 웹서버 없음) |
| 주가 갱신 주기 | 페이지 로드 시 갱신 (yfinance 호출) |
| 한국 주식 지원 | KOSPI / KOSDAQ (FinanceDataReader + yfinance .KS) |
| 사용자 설정 저장 | SQLite DB (관심종목, 패널 설정, 이벤트 필터) |
| 포트 | Railway `$PORT` 환경변수 사용 |
