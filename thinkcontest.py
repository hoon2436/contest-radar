"""링커리어 (linkareer.com) 스크래퍼 - Selenium"""

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

IT_KEYWORDS = [
    "ai", "인공지능", "sw", "소프트웨어", "코딩", "프로그래밍", "해커톤",
    "hackathon", "데이터", "블록체인", "ict", "it", "앱", "웹", "개발",
    "알고리즘", "로봇", "디지털", "클라우드", "보안", "게임", "iot",
    "빅데이터", "머신러닝", "딥러닝", "gpt", "llm", "과학", "공학", "테크",
]


class LinkareerScraper(BaseScraper):
    SOURCE_NAME = "linkareer"
    BASE_URL = "https://linkareer.com"
    LIST_URL = "https://linkareer.com/list/contest?filterBy_status=OPEN&orderBy_direction=DESC&orderBy_field=CREATED_AT"

    def scrape(self) -> list:
        self.logger.info("Linkareer 크롤링 시작")
        if not HAS_SELENIUM:
            self.logger.error("Selenium 없음")
            return []

        contests = []
        driver = None
        try:
            opts = Options()
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
            opts.add_argument(f"user-agent={self._headers()['User-Agent']}")
            driver = webdriver.Chrome(options=opts)
            driver.get(self.LIST_URL)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/activity/']"))
                )
            except Exception:
                self.logger.warning("Linkareer: 로딩 타임아웃")
                return []
            self._delay()

            cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/activity/']")
            self.logger.info(f"Linkareer: {len(cards)}개 링크 발견")

            seen = set()
            for card in cards:
                try:
                    href = card.get_attribute("href") or ""
                    id_m = re.search(r"/activity/(\d+)", href)
                    if not id_m or id_m.group(1) in seen:
                        continue
                    node_id = id_m.group(1)

                    title = ""
                    for sel in ["h5", "h4", "h3", "[class*='title']", "strong", "span"]:
                        try:
                            el = card.find_element(By.CSS_SELECTOR, sel)
                            t = el.text.strip()
                            if t and len(t) >= 3:
                                title = t
                                break
                        except Exception:
                            continue

                    if not title:
                        lines = [l.strip() for l in card.text.split("\n") if len(l.strip()) >= 3]
                        title = max(lines, key=len) if lines else ""

                    title = re.sub(r"^추천\s*", "", title)
                    if not title or len(title) < 3:
                        continue
                    if not any(kw in title.lower() for kw in IT_KEYWORDS):
                        continue
                    seen.add(node_id)

                    organizer = ""
                    try:
                        organizer = card.find_element(By.CSS_SELECTOR, "p[class*='organization']").text.strip()
                    except Exception:
                        pass

                    deadline = datetime.now().strftime("%Y-%m-%d")
                    dm = re.search(r"D-(\d+)", card.text)
                    if dm:
                        deadline = (datetime.now() + timedelta(days=int(dm.group(1)))).strftime("%Y-%m-%d")

                    contests.append(Contest(
                        id=f"linkareer-{node_id}", title=title, description="",
                        organizer=organizer, deadline=deadline,
                        start_date=datetime.now().strftime("%Y-%m-%d"),
                        prize="", url=href, thumbnail_url="",
                        category=self._categorize(title), source=self.SOURCE_NAME,
                        tags=self._extract_tags(title), scraped_at=self.now(),
                    ))
                except Exception as e:
                    self.logger.warning(f"항목 실패: {e}")
        except Exception as e:
            self.logger.error(f"Linkareer 실패: {e}")
        finally:
            if driver:
                driver.quit()
        self.logger.info(f"Linkareer: {len(contests)}개 수집")
        return contests
