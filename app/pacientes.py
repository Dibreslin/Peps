import streamlit as st
import pandas as pd

def show():
    st.title("👤 Gestión de Pacientes")
    
    tab1, tab2 = st.tabs(["📋 Lista de Pacientes", "➕ Nuevo Paciente"])
    
    with tab1:
        pacientes = pd.DataFrame({
            "DNI": ["12.345.678", "23.456.789", "34.567.890"],
            "Nombre": ["Juan Pérez", "María Gómez", "Carlos López"],
            "Teléfono": ["011-1234-5678", "011-2345-6789", "011-3456-7890"],
            "Estado": ["Activo", "Activo", "Activo"]
        })
        st.dataframe(pacientes, use_container_width=True, hide_index=True)
    
    with tab2:
        with st.form("nuevo_paciente"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre")
                apellido = st.text_input("Apellido")
                tipo_doc = st.selectbox("Tipo de Documento", ["DNI", "LC", "LE", "Pasaporte"])
                nro_doc = st.text_input("Número de Documento")
            with col2:
                telefono = st.text_input("Teléfono")
                email = st.text_input("Email")
                fecha_nac = st.date_input("Fecha de Nacimiento")
            
            if st.form_submit_button("💾 Guardar Paciente"):
                st.success("✅ Paciente registrado correctamente")
