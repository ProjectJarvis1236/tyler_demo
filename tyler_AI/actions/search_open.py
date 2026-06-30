import webbrowser
import logging

from .web_search import WebSearch

logger = logging.getLogger("SearchOpen")


class SearchOpen:
    def __init__(self):
        self.ws = WebSearch()

    async def run(self, params, chat_id: str):
        query = params.get("query")
        search_type = params.get("search_type")
        platform = params.get("platform")

        if not query:
            return "Нет запроса"

        logger.info(f"Поиск: type={search_type}, query={query}")

        results = []

        if search_type == "text":
            results = self.ws.search_text(query)

            logger.info(f"[PRIMARY] results: {len(results)}")

            if not results:
                logger.info("[FALLBACK] Wikipedia")
                results = self.ws.search_wikipedia(query)

            if results:
                url = results[0].get("link") or results[0].get("url")
                if url:
                    logger.info(f"[OPEN] {url}")
                    webbrowser.open(url)

        elif search_type in ("image", "shopping", "news"):
            url = self.ws.generate_url(query, platform, search_type)

            if isinstance(url, str):
                logger.info(f"[OPEN] {url}")
                webbrowser.open(url)
                return url

        elif search_type == "video":
            url = self.ws.search_video(query)

            if isinstance(url, str):
                logger.info(f"[OPEN] {url}")
                webbrowser.open(url)
                return url

        else:
            return f"Неизвестный тип поиска {search_type}"

        return results
