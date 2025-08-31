import os
import streamlit as st
from app.db.repository import get_job
from app.settings import settings

st.title("03 · Предпросмотр и редактор")

job_id = st.session_state.get("last_job_id")
if not job_id:
    st.info("Нет активной задачи. Запустите транскрипцию на странице Загрузка.")
    st.stop()

job = get_job(job_id)
st.write(f"Статус: **{job.status}** · Прогресс: **{job.progress}%**")
if job.status != "done":
    st.warning("Задача в процессе. Обновите страницу позднее.")
    st.stop()

base = os.path.join(settings.storage_dir, f"job_{job_id}")
mx = os.path.join(base, "score.musicxml")
png = os.path.join(base, "score.png")
wav = os.path.join(base, "preview.wav")

st.subheader("Синтезированный рендер")
if os.path.exists(wav):
    st.audio(wav)

st.subheader("Партитура (PNG)")
if os.path.exists(png):
    st.image(png, caption="Автосгенерированный нотный стан (PNG)")
else:
    st.info("PNG отсутствует. Включите рендерер (MuseScore/Verovio) в .env и пересоберите образ.")
