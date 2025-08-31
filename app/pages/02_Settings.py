import streamlit as st
import json
from datetime import datetime
from app.db.repository import get_job, get_upload, update_job_status
from app.tasks.utils import get_job_progress, cancel_job, retry_failed_job

st.set_page_config(page_title="Настройки - Melody→Score", page_icon="⚙️")

# Page header
st.title("⚙️ 02 · Настройки и мониторинг")
st.markdown("Управление задачами и настройка параметров обработки.")

# Check if we have a job from previous page
if "last_job_id" not in st.session_state:
    st.warning("⚠️ Нет активной задачи. Перейдите на страницу **01_Загрузка** для создания задачи.")
    st.stop()

job_id = st.session_state["last_job_id"]

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
    
    # Job status and progress
    st.subheader("📊 Статус задачи")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("ID задачи", job_id)
    with col2:
        status_color = {
            "queued": "🟡",
            "running": "🟢", 
            "done": "✅",
            "failed": "❌",
            "cancelled": "⏹️"
        }.get(job.status, "❓")
        st.metric("Статус", f"{status_color} {job.status}")
    with col3:
        st.metric("Прогресс", f"{job.progress}%")
    with col4:
        if job.created_at:
            st.metric("Создана", job.created_at.strftime("%H:%M:%S"))
    
    # Progress bar
    st.progress(job.progress / 100)
    
    # Job details
    with st.expander("📋 Детали задачи", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Файл:**")
            st.code(f"Имя: {upload.filename}")
            st.code(f"Размер: {upload.size_bytes / (1024*1024):.1f} МБ")
            st.code(f"Длительность: {upload.duration_sec} сек")
            st.code(f"Частота: {upload.sr} Гц")
        
        with col2:
            st.markdown("**Параметры:**")
            params = job.params_json
            st.json(params)
    
    # Job actions
    st.subheader("🎛️ Действия")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if job.status in ["queued", "running"]:
            if st.button("⏹️ Отменить задачу", type="secondary"):
                if cancel_job(job_id):
                    st.success("✅ Задача отменена")
                    st.rerun()
                else:
                    st.error("❌ Не удалось отменить задачу")
        else:
            st.button("⏹️ Отменить задачу", disabled=True)
    
    with col2:
        if job.status == "failed":
            if st.button("🔄 Повторить задачу", type="secondary"):
                if retry_failed_job(job_id):
                    st.success("✅ Задача отправлена на повторное выполнение")
                    st.rerun()
                else:
                    st.error("❌ Не удалось повторить задачу")
        else:
            st.button("🔄 Повторить задачу", disabled=True)
    
    with col3:
        if st.button("🔄 Обновить статус", type="secondary"):
            st.rerun()
    
    # Error information
    if job.status == "failed" and job.error:
        st.error("❌ Ошибка выполнения:")
        st.code(job.error)
    
    # Parameter modification (for queued jobs)
    if job.status == "queued":
        st.subheader("🔧 Изменение параметров")
        st.info("💡 Вы можете изменить параметры задачи, пока она в очереди")
        
        with st.form("modify_params"):
            st.markdown("**Новые параметры:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_separation = st.selectbox(
                    "Разделение источников",
                    ["none", "demucs", "spleeter"],
                    index=["none", "demucs", "spleeter"].index(params.get("separation", "demucs")),
                    format_func=lambda x: {
                        "none": "Без разделения",
                        "demucs": "Demucs",
                        "spleeter": "Spleeter"
                    }[x]
                )
                
                new_f0_backend = st.selectbox(
                    "Метод F0",
                    ["torchcrepe", "pyin"],
                    index=["torchcrepe", "pyin"].index(params.get("f0_backend", "torchcrepe")),
                    format_func=lambda x: {
                        "torchcrepe": "Torchcrepe",
                        "pyin": "pYIN"
                    }[x]
                )
            
            with col2:
                new_quantization_grid = st.selectbox(
                    "Сетка квантования",
                    [0.25, 0.125, 0.5, 1.0],
                    index=[0.25, 0.125, 0.5, 1.0].index(params.get("quantization_grid", 0.25)),
                    format_func=lambda x: f"{x} (1/{int(1/x)})"
                )
                
                new_time_signature = st.selectbox(
                    "Размер",
                    ["4/4", "3/4", "2/4", "6/8", "3/8", "2/2"],
                    index=["4/4", "3/4", "2/4", "6/8", "3/8", "2/2"].index(params.get("time_signature", "4/4"))
                )
            
            submitted = st.form_submit_button("💾 Сохранить изменения")
            
            if submitted:
                # Update parameters
                new_params = params.copy()
                new_params.update({
                    "separation": new_separation,
                    "f0_backend": new_f0_backend,
                    "quantization_grid": new_quantization_grid,
                    "time_signature": new_time_signature
                })
                
                # Update job
                update_job_status(job_id, params_json=new_params)
                st.success("✅ Параметры обновлены")
                st.rerun()
    
    # Navigation
    st.markdown("---")
    st.markdown("**Навигация:**")
    
    if job.status == "done":
        st.success("✅ Задача завершена! Перейдите на страницу **03_Предпросмотр** для просмотра результатов")
    elif job.status == "failed":
        st.error("❌ Задача завершилась с ошибкой. Проверьте параметры и попробуйте повторить")
    elif job.status == "running":
        st.info("🔄 Задача выполняется. Обновите страницу для проверки прогресса")
    else:
        st.info("⏳ Задача в очереди. Ожидайте начала выполнения")
    
    # Auto-refresh for running jobs
    if job.status == "running":
        st.markdown("🔄 Автообновление каждые 5 секунд...")
        time.sleep(5)
        st.rerun()

except Exception as e:
    st.error(f"❌ Ошибка загрузки информации о задаче: {e}")
    st.error("Попробуйте обновить страницу или обратитесь к администратору")
