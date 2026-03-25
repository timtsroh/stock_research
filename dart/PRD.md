# PRD: DART 전자공시 텔레그램 피드 봇

## 1. 개요

Google Sheets에 등록된 한국 기업 목록(Light, Atom 시트)을 기반으로 금융감독원 DART(전자공시시스템) OpenAPI를 통해 신규 공시를 수집하고, 매일 2회 Telegram 채널로 자동 발송하는 파이프라인.
`news_kor` 프로젝트와 동일한 기업 목록 및 채널 구조를 재사용하며, 뉴스가 아닌 공식 공시 정보를 피드한다.

---

## 2. 목표

- 관심 기업의 신규 공시(사업보고서, 수시공시, 주요사항보고 등)를 수동 확인 없이 자동 수집
- Telegram 채널을 통해 뉴스피드와 동일한 구조로 공시 알림 전달
- GitHub Actions로 완전 자동화 (서버 불필요)
- `news_kor`와 동일한 Google Sheets 기업 목록 공유

---

## 3. DART OpenAPI 개요

| 항목 | 내용 |
|---|---|
| 제공 기관 | 금융감독원 (FSS) |
| API 포털 | https://opendart.fss.or.kr |
| 인증 방식 | API Key (쿼리 파라미터 `crtfc_key`) |
| 기업 식별자 | `corp_code` (8자리 고유 번호) |
| 공시목록 엔드포인트 | `GET https://opendart.fss.or.kr/api/list.json` |

### 3.1 corp_code 조회 전략

Google Sheets의 **D열**에 각 기업의 DART `corp_code`가 미리 기재되어 있다.
실행 시 회사명(B열)과 corp_code(D열)를 함께 읽어 사용한다. 별도 매핑 테이블 구성 불필요.

### 3.2 공시목록 조회 파라미터

| 파라미터 | 설명 | 사용 값 |
|---|---|---|
| `crtfc_key` | API 인증키 | 환경 변수 |
| `corp_code` | 기업 고유 코드 | 시트 D열에서 읽은 값 |
| `bgn_de` | 시작일 (YYYYMMDD) | 실행 기준 전날 |
| `end_de` | 종료일 (YYYYMMDD) | 실행 당일 |
| `last_reprt_at` | 최종보고서 여부 | `N` (전체) |
| `page_count` | 페이지당 건수 | `10` |

### 3.3 주요 공시 유형 (pblntf_ty)

| 코드 | 분류 |
|---|---|
| `A` | 정기공시 (사업보고서, 반기보고서 등) |
| `B` | 주요사항보고 (유상증자, 자기주식 등) |
| `C` | 발행공시 |
| `D` | 지분공시 |
| `E` | 기타공시 |
| `F` | 외부감사 관련 |

→ 초기 범위: **전체** (`pblntf_ty` 파라미터 생략, 모든 유형 수집)

---

## 4. 주요 구성 요소

| 구성 요소 | 역할 | 세부 내용 |
|---|---|---|
| Google Sheets | 기업 목록 + corp_code 소스 | Light/Atom 시트 B열(회사명), D열(corp_code) |
| DART OpenAPI | 공시 수집 | `opendart.fss.or.kr/api/list.json` |
| Telegram Bot | 공시 발송 | Light/Atom 각각 별도 채널 |
| GitHub Actions | 스케줄 실행 | 매일 06:00, 18:00 KST |

---

## 5. 외부 연동 정보

| 항목 | 값 |
|---|---|
| Google Sheets URL | `https://docs.google.com/spreadsheets/d/1sfDjoKbrEbKvA0qwMA1nPdcEu628YgNX0A_JLLOB4WA/edit` |
| Light 시트 | B열(회사명), D열(corp_code) |
| Atom 시트 | B열(회사명), D열(corp_code) |
| DART API 포털 | `https://opendart.fss.or.kr` |
| DART 공시목록 엔드포인트 | `https://opendart.fss.or.kr/api/list.json` |
| 공시 상세 링크 | `https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp_no}` |
| GitHub 레포 | `https://github.com/timtsroh/stock_research` |
| 코드 경로 | `dart/` |

---

## 6. 기능 요구사항

### 6.1 Google Sheets 기업 목록 읽기

- `news_kor/sheets_reader.py`의 구조를 참고하여 `get_companies_with_corp_code(sheet_id, sheet_name)` 구현
- B열(name_col=2): 회사명
- D열(corp_code_col=4): DART corp_code
- 첫 행(헤더) 항상 스킵, 빈 셀 스킵
- `corp_code`가 없는 행은 스킵 + 로그 출력
- 반환 형태: `[(corp_name, corp_code), ...]`

### 6.2 DART 공시 조회

- 각 기업의 `corp_code`로 `/api/list.json` 호출
- 조회 기간: 최근 12시간 (news_kor와 동일한 시간 윈도우)
  - `bgn_de`: 전일 날짜
  - `end_de`: 당일 날짜
  - 응답 결과에서 `rcept_dt` 기준 12시간 이내 항목만 최종 필터링
- 회사당 최대 3건
- 중복 접수번호(`rcept_no`) 필터링 (동일 실행 내)

**응답 필드 활용:**

| 필드 | 설명 | 활용 |
|---|---|---|
| `rcept_no` | 접수번호 | 상세 링크 생성, 중복 제거 키 |
| `corp_name` | 회사명 | 표시용 |
| `report_nm` | 보고서명 | 공시 제목 |
| `rcept_dt` | 접수일자 (YYYYMMDD) | 시간 필터링 |
| `flr_nm` | 공시 제출인 | 표시용 |
| `rm` | 비고 | 정정/첨부 여부 |

### 6.3 Telegram 발송

- `news_kor/telegram_sender.py`의 구조를 참고하여 별도 `telegram_sender.py` 작성
- 한 피드(Light 또는 Atom)의 모든 회사 공시를 하나의 메시지로 통합 전송
- Light → `TELEGRAM_CHAT_ID_Light` 채널
- Atom → `TELEGRAM_CHAT_ID_Atom` 채널
- HTML `parse_mode` 사용
- 공시가 0건인 회사는 메시지에서 생략
- 전체 공시가 0건이면 메시지 미전송

**메시지 형식:**
```
📋 등대 포트폴리오 DART 공시피드
🕐 2026-03-25 06:00 KST

<b>삼성전자</b>
주요사항보고서(자기주식취득결정)
https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260325000123
제출인: 삼성전자 | 2026-03-25

<b>SK하이닉스</b>
...
```

### 6.4 실행 로직 흐름

```
main.py 실행
  │
  ├─ 환경 변수 로드
  │
  ├─ [Light 피드]
  │     ├─ Light 시트 B열(회사명) + D열(corp_code) 로드
  │     ├─ 각 회사 DART 공시 조회 (최근 12시간, 최대 3건)
  │     ├─ 공시 있는 회사만 메시지 구성
  │     └─ 통합 메시지 → TELEGRAM_CHAT_ID_Light 전송
  │
  └─ [Atom 피드]
        ├─ Atom 시트 B열(회사명) + D열(corp_code) 로드
        ├─ 각 회사 DART 공시 조회 (최근 12시간, 최대 3건)
        ├─ 공시 있는 회사만 메시지 구성
        └─ 통합 메시지 → TELEGRAM_CHAT_ID_Atom 전송
```

---

## 7. 비기능 요구사항

- **Rate Limiting**: 회사별 DART API 호출 사이 0.5초 딜레이
- **에러 처리**: API 호출 실패 시 해당 회사 스킵, 로그 출력 후 계속 진행
- **타임존**: 모든 시간 표시는 KST (UTC+9)
- **로그**: 실행 시작/종료, 처리 회사 수, 수집 공시 수, 전송 여부 출력
- **의존성 최소화**: `news_kor`와 동일한 라이브러리 범위 내에서 구현

---

## 8. 파일 구조

```
stock_research/
├── .github/
│   └── workflows/
│       ├── news_kor.yml          (기존)
│       └── dart.yml              (신규)
├── news_kor/                     (기존)
└── dart/                         (신규)
    ├── PRD.md
    ├── main.py                   # 진입점 및 오케스트레이션
    ├── sheets_reader.py          # Google Sheets 연동 (B열 + D열 읽기)
    ├── dart_fetcher.py           # DART API 연동 (공시 조회)
    ├── telegram_sender.py        # 메시지 포맷 + Telegram 전송
    ├── requirements.txt
    ├── .env.example
    └── .env                      (gitignore)
```

---

## 9. 환경 변수 / GitHub Secrets

| Secret 이름 | 설명 | 신규 여부 |
|---|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google 서비스 계정 JSON | 재사용 (news_kor와 동일) |
| `GOOGLE_SHEET_ID` | 스프레드시트 ID | 재사용 |
| `DART_API_KEY` | DART OpenAPI 인증키 | **신규** |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 재사용 |
| `TELEGRAM_CHAT_ID_Light` | Light 포트폴리오 채널 ID | 재사용 |
| `TELEGRAM_CHAT_ID_Atom` | Atom 포트폴리오 채널 ID | 재사용 |

---

## 10. GitHub Actions 스케줄

```yaml
# .github/workflows/dart.yml
on:
  schedule:
    - cron: '10 21 * * *'   # KST 06:10 (news_kor 06:00 이후 10분)
    - cron: '10 9 * * *'    # KST 18:10 (news_kor 18:00 이후 10분)
  workflow_dispatch:          # 수동 트리거 (테스트용)
```

---

## 11. 의존성 (requirements.txt)

```
gspread==6.1.4
google-auth==2.38.0
requests==2.32.3
python-dotenv==1.1.0
pytz==2024.2
```

`news_kor`와 동일한 패키지 세트. 추가 라이브러리 불필요.
