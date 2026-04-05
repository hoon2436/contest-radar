"""한국어 날짜 파싱 유틸리티"""

import re
from datetime import datetime, timedelta
from typing import Optional


def parse_korean_date(text: str) -> Optional[str]:
    if not text:
        return None
    text = text.strip()

    # YYYY.MM.DD / YYYY-MM-DD / YYYY/MM/DD
    m = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    # YYYY년 M월 D일
    m = re.search(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    # MM.DD (올해로 가정)
    m = re.search(r"(?<!\d)(\d{1,2})[.\-/](\d{1,2})(?!\d)", text)
    if m:
        year = datetime.now().year
        month, day = int(m.group(1)), int(m.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{year}-{month:02d}-{day:02d}"

    # D-N
    m = re.search(r"D[-–](\d+)", text)
    if m:
        return (datetime.now() + timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d")

    return None
