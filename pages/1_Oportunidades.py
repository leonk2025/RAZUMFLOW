# 1_Oportunidades.py
# Import time para los sleep
import time
import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
import random
from models import Proyecto, Estado

# ==============================
# Configuración de la página
# ==============================
st.set_page_config(page_title="Dashboard de Oportunidades", layout="wide", page_icon="📊")

DB_PATH = "proyectos.db"

# ==============================
# Funciones de Base de Datos (Sincronizadas con main)
# ==============================
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def inicializar_db():
    """Asegura que la tabla tenga las columnas necesarias para doble moneda"""
    conn = get_connection()
    c = conn.cursor()

    # Verificar si las columnas de moneda existen, si no, agregarlas
    c.execute("PRAGMA table_info(proyectos)")
    columns = [column[1] for column in c.fetchall()]

    if 'moneda' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN moneda TEXT DEFAULT 'PEN'")
        print("✅ Columna 'moneda' añadida a la tabla proyectos")
    
    if 'tipo_cambio_historico' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN tipo_cambio_historico REAL DEFAULT 3.80")
        print("✅ Columna 'tipo_cambio_historico' añadida a la tabla proyectos")
    
    if 'activo' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN activo INTEGER DEFAULT 1")
        print("✅ Columna 'activo' añadida a la tabla proyectos")

    # Verificar y agregar columnas de fechas si no existen
    if 'fecha_deadline_propuesta' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN fecha_deadline_propuesta TEXT")
        print("✅ Columna 'fecha_deadline_propuesta' añadida")
    
    if 'fecha_presentacion_cotizacion' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN fecha_presentacion_cotizacion TEXT")
        print("✅ Columna 'fecha_presentacion_cotizacion' añadida")

    conn.commit()
    conn.close()

def cargar_proyectos_activos():
    """Carga solo proyectos activos (no eliminados) con todas las columnas"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM proyectos WHERE activo = 1 OR activo IS NULL")
    rows = c.fetchall()
    conn.close()

    proyectos = []
    for row in rows:
        # Manejar diferentes estructuras de tabla
        if len(row) == 11:  # Sin columnas de moneda ni activo (estructura antigua)
            (id_, codigo, nombre, cliente, descripcion, valor, asignado_a,
             estado, fecha_creacion, fecha_update, historial) = row
            moneda = 'PEN'
            tipo_cambio = 3.80
            activo = 1
            fecha_deadline = None
            fecha_cotizacion = None
            
        elif len(row) == 12:  # Con columna activo pero sin moneda
            (id_, codigo, nombre, cliente, descripcion, valor, asignado_a,
             estado, fecha_creacion, fecha_update, historial, activo) = row
            moneda = 'PEN'
            tipo_cambio = 3.80
            fecha_deadline = None
            fecha_cotizacion = None
            
        elif len(row) == 14:  # Con moneda pero sin fechas adicionales
            (id_, codigo, nombre, cliente, descripcion, valor, moneda,
             tipo_cambio, asignado_a, estado, fecha_creacion, fecha_update, historial, activo) = row
            fecha_deadline = None
            fecha_cotizacion = None
            
        elif len(row) == 16:  # CON TODAS LAS COLUMNAS
            (id_, codigo, nombre, cliente, descripcion, valor, moneda,
             tipo_cambio, asignado_a, estado, fecha_creacion, fecha_update, 
             fecha_deadline, fecha_cotizacion, historial, activo) = row
        else:
            continue

        p = Proyecto(
            nombre=nombre,
            cliente=cliente,
            valor_estimado=valor,
            descripcion=descripcion,
            asignado_a=asignado_a
        )
        p.id = id_
        p.codigo_proyecto = codigo
        p.estado_actual = Estado[estado]
        p.fecha_creacion = datetime.fromisoformat(fecha_creacion)
        p.fecha_ultima_actualizacion = datetime.fromisoformat(fecha_update)
        p.historial = json.loads(historial) if historial else []
        p.moneda = moneda
        p.tipo_cambio_historico = tipo_cambio
        
        # Asignar fechas adicionales si existen
        if fecha_deadline:
            p.fecha_deadline_propuesta = datetime.fromisoformat(fecha_deadline)
        if fecha_cotizacion:
            p.fecha_presentacion_cotizacion = datetime.fromisoformat(fecha_cotizacion)
            
        proyectos.append(p)
    return proyectos

def crear_proyecto(proyecto: Proyecto):
    """Inserta un nuevo proyecto en la base de datos con soporte para doble moneda"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO proyectos
        (codigo_proyecto, nombre, cliente, descripcion, valor_estimado, moneda,
         tipo_cambio_historico, asignado_a, estado_actual, fecha_creacion, 
         fecha_ultima_actualizacion, fecha_deadline_propuesta, fecha_presentacion_cotizacion,
         historial, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        proyecto.codigo_proyecto,
        proyecto.nombre,
        proyecto.cliente,
        proyecto.descripcion,
        proyecto.valor_estimado,
        getattr(proyecto, 'moneda', 'PEN'),
        getattr(proyecto, 'tipo_cambio_historico', 3.80),
        proyecto.asignado_a,
        proyecto.estado_actual.name,
        proyecto.fecha_creacion.isoformat(),
        proyecto.fecha_ultima_actualizacion.isoformat(),
        proyecto.fecha_deadline_propuesta.isoformat() if proyecto.fecha_deadline_propuesta else None,
        proyecto.fecha_presentacion_cotizacion.isoformat() if proyecto.fecha_presentacion_cotizacion else None,
        json.dumps(proyecto.historial)
    ))

    proyecto.id = c.lastrowid
    conn.commit()
    conn.close()
    return proyecto

def actualizar_proyecto(proyecto: Proyecto):
    """Actualiza un proyecto existente con todas las columnas"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        UPDATE proyectos
        SET nombre=?, cliente=?, descripcion=?, valor_estimado=?, moneda=?,
            tipo_cambio_historico=?, asignado_a=?, estado_actual=?, 
            fecha_ultima_actualizacion=?, fecha_deadline_propuesta=?, 
            fecha_presentacion_cotizacion=?, historial=?
        WHERE id=?
    """, (
        proyecto.nombre,
        proyecto.cliente,
        proyecto.descripcion,
        proyecto.valor_estimado,
        getattr(proyecto, 'moneda', 'PEN'),
        getattr(proyecto, 'tipo_cambio_historico', 3.80),
        proyecto.asignado_a,
        proyecto.estado_actual.name,
        proyecto.fecha_ultima_actualizacion.isoformat(),
        proyecto.fecha_deadline_propuesta.isoformat() if proyecto.fecha_deadline_propuesta else None,
        proyecto.fecha_presentacion_cotizacion.isoformat() if proyecto.fecha_presentacion_cotizacion else None,
        json.dumps(proyecto.historial),
        proyecto.id
    ))
    
    conn.commit()
    conn.close()

def eliminar_proyecto_soft(proyecto_id: int):
    """Soft delete - marca el proyecto como inactivo pero no lo borra"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        UPDATE proyectos
        SET activo = 0, fecha_ultima_actualizacion = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), proyecto_id))
    
    conn.commit()
    conn.close()

def registrar_contacto(proyecto_id: int):
    """Registra un contacto y actualiza las fechas"""
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT historial FROM proyectos WHERE id = ?", (proyecto_id,))
    result = c.fetchone()

    if result:
        historial = json.loads(result[0]) if result[0] else []
        historial.append(f"Contacto registrado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        c.execute("""
            UPDATE proyectos
            SET fecha_ultima_actualizacion = ?, historial = ?
            WHERE id = ?
        """, (
            datetime.now().isoformat(),
            json.dumps(historial),
            proyecto_id
        ))
        conn.commit()

    conn.close()
    return datetime.now() + timedelta(days=random.randint(2, 7))

# ==============================
# Funciones de conversión de moneda
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
inicializar_db()

# Listas de opciones
CLIENTES_DISPONIBLES = ['TechCorp Solutions', 'Banco Regional', 'RestauGroup SA', 
                        'LogiStock Ltda', 'IndustrialPro', 'HumanTech SA', 
                        'SalesMax Corp', 'Universidad Digital']
EJECUTIVOS_DISPONIBLES = ['Ana García', 'Carlos López', 'María Rodríguez', 
                          'Pedro Martínez', 'Sofia Herrera']
MONEDAS_DISPONIBLES = ['PEN', 'USD']

# Session state para edición
if 'editing_project' not in st.session_state:
    st.session_state.editing_project = None

# ==============================
# Título y navegación
# ==============================
st.title("📊 Dashboard de OPORTUNIDADES")
st.page_link("main_app.py", label="🔙 Volver al Workflow Principal")

# ==============================
# Cargar datos
# ==============================
proyectos_todos = cargar_proyectos_activos()
proyectos_oportunidades = [p for p in proyectos_todos if p.estado_actual == Estado.OPORTUNIDAD]

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
                getattr(p, 'moneda', 'PEN'), 
                moneda_visualizacion,
                getattr(p, 'tipo_cambio_historico', 3.80)
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
                getattr(p, 'moneda', 'PEN'), 
                moneda_visualizacion,
                getattr(p, 'tipo_cambio_historico', 3.80)
            )
            valor_pipeline += valor_convertido
        
        st.metric("💰 Valor del Pipeline", formatear_moneda(valor_pipeline, moneda_visualizacion))

    with col2:
        total_valor = 0
        for p in proyectos_oportunidades:
            valor_convertido = convertir_moneda(
                p.valor_estimado,
                getattr(p, 'moneda', 'PEN'), 
                moneda_visualizacion,
                getattr(p, 'tipo_cambio_historico', 3.80)
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
# Formulario para crear nueva oportunidad
# ==============================
st.markdown("---")
with st.expander("➕ Crear Nueva Oportunidad", expanded=False):
    with st.form("form_nueva_oportunidad"):
        col1, col2, col3 = st.columns(3)

        with col1:
            nombre = st.text_input("Nombre de la Oportunidad*", placeholder="Ej: Proyecto Sistema CRM")
            cliente = st.selectbox("Cliente*", CLIENTES_DISPONIBLES)
            moneda = st.selectbox("Moneda*", MONEDAS_DISPONIBLES, index=0)

        with col2:
            descripcion = st.text_area("Descripción Breve*", placeholder="Describe brevemente el proyecto...")
            asignado_a = st.selectbox("Asignar a*", EJECUTIVOS_DISPONIBLES)
            valor_estimado = st.number_input("Valor Estimado*", min_value=0, value=10000, step=1000)

        with col3:
            tipo_cambio = st.number_input("Tipo de Cambio (si aplica)", min_value=0.0, value=3.80, step=0.01, 
                                         disabled=moneda != 'USD',
                                         help="Solo aplicable para moneda USD")
            fecha_deadline = st.date_input("Fecha Deadline (Opcional)", 
                                         value=datetime.now() + timedelta(days=7),
                                         format="DD/MM/YYYY")
            codigo_convocatoria = st.text_input("Código de Convocatoria (Opcional)", placeholder="CONV-2024-001")

        submitted = st.form_submit_button("🚀 Crear Oportunidad", use_container_width=True)

        if submitted:
            if nombre and cliente and descripcion and asignado_a:
                try:
                    nuevo_proyecto = Proyecto(
                        nombre=nombre,
                        cliente=cliente,
                        valor_estimado=valor_estimado,
                        descripcion=descripcion,
                        asignado_a=asignado_a
                    )
                    
                    nuevo_proyecto.moneda = moneda
                    if moneda == 'USD':
                        nuevo_proyecto.tipo_cambio_historico = tipo_cambio
                    
                    # Establecer deadline si se proporcionó
                    nuevo_proyecto.fecha_deadline_propuesta = datetime.combine(fecha_deadline, datetime.min.time())

                    if codigo_convocatoria:
                        nuevo_proyecto.codigo_convocatoria = codigo_convocatoria

                    nuevo_proyecto = crear_proyecto(nuevo_proyecto)

                    st.success(f"✅ Oportunidad creada exitosamente!")
                    st.info(f"🔢 Código asignado: **{nuevo_proyecto.codigo_proyecto}**")
                    time.sleep(1)
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al crear la oportunidad: {str(e)}")
            else:
                st.error("⚠️ Por favor complete todos los campos obligatorios (*)")

# ==============================
# Formulario de Edición
# ==============================
if st.session_state.editing_project is not None:
    proyecto_editar = next((p for p in proyectos_oportunidades if p.id == st.session_state.editing_project), None)

    if proyecto_editar:
        st.markdown("---")
        with st.expander("✏️ Editando Oportunidad", expanded=True):
            st.info(f"📝 Editando: **{proyecto_editar.codigo_proyecto}** - {proyecto_editar.nombre}")

            with st.form("form_editar_oportunidad"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    nuevo_nombre = st.text_input("Nombre", value=proyecto_editar.nombre)
                    nuevo_cliente = st.selectbox("Cliente", CLIENTES_DISPONIBLES,
                                               index=CLIENTES_DISPONIBLES.index(proyecto_editar.cliente)
                                               if proyecto_editar.cliente in CLIENTES_DISPONIBLES else 0)
                    nueva_moneda = st.selectbox("Moneda", MONEDAS_DISPONIBLES,
                                              index=MONEDAS_DISPONIBLES.index(getattr(proyecto_editar, 'moneda', 'PEN')))

                with col2:
                    nueva_descripcion = st.text_area("Descripción", value=proyecto_editar.descripcion)
                    nuevo_asignado = st.selectbox("Asignado a", EJECUTIVOS_DISPONIBLES,
                                                index=EJECUTIVOS_DISPONIBLES.index(proyecto_editar.asignado_a)
                                                if proyecto_editar.asignado_a in EJECUTIVOS_DISPONIBLES else 0)
                    nuevo_valor = st.number_input("Valor Estimado", value=int(proyecto_editar.valor_estimado), step=1000)

                with col3:
                    # Fecha deadline - editable para oportunidades
                    nueva_fecha_deadline = st.date_input(
                        "Fecha Deadline",
                        value=proyecto_editar.fecha_deadline_propuesta.date() if proyecto_editar.fecha_deadline_propuesta else datetime.now().date(),
                        format="DD/MM/YYYY"
                    )
                    nuevo_tipo_cambio = st.number_input("Tipo de Cambio", 
                                                       value=float(getattr(proyecto_editar, 'tipo_cambio_historico', 3.80)),
                                                       step=0.01,
                                                       disabled=nueva_moneda != 'USD')
                    nuevo_codigo_conv = st.text_input("Código Convocatoria",
                                                     value=getattr(proyecto_editar, 'codigo_convocatoria', '') or "")

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                        try:
                            proyecto_editar.nombre = nuevo_nombre
                            proyecto_editar.cliente = nuevo_cliente
                            proyecto_editar.valor_estimado = nuevo_valor
                            proyecto_editar.descripcion = nueva_descripcion
                            proyecto_editar.asignado_a = nuevo_asignado
                            proyecto_editar.moneda = nueva_moneda
                            proyecto_editar.tipo_cambio_historico = nuevo_tipo_cambio
                            proyecto_editar.codigo_convocatoria = nuevo_codigo_conv if nuevo_codigo_conv else None
                            
                            # Actualizar fecha deadline
                            proyecto_editar.fecha_deadline_propuesta = datetime.combine(nueva_fecha_deadline, datetime.min.time())
                            
                            proyecto_editar.fecha_ultima_actualizacion = datetime.now()
                            proyecto_editar.historial.append(f"Editado el {proyecto_editar.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}")

                            actualizar_proyecto(proyecto_editar)

                            st.session_state.editing_project = None
                            st.success("✅ Cambios guardados exitosamente!")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Error al guardar: {str(e)}")

                with col2:
                    if st.form_submit_button("❌ Cancelar", use_container_width=True):
                        st.session_state.editing_project = None
                        st.rerun()

# ==============================
# Aplicar filtros
# ==============================
proyectos_filtrados = proyectos_oportunidades.copy()

if filtro_ejecutivo != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados if p.asignado_a == filtro_ejecutivo]

if filtro_cliente != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados if p.cliente == filtro_cliente]

if filtro_moneda != "Todas":
    proyectos_filtrados = [p for p in proyectos_filtrados if getattr(p, 'moneda', 'PEN') == filtro_moneda]

if filtro_riesgo != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados
                          if get_estado_riesgo((datetime.now() - p.fecha_ultima_actualizacion).days) == filtro_riesgo]

if filtro_deadline != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados
                          if calcular_criticidad_deadline(p) == filtro_deadline.lower().replace(' ', '_')]

# ==============================
# Lista de Oportunidades
# ==============================
st.markdown("---")
st.header(f"📋 Lista de Oportunidades ({len(proyectos_filtrados)} encontradas)")

if not proyectos_filtrados:
    st.info("🔍 No hay oportunidades que coincidan con los filtros aplicados.")
    st.markdown("**Sugerencias:**")
    st.markdown("- Cambia los filtros en el sidebar")
    st.markdown("- Crea una nueva oportunidad usando el formulario de arriba")

# ==============================
# VISTA DE TARJETAS
# ==============================

elif vista_modo == "Tarjetas":
    cols = st.columns(3)

    for i, proyecto in enumerate(proyectos_filtrados):
        # Calcular criticidad del deadline
        criticidad_deadline = calcular_criticidad_deadline(proyecto)
        estilo_deadline = obtener_estilo_deadline(criticidad_deadline)

        # Obtener información de moneda
        moneda_proyecto = getattr(proyecto, 'moneda', 'PEN')
        tipo_cambio = getattr(proyecto, 'tipo_cambio_historico', 3.80)

        # Convertir valor a moneda de visualización
        valor_convertido = convertir_moneda(
            proyecto.valor_estimado,
            moneda_proyecto,
            moneda_visualizacion,
            tipo_cambio
        )

        # Formatear valor según moneda
        valor_formateado = formatear_moneda(valor_convertido, moneda_visualizacion)

        # Calcular próximo contacto
        fecha_proximo_contacto = proyecto.fecha_ultima_actualizacion + timedelta(days=random.randint(1, 5))

        with cols[i % 3]:
            with st.container():
                # Información del deadline - construida directamente en el HTML
                deadline_html = ""
                if proyecto.fecha_deadline_propuesta:
                    dias_restantes = (proyecto.fecha_deadline_propuesta - datetime.now()).days
                    texto_dias = f"{abs(dias_restantes)} días {'pasados' if dias_restantes < 0 else 'restantes'}"
                    deadline_html = {estilo_deadline['icono']} Deadline: {proyecto.fecha_deadline_propuesta.strftime('%d/%m/%y')}({texto_dias})
                    
                else:
                    deadline_html = {estilo_deadline['icono']} Sin deadline
            

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
                    <p style="margin: 4px 0; font-size: 12px; color: #666;">💰 {valor_formateado} <small>({moneda_proyecto})</small></p>
                    {deadline_html}
                    <p style="margin: 4px 0; font-size: 11px; color: #666;">📅 Próximo: {fecha_proximo_contacto.strftime('%d/%m')}</p>
                </div>
                """, unsafe_allow_html=True)

                # Botones de acción (se mantienen igual)
                col1, col2, col3, col4 = st.columns(4)
               
                with col1:
                    if st.button("✏️", key=f"edit_{proyecto.id}", help="Editar oportunidad"):
                        st.session_state.editing_project = proyecto.id
                        st.rerun()

                with col2:
                    if st.button("📞", key=f"contact_{proyecto.id}", help="Registrar contacto"):
                        try:
                            registrar_contacto(proyecto.id)
                            st.success("✅ Contacto registrado!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

                with col3:
                    if st.button("📤", key=f"prev_{proyecto.id}", help="Mover a Preventa"):
                        try:
                            proyecto.estado_actual = Estado.PREVENTA
                            proyecto.fecha_ultima_actualizacion = datetime.now()
                            proyecto.historial.append(f"Movido a PREVENTA el {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}")
                            actualizar_proyecto(proyecto)
                            st.success("✅ Movido a PREVENTA!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

                with col4:
                    if st.button("🗑️", key=f"delete_{proyecto.id}", help="Eliminar oportunidad"):
                        try:
                            eliminar_proyecto_soft(proyecto.id)
                            st.success("🗑️ Oportunidad eliminada!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

# ==============================
# VISTA DE TABLA
# ==============================
elif vista_modo == "Tabla":
    data = []
    for proyecto in proyectos_filtrados:
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
        estado_riesgo = get_estado_riesgo(dias_sin_actualizar)
        criticidad_deadline = calcular_criticidad_deadline(proyecto)
        estilo_deadline = obtener_estilo_deadline(criticidad_deadline)
        
        # Obtener información de moneda
        moneda_proyecto = getattr(proyecto, 'moneda', 'PEN')
        tipo_cambio = getattr(proyecto, 'tipo_cambio_historico', 3.80)
        
        # Convertir valor a moneda de visualización
        valor_convertido = convertir_moneda(
            proyecto.valor_estimado, 
            moneda_proyecto, 
            moneda_visualizacion,
            tipo_cambio
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
            "Cliente": proyecto.cliente,
            f"Valor ({moneda_visualizacion})": valor_formateado,
            "Moneda Orig.": moneda_proyecto,
            "Asignado a": proyecto.asignado_a,
            "Deadline": info_deadline,
            "Estado Deadline": criticidad_deadline,
            "Días sin Actualizar": dias_sin_actualizar,
            "Estado Riesgo": estado_riesgo,
            "ID": proyecto.id
        })

    if data:
        df = pd.DataFrame(data)

        # Aplicar estilos
        def aplicar_color_riesgo(val):
            if val == 'Crítico':
                return 'background-color: #ffe6e6; color: #d32f2f; font-weight: bold'
            elif val == 'En Riesgo':
                return 'background-color: #fff3e0; color: #f57c00; font-weight: bold'
            else:
                return 'background-color: #e8f5e8; color: #388e3c; font-weight: bold'

        def aplicar_color_deadline(val):
            estilos = obtener_estilo_deadline(val)  # ← Usar la misma función de estilos
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

        # Acciones masivas
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
                        registrar_contacto(proyecto.id)
                        st.success("✅ Contacto registrado!")
                        st.rerun()

                with col3:
                    if st.button("📤 Preventa", key=f"prev_tab_{proyecto.id}", use_container_width=True):
                        proyecto.estado_actual = Estado.PREVENTA
                        proyecto.fecha_ultima_actualizacion = datetime.now()
                        proyecto.historial.append(f"Movido a PREVENTA el {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}")
                        actualizar_proyecto(proyecto)
                        st.success("✅ Movido a PREVENTA!")
                        st.rerun()

                with col4:
                    if st.button("🗑️ Eliminar", key=f"delete_tab_{proyecto.id}", use_container_width=True):
                        eliminar_proyecto_soft(proyecto.id)
                        st.success("🗑️ Eliminado!")
                        st.rerun()

                with col5:
                    with st.popover("📊 Ver Detalles"):
                        st.write(f"**Descripción:** {proyecto.descripcion}")
                        st.write(f"**Moneda:** {getattr(proyecto, 'moneda', 'PEN')}")
                        if getattr(proyecto, 'moneda', 'PEN') == 'USD':
                            st.write(f"**Tipo de cambio:** {getattr(proyecto, 'tipo_cambio_historico', 3.80)}")
                        if proyecto.fecha_deadline_propuesta:
                            dias_restantes = (proyecto.fecha_deadline_propuesta - datetime.now()).days
                            st.write(f"**Deadline:** {proyecto.fecha_deadline_propuesta.strftime('%d/%m/%Y')} ({dias_restantes} días)")
                        st.write(f"**Creado:** {proyecto.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
                        st.write(f"**Última actualización:** {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}")
                        if hasattr(proyecto, 'historial') and proyecto.historial:
                            st.write("**Historial:**")
                            for h in proyecto.historial[-3:]:
                                st.write(f"• {h}")

# ==============================
# Footer con información adicional
# ==============================
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📈 Estadísticas")
    if proyectos_oportunidades:
        criticas = len([p for p in proyectos_oportunidades
                       if (datetime.now() - p.fecha_ultima_actualizacion).days > 15])
        riesgo = len([p for p in proyectos_oportunidades
                     if 7 < (datetime.now() - p.fecha_ultima_actualizacion).days <= 15])
        normales = len(proyectos_oportunidades) - criticas - riesgo

        st.write(f"🟢 Normales: {normales}")
        st.write(f"🟠 En Riesgo: {riesgo}")
        st.write(f"🔴 Críticas: {criticas}")

with col2:
    st.markdown("### 💡 Consejos")
    st.write("• Contacta oportunidades críticas (>15 días)")
    st.write("• Actualiza el estado regularmente")
    st.write("• Mueve a Preventa cuando esté listo")

with col3:
    st.markdown("### 🔗 Navegación")
    st.page_link("main_app.py", label="🏠 Workflow Principal")
    st.write("💾 Todos los cambios se guardan automáticamente")

st.markdown("---")
st.caption(f"💾 Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')} | 📊 {len(proyectos_filtrados)} oportunidades mostradas | 💰 Moneda: {moneda_visualizacion}")
