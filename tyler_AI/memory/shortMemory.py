import configs
from memory import chat_func

#короткая память!
#можно добавить проверку на длину сообщения, если сообщение слишком длинное, то,
#перед сохранением в память делать summary через функцию в dialog memory

#def add_message(sender: str, text: str):
#    messages.append({"sender": sender, "text": text})

#def get_messages() -> list:
#    return messages

async def get_short_context(chat_id) -> str:
    return " | ".join(m["text"] for m in get_short_memory(chat_id))


async def get_short_memory(chat_id) -> list:
    short_memory = []

    messages = chat_func.get_last_messages(chat_id, configs.MEMORY_LIMIT)

    for m in messages:
        text = m["text"]

        # if len(text) > 200:
        #     text = dialog_memory.create_summary(text)

        role = "assistant" if m["sender"] == "bot" else "user"

        short_memory.append({
            "role": role,
            "content": text
        })

    return short_memory