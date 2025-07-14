import os
import tempfile
import subprocess
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from config import S3_BUCKET, S3_ENDPOINT, S3_PASSWORD, S3_USERNAME

def download_and_convert_to_wav(source: str) -> str:
    """
    source: object key в S3 (без .wav)
    Возвращает путь к локальному временно скачанному .wav файлу, кешируемому в S3
    """

    s3 = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_USERNAME,
        aws_secret_access_key=S3_PASSWORD,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1',
    )

    wav_key = f"{source}.wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        wav_path = tmp_wav.name

    try:
        s3.download_file(S3_BUCKET, wav_key, wav_path)
        return wav_path
    except ClientError as e:
        if e.response['Error']['Code'] != "404":
            raise

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp_raw:
        raw_path = tmp_raw.name
    s3.download_file(S3_BUCKET, source, raw_path)

    subprocess.run([
        "ffmpeg", "-y", "-i", raw_path,
        "-ar", "16000", "-ac", "1", "-f", "wav", wav_path
    ], check=True)

    os.remove(raw_path)

    s3.upload_file(wav_path, S3_BUCKET, wav_key)

    return wav_path
