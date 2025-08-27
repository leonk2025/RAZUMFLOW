# main_app.py
import streamlit as st
from datetime import datetime
import pandas as pd
from streamlit.components.v1 import html

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

# Función para crear una tarjeta de estado con Streamlit nativo
def crear_tarjeta_estado_streamlit(estado, datos):
    color = datos['color']
    icono = datos['icono']

    # Crear un container con estilo
    with st.container():
        # Usar markdown con HTML para el estilo del container
        st.markdown(f"""
        <div style="
            border: 2px solid {color};
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background-color: {color}10;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
        """, unsafe_allow_html=True)

        # Contenido de la tarjeta
        col_icon, col_text = st.columns([1, 3])
        with col_icon:
            st.markdown(f"<h1 style='text-align: center; color: {color};'>{icono}</h1>", unsafe_allow_html=True)
        with col_text:
            st.markdown(f"<h3 style='color: {color}; margin: 0;'>{estado.capitalize()}</h3>", unsafe_allow_html=True)

        # Separador
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

        # Métricas específicas por estado
        if estado == 'oportunidades':
            st.metric("Valor Pipeline", f"${datos['valor_pipeline']:,.0f}")
            st.metric("Oportunidades", f"{datos['activas']}/{datos['total']}")

        elif estado == 'preventa':
            st.metric("Valor Contratado", f"${datos['valor_contratado']:,.0f}")
            st.metric("Pendientes", f"{datos['pendientes']}")

        elif estado == 'delivery':
            st.metric("Proyectos Activos", f"{datos['activos']}")
            st.metric("Atrasados", f"{datos['atrasados']}")

        elif estado == 'cobranza':
            st.metric("Por Cobrar", f"${datos['por_cobrar']:,.0f}")
            st.metric("Vencidos", f"${datos['vencidos']:,.0f}")

        elif estado == 'postventa':
            st.metric("Garantías Activas", f"{datos['garantias_activas']}")
            st.metric("Próx. a Vencer", f"{datos['proximas_vencer']}")

        # Cerrar el div
        st.markdown("</div>", unsafe_allow_html=True)

# Crear 5 columnas para los 5 estados
col1, col2, col3, col4, col5 = st.columns(5)

# 🎯 ESTADO 1: OPORTUNIDADES
with col1:
    crear_tarjeta_estado_streamlit('oportunidades', estadisticas['oportunidades'])
    if st.button("📊 Abrir Dashboard", key="btn_oportunidades", use_container_width=True):
        st.switch_page("pages/1_Oportunidades.py")

# 📋 ESTADO 2: PREVENTA
with col2:
    crear_tarjeta_estado_streamlit('preventa', estadisticas['preventa'])
    st.button("⏳ Próximamente", key="btn_preventa", disabled=True, use_container_width=True)

# 🚀 ESTADO 3: DELIVERY
with col3:
    crear_tarjeta_estado_streamlit('delivery', estadisticas['delivery'])
    st.button("⏳ Próximamente", key="btn_delivery", disabled=True, use_container_width=True)

# 💰 ESTADO 4: COBRANZA
with col4:
    crear_tarjeta_estado_streamlit('cobranza', estadisticas['cobranza'])
    st.button("⏳ Próximamente", key="btn_cobranza", disabled=True, use_container_width=True)

# 🔧 ESTADO 5: POSTVENTA
with col5:
    crear_tarjeta_estado_streamlit('postventa', estadisticas['postventa'])
    st.button("⏳ Próximamente", key="btn_postventa", disabled=True, use_container_width=True)

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
