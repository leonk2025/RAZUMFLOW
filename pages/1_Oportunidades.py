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
    """Asegura que la tabla tenga la columna 'activo' para soft delete"""
    conn = get_connection()
    c = conn.cursor()
    
    # Verificar si la columna 'activo' existe, si no, agregarla
    c.execute("PRAGMA table_info(proyectos)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'activo' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN activo INTEGER DEFAULT 1")
        conn.commit()
    
    conn.close()

def cargar_proyectos_activos():
    """Carga solo proyectos activos (no eliminados)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM proyectos WHERE activo = 1 OR activo IS NULL")
    rows = c.fetchall()
    conn.close()

    proyectos = []
    for row in rows:
        if len(row) == 11:  # Sin columna activo
            (id_, codigo, nombre, cliente, descripcion, valor, asignado_a,
             estado, fecha_creacion, fecha_update, historial) = row
        else:  # Con columna activo
            (id_, codigo, nombre, cliente, descripcion, valor, asignado_a,
             estado, fecha_creacion, fecha_update, historial, activo) = row

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
        proyectos.append(p)
    return proyectos

def crear_proyecto(proyecto: Proyecto):
    """Inserta un nuevo proyecto en la base de datos"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO proyectos 
        (codigo_proyecto, nombre, cliente, descripcion, valor_estimado, asignado_a,
         estado_actual, fecha_creacion, fecha_ultima_actualizacion, historial, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
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
    ))
    
    proyecto.id = c.lastrowid
    conn.commit()
    conn.close()
    return proyecto

def actualizar_proyecto(proyecto: Proyecto):
    """Actualiza un proyecto existente"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE proyectos
        SET nombre=?, cliente=?, descripcion=?, valor_estimado=?, asignado_a=?,
            estado_actual=?, fecha_ultima_actualizacion=?, historial=?
        WHERE id=?
    """, (
        proyecto.nombre,
        proyecto.cliente,
        proyecto.descripcion,
        proyecto.valor_estimado,
        proyecto.asignado_a,
        proyecto.estado_actual.name,
        proyecto.fecha_ultima_actualizacion.isoformat(),
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
    
    # Obtener proyecto actual
    c.execute("SELECT historial FROM proyectos WHERE id = ?", (proyecto_id,))
    result = c.fetchone()
    
    if result:
        historial = json.loads(result[0]) if result[0] else []
        historial.append(f"Contacto registrado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Actualizar fechas
        nueva_fecha_contacto = datetime.now() + timedelta(days=random.randint(2, 7))
        
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
# Inicialización
# ==============================
inicializar_db()

# Listas de opciones
CLIENTES_DISPONIBLES = ['Cliente A', 'Cliente B', 'Cliente C', 'Cliente D', 'Cliente E']
EJECUTIVOS_DISPONIBLES = ['Ana García', 'Carlos López', 'María Rodríguez', 'Pedro Martínez', 'Sofia Herrera']

# Session state para edición
if 'editing_project' not in st.session_state:
    st.session_state.editing_project = None

# ==============================
# Funciones auxiliares
# ==============================
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

    st.header("🔍 Filtros")
    filtro_ejecutivo = st.selectbox("Ejecutivo", ["Todos"] + EJECUTIVOS_DISPONIBLES)
    filtro_cliente = st.selectbox("Cliente", ["Todos"] + CLIENTES_DISPONIBLES)
    filtro_riesgo = st.selectbox("Estado de Riesgo", ["Todos", "Normal", "En Riesgo", "Crítico"])

    st.divider()
    st.header("📈 Estadísticas Rápidas")
    total_oportunidades = len(proyectos_oportunidades)
    st.metric("Total Oportunidades", total_oportunidades)
    
    if total_oportunidades > 0:
        valor_total = sum(p.valor_estimado for p in proyectos_oportunidades)
        st.metric("Valor Total Pipeline", f"${valor_total:,.0f}")
        
        oportunidades_riesgo = len([p for p in proyectos_oportunidades 
                                   if (datetime.now() - p.fecha_ultima_actualizacion).days > 7])
        st.metric("En Riesgo", oportunidades_riesgo, delta=-oportunidades_riesgo if oportunidades_riesgo > 0 else 0)

# ==============================
# KPIs principales
# ==============================
if proyectos_oportunidades:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        valor_pipeline = sum(p.valor_estimado * (getattr(p, 'probabilidad_cierre', 25) / 100) 
                           for p in proyectos_oportunidades)
        st.metric("💰 Valor del Pipeline", f"${valor_pipeline:,.0f}")
    
    with col2:
        total_valor = sum(p.valor_estimado for p in proyectos_oportunidades)
        st.metric("💸 Valor Total Estimado", f"${total_valor:,.0f}")
    
    with col3:
        avg_valor = total_valor / len(proyectos_oportunidades)
        st.metric("📊 Valor Promedio", f"${avg_valor:,.0f}")
    
    with col4:
        oportunidades_riesgo = len([p for p in proyectos_oportunidades 
                                   if (datetime.now() - p.fecha_ultima_actualizacion).days > 7])
        st.metric("⚠️ Oportunidades en Riesgo", oportunidades_riesgo)

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
            valor_estimado = st.number_input("Valor Estimado (USD)*", min_value=0, value=10000, step=1000)
        
        with col2:
            descripcion = st.text_area("Descripción Breve*", placeholder="Describe brevemente el proyecto...")
            asignado_a = st.selectbox("Asignar a*", EJECUTIVOS_DISPONIBLES)
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
                    
                    # Agregar código de convocatoria si existe
                    if codigo_convocatoria:
                        nuevo_proyecto.codigo_convocatoria = codigo_convocatoria
                    
                    # Crear en la base de datos
                    nuevo_proyecto = crear_proyecto(nuevo_proyecto)
                    
                    st.success(f"✅ Oportunidad creada exitosamente!")
                    st.info(f"🔢 Código asignado: **{nuevo_proyecto.codigo_proyecto}**")
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
            st.info(f"📝 Editando: **{proyecto_editar.codigo_proyecto}** - {proyecto_editar.nombre}")
            
            with st.form("form_editar_oportunidad"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nuevo_nombre = st.text_input("Nombre", value=proyecto_editar.nombre)
                    nuevo_cliente = st.selectbox("Cliente", CLIENTES_DISPONIBLES,
                                               index=CLIENTES_DISPONIBLES.index(proyecto_editar.cliente)
                                               if proyecto_editar.cliente in CLIENTES_DISPONIBLES else 0)
                    nuevo_valor = st.number_input("Valor Estimado", value=int(proyecto_editar.valor_estimado), step=1000)
                
                with col2:
                    nueva_descripcion = st.text_area("Descripción", value=proyecto_editar.descripcion)
                    nuevo_asignado = st.selectbox("Asignado a", EJECUTIVOS_DISPONIBLES,
                                                index=EJECUTIVOS_DISPONIBLES.index(proyecto_editar.asignado_a)
                                                if proyecto_editar.asignado_a in EJECUTIVOS_DISPONIBLES else 0)
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
                            proyecto_editar.codigo_convocatoria = nuevo_codigo_conv if nuevo_codigo_conv else None
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

if filtro_riesgo != "Todos":
    proyectos_filtrados = [p for p in proyectos_filtrados 
                          if get_estado_riesgo((datetime.now() - p.fecha_ultima_actualizacion).days) == filtro_riesgo]

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
        
        # Calcular próximo contacto (simulado)
        fecha_proximo_contacto = proyecto.fecha_ultima_actualizacion + timedelta(days=random.randint(1, 5))
        
        with cols[i % 3]:
            with st.container():
                # Tarjeta con estilo
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
                    <p style="margin: 4px 0; font-size: 13px; font-weight: bold; color: {color};">💰 ${proyecto.valor_estimado:,.0f}</p>
                    <p style="margin: 4px 0; font-size: 11px; color: #666;">⏰ {dias_sin_actualizar} días sin actualizar</p>
                    <p style="margin: 4px 0; font-size: 11px; color: #666;">📅 Próximo: {fecha_proximo_contacto.strftime('%d/%m')}</p>
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
        fecha_proximo_contacto = proyecto.fecha_ultima_actualizacion + timedelta(days=random.randint(1, 5))

        data.append({
            "Código": proyecto.codigo_proyecto,
            "Nombre": proyecto.nombre,
            "Cliente": proyecto.cliente,
            "Valor Estimado": f"${proyecto.valor_estimado:,.0f}",
            "Asignado a": proyecto.asignado_a,
            "Próximo Contacto": fecha_proximo_contacto.strftime("%d/%m/%Y"),
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

        styled_df = df.style.applymap(aplicar_color_riesgo, subset=['Estado Riesgo'])
        
        # Mostrar tabla sin la columna ID
        st.dataframe(styled_df.format({"ID": lambda x: ""}), 
                    column_config={"ID": None}, 
                    hide_index=True, 
                    use_container_width=True)
        
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
st.caption(f"💾 Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')} | 📊 {len(proyectos_filtrados)} oportunidades mostradas")

