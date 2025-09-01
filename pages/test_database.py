import streamlit as st
from database import engine, Base
from models import Proyecto, Usuario, Cliente, Contacto, EventoHistorial

def test_database_connection():
    """Prueba la conexión a la base de datos y verifica tablas"""
    
    st.title("🔍 Prueba de Conexión a Base de Datos")
    
    # 1. Probar conexión básica
    try:
        with engine.connect() as conn:
            st.success("✅ Conexión exitosa a la base de datos")
    except Exception as e:
        st.error(f"❌ Error de conexión: {str(e)}")
        return False
    
    # 2. Listar tablas existentes
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in result]
            
            st.subheader("📊 Tablas encontradas:")
            for table in tables:
                st.write(f"- {table}")
                
            # 3. Verificar tablas esperadas
            expected_tables = ['proyectos', 'usuarios', 'clientes', 'contactos', 'eventos_historial']
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                st.warning(f"⚠️ Tablas faltantes: {missing_tables}")
            else:
                st.success("✅ Todas las tablas esperadas están presentes")
                
    except Exception as e:
        st.error(f"❌ Error al leer tablas: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_database_connection()
