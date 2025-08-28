import streamlit as st
from datetime import datetime, timedelta
from models import Proyecto, Estado

# ==============================
# Inicialización de datos
# ==============================
st.set_page_config(page_title="Workflow de Proyectos", page_icon="🏢", layout="wide")

if 'proyectos' not in st.session_state:
    st.session_state.proyectos = []
if 'solicitudes_revision' not in st.session_state:
    st.session_state.solicitudes_revision = []
if 'editando' not in st.session_state:
    st.session_state.editando = None
if "ejemplos_cargados" not in st.session_state:
    st.session_state.ejemplos_cargados = False

# Cargar proyectos de ejemplo solo una vez
if not st.session_state.ejemplos_cargados:
    ejemplos = [
        {"nombre": "Sistema ERP Cliente A", "cliente": "Cliente A", "valor_estimado": 50000,
         "descripcion": "Proyecto ERP", "asignado_a": "Ana García"},
        {"nombre": "App Móvil Retail B", "cliente": "Cliente B", "valor_estimado": 35000,
         "descripcion": "Aplicación móvil para retail", "asignado_a": "Carlos López"},
        {"nombre": "Portal Web Educativo C", "cliente": "Cliente C", "valor_estimado": 42000,
         "descripcion": "Portal educativo online", "asignado_a": "María Rodríguez"},
        {"nombre": "Cloud Migration D", "cliente": "Cliente D", "valor_estimado": 68000,
         "descripcion": "Migración a la nube", "asignado_a": "Pedro Martínez"},
    ]
    for p in ejemplos:
        st.session_state.proyectos.append(
            Proyecto(
                nombre=p["nombre"],
                cliente=p["cliente"],
                valor_estimado=p["valor_estimado"],
                descripcion=p["descripcion"],
                asignado_a=p["asignado_a"]
            )
        )
    st.session_state.ejemplos_cargados = True

# ==============================
# Definir flujo de estados
# ==============================
flujo_estados = [
    Estado.OPORTUNIDAD,
    Estado.PREVENTA,
    Estado.DELIVERY,
    Estado.COBRANZA,
    Estado.POSTVENTA,
    Estado.CERRADO_EXITOSO,
    Estado.CERRADO_PERDIDO
]

# ==============================
# Manejo de parámetros de query
# ==============================
if "edit" in st.query_params:
    try:
        st.session_state.editando = int(st.query_params["edit"])
    except:
        st.session_state.editando = None

def _clear_query_edit():
    if "edit" in st.query_params:
        del st.query_params["edit"]

def _close_editor():
    st.session_state.editando = None
    _clear_query_edit()
    st.rerun()

# ==============================
# ... [aquí se mantiene igual todo el código de estilos, tarjetas y tablero Kanban]
# ==============================

# ==============================
# Panel lateral de edición
# ==============================
if st.session_state.editando:
    proyecto = next((p for p in st.session_state.proyectos if p.id == st.session_state.editando), None)

    if proyecto:
        with st.sidebar:
            st.header(f"✏️ Editar Proyecto #{proyecto.id}")
            st.caption(f"Código: **{proyecto.codigo_proyecto}** • Estado actual: **{proyecto.estado_actual.value}**")

            # --- Formulario (igual que antes) ---
            # [.. lo dejamos igual, no lo repito para ahorrar espacio ..]

            st.markdown("---")
            st.subheader("Acciones de Flujo")

            # Determinar posición en el flujo
            idx = flujo_estados.index(proyecto.estado_actual)
            anterior = flujo_estados[idx-1] if idx > 0 else None
            siguiente = flujo_estados[idx+1] if idx < len(flujo_estados)-1 else None

            # Botón para retroceder
            if anterior:
                if st.button(f"⬅️ Retroceder a {anterior.value}"):
                    proyecto.estado_actual = anterior
                    proyecto.actualizar()
                    _close_editor()

            # Botón para avanzar
            if siguiente:
                if st.button(f"➡️ Avanzar a {siguiente.value}"):
                    proyecto.estado_actual = siguiente
                    proyecto.actualizar()
                    _close_editor()

            st.markdown("---")
            st.subheader("Historial")
            for h in getattr(proyecto, "historial", []):
                st.write(f"• {h}")
