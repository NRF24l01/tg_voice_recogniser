import subprocess
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import tempfile
import os
from time import time

# Настройка устройства
device = "cuda:0" if torch.cuda.is_available() else "cpu"
device = "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Модель
model_id = "openai/whisper-small"
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
).to(device)
processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
)

# Путь к видео
video_path = "round.mp4"

# Извлечение аудио через ffmpeg
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
    tmp_audio_path = tmp_audio.name

subprocess.run([
    "ffmpeg", "-y", "-i", video_path,
    "-ar", "16000",  # частота дискретизации
    "-ac", "1",      # моно
    "-f", "wav",     # формат
    tmp_audio_path
], check=True)

# Распознавание
t = time()
result = pipe(tmp_audio_path, return_timestamps=True)
print(time()-t)
print(result["text"])

# Очистка
os.remove(tmp_audio_path)
