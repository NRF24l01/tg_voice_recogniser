# Сервис для преобразования войсов и кружочков в текст

Умеет преобразовывать голосовые и кружочки в текст
- Файлы через s3
- Распознование за счёт библиотек transformers+torch
- ТОРЧ НАДО РУКАМИ СТАВИТЬ
- и ffmpeg нужен

## УСТАНОВКА
- Установите зависимости
```
pip install -r requirements.txt
```

- Поставьте торчу
```
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

- Радуйтесь, отвечая на кружочки или голосовые через /to_text
