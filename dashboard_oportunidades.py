# dashboard_oportunidades.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
from enum import Enum

# Simulación de una base de datos simple en memoria
if 'proyectos' not in st.session_state:
    st.session_state.proyectos = []
if 'clientes' not in st.session_state:
    st.session_state.clientes = ['Cliente A', 'Cliente B', 'Cliente C', 'Cliente D']
if 'ejecutivos' not in st.session_state:
    st.session_state.ejecutivos = ['Ana García', 'Carlos López', 'María Rodríguez', 'Pedro Martínez']
if 'solicitudes_revision' not in st.session_state:
    st.session_state.solicitudes_revision = []

class Estado(Enum):
    OPORTUNIDAD = "OPORTUNIDAD"
    PREVENTA = "PREVENTA"
    DELIVERY = "DELIVERY"
    COBRANZA = "COBRANZA"
    POSTVENTA = "POSTVENTA"
    CERRADO_PERDIDO = "CERRADO_PERDIDO"
    CERRADO_EXITOSO = "CERRADO_EXITOSO"

class Proyecto:
    def __init__(self, nombre, cliente, valor_estimado, descripcion, asignado_a, codigo_convocatoria=None):
        self.id = len(st.session_state.proyectos) + 1
        self.codigo_proyecto = self._generar_codigo_proyecto()
        self.nombre = nombre
        self.cliente = cliente
        self.descripcion = descripcion
        self.valor_estimado = valor_estimado
        self.valor_contratado = 0
        self.asignado_a = asignado_a
        self.estado_actual = Estado.OPORTUNIDAD
        self.probabilidad_cierre = 20
        self.codigo_convocatoria = codigo_convocatoria
        self.fecha_creacion = datetime.now()
        self.fecha_ultima_actualizacion = datetime.now()
        self.fecha_proximo_contacto = datetime.now() + timedelta(days=3)
        self.historial = [f"{datetime.now()}: Oportunidad creada por {asignado_a}"]

    def _generar_codigo_proyecto(self):
        anio_actual = datetime.now().year
        numero = len([p for p in st.session_state.proyectos if p.fecha_creacion.year == anio_actual]) + 1
        return f"P-{anio_actual}-{numero:03d}"

    def actualizar(self):
        self.fecha_ultima_actualizacion = datetime.now()

    def solicitar_revision_preventa(self):
        st.session_state.solicitudes_revision.append({
            'id_proyecto': self.id,
            'solicitante': self.asignado_a,
            'fecha_solicitud': datetime.now(),
            'estado': 'PENDIENTE'
        })
        self.historial.append(f"{datetime.now()}: Solicitud de revisión para Preventa enviada")

# Configuración de la página
st.set_page_config(page_title="Dashboard de Oportunidades", layout="wide", page_icon="📊")
st.title("📊 Dashboard de OPORTUNIDADES")

# Sidebar para filtros
with st.sidebar:
    st.header("Filtros")
    filtro_ejecutivo = st.selectbox("Ejecutivo", ["Todos"] + st.session_state.ejecutivos)
    filtro_riesgo = st.selectbox("Estado de Riesgo", ["Todos", "Normal", "En Riesgo", "Crítico"])
    st.divider()
    st.header("Estadísticas Rápidas")
    total_oportunidades = len(st.session_state.proyectos)
    st.metric("Total Oportunidades", total_oportunidades)

# Sección 1: KPIs y Métricas
col1, col2, col3, col4 = st.columns(4)
with col1:
    valor_pipeline = sum(p.valor_estimado * (p.probabilidad_cierre / 100) for p in st.session_state.proyectos)
    st.metric("Valor del Pipeline", f"${valor_pipeline:,.0f}")
with col2:
    total_valor = sum(p.valor_estimado for p in st.session_state.proyectos)
    st.metric("Valor Total Estimado", f"${total_valor:,.0f}")
with col3:
    avg_valor = total_valor / total_oportunidades if total_oportunidades > 0 else 0
    st.metric("Valor Promedio", f"${avg_valor:,.0f}")
with col4:
    oportunidades_riesgo = len([p for p in st.session_state.proyectos if (datetime.now() - p.fecha_ultima_actualizacion).days > 7])
    st.metric("Oportunidades en Riesgo", oportunidades_riesgo)

# Sección 2: Formulario para crear nueva oportunidad
with st.expander("➕ Crear Nueva Oportunidad", expanded=False):
    with st.form("form_nueva_oportunidad"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre de la Oportunidad*")
            cliente = st.selectbox("Cliente*", st.session_state.clientes)
            valor_estimado = st.number_input("Valor Estimado (USD)*", min_value=0, value=10000)
        with col2:
            descripcion = st.text_area("Descripción Breve*")
            asignado_a = st.selectbox("Asignar a*", st.session_state.ejecutivos)
            codigo_convocatoria = st.text_input("Código de Convocatoria (Opcional)")

        submitted = st.form_submit_button("Crear Oportunidad")
        if submitted:
            if nombre and cliente and descripcion:
                nuevo_proyecto = Proyecto(
                    nombre=nombre,
                    cliente=cliente,
                    valor_estimado=valor_estimado,
                    descripcion=descripcion,
                    asignado_a=asignado_a,
                    codigo_convocatoria=codigo_convocatoria if codigo_convocatoria else None
                )
                st.session_state.proyectos.append(nuevo_proyecto)
                st.success(f"✅ Oportunidad creada exitosamente! Código: {nuevo_proyecto.codigo_proyecto}")
            else:
                st.error("Por favor complete todos los campos obligatorios (*)")

# Sección 3: Lista de Oportunidades
st.header("📋 Lista de Oportunidades")

# Aplicar filtros
proyectos_filtrados = st.session_state.proyectos.copy()

if filtro_ejecutivo != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados if p.asignado_a == filtro_ejecutivo]

if filtro_riesgo != "Todos":
    dias_limite = 15 if filtro_riesgo == "Crítico" else 7 if filtro_riesgo == "En Riesgo" else 0
    proyectos_filtrados = [p for p in proyectos_filtrados
                          if (datetime.now() - p.fecha_ultima_actualizacion).days >= dias_limite]

# Mostrar tabla de oportunidades
if proyectos_filtrados:
    data = []
    for proyecto in proyectos_filtrados:
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
        if dias_sin_actualizar > 15:
            estado_riesgo = "Crítico"
        elif dias_sin_actualizar > 7:
            estado_riesgo = "En Riesgo"
        else:
            estado_riesgo = "Normal"

        data.append({
            "Código": proyecto.codigo_proyecto,
            "Nombre": proyecto.nombre,
            "Cliente": proyecto.cliente,
            "Valor Estimado": f"${proyecto.valor_estimado:,.0f}",
            "Probabilidad": f"{proyecto.probabilidad_cierre}%",
            "Asignado a": proyecto.asignado_a,
            "Próximo Contacto": proyecto.fecha_proximo_contacto.strftime("%d/%m/%Y"),
            "Días sin Actualizar": dias_sin_actualizar,
            "Riesgo": estado_riesgo,
            "Acciones": proyecto.id  # Para identificar el proyecto en acciones
        })

    df = pd.DataFrame(data)

    # Función para aplicar estilo de color según el riesgo
    def color_risko(val):
        color = 'red' if val == 'Crítico' else 'orange' if val == 'En Riesgo' else 'green'
        return f'color: {color}; font-weight: bold'

    styled_df = df.style.applymap(color_risko, subset=['Riesgo'])
    st.dataframe(styled_df, hide_index=True, use_container_width=True)

    # Botones de acción para cada proyecto
    for proyecto in proyectos_filtrados:
        with st.expander(f"Acciones para {proyecto.codigo_proyecto}", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📞 Registrar Contacto", key=f"contact_{proyecto.id}"):
                    proyecto.fecha_ultima_actualizacion = datetime.now()
                    proyecto.fecha_proximo_contacto = datetime.now() + timedelta(days=random.randint(2, 7))
                    proyecto.historial.append(f"{datetime.now()}: Contacto registrado con el cliente")
                    st.success("Contacto registrado exitosamente!")
            with col2:
                if st.button(f"📤 Solicitar Preventa", key=f"prev_{proyecto.id}"):
                    proyecto.solicitar_revision_preventa()
                    st.success("Solicitud de revisión enviada a gerencia!")
            with col3:
                if st.button(f"❌ Cerrar Oportunidad", key=f"close_{proyecto.id}"):
                    proyecto.estado_actual = Estado.CERRADO_PERDIDO
                    proyecto.historial.append(f"{datetime.now()}: Oportunidad cerrada como perdida")
                    st.success("Oportunidad cerrada exitosamente!")
else:
    st.info("No hay oportunidades que coincidan con los filtros aplicados.")

# Sección 4: Solicitudes de Revisión (solo visible para gerentes)
if st.session_state.solicitudes_revision:
    st.header("📨 Solicitudes de Revisión para Preventa")
    for solicitud in st.session_state.solicitudes_revision:
        proyecto = next((p for p in st.session_state.proyectos if p.id == solicitud['id_proyecto']), None)
        if proyecto:
            with st.expander(f"Solicitud de {solicitud['solicitante']} - {proyecto.codigo_proyecto}"):
                st.write(f"**Proyecto:** {proyecto.nombre}")
                st.write(f"**Cliente:** {proyecto.cliente}")
                st.write(f"**Valor Estimado:** ${proyecto.valor_estimado:,.0f}")
                st.write(f"**Solicitado el:** {solicitud['fecha_solicitud'].strftime('%d/%m/%Y %H:%M')}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Aprobar", key=f"approve_{solicitud['id_proyecto']}"):
                        proyecto.estado_actual = Estado.PREVENTA
                        proyecto.probabilidad_cierre = 70
                        solicitud['estado'] = 'APROBADO'
                        st.success("Oportunidad movida a PREVENTA!")
                with col2:
                    if st.button(f"❌ Rechazar", key=f"reject_{solicitud['id_proyecto']}"):
                        solicitud['estado'] = 'RECHAZADO'
                        st.success("Solicitud rechazada!")
