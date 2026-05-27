import mysql.connector

def conectar_db():
    try:
        conexion = mysql.connector.connect(
            host='localhost',          # Cambiar por la IP del servidor si estás en red local
            user='root',               # Tu usuario de BD
            password='',               # Tu contraseña de BD
            database='bd_peluches',    # Tu base de datos
            use_pure=True,             #S Forza el uso de Python puro para evitar líos al compilar
            connect_timeout=10,        # ROBUSTEZ: Tiempo máximo de espera para evitar congelamientos
            autocommit=False           # ROBUSTEZ: Transacciones seguras manuales
        )
        
        # Validamos si la conexión fue exitosa
        if conexion.is_connected():
            return conexion
            
        # Retorno explícito si falló la conexión sin lanzar excepción
        return None

    except mysql.connector.Error as error_bd:
        # Capturamos específicamente errores de MySQL (credenciales, red, etc.)
        print(f"[Error de Base de Datos] No se pudo conectar: {error_bd}")
        return None
        
    except Exception as e:
        # Capturamos cualquier otro error inesperado
        print(f"[Error Inesperado] Fallo en el módulo de conexión: {e}")
        return None