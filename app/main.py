import streamlit as st
from app.utils.logging import configure_json_logging
from app.db.repository import init_db, check_db_connection
from app.db.migrations import run_migrations
from app.db.migrations import create_logs_table
from app.settings import settings

configure_json_logging()

# Initialize database
try:
    init_db()
    run_migrations()
    create_logs_table()
    
    if not check_db_connection():
        st.error("❌ Не удалось подключиться к базе данных")
        st.stop()
    else:
        st.success("✅ База данных подключена")
        
except Exception as e:
    st.error(f"❌ Ошибка инициализации базы данных: {e}")
    st.stop()

st.set_page_config(page_title="Melody→Score", page_icon="🎼", layout="wide")
st.title("🎼 Melody → Score (MVP)")
st.write("Загрузите аудио на странице **01_Upload** и следуйте шагам (Настройки → Предпросмотр/Редактор → Экспорт → История).")

st.sidebar.markdown("**Хранилище**")
st.sidebar.code(settings.storage_dir)
