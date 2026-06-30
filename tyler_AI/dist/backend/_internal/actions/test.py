import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from actions.app_open import AppOpen


async def main():
    app = AppOpen()

    #print(await app.run({"app": "notepad"}))
    #print(await app.run({"app": "vscode"}))
    print(await app.run({"app": "browser", "url": "https://google.com"}))
    #print(await app.run({"app": "telegram"}))
    #print(await app.run({"app": "word"}))


asyncio.run(main())