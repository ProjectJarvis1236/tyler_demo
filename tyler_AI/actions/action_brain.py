from . import registry as reg
from memory import action_memory

class ActionBrain:
    def __init__(self):
        pass

    async def execute_actions(self, actions: list, chat_id: str):
        results = []
        if not actions: return results

        for action in actions:
            action_type = action.get("type")
            params = action.get("params", {})

            if not action_type: 
                results.append({"error": "Что-то не так с action_type"})
                continue

            handler = reg.ACTION_REGISTRY.get(action_type)
            if not handler: 
                results.append({"error": f"Неизвестное действие {action_type}"})
                continue

            try:
                result = await handler.run(params, chat_id)
    
                results.append({
                    "type": action_type,
                    "result": result
                })

                action_memory.add_action(chat_id, action_type, {
                "params": params,
                "status": "success"
                #"result": result
                })


            except Exception as e:
                results.append({
                    "type": action_type,
                    "error": str(e)
                })

                action_memory.add_action(chat_id, action_type, {
                "params": params,
                "status": "error"
                #"result": result
                })

        return results

           