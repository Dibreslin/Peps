import streamlit as st
import pandas as pd
from datetime import datetime, date
from app.supabase_client import get_supabase

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(
    page_title="PEP'S - Gestión de Consultorios",
    page_icon="🧠",
    layout="wide"
)

# ============================================
# INICIALIZACIÓN
# ============================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# Conectar a Supabase
supabase = get_supabase()

# ============================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================
def do_login(email, password):
    """Login usando Supabase Auth"""
    if not supabase:
        st.error("❌ No hay conexión con Supabase")
        return False
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            st.session_state.authenticated = True
            st.session_state.user = email
            st.session_state.user_name = response.user.user_metadata.get("nombre", email.split("@")[0].capitalize())
            return True
    except Exception as e:
        st.error(f"❌ Error de login: {str(e)}")
        return False
    
    return False

def do_logout():
    if supabase:
        supabase.auth.sign_out()
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.user_name = ""
    st.rerun()

# ============================================
# FUNCIONES PARA OBTENER DATOS
# ============================================
def get_pacientes():
    """Obtener lista de pacientes"""
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table("pacientes").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error obteniendo pacientes: {str(e)}")
        return pd.DataFrame()

def get_turnos_hoy():
    """Obtener turnos de hoy"""
    if not supabase:
        return pd.DataFrame()
    
    try:
        hoy = date.today().isoformat()
        response = supabase.table("turnos")\
            .select("*, pacientes(nombre, apellido)")\
            .eq("fecha", hoy)\
            .execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # Formatear nombres
            df["paciente_nombre"] = df["pacientes"].apply(
                lambda x: f"{x['nombre']} {x['apellido']}" if x else "Sin asignar"
            )
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error obteniendo turnos: {str(e)}")
        return pd.DataFrame()

# ============================================
# LOGIN
# ============================================
if not st.session_state.authenticated:
    st.title("🧠 PEP'S - Sistema de Gestión")
    st.subheader("Iniciar Sesión")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### 🔐 Acceso al Sistema")
            
            with st.form("login_form"):
                email = st.text_input("📧 Email", placeholder="marina@peps.com")
                password = st.text_input("🔑 Contraseña", type="password", placeholder="••••••••")
                
                if st.form_submit_button("🚀 Ingresar", use_container_width=True, type="primary"):
                    if do_login(email, password):
                        st.success("✅ Sesión iniciada")
                        st.rerun()
            
            st.divider()
            st.caption("📝 Usuario de prueba: marina@peps.com")
            st.caption("🔑 Contraseña: configurada en Supabase Auth")
    
    st.stop()

# ============================================
# MENÚ PRINCIPAL
# ============================================
st.sidebar.title("🧠 PEP'S")
st.sidebar.divider()
st.sidebar.write(f"👋 **{st.session_state.user_name}**")
st.sidebar.caption(f"📧 {st.session_state.user}")
st.sidebar.divider()

if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    do_logout()

menu = st.sidebar.radio(
    "📋 Navegación",
    ["📅 Dashboard", "👤 Pacientes", "📆 Turnos", "💰 Pagos", "🏥 Obras Sociales"],
    index=0
)

# ============================================
# DASHBOARD
# ============================================
if menu == "📅 Dashboard":
    st.title("📅 Dashboard")
    st.caption(f"📆 {datetime.now().strftime('%A, %d de %B de %Y')}")
    
    # Obtener datos reales
    pacientes_df = get_pacientes()
    turnos_df = get_turnos_hoy()
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Pacientes", len(pacientes_df) if not pacientes_df.empty else 0)
    with col2:
        st.metric("📆 Turnos Hoy", len(turnos_df) if not turnos_df.empty else 0)
    with col3:
        st.metric("💰 Ingresos del Mes", "$ 720.000", delta="+15%")
    with col4:
        st.metric("⏳ Pendientes", "$ 120.000")
    
    st.divider()
    
    # Turnos de hoy
    st.subheader("📋 Turnos de Hoy")
    if not turnos_df.empty:
        # Mostrar solo las columnas relevantes
        columnas = ["hora_inicio", "paciente_nombre", "estado"]
        st.dataframe(turnos_df[columnas], use_container_width=True, hide_index=True)
    else:
        st.info("No hay turnos para hoy")

# ============================================
# PACIENTES
# ============================================
elif menu == "👤 Pacientes":
    st.title("👤 Gestión de Pacientes")
    
    tab1, tab2 = st.tabs(["📋 Lista de Pacientes", "➕ Nuevo Paciente"])
    
    with tab1:
        df = get_pacientes()
        if not df.empty:
            columnas = ["nombre", "apellido", "tipo_documento", "nro_documento", "telefono", "email"]
            st.dataframe(df[columnas], use_container_width=True, hide_index=True)
        else:
            st.info("No hay pacientes registrados")
    
    with tab2:
        with st.form("nuevo_paciente"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre *")
                apellido = st.text_input("Apellido *")
                tipo_doc = st.selectbox("Tipo de Documento", ["DNI", "LC", "LE", "Pasaporte", "CI"])
                nro_doc = st.text_input("Número de Documento *")
            with col2:
                telefono = st.text_input("Teléfono")
                email = st.text_input("Email")
                fecha_nac = st.date_input("Fecha de Nacimiento")
            
            if st.form_submit_button("💾 Guardar Paciente"):
                if nombre and apellido and nro_doc:
                    try:
                        data = {
                            "nombre": nombre,
                            "apellido": apellido,
                            "tipo_documento": tipo_doc,
                            "nro_documento": nro_doc,
                            "telefono": telefono,
                            "email": email,
                            "fecha_nacimiento": fecha_nac.isoformat() if fecha_nac else None
                        }
                        response = supabase.table("pacientes").insert(data).execute()
                        st.success("✅ Paciente guardado correctamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Completá los campos obligatorios (*)")

# ============================================
# TURNOS
# ============================================
elif menu == "📆 Turnos":
    st.title("📆 Gestión de Turnos")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        fecha_selector = st.date_input("📅 Fecha", value=date.today())
    
    # Obtener pacientes para el select
    pacientes_df = get_pacientes()
    
    st.divider()
    
    with st.form("nuevo_turno"):
        col1, col2 = st.columns(2)
        with col1:
            paciente_id = st.selectbox(
                "Paciente",
                options=pacientes_df["id_paciente"].tolist() if not pacientes_df.empty else [],
                format_func=lambda x: f"{pacientes_df[pacientes_df['id_paciente']==x]['nombre'].iloc[0]} {pacientes_df[pacientes_df['id_paciente']==x]['apellido'].iloc[0]}" if not pacientes_df.empty else "Sin pacientes"
            )
            hora_inicio = st.time_input("Hora de Inicio", value=datetime.strptime("10:00", "%H:%M").time())
        with col2:
            fecha = st.date_input("Fecha", value=fecha_selector)
            duracion = st.selectbox("Duración (minutos)", [30, 45, 60], index=1)
        
        estado = st.selectbox("Estado", ["programado", "confirmado", "realizado", "cancelado"])
        
        if st.form_submit_button("💾 Guardar Turno"):
            if paciente_id and fecha and hora_inicio:
                try:
                    # Calcular hora fin
                    from datetime import timedelta
                    hora_fin = (datetime.combine(date.today(), hora_inicio) + timedelta(minutes=duracion)).time()
                    
                    data = {
                        "id_paciente": paciente_id,
                        "fecha": fecha.isoformat(),
                        "hora_inicio": hora_inicio.isoformat(),
                        "hora_fin": hora_fin.isoformat(),
                        "estado": estado,
                        "duracion_minutos": duracion
                    }
                    response = supabase.table("turnos").insert(data).execute()
                    st.success("✅ Turno guardado correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================
# PAGOS
# ============================================
elif menu == "💰 Pagos":
    st.title("💰 Gestión de Pagos")
    st.info("🔧 Módulo en desarrollo - Próximamente")

# ============================================
# OBRAS SOCIALES
# ============================================
elif menu == "🏥 Obras Sociales":
    st.title("🏥 Gestión de Obras Sociales")
    st.info("🔧 Módulo en desarrollo - Próximamente")

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption("🧠 PEP'S - Sistema de Gestión para Consultorios v2.0")
