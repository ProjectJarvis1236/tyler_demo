from pathlib import Path
from typing import Dict, Any
from .patch_applier import PatchApplier
from .planner import PlannerModule



class CodeEditorModule:
    def __init__(self):
        self.planner = PlannerModule()
        self.patcher = PatchApplier()

    def _read_file(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists(): raise FileNotFoundError(f"Файл не найден: {file_path}")

        return path.read_text(encoding="utf-8")
    
    def _write_file(self, file_path: str, content: str) -> None:
        Path(file_path).write_text(content, encoding="utf-8")

    def _backup_file(self, file_path: str) -> None:
        content = self._read_file(file_path)
        backup_file = f"{file_path}.bak"
        Path(backup_file).write_text(content, encoding="utf-8")



    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        file_path = params.get("file_path")
        task = params.get("prompt")

        if not file_path: return {"success": False, "error": "Не передан prompt"}
        if not task: return {"success": False, "error": "Не передан task"}

        code  = self._read_file(file_path)
        operations_result = self.planner.run({"code": code, "prompt": task})
        new_code = self.patcher.apply_operations(code, operations_result["operations"])

        self._backup_file(file_path)
        self._write_file(file_path, new_code)

        return {"success": True, "file": file_path}


         
              
         