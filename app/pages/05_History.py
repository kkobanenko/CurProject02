import streamlit as st
from app.db.repository import session_scope
from app.db.models import Job

st.title("05 · История")

with session_scope() as s:
    jobs = s.query(Job).order_by(Job.created_at.desc()).limit(50).all()

for j in jobs:
    st.write(f"#{j.id} · статус: {j.status} · создано: {j.created_at} · ошибка: {j.error or '—'}")
