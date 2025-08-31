import streamlit as st
st.title("02 · Настройки (MVP)")
st.caption("Часть настроек зашита в параметры задачи. Расширяется в следующих итерациях.")
st.json({
    "separation": "demucs",
    "f0_backend": "torchcrepe",
    "quant_grid": "1/16",
    "auto_key": True,
    "time_signature": "4/4",
    "tempo": "auto",
})
