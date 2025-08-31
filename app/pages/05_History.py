import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from app.db.repository import get_uploads, get_jobs_by_upload, get_database_stats, cleanup_old_data

st.set_page_config(page_title="История - Melody→Score", page_icon="📚")

# Page header
st.title("📚 05 · История")
st.markdown("Просмотр истории всех загрузок и задач транскрипции.")

# Database statistics
try:
    stats = get_database_stats()
    
    st.subheader("📊 Статистика базы данных")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Загрузок", stats.get("uploads", 0))
    with col2:
        st.metric("Задач", stats.get("jobs", 0))
    with col3:
        st.metric("Артефактов", stats.get("artifacts", 0))
    with col4:
        st.metric("Логов", stats.get("logs", 0))
    
    # Jobs by status
    if stats.get("jobs_by_status"):
        st.markdown("**Задачи по статусу:**")
        status_cols = st.columns(len(stats["jobs_by_status"]))
        for i, (status, count) in enumerate(stats["jobs_by_status"].items()):
            with status_cols[i]:
                status_icons = {
                    "queued": "🟡",
                    "running": "🟢",
                    "done": "✅",
                    "failed": "❌",
                    "cancelled": "⏹️"
                }
                icon = status_icons.get(status, "❓")
                st.metric(f"{icon} {status.title()}", count)
    
    # Cleanup section
    st.subheader("🧹 Очистка данных")
    
    col1, col2 = st.columns(2)
    with col1:
        days_to_keep = st.slider(
            "Удалить данные старше (дней)",
            min_value=1,
            max_value=30,
            value=7,
            help="Удалить загрузки и задачи старше указанного количества дней"
        )
    
    with col2:
        if st.button("🗑️ Очистить старые данные", type="secondary"):
            with st.spinner("Очистка данных..."):
                try:
                    deleted_counts = cleanup_old_data(days_to_keep)
                    st.success(f"✅ Очистка завершена: {deleted_counts}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Ошибка очистки: {e}")
    
    # Uploads list
    st.subheader("📁 История загрузок")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        limit = st.selectbox(
            "Количество записей",
            [10, 25, 50, 100],
            index=1
        )
    
    with col2:
        show_only_completed = st.checkbox(
            "Только завершенные",
            value=False,
            help="Показать только загрузки с завершенными задачами"
        )
    
    with col3:
        if st.button("🔄 Обновить список"):
            st.rerun()
    
    # Get uploads
    uploads = get_uploads(limit=limit)
    
    if not uploads:
        st.info("📋 Нет загрузок в истории")
        st.stop()
    
    # Create uploads dataframe
    uploads_data = []
    for upload in uploads:
        # Get jobs for this upload
        jobs = get_jobs_by_upload(upload.id)
        
        # Filter by completion status if requested
        if show_only_completed:
            if not any(job.status == "done" for job in jobs):
                continue
        
        # Get latest job
        latest_job = jobs[0] if jobs else None
        
        uploads_data.append({
            "ID": upload.id,
            "Файл": upload.filename,
            "Размер (МБ)": f"{upload.size_bytes / (1024*1024):.1f}",
            "Длительность (сек)": upload.duration_sec,
            "Загружен": upload.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "Задач": len(jobs),
            "Последний статус": latest_job.status if latest_job else "Нет",
            "Последний прогресс": f"{latest_job.progress}%" if latest_job else "N/A"
        })
    
    if uploads_data:
        df = pd.DataFrame(uploads_data)
        st.dataframe(df, use_container_width=True)
        
        # Upload details
        st.subheader("📋 Детали загрузки")
        
        selected_upload_id = st.selectbox(
            "Выберите загрузку для просмотра деталей",
            options=[row["ID"] for row in uploads_data],
            format_func=lambda x: f"ID {x} - {next(row['Файл'] for row in uploads_data if row['ID'] == x)}"
        )
        
        if selected_upload_id:
            # Get upload details
            selected_upload = next(u for u in uploads if u.id == selected_upload_id)
            selected_jobs = get_jobs_by_upload(selected_upload_id)
            
            # Upload info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Информация о файле:**")
                st.write(f"**Имя:** {selected_upload.filename}")
                st.write(f"**Размер:** {selected_upload.size_bytes / (1024*1024):.1f} МБ")
                st.write(f"**Формат:** {selected_upload.ext}")
            with col2:
                st.markdown("**Аудио параметры:**")
                st.write(f"**Частота:** {selected_upload.sr} Гц")
                st.write(f"**Длительность:** {selected_upload.duration_sec} сек")
                st.write(f"**Путь:** {selected_upload.path}")
            with col3:
                st.markdown("**Метаданные:**")
                st.write(f"**ID:** {selected_upload.id}")
                st.write(f"**Загружен:** {selected_upload.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**Задач:** {len(selected_jobs)}")
            
            # Jobs for this upload
            if selected_jobs:
                st.markdown("**Задачи для этой загрузки:**")
                
                jobs_data = []
                for job in selected_jobs:
                    jobs_data.append({
                        "ID задачи": job.id,
                        "Статус": job.status,
                        "Прогресс": f"{job.progress}%",
                        "Создана": job.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "Завершена": job.finished_at.strftime("%Y-%m-%d %H:%M:%S") if job.finished_at else "N/A",
                        "Ошибка": job.error[:50] + "..." if job.error and len(job.error) > 50 else job.error or "N/A"
                    })
                
                jobs_df = pd.DataFrame(jobs_data)
                st.dataframe(jobs_df, use_container_width=True)
                
                # Job actions
                if selected_jobs:
                    latest_job = selected_jobs[0]  # Most recent
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if latest_job.status == "done":
                            st.success("✅ Последняя задача завершена успешно")
                            if st.button("👁️ Просмотреть результаты", key="view_results"):
                                st.session_state["last_job_id"] = latest_job.id
                                st.success("✅ Перейдите на страницу **03_Предпросмотр** для просмотра результатов")
                        elif latest_job.status == "failed":
                            st.error("❌ Последняя задача завершилась с ошибкой")
                            if st.button("🔄 Повторить задачу", key="retry_job"):
                                from app.tasks.utils import retry_failed_job
                                if retry_failed_job(latest_job.id):
                                    st.success("✅ Задача отправлена на повторное выполнение")
                                    st.rerun()
                                else:
                                    st.error("❌ Не удалось повторить задачу")
                        else:
                            st.info(f"ℹ️ Последняя задача: {latest_job.status}")
                    
                    with col2:
                        if st.button("🗑️ Удалить загрузку", key="delete_upload", type="secondary"):
                            from app.db.repository import delete_upload
                            if delete_upload(selected_upload_id):
                                st.success("✅ Загрузка удалена")
                                st.rerun()
                            else:
                                st.error("❌ Не удалось удалить загрузку")
            else:
                st.info("📋 Нет задач для этой загрузки")
    else:
        st.info("📋 Нет загрузок, соответствующих фильтрам")
    
    # Navigation
    st.markdown("---")
    st.markdown("**Навигация:**")
    st.markdown("1. Перейдите на страницу **01_Загрузка** для создания новой задачи")
    st.markdown("2. Перейдите на страницу **02_Настройки** для мониторинга активных задач")

except Exception as e:
    st.error(f"❌ Ошибка загрузки данных: {e}")
    st.error("Попробуйте обновить страницу или обратитесь к администратору")
