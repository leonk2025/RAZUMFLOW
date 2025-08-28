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
.kanban-container {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding: 10px 0;
}
.kanban-column {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 15px;
    min-height: 600px;
    border: 2px solid #e9ecef;
    min-width: 280px;
    flex: 1;
}
.kanban-header {
    text-align: center;
    padding: 12px;
    margin-bottom: 15px;
    border-radius: 8px;
    font-weight: bold;
    color: white;
    font-size: 14px;
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
    background-color: white;
    color: #6c757d;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-left: 8px;
    font-size: 12px;
}
.empty-state {
    text-align: center;
    color: #6c757d;
    padding: 40px 20px;
    font-style: italic;
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

# Función para crear el HTML completo de una columna Kanban
def crear_columna_kanban(estado, proyectos_estado):
    color = colores_estados[estado]
    count = len(proyectos_estado)

    # Construir el HTML de las tarjetas de proyecto
    proyectos_html = ""
    for proyecto in proyectos_estado:
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

        proyectos_html += f"""
        <div class="project-card" style="border-left-color: {color};">
            <div style="font-weight: bold; margin-bottom: 5px; font-size: 14px;">{proyecto['nombre']}</div>
            <div style="color: #6c757d; font-size: 11px; margin-bottom: 3px;">🏢 {proyecto['cliente']}</div>
            <div style="color: #6c757d; font-size: 11px; margin-bottom: 3px;">👤 {proyecto['ejecutivo']}</div>
            <div style="color: #28a745; font-weight: bold; margin-bottom: 5px; font-size: 13px;">💰 ${proyecto['valor']:,.0f}</div>
            {info_extra}
        </div>
        """

    # Si no hay proyectos, mostrar estado vacío
    if count == 0:
        proyectos_html = f"""
        <div class="empty-state">
            <div style="font-size: 48px; margin-bottom: 10px;">{iconos_estados[estado]}</div>
            <div>No hay proyectos</div>
            <div style="font-size: 12px; margin-top: 5px;">en este estado</div>
        </div>
        """

    # Construir el HTML completo de la columna
    columna_html = f"""
    <div class="kanban-column">
        <div class="kanban-header" style="background-color: {color};">
            {iconos_estados[estado]} {nombres_estados[estado]}
            <span class="count-badge">{count}</span>
        </div>
        {proyectos_html}
    </div>
    """

    return columna_html

# Crear las 5 columnas del Kanban
st.markdown("## 📋 Vista General del Workflow")
st.markdown("### Visualiza el flujo de proyectos entre estados")

# Contenedor principal Kanban
kanban_html = """
<div class="kanban-container">
"""

# Agregar cada columna al contenedor
for estado, proyectos_estado in proyectos.items():
    kanban_html += crear_columna_kanban(estado, proyectos_estado)

kanban_html += """
</div>
"""

# Renderizar el Kanban completo
st.markdown(kanban_html, unsafe_allow_html=True)

# Botones de acción debajo de cada columna
st.markdown("<br>", unsafe_allow_html=True)
accion_cols = st.columns(5)

with accion_cols[0]:
    if st.button("📊 Gestionar Oportunidades", key="btn_kanban_oportunidades", use_container_width=True):
        st.switch_page("pages/1_Oportunidades.py")

with accion_cols[1]:
    st.button("⏳ Próximamente", key="btn_kanban_preventa", disabled=True, use_container_width=True)

with accion_cols[2]:
    st.button("⏳ Próximamente", key="btn_kanban_delivery", disabled=True, use_container_width=True)

with accion_cols[3]:
    st.button("⏳ Próximamente", key="btn_kanban_cobranza", disabled=True, use_container_width=True)

with accion_cols[4]:
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
        <div style="text-align: center; padding: 15px; background-color: {color}20; border-radius: 10px; border: 2px solid {color}40;">
            <div style="font-size: 28px; color: {color}; margin-bottom: 5px;">{iconos_estados[estado]}</div>
            <div style="font-weight: bold; color: {color}; font-size: 14px; margin-bottom: 8px;">{nombres_estados[estado]}</div>
            <div style="font-size: 20px; font-weight: bold; color: {color};">{len(proyectos_list)}</div>
            <div style="font-size: 11px; color: #6c757d; margin-bottom: 8px;">proyectos</div>
            <div style="font-size: 16px; color: {color}; font-weight: bold;">${total_valor:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"*Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
st.caption("💡 **Haz clic en 'Gestionar Oportunidades' para ver el dashboard detallado**")
