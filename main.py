from modules import Client, Logger, download_and_convert_to_wav, ModelWorker, Task, Result, Message
from asyncio import Queue, create_task
from asyncio import run, sleep
from snowflake import SnowflakeGenerator
from config import HOST, PORT, API_KEY
from time import time

class Recognizer(Client):
    def __init__(self, logger):
        super().__init__(logger)
        self._results = Queue()
        self._worker = ModelWorker(result_callback=self._on_model_result)
        self._loop = None
        self.gen = SnowflakeGenerator(1)

    def _on_model_result(self, result: Result):
        self._loop.call_soon_threadsafe(self._results.put_nowait, result)

    async def _result_dispatcher(self):
        while True:
            result = await self._results.get()
            self.logger.debug(f"Message(task - {result.uuid}) parsed, text: '{result.text}'")
            msg = Message(self, result.meta["chat_id"], result.meta["msg_id"], {})
            await msg.edit(f"А чё я сразу, думал {round(time()-result.meta["stime"], 2)}с, там короче чёт такое было: ``` {result.text}```")
            self.logger.info("Processing completed")

    async def process_message(self, message_type: int, payload: dict, config: dict):
        if message_type == 1:
            if not payload["my_message"]:
                return
            message = payload["message"].strip()
            if message.startswith("/to_text"):
                file_link = payload.get("reply_to_media_id")
                uuid = next(self.gen)
                chat_id = payload["chat_id"]
                if not file_link:
                    self.logger.warning(f"Got non media message")
                    await self.send_message(chat_id, "Ты втираешь мне какую-то дичь, это не кружочек или войса", reply_to=payload["msg_id"])
                    return
                self.logger.debug("sending message about start")
                msg = await self.send_message(chat_id, "Запрос на обработку добавлен, ожидайте много время", reply_to=payload["msg_id"])

                wav_path = download_and_convert_to_wav(file_link)
                print(f"[{uuid}] File downloaded: {wav_path}")
                task = Task(uuid=uuid, path=wav_path, meta={"chat_id": chat_id, "msg_id": msg.message_id, "stime": time()})
                self._worker.submit(task)

    async def init(self, *args, **kwargs):
        await super().init(*args, **kwargs)
        self._loop = self.get_loop()
        create_task(self._result_dispatcher())

    def get_loop(self):
        import asyncio
        return asyncio.get_running_loop()

    def stop(self):
        self._worker.stop()

async def main():
    logger = Logger()
    client = Recognizer(logger)
    await client.init(HOST, PORT, API_KEY)
    await client.polling()

if __name__ == "__main__":
    try:
        run(main())
    finally:
        worker.stop()
