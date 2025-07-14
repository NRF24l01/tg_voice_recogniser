from modules import Client, Logger, download_and_convert_to_wav, ModelWorker, Task, Result
from asyncio import Queue, create_task
from asyncio import run
from config import HOST, PORT, API_KEY

class Recognizer(Client):
    def __init__(self, logger):
        super().__init__(logger)
        self._results = Queue()
        self._worker = ModelWorker(result_callback=self._on_model_result)
        self._loop = None

    def _on_model_result(self, result: Result):
        self._loop.call_soon_threadsafe(self._results.put_nowait, result)

    async def _result_dispatcher(self):
        while True:
            result = await self._results.get()
            print(f"[{result.uuid}] TEXT: {result.text}")

    async def process_message(self, message_type: int, payload: dict, config: dict):
        if message_type == 1:
            message = payload["message"].strip()
            if message.startswith("/to_text"):
                file_link = payload.get("reply_to_media_id")
                uuid = payload.get("uuid") or "unknown"
                chat_id = payload["chat_id"]
                if not file_link:
                    return

                wav_path = download_and_convert_to_wav(file_link)
                print(f"[{uuid}] File downloaded: {wav_path}")
                task = Task(uuid=uuid, path=wav_path, meta={"chat_id": chat_id})
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
