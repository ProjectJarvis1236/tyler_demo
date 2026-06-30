import httpx
import json

import configs
from memory import chat_func
from memory import action_memory

API_KEYS = {
    "nvidia/nemotron-3-super-120b-a12b:free": configs.OPENROUTER_KEY, 
    "apifreellm": configs.APIFREELLM_KEY,
    "gpt-4.1-nano": configs.OPENAI_KEY,
    "openai/gpt-oss-120b:free": configs.KODIK_KEY,
    "google/gemma-4-26b-a4b-it:free": configs.KODIK_KEY,
    "cerebras/gpt-oss-120b": configs.CEREBRAS_KEY,
    "deepseek-v4-flash": configs.DEEPSEEK_KEY,
    "gpt-oss-120b": configs.SAMBA_KEY
    }


def build_context(chat_id):
    SYSTEM_PROMPTS = [
        configs.CORE_RULES,
        build(),
        configs.ACTION_RULES, 
        configs.FORMAT_RULES,
        configs.PROACTIVE_RULES,
        configs.FAIL_RULES
    ]

    prev_summary = chat_func.get_summary(chat_id)
    prev_actions = action_memory.get_last_actions(chat_id)

    system_messages = [{"role": "system", "content": p} for p in SYSTEM_PROMPTS]

    if prev_summary:
        system_messages.append({
            "role": "system",
            "content": f"Резюме диалога: {prev_summary}"
        })

    if prev_actions:
        system_messages.append({
            "role": "system",
            "content": "Последние действия:\n" + json.dumps(prev_actions, ensure_ascii=False)
        })

    return system_messages


async def ask_llm(messages: list, model: str, chat_id: str):    
    if model not in API_KEYS:
        return f"[Ошибка: модель {model} не поддерживается]"

    API_KEY = API_KEYS[model]
    url = configs.URLS[model]

    system_messages = build_context(chat_id)

    if model in ["nvidia/nemotron-3-super-120b-a12b:free", "gpt-4.1-nano", "openai/gpt-oss-120b:free",
                 "cerebras/gpt-oss-120b", "deepseek-v4-flash", "gpt-oss-120b"]:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": system_messages + messages
        }



    elif model == "apifreellm":
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "message":
                "\n---\n".join([p["content"] for p in system_messages]) + "\n" +
                f"Контекст:\n" +
                "\n".join(f"{m['role']}: {m['content']}" for m in messages[:-1]) +
                f"\nТекущий запрос: {messages[-1]['content']}"
        }


    async with httpx.AsyncClient(timeout=configs.TIMEOUT) as client:
        response = await client.post(url, headers=headers, json=data)

        result = response.json()

        if model == "apifreellm":
            return result.get("response", "[Ошибка: пустой ответ]")

        elif model in ["nvidia/nemotron-3-super-120b-a12b:free", "gpt-4.1-nano", "openai/gpt-oss-120b:free", 
                       "cerebras/gpt-oss-120b", "deepseek-v4-flash", "gpt-oss-120b"]:
            return result["choices"][0]["message"]["content"]

        return "[llm_selector] Неизвестная модель"
    




def build() -> str:
    return f"""
СПИСОК ДОСТУПНЫХ ДЕЙСТВИЙ:
1) web_search
Описание: находит информацию в интернете и открывает результаты поиска в браузере на ПК пользователя.
Когда использовать: пользователь явно просит найти и открыть информацию в интернете
Когда НЕ использовать: пользователь просто задаёт вопрос; пользователь не просил поиск в интернете
Если не знаешь ответ: предложи выполнить поиск и дождись подтверждения или используй llm_searching

params:
{{
    "query": "<оптимизированный поисковой запрос>",
    "search_type": "text" | "video" | "image" | "news" | "shopping",
    "platform": "bing" | "yandex" | "google" | "ozon" | "wildberries" | "yandex_market" | "google_market"
}}

Правила заполнения:
- query должен быть оптимизирован под поиск
- search_type выбирай по задаче пользователя
- если platform не указан: используй yandex

Примечания:
text/video/image/news: - platform: bing, yandex, google
shopping: - platform: ozon, wildberries, yandex_market, google_market


2) app_open
Описание: открывает приложение на ПК пользователя.
Когда использовать: пользователь явно просит открыть или запустить приложение
Когда НЕ использовать: пользователь не просил явно открыть приложение

params:
{{
    "app": "<название приложения из списка>",
    "flag": "1" | "0"
}}

Правила заполнения:
- app должен строго совпадать с названием из списка
- не изменяй регистр, пробелы и написание
- flag = "1", если пользователь явно просит новое окно, иначе flag = "0"

Примечания:
Список приложений:
{configs.APP_NAMES}
Если приложения нет: сообщи пользователю, что оно недоступно


3) win_settings
Описание: изменяет системные настройки Windows. 
Когда использовать: пользователь просит изменить системные параметры
Когда НЕ использовать: запрос не связан с системными настройками

params:
{{
    "function": "set_volume" | "set_brightness" | "toggle_mute" | "switch_lang" | "set_lang",
    "definition": <значение или null>
}}

Правила заполнения:
set_volume:
- использовать, если нужно поменять громкость
- definition = число 0-100

set_brightness:
- использовать, если нужно поменять яркость
- definition = число 0-100

toggle_mute:
- использовать, если нужно выключить звук
- definition = null

switch_lang:
- использовать, если нужен следующий язык
- definition = null

set_lang:
- использовать, если нужно установить определённый язык, который попросил пользователь
- definition = hex код языка

Примечания:
0x409 — English
0x419 — Russian
0x407 — German
0x40c — French


4) windows_open
Описание: располагает окна приложений на экране.
Когда использовать: пользователь просит расположить окна
Когда НЕ использовать: пользователь не просил менять layout окон

params:
{{
    "layout": <формат расположения окон>,
    "apps": [<массив приложений>]
}}

Правила заполнения:
layout:
- "50x50" = 2 окна пополам
apps: только приложения из списка доступных

Примечания: Можно указывать одно или несколько приложений.

5) Web_parse
Описание: создаёт Word-документ на основе статей из интернета.
Когда использовать: пользователь просит создать документ по ссылкам или статьям
Когда НЕ использовать: нет ссылок или задачи обработки текста

params:
{{
    "urls": [<массив ссылок, которые прислал пользователь>],    #обязательное поле
    "task_description": "<описание задачи>",        #обязательное поле
    "filename": "<имя файла или пусто>"
}}

Правила заполнения:
- urls обязательно
- task_description обязательно - нужно сделать доклад, пересказ или что-то ещё
- filename заполняй только если пользователь явно указал имя файла

6) Emails
Описание: отправляет письма или читает последние письма.
Когда использовать:
- пользователь просит отправить письмо
- пользователь просит проверить почту
Когда НЕ использовать: запрос не связан с email

params:
{{
    "action": "send_email" | "check_for_emails",
    "receiver_email": <почта получателя>,
    "text": <текст письма>,
    "subject": <тема письма>
}}

Правила заполнения:
send_email:
- обязательно receiver_email
- обязательно text
- желательно subject
check_for_emails: остальные поля можно оставить пустыми

Примечания:
check_for_emails читает 10 последних писем.


7) excel_manager
Описание: создаёт или редактирует Excel-файлы.
Когда использовать: пользователь явно просит работать с Excel или таблицей
Когда НЕ использовать: запрос не связан с таблицами

params:
{{
    "action": "create" | "update",
    "filename": "<имя Excel-файла>", #обязательно поле, указывай примерное название файла, если не указано точное
    "sheet": "<имя листа>",
    "data": {{
        "headers": [...],
        "rows": [...]
    }},
    "updates": {{
        "mission": "<задача>"
    }}
}}

Правила заполнения:
create: используй headers и rows, чтобы создать excel файл
update: используй updates, чтобы отредактировать excel файл
mission: формулируй общую задачу без лишней конкретики

Примечания:
Если пользователь редактирует готовый файл: backend находит, анализирует и редактирует файл сам

8) create_presentation
Описание: создаёт презентации.
Когда использовать: пользователь просит создать презентацию
Когда НЕ использовать: запрос не связан с презентацией

params:
{{ 
    "filename": "<Название файла с презентацией>"
    "topic": "<Тема презентации>",
    "slide_count": "<Количество слайдов>"
    "additional_info": "<Дополнительная информация от пользователя>"
}}

Правила заполнения:
filename обязателен, если не указано — придумай название
topic — основная тема презентации
slide_count — количество слайдов (включая титульный и финальный), финальный слайд всегда заканчивается фразой "Спасибо за внимание!"
additional_info — любые детали от пользователя (стиль, акценты, конкретные пункты)

Примечания:
backend сам сгенерирует структуру слайдов на основе этих параметров

9) file_manager
Описание: создаёт или открывает файлы.
Когда использовать: пользователь просит открыть или создать файл
Когда НЕ использовать: запрос не связан с файлами

params:
{{
  "name": "<название файла без расширения>",
  "action": "create_file" | "open_file",
  "description": "<описание содержания файла, пиши, если пользователь сказал, что лежит в файле, но не сказал его название>"
  "extension": ".pdf" | ".txt" | ".docx" | ".xlsx" | ".pptx",
  "content": "<Содержимое файла, если пользователь попросил туда что-то записать>"
}}
Правила заполнения:
- extension обязателен
- обязательно name или description
Если пользователь знает имя: используй name
Если имя неизвестно: используй description

Примечания:
При создании файла, если имя не было задано пользователем, то придумай название сам.


10) llm_searching
Описание: находит 10 ссылок по теме в Интернете и вызывает вторую ЛЛМ, чтобы та дала ответ на основе найденных источников 
Когда использовать: нужна информация из интернета, но пользователь не просил открывать браузер
Когда НЕ использовать: пользователь явно хочет web_search

params:
{{
    "question": <оптимизированный вопрос пользователя, на который должна ответить ЛЛМ>,
    "search_query": <поисковой запрос для поиска источников, максимально подходящих под вопрос пользователя>
}}

Примечания:
- используй, как внутренний поиск
- необязателен явный вызов этого действия от лица пользователя


11) tg_message - отправляет сообщение какому-то контакту от лица пользователя
Описание: отправляет сообщение Telegram-контакту.
Когда использовать: пользователь просит отправить сообщение
Когда НЕ использовать: запрос не связан с Telegram

params:
{{
    "message": <текст сообщения, которое нужно отправить>,
    "user": <полное имя контакта из списка контактов>
}}

Правила заполнения:
- пользователь может назвать short_name или full_name
- всегда возвращай full_name

Примечания:
Список контактов:
{configs.TG_CONTACTS}

12) word_manager
Описание: редактирует Word-документы (.docx) по текстовому запросу.
Когда использовать: пользователь просит изменить, заполнить или отредактировать существующий .docx файл.
Когда НЕ использовать: запрос не связан с Word; нужно создать новый файл (используй file_manager); нужно просто прочитать без изменений (используй file_manager).

params:
{{
    "file_path": "<путь к файлу>",
    "output_path": "<путь к новому файлу>",
    "prompt": "Заполни документ",
    "llm_state": {{}}
}}

Правила заполнения:
- file_path обязателен
- output_path обязателен, используй исходный путь, но с изменённым названием файла
- prompt обязателен, опиши задачу редактирования (заполнить поля, изменить текст и т.п.)


Примечания:
Система сама анализирует структуру документа и вносит точечные изменения, не затрагивая заголовки и служебный текст.
Используй, если пользователь просит заполнить или отредактировать уже готовый документ, а не создать новый
"""