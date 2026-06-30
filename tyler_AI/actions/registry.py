from .search_open import SearchOpen
from .app_open import AppOpen
from .win_settings import WinSet
from .windows_manager import WindowsManager
from .Parse_to_text import WordCoordinator
from .excel_manager import ExcelManager
from .presentation_manager import PresentationManager
from .emails import Emails
from .File_manager import FileManager
from .llm_searching import LLMWebSearch
from .tg_mess import TgMessage
from .word_manager import DocumentWorker

ACTION_REGISTRY = {
    "web_search": SearchOpen(),
    "app_open": AppOpen(),
    "win_settings": WinSet(),
    "windows_open": WindowsManager(),
    "Web_parse": WordCoordinator(),
    "excel_manager": ExcelManager(),
    "create_presentation": PresentationManager(),
    "Emails": Emails(),
    "file_manager": FileManager(),
    "llm_searching": LLMWebSearch(),
    "tg_message": TgMessage(),
    "word_manager": DocumentWorker()
}
