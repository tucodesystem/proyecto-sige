import os
import sys
import customtkinter as ctk
from interfaz.vistas import VistaInventario, VistaDashboard, VistaTerceros
from interfaz.facturacion import VistaFacturacion 
from interfaz.consultas_remisiones import VistaConsultarRemisiones
from logica.consultas import obtener_detalle_completo_remision

# Importamos la conexión
from db.conexion import conectar_db

def obtener_ruta_recurso(ruta_relativa):
    """ Obtiene la ruta absoluta para recursos, compatible con PyInstaller y desarrollo """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, ruta_relativa)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión - Peluches Salem")
        self.geometry("1200x700")

        # --- 0. ESTABLECER CONEXIÓN INICIAL ---
        # Creamos una conexión persistente para pasar a las vistas que la requieran
        self.conexion_db = conectar_db()

        # --- CONFIGURACIÓN DEL ICONO DE LA VENTANA ---
        ruta_icono = obtener_ruta_recurso(os.path.join("imagenes", "logo.png"))
        if os.path.exists(ruta_icono):
            try:
                self.after(200, lambda: self.iconbitmap(ruta_icono))
            except Exception:
                self.wm_iconbitmap(ruta_icono)

        # Configuración de layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- 1. MENÚ DE NAVEGACIÓN (Lateral) ---
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        
        self.navigation_label = ctk.CTkLabel(self.navigation_frame, text="PELUCHES SALEM", 
                                             font=ctk.CTkFont(size=16, weight="bold"))
        self.navigation_label.grid(row=0, column=0, padx=20, pady=20)

        # Botones del Menú
        self.btn_dash = ctk.CTkButton(self.navigation_frame, text="📊 Dashboard ", 
                                      fg_color="transparent", text_color=("gray10", "gray90"), 
                                      hover_color=("gray70", "gray30"), anchor="w",
                                      command=self.mostrar_dashboard)
        self.btn_dash.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.btn_facturacion = ctk.CTkButton(self.navigation_frame, text="🧾 Nueva Remisión", 
                                             anchor="w", command=self.mostrar_facturacion)
        self.btn_facturacion.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.btn_consultas = ctk.CTkButton(self.navigation_frame, text="📋 Historial Remisiones", 
                                           anchor="w", command=self.mostrar_consultas)
        self.btn_consultas.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        self.btn_inventario = ctk.CTkButton(self.navigation_frame, text="📦 Inventario", 
                                            anchor="w", command=self.mostrar_inventario)
        self.btn_inventario.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        self.btn_terceros = ctk.CTkButton(self.navigation_frame, text="👥 Clientes", 
                                          anchor="w", command=self.mostrar_terceros)
        self.btn_terceros.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        # --- 2. CONTENEDOR DINÁMICO ---
        self.contenedor_vistas = ctk.CTkFrame(self, fg_color="transparent")
        self.contenedor_vistas.grid(row=0, column=1, sticky="nsew")
        
        # --- 3. INICIALIZACIÓN DE VISTAS (Inyectando conexión donde hace falta) ---
        self.vista_dash = VistaDashboard(self.contenedor_vistas)
        self.vista_inv = VistaInventario(self.contenedor_vistas)
        self.vista_terceros = VistaTerceros(self.contenedor_vistas)
        self.vista_fac = VistaFacturacion(self.contenedor_vistas)
        
        # CORRECCIÓN: Ahora pasamos 'self.conexion_db' para cumplir con el __init__ de la vista
        self.vista_consultas = VistaConsultarRemisiones(
            self.contenedor_vistas, 
            conexion=self.conexion_db, 
            comando_editar=self.ir_a_editar
        )

        # --- 4. VISTA INICIAL ---
        self.mostrar_dashboard()

    # --- MÉTODOS DE NAVEGACIÓN ---
    def ocultar_todas(self):
        self.vista_inv.pack_forget()
        self.vista_fac.pack_forget()
        self.vista_terceros.pack_forget()
        self.vista_dash.pack_forget()
        self.vista_consultas.pack_forget()

    def mostrar_dashboard(self):
        self.ocultar_todas()
        self.vista_dash.pack(fill="both", expand=True)

    def mostrar_facturacion(self):
        self.ocultar_todas()
        self.vista_fac.pack(fill="both", expand=True)

    def mostrar_consultas(self):
        self.ocultar_todas()
        self.vista_consultas.pack(fill="both", expand=True)
        # Solo intentamos cargar si la conexión existe
        if self.conexion_db:
            self.vista_consultas.cargar_datos()

    def mostrar_inventario(self):
        self.ocultar_todas()
        from logica.inventario import obtener_todos_los_productos
        datos = obtener_todos_los_productos()
        self.vista_inv.pack(fill="both", expand=True)
        self.vista_inv.cargar_datos(datos)

    def mostrar_terceros(self):
        self.ocultar_todas()
        self.vista_terceros.pack(fill="both", expand=True)
        self.vista_terceros.configurar_tab_clientes()

    def ir_a_editar(self, id_remision):
        # Aquí también podrías pasar la conexión si obtener_detalle_completo_remision la requiere
        maestra, carrito = obtener_detalle_completo_remision(id_remision)
        if maestra:
            self.mostrar_facturacion()
            self.vista_fac.cargar_remision_para_edicion(maestra, carrito)
        else:
            print("Error: No se pudo cargar la remisión para editar.")

if __name__ == "__main__":
    app = App()
    app.mainloop()