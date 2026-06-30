class PatchApplier:
    def __init__(self):
        pass

    def apply_operations(self, code: str, operations: list) -> str:
        updated_code = code

        for op in operations:
            action = op["action"]

            if action == "replace":
                updated_code = updated_code.replace(op["target"], op["new_code"])
            elif action == "append": 
                updated_code += "\n" + op["new_code"]

        return updated_code
