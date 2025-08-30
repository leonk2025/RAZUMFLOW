import streamlit as st
from datetime import datetime
from models import Proyecto, Estado, Usuario, Cliente, Contacto, EventoHistorial, Base
from database import SessionLocal, engine
from sqlalchemy.orm import Session
import requests

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="Workflow de Proyectos", page_icon="🏢", layout="wide")

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

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
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def cargar_proyectos(db: Session):
    """Carga todos los proyectos activos desde la base de datos"""
    try:
        proyectos = db.query(Proyecto).filter(Proyecto.activo == True).all()
        return proyectos
    except Exception as e:
        st.error(f"❌ Error cargando proyectos: {str(e)}")
        return []

def cargar_usuarios(db: Session):
    """Carga todos los usuarios activos"""
    try:
        return db.query(Usuario).filter(Usuario.activo == True).all()
    except Exception as e:
        st.error(f"❌ Error cargando usuarios: {str(e)}")
        return []

def cargar_clientes(db: Session):
    """Carga todos los clientes activos"""
    try:
        return db.query(Cliente).filter(Cliente.activo == True).all()
    except Exception as e:
        st.error(f"❌ Error cargando clientes: {str(e)}")
        return []

def cargar_contactos(db: Session, cliente_id: int = None):
    """Carga contactos, opcionalmente filtrados por cliente"""
    try:
        query = db.query(Contacto)
        if cliente_id:
            query = query.filter(Contacto.cliente_id == cliente_id)
        return query.all()
    except Exception as e:
        st.error(f"❌ Error cargando contactos: {str(e)}")
        return []

def actualizar_proyecto(db: Session, proyecto: Proyecto):
    """Actualiza un proyecto en la base de datos"""
    try:
        db.commit()
        db.refresh(proyecto)
        return True
    except Exception as e:
        db.rollback()
        st.error(f"❌ Error actualizando proyecto: {str(e)}")
        return False

def crear_proyecto(db: Session, proyecto_data: dict):
    """Crea un nuevo proyecto en la base de datos"""
    try:
        nuevo_proyecto = Proyecto(**proyecto_data)
        db.add(nuevo_proyecto)
        db.commit()
        db.refresh(nuevo_proyecto)
        return nuevo_proyecto
    except Exception as e:
        db.rollback()
        st.error(f"❌ Error creando proyecto: {str(e)}")
        return None

# ==============================
# Inicialización segura
# ==============================
try:
    db = next(get_db())

    if "db" not in st.session_state:
        st.session_state.db = db

    if "proyectos" not in st.session_state:
        st.session_state.proyectos = cargar_proyectos(db)

    if "usuarios" not in st.session_state:
        st.session_state.usuarios = cargar_usuarios(db)

    if "clientes" not in st.session_state:
        st.session_state.clientes = cargar_clientes(db)

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
    st.session_state.proyectos = cargar_proyectos(st.session_state.db)
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

    # Agregar esta lógica en la sección de PREVENTA:
    if estado == Estado.PREVENTA:
        if proyecto.fecha_presentacion_cotizacion:
            # ✅ COTIZACIÓN PRESENTADA - Mostrar en verde
            extra_lines.append(
                f"<div style='color: #16a34a; font-size: 11px; margin-top: 4px;'>"
                f"✅ Cotización presentada: {proyecto.fecha_presentacion_cotizacion.strftime('%d/%m/%y')}"
                f"</div>"
            )
        else:
            # ⏳ COTIZACIÓN PENDIENTE - Mostrar en naranja
            extra_lines.append(
                f"<div style='color: #ea580c; font-size: 11px; margin-top: 4px;'>"
                f"⏳ Cotización en preparación"
                f"</div>"
            )

    # Mostrar deadline en OPORTUNIDAD y PREVENTA
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

    # Obtener nombres de relaciones
    nombre_cliente = proyecto.cliente.nombre if proyecto.cliente else "Sin cliente"
    nombre_asignado = proyecto.asignado.nombre if proyecto.asignado else "Sin asignar"

    # Crear contenedor para la tarjeta con botón
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(f"""
        <div class='card' style='border-color:{color}; margin-bottom: 5px;'>
            <strong>{proyecto.nombre}</strong><br>
            <span style="font-size:12px;">🏢 {nombre_cliente}</span><br>
            <span style="font-size:12px;">👤 {nombre_asignado}</span><br>
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
        proyectos_estado = [p for p in st.session_state.proyectos if p.estado_actual == estado]

        with col:
            st.markdown(
                f"<div class='section-header' style='background:{colores_estados[estado]};'>"
                f"<h3 style='margin:0;'>{iconos_estados[estado]} {nombres_estados[estado]}</h3>"
                f"<div class='badge' style='color:{colores_estados[estado]};'>{len(proyectos_estado)}</div>"
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
                cliente_actual_id = proyecto.cliente_id if proyecto.cliente_id else None
                opciones_clientes = {c.id: c.nombre for c in st.session_state.clientes}
                cliente_seleccionado = st.selectbox(
                    "Cliente",
                    options=list(opciones_clientes.keys()),
                    format_func=lambda x: opciones_clientes[x],
                    index=list(opciones_clientes.keys()).index(cliente_actual_id) if cliente_actual_id in opciones_clientes else 0
                )

                nueva_descripcion = st.text_area("Descripción", proyecto.descripcion)

                col_moneda, col_valor = st.columns(2)
                with col_moneda:
                    nueva_moneda = st.selectbox("Moneda", ["PEN", "USD"], index=0 if proyecto.moneda == "PEN" else 1)
                with col_valor:
                    nuevo_valor = st.number_input("Valor estimado", min_value=0, step=1000, value=int(proyecto.valor_estimado))

                # Selector de usuario asignado
                usuario_actual_id = proyecto.asignado_a_id if proyecto.asignado_a_id else None
                opciones_usuarios = {u.id: u.nombre for u in st.session_state.usuarios}
                usuario_seleccionado = st.selectbox(
                    "Asignado a",
                    options=list(opciones_usuarios.keys()),
                    format_func=lambda x: opciones_usuarios[x],
                    index=list(opciones_usuarios.keys()).index(usuario_actual_id) if usuario_actual_id in opciones_usuarios else 0
                )

                # Selector de contacto principal
                contactos_cliente = cargar_contactos(st.session_state.db, cliente_seleccionado)
                opciones_contactos = {c.id: f"{c.nombre} - {c.cargo}" for c in contactos_cliente}

                contacto_actual_id = proyecto.contacto_principal_id if proyecto.contacto_principal_id else None
                contacto_seleccionado = st.selectbox(
                    "Contacto principal",
                    options=list(opciones_contactos.keys()),
                    format_func=lambda x: opciones_contactos[x],
                    index=list(opciones_contactos.keys()).index(contacto_actual_id) if contacto_actual_id in opciones_contactos else 0,
                    disabled=len(contactos_cliente) == 0
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
                        proyecto.contacto_principal_id = contacto_seleccionado if contacto_seleccionado else None

                        if nueva_fecha_cotizacion:
                            proyecto.fecha_presentacion_cotizacion = datetime.combine(nueva_fecha_cotizacion, datetime.min.time())
                        if nueva_fecha_deadline:
                            proyecto.fecha_deadline_propuesta = datetime.combine(nueva_fecha_deadline, datetime.min.time())

                        proyecto.fecha_ultima_actualizacion = datetime.now()

                        # Agregar evento al historial
                        proyecto.agregar_evento_historial(f"Editado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")

                        if actualizar_proyecto(st.session_state.db, proyecto):
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
                    proyecto.agregar_evento_historial(f"Retrocedido a {anterior.value}")

                    if actualizar_proyecto(st.session_state.db, proyecto):
                        st.success(f"✅ Movido a {anterior.value}")
                        _close_editor()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            if siguiente and st.button(f"➡️ Avanzar a {siguiente.value}"):
                try:
                    proyecto.estado_actual = siguiente
                    proyecto.fecha_ultima_actualizacion = datetime.now()
                    proyecto.agregar_evento_historial(f"Avanzado a {siguiente.value}")

                    if actualizar_proyecto(st.session_state.db, proyecto):
                        st.success(f"✅ Movido a {siguiente.value}")
                        _close_editor()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            st.markdown("---")
            st.subheader("📜 Historial")
            historial_items = proyecto.historial[-5:] if proyecto.historial else []
            for evento in historial_items:
                st.write(f"• {evento.timestamp.strftime('%d/%m/%Y %H:%M')} - {evento.evento}")

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
    st.session_state.proyectos = cargar_proyectos(st.session_state.db)
    st.session_state.usuarios = cargar_usuarios(st.session_state.db)
    st.session_state.clientes = cargar_clientes(st.session_state.db)
    st.session_state.tipo_cambio_actual = obtener_tipo_cambio_actual()
    st.success("✅ Datos actualizados!")
    st.rerun()
