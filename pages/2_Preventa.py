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
# FUNCIONES PARA GESTIÓN DE ARCHIVOS (COPIADAS DE OPORTUNIDADES)
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
            f.write(archio.getvalue())
        
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

def mover_a_propuesta_orm(proyecto_id):
    """Mueve proyecto a propuesta usando ORM"""
    try:
        db = SessionLocal()

        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if proyecto:
            proyecto.mover_a_estado(Estado.PROPUESTA)
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
# Funciones para deadlines y criticidad (COPIADAS DE OPORTUNIDADES)
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

# Actualizar listas de opciones
EJECUTIVOS_DISPONIBLES = [u.nombre for u in usuarios_db]
CLIENTES_DISPONIBLES = [c.nombre for c in clientes_db]

# Mapeos para IDs
usuario_nombre_a_id = {u.nombre: u.id for u in usuarios_db}
cliente_nombre_a_id = {c.nombre: c.id for c in clientes_db}

# Cargar tipos de archivo
tipos_archivo_db = obtener_tipos_archivo()

# ==============================
# MODAL PARA GESTIÓN DE ARCHIVOS (COPIADO DE OPORTUNIDADES)
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
    vista_modo = st.radio("Modo de vista:", ["Tarjetas", "Tabla", "Timeline"])

    moneda_visualizacion = st.selectbox("Moneda para visualización:", MONEDAS_DISPONIBLES)

    st.header("🔍 Filtros")
    filtro_ejecutivo = st.selectbox("Ejecutivo", ["Todos"] + EJECUTIVOS_DISPONIBLES)
    filtro_cliente = st.selectbox("Cliente", ["Todos"] + CLIENTES_DISPONIBLES)
    filtro_moneda = st.selectbox("Moneda", ["Todas"] + MONEDAS_DISPONIBLES)
    filtro_riesgo = st.selectbox("Estado de Riesgo", ["Todos", "Normal", "En Riesgo", "Crítico"])
    filtro_deadline = st.selectbox("Estado Deadline", ["Todos", "Vencido", "Crítico", "Urgente", "Por Vencer", "Disponible", "Sin Deadline"])

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
            valor_convertido = convertir_moneda(
                p.valor_estimado * 0.50,  # 50% de probabilidad en preventa
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
        avg_valor = total_valor / len(proyectos_preventa) if proyectos_preventa else 0
        st.metric("📊 Valor Promedio", formatear_moneda(avg_valor, moneda_visualizacion))

    with col4:
        # Contar preventas con deadline vencido
        preventas_vencidas = len([p for p in proyectos_preventa
                                if p.fecha_deadline_propuesta and p.fecha_deadline_propuesta < datetime.now()])
        st.metric("⏰ Deadlines Vencidos", preventas_vencidas)

# ==============================
# Formulario de Edición (COPIADO DE OPORTUNIDADES)
# ==============================
if st.session_state.editing_project is not None:
    proyecto_editar = next((p for p in proyectos_preventa if p.id == st.session_state.editing_project), None)

    if proyecto_editar:
        st.markdown("---")
        with st.expander("✏️ Editando Preventa", expanded=True):
            st.info(f"📝 Editando: **{proyecto_editar.codigo_proyecto}** - {proyecto_editar.nombre}")

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
                    if st.button("🗑️", help="Eliminar TDR"):
                        st.warning("Funcionalidad de eliminación pendiente")
            else:
                st.info("📝 No hay TDR subidos para este proyecto")
            
            # Botón para ver todos los archivos
            if st.button("👁️ Ver todos los archivos", key="ver_archivos"):
                st.session_state.modal_archivos_abierto = True
                st.session_state.proyecto_archivos = proyecto_editar
                st.rerun()
            
            st.markdown("---")
            
            # Formulario de edición
            with st.form("form_editar_preventa"):
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
                    # Fecha deadline - editable para preventa
                    col_fecha, col_hora = st.columns(2)

                    fecha_actual = proyecto_editar.fecha_deadline_propuesta if proyecto_editar.fecha_deadline_propuesta else datetime.now()

                    with col_fecha:
                        nueva_fecha_deadline = st.date_input(
                            "Fecha Deadline",
                            value=proyecto_editar.fecha_deadline_propuesta.date() if proyecto_editar.fecha_deadline_propuesta else datetime.now().date(),
                            format="DD/MM/YYYY"
                        )
                    with col_hora:
                        nueva_hora_deadline = st.time_input(
                        "Hora Deadline",
                        value=fecha_actual.time(),
                        step=3600  # Incrementos de 1 hora
                        )

                    nuevo_tipo_cambio = st.number_input("Tipo de Cambio",
                                                       value=float(proyecto_editar.tipo_cambio_historico),
                                                       step=0.01,
                                                       disabled=nueva_moneda != 'USD')
                    nuevo_codigo_conv = st.text_input("Código Convocatoria",
                                                     value=proyecto_editar.codigo_convocatoria or "")

                # Subir nuevo archivo en edición
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
                            'fecha_deadline': datetime.combine(nueva_fecha_deadline, nueva_hora_deadline) if nueva_fecha_deadline else None,
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

if filtro_deadline != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados
                          if calcular_criticidad_deadline(p) == filtro_deadline.lower().replace(' ', '_')]

# ==============================
# Lista de Preventas
# ==============================
st.markdown("---")
st.header(f"📋 Lista de Preventas ({len(proyectos_filtrados)} encontradas)")

if not proyectos_filtrados:
    st.info("🔍 No hay preventas que coincidan con los filtros aplicados.")
    st.markdown("**Sugerencias:**")
    st.markdown("- Cambia los filtros en el sidebar")
    st.markdown("- Revisa si hay proyectos en estado Oportunidad que puedan moverse a Preventa")

# ==============================
# VISTA DE TARJETAS (COPIADO DE OPORTUNIDADES)
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
        valor_visualizacion = convertir_moneda(
            proyecto.valor_estimado,
            proyecto.moneda,
            moneda_visualizacion,
            proyecto.tipo_cambio_historico
        )

        with cols[i % 3]:
            with st.container():
                # Header con información crítica
                st.markdown(f"""
                <div style='border-radius:10px; padding:15px; margin-bottom:15px; 
                            background-color:{color_riesgo}20; border-left:5px solid {color_riesgo}'>
                    <h4 style='margin:0; color:{color_riesgo}'>{estado_riesgo}</h4>
                    <p style='margin:0; font-size:0.8em; color:#666'>
                        Últ. actualización: {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y')}
                        ({dias_sin_actualizar} días)
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

                # Deadline con criticidad visual
                if proyecto.fecha_deadline_propuesta:
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
                else:
                    st.info("📌 Sin deadline definido")

                # Historial reciente
                historial = cargar_historial_proyecto(proyecto.id)
                if historial:
                    with st.expander("📋 Historial reciente"):
                        for evento in historial:
                            fecha_evento = evento[0].strftime('%d/%m/%Y %H:%M') if hasattr(evento[0], 'strftime') else str(evento[0])
                            st.markdown(f"`{fecha_evento}` - {evento[1]}")

                # Botones de acción
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
                    if st.button("➡️", key=f"move_{proyecto.id}", help="Mover a Propuesta"):
                        if mover_a_propuesta_orm(proyecto.id):
                            st.success("✅ Movido a Propuesta exitosamente!")
                            time.sleep(2)
                            st.rerun()

                st.markdown("---")

# ==============================
# VISTA DE TABLA (COPIADO DE OPORTUNIDADES)
# ==============================
elif vista_modo == "Tabla":
    # Preparar datos para la tabla
    datos_tabla = []
    for proyecto in proyectos_filtrados:
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
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
            'Deadline': proyecto.fecha_deadline_propuesta.strftime('%d/%m/%Y %H:%M') if proyecto.fecha_deadline_propuesta else 'Sin definir',
            'Criticidad': estilo_deadline['icono'],
            'Últ. Actualización': proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y'),
            'Días sin actualizar': dias_sin_actualizar,
            'ID': proyecto.id
        })

    # Mostrar tabla
    df = pd.DataFrame(datos_tabla)
    st.dataframe(
        df,
        column_config={
            "Criticidad": st.column_config.TextColumn("Estado", help="Icono de criticidad del deadline"),
            "ID": None  # Ocultar columna ID
        },
        hide_index=True,
        use_container_width=True
    )

# ==============================
# VISTA DE TIMELINE (NUEVA IMPLEMENTACIÓN)
# ==============================
elif vista_modo == "Timeline":
    st.markdown("### 📅 Vista de Timeline con Deadlines")
    
    # Ordenar proyectos por deadline (los que no tienen deadline van al final)
    proyectos_ordenados = sorted(
        proyectos_filtrados,
        key=lambda x: (x.fecha_deadline_propuesta is None, x.fecha_deadline_propuesta or datetime.max)
    )
    
    for proyecto in proyectos_ordenados:
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
        color_riesgo = get_color_riesgo(dias_sin_actualizar)
        estado_riesgo = get_estado_riesgo(dias_sin_actualizar)
        
        # Calcular criticidad del deadline
        criticidad_deadline = calcular_criticidad_deadline(proyecto)
        estilo_deadline = obtener_estilo_deadline(criticidad_deadline)
        
        # Convertir valor a moneda de visualización
        valor_visualizacion = convertir_moneda(
            proyecto.valor_estimado,
            proyecto.moneda,
            moneda_visualizacion,
            proyecto.tipo_cambio_historico
        )
        
        # Crear tarjeta de timeline
        with st.container():
            col1, col2 = st.columns([1, 4])
            
            with col1:
                # Indicador visual de criticidad (barra lateral)
                st.markdown(f"""
                <div style='background-color:{estilo_deadline['color']}; 
                            height:100px; width:10px; border-radius:5px; 
                            margin:10px 0;'></div>
                """, unsafe_allow_html=True)
                
                # Icono de criticidad
                st.markdown(f"<div style='text-align:center; font-size:1.5em;'>{estilo_deadline['icono']}</div>", 
                           unsafe_allow_html=True)
            
            with col2:
                # Información del proyecto
                st.markdown(f"""
                <div style='border-radius:10px; padding:15px; margin:10px 0; 
                            background-color:#f8f9fa; border-left:3px solid {estilo_deadline['color']}'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <h3 style='margin:0;'>{proyecto.codigo_proyecto} - {proyecto.nombre}</h3>
                        <span style='background-color:{color_riesgo}20; color:{color_riesgo}; 
                                    padding:5px 10px; border-radius:15px; font-size:0.8em;'>
                            {estado_riesgo}
                        </span>
                    </div>
                    
                    <p style='margin:5px 0; color:#666;'>{proyecto.cliente.nombre}</p>
                    
                    <div style='display:flex; justify-content:space-between; margin:10px 0;'>
                        <div>
                            <strong>Valor:</strong> {formatear_moneda(valor_visualizacion, moneda_visualizacion)}<br>
                            <strong>Asignado:</strong> {proyecto.asignado_a.nombre if proyecto.asignado_a else 'Sin asignar'}
                        </div>
                        
                        <div style='text-align:right;'>
                            <strong style='color:{estilo_deadline['color']}'>Deadline</strong><br>
                            {proyecto.fecha_deadline_propuesta.strftime('%d/%m/%Y %H:%M') if proyecto.fecha_deadline_propuesta else 'Sin definir'}<br>
                            {f"<small>{estilo_deadline['icono']} {criticidad_deadline.replace('_', ' ').title()}</small>" if proyecto.fecha_deadline_propuesta else ''}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Botones de acción
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                
                with col_btn1:
                    if st.button("✏️ Editar", key=f"edit_tl_{proyecto.id}", use_container_width=True):
                        st.session_state.editing_project = proyecto.id
                        st.rerun()
                
                with col_btn2:
                    if st.button("📞 Contacto", key=f"contact_tl_{proyecto.id}", use_container_width=True):
                        nuevo_deadline = registrar_contacto_orm(proyecto.id)
                        st.success(f"✅ Contacto registrado. Próximo seguimiento: {nuevo_deadline.strftime('%d/%m/%Y')}")
                        time.sleep(2)
                        st.rerun()
                
                with col_btn3:
                    if st.button("➡️ Propuesta", key=f"move_tl_{proyecto.id}", use_container_width=True):
                        if mover_a_propuesta_orm(proyecto.id):
                            st.success("✅ Movido a Propuesta exitosamente!")
                            time.sleep(2)
                            st.rerun()
                
                with col_btn4:
                    if st.button("📁 Archivos", key=f"files_tl_{proyecto.id}", use_container_width=True):
                        st.session_state.modal_archivos_abierto = True
                        st.session_state.proyecto_archivos = proyecto
                        st.rerun()
            
            st.markdown("---")

# ==============================
# Footer y estadísticas
# ==============================
st.markdown("---")
st.caption(f"📊 Dashboard de Preventa - Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
