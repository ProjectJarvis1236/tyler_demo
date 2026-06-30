import os
import winreg
import psutil
from pathlib import Path
import win32com.client
from typing import Dict

MAX_APPS = 50

KEYWORDS = ["excel", "powerpnt", "winword", "photoshop", "steam",
            "telegram", "discord", "microsoft", "msedge", "firefox",
            "chrome", "yandex", "vpn", "devenv", "counter-Strike",
            "blend", "notepad", "explorer", "creative cloud", "unity",
            "visual studio", "code"]

def matches_keywords(name: str)->bool:
    name = normalize(name)
    for kw in KEYWORDS:
        if kw in name: return True
    return False


def normalize(name: str) -> str:
    name = name.lower().strip()
    if name.endswith(".exe"):
        name = name[:-4]
    return name


def scan_start_menu(result: Dict[str, dict]) -> None:
    start_paths = [
        Path(os.environ["ProgramData"]) / r"Microsoft\\Windows\\Start Menu\\Programs",
        Path(os.environ["APPDATA"]) / r"Microsoft\\Windows\\Start Menu\\Programs",
    ]

    shell = win32com.client.Dispatch("WScript.Shell")

    for base in start_paths:
        if not base.exists(): continue
        

        for lnk in base.rglob("*.lnk"):
            try:
                shortcut = shell.CreateShortCut(str(lnk))
                target = shortcut.Targetpath

                if not target or not target.lower().endswith(".exe"):
                    continue

                if not os.path.exists(target):
                    continue

                key = normalize(os.path.basename(target))
                if not matches_keywords(key): continue

                if key not in result:
                    result[key] = {
                        "path": target,
                        "name": os.path.basename(target)
                    }

                    if len(result) >= MAX_APPS:
                        return

            except Exception:
                continue


def scan_registry(result: Dict[str, dict]) -> None:
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
    ]

    for root, path in reg_paths:
        try:
            main_key = winreg.OpenKey(root, path)
        except Exception:
            continue

        try:
            count = winreg.QueryInfoKey(main_key)[0]
        except Exception:
            continue

        for i in range(count):
            try:
                subkey_name = winreg.EnumKey(main_key, i)
                subkey = winreg.OpenKey(main_key, subkey_name)

                install_location, _ = winreg.QueryValueEx(subkey, "InstallLocation")

                if not install_location or not os.path.exists(install_location):
                    continue

                for file in os.listdir(install_location):
                    if not file.lower().endswith(".exe"):
                        continue

                    key = normalize(file)
                    if not matches_keywords(key): continue

                    if key not in result:
                        result[key] = {
                            "path": os.path.join(install_location, file),
                            "name": file
                        }

                        if len(result) >= MAX_APPS:
                            return

                    break

            except Exception:
                continue


def scan_running_processes(result: Dict[str, dict]) -> None:
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            exe_path = proc.info["exe"]
            exe_name = proc.info["name"]

            if not exe_path or not exe_path.lower().endswith(".exe"):
                continue

            key = normalize(exe_name)
            if not matches_keywords(key): continue

            if key not in result:
                result[key] = {
                    "path": exe_path,
                    "name": exe_name
                }

                if len(result) >= MAX_APPS:
                    return

        except Exception:
            continue


def build_app_dictionary() -> Dict[str, dict]:
    result: Dict[str, dict] = {}
    scan_start_menu(result)
    if len(result) >= MAX_APPS:
        return result

    scan_registry(result)
    if len(result) >= MAX_APPS:
        return result

    scan_running_processes(result)
    
#здесь нужно сделать добавление приложений пользователя 
    return result