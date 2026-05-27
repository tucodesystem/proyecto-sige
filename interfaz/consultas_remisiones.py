import os
import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog

# Importamos la lógica de base de datos
from logica.consultas import (
    obtener_remisiones_listado, 
    anular_remision_bd,
    obtener_maestra_remision,
    obtener_detalle_remision
)

# Importamos el generador de PDF
from utilidades.generador_pdf import generar_pdf_remision


class VistaConsultarRemisiones(ctk.CTkFrame):
    def __init__(self, master, conexion, comando_editar=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.comando_editar = comando_editar
        self.conexion_actual = conexion  # Conexión inyectada desde App

        # --- ESTILOS DE LA TABLA ---
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", 
                        fieldbackground="#2b2b2b", borderwidth=0, rowheight=30)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[('selected', '#1f538d')])

        ctk.CTkLabel(self, text="📋 HISTORIAL DE REMISIONES", font=("Arial", 22, "bold")).pack(pady=10)

        # --- 1. Buscador y Botón Recargar ---
        self.frame_busqueda = ctk.CTkFrame(self)
        self.frame_busqueda.pack(fill="x", padx=20, pady=10)
        
        self.ent_busqueda = ctk.CTkEntry(self.frame_busqueda, placeholder_text="🔍 Buscar por cliente, NIT o # Remisión...", width=400)
        self.ent_busqueda.pack(side="left", padx=10, pady=10)
        
        # 🔄 NUEVO: Botón para recargar los datos manualmente
        self.btn_recargar = ctk.CTkButton(
            self.frame_busqueda, 
            text="🔄 Actualizar", 
            width=110, 
            fg_color="#28a745", 
            hover_color="#218838", 
            command=self.cargar_datos
        )
        self.btn_recargar.pack(side="left", padx=5, pady=10)
        
        # Evento para buscar mientras se escribe
        self.ent_busqueda.bind("<KeyRelease>", lambda e: self.cargar_datos())

        # --- 2. Tabla ---
        self.frame_tabla = ctk.CTkFrame(self)
        self.frame_tabla.pack(fill="both", expand=True, padx=20, pady=5)
        
        cols = ("id", "fecha", "nit", "cliente", "total")
        self.tabla = ttk.Treeview(self.frame_tabla, columns=cols, show="headings")
        
        self.tabla.heading("id", text="# REMISIÓN")
        self.tabla.column("id", width=100, anchor="center")
        
        self.tabla.heading("fecha", text="FECHA")
        self.tabla.column("fecha", width=120, anchor="center")
        
        self.tabla.heading("nit", text="NIT CLIENTE")
        self.tabla.column("nit", width=150, anchor="center")
        
        self.tabla.heading("cliente", text="RAZÓN SOCIAL")
        self.tabla.column("cliente", width=300, anchor="w")
        
        self.tabla.heading("total", text="VALOR TOTAL")
        self.tabla.column("total", width=150, anchor="e")
        
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

        # --- 3. Botones de Acción ---
        self.frame_acciones = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acciones.pack(fill="x", padx=20, pady=15)
        
        self.btn_ver = ctk.CTkButton(self.frame_acciones, text="👁️ Ver Detalle / PDF", fg_color="#1f538d", command=self.exportar_y_abrir_pdf)
        self.btn_ver.pack(side="left", padx=5)

        self.btn_anular = ctk.CTkButton(self.frame_acciones, text="🗑️ Anular", fg_color="#dc3545", hover_color="#c82333", command=self.ejecutar_anulacion)
        self.btn_anular.pack(side="right", padx=5)
        
        self.btn_editar = ctk.CTkButton(self.frame_acciones, text="✏️ Editar", fg_color="#ffc107", hover_color="#e0a800", text_color="black", command=self.solicitar_edicion)
        self.btn_editar.pack(side="right", padx=5)

        # Cargar datos al iniciar
        self.cargar_datos()

    def cargar_datos(self):
        """Refresca la tabla con los datos de la DB"""
        try:
            # 1. Limpiamos la tabla
            for i in self.tabla.get_children(): 
                self.tabla.delete(i)
                
            # 2. Obtenemos el texto de búsqueda
            busqueda = self.ent_busqueda.get()
            
            # 3. Llamamos a la lógica inyectando la conexión
            remisiones = obtener_remisiones_listado(busqueda, self.conexion_actual)
            
            # 4. Llenamos la tabla
            if remisiones:
                for r in remisiones:
                    # Formateo de moneda
                    valor_num = r.get('total', 0)
                    total_fmt = f"${float(valor_num):,.0f}".replace(",", ".")
                    
                    self.tabla.insert("", "end", values=(
                        r.get('id_remision', 'N/A'), 
                        r.get('fecha_compra', 'N/A'), 
                        r.get('nit_cliente', 'N/A'), 
                        r.get('razon_social', 'SIN NOMBRE'), 
                        total_fmt
                    ))
                
        except ConnectionError as ce:
            messagebox.showerror("Error de Conexión", str(ce))
        except Exception as e:
            messagebox.showerror("Error del Sistema", f"No se pudo cargar la tabla:\n{str(e)}")

    def ejecutar_anulacion(self):
        """Borra la remisión y devuelve el stock"""
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione una remisión de la lista.")
            return
        
        id_rem = self.tabla.item(seleccion)['values'][0]
        if messagebox.askyesno("Confirmar", f"¿Está seguro de ANULAR la remisión #{id_rem}?\nEsto devolverá los artículos al inventario."):
            exito, msj = anular_remision_bd(id_rem, self.conexion_actual)
            
            if exito:
                messagebox.showinfo("Éxito", msj)
                self.cargar_datos() # Refrescamos la tabla automáticamente al anular
            else:
                messagebox.showerror("Error", msj)

    def solicitar_edicion(self):
        """Envía el ID al comando puente en AppPrincipal"""
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione una remisión para editar.")
            return
        
        id_rem = self.tabla.item(seleccion)['values'][0]
        if self.comando_editar:
            self.comando_editar(id_rem)

    def exportar_y_abrir_pdf(self):
        """Genera y abre el PDF Premium de la remisión seleccionada"""
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona una remisión de la tabla para generar el PDF.")
            return

        valores_fila = self.tabla.item(seleccion[0], "values")
        id_remision = valores_fila[0]
        nombre_cliente = valores_fila[3].replace(" ", "_") 

        try:
            maestra = obtener_maestra_remision(id_remision, self.conexion_actual)
            productos = obtener_detalle_remision(id_remision, self.conexion_actual)

            if not maestra or not productos:
                messagebox.showerror("Error", "Datos incompletos de la remisión en la base de datos.")
                return

            nombre_sugerido = f"Remision_{id_remision}_{nombre_cliente}.pdf"
            ruta_guardado = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile=nombre_sugerido,
                filetypes=[("Archivo PDF", "*.pdf")],
                title="Guardar PDF de Remisión"
            )

            if not ruta_guardado:
                return  

            exito, msj = generar_pdf_remision(ruta_guardado, maestra, productos)

            if exito:
                if os.name == 'nt':
                    os.startfile(ruta_guardado)
                elif os.name == 'posix':
                    import subprocess
                    subprocess.call(['open' if 'darwin' in os.sys.platform else 'xdg-open', ruta_guardado])
            else:
                messagebox.showerror("Error al generar PDF", msj)

        except ConnectionError as ce:
            messagebox.showerror("Error de Conexión", str(ce))
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al procesar el PDF:\n{str(e)}")