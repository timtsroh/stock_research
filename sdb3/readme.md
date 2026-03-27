# Stock Research Dashboard

PRD1 기준 개인용 주식 투자 대시보드입니다.

## 포함 기능

- 관심종목: 종목 추가/삭제, 시세/시총/PER/PBR/52주 고저, 상세 차트, 최근 분기 재무
- 거시변수: 6개 패널, 1Y/3Y/5Y 전환, 패널별 지표 교체
- 캘린더: 월간/주간 보기, 이벤트 필터, D-Day, 관심종목 실적 일정 연동
- 공통: 다크 UI, 반응형 레이아웃, 1시간 캐시, API 실패 시 캐시 fallback

## 로컬 실행

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 배포

- Railway: 현재 저장소에 있는 `railway.toml`과 `start.sh`로 바로 배포하기 가장 편합니다.
- Vercel: 프론트엔드 단독 배포는 좋지만, 현재처럼 FastAPI 백엔드와 SQLite를 함께 운용할 때는 추가 분리가 필요합니다.
