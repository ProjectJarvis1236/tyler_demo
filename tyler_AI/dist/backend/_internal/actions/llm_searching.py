import httpx
import json
import traceback
from actions.web_search import WebSearch
import memory.chat_func as chat_func
import configs
import memory.shortMemory as short_memory

API_KEYS = {
    "nvidia/nemotron-3-super-120b-a12b:free": configs.OPENROUTER_KEY, 
    "apifreellm": configs.APIFREELLM_KEY
}

class LLMWebSearch:
    def __init__(self):
        self.web_search = WebSearch()

    async def run(self, params: dict, chat_id: str):
        query = params.get("question", "").strip()
        search_query = params.get("search_query", query)
        if not query:
            return {"reply": "", "meta": {"sources": [], "context": ""}}

        raw_results = self._web_search(search_query)
        if hasattr(raw_results, '__await__'):
            raw_results = await raw_results
        results = raw_results[:10] if raw_results else []
        context = self._build_context(results)

        model = params.get("model", "apifreellm")
        messages = await short_memory.get_short_memory(chat_id)
        if not isinstance(messages, list):
            messages = []
        return await self.ask_llm(messages, model, chat_id, query, context)

    def _web_search(self, query: str):
        return self.web_search.search_text(query)

    def _build_context(self, results):
        if not results:
            return ""
        blocks = []
        for i, r in enumerate(results):
            title = r.get("title", "Без заголовка").strip()
            link = r.get("link", "").strip()
            snippet = r.get("snippet", "").strip()
            blocks.append(f"[{i + 1}] {title}\n{link}\n{snippet}")
        return "\n\n".join(blocks)

    async def ask_llm(self, messages: list, model: str, chat_id: str, query: str, context: str):
        if model not in API_KEYS:
            return {"reply": f"[Ошибка: модель {model} не поддерживается]", "meta": {}}

        API_KEY = API_KEYS[model]
        url = configs.URLS.get(model)
        if not url or not API_KEY:
            return {"reply": "[Ошибка: конфигурация API отсутствует]", "meta": {}}

        SYSTEM_PROMPTS = [configs.CORE_RULES, configs.FORMAT_RULES, configs.FAIL_RULES]
        summary = chat_func.get_summary(chat_id)
        if hasattr(summary, '__await__'):
            summary = await summary

        prompt = "\n\n".join([
            '\n---\n'.join(SYSTEM_PROMPTS),
            f"Резюме диалога: {summary}",
            "Контекст диалога:",
            "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages[:-1]),
            f"Используй эти источники для ответа:\n{context}. Рядом с каждым фактом пиши в квадратных скобках ссылку на источник, откуда был взят этот факт.",
            f"Текущий запрос: {query}"
        ])

        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        data = {"message": prompt}

        try:
            timeout = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=data)
                if response.status_code >= 400:
                    response.raise_for_status()
                result = response.json()
        except Exception as e:
            print(f"[ERROR] LLM request failed: {type(e).__name__}: {e}")
            return {"reply": f"[Ошибка API: {str(e)}]", "meta": {}}

        # 🎯 Парсинг ответа с поддержкой apifreellm обёртки и Markdown-блоков
        if model == "apifreellm":
            raw = result.get("response", "")
            if isinstance(raw, str):
                text = raw.strip()
                # Удаляем ```json ... ``` обёртку
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                    if text.rstrip().endswith("```"):
                        text = text.rstrip()[:-3].rstrip()
                    text = text.strip()
                if text.startswith(("{", "[")):
                    try:
                        result = json.loads(text)
                    except json.JSONDecodeError:
                        result = {"reply": raw, "actions": []}
                else:
                    result = {"reply": raw, "actions": []}
            elif isinstance(raw, dict):
                result = raw

        reply = result.get("reply") or result.get("content") or result.get("text") or "Нет ответа"
        actions = result.get("actions", [])
        meta = result.get("meta", {})

        print(f"[DEBUG] Reply: {str(reply)[:100]}... | Actions: {len(actions)}")
        return {"reply": str(reply), "actions": actions, "results": "", "meta": meta}