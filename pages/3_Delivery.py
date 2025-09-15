# pages/3_Delivery.py
import time
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import os
import re
from models import Proyecto, Estado, Usuario, Cliente, Contacto, TiposArchivo, ProyectoArchivos
from database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from sqlalchemy import desc

# ==============================
# Configuración de la página
# ==============================
st.set_page_config(page_title="Dashboard de Delivery", layout="wide", page_icon="🚀")

# ==============================
# FUNCIONES PARA GESTIÓN DE ARCHIVOS (MISMAS QUE PREVENTA)
# ==============================
def sanitizar_nombre(texto):
    """Sanitiza nombres para usar en filesystem"""
    texto = re.sub(r'[<>:"/\\|?*]', '', texto)
    texto = texto.replace(' ', '_')
    texto = texto.upper()
    texto = texto.replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
    texto = texto.replace('Ó', 'O').replace('Ú', 'U').replace('Ñ', 'N')
    return texto

def sanitizar_nombre_archivo(nombre_archivo):
    """Sanitiza nombres de archivos para filesystem"""
    nombre, extension = os.path.splitext(nombre_archivo)
    nombre = re.sub(r'[<>:"/\\|?*]', '', nombre)
    nombre = nombre.replace(' ', '_')
    nombre = nombre.lower()
    nombre = nombre.replace('á', 'a').replace('é', 'e').replace('í', 'i')
    nombre = nombre.replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
    return f"{nombre}{extension.lower()}"

def obtener_ruta_proyecto(proyecto_id):
    """Obtiene la ruta del filesystem para un proyecto"""
    db = SessionLocal()
    try:
        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto and proyecto.cliente:
            nombre_cliente = sanitizar_nombre(proyecto.cliente.nombre)
            codigo_proyecto = proyecto.codigo_proyecto
            return f"files/proyectos/{nombre_cliente}/{codigo_proyecto}/"
        return f"files/proyectos/sin_cliente/{proyecto_id}/"
    finally:
        db.close()

def obtener_tipos_archivo():
    """Obtiene tipos de archivo desde BD"""
    db = SessionLocal()
    try:
        tipos = db.query(TiposArchivo).filter(TiposArchivo.activo == True).all()
        return tipos
    finally:
        db.close()

def verificar_archivo_duplicado(proyecto_id, tipo_archivo, nombre_archivo):
    """Verifica si ya existe un archivo con el mismo nombre"""
    ruta_base = obtener_ruta_proyecto(proyecto_id)
    nombre_final = f"{tipo_archivo}_{sanitizar_nombre_archivo(nombre_archivo)}"
    ruta_completa = os.path.join(ruta_base, nombre_final)
    
    return os.path.exists(ruta_completa), nombre_final, ruta_completa

def obtener_ultimo_archivo_por_tipo(proyecto_id, nombre_tipo_archivo):
    """Obtiene el último archivo subido de un tipo específico para un proyecto"""
    db = SessionLocal()
    try:
        tipo_archivo = db.query(TiposArchivo).filter(
            TiposArchivo.nombre == nombre_tipo_archivo,
            TiposArchivo.activo == True
        ).first()
        
        if not tipo_archivo:
            return None
        
        archivo = db.query(ProyectoArchivos).filter(
            ProyectoArchivos.proyecto_id == proyecto_id,
            ProyectoArchivos.tipo_archivo_id == tipo_archivo.id
        ).order_by(desc(ProyectoArchivos.fecha_subida)).first()
        
        return archivo
    finally:
        db.close()

def obtener_archivos_proyecto(proyecto_id):
    """Obtiene todos los archivos de un proyecto"""
    db = SessionLocal()
    try:
        archivos = db.query(ProyectoArchivos).filter(
            ProyectoArchivos.proyecto_id == proyecto_id
        ).options(
            joinedload(ProyectoArchivos.tipo_archivo),
            joinedload(ProyectoArchivos.usuario),
            joinedload(ProyectoArchivos.proyecto)
        ).all()
        return archivos
    finally:
        db.close()

def subir_archivo_proyecto(proyecto_id, tipo_archivo_id, archivo, usuario_id):
    """Sube un archivo al proyecto"""
    db = SessionLocal()
    try:
        tipo_archivo = db.query(TiposArchivo).filter(TiposArchivo.id == tipo_archivo_id).first()
        if not tipo_archivo:
            raise ValueError("Tipo de archivo no válido")
        
        ruta_base = obtener_ruta_proyecto(proyecto_id)
        os.makedirs(ruta_base, exist_ok=True)
        
        nombre_sanitizado = f"{tipo_archivo.nombre}_{sanitizar_nombre_archivo(archivo.name)}"
        ruta_completa = os.path.join(ruta_base, nombre_sanitizado)
        
        if os.path.exists(ruta_completa):
            raise FileExistsError(f"Ya existe un archivo con el nombre: {nombre_sanitizado}")
        
        with open(ruta_completa, "wb") as f:
            f.write(archivo.getvalue())
        
        nuevo_archivo = ProyectoArchivos(
            proyecto_id=proyecto_id,
            tipo_archivo_id=tipo_archivo_id,
            nombre_archivo=archivo.name,
            ruta_archivo=ruta_completa,
            subido_por_id=usuario_id
        )
        
        db.add(nuevo_archivo)
        db.commit()
        
        return nuevo_archivo
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# ==============================
# FUNCIONES ESPECÍFICAS PARA DELIVERY
# ==============================
def subir_factura_orm(proyecto_id, usuario_id, dias_pago=15):
    """Sube factura y actualiza campos de pago"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.fecha_facturacion = datetime.now()
            proyecto.dias_pago = dias_pago
            proyecto.probabilidad_cierre = 90
            proyecto.agregar_evento_historial(f"📄 Factura subida - {dias_pago} días de pago")
            proyecto.fecha_ultima_actualizacion = datetime.now()
            
            db.commit()

        db.close()
        return True
    except Exception as e:
        db.rollback()
        raise e

def mover_a_cobranza_orm(proyecto_id, usuario_id):
    """Mueve proyecto a cobranza"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.mover_a_estado(Estado.COBRANZA, usuario_id)
            proyecto.agregar_evento_historial("➡️ Movido a COBRANZA")
            db.commit()

        db.close()
        return True
    except Exception as e:
        db.rollback()
        raise e

def obtener_estado_delivery(proyecto):
    """Determina el sub-estado de delivery"""
    if proyecto.fecha_facturacion:
        dias_transcurridos = (datetime.now() - proyecto.fecha_facturacion).days
        dias_restantes_pago = proyecto.dias_pago - dias_transcurridos if proyecto.dias_pago else 15 - dias_transcurridos
        
        if dias_restantes_pago <= 0:
            return {'nombre': '⏰ PAGO VENCIDO', 'color': '#dc2626', 'icono': '⏰'}
        elif dias_restantes_pago <= 3:
            return {'nombre': '⚠️ POR VENCER', 'color': '#ea580c', 'icono': '⚠️'}
        else:
            return {'nombre': '📄 FACTURA EMITIDA', 'color': '#4ECDC4', 'icono': '📄'}
    else:
        return {'nombre': '🚀 DELIVERY ACTIVO', 'color': '#45B7D1', 'icono': '🚀'}

# ==============================
# FUNCIONES DE BASE DE DATOS (MISMAS QUE PREVENTA)
# ==============================
def cargar_proyectos_activos():
    """Carga proyectos activos con relaciones"""
    try:
        db = SessionLocal()
        proyectos = db.query(Proyecto).filter(Proyecto.activo == True).all()

        for proyecto in proyectos:
            _ = proyecto.cliente
            _ = proyecto.asignado_a
            _ = proyecto.contacto_principal

        db.close()
        return proyectos
    except Exception as e:
        st.error(f"❌ Error cargando proyectos: {str(e)}")
        return []

def actualizar_proyecto_orm(proyecto_id, datos_actualizados):
    """Actualiza un proyecto existente"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if not proyecto:
            raise ValueError("Proyecto no encontrado")

        # Actualizar campos
        proyecto.nombre = datos_actualizados['nombre']
        proyecto.descripcion = datos_actualizados['descripcion']
        proyecto.valor_estimado = datos_actualizados['valor_estimado']
        proyecto.moneda = datos_actualizados['moneda']
        proyecto.tipo_cambio_historico = datos_actualizados.get('tipo_cambio', 3.80)
        proyecto.cliente_id = datos_actualizados['cliente_id']
        proyecto.asignado_a_id = datos_actualizados['asignado_a_id']
        proyecto.fecha_ultima_actualizacion = datetime.now()

        proyecto.agregar_evento_historial(f"Editado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        db.commit()
        db.refresh(proyecto)
        db.close()

        return proyecto
    except Exception as e:
        db.rollback()
        raise e

def cargar_usuarios_activos():
    """Carga usuarios activos"""
    try:
        db = SessionLocal()
        usuarios = db.query(Usuario).filter(Usuario.activo == True).all()
        db.close()
        return usuarios
    except Exception as e:
        st.error(f"❌ Error cargando usuarios: {str(e)}")
        return []

def cargar_clientes_activos():
    """Carga clientes activos"""
    try:
        db = SessionLocal()
        clientes = db.query(Cliente).filter(Cliente.activo == True).all()
        db.close()
        return clientes
    except Exception as e:
        st.error(f"❌ Error cargando clientes: {str(e)}")
        return []

# ==============================
# INICIALIZACIÓN
# ==============================
if 'editing_project' not in st.session_state:
    st.session_state.editing_project = None

if 'modal_archivos_abierto' not in st.session_state:
    st.session_state.modal_archivos_abierto = False
if 'proyecto_archivos' not in st.session_state:
    st.session_state.proyecto_archivos = None

# ==============================
# TÍTULO Y NAVEGACIÓN
# ==============================
st.title("🚀 Dashboard de DELIVERY")
st.page_link("main_app.py", label="🔙 Volver al Workflow Principal")

# ==============================
# CARGA DE DATOS
# ==============================
proyectos_todos = cargar_proyectos_activos()
proyectos_delivery = [p for p in proyectos_todos if p.estado_actual == Estado.DELIVERY.value]

usuarios_db = cargar_usuarios_activos()
clientes_db = cargar_clientes_activos()

EJECUTIVOS_DISPONIBLES = [u.nombre for u in usuarios_db]
CLIENTES_DISPONIBLES = [c.nombre for c in clientes_db]

usuario_nombre_a_id = {u.nombre: u.id for u in usuarios_db}
cliente_nombre_a_id = {c.nombre: c.id for c in clientes_db}

tipos_archivo_db = obtener_tipos_archivo()

# ==============================
# INTERFAZ PRINCIPAL
# ==============================
# (Aquí va el resto de la estructura similar a Preventa:
#  - Sidebar con filtros
#  - KPIs 
#  - Formulario de edición
#  - Vista de tarjetas/tabla
#  - Modal de archivos)

# ... el código continuaría con la misma estructura de Preventa pero adaptado para Delivery ...
