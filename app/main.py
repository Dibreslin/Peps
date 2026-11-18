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
# CSS PERSONALIZADO - REDUCIR ESPACIOS
# ============================================
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    h1 { font-size: 1.3rem !important; margin-top: 0.5rem !important; margin-bottom: 0.2rem !important; }
    h2 { font-size: 1.1rem !important; margin-top: 0.3rem !important; margin-bottom: 0.2rem !important; }
    h3 { font-size: 0.95rem !important; margin-top: 0.2rem !important; margin-bottom: 0.1rem !important; }
    .stElementContainer { margin-bottom: 0.2rem !important; }
    .stDataFrame { font-size: 0.8rem !important; }
    .stMetric { padding: 0.2rem !important; }
    .stForm { padding: 0.3rem !important; }
    section[data-testid="stSidebar"] { padding-top: 0.5rem !important; }
    .stColumns { gap: 0.3rem !important; }
    hr { margin: 0.3rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ============================================
# INICIALIZACIÓN
# ============================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "contador_seleccion" not in st.session_state:
    st.session_state.contador_seleccion = 0
if "contador_grilla" not in st.session_state:
    st.session_state.contador_grilla = 0


# ============================================
# CONEXIÓN A SUPABASE POR SESIÓN
# ============================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

    # Cada sesión de Streamlit mantiene su propio cliente.
    if "supabase_client" not in st.session_state:
        st.session_state.supabase_client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

    supabase = st.session_state.supabase_client

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
# FUNCIONES DE AUDITORÍA
# ============================================


def get_contexto_usuario():
    """
    Identifica al usuario autenticado y obtiene su contexto interno.
    No utiliza el email como mecanismo de identificación.
    """
    try:
        auth_user_id = st.session_state.get("auth_user_id")

        if not st.session_state.get("authenticated") or not auth_user_id:
            return None

        response = (
            supabase.table("usuarios")
            .select(
                "id_usuario, id_organizacion, email, nombre, apellido, rol"
            )
            .eq("auth_user_id", auth_user_id)
            .is_("fecha_caducacion", "null")
            .execute()
        )

        if len(response.data) != 1:
            return None

        usuario = response.data[0]

        contexto = {
            "id_usuario": usuario["id_usuario"],
            "id_organizacion": usuario["id_organizacion"],
            "email": usuario["email"],
            "nombre": usuario["nombre"],
            "apellido": usuario["apellido"],
            "rol": usuario["rol"],
            "id_profesional": None
        }

        if usuario["rol"] == "profesional":
            profesional = (
                supabase.table("profesionales")
                .select("id_profesional")
                .eq("id_usuario", usuario["id_usuario"])
                .eq("id_organizacion", usuario["id_organizacion"])
                .is_("fecha_caducacion", "null")
                .execute()
            )

            if len(profesional.data) != 1:
                return None

            contexto["id_profesional"] = (
                profesional.data[0]["id_profesional"]
            )

        elif usuario["rol"] != "admin":
            return None

        return contexto

    except Exception as e:
        st.error(f"Error identificando al usuario: {str(e)}")
        return None


def get_usuario_actual():
    """Obtiene el ID interno del usuario autenticado."""
    contexto = get_contexto_usuario()
    return contexto["id_usuario"] if contexto else None


def get_org_id():
    """Obtiene la organización del usuario autenticado."""
    contexto = get_contexto_usuario()
    return contexto["id_organizacion"] if contexto else None




def insertar_con_auditoria(tabla, data):
    """
    Inserta un registro agregando fecha_alta y usuario_alta.
    """
    try:
        contexto = get_contexto_usuario()

        if not contexto:
            raise Exception("No se pudo identificar al usuario autenticado.")

        datos_insertar = data.copy()
        datos_insertar["fecha_alta"] = datetime.now().isoformat()
        datos_insertar["usuario_alta"] = contexto["id_usuario"]

        response = supabase.table(tabla).insert(datos_insertar).execute()
        return response

    except Exception as e:
        raise e


def obtener_activos(tabla, columnas="*"):
    """
    Obtiene solo los registros activos (fecha_caducacion IS NULL)
    """
    try:
        response = supabase.table(tabla)\
            .select(columnas)\
            .is_("fecha_caducacion", "null")\
            .execute()
        return response
    except Exception as e:
        raise e


def eliminar_logico(tabla, campo_id, valor_id):
    """
    Eliminación lógica: actualiza fecha_caducacion en lugar de borrar
    """
    try:
        data = {
            "fecha_caducacion": datetime.now().isoformat()
        }
        
        usuario_id = get_usuario_actual()
        if usuario_id:
            data["usuario_caducacion"] = usuario_id
        
        response = supabase.table(tabla)\
            .update(data)\
            .eq(campo_id, valor_id)\
            .execute()
        return response
    except Exception as e:
        raise e


# ============================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================

def do_login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user and response.session:
            st.session_state.authenticated = True
            st.session_state.user = response.user.email
            st.session_state.auth_user_id = response.user.id
            st.session_state.user_name = (
                response.user.email.split("@")[0].capitalize()
            )
            return True

        return False

    except Exception as e:
        st.error(f"❌ Error de login: {str(e)}")
        return False


def do_logout():
    try:
        supabase.auth.sign_out()
    except Exception as e:
        st.warning(f"No se pudo cerrar la sesión de Auth: {str(e)}")

    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.auth_user_id = None
    st.session_state.user_name = ""

    # Descartar el cliente para evitar reutilizar su estado.
    st.session_state.pop("supabase_client", None)

    st.rerun()

# ============================================
# FUNCIÓN cancelar_turno_y_reprogramar
# ============================================

def cancelar_turno_y_reprogramar(turno_id, motivo="Cancelado por el profesional"):
    """
    Cancela un turno y libera su horario mediante una operación
    transaccional en Supabase.
    """
    try:
        contexto = get_contexto_usuario()

        if not contexto or contexto["rol"] != "profesional":
            return {"error": "No hay un profesional autenticado"}

        response = supabase.rpc(
            "cancelar_turno_profesional",
            {
                "p_turno_id": str(turno_id),
                "p_motivo": motivo
            }
        ).execute()

        resultado = response.data

        if isinstance(resultado, dict) and resultado.get("success"):
            st.session_state.pop("turno_seleccionado", None)

            return {
                "success": True,
                "message": "Turno cancelado y horario liberado correctamente",
                "turno_original": resultado["turno_original"],
                "nuevo_turno": resultado["nuevo_turno"],
                "cancelacion_tardia": resultado["cancelacion_tardia"]
            }

        return {"error": "Supabase no confirmó la cancelación"}

    except Exception as e:
        return {"error": str(e)}



# ============================================
# FUNCIONES PARA OBTENER DATOS
# ============================================

def get_pacientes():
    """Obtiene únicamente los pacientes de la cuenta del profesional."""
    try:
        contexto = get_contexto_usuario()

        if not contexto or contexto["rol"] != "profesional":
            return pd.DataFrame()

        response = (
            supabase.table("pacientes")
            .select("*")
            .eq("id_organizacion", contexto["id_organizacion"])
            .is_("fecha_caducacion", "null")
            .order("apellido")
            .execute()
        )

        return pd.DataFrame(response.data) if response.data else pd.DataFrame()

    except Exception as e:
        st.error(f"Error al obtener pacientes: {str(e)}")
        return pd.DataFrame()


def get_turnos_hoy():
    """Obtiene los turnos del día del profesional autenticado."""
    try:
        contexto = get_contexto_usuario()

        if not contexto or contexto["rol"] != "profesional":
            return pd.DataFrame()

        hoy = date.today().strftime("%Y-%m-%d")

        response = (
            supabase.table("turnos")
            .select("*, pacientes(nombre, apellido)")
            .eq("id_organizacion", contexto["id_organizacion"])
            .eq("id_profesional", contexto["id_profesional"])
            .eq("fecha", hoy)
            .is_("fecha_caducacion", "null")
            .execute()
        )

        if response.data:
            df = pd.DataFrame(response.data)
            df["paciente_nombre"] = df["pacientes"].apply(
                lambda x: (
                    f"{x['nombre']} {x['apellido']}"
                    if isinstance(x, dict) and x
                    else "Sin asignar"
                )
            )
            return df

        return pd.DataFrame()

    except Exception as e:
        st.error(f"Error al obtener turnos de hoy: {str(e)}")
        return pd.DataFrame()


def get_disponibilidades():
    """Obtiene las disponibilidades del profesional autenticado."""
    try:
        contexto = get_contexto_usuario()

        if not contexto or contexto["rol"] != "profesional":
            return pd.DataFrame()

        response = (
            supabase.table("disponibilidades")
            .select("*")
            .eq("id_profesional", contexto["id_profesional"])
            .is_("fecha_caducacion", "null")
            .execute()
        )

        return pd.DataFrame(response.data) if response.data else pd.DataFrame()

    except Exception as e:
        st.error(f"Error al obtener disponibilidades: {str(e)}")
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
                        insertar_con_auditoria("pacientes", data)
                        st.success("✅ Paciente guardado correctamente")
                        st.rerun()
                    except Exception as e:
                        error_msg = str(e)
                        if "duplicate key" in error_msg or "uk_paciente_org_doc" in error_msg:
                            st.warning("⚠️ **Ya existe un paciente con ese DNI** en el sistema. Verificá los datos.")
                        else:
                            st.error(f"❌ Error: {error_msg}")
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
    # TAB 1: Ver y gestionar turnos generados
    # ============================================
    with tab1:
        st.subheader("📋 Turnos generados")
        
        # Filtros
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            fecha_desde_filtro = st.date_input("📅 Desde", value=date.today())
        with col2:
            fecha_hasta_filtro = st.date_input("📅 Hasta", value=date.today() + timedelta(days=30))
        with col3:
            estado_filtro = st.selectbox(
                "Estado",
                ["todos", "disponible", "programado", "confirmado", "realizado", "cancelado"],
                key="estado_filtro_tab1"
            )
        
        try:
            # Convertir fechas a string
            fecha_desde_str = fecha_desde_filtro.strftime("%Y-%m-%d")
            fecha_hasta_str = fecha_hasta_filtro.strftime("%Y-%m-%d")
            
            # Consulta base (solo turnos activos)
            query = supabase.table("turnos")\
                .select("*")\
                .gte("fecha", fecha_desde_str)\
                .lte("fecha", fecha_hasta_str)\
                .is_("fecha_caducacion", "null")
            
            if estado_filtro != "todos":
                query = query.eq("estado", estado_filtro)
            
            response = query.execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                
                # Usar dataframe con selección
                df_mostrar = df[["id_turno", "fecha", "hora_inicio", "hora_fin", "estado"]].copy()
                df_mostrar["fecha"] = pd.to_datetime(df_mostrar["fecha"]).dt.strftime("%Y-%m-%d")
                
                # Mostrar la grilla con selección
                event = st.dataframe(
                    df_mostrar,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="tabla_turnos",
                    column_config={
                        "id_turno": None,
                        "fecha": "📅 Fecha",
                        "hora_inicio": "🕐 Inicio",
                        "hora_fin": "🕐 Fin",
                        "estado": "📌 Estado"
                    }
                )
                
                st.caption(f"📊 Total: {len(df)} turnos")
                
                # Procesar selección de la grilla
                if event.selection and event.selection.rows:
                    idx = event.selection.rows[0]
                    turno_desde_grilla = df_mostrar.iloc[idx]["id_turno"]
                    
                    if st.session_state.get("turno_seleccionado_id") != turno_desde_grilla:
                        st.session_state["turno_seleccionado_id"] = turno_desde_grilla
                        st.session_state.contador_grilla += 1
                
                # ============================================
                # SECCIÓN DE ACCIONES
                # ============================================
                st.subheader("🔧 Acciones sobre turnos")
                
                turnos_opciones = []
                for _, row in df.iterrows():
                    turnos_opciones.append({
                        "id": row["id_turno"],
                        "label": f"{row['fecha']} {row['hora_inicio']} - {row['estado']}"
                    })
                
                if turnos_opciones:
                    key_dinamica = f"turno_seleccionado_acciones_{st.session_state.contador_grilla}"
                    
                    opciones_ids = [op["id"] for op in turnos_opciones]
                    turno_guardado = st.session_state.get("turno_seleccionado_id", None)
                    
                    if turno_guardado and turno_guardado in opciones_ids:
                        idx_default = opciones_ids.index(turno_guardado)
                    else:
                        idx_default = 0
                    
                    turno_seleccionado = st.selectbox(
                        "Seleccioná un turno para modificar",
                        options=turnos_opciones,
                        format_func=lambda x: x["label"],
                        index=idx_default,
                        key=key_dinamica
                    )
                    
                    if turno_seleccionado:
                        st.session_state["turno_seleccionado_id"] = turno_seleccionado["id"]
                    
                    if turno_seleccionado:
                        turno_data_filtrado = df[df["id_turno"] == turno_seleccionado["id"]]
                        
                        if turno_data_filtrado.empty:
                            st.stop()
                        
                        turno_data = turno_data_filtrado.iloc[0]
                        estado_actual = turno_data["estado"]
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("**🔄 Cambiar estado**")
                            
                            if estado_actual not in ["realizado", "cancelado"]:
                                if estado_actual == "disponible":
                                    opciones_estado = ["disponible", "programado", "confirmado"]
                                elif estado_actual == "programado":
                                    opciones_estado = ["programado", "confirmado", "realizado", "cancelado"]
                                elif estado_actual == "confirmado":
                                    opciones_estado = ["confirmado", "realizado", "cancelado"]
                                else:
                                    opciones_estado = [estado_actual]
                                
                                idx_actual = opciones_estado.index(estado_actual) if estado_actual in opciones_estado else 0
                                
                                nuevo_estado = st.selectbox(
                                    "Nuevo estado",
                                    options=opciones_estado,
                                    index=idx_actual,
                                    key="nuevo_estado_acciones"
                                )
                                
                                if st.button("🔄 Actualizar", key="btn_actualizar_acciones"):
                                    try:
                                        supabase.table("turnos")\
                                            .update({"estado": nuevo_estado})\
                                            .eq("id_turno", turno_seleccionado["id"])\
                                            .execute()
                                        st.success(f"✅ Estado actualizado a **{nuevo_estado}**")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Error: {str(e)}")
                            else:
                                st.info(f"Este turno está **{estado_actual}** y no se puede modificar")
                        
                        with col2:
                            st.markdown("**🗑️ Cancelar turno**")
                            
                            if estado_actual in ["disponible", "programado", "confirmado"]:
                                try:
                                    fecha_hora_turno = datetime.combine(
                                        datetime.strptime(turno_data["fecha"], "%Y-%m-%d").date(),
                                        datetime.strptime(turno_data["hora_inicio"], "%H:%M:%S").time()
                                    )
                                    es_futuro = fecha_hora_turno > datetime.now()
                                except:
                                    es_futuro = True
                                
                                if es_futuro:
                                    motivo = st.text_input("Motivo de cancelación (opcional)", key="motivo_cancelacion_acciones")
                                    
                                    if st.button("🗑️ Cancelar y liberar horario", type="secondary", key="btn_cancelar_acciones"):
                                        with st.spinner("🔄 Cancelando turno..."):
                                            resultado = cancelar_turno_y_reprogramar(
                                                turno_seleccionado["id"],
                                                motivo or "Cancelado por usuario"
                                            )
                                        
                                        if "error" in resultado:
                                            st.error(f"❌ {resultado['error']}")
                                        else:
                                            st.success(f"✅ {resultado['message']}")
                                            # LIMPIAR SELECCIÓN DE LA GRILLA
                                            st.session_state["turno_seleccionado_id"] = None
                                            st.session_state.contador_grilla += 1
                                            st.rerun()
                                else:
                                    st.info("🔒 Este turno ya pasó y no se puede cancelar")
                            else:
                                st.info(f"🔒 Turno {estado_actual} no se puede cancelar")
                        
                        with col3:
                            st.markdown("**👤 Asignar paciente**")
                            
                            if estado_actual == "disponible":
                                pacientes_df = get_pacientes()
                                
                                if not pacientes_df.empty:
                                    paciente_seleccionado = st.selectbox(
                                        "Seleccionar paciente",
                                        options=pacientes_df["id_paciente"].tolist(),
                                        format_func=lambda x: f"{pacientes_df[pacientes_df['id_paciente']==x]['nombre'].iloc[0]} {pacientes_df[pacientes_df['id_paciente']==x]['apellido'].iloc[0]}",
                                        key="paciente_asignar_acciones"
                                    )
                                    
                                    if st.button("📌 Asignar", key="btn_asignar_acciones"):
                                        try:
                                            supabase.table("turnos")\
                                                .update({
                                                    "id_paciente": paciente_seleccionado,
                                                    "estado": "programado"
                                                })\
                                                .eq("id_turno", turno_seleccionado["id"])\
                                                .execute()
                                            st.success("✅ Paciente asignado correctamente")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error: {str(e)}")
                                else:
                                    st.info("No hay pacientes registrados")
                            else:
                                st.info(f"🔒 Turno {estado_actual}")
                else:
                    st.info("No hay turnos para gestionar")
            else:
                st.info("No hay turnos en el rango seleccionado")
        
        except Exception as e:
            st.error(f"❌ Error al cargar turnos: {str(e)}")
    
    # ============================================
    # TAB 2: Generar turnos masivos
    # ============================================
    with tab2:
        st.subheader("🔄 Generar turnos en masa")
        st.caption("Define una regla y el sistema generará todos los turnos automáticamente")
        
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
        
        st.divider()
        
        # Calcular turnos según los valores actuales
        total_turnos = 0
        dias_habiles = 0
        
        if dias and hora_inicio < hora_fin and fecha_desde <= fecha_hasta:
            dias_numeros = []
            for dia in dias:
                if dia == "Lunes": dias_numeros.append(0)
                elif dia == "Martes": dias_numeros.append(1)
                elif dia == "Miércoles": dias_numeros.append(2)
                elif dia == "Jueves": dias_numeros.append(3)
                elif dia == "Viernes": dias_numeros.append(4)
                elif dia == "Sábado": dias_numeros.append(5)
                elif dia == "Domingo": dias_numeros.append(6)
            
            fecha_actual = fecha_desde
            while fecha_actual <= fecha_hasta:
                if fecha_actual.weekday() in dias_numeros:
                    dias_habiles += 1
                fecha_actual += timedelta(days=1)
            
            minutos_totales = (datetime.combine(date.today(), hora_fin) - datetime.combine(date.today(), hora_inicio)).seconds // 60
            turnos_por_dia = minutos_totales // duracion
            total_turnos = dias_habiles * turnos_por_dia
            
            st.info(f"📊 Se generarán aproximadamente **{total_turnos}** turnos en **{dias_habiles}** días hábiles")
            
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
                            with st.expander(f"⚠️ Ver {len(resultado['errores'])} errores"):
                                for error in resultado["errores"]:
                                    st.code(error)
                        
                        if resultado["creados"] > 0:
                            st.rerun()
    
    # ============================================
    # TAB 3: Resumen
    # ============================================
    with tab3:
        st.subheader("📊 Resumen de la agenda")
        
        try:
            response = supabase.table("turnos")\
                .select("id_turno", count="exact")\
                .eq("estado", "disponible")\
                .is_("fecha_caducacion", "null")\
                .execute()
            total_disponibles = response.count
            
            response = supabase.table("turnos")\
                .select("id_turno", count="exact")\
                .eq("estado", "programado")\
                .is_("fecha_caducacion", "null")\
                .execute()
            total_programados = response.count
            
            response = supabase.table("turnos")\
                .select("id_turno", count="exact")\
                .eq("estado", "realizado")\
                .is_("fecha_caducacion", "null")\
                .execute()
            total_realizados = response.count
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📌 Disponibles", total_disponibles or 0)
            with col2:
                st.metric("📆 Programados", total_programados or 0)
            with col3:
                st.metric("✅ Realizados", total_realizados or 0)
            
            st.divider()
            st.subheader("📈 Ocupación")
            st.caption("Próximos 7 días")
            
            fechas = []
            disponibles = []
            ocupados = []
            
            for i in range(7):
                fecha = date.today() + timedelta(days=i)
                fechas.append(fecha.strftime("%d/%m"))
                
                response = supabase.table("turnos")\
                    .select("id_turno", count="exact")\
                    .eq("fecha", fecha.isoformat())\
                    .eq("estado", "disponible")\
                    .is_("fecha_caducacion", "null")\
                    .execute()
                disponibles.append(response.count or 0)
                
                response = supabase.table("turnos")\
                    .select("id_turno", count="exact")\
                    .eq("fecha", fecha.isoformat())\
                    .neq("estado", "disponible")\
                    .is_("fecha_caducacion", "null")\
                    .execute()
                ocupados.append(response.count or 0)
            
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
