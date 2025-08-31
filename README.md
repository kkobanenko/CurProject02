# Melody → Score (MVP)

Стримлит-приложение для извлечения основной мелодической линии из коротких аудио (≤5 мин, ≤100 МБ) и экспорта MusicXML (+ опционально PDF/PNG).

## Быстрый старт
```bash
cp .env.example .env
docker compose up --build
```

Откройте http://localhost:8501, загрузите файл на странице **01_Upload**, дождитесь завершения задачи, затем перейдите в **03_Preview_and_Editor** и **04_Export**.

### Рендер PDF/PNG
По умолчанию `RENDERER=none` — экспортируется только MusicXML.
Чтобы включить рендер:
1) Установите MuseScore CLI или Verovio в `docker/Dockerfile.app` (раскомментируйте установку).
2) Поставьте `RENDERER=mscore` или `RENDERER=verovio` в `.env`.

## Примечания
- Разделение источников реализовано через **Demucs** (PyTorch), чтобы избежать проблем TF/Spleeter в slim-образах.
- Добавлены все `__init__.py` для корректных импортов.
