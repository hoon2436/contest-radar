"""공모전 스크래퍼 베이스 클래스"""

import time
import random
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Contest:
    id: str
    title: str
    description: str
    organizer: str
    deadline: str
    start_date: str
    prize: str
    url: str
    thumbnail_url: str
    category: str
    source: str
    tags: list = field(default_factory=list)
    scraped_at: str = ""
    status: str = "active"

    def to_dict(self) -> dict:
        d = asdict(self)
        return {
            "id": d["id"],
            "title": d["title"],
            "description": d["description"],
            "organizer": d["organizer"],
            "deadline": d["deadline"],
            "startDate": d["start_date"],
            "prize": d["prize"],
            "url": d["url"],
            "thumbnailUrl": d["thumbnail_url"],
            "category": d["category"],
            "source": d["source"],
            "tags": d["tags"],
            "scrapedAt": d["scraped_at"],
            "status": d["status"],
        }


class BaseScraper(ABC):
    SOURCE_NAME: str = ""
    BASE_URL: str = ""
    MIN_DELAY: float = 1.5
    MAX_DELAY: float = 4.0

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _delay(self):
        time.sleep(random.uniform(self.MIN_DELAY, self.MAX_DELAY))

    def _headers(self) -> dict:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        }

    def _categorize(self, title: str, description: str = "") -> str:
        text = (title + " " + description).lower()
        rules = [
            ("algorithm",  ["알고리즘", "코딩테스트", "프로그래밍 대회"]),
            ("hackathon",  ["해커톤", "hackathon"]),
            ("ai_ml",      ["인공지능", "머신러닝", "딥러닝", "machine learning", "llm", "생성형"]),
            ("web_mobile", ["웹", "앱", "모바일", "프론트엔드", "백엔드"]),
            ("game",       ["게임", "game", "유니티", "언리얼"]),
            ("security",   ["보안", "security", "ctf", "해킹"]),
            ("data",       ["데이터", "data", "빅데이터", "분석"]),
            ("iot",        ["iot", "사물인터넷", "임베디드", "로봇"]),
            ("sw_general", ["소프트웨어", "sw ", "오픈소스", "개발"]),
        ]
        for cat, keywords in rules:
            if any(kw in text for kw in keywords):
                return cat
        return "other"

    def _extract_tags(self, title: str, description: str = "") -> list:
        text = title + " " + description
        candidates = [
            "AI", "인공지능", "해커톤", "웹", "앱", "데이터", "보안",
            "알고리즘", "오픈소스", "클라우드", "IoT", "로봇",
            "SW", "IT", "코딩", "소프트웨어", "게임", "모바일",
            "LLM", "딥러닝", "머신러닝", "스타트업",
        ]
        return [kw for kw in candidates if kw.lower() in text.lower()][:5]

    def now(self) -> str:
        return datetime.now().isoformat()

    @abstractmethod
    def scrape(self) -> list:
        pass
