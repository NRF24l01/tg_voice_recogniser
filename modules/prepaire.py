import os
import tempfile
import subprocess
import requests
import boto3
from botocore.client import Config
from urllib.parse import urlparse
from config import S3_BUCKET, S3_ENDPOINT, S3_PASSWORD, S3_USERNAME

def download_and_convert_to_wav(source: str, use_boto=False):
    """
    source: can be a URL or object key
    use_boto: True to use boto3 + key; False to use direct HTTP request
    returns: path to temp WAV file
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp_raw:
        raw_path = tmp_raw.name

    if use_boto:
        # assume source is an S3 key
        s3 = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_USERNAME,
            aws_secret_access_key=S3_PASSWORD,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',
        )
        s3.download_file(S3_BUCKET, source, raw_path)
    else:
        # assume source is a full URL
        r = requests.get(source)
        r.raise_for_status()
        with open(raw_path, 'wb') as f:
            f.write(r.content)

    # Convert to WAV
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        wav_path = tmp_wav.name

    subprocess.run([
        "ffmpeg", "-y", "-i", raw_path,
        "-ar", "16000", "-ac", "1", "-f", "wav", wav_path
    ], check=True)

    os.remove(raw_path)
    return wav_path
