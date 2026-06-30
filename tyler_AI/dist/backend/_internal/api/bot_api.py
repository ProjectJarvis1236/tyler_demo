from fastapi import APIRouter, Request
from pydantic import BaseModel
import asyncio
import configs
from actions.action_brain import ActionBrain
from services.chat_services import process_chat
from services.voice_mode import VoiceService

router = APIRouter()
action_brain = ActionBrain()
WAKEWORD = 'аладин'

class UserMessage(BaseModel):
    text: str
    chat_id: str
    model: str = "nvidia/nemotron-3-super-120b-a12b:free"

@router.post("/voice/on")
async def voice_on(msg: UserMessage, request: Request):
        voice_service = getattr(request.app.state, "voice_service", None)    
        # Создаём и запускаем новый сервис
        print("🎤 Запуск VoiceService")
        voice_service = VoiceService(
            wakeword=WAKEWORD,
            process_func=process_chat,
            default_chat_id=msg.chat_id,
            default_model=msg.model
        )
        await voice_service.start()
        request.app.state.voice_service = voice_service
        return {"status": "voice_started"}

@router.post("/voice/off")
async def voice_off(request: Request):
    voice_service = getattr(request.app.state, "voice_service", None)
    if voice_service:
        print("🛑 Остановка VoiceService")
        await voice_service.stop()
        request.app.state.voice_service = None
        return {"status": "voice_stopped"}
    return {"status": "voice_not_running"}

@router.post("/chat")
async def chat(msg: UserMessage, request: Request):
    print(f"📨 Текстовое сообщение: {msg.text}")
    api_resp, _ = await process_chat(msg.text, msg.chat_id, msg.model)
    return api_resp

from memory.chat_func import get_messages
@router.get("/debug/chat/{chat_id}")
def debug_chat(chat_id: str):
    return {
        "chat_id": chat_id,
        "messages": get_messages(chat_id)
    }