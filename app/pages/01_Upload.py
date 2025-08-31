import os
import streamlit as st
import time
from datetime import datetime
import plotly.graph_objects as go
import numpy as np
from app.settings import settings
from app.db.repository import create_upload
from app.tasks.utils import submit_transcription_job
from app.audio.io import get_audio_info, validate_audio

st.set_page_config(page_title="Загрузка - Melody→Score", page_icon="🎼")

# Page header
st.title("🎼 01 · Загрузка аудио")
st.markdown("Загрузите аудиофайл для извлечения мелодии и создания нотной записи.")

# File uploader
uploaded_file = st.file_uploader(
    "Выберите аудиофайл",
    type=["mp3", "wav", "flac", "m4a", "ogg"],
    help="Поддерживаемые форматы: MP3, WAV, FLAC, M4A, OGG. Максимум 5 минут, 100 МБ"
)

if not uploaded_file:
    st.info("👆 Выберите аудиофайл для начала работы")
    st.stop()

# File validation and info
try:
    # Save uploaded file
    os.makedirs(settings.storage_dir, exist_ok=True)
    file_path = os.path.join(settings.storage_dir, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Get file info
    file_info = get_audio_info(file_path)
    
    # Validate file
    try:
        validate_audio(file_path, settings.max_duration_sec, settings.max_file_mb)
        st.success("✅ Файл прошел валидацию")
    except Exception as e:
        st.error(f"❌ Ошибка валидации: {e}")
        st.stop()
    
    # Display file info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Размер", f"{file_info['size_mb']:.1f} МБ")
    with col2:
        st.metric("Длительность", f"{file_info['duration_sec']:.1f} сек")
    with col3:
        st.metric("Частота", f"{file_info['sample_rate']} Гц")
    
    # Audio player
    st.subheader("🎵 Прослушивание")
    st.audio(file_path, format=f"audio/{file_info['extension']}")
    
    # Waveform visualization
    try:
        import librosa
        y, sr = librosa.load(file_path, sr=None, duration=30)  # Load first 30 seconds
        
        # Create waveform plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=y[::100],  # Downsample for performance
            mode='lines',
            name='Waveform',
            line=dict(color='#1f77b4', width=1)
        ))
        fig.update_layout(
            title="Волновая форма (первые 30 секунд)",
            xaxis_title="Время (сэмплы)",
            yaxis_title="Амплитуда",
            height=200,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.warning(f"Не удалось создать визуализацию: {e}")
    
    # Processing parameters
    st.subheader("⚙️ Параметры обработки")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Разделение источников**")
        separation = st.selectbox(
            "Метод разделения",
            ["none", "demucs", "spleeter"],
            format_func=lambda x: {
                "none": "Без разделения",
                "demucs": "Demucs (рекомендуется)",
                "spleeter": "Spleeter"
            }[x],
            help="Разделение вокала и аккомпанемента"
        )
        
        st.markdown("**Предобработка**")
        highpass = st.checkbox("Высокочастотный фильтр", value=True, help="Удаление низкочастотного шума")
        denoise = st.checkbox("Шумоподавление", value=True, help="Спектральное шумоподавление")
        trim = st.checkbox("Обрезка тишины", value=True, help="Удаление тишины в начале и конце")
        normalize = st.checkbox("Нормализация", value=True, help="Нормализация громкости")
    
    with col2:
        st.markdown("**Анализ частоты**")
        f0_backend = st.selectbox(
            "Метод F0",
            ["torchcrepe", "pyin"],
            format_func=lambda x: {
                "torchcrepe": "Torchcrepe (рекомендуется)",
                "pyin": "pYIN"
            }[x],
            help="Метод извлечения основной частоты"
        )
        
        st.markdown("**Квантование**")
        quantization_grid = st.selectbox(
            "Сетка квантования",
            [0.25, 0.125, 0.5, 1.0],
            format_func=lambda x: f"{x} (1/{int(1/x)})",
            help="Размер сетки для квантования ритма"
        )
        
        min_note_duration = st.selectbox(
            "Мин. длительность ноты",
            [0.125, 0.25, 0.5, 1.0],
            format_func=lambda x: f"{x} (1/{int(1/x)})",
            help="Минимальная длительность ноты"
        )
    
    # Advanced settings
    with st.expander("🔧 Дополнительные настройки"):
        col1, col2 = st.columns(2)
        
        with col1:
            auto_key = st.checkbox("Автоопределение тональности", value=True)
            if not auto_key:
                key_signature = st.selectbox(
                    "Тональность",
                    ["C", "G", "D", "A", "E", "B", "F#", "C#", "F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"],
                    help="Тональность произведения"
                )
            else:
                key_signature = "C"
            
            time_signature = st.selectbox(
                "Размер",
                ["4/4", "3/4", "2/4", "6/8", "3/8", "2/2"],
                help="Музыкальный размер"
            )
        
        with col2:
            tempo_qpm = st.number_input(
                "Темп (BPM)",
                min_value=40.0,
                max_value=200.0,
                value=120.0,
                step=5.0,
                help="Темп в ударах в минуту (0 = автоопределение)"
            )
            
            synthesis_type = st.selectbox(
                "Тип синтеза",
                ["sine", "piano"],
                format_func=lambda x: {
                    "sine": "Синусоида",
                    "piano": "Пиано"
                }[x],
                help="Тип синтеза для аудиопревью"
            )
    
    # Submit button
    st.subheader("🚀 Запуск обработки")
    
    if st.button("🎵 Начать транскрипцию", type="primary", use_container_width=True):
        with st.spinner("Создание задачи..."):
            try:
                # Create upload record
                upload = create_upload(
                    filename=uploaded_file.name,
                    ext=file_info['extension'],
                    sr=file_info['sample_rate'],
                    duration_sec=int(file_info['duration_sec']),
                    size_bytes=file_info['size_mb'] * 1024 * 1024,
                    path=file_path
                )
                
                # Prepare parameters
                params = {
                    "separation": separation,
                    "highpass": highpass,
                    "denoise": denoise,
                    "trim": trim,
                    "normalize": normalize,
                    "f0_backend": f0_backend,
                    "quantization_grid": quantization_grid,
                    "min_note_duration": min_note_duration,
                    "auto_key": auto_key,
                    "key_signature": key_signature if not auto_key else "C",
                    "time_signature": time_signature,
                    "tempo_qpm": tempo_qpm if tempo_qpm > 0 else None,
                    "synthesis_type": synthesis_type,
                    "title": f"Extracted from {uploaded_file.name}"
                }
                
                # Submit job
                result = submit_transcription_job(upload.id, file_path, params)
                
                # Success message
                st.success(f"✅ Задача создана! ID: {result['job_id']}")
                st.info(f"📋 Статус: {result['status']}")
                
                # Store job ID in session state
                st.session_state["last_job_id"] = result['job_id']
                st.session_state["last_upload_id"] = upload.id
                
                # Navigation hint
                st.markdown("---")
                st.markdown("**Следующие шаги:**")
                st.markdown("1. Перейдите на страницу **02_Настройки** для дополнительной настройки")
                st.markdown("2. Перейдите на страницу **03_Предпросмотр** для просмотра результатов")
                
            except Exception as e:
                st.error(f"❌ Ошибка создания задачи: {e}")
                st.error("Попробуйте еще раз или обратитесь к администратору")

except Exception as e:
    st.error(f"❌ Ошибка обработки файла: {e}")
    st.error("Проверьте формат файла и попробуйте еще раз")
