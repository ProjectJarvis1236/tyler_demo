import json

from memory import chat_func
from memory import dialog_memory
from memory import shortMemory
from actions import ActionBrain
from . import llm_selector



async def process_chat(text: str, chat_id: str, model: str, request=None):
    print(f"fr[process_chat] ВЫЗВАН с text='{text}', chat_id='{chat_id}', model='{model}'")
    chat_func.add_message(chat_id, "user", text)
    await dialog_memory.update_summary(chat_id)

    action_brain = ActionBrain()

    memory = await shortMemory.get_short_memory(chat_id)
    llm_respose = await llm_selector.ask_llm(memory, model, chat_id)

    llm_json = {"reply": "", "actions": [], "meta": {}}
    print(f"[process_chat] llm_respose (raw): {llm_respose}")
    if isinstance(llm_respose, str):
        cleaned = llm_respose.strip()
        if cleaned.lower().startswith("json"): 
            cleaned = cleaned[4:].strip()
        try:
            llm_json = json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start != -1 and end != -1:
                try:
                    llm_json = json.loads(cleaned[start:end])
                except Exception:
                    llm_json = {"reply": cleaned, "actions": [], "meta": {}}
    elif isinstance(llm_respose, dict):
        llm_json = llm_respose

    reply_text = llm_json.get("reply", "")
    actions = llm_json.get("actions", [])
    meta = llm_json.get("meta", {})

    action_results = []
    if actions:
        action_results = await action_brain.execute_actions(actions, chat_id)
        for res in action_results:
            result = res.get("result", {})
            if isinstance(result, dict) and "reply" in result:
                reply_text = result["reply"]

    chat_func.add_message(chat_id, "bot", reply_text)
    await dialog_memory.update_summary(chat_id)

    # Если передан request и голосовой сервис активен, озвучиваем ответ
    if request:
        voice_service = getattr(request.app.state, "voice_service", None)
        #if voice_service and voice_service._task and not voice_service._task.done():
            # Сервис запущен — озвучиваем ответ
            #asyncio.create_task(speak_response(reply_text))

    api_resp = {
        "reply": reply_text,
        "history": chat_func.get_messages(chat_id),
        "summary": chat_func.get_summary(chat_id)
    }
    return api_resp, reply_text