from db.conexion import conectar_db

def obtener_todos_los_productos():
    conexion = conectar_db()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM productos")
            return cursor.fetchall() # Esto ahora devolverá 'id_id_producto'
        finally:
            conexion.close()
    return []

def registrar_nuevo_producto(id_manual, nombre, precio, stock, minimo):
    conexion = conectar_db()
    if not conexion: return False
    try:
        cursor = conexion.cursor()
        
        # 1. Primero verificamos si existe
        cursor.execute("SELECT id_id_producto FROM productos WHERE id_id_producto = %s", (id_manual,))
        if cursor.fetchone():
            print(f"Aviso: El código {id_manual} ya está en el inventario.")
            return "duplicado" # Retornamos un valor específico para manejarlo en la UI

        # 2. Si no existe, procedemos al INSERT
        query = """
            INSERT INTO productos (id_id_producto, nombre, precio, stock, stock_minimo) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (id_manual, nombre, precio, stock, minimo))
        conexion.commit()
        return True
    except Exception as e:
        print(f"Error crítico al registrar: {e}")
        return False
    finally:
        conexion.close()
        
def actualizar_producto_db(id_p, nombre, precio, stock, minimo):
    """Actualiza la información usando el nombre de columna real: id_id_producto."""
    conexion = conectar_db()
    if not conexion: return False
    try:
        cursor = conexion.cursor()
        # CAMBIO: id_producto -> id_id_producto
        query = """
            UPDATE productos 
            SET nombre = %s, precio = %s, stock = %s, stock_minimo = %s 
            WHERE id_id_producto = %s
        """
        valores = (nombre, precio, stock, minimo, id_p)
        cursor.execute(query, valores)
        conexion.commit()
        return True
    except Exception as e:
        print(f"❌ Error al actualizar: {e}")
        return False
    finally:
        conexion.close()

def eliminar_producto_db(id_p):
    """Elimina el producto usando el nombre de columna real: id_id_producto."""
    conexion = conectar_db()
    if not conexion: return False
    try:
        cursor = conexion.cursor()
        # Usamos el nombre de columna unificado que arreglamos en la base de datos
        query = "DELETE FROM productos WHERE id_id_producto = %s"
        cursor.execute(query, (id_p,))
        conexion.commit()
        
        # IMPORTANTE: Verificamos si se borró al menos una fila
        if cursor.rowcount > 0:
            return True
        else:
            print(f"⚠️ No se encontró el producto con ID: {id_p}")
            return False

    except Exception as e:
        # Esto atrapará errores si el producto está siendo usado en una remisión (Foreign Key)
        print(f"❌ Error al eliminar en la base de datos: {e}")
        return False
    finally:
        conexion.close()

def obtener_sugerencias_produccion():
    """Trae los productos con bajo stock."""
    conexion = conectar_db()
    if not conexion: return []
    
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT nombre, stock, stock_minimo, 
            (stock_minimo - stock) as sugerencia 
            FROM productos 
            WHERE stock < stock_minimo
            ORDER BY sugerencia DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error en sugerencias: {e}")
        return []
    finally:
        if conexion and conexion.is_connected():
            conexion.close()
    
def buscar_productos_remision(termino):
    """Busca productos por nombre para la remisión."""
    conexion = conectar_db()
    if not conexion: return []
    
    try:
        cursor = conexion.cursor(dictionary=True)
        query = "SELECT * FROM productos WHERE nombre LIKE %s AND stock > 0"
        cursor.execute(query, (f"%{termino}%",))
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error en búsqueda de productos: {e}")
        return []
    finally:
        if conexion and conexion.is_connected():
            conexion.close()
    
def ajustar_stock_rapido(id_p, cantidad_cambio):
    """
    Actualiza el stock sumando o restando el valor recibido.
    id_p: El código del peluche (VARCHAR).
    cantidad_cambio: 1 para sumar, -1 para restar.
    """
    # Asegúrate de que conectar_db esté importado o disponible en este archivo
    from db.conexion import conectar_db 
    
    conexion = conectar_db()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()
        
        # Usamos stock = stock + %s para que MySQL haga la cuenta matemática directamente.
        # Si cantidad_cambio es -1, la suma de un negativo restará el stock.
        query = "UPDATE productos SET stock = stock + %s WHERE id_id_producto = %s"
        
        cursor.execute(query, (cantidad_cambio, id_p))
        conexion.commit()
        
        # Verificamos si realmente se actualizó alguna fila
        return cursor.rowcount > 0

    except Exception as e:
        print(f"❌ Error en ajustar_stock_rapido: {e}")
        return False
    finally:
        conexion.close()
