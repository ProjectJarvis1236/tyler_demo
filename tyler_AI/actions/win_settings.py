import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities

import time
import ctypes

class WinSet:
    def __init__(self):
        self.volume = AudioUtilities.GetSpeakers().EndpointVolume
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)


    def _get_handler(self, func: str):
        handlers = {
            "brightness": self.set_bright,
            "volume": self.set_volume
        }

        return handlers.get(func)


    def set_bright(self, level: int):
        try:
            sbc.set_brightness(level)
        except Exception as e: print(f"Ошибка яркости {e}")


    
    def set_volume(self, level: int):
        try:
            self.volume.SetMasterVolumeLevelScalar(level/100.0, None)
            print(f"Усьановлена громкость {level}")
        except Exception as e: print(f"Ошибка громкости {e}")



    def toggle_mute(self):
        current = self.volume.GetMute()
        self.volume.SetMute(not current, None)


    
    def get_layouts(self):
        count = self.user32.GetKeyboardLayoutList(0, None)
        arr = (ctypes.c_void_p * count)()
        self.user32.GetKeyboardLayoutList(count, arr)

        return list(arr)
    
    def get_current_layout(self):
        hwnd = self.user32.GetForegroundWindow()
        thread_id = self.user32.GetWindowThreadProcessId(hwnd, None)
        return self.user32.GetKeyboardLayout(thread_id)

    def switch_to_next_layout(self):
        VK_MENU = 0x12  # Alt
        VK_SHIFT = 0x10  # Shift
        KEYEVENTF_KEYDOWN = 0
        KEYEVENTF_KEYUP = 2
       
        ctypes.windll.user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYDOWN, 0) # нажать Alt
        ctypes.windll.user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYDOWN, 0) # нажать Shift
        ctypes.windll.user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0) # отпустить Shift
        ctypes.windll.user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0) # отпустить Alt

    def get_lang_code(self):
        layout = self.get_current_layout()
        return hex(layout & 0xFFFF)
    
    def set_lang(self, target_code):
        # получаем текущий язык
        current = self.get_lang_code()
        max_attempts = 10  # чтобы не зациклиться
        attempts = 0

        while current != target_code and attempts < max_attempts:
        # эмуляция Alt+Shift
            VK_MENU = 0x12  # Alt
            VK_SHIFT = 0x10  # Shift
            KEYEVENTF_KEYDOWN = 0
            KEYEVENTF_KEYUP = 2

            ctypes.windll.user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYDOWN, 0)
            ctypes.windll.user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYDOWN, 0)
            ctypes.windll.user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
            ctypes.windll.user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)

            time.sleep(0.1)  # дождаться обновления
            current = self.get_lang_code()
            attempts += 1

        if current != target_code:
            print(f"Не удалось переключить язык на {hex(target_code)}")
        else:
            print(f"Язык установлен: {hex(target_code)}")

    def run(self, params: dict, chat_id: str):
        actions = {
            "set_brightness": lambda: self.set_bright(params.get("definition")),
            "set_volume": lambda: self.set_volume(params.get("definition")),
            "toggle_mute": self.toggle_mute,
            "switch_lang": self.switch_to_next_layout,
            "set_lang": lambda: self.set_lang(params.get("definition"))
        }

        handler = actions.get(params.get("function"))
        if not handler: print(f"Неизвестная функция: {params.get('function')}")
        return handler()


