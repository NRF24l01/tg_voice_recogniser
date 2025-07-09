from modules import Client, Logger, download_and_convert_to_wav
from asyncio import run
from config import HOST, PORT, API_KEY

class Recognizer(Client):
    async def process_message(self, message_type: int, payload: dict, config: dict):
        print(message_type, payload, config)
        if message_type == 1:
            message = payload["message"].strip()
            if message.startswith("/to_text"):
                model = config.get("model", "openai/whisper-large-v3-turbo")
                file_link = payload["reply_to_media_id"]
                if not file_link:
                    return
                
                wav_path = download_and_convert_to_wav(file_link)
                print(wav_path)
                

async def main():
    logger = Logger()
    client = Recognizer(logger)
    await client.init(HOST, PORT, API_KEY)

    await client.polling()

if __name__ == "__main__":
    run(main())