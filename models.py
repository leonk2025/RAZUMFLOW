from datetime import datetime, timedelta
import streamlit as st
from enum import Enum

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
        self.id = len(st.session_state.proyectos) + 1 if "proyectos" in st.session_state else 1
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
        numero = len([p for p in st.session_state.proyectos if p.fecha_creacion.year == anio_actual]) + 1 if "proyectos" in st.session_state else 1
        return f"P-{anio_actual}-{numero:03d}"

    def actualizar(self):
        self.fecha_ultima_actualizacion = datetime.now()

    def solicitar_revision_preventa(self):
        if "solicitudes_revision" not in st.session_state:
            st.session_state.solicitudes_revision = []
        st.session_state.solicitudes_revision.append({
            'id_proyecto': self.id,
            'solicitante': self.asignado_a,
            'fecha_solicitud': datetime.now(),
            'estado': 'PENDIENTE'
        })
        self.historial.append(f"{datetime.now()}: Solicitud de revisión para Preventa enviada")
