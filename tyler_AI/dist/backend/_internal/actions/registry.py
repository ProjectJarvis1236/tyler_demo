from actions.search_open import SearchOpen
from actions.app_open import AppOpen
from actions.win_settings import WinSet
from actions.windows_manager import WindowsManager
from actions.Parse_to_text import WordCoordinator
from actions.excel_manager import ExcelManager
from actions.presentation_manager import PresentationManager
from actions.emails import Emails
from actions.File_manager import FileManager
from actions.llm_searching import LLMWebSearch
from actions.tg_mess import TgMessage

ACTION_REGISTRY = {
    "web_search": SearchOpen(),
    "app_open": AppOpen(),
    "win_settings": WinSet(),
    "windows_open": WindowsManager(),
    "Web_parse" : WordCoordinator(),
    "excel_manager": ExcelManager(),
    "create_presentation": PresentationManager(),
    "Emails": Emails(),
    "file_manager": FileManager(),
    "llm_searching": LLMWebSearch(),
    "tg_message": TgMessage()
}