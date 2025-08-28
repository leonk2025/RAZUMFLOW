import streamlit as st
from datetime import datetime
from models import Proyecto, Estado

st.set_page_config(page_title="Oportunidades", page_icon="🎯", layout="wide")

# ==============================
# Inicialización
# ==============================
if "proyectos" not in st.session_state:
    st.session_state.proyectos = []
if "editando" not in st.session_state:
    st.session_state.editando = None

st.title("🎯 Gestión de Oportunidades")
st.markdown("---")

# ==============================
# Crear nueva oportunidad
# ==============================
st.subheader("➕ Crear nueva oportunidad")

with st.form("form_crear_oportunidad", clear_on_submit=True):
    nombre = st.text_input("Nombre del proyecto")
    cliente = st.text_input("Cliente")
    descripcion = st.text_area("Descripción")
    valor = st.number_input("Valor estimado", min_value=0, step=1000)
    asignado_a = st.text_input("Asignado a")

    submitted = st.form_submit_button("💾 Crear Proyecto")

    if submitted:
        nuevo = Proyecto(
            nombre=nombre,
            cliente=cliente,
            valor_estimado=valor,
            descripcion=descripcion,
            asignado_a=asignado_a,
        )
        nuevo.estado_actual = Estado.OPORTUNIDAD
        st.session_state.proyectos.append(nuevo)
        st.success(f"Proyecto '{nombre}' creado correctamente 🎉")

st.markdown("---")

# ==============================
# Listar solo proyectos en OPORTUNIDAD
# ==============================
st.subheader("📋 Lista de Oportunidades")

proyectos_oportunidad = [
    p for p in st.session_state.proyectos if p.estado_actual == Estado.OPORTUNIDAD
]

if len(proyectos_oportunidad) == 0:
    st.info("No hay proyectos en estado **Oportunidad** en este momento.")
else:
    for proyecto in proyectos_oportunidad:
        with st.container():
            st.markdown(
                f"""
            <div style='border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:10px;'>
                <strong>{proyecto.nombre}</strong><br>
                🏢 {proyecto.cliente}<br>
                👤 {proyecto.asignado_a}<br>
                💰 ${proyecto.valor_estimado:,.0f}<br>
                <span style='font-size:12px; color:gray;'>Última actualización: {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )
