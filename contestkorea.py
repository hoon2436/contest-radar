"""씽굿 (thinkcontest.com) 스크래퍼 - JSON API"""

import re
import requests
from datetime import datetime
from .base import BaseScraper, Contest
from ..utils.date_parser import parse_korean_date

IT_FIELDS = ["게임", "소프트웨어", "과학", "IT", "ICT", "SW", "AI", "정보통신",
             "컴퓨터", "디지털", "프로그래밍", "코딩", "인공지능", "빅데이터",
             "데이터", "전자", "기술", "테크", "로봇", "웹", "앱", "해커톤", "보안", "IoT"]
IT_TITLES = ["ai", "인공지능", "sw", "소프트웨어", "코딩", "프로그래밍", "해커톤",
             "데이터", "블록체인", "ict", "it", "앱", "웹", "개발", "알고리즘",
             "로봇", "디지털", "보안", "게임", "iot", "머신러닝", "딥러닝", "llm"]


class ThinkContestScraper(BaseScraper):
    SOURCE_NAME = "thinkcontest"
    BASE_URL = "https://www.thinkcontest.com"
    API_URL = "https://www.thinkcontest.com/thinkgood/user/contest/subList.do"

    def scrape(self) -> list:
        self.logger.info("ThinkContest 크롤링 시작")
        contests = []
        try:
            resp = requests.post(
                self.API_URL,
                json={"pageIndex": 1, "pageSize": 50, "sort_type": "REG_DT",
                      "sort_order": "DESC", "search_status": "접수중"},
                headers={**self._headers(), "Content-Type": "application/json"},
                timeout=15,
            )
            resp.raise_for_status()
            items = resp.json().get("listJsonData", [])
            self.logger.info(f"ThinkContest: {len(items)}개 발견")
            for item in items:
                try:
                    c = self._parse(item)
                    if c:
                        contests.append(c)
                except Exception as e:
                    self.logger.warning(f"파싱 실패: {e}")
        except Exception as e:
            self.logger.error(f"ThinkContest 실패: {e}")
        self.logger.info(f"ThinkContest: {len(contests)}개 수집")
        return contests

    def _parse(self, item: dict) -> Contest | None:
        field = item.get("contest_field_nm", "")
        title = (item.get("program_nm") or "").strip()
        if not (any(kw in field for kw in IT_FIELDS) or any(kw in title.lower() for kw in IT_TITLES)):
            return None
        pk = str(item.get("contest_pk", ""))
        if not pk or not title:
            return None

        deadline = self._date(item.get("finish_dt", ""))
        start_date = self._date(item.get("accept_dt", ""))
        if not deadline:
            period = item.get("receive_period", "")
            if period:
                parts = re.split(r"\s*~\s*", period)
                if len(parts) == 2:
                    start_date = start_date or parse_korean_date(parts[0].strip())
                    deadline = parse_korean_date(parts[1].strip())
        if not deadline:
            return None
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")

        poster = item.get("poster_name", "")
        path = item.get("poster_path", "")
        thumbnail = f"{self.BASE_URL}/_attach/thinkgood/{path}{poster}" if poster and path else ""

        return Contest(
            id=f"thinkcontest-{pk}", title=title, description="",
            organizer=item.get("host_company", "") or "",
            deadline=deadline, start_date=start_date,
            prize=item.get("prize_money", "") or "",
            url=f"{self.BASE_URL}/thinkgood/user/contest/view.do?contest_pk={pk}",
            thumbnail_url=thumbnail, category=self._categorize(title),
            source=self.SOURCE_NAME, tags=self._extract_tags(title), scraped_at=self.now(),
        )

    @staticmethod
    def _date(s: str):
        if not s:
            return None
        m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
        return m.group(1) if m else None
