import streamlit as st
from supabase import create_client, Client

# ============================================
# CONEXIÓN A SUPABASE
# ============================================
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception as e:
    supabase = None
    st.error(f"❌ Error conectando a Supabase: {str(e)}")

def get_supabase():
    """Devuelve el cliente de Supabase"""
    return supabase
