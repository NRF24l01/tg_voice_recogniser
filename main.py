from modules import Client, Logger
from asyncio import run
from config import HOST, PORT, API_KEY

class Parrot(Client):
    async def process_message(self, message_type: int, payload: dict, config: dict):
        if message_type == 1:
            if config.get("reply_me", "true") == "true" and payload["my_message"]:
                async with self.to_send_lock:
                    task = {
                        "type": 1,
                        "payload": {
                            "message": payload["message"],
                            "to": payload["from"]
                        }
                    }
                    await self.to_send.put(task)
            if config.get("reply_others", "false") == "true" and not payload["my_message"]:
                async with self.to_send_lock:
                    task = {
                        "type": 1,
                        "payload": {
                            "message": payload["message"],
                            "to": payload["from"]
                        }
                    }
                    await self.to_send.put(task)

async def main():
    logger = Logger()
    client = Parrot(logger)
    await client.init(HOST, PORT, API_KEY)

    await client.polling()

if __name__ == "__main__":
    run(main())