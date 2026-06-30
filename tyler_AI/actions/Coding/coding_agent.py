from .codebase_scanner import CodebaseScanner
from .code_editor import CodeEditorModule


class CodingAgent:
    def __init__(self):
        self.scanner = CodebaseScanner()
        self.editor = CodeEditorModule()

    def run(self, params: dict):
        scan_result = self.scanner.run(params)

        if not scan_result["success"]: return scan_result
        results = []

        for file_path in scan_result["files"]:
            result = self.editor.run({
                "file_path": file_path,
                "prompt": params["prompt"]
            })

            results.append(result)

        return {"success": True, "results": results}