"""데이콘 (dacon.io) 스크래퍼"""

import re
import json
import requests
from datetime import datetime
from .base import BaseScraper, Contest


class DaconScraper(BaseScraper):
    SOURCE_NAME = "dacon"
    BASE_URL = "https://dacon.io"
    LIST_URL = "https://dacon.io/competitions/"

    def scrape(self) -> list:
        self.logger.info("Dacon 크롤링 시작")
        contests = []
        try:
            resp = requests.get(self.LIST_URL, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            comp_data = self._extract_nuxt(resp.text)
            if not comp_data:
                self.logger.warning("Dacon: __NUXT__ 데이터 없음")
                return []
            self.logger.info(f"Dacon: {len(comp_data)}개 발견")
            for item in comp_data:
                try:
                    c = self._parse(item)
                    if c:
                        contests.append(c)
                except Exception as e:
                    self.logger.warning(f"Dacon 파싱 실패: {e}")
        except Exception as e:
            self.logger.error(f"Dacon 실패: {e}")
        self.logger.info(f"Dacon: {len(contests)}개 수집")
        return contests

    def _extract_nuxt(self, html: str):
        m = re.search(r"window\.__NUXT__\s*=\s*(.+?);\s*</script>", html, re.DOTALL)
        if not m:
            return None
        raw = m.group(1).strip()
        try:
            return self._find_comp(json.loads(raw))
        except Exception:
            pass
        try:
            return self._parse_iife(raw)
        except Exception as e:
            self.logger.warning(f"IIFE 파싱 실패: {e}")
        return None

    def _find_comp(self, data: dict):
        for item in data.get("data", []):
            if isinstance(item, dict) and "compData" in item:
                return item["compData"]
        return None

    def _parse_iife(self, raw: str):
        pm = re.match(r"\(?\s*function\s*\(([^)]*)\)", raw)
        if not pm:
            return None
        params = [p.strip() for p in pm.group(1).split(",")]
        half = len(raw) // 2
        ab = re.search(r"\}\s*\(", raw[half:])
        if not ab:
            return None
        arg_start = half + ab.end()
        arg_end = len(raw.rstrip()) - 2
        args = self._tokenize(raw[arg_start:arg_end])
        count = min(len(params), len(args))
        var_map = dict(zip(params[:count], args[:count]))

        bm = re.search(r"\breturn\s+(\{.+\})\s*\}", raw, re.DOTALL)
        if not bm:
            return None
        body = bm.group(1)
        body = re.sub(r"\bvoid\s+0\b", "null", body)

        def sub(m):
            n = m.group(1)
            return var_map.get(n, n) if n not in ("true", "false", "null") else m.group(0)

        body = re.sub(r"(?<=:)\s*([a-zA-Z_]\w*)\s*(?=[,}\]])", sub, body)
        body = re.sub(r"(?<=[\[,])\s*([a-zA-Z_]\w*)\s*(?=[,\]])", sub, body)
        body = re.sub(r"(?<=[{,])\s*([a-zA-Z_]\w*)\s*:", r'"\1":', body)
        body = re.sub(r",\s*([}\]])", r"\1", body)
        return self._find_comp(json.loads(body))

    def _tokenize(self, s: str) -> list:
        tokens, cur, depth, in_str, sc = [], [], 0, False, None
        i = 0
        while i < len(s):
            ch = s[i]
            if in_str:
                cur.append(ch)
                if ch == "\\" and i + 1 < len(s):
                    cur.append(s[i + 1]); i += 2; continue
                if ch == sc:
                    in_str = False
            elif ch in ('"', "'"):
                in_str, sc = True, ch; cur.append(ch)
            elif ch in "([{":
                depth += 1; cur.append(ch)
            elif ch in ")]}":
                depth -= 1; cur.append(ch)
            elif ch == "," and depth == 0:
                t = "".join(cur).strip()
                tokens.append("null" if t == "void 0" else t); cur = []
            else:
                cur.append(ch)
            i += 1
        t = "".join(cur).strip()
        if t:
            tokens.append("null" if t == "void 0" else t)
        return tokens

    def _parse(self, item: dict):
        cid = item.get("cpt_id")
        name = (item.get("name") or "").strip()
        if not cid or not name:
            return None
        deadline = self._date(item.get("period_end", ""))
        if not deadline:
            return None
        start = self._date(item.get("period_start", "")) or datetime.now().strftime("%Y-%m-%d")
        prize_raw = str(item.get("prize", "0"))
        prize = f"{prize_raw}만원" if prize_raw and prize_raw != "0" else ""
        kw = item.get("keyword", "") or ""
        tags = [t.strip() for t in kw.split("|") if t.strip()][:5]
        return Contest(
            id=f"dacon-{cid}", title=name, description="",
            organizer=item.get("sponsor", "") or "",
            deadline=deadline, start_date=start, prize=prize,
            url=f"{self.BASE_URL}/competitions/official/{cid}/overview",
            thumbnail_url="", category=self._categorize(name, kw),
            source=self.SOURCE_NAME, tags=tags, scraped_at=self.now(),
        )

    def _date(self, s: str):
        if not s:
            return None
        m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
        return m.group(1) if m else None
