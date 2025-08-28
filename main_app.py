import streamlit as st
from datetime import datetime, timedelta
from models import Proyecto, Estado

# ==============================
# Configuración inicial
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

# ==============================
# Cargar proyectos de ejemplo (una sola vez)
# ==============================
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
# Flujo lineal de estados
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
# Manejo de query params
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
# Estilos CSS
# ==============================
st.markdown("""
<style>
.card {
  position: relative;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
  padding: 12px 12px 8px 12px;
  margin-bottom: 10px;
  box-shadow: 2px 2px 6px rgba(0,0,0,0.07);
  font-size: 14px;
}
.card .edit-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  text-decoration: none;
  padding: 4px 7px;
  border-radius: 8px;
  background: rgba(0,0,0,0.05);
  font-size: 13px;
}
.card .edit-btn:hover { background: rgba(0,0,0,0.12); }
.section-header {
  color: white; padding: 14px; border-radius: 10px; text-align:center; margin-bottom: 14px;
}
.badge {
  background: white; border-radius: 50%; width: 30px; height: 30px;
  display: inline-flex; align-items: center; justify-content: center; font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# Configuración visual
# ==============================
colores_estados = {
    Estado.OPORTUNIDAD: '#FF6B6B',
    Estado.PREVENTA: '#4ECDC4',
    Estado.DELIVERY: '#45B7D1',
    Estado.COBRANZA: '#96CEB4',
    Estado.POSTVENTA: '#FFEAA7'
}

iconos_estados = {
    Estado.OPORTUNIDAD: '🎯',
    Estado.PREVENTA: '📋',
    Estado.DELIVERY: '🚀',
    Estado.COBRANZA: '💰',
    Estado.POSTVENTA: '🔧'
}

nombres_estados = {
    Estado.OPORTUNIDAD: 'OPORTUNIDADES',
    Estado.PREVENTA: 'PREVENTA',
    Estado.DELIVERY: 'DELIVERY',
    Estado.COBRANZA: 'COBRANZA',
    Estado.POSTVENTA: 'POSTVENTA'
}

# ==============================
# Cabecera
# ==============================
st.title("🏢 Workflow de Gestión de Proyectos")
st.markdown("---")
st.markdown("## 📋 Vista General del Workflow")
st.markdown("### Visualiza el flujo de proyectos entre estados")
st.markdown("<div id='edit-panel'></div>", unsafe_allow_html=True)

# ==============================
# Función para tarjetas
# ==============================
def crear_tarjeta_proyecto(proyecto, estado):
    color = colores_estados.get(estado, "#ccc")
    dias_sin = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
    extra_line = ""

    if estado == Estado.OPORTUNIDAD:
        color_estado = "green" if dias_sin < 3 else "orange" if dias_sin < 7 else "red"
        extra_line = f"<span style='font-size:12px; color:{color_estado};'>⏰ {dias_sin} días sin actualizar</span>"

    st.markdown(f"""
    <div class='card' style='border-color:{color};'>
        <a class='edit-btn' href='?edit={proyecto.id}#edit-panel' title='Editar'>✏️</a>
        <strong>{proyecto.nombre}</strong><br>
        <span style="font-size:12px;">🏢 {proyecto.cliente}</span><br>
        <span style="font-size:12px;">👤 {proyecto.asignado_a}</span><br>
        <span style="font-size:13px; font-weight:bold; color:{color};">💰 ${proyecto.valor_estimado:,.0f}</span><br>
        {extra_line}
    </div>
    """, unsafe_allow_html=True)

# ==============================
# Construcción del tablero Kanban
# ==============================
col1, col2, col3, col4, col5 = st.columns(5)
cols_map = {
    Estado.OPORTUNIDAD: col1,
    Estado.PREVENTA: col2,
    Estado.DELIVERY: col3,
    Estado.COBRANZA: col4,
    Estado.POSTVENTA: col5
}

for estado, col in cols_map.items():
    color = colores_estados[estado]
    proyectos_estado = [p for p in st.session_state.proyectos if p.estado_actual == estado]

    with col:
        st.markdown(
            f"<div class='section-header' style='background:{color};'>"
            f"<h3 style='margin:0;'>{iconos_estados[estado]} {nombres_estados[estado]}</h3>"
            f"<div class='badge' style='color:{color};'>{len(proyectos_estado)}</div>"
            f"</div>", unsafe_allow_html=True
        )

        for proyecto in proyectos_estado:
            with st.container():
                crear_tarjeta_proyecto(proyecto, estado)

        if estado == Estado.OPORTUNIDAD:
            st.page_link("pages/1_Oportunidades.py", label="📊 Gestionar Oportunidades")
        else:
            st.button("⏳ Próximamente", key=f"btn_{estado}", disabled=True, use_container_width=True)

# ==============================
# Sidebar de edición con flujo lineal
# ==============================
if st.session_state.editando:
    proyecto = next((p for p in st.session_state.proyectos if p.id == st.session_state.editando), None)

    if proyecto:
        with st.sidebar:
            st.header(f"✏️ Editar Proyecto #{proyecto.id}")
            st.caption(f"Código: **{proyecto.codigo_proyecto}** • Estado actual: **{proyecto.estado_actual.value}**")

            with st.form(f"form_edit_{proyecto.id}", clear_on_submit=False):
                nuevo_nombre = st.text_input("Nombre", proyecto.nombre)
                nuevo_cliente = st.text_input("Cliente", proyecto.cliente)
                nueva_descripcion = st.text_area("Descripción", proyecto.descripcion)
                nuevo_valor = st.number_input("Valor estimado", min_value=0, step=1000, value=int(proyecto.valor_estimado))
                nuevo_asignado = st.text_input("Asignado a", proyecto.asignado_a)

                guardar = st.form_submit_button("💾 Guardar cambios")
                cancelar = st.form_submit_button("❌ Cancelar")

                if guardar:
                    proyecto.nombre = nuevo_nombre
                    proyecto.cliente = nuevo_cliente
                    proyecto.descripcion = nueva_descripcion
                    proyecto.valor_estimado = nuevo_valor
                    proyecto.asignado_a = nuevo_asignado
                    proyecto.actualizar()
                    _close_editor()

                if cancelar:
                    _close_editor()

            st.markdown("---")
            st.subheader("Acciones de Flujo")

            idx = flujo_estados.index(proyecto.estado_actual)
            anterior = flujo_estados[idx-1] if idx > 0 else None
            siguiente = flujo_estados[idx+1] if idx < len(flujo_estados)-1 else None

            if anterior and st.button(f"⬅️ Retroceder a {anterior.value}"):
                proyecto.estado_actual = anterior
                proyecto.actualizar()
                _close_editor()

            if siguiente and st.button(f"➡️ Avanzar a {siguiente.value}"):
                proyecto.estado_actual = siguiente
                proyecto.actualizar()
                _close_editor()

            st.markdown("---")
            st.subheader("Historial")
            for h in getattr(proyecto, "historial", []):
                st.write(f"• {h}")

# ==============================
# Resumen general
# ==============================
st.markdown("---")
st.markdown("## 📊 Resumen General por Estado")

resumen_cols = st.columns(5)
for i, estado in enumerate(cols_map.keys()):
    proyectos_estado = [p for p in st.session_state.proyectos if p.estado_actual == estado]
    color = colores_estados[estado]
    total_valor = sum(p.valor_estimado for p in proyectos_estado)

    with resumen_cols[i]:
        st.markdown(f"""
        <div style='text-align: center; padding: 15px; background-color: {color}20; border-radius: 10px; border: 2px solid {color};'>
            <div style='font-size: 24px;'>{iconos_estados[estado]}</div>
            <div style='font-weight: bold; color: {color};'>{nombres_estados[estado]}</div>
            <div style='font-size: 20px; font-weight: bold;'>{len(proyectos_estado)}</div>
            <div style='font-size: 12px;'>proyectos</div>
            <div style='font-size: 16px; font-weight: bold; color: {color};'>${total_valor:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# Footer
# ==============================
st.markdown("---")
st.markdown(f"*Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
st.caption("💡 Haz clic en el ícono ✏️ dentro de cada tarjeta para editar sin salir del main")
