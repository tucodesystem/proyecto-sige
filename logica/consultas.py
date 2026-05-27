from db.conexion import conectar_db

def obtener_remisiones_listado(busqueda, conexion):
    # 🛡️ Protección visual: En vez de explotar, devolvemos lista vacía si no hay red
    if conexion is None or not conexion.is_connected():
        return []

    try:
        # 🌟 EL TRUCO DEL ARQUITECTO: Romper la burbuja de tiempo.
        # Esto obliga a MySQL a soltar la caché vieja y leer los datos nuevos.
        conexion.commit() 
        
        cursor = conexion.cursor(dictionary=True)
        
        # Unimos remisiones (r) con clientes (t) 
        query = """
            SELECT r.*, t.razon_social 
            FROM remisiones r
            INNER JOIN clientes t ON r.nit_cliente = t.nit
            WHERE t.razon_social LIKE %s OR r.id_remision LIKE %s
        """
        
        parametro = f"%{busqueda}%"
        cursor.execute(query, (parametro, parametro))
        
        resultados = cursor.fetchall()
        return resultados
        
    except Exception as e:
        print(f"Fallo en SQL al listar: {str(e)}")
        return [] # Evita que la interfaz se caiga si hay un error SQL
        
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()

def anular_remision_bd(id_remision, conexion):
    """Borra la remisión y restaura el stock usando la conexión inyectada"""
    if conexion is None or not conexion.is_connected():
        return False, "Sin conexión a la base de datos."
        
    cursor = conexion.cursor(dictionary=True)
    try:
        # 1. Obtener productos para devolver al stock
        cursor.execute("SELECT referencia_producto, cantidad FROM remisiones_detalle WHERE id_remision = %s", (id_remision,))
        detalles = cursor.fetchall()
        
        query_stock = "UPDATE productos SET stock = stock + %s WHERE id_id_producto = %s"
        for item in detalles:
            cursor.execute(query_stock, (item['cantidad'], item['referencia_producto']))
            
        # 2. Borrar detalle y cabecera
        cursor.execute("DELETE FROM remisiones_detalle WHERE id_remision = %s", (id_remision,))
        cursor.execute("DELETE FROM remisiones WHERE id_remision = %s", (id_remision,))
        
        conexion.commit()
        return True, "Remisión anulada y stock restaurado con éxito."
    except Exception as e:
        conexion.rollback()
        return False, f"Error al anular: {str(e)}"
    finally:
        cursor.close()

# 3. DATOS MAESTROS (PARA PDF / EDICIÓN)
def obtener_maestra_remision(id_remision, conexion):
    """Trae los datos de cabecera emparejados con la tabla clientes"""
    if conexion is None or not conexion.is_connected():
        return None

    cursor = conexion.cursor(dictionary=True)
    try:
        # Usamos los nombres exactos de tu captura de pantalla (razon_social, representante_legal, etc.)
        query = """
            SELECT 
                r.*, 
                c.razon_social, 
                c.direccion, 
                c.telefono, 
                c.ciudad,
                c.departamento,
                c.representante_legal,
                c.documento_rp,
                c.plazo_pago_dias,
                c.descuento_predeterminado 
            FROM remisiones r 
            JOIN clientes c ON r.nit_cliente = c.nit 
            WHERE r.id_remision = %s
        """
        cursor.execute(query, (id_remision,))
        return cursor.fetchone()
    finally:
        cursor.close()

# 4. DETALLE DE PRODUCTOS
def obtener_detalle_remision(id_remision, conexion):
    """Trae la lista de productos de una remisión"""
    if conexion is None or not conexion.is_connected():
        return []

    cursor = conexion.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                rd.referencia_producto AS id_producto, 
                p.nombre, 
                rd.cantidad, 
                rd.valor_unitario AS precio_unitario, 
                rd.total_linea AS subtotal_linea
            FROM remisiones_detalle rd
            JOIN productos p ON rd.referencia_producto = p.id_id_producto
            WHERE rd.id_remision = %s
        """
        cursor.execute(query, (id_remision,))
        return cursor.fetchall()
    finally:
        cursor.close()
        
# 5. FUNCIÓN COMPLETA PARA EDICIÓN
def obtener_detalle_completo_remision(id_remision, conexion):
    """Retorna maestra y carrito en una sola llamada"""
    maestra = obtener_maestra_remision(id_remision, conexion)
    carrito = obtener_detalle_remision(id_remision, conexion)
    return maestra, carrito