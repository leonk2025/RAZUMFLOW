import streamlit as st
import sqlite3
import json
from datetime import datetime
from models import Proyecto, Estado
import requests

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="Workflow de Proyectos", page_icon="🏢", layout="wide")

DB_PATH = "proyectos.db"

# ==============================
# Función para obtener tipo de cambio SUNAT
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
# Funciones de Base de Datos
# ==============================
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def verificar_y_crear_tablas():
    """Verifica que las tablas existen y las crea si es necesario"""
    conn = get_connection()
    c = conn.cursor()

    # Verificar si la tabla proyectos existe
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='proyectos'")
    if not c.fetchone():
        # Crear tabla proyectos si no existe
        c.execute("""
            CREATE TABLE proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_proyecto TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                cliente_id INTEGER,
                descripcion TEXT,
                valor_estimado REAL DEFAULT 0,
                moneda TEXT DEFAULT 'PEN',
                tipo_cambio_historico REAL DEFAULT 3.80,
                asignado_a_id INTEGER,
                estado_actual TEXT DEFAULT 'OPORTUNIDAD',
                fecha_creacion TEXT NOT NULL,
                fecha_ultima_actualizacion TEXT NOT NULL,
                fecha_deadline_propuesta TEXT,
                fecha_presentacion_cotizacion TEXT,
                historial TEXT DEFAULT '[]',
                activo INTEGER DEFAULT 1,
                contacto_principal_id INTEGER
            )
        """)
        conn.commit()
        st.success("✅ Tabla de proyectos creada exitosamente!")

    # Verificar si la tabla usuarios existe
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
    if not c.fetchone():
        # Crear tabla usuarios si no existe
        c.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telefono TEXT,
                cargo TEXT,
                rol TEXT DEFAULT 'operacion',
                activo INTEGER DEFAULT 1,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Insertar usuarios por defecto
        usuarios = [
            ('Carlos León Legua', 'cgleon@razumtek.pe', '980335105', 'CEO', 'admin'),
            ('Fabiola Sánchez Medina', 'fabiola.sanchez@razumtek.pe', '917306607', 'Logística', 'operacion'),
            ('Yusneidy Nuñez Gonzales', 'yusneidy.nunez@razumtek.pe', '945833560', 'Ejecutiva Comercial', 'operacion')
        ]
        for usuario in usuarios:
            c.execute("INSERT INTO usuarios (nombre, email, telefono, cargo, rol) VALUES (?, ?, ?, ?, ?)", usuario)
        conn.commit()
        st.success("✅ Tabla de usuarios creada exitosamente!")

    # Verificar si la tabla clientes existe
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
    if not c.fetchone():
        # Crear tabla clientes si no existe
        c.execute("""
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                ruc TEXT UNIQUE,
                industria TEXT,
                tamaño_empresa TEXT,
                activo INTEGER DEFAULT 1,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Insertar clientes por defecto
        clientes = [
            ('PETROPERÚ', '20100043217', 'Minería', 'Grande'),
            ('Poder Judicial', '20100138541', 'Gobierno', 'Grande'),
            ('Ministerio Público', '20100102731', 'Gobierno', 'Grande')
        ]
        for cliente in clientes:
            c.execute("INSERT INTO clientes (nombre, ruc, industria, tamaño_empresa) VALUES (?, ?, ?, ?)", cliente)
        conn.commit()
        st.success("✅ Tabla de clientes creada exitosamente!")

    # Verificar columnas adicionales en proyectos
    c.execute("PRAGMA table_info(proyectos)")
    columns = [column[1] for column in c.fetchall()]

    # Actualizar columnas si es necesario (mantener compatibilidad)
    if 'cliente_id' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN cliente_id INTEGER")
        # Migrar datos existentes
        c.execute("UPDATE proyectos SET cliente_id = 1 WHERE cliente_id IS NULL")
        conn.commit()

    if 'asignado_a_id' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN asignado_a_id INTEGER")
        c.execute("UPDATE proyectos SET asignado_a_id = 1 WHERE asignado_a_id IS NULL")
        conn.commit()

    if 'contacto_principal_id' not in columns:
        c.execute("ALTER TABLE proyectos ADD COLUMN contacto_principal_id INTEGER")
        conn.commit()

    conn.close()

def cargar_usuarios():
    """Carga todos los usuarios activos"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, nombre, email, cargo FROM usuarios WHERE activo = 1")
        usuarios = c.fetchall()
        conn.close()
        return usuarios
    except Exception as e:
        st.error(f"❌ Error cargando usuarios: {str(e)}")
        return []

def cargar_clientes():
    """Carga todos los clientes activos"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, nombre, ruc FROM clientes WHERE activo = 1")
        clientes = c.fetchall()
        conn.close()
        return clientes
    except Exception as e:
        st.error(f"❌ Error cargando clientes: {str(e)}")
        return []

def cargar_proyectos():
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT p.*, c.nombre as cliente_nombre, u.nombre as usuario_nombre 
            FROM proyectos p 
            LEFT JOIN clientes c ON p.cliente_id = c.id 
            LEFT JOIN usuarios u ON p.asignado_a_id = u.id 
            WHERE p.activo = 1
        """)
        rows = c.fetchall()
        conn.close()

        proyectos = []
        for row in rows:
            try:
                # Estructura actualizada con joins
                (id_, codigo, nombre, cliente_id, descripcion, valor, moneda,
                 tipo_cambio_historico, asignado_a_id, estado, fecha_creacion, 
                 fecha_update, fecha_deadline, fecha_cotizacion, historial, 
                 activo, contacto_id, cliente_nombre, usuario_nombre) = row

                # Solo procesar proyectos activos
                if activo == 0:
                    continue
                    
                p = Proyecto(
                    nombre=nombre,
                    cliente=cliente_nombre or "Sin cliente",
                    valor_estimado=valor,
                    descripcion=descripcion or "",
                    asignado_a=usuario_nombre or "Sin asignar",
                    moneda=moneda or 'PEN',
                    tipo_cambio_historico=tipo_cambio_historico or 3.80
                )
                p.id = id_
                p.codigo_proyecto = codigo
                p.cliente_id = cliente_id
                p.asignado_a_id = asignado_a_id

                # Verificar que el estado existe en el enum
                try:
                    p.estado_actual = Estado[estado]
                except KeyError:
                    st.warning(f"⚠️ Estado desconocido '{estado}' para proyecto {codigo}. Usando OPORTUNIDAD.")
                    p.estado_actual = Estado.OPORTUNIDAD

                # Convertir fechas de forma segura
                try:
                    if isinstance(fecha_creacion, str):
                        p.fecha_creacion = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                    else:
                        p.fecha_creacion = datetime.now()
                except (ValueError, TypeError):
                    p.fecha_creacion = datetime.now()
                    
                try:
                    if isinstance(fecha_update, str):
                        p.fecha_ultima_actualizacion = datetime.fromisoformat(fecha_update.replace('Z', '+00:00'))
                    else:
                        p.fecha_ultima_actualizacion = datetime.now()
                except (ValueError, TypeError):
                    p.fecha_ultima_actualizacion = datetime.now()

                # Manejar fechas de cotización y deadline
                try:
                    if fecha_cotizacion and isinstance(fecha_cotizacion, str):
                        p.fecha_presentacion_cotizacion = datetime.fromisoformat(fecha_cotizacion.replace('Z', '+00:00'))
                    else:
                        p.fecha_presentacion_cotizacion = None
                except (ValueError, TypeError):
                    p.fecha_presentacion_cotizacion = None

                try:
                    if fecha_deadline and isinstance(fecha_deadline, str):
                        p.fecha_deadline_propuesta = datetime.fromisoformat(fecha_deadline.replace('Z', '+00:00'))
                    else:
                        p.fecha_deadline_propuesta = None
                except (ValueError, TypeError):
                    p.fecha_deadline_propuesta = None

                # Manejar historial
                if historial:
                    try:
                        if isinstance(historial, str) and historial.strip().startswith('['):
                            p.historial = json.loads(historial)
                        else:
                            p.historial = [str(historial)]
                    except (json.JSONDecodeError, AttributeError, TypeError):
                        p.historial = []
                else:
                    p.historial = []

                proyectos.append(p)

            except Exception as e:
                st.error(f"❌ Error procesando proyecto {row[0] if row else 'desconocido'}: {str(e)}")
                continue

        return proyectos

    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            st.error("❌ La tabla 'proyectos' no existe. Ejecuta el script de creación primero.")
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
            SET nombre=?, cliente_id=?, descripcion=?, valor_estimado=?, moneda=?,
                tipo_cambio_historico=?, asignado_a_id=?, estado_actual=?, 
                fecha_ultima_actualizacion=?, fecha_deadline_propuesta=?, fecha_presentacion_cotizacion=?,
                historial=?
            WHERE id=?
        """, (
            proyecto.nombre,
            proyecto.cliente_id,
            proyecto.descripcion,
            proyecto.valor_estimado,
            proyecto.moneda,
            proyecto.tipo_cambio_historico,
            proyecto.asignado_a_id,
            proyecto.estado_actual.name,
            proyecto.fecha_ultima_actualizacion.isoformat(),
            proyecto.fecha_deadline_propuesta.isoformat() if proyecto.fecha_deadline_propuesta else None,
            proyecto.fecha_presentacion_cotizacion.isoformat() if proyecto.fecha_presentacion_cotizacion else None,
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
    verificar_y_crear_tablas()

    if "proyectos" not in st.session_state:
        st.session_state.proyectos = cargar_proyectos()
    if "usuarios" not in st.session_state:
        st.session_state.usuarios = cargar_usuarios()
    if "clientes" not in st.session_state:
        st.session_state.clientes = cargar_clientes()
    if "editando" not in st.session_state:
        st.session_state.editando = None
    if "tipo_cambio_actual" not in st.session_state:
        st.session_state.tipo_cambio_actual = obtener_tipo_cambio_actual()

except Exception as e:
    st.error("❌ Error crítico inicializando la aplicación:")
    st.error(str(e))
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

def convertir_a_pen(valor, moneda):
    """Convierte un valor a PEN usando el tipo de cambio actual"""
    if moneda == 'PEN':
        return valor
    else:
        return valor * st.session_state.tipo_cambio_actual

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
.moneda-badge {
  font-size: 10px; 
  padding: 2px 6px;
  border-radius: 8px;
  margin-left: 4px;
}
.deadline-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 10px;
  margin-top: 4px;
  display: inline-block;
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
    # Calcular totales EN PEN
    total_valor_pen = sum(convertir_a_pen(p.valor_estimado, p.moneda) for p in st.session_state.proyectos)
    total_proyectos = len(st.session_state.proyectos)

    st.markdown(f"""
    <div class="status-info">
        <strong>📊 Estado del Sistema:</strong> {total_proyectos} proyectos activos |
        💰 Valor total: <strong>S/ {total_valor_pen:,.0f}</strong> |
        💵 Tipo cambio: S/ {st.session_state.tipo_cambio_actual:.2f} por $1 |
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
    extra_lines = []

    if estado == Estado.OPORTUNIDAD:
        color_estado = "green" if dias_sin < 3 else "orange" if dias_sin < 7 else "red"
        extra_lines.append(f"<span style='font-size:12px; color:{color_estado};'>⏰ {dias_sin} días sin actualizar</span>")

    if estado == Estado.PREVENTA:
        if proyecto.fecha_presentacion_cotizacion:
            extra_lines.append(
                f"<div style='color: #16a34a; font-size: 11px; margin-top: 4px;'>"
                f"✅ Cotización presentada: {proyecto.fecha_presentacion_cotizacion.strftime('%d/%m/%y')}"
                f"</div>"
            )
        else:
            extra_lines.append(
                f"<div style='color: #ea580c; font-size: 11px; margin-top: 4px;'>"
                f"⏳ Cotización en preparación"
                f"</div>"
            )
        
    if estado in [Estado.OPORTUNIDAD, Estado.PREVENTA] and proyecto.fecha_deadline_propuesta:
        nivel_alerta = proyecto.obtener_nivel_alerta_deadline()
        estilo = obtener_estilo_deadline(nivel_alerta)
        dias_restantes = proyecto.dias_restantes_deadline()
        
        if dias_restantes is not None and not proyecto.fecha_presentacion_cotizacion:
            texto_dias = f"{abs(dias_restantes)} días {'pasados' if dias_restantes < 0 else 'restantes'}"
            extra_lines.append(
                f"<div class='deadline-badge' style='background:{estilo['fondo']}; color:{estilo['color']}; border:1px solid {estilo['color']}20;'>"
                f"{estilo['icono']} Deadline: {proyecto.fecha_deadline_propuesta.strftime('%d/%m/%y')} "
                f"({texto_dias})</div>"
            )

    # Convertir valor a PEN para mostrar
    valor_pen = convertir_a_pen(proyecto.valor_estimado, proyecto.moneda)
    moneda_badge_color = "#4CAF50" if proyecto.moneda == 'PEN' else "#2196F3"
    moneda_text = "S/ " if proyecto.moneda == 'PEN' else "$ "

    # Crear contenedor para la tarjeta con botón
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(f"""
        <div class='card' style='border-color:{color}; margin-bottom: 5px;'>
            <strong>{proyecto.nombre}</strong><br>
            <span style="font-size:12px;">🏢 {proyecto.cliente}</span><br>
            <span style="font-size:12px;">👤 {proyecto.asignado_a}</span><br>
            <span style="font-size:13px; font-weight:bold; color:{color};">
                💰 {moneda_text}{proyecto.valor_estimado:,.0f}
                <span class='moneda-badge' style='background:{moneda_badge_color}; color:white;'>
                    {proyecto.moneda}
                </span>
            </span><br>
            <span style="font-size:12px; color:#666;">
                ≈ S/ {valor_pen:,.0f}
            </span><br>
            {'<br>'.join(extra_lines)}
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
                
                # Selector de cliente
                opciones_clientes = {c[0]: f"{c[1]} ({c[2]})" for c in st.session_state.clientes}
                cliente_seleccionado = st.selectbox(
                    "Cliente",
                    options=list(opciones_clientes.keys()),
                    format_func=lambda x: opciones_clientes[x],
                    index=0
                )
                
                nueva_descripcion = st.text_area("Descripción", proyecto.descripcion)
                
                col_moneda, col_valor = st.columns(2)
                with col_moneda:
                    nueva_moneda = st.selectbox("Moneda", ["PEN", "USD"], index=0 if proyecto.moneda == "PEN" else 1)
                with col_valor:
                    nuevo_valor = st.number_input("Valor estimado", min_value=0, step=1000, value=int(proyecto.valor_estimado))
                
                # Selector de usuario asignado
                opciones_usuarios = {u[0]: f"{u[1]} ({u[3]})" for u in st.session_state.usuarios}
                usuario_seleccionado = st.selectbox(
                    "Asignado a",
                    options=list(opciones_usuarios.keys()),
                    format_func=lambda x: opciones_usuarios[x],
                    index=0
                )

                # Fechas adicionales
                col_fecha1, col_fecha2 = st.columns(2)
                
                with col_fecha1:
                    disabled_cotizacion = proyecto.estado_actual != Estado.PREVENTA
                    nueva_fecha_cotizacion = st.date_input(
                        "Fecha presentación cotización",
                        value=proyecto.fecha_presentacion_cotizacion.date() if proyecto.fecha_presentacion_cotizacion else None,
                        format="DD/MM/YYYY",
                        disabled=disabled_cotizacion,
                        help="Solo editable en estado PREVENTA" if disabled_cotizacion else None
                    )
                
                with col_fecha2:
                    disabled_deadline = proyecto.estado_actual not in [Estado.OPORTUNIDAD, Estado.PREVENTA]
                    nueva_fecha_deadline = st.date_input(
                        "Fecha deadline propuesta",
                        value=proyecto.fecha_deadline_propuesta.date() if proyecto.fecha_deadline_propuesta else None,
                        format="DD/MM/YYYY",
                        disabled=disabled_deadline,
                        help="Solo editable en estados OPORTUNIDAD y PREVENTA" if disabled_deadline else None
                    )
                
                col1, col2 = st.columns(2)
                with col1:
                    guardar = st.form_submit_button("💾 Guardar")
                with col2:
                    cancelar = st.form_submit_button("❌ Cancelar")

                if guardar:
                    try:
                        proyecto.nombre = nuevo_nombre
                        proyecto.cliente_id = cliente_seleccionado
                        proyecto.descripcion = nueva_descripcion
                        proyecto.valor_estimado = nuevo_valor
                        proyecto.moneda = nueva_moneda
                        proyecto.asignado_a_id = usuario_seleccionado
                        
                        if nueva_fecha_cotizacion:
                            proyecto.fecha_presentacion_cotizacion = datetime.combine(nueva_fecha_cotizacion, datetime.min.time())
                        if nueva_fecha_deadline:
                            proyecto.fecha_deadline_propuesta = datetime.combine(nueva_fecha_deadline, datetime.min.time())
                        
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
        
        total_valor_pen = sum(convertir_a_pen(p.valor_estimado, p.moneda) for p in proyectos_estado)

        with resumen_cols[i]:
            st.markdown(f"""
            <div style='text-align: center; padding: 15px; background-color: {color}20; border-radius: 10px; border: 2px solid {color};'>
                <div style='font-size: 24px;'>{iconos_estados[estado]}</div>
                <div style='font-weight: bold; color: {color};'>{nombres_estados[estado]}</div>
                <div style='font-size: 20px; font-weight: bold;'>{len(proyectos_estado)}</div>
                <div style='font-size: 12px;'>proyectos</div>
                <div style='font-size: 16px; font-weight: bold; color: {color};'>S/ {total_valor_pen:,.0f}</div>
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
    st.session_state.usuarios = cargar_usuarios()
    st.session_state.clientes = cargar_clientes()
    st.session_state.tipo_cambio_actual = obtener_tipo_cambio_actual()
    st.success("✅ Datos actualizados!")
    st.rerun()
