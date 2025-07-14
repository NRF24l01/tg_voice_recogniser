import threading
import time
import queue
import os
from dataclasses import dataclass
from typing import Callable, Any
from transformers import pipeline, AutoProcessor, AutoModelForSpeechSeq2Seq
import torch

@dataclass
class Task:
    uuid: str
    path: str
    meta: dict

@dataclass
class Result:
    uuid: str
    text: str
    meta: dict

class ModelWorker:
    def __init__(self, result_callback: Callable[[Result], Any],
                 model_id="openai/whisper-large-v3-turbo", ttl=600):
        self.queue = queue.Queue()
        self._result_callback = result_callback
        self._model = None
        self._model_loaded_at = 0
        self._model_ttl = ttl
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.model_id = model_id
        self._thread.start()

    def _load_model(self):
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if "cuda" in device else torch.float32
        print("[Model] Loading...")
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        ).to(device)
        processor = AutoProcessor.from_pretrained(self.model_id)
        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=device,
        )
        print("[Model] Loaded.")
        return pipe, time.time()

    def _get_model(self):
        with self._lock:
            now = time.time()
            if self._model is None or (now - self._model_loaded_at > self._model_ttl):
                self._model, self._model_loaded_at = self._load_model()
        return self._model

    def _run(self):
        while not self._stop.is_set():
            try:
                task: Task = self.queue.get(timeout=1)
            except queue.Empty:
                continue

            model = self._get_model()
            try:
                result = model(task.path, return_timestamps=True)
                output = result["text"]
            except Exception as e:
                output = f"[ERROR] {e}"

            try:
                os.remove(task.path)
            except Exception:
                pass

            self._result_callback(Result(uuid=task.uuid, text=output, meta=task.meta))

    def stop(self):
        self._stop.set()
        self._thread.join()

    def submit(self, task: Task):
        self.queue.put(task)
