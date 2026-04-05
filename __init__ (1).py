"""크롤러 메인 - 모든 스크래퍼 실행 후 데이터 병합"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .scrapers import ContestKoreaScraper, ThinkContestScraper, LinkareerScraper, WevityScraper, DaconScraper
from .utils.dedup import deduplicate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")

DATA_DIR = Path(__file__).parent.parent / "data"
CONTESTS_FILE = DATA_DIR / "contests.json"
METADATA_FILE = DATA_DIR / "metadata.json"
RETENTION_DAYS = 90


def load_existing() -> list:
    if CONTESTS_FILE.exists():
        try:
            with open(CONTESTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("contests", [])
        except Exception as e:
            logger.warning(f"기존 데이터 로드 실패: {e}")
    return []


def cleanup(contests: list) -> list:
    cutoff = (datetime.now() - timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d")
    before = len(contests)
    contests = [c for c in contests if c.get("deadline", "9999-99-99") >= cutoff]
    removed = before - len(contests)
    if removed:
        logger.info(f"{removed}개 오래된 공모전 정리")
    return contests


def run_scraper(scraper_class, metadata: dict) -> list:
    name = getattr(scraper_class, "SOURCE_NAME", scraper_class.__name__)
    try:
        items = scraper_class().scrape()
        contests = [item.to_dict() for item in items]
        metadata["sources"][name] = {
            "lastSuccess": datetime.now().isoformat(),
            "count": len(contests),
            "errors": [],
        }
        logger.info(f"{name}: {len(contests)}개 수집 성공")
        return contests
    except Exception as e:
        logger.error(f"{name} 실패: {e}")
        metadata["sources"].setdefault(name, {})["errors"] = [
            {"time": datetime.now().isoformat(), "message": str(e)}
        ]
        return []


def main():
    logger.info("=== 크롤링 시작 ===")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    metadata = {"lastCrawl": datetime.now().isoformat(), "sources": {}}
    existing = load_existing()
    logger.info(f"기존 데이터: {len(existing)}개")

    scrapers = [ContestKoreaScraper, ThinkContestScraper, LinkareerScraper, WevityScraper, DaconScraper]
    new_contests = []
    success_count = 0

    for scraper_class in scrapers:
        results = run_scraper(scraper_class, metadata)
        if results:
            new_contests.extend(results)
            success_count += 1

    if success_count == 0:
        logger.error("모든 스크래퍼 실패!")
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        sys.exit(1)

    logger.info(f"새로 수집: {len(new_contests)}개 (성공: {success_count}/{len(scrapers)})")

    # 성공한 소스의 기존 데이터는 교체, 실패한 소스는 유지
    succeeded = {
        s.SOURCE_NAME for s in scrapers
        if metadata["sources"].get(s.SOURCE_NAME, {}).get("count", 0) > 0
        or not metadata["sources"].get(s.SOURCE_NAME, {}).get("errors")
    }
    retained = [c for c in existing if c.get("source") not in succeeded]
    all_contests = deduplicate(new_contests + retained)

    today = datetime.now().strftime("%Y-%m-%d")
    for c in all_contests:
        if c.get("deadline", "9999-99-99") < today:
            c["status"] = "completed"
        else:
            c.setdefault("status", "active")

    all_contests = cleanup(all_contests)
    all_contests.sort(key=lambda c: c.get("deadline", "9999-99-99"))

    logger.info(f"최종: {len(all_contests)}개")

    with open(CONTESTS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "lastUpdated": datetime.now().isoformat(),
            "totalCount": len(all_contests),
            "contests": all_contests,
        }, f, ensure_ascii=False, indent=2)

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info("=== 크롤링 완료 ===")


if __name__ == "__main__":
    main()
