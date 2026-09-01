import streamlit as st

# Importar páginas
from app import home, pacientes, turnos, pagos

# Configuración
st.set_page_config(
    page_title="PEP'S - Gestión de Consultorios",
    page_icon="🧠",
    layout="wide"
)

# Estado de sesión
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None

# ============================================
# LOGIN
# ============================================
if not st.session_state.authenticated:
    st.title("🧠 PEP'S - Sistema de Gestión")
    st.subheader("Iniciar Sesión")
    
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        
        if st.form_submit_button("Ingresar"):
            if email and password:
                st.session_state.authenticated = True
                st.session_state.user = email
                st.rerun()
            else:
                st.error("Completá todos los campos")
    
    st.caption("📝 Datos de prueba: cualquier email/contraseña")
    st.stop()

# ============================================
# MENÚ PRINCIPAL
# ============================================
st.sidebar.title("🧠 PEP'S")
st.sidebar.write(f"👋 {st.session_state.user}")

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()

menu = st.sidebar.radio(
    "Menú",
    ["📅 Dashboard", "👤 Pacientes", "📆 Turnos", "💰 Pagos"]
)

# Navegación
if menu == "📅 Dashboard":
    home.show()
elif menu == "👤 Pacientes":
    pacientes.show()
elif menu == "📆 Turnos":
    turnos.show()
elif menu == "💰 Pagos":
    pagos.show()
