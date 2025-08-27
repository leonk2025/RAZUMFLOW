# main_app.py
import streamlit as st
from datetime import datetime, timedelta
import random

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

# CSS para el estilo Kanban
st.markdown("""
<style>
.kanban-column {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 15px;
    margin: 5px;
    min-height: 600px;
    border: 2px solid #e9ecef;
}
.kanban-header {
    text-align: center;
    padding: 10px;
    margin-bottom: 15px;
    border-radius: 8px;
    font-weight: bold;
    color: white;
}
.project-card {
    background: white;
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid;
    cursor: pointer;
    transition: transform 0.2s;
}
.project-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}
.count-badge {
    background-color: #6c757d;
    color: white;
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 12px;
    margin-left: 8px;
}
</style>
""", unsafe_allow_html=True)

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

# Función para crear una tarjeta de proyecto
def crear_tarjeta_proyecto(proyecto, estado):
    color = colores_estados[estado]

    # Determinar información adicional según el estado
    info_extra = ""
    if estado == 'oportunidades':
        dias = proyecto['dias_sin_actualizar']
        color_estado = "#28a745" if dias < 3 else "#ffc107" if dias < 7 else "#dc3545"
        info_extra = f"<div style='color: {color_estado}; font-size: 12px;'>⏰ {dias} días sin actualizar</div>"
    elif estado == 'preventa':
        info_extra = f"<div style='color: #6c757d; font-size: 12px;'>⏳ {proyecto['dias_espera']} días en espera</div>"
    elif estado == 'delivery':
        info_extra = f"<div style='color: #007bff; font-size: 12px;'>📊 {proyecto['progreso']}% completado</div>"
    elif estado == 'cobranza':
        color_estado = "#dc3545" if proyecto['dias_vencido'] > 10 else "#ffc107"
        info_extra = f"<div style='color: {color_estado}; font-size: 12px;'>⚠️ {proyecto['dias_vencido']} días vencido</div>"
    elif estado == 'postventa':
        info_extra = f"<div style='color: #6c757d; font-size: 12px;'>📅 {proyecto['dias_restantes']} días restantes</div>"

    tarjeta_html = f"""
    <div class="project-card" style="border-left-color: {color};">
        <div style="font-weight: bold; margin-bottom: 5px;">{proyecto['nombre']}</div>
        <div style="color: #6c757d; font-size: 12px; margin-bottom: 3px;">🏢 {proyecto['cliente']}</div>
        <div style="color: #6c757d; font-size: 12px; margin-bottom: 3px;">👤 {proyecto['ejecutivo']}</div>
        <div style="color: #28a745; font-weight: bold; margin-bottom: 5px;">💰 ${proyecto['valor']:,.0f}</div>
        {info_extra}
    </div>
    """
    return tarjeta_html

# Crear las 5 columnas del Kanban
st.markdown("## 📋 Vista General del Workflow")
st.markdown("### Arrastra visualmente los proyectos entre estados (simulación)")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    estado = 'oportunidades'
    color = colores_estados[estado]
    count = len(proyectos[estado])
    st.markdown(f"""
    <div class="kanban-header" style="background-color: {color};">
        {iconos_estados[estado]} {nombres_estados[estado]}
        <span class="count-badge">{count}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="kanban-column">', unsafe_allow_html=True)
    for proyecto in proyectos[estado]:
        st.markdown(crear_tarjeta_proyecto(proyecto, estado), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("📊 Gestionar Oportunidades", key="btn_kanban_oportunidades", use_container_width=True):
        st.switch_page("pages/1_Oportunidades.py")

with col2:
    estado = 'preventa'
    color = colores_estados[estado]
    count = len(proyectos[estado])
    st.markdown(f"""
    <div class="kanban-header" style="background-color: {color};">
        {iconos_estados[estado]} {nombres_estados[estado]}
        <span class="count-badge">{count}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="kanban-column">', unsafe_allow_html=True)
    for proyecto in proyectos[estado]:
        st.markdown(crear_tarjeta_proyecto(proyecto, estado), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.button("⏳ Próximamente", key="btn_kanban_preventa", disabled=True, use_container_width=True)

with col3:
    estado = 'delivery'
    color = colores_estados[estado]
    count = len(proyectos[estado])
    st.markdown(f"""
    <div class="kanban-header" style="background-color: {color};">
        {iconos_estados[estado]} {nombres_estados[estado]}
        <span class="count-badge">{count}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="kanban-column">', unsafe_allow_html=True)
    for proyecto in proyectos[estado]:
        st.markdown(crear_tarjeta_proyecto(proyecto, estado), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.button("⏳ Próximamente", key="btn_kanban_delivery", disabled=True, use_container_width=True)

with col4:
    estado = 'cobranza'
    color = colores_estados[estado]
    count = len(proyectos[estado])
    st.markdown(f"""
    <div class="kanban-header" style="background-color: {color};">
        {iconos_estados[estado]} {nombres_estados[estado]}
        <span class="count-badge">{count}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="kanban-column">', unsafe_allow_html=True)
    for proyecto in proyectos[estado]:
        st.markdown(crear_tarjeta_proyecto(proyecto, estado), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.button("⏳ Próximamente", key="btn_kanban_cobranza", disabled=True, use_container_width=True)

with col5:
    estado = 'postventa'
    color = colores_estados[estado]
    count = len(proyectos[estado])
    st.markdown(f"""
    <div class="kanban-header" style="background-color: {color};">
        {iconos_estados[estado]} {nombres_estados[estado]}
        <span class="count-badge">{count}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="kanban-column">', unsafe_allow_html=True)
    for proyecto in proyectos[estado]:
        st.markdown(crear_tarjeta_proyecto(proyecto, estado), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.button("⏳ Próximamente", key="btn_kanban_postventa", disabled=True, use_container_width=True)

# Resumen general
st.markdown("---")
st.markdown("## 📊 Resumen General por Estado")

resumen_cols = st.columns(5)
for i, (estado, proyectos_list) in enumerate(proyectos.items()):
    with resumen_cols[i]:
        color = colores_estados[estado]
        total_valor = sum(p['valor'] for p in proyectos_list)
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: {color}20; border-radius: 10px;">
            <div style="font-size: 24px; color: {color};">{iconos_estados[estado]}</div>
            <div style="font-weight: bold; color: {color};">{nombres_estados[estado]}</div>
            <div style="font-size: 18px; font-weight: bold;">{len(proyectos_list)}</div>
            <div style="font-size: 12px; color: #6c757d;">proyectos</div>
            <div style="font-size: 14px; color: {color}; font-weight: bold;">${total_valor:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"*Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
st.caption("💡 **Haz clic en 'Gestionar Oportunidades' para ver el dashboard detallado**")
