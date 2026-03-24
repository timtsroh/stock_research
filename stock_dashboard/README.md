# Stock Research Dashboard

관심종목·거시변수·캘린더를 한 화면에서 확인하는 개인용 주식 리서치 대시보드.

## 실행 방법

### 백엔드

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## 구조

```
dashboard/
├── backend/
│   ├── main.py                      # FastAPI 앱
│   ├── database.py                  # SQLite 초기화
│   ├── routers/
│   │   ├── watchlist.py             # 관심종목 CRUD + 주가/재무
│   │   ├── macro.py                 # 거시변수 차트
│   │   └── calendar_events.py       # 경제 이벤트 캘린더
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # 탭 네비게이션
│   │   ├── pages/
│   │   │   ├── WatchlistPage.jsx    # 관심종목 탭
│   │   │   ├── MacroPage.jsx        # 거시변수 탭
│   │   │   └── CalendarPage.jsx     # 캘린더 탭
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js               # /api → localhost:8000 프록시
└── PRD.md
```

## 주요 기능

| 탭 | 기능 |
|----|------|
| 관심종목 | 미국·한국 주식 추가/삭제, 주가·시총·PER·PBR 테이블, 재무 분기 차트 |
| 거시변수 | 3×2 차트 (금리/S&P500/DXY/WTI/VIX/나스닥), 1Y·3Y·5Y 전환, 패널 지표 교체 |
| 캘린더 | FOMC·CPI·NFP 등 10종 이벤트, 체크박스 필터, D-day 카운트 |

## 데이터 소스
- 주가·재무: `yfinance`
- 한국 주식: `FinanceDataReader`
- 설정 저장: SQLite (`stock_dashboard.db`)
- 데이터 갱신: 1시간 주기 (API 호출 시 최신화)
