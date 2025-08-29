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
import requests

# ==============================
# ConfiguraciÃ³n de la pÃ¡gina
# ==============================
st.set_page_config(page_title="Dashboard de Oportunidades", layout="wide", page_icon="ðŸ"Š")

DB_PATH = "proyectos.db"

# ==============================
# FunciÃ³n para obtener tipo de cambio SUNAT
# ==============================
def obtener_tipo_cambio_actual():
    """Obtiene el tipo de cambio actual desde SUNAT"""
    try:
        url = "https://api.apis.net.pe/v1/tipo-cambio-sunat"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['venta']  # Precio de venta SUNAT
    except Exception as e:
        st.warning(f"⚠️ No se pudo obtener tipo de cambio SUNAT: {str(e)}")
        return 3.80  # Valor por defecto

# ==============================
# Funciones de Base de Datos (Sincronizadas con main)
# ==============================
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def inicializar_db():
    """Asegura que la tabla tenga las columnas necesarias para doble moneda y fechas"""
    conn = get_connection()
    c = conn.cursor()

    # Verificar si las columnas existen, si no, agregarlas
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
    
    # Nuevas columnas para gestión temporal
    if 'fecha_limite_cotizacion' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN fecha_limite_cotizacion TEXT")
        print("✅ Columna 'fecha_limite_cotizacion' añadida a la tabla proyectos")
    
    if 'fecha_apertura_convocatoria' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN fecha_apertura_convocatoria TEXT")
        print("✅ Columna 'fecha_apertura_convocatoria' añadida a la tabla proyectos")
    
    if 'tipo_convocatoria' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN tipo_convocatoria TEXT DEFAULT 'privada'")
        print("✅ Columna 'tipo_convocatoria' añadida a la tabla proyectos")
    
    if 'fecha_proximo_contacto' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN fecha_proximo_contacto TEXT")
        print("✅ Columna 'fecha_proximo_contacto' añadida a la tabla proyectos")

    conn.commit()
    conn.close()

def cargar_proyectos():
    """Carga proyectos con manejo robusto - sincronizada con main"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM proyectos WHERE activo = 1 OR activo IS NULL")
        rows = c.fetchall()
        conn.close()

        proyectos = []
        for row in rows:
            try:
                # Obtener información de columnas dinámicamente
                conn_temp = get_connection()
                c_temp = conn_temp.cursor()
                c_temp.execute("PRAGMA table_info(proyectos)")
                columns_info = c_temp.fetchall()
                columns_names = [col[1] for col in columns_info]
                conn_temp.close()

                # Crear diccionario con valores por posición
                row_dict = {}
                for i, col_name in enumerate(columns_names):
                    row_dict[col_name] = row[i] if i < len(row) else None

                # Crear proyecto con valores por defecto seguros
                p = Proyecto(
                    nombre=row_dict.get('nombre', ''),
                    cliente=row_dict.get('cliente', ''),
                    valor_estimado=row_dict.get('valor_estimado', 0),
                    descripcion=row_dict.get('descripcion', ''),
                    asignado_a=row_dict.get('asignado_a', ''),
                    moneda=row_dict.get('moneda', 'PEN'),
                    tipo_cambio_historico=row_dict.get('tipo_cambio_historico', 3.80)
                )
                
                p.id = row_dict.get('id')
                p.codigo_proyecto = row_dict.get('codigo_proyecto', '')

                # Verificar que el estado existe en el enum
                try:
                    estado_str = row_dict.get('estado_actual', 'OPORTUNIDAD')
                    p.estado_actual = Estado[estado_str]
                except KeyError:
                    p.estado_actual = Estado.OPORTUNIDAD

                # Convertir fechas de forma segura
                try:
                    fecha_creacion = row_dict.get('fecha_creacion')
                    if isinstance(fecha_creacion, str) and 'T' in fecha_creacion:
                        p.fecha_creacion = datetime.fromisoformat(fecha_creacion)
                    else:
                        p.fecha_creacion = datetime.now()
                except:
                    p.fecha_creacion = datetime.now()
                    
                try:
                    fecha_update = row_dict.get('fecha_ultima_actualizacion')
                    if isinstance(fecha_update, str) and 'T' in fecha_update:
                        p.fecha_ultima_actualizacion = datetime.fromisoformat(fecha_update)
                    else:
                        p.fecha_ultima_actualizacion = datetime.now()
                except:
                    p.fecha_ultima_actualizacion = datetime.now()

                # Fechas específicas para oportunidades
                try:
                    fecha_limite = row_dict.get('fecha_limite_cotizacion')
                    if fecha_limite:
                        p.fecha_limite_cotizacion = datetime.fromisoformat(fecha_limite)
                    else:
                        p.fecha_limite_cotizacion = None
                except:
                    p.fecha_limite_cotizacion = None

                try:
                    fecha_apertura = row_dict.get('fecha_apertura_convocatoria')
                    if fecha_apertura:
                        p.fecha_apertura_convocatoria = datetime.fromisoformat(fecha_apertura)
                    else:
                        p.fecha_apertura_convocatoria = None
                except:
                    p.fecha_apertura_convocatoria = None

                try:
                    fecha_proximo = row_dict.get('fecha_proximo_contacto')
                    if fecha_proximo:
                        p.fecha_proximo_contacto = datetime.fromisoformat(fecha_proximo)
                    else:
                        p.fecha_proximo_contacto = datetime.now() + timedelta(days=3)
                except:
                    p.fecha_proximo_contacto = datetime.now() + timedelta(days=3)

                # Campos adicionales
                p.tipo_convocatoria = row_dict.get('tipo_convocatoria', 'privada')

                # Manejar historial JSON de forma robusta
                historial_raw = row_dict.get('historial', '[]')
                if historial_raw:
                    try:
                        if isinstance(historial_raw, str) and historial_raw.strip().startswith('['):
                            p.historial = json.loads(historial_raw)
                        else:
                            p.historial = [str(historial_raw)]
                    except:
                        p.historial = []
                else:
                    p.historial = []

                proyectos.append(p)

            except Exception as e:
                st.error(f"❌ Error procesando proyecto {row[0] if row else 'desconocido'}: {str(e)}")
                continue

        return proyectos

    except Exception as e:
        st.error(f"❌ Error inesperado cargando proyectos: {str(e)}")
        return []

def cargar_proyectos_activos():
    """Wrapper para mantener compatibilidad"""
    return [p for p in cargar_proyectos() if p.estado_actual == Estado.OPORTUNIDAD]

def crear_proyecto(proyecto: Proyecto):
    """Inserta un nuevo proyecto en la base de datos con soporte para fechas de deadline"""
    conn = get_connection()
    c = conn.cursor()
    
    # Verificar estructura de la tabla para ver qué columnas tiene
    c.execute("PRAGMA table_info(proyectos)")
    columns = [column[1] for column in c.fetchall()]
    
    # Preparar valores para insertar
    valores_base = [
        proyecto.codigo_proyecto,
        proyecto.nombre,
        proyecto.cliente,
        proyecto.descripcion,
        proyecto.valor_estimado,
        proyecto.asignado_a,
        proyecto.estado_actual.name,
        proyecto.fecha_creacion.isoformat(),
        proyecto.fecha_ultima_actualizacion.isoformat(),
        json.dumps(proyecto.historial)
    ]
    
    query_base = """
        INSERT INTO proyectos
        (codigo_proyecto, nombre, cliente, descripcion, valor_estimado, asignado_a,
         estado_actual, fecha_creacion, fecha_ultima_actualizacion, historial
    """
    
    # Agregar columnas opcionales si existen
    if 'moneda' in columns:
        query_base += ", moneda"
        valores_base.append(getattr(proyecto, 'moneda', 'PEN'))
    
    if 'tipo_cambio_historico' in columns:
        query_base += ", tipo_cambio_historico"
        valores_base.append(getattr(proyecto, 'tipo_cambio_historico', 3.80))
    
    if 'activo' in columns:
        query_base += ", activo"
        valores_base.append(1)
    
    if 'fecha_limite_cotizacion' in columns:
        query_base += ", fecha_limite_cotizacion"
        fecha_limite = getattr(proyecto, 'fecha_limite_cotizacion', None)
        valores_base.append(fecha_limite.isoformat() if fecha_limite else None)
    
    if 'fecha_apertura_convocatoria' in columns:
        query_base += ", fecha_apertura_convocatoria"
        fecha_apertura = getattr(proyecto, 'fecha_apertura_convocatoria', None)
        valores_base.append(fecha_apertura.isoformat() if fecha_apertura else None)
    
    if 'tipo_convocatoria' in columns:
        query_base += ", tipo_convocatoria"
        valores_base.append(getattr(proyecto, 'tipo_convocatoria', 'privada'))
    
    if 'fecha_proximo_contacto' in columns:
        query_base += ", fecha_proximo_contacto"
        fecha_proximo = getattr(proyecto, 'fecha_proximo_contacto', None)
        valores_base.append(fecha_proximo.isoformat() if fecha_proximo else None)

    # Completar query
    placeholders = ", ".join(["?"] * len(valores_base))
    query_complete = query_base + f") VALUES ({placeholders})"
    
    c.execute(query_complete, valores_base)
    proyecto.id = c.lastrowid
    conn.commit()
    conn.close()
    return proyecto

def actualizar_proyecto(proyecto: Proyecto):
    """Actualiza un proyecto existente con soporte para fechas de deadline"""
    conn = get_connection()
    c = conn.cursor()
    
    # Verificar estructura de la tabla
    c.execute("PRAGMA table_info(proyectos)")
    columns = [column[1] for column in c.fetchall()]
    
    # Query base
    query_parts = [
        "nombre=?", "cliente=?", "descripcion=?", "valor_estimado=?", 
        "asignado_a=?", "estado_actual=?", "fecha_ultima_actualizacion=?", "historial=?"
    ]
    valores = [
        proyecto.nombre, proyecto.cliente, proyecto.descripcion, proyecto.valor_estimado,
        proyecto.asignado_a, proyecto.estado_actual.name, 
        proyecto.fecha_ultima_actualizacion.isoformat(), json.dumps(proyecto.historial)
    ]
    
    # Agregar columnas opcionales si existen
    if 'moneda' in columns:
        query_parts.append("moneda=?")
        valores.append(getattr(proyecto, 'moneda', 'PEN'))
    
    if 'tipo_cambio_historico' in columns:
        query_parts.append("tipo_cambio_historico=?")
        valores.append(getattr(proyecto, 'tipo_cambio_historico', 3.80))
    
    if 'fecha_limite_cotizacion' in columns:
        query_parts.append("fecha_limite_cotizacion=?")
        fecha_limite = getattr(proyecto, 'fecha_limite_cotizacion', None)
        valores.append(fecha_limite.isoformat() if fecha_limite else None)
    
    if 'fecha_apertura_convocatoria' in columns:
        query_parts.append("fecha_apertura_convocatoria=?")
        fecha_apertura = getattr(proyecto, 'fecha_apertura_convocatoria', None)
        valores.append(fecha_apertura.isoformat() if fecha_apertura else None)
    
    if 'tipo_convocatoria' in columns:
        query_parts.append("tipo_convocatoria=?")
        valores.append(getattr(proyecto, 'tipo_convocatoria', 'privada'))
    
    if 'fecha_proximo_contacto' in columns:
        query_parts.append("fecha_proximo_contacto=?")
        fecha_proximo = getattr(proyecto, 'fecha_proximo_contacto', None)
        valores.append(fecha_proximo.isoformat() if fecha_proximo else None)
    
    # Completar query
    query = f"UPDATE proyectos SET {', '.join(query_parts)} WHERE id=?"
    valores.append(proyecto.id)
    
    c.execute(query, valores)
    conn.commit()
    conn.close()

def eliminar_proyecto_soft(proyecto_id: int):
    """Soft delete - marca el proyecto como inactivo pero no lo borra"""
    conn = get_connection()
    c = conn.cursor()
    
    # Verificar si existe la columna activo
    c.execute("PRAGMA table_info(proyectos)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'activo' in columns:
        c.execute("""
            UPDATE proyectos
            SET activo = 0, fecha_ultima_actualizacion = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), proyecto_id))
    else:
        # Si no existe la columna activo, crear un registro de eliminación en el historial
        c.execute("SELECT historial FROM proyectos WHERE id = ?", (proyecto_id,))
        result = c.fetchone()
        
        if result:
            historial = json.loads(result[0]) if result[0] else []
            historial.append(f"Eliminado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
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

def registrar_contacto(proyecto_id: int):
    """Registra un contacto y actualiza las fechas"""
    conn = get_connection()
    c = conn.cursor()

    # Obtener proyecto actual
    c.execute("SELECT historial FROM proyectos WHERE id = ?", (proyecto_id,))
    result = c.fetchone()

    if result:
        historial = json.loads(result[0]) if result[0] else []
        historial.append(f"Contacto registrado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        # Actualizar fechas
        nueva_fecha_contacto = datetime.now() + timedelta(days=random.randint(2, 7))

        # Verificar si existe la columna fecha_proximo_contacto
        c.execute("PRAGMA table_info(proyectos)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'fecha_proximo_contacto' in columns:
            c.execute("""
                UPDATE proyectos
                SET fecha_ultima_actualizacion = ?, historial = ?, fecha_proximo_contacto = ?
                WHERE id = ?
            """, (
                datetime.now().isoformat(),
                json.dumps(historial),
                nueva_fecha_contacto.isoformat(),
                proyecto_id
            ))
        else:
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
    return nueva_fecha_contacto

# ==============================
# Funciones de conversión de moneda
# ==============================
def convertir_moneda(valor, moneda_origen, moneda_destino, tipo_cambio=3.8):
    """Convierte un valor entre PEN y USD"""
    if moneda_origen == moneda_destino:
        return valor
    
    if moneda_origen == 'PEN' and moneda_destino == 'USD':
        return valor / tipo_cambio  # Convertir PEN a USD
    elif moneda_origen == 'USD' and moneda_destino == 'PEN':
        return valor * tipo_cambio  # Convertir USD a PEN
    else:
        return valor

def formatear_moneda(valor, moneda):
    """Formatea un valor numérico según la moneda"""
    if moneda == 'PEN':
        return f"S/ {valor:,.2f}"
    else:
        return f"$ {valor:,.2f}"

# ==============================
# Funciones auxiliares para gestión temporal
# ==============================
def calcular_dias_hasta_deadline(fecha_limite):
    """Calcula días restantes hasta el deadline"""
    if not fecha_limite:
        return None
    return (fecha_limite - datetime.now()).days

def get_urgencia_deadline(dias_restantes):
    """Determina el nivel de urgencia basado en días restantes"""
    if dias_restantes is None:
        return "sin_deadline", "#666666"
    elif dias_restantes < 0:
        return "vencido", "#ff1744"
    elif dias_restantes <= 2:
        return "critico", "#ff4444"
    elif dias_restantes <= 7:
        return "urgente", "#ff9800"
    elif dias_restantes <= 14:
        return "atencion", "#ffc107"
    else:
        return "normal", "#4caf50"

def get_color_riesgo(dias_sin_actualizar):
    """Determina el color según la criticidad"""
    if dias_sin_actualizar > 15:
        return "#ff4b4b"  # Rojo - Crítico
    elif dias_sin_actualizar > 7:
        return "#ffa64b"  # Naranja - En Riesgo
    else:
        return "#4caf50"   # Verde - Normal

def get_estado_riesgo(dias_sin_actualizar):
    """Determina el estado textual del riesgo"""
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

# Inicializar session state
if 'tipo_cambio_actual' not in st.session_state:
    st.session_state.tipo_cambio_actual = obtener_tipo_cambio_actual()

# Listas de opciones
CLIENTES_DISPONIBLES = ['TechCorp Solutions', 'Banco Regional', 'RestauGroup SA', 
                        'LogiStock Ltda', 'IndustrialPro', 'HumanTech SA', 
                        'SalesMax Corp', 'Universidad Digital']
EJECUTIVOS_DISPONIBLES = ['Ana García', 'Carlos López', 'María Rodríguez', 
                          'Pedro Martínez', 'Sofia Herrera']
MONEDAS_DISPONIBLES = ['PEN', 'USD']
TIPOS_CONVOCATORIA = ['publica', 'privada', 'concurso', 'invitacion']

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
proyectos_todos = cargar_proyectos()
proyectos_oportunidades = [p for p in proyectos_todos if p.estado_actual == Estado.OPORTUNIDAD]

# ==============================
# Sidebar para filtros y vista
# ==============================
with st.sidebar:
    st.header("🎛️ Opciones de Visualización")
    vista_modo = st.radio("Modo de vista:", ["Tarjetas", "Tabla"])
    
    # Selector de moneda para visualización
    moneda_visualizacion = st.selectbox("Moneda para visualización:", MONEDAS_DISPONIBLES)

    st.header("🔍 Filtros")
    filtro_ejecutivo = st.selectbox("Ejecutivo", ["Todos"] + EJECUTIVOS_DISPONIBLES)
    filtro_cliente = st.selectbox("Cliente", ["Todos"] + CLIENTES_DISPONIBLES)
    filtro_moneda = st.selectbox("Moneda", ["Todas"] + MONEDAS_DISPONIBLES)
    filtro_riesgo = st.selectbox("Estado de Riesgo", ["Todos", "Normal", "En Riesgo", "Crítico"])
    filtro_urgencia = st.selectbox("Urgencia Deadline", ["Todas", "Crítico", "Urgente", "Atención", "Normal", "Sin Deadline"])

    st.divider()
    st.header("📈 Estadísticas Rápidas")
    total_oportunidades = len(proyectos_oportunidades)
    st.metric("Total Oportunidades", total_oportunidades)

    if total_oportunidades > 0:
        # Calcular valor total en la moneda seleccionada
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

        # Estadísticas de deadline
        con_deadline = len([p for p in proyectos_oportunidades if getattr(p, 'fecha_limite_cotizacion', None)])
        st.metric("Con Deadline", con_deadline)

# ==============================
# KPIs principales
# ==============================
if proyectos_oportunidades:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Valor del pipeline (convertido a moneda seleccionada)
        valor_pipeline = 0
        for p in proyectos_oportunidades:
            valor_convertido = convertir_moneda(
                p.valor_estimado * (getattr(p, 'probabilidad_cierre', 25) / 100),
                getattr(p, 'moneda', 'PEN'), 
                moneda_visualizacion,
                getattr(p, 'tipo_cambio_historico', 3.80)
            )
            valor_pipeline += valor_convertido
        
        st.metric("💰 Valor del Pipeline", formatear_moneda(valor_pipeline, moneda_visualizacion))

    with col2:
        # Valor total estimado (convertido a moneda seleccionada)
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
        # Valor promedio (convertido a moneda seleccionada)
        avg_valor = total_valor / len(proyectos_oportunidades) if proyectos_oportunidades else 0
        st.metric("📊 Valor Promedio", formatear_moneda(avg_valor, moneda_visualizacion))

    with col4:
        # Oportunidades con deadline próximo
        deadline_criticas = len([p for p in proyectos_oportunidades 
                               if getattr(p, 'fecha_limite_cotizacion', None) and 
                               calcular_dias_hasta_deadline(p.fecha_limite_cotizacion) is not None and
                               calcular_dias_hasta_deadline(p.fecha_limite_cotizacion) <= 7])
        st.metric("🚨 Deadlines Próximos", deadline_criticas)

# ==============================
# Formulario para crear nueva oportunidad
# ==============================
st.markdown("---")
with st.expander("➕ Crear Nueva Oportunidad", expanded=False):
    with st.form("form_nueva_oportunidad"):
        col1, col2 = st.columns(2)

        with col1:
            nombre = st.text_input("Nombre de la Oportunidad*", placeholder="Ej: Proyecto Sistema CRM")
            cliente = st.selectbox("Cliente*", CLIENTES_DISPONIBLES)
            moneda = st.selectbox("Moneda*", MONEDAS_DISPONIBLES, index=0)
            valor_estimado = st.number_input("Valor Estimado*", min_value=0, value=10000, step=1000)
            tipo_convocatoria = st.selectbox("Tipo de Convocatoria", TIPOS_CONVOCATORIA, index=1)

        with col2:
            descripcion = st.text_area("Descripción Breve*", placeholder="Describe brevemente el proyecto...")
            asignado_a = st.selectbox("Asignar a*", EJECUTIVOS_DISPONIBLES)
            tipo_cambio = st.number_input("Tipo de Cambio (si aplica)", min_value=0.0, 
                                         value=st.session_state.tipo_cambio_actual, step=0.01, 
                                         help="Solo aplicable para moneda USD")
            codigo_convocatoria = st.text_input("Código de Convocatoria (Opcional)", placeholder="CONV-2024-001")

        # Fechas importantes
        st.markdown("#### 📅 Gestión Temporal")
        col_fecha1, col_fecha2 = st.columns(2)
        
        with col_fecha1:
            fecha_apertura = st.date_input("Fecha Apertura Convocatoria", 
                                         value=datetime.now().date(),
                                         help="Fecha en que se abrió la convocatoria")
        
        with col_fecha2:
            fecha_limite = st.date_input("Fecha Límite Cotización*", 
                                       value=datetime.now().date() + timedelta(days=14),
                                       min_value=datetime.now().date(),
                                       help="Fecha límite para presentar la cotización")

        submitted = st.form_submit_button("🚀 Crear Oportunidad", use_container_width=True)

        if submitted:
            if nombre and cliente and descripcion and asignado_a and fecha_limite:
                try:
                    nuevo_proyecto = Proyecto(
                        nombre=nombre,
                        cliente=cliente,
                        valor_estimado=valor_estimado,
                        descripcion=descripcion,
                        asignado_a=asignado_a
                    )
                    
                    # Asignar propiedades de moneda
                    nuevo_proyecto.moneda = moneda
                    if moneda == 'USD':
                        nuevo_proyecto.tipo_cambio_historico = tipo_cambio

                    # Asignar fechas y propiedades temporales
                    nuevo_proyecto.fecha_apertura_convocatoria = datetime.combine(fecha_apertura, datetime.min.time())
                    nuevo_proyecto.fecha_limite_cotizacion = datetime.combine(fecha_limite, datetime.min.time())
                    nuevo_proyecto.tipo_convocatoria = tipo_convocatoria
                    nuevo_proyecto.fecha_proximo_contacto = datetime.now() + timedelta(days=3)

                    # Agregar código de convocatoria si existe
                    if codigo_convocatoria:
                        nuevo_proyecto.codigo_convocatoria = codigo_convocatoria

                    # Actualizar historial con información de fechas
                    dias_para_deadline = calcular_dias_hasta_deadline(nuevo_proyecto.fecha_limite_cotizacion)
                    nuevo_proyecto.historial.append(
                        f"Creado el {nuevo_proyecto.fecha_creacion.strftime('%d/%m/%Y %H:%M')} - "
                        f"Deadline: {fecha_limite.strftime('%d/%m/%Y')} "
                        f"({dias_para_deadline} días restantes)" if dias_para_deadline else "sin deadline"
                    )

                    # Crear en la base de datos
                    nuevo_proyecto = crear_proyecto(nuevo_proyecto)

                    st.success(f"✅ Oportunidad creada exitosamente!")
                    st.info(f"📢 Código asignado: **{nuevo_proyecto.codigo_proyecto}**")
                    
                    # Mostrar información temporal
                    if dias_para_deadline:
                        urgencia, color = get_urgencia_deadline(dias_para_deadline)
                        st.markdown(f"""
                        <div style="background: {color}20; border: 1px solid {color}; padding: 8px; border-radius: 6px; margin: 8px 0;">
                            <strong>⏰ Deadline:</strong> {fecha_limite.strftime('%d/%m/%Y')} 
                            ({dias_para_deadline} días restantes - {urgencia.upper()})
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.balloons()

                    # Recargar datos
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
            st.info(f"🔍 Editando: **{proyecto_editar.codigo_proyecto}** - {proyecto_editar.nombre}")

            # Mostrar información actual de fechas
            fecha_limite_actual = getattr(proyecto_editar, 'fecha_limite_cotizacion', None)
            if fecha_limite_actual:
                dias_restantes = calcular_dias_hasta_deadline(fecha_limite_actual)
                urgencia, color = get_urgencia_deadline(dias_restantes)
                st.markdown(f"""
                <div style="background: {color}20; border: 1px solid {color}; padding: 8px; border-radius: 6px; margin: 8px 0;">
                    <strong>⏰ Deadline actual:</strong> {fecha_limite_actual.strftime('%d/%m/%Y')} 
                    ({dias_restantes} días restantes - {urgencia.upper()})
                </div>
                """, unsafe_allow_html=True)

            with st.form("form_editar_oportunidad"):
                col1, col2 = st.columns(2)

                with col1:
                    nuevo_nombre = st.text_input("Nombre", value=proyecto_editar.nombre)
                    nuevo_cliente = st.selectbox("Cliente", CLIENTES_DISPONIBLES,
                                               index=CLIENTES_DISPONIBLES.index(proyecto_editar.cliente)
                                               if proyecto_editar.cliente in CLIENTES_DISPONIBLES else 0)
                    nueva_moneda = st.selectbox("Moneda", MONEDAS_DISPONIBLES,
                                              index=MONEDAS_DISPONIBLES.index(getattr(proyecto_editar, 'moneda', 'PEN')))
                    nuevo_valor = st.number_input("Valor Estimado", value=int(proyecto_editar.valor_estimado), step=1000)
                    nuevo_tipo_conv = st.selectbox("Tipo de Convocatoria", TIPOS_CONVOCATORIA,
                                                 index=TIPOS_CONVOCATORIA.index(getattr(proyecto_editar, 'tipo_convocatoria', 'privada')))

                with col2:
                    nueva_descripcion = st.text_area("Descripción", value=proyecto_editar.descripcion)
                    nuevo_asignado = st.selectbox("Asignado a", EJECUTIVOS_DISPONIBLES,
                                                index=EJECUTIVOS_DISPONIBLES.index(proyecto_editar.asignado_a)
                                                if proyecto_editar.asignado_a in EJECUTIVOS_DISPONIBLES else 0)
                    nuevo_tipo_cambio = st.number_input("Tipo de Cambio", 
                                                       value=float(getattr(proyecto_editar, 'tipo_cambio_historico', 3.80)),
                                                       step=0.01)
                    nuevo_codigo_conv = st.text_input("Código Convocatoria",
                                                     value=getattr(proyecto_editar, 'codigo_convocatoria', '') or "")

                # Fechas importantes (fecha de presentación NO editable)
                st.markdown("#### 📅 Gestión Temporal")
                col_fecha1, col_fecha2 = st.columns(2)
                
                with col_fecha1:
                    fecha_apertura_actual = getattr(proyecto_editar, 'fecha_apertura_convocatoria', None)
                    nueva_fecha_apertura = st.date_input("Fecha Apertura Convocatoria", 
                                                       value=fecha_apertura_actual.date() if fecha_apertura_actual else datetime.now().date(),
                                                       help="Fecha en que se abrió la convocatoria")
                
                with col_fecha2:
                    # FECHA LÍMITE NO EDITABLE - Solo mostrar
                    if fecha_limite_actual:
                        st.markdown("**Fecha Límite Cotización** (No editable)")
                        st.info(f"📅 {fecha_limite_actual.strftime('%d/%m/%Y')}")
                        st.caption("Esta fecha no se puede modificar una vez establecida")
                    else:
                        st.warning("⚠️ Este proyecto no tiene fecha límite establecida")

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
                            proyecto_editar.tipo_convocatoria = nuevo_tipo_conv
                            proyecto_editar.fecha_apertura_convocatoria = datetime.combine(nueva_fecha_apertura, datetime.min.time())
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

if filtro_urgencia != "Todas":
    def filtro_por_urgencia(proyecto):
        fecha_limite = getattr(proyecto, 'fecha_limite_cotizacion', None)
        if not fecha_limite and filtro_urgencia == "Sin Deadline":
            return True
        elif not fecha_limite:
            return False
        
        dias_restantes = calcular_dias_hasta_deadline(fecha_limite)
        urgencia, _ = get_urgencia_deadline(dias_restantes)
        return urgencia.title() == filtro_urgencia
    
    proyectos_filtrados = [p for p in proyectos_filtrados if filtro_por_urgencia(p)]

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
        dias_sin_actualizar = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
        color = get_color_riesgo(dias_sin_actualizar)
        estado_riesgo = get_estado_riesgo(dias_sin_actualizar)
        
        # Información temporal
        fecha_limite = getattr(proyecto, 'fecha_limite_cotizacion', None)
        dias_deadline = calcular_dias_hasta_deadline(fecha_limite) if fecha_limite else None
        urgencia_deadline, color_deadline = get_urgencia_deadline(dias_deadline)
        
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
        fecha_proximo_contacto = getattr(proyecto, 'fecha_proximo_contacto', None)
        if not fecha_proximo_contacto:
            fecha_proximo_contacto = proyecto.fecha_ultima_actualizacion + timedelta(days=random.randint(2, 7))

        with cols[i % 3]:
            with st.container():
                # Tarjeta con estilo mejorado
                badge_deadline = ""
                if fecha_limite:
                    if dias_deadline is not None:
                        badge_deadline = f"""
                        <div style="background: {color_deadline}; color: white; padding: 2px 6px; border-radius: 8px; font-size: 9px; font-weight: bold; margin: 4px 0;">
                            📅 {urgencia_deadline.upper()}: {abs(dias_deadline)} días {'restantes' if dias_deadline >= 0 else 'vencidos'}
                        </div>
                        """

                st.markdown(f"""
                <div style="
                    border: 2px solid {color};
                    border-radius: 12px;
                    padding: 16px;
                    margin: 8px 0;
                    background: linear-gradient(145deg, {color}08, {color}15);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h4 style="color: {color}; margin: 0; font-size: 16px;">{proyecto.codigo_proyecto}</h4>
                        <span style="background: {color}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 10px; font-weight: bold;">
                            {estado_riesgo}
                        </span>
                    </div>
                    <p style="margin: 8px 0; font-weight: bold; font-size: 14px;">{proyecto.nombre}</p>
                    <p style="margin: 4px 0; font-size: 12px;">👤 {proyecto.asignado_a}</p>
                    <p style="margin: 4px 0; font-size: 12px;">🏢 {proyecto.cliente}</p>
                    <p style="margin: 4px 0; font-size: 12px; color: #666;">💰 {valor_formateado} <small>({moneda_proyecto})</small></p>
                    <p style="margin: 4px 0; font-size: 11px; color: #666;">⏰ {dias_sin_actualizar} días sin actualizar</p>
                    <p style="margin: 4px 0; font-size: 11px; color: #666;">📞 Próximo: {fecha_proximo_contacto.strftime('%d/%m') if isinstance(fecha_proximo_contacto, datetime) else 'No programado'}</p>
                    {badge_deadline}
                </div>
                """, unsafe_allow_html=True)

                # Botones de acción
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("✏️", key=f"edit_{proyecto.id}", help="Editar oportunidad"):
                        st.session_state.editing_project = proyecto.id
                        st.rerun()

                with col2:
                    if st.button("📞", key=f"contact_{proyecto.id}", help="Registrar contacto"):
                        try:
                            nueva_fecha = registrar_contacto(proyecto.id)
                            st.success("✅ Contacto registrado!")
                            st.info(f"📅 Próximo contacto: {nueva_fecha.strftime('%d/%m/%Y')}")
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
        
        # Información temporal
        fecha_limite = getattr(proyecto, 'fecha_limite_cotizacion', None)
        dias_deadline = calcular_dias_hasta_deadline(fecha_limite) if fecha_limite else None
        urgencia_deadline, _ = get_urgencia_deadline(dias_deadline)
        
        # Información de fechas
        fecha_proximo_contacto = getattr(proyecto, 'fecha_proximo_contacto', None)
        if not fecha_proximo_contacto:
            fecha_proximo_contacto = proyecto.fecha_ultima_actualizacion + timedelta(days=random.randint(1, 5))
        
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

        data.append({
            "Código": proyecto.codigo_proyecto,
            "Nombre": proyecto.nombre,
            "Cliente": proyecto.cliente,
            f"Valor ({moneda_visualizacion})": valor_formateado,
            "Moneda Orig.": moneda_proyecto,
            "Asignado a": proyecto.asignado_a,
            "Deadline": fecha_limite.strftime("%d/%m/%Y") if fecha_limite else "Sin deadline",
            "Días Deadline": dias_deadline if dias_deadline is not None else "N/A",
            "Urgencia": urgencia_deadline.title(),
            "Próximo Contacto": fecha_proximo_contacto.strftime("%d/%m/%Y") if isinstance(fecha_proximo_contacto, datetime) else "No programado",
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

        def aplicar_color_urgencia(val):
            if val == 'Vencido':
                return 'background-color: #ffebee; color: #c62828; font-weight: bold'
            elif val == 'Critico':
                return 'background-color: #fff3e0; color: #ef6c00; font-weight: bold'
            elif val == 'Urgente':
                return 'background-color: #fff8e1; color: #f57f17; font-weight: bold'
            elif val == 'Atencion':
                return 'background-color: #f3e5f5; color: #7b1fa2; font-weight: bold'
            else:
                return 'background-color: #e8f5e8; color: #388e3c; font-weight: bold'

        styled_df = df.style.applymap(aplicar_color_riesgo, subset=['Estado Riesgo']) \
                           .applymap(aplicar_color_urgencia, subset=['Urgencia'])

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
            # Información temporal para el expandible
            fecha_limite = getattr(proyecto, 'fecha_limite_cotizacion', None)
            dias_deadline = calcular_dias_hasta_deadline(fecha_limite) if fecha_limite else None
            urgencia_texto = ""
            if fecha_limite and dias_deadline is not None:
                urgencia, color_urgencia = get_urgencia_deadline(dias_deadline)
                urgencia_texto = f" - ⏰ {urgencia.upper()} ({abs(dias_deadline)} días {'restantes' if dias_deadline >= 0 else 'vencidos'})"

            with st.expander(f"⚙️ Acciones para {proyecto.codigo_proyecto} - {proyecto.nombre}{urgencia_texto}", expanded=False):
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    if st.button("✏️ Editar", key=f"edit_tab_{proyecto.id}", use_container_width=True):
                        st.session_state.editing_project = proyecto.id
                        st.rerun()

                with col2:
                    if st.button("📞 Contacto", key=f"contact_tab_{proyecto.id}", use_container_width=True):
                        nueva_fecha = registrar_contacto(proyecto.id)
                        st.success("✅ Contacto registrado!")
                        st.info(f"📅 Próximo: {nueva_fecha.strftime('%d/%m/%Y')}")
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
                        
                        # Información temporal
                        st.write("---")
                        st.write("**📅 Información Temporal:**")
                        
                        fecha_apertura = getattr(proyecto, 'fecha_apertura_convocatoria', None)
                        if fecha_apertura:
                            st.write(f"**Apertura:** {fecha_apertura.strftime('%d/%m/%Y')}")
                        
                        if fecha_limite:
                            st.write(f"**Deadline:** {fecha_limite.strftime('%d/%m/%Y')}")
                            if dias_deadline is not None:
                                st.write(f"**Días restantes:** {dias_deadline}")
                        else:
                            st.write("**Deadline:** No establecido")
                        
                        tipo_conv = getattr(proyecto, 'tipo_convocatoria', 'privada')
                        st.write(f"**Tipo:** {tipo_conv.title()}")
                        
                        st.write(f"**Creado:** {proyecto.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
                        st.write(f"**Última actualización:** {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}")
                        
                        if hasattr(proyecto, 'historial') and proyecto.historial:
                            st.write("**Historial:**")
                            for h in proyecto.historial[-3:]:  # Últimos 3
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
        st.write(f"🟡 En Riesgo: {riesgo}")
        st.write(f"🔴 Críticas: {criticas}")
        
        # Estadísticas de deadline
        con_deadline = len([p for p in proyectos_oportunidades if getattr(p, 'fecha_limite_cotizacion', None)])
        deadline_criticas = len([p for p in proyectos_oportunidades 
                               if getattr(p, 'fecha_limite_cotizacion', None) and 
                               calcular_dias_hasta_deadline(p.fecha_limite_cotizacion) is not None and
                               calcular_dias_hasta_deadline(p.fecha_limite_cotizacion) <= 2])
        
        st.write(f"📅 Con Deadline: {con_deadline}")
        st.write(f"🚨 Deadline Crítico: {deadline_criticas}")

with col2:
    st.markdown("### 💡 Consejos")
    st.write("• Contacta oportunidades críticas (>15 días)")
    st.write("• Revisa deadlines próximos diariamente")
    st.write("• Actualiza el estado regularmente")
    st.write("• Mueve a Preventa cuando esté listo")
    st.write("• Programa contactos antes del deadline")

with col3:
    st.markdown("### 🔗 Navegación")
    st.page_link("main_app.py", label="🏠 Workflow Principal")
    st.write("💾 Todos los cambios se guardan automáticamente")
    st.write("⏰ Deadlines no editables una vez establecidos")

st.markdown("---")
st.caption(f"💾 Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')} | 📊 {len(proyectos_filtrados)} oportunidades mostradas | 💰 Moneda: {moneda_visualizacion} | 💱 TC: S/ {st.session_state.tipo_cambio_actual:.2f}")
