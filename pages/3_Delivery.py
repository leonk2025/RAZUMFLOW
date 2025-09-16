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
st.set_page_config(page_title="Dashboard de Delivery", layout="wide", page_icon="🚚")

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

def subir_guia_remision_orm(proyecto_id, usuario_id, fecha_entrega):
    """Sube guía de remisión y marca como entregado"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.fecha_entrega = fecha_entrega
            proyecto.entregado = True
            proyecto.agregar_evento_historial("📦 Guía de remisión subida - Proyecto ENTREGADO")
            proyecto.fecha_ultima_actualizacion = datetime.now()

            db.commit()

        db.close()
        return True
    except Exception as e:
        db.rollback()
        raise e

def subir_factura_orm(proyecto_id, usuario_id, fecha_facturacion, dias_pago=15):
    """Sube factura y avanza a COBRANZA"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.fecha_facturacion = fecha_facturacion
            proyecto.facturado = True
            proyecto.dias_pago = dias_pago
            proyecto.agregar_evento_historial("🧾 Factura subida - Movido a COBRANZA")
            proyecto.fecha_ultima_actualizacion = datetime.now()

            # Auto-avance a COBRANZA
            proyecto.mover_a_estado(Estado.COBRANZA, usuario_id)

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
def obtener_estilo_entrega(nivel_alerta):
    """Devuelve estilo CSS según el nivel de alerta de entrega"""
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

def calcular_criticidad_entrega(proyecto):
    """Calcula la criticidad basada en la fecha de entrega"""
    if not proyecto.fecha_ingreso_oc or not proyecto.plazo_entrega:
        return 'sin_deadline'

    fecha_entrega_estimada = proyecto.fecha_ingreso_oc + timedelta(days=proyecto.plazo_entrega)
    dias_restantes = (fecha_entrega_estimada - datetime.now()).days

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

def obtener_estado_delivery(proyecto):
    """Determina el sub-estado de delivery basado en flags"""
    if proyecto.facturado:
        return {'nombre': '🧾 FACTURADO', 'color': '#16a34a', 'icono': '🧾'}
    elif proyecto.entregado:
        return {'nombre': '✅ ENTREGADO', 'color': '#4ECDC4', 'icono': '✅'}
    else:
        return {'nombre': '📦 PENDIENTE DE ENTREGA', 'color': '#f59e0b', 'icono': '📦'}

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
st.title("🚚 Dashboard de DELIVERY")
st.page_link("main_app.py", label="🔙 Volver al Workflow Principal")

# ==============================
# Cargar datos desde ORM
# ==============================
proyectos_todos = cargar_proyectos_activos()
proyectos_delivery = [p for p in proyectos_todos if p.estado_actual == Estado.DELIVERY.value]

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
    
    # Filtro por sub-estado de delivery
    filtro_subestado = st.selectbox("Estado Delivery", [
        "Todos", 
        "📦 PENDIENTE DE ENTREGA", 
        "✅ ENTREGADO", 
        "🧾 FACTURADO"
    ])
    
    filtro_entrega = st.selectbox("Estado Entrega", [
        "Todos", 
        "Vencido", 
        "Crítico", 
        "Urgente", 
        "Por Vencer", 
        "Disponible", 
        "Sin Deadline"
    ])

    st.divider()
    st.header("📈 Estadísticas Rápidas")
    total_delivery = len(proyectos_delivery)
    st.metric("Total Delivery", total_delivery)

    if total_delivery > 0:
        valor_total = 0
        for p in proyectos_delivery:
            valor_convertido = convertir_moneda(
                p.valor_estimado,
                p.moneda,
                moneda_visualizacion,
                p.tipo_cambio_historico
            )
            valor_total += valor_convertido

        st.metric("Valor Total Pipeline", formatear_moneda(valor_total, moneda_visualizacion))

        deliveries_riesgo = len([p for p in proyectos_delivery
                               if (datetime.now() - p.fecha_ultima_actualizacion).days > 7])
        st.metric("En Riesgo", deliveries_riesgo, delta=-deliveries_riesgo if deliveries_riesgo > 0 else 0)

# ==============================
# KPIs principales 
# ==============================
if proyectos_delivery:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        valor_pipeline = 0
        for p in proyectos_delivery:
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
        for p in proyectos_delivery:
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
        pendientes = len([p for p in proyectos_delivery if not p.entregado])
        entregados = len([p for p in proyectos_delivery if p.entregado and not p.facturado])
        facturados = len([p for p in proyectos_delivery if p.facturado])
        
        st.metric("📦 Pendientes de Entrega", pendientes)
        st.metric("✅ Entregados", entregados)
        st.metric("🧾 Facturados", facturados)

    with col4:
        # Contar deliveries con entrega vencida
        entregas_vencidas = len([p for p in proyectos_delivery
                                if p.fecha_ingreso_oc and p.plazo_entrega and
                                (p.fecha_ingreso_oc + timedelta(days=p.plazo_entrega)) < datetime.now() and
                                not p.entregado])
        st.metric("⏰ Entregas Vencidas", entregas_vencidas)

# ==============================
# Formulario de Edición
# ==============================
if st.session_state.editing_project is not None:
    proyecto_editar = next((p for p in proyectos_delivery if p.id == st.session_state.editing_project), None)

    if proyecto_editar:
        st.markdown("---")
        with st.expander("✏️ Editando Delivery", expanded=True):
            st.info(f"📝 Editando: **{proyecto_editar.codigo_proyecto}** - {proyecto_editar.nombre}")
            
            # Determinar el estado basado en flags de entrega y facturación
            estado_delivery = obtener_estado_delivery(proyecto_editar)
            
            # Mostrar estado actual de delivery
            st.markdown(f"""
            <div style='background-color:{estado_delivery['color']}20; padding:10px; border-radius:5px; border-left:4px solid {estado_delivery['color']}'>
                <strong>{estado_delivery['icono']} {estado_delivery['nombre']}</strong><br>
                <small>Probabilidad de cierre: {proyecto_editar.probabilidad_cierre}%</small>
            </div>
            """, unsafe_allow_html=True)

            # Obtener los últimos archivos por tipo
            ultima_guia = obtener_ultimo_archivo_por_tipo(proyecto_editar.id, "GUIA")
            ultima_factura = obtener_ultimo_archivo_por_tipo(proyecto_editar.id, "FACTURA")
            
            # SECCIÓN DIFERENCIADA POR ESTADO
            if proyecto_editar.facturado:
                # ESTADO: FACTURADO (ya facturado)
                st.success("✅ **FACTURADO** - Proyecto facturado y movido a COBRANZA")
                
                # Mostrar última factura si existe
                if ultima_factura:
                    st.subheader("🧾 Última Factura")
                    col_fact1, col_fact2, col_fact3 = st.columns([3, 1, 1])
                    with col_fact1:
                        st.success(f"**Factura:** {ultima_factura.nombre_archivo}")
                        st.caption(f"Subida el: {ultima_factura.fecha_subida.strftime('%d/%m/%Y %H:%M')}")
                        st.caption(f"Fecha facturación: {proyecto_editar.fecha_facturacion.strftime('%d/%m/%Y') if proyecto_editar.fecha_facturacion else 'N/A'}")
                        st.caption(f"Días de pago: {proyecto_editar.dias_pago}")
                    
                    with col_fact2:
                        if os.path.exists(ultima_factura.ruta_archivo):
                            with open(ultima_factura.ruta_archivo, "rb") as f:
                                st.download_button(
                                    "⬇️ Descargar",
                                    f.read(),
                                    ultima_factura.nombre_archivo,
                                    key="download_factura"
                                )
                    
                    with col_fact3:
                        if st.button("🗑️", help="Eliminar Factura", key="eliminar_factura"):
                            st.warning("Funcionalidad de eliminación pendiente")

            elif proyecto_editar.entregado:
                # ESTADO: ENTREGADO (pero no facturado)
                st.info("✅ **ENTREGADO** - Pendiente de facturación")
                
                # Mostrar última guía si existe
                if ultima_guia:
                    st.subheader("📦 Última Guía de Remisión")
                    col_guia1, col_guia2, col_guia3 = st.columns([3, 1, 1])
                    with col_guia1:
                        st.info(f"**Guía:** {ultima_guia.nombre_archivo}")
                        st.caption(f"Subida el: {ultima_guia.fecha_subida.strftime('%d/%m/%Y %H:%M')}")
                        st.caption(f"Fecha entrega: {proyecto_editar.fecha_entrega.strftime('%d/%m/%Y') if proyecto_editar.fecha_entrega else 'N/A'}")
                    
                    with col_guia2:
                        if os.path.exists(ultima_guia.ruta_archivo):
                            with open(ultima_guia.ruta_archivo, "rb") as f:
                                st.download_button(
                                    "⬇️ Descargar",
                                    f.read(),
                                    ultima_guia.nombre_archivo,
                                    key="download_guia"
                                )
                    
                    with col_guia3:
                        if st.button("🗑️", help="Eliminar Guía", key="eliminar_guia"):
                            st.warning("Funcionalidad de eliminación pendiente")

                # Opción para subir factura
                st.markdown("---")
                st.subheader("🧾 Subir Factura")

                col_archivo1, col_archivo2 = st.columns([3, 1])
                with col_archivo1:
                    nueva_factura = st.file_uploader("Seleccionar Factura", type=['pdf', 'docx', 'xlsx'], key="nueva_factura")
                with col_archivo2:
                    st.selectbox("Tipo", options=["FACTURA"], disabled=True, key="tipo_factura")

                # Campos para facturación
                col_fecha_fact, col_dias_pago = st.columns(2)
                with col_fecha_fact:
                    fecha_facturacion = st.date_input("Fecha de Facturación", value=datetime.now().date(), format="DD/MM/YYYY")
                with col_dias_pago:
                    dias_pago = st.number_input("Días de Pago", min_value=0, value=15, step=1, help="Días para el pago (15 por defecto)")

                if nueva_factura:
                    duplicado, nombre_final, ruta_completa = verificar_archivo_duplicado(
                        proyecto_editar.id, "FACTURA", nueva_factura.name
                    )

                    if duplicado:
                        st.error(f"❌ Ya existe un archivo con el nombre: {nombre_final}")
                    else:
                        st.success(f"✅ Factura lista para subir: {nombre_final}")

                        if st.button("Subir Factura", key="subir_factura"):
                            try:
                                tipo_factura_id = next((t.id for t in tipos_archivo_db if t.nombre == "FACTURA"), 4)
                                subir_archivo_proyecto(
                                    proyecto_editar.id,
                                    tipo_factura_id,
                                    nueva_factura,
                                    1  # ID del usuario actual
                                )

                                # Actualizar campos de facturación
                                fecha_fact_completa = datetime.combine(fecha_facturacion, datetime.now().time())
                                if subir_factura_orm(proyecto_editar.id, 1, fecha_fact_completa, dias_pago):
                                    st.balloons()
                                    st.success("🎉 ¡Factura subida y proyecto movido a COBRANZA!")
                                    time.sleep(3)
                                    st.session_state.editing_project = None
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al subir archivo: {str(e)}")

            else:
                # ESTADO: PENDIENTE DE ENTREGA
                st.warning("📦 **PENDIENTE DE ENTREGA** - Esperando guía de remisión")
                
                # Opción para subir guía de remisión
                st.markdown("---")
                st.subheader("📦 Subir Guía de Remisión")

                col_archivo1, col_archivo2 = st.columns([3, 1])
                with col_archivo1:
                    nueva_guia = st.file_uploader("Seleccionar Guía de Remisión", type=['pdf', 'docx', 'xlsx'], key="nueva_guia")
                with col_archivo2:
                    st.selectbox("Tipo", options=["GUIA"], disabled=True, key="tipo_guia")

                # Campo para fecha de entrega
                fecha_entrega = st.date_input("Fecha de Entrega", value=datetime.now().date(), format="DD/MM/YYYY")

                if nueva_guia:
                    duplicado, nombre_final, ruta_completa = verificar_archivo_duplicado(
                        proyecto_editar.id, "GUIA", nueva_guia.name
                    )

                    if duplicado:
                        st.error(f"❌ Ya existe un archivo con el nombre: {nombre_final}")
                    else:
                        st.success(f"✅ Guía lista para subir: {nombre_final}")

                        if st.button("Subir Guía de Remisión", key="subir_guia"):
                            try:
                                tipo_guia_id = next((t.id for t in tipos_archivo_db if t.nombre == "GUIA"), 5)
                                subir_archivo_proyecto(
                                    proyecto_editar.id,
                                    tipo_guia_id,
                                    nueva_guia,
                                    1  # ID del usuario actual
                                )

                                # Actualizar campos de entrega
                                fecha_entrega_completa = datetime.combine(fecha_entrega, datetime.now().time())
                                if subir_guia_remision_orm(proyecto_editar.id, 1, fecha_entrega_completa):
                                    st.balloons()
                                    st.success("✅ ¡Guía de remisión subida y proyecto marcado como ENTREGADO!")
                                    time.sleep(3)
                                    st.session_state.editing_project = None
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al subir archivo: {str(e)}")
            
            # Botón para ver todos los archivos (común a todos los estados)
            if st.button("👁️ Ver todos los archivos", key="ver_archivos"):
                st.session_state.modal_archivos_abierto = True
                st.session_state.proyecto_archivos = proyecto_editar
                st.rerun()
            
            st.markdown("---")
            
            # Formulario de edición general (común a todos los estados)
            with st.form("form_editar_delivery"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    nuevo_nombre = st.text_input("Nombre", value=proyecto_editar.nombre)
                    nuevo_cliente_nombre = st.selectbox("Cliente", CLIENTES_DISPONIBLES,
                                                      index=CLIENTES_DISPONIBLES.index(proyecto_editar.cliente.nombre)
                                                      if proyecto_editar.cliente and proyecto_editar.cliente.nombre in CLIENTES_DISPONIBLES else 0)
                    nueva_moneda = st.selectbox("Moneda", MONEDAS_DISPONIBLES,
                                              index=MONEDAS_DISPONIBLES.index(proyecto_editar.moneda))

                with col2:
                    nueva_descripcion = st.text_area("Descripción", value=proyecto_editar.descripcion or "")
                    nuevo_ejecutivo_nombre = st.selectbox("Asignado a", EJECUTIVOS_DISPONIBLES,
                                                        index=EJECUTIVOS_DISPONIBLES.index(proyecto_editar.asignado_a.nombre)
                                                        if proyecto_editar.asignado_a and proyecto_editar.asignado_a.nombre in EJECUTIVOS_DISPONIBLES else 0)
                    nuevo_valor = st.number_input("Valor Estimado", value=int(proyecto_editar.valor_estimado), step=1000)

                with col3:
                    # Mostrar información de plazo de entrega (solo lectura)
                    if proyecto_editar.fecha_ingreso_oc and proyecto_editar.plazo_entrega:
                        fecha_entrega_estimada = proyecto_editar.fecha_ingreso_oc + timedelta(days=proyecto_editar.plazo_entrega)
                        st.info(f"**Plazo de entrega:** {proyecto_editar.plazo_entrega} días")
                        st.info(f"**Entrega estimada:** {fecha_entrega_estimada.strftime('%d/%m/%Y')}")
                    else:
                        st.warning("⚠️ Sin información de plazo de entrega")

                    nuevo_tipo_cambio = st.number_input("Tipo de Cambio",
                                                       value=float(proyecto_editar.tipo_cambio_historico),
                                                       step=0.01,
                                                       disabled=nueva_moneda != 'USD')

                col1, col2 = st.columns(2)
                with col1:
                    guardar = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                with col2:
                    cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

                if guardar:
                    try:
                        cliente_id = cliente_nombre_a_id[nuevo_cliente_nombre]
                        asignado_a_id = usuario_nombre_a_id[nuevo_ejecutivo_nombre]

                        datos_actualizados = {
                            'nombre': nuevo_nombre,
                            'descripcion': nueva_descripcion,
                            'valor_estimado': nuevo_valor,
                            'moneda': nueva_moneda,
                            'tipo_cambio': nuevo_tipo_cambio,
                            'cliente_id': cliente_id,
                            'asignado_a_id': asignado_a_id
                        }

                        actualizar_proyecto_orm(proyecto_editar.id, datos_actualizados)

                        st.session_state.editing_project = None
                        st.success("✅ Cambios guardados exitosamente!")
                        time.sleep(3)
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error al guardar: {str(e)}")

                if cancelar:
                    st.session_state.editing_project = None
                    time.sleep(1)
                    st.rerun()

# ==============================
# Aplicar filtros
# ==============================
proyectos_filtrados = proyectos_delivery.copy()

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
    if filtro_subestado == "📦 PENDIENTE DE ENTREGA":
        proyectos_filtrados = [p for p in proyectos_filtrados if not p.entregado]
    elif filtro_subestado == "✅ ENTREGADO":
        proyectos_filtrados = [p for p in proyectos_filtrados if p.entregado and not p.facturado]
    elif filtro_subestado == "🧾 FACTURADO":
        proyectos_filtrados = [p for p in proyectos_filtrados if p.facturado]

if filtro_entrega != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados
                          if calcular_criticidad_entrega(p) == filtro_entrega.lower().replace(' ', '_')]

# ==============================
# Lista de Deliveries
# ==============================
st.markdown("---")
st.header(f"📋 Lista de Deliveries ({len(proyectos_filtrados)} encontradas)")

if not proyectos_filtrados:
    st.info("🔍 No hay deliveries que coincidan con los filtros aplicados.")

# ==============================
# VISTA DE TARJETAS
# ==============================
elif vista_modo == "Tarjetas":
    cols = st.columns(3)

    for i, proyecto in enumerate(proyectos_filtrados):
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
        color_riesgo = get_color_riesgo(dias_sin_actualizar)
        estado_riesgo = get_estado_riesgo(dias_sin_actualizar)

        # Obtener sub-estado de delivery
        estado_delivery = obtener_estado_delivery(proyecto)
        criticidad_entrega = calcular_criticidad_entrega(proyecto)
        estilo_entrega = obtener_estilo_entrega(criticidad_entrega)

        # Convertir valor a moneda de visualización
        valor_convertido = convertir_moneda(
            proyecto.valor_estimado,
            proyecto.moneda,
            moneda_visualizacion,
            proyecto.tipo_cambio_historico
        )

        # Formatear valor según moneda
        valor_formateado = formatear_moneda(valor_convertido, moneda_visualizacion)

        with cols[i % 3]:
            with st.container():
                # Información de entrega
                info_entrega = ""
                if proyecto.fecha_ingreso_oc and proyecto.plazo_entrega:
                    fecha_entrega_estimada = proyecto.fecha_ingreso_oc + timedelta(days=proyecto.plazo_entrega)
                    dias_restantes = (fecha_entrega_estimada - datetime.now()).days
                    texto_dias = f"{abs(dias_restantes)} días {'pasados' if dias_restantes < 0 else 'restantes'}"
                    entrega_html = f"""{estilo_entrega['icono']} Entrega: {fecha_entrega_estimada.strftime('%d/%m/%y')} ({texto_dias})"""
                else:
                    entrega_html = f"{estilo_entrega['icono']} Sin fecha de entrega"

                # TARJETA CON ESTILO
                st.markdown(f"""
                <div style="
                    border: 2px solid {estado_delivery['color']};
                    border-radius: 12px;
                    padding: 16px;
                    margin: 8px 0;
                    background: linear-gradient(145deg, {estado_delivery['color']}08, {estado_delivery['color']}15);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h4 style="color: {estado_delivery['color']}; margin: 0; font-size: 16px;">{proyecto.codigo_proyecto}</h4>
                        <span style="background-color: {estado_delivery['color']}20; color: {estado_delivery['color']};
                                    padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                            {estado_delivery['icono']} {estado_delivery['nombre'].split()[-1]}
                        </span>
                    </div>
                    <p style="margin: 8px 0; font-weight: bold; font-size: 14px;">{proyecto.nombre}</p>
                    <p style="margin: 4px 0; font-size: 12px;">👤 {proyecto.asignado_a.nombre if proyecto.asignado_a else 'Sin asignar'}</p>
                    <p style="margin: 4px 0; font-size: 12px;">🏢 {proyecto.cliente.nombre if proyecto.cliente else 'Sin cliente'}</p>
                    <p style="margin: 4px 0; font-size: 12px; color: #666;">💰 {valor_formateado} <small>({proyecto.moneda})</small></p>
                    <p style="margin: 4px 0; font-size: 11px; color: {estado_delivery['color']};">{entrega_html}</p>
                </div>
                """, unsafe_allow_html=True)

                # Botones de acción
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

                with col_btn1:
                    if st.button("✏️", key=f"edit_{proyecto.id}", help="Editar delivery"):
                        st.session_state.editing_project = proyecto.id
                        st.rerun()

                with col_btn2:
                    if st.button("📞", key=f"contact_{proyecto.id}", help="Registrar contacto"):
                        nuevo_deadline = registrar_contacto_orm(proyecto.id)
                        st.success(f"✅ Contacto registrado. Próximo seguimiento: {nuevo_deadline.strftime('%d/%m/%Y')}")
                        time.sleep(2)
                        st.rerun()

                with col_btn3:
                    if not proyecto.entregado:
                        if st.button("📦", key=f"guia_{proyecto.id}", help="Subir Guía"):
                            st.session_state.editing_project = proyecto.id
                            st.rerun()
                    elif not proyecto.facturado:
                        if st.button("🧾", key=f"factura_{proyecto.id}", help="Subir Factura"):
                            st.session_state.editing_project = proyecto.id
                            st.rerun()

                with col_btn4:
                    if st.button("🗑️", key=f"delete_{proyecto.id}", help="Eliminar delivery"):
                        try:
                            eliminar_proyecto_soft_orm(proyecto.id)
                            st.success("🗑️ Delivery eliminado!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

# ==============================
# VISTA DE TABLA
# ==============================
elif vista_modo == "Tabla":
    datos_tabla = []
    for proyecto in proyectos_filtrados:
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
        estado_delivery = obtener_estado_delivery(proyecto)
        criticidad_entrega = calcular_criticidad_entrega(proyecto)
        estilo_entrega = obtener_estilo_entrega(criticidad_entrega)

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
            'Estado': estado_delivery['nombre'],
            'Entrega Estimada': (proyecto.fecha_ingreso_oc + timedelta(days=proyecto.plazo_entrega)).strftime('%d/%m/%Y') if proyecto.fecha_ingreso_oc and proyecto.plazo_entrega else 'N/A',
            'Últ. Actualización': proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y'),
            'Días sin actualizar': dias_sin_actualizar,
            'ID': proyecto.id
        })

    # Asegurar selección única
    if 'selected_project_id' not in st.session_state:
        st.session_state.selected_project_id = None

    # Marcar como seleccionado solo el proyecto en session_state
    for i, proyecto in enumerate(proyectos_filtrados):
        datos_tabla[i]['Seleccionar'] = (proyecto.id == st.session_state.selected_project_id)

    df = pd.DataFrame(datos_tabla)

    # Reordenar columnas para que "Seleccionar" sea la primera
    column_order = ['Seleccionar'] + [col for col in df.columns if col != 'Seleccionar' and col != 'ID']
    df = df[column_order + ['ID']]

    # Mostrar el DataFrame con checkboxes
    edited_df = st.data_editor(
        df,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn(
                "✓",
                help="Selecciona un proyecto para editar",
                width="small"
            ),
            "ID": None,
            "Código": st.column_config.TextColumn("Código", width="small"),
            "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
            "Cliente": st.column_config.TextColumn("Cliente", width="medium"),
            "Valor": st.column_config.TextColumn("Valor", width="small"),
            "Asignado": st.column_config.TextColumn("Asignado a", width="small"),
            "Estado": st.column_config.TextColumn("Estado", width="medium"),
            "Entrega Estimada": st.column_config.TextColumn("Entrega Est.", width="small"),
            "Últ. Actualización": st.column_config.TextColumn("Últ. Actualiz.", width="small"),
            "Días sin actualizar": st.column_config.NumberColumn("Días sin act.", width="small")
        },
        hide_index=True,
        use_container_width=True,
        disabled=["Código", "Nombre", "Cliente", "Valor", "Asignado", "Estado",
                 "Entrega Estimada", "Últ. Actualización", "Días sin actualizar", "ID"]
    )

    # Actualizar selección automáticamente
    selected_rows = edited_df[edited_df["Seleccionar"]]
    if not selected_rows.empty:
        new_selected_id = selected_rows.iloc[0]["ID"]
        if new_selected_id != st.session_state.selected_project_id:
            st.session_state.selected_project_id = new_selected_id
            st.rerun()
    else:
        # Si se deseleccionó todo, limpiar la selección
        if st.session_state.selected_project_id is not None:
            st.session_state.selected_project_id = None
            st.rerun()

    # Botón de edición
    st.markdown("---")
    if st.session_state.selected_project_id:
        selected_project = next((p for p in proyectos_filtrados if p.id == st.session_state.selected_project_id), None)
        if selected_project:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info(f"**Seleccionado:** {selected_project.codigo_proyecto} - {selected_project.nombre}")

            with col2:
                if st.button(
                    "✏️ Editar",
                    use_container_width=True,
                    type="primary",
                    key="edit_selected"
                ):
                    st.session_state.editing_project = selected_project.id
                    st.rerun()

            with col3:
                if st.button(
                    "🗑️ Limpiar",
                    use_container_width=True,
                    key="clear_selected"
                ):
                    st.session_state.selected_project_id = None
                    st.rerun()
    else:
        st.info("ℹ️ Selecciona un proyecto de la tabla para habilitar la edición")

# ==============================
# Footer
# ==============================
st.markdown("---")
st.caption(f"🚚 Dashboard de Delivery - Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
