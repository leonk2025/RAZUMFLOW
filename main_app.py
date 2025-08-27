# main_app.py
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

# Función para obtener estadísticas (simuladas por ahora)
def obtener_estadisticas_generales():
    return {
        'oportunidades': {
            'total': 15,
            'activas': 12,
            'valor_pipeline': 1250000,
            'color': '#FF6B6B',
            'icono': '🎯'
        },
        'preventa': {
            'total': 8,
            'pendientes': 3,
            'valor_contratado': 850000,
            'color': '#4ECDC4',
            'icono': '📋'
        },
        'delivery': {
            'total': 5,
            'activos': 3,
            'atrasados': 2,
            'color': '#45B7D1',
            'icono': '🚀'
        },
        'cobranza': {
            'total': 10,
            'por_cobrar': 450000,
            'vencidos': 120000,
            'color': '#96CEB4',
            'icono': '💰'
        },
        'postventa': {
            'total': 7,
            'garantias_activas': 4,
            'proximas_vencer': 2,
            'color': '#FFEAA7',
            'icono': '🔧'
        }
    }

estadisticas = obtener_estadisticas_generales()

# CSS para mejorar el diseño de las tarjetas
st.markdown("""
<style>
.estado-card {
    border: 2px solid;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s ease;
}
.estado-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}
.metric-value {
    font-size: 24px;
    font-weight: bold;
    margin: 5px 0;
}
.metric-label {
    font-size: 14px;
    color: #666;
}
</style>
""", unsafe_allow_html=True)

# Crear 5 columnas para los 5 estados
col1, col2, col3, col4, col5 = st.columns(5)

# Función para crear una tarjeta de estado
def crear_tarjeta_estado(estado, datos, habilitado=True):
    color = datos['color']
    icono = datos['icono']

    card_html = f"""
    <div class="estado-card" style="border-color: {color}; background-color: {color}10;">
        <div style="text-align: center; margin-bottom: 15px;">
            <span style="font-size: 32px;">{icono}</span>
            <h3 style="color: {color}; margin: 10px 0;">{estado.capitalize()}</h3>
        </div>
    """

    # Métricas específicas por estado
    if estado == 'oportunidades':
        card_html += f"""
            <div class="metric-value" style="color: {color};">${datos['valor_pipeline']:,.0f}</div>
            <div class="metric-label">Valor en Pipeline</div>
            <div class="metric-value" style="color: {color};">{datos['activas']}/{datos['total']}</div>
            <div class="metric-label">Oportunidades Activas</div>
        """
    elif estado == 'preventa':
        card_html += f"""
            <div class="metric-value" style="color: {color};">${datos['valor_contratado']:,.0f}</div>
            <div class="metric-label">Valor Contratado</div>
            <div class="metric-value" style="color: {color};">{datos['pendientes']} pendientes</div>
            <div class="metric-label">Por aprobar</div>
        """
    elif estado == 'delivery':
        card_html += f"""
            <div class="metric-value" style="color: {color};">{datos['activos']} activos</div>
            <div class="metric-label">Proyectos en ejecución</div>
            <div class="metric-value" style="color: {color};">{datos['atrasados']} atrasados</div>
            <div class="metric-label">Requieren atención</div>
        """
    elif estado == 'cobranza':
        card_html += f"""
            <div class="metric-value" style="color: {color};">${datos['por_cobrar']:,.0f}</div>
            <div class="metric-label">Por cobrar</div>
            <div class="metric-value" style="color: {color};">${datos['vencidos']:,.0f}</div>
            <div class="metric-label">Vencidos</div>
        """
    elif estado == 'postventa':
        card_html += f"""
            <div class="metric-value" style="color: {color};">{datos['garantias_activas']} activas</div>
            <div class="metric-label">Garantías</div>
            <div class="metric-value" style="color: {color};">{datos['proximas_vencer']} por vencer</div>
            <div class="metric-label">Próximas a vencer</div>
        """

    card_html += "</div>"
    return card_html

# 🎯 ESTADO 1: OPORTUNIDADES
with col1:
    st.markdown(crear_tarjeta_estado('oportunidades', estadisticas['oportunidades']), unsafe_allow_html=True)
    if st.button("📊 Abrir Dashboard de Oportunidades", key="btn_oportunidades", use_container_width=True):
        st.switch_page("pages/1_Oportunidades.py")

# 📋 ESTADO 2: PREVENTA
with col2:
    st.markdown(crear_tarjeta_estado('preventa', estadisticas['preventa']), unsafe_allow_html=True)
    st.button("⏳ Próximamente - Preventa", key="btn_preventa", disabled=True, use_container_width=True)

# 🚀 ESTADO 3: DELIVERY
with col3:
    st.markdown(crear_tarjeta_estado('delivery', estadisticas['delivery']), unsafe_allow_html=True)
    st.button("⏳ Próximamente - Delivery", key="btn_delivery", disabled=True, use_container_width=True)

# 💰 ESTADO 4: COBRANZA
with col4:
    st.markdown(crear_tarjeta_estado('cobranza', estadisticas['cobranza']), unsafe_allow_html=True)
    st.button("⏳ Próximamente - Cobranza", key="btn_cobranza", disabled=True, use_container_width=True)

# 🔧 ESTADO 5: POSTVENTA
with col5:
    st.markdown(crear_tarjeta_estado('postventa', estadisticas['postventa']), unsafe_allow_html=True)
    st.button("⏳ Próximamente - Postventa", key="btn_postventa", disabled=True, use_container_width=True)

# Separador
st.markdown("---")

# 📊 VISTA DE GRÁFICO GENERAL
st.markdown("## 📊 Distribución de Proyectos por Estado")

# Datos para el gráfico
data_grafico = {
    'Estado': ['Oportunidades', 'Preventa', 'Delivery', 'Cobranza', 'Postventa'],
    'Cantidad': [
        estadisticas['oportunidades']['total'],
        estadisticas['preventa']['total'],
        estadisticas['delivery']['total'],
        estadisticas['cobranza']['total'],
        estadisticas['postventa']['total']
    ],
    'Color': [
        estadisticas['oportunidades']['color'],
        estadisticas['preventa']['color'],
        estadisticas['delivery']['color'],
        estadisticas['cobranza']['color'],
        estadisticas['postventa']['color']
    ]
}

df_grafico = pd.DataFrame(data_grafico)

# Mostrar gráfico de barras
st.bar_chart(df_grafico.set_index('Estado')['Cantidad'])

# 📈 MÉTRICAS FINANCIERAS
st.markdown("## 💰 Resumen Financiero")

fin_col1, fin_col2, fin_col3, fin_col4 = st.columns(4)

with fin_col1:
    st.metric("Valor Total Pipeline", f"${estadisticas['oportunidades']['valor_pipeline']:,.0f}")

with fin_col2:
    st.metric("Valor Contratado", f"${estadisticas['preventa']['valor_contratado']:,.0f}")

with fin_col3:
    st.metric("Por Cobrar", f"${estadisticas['cobranza']['por_cobrar']:,.0f}")

with fin_col4:
    st.metric("Vencido", f"${estadisticas['cobranza']['vencidos']:,.0f}", delta="-5%")

# Footer
st.markdown("---")
st.markdown(f"*Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
st.caption("💡 **Solo el dashboard de Oportunidades está habilitado por el momento. Los demás estados se habilitarán progresivamente.**")

