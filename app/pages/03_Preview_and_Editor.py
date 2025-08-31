import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from app.db.repository import get_job, get_upload, get_artifacts_by_job
from app.settings import settings

st.set_page_config(page_title="Предпросмотр - Melody→Score", page_icon="🎵")

# Page header
st.title("🎵 03 · Предпросмотр и редактор")
st.markdown("Просмотр результатов транскрипции и редактирование нотной записи.")

# Check for active job
job_id = st.session_state.get("last_job_id")
if not job_id:
    st.warning("⚠️ Нет активной задачи. Перейдите на страницу **01_Загрузка** для создания задачи.")
    st.stop()

# Get job information
try:
    job = get_job(job_id)
    if not job:
        st.error(f"❌ Задача {job_id} не найдена")
        st.stop()
    
    upload = get_upload(job.upload_id)
    if not upload:
        st.error(f"❌ Загрузка для задачи {job_id} не найдена")
        st.stop()
    
    # Job status check
    if job.status != "done":
        st.warning(f"⚠️ Задача еще не завершена. Статус: {job.status}, Прогресс: {job.progress}%")
        st.info("🔄 Обновите страницу после завершения задачи")
        st.stop()
    
    # Job metadata
    st.subheader("📊 Информация о задаче")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("ID задачи", job_id)
    with col2:
        st.metric("Файл", upload.filename)
    with col3:
        st.metric("Длительность", f"{upload.duration_sec} сек")
    with col4:
        if job.finished_at:
            st.metric("Завершена", job.finished_at.strftime("%H:%M:%S"))
    
    # Get artifacts
    artifacts = get_artifacts_by_job(job_id)
    artifact_paths = {a.kind: a.path for a in artifacts}
    
    # Job directory
    job_dir = os.path.join(settings.storage_dir, f"job_{job_id}")
    
    # Parameters display
    with st.expander("⚙️ Параметры обработки"):
        params = job.params_json
        st.json(params)
    
    # Audio preview
    st.subheader("🎵 Аудиопревью")
    
    if "audio_preview" in artifact_paths and os.path.exists(artifact_paths["audio_preview"]):
        st.audio(artifact_paths["audio_preview"], format="audio/wav")
        
        # Audio comparison
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Оригинал:**")
            st.audio(upload.path, format=f"audio/{upload.ext}")
        with col2:
            st.markdown("**Синтезированная мелодия:**")
            st.audio(artifact_paths["audio_preview"], format="audio/wav")
    else:
        st.warning("⚠️ Аудиопревью не найдено")
    
    # Score visualization
    st.subheader("📜 Нотная запись")
    
    # Check for different score formats
    score_available = False
    
    if "png" in artifact_paths and os.path.exists(artifact_paths["png"]):
        st.markdown("**PNG рендер:**")
        st.image(artifact_paths["png"], caption="Нотная запись (PNG)")
        score_available = True
    
    if "pdf" in artifact_paths and os.path.exists(artifact_paths["pdf"]):
        st.markdown("**PDF рендер:**")
        with open(artifact_paths["pdf"], "rb") as f:
            st.download_button(
                label="📄 Скачать PDF",
                data=f.read(),
                file_name=f"score_{job_id}.pdf",
                mime="application/pdf"
            )
        score_available = True
    
    if "musicxml" in artifact_paths and os.path.exists(artifact_paths["musicxml"]):
        st.markdown("**MusicXML файл:**")
        with open(artifact_paths["musicxml"], "r") as f:
            musicxml_content = f.read()
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 Скачать MusicXML",
                data=musicxml_content,
                file_name=f"score_{job_id}.musicxml",
                mime="application/xml"
            )
        with col2:
            if st.button("👁️ Просмотреть MusicXML"):
                st.code(musicxml_content, language="xml")
        
        score_available = True
    
    if not score_available:
        st.error("❌ Нотная запись не найдена")
        st.info("💡 Убедитесь, что рендерер (MuseScore/Verovio) включен в настройках")
    
    # Note editor (simplified)
    st.subheader("✏️ Редактор нот")
    
    # Create sample note data for demonstration
    if "musicxml" in artifact_paths:
        try:
            # Parse basic note information from MusicXML
            import xml.etree.ElementTree as ET
            tree = ET.parse(artifact_paths["musicxml"])
            root = tree.getroot()
            
            # Extract notes (simplified)
            notes_data = []
            for note in root.findall(".//note"):
                pitch_elem = note.find("pitch")
                duration_elem = note.find("duration")
                
                if pitch_elem is not None:
                    step = pitch_elem.find("step")
                    octave = pitch_elem.find("octave")
                    if step is not None and octave is not None:
                        pitch = f"{step.text}{octave.text}"
                        duration = float(duration_elem.text) / 4 if duration_elem is not None else 1.0
                        notes_data.append({
                            "Нота": pitch,
                            "Длительность": f"{duration:.2f}",
                            "Такт": len(notes_data) // 4 + 1
                        })
            
            if notes_data:
                df = pd.DataFrame(notes_data)
                st.markdown("**Извлеченные ноты:**")
                st.dataframe(df, use_container_width=True)
                
                # Note editing interface
                st.markdown("**Редактирование нот:**")
                st.info("💡 Функция редактирования нот будет добавлена в следующих версиях")
                
                # Export edited notes
                if st.button("💾 Сохранить изменения"):
                    st.success("✅ Изменения сохранены (демо)")
            else:
                st.warning("⚠️ Не удалось извлечь ноты из MusicXML")
                
        except Exception as e:
            st.warning(f"⚠️ Ошибка парсинга MusicXML: {e}")
    
    # Statistics and analysis
    st.subheader("📈 Статистика")
    
    if "musicxml" in artifact_paths:
        try:
            # Basic statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Всего нот", len(notes_data) if 'notes_data' in locals() else "N/A")
            with col2:
                if 'notes_data' in locals() and notes_data:
                    unique_pitches = len(set(note["Нота"] for note in notes_data))
                    st.metric("Уникальных нот", unique_pitches)
                else:
                    st.metric("Уникальных нот", "N/A")
            with col3:
                if 'notes_data' in locals() and notes_data:
                    avg_duration = sum(float(note["Длительность"]) for note in notes_data) / len(notes_data)
                    st.metric("Средняя длительность", f"{avg_duration:.2f}")
                else:
                    st.metric("Средняя длительность", "N/A")
            
            # Pitch distribution chart
            if 'notes_data' in locals() and notes_data:
                pitch_counts = {}
                for note in notes_data:
                    pitch = note["Нота"]
                    pitch_counts[pitch] = pitch_counts.get(pitch, 0) + 1
                
                fig = px.bar(
                    x=list(pitch_counts.keys()),
                    y=list(pitch_counts.values()),
                    title="Распределение нот по высоте",
                    labels={"x": "Нота", "y": "Количество"}
                )
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.warning(f"⚠️ Ошибка анализа статистики: {e}")
    
    # Navigation
    st.markdown("---")
    st.markdown("**Навигация:**")
    st.markdown("1. Перейдите на страницу **04_Экспорт** для скачивания файлов")
    st.markdown("2. Перейдите на страницу **05_История** для просмотра всех задач")
    
    # Auto-refresh option
    if st.button("🔄 Обновить данные"):
        st.rerun()

except Exception as e:
    st.error(f"❌ Ошибка загрузки данных: {e}")
    st.error("Попробуйте обновить страницу или обратитесь к администратору")
