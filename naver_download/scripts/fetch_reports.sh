#!/bin/bash
# fetch_reports.sh
# 네이버 금융 산업분석 페이지에서 특정 날짜의 보고서 목록을 파싱한다.
#
# 사용법:
#   bash fetch_reports.sh <URL> <YESTERDAY>
#
# 인자:
#   URL       - 네이버 금융 섹터 URL (references/naver_urls.md 참조)
#   YESTERDAY - yy.mm.dd 형식의 날짜 (예: 26.03.18)
#
# 출력 형식 (한 줄 = 보고서 1건):
#   BROKER:<증권사>|TITLE:<제목>|PDF:<PDF_URL 또는 빈값>

URL="$1"
YESTERDAY="$2"

curl -s -L --compressed \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept-Language: ko-KR,ko;q=0.9" \
  "$URL" | python3 -c "
import sys, re
content = sys.stdin.buffer.read().decode('euc-kr', errors='replace')
tr_blocks = re.split(r'<tr>', content)
yesterday = '$YESTERDAY'
results = []
for block in tr_blocks:
    date_m = re.search(r'class=\"date\"[^>]*>(\d{2}\.\d{2}\.\d{2})</td>', block)
    if not date_m or date_m.group(1) != yesterday:
        continue
    title_m = re.search(r'<a href=\"industry_read[^\"]+\">([^<]+)</a>', block)
    broker_m = re.search(r'</td>\s*<td>([^<\n]{2,30})</td>\s*<td class=\"file\"', block)
    pdf_m = re.search(r'href=\"(https://stock\.pstatic\.net[^\"]+\.pdf)\"', block)
    title = title_m.group(1).strip() if title_m else ''
    broker = broker_m.group(1).strip() if broker_m else ''
    pdf = pdf_m.group(1) if pdf_m else ''
    if title:
        print(f'BROKER:{broker}|TITLE:{title}|PDF:{pdf}')
"
