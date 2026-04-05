"""위비티 (wevity.com) 스크래퍼 - Selenium"""

import re
from datetime import datetime, timedelta
from .base import BaseScraper, Contest

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False


class WevityScraper(BaseScraper):
    SOURCE_NAME = "wevity"
    BASE_URL = "https://www.wevity.com"
    CATEGORIES = [
        "?c=find&s=1&gub=1&cidx=20&mode=ing",
        "?c=find&s=1&gub=1&cidx=21&mode=ing",
        "?c=find&s=1&gub=1&cidx=22&mode=ing",
    ]

    def scrape(self) -> list:
        self.logger.info("Wevity 크롤링 시작")
        if not HAS_SELENIUM:
            self.logger.error("Selenium 없음")
            return []

        contests = []
        seen = set()
        driver = None
        try:
            opts = Options()
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
            opts.add_argument(f"user-agent={self._headers()['User-Agent']}")
            driver = webdriver.Chrome(options=opts)

            for params in self.CATEGORIES:
                try:
                    driver.get(f"{self.BASE_URL}/{params}")
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list > li"))
                        )
                    except Exception:
                        continue
                    self._delay()

                    for item in driver.find_elements(By.CSS_SELECTOR, "ul.list > li"):
                        try:
                            c = self._parse(item)
                            if c and c.id not in seen:
                                seen.add(c.id)
                                contests.append(c)
                        except Exception as e:
                            self.logger.warning(f"파싱 실패: {e}")
                except Exception as e:
                    self.logger.error(f"Wevity 카테고리 실패: {e}")
        except Exception as e:
            self.logger.error(f"Wevity 실패: {e}")
        finally:
            if driver:
                driver.quit()
        self.logger.info(f"Wevity: {len(contests)}개 수집")
        return contests

    def _parse(self, item) -> Contest | None:
        try:
            tit = item.find_element(By.CSS_SELECTOR, "div.tit")
            link = tit.find_element(By.CSS_SELECTOR, "a")
        except Exception:
            return None
        href = link.get_attribute("href") or ""
        title = re.sub(r"\b(신규|NEW|IDEA|SPECIAL)\b", "", link.text.strip()).strip()
        if not title or not href:
            return None
        m = re.search(r"ix=(\d+)", href)
        if not m:
            return None
        url = href if href.startswith("http") else f"{self.BASE_URL}/{href}"
        organizer = ""
        try:
            organizer = item.find_element(By.CSS_SELECTOR, "div.organ").text.strip()
        except Exception:
            pass
        try:
            day_text = item.find_element(By.CSS_SELECTOR, "div.day").text.strip()
        except Exception:
            return None
        if "D+" in day_text:
            return None
        dm = re.search(r"D-(\d+)", day_text)
        if not dm:
            return None
        deadline = (datetime.now() + timedelta(days=int(dm.group(1)))).strftime("%Y-%m-%d")
        return Contest(
            id=f"wevity-{m.group(1)}", title=title, description="",
            organizer=organizer, deadline=deadline,
            start_date=datetime.now().strftime("%Y-%m-%d"),
            prize="", url=url, thumbnail_url="",
            category=self._categorize(title), source=self.SOURCE_NAME,
            tags=self._extract_tags(title), scraped_at=self.now(),
        )
