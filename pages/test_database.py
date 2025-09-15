import streamlit as st
from database import engine
from sqlalchemy import text

st.title("🔍 Debug de Conexión SQLiteCloud")

# 1. Verificar connection string actual
st.subheader("📋 Connection String")
st.code(f"{engine.url}")

# 2. Verificar qué bases de datos están disponibles
try:
    with engine.connect() as conn:
        # Intentar listar databases (si SQLiteCloud lo permite)
        try:
            result = conn.execute(text("SHOW DATABASES;"))
            dbs = [row[0] for row in result]
            st.subheader("🗄️ Bases de datos disponibles:")
            for db in dbs:
                st.write(f"- {db}")
        except:
            st.info("ℹ️ Comando 'SHOW DATABASES' no disponible")
        
        # 3. Verificar la base de datos actual
        try:
            result = conn.execute(text("SELECT DATABASE();"))
            current_db = result.scalar()
            st.subheader("🎯 Base de datos actual:")
            st.success(f"{current_db}")
        except:
            st.info("ℹ️ Comando 'SELECT DATABASE()' no disponible")
            
        # 4. Intentar métodos alternativos para ver tablas
        st.subheader("🔎 Buscando tablas con diferentes métodos:")
        
        # Método 1: SQL estándar
        try:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
            """))
            tables = [row[0] for row in result]
            st.success("✅ Tablas encontradas con sqlite_master:")
            for table in tables:
                st.write(f"- {table}")
        except Exception as e:
            st.error(f"❌ sqlite_master falló: {e}")
            
        # Método 2: Information schema (estándar SQL)
        #SELECT table_name FROM information_schema.tables 
        #WHERE table_schema = DATABASE();
        try:
            result = conn.execute(text("""
                SELECT * FROM proyectos  
                WHERE id = 1;
            """))
            tables = [row[0] for row in result]
            st.success("✅ Tablas encontradas con information_schema:")
            for table in tables:
                st.write(f"- {table}")
        except Exception as e:
            st.error(f"❌ information_schema falló: {e}")

except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
