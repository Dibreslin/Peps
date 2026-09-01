import streamlit as st
import pandas as pd
from datetime import date

def show():
    st.title("💰 Gestión de Pagos")
    
    tab1, tab2 = st.tabs(["📋 Pagos Registrados", "➕ Nuevo Pago"])
    
    with tab1:
        pagos = pd.DataFrame({
            "Fecha": ["26/08/2026", "25/08/2026", "24/08/2026"],
            "Paciente": ["Juan Pérez", "María Gómez", "Carlos López"],
            "Monto": ["$30.000", "$30.000", "$60.000"],
            "Estado": ["Confirmado", "Confirmado", "Pendiente"]
        })
        st.dataframe(pagos, use_container_width=True, hide_index=True)
        st.metric("💰 Total Cobrado Este Mes", "$ 720.000")
    
    with tab2:
        with st.form("nuevo_pago"):
            paciente = st.selectbox("Paciente", ["Juan Pérez", "María Gómez", "Carlos López"])
            monto = st.number_input("Monto", min_value=0, value=30000)
            metodo = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Mercado Pago"])
            
            if st.form_submit_button("💾 Registrar Pago"):
                st.success("✅ Pago registrado correctamente")
