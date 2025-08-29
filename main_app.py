# main_app.py
import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
from enum import Enum
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# ==============================
# Configuración de la página
# ==============================
st.set_page_config(
    page_title="Sistema de Gestión de Proyectos",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# Enums y Clases
# ==============================
class Estado(Enum):
    OPORTUNIDAD = "OPORTUNIDAD"
    PREVENTA = "PREVENTA"
    DELIVERY = "DELIVERY"
    COBRANZA = "COBRANZA"
    POSTVENTA = "POSTVENTA"

class Proyecto:
    def __init__(self, nombre, cliente, valor_estimado, descripcion="", asignado_a=""):
        self.id = None
        self.codigo_proyecto = self.generar_codigo()
        self.nombre = nombre
        self.cliente = cliente
        self.descripcion = descripcion
        self.valor_estimado = valor_estimado
        self.moneda = "PEN"
        self.tipo_cambio_historico = 3.80
        self.asignado_a = asignado_a
        self.estado_actual = Estado.OPORTUNIDAD
        self.fecha_creacion = datetime.now()
        self.fecha_ultima_actualizacion = datetime.now()
        self.fecha_deadline_propuesta = None
        self.fecha_presentacion_cotizacion = None
        self.historial = []
        self.activo = True
        self.codigo_convocatoria = None
        self.probabilidad_cierre = 25

    def generar_codigo(self):
        import random
        return f"OPP-{datetime.now().year}-{random.randint(1000, 9999)}"

    def agregar_evento_historial(self, evento):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.historial.append(f"{timestamp} - {evento}")
        self.fecha_ultima_actualizacion = datetime.now()

    def establecer_deadline(self, fecha_deadline):
        if isinstance(fecha_deadline, datetime):
            self.fecha_deadline_propuesta = fecha_deadline
            self.agregar_evento_historial(f"Deadline establecido: {fecha_deadline.strftime('%d/%m/%Y %H:%M')}")

    def registrar_presentacion_cotizacion(self):
        self.fecha_presentacion_cotizacion = datetime.now()
        self.agregar_evento_historial("Cotización presentada al cliente")

    def dias_restantes_deadline(self):
        if self.fecha_deadline_propuesta and isinstance(self.fecha_deadline_propuesta, datetime):
            diferencia = self.fecha_deadline_propuesta - datetime.now()
            return diferencia.days
        return None

    def obtener_nivel_alerta_deadline(self):
        dias_restantes = self.dias_restantes_deadline()
        
        if dias_restantes is None:
            return "sin_deadline"
        if dias_restantes < 0:
            return "vencido"
        elif dias_restantes == 0:
            return "critico"
        elif dias_restantes <= 1:
            return "muy_urgente"
        elif dias_restantes <= 3:
            return "urgente"
        elif dias_restantes <= 7:
            return "por_vencer"
        else:
            return "disponible"

# ==============================
# Funciones de Base de Datos
# ==============================
DB_PATH = "proyectos.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def inicializar_db():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("PRAGMA table_info(proyectos)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'moneda' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN moneda TEXT DEFAULT 'PEN'")
    if 'tipo_cambio_historico' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN tipo_cambio_historico REAL DEFAULT 3.80")
    if 'fecha_deadline_propuesta' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN fecha_deadline_propuesta TEXT")
    if 'fecha_presentacion_cotizacion' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN fecha_presentacion_cotizacion TEXT")
    if 'activo' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN activo INTEGER DEFAULT 1")
    
    conn.commit()
    conn.close()

def cargar_proyectos_activos():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM proyectos WHERE activo = 1 OR activo IS NULL")
    rows = c.fetchall()
    conn.close()

    proyectos = []
    for row in rows:
        if len(row) == 11:
            (id_, codigo, nombre, cliente, descripcion, valor, asignado_a,
             estado, fecha_creacion, fecha_update, historial) = row
            moneda, tipo_cambio, fecha_deadline, fecha_cotizacion, activo = 'PEN', 3.80, None, None, 1
        elif len(row) == 12:
            (id_, codigo, nombre, cliente, descripcion, valor, asignado_a,
             estado, fecha_creacion, fecha_update, historial, activo) = row
            moneda, tipo_cambio, fecha_deadline, fecha_cotizacion = 'PEN', 3.80, None, None
        elif len(row) == 14:
            (id_, codigo, nombre, cliente, descripcion, valor, moneda,
             tipo_cambio, asignado_a, estado, fecha_creacion, fecha_update, historial, activo) = row
            fecha_deadline, fecha_cotizacion = None, None
        else:
            (id_, codigo, nombre, cliente, descripcion, valor, moneda,
             tipo_cambio, asignado_a, estado, fecha_creacion, fecha_update,
             fecha_deadline, fecha_cotizacion, historial, activo) = row

        p = Proyecto(nombre=nombre, cliente=cliente, valor_estimado=valor, 
                    descripcion=descripcion, asignado_a=asignado_a)
        p.id = id_
        p.codigo_proyecto = codigo
        p.estado_actual = Estado[estado]
        p.fecha_creacion = datetime.fromisoformat(fecha_creacion)
        p.fecha_ultima_actualizacion = datetime.fromisoformat(fecha_update)
        p.historial = json.loads(historial) if historial else []
        p.moneda = moneda
        p.tipo_cambio_historico = tipo_cambio
        p.fecha_deadline_propuesta = datetime.fromisoformat(fecha_deadline) if fecha_deadline else None
        p.fecha_presentacion_cotizacion = datetime.fromisoformat(fecha_cotizacion) if fecha_cotizacion else None
        proyectos.append(p)
    
    return proyectos

def convertir_moneda(valor, moneda_origen, moneda_destino, tipo_cambio=3.8):
    if moneda_origen == moneda_destino:
        return valor
    if moneda_origen == 'PEN' and moneda_destino == 'USD':
        return valor / tipo_cambio
    elif moneda_origen == 'USD' and moneda_destino == 'PEN':
        return valor * tipo_cambio
    return valor

def formatear_moneda(valor, moneda):
    if moneda == 'PEN':
        return f"S/ {valor:,.2f}"
    else:
        return f"$ {valor:,.2f}"

def get_color_riesgo(dias_sin_actualizar):
    if dias_sin_actualizar > 15:
        return "#ff4b4b"
    elif dias_sin_actualizar > 7:
        return "#ffa64b"
    else:
        return "#4caf50"

def get_estado_riesgo(dias_sin_actualizar):
    if dias_sin_actualizar > 15:
        return "Crítico"
    elif dias_sin_actualizar > 7:
        return "En Riesgo"
    else:
        return "Normal"

def get_color_deadline(nivel_alerta):
    colores = {
        'vencido': '#d32f2f',
        'critico': '#f44336',
        'muy_urgente': '#ff9800',
        'urgente': '#ffc107',
        'por_vencer': '#4caf50',
        'disponible': '#2196f3',
        'sin_deadline': '#9e9e9e'
    }
    return colores.get(nivel_alerta, '#9e9e9e')

# ==============================
# Inicialización
# ==============================
inicializar_db()
proyectos = cargar_proyectos_activos()

CLIENTES_DISPONIBLES = ['TechCorp Solutions', 'Banco Regional', 'RestauGroup SA', 
                        'LogiStock Ltda', 'IndustrialPro', 'HumanTech SA', 
                        'SalesMax Corp', 'Universidad Digital']
EJECUTIVOS_DISPONIBLES = ['Ana García', 'Carlos López', 'María Rodríguez', 
                          'Pedro Martínez', 'Sofia Herrera']
MONEDAS_DISPONIBLES = ['PEN', 'USD']

# ==============================
# Sidebar Navigation
# ==============================
with st.sidebar:
    st.title("🚀 Sales Pipeline")
    
    selected = option_menu(
        menu_title="Menú Principal",
        options=["Dashboard", "Oportunidades", "Preventa", "Delivery", "Cobranza", "Postventa", "Configuración"],
        icons=["speedometer", "lightbulb", "clipboard-check", "gear", "cash-coin", "headset", "gear"],
        default_index=0,
        styles={
            "container": {"padding": "5px", "background-color": "#f0f2f6"},
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px"},
            "nav-link-selected": {"background-color": "#2c3e50"},
        }
    )
    
    st.markdown("---")
    st.subheader("📊 Estadísticas Rápidas")
    
    total_proyectos = len(proyectos)
    st.metric("Total Proyectos", total_proyectos)
    
    valor_total = sum(p.valor_estimado for p in proyectos)
    st.metric("Valor Total", f"${valor_total:,.0f}")
    
    st.markdown("---")
    st.subheader("🎛️ Configuración")
    
    moneda_visualizacion = st.selectbox("Moneda Visualización", MONEDAS_DISPONIBLES)
    
    st.markdown("---")
    st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ==============================
# Página: Dashboard
# ==============================
if selected == "Dashboard":
    st.title("📊 Dashboard General")
    
    # KPIs principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        oportunidades = [p for p in proyectos if p.estado_actual == Estado.OPORTUNIDAD]
        st.metric("🎯 Oportunidades", len(oportunidades))
    
    with col2:
        preventa = [p for p in proyectos if p.estado_actual == Estado.PREVENTA]
        st.metric("📋 Preventa", len(preventa))
    
    with col3:
        delivery = [p for p in proyectos if p.estado_actual == Estado.DELIVERY]
        st.metric("⚡ Delivery", len(delivery))
    
    with col4:
        cobranza = [p for p in proyectos if p.estado_actual == Estado.COBANZA]
        st.metric("💰 Cobranza", len(cobranza))
    
    st.markdown("---")
    
    # Gráfico de distribución por estado
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Distribución por Estado")
        estado_counts = {estado.value: 0 for estado in Estado}
        for p in proyectos:
            estado_counts[p.estado_actual.value] += 1
        
        fig_estados = px.pie(
            values=list(estado_counts.values()),
            names=list(estado_counts.keys()),
            color=list(estado_counts.keys()),
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_estados, use_container_width=True)
    
    with col2:
        st.subheader("💰 Valor por Estado")
        estado_valores = {estado.value: 0 for estado in Estado}
        for p in proyectos:
            valor_convertido = convertir_moneda(
                p.valor_estimado, 
                getattr(p, 'moneda', 'PEN'), 
                moneda_visualizacion,
                getattr(p, 'tipo_cambio_historico', 3.80)
            )
            estado_valores[p.estado_actual.value] += valor_convertido
        
        fig_valores = px.bar(
            x=list(estado_valores.keys()),
            y=list(estado_valores.values()),
            labels={'x': 'Estado', 'y': f'Valor ({moneda_visualizacion})'},
            color=list(estado_valores.keys()),
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_valores, use_container_width=True)
    
    # Deadlines críticos
    st.markdown("---")
    st.subheader("⏰ Deadlines Críticos")
    
    proyectos_con_deadline = [p for p in proyectos if p.fecha_deadline_propuesta]
    proyectos_con_deadline.sort(key=lambda x: x.fecha_deadline_propuesta if x.fecha_deadline_propuesta else datetime.max)
    
    if proyectos_con_deadline:
        deadline_data = []
        for p in proyectos_con_deadline[:5]:  # Top 5 más críticos
            dias_restantes = p.dias_restantes_deadline()
            nivel_alerta = p.obtener_nivel_alerta_deadline()
            
            deadline_data.append({
                "Proyecto": p.nombre,
                "Cliente": p.cliente,
                "Deadline": p.fecha_deadline_propuesta.strftime('%d/%m/%Y %H:%M'),
                "Días Restantes": dias_restantes if dias_restantes is not None else "N/A",
                "Estado": nivel_alerta.capitalize(),
                "Color": get_color_deadline(nivel_alerta)
            })
        
        df_deadlines = pd.DataFrame(deadline_data)
        
        # Aplicar colores a la tabla
        def color_row(row):
            return [f'background-color: {row["Color"]}; color: white; font-weight: bold'] * len(row)
        
        st.dataframe(
            df_deadlines.style.apply(color_row, axis=1),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No hay proyectos con deadlines establecidos.")

# ==============================
# Páginas de Estados
# ==============================
elif selected == "Oportunidades":
    st.switch_page("pages/1_Oportunidades.py")

elif selected == "Preventa":
    st.title("📋 Pipeline de Preventa")
    proyectos_preventa = [p for p in proyectos if p.estado_actual == Estado.PREVENTA]
    
    if not proyectos_preventa:
        st.info("No hay proyectos en etapa de Preventa.")
    else:
        st.subheader(f"Proyectos en Preventa ({len(proyectos_preventa)})")
        
        for proyecto in proyectos_preventa:
            with st.expander(f"{proyecto.codigo_proyecto} - {proyecto.nombre}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Cliente:** {proyecto.cliente}")
                    st.write(f"**Valor:** {formatear_moneda(proyecto.valor_estimado, proyecto.moneda)}")
                    st.write(f"**Asignado a:** {proyecto.asignado_a}")
                
                with col2:
                    if proyecto.fecha_deadline_propuesta:
                        dias_restantes = proyecto.dias_restantes_deadline()
                        nivel_alerta = proyecto.obtener_nivel_alerta_deadline()
                        st.write(f"**Deadline:** {proyecto.fecha_deadline_propuesta.strftime('%d/%m/%Y %H:%M')}")
                        st.write(f"**Días restantes:** {dias_restantes}")
                        st.markdown(f"<span style='color: {get_color_deadline(nivel_alerta)}; font-weight: bold;'>{nivel_alerta.capitalize()}</span>", unsafe_allow_html=True)
                
                st.write(f"**Descripción:** {proyecto.descripcion}")

elif selected in ["Delivery", "Cobranza", "Postventa"]:
    estado_map = {
        "Delivery": Estado.DELIVERY,
        "Cobranza": Estado.COBRANZA,
        "Postventa": Estado.POSTVENTA
    }
    
    estado_actual = estado_map[selected]
    st.title(f"📊 {selected}")
    
    proyectos_estado = [p for p in proyectos if p.estado_actual == estado_actual]
    
    if not proyectos_estado:
        st.info(f"No hay proyectos en etapa de {selected}.")
    else:
        st.subheader(f"Proyectos en {selected} ({len(proyectos_estado)})")
        
        for proyecto in proyectos_estado:
            with st.expander(f"{proyecto.codigo_proyecto} - {proyecto.nombre}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Cliente:** {proyecto.cliente}")
                    st.write(f"**Valor:** {formatear_moneda(proyecto.valor_estimado, proyecto.moneda)}")
                    st.write(f"**Asignado a:** {proyecto.asignado_a}")
                
                with col2:
                    st.write(f"**Fecha creación:** {proyecto.fecha_creacion.strftime('%d/%m/%Y')}")
                    st.write(f"**Última actualización:** {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y')}")
                
                st.write(f"**Descripción:** {proyecto.descripcion}")

# ==============================
# Página: Configuración
# ==============================
elif selected == "Configuración":
    st.title("⚙️ Configuración")
    
    st.subheader("Base de Datos")
    if st.button("🔄 Reinicializar Base de Datos", type="secondary"):
        try:
            import crear_proyectos_db2
            crear_proyectos_db2.crear_proyectos_db()
            st.success("Base de datos reinicializada correctamente")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    st.subheader("Estadísticas de la BD")
    conn = get_connection()
    
    # Contar proyectos por estado
    query_estados = """
    SELECT estado_actual, COUNT(*) 
    FROM proyectos 
    WHERE activo = 1 
    GROUP BY estado_actual
    """
    df_estados = pd.read_sql_query(query_estados, conn)
    st.write("**Proyectos por estado:**")
    st.dataframe(df_estados, hide_index=True)
    
    # Proyectos con deadlines
    query_deadlines = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN fecha_deadline_propuesta IS NOT NULL THEN 1 ELSE 0 END) as con_deadline,
        SUM(CASE WHEN fecha_deadline_propuesta IS NULL THEN 1 ELSE 0 END) as sin_deadline,
        SUM(CASE WHEN fecha_deadline_propuesta < datetime('now') THEN 1 ELSE 0 END) as deadlines_vencidos
    FROM proyectos 
    WHERE activo = 1
    """
    df_deadlines = pd.read_sql_query(query_deadlines, conn)
    st.write("**Estadísticas de deadlines:**")
    st.dataframe(df_deadlines, hide_index=True)
    
    conn.close()

# ==============================
# Footer
# ==============================
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("**📞 Contacto**")
    st.markdown("✉️ info@empresa.com")
    st.markdown("📱 +51 123 456 789")

with footer_col2:
    st.markdown("**🚀 Recursos**")
    st.markdown("[📚 Documentación](#)")
    st.markdown("[🎓 Tutoriales](#)")
    st.markdown("[💬 Soporte](#)")

with footer_col3:
    st.markdown("**📊 Sistema**")
    st.markdown(f"Proyectos activos: {len(proyectos)}")
    st.markdown(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.markdown("v2.0 - Sistema de Doble Moneda")

st.markdown("---")
st.caption("© 2024 Sistema de Gestión de Proyectos - Todos los derechos reservados")
