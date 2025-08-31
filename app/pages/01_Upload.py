import os
import streamlit as st
from app.settings import settings
from app.db.repository import create_upload, create_job
from app.tasks.celery_tasks import transcribe_job

st.title("01 · Загрузка")

f = st.file_uploader("Файл аудио (mp3/wav/flac/m4a/ogg), до 5 минут и 100 МБ", type=["mp3","wav","flac","m4a","ogg"])
if not f:
    st.info("Выберите файл.")
    st.stop()

os.makedirs(settings.storage_dir, exist_ok=True)
tmp_path = os.path.join(settings.storage_dir, f.name)
with open(tmp_path, "wb") as w:
    w.write(f.read())

st.audio(tmp_path)

if st.button("Запустить транскрипцию"):
    upload = create_upload(
        filename=f.name, ext=os.path.splitext(f.name)[1][1:], sr=settings.default_sr,
        duration_sec=0, size_bytes=os.path.getsize(tmp_path), path=tmp_path
    )
    params = {
        "separation": "demucs",
        "highpass": True, "denoise": True, "trim": True, "normalize": True,
        "f0_backend": "torchcrepe", "auto_key": True
    }
    job = create_job(upload_id=upload.id, params_json=params)
    transcribe_job.apply_async(args=[job.id, tmp_path, params], queue="default")
    st.success(f"Задача запущена. ID: {job.id}")
    st.session_state["last_job_id"] = job.id
