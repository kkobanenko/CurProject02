"""
Reusable UI components for Streamlit pages.
"""
from __future__ import annotations
import streamlit as st
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

def show_audio_waveform(audio_data: np.ndarray, sample_rate: int, title: str = "Waveform") -> None:
    """Display audio waveform using Plotly."""
    if len(audio_data) == 0:
        st.warning("No audio data to display")
        return
    
    # Downsample for performance
    downsample_factor = max(1, len(audio_data) // 10000)
    y = audio_data[::downsample_factor]
    x = np.arange(len(y)) * downsample_factor / sample_rate
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        name='Waveform',
        line=dict(color='#1f77b4', width=1)
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Time (seconds)",
        yaxis_title="Amplitude",
        height=200,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

def show_job_status_card(job_data: Dict[str, Any]) -> None:
    """Display job status in a card format."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("ID", job_data.get("job_id", "N/A"))
    with col2:
        status = job_data.get("status", "unknown")
        status_icons = {
            "queued": "🟡",
            "running": "🟢",
            "done": "✅",
            "failed": "❌",
            "cancelled": "⏹️"
        }
        icon = status_icons.get(status, "❓")
        st.metric("Status", f"{icon} {status}")
    with col3:
        progress = job_data.get("progress", 0)
        st.metric("Progress", f"{progress}%")
    with col4:
        created_at = job_data.get("created_at", "N/A")
        st.metric("Created", created_at)

def show_progress_bar(progress: int, status: str) -> None:
    """Display progress bar with status."""
    st.progress(progress / 100)
    st.caption(f"Status: {status}")

def show_error_message(error: str) -> None:
    """Display error message in a consistent format."""
    st.error(f"❌ {error}")

def show_success_message(message: str) -> None:
    """Display success message in a consistent format."""
    st.success(f"✅ {message}")

def show_info_message(message: str) -> None:
    """Display info message in a consistent format."""
    st.info(f"ℹ️ {message}")

def show_warning_message(message: str) -> None:
    """Display warning message in a consistent format."""
    st.warning(f"⚠️ {message}")

def create_download_button(label: str, data: Any, file_name: str, mime_type: str) -> None:
    """Create a download button with consistent styling."""
    st.download_button(
        label=label,
        data=data,
        file_name=file_name,
        mime=mime_type,
        use_container_width=True
    )

def show_file_info(file_info: Dict[str, Any]) -> None:
    """Display file information in a structured format."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Size", f"{file_info.get('size_mb', 0):.1f} MB")
    with col2:
        st.metric("Duration", f"{file_info.get('duration_sec', 0):.1f} sec")
    with col3:
        st.metric("Sample Rate", f"{file_info.get('sample_rate', 0)} Hz")

def show_navigation_hint() -> None:
    """Show navigation hints for users."""
    st.markdown("---")
    st.markdown("**Навигация:**")
    st.markdown("1. **01_Upload** - Загрузка аудиофайлов")
    st.markdown("2. **02_Settings** - Настройки и мониторинг")
    st.markdown("3. **03_Preview** - Предпросмотр результатов")
    st.markdown("4. **04_Export** - Скачивание файлов")
    st.markdown("5. **05_History** - История задач")
