import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client

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

# ============================================
# CONEXIÓN A SUPABASE
# ============================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"❌ Error de conexión: {str(e)}")
    st.stop()

# ============================================
# FUNCIÓN PARA OBTENER ID DE ORGANIZACIÓN
# ============================================
def get_org_id():
    try:
        response = supabase.table("organizaciones").select("id_organizacion").limit(1).execute()
        if response.data:
            return response.data[0]["id_organizacion"]
        return None
    except Exception as e:
        return None

# ============================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================
def do_login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user:
            st.session_state.authenticated = True
            st.session_state.user = email
            st.session_state.user_name = email.split("@")[0].capitalize()
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
    try:
        response = supabase.table("pacientes").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def get_turnos_hoy():
    try:
        hoy = date.today().isoformat()
        response = supabase.table("turnos").select("*, pacientes(nombre, apellido)").eq("fecha", hoy).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df["paciente_nombre"] = df["pacientes"].apply(
                lambda x: f"{x['nombre']} {x['apellido']}" if x else "Sin asignar"
            )
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def get_disponibilidades():
    try:
        response = supabase.table("disponibilidades").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# ============================================
# LOGIN
# ============================================
if not st.session_state.authenticated:
    st.title("🧠 PEP'S - Sistema de Gestión")
    st.subheader("Iniciar Sesión")
    
    with st.form("login_form"):
        email = st.text_input("📧 Email", placeholder="admin@peps.com")
        password = st.text_input("🔑 Contraseña", type="password", placeholder="••••••••")
        
        if st.form_submit_button("🚀 Ingresar", use_container_width=True, type="primary"):
            if do_login(email, password):
                st.success("✅ Sesión iniciada")
                st.rerun()
    
    st.caption("📝 Usuario: admin@peps.com | Contraseña: admin123")
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
    ["📅 Dashboard", "👤 Pacientes", "📆 Turnos", "💰 Pagos", "🏥 Obras Sociales", "⏰ Disponibilidad"],
    index=0
)

# ============================================
# DASHBOARD
# ============================================
if menu == "📅 Dashboard":
    st.title("📅 Dashboard")
    st.caption(f"📆 {datetime.now().strftime('%A, %d de %B de %Y')}")
    
    pacientes_df = get_pacientes()
    turnos_df = get_turnos_hoy()
    disponibilidad_df = get_disponibilidades()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Pacientes", len(pacientes_df))
    with col2:
        st.metric("📆 Turnos Hoy", len(turnos_df))
    with col3:
        st.metric("⏰ Horarios", len(disponibilidad_df))
    with col4:
        st.metric("💰 Ingresos", "$ 0")
    
    st.divider()
    st.subheader("📋 Turnos de Hoy")
    if not turnos_df.empty:
        st.dataframe(turnos_df[["hora_inicio", "paciente_nombre", "estado"]], use_container_width=True, hide_index=True)
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
                    org_id = get_org_id()
                    if not org_id:
                        st.error("❌ No hay organización configurada")
                        st.stop()
                    
                    try:
                        data = {
                            "id_organizacion": org_id,
                            "nombre": nombre,
                            "apellido": apellido,
                            "tipo_documento": tipo_doc,
                            "nro_documento": nro_doc,
                            "telefono": telefono,
                            "email": email,
                            "fecha_nacimiento": fecha_nac.isoformat() if fecha_nac else None
                        }
                        supabase.table("pacientes").insert(data).execute()
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
    st.info("🔧 Módulo en desarrollo - Próximamente")

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
# DISPONIBILIDAD
# ============================================
elif menu == "⏰ Disponibilidad":
    st.title("⏰ Gestión de Disponibilidad")
    st.subheader("Configuración de horarios del profesional")
    
    # Obtener el primer profesional
    profesional_id = None
    try:
        response = supabase.table("profesionales").select("id_profesional").limit(1).execute()
        if response.data:
            profesional_id = response.data[0]["id_profesional"]
    except Exception as e:
        st.warning("⚠️ No se encontró un profesional configurado")
    
    if not profesional_id:
        st.info("💡 Primero debés configurar un profesional en la base de datos.")
        st.stop()
    
    tab1, tab2 = st.tabs(["📋 Mi Disponibilidad", "➕ Nueva Disponibilidad"])
    
    with tab1:
        st.subheader("Horarios configurados")
        
        try:
            response = supabase.table("disponibilidades")\
                .select("*")\
                .eq("id_profesional", profesional_id)\
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                dias = {0: "Domingo", 1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado"}
                df["dia_nombre"] = df["dia_semana"].map(dias)
                
                columnas = ["dia_nombre", "hora_inicio", "hora_fin", "duracion_minutos", "estado"]
                st.dataframe(df[columnas], use_container_width=True, hide_index=True)
            else:
                st.info("No hay horarios configurados")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.subheader("Configurar nuevo horario")
        
        with st.form("nueva_disponibilidad"):
            col1, col2 = st.columns(2)
            
            with col1:
                dia_semana = st.selectbox(
                    "Día de la semana",
                    options=[(0, "Domingo"), (1, "Lunes"), (2, "Martes"), (3, "Miércoles"), 
                             (4, "Jueves"), (5, "Viernes"), (6, "Sábado")],
                    format_func=lambda x: x[1]
                )
                
                hora_inicio = st.time_input("Hora de inicio", value=datetime.strptime("09:00", "%H:%M").time())
                hora_fin = st.time_input("Hora de fin", value=datetime.strptime("17:00", "%H:%M").time())
            
            with col2:
                duracion = st.selectbox("Duración de la sesión (minutos)", [30, 45, 50, 60, 90], index=2)
                fecha_desde = st.date_input("Fecha de inicio", value=date.today())
                fecha_hasta = st.date_input("Fecha de fin (opcional)", value=None)
                estado = st.selectbox("Estado", ["activo", "pausado"])
            
            if st.form_submit_button("💾 Guardar disponibilidad"):
                if hora_inicio >= hora_fin:
                    st.warning("⚠️ La hora de inicio debe ser anterior a la hora de fin")
                else:
                    org_id = get_org_id()
                    if not org_id:
                        st.error("❌ No hay organización configurada")
                        st.stop()
                    
                    try:
                        data = {
                            "id_profesional": profesional_id,
                            "id_organizacion": org_id,
                            "dia_semana": dia_semana[0],
                            "hora_inicio": hora_inicio.strftime("%H:%M:%S"),
                            "hora_fin": hora_fin.strftime("%H:%M:%S"),
                            "duracion_minutos": duracion,
                            "fecha_desde": fecha_desde.isoformat(),
                            "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
                            "estado": estado
                        }
                        supabase.table("disponibilidades").insert(data).execute()
                        st.success("✅ Disponibilidad guardada correctamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption("🧠 PEP'S - Sistema de Gestión para Consultorios v2.0")
