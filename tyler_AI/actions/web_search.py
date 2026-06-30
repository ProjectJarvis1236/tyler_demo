import logging
import time
import hashlib
import requests

import configs

logger = logging.getLogger(__name__)


class WebSearch:
    def __init__(self):
        self.cache = {}
        self.api_key = configs.WEB_API_KEY

    def _cache_key(self, query: str):
        return hashlib.md5(query.encode()).hexdigest()

    def _get_cache(self, query: str):
        key = self._cache_key(query)
        item = self.cache.get(key)

        if item and time.time() - item["time"] < 3600:
            return item["data"]

        return None

    def _set_cache(self, query: str, data):
        key = self._cache_key(query)
        self.cache[key] = {"data": data, "time": time.time()}

    def search_text(self, query: str):
        print(f"[Tavily] query: {query}")

        cached = self._get_cache(query)
        if cached:
            return cached

        try:
            url = "https://api.tavily.com/search"

            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": False,
                "max_results": 5
            }

            r = requests.post(url, json=payload, timeout=10)
            data = r.json()

            results = []

            for item in data.get("results", []):
                results.append({
                    "title": item.get("title"),
                    "link": item.get("url"),
                    "snippet": item.get("content")
                })

            print(f"[Tavily] results: {len(results)}")

            self._set_cache(query, results)
            return results

        except Exception as e:
            print(f"[Tavily ERROR]: {e}")
            return []

    def search_video(self, query, platform="youtube"):
        if platform == "youtube":
            return f"https://www.youtube.com/results?search_query={query}"

        return f"https://yandex.ru/video/search?text={query}"

    def generate_url(self, query: str, platform: str, type_: str):
        template = configs.SEARCH_WEB.get(platform).get(type_)
        return template.format(query=query)


    def search_wikipedia(self, query: str):
        try:
            url = "https://ru.wikipedia.org/w/api.php"

            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "utf8": 1
            }

            res = requests.get(url, params=params, timeout=5).json()

            results = []

            for item in res.get("query", {}).get("search", [])[:5]:
                title = item["title"]
                link = f"https://ru.wikipedia.org/wiki/{title.replace(' ', '_')}"
                snippet = item.get("snippet", "")

                results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })

            return results

        except Exception:
            return []