from . import AsyncSocketController, Logger
from asyncio import open_connection, sleep, Lock, Queue
from typing import Any, Dict


class Message:
    def __init__(self, client: "Client", chat_id: int, msg_id: int, message: Dict[str, Any]):
        self._client = client
        self.message_dict = message
        self.message_id = msg_id
        self.chat_id = chat_id
    
    async def edit(self, text):
        payload = {
            "type": 2,
            "payload": {
                "chat_id": self.chat_id,
                "message_id": self.message_id,
                "text": text
            }
        }
        await self._client._send_command(payload)


class Client(AsyncSocketController):
    def __init__(self, logger: Logger):
        super().__init__()
        self.logger = logger
        self.to_send = Queue()
        self.to_send_lock = Lock()

    async def init(self, host: str, port: int, key: str):
        self.logger.info(f"Trying to connect to {host}:{port}")
        self.reader, self.writer = await open_connection(host, port)
        self.logger.info(f"Success!")
        await self.send_json({"key": key})
        answer = await self.read_json()
        if not answer["connected"]:
            self.logger.critical("Key is invalid.")
            raise Exception("Key is invalid.")
        self.logger.info(f"Registered as {answer['name']}")
    
    async def send_message(self, chat_id: int, text: str, reply_to: int | None = None):
        payload = {
            "type": 1,
            "require_answer": True,
            "payload": {
                "to": chat_id,
                "message": text,
                "reply_to": reply_to,
            }
        }
        await self._send_command(payload)
        self.logger.debug("Started waiting for message id")
        answer = await self.wait_for_answer()
        self.logger.debug("Got answer with msg id")
        msg = Message(client=self, chat_id=answer["chat_id"], msg_id=answer["message"]["id"], message=answer["message"])
        return msg
    
    async def _send_command(self, cmd: Dict[str, Any]):
        self.logger.debug("Sending json")
        async with self.to_send_lock:
            await self.send_json(cmd)
    
    async def wait_for_answer(self):
        answer = None
        while not answer:
            if await self.data_available():
                self.logger.debug("Some bytes available")
                try:
                    data = await self.read_json()
                    self.logger.debug("Received message from server:", data)
                    if data.get("type", None) == 0:
                        answer = data
                        return data
                    else:
                        await self.process_message(message_type=data["type"], payload=data["payload"], config=data["config"])
                except Exception as e:
                    raise e
                    self.logger.warning(f"Error reading message from server: {e}")
    
    async def polling(self):
        try:
            while True:
                if await self.data_available():
                    try:
                        data = await self.read_json()
                        self.logger.debug("Received message from server:", data)
                        await self.process_message(message_type=data["type"], payload=data["payload"], config=data["config"])
                    except Exception as e:
                        raise e
                        self.logger.warning(f"Error reading message from server: {e}")
                
                async with self.to_send_lock:
                    while not self.to_send.empty():
                        task = await self.to_send.get()
                        await self.send_json(task)

                await sleep(0.05)

        except Exception as e:
            raise e
            self.logger.info(f"Host disconnected: {e}")
            self.writer.close()
            await self.writer.wait_closed()
    
    async def process_message(self, message_type: int, payload: dict):
        raise NotImplementedError