"""컨테스트코리아 (contestkorea.com) 스크래퍼"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, Contest
from ..utils.date_parser import parse_korean_date


class ContestKoreaScraper(BaseScraper):
    SOURCE_NAME = "contestkorea"
    BASE_URL = "https://www.contestkorea.com"
    LIST_URL = "https://www.contestkorea.com/sub/list.php"

    def scrape(self) -> list:
        self.logger.info("ContestKorea 크롤링 시작")
        contests = []
        try:
            resp = requests.get(
                self.LIST_URL,
                params={"int_gbn": "1", "Txt_bcode": "030310001"},
                headers=self._headers(), timeout=15,
            )
            resp.raise_for_status()
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            items = []
            for div in soup.select("div.title"):
                link = div.select_one('a[href*="view.php"]')
                if link:
                    li = div.find_parent("li")
                    if li:
                        items.append(li)

            self.logger.info(f"ContestKorea: {len(items)}개 발견")
            for item in items:
                try:
                    c = self._parse(item)
                    if c:
                        contests.append(c)
                except Exception as e:
                    self.logger.warning(f"파싱 실패: {e}")
        except Exception as e:
            self.logger.error(f"ContestKorea 실패: {e}")
        self.logger.info(f"ContestKorea: {len(contests)}개 수집")
        return contests

    def _parse(self, item) -> Contest | None:
        link = item.select_one('div.title a[href*="view.php"]')
        if not link:
            return None
        href = link.get("href", "")
        m = re.search(r"str_no=(\w+)", href)
        if not m:
            return None
        url = href if href.startswith("http") else f"{self.BASE_URL}/sub/{href}"
        title_tag = item.select_one("span.txt")
        title = title_tag.get_text(strip=True) if title_tag else ""
        if not title:
            return None

        organizer = ""
        org = item.select_one("ul.host li.icon_1")
        if org:
            organizer = re.sub(r"^주최\s*[.·]\s*", "", org.get_text(strip=True))

        deadline = start_date = None
        step1 = item.select_one(".date-detail .step-1")
        if step1:
            date_text = re.sub(r"^접수\s*", "", step1.get_text(strip=True))
            parts = re.split(r"\s*[~～–]\s*", date_text)
            if len(parts) >= 2:
                start_date = parse_korean_date(parts[0])
                deadline = parse_korean_date(parts[-1])
            else:
                deadline = parse_korean_date(date_text)

        if not deadline:
            return None
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")

        img = item.select_one("div.title img")
        thumbnail = ""
        if img:
            src = img.get("src", "")
            thumbnail = src if src.startswith("http") else f"{self.BASE_URL}{src}"

        return Contest(
            id=f"contestkorea-{m.group(1)}", title=title, description="",
            organizer=organizer, deadline=deadline, start_date=start_date,
            prize="", url=url, thumbnail_url=thumbnail,
            category=self._categorize(title), source=self.SOURCE_NAME,
            tags=self._extract_tags(title), scraped_at=self.now(),
        )
