# 1_Oportunidades.py
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
EJECUTIVOS_DISPONIBLES = ["Carlos", "Ana", "Luis", "María"]

# ==============================
# Funciones de Base de Datos
# ==============================
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def inicializar_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("PRAGMA table_info(proyectos)")
    columns = [column[1] for column in c.fetchall()]

    if 'moneda' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN moneda TEXT DEFAULT 'PEN'")
    if 'tipo_cambio_historico' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN tipo_cambio_historico REAL DEFAULT 3.80")
    if 'activo' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN activo INTEGER DEFAULT 1")
    if 'fecha_deadline_propuesta' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN fecha_deadline_propuesta TEXT")
    if 'fecha_presentacion_cotizacion' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN fecha_presentacion_cotizacion TEXT")

    conn.commit()
    conn.close()

def cargar_proyectos_activos():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM proyectos WHERE activo = 1 OR activo IS NULL")
    rows = c.fetchall()
    conn.close()

    proyectos = []
    for row in rows:
        try:
            if len(row) >= 15:
                (id_, codigo, nombre, cliente, descripcion, valor, moneda,
                 tipo_cambio, asignado_a, estado, fecha_creacion, fecha_update,
                 fecha_deadline, fecha_cotizacion, historial, activo) = row
            elif len(row) == 12:
                (id_, codigo, nombre, cliente, descripcion, valor, asignado_a,
                 estado, fecha_creacion, fecha_update, historial, activo) = row
                moneda = 'PEN'; tipo_cambio = 3.80; fecha_deadline = None; fecha_cotizacion = None
            else:
                continue

            p = Proyecto(nombre=nombre, cliente=cliente, valor_estimado=valor, descripcion=descripcion, asignado_a=asignado_a)
            p.id = id_
            p.codigo_proyecto = codigo
            p.estado_actual = Estado[estado]
            p.fecha_creacion = datetime.fromisoformat(fecha_creacion)
            p.fecha_ultima_actualizacion = datetime.fromisoformat(fecha_update)
            p.historial = json.loads(historial) if historial else []
            p.moneda = moneda
            p.tipo_cambio_historico = tipo_cambio
            if fecha_deadline:
                try: p.fecha_deadline_propuesta = datetime.fromisoformat(fecha_deadline)
                except: p.fecha_deadline_propuesta = None
            if fecha_cotizacion:
                try: p.fecha_presentacion_cotizacion = datetime.fromisoformat(fecha_cotizacion)
                except: p.fecha_presentacion_cotizacion = None
            proyectos.append(p)
        except Exception as e:
            st.error(f"❌ Error cargando proyecto {row[0]}: {e}")
    return proyectos

def crear_proyecto(proyecto: Proyecto):
    conn = get_connection(); c = conn.cursor(); c.execute("PRAGMA table_info(proyectos)"); columns = [column[1] for column in c.fetchall()]
    if 'fecha_deadline_propuesta' in columns and 'fecha_presentacion_cotizacion' in columns:
        c.execute("""
            INSERT INTO proyectos
            (codigo_proyecto, nombre, cliente, descripcion, valor_estimado, moneda,
             tipo_cambio_historico, asignado_a, estado_actual, fecha_creacion,
             fecha_ultima_actualizacion, fecha_deadline_propuesta, fecha_presentacion_cotizacion,
             historial, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            proyecto.codigo_proyecto, proyecto.nombre, proyecto.cliente, proyecto.descripcion, proyecto.valor_estimado,
            getattr(proyecto, 'moneda', 'PEN'), getattr(proyecto, 'tipo_cambio_historico', 3.80), proyecto.asignado_a,
            proyecto.estado_actual.name, proyecto.fecha_creacion.isoformat(), proyecto.fecha_ultima_actualizacion.isoformat(),
            proyecto.fecha_deadline_propuesta.isoformat() if proyecto.fecha_deadline_propuesta else None,
            proyecto.fecha_presentacion_cotizacion.isoformat() if proyecto.fecha_presentacion_cotizacion else None,
            json.dumps(proyecto.historial)
        ))
    proyecto.id = c.lastrowid; conn.commit(); conn.close(); return proyecto

def actualizar_proyecto(proyecto: Proyecto):
    conn = get_connection(); c = conn.cursor(); c.execute("PRAGMA table_info(proyectos)"); columns = [column[1] for column in c.fetchall()]
    if 'fecha_deadline_propuesta' in columns and 'fecha_presentacion_cotizacion' in columns:
        c.execute("""
            UPDATE proyectos
            SET nombre=?, cliente=?, descripcion=?, valor_estimado=?, moneda=?, tipo_cambio_historico=?, asignado_a=?, estado_actual=?,
                fecha_ultima_actualizacion=?, fecha_deadline_propuesta=?, fecha_presentacion_cotizacion=?, historial=?
            WHERE id=?
        """, (
            proyecto.nombre, proyecto.cliente, proyecto.descripcion, proyecto.valor_estimado, getattr(proyecto, 'moneda', 'PEN'),
            getattr(proyecto, 'tipo_cambio_historico', 3.80), proyecto.asignado_a, proyecto.estado_actual.name,
            proyecto.fecha_ultima_actualizacion.isoformat(),
            proyecto.fecha_deadline_propuesta.isoformat() if proyecto.fecha_deadline_propuesta else None,
            proyecto.fecha_presentacion_cotizacion.isoformat() if proyecto.fecha_presentacion_cotizacion else None,
            json.dumps(proyecto.historial), proyecto.id
        ))
    conn.commit(); conn.close()

# ==============================
# Interfaz Streamlit (look & feel original + fechas deadline)
# ==============================

def mostrar_tarjeta(proyecto: Proyecto):
    with st.container():
        st.markdown(f"### {proyecto.nombre} ({proyecto.codigo_proyecto})")
        st.write(f"Cliente: {proyecto.cliente}")
        st.write(f"Estado: {proyecto.estado_actual.name}")
        st.write(f"Valor estimado: {proyecto.valor_estimado} {proyecto.moneda}")
        if proyecto.fecha_deadline_propuesta:
            nivel = proyecto.obtener_nivel_alerta_deadline()
            color_map = {"Vencido": "#FF4C4C", "Crítico": "#FF8000", "Urgente": "#FFD700", "Normal": "#4CAF50"}
            st.markdown(f"<div style='padding:5px; border-radius:5px; background:{color_map.get(nivel,'#EEE')}; color:black'>📅 Deadline: {proyecto.fecha_deadline_propuesta.strftime('%d/%m/%Y')} ({nivel})</div>", unsafe_allow_html=True)

def mostrar_tabla(proyectos):
    data = []
    for p in proyectos:
        nivel = p.obtener_nivel_alerta_deadline() if p.fecha_deadline_propuesta else "-"
        deadline = p.fecha_deadline_propuesta.strftime('%d/%m/%Y') if p.fecha_deadline_propuesta else "-"
        data.append([p.codigo_proyecto, p.nombre, p.cliente, p.estado_actual.name, p.valor_estimado, p.moneda, deadline, nivel])
    df = pd.DataFrame(data, columns=["Código","Nombre","Cliente","Estado","Valor","Moneda","Deadline","Criticidad"])
    st.dataframe(df, use_container_width=True)

# ==============================
# Página principal
# ==============================
inicializar_db()
proyectos = cargar_proyectos_activos()

vista = st.radio("Vista", ["Tarjetas", "Tabla"], horizontal=True)
if vista == "Tarjetas":
    for p in proyectos:
        mostrar_tarjeta(p)
elif vista == "Tabla":
    mostrar_tabla(proyectos)
