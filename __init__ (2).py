"""Discord 웹훅 알림 전송"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("notify")

DATA_DIR = Path(__file__).parent.parent / "data"
CONTESTS_FILE = DATA_DIR / "contests.json"
NOTIFIED_FILE = DATA_DIR / "notified.json"

# 카테고리별 색상 (Discord embed color)
COLORS = {
    "algorithm":  0x3498DB,  # 파랑
    "hackathon":  0xE74C3C,  # 빨강
    "ai_ml":      0x9B59B6,  # 보라
    "web_mobile": 0x2ECC71,  # 초록
    "game":       0xF39C12,  # 주황
    "security":   0x1ABC9C,  # 청록
    "data":       0x34495E,  # 어두운 파랑
    "iot":        0xE67E22,  # 오렌지
    "sw_general": 0x2980B9,  # 파랑
    "other":      0x95A5A6,  # 회색
}

LABELS = {
    "algorithm":  "알고리즘",
    "hackathon":  "해커톤",
    "ai_ml":      "AI/ML",
    "web_mobile": "웹/모바일",
    "game":       "게임",
    "security":   "보안",
    "data":       "데이터",
    "iot":        "IoT",
    "sw_general": "SW 일반",
    "other":      "기타",
}

SOURCE_LABELS = {
    "dacon":        "데이콘",
    "wevity":       "위비티",
    "linkareer":    "링커리어",
    "thinkcontest": "씽굿",
    "contestkorea": "컨테스트코리아",
}


def load_notified() -> set:
    if NOTIFIED_FILE.exists():
        try:
            with open(NOTIFIED_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_notified(ids: set):
    with open(NOTIFIED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f, ensure_ascii=False, indent=2)


def dday(deadline: str) -> str:
    try:
        d = datetime.strptime(deadline, "%Y-%m-%d")
        diff = (d - datetime.now()).days
        if diff < 0:
            return f"D+{abs(diff)}"
        if diff == 0:
            return "🔥 D-Day"
        return f"D-{diff}"
    except ValueError:
        return ""


def build_embed(c: dict) -> dict:
    cat = c.get("category", "other")
    dd = dday(c.get("deadline", ""))
    deadline_str = c.get("deadline", "미정")
    if dd:
        deadline_str = f"{deadline_str} ({dd})"

    fields = [
        {"name": "🏢 주최", "value": c.get("organizer", "-") or "-", "inline": True},
        {"name": "📅 마감", "value": deadline_str, "inline": True},
        {"name": "🏷️ 분류", "value": LABELS.get(cat, "기타"), "inline": True},
    ]
    if c.get("prize"):
        fields.append({"name": "🏆 시상", "value": c["prize"], "inline": True})
    if c.get("source"):
        fields.append({"name": "🔗 출처", "value": SOURCE_LABELS.get(c["source"], c["source"]), "inline": True})
    if c.get("tags"):
        fields.append({"name": "🔖 태그", "value": " ".join(f"`{t}`" for t in c["tags"][:5]), "inline": False})

    embed = {
        "title": c.get("title", "제목 없음"),
        "url": c.get("url", ""),
        "color": COLORS.get(cat, 0x95A5A6),
        "fields": fields,
        "footer": {"text": "공모전 알리미 🤖"},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if c.get("thumbnailUrl"):
        embed["thumbnail"] = {"url": c["thumbnailUrl"]}
    return embed


def send(webhook_url: str, embeds: list):
    for i in range(0, len(embeds), 10):
        batch = embeds[i:i + 10]
        content = f"**🎉 새로운 공모전 {len(batch)}개가 등록되었습니다!**" if i == 0 else None
        payload = json.dumps({
            "username": "공모전 알리미",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/2721/2721297.png",
            "content": content,
            "embeds": batch,
        }).encode("utf-8")

        req = Request(webhook_url, data=payload, headers={
            "Content-Type": "application/json",
            "User-Agent": "ContestBot/1.0",
        })
        try:
            with urlopen(req) as resp:
                logger.info(f"웹훅 전송 성공 (batch {i // 10 + 1}, status {resp.status})")
        except URLError as e:
            logger.error(f"웹훅 전송 실패: {e}")


def main():
    # 환경변수 없으면 하드코딩된 URL 사용 (GitHub Actions에서는 secret 사용 권장)
    webhook_url = os.environ.get(
        "DISCORD_WEBHOOK_URL",
        "https://discord.com/api/webhooks/1489980832906219713/7M83nPWgK8lkd5XfaJ4MvJXOZScPxYAoj2_bn3OBzr6zTrGaKy1ZINHd_fEvoOVAke2-"
    )

    if not CONTESTS_FILE.exists():
        logger.warning("contests.json 없음")
        return

    with open(CONTESTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    active = [c for c in data.get("contests", []) if c.get("status") == "active"]
    notified = load_notified()
    new = [c for c in active if c["id"] not in notified]

    if not new:
        logger.info("새 공모전 없음")
        return

    logger.info(f"새 공모전 {len(new)}개 알림 전송")
    send(webhook_url, [build_embed(c) for c in new])

    notified.update(c["id"] for c in new)
    save_notified(notified)
    logger.info("알림 완료")


if __name__ == "__main__":
    main()
