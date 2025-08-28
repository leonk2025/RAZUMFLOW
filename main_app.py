import streamlit as st
import sqlite3
import json
from datetime import datetime
from models import Proyecto, Estado

st.set_page_config(page_title="Gestión de Proyectos", page_icon="📊", layout="wide")

DB_PATH = "proyectos.db"

# ==============================
# Funciones DB
# ==============================
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def cargar_proyectos():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM proyectos")
    rows = c.fetchall()
    conn.close()

    proyectos = []
    for row in rows:
        (
            id_, codigo, nombre, cliente, descripcion, valor, asignado_a,
            estado, fecha_creacion, fecha_update, historial
        ) = row

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
        p.historial = json.loads(historial)
        proyectos.append(p)
    return proyectos

def actualizar_proyecto(proyecto: Proyecto):
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

# ==============================
# Inicialización
# ==============================
if "proyectos" not in st.session_state:
    st.session_state.proyectos = cargar_proyectos()
if "editando" not in st.session_state:
    st.session_state.editando = None

# ==============================
# Render del tablero Kanban
# ==============================
st.title("📊 Tablero de Proyectos")
cols = st.columns(4)
cols_map = {
    Estado.OPORTUNIDAD: cols[0],
    Estado.PREVENTA: cols[1],
    Estado.DELIVERY: cols[2],
    Estado.CERRADO: cols[3],
}

for estado, col in cols_map.items():
    with col:
        st.subheader(estado.name.title())
        proyectos_estado = [p for p in st.session_state.proyectos if p.estado_actual == estado]
        for proyecto in proyectos_estado:
            with st.container():
                c1, c2 = st.columns([0.85, 0.15])
                with c1:
                    st.markdown(
                        f"""
                        <div style='border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:10px;'>
                            <strong>{proyecto.nombre}</strong><br>
                            🏢 {proyecto.cliente}<br>
                            👤 {proyecto.asignado_a}<br>
                            💰 ${proyecto.valor_estimado:,.0f}<br>
                            <span style='font-size:12px; color:gray;'>Última actualización: {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with c2:
                    if st.button("✏️", key=f"edit_{proyecto.id}"):
                        st.session_state.editando = proyecto.id

# ==============================
# Sidebar de edición
# ==============================
st.sidebar.header("⚙️ Editar Proyecto")
if st.session_state.editando is not None:
    proyecto = next((p for p in st.session_state.proyectos if p.id == st.session_state.editando), None)

    if proyecto:
        with st.sidebar.form("editar_form"):
            proyecto.nombre = st.text_input("Nombre", proyecto.nombre)
            proyecto.cliente = st.text_input("Cliente", proyecto.cliente)
            proyecto.descripcion = st.text_area("Descripción", proyecto.descripcion)
            proyecto.valor_estimado = st.number_input("Valor estimado", value=proyecto.valor_estimado, step=1000)
            proyecto.asignado_a = st.text_input("Asignado a", proyecto.asignado_a)

            # Flujo lineal: solo avanzar/retroceder un estado
            idx = list(Estado).index(proyecto.estado_actual)
            if idx > 0:
                retroceder = st.form_submit_button("⬅️ Retroceder")
                if retroceder:
                    proyecto.estado_actual = list(Estado)[idx - 1]
            if idx < len(Estado) - 1:
                avanzar = st.form_submit_button("➡️ Avanzar")
                if avanzar:
                    proyecto.estado_actual = list(Estado)[idx + 1]

            guardar = st.form_submit_button("💾 Guardar cambios")
            if guardar:
                proyecto.fecha_ultima_actualizacion = datetime.now()
                proyecto.historial.append(f"Editado el {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}")
                actualizar_proyecto(proyecto)
                st.session_state.editando = None
                st.rerun()
