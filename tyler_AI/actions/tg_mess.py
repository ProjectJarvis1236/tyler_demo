import time
import pyautogui
import pyperclip
import random
import asyncio
import keyboard
import pygetwindow as gw

from .app_open import AppOpen


class TgMessage:
    def __init__(self):
        self.ao = AppOpen()

    async def run(self, params: dict, chat_id: str) -> str:
        user = params.get("user", "").strip()
        message = params.get("message", "").strip()

        if not user or not message:
            return "Ошибка: не указан пользователь или сообщение"

        try:
            await self._open_telegram(chat_id)
            await asyncio.sleep(self.delay("long"))

            await asyncio.to_thread(self._send_message, user, message)

            return f"Сообщение отправлено пользователю: {user}"

        except Exception as e:
            return f"Ошибка: {e}"

    async def _open_telegram(self, chat_id: str):
        await self.ao.run({"app": "telegram"}, chat_id)

    def _focus_telegram(self):
        tg_windows = gw.getWindowsWithTitle("Telegram")
        if not tg_windows:
            return
        win = tg_windows[0]
        if win.isMinimized:
            win.restore()
        win.activate()
        x = win.left + win.width // 2
        y = win.top + 120
        pyautogui.click(x, y)
        time.sleep(self.delay("short"))

    def _send_message(self, user: str, message: str):
        self._reset_modifiers()

        pyautogui.press("esc")
        time.sleep(self.delay("short"))
        pyautogui.press("esc")
        time.sleep(self.delay("short"))

        self._focus_telegram()

        self._ctrl_key("f")
        time.sleep(self.delay("medium"))

        self._focus_telegram()

        pyperclip.copy(user)
        time.sleep(0.3)
        self._ctrl_key("v")
        time.sleep(self.delay("medium"))

        pyautogui.press("down")
        time.sleep(self.delay("short"))
        pyautogui.press("enter")
        time.sleep(self.delay("long"))

        pyperclip.copy(message)
        time.sleep(0.1)
        self._ctrl_key("v")
        time.sleep(self.delay("short"))

        pyautogui.press("enter")

        self._reset_modifiers()

    def _ctrl_key(self, key: str):
        try:
            keyboard.press("ctrl")
            time.sleep(0.03)
            keyboard.press(key)
            time.sleep(0.03)
            keyboard.release(key)
        finally:
            keyboard.release("ctrl")

    def _reset_modifiers(self):
        for k in ['ctrl', 'shift', 'alt']:
            try:
                keyboard.release(k)
            except:
                pass
            try:
                pyautogui.keyUp(k)
            except:
                pass

        # try: pyautogui.keyUp('win')
        # except: pass

        time.sleep(0.05)

    def delay(self, type: str):
        num = random.random() * 0.27

        if type == "short":
            num += 0.2
        elif type == "medium":
            num += 0.4
        elif type == "long":
            num += 0.5

        return num
