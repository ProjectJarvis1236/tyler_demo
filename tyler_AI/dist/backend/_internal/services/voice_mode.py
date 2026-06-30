import os
import sys
import sounddevice as sd
import numpy as np
import json
import asyncio
import webrtcvad
from vosk import Model, KaldiRecognizer
import time
import aiohttp
from api.tts_api import EdgeTTS

# Добавляем путь к DLL onnxruntime (для всех процессов)
if sys.platform == 'win32':
    try:
        import site
        site_packages = site.getsitepackages()[0]
        capi_path = os.path.join(site_packages, 'onnxruntime', 'capi')
        if os.path.exists(capi_path):
            os.add_dll_directory(capi_path)
            print(f"[INFO] Added DLL directory: {capi_path}")
        else:
            venv_path = os.environ.get('VIRTUAL_ENV')
            if venv_path:
                alt_capi = os.path.join(venv_path, 'Lib', 'site-packages', 'onnxruntime', 'capi')
                if os.path.exists(alt_capi):
                    os.add_dll_directory(alt_capi)
                    print(f"[INFO] Added DLL directory from venv: {alt_capi}")
    except Exception as e:
        print(f"[WARN] Failed to add DLL directory: {e}")

class VoiceService:
    def __init__(self, wakeword: str, process_func=None, default_chat_id="voice", default_model="qwen/qwen3-235b-a22b-thinking-2507"):
        self.SAMPLE_RATE = 16000
        self.FRAME_DURATION = 30
        self.FRAME_SIZE = int(self.SAMPLE_RATE * self.FRAME_DURATION / 1000)
        self.WAKEWORD = wakeword.lower()
        self.MODEL_PATH = "vosk"


        self.tts = EdgeTTS()

        if not os.path.exists(self.MODEL_PATH):
            raise FileNotFoundError(f"Модель Vosk не найдена по пути {self.MODEL_PATH}")
        self.vosk_model = Model(self.MODEL_PATH)
        self.vosk_recognizer = KaldiRecognizer(self.vosk_model, self.SAMPLE_RATE)

        import onnx_asr
        print("🔄 Загрузка GigaAM...")
        self.gigaam_model = onnx_asr.load_model("gigaam-v3-e2e-rnnt")
        print("✅ Модель GigaAM загружена")

        self.vad = webrtcvad.Vad(2)
        self.SILENCE_TIMEOUT = 1

        self.audio_queue = asyncio.Queue()
        self.stream = None
        self.wakeword_detected = False
        self.loop = None
        self._task = None

        self.process_func = process_func
        self.default_chat_id = default_chat_id
        self.default_model = default_model

    def mic_callback(self, indata, frames, time_info, status):
        if self.loop:
            self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, bytes(indata))

    def start_stream(self):
        if self.stream:
            return
        self.stream = sd.RawInputStream(
            samplerate=self.SAMPLE_RATE,
            blocksize=self.FRAME_SIZE,
            dtype='int16',
            channels=1,
            callback=self.mic_callback
        )
        self.stream.start()
        print("🎤 Поток микрофона запущен")

    def stop_stream(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            print("🎤 Поток микрофона остановлен")

    async def run(self):
        self.loop = asyncio.get_running_loop()
        self.start_stream()
        print(f"🎧 Ожидание wake word '{self.WAKEWORD}'...")

        while True:
            data = await self.audio_queue.get()

            if not self.wakeword_detected:
                if self.vosk_recognizer.AcceptWaveform(data):
                    result = json.loads(self.vosk_recognizer.Result())
                    text = result.get("text", "").lower()
                    if self.WAKEWORD in text:
                        print(f"🔥 Wake word '{self.WAKEWORD}' обнаружен! Слушаю команду...")
                        self.wakeword_detected = True
                        try:
                            await self.record_and_recognize()
                        finally:
                            self.wakeword_detected = False
                            print("🎧 Снова жду wake word...")

    async def record_and_recognize(self):
        start_time = time.time()
        audio_buffer = bytearray()
        silence_frames = 0
        speech_started = False

        frames_per_second = self.SAMPLE_RATE / self.FRAME_SIZE
        silence_threshold_frames = int(0.5 * frames_per_second)

        while True:
            chunk = await self.audio_queue.get()
            audio_buffer.extend(chunk)

            is_speech = self.vad.is_speech(chunk, self.SAMPLE_RATE)

            if is_speech:
                silence_frames = 0
                if not speech_started:
                    speech_started = True
            else:
                if speech_started:
                    silence_frames += 1

            if speech_started and silence_frames >= silence_threshold_frames:
                trim_size = silence_frames * self.FRAME_SIZE
                if trim_size < len(audio_buffer):
                    audio_buffer = audio_buffer[:-trim_size]
                break

            if len(audio_buffer) > 10 * self.SAMPLE_RATE * 2:
                print("⚠️ Слишком длинная команда, обрезаю")
                break

        if not speech_started or len(audio_buffer) < self.FRAME_SIZE * 5:
            print("⚠️ Команда не распознана (речь не обнаружена)")
            return

        audio_int16 = np.frombuffer(audio_buffer, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0

        result = self.gigaam_model.recognize(audio_float32, sample_rate=self.SAMPLE_RATE)

        elapsed = time.time() - start_time
        print(f"⏱ Время обработки команды: {elapsed:.2f} сек")

        if result:
            text = result if isinstance(result, str) else getattr(result, 'text', '')
            if text:
                print(f"✅ Команда: {text}")
                if self.process_func:
                    print(f"📞 [VoiceService] process_func будет вызван с текстом: '{text}'")
                    asyncio.create_task(self.safe_process_func(text))
                else:
                    print("⚠️ [VoiceService] process_func не задана")
            else:
                print("⚠️ Пустой результат")
        else:
            print("⚠️ Ошибка распознавания")

    async def safe_process_func(self, text):
        try:
            print(f"📞 [VoiceService] Вызов process_func...")
            api_resp, rep_text = await self.process_func(text, self.default_chat_id, self.default_model)
            print(f"✅ [VoiceService] process_func завершён")
            if rep_text:
                await self.tts.speak(rep_text)
        except Exception as e:
            print(f"❌ [VoiceService] Ошибка в process_func: {e}")

    async def start(self):
        print("▶️ Запуск voice service...")
        self._task = asyncio.create_task(self.run())
        print("✅ Задача voice service создана")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.stop_stream()