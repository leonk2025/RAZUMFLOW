import streamlit as st
import sqlite3
import json
from datetime import datetime
from models import Proyecto, Estado

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="Workflow de Proyectos", page_icon="🏢", layout="wide")

DB_PATH = "proyectos.db"

# ==============================
# Funciones de Base de Datos
# ==============================
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def verificar_y_crear_tabla():
    """Verifica que la tabla existe y la crea si es necesario"""
    conn = get_connection()
    c = conn.cursor()
    
    # Verificar si la tabla existe
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='proyectos'")
    if not c.fetchone():
        # Crear tabla si no existe
        c.execute("""
            CREATE TABLE proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_proyecto TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                cliente TEXT NOT NULL,
                descripcion TEXT,
                valor_estimado REAL DEFAULT 0,
                asignado_a TEXT,
                estado_actual TEXT DEFAULT 'OPORTUNIDAD',
                fecha_creacion TEXT NOT NULL,
                fecha_ultima_actualizacion TEXT NOT NULL,
                historial TEXT DEFAULT '[]',
                activo INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        st.success("✅ Tabla de proyectos creada exitosamente!")
    
    # Verificar si existe la columna 'activo'
    c.execute("PRAGMA table_info(proyectos)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'activo' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN activo INTEGER DEFAULT 1")
        conn.commit()
    
    conn.close()

def cargar_proyectos():
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM proyectos WHERE activo = 1 OR activo IS NULL")
        rows = c.fetchall()
        conn.close()

        proyectos = []
        for row in rows:
            try:
                # Manejar diferentes estructuras de tabla
                if len(row) == 11:  # Sin columna activo
                    (id_, codigo, nombre, cliente, descripcion, valor, asignado_a,
                     estado, fecha_creacion, fecha_update, historial) = row
                elif len(row) == 12:  # Con columna activo
                    (id_, codigo, nombre, cliente, descripcion, valor, asignado_a,
                     estado, fecha_creacion, fecha_update, historial, activo) = row
                else:
                    st.error(f"❌ Estructura de tabla inesperada: {len(row)} columnas")
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
                
                # Verificar que el estado existe en el enum
                try:
                    p.estado_actual = Estado[estado]
                except KeyError:
                    st.warning(f"⚠️ Estado desconocido '{estado}' para proyecto {codigo}. Usando OPORTUNIDAD.")
                    p.estado_actual = Estado.OPORTUNIDAD
                
                p.fecha_creacion = datetime.fromisoformat(fecha_creacion)
                p.fecha_ultima_actualizacion = datetime.fromisoformat(fecha_update)
                
                # Manejar historial JSON
                try:
                    p.historial = json.loads(historial) if historial else []
                except json.JSONDecodeError:
                    p.historial = [historial] if historial else []
                
                proyectos.append(p)
                
            except Exception as e:
                st.error(f"❌ Error procesando proyecto {row[0] if row else 'desconocido'}: {str(e)}")
                continue
        
        return proyectos
    
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            st.error("❌ La tabla 'proyectos' no existe. Ejecuta el script init_database.py primero.")
            st.stop()
        else:
            st.error(f"❌ Error de base de datos: {str(e)}")
            st.stop()
    except Exception as e:
        st.error(f"❌ Error inesperado cargando proyectos: {str(e)}")
        st.stop()

def actualizar_proyecto(proyecto: Proyecto):
    try:
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
    except Exception as e:
        st.error(f"❌ Error actualizando proyecto: {str(e)}")

# ==============================
# Inicialización segura
# ==============================
try:
    verificar_y_crear_tabla()
    
    if "proyectos" not in st.session_state:
        st.session_state.proyectos = cargar_proyectos()
    if "editando" not in st.session_state:
        st.session_state.editando = None
        
except Exception as e:
    st.error("❌ Error crítico inicializando la aplicación:")
    st.error(str(e))
    st.info("💡 **Solución sugerida:**")
    st.code("python init_database.py", language="bash")
    st.stop()

# ==============================
# Flujo lineal de estados
# ==============================
flujo_estados = [
    Estado.OPORTUNIDAD,
    Estado.PREVENTA,
    Estado.DELIVERY,
    Estado.COBRANZA,
    Estado.POSTVENTA
]

# ==============================
# Funciones auxiliares
# ==============================
def _close_editor():
    st.session_state.editando = None
    st.session_state.proyectos = cargar_proyectos()
    st.rerun()

# ==============================
# Estilos CSS
# ==============================
st.markdown("""
<style>
.card {
  position: relative;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
  padding: 12px 12px 8px 12px;
  margin-bottom: 10px;
  box-shadow: 2px 2px 6px rgba(0,0,0,0.07);
  font-size: 14px;
}
.section-header {
  color: white; padding: 14px; border-radius: 10px; text-align:center; margin-bottom: 14px;
}
.badge {
  background: white; border-radius: 50%; width: 30px; height: 30px;
  display: inline-flex; align-items: center; justify-content: center; font-weight: 700;
}
.status-info {
  background: #f0f9ff; 
  border: 1px solid #0ea5e9; 
  border-radius: 8px; 
  padding: 12px; 
  margin: 16px 0;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# Configuración visual
# ==============================
colores_estados = {
    Estado.OPORTUNIDAD: '#FF6B6B',
    Estado.PREVENTA: '#4ECDC4',
    Estado.DELIVERY: '#45B7D1',
    Estado.COBRANZA: '#96CEB4',
    Estado.POSTVENTA: '#FFEAA7'
}

iconos_estados = {
    Estado.OPORTUNIDAD: '🎯',
    Estado.PREVENTA: '📋',
    Estado.DELIVERY: '🚀',
    Estado.COBRANZA: '💰',
    Estado.POSTVENTA: '🔧'
}

nombres_estados = {
    Estado.OPORTUNIDAD: 'OPORTUNIDADES',
    Estado.PREVENTA: 'PREVENTA',
    Estado.DELIVERY: 'DELIVERY',
    Estado.COBRANZA: 'COBRANZA',
    Estado.POSTVENTA: 'POSTVENTA'
}

# ==============================
# Cabecera
# ==============================
st.title("🏢 Workflow de Gestión de Proyectos")

# Mostrar información del estado de la base de datos
if st.session_state.proyectos:
    total_proyectos = len(st.session_state.proyectos)
    valor_total = sum(p.valor_estimado for p in st.session_state.proyectos)
    
    st.markdown(f"""
    <div class="status-info">
        <strong>📊 Estado del Sistema:</strong> {total_proyectos} proyectos activos | 
        💰 Valor total: ${valor_total:,.0f} | 
        📅 Última carga: {datetime.now().strftime('%H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="status-info">
        <strong>ℹ️ Sistema iniciado:</strong> No hay proyectos en el sistema. 
        <a href="pages/1_Oportunidades.py">Crear nueva oportunidad →</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("## 📋 Vista General del Workflow")
st.markdown("### Visualiza el flujo de proyectos entre estados")

# ==============================
# Función para tarjetas
# ==============================
def crear_tarjeta_proyecto(proyecto, estado):
    color = colores_estados.get(estado, "#ccc")
    dias_sin = (datetime.now() - proyecto.fecha_ultima_actualizacion).days
    extra_line = ""

    if estado == Estado.OPORTUNIDAD:
        color_estado = "green" if dias_sin < 3 else "orange" if dias_sin < 7 else "red"
        extra_line = f"<span style='font-size:12px; color:{color_estado};'>⏰ {dias_sin} días sin actualizar</span>"

    # Crear contenedor para la tarjeta con botón
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f"""
        <div class='card' style='border-color:{color}; margin-bottom: 5px;'>
            <strong>{proyecto.nombre}</strong><br>
            <span style="font-size:12px;">🏢 {proyecto.cliente}</span><br>
            <span style="font-size:12px;">👤 {proyecto.asignado_a}</span><br>
            <span style="font-size:13px; font-weight:bold; color:{color};">💰 ${proyecto.valor_estimado:,.0f}</span><br>
            {extra_line}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("✏️", key=f"edit_{proyecto.id}", help="Editar proyecto"):
            st.session_state.editando = proyecto.id
            st.rerun()

# ==============================
# Construcción del tablero Kanban
# ==============================
if st.session_state.proyectos:
    col1, col2, col3, col4, col5 = st.columns(5)
    cols_map = {
        Estado.OPORTUNIDAD: col1,
        Estado.PREVENTA: col2,
        Estado.DELIVERY: col3,
        Estado.COBRANZA: col4,
        Estado.POSTVENTA: col5
    }

    for estado, col in cols_map.items():
        color = colores_estados[estado]
        proyectos_estado = [p for p in st.session_state.proyectos if p.estado_actual == estado]

        with col:
            st.markdown(
                f"<div class='section-header' style='background:{color};'>"
                f"<h3 style='margin:0;'>{iconos_estados[estado]} {nombres_estados[estado]}</h3>"
                f"<div class='badge' style='color:{color};'>{len(proyectos_estado)}</div>"
                f"</div>", unsafe_allow_html=True
            )

            if not proyectos_estado:
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; color: #666; font-style: italic;'>
                    Sin proyectos en {estado.value}
                </div>
                """, unsafe_allow_html=True)
            else:
                for proyecto in proyectos_estado:
                    with st.container():
                        crear_tarjeta_proyecto(proyecto, estado)

            if estado == Estado.OPORTUNIDAD:
                st.page_link("pages/1_Oportunidades.py", label="📊 Gestionar Oportunidades")
            else:
                st.button("⏳ Próximamente", key=f"btn_{estado}", disabled=True, use_container_width=True)

else:
    st.info("🚀 ¡Bienvenido! No hay proyectos en el sistema aún.")
    st.markdown("### Para comenzar:")
    st.markdown("1. 📊 Ve a **Gestionar Oportunidades**")
    st.markdown("2. ➕ Crea tu primera oportunidad") 
    st.markdown("3. 🔄 Observa cómo fluye por los estados")
    
    st.page_link("pages/1_Oportunidades.py", label="🚀 Crear Primera Oportunidad")

# ==============================
# Sidebar de edición con flujo lineal
# ==============================
if st.session_state.editando:
    proyecto = next((p for p in st.session_state.proyectos if p.id == st.session_state.editando), None)

    if proyecto:
        with st.sidebar:
            st.header(f"✏️ Editar Proyecto #{proyecto.id}")
            st.caption(f"Código: **{proyecto.codigo_proyecto}** • Estado actual: **{proyecto.estado_actual.value}**")

            with st.form(f"form_edit_{proyecto.id}", clear_on_submit=False):
                nuevo_nombre = st.text_input("Nombre", proyecto.nombre)
                nuevo_cliente = st.text_input("Cliente", proyecto.cliente)
                nueva_descripcion = st.text_area("Descripción", proyecto.descripcion)
                nuevo_valor = st.number_input("Valor estimado", min_value=0, step=1000, value=int(proyecto.valor_estimado))
                nuevo_asignado = st.text_input("Asignado a", proyecto.asignado_a)

                col1, col2 = st.columns(2)
                with col1:
                    guardar = st.form_submit_button("💾 Guardar")
                with col2:
                    cancelar = st.form_submit_button("❌ Cancelar")

                if guardar:
                    try:
                        proyecto.nombre = nuevo_nombre
                        proyecto.cliente = nuevo_cliente
                        proyecto.descripcion = nueva_descripcion
                        proyecto.valor_estimado = nuevo_valor
                        proyecto.asignado_a = nuevo_asignado
                        proyecto.fecha_ultima_actualizacion = datetime.now()
                        proyecto.historial.append(f"Editado el {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}")
                        actualizar_proyecto(proyecto)
                        st.success("✅ Guardado!")
                        _close_editor()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

                if cancelar:
                    _close_editor()

            st.markdown("---")
            st.subheader("🔄 Acciones de Flujo")

            idx = flujo_estados.index(proyecto.estado_actual)
            anterior = flujo_estados[idx-1] if idx > 0 else None
            siguiente = flujo_estados[idx+1] if idx < len(flujo_estados)-1 else None

            if anterior and st.button(f"⬅️ Retroceder a {anterior.value}"):
                try:
                    proyecto.estado_actual = anterior
                    proyecto.fecha_ultima_actualizacion = datetime.now()
                    proyecto.historial.append(f"Retrocedido a {anterior.value} el {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}")
                    actualizar_proyecto(proyecto)
                    st.success(f"✅ Movido a {anterior.value}")
                    _close_editor()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            if siguiente and st.button(f"➡️ Avanzar a {siguiente.value}"):
                try:
                    proyecto.estado_actual = siguiente
                    proyecto.fecha_ultima_actualizacion = datetime.now()
                    proyecto.historial.append(f"Avanzado a {siguiente.value} el {proyecto.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')}")
                    actualizar_proyecto(proyecto)
                    st.success(f"✅ Movido a {siguiente.value}")
                    _close_editor()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            st.markdown("---")
            st.subheader("📜 Historial")
            historial_items = getattr(proyecto, "historial", [])[-5:]  # Últimos 5
            for h in historial_items:
                st.write(f"• {h}")
    else:
        st.session_state.editando = None
        st.rerun()

# ==============================
# Resumen general
# ==============================
if st.session_state.proyectos:
    st.markdown("---")
    st.markdown("## 📊 Resumen General por Estado")

    resumen_cols = st.columns(5)
    for i, estado in enumerate(flujo_estados):
        proyectos_estado = [p for p in st.session_state.proyectos if p.estado_actual == estado]
        color = colores_estados[estado]
        total_valor = sum(p.valor_estimado for p in proyectos_estado)

        with resumen_cols[i]:
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background-color: {color}20; border-radius: 10px; border: 2px solid {color};'>
                <div style='font-size: 24px;'>{iconos_estados[estado]}</div>
                <div style='font-weight: bold; color: {color};'>{nombres_estados[estado]}</div>
                <div style='font-size: 20px; font-weight: bold;'>{len(proyectos_estado)}</div>
                <div style='font-size: 12px;'>proyectos</div>
                <div style='font-size: 16px; font-weight: bold; color: {color};'>${total_valor:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

# ==============================
# Footer
# ==============================
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"*📅 Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")

with col2:
    st.markdown("*💡 Haz clic en ✏️ de cada tarjeta para editar*")

# Botón de refresh de datos
if st.button("🔄 Actualizar Datos", help="Recargar datos desde la base de datos"):
    st.session_state.proyectos = cargar_proyectos()
    st.success("✅ Datos actualizados!")
    st.rerun()
