import streamlit as st
import pandas as pd
from datetime import date

def show():
    st.title("📆 Gestión de Turnos")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        fecha_selector = st.date_input("📅 Fecha", value=date.today())
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("➕ Nuevo Turno", use_container_width=True, type="primary")
    
    turnos = pd.DataFrame({
        "Hora": ["10:00", "11:00", "14:00", "15:00"],
        "Paciente": ["Juan Pérez", "María Gómez", "Carlos López", "Ana Martínez"],
        "Estado": ["✅ Realizado", "⏳ En espera", "✅ Realizado", "⏳ En espera"]
    })
    st.dataframe(turnos, use_container_width=True, hide_index=True)
