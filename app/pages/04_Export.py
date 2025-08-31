import os
import streamlit as st
from app.settings import settings

st.title("04 · Экспорт")

job_id = st.session_state.get("last_job_id")
if not job_id:
    st.info("Нет активной задачи.")
    st.stop()

base = os.path.join(settings.storage_dir, f"job_{job_id}")
for fname in ("score.musicxml", "score.pdf", "score.png", "preview.wav"):
    path = os.path.join(base, fname)
    if os.path.exists(path):
        with open(path, "rb") as f:
            st.download_button(f"Скачать {fname}", data=f, file_name=fname)
