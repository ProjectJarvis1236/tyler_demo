import win32gui
import win32con
import win32api
from actions.app_open import AppOpen
import asyncio
import time
import ctypes
import pyautogui

from actions.app_open import AppOpen


# Эти 70 строк кода рожались на протяжении 6 часов, лучше это не ломать)
# Надо как-то сделать для окон 2 на 2, а не только 50 на 50, но это позже

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
SW_RESTORE = 9
SW_MINIMIZE = 6

class WindowsManager:
    def __init__(self):
        self.width = win32api.GetSystemMetrics(0)
        self.height = win32api.GetSystemMetrics(1)
        self.app_open = AppOpen()

    async def run(self, params: dict, chat_id: str):
        apps = params.get("apps", [])
        if len(apps) != 2:
            print("Нужны ровно два приложения для 50x50 Snap Group")
            return

        # Сворачиваем все окна
        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                win32gui.ShowWindow(hwnd, SW_MINIMIZE)
            return True
        win32gui.EnumWindows(enum_callback, None)
        await asyncio.sleep(0.3)

        hwnds = []
        for app in apps:
            result = await self.app_open.run({"app": app, "flag": 0})
            hwnd = result.get("hwnd")
            if not hwnd:
                for _ in range(10):
                    hwnd = self.app_open._activate_window(app)
                    if hwnd:
                        break
                    await asyncio.sleep(0.2)
            if hwnd:
                self.app_open._activate_window_hwnd(hwnd)
                await asyncio.sleep(0.5)
                hwnds.append(hwnd)
            else:
                print(f"Не удалось получить окно для {app}")
                return

        # Snap Group: первый слева, второй справа
        self.snap_left(hwnds[0])
        await asyncio.sleep(0.5)
        self.snap_right(hwnds[1])
        await asyncio.sleep(0.5)


    def snap_left(self, hwnd):
        self.app_open._activate_window_hwnd(hwnd)
        pyautogui.hotkey('win', 'left')
        time.sleep(0.5)

    def snap_right(self, hwnd):
        self.app_open._activate_window_hwnd(hwnd)
        pyautogui.hotkey('win', 'right')
        time.sleep(0.5)
        pyautogui.press('space')