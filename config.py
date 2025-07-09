from dotenv import load_dotenv
from os import getenv

load_dotenv()

# Socket server conifg
HOST = getenv("HOST", "127.0.0.1")
PORT = int(getenv("PORT", "4375"))
API_KEY = getenv("API_KEY")

# S3 config
S3_ENDPOINT = getenv("S3_ENDPOINT", "http://127.0.0.1:9000")
S3_USERNAME = getenv("S3_USERNAME")
S3_PASSWORD = getenv("S3_PASSWORD")
S3_BUCKET = getenv("S3_BUCKET")