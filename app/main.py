import streamlit as st
import pandas as pd
from datetime import datetime, date

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="PEP'S - Gestión de Consultorios",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# INICIALIZACIÓN DEL ESTADO DE SESIÓN
# ============================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# ============================================
# FUNCIONES DE LOGIN
# ============================================
def do_login(email, password):
    if email and password:
        st.session_state.authenticated = True
        st.session_state.user = email
        st.session_state.user_name = email.split("@")[0].capitalize()
        return True
    return False

def do_logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.user_name = ""
    st.rerun()

# ============================================
# PÁGINA DE LOGIN
# ============================================
if not st.session_state.authenticated:
    st.title("🧠 PEP'S - Sistema de Gestión para Consultorios")
    st.subheader("Iniciar Sesión")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### 🔐 Acceso al Sistema")
            
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("📧 Email", placeholder="marina@peps.com")
                password = st.text_input("🔑 Contraseña", type="password", placeholder="••••••••")
                
                submit = st.form_submit_button("🚀 Ingresar", use_container_width=True, type="primary")
                
                if submit:
                    if do_login(email, password):
                        st.success("✅ Sesión iniciada correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Completá todos los campos")
            
            st.divider()
            st.caption("📝 Datos de prueba: cualquier email/contraseña")
    
    st.stop()

# ============================================
# MENÚ PRINCIPAL (usuario autenticado)
# ============================================

# Barra lateral
st.sidebar.title("🧠 PEP'S")
st.sidebar.divider()
st.sidebar.write(f"👋 **{st.session_state.user_name}**")
st.sidebar.caption(f"📧 {st.session_state.user}")
st.sidebar.divider()

# Menú de navegación
menu = st.sidebar.radio(
    "📋 Navegación",
    ["📅 Dashboard", "👤 Pacientes", "📆 Turnos", "💰 Pagos"],
    index=0
)

# Botón de logout
st.sidebar.divider()
if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
    do_logout()

# ============================================
# SECCIÓN: DASHBOARD
# ============================================
if menu == "📅 Dashboard":
    st.title("📅 Dashboard")
    st.caption(f"📆 {datetime.now().strftime('%A, %d de %B de %Y')}")
    
    # Métricas principales
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
    
    # Turnos del día
    st.subheader("📋 Turnos de Hoy")
    
    turnos_hoy = pd.DataFrame({
        "Hora": ["10:00", "11:00", "14:00", "15:00", "16:00", "18:00"],
        "Paciente": ["Juan Pérez", "María Gómez", "Carlos López", "Ana Martínez", "Luis Fernández", "Sofía Torres"],
        "Estado": ["✅ Realizado", "✅ Realizado", "⏳ En espera", "⏳ En espera", "❌ Cancelado", "⏳ En espera"],
        "Pago": ["Pagado", "Pagado", "Pendiente", "Pagado", "Cancelado", "Pendiente"]
    })
    st.dataframe(turnos_hoy, use_container_width=True, hide_index=True)

# ============================================
# SECCIÓN: PACIENTES
# ============================================
elif menu == "👤 Pacientes":
    st.title("👤 Gestión de Pacientes")
    
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Pacientes", "➕ Nuevo Paciente", "🔍 Buscar"])
    
    with tab1:
        pacientes = pd.DataFrame({
            "DNI": ["12.345.678", "23.456.789", "34.567.890", "45.678.901"],
            "Nombre": ["Juan Pérez", "María Gómez", "Carlos López", "Ana Martínez"],
            "Teléfono": ["011-1234-5678", "011-2345-6789", "011-3456-7890", "011-4567-8901"],
            "Email": ["juan@mail.com", "maria@mail.com", "carlos@mail.com", "ana@mail.com"],
            "Última Sesión": ["25/08/2026", "20/08/2026", "28/08/2026", "22/08/2026"],
            "Estado": ["Activo", "Activo", "Activo", "Activo"]
        })
        st.dataframe(pacientes, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("👥 Total: 24 pacientes activos")
        with col2:
            st.warning("⏳ 3 pacientes con deuda pendiente")
    
    with tab2:
        with st.form("nuevo_paciente"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre")
                apellido = st.text_input("Apellido")
                tipo_doc = st.selectbox("Tipo de Documento", ["DNI", "LC", "LE", "Pasaporte"])
                nro_doc = st.text_input("Número de Documento")
                fecha_nac = st.date_input("Fecha de Nacimiento")
            with col2:
                telefono = st.text_input("Teléfono")
                email = st.text_input("Email")
                direccion = st.text_area("Dirección", height=68)
                observaciones = st.text_area("Observaciones", height=68)
            
            if st.form_submit_button("💾 Guardar Paciente"):
                st.success("✅ Paciente registrado correctamente")
    
    with tab3:
        busqueda = st.text_input("🔍 Buscar por nombre, DNI o teléfono")
        if busqueda:
            st.info(f"Resultados para: {busqueda}")
            st.dataframe(pd.DataFrame({
                "Nombre": ["Juan Pérez"],
                "DNI": ["12.345.678"],
                "Teléfono": ["011-1234-5678"]
            }), hide_index=True)

# ============================================
# SECCIÓN: TURNOS
# ============================================
elif menu == "📆 Turnos":
    st.title("📆 Gestión de Turnos")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        fecha_selector = st.date_input("📅 Fecha", value=date.today())
    with col2:
        profesional = st.selectbox("👤 Profesional", ["Todos", "Marina Breslin", "Carlos Gómez"])
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("➕ Nuevo Turno", use_container_width=True, type="primary")
    with col2:
        st.button("📋 Ver Agenda", use_container_width=True)
    with col3:
        st.button("📤 Exportar", use_container_width=True)
    
    # Mostrar turnos
    turnos = pd.DataFrame({
        "Hora": ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"],
        "Paciente": ["Ana Martínez", "Juan Pérez", "María Gómez", "-", "Carlos López", "-", "Sofía Torres", "-"],
        "Estado": ["Confirmado", "Realizado", "Pendiente", "Libre", "Confirmado", "Libre", "Cancelado", "Libre"],
        "Espacio": ["Individual", "Individual", "Pareja", "-", "Individual", "-", "Familiar", "-"]
    })
    st.dataframe(turnos, use_container_width=True, hide_index=True)

# ============================================
# SECCIÓN: PAGOS
# ============================================
else:
    st.title("💰 Gestión de Pagos")
    
    tab1, tab2 = st.tabs(["📋 Pagos Registrados", "➕ Nuevo Pago"])
    
    with tab1:
        pagos = pd.DataFrame({
            "Fecha": ["26/08/2026", "25/08/2026", "24/08/2026"],
            "Paciente": ["Juan Pérez", "María Gómez", "Carlos López"],
            "Monto": ["$30.000", "$30.000", "$60.000"],
            "Método": ["Transferencia", "Efectivo", "Mercado Pago"],
            "Estado": ["Confirmado", "Confirmado", "Pendiente"]
        })
        st.dataframe(pagos, use_container_width=True, hide_index=True)
        
        st.metric("💰 Total Cobrado Este Mes", "$ 720.000")
    
    with tab2:
        with st.form("nuevo_pago"):
            col1, col2 = st.columns(2)
            with col1:
                paciente = st.selectbox("Paciente", ["Juan Pérez", "María Gómez", "Carlos López"])
                monto = st.number_input("Monto", min_value=0, value=30000)
                metodo = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Mercado Pago", "Western Union"])
            with col2:
                fecha_pago = st.date_input("Fecha de Pago", value=date.today())
                sesiones = st.multiselect("Sesiones a aplicar", ["Sesión 45", "Sesión 46", "Sesión 47", "Sesión 48"])
                observaciones = st.text_area("Observaciones")
            
            if st.form_submit_button("💾 Registrar Pago"):
                st.success("✅ Pago registrado correctamente")

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption("🧠 PEP'S - Sistema de Gestión para Consultorios v1.0")
st.caption("© 2026 - Desarrollado para Consultorio de Marina Breslin")
