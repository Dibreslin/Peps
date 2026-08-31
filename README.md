# 🧠 PEP'S - Sistema de Gestión para Consultorios Psicológicos

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://peps.streamlit.app)

## 📋 Descripción

PEP'S es un sistema SaaS para gestión de consultorios psicológicos que permite:

- 📅 Gestión de turnos con agenda recurrente
- 👤 Administración de pacientes (con DNI y datos de contacto)
- 💰 Control de pagos y saldos
- 📊 Reportes y estadísticas
- 🔐 Autenticación para profesionales y pacientes
- 📱 Portal público para solicitud de turnos

## 🏗️ Tecnologías

- **Frontend:** [Streamlit](https://streamlit.io)
- **Backend/DB:** [Supabase](https://supabase.com) (PostgreSQL)
- **Auth:** Supabase Auth
- **Email:** Resend
- **Hosting:** Streamlit Cloud

## 🚀 Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/peps.git
cd peps

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .streamlit/secrets.toml con tus credenciales
# (ver sección de configuración)

# Ejecutar app
streamlit run app/main.py
