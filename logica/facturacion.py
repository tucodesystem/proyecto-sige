from datetime import datetime, timedelta
from db.conexion import conectar_db

def buscar_cliente_remision(termino):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT nit, razon_social, descuento_predeterminado FROM clientes WHERE nit LIKE %s OR razon_social LIKE %s LIMIT 5"
    cursor.execute(query, (f"%{termino}%", f"%{termino}%"))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def buscar_producto_remision(termino):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    query = """
        SELECT id_id_producto AS id_producto, nombre, precio, stock 
        FROM productos 
        WHERE id_id_producto LIKE %s OR nombre LIKE %s 
        LIMIT 10
    """
    cursor.execute(query, (f"%{termino}%", f"%{termino}%"))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def guardar_remision_bd(cliente_nit, carrito, forma_pago, plazo_dias, subtotal, descuento, total, observaciones="", id_edicion=None, fecha_manual=None):
    conexion = conectar_db()
    # Aseguramos que el cursor se defina como None por si falla la apertura
    cursor = None 
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # 1. ¡CRUCIAL! Iniciamos una transacción atómica explícita.
        # Esto le dice a MySQL: "No guardes nada en el disco hasta que yo te diga COMMIT"
        conexion.start_transaction()
        
        # Validar y limpiar datos
        plazo_int = int(plazo_dias) if str(plazo_dias).isdigit() else 0
        
        if fecha_manual:
            try:
                fecha_final = datetime.strptime(fecha_manual, "%Y-%m-%d").date()
            except:
                fecha_final = datetime.now().date()
        else:
            fecha_final = datetime.now().date()

        fecha_vencimiento = fecha_final + timedelta(days=plazo_int)
        
        if id_edicion:
            # --- MODO EDICIÓN ---
            cursor.execute("SELECT referencia_producto, cantidad FROM remisiones_detalle WHERE id_remision = %s", (id_edicion,))
            productos_antiguos = cursor.fetchall()
            
            # Devolver stock anterior
            for v in productos_antiguos:
                cursor.execute("UPDATE productos SET stock = stock + %s WHERE id_id_producto = %s", (v['cantidad'], v['referencia_producto']))
            
            # Limpiar detalles anteriores
            cursor.execute("DELETE FROM remisiones_detalle WHERE id_remision = %s", (id_edicion,))
            
            query_maestra = """
                UPDATE remisiones SET nit_cliente=%s, fecha_compra=%s, forma_pago=%s, plazo_dias=%s, 
                fecha_vencimiento=%s, subtotal=%s, descuento=%s, total=%s, observaciones=%s 
                WHERE id_remision=%s
            """
            cursor.execute(query_maestra, (cliente_nit, fecha_final, forma_pago, plazo_int, fecha_vencimiento, subtotal, descuento, total, observaciones, id_edicion))
            id_remision = id_edicion
        else:
            # --- MODO CREACIÓN ---
            query_maestra = """
                INSERT INTO remisiones (nit_cliente, fecha_compra, forma_pago, plazo_dias, fecha_vencimiento, subtotal, descuento, total, observaciones) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_maestra, (cliente_nit, fecha_final, forma_pago, plazo_int, fecha_vencimiento, subtotal, descuento, total, observaciones))
            id_remision = cursor.lastrowid
        
        # 2. Preparar consultas para el carrito
        query_detalle = "INSERT INTO remisiones_detalle (id_remision, referencia_producto, cantidad, valor_unitario, total_linea) VALUES (%s, %s, %s, %s, %s)"
        query_stock = "UPDATE productos SET stock = stock - %s WHERE id_id_producto = %s"
        
        # Ejecutar ráfaga de comandos en memoria
        for item in carrito:
            cursor.execute(query_detalle, (id_remision, item['id_producto'], item['cantidad'], item['precio_unitario'], item['subtotal_linea']))
            cursor.execute(query_stock, (item['cantidad'], item['id_producto']))
            
        # 3. Al terminar todo el bucle de manera exitosa, consolidamos en la BD de un solo golpe
        conexion.commit()
        return True, id_remision

    except Exception as e:
        # Si algo falló en cualquier inserción, deshacemos TODO al 100%
        if conexion:
            conexion.rollback()
        print(f"Error en guardar_remision_bd: {str(e)}")
        return False, str(e)
        
    finally:
        # Cerramos los recursos de manera ordenada para liberar la red
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()