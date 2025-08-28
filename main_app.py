import streamlit as st
from datetime import datetime, timedelta

# ==============================
# Inicializar proyectos en session_state
# ==============================
if 'proyectos' not in st.session_state:
    st.session_state.proyectos = []

    # Clase Proyecto básica (compatible con Oportunidades)
    class Proyecto:
        def __init__(self, id, nombre, cliente, valor_estimado, asignado_a,
                     estado, dias_sin_actualizar=0, dias_espera=None,
                     progreso=None, dias_vencido=None, dias_restantes=None):
            self.id = id
            self.nombre = nombre
            self.cliente = cliente
            self.valor_estimado = valor_estimado
            self.asignado_a = asignado_a
            self.estado_actual = estado
            self.fecha_ultima_actualizacion = datetime.now() - timedelta(days=dias_sin_actualizar)
            self.dias_espera = dias_espera
            self.progreso = progreso
            self.dias_vencido = dias_vencido
            self.dias_restantes = dias_restantes

    # Proyectos de ejemplo
    ejemplos = {
        'OPORTUNIDAD': [
            {'id': 1, 'nombre': 'Sistema ERP Cliente A', 'cliente': 'Cliente A', 'valor': 50000, 'ejecutivo': 'Ana García', 'dias_sin_actualizar': 2},
            {'id': 2, 'nombre': 'App Móvil Retail B', 'cliente': 'Cliente B', 'valor': 35000, 'ejecutivo': 'Carlos López', 'dias_sin_actualizar': 5},
            {'id': 3, 'nombre': 'Portal Web Educativo C', 'cliente': 'Cliente C', 'valor': 42000, 'ejecutivo': 'María Rodríguez', 'dias_sin_actualizar': 1},
            {'id': 4, 'nombre': 'Cloud Migration D', 'cliente': 'Cliente D', 'valor': 68000, 'ejecutivo': 'Pedro Martínez', 'dias_sin_actualizar': 7}
        ],
        'PREVENTA': [
            {'id': 5, 'nombre': 'CRM Empresarial E', 'cliente': 'Cliente E', 'valor': 55000, 'ejecutivo': 'Ana García', 'dias_espera': 3},
            {'id': 6, 'nombre': 'E-commerce F', 'cliente': 'Cliente F', 'valor': 72000, 'ejecutivo': 'Carlos López', 'dias_espera': 1}
        ],
        'DELIVERY': [
            {'id': 7, 'nombre': 'Sistema Contabilidad G', 'cliente': 'Cliente G', 'valor': 48000, 'ejecutivo': 'María Rodríguez', 'progreso': 75},
            {'id': 8, 'nombre': 'App Logística H', 'cliente': 'Cliente H', 'valor': 61000, 'ejecutivo': 'Pedro Martínez', 'progreso': 45}
        ],
        'COBRANZA': [
            {'id': 9, 'nombre': 'Software Factory I', 'cliente': 'Cliente I', 'valor': 89000, 'ejecutivo': 'Ana García', 'dias_vencido': 15},
            {'id': 10, 'nombre': 'Consultoría Cloud J', 'cliente': 'Cliente J', 'valor': 32000, 'ejecutivo': 'Carlos López', 'dias_vencido': 5}
        ],
        'POSTVENTA': [
            {'id': 11, 'nombre': 'Soporte Sistema K', 'cliente': 'Cliente K', 'valor': 15000, 'ejecutivo': 'María Rodríguez', 'dias_restantes': 60},
            {'id': 12, 'nombre': 'Mantenimiento App L', 'cliente': 'Cliente L', 'valor': 18000, 'ejecutivo': 'Pedro Martínez', 'dias_restantes': 30}
        ]
    }

    # Cargar proyectos iniciales
    for estado, lista in ejemplos.items():
        for p in lista:
            st.session_state.proyectos.append(
                Proyecto(
                    id=p['id'],
                    nombre=p['nombre'],
                    cliente=p['cliente'],
                    valor_estimado=p['valor'],
                    asignado_a=p['ejecutivo'],
                    estado=estado,
                    dias_sin_actualizar=p.get('dias_sin_actualizar', 0),
                    dias_espera=p.get('dias_espera'),
                    progreso=p.get('progreso'),
                    dias_vencido=p.get('dias_vencido'),
                    dias_restantes=p.get('dias_restantes')
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
    'OPORTUNIDAD': '#FF6B6B',
    'PREVENTA': '#4ECDC4',
    'DELIVERY': '#45B7D1',
    'COBRANZA': '#96CEB4',
    'POSTVENTA': '#FFEAA7'
}

iconos_estados = {
    'OPORTUNIDAD': '🎯',
    'PREVENTA': '📋',
    'DELIVERY': '🚀',
    'COBRANZA': '💰',
    'POSTVENTA': '🔧'
}

nombres_estados = {
    'OPORTUNIDAD': 'OPORTUNIDADES',
    'PREVENTA': 'PREVENTA',
    'DELIVERY': 'DELIVERY',
    'COBRANZA': 'COBRANZA',
    'POSTVENTA': 'POSTVENTA'
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

    if estado == 'OPORTUNIDAD':
        color_estado = "green" if dias_sin < 3 else "orange" if dias_sin < 7 else "red"
        st.markdown(f"<span style='font-size:12px; color:{color_estado};'>⏰ {dias_sin} días sin actualizar</span>", unsafe_allow_html=True)
    elif estado == 'PREVENTA' and proyecto.dias_espera is not None:
        st.markdown(f"<span style='font-size:12px;'>⏳ {proyecto.dias_espera} días en espera</span>", unsafe_allow_html=True)
    elif estado == 'DELIVERY' and proyecto.progreso is not None:
        st.markdown(f"<span style='font-size:12px;'>📊 {proyecto.progreso}% completado</span>", unsafe_allow_html=True)
    elif estado == 'COBRANZA' and proyecto.dias_vencido is not None:
        color_estado = "red" if proyecto.dias_vencido > 10 else "orange"
        st.markdown(f"<span style='font-size:12px; color:{color_estado};'>⚠️ {proyecto.dias_vencido} días vencido</span>", unsafe_allow_html=True)
    elif estado == 'POSTVENTA' and proyecto.dias_restantes is not None:
        st.markdown(f"<span style='font-size:12px;'>📅 {proyecto.dias_restantes} días restantes</span>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# Construcción del tablero Kanban
# ==============================
st.markdown("## 📋 Vista General del Workflow")
st.markdown("### Visualiza el flujo de proyectos entre estados")

col1, col2, col3, col4, col5 = st.columns(5)
cols_map = {
    'OPORTUNIDAD': col1,
    'PREVENTA': col2,
    'DELIVERY': col3,
    'COBRANZA': col4,
    'POSTVENTA': col5
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

        if estado == 'OPORTUNIDAD':
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
