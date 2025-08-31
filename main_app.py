import streamlit as st
from sqlalchemy.orm import Session
from datetime import datetime
import requests
from database import SessionLocal
from models import Proyecto, Estado, Usuario, Cliente, Contacto

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="Workflow de Proyectos", page_icon="🏢", layout="wide")

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
# Funciones de Base de Datos ORM
# ==============================
def cargar_proyectos():
    """Carga todos los proyectos activos con relaciones"""
    try:
        db = SessionLocal()
        proyectos = db.query(Proyecto).filter(Proyecto.activo == True).all()

        # Cargar relaciones para evitar lazy loading
        for proyecto in proyectos:
            # Forzar carga de relaciones
            _ = proyecto.cliente
            _ = proyecto.asignado_a
            _ = proyecto.contacto_principal

            # Convertir strings de fecha a datetime objects
            if isinstance(proyecto.fecha_creacion, str):
                try:
                    proyecto.fecha_creacion = datetime.fromisoformat(proyecto.fecha_creacion.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    proyecto.fecha_creacion = datetime.now()

            if isinstance(proyecto.fecha_ultima_actualizacion, str):
                try:
                    proyecto.fecha_ultima_actualizacion = datetime.fromisoformat(proyecto.fecha_ultima_actualizacion.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    proyecto.fecha_ultima_actualizacion = datetime.now()

            if proyecto.fecha_deadline_propuesta and isinstance(proyecto.fecha_deadline_propuesta, str):
                try:
                    proyecto.fecha_deadline_propuesta = datetime.fromisoformat(proyecto.fecha_deadline_propuesta.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    proyecto.fecha_deadline_propuesta = None

            if proyecto.fecha_presentacion_cotizacion and isinstance(proyecto.fecha_presentacion_cotizacion, str):
                try:
                    proyecto.fecha_presentacion_cotizacion = datetime.fromisoformat(proyecto.fecha_presentacion_cotizacion.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    proyecto.fecha_presentacion_cotizacion = None

        db.close()
        return proyectos
    except Exception as e:
        st.error(f"❌ Error cargando proyectos: {str(e)}")
        return []

def cargar_usuarios():
    """Carga todos los usuarios activos"""
    try:
        db = SessionLocal()
        usuarios = db.query(Usuario).filter(Usuario.activo == True).all()
        db.close()
        return usuarios
    except Exception as e:
        st.error(f"❌ Error cargando usuarios: {str(e)}")
        return []

def cargar_clientes():
    """Carga todos los clientes activos"""
    try:
        db = SessionLocal()
        clientes = db.query(Cliente).filter(Cliente.activo == True).all()
        db.close()
        return clientes
    except Exception as e:
        st.error(f"❌ Error cargando clientes: {str(e)}")
        return []

def cargar_contactos():
    """Carga todos los contactos"""
    try:
        db = SessionLocal()
        contactos = db.query(Contacto).all()
        db.close()
        return contactos
    except Exception as e:
        st.error(f"❌ Error cargando contactos: {str(e)}")
        return []

def refrescar_proyecto(proyecto_id):
    with SessionLocal() as db:
        return db.query(Proyecto).filter_by(id=proyecto_id).first()

def actualizar_proyecto(proyecto_actualizado):
    """Actualiza un proyecto en la base de datos"""
    db = SessionLocal()
    try:


        # Obtener el proyecto usando with_for_update para bloqueo
        proyecto_db = db.query(Proyecto).filter(Proyecto.id == proyecto_actualizado.id).with_for_update().first()

        if proyecto_db:
            # Actualizar campos básicos
            proyecto_db.nombre = proyecto_actualizado.nombre
            proyecto_db.descripcion = proyecto_actualizado.descripcion
            proyecto_db.valor_estimado = proyecto_actualizado.valor_estimado
            proyecto_db.moneda = proyecto_actualizado.moneda
            proyecto_db.estado_actual = proyecto_actualizado.estado_actual
            proyecto_db.fecha_ultima_actualizacion = datetime.now()
            proyecto_db.fecha_deadline_propuesta = proyecto_actualizado.fecha_deadline_propuesta
            proyecto_db.fecha_presentacion_cotizacion = proyecto_actualizado.fecha_presentacion_cotizacion

            # Actualizar relaciones
            proyecto_db.cliente_id = proyecto_actualizado.cliente_id
            proyecto_db.asignado_a_id = proyecto_actualizado.asignado_a_id
            proyecto_db.contacto_principal_id = proyecto_actualizado.contacto_principal_id

            # DEBUG: Verificar cambios
            logger.debug(f"DEBUG: Actualizando proyecto ID {proyecto_db.id}")
            logger.debug(f"DEBUG: Nuevos valores - Nombre: {proyecto_db.nombre}, Cliente ID: {proyecto_db.cliente_id}, Asignado ID: {proyecto_db.asignado_a_id}")


            db.commit()
            db.refresh(proyecto_db)
            #db.execute(text("PRAGMA wal_checkpoint(FULL);"))
            st.cache_data.clear()
            logger.debug("DEBUG: Commit exitoso")


        return True
    except Exception as e:
        st.error(f"❌ Error actualizando proyecto: {str(e)}")
        return False
    finally:
        db.close()

# ==============================
# Inicialización segura
# ==============================
# Inicializar primero el estado de edición FUERA del try-catch
if "editando" not in st.session_state:
    st.session_state.editando = None

try:
    if "proyectos" not in st.session_state:
        st.session_state.proyectos = cargar_proyectos()
    if "usuarios" not in st.session_state:
        st.session_state.usuarios = cargar_usuarios()
    if "clientes" not in st.session_state:
        st.session_state.clientes = cargar_clientes()
    if "contactos" not in st.session_state:
        st.session_state.contactos = cargar_contactos()
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

     # 👇 sincronizar solo el proyecto editado
    #proyecto_refrescado = refrescar_proyecto(proyecto.id)
    #for idx, p in enumerate(st.session_state.proyectos):
    #    if p.id == proyecto.id:
    #        st.session_state.proyectos[idx] = proyecto_refrescado
    #        break

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

    # Obtener nombres de relaciones
    cliente_nombre = proyecto.cliente.nombre if proyecto.cliente else "Sin cliente"
    usuario_nombre = proyecto.asignado_a.nombre if proyecto.asignado_a else "Sin asignar"

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
            <span style="font-size:12px;">🏢 {cliente_nombre}</span><br>
            <span style="font-size:12px;">👤 {usuario_nombre}</span><br>
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
        if st.button("✏️", key=f"edit_{proyecto.codigo_proyecto}", help="Editar proyecto"):
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
        proyectos_estado = [p for p in st.session_state.proyectos if p.estado_actual == estado.value]

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

            # BOTÓN MODIFICADO - Ahora redirige a la página de oportunidades
            if estado == Estado.OPORTUNIDAD:
                if st.button("📊 Administrar Oportunidades", key=f"btn_{estado}", use_container_width=True):
                    st.switch_page("pages/1_Oportunidades.py")
            else:
                st.button("⏳ Próximamente", key=f"btn_{estado}", disabled=True, use_container_width=True)

else:
    st.info("🚀 ¡Bienvenido! No hay proyectos en el sistema aún.")
    st.markdown("### Para comenzar:")
    st.markdown("1. 📊 Ejecuta el script de creación de base de datos")
    st.markdown("2. 🔄 Recarga la aplicación")
    st.markdown("3. ➕ Crea tu primera oportunidad")

# ==============================
# Sidebar de edición con flujo lineal
# ==============================
if st.session_state.editando:
    try:
        print(f"DEBUG: Buscando proyecto ID {st.session_state.editando}")
        print(f"DEBUG: Proyectos disponibles: {[p.id for p in st.session_state.proyectos]}")
        proyecto = next((p for p in st.session_state.proyectos if p.id == st.session_state.editando), None)

        # DEBUG: Mostrar si se encontró el proyecto
        if not proyecto:
            st.sidebar.error("❌ Proyecto no encontrado")
            st.session_state.editando = None
            st.rerun()

        with st.sidebar:
            st.header(f"✏️ Editar Proyecto #{proyecto.id}")
            st.caption(f"Código: **{proyecto.codigo_proyecto}** • Estado actual: **{proyecto.estado_actual}**")

            with st.form(f"form_edit_{proyecto.id}", clear_on_submit=False):
                nuevo_nombre = st.text_input("Nombre", proyecto.nombre)

                # Selector de cliente
                opciones_clientes = {c.id: f"{c.nombre} ({c.ruc})" for c in st.session_state.clientes}

                cliente_ids = list(opciones_clientes.keys())
                # calcular índice real
                cliente_index = cliente_ids.index(proyecto.cliente_id) if proyecto.cliente_id in cliente_ids else 0

                cliente_seleccionado = st.selectbox(
                    "Cliente",
                    options=list(opciones_clientes.keys()),
                    format_func=lambda x: opciones_clientes[x],
                    index=cliente_index
                )

                nueva_descripcion = st.text_area("Descripción", proyecto.descripcion or "")

                col_moneda, col_valor = st.columns(2)
                with col_moneda:
                    nueva_moneda = st.selectbox("Moneda", ["PEN", "USD"], index=0 if proyecto.moneda == "PEN" else 1)
                with col_valor:
                    nuevo_valor = st.number_input("Valor estimado", min_value=0, step=1000, value=int(proyecto.valor_estimado))

                # Selector de usuario asignado
                opciones_usuarios = {u.id: f"{u.nombre} ({u.cargo})" for u in st.session_state.usuarios}

                usuario_ids = list(opciones_usuarios.keys())
                usuario_index = usuario_ids.index(proyecto.asignado_a_id) if proyecto.asignado_a_id in usuario_ids else 0

                usuario_seleccionado = st.selectbox(
                    "Asignado a",
                    options=usuario_ids,  # usar la misma lista que para calcular el índice
                    format_func=lambda x: opciones_usuarios[x],
                    index=usuario_index
                )


                # Selector de contacto principal
                # Selector de contacto principal - CON VERIFICACIÓN
                contactos_cliente = [c for c in st.session_state.contactos if c and hasattr(c, 'cliente_id') and c.cliente_id == cliente_seleccionado]
                opciones_contactos = {c.id: f"{c.nombre} - {c.cargo}" for c in contactos_cliente if c and hasattr(c, 'nombre')}

                contacto_ids = list(opciones_contactos.keys())

                #contacto_seleccionado = st.selectbox(
                #    "Contacto principal",
                #    options=list(opciones_contactos.keys()),
                #    format_func=lambda x: opciones_contactos[x],
                #    index=0 if not opciones_contactos else None,
                #    disabled=not opciones_contactos
                #)

                if contacto_ids:
                    contacto_index = contacto_ids.index(proyecto.contacto_principal_id) if proyecto.contacto_principal_id in contacto_ids else 0
                    contacto_seleccionado = st.selectbox(
                        "Contacto principal",
                        options=contacto_ids,
                        format_func=lambda x: opciones_contactos[x],
                        index=contacto_index
                    )
                else:
                    contacto_seleccionado = None
                    st.selectbox("Contacto principal", options=["(sin contactos)"], disabled=True)

                # Fechas adicionales
                col_fecha1, col_fecha2 = st.columns(2)

                with col_fecha1:
                    disabled_cotizacion = proyecto.estado_actual != "PREVENTA"
                    nueva_fecha_cotizacion = st.date_input(
                        "Fecha presentación cotización",
                        value=proyecto.fecha_presentacion_cotizacion.date() if proyecto.fecha_presentacion_cotizacion else None,
                        format="DD/MM/YYYY",
                        disabled=disabled_cotizacion,
                        help="Solo editable en estado PREVENTA" if disabled_cotizacion else None
                    )

                with col_fecha2:
                    disabled_deadline = proyecto.estado_actual not in ["OPORTUNIDAD", "PREVENTA"]
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

                        # DEBUG: Mostrar lo que se va a guardar
                        st.write(f"DEBUG: Guardando proyecto ID {proyecto.id}")
                        st.write(f"DEBUG: Nuevo nombre: {nuevo_nombre}")
                        st.write(f"DEBUG: Nuevo cliente ID: {cliente_seleccionado}")
                        st.write(f"DEBUG: Nuevo usuario ID: {usuario_seleccionado}")

                        proyecto.nombre = nuevo_nombre
                        proyecto.descripcion = nueva_descripcion
                        proyecto.valor_estimado = nuevo_valor
                        proyecto.moneda = nueva_moneda
                        proyecto.cliente_id = cliente_seleccionado
                        proyecto.asignado_a_id = usuario_seleccionado
                        proyecto.contacto_principal_id = contacto_seleccionado if contacto_seleccionado else None

                        if nueva_fecha_cotizacion:
                            proyecto.fecha_presentacion_cotizacion = datetime.combine(nueva_fecha_cotizacion, datetime.min.time())
                        if nueva_fecha_deadline:
                            proyecto.fecha_deadline_propuesta = datetime.combine(nueva_fecha_deadline, datetime.min.time())

                        proyecto.fecha_ultima_actualizacion = datetime.now()

                        # DEBUG: Verificar el objeto antes de guardar
                        st.write(f"DEBUG: Proyecto a guardar - ID: {proyecto.id}, Nombre: {proyecto.nombre}")

                        if actualizar_proyecto(proyecto):
                            st.success("✅ Guardado!")
                            _close_editor()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

                if cancelar:
                    _close_editor()

            st.markdown("---")
            st.subheader("🔄 Acciones de Flujo")

            # Convertir estado actual a Enum para el flujo
            try:
                estado_actual_enum = Estado(proyecto.estado_actual)
                idx = flujo_estados.index(estado_actual_enum)
            except:
                idx = 0

            anterior = flujo_estados[idx-1] if idx > 0 else None
            siguiente = flujo_estados[idx+1] if idx < len(flujo_estados)-1 else None

            if anterior and st.button(f"⬅️ Retroceder a {anterior.value}"):
                try:
                    proyecto.estado_actual = anterior.value
                    proyecto.fecha_ultima_actualizacion = datetime.now()
                    if actualizar_proyecto(proyecto):
                        st.success(f"✅ Movido a {anterior.value}")
                        _close_editor()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            if siguiente and st.button(f"➡️ Avanzar a {siguiente.value}"):
                try:
                    proyecto.estado_actual = siguiente.value
                    proyecto.fecha_ultima_actualizacion = datetime.now()
                    if actualizar_proyecto(proyecto):
                        st.success(f"✅ Movido a {siguiente.value}")
                        _close_editor()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    except Exception as e:
        st.sidebar.error(f"❌ Error cargando proyecto: {str(e)}")
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
        proyectos_estado = [p for p in st.session_state.proyectos if p.estado_actual == estado.value]
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
    st.session_state.contactos = cargar_contactos()
    st.session_state.tipo_cambio_actual = obtener_tipo_cambio_actual()
    st.success("✅ Datos actualizados!")
    st.rerun()
