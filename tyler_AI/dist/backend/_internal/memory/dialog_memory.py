import memory.chat_func as chat_func
import configs
import services.llm_selector as llm_selector
import requests
import asyncio
import httpx

SUMMARY_MODEL = "google/gemma-3n-e2b-it:free"
API_KEY = configs.OPENROUTER_KEY
URL = configs.URLS[SUMMARY_MODEL]


async def update_summary(chat_id):
    try:

        if chat_func.get_col(chat_id) % configs.MEMORY_LIMIT != 0: return

        summary = await _new_summary_prompt(chat_id)

        if summary.strip():
            chat_func.add_summary(chat_id, summary)

    except Exception as e:
        print("SUMMARY ERROR:", e)


async def _new_summary_prompt(chat_id: str) -> str:
    buf = "\n".join(f"{m['sender']}: {m['text']}" for m in chat_func.get_messages(chat_id)[-configs.MEMORY_LIMIT:])
    prompt = "Предыдущее summary: " + chat_func.get_summary(chat_id) + "\nНовые сообщения: " + buf
    return await create_summary(prompt)


async def create_summary(text: str) -> str:

    payload = {
        "model": SUMMARY_MODEL,
        "messages": [
            {
                "role": "user",
                "content": ( "Это диалог пользователя с ассистентом. Тебе нужно сделать краткое содержание диалога, строго до 50 слов!" + text )
            }
        ],
        "temperature": 0.2,
        "max_tokens": 100
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(URL, headers=headers, json=payload)

        if r.status_code != 200:
            print("SUMMARY API ERROR:", r.text)
            return ""

        data = r.json()

        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

    except Exception as e:
        print("SUMMARY REQUEST FAILED:", e)
        return ""