import streamlit as st
from datetime import datetime
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Workflow de Proyectos",
    page_icon="🏢",
    layout="wide"
)

# Título principal
st.title("🏢 Workflow de Gestión de Proyectos")
st.markdown("---")

# Simular datos de proyectos para cada estado
def obtener_proyectos_ejemplo():
    return {
        'oportunidades': [
            {'id': 1, 'nombre': 'Sistema ERP Cliente A', 'cliente': 'Cliente A', 'valor': 50000, 'ejecutivo': 'Ana García', 'dias_sin_actualizar': 2},
            {'id': 2, 'nombre': 'App Móvil Retail B', 'cliente': 'Cliente B', 'valor': 35000, 'ejecutivo': 'Carlos López', 'dias_sin_actualizar': 5},
            {'id': 3, 'nombre': 'Portal Web Educativo C', 'cliente': 'Cliente C', 'valor': 42000, 'ejecutivo': 'María Rodríguez', 'dias_sin_actualizar': 1},
            {'id': 4, 'nombre': 'Cloud Migration D', 'cliente': 'Cliente D', 'valor': 68000, 'ejecutivo': 'Pedro Martínez', 'dias_sin_actualizar': 7}
        ],
        'preventa': [
            {'id': 5, 'nombre': 'CRM Empresarial E', 'cliente': 'Cliente E', 'valor': 55000, 'ejecutivo': 'Ana García', 'dias_espera': 3},
            {'id': 6, 'nombre': 'E-commerce F', 'cliente': 'Cliente F', 'valor': 72000, 'ejecutivo': 'Carlos López', 'dias_espera': 1}
        ],
        'delivery': [
            {'id': 7, 'nombre': 'Sistema Contabilidad G', 'cliente': 'Cliente G', 'valor': 48000, 'ejecutivo': 'María Rodríguez', 'progreso': 75},
            {'id': 8, 'nombre': 'App Logística H', 'cliente': 'Cliente H', 'valor': 61000, 'ejecutivo': 'Pedro Martínez', 'progreso': 45}
        ],
        'cobranza': [
            {'id': 9, 'nombre': 'Software Factory I', 'cliente': 'Cliente I', 'valor': 89000, 'ejecutivo': 'Ana García', 'dias_vencido': 15},
            {'id': 10, 'nombre': 'Consultoría Cloud J', 'cliente': 'Cliente J', 'valor': 32000, 'ejecutivo': 'Carlos López', 'dias_vencido': 5}
        ],
        'postventa': [
            {'id': 11, 'nombre': 'Soporte Sistema K', 'cliente': 'Cliente K', 'valor': 15000, 'ejecutivo': 'María Rodríguez', 'dias_restantes': 60},
            {'id': 12, 'nombre': 'Mantenimiento App L', 'cliente': 'Cliente L', 'valor': 18000, 'ejecutivo': 'Pedro Martínez', 'dias_restantes': 30}
        ]
    }

proyectos = obtener_proyectos_ejemplo()

# Colores para cada estado
colores_estados = {
    'oportunidades': '#FF6B6B',
    'preventa': '#4ECDC4',
    'delivery': '#45B7D1',
    'cobranza': '#96CEB4',
    'postventa': '#FFEAA7'
}

# Iconos para cada estado
iconos_estados = {
    'oportunidades': '🎯',
    'preventa': '📋',
    'delivery': '🚀',
    'cobranza': '💰',
    'postventa': '🔧'
}

# Nombres bonitos para los estados
nombres_estados = {
    'oportunidades': 'OPORTUNIDADES',
    'preventa': 'PREVENTA',
    'delivery': 'DELIVERY',
    'cobranza': 'COBRANZA',
    'postventa': 'POSTVENTA'
}

# Crear las 5 columnas del Kanban
st.markdown("## 📋 Vista General del Workflow")
st.markdown("### Visualiza el flujo de proyectos entre estados")

# Contenedor principal con columnas
col1, col2, col3, col4, col5 = st.columns(5)

# Función para crear una tarjeta de proyecto mejorada
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
        <strong>{proyecto['nombre']}</strong><br>
        <span style="font-size:12px;">🏢 {proyecto['cliente']}</span><br>
        <span style="font-size:12px;">👤 {proyecto['ejecutivo']}</span><br>
        <span style="font-size:13px; font-weight:bold; color:{color};">💰 ${proyecto['valor']:,.0f}</span><br>
    """, unsafe_allow_html=True)

    if estado == 'oportunidades':
        dias = proyecto['dias_sin_actualizar']
        color_estado = "green" if dias < 3 else "orange" if dias < 7 else "red"
        st.markdown(f"<span style='font-size:12px; color:{color_estado};'>⏰ {dias} días sin actualizar</span>", unsafe_allow_html=True)
    elif estado == 'preventa':
        st.markdown(f"<span style='font-size:12px;'>⏳ {proyecto['dias_espera']} días en espera</span>", unsafe_allow_html=True)
    elif estado == 'delivery':
        st.markdown(f"<span style='font-size:12px;'>📊 {proyecto['progreso']}% completado</span>", unsafe_allow_html=True)
    elif estado == 'cobranza':
        color_estado = "red" if proyecto['dias_vencido'] > 10 else "orange"
        st.markdown(f"<span style='font-size:12px; color:{color_estado};'>⚠️ {proyecto['dias_vencido']} días vencido</span>", unsafe_allow_html=True)
    elif estado == 'postventa':
        st.markdown(f"<span style='font-size:12px;'>📅 {proyecto['dias_restantes']} días restantes</span>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# 🎯 COLUMNA 1: OPORTUNIDADES
with col1:
    estado = 'oportunidades'
    color = colores_estados[estado]

    st.markdown(f"""
    <div style='background-color: {color}; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;'>
        <h3 style='margin: 0;'>🎯 OPORTUNIDADES</h3>
        <div style='background-color: white; color: {color}; border-radius: 50%; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold;'>
            {len(proyectos[estado])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    for proyecto in proyectos[estado]:
        with st.container():
            crear_tarjeta_proyecto(proyecto, estado)

    if st.button("📊 Gestionar Oportunidades", key="btn_oportunidades", use_container_width=True):
        st.switch_page("pages/1_Oportunidades.py")

# 📋 COLUMNA 2: PREVENTA
with col2:
    estado = 'preventa'
    color = colores_estados[estado]

    st.markdown(f"""
    <div style='background-color: {color}; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;'>
        <h3 style='margin: 0;'>📋 PREVENTA</h3>
        <div style='background-color: white; color: {color}; border-radius: 50%; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold;'>
            {len(proyectos[estado])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    for proyecto in proyectos[estado]:
        with st.container():
            crear_tarjeta_proyecto(proyecto, estado)

    st.button("⏳ Próximamente", key="btn_preventa", disabled=True, use_container_width=True)

# 🚀 COLUMNA 3: DELIVERY
with col3:
    estado = 'delivery'
    color = colores_estados[estado]

    st.markdown(f"""
    <div style='background-color: {color}; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;'>
        <h3 style='margin: 0;'>🚀 DELIVERY</h3>
        <div style='background-color: white; color: {color}; border-radius: 50%; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold;'>
            {len(proyectos[estado])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    for proyecto in proyectos[estado]:
        with st.container():
            crear_tarjeta_proyecto(proyecto, estado)

    st.button("⏳ Próximamente", key="btn_delivery", disabled=True, use_container_width=True)

# 💰 COLUMNA 4: COBRANZA
with col4:
    estado = 'cobranza'
    color = colores_estados[estado]

    st.markdown(f"""
    <div style='background-color: {color}; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;'>
        <h3 style='margin: 0;'>💰 COBRANZA</h3>
        <div style='background-color: white; color: {color}; border-radius: 50%; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold;'>
            {len(proyectos[estado])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    for proyecto in proyectos[estado]:
        with st.container():
            crear_tarjeta_proyecto(proyecto, estado)

    st.button("⏳ Próximamente", key="btn_cobranza", disabled=True, use_container_width=True)

# 🔧 COLUMNA 5: POSTVENTA
with col5:
    estado = 'postventa'
    color = colores_estados[estado]

    st.markdown(f"""
    <div style='background-color: {color}; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;'>
        <h3 style='margin: 0;'>🔧 POSTVENTA</h3>
        <div style='background-color: white; color: {color}; border-radius: 50%; width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold;'>
            {len(proyectos[estado])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    for proyecto in proyectos[estado]:
        with st.container():
            crear_tarjeta_proyecto(proyecto, estado)

    st.button("⏳ Próximamente", key="btn_postventa", disabled=True, use_container_width=True)

# Resumen general
st.markdown("---")
st.markdown("## 📊 Resumen General por Estado")

resumen_cols = st.columns(5)
for i, (estado, proyectos_list) in enumerate(proyectos.items()):
    with resumen_cols[i]:
        color = colores_estados[estado]
        total_valor = sum(p['valor'] for p in proyectos_list)

        st.markdown(f"""
        <div style='text-align: center; padding: 15px; background-color: {color}20; border-radius: 10px; border: 2px solid {color};'>
            <div style='font-size: 24px;'>{iconos_estados[estado]}</div>
            <div style='font-weight: bold; color: {color};'>{nombres_estados[estado]}</div>
            <div style='font-size: 20px; font-weight: bold;'>{len(proyectos_list)}</div>
            <div style='font-size: 12px;'>proyectos</div>
            <div style='font-size: 16px; font-weight: bold; color: {color};'>${total_valor:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"*Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
st.caption("💡 **Haz clic en 'Gestionar Oportunidades' para ver el dashboard detallado**")
