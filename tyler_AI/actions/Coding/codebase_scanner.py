from pathlib import Path
from typing import Dict, Any, List


class CodebaseScanner:
    def __init__(self):
        pass

    def _scan_files(self, root_path: str, extensions: List[str]) -> List[str]:
        root = Path(root_path)
        files = []

        for file in root.rglob("*"):
            if file.is_file() and file.suffix in extensions: files.append(str(file))
        
        return files
    
    def _filter_relevant_files(self, files: List[str], task: str) -> List[str]:
        keywords = task.lower.split()
        relevant = []

        for file in files:
            path_lower = file.lower()
            if any(word in path_lower for word in keywords): relevant.append(file)

        return relevant[:10]
    
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root_path = params.get("root_path")
        task = params.get("prompt")
        extensions = params.get("extensions", [".py", ".js", ".ts", ".tsx", ".jsx"])

        if not root_path: return{"success": False, "error": "Не передан root_path"}
        if not task: return{"success": False, "error": "Не передан task"}

        try:
            files = self._scan_files(root_path, extensions)
            relevant_files = self._filter_relevant_files(files, task)

            return {"success": True, "files": relevant_files}
        except Exception as e: return {"success": False, "error": str(e)}