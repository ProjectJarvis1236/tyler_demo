import json
import httpx

import configs


SYSTEM_PROMPT = """Ты супер прогер и тд"""

API_KEYS = {
    "nvidia/nemotron-3-super-120b-a12b:free": configs.OPENROUTER_KEY, 
    "apifreellm": configs.APIFREELLM_KEY
}

class PlannerModule:
    def __init__(self):
        pass

    def _build_prompt(self, code: str, task: str) -> str:
        return f"""
Ты - планировщик изменений кода.
Задача: {task}
Код: {code}
Верни {{"operations": 
[{{
    "action": "replace" | "append",
    "target": "<cтарый код>",
    "new_code": "<новый код>"
}}]}}
"""
    
    async def _call_llm(self, prompt: str) -> str:
            model = "nvidia/nemotron-3-super-120b-a12b:free"
            API_KEY = API_KEYS[model]
            url = configs.URLS[model]

            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            system_prompt = SYSTEM_PROMPT

            data = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
            
            async with httpx.AsyncClient(timeout=configs.TIMEOUT) as client:
                response = await client.post(url, headers=headers, json=data)
                result = response.json()

            content = result["choices"][0]["message"]["content"]
            return json.loads(content)
    
