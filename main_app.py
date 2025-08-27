# main_app.py
import streamlit as st
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Workflow de Proyectos",
    page_icon="🏢",
    layout="wide"
)

# Título principal
st.title("🏢 Workflow de Gestión de Proyectos")
st.markdown("---")

# Simulación de datos para la vista general (luego vendrán de la BD)
def obtener_estadisticas_generales():
    return {
        'oportunidades': {'total': 15, 'activas': 12, 'valor_pipeline': 1250000},
        'preventa': {'total': 8, 'pendientes': 3, 'valor_contratado': 850000},
        'delivery': {'total': 5, 'activos': 3, 'atrasados': 2},
        'cobranza': {'total': 10, 'por_cobrar': 450000, 'vencidos': 120000},
        'postventa': {'total': 7, 'garantias_activas': 4, 'proximas_vencer': 2}
    }

estadisticas = obtener_estadisticas_generales()

# Crear 5 columnas para los 5 estados
col1, col2, col3, col4, col5 = st.columns(5)

# 🎯 ESTADO 1: OPORTUNIDADES
with col1:
    st.markdown("### 🎯 Oportunidades")
    st.markdown(f"**Total:** {estadisticas['oportunidades']['total']}")
    st.markdown(f"**Activas:** {estadisticas['oportunidades']['activas']}")
    st.markdown(f"**Valor Pipeline:** ${estadisticas['oportunidades']['valor_pipeline']:,.0f}")

    # Botón para navegar al dashboard de oportunidades
    if st.button("📊 Abrir Dashboard", key="btn_oportunidades", use_container_width=True):
        st.switch_page("pages/1_Oportunidades.py")
    st.markdown("---")

# 📋 ESTADO 2: PREVENTA (Por ahora deshabilitado)
with col2:
    st.markdown("### 📋 Preventa")
    st.markdown(f"**Total:** {estadisticas['preventa']['total']}")
    st.markdown(f"**Pendientes:** {estadisticas['preventa']['pendientes']}")
    st.markdown(f"**Valor Contratado:** ${estadisticas['preventa']['valor_contratado']:,.0f}")

    # Botón deshabilitado por ahora
    st.button("⏳ Próximamente", key="btn_preventa", disabled=True, use_container_width=True)
    st.markdown("---")

# 🚀 ESTADO 3: DELIVERY (Por ahora deshabilitado)
with col3:
    st.markdown("### 🚀 Delivery")
    st.markdown(f"**Total:** {estadisticas['delivery']['total']}")
    st.markdown(f"**Activos:** {estadisticas['delivery']['activos']}")
    st.markdown(f"**Atrasados:** {estadisticas['delivery']['atrasados']}")

    st.button("⏳ Próximamente", key="btn_delivery", disabled=True, use_container_width=True)
    st.markdown("---")

# 💰 ESTADO 4: COBRANZA (Por ahora deshabilitado)
with col4:
    st.markdown("### 💰 Cobranza")
    st.markdown(f"**Total:** {estadisticas['cobranza']['total']}")
    st.markdown(f"**Por Cobrar:** ${estadisticas['cobranza']['por_cobrar']:,.0f}")
    st.markdown(f"**Vencidos:** ${estadisticas['cobranza']['vencidos']:,.0f}")

    st.button("⏳ Próximamente", key="btn_cobranza", disabled=True, use_container_width=True)
    st.markdown("---")

# 🔧 ESTADO 5: POSTVENTA (Por ahora deshabilitado)
with col5:
    st.markdown("### 🔧 Postventa")
    st.markdown(f"**Total:** {estadisticas['postventa']['total']}")
    st.markdown(f"**Garantías Activas:** {estadisticas['postventa']['garantias_activas']}")
    st.markdown(f"**Próximas a Vencer:** {estadisticas['postventa']['proximas_vencer']}")

    st.button("⏳ Próximamente", key="btn_postventa", disabled=True, use_container_width=True)
    st.markdown("---")

# Sección inferior con información general
st.markdown("## 📈 Resumen General")
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric("Proyectos Totales", "45", "12%")

with metric_col2:
    st.metric("Valor Total", "$2.5M", "8%")

with metric_col3:
    st.metric("Tasa de Éxito", "78%", "5%")

with metric_col4:
    st.metric("Clientes Activos", "23", "3")

# Footer
st.markdown("---")
st.markdown(f"*Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
