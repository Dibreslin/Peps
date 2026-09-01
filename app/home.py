import streamlit as st
from datetime import datetime

def show():
    st.title("📅 Dashboard")
    st.caption(f"📆 {datetime.now().strftime('%A, %d de %B de %Y')}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Pacientes Activos", "24", delta="+2")
    with col2:
        st.metric("📆 Turnos Hoy", "6", delta="3 confirmados")
    with col3:
        st.metric("💰 Ingresos del Mes", "$ 720.000", delta="+15%")
    with col4:
        st.metric("⏳ Pendientes de Cobro", "$ 120.000", delta="-5%")
    
    st.divider()
    st.subheader("📋 Turnos de Hoy")
    st.info("Aquí se mostrarán los turnos del día")
