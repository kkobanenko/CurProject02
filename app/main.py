import streamlit as st
from app.utils.logging import configure_json_logging
from app.db.repository import init_db
from app.settings import settings

configure_json_logging()
init_db()

st.set_page_config(page_title="Melody→Score", page_icon="🎼", layout="wide")
st.title("🎼 Melody → Score (MVP)")
st.write("Загрузите аудио на странице **01_Upload** и следуйте шагам (Настройки → Предпросмотр/Редактор → Экспорт → История).")

st.sidebar.markdown("**Хранилище**")
st.sidebar.code(settings.storage_dir)
