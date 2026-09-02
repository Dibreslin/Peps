import streamlit as st
from supabase import create_client

st.title("🔍 Prueba de Conexión")

# Mostrar URL (ocultando parte de la key por seguridad)
st.write(f"URL: {st.secrets['SUPABASE_URL']}")
key = st.secrets['SUPABASE_KEY']
st.write(f"KEY: {key[:15]}...{key[-5:]}")

try:
    # Crear cliente
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
    st.success("✅ Cliente creado correctamente")
    
    # Probar consulta simple
    response = supabase.table("organizaciones").select("*").limit(1).execute()
    st.success(f"✅ Conexión exitosa: {len(response.data)} organizaciones")
    
    # Probar autenticación
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": "marina@peps.com",
            "password": "123456"
        })
        st.success("✅ Login exitoso")
        st.write(f"Usuario: {auth_response.user.email}")
    except Exception as e:
        st.error(f"❌ Error de login: {str(e)}")
        
except Exception as e:
    st.error(f"❌ Error general: {str(e)}")
    st.write("📝 Verificá que la URL y KEY sean correctas")
