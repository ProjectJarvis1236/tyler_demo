import os
import time
import asyncio
import psutil
import ctypes
from ctypes import wintypes

import configs
from core import logger

logger = logger.get_logger("AppOpen") 

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
SW_RESTORE = 9


APP_TO_PROCESS = {
    # --- уже были ---
    "code": "code.exe",
    "telegram": "telegram.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "msedge": "msedge.exe",
    "discord": "discord.exe",
    "steam": "steam.exe",
    "explorer": "explorer.exe",
    "notepad": "notepad.exe",
    "winword": "winword.exe",

    # --- Office ---
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
    "onenote": "onenote.exe",
    "access": "msaccess.exe",
    "publisher": "mspub.exe",

    # --- Adobe ---
    "photoshop": "photoshop.exe",
    "illustrator": "illustrator.exe",
    "acrobat": "acrobat.exe",        # Acrobat Reader / Pro
    "indesign": "indesign.exe",
    "premiere": "premierepro.exe",
    "aftereffects": "afterfx.exe",

    # --- Стандартные Windows ---
    "paint": "mspaint.exe",
    "calculator": "calculatorapp.exe",   # современное UWP-приложение, может отличаться
    "snippingtool": "snippingtool.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "terminal": "wt.exe",                # Windows Terminal

    # --- Медиа ---
    "vlc": "vlc.exe",
    "spotify": "spotify.exe",

    # --- Браузеры (доп.) ---
    "firefox": "firefox.exe",
    "opera": "opera.exe",
    "brave": "brave.exe",

    # --- Разработка ---
    "pycharm": "pycharm64.exe",
    "idea": "idea64.exe",
    "sublime": "sublime_text.exe",
    "notepad++": "notepad++.exe",

    # --- Мессенджеры ---
    "whatsapp": "whatsapp.exe",
    "slack": "slack.exe",
    "teams": "teams.exe",
    "zoom": "zoom.exe",
}





class AppOpen:
    async def run(self, params: dict, chat_id: str):
        app = params.get("app")
        flag = int(params.get("flag", 0))  # 0 = открыть новое, 1 = использовать существующее

        if not app:
            logger.error("Не указан app")
            return {"error": "Не указан app"}

        try:
            name = configs.ADRES[app]["name"]
            path = configs.ADRES[app]["path"]
            process_name = APP_TO_PROCESS.get(app)
            if not process_name:
                return {"error": f"Неизвестное приложение: {app}"}
        except KeyError:
            return {"error": f"Приложение {app} не найдено в configs.ADRES"}

        if not os.path.exists(path):
            return {"error": f"Файл не найден: {path}"}

        # Получаем существующие окна
        existing_hwnds = self._get_window_hwnds_by_keywords(WINDOW_KEYWORDS.get(app, []))

        # Запускаем новое окно если flag=0 или процесс не запущен
        if flag == 0 or not any(p.name().lower() == process_name.lower() for p in psutil.process_iter(["name"])):
            logger.debug(f"Запуск {app} ({process_name})")
            os.startfile(path)

        # Ждём появления окна
        hwnd = await self._wait_for_new_window(app, existing_hwnds)
        if hwnd:
            # Стабилизируем окно
            stable = False
            last_rect = None
            for _ in range(20):
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                current_rect = (rect.left, rect.top, rect.right, rect.bottom)
                if current_rect == last_rect:
                    stable = True
                    break
                last_rect = current_rect
                await asyncio.sleep(0.2)

            # Разворачиваем и активируем
            user32.ShowWindow(hwnd, SW_RESTORE)
            time.sleep(0.1)
            self._activate_window_hwnd(hwnd)

            return {"status": "ok", "result": f"{name} запущен", "hwnd": hwnd}

        # Если окно не появилось — пробуем активировать старое
        hwnd = self._activate_existing_window(app)
        if hwnd:
            return {"status": "ok", "result": f"{name} запущен (старое окно)", "hwnd": hwnd}
        else:
            return {"error": f"{name} не удалось открыть"}

    def _get_window_hwnds_by_keywords(self, keywords: list) -> set:
        found_hwnds = set()

        def enum(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.lower()
            if any(kw.lower() in title for kw in keywords):
                found_hwnds.add(hwnd)
            return True

        EnumFunc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(EnumFunc(enum), 0)
        return found_hwnds

    async def _wait_for_new_window(self, app_key: str, existing_hwnds: set, timeout=1):
        keywords = WINDOW_KEYWORDS.get(app_key, [])
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_hwnds = self._get_window_hwnds_by_keywords(keywords)
            new_hwnds = all_hwnds - existing_hwnds
            if new_hwnds:
                return next(iter(new_hwnds))
            await asyncio.sleep(0.3)
        return None

    def _activate_window_hwnd(self, hwnd: int):
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
            time.sleep(0.1)
        current_thread = kernel32.GetCurrentThreadId()
        window_thread = user32.GetWindowThreadProcessId(hwnd, None)
        if current_thread != window_thread:
            user32.AttachThreadInput(current_thread, window_thread, True)
            user32.SetForegroundWindow(hwnd)
            user32.AttachThreadInput(current_thread, window_thread, False)
        else:
            user32.SetForegroundWindow(hwnd)

    def _activate_existing_window(self, app_key: str):
        keywords = WINDOW_KEYWORDS.get(app_key, [])
        found_hwnd = None

        def enum(hwnd, _):
            nonlocal found_hwnd
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.lower()
            if any(kw.lower() in title for kw in keywords):
                found_hwnd = hwnd
                return False
            return True

        EnumFunc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(EnumFunc(enum), 0)
        if found_hwnd:
            self._activate_window_hwnd(found_hwnd)
        return found_hwnd








WINDOW_KEYWORDS = {
    # --- уже были ---
    "code": ["Visual Studio Code", "Code", "VS Code"],
    "telegram": ["Telegram", "Telegram Desktop"],
    "chrome": ["Google Chrome", "Chrome"],
    "edge": ["Microsoft Edge", "Edge"],
    "msedge": ["Microsoft Edge", "Edge"],
    "discord": ["Discord"],
    "steam": ["Steam"],
    "explorer": ["Проводник", "File Explorer", "Explorer"],
    "notepad": ["Блокнот", "Notepad"],
    "winword": ["Word"],

    # --- Office ---
    "excel": ["Excel", "Microsoft Excel"],
    "powerpoint": ["PowerPoint", "Microsoft PowerPoint"],
    "outlook": ["Outlook", "Microsoft Outlook"],
    "onenote": ["OneNote", "Microsoft OneNote"],
    "access": ["Access", "Microsoft Access"],
    "publisher": ["Publisher", "Microsoft Publisher"],

    # --- Adobe ---
    "photoshop": ["Adobe Photoshop", "Photoshop"],
    "illustrator": ["Adobe Illustrator", "Illustrator"],
    "acrobat": ["Adobe Acrobat", "Acrobat Reader", "Acrobat"],
    "indesign": ["Adobe InDesign", "InDesign"],
    "premiere": ["Adobe Premiere Pro", "Premiere Pro"],
    "aftereffects": ["Adobe After Effects", "After Effects"],

    # --- Стандартные Windows ---
    "paint": ["Paint", "Рисование"],
    "calculator": ["Калькулятор", "Calculator"],
    "snippingtool": ["Ножницы", "Snipping Tool"],
    "cmd": ["Командная строка", "Command Prompt", "cmd.exe"],
    "powershell": ["Windows PowerShell", "PowerShell"],
    "terminal": ["Windows Terminal", "Terminal"],

    # --- Медиа ---
    "vlc": ["VLC media player", "VLC"],
    "spotify": ["Spotify"],

    # --- Браузеры (доп.) ---
    "firefox": ["Mozilla Firefox", "Firefox"],
    "opera": ["Opera", "Opera Browser"],
    "brave": ["Brave"],

    # --- Разработка ---
    "pycharm": ["PyCharm", "JetBrains"],
    "idea": ["IntelliJ IDEA", "JetBrains"],
    "sublime": ["Sublime Text"],
    "notepad++": ["Notepad++"],

    # --- Мессенджеры ---
    "whatsapp": ["WhatsApp"],
    "slack": ["Slack"],
    "teams": ["Microsoft Teams", "Teams"],
    "zoom": ["Zoom"],
}