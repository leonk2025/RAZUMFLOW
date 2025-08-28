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
if "solicitudes_revision" not in st.session_state:
    st.session_state.solicitudes_revision = []

st.title("🎯 Gestión de Oportunidades")
st.markdown("---")

# ==============================
# Filtros
# ==============================
st.sidebar.header("🔍 Filtros de visualización")

filtro_ejecutivo = st.sidebar.selectbox(
    "Filtrar por Ejecutivo",
    ["Todos"] + list({p.asignado_a for p in st.session_state.proyectos}),
)

filtro_riesgo = st.sidebar.selectbox(
    "Filtrar por Riesgo", ["Todos", "Crítico", "En Riesgo", "Bajo Riesgo"]
)

vista = st.sidebar.radio("Vista", ["Tarjetas", "Tabla"])

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
# Lista de Oportunidades
# ==============================
st.header("📋 Lista de Oportunidades")

# Solo proyectos en estado OPORTUNIDAD
proyectos_filtrados = [
    p for p in st.session_state.proyectos if p.estado_actual == Estado.OPORTUNIDAD
]

# Aplicar filtros adicionales
if filtro_ejecutivo != "Todos":
    proyectos_filtrados = [
        p for p in proyectos_filtrados if p.asignado_a == filtro_ejecutivo
    ]

if filtro_riesgo != "Todos":
    dias_limite = 15 if filtro_riesgo == "Crítico" else 7 if filtro_riesgo == "En Riesgo" else 0
    proyectos_filtrados = [
        p for p in proyectos_filtrados
        if (datetime.now() - p.fecha_ultima_actualizacion).days >= dias_limite
    ]

# Mostrar según vista seleccionada
if len(proyectos_filtrados) == 0:
    st.info("No hay proyectos en estado **Oportunidad** que coincidan con los filtros.")
else:
    if vista == "Tarjetas":
        for proyecto in proyectos_filtrados:
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
    else:
        import pandas as pd

        data = [
            {
                "ID": p.id,
                "Nombre": p.nombre,
                "Cliente": p.cliente,
                "Ejecutivo": p.asignado_a,
                "Valor": p.valor_estimado,
                "Última actualización": p.fecha_ultima_actualizacion.strftime(
                    "%d/%m/%Y %H:%M"
                ),
            }
            for p in proyectos_filtrados
        ]
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

# ==============================
# Solicitudes de Revisión (Preventa)
# ==============================
st.markdown("---")
st.header("📌 Solicitudes de Revisión de Preventa")

with st.form("form_solicitud_preventa", clear_on_submit=True):
    proyecto_id = st.selectbox(
        "Selecciona proyecto",
        [p.id for p in st.session_state.proyectos if p.estado_actual == Estado.OPORTUNIDAD],
        format_func=lambda x: next(
            (p.nombre for p in st.session_state.proyectos if p.id == x), ""
        ),
    )
    comentario = st.text_area("Comentario para el equipo de preventa")
    submit_solicitud = st.form_submit_button("📨 Enviar Solicitud")

    if submit_solicitud:
        st.session_state.solicitudes_revision.append(
            {"proyecto_id": proyecto_id, "comentario": comentario}
        )
        st.success("Solicitud enviada correctamente ✅")

if len(st.session_state.solicitudes_revision) == 0:
    st.info("No hay solicitudes pendientes.")
else:
    for s in st.session_state.solicitudes_revision:
        proyecto = next((p for p in st.session_state.proyectos if p.id == s["proyecto_id"]), None)
        if proyecto:
            st.write(
                f"🔔 Proyecto **{proyecto.nombre}** ({proyecto.cliente}) - Comentario: {s['comentario']}"
            )
