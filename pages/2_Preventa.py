# pages/2_Preventa.py
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

# ==============================
# Configuración de la página
# ==============================
st.set_page_config(page_title="Dashboard de Preventa", layout="wide", page_icon="📊")

# ==============================
# FUNCIONES PARA GESTIÓN DE ARCHIVOS
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

def obtener_ultima_oc(proyecto_id):
    """Obtiene la última Orden de Compra subida para un proyecto"""
    db = SessionLocal()
    try:
        # Buscar archivos de tipo OC (asumiendo que el ID para OC es 2)
        oc = db.query(ProyectoArchivos).filter(
            ProyectoArchivos.proyecto_id == proyecto_id,
            ProyectoArchivos.tipo_archivo_id == 2  # ID para OC
        ).order_by(ProyectoArchivos.fecha_subida.desc()).first()
        
        return oc
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
            joinedload(ProyectoArchivos.usuario)
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
# Funciones de Base de Datos ORM
# ==============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def cargar_proyectos_activos():
    """Carga solo proyectos activos con todas las relaciones usando ORM"""
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

def cargar_historial_proyecto(proyecto_id):
    """Carga el historial de eventos para un proyecto específico"""
    try:
        db = SessionLocal()
        historial = db.execute(
            text("SELECT timestamp, evento FROM eventos_historial WHERE proyecto_id = :proyecto_id ORDER BY timestamp DESC LIMIT 3"),
            {"proyecto_id": proyecto_id}
        ).fetchall()
        db.close()
        return historial
    except Exception as e:
        st.error(f"Error cargando historial: {str(e)}")
        return []

def actualizar_proyecto_orm(proyecto_id, datos_actualizados):
    """Actualiza un proyecto existente usando ORM"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if not proyecto:
            raise ValueError("Proyecto no encontrado")

        proyecto.nombre = datos_actualizados['nombre']
        proyecto.descripcion = datos_actualizados['descripcion']
        proyecto.valor_estimado = datos_actualizados['valor_estimado']
        proyecto.moneda = datos_actualizados['moneda']
        proyecto.tipo_cambio_historico = datos_actualizados.get('tipo_cambio', 3.80)
        proyecto.cliente_id = datos_actualizados['cliente_id']
        proyecto.asignado_a_id = datos_actualizados['asignado_a_id']
        proyecto.fecha_deadline_propuesta = datos_actualizados.get('fecha_deadline')
        proyecto.codigo_convocatoria = datos_actualizados.get('codigo_convocatoria')
        proyecto.fecha_ultima_actualizacion = datetime.now()

        proyecto.agregar_evento_historial(f"Editado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        db.commit()
        db.refresh(proyecto)
        db.close()

        return proyecto
    except Exception as e:
        db.rollback()
        raise e

def eliminar_proyecto_soft_orm(proyecto_id):
    """Soft delete usando ORM"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.activo = False
            proyecto.fecha_ultima_actualizacion = datetime.now()
            proyecto.agregar_evento_historial(f"Eliminado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")

            db.commit()

        db.close()
        return True
    except Exception as e:
        db.rollback()
        raise e

def registrar_contacto_orm(proyecto_id):
    """Registra un contacto usando ORM"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.agregar_evento_historial(f"Contacto registrado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            proyecto.fecha_ultima_actualizacion = datetime.now()

            db.commit()

        db.close()
        return datetime.now() + timedelta(days=random.randint(2, 7))
    except Exception as e:
        db.rollback()
        raise e

def marcar_propuesta_presentada_orm(proyecto_id):
    """Marca la propuesta como presentada y actualiza probabilidad al 50%"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.fecha_presentacion_cotizacion = datetime.now()
            proyecto.probabilidad_cierre = 50
            proyecto.agregar_evento_historial("✅ Propuesta presentada al cliente - Probabilidad 50%")
            proyecto.fecha_ultima_actualizacion = datetime.now()

            db.commit()

        db.close()
        return True
    except Exception as e:
        db.rollback()
        raise e

def subir_orden_compra_orm(proyecto_id, usuario_id):
    """Sube orden de compra y avanza automáticamente a DELIVERY si es exitoso"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.probabilidad_cierre = 75
            proyecto.agregar_evento_historial("🎉 Orden de Compra recibida - Probabilidad 75%")
            proyecto.fecha_ultima_actualizacion = datetime.now()
            
            # Auto-avance a DELIVERY
            proyecto.mover_a_estado(Estado.DELIVERY, usuario_id)
            
            db.commit()

        db.close()
        return True
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

def cargar_contactos_activos():
    """Carga contactos activos"""
    try:
        db = SessionLocal()
        contactos = db.query(Contacto).all()
        db.close()
        return contactos
    except Exception as e:
        st.error(f"❌ Error cargando contactos: {str(e)}")
        return []

# ==============================
# Funciones de conversión de moneda
# ==============================
def convertir_moneda(valor, moneda_origen, moneda_destino, tipo_cambio=3.8):
    """Convierte un valor entre PEN and USD"""
    if moneda_origen == moneda_destino:
        return valor

    if moneda_origen == 'PEN' and moneda_destino == 'USD':
        return valor / tipo_cambio
    elif moneda_origen == 'USD' and moneda_destino == 'PEN':
        return valor * tipo_cambio
    else:
        return valor

def formatear_moneda(valor, moneda):
    """Formatea un valor numérico según la moneda"""
    if moneda == 'PEN':
        return f"S/ {valor:,.2f}"
    else:
        return f"$ {valor:,.2f}"

# ==============================
# Funciones para deadlines y criticidad
# ==============================
def obtener_estilo_deadline(nivel_alerta):
    """Devuelve estilo CSS según el nivel de alerta del deadline"""
    estilos = {
        'vencido': {'color': '#666666', 'icono': '☠️', 'fondo': '#F5F5F5'},
        'critico': {'color': '#dc2626', 'icono': '🔥', 'fondo': '#fef2f2'},
        'muy_urgente': {'color': '#ea580c', 'icono': '⏰', 'fondo': '#fff7ed'},
        'urgente': {'color': '#ea580c', 'icono': '⏳', 'fondo': '#fff7ed'},
        'por_vencer': {'color': '#ca8a04', 'icono': '📅', 'fondo': '#fefce8'},
        'disponible': {'color': '#16a34a', 'icono': '✅', 'fondo': '#f0fdf4'},
        'sin_deadline': {'color': '#16a34a', 'icono': '📌', 'fondo': '#f0fdf4'}
    }
    return estilos.get(nivel_alerta, estilos['sin_deadline'])

def calcular_criticidad_deadline(proyecto):
    """Calcula la criticidad basada en el deadline"""
    # Si ya se presentó propuesta, el deadline ya no es relevante
    if proyecto.fecha_presentacion_cotizacion:
        return 'propuesta_presentada'
    
    if not proyecto.fecha_deadline_propuesta:
        return 'sin_deadline'

    dias_restantes = (proyecto.fecha_deadline_propuesta - datetime.now()).days

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

def get_color_riesgo(dias_sin_actualizar):
    """Determina el color según la criticidad por inactividad"""
    if dias_sin_actualizar > 15:
        return "#ff4b4b"
    elif dias_sin_actualizar > 7:
        return "#ffa64b"
    else:
        return "#4caf50"

def get_estado_riesgo(dias_sin_actualizar):
    """Determina el estado textual del riesgo por inactividad"""
    if dias_sin_actualizar > 15:
        return "Crítico"
    elif dias_sin_actualizar > 7:
        return "En Riesgo"
    else:
        return "Normal"

def obtener_estado_preventa(proyecto):
    """Determina el sub-estado de preventa basado en probabilidad_cierre"""
    if proyecto.probabilidad_cierre >= 75:
        return {'nombre': '🎉 OC FIRMADA', 'color': '#16a34a', 'icono': '🎉'}
    elif proyecto.probabilidad_cierre >= 50:
        return {'nombre': '📤 PROPUESTA ENTREGADA', 'color': '#3b82f6', 'icono': '📤'}
    else:
        return {'nombre': '📋 PREVENTA ACTIVA', 'color': '#f59e0b', 'icono': '📋'}

# ==============================
# Inicialización
# ==============================
EJECUTIVOS_DISPONIBLES = []
CLIENTES_DISPONIBLES = []
MONEDAS_DISPONIBLES = ['PEN', 'USD']

if 'editing_project' not in st.session_state:
    st.session_state.editing_project = None

if 'modal_archivos_abierto' not in st.session_state:
    st.session_state.modal_archivos_abierto = False
if 'proyecto_archivos' not in st.session_state:
    st.session_state.proyecto_archivos = None

# ==============================
# Título y navegación
# ==============================
st.title("📊 Dashboard de PREVENTA")
st.page_link("main_app.py", label="🔙 Volver al Workflow Principal")

# ==============================
# Cargar datos desde ORM
# ==============================
proyectos_todos = cargar_proyectos_activos()
proyectos_preventa = [p for p in proyectos_todos if p.estado_actual == Estado.PREVENTA.value]

# Cargar datos para selects
usuarios_db = cargar_usuarios_activos()
clientes_db = cargar_clientes_activos()
contactos_db = cargar_contactos_activos()

EJECUTIVOS_DISPONIBLES = [u.nombre for u in usuarios_db]
CLIENTES_DISPONIBLES = [c.nombre for c in clientes_db]

usuario_nombre_a_id = {u.nombre: u.id for u in usuarios_db}
cliente_nombre_a_id = {c.nombre: c.id for c in clientes_db}

tipos_archivo_db = obtener_tipos_archivo()

# ==============================
# MODAL PARA GESTIÓN DE ARCHIVOS
# ==============================
if st.session_state.modal_archivos_abierto and st.session_state.proyecto_archivos:
    with st.sidebar:
        st.header("📁 Gestión de Archivos")
        st.write(f"Proyecto: **{st.session_state.proyecto_archivos.codigo_proyecto}**")
        
        with st.expander("📤 Subir nuevo archivo", expanded=True):
            archivo_subir = st.file_uploader("Seleccionar archivo", type=['pdf', 'docx', 'xlsx', 'jpg', 'png'])
            tipo_seleccionado = st.selectbox("Tipo de archivo", 
                                           options=[(t.id, t.nombre) for t in tipos_archivo_db],
                                           format_func=lambda x: x[1])
            
            if archivo_subir and st.button("Subir archivo"):
                try:
                    subir_archivo_proyecto(
                        st.session_state.proyecto_archivos.id,
                        tipo_seleccionado[0],
                        archivo_subir,
                        1  # ID del usuario actual
                    )
                    st.success("✅ Archivo subido correctamente")
                    time.sleep(1)
                    st.rerun()
                except FileExistsError as e:
                    st.error(f"❌ {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error al subir archivo: {str(e)}")
        
        st.divider()
        st.subheader("Archivos del proyecto")
        archivos = obtener_archivos_proyecto(st.session_state.proyecto_archivos.id)
        
        if not archivos:
            st.info("📝 No hay archivos subidos para este proyecto")
        else:
            for archivo in archivos:
                with st.expander(f"{archivo.tipo_archivo.nombre}: {archivo.nombre_archivo}"):
                    st.write(f"**Subido por:** {archivo.usuario.nombre if archivo.usuario else 'N/A'}")
                    st.write(f"**Fecha:** {archivo.fecha_subida.strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"**Tamaño:** {os.path.getsize(archivo.ruta_archivo) if os.path.exists(archivo.ruta_archivo) else 'N/A'} bytes")
                    
                    if os.path.exists(archivo.ruta_archivo):
                        with open(archivo.ruta_archivo, "rb") as f:
                            st.download_button(
                                "⬇️ Descargar",
                                f.read(),
                                archivo.nombre_archivo,
                                key=f"download_{archivo.id}"
                            )
                    else:
                        st.warning("⚠️ Archivo no encontrado en el filesystem")
        
        if st.button("Cerrar gestión de archivos"):
            st.session_state.modal_archivos_abierto = False
            st.rerun()

# ==============================
# Sidebar para filtros y vista 
# ==============================
with st.sidebar:
    st.header("🎛️ Opciones de Visualización")
    vista_modo = st.radio("Modo de vista:", ["Tarjetas", "Tabla"])

    moneda_visualizacion = st.selectbox("Moneda para visualización:", MONEDAS_DISPONIBLES)

    st.header("🔍 Filtros")
    filtro_ejecutivo = st.selectbox("Ejecutivo", ["Todos"] + EJECUTIVOS_DISPONIBLES)
    filtro_cliente = st.selectbox("Cliente", ["Todos"] + CLIENTES_DISPONIBLES)
    filtro_moneda = st.selectbox("Moneda", ["Todas"] + MONEDAS_DISPONIBLES)
    filtro_riesgo = st.selectbox("Estado de Riesgo", ["Todos", "Normal", "En Riesgo", "Crítico"])
    
    # Filtro por sub-estado de preventa
    filtro_subestado = st.selectbox("Estado Preventa", [
        "Todos", 
        "📋 PREVENTA ACTIVA (25%)", 
        "📤 PROPUESTA ENTREGADA (50%)", 
        "🎉 OC FIRMADA (75%)"
    ])
    
    filtro_deadline = st.selectbox("Estado Deadline", [
        "Todos", 
        "Vencido", 
        "Crítico", 
        "Urgente", 
        "Por Vencer", 
        "Disponible", 
        "Sin Deadline",
        "✅ Propuesta Presentada"
    ])

    st.divider()
    st.header("📈 Estadísticas Rápidas")
    total_preventa = len(proyectos_preventa)
    st.metric("Total Preventas", total_preventa)

    if total_preventa > 0:
        valor_total = 0
        for p in proyectos_preventa:
            valor_convertido = convertir_moneda(
                p.valor_estimado,
                p.moneda,
                moneda_visualizacion,
                p.tipo_cambio_historico
            )
            valor_total += valor_convertido

        st.metric("Valor Total Pipeline", formatear_moneda(valor_total, moneda_visualizacion))

        preventas_riesgo = len([p for p in proyectos_preventa
                               if (datetime.now() - p.fecha_ultima_actualizacion).days > 7])
        st.metric("En Riesgo", preventas_riesgo, delta=-preventas_riesgo if preventas_riesgo > 0 else 0)

# ==============================
# KPIs principales 
# ==============================
if proyectos_preventa:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        valor_pipeline = 0
        for p in proyectos_preventa:
            # Valor ponderado por probabilidad
            valor_convertido = convertir_moneda(
                p.valor_estimado * (p.probabilidad_cierre / 100),
                p.moneda,
                moneda_visualizacion,
                p.tipo_cambio_historico
            )
            valor_pipeline += valor_convertido

        st.metric("💰 Valor del Pipeline", formatear_moneda(valor_pipeline, moneda_visualizacion))

    with col2:
        total_valor = 0
        for p in proyectos_preventa:
            valor_convertido = convertir_moneda(
                p.valor_estimado,
                p.moneda,
                moneda_visualizacion,
                p.tipo_cambio_historico
            )
            total_valor += valor_convertido

        st.metric("💸 Valor Total Estimado", formatear_moneda(total_valor, moneda_visualizacion))

    with col3:
        # Contar proyectos por sub-estado
        preventa_activa = len([p for p in proyectos_preventa if p.probabilidad_cierre == 25])
        propuesta_entregada = len([p for p in proyectos_preventa if p.probabilidad_cierre == 50])
        oc_firmada = len([p for p in proyectos_preventa if p.probabilidad_cierre >= 75])
        
        st.metric("📋 Preventa Activa", preventa_activa)
        st.metric("📤 Propuesta Entregada", propuesta_entregada)
        st.metric("🎉 OC Firmada", oc_firmada)

    with col4:
        # Contar preventas con deadline vencido (solo las que están en preventa activa)
        preventas_vencidas = len([p for p in proyectos_preventa
                                if p.fecha_deadline_propuesta and 
                                p.fecha_deadline_propuesta < datetime.now() and
                                p.probabilidad_cierre < 50])
        st.metric("⏰ Deadlines Vencidos", preventas_vencidas)

# ==============================
# EL FORMULARIO DE EDICIÓN
# ==============================
if st.session_state.editing_project is not None:
    proyecto_editar = next((p for p in proyectos_preventa if p.id == st.session_state.editing_project), None)

    if proyecto_editar:
        st.markdown("---")
        with st.expander("✏️ Editando Preventa", expanded=True):
            st.info(f"📝 Editando: **{proyecto_editar.codigo_proyecto}** - {proyecto_editar.nombre}")

            # Obtener documentos del proyecto
            archivos_proyecto = obtener_archivos_proyecto(proyecto_editar.id)
            
            # Determinar el estado basado en AMBAS condiciones:
            # 1. Fecha de presentación de propuesta
            # 2. Probabilidad de cierre = 50%
            tiene_fecha_presentacion = proyecto_editar.fecha_presentacion_propuesta is not None
            probabilidad_50 = proyecto_editar.probabilidad_cierre == 50
            
            es_propuesta_entregada = tiene_fecha_presentacion and probabilidad_50
            
            # Obtener último TDR para mostrar
            ultimo_tdr = obtener_ultimo_tdr(proyecto_editar.id)
            
            # Visualización de último TDR
            st.subheader("📎 Documentos TDR")
            
            if ultimo_tdr:
                col_tdr1, col_tdr2, col_tdr3 = st.columns([3, 1, 1])
                with col_tdr1:
                    st.info(f"**Último TDR:** {ultimo_tdr.nombre_archivo}")
                    st.caption(f"Subido el: {ultimo_tdr.fecha_subida.strftime('%d/%m/%Y %H:%M')}")
                
                with col_tdr2:
                    if os.path.exists(ultimo_tdr.ruta_archivo):
                        with open(ultimo_tdr.ruta_archivo, "rb") as f:
                            st.download_button(
                                "⬇️ Descargar",
                                f.read(),
                                ultimo_tdr.nombre_archivo,
                                key="download_tdr"
                            )
                
                with col_tdr3:
                    if st.button("🗑️", help="Eliminar TDR", key="eliminar_tdr"):
                        st.warning("Funcionalidad de eliminación pendiente")
            else:
                st.info("📝 No hay TDR subidos para este proyecto")
            
            # SECCIÓN DE PROPUESTA según el estado (basado en AMBAS condiciones)
            st.subheader("📄 Gestión de Propuesta")
            
            # Mostrar estado actual de las condiciones
            col_cond1, col_cond2 = st.columns(2)
            with col_cond1:
                estado_fecha = "✅" if tiene_fecha_presentacion else "❌"
                st.write(f"{estado_fecha} **Fecha de presentación:** {proyecto_editar.fecha_presentacion_propuesta.strftime('%d/%m/%Y %H:%M') if tiene_fecha_presentacion else 'No establecida'}")
            
            with col_cond2:
                estado_prob = "✅" if probabilidad_50 else "❌"
                st.write(f"{estado_prob} **Probabilidad de cierre:** {proyecto_editar.probabilidad_cierre}%")
            
            if es_propuesta_entregada:
                # ESTADO: Propuesta Entregada - Cumple AMBAS condiciones
                st.success("**✅ ESTADO: Propuesta Entregada** - Cumple con fecha de presentación y 50% de probabilidad")
                
                # Buscar si existe archivo de propuesta
                archivo_propuesta = next((archivo for archivo in archivos_proyecto 
                                        if archivo.tipo_archivo.nombre.lower() == 'propuesta'), None)
                
                if archivo_propuesta:
                    col_prop1, col_prop2, col_prop3 = st.columns([3, 1, 1])
                    with col_prop1:
                        st.info(f"**Archivo de Propuesta:** {archivo_propuesta.nombre_archivo}")
                        st.caption(f"Subido el: {archivo_propuesta.fecha_subida.strftime('%d/%m/%Y %H:%M')}")
                    
                    with col_prop2:
                        if os.path.exists(archivo_propuesta.ruta_archivo):
                            with open(archivo_propuesta.ruta_archivo, "rb") as f:
                                st.download_button(
                                    "⬇️ Descargar Propuesta",
                                    f.read(),
                                    archivo_propuesta.nombre_archivo,
                                    key="download_propuesta"
                                )
                    
                    with col_prop3:
                        if st.button("🗑️ Propuesta", help="Eliminar Propuesta", key="eliminar_propuesta"):
                            st.warning("Funcionalidad de eliminación pendiente")
                else:
                    st.warning("⚠️ Estado de propuesta entregada pero no se encontró archivo de propuesta")
                
                # Opción para subir Orden de Compra
                st.markdown("---")
                st.subheader("📋 Orden de Compra")
                
                # Verificar si ya tiene orden de compra
                tiene_oc = any(archivo.tipo_archivo.nombre.lower() in ['orden de compra', 'oc'] for archivo in archivos_proyecto)
                
                if tiene_oc:
                    oc_subida = next((archivo for archivo in archivos_proyecto 
                                    if archivo.tipo_archivo.nombre.lower() in ['orden de compra', 'oc']), None)
                    
                    col_oc1, col_oc2, col_oc3 = st.columns([3, 1, 1])
                    with col_oc1:
                        st.success(f"**✅ Orden de Compra Subida:** {oc_subida.nombre_archivo}")
                        st.caption(f"Subida el: {oc_subida.fecha_subida.strftime('%d/%m/%Y %H:%M')}")
                    
                    with col_oc2:
                        if os.path.exists(oc_subida.ruta_archivo):
                            with open(oc_subida.ruta_archivo, "rb") as f:
                                st.download_button(
                                    "⬇️ Descargar OC",
                                    f.read(),
                                    oc_subida.nombre_archivo,
                                    key="download_oc"
                                )
                    
                    with col_oc3:
                        if st.button("🗑️ OC", help="Eliminar Orden de Compra", key="eliminar_oc"):
                            st.warning("Funcionalidad de eliminación pendiente")
                else:
                    # Subir nueva orden de compra
                    col_oc1, col_oc2 = st.columns([3, 1])
                    with col_oc1:
                        archivo_oc = st.file_uploader("Seleccionar Orden de Compra", 
                                                    type=['pdf', 'docx', 'xlsx'], 
                                                    key="nuevo_archivo_oc")
                    with col_oc2:
                        st.selectbox("Tipo", options=["Orden de Compra"], 
                                    key="nuevo_tipo_oc", disabled=True)
                    
                    if archivo_oc:
                        # Buscar ID para tipo "Orden de Compra"
                        tipo_oc_id = next((t.id for t in tipos_archivo_db 
                                         if t.nombre.lower() in ['orden de compra', 'oc']), 4)  # Valor por defecto
                        
                        # Verificar duplicados
                        duplicado_oc, nombre_final_oc, ruta_completa_oc = verificar_archivo_duplicado(
                            proyecto_editar.id, "OC", archivo_oc.name
                        )
                        
                        if duplicado_oc:
                            st.error(f"❌ Ya existe un archivo con el nombre: {nombre_final_oc}")
                        else:
                            st.success(f"✅ Archivo listo para subir: {nombre_final_oc}")
                            
                            if st.button("Subir Orden de Compra", key="subir_oc"):
                                try:
                                    subir_archivo_proyecto(
                                        proyecto_editar.id,
                                        tipo_oc_id,
                                        archivo_oc,
                                        1  # ID del usuario actual
                                    )
                                    st.success("✅ Orden de Compra subida correctamente")
                                    time.sleep(2)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al subir archivo: {str(e)}")
            
            else:
                # ESTADO: Preventa Activa - No cumple AMBAS condiciones
                st.info("**📝 ESTADO: Preventa Activa** - No cumple ambas condiciones para propuesta entregada")
                
                # Formulario para establecer las condiciones de propuesta entregada
                with st.form("form_establecer_propuesta"):
                    st.subheader("Establecer como Propuesta Entregada")
                    
                    col_fecha, col_hora, col_prob = st.columns([2, 1, 1])
                    
                    with col_fecha:
                        fecha_presentacion = st.date_input(
                            "Fecha de Presentación",
                            value=datetime.now().date(),
                            format="DD/MM/YYYY",
                            key="fecha_presentacion"
                        )
                    
                    with col_hora:
                        hora_presentacion = st.time_input(
                            "Hora de Presentación",
                            value=datetime.now().time(),
                            step=3600,
                            key="hora_presentacion"
                        )
                    
                    with col_prob:
                        # Forzar probabilidad a 50% para propuesta entregada
                        probabilidad_cierre = st.number_input(
                            "Probabilidad de Cierre (%)",
                            min_value=0,
                            max_value=100,
                            value=50,
                            step=5,
                            disabled=True,  # Forzado a 50%
                            help="Para propuesta entregada, la probabilidad debe ser 50%"
                        )
                    
                    # Opción para subir propuesta (opcional)
                    col_prop1, col_prop2 = st.columns([3, 1])
                    with col_prop1:
                        archivo_propuesta = st.file_uploader("Subir Propuesta Final (Opcional)", 
                                                           type=['pdf', 'docx', 'xlsx'], 
                                                           key="nuevo_archivo_propuesta")
                    with col_prop2:
                        st.selectbox("Tipo", options=["Propuesta"], 
                                    key="nuevo_tipo_propuesta", disabled=True)
                    
                    if st.form_submit_button("✅ Marcar como Propuesta Entregada", use_container_width=True):
                        try:
                            # Actualizar las condiciones en la base de datos
                            db = SessionLocal()
                            proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_editar.id).first()
                            if proyecto:
                                # Establecer AMBAS condiciones
                                proyecto.fecha_presentacion_propuesta = datetime.combine(fecha_presentacion, hora_presentacion)
                                proyecto.probabilidad_cierre = 50  # Forzar a 50%
                                
                                proyecto.agregar_evento_historial(
                                    f"Propuesta entregada el {fecha_presentacion.strftime('%d/%m/%Y %H:%M')} " +
                                    f"con probabilidad de cierre al 50%"
                                )
                                
                                # Subir archivo de propuesta si se proporcionó
                                if archivo_propuesta:
                                    tipo_propuesta_id = next((t.id for t in tipos_archivo_db 
                                                            if t.nombre.lower() == 'propuesta'), 2)
                                    subir_archivo_proyecto(
                                        proyecto_editar.id,
                                        tipo_propuesta_id,
                                        archivo_propuesta,
                                        1  # ID del usuario actual
                                    )
                                
                                db.commit()
                                st.success("✅ Propuesta marcada como entregada correctamente")
                                time.sleep(2)
                                st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"❌ Error al actualizar: {str(e)}")
                        finally:
                            db.close()
            
            # Botón para ver todos los archivos
            if st.button("👁️ Ver todos los archivos", key="ver_archivos"):
                st.session_state.modal_archivos_abierto = True
                st.session_state.proyecto_archivos = proyecto_editar
                st.rerun()
            
            st.markdown("---")
            
            # Resto del formulario de edición (se mantiene igual)
            with st.form("form_editar_preventa"):
                # ... (el resto del formulario permanece igual)


# ==============================
# Aplicar filtros
# ==============================
proyectos_filtrados = proyectos_preventa.copy()

if filtro_ejecutivo != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados if p.asignado_a.nombre == filtro_ejecutivo]

if filtro_cliente != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados if p.cliente.nombre == filtro_cliente]

if filtro_moneda != "Todas":
    proyectos_filtrados = [p for p in proyectos_filtrados if p.moneda == filtro_moneda]

if filtro_riesgo != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados
                          if get_estado_riesgo((datetime.now() - p.fecha_ultima_actualizacion).days) == filtro_riesgo]

if filtro_subestado != "Todos":
    if filtro_subestado == "📋 PREVENTA ACTIVA (25%)":
        proyectos_filtrados = [p for p in proyectos_filtrados if p.probabilidad_cierre == 25]
    elif filtro_subestado == "📤 PROPUESTA ENTREGADA (50%)":
        proyectos_filtrados = [p for p in proyectos_filtrados if p.probabilidad_cierre == 50]
    elif filtro_subestado == "🎉 OC FIRMADA (75%)":
        proyectos_filtrados = [p for p in proyectos_filtrados if p.probabilidad_cierre >= 75]

if filtro_deadline != "Todos":
    if filtro_deadline == "✅ Propuesta Presentada":
        proyectos_filtrados = [p for p in proyectos_filtrados if p.fecha_presentacion_cotizacion is not None]
    else:
        proyectos_filtrados = [p for p in proyectos_filtrados
                          if calcular_criticidad_deadline(p) == filtro_deadline.lower().replace(' ', '_')]

# ==============================
# Lista de Preventas
# ==============================
st.markdown("---")
st.header(f"📋 Lista de Preventas ({len(proyectos_filtrados)} encontradas)")

if not proyectos_filtrados:
    st.info("🔍 No hay preventas que coincidan con los filtros aplicados.")

# ==============================
# VISTA DE TARJETAS
# ==============================
elif vista_modo == "Tarjetas":
    cols = st.columns(3)

    for i, proyecto in enumerate(proyectos_filtrados):
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
        color_riesgo = get_color_riesgo(dias_sin_actualizar)
        estado_riesgo = get_estado_riesgo(dias_sin_actualizar)

        # Obtener sub-estado de preventa
        estado_preventa = obtener_estado_preventa(proyecto)
        criticidad_deadline = calcular_criticidad_deadline(proyecto)
        estilo_deadline = obtener_estilo_deadline(criticidad_deadline)

        # Convertir valor a moneda de visualización
        valor_visualizacion = convertir_moneda(
            proyecto.valor_estimado,
            proyecto.moneda,
            moneda_visualizacion,
            proyecto.tipo_cambio_historico
        )

        with cols[i % 3]:
            with st.container():
                # Header con información de sub-estado
                st.markdown(f"""
                <div style='border-radius:10px; padding:15px; margin-bottom:15px; 
                            background-color:{estado_preventa['color']}20; border-left:5px solid {estado_preventa['color']}'>
                    <h4 style='margin:0; color:{estado_preventa['color']}'>{estado_preventa['icono']} {estado_preventa['nombre']}</h4>
                    <p style='margin:0; font-size:0.8em; color:#666'>
                        Probabilidad: {proyecto.probabilidad_cierre}% | 
                        Últ. actualización: {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y')}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # Información principal del proyecto
                st.markdown(f"### {proyecto.codigo_proyecto}")
                st.markdown(f"**{proyecto.nombre}**")
                st.markdown(f"*{proyecto.cliente.nombre}*")

                # Valor estimado
                st.markdown(f"**Valor:** {formatear_moneda(valor_visualizacion, moneda_visualizacion)}")

                # Información de asignación
                st.markdown(f"**Asignado a:** {proyecto.asignado_a.nombre if proyecto.asignado_a else 'Sin asignar'}")

                # Deadline solo si es relevante
                if proyecto.probabilidad_cierre < 50 and proyecto.fecha_deadline_propuesta:
                    dias_restantes = (proyecto.fecha_deadline_propuesta - datetime.now()).days
                    fecha_formateada = proyecto.fecha_deadline_propuesta.strftime('%d/%m/%Y %H:%M')
                    
                    st.markdown(f"""
                    <div style='background-color:{estilo_deadline['fondo']}; 
                                padding:10px; border-radius:5px; margin:10px 0; 
                                border-left:3px solid {estilo_deadline['color']}'>
                        <div style='display:flex; align-items:center;'>
                            <span style='font-size:1.2em; margin-right:10px;'>{estilo_deadline['icono']}</span>
                            <div>
                                <strong style='color:{estilo_deadline['color']}'>Deadline</strong><br>
                                {fecha_formateada}<br>
                                <small>{dias_restantes} días restantes</small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif proyecto.fecha_presentacion_cotizacion:
                    st.success(f"✅ Propuesta presentada: {proyecto.fecha_presentacion_cotizacion.strftime('%d/%m/%Y')}")

                # Historial reciente
                historial = cargar_historial_proyecto(proyecto.id)
                if historial:
                    with st.expander("📋 Historial reciente"):
                        for evento in historial:
                            fecha_evento = evento[0].strftime('%d/%m/%Y %H:%M') if hasattr(evento[0], 'strftime') else str(evento[0])
                            st.markdown(f"`{fecha_evento}` - {evento[1]}")

                # Botones de acción según sub-estado
                col_btn1, col_btn2, col_btn3 = st.columns(3)

                with col_btn1:
                    if st.button("✏️", key=f"edit_{proyecto.id}", help="Editar preventa"):
                        st.session_state.editing_project = proyecto.id
                        st.rerun()

                with col_btn2:
                    if st.button("📞", key=f"contact_{proyecto.id}", help="Registrar contacto"):
                        nuevo_deadline = registrar_contacto_orm(proyecto.id)
                        st.success(f"✅ Contacto registrado. Próximo seguimiento: {nuevo_deadline.strftime('%d/%m/%Y')}")
                        time.sleep(2)
                        st.rerun()

                with col_btn3:
                    if proyecto.probabilidad_cierre == 25:
                        if st.button("📤", key=f"propuesta_{proyecto.id}", help="Marcar propuesta presentada"):
                            if marcar_propuesta_presentada_orm(proyecto.id):
                                st.success("✅ Propuesta marcada como presentada!")
                                time.sleep(2)
                                st.rerun()
                    elif proyecto.probabilidad_cierre == 50:
                        if st.button("🎉", key=f"oc_{proyecto.id}", help="Subir Orden de Compra"):
                            st.session_state.editing_project = proyecto.id
                            st.rerun()

                st.markdown("---")

# ==============================
# VISTA DE TABLA
# ==============================
elif vista_modo == "Tabla":
    datos_tabla = []
    for proyecto in proyectos_filtrados:
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
        estado_preventa = obtener_estado_preventa(proyecto)
        criticidad_deadline = calcular_criticidad_deadline(proyecto)
        estilo_deadline = obtener_estilo_deadline(criticidad_deadline)

        valor_visualizacion = convertir_moneda(
            proyecto.valor_estimado,
            proyecto.moneda,
            moneda_visualizacion,
            proyecto.tipo_cambio_historico
        )

        datos_tabla.append({
            'Código': proyecto.codigo_proyecto,
            'Nombre': proyecto.nombre,
            'Cliente': proyecto.cliente.nombre,
            'Valor': formatear_moneda(valor_visualizacion, moneda_visualizacion),
            'Asignado': proyecto.asignado_a.nombre if proyecto.asignado_a else 'Sin asignar',
            'Estado': estado_preventa['nombre'],
            'Probabilidad': f"{proyecto.probabilidad_cierre}%",
            'Deadline': proyecto.fecha_deadline_propuesta.strftime('%d/%m/%Y %H:%M') if proyecto.probabilidad_cierre < 50 and proyecto.fecha_deadline_propuesta else 'N/A',
            'Propuesta': proyecto.fecha_presentacion_cotizacion.strftime('%d/%m/%Y') if proyecto.fecha_presentacion_cotizacion else 'Pendiente',
            'Últ. Actualización': proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y'),
            'Días sin actualizar': dias_sin_actualizar,
            'ID': proyecto.id
        })

    df = pd.DataFrame(datos_tabla)
    st.dataframe(
        df,
        column_config={
            "ID": None
        },
        hide_index=True,
        use_container_width=True
    )



# ==============================
# Footer
# ==============================
st.markdown("---")
st.caption(f"📊 Dashboard de Preventa - Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
