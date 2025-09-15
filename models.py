from datetime import datetime
from enum import Enum
import random
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Estado(Enum):
    OPORTUNIDAD = "OPORTUNIDAD"
    PREVENTA = "PREVENTA"
    DELIVERY = "DELIVERY"
    COBRANZA = "COBRANZA"
    POSTVENTA = "POSTVENTA"

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    telefono = Column(String(20))
    cargo = Column(String(100))
    rol = Column(String(50), default="operacion")
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)

    proyectos = relationship("Proyecto", back_populates="asignado_a")

    def __str__(self):
        return f"{self.nombre} ({self.email})"

class Cliente(Base):
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    ruc = Column(String(20), unique=True)
    industria = Column(String(100))
    tamanio_empresa = Column(String(50))
    pais = Column(String(100), default="Perú")
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)

    proyectos = relationship("Proyecto", back_populates="cliente")
    contactos = relationship("Contacto", back_populates="cliente")

    def __str__(self):
        return f"{self.nombre} ({self.ruc})"

class Contacto(Base):
    __tablename__ = 'contactos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    cargo = Column(String(100))
    email = Column(String(150))
    telefono = Column(String(20))
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)

    cliente = relationship("Cliente", back_populates="contactos")

    def __str__(self):
        return f"{self.nombre} - {self.cargo}"

class EventoHistorial(Base):
    __tablename__ = 'eventos_historial'

    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey('proyectos.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    evento = Column(String(500), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))

    proyecto = relationship("Proyecto", back_populates="historial")
    usuario = relationship("Usuario")

class Proyecto(Base):
    __tablename__ = 'proyectos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_proyecto = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(String(1000))
    valor_estimado = Column(Float, nullable=False)
    moneda = Column(String(10), default="PEN")
    tipo_cambio_historico = Column(Float, default=3.80)

    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    asignado_a_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    contacto_principal_id = Column(Integer, ForeignKey('contactos.id'))

    estado_actual = Column(String(20), default="OPORTUNIDAD")
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_ultima_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    fecha_deadline_propuesta = Column(DateTime)
    fecha_presentacion_cotizacion = Column(DateTime)
    activo = Column(Boolean, default=True)
    codigo_convocatoria = Column(String(100))
    probabilidad_cierre = Column(Integer, default=25)

    # NUEVOS CAMPOS
    fecha_ingreso_oc = Column(DateTime)  # Fecha de Ingreso OC
    plazo_entrega = Column(Integer)       # Plazo de Entrega en días
    fecha_facturacion = Column(DateTime)  # Fecha de Facturación
    dias_pago = Column(Integer, default=15)  # Días de Pago (15 por defecto)

    # Relaciones
    cliente = relationship("Cliente", back_populates="proyectos")
    asignado_a = relationship("Usuario", back_populates="proyectos")
    contacto_principal = relationship("Contacto")
    historial = relationship("EventoHistorial", back_populates="proyecto", order_by="EventoHistorial.timestamp.desc()")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.codigo_proyecto:
            self.codigo_proyecto = self.generar_codigo()

    def generar_codigo(self):
        return f"OPP-{datetime.now().year}-{random.randint(1000, 9999)}"

    def agregar_evento_historial(self, evento, usuario_id=None):
        evento_obj = EventoHistorial(
            proyecto_id=self.id,
            evento=evento,
            usuario_id=usuario_id
        )
        self.historial.append(evento_obj)
        self.fecha_ultima_actualizacion = datetime.now()

    def mover_a_estado(self, nuevo_estado, usuario_id=None):
        estado_anterior = self.estado_actual
        self.estado_actual = nuevo_estado.value if isinstance(nuevo_estado, Estado) else nuevo_estado
        self.actualizar_probabilidad_cierre()
        self.agregar_evento_historial(
            f"Estado cambiado de {estado_anterior} a {self.estado_actual}",
            usuario_id
        )

    def actualizar_probabilidad_cierre(self):
        probabilidades = {
            "OPORTUNIDAD": 25,
            "PREVENTA": 50,
            "DELIVERY": 75,
            "COBRANZA": 90,
            "POSTVENTA": 100
        }
        self.probabilidad_cierre = probabilidades.get(self.estado_actual, 25)

    def establecer_deadline(self, fecha_deadline, usuario_id=None):
        if isinstance(fecha_deadline, datetime):
            self.fecha_deadline_propuesta = fecha_deadline
            self.agregar_evento_historial(
                f"Deadline establecido: {fecha_deadline.strftime('%d/%m/%Y %H:%M')}",
                usuario_id
            )

    def obtener_nivel_alerta_deadline(self):
        if not self.fecha_deadline_propuesta:
            return 'sin_deadline'

        dias_restantes = (self.fecha_deadline_propuesta - datetime.now()).days

        if dias_restantes < 0:
            return 'vencido'
        elif dias_restantes == 0:
            return 'critico'
        elif dias_restantes <= 1:
            return 'muy_urgente'
        elif dias_restantes <= 3:
            return 'urgente'
        elif dias_restantes <= 7:
            return 'por_vencer'
        else:
            return 'disponible'

    def obtener_nivel_alerta_entrega(self):
        if not self.fecha_ingreso_oc:
            return 'sin_deadline'

        fecha_entrega = self.fecha_ingreso_oc + timedelta(days=self.plazo_entrega +1 )
        dias_restantes = (fecha_entrega - datetime.now()).days

        if dias_restantes < 0:
            return 'vencido'
        elif dias_restantes == 0:
            return 'critico'
        elif dias_restantes <= 1:
            return 'muy_urgente'
        elif dias_restantes <= 5:
            return 'urgente'
        elif dias_restantes <= 7:
            return 'por_vencer'
        else:
            return 'disponible'



    def dias_restantes_deadline(self):
        if not self.fecha_deadline_propuesta:
            return None
        return (self.fecha_deadline_propuesta - datetime.now()).days

    def dias_restantes_entrega(self):
        if not self.fecha_ingreso_oc:
            return None
        fecha_entrega = self.fecha_ingreso_oc + timedelta(days=self.plazo_entrega +1 )
        dias_restantes = (fecha_entrega - datetime.now()).days
        return dias_restantes

    def __str__(self):
        return f"{self.codigo_proyecto} - {self.nombre} ({self.estado_actual})"
