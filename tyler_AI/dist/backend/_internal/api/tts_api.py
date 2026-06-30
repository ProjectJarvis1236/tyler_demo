import asyncio
import edge_tts
import sounddevice as sd
import miniaudio
import numpy as np

voice = "ru-RU-DmitryNeural"

class EdgeTTS:
    def __init__(self, voice=voice):
        self.voice = voice
        self.sample_rate = 32000

    async def speak(self, text: str):
        communicate = edge_tts.Communicate(text, self.voice)

        stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=4096,          # размер блока, который запрашивается за раз
            latency='high'            # увеличивает буфер, снижая риск underflow
            )
        stream.start()

        # Накопительный буфер для плавности
        buffer = bytearray()
        target_samples = int(self.sample_rate * 1)  # 1 с буфера

        try:
            async for chunk in communicate.stream():
                if chunk["type"] != "audio":
                    continue

                # Декодируем MP3 в PCM
                decoded = miniaudio.decode(
                    chunk["data"],
                    sample_rate=self.sample_rate,
                    nchannels=1
                    
                )

                # Преобразуем array.array в байты, затем в numpy
                raw_bytes = decoded.samples.tobytes()  # array.array -> bytes
                samples = np.frombuffer(raw_bytes, dtype=np.int16)
                buffer.extend(samples.tobytes())

                # Отправляем накопленными порциями
                while len(buffer) // 2 >= target_samples:
                    chunk_data = buffer[:target_samples * 2]
                    buffer = buffer[target_samples * 2:]
                    out_samples = np.frombuffer(chunk_data, dtype=np.int16)
                    stream.write(out_samples)

        finally:
            # Отправляем остатки
            if buffer:
                out_samples = np.frombuffer(buffer, dtype=np.int16)
                stream.write(out_samples)

            stream.stop()
            stream.close()