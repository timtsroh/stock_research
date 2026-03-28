#!/usr/bin/env python3
"""
count_pages.py
PDF 파일의 페이지 수를 반환한다. 외부 라이브러리 없이 바이너리 파싱으로 동작한다.

사용법:
    python3 count_pages.py <filepath>

출력:
    정수 (페이지 수). 파싱 실패 시 0 출력.
"""

import re
import sys


def count_pdf_pages(filepath: str) -> int:
    with open(filepath, "rb") as f:
        content = f.read()

    # /Type /Page 엔트리로 개별 페이지 오브젝트 카운트
    pages = re.findall(rb"/Type\s*/Page[^s]", content)
    if pages:
        return len(pages)

    # 폴백: /Count N 값 중 최대값 사용
    counts = re.findall(rb"/Count\s+(\d+)", content)
    if counts:
        return max(int(c) for c in counts)

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 count_pages.py <filepath>")
        sys.exit(1)

    filepath = sys.argv[1]
    print(count_pdf_pages(filepath))
