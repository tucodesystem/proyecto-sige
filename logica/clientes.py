from db.conexion import conectar_db

# ==========================================
# --- LÓGICA DE VENDEDORES ---
# ==========================================

def registrar_vendedor(nombre):
    """Registra un nuevo vendedor en la base de datos."""
    conexion = conectar_db()
    if not conexion: return False
    try:
        cursor = conexion.cursor()
        query = "INSERT INTO vendedores (nombre_vendedor) VALUES (%s)"
        cursor.execute(query, (nombre.strip(),)) # .strip() quita espacios accidentales
        conexion.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ Error al registrar vendedor: {e}")
        return False
    finally:
        conexion.close()

def obtener_vendedores():
    """Retorna la lista de todos los vendedores ordenados alfabéticamente."""
    conexion = conectar_db()
    if not conexion: return []
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vendedores ORDER BY nombre_vendedor ASC")
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error al obtener vendedores: {e}")
        return []
    finally:
        conexion.close()


# ==========================================
# --- LÓGICA DE CLIENTES (DISTRIBUIDORES) ---
# ==========================================

# Reemplaza o actualiza estas funciones en logica/clientes.py

def registrar_cliente(nit, razon, rep_legal, doc_rp, direccion, ciudad, depto, telefono, id_distribuidor):
    from db.conexion import conectar_db
    conexion = conectar_db()
    if not conexion: return False
    try:
        cursor = conexion.cursor()
        query = """
            INSERT INTO clientes 
            (nit, razon_social, representante_legal, documento_rp, direccion, ciudad, departamento, telefono, id_vendedor_asignado) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (nit, razon, rep_legal, doc_rp, direccion, ciudad, depto, telefono, id_distribuidor)
        cursor.execute(query, valores)
        conexion.commit()
        return True
    except Exception as e:
        print(f"❌ Error al registrar cliente: {e}")
        return False
    finally:
        conexion.close()

def obtener_todos_los_clientes():
    """Retorna todos los clientes con el nombre de su vendedor asignado."""
    conexion = conectar_db()
    if not conexion: return []
    try:
        cursor = conexion.cursor(dictionary=True)
        # Usamos LEFT JOIN para traer el nombre del vendedor en lugar de solo su ID
        query = """
            SELECT c.*, v.nombre_vendedor 
            FROM clientes c
            LEFT JOIN vendedores v ON c.id_vendedor_asignado = v.id_vendedor
            ORDER BY c.razon_social ASC
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error al obtener clientes: {e}")
        return []
    finally:
        conexion.close()

def obtener_clientes_busqueda(termino):
    """Busca clientes por NIT o Razón Social para el buscador en tiempo real."""
    conexion = conectar_db()
    if not conexion: return []
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT c.*, v.nombre_vendedor 
            FROM clientes c
            LEFT JOIN vendedores v ON c.id_vendedor_asignado = v.id_vendedor
            WHERE c.nit LIKE %s OR c.razon_social LIKE %s
            ORDER BY c.razon_social ASC
        """
        like_term = f"%{termino}%"
        cursor.execute(query, (like_term, like_term))
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error en la búsqueda de clientes: {e}")
        return []
    finally:
        conexion.close()

def actualizar_cliente_db(nit_original, nit_nuevo, razon, rep, doc, direccion, ciudad, depto, tel, id_dist):
    from db.conexion import conectar_db
    conexion = conectar_db()
    if not conexion: return False
    try:
        cursor = conexion.cursor()
        query = """
            UPDATE clientes 
            SET nit=%s, razon_social=%s, representante_legal=%s, documento_rp=%s, 
                direccion=%s, ciudad=%s, departamento=%s, telefono=%s, id_vendedor_asignado=%s
            WHERE nit=%s
        """
        cursor.execute(query, (nit_nuevo, razon, rep, doc, direccion, ciudad, depto, tel, id_dist, nit_original))
        conexion.commit()
        return True
    except Exception as e:
        print(f"❌ Error al actualizar: {e}")
        return False
    finally:
        conexion.close()

def eliminar_cliente_db(nit):
    """Elimina un cliente de la base de datos si no tiene ventas asociadas."""
    conexion = conectar_db()
    if not conexion: return False
    try:
        cursor = conexion.cursor()
        query = "DELETE FROM clientes WHERE nit = %s"
        cursor.execute(query, (nit,))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ Error al eliminar cliente (¿Tiene ventas asociadas?): {e}")
        return False
    finally:
        conexion.close()

def actualizar_vendedor_db(id_vendedor, nuevo_nombre):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE vendedores SET nombre_vendedor = %s WHERE id_vendedor = %s", 
                       (nuevo_nombre, id_vendedor))
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conexion.close()

def eliminar_vendedor_db(id_vendedor):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM vendedores WHERE id_vendedor = %s", (id_vendedor,))
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conexion.close()