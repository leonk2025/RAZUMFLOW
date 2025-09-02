# pages/1_Oportunidades.py
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
st.set_page_config(page_title="Dashboard de Oportunidades", layout="wide", page_icon="📊")

# ==============================
# NUEVAS FUNCIONES PARA GESTIÓN DE ARCHIVOS
# ==============================
def sanitizar_nombre(texto):
    """Sanitiza nombres para usar en filesystem"""
    # Remover caracteres inválidos
    texto = re.sub(r'[<>:"/\\|?*]', '', texto)
    # Reemplazar espacios por guiones bajos
    texto = texto.replace(' ', '_')
    # Convertir a MAYÚSCULAS y remover tildes
    texto = texto.upper()
    texto = texto.replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
    texto = texto.replace('Ó', 'O').replace('Ú', 'U').replace('Ñ', 'N')
    return texto

def sanitizar_nombre_archivo(nombre_archivo):
    """Sanitiza nombres de archivos para filesystem"""
    # Separar nombre y extensión
    nombre, extension = os.path.splitext(nombre_archivo)
    # Sanitizar nombre
    nombre = re.sub(r'[<>:"/\\|?*]', '', nombre)
    nombre = nombre.replace(' ', '_')
    nombre = nombre.lower()
    nombre = nombre.replace('á', 'a').replace('é', 'e').replace('í', 'i')
    nombre = nombre.replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
    # Devolver en minúsculas
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

def obtener_ultimo_tdr(proyecto_id):
    """Obtiene el último TDR subido para un proyecto"""
    db = SessionLocal()
    try:
        tdr = db.query(ProyectoArchivos).filter(
            ProyectoArchivos.proyecto_id == proyecto_id,
            ProyectoArchivos.tipo_archivo_id == 1  # ID para TDR
        ).order_by(ProyectoArchivos.fecha_subida.desc()).first()
        
        return tdr
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
        # Obtener información del tipo de archivo
        tipo_archivo = db.query(TiposArchivo).filter(TiposArchivo.id == tipo_archivo_id).first()
        if not tipo_archivo:
            raise ValueError("Tipo de archivo no válido")
        
        # Obtener ruta del proyecto
        ruta_base = obtener_ruta_proyecto(proyecto_id)
        os.makedirs(ruta_base, exist_ok=True)
        
        # Sanitizar nombre del archivo
        nombre_sanitizado = f"{tipo_archivo.nombre}_{sanitizar_nombre_archivo(archivo.name)}"
        ruta_completa = os.path.join(ruta_base, nombre_sanitizado)
        
        # Verificar duplicados
        if os.path.exists(ruta_completa):
            raise FileExistsError(f"Ya existe un archivo con el nombre: {nombre_sanitizado}")
        
        # Guardar archivo en filesystem
        with open(ruta_completa, "wb") as f:
            f.write(archivo.getvalue())
        
        # Registrar en BD
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
# Funciones de Base de Datos ORM (EXISTENTES)
# ==============================
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

        # Cargar relaciones para evitar lazy loading
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


def crear_proyecto_orm(proyecto_data):
    """Crea un nuevo proyecto usando ORM"""
    try:
        db = SessionLocal()

        nuevo_proyecto = Proyecto(
            nombre=proyecto_data['nombre'],
            descripcion=proyecto_data['descripcion'],
            valor_estimado=proyecto_data['valor_estimado'],
            moneda=proyecto_data['moneda'],
            tipo_cambio_historico=proyecto_data.get('tipo_cambio', 3.80),
            cliente_id=proyecto_data['cliente_id'],
            asignado_a_id=proyecto_data['asignado_a_id'],
            estado_actual=Estado.OPORTUNIDAD.value,
            fecha_deadline_propuesta=proyecto_data.get('fecha_deadline'),
            codigo_convocatoria=proyecto_data.get('codigo_convocatoria')
        )

        db.add(nuevo_proyecto)
        db.commit()
        db.refresh(nuevo_proyecto)
        db.close()

        return nuevo_proyecto
    except Exception as e:
        db.rollback()
        raise e

def actualizar_proyecto_orm(proyecto_id, datos_actualizados):
    """Actualiza un proyecto existente usando ORM"""
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
        proyecto.fecha_deadline_propuesta = datos_actualizados.get('fecha_deadline')
        proyecto.codigo_convocatoria = datos_actualizados.get('codigo_convocatoria')
        proyecto.fecha_ultima_actualizacion = datetime.now()

        # Agregar evento al historial
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

def mover_a_preventa_orm(proyecto_id):
    """Mueve proyecto a preventa usando ORM"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.mover_a_estado(Estado.PREVENTA)
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
# Funciones de conversión de moneda (mantenidas igual)
# ==============================
def convertir_moneda(valor, moneda_origen, moneda_destino, tipo_cambio=3.8):
    """Convierte un valor entre PEN y USD"""
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
# Funciones para deadlines y criticidad (mantenidas igual)
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

# ==============================
# Inicialización
# ==============================
# Listas de opciones (ahora se cargan desde la BD)
EJECUTIVOS_DISPONIBLES = []
CLIENTES_DISPONIBLES = []
MONEDAS_DISPONIBLES = ['PEN', 'USD']

# Session state para edición
if 'editing_project' not in st.session_state:
    st.session_state.editing_project = None

# Session state para modales de archivos
if 'modal_archivos_abierto' not in st.session_state:
    st.session_state.modal_archivos_abierto = False
if 'proyecto_archivos' not in st.session_state:
    st.session_state.proyecto_archivos = None

# ==============================
# Título y navegación
# ==============================
st.title("📊 Dashboard de OPORTUNIDADES")
st.page_link("main_app.py", label="🔙 Volver al Workflow Principal")

# ==============================
# Cargar datos desde ORM
# ==============================
proyectos_todos = cargar_proyectos_activos()
proyectos_oportunidades = [p for p in proyectos_todos if p.estado_actual == Estado.OPORTUNIDAD.value]

# Cargar datos para selects
usuarios_db = cargar_usuarios_activos()
clientes_db = cargar_clientes_activos()
contactos_db = cargar_contactos_activos()

# Actualizar listas de opciones
EJECUTIVOS_DISPONIBLES = [u.nombre for u in usuarios_db]
CLIENTES_DISPONIBLES = [c.nombre for c in clientes_db]

# Mapeos para IDs
usuario_nombre_a_id = {u.nombre: u.id for u in usuarios_db}
cliente_nombre_a_id = {c.nombre: c.id for c in clientes_db}

# Cargar tipos de archivo
tipos_archivo_db = obtener_tipos_archivo()

# ==============================
# MODAL PARA GESTIÓN DE ARCHIVOS
# ==============================
if st.session_state.modal_archivos_abierto and st.session_state.proyecto_archivos:
    with st.sidebar:
        st.header("📁 Gestión de Archivos")
        st.write(f"Proyecto: **{st.session_state.proyecto_archivos.codigo_proyecto}**")
        
        # Subir nuevo archivo
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
                        1  # ID del usuario actual (deberías obtenerlo de session)
                    )
                    st.success("✅ Archivo subido correctamente")
                    time.sleep(1)
                    st.rerun()
                except FileExistsError as e:
                    st.error(f"❌ {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error al subir archivo: {str(e)}")
        
        # Listar archivos existentes
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
    filtro_deadline = st.selectbox("Estado Deadline", ["Todos", "Vencido", "Crítico", "Urgente", "Por Vencer", "Disponible", "Sin Deadline"])

    st.divider()
    st.header("📈 Estadísticas Rápidas")
    total_oportunidades = len(proyectos_oportunidades)
    st.metric("Total Oportunidades", total_oportunidades)

    if total_oportunidades > 0:
        valor_total = 0
        for p in proyectos_oportunidades:
            valor_convertido = convertir_moneda(
                p.valor_estimado,
                p.moneda,
                moneda_visualizacion,
                p.tipo_cambio_historico
            )
            valor_total += valor_convertido

        st.metric("Valor Total Pipeline", formatear_moneda(valor_total, moneda_visualizacion))

        oportunidades_riesgo = len([p for p in proyectos_oportunidades
                                   if (datetime.now() - p.fecha_ultima_actualizacion).days > 7])
        st.metric("En Riesgo", oportunidades_riesgo, delta=-oportunidades_riesgo if oportunidades_riesgo > 0 else 0)

# ==============================
# KPIs principales 
# ==============================
if proyectos_oportunidades:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        valor_pipeline = 0
        for p in proyectos_oportunidades:
            valor_convertido = convertir_moneda(
                p.valor_estimado * 0.25,  # 25% de probabilidad
                p.moneda,
                moneda_visualizacion,
                p.tipo_cambio_historico
            )
            valor_pipeline += valor_convertido

        st.metric("💰 Valor del Pipeline", formatear_moneda(valor_pipeline, moneda_visualizacion))

    with col2:
        total_valor = 0
        for p in proyectos_oportunidades:
            valor_convertido = convertir_moneda(
                p.valor_estimado,
                p.moneda,
                moneda_visualizacion,
                p.tipo_cambio_historico
            )
            total_valor += valor_convertido

        st.metric("💸 Valor Total Estimado", formatear_moneda(total_valor, moneda_visualizacion))

    with col3:
        avg_valor = total_valor / len(proyectos_oportunidades) if proyectos_oportunidades else 0
        st.metric("📊 Valor Promedio", formatear_moneda(avg_valor, moneda_visualizacion))

    with col4:
        # Contar oportunidades con deadline vencido
        oportunidades_vencidas = len([p for p in proyectos_oportunidades
                                    if p.fecha_deadline_propuesta and p.fecha_deadline_propuesta < datetime.now()])
        st.metric("⏰ Deadlines Vencidos", oportunidades_vencidas)

# ==============================
# Formulario para crear nueva oportunidad (MODIFICADO)
# ==============================
st.markdown("---")
with st.expander("➕ Crear Nueva Oportunidad", expanded=False):
    with st.form("form_nueva_oportunidad"):
        col1, col2, col3 = st.columns(3)

        with col1:
            nombre = st.text_input("Nombre de la Oportunidad*", placeholder="Ej: Proyecto Sistema CRM")
            cliente_nombre = st.selectbox("Cliente*", CLIENTES_DISPONIBLES)
            moneda = st.selectbox("Moneda*", MONEDAS_DISPONIBLES, index=0)

        with col2:
            descripcion = st.text_area("Descripción Breve*", placeholder="Describe brevemente el proyecto...")
            ejecutivo_nombre = st.selectbox("Asignar a*", EJECUTIVOS_DISPONIBLES)
            valor_estimado = st.number_input("Valor Estimado*", min_value=0, value=10000, step=1000)

        with col3:
            tipo_cambio = st.number_input("Tipo de Cambio (si aplica)", min_value=0.0, value=3.80, step=0.01,
                                         disabled=moneda != 'USD',
                                         help="Solo aplicable para moneda USD")
            fecha_deadline = st.date_input("Fecha Deadline (Opcional)",
                                         value=datetime.now() + timedelta(days=7),
                                         format="DD/MM/YYYY")
            codigo_convocatoria = st.text_input("Código de Convocatoria (Opcional)", placeholder="CONV-2024-001")

        # NUEVA SECCIÓN: Gestión de archivos TDR
        st.markdown("---")
        st.subheader("📎 Documentos TDR")
        
        col_archivo1, col_archivo2 = st.columns([3, 1])
        with col_archivo1:
            archivo_tdr = st.file_uploader("Subir TDR", type=['pdf', 'docx', 'xlsx'], key="tdr_upload")
        with col_archivo2:
            tipo_tdr = st.selectbox("Tipo", options=[t.nombre for t in tipos_archivo_db], index=0, key="tdr_type")
        
        if archivo_tdr:
            # Verificar duplicados (simulado para nuevo proyecto)
            nombre_sanitizado = f"{tipo_tdr}_{sanitizar_nombre_archivo(archivo_tdr.name)}"
            st.info(f"📄 Archivo a subir: {nombre_sanitizado}")
        
        submitted = st.form_submit_button("🚀 Crear Oportunidad", use_container_width=True)

        if submitted:
            if nombre and cliente_nombre and descripcion and ejecutivo_nombre:
                try:
                    # Convertir nombres a IDs
                    cliente_id = cliente_nombre_a_id[cliente_nombre]
                    asignado_a_id = usuario_nombre_a_id[ejecutivo_nombre]

                    proyecto_data = {
                        'nombre': nombre,
                        'descripcion': descripcion,
                        'valor_estimado': valor_estimado,
                        'moneda': moneda,
                        'tipo_cambio': tipo_cambio if moneda == 'USD' else 3.80,
                        'cliente_id': cliente_id,
                        'asignado_a_id': asignado_a_id,
                        'fecha_deadline': datetime.combine(fecha_deadline, datetime.min.time()) if fecha_deadline else None,
                        'codigo_convocatoria': codigo_convocatoria or None
                    }

                    nuevo_proyecto = crear_proyecto_orm(proyecto_data)
                    
                    # Subir archivo TDR si se proporcionó
                    if archivo_tdr:
                        try:
                            tipo_archivo_id = next((t.id for t in tipos_archivo_db if t.nombre == tipo_tdr), 1)
                            subir_archivo_proyecto(
                                nuevo_proyecto.id,
                                tipo_archivo_id,
                                archivo_tdr,
                                1  # ID del usuario actual
                            )
                        except Exception as e:
                            st.warning(f"⚠️ Oportunidad creada, pero error al subir archivo: {str(e)}")

                    st.success(f"✅ Oportunidad creada exitosamente!")
                    st.info(f"🔢 Código asignado: **{nuevo_proyecto.codigo_proyecto}**")
                    time.sleep(1)
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al crear la oportunidad: {str(e)}")
            else:
                st.error("⚠️ Por favor complete todos los campos obligatorios (*)")

# ==============================
# Formulario de Edición (MODIFICADO)
# ==============================
if st.session_state.editing_project is not None:
    proyecto_editar = next((p for p in proyectos_oportunidades if p.id == st.session_state.editing_project), None)

    if proyecto_editar:
        st.markdown("---")
        with st.expander("✏️ Editando Oportunidad", expanded=True):
            st.info(f"📝 Editando: **{proyecto_editar.codigo_proyecto}** - {proyecto_editar.nombre}")

            # Obtener último TDR para mostrar
            ultimo_tdr = obtener_ultimo_tdr(proyecto_editar.id)
            
            # NUEVA SECCIÓN: Visualización de último TDR
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
                    if st.button("🗑️", help="Eliminar TDR"):
                        # Aquí iría la función para eliminar el archivo
                        st.warning("Funcionalidad de eliminación pendiente")
            else:
                st.info("📝 No hay TDR subidos para este proyecto")
            
            # Botón para ver todos los archivos
            if st.button("👁️ Ver todos los archivos", key="ver_archivos"):
                st.session_state.modal_archivos_abierto = True
                st.session_state.proyecto_archivos = proyecto_editar
                st.rerun()
            
            st.markdown("---")
            
            # Formulario de edición existente
            with st.form("form_editar_oportunidad"):
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
                    # Fecha deadline - editable para oportunidades
                    nueva_fecha_deadline = st.date_input(
                        "Fecha Deadline",
                        value=proyecto_editar.fecha_deadline_propuesta.date() if proyecto_editar.fecha_deadline_propuesta else datetime.now().date(),
                        format="DD/MM/YYYY"
                    )
                    nuevo_tipo_cambio = st.number_input("Tipo de Cambio",
                                                       value=float(proyecto_editar.tipo_cambio_historico),
                                                       step=0.01,
                                                       disabled=nueva_moneda != 'USD')
                    nuevo_codigo_conv = st.text_input("Código Convocatoria",
                                                     value=proyecto_editar.codigo_convocatoria or "")

                # NUEVA SECCIÓN: Subir nuevo archivo en edición
                st.markdown("---")
                st.subheader("📤 Subir nuevo documento")
                
                col_archivo1, col_archivo2 = st.columns([3, 1])
                with col_archivo1:
                    nuevo_archivo = st.file_uploader("Seleccionar archivo", type=['pdf', 'docx', 'xlsx'], key="nuevo_archivo")
                with col_archivo2:
                    nuevo_tipo_archivo = st.selectbox("Tipo", options=[t.nombre for t in tipos_archivo_db], key="nuevo_tipo")
                
                if nuevo_archivo:
                    # Verificar duplicados
                    duplicado, nombre_final, ruta_completa = verificar_archivo_duplicado(
                        proyecto_editar.id, nuevo_tipo_archivo, nuevo_archivo.name
                    )
                    
                    if duplicado:
                        st.error(f"❌ Ya existe un archivo con el nombre: {nombre_final}")
                        st.info("Por favor, cambie el nombre del archivo antes de subirlo")
                    else:
                        st.success(f"✅ Archivo listo para subir: {nombre_final}")

                col1, col2 = st.columns(2)
                with col1:
                    guardar = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                with col2:
                    cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

                if guardar:
                    try:
                        # Convertir nombres a IDs
                        cliente_id = cliente_nombre_a_id[nuevo_cliente_nombre]
                        asignado_a_id = usuario_nombre_a_id[nuevo_ejecutivo_nombre]

                        datos_actualizados = {
                            'nombre': nuevo_nombre,
                            'descripcion': nueva_descripcion,
                            'valor_estimado': nuevo_valor,
                            'moneda': nueva_moneda,
                            'tipo_cambio': nuevo_tipo_cambio,
                            'cliente_id': cliente_id,
                            'asignado_a_id': asignado_a_id,
                            'fecha_deadline': datetime.combine(nueva_fecha_deadline, datetime.min.time()) if nueva_fecha_deadline else None,
                            'codigo_convocatoria': nuevo_codigo_conv or None
                        }

                        # Subir nuevo archivo si se proporcionó y no hay duplicados
                        if nuevo_archivo and not duplicado:
                            try:
                                tipo_archivo_id = next((t.id for t in tipos_archivo_db if t.nombre == nuevo_tipo_archivo), 1)
                                subir_archivo_proyecto(
                                    proyecto_editar.id,
                                    tipo_archivo_id,
                                    nuevo_archivo,
                                    1  # ID del usuario actual
                                )
                            except Exception as e:
                                st.warning(f"⚠️ Cambios guardados, pero error al subir archivo: {str(e)}")

                        actualizar_proyecto_orm(proyecto_editar.id, datos_actualizados)

                        st.session_state.editing_project = None
                        st.success("✅ Cambios guardados exitosamente!")
                        time.sleep(3)
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error al guardar: {str(e)}")

                if cancelar:
                    st.session_state.editing_project = None
                    time.sleep(3)
                    st.rerun()

# ==============================
# Resto del código EXISTENTE (sin modificaciones)
# ==============================
# [Todo el resto del código existente se mantiene igual]
# ... (Aplicar filtros, Vista de Tarjetas, Vista de Tabla, Footer, etc.) ...

# ==============================
# Aplicar filtros (mantenido igual)
# ==============================
proyectos_filtrados = proyectos_oportunidades.copy()

if filtro_ejecutivo != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados if p.asignado_a.nombre == filtro_ejecutivo]

if filtro_cliente != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados if p.cliente.nombre == filtro_cliente]

if filtro_moneda != "Todas":
    proyectos_filtrados = [p for p in proyectos_filtrados if p.moneda == filtro_moneda]

if filtro_riesgo != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados
                          if get_estado_riesgo((datetime.now() - p.fecha_ultima_actualizacion).days) == filtro_riesgo]

if filtro_deadline != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados
                          if calcular_criticidad_deadline(p) == filtro_deadline.lower().replace(' ', '_')]

# ==============================
# Lista de Oportunidades (mantenido igual)
# ==============================
st.markdown("---")
st.header(f"📋 Lista de Oportunidades ({len(proyectos_filtrados)} encontradas)")

if not proyectos_filtrados:
    st.info("🔍 No hay oportunidades que coincidan con los filtros aplicados.")
    st.markdown("**Sugerencias:**")
    st.markdown("- Cambia los filtros en el sidebar")
    st.markdown("- Crea una nueva oportunidad usando el formulario de arriba")

# ==============================
# VISTA DE TARJETAS (mantenido igual excepto llamadas a funciones ORM)
# ==============================
elif vista_modo == "Tarjetas":
    cols = st.columns(3)

    for i, proyecto in enumerate(proyectos_filtrados):
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
        color_riesgo = get_color_riesgo(dias_sin_actualizar)
        estado_riesgo = get_estado_riesgo(dias_sin_actualizar)

        # Calcular criticidad del deadline
        criticidad_deadline = calcular_criticidad_deadline(proyecto)
        estilo_deadline = obtener_estilo_deadline(criticidad_deadline)

        # Convertir valor a moneda de visualización
        valor_convertido = convertir_moneda(
            proyecto.valor_estimado,
            proyecto.moneda,
            moneda_visualizacion,
            proyecto.tipo_cambio_historico
        )

        # Formatear valor según moneda
        valor_formateado = formatear_moneda(valor_convertido, moneda_visualizacion)

        # Calcular próximo contacto
        fecha_proximo_contacto = proyecto.fecha_ultima_actualizacion + timedelta(days=random.randint(1, 5))

        with cols[i % 3]:
            with st.container():
                # Información del deadline
                info_deadline = ""
                if proyecto.fecha_deadline_propuesta:
                    dias_restantes = (proyecto.fecha_deadline_propuesta - datetime.now()).days
                    texto_dias = f"{abs(dias_restantes)} días {'pasados' if dias_restantes < 0 else 'restantes'}"
                    deadline_html = f"""{estilo_deadline['icono']} Deadline: {proyecto.fecha_deadline_propuesta.strftime('%d/%m/%y')} ({texto_dias})"""
                else:
                    deadline_html = f"{estilo_deadline['icono']} Sin deadline"

                # Tarjeta con estilo basado en el deadline
                st.markdown(f"""
                <div style="
                    border: 2px solid {estilo_deadline['color']};
                    border-radius: 12px;
                    padding: 16px;
                    margin: 8px 0;
                    background: linear-gradient(145deg, {estilo_deadline['color']}08, {estilo_deadline['color']}15);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h4 style="color: {estilo_deadline['color']}; margin: 0; font-size: 16px;">{proyecto.codigo_proyecto}</h4>
                    </div>
                    <p style="margin: 8px 0; font-weight: bold; font-size: 14px;">{proyecto.nombre}</p>
                    <p style="margin: 4px 0; font-size: 12px;">👤 {proyecto.asignado_a}</p>
                    <p style="margin: 4px 0; font-size: 12px;">🏢 {proyecto.cliente}</p>
                    <p style="margin: 4px 0; font-size: 12px; color: #666;">💰 {valor_formateado} <small>({proyecto.moneda})</small></p>
                    {deadline_html}
                    <p style="margin: 4px 0; font-size: 11px; color: #666;">📅 Próximo: {fecha_proximo_contacto.strftime('%d/%m')}</p>
                </div>
                """, unsafe_allow_html=True)

                # Botones de acción (actualizados para usar ORM)
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("✏️", key=f"edit_{proyecto.id}", help="Editar oportunidad"):
                        st.session_state.editing_project = proyecto.id
                        st.rerun()

                with col2:
                    if st.button("📞", key=f"contact_{proyecto.id}", help="Registrar contacto"):
                        try:
                            registrar_contacto_orm(proyecto.id)
                            st.success("✅ Contacto registrado!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

                with col3:
                    if st.button("📤", key=f"prev_{proyecto.id}", help="Mover a Preventa"):
                        try:
                            mover_a_preventa_orm(proyecto.id)
                            st.success("✅ Movido a PREVENTA!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

                with col4:
                    if st.button("🗑️", key=f"delete_{proyecto.id}", help="Eliminar oportunidad"):
                        try:
                            eliminar_proyecto_soft_orm(proyecto.id)
                            st.success("🗑️ Oportunidad eliminada!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

# ==============================
# VISTA DE TABLA (mantenido igual excepto llamadas a funciones ORM)
# ==============================
elif vista_modo == "Tabla":
    data = []
    for proyecto in enumerate(proyectos_filtrados):
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
        estado_riesgo = get_estado_riesgo(dias_sin_actualizar)
        criticidad_deadline = calcular_criticidad_deadline(proyecto)
        estilo_deadline = obtener_estilo_deadline(criticidad_deadline)

        # Convertir valor a moneda de visualización
        valor_convertido = convertir_moneda(
            proyecto.valor_estimado,
            proyecto.moneda,
            moneda_visualizacion,
            proyecto.tipo_cambio_historico
        )

        # Formatear valor según moneda
        valor_formateado = formatear_moneda(valor_convertido, moneda_visualizacion)

        # Información del deadline
        info_deadline = "Sin deadline"
        if proyecto.fecha_deadline_propuesta:
            dias_restantes = (proyecto.fecha_deadline_propuesta - datetime.now()).days
            info_deadline = f"{proyecto.fecha_deadline_propuesta.strftime('%d/%m/%y')} ({dias_restantes} días)"

        data.append({
            "Código": proyecto.codigo_proyecto,
            "Nombre": proyecto.nombre,
            "Cliente": proyecto.cliente.nombre if proyecto.cliente else "Sin cliente",
            f"Valor ({moneda_visualizacion})": valor_formateado,
            "Moneda Orig.": proyecto.moneda,
            "Asignado a": proyecto.asignado_a.nombre if proyecto.asignado_a else "Sin asignar",
            "Deadline": info_deadline,
            "Estado Deadline": criticidad_deadline,
            "Días sin Actualizar": dias_sin_actualizar,
            "Estado Riesgo": estado_riesgo,
            "ID": proyecto.id
        })

    if data:
        df = pd.DataFrame(data)

        # Aplicar estilos (mantenido igual)
        def aplicar_color_riesgo(val):
            if val == 'Crítico':
                return 'background-color: #ffe6e6; color: #d32f2f; font-weight: bold'
            elif val == 'En Riesgo':
                return 'background-color: #fff3e0; color: #f57c00; font-weight: bold'
            else:
                return 'background-color: #e8f5e8; color: #388e3c; font-weight: bold'

        def aplicar_color_deadline(val):
            estilos = obtener_estilo_deadline(val)
            return f'background-color: {estilos["fondo"]}; color: {estilos["color"]}; font-weight: bold'

        styled_df = df.style \
            .applymap(aplicar_color_riesgo, subset=['Estado Riesgo']) \
            .applymap(aplicar_color_deadline, subset=['Estado Deadline'])

        # Mostrar tabla sin la columna ID
        columnas_mostrar = [col for col in df.columns if col != "ID"]
        st.dataframe(styled_df.format({"ID": lambda x: ""}),
                    column_config={"ID": None},
                    hide_index=True,
                    use_container_width=True,
                    column_order=columnas_mostrar)

        # Acciones masivas (actualizadas para usar ORM)
        st.markdown("#### 🎛️ Acciones Rápidas")

        for proyecto in proyectos_filtrados:
            with st.expander(f"⚙️ Acciones para {proyecto.codigo_proyecto} - {proyecto.nombre}", expanded=False):
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    if st.button("✏️ Editar", key=f"edit_tab_{proyecto.id}", use_container_width=True):
                        st.session_state.editing_project = proyecto.id
                        st.rerun()

                with col2:
                    if st.button("📞 Contacto", key=f"contact_tab_{proyecto.id}", use_container_width=True):
                        registrar_contacto_orm(proyecto.id)
                        st.success("✅ Contacto registrado!")
                        st.rerun()

                with col3:
                    if st.button("📤 Preventa", key=f"prev_tab_{proyecto.id}", use_container_width=True):
                        mover_a_preventa_orm(proyecto.id)
                        st.success("✅ Movido a PREVENTA!")
                        st.rerun()

                with col4:
                    if st.button("🗑️ Eliminar", key=f"delete_tab_{proyecto.id}", use_container_width=True):
                        eliminar_proyecto_soft_orm(proyecto.id)
                        st.success("🗑️ Eliminado!")
                        st.rerun()

                with col5:
                    with st.popover("📊 Ver Detalles"):
                        st.write(f"**Descripción:** {proyecto.descripcion}")
                        st.write(f"**Moneda:** {proyecto.moneda}")
                        if proyecto.moneda == 'USD':
                            st.write(f"**Tipo de cambio:** {proyecto.tipo_cambio_historico}")
                        if proyecto.fecha_deadline_propuesta:
                            dias_restantes = (proyecto.fecha_deadline_propuesta - datetime.now()).days
                            st.write(f"**Deadline:** {proyecto.fecha_deadline_propuesta.strftime('%d/%m/%Y')} ({dias_restantes} días)")
                        st.write(f"**Creado:** {proyecto.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
                        st.write(f"**Última actualización:** {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}")

# ==============================
# Footer con información adicional (mantenido igual)
# ==============================
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📈 Estadísticas por Deadline")
    if proyectos_oportunidades:
        alta_prioridad = len([p for p in proyectos_oportunidades
                            if calcular_criticidad_deadline(p) in ['vencido', 'critico', 'muy_urgente']])
        media_prioridad = len([p for p in proyectos_oportunidades
                             if calcular_criticidad_deadline(p) in ['urgente', 'por_vencer']])
        baja_prioridad = len([p for p in proyectos_oportunidades
                            if calcular_criticidad_deadline(p) in ['disponible', 'sin_deadline']])

        st.write(f"🔴 Alta Prioridad: {alta_prioridad}")
        st.write(f"🟠 Media Prioridad: {media_prioridad}")
        st.write(f"🟢 Baja Prioridad: {baja_prioridad}")
        st.write(f"📋 Total: {len(proyectos_oportunidades)}")

with col2:
    st.markdown("### 💡 Consejos")
    st.write("• Trabajar oportunidades críticas primero (<1 día)")
    st.write("• Actualiza el estado regularmente")
    st.write("• Mueve a Preventa cuando esté listo")

with col3:
    st.markdown("### 🔗 Navegación")
    st.page_link("main_app.py", label="🏠 Workflow Principal")
    st.write("💾 Todos los cambios se guardan automáticamente")

st.markdown("---")
st.caption(f"💾 Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')} | 📊 {len(proyectos_filtrados)} oportunidades mostradas | 💰 Moneda: {moneda_visualizacion}")
