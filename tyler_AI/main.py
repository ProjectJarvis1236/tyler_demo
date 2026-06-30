import os
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from core.scanner import build_app_dictionary
from api.bot_api import router as bot_router
from memory.chat_func import init_db
import configs

# Определяем базовую директорию
if getattr(sys, 'frozen', False):
    # Если приложение скомпилировано PyInstaller
    BASE_DIR = sys._MEIPASS
else:
    # Обычный запуск Python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Переключаем рабочий каталог в BASE_DIR, чтобы относительные пути (например, "vosk") работали
os.chdir(BASE_DIR)

# Инициализация БД
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    apps = build_app_dictionary()
    configs.ADRES.clear()
    configs.APP_NAMES.clear()
    for key, data in apps.items():
        configs.ADRES[key] = {
            "path": data["path"],
            "name": data["name"]
        }
        configs.APP_NAMES.append(key)
    print(f"Загружено {len(configs.ADRES)} приложений и {len(configs.APP_NAMES)} имён")
    print(configs.APP_NAMES)

    yield

    # Остановка голосового сервиса
    voice_service = getattr(app.state, "voice_service", None)
    if voice_service:
        print("Остановка голосового сервиса при завершении...")
        await voice_service.stop()
        app.state.voice_service = None

app = FastAPI(lifespan=lifespan)
app.include_router(bot_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

print("Зарегистрированные маршруты:")
for route in app.routes:
    print(f"  {route.path} [{','.join(route.methods)}]")

# Запуск для режима разработки (не используется в собранном .exe)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )