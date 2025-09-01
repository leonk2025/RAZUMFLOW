import streamlit as st
from database import engine, Base
from sqlalchemy import text

def test_database_connection():
    """Prueba la conexión a SQLiteCloud y verifica tablas"""
    
    st.title("🔍 Prueba de Conexión a SQLiteCloud")
    
    # 1. Probar conexión básica
    try:
        with engine.connect() as conn:
            st.success("✅ Conexión exitosa a SQLiteCloud")
    except Exception as e:
        st.error(f"❌ Error de conexión: {str(e)}")
        return False
    
    # 2. Intentar listar tablas (método compatible con SQLiteCloud)
    try:
        with engine.connect() as conn:
            # SQL estándar para listar tablas (probablemente funcione en SQLiteCloud)
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            
            st.subheader("📊 Tablas encontradas:")
            for table in tables:
                st.write(f"- {table}")
                
        return True
        
    except Exception as e:
        st.warning("⚠️ No se pudieron listar tablas con sqlite_master")
        st.info("Probando métodos alternativos...")
        
        # 3. Método alternativo: probar con cada tabla esperada
        expected_tables = ['proyectos', 'usuarios', 'clientes', 'contactos', 'eventos_historial']
        existing_tables = []
        
        for table_name in expected_tables:
            try:
                with engine.connect() as conn:
                    # Intentar hacer un SELECT simple de cada tabla
                    conn.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1;"))
                    existing_tables.append(table_name)
                    st.write(f"✅ Tabla '{table_name}' existe")
            except:
                st.write(f"❌ Tabla '{table_name}' no existe o no accessible")
        
        if existing_tables:
            st.success(f"✅ Tablas accesibles: {existing_tables}")
            return True
        else:
            st.error("❌ No se pudo acceder a ninguna tabla")
            return False

# 4. Probar operaciones CRUD básicas
def test_crud_operations():
    """Prueba operaciones básicas de CRUD"""
    
    st.subheader("🧪 Pruebas CRUD")
    
    try:
        with engine.connect() as conn:
            # Probar INSERT
            conn.execute(text("""
                INSERT INTO usuarios (nombre, email, cargo, activo) 
                VALUES ('Usuario Prueba', 'test@example.com', 'Tester', 1)
            """))
            st.success("✅ INSERT prueba exitoso")
            
            # Probar SELECT
            result = conn.execute(text("SELECT * FROM usuarios WHERE email = 'test@example.com'"))
            user = result.fetchone()
            st.success(f"✅ SELECT prueba exitoso: Usuario ID {user[0]}")
            
            # Probar DELETE
            conn.execute(text("DELETE FROM usuarios WHERE email = 'test@example.com'"))
            st.success("✅ DELETE prueba exitoso")
            
            conn.commit()
            return True
            
    except Exception as e:
        st.error(f"❌ Error en operaciones CRUD: {str(e)}")
        return False

if __name__ == "__main__":
    if test_database_connection():
        test_crud_operations()
