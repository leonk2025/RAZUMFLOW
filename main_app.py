import streamlit as st
from datetime import datetime
from models import Proyecto, Estado

# ==============================
# Inicialización de datos
# ==============================
if 'proyectos' not in st.session_state:
    st.session_state.proyectos = []
if 'solicitudes_revision' not in st.session_state:
    st.session_state.solicitudes_revision = []

# Cargar proyectos de ejemplo solo si la lista está vacía
if not st.session_state.proyectos:
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

# ==============================
# Configuración de la página
# ==============================
st.set_page_config(
    page_title="Workflow de Proyectos",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Workflow de Gestión de Proyectos")
st.markdown("---")

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
# Función para mostrar tarjetas
# ==============================
def crear_tarjeta_proyecto(proyecto, estado):
    color = colores_estados[estado]

    st.markdown(f"""
    <div style='
        border: 2px solid {color};
        border-radius: 10px;
        background-color: #ffffff;
        padding: 10px;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        font-size: 14px;
    '>
        <strong>{proyecto.nombre}</strong><br>
        <span style="font-size:12px;">🏢 {proyecto.cliente}</span><br>
        <span style="font-size:12px;">👤 {proyecto.asignado_a}</span><br>
        <span style="font-size:13px; font-weight:bold; color:{color};">💰 ${proyecto.valor_estimado:,.0f}</span><br>
    """, unsafe_allow_html=True)

    dias_sin = (datetime.now() - proyecto.fecha_ultima_actualizacion).days

    if estado == Estado.OPORTUNIDAD:
        color_estado = "green" if dias_sin < 3 else "orange" if dias_sin < 7 else "red"
        st.markdown(f"<span style='font-size:12px; color:{color_estado};'>⏰ {dias_sin} días sin actualizar</span>", unsafe_allow_html=True)
    elif estado == Estado.PREVENTA:
        st.markdown(f"<span style='font-size:12px;'>⏳ En preventa</span>", unsafe_allow_html=True)
    elif estado == Estado.DELIVERY:
        st.markdown(f"<span style='font-size:12px;'>📊 En delivery</span>", unsafe_allow_html=True)
    elif estado == Estado.COBRANZA:
        st.markdown(f"<span style='font-size:12px;'>⚠️ En cobranza</span>", unsafe_allow_html=True)
    elif estado == Estado.POSTVENTA:
        st.markdown(f"<span style='font-size:12px;'>📅 En postventa</span>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# Construcción del tablero Kanban
# ==============================
st.markdown("## 📋 Vista General del Workflow")
st.markdown("### Visualiza el flujo de proyectos entre estados")

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
        st.markdown(f"""
        <div style='background-color: {color}; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;'>
            <h3 style='margin: 0;'>{iconos_estados[estado]} {nombres_estados[estado]}</h3>
            <div style='background-color: white; color: {color}; border-radius: 50%; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold;'>
                {len(proyectos_estado)}
            </div>
        </div>
        """, unsafe_allow_html=True)

        for proyecto in proyectos_estado:
            with st.container():
                crear_tarjeta_proyecto(proyecto, estado)

        if estado == Estado.OPORTUNIDAD:
            if st.button("📊 Gestionar Oportunidades", key="btn_oportunidades", use_container_width=True):
                st.switch_page("pages/1_Oportunidades.py")
        else:
            st.button("⏳ Próximamente", key=f"btn_{estado}", disabled=True, use_container_width=True)

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
st.caption("💡 **Haz clic en 'Gestionar Oportunidades' para ver el dashboard detallado**")

