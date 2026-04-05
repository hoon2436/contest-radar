"""공모전 중복 제거"""

import re


def normalize_title(title: str) -> str:
    return re.sub(r"[^\w가-힣]", "", title).lower()


def deduplicate(contests: list) -> list:
    seen_ids: dict = {}
    seen_titles: dict = {}
    result = []

    for c in contests:
        cid = c["id"]
        if cid in seen_ids:
            if c.get("scrapedAt", "") > seen_ids[cid].get("scrapedAt", ""):
                seen_ids[cid] = c
                result = [x for x in result if x["id"] != cid]
                result.append(c)
            continue

        nt = normalize_title(c.get("title", ""))
        if nt in seen_titles:
            if c.get("scrapedAt", "") > seen_titles[nt].get("scrapedAt", ""):
                seen_titles[nt] = c
                result = [x for x in result if normalize_title(x.get("title", "")) != nt]
                result.append(c)
            continue

        seen_ids[cid] = c
        seen_titles[nt] = c
        result.append(c)

    return result
