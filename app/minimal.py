import streamlit as st

st.set_page_config(page_title="PEP'S - Test", page_icon="🧠")

st.title("🧠 PEP'S - Test de Despliegue")
st.write("✅ Si ves este mensaje, el despliegue funciona correctamente.")

if st.button("Hacé click acá"):
    st.balloons()
    st.success("🚀 ¡Funciona perfectamente!")
