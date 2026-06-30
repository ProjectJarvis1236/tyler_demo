# actions/Web_parse.py
import requests
import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PageParser:
    def __init__(self):
        # Убираем инициализацию WordCreator, он не нужен в этом файле
        pass

    def parse_single_url(self, url: str) -> Dict[str, Any]:
        """
        Парсит одну веб-страницу и возвращает её содержимое.
        """
        try:
            logger.info(f"Парсинг URL: {url}")
            
            # Получаем HTML
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, timeout=10, headers=headers)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP ошибка: {response.status_code} для URL: {url}",
                    "url": url
                }
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Удаляем мусор
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "meta", "link"]):
                tag.decompose()
            
            # Извлекаем текст
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Ограничиваем длину (опционально, для экономии токенов LLM)
            MAX_LENGTH = 10000
            if len(text_content) > MAX_LENGTH:
                 text_content = text_content[:MAX_LENGTH] + "... [TEXT TRUNCATED]"
            
            logger.info(f"Парсинг {url} завершён, длина текста: {len(text_content)} символов.")
            
            return {
                "success": True,
                "url": url,
                "content": text_content
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }

    # Убираем старый async def run, он больше не нужен в этом файле
    # или оставляем его как альтернативный интерфейс, если нужно
    # async def run(self, params: dict) -> dict:
    #     url = params.get("url")
    #     return self.parse_single_url(url)
