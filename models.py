from datetime import datetime
from enum import Enum
import random

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
        self.moneda = "PEN"  # Valor por defecto
        self.tipo_cambio_historico = 3.80  # Valor por defecto
        self.asignado_a = asignado_a
        self.estado_actual = Estado.OPORTUNIDAD
        self.fecha_creacion = datetime.now()
        self.fecha_ultima_actualizacion = datetime.now()
        self.fecha_deadline_propuesta = None  # Nueva fecha opcional
        self.fecha_presentacion_cotizacion = None  # Nueva fecha manual
        self.historial = []
        self.activo = True

        # Campos adicionales opcionales
        self.codigo_convocatoria = None
        self.probabilidad_cierre = 25  # Porcentaje default

    def generar_codigo(self):
        """Genera un código único para el proyecto"""
        return f"OPP-{datetime.now().year}-{random.randint(1000, 9999)}"

    def agregar_evento_historial(self, evento):
        """Agrega un evento al historial del proyecto"""
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.historial.append(f"{timestamp} - {evento}")
        self.fecha_ultima_actualizacion = datetime.now()

    def mover_a_estado(self, nuevo_estado):
        """Mueve el proyecto a un nuevo estado"""
        if isinstance(nuevo_estado, Estado):
            estado_anterior = self.estado_actual
            self.estado_actual = nuevo_estado
            self.agregar_evento_historial(f"Estado cambiado de {estado_anterior.value} a {nuevo_estado.value}")
        else:
            raise ValueError("El nuevo estado debe ser una instancia de Estado")

    def establecer_deadline(self, fecha_deadline):
        """Establece la fecha de deadline para la propuesta"""
        if isinstance(fecha_deadline, datetime):
            self.fecha_deadline_propuesta = fecha_deadline
            self.agregar_evento_historial(f"Deadline establecido: {fecha_deadline.strftime('%d/%m/%Y %H:%M')}")
        else:
            raise ValueError("La fecha de deadline debe ser un objeto datetime")

    def registrar_presentacion_cotizacion(self):
        """Registra la fecha de presentación de cotización"""
        self.fecha_presentacion_cotizacion = datetime.now()
        self.agregar_evento_historial("Cotización presentada al cliente")

    def dias_restantes_deadline(self):
        """Calcula los días restantes para el deadline (retorna None si no hay deadline)"""
        if self.fecha_deadline_propuesta and isinstance(self.fecha_deadline_propuesta, datetime):
            diferencia = self.fecha_deadline_propuesta - datetime.now()
            return diferencia.days
        return None

    def obtener_nivel_alerta_deadline(self):
        """Determina el nivel de alerta basado en la proximidad al deadline"""
        dias_restantes = self.dias_restantes_deadline()

        if dias_restantes is None:
            return "sin_deadline"  # No hay deadline establecido

        if dias_restantes < 0:
            return "vencido"  # Deadline pasado
        elif dias_restantes == 0:
            return "critico"  # Hoy es el deadline
        elif dias_restantes <= 1:
            return "muy_urgente"  # Menos de 24 horas
        elif dias_restantes <= 3:
            return "urgente"  # 1-3 días
        elif dias_restantes <= 7:
            return "por_vencer"  # 3-7 días
        else:
            return "disponible"  # Más de 7 días

    def __str__(self):
        return f"{self.codigo_proyecto} - {self.nombre} ({self.estado_actual.value})"
