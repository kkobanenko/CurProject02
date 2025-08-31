import os
import streamlit as st
import zipfile
import tempfile
from datetime import datetime
from app.db.repository import get_job, get_upload, get_artifacts_by_job
from app.settings import settings

st.set_page_config(page_title="Экспорт - Melody→Score", page_icon="📤")

# Page header
st.title("📤 04 · Экспорт")
st.markdown("Скачивание результатов транскрипции в различных форматах.")

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
    
    # Job info
    st.subheader("📋 Информация о задаче")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ID задачи", job_id)
    with col2:
        st.metric("Файл", upload.filename)
    with col3:
        if job.finished_at:
            st.metric("Завершена", job.finished_at.strftime("%H:%M:%S"))
    
    # Get artifacts
    artifacts = get_artifacts_by_job(job_id)
    artifact_paths = {a.kind: a.path for a in artifacts}
    
    # Job directory
    job_dir = os.path.join(settings.storage_dir, f"job_{job_id}")
    
    # File availability check
    st.subheader("📁 Доступные файлы")
    
    file_status = {}
    for kind, path in artifact_paths.items():
        if os.path.exists(path):
            file_size = os.path.getsize(path) / (1024 * 1024)  # MB
            file_status[kind] = {"exists": True, "size": file_size}
        else:
            file_status[kind] = {"exists": False, "size": 0}
    
    # Display file status
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if file_status.get("musicxml", {}).get("exists"):
            st.success("✅ MusicXML")
            st.caption(f"{file_status['musicxml']['size']:.1f} МБ")
        else:
            st.error("❌ MusicXML")
    with col2:
        if file_status.get("pdf", {}).get("exists"):
            st.success("✅ PDF")
            st.caption(f"{file_status['pdf']['size']:.1f} МБ")
        else:
            st.error("❌ PDF")
    with col3:
        if file_status.get("png", {}).get("exists"):
            st.success("✅ PNG")
            st.caption(f"{file_status['png']['size']:.1f} МБ")
        else:
            st.error("❌ PNG")
    with col4:
        if file_status.get("audio_preview", {}).get("exists"):
            st.success("✅ WAV")
            st.caption(f"{file_status['audio_preview']['size']:.1f} МБ")
        else:
            st.error("❌ WAV")
    
    # Individual file downloads
    st.subheader("📥 Скачивание файлов")
    
    # MusicXML
    if file_status.get("musicxml", {}).get("exists"):
        with open(artifact_paths["musicxml"], "r") as f:
            musicxml_content = f.read()
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 Скачать MusicXML",
                data=musicxml_content,
                file_name=f"score_{job_id}.musicxml",
                mime="application/xml",
                help="Стандартный формат нотной записи"
            )
        with col2:
            st.info("🎼 MusicXML - стандартный формат для нотных редакторов")
    else:
        st.warning("⚠️ MusicXML файл недоступен")
    
    # PDF
    if file_status.get("pdf", {}).get("exists"):
        with open(artifact_paths["pdf"], "rb") as f:
            pdf_content = f.read()
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 Скачать PDF",
                data=pdf_content,
                file_name=f"score_{job_id}.pdf",
                mime="application/pdf",
                help="Векторный формат для печати"
            )
        with col2:
            st.info("📄 PDF - векторный формат для печати и просмотра")
    else:
        st.warning("⚠️ PDF файл недоступен")
    
    # PNG
    if file_status.get("png", {}).get("exists"):
        with open(artifact_paths["png"], "rb") as f:
            png_content = f.read()
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="🖼️ Скачать PNG",
                data=png_content,
                file_name=f"score_{job_id}.png",
                mime="image/png",
                help="Растровый формат для веб"
            )
        with col2:
            st.info("🖼️ PNG - растровый формат для веб-страниц")
    else:
        st.warning("⚠️ PNG файл недоступен")
    
    # Audio preview
    if file_status.get("audio_preview", {}).get("exists"):
        with open(artifact_paths["audio_preview"], "rb") as f:
            wav_content = f.read()
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="🎵 Скачать WAV",
                data=wav_content,
                file_name=f"preview_{job_id}.wav",
                mime="audio/wav",
                help="Аудиопревью синтезированной мелодии"
            )
        with col2:
            st.info("🎵 WAV - аудиопревью синтезированной мелодии")
    else:
        st.warning("⚠️ WAV файл недоступен")
    
    # Batch download
    st.subheader("📦 Пакетное скачивание")
    
    available_files = [kind for kind, status in file_status.items() if status.get("exists")]
    
    if available_files:
        # Create ZIP archive
        if st.button("📦 Скачать все файлы (ZIP)", type="primary"):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
                    with zipfile.ZipFile(tmp_file.name, 'w') as zipf:
                        for kind in available_files:
                            file_path = artifact_paths[kind]
                            file_name = f"{kind}_{job_id}.{kind}"
                            zipf.write(file_path, file_name)
                    
                    # Read ZIP content
                    with open(tmp_file.name, "rb") as f:
                        zip_content = f.read()
                    
                    # Clean up temp file
                    os.unlink(tmp_file.name)
                    
                    # Download ZIP
                    st.download_button(
                        label="📦 Скачать ZIP архив",
                        data=zip_content,
                        file_name=f"melody2score_{job_id}.zip",
                        mime="application/zip",
                        key="zip_download"
                    )
                    
                    st.success("✅ ZIP архив создан успешно")
                    
            except Exception as e:
                st.error(f"❌ Ошибка создания ZIP архива: {e}")
    else:
        st.warning("⚠️ Нет доступных файлов для скачивания")
    
    # Export options
    st.subheader("⚙️ Настройки экспорта")
    
    with st.expander("🔧 Дополнительные форматы"):
        st.markdown("**Поддерживаемые форматы экспорта:**")
        
        formats = {
            "MusicXML": "Стандартный формат для нотных редакторов (MuseScore, Finale, Sibelius)",
            "PDF": "Векторный формат для печати и просмотра",
            "PNG": "Растровый формат для веб-страниц и презентаций",
            "MIDI": "MIDI файл для синтезаторов и DAW",
            "WAV": "Аудиопревью синтезированной мелодии"
        }
        
        for format_name, description in formats.items():
            st.markdown(f"• **{format_name}**: {description}")
        
        st.markdown("**Планируемые форматы:**")
        planned_formats = [
            "SVG - векторная графика для веб",
            "EPS - векторный формат для печати",
            "MP3 - сжатое аудио",
            "FLAC - безпотерьное аудио"
        ]
        
        for format_name in planned_formats:
            st.markdown(f"• {format_name}")
    
    # File information
    st.subheader("📊 Информация о файлах")
    
    if available_files:
        file_info_data = []
        for kind in available_files:
            path = artifact_paths[kind]
            size_mb = os.path.getsize(path) / (1024 * 1024)
            modified_time = datetime.fromtimestamp(os.path.getmtime(path))
            
            file_info_data.append({
                "Формат": kind.upper(),
                "Размер (МБ)": f"{size_mb:.2f}",
                "Изменен": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Путь": os.path.basename(path)
            })
        
        import pandas as pd
        df = pd.DataFrame(file_info_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("📋 Нет доступных файлов")
    
    # Navigation
    st.markdown("---")
    st.markdown("**Навигация:**")
    st.markdown("1. Перейдите на страницу **03_Предпросмотр** для просмотра результатов")
    st.markdown("2. Перейдите на страницу **05_История** для просмотра всех задач")
    
    # Refresh option
    if st.button("🔄 Обновить список файлов"):
        st.rerun()

except Exception as e:
    st.error(f"❌ Ошибка загрузки данных: {e}")
    st.error("Попробуйте обновить страницу или обратитесь к администратору")
