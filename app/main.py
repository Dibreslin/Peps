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

def generar_turnos_masivos(profesional_id, org_id, dias_seleccionados, hora_inicio, hora_fin, duracion, fecha_desde, fecha_hasta):
    """
    Genera turnos automáticamente para un rango de fechas
    """
    if not supabase:
        return {"error": "No hay conexión a Supabase"}
    
    try:
        turnos_creados = 0
        turnos_existentes = 0
        errores = []
        
        # Convertir días seleccionados a lista de números (0=Domingo, 1=Lunes...)
        dias_numeros = []
        for dia in dias_seleccionados:
            if dia == "Lunes": dias_numeros.append(1)
            elif dia == "Martes": dias_numeros.append(2)
            elif dia == "Miércoles": dias_numeros.append(3)
            elif dia == "Jueves": dias_numeros.append(4)
            elif dia == "Viernes": dias_numeros.append(5)
            elif dia == "Sábado": dias_numeros.append(6)
            elif dia == "Domingo": dias_numeros.append(0)
        
        # Generar fechas
        fecha_actual = fecha_desde
        delta = timedelta(days=1)
        
        while fecha_actual <= fecha_hasta:
            # Verificar si es un día seleccionado
            if fecha_actual.weekday() in dias_numeros:
                # Generar turnos dentro del bloque horario
                hora_actual = datetime.combine(fecha_actual, hora_inicio)
                hora_final = datetime.combine(fecha_actual, hora_fin)
                
                while hora_actual + timedelta(minutes=duracion) <= hora_final:
                    hora_fin_turno = hora_actual + timedelta(minutes=duracion)
                    
                    # Verificar si el turno ya existe (para no duplicar)
                    try:
                        check = supabase.table("turnos")\
                            .select("id_turno")\
                            .eq("fecha", fecha_actual.isoformat())\
                            .eq("hora_inicio", hora_actual.time().strftime("%H:%M:%S"))\
                            .execute()
                        
                        if not check.data:
                            # Crear turno
                            data = {
                                "id_profesional": profesional_id,
                                "id_organizacion": org_id,
                                "fecha": fecha_actual.isoformat(),
                                "hora_inicio": hora_actual.time().strftime("%H:%M:%S"),
                                "hora_fin": hora_fin_turno.time().strftime("%H:%M:%S"),
                                "duracion_minutos": duracion,
                                "estado": "disponible",
                                "origen": "masivo"
                            }
                            supabase.table("turnos").insert(data).execute()
                            turnos_creados += 1
                        else:
                            turnos_existentes += 1
                    except Exception as e:
                        errores.append(str(e))
                    
                    hora_actual = hora_fin_turno
            
            fecha_actual += delta
        
        return {
            "creados": turnos_creados,
            "existentes": turnos_existentes,
            "errores": errores
        }
        
    except Exception as e:
        return {"error": str(e)}



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
# DISPONIBILIDAD - VERSIÓN MEJORADA
# ============================================
elif menu == "⏰ Disponibilidad":
    st.title("⏰ Gestión de Agenda")
    st.subheader("Configuración masiva de turnos")
    
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
    
    # ============================================
    # TABS
    # ============================================
    tab1, tab2, tab3 = st.tabs(["📋 Turnos Generados", "🔄 Generar Turnos", "📊 Resumen"])
    
    # ============================================
    # TAB 1: Ver turnos generados
    # ============================================
    with tab1:
        st.subheader("Turnos disponibles")
        
        # Filtro por fecha
        col1, col2 = st.columns(2)
        with col1:
            fecha_desde_filtro = st.date_input("Desde", value=date.today())
        with col2:
            fecha_hasta_filtro = st.date_input("Hasta", value=date.today() + timedelta(days=30))
        
        try:
            response = supabase.table("turnos")\
                .select("*")\
                .gte("fecha", fecha_desde_filtro.isoformat())\
                .lte("fecha", fecha_hasta_filtro.isoformat())\
                .eq("estado", "disponible")\
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                # Mostrar solo columnas relevantes
                columnas = ["fecha", "hora_inicio", "hora_fin", "estado"]
                st.dataframe(df[columnas], use_container_width=True, hide_index=True)
                st.caption(f"Total: {len(df)} turnos disponibles")
            else:
                st.info("No hay turnos disponibles en el rango seleccionado")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
     # ============================================
    # TAB 2: Generar turnos masivos
    # ============================================
    with tab2:
        st.subheader("🔄 Generar turnos en masa")
        st.caption("Define una regla y el sistema generará todos los turnos automáticamente")
        
        # ============================================
        # CONFIGURACIÓN (fuera del form)
        # ============================================
        col1, col2 = st.columns(2)
        
        with col1:
            dias = st.multiselect(
                "Días de la semana",
                options=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
                default=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
                key="dias_disponibilidad"
            )
            
            hora_inicio = st.time_input(
                "Hora de inicio",
                value=datetime.strptime("17:00", "%H:%M").time(),
                key="hora_inicio_disponibilidad"
            )
            hora_fin = st.time_input(
                "Hora de fin",
                value=datetime.strptime("20:00", "%H:%M").time(),
                key="hora_fin_disponibilidad"
            )
        
        with col2:
            duracion = st.selectbox(
                "Duración de la sesión (minutos)",
                [30, 45, 50, 60, 75, 90],
                index=2,
                key="duracion_disponibilidad"
            )
            
            fecha_desde = st.date_input(
                "Fecha de inicio",
                value=date.today(),
                key="fecha_desde_disponibilidad"
            )
            fecha_hasta = st.date_input(
                "Fecha de fin",
                value=date.today() + timedelta(days=90),
                key="fecha_hasta_disponibilidad"
            )
        
        # ============================================
        # RESUMEN DINÁMICO (se actualiza con cada cambio)
        # ============================================
        st.divider()
        
        # Calcular turnos según los valores actuales
        total_turnos = 0
        dias_habiles = 0
        
        if dias and hora_inicio < hora_fin and fecha_desde <= fecha_hasta:
            # Mapear días
            dias_numeros = []
            for dia in dias:
                if dia == "Lunes": dias_numeros.append(1)
                elif dia == "Martes": dias_numeros.append(2)
                elif dia == "Miércoles": dias_numeros.append(3)
                elif dia == "Jueves": dias_numeros.append(4)
                elif dia == "Viernes": dias_numeros.append(5)
                elif dia == "Sábado": dias_numeros.append(6)
                elif dia == "Domingo": dias_numeros.append(0)
            
            # Contar días hábiles
            fecha_actual = fecha_desde
            while fecha_actual <= fecha_hasta:
                if fecha_actual.weekday() in dias_numeros:
                    dias_habiles += 1
                fecha_actual += timedelta(days=1)
            
            # Calcular turnos por día
            minutos_totales = (datetime.combine(date.today(), hora_fin) - datetime.combine(date.today(), hora_inicio)).seconds // 60
            turnos_por_dia = minutos_totales // duracion
            total_turnos = dias_habiles * turnos_por_dia
            
            # Mostrar resumen
            st.info(f"📊 Se generarán aproximadamente **{total_turnos}** turnos en **{dias_habiles}** días hábiles")
            
            # Mostrar desglose
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📅 Días hábiles", dias_habiles)
            with col2:
                st.metric("⏰ Turnos por día", turnos_por_dia)
            with col3:
                st.metric("📌 Total", total_turnos)
        else:
            st.warning("⚠️ Configurá correctamente los parámetros para ver el resumen")
        
        st.divider()
        
        # ============================================
        # FORMULARIO PARA GENERAR
        # ============================================
        with st.form("generar_turnos_masivos"):
            confirmar = st.checkbox("✅ Confirmo que quiero generar estos turnos", value=False)
            
            if st.form_submit_button("🚀 Generar Turnos", use_container_width=True, type="primary"):
                if not confirmar:
                    st.warning("⚠️ Marcá el checkbox para confirmar la generación")
                elif not dias:
                    st.warning("⚠️ Seleccioná al menos un día")
                elif hora_inicio >= hora_fin:
                    st.warning("⚠️ La hora de inicio debe ser anterior a la hora de fin")
                elif fecha_desde > fecha_hasta:
                    st.warning("⚠️ La fecha de inicio debe ser anterior a la fecha de fin")
                elif total_turnos == 0:
                    st.warning("⚠️ No hay turnos para generar con la configuración actual")
                else:
                    org_id = get_org_id()
                    if not org_id:
                        st.error("❌ No hay organización configurada")
                        st.stop()
                    
                    with st.spinner("🔄 Generando turnos..."):
                        resultado = generar_turnos_masivos(
                            profesional_id,
                            org_id,
                            dias,
                            hora_inicio,
                            hora_fin,
                            duracion,
                            fecha_desde,
                            fecha_hasta
                        )
                    
                    if "error" in resultado:
                        st.error(f"❌ Error: {resultado['error']}")
                    else:
                        st.success(f"✅ Turnos generados correctamente")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("🆕 Creados", resultado["creados"])
                        with col2:
                            st.metric("📌 Ya existentes", resultado["existentes"])
                        if resultado["errores"]:
                            st.warning(f"⚠️ {len(resultado['errores'])} errores")
                        
                        if resultado["creados"] > 0:
                            st.rerun()
    
    # ============================================
    # TAB 3: Resumen
    # ============================================
    with tab3:
        st.subheader("📊 Resumen de la agenda")
        
        try:
            # Total de turnos disponibles
            response = supabase.table("turnos")\
                .select("id_turno", count="exact")\
                .eq("estado", "disponible")\
                .execute()
            total_disponibles = response.count
            
            # Turnos ocupados (con paciente asignado)
            response = supabase.table("turnos")\
                .select("id_turno", count="exact")\
                .eq("estado", "programado")\
                .execute()
            total_programados = response.count
            
            # Turnos realizados
            response = supabase.table("turnos")\
                .select("id_turno", count="exact")\
                .eq("estado", "realizado")\
                .execute()
            total_realizados = response.count
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📌 Disponibles", total_disponibles or 0)
            with col2:
                st.metric("📆 Programados", total_programados or 0)
            with col3:
                st.metric("✅ Realizados", total_realizados or 0)
            
            # Gráfico simple de ocupación
            st.divider()
            st.subheader("📈 Ocupación")
            
            # Próximos 7 días
            st.caption("Próximos 7 días")
            fechas = []
            disponibles = []
            ocupados = []
            
            for i in range(7):
                fecha = date.today() + timedelta(days=i)
                fechas.append(fecha.strftime("%d/%m"))
                
                # Contar disponibles
                response = supabase.table("turnos")\
                    .select("id_turno", count="exact")\
                    .eq("fecha", fecha.isoformat())\
                    .eq("estado", "disponible")\
                    .execute()
                disponibles.append(response.count or 0)
                
                # Contar ocupados
                response = supabase.table("turnos")\
                    .select("id_turno", count="exact")\
                    .eq("fecha", fecha.isoformat())\
                    .neq("estado", "disponible")\
                    .execute()
                ocupados.append(response.count or 0)
            
            # Mostrar como tabla
            df_resumen = pd.DataFrame({
                "Fecha": fechas,
                "Disponibles": disponibles,
                "Ocupados": ocupados
            })
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"❌ Error obteniendo resumen: {str(e)}")
# ============================================
# FOOTER
# ============================================
st.divider()
st.caption("🧠 PEP'S - Sistema de Gestión para Consultorios v2.0")
