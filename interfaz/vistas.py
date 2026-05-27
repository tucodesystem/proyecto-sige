import csv
import customtkinter as ctk
from tkinter import messagebox, filedialog

# Importaciones lógicas globales
from logica.inventario import obtener_sugerencias_produccion
from logica.clientes import (
    registrar_vendedor, 
    obtener_vendedores, 
    actualizar_vendedor_db,
    eliminar_vendedor_db,
    registrar_cliente, 
    obtener_todos_los_clientes, 
    obtener_clientes_busqueda, 
    eliminar_cliente_db, 
    actualizar_cliente_db
)

# =================================================================
# 1. VISTA DASHBOARD (Sugerencias de Producción)
# =================================================================
class VistaDashboard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.label_titulo = ctk.CTkLabel(self, text="📊 Sugerencias de Producción Inmediata", 
                                         font=ctk.CTkFont(size=22, weight="bold"))
        self.label_titulo.pack(pady=20)

        self.frame_tabla = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frame_tabla.pack(expand=True, fill="both", padx=30, pady=10)

        self.cargar_sugerencias()

    def cargar_sugerencias(self):

        try:
            datos = obtener_sugerencias_produccion()
            if datos is None:
                # En lugar de colapsar, mostramos un aviso
                print("No se pudo conectar a la base de datos.")
                return
            # ... resto de tu código para cargar datos
        except Exception as e:
            print(f"Error al cargar sugerencias: {e}")
        
        for widget in self.frame_tabla.winfo_children():
            widget.destroy()

        datos = obtener_sugerencias_produccion()

        if not datos:
            ctk.CTkLabel(self.frame_tabla, text="✅ Todo el stock está al día.", 
                         font=("Arial", 16)).pack(pady=50)
            return

        header_font = ("Arial", 14, "bold")
        ctk.CTkLabel(self.frame_tabla, text="Peluche", font=header_font).grid(row=0, column=0, padx=20, pady=10)
        ctk.CTkLabel(self.frame_tabla, text="Stock Actual", font=header_font).grid(row=0, column=1, padx=20, pady=10)
        ctk.CTkLabel(self.frame_tabla, text="Mínimo", font=header_font).grid(row=0, column=2, padx=20, pady=10)
        ctk.CTkLabel(self.frame_tabla, text="Fabricar (Sugerido)", font=header_font).grid(row=0, column=3, padx=20, pady=10)

        for i, fila in enumerate(datos, start=1):
            color = "#FF4C4C" if fila['stock'] == 0 else "#FFA500" 
            
            ctk.CTkLabel(self.frame_tabla, text=fila['nombre']).grid(row=i, column=0, pady=5)
            ctk.CTkLabel(self.frame_tabla, text=fila['stock']).grid(row=i, column=1)
            ctk.CTkLabel(self.frame_tabla, text=fila['stock_minimo']).grid(row=i, column=2)
            ctk.CTkLabel(self.frame_tabla, text=f"+ {fila['sugerencia']}", 
                         text_color=color, font=("Arial", 14, "bold")).grid(row=i, column=3)


# =================================================================
# 2. VENTANA EMERGENTE PARA NUEVO PRODUCTO
# =================================================================
class VentanaNuevoProducto(ctk.CTkToplevel):
    def __init__(self, master, callback_actualizar, producto_editar=None, **kwargs):
        super().__init__(master, **kwargs)
        self.producto_editar = producto_editar
        self.callback_actualizar = callback_actualizar
        
        self.title("Editar Peluche" if producto_editar else "Añadir Peluche")
        self.geometry("400x600") 
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="Datos del Peluche", font=("Arial", 20, "bold")).pack(pady=20)

        # Campo Código
        ctk.CTkLabel(self, text="Código Único (Ej: PEL-001):", font=("Arial", 12)).pack(pady=(10, 0))
        self.entry_id = ctk.CTkEntry(self, placeholder_text="Código del peluche", width=250)
        self.entry_id.pack(pady=(5, 10))

        # Campo Nombre
        ctk.CTkLabel(self, text="Nombre:", font=("Arial", 12)).pack(pady=(10, 0))
        self.entry_nombre = ctk.CTkEntry(self, placeholder_text="Nombre", width=250)
        self.entry_nombre.pack(pady=(5, 10))
        
        # Campo Precio
        ctk.CTkLabel(self, text="Precio ($):", font=("Arial", 12)).pack(pady=(10, 0))
        self.entry_precio = ctk.CTkEntry(self, placeholder_text="Precio", width=250)
        self.entry_precio.pack(pady=(5, 10))
        
        # Campo Stock
        ctk.CTkLabel(self, text="Cantidad en Stock:", font=("Arial", 12)).pack(pady=(10, 0))
        self.entry_stock = ctk.CTkEntry(self, placeholder_text="Stock", width=250)
        self.entry_stock.pack(pady=(5, 10))
        
        # Campo Stock Mínimo
        ctk.CTkLabel(self, text="Mínimo para Alerta:", font=("Arial", 12)).pack(pady=(10, 0))
        self.entry_stock_minimo = ctk.CTkEntry(self, placeholder_text="Mínimo", width=250)
        self.entry_stock_minimo.pack(pady=(5, 10))

        # Lógica de Edición
        if self.producto_editar:
            self.entry_id.insert(0, self.producto_editar['id_id_producto'])
            self.entry_id.configure(state="disabled") 
            
            self.entry_nombre.insert(0, self.producto_editar['nombre'])
            self.entry_precio.insert(0, str(self.producto_editar['precio']))
            self.entry_stock.insert(0, str(self.producto_editar['stock']))
            self.entry_stock_minimo.insert(0, str(self.producto_editar['stock_minimo']))

        texto_btn = "Actualizar Cambios" if producto_editar else "Guardar Peluche"
        color_btn = "#28a745" if not producto_editar else "#ffc107"
        txt_color = "white" if not producto_editar else "black"

        self.btn_guardar = ctk.CTkButton(self, text=texto_btn, 
                                         fg_color=color_btn, 
                                         text_color=txt_color,
                                         command=self.validar_y_guardar)
        self.btn_guardar.pack(pady=40)

    def validar_y_guardar(self):
        try:
            id_manual = self.entry_id.get().strip() 
            nombre = self.entry_nombre.get().strip()
            precio_str = self.entry_precio.get().strip()
            stock_str = self.entry_stock.get().strip()
            minimo_str = self.entry_stock_minimo.get().strip()

            if not self.producto_editar and not id_manual:
                messagebox.showwarning("Atención", "El Código Único es obligatorio.")
                return
            if not nombre:
                messagebox.showwarning("Atención", "El Nombre es obligatorio.")
                return

            try:
                precio = float(precio_str)
                stock = int(stock_str)
                minimo = int(minimo_str)
                
                if precio < 0 or stock < 0 or minimo < 0:
                     messagebox.showwarning("Atención", "Los números no pueden ser negativos.")
                     return
            except ValueError:
                messagebox.showerror("Error", "Precio, Stock y Mínimo deben ser números válidos.")
                return

            # Importación local para evitar bucles circulares
            from logica.inventario import registrar_nuevo_producto, actualizar_producto_db
            
            if self.producto_editar:
                id_fijo = self.producto_editar['id_id_producto']
                exito = actualizar_producto_db(id_fijo, nombre, precio, stock, minimo)
            else:
                exito = registrar_nuevo_producto(id_manual, nombre, precio, stock, minimo)

            if exito:
                messagebox.showinfo("Éxito", "Peluche guardado correctamente.")
                self.callback_actualizar()
                self.destroy() 
            else:
                messagebox.showerror("Error", "No se pudo guardar en la base de datos.")

        except Exception as e:
            messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado:\n{e}")


# =================================================================
# 3. VISTA INVENTARIO
# =================================================================
class VistaInventario(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.productos_todos = [] 
        
        self.label = ctk.CTkLabel(self, text="📦 Gestión de Inventario", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=10)

        self.frame_control = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_control.pack(pady=10, padx=20, fill="x")

        self.entry_busqueda = ctk.CTkEntry(self.frame_control, placeholder_text="🔍 Buscar por nombre o código...", width=300)
        self.entry_busqueda.pack(side="left", padx=5)
        self.entry_busqueda.bind("<KeyRelease>", lambda event: self.filtrar_productos())

        self.combo_orden = ctk.CTkComboBox(
            self.frame_control, 
            values=["Orden: Por Defecto", "Stock: Mayor a Menor", "Stock: Menor a Mayor", "Nombre: A-Z"],
            command=lambda choice: self.filtrar_productos(),
            width=180
        )
        self.combo_orden.pack(side="left", padx=5)
        self.combo_orden.set("Orden: Por Defecto")

        self.btn_nuevo = ctk.CTkButton(
            self.frame_control, text="+ Nuevo Peluche", 
            fg_color="#28a745", hover_color="#218838", width=130,
            command=self.abrir_ventana_registro
        )
        self.btn_nuevo.pack(side="right", padx=5)

        self.btn_exportar = ctk.CTkButton(
            self.frame_control, text="📥 Exportar Excel", 
            fg_color="#17a2b8", hover_color="#138496", width=130,
            command=self.exportar_inventario
        )
        self.btn_exportar.pack(side="right", padx=5)

        self.contenedor_tabla = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.contenedor_tabla.pack(padx=20, pady=10, fill="both", expand=True)

        self.actualizar_lista_completa()

    def actualizar_lista_completa(self):
        from logica.inventario import obtener_todos_los_productos
        self.productos_todos = obtener_todos_los_productos()
        self.cargar_datos(self.productos_todos)

    def filtrar_productos(self, event=None): 
        termino = self.entry_busqueda.get().lower()
        orden = self.combo_orden.get()
        
        filtrados = [
            p for p in self.productos_todos 
            if termino in p['nombre'].lower() or termino in str(p['id_id_producto']).lower()
        ]
        
        if orden == "Stock: Mayor a Menor":
            filtrados.sort(key=lambda x: x['stock'], reverse=True)
        elif orden == "Stock: Menor a Mayor":
            filtrados.sort(key=lambda x: x['stock'])
        elif orden == "Nombre: A-Z":
            filtrados.sort(key=lambda x: x['nombre'].lower())

        self.cargar_datos(filtrados)

    def abrir_ventana_registro(self, producto_para_editar=None):
        VentanaNuevoProducto(
            self, 
            callback_actualizar=self.actualizar_lista_completa,
            producto_editar=producto_para_editar
        )

    def ajustar_stock(self, producto, cantidad):
        from logica.inventario import ajustar_stock_rapido, obtener_todos_los_productos
        id_p = producto['id_id_producto']
        
        if ajustar_stock_rapido(id_p, cantidad):
            self.productos_todos = obtener_todos_los_productos()
            self.filtrar_productos() 
        else:
            messagebox.showerror("Error", "No se pudo actualizar el stock en la base de datos.")

    def confirmar_eliminacion(self, producto):
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar '{producto['nombre']}'?"):
            from logica.inventario import eliminar_producto_db
            if eliminar_producto_db(producto['id_id_producto']):
                self.actualizar_lista_completa()
                messagebox.showinfo("Éxito", "Producto eliminado correctamente")
            else:
                messagebox.showerror("Error", "No se pudo eliminar. Verifica si tiene ventas asociadas.")

    def cargar_datos(self, lista):
        for child in self.contenedor_tabla.winfo_children():
            child.destroy()

        headers = ["ID", "Nombre", "Precio", "Stock", "Mínimo", "Acciones"]
        h_frame = ctk.CTkFrame(self.contenedor_tabla, fg_color="gray30")
        h_frame.pack(fill="x", pady=2, padx=5)
        
        for i, text in enumerate(headers):
            ancho = 100 if i != 1 else 180 
            ctk.CTkLabel(h_frame, text=text, width=ancho, font=("Arial", 12, "bold")).grid(row=0, column=i, padx=5)

        for p in lista:
            fila = ctk.CTkFrame(self.contenedor_tabla)
            fila.pack(fill="x", pady=1, padx=5)

            # 1. ID
            ctk.CTkLabel(fila, text=p['id_id_producto'], width=100).grid(row=0, column=0, padx=5)
            
            # 2. Nombre
            ctk.CTkLabel(fila, text=p['nombre'], width=180, anchor="w").grid(row=0, column=1, padx=5)
            
            # 3. PRECIO (FORMATO COLOMBIANO FORZADO)
            # Convertimos a float por si viene como string de la BD
            valor_precio = float(p['precio'])
            precio_fmt = f"${valor_precio:,.0f}".replace(",", ".")
            ctk.CTkLabel(fila, text=precio_fmt, width=100).grid(row=0, column=2, padx=5)
            
            # 4. STOCK
            color_txt = "white" if p['stock'] > p['stock_minimo'] else "#ff6666"
            ctk.CTkLabel(fila, text=p['stock'], width=100, text_color=color_txt, font=("Arial", 13, "bold")).grid(row=0, column=3, padx=5)
            
            # 5. MÍNIMO
            ctk.CTkLabel(fila, text=p['stock_minimo'], width=100).grid(row=0, column=4, padx=5)

            # 6. ACCIONES
            frame_acciones = ctk.CTkFrame(fila, fg_color="transparent")
            frame_acciones.grid(row=0, column=5, padx=5)

            ctk.CTkButton(frame_acciones, text="-", width=30, height=28, fg_color="#c0392b", 
                          command=lambda prod=p: self.ajustar_stock(prod, -1)).pack(side="left", padx=1)
            
            ctk.CTkButton(frame_acciones, text="+", width=30, height=28, fg_color="#27ae60", 
                          command=lambda prod=p: self.ajustar_stock(prod, 1)).pack(side="left", padx=1)

            ctk.CTkButton(frame_acciones, text="✏️", width=30, height=28, fg_color="#34495e", 
                          command=lambda prod=p: self.abrir_ventana_registro(prod)).pack(side="left", padx=1)

            ctk.CTkButton(frame_acciones, text="🗑️", width=30, height=28, fg_color="#721c24", hover_color="#dc3545",
                          command=lambda prod=p: self.confirmar_eliminacion(prod)).pack(side="left", padx=1)
            
    def exportar_inventario(self):
        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv"), ("Todos los archivos", "*.*")],
            title="Guardar Inventario como..."
        )
        
        if not ruta_archivo:
            return 
            
        try:
            with open(ruta_archivo, mode='w', newline='', encoding='utf-8-sig') as archivo:
                writer = csv.writer(archivo, delimiter=';') 
                writer.writerow(["ID / Código", "Nombre del Peluche", "Precio ($)", "Stock Actual", "Stock Mínimo"])
                
                for p in self.productos_todos:
                    writer.writerow([
                        p['id_id_producto'], 
                        p['nombre'], 
                        p['precio'], 
                        p['stock'], 
                        p['stock_minimo']
                    ])
            
            messagebox.showinfo("Éxito", "¡Inventario exportado correctamente!\nYa puedes abrirlo en Excel.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al exportar:\n{e}")


# =================================================================
# 4. VISTA TERCEROS (Clientes y Distribuidores)
# =================================================================
class VistaTerceros(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.distribuidores_db = []
        self.editando_nit = None           
        self.editando_vendedor_id = None    
        
        self.label_titulo = ctk.CTkLabel(self, text="👥 Gestión de Red Comercial (Salem)", 
                                        font=ctk.CTkFont(size=24, weight="bold"))
        self.label_titulo.pack(pady=10)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.tab_clientes = self.tabs.add("Clientes (Locales)")
        self.tab_distribuidores = self.tabs.add("Distribuidores")

        self.configurar_tab_clientes()
        self.configurar_tab_distribuidores()

    def configurar_tab_clientes(self):
        for widget in self.tab_clientes.winfo_children(): widget.destroy()

        self.frame_form = ctk.CTkFrame(self.tab_clientes)
        self.frame_form.pack(pady=15, padx=20, fill="x")
        
        self.lbl_form_info = ctk.CTkLabel(self.frame_form, text="📝 REGISTRAR NUEVO LOCAL", font=("Arial", 13, "bold"))
        self.lbl_form_info.grid(row=0, column=0, columnspan=6, pady=10)

        campos = [
            ("NIT:", "ent_nit", 1, 0), ("Razón Social:", "ent_razon", 1, 2), ("Teléfono:", "ent_tel", 1, 4),
            ("Rep. Legal:", "ent_rep", 2, 0), ("Doc. RP:", "ent_doc_rp", 2, 2), ("Distribuidor:", "combo_dist", 2, 4),
            ("Dirección:", "ent_dir", 3, 0), ("Ciudad:", "ent_ciudad", 3, 2), ("Departamento:", "ent_depto", 3, 4)
        ]

        for label, var_name, r, c in campos:
            ctk.CTkLabel(self.frame_form, text=label).grid(row=r, column=c, padx=5, pady=5, sticky="e")
            if var_name == "combo_dist":
                self.combo_dist = ctk.CTkComboBox(self.frame_form, values=["Ninguno"], width=150)
                self.combo_dist.grid(row=r, column=c+1, padx=5, pady=5)
            else:
                setattr(self, var_name, ctk.CTkEntry(self.frame_form, width=150 if "razon" not in var_name else 200))
                getattr(self, var_name).grid(row=r, column=c+1, padx=5, pady=5)

        self.btn_save = ctk.CTkButton(self.frame_form, text="💾 Guardar Cliente", fg_color="#28a745", 
                                     command=self.guardar_cliente, height=35)
        self.btn_save.grid(row=4, column=2, columnspan=2, pady=15)

        self.btn_cancelar = ctk.CTkButton(self.frame_form, text="Cancelar", fg_color="#6c757d", 
                                        command=self.limpiar_formulario, height=35)

        self.ent_buscar = ctk.CTkEntry(self.tab_clientes, placeholder_text="🔍 Buscar por NIT o Razón Social...", width=450)
        self.ent_buscar.pack(pady=10)
        self.ent_buscar.bind("<KeyRelease>", lambda e: self.actualizar_tabla_clientes())

        self.frame_tabla = ctk.CTkScrollableFrame(self.tab_clientes, fg_color="transparent")
        self.frame_tabla.pack(fill="both", expand=True, padx=20, pady=5)

        self.cargar_distribuidores_en_combo()
        self.actualizar_tabla_clientes()

    def guardar_cliente(self):
        nit_n = self.ent_nit.get()
        razon = self.ent_razon.get()
        if not nit_n or not razon:
            messagebox.showwarning("Atención", "NIT y Razón Social requeridos")
            return

        dist_nom = self.combo_dist.get()
        id_dist = next((d['id_vendedor'] for d in self.distribuidores_db if d['nombre_vendedor'] == dist_nom), None)

        if self.editando_nit:
            exito = actualizar_cliente_db(self.editando_nit, nit_n, razon, self.ent_rep.get(), 
                                         self.ent_doc_rp.get(), self.ent_dir.get(), 
                                         self.ent_ciudad.get(), self.ent_depto.get(), 
                                         self.ent_tel.get(), id_dist)
            mensaje = "Cliente actualizado correctamente"
        else:
            exito = registrar_cliente(nit_n, razon, self.ent_rep.get(), self.ent_doc_rp.get(), 
                                     self.ent_dir.get(), self.ent_ciudad.get(), 
                                     self.ent_depto.get(), self.ent_tel.get(), id_dist)
            mensaje = "Cliente registrado con éxito"

        if exito:
            messagebox.showinfo("Éxito", mensaje)
            self.limpiar_formulario()
            self.actualizar_tabla_clientes()
        else:
            messagebox.showerror("Error", "No se pudo procesar la solicitud")

    def preparar_edicion(self, c):
        self.editando_nit = c['nit']
        self.lbl_form_info.configure(text=f"⚠️ EDITANDO CLIENTE: {c['razon_social']}", text_color="#ffc107")
        self.btn_save.configure(text="🔄 Actualizar Datos", fg_color="#1f538d")
        self.btn_cancelar.grid(row=4, column=4, padx=5)

        self.ent_nit.delete(0, 'end'); self.ent_nit.insert(0, c['nit'])
        self.ent_razon.delete(0, 'end'); self.ent_razon.insert(0, c['razon_social'])
        self.ent_tel.delete(0, 'end'); self.ent_tel.insert(0, c['telefono'])
        self.ent_rep.delete(0, 'end'); self.ent_rep.insert(0, c['representante_legal'] or "")
        self.ent_doc_rp.delete(0, 'end'); self.ent_doc_rp.insert(0, c['documento_rp'] or "")
        self.ent_dir.delete(0, 'end'); self.ent_dir.insert(0, c['direccion'] or "")
        self.ent_ciudad.delete(0, 'end'); self.ent_ciudad.insert(0, c['ciudad'] or "")
        self.ent_depto.delete(0, 'end'); self.ent_depto.insert(0, c['departamento'] or "")
        self.combo_dist.set(c['nombre_vendedor'] if c['nombre_vendedor'] else "Ninguno")

    def limpiar_formulario(self):
        self.editando_nit = None
        self.lbl_form_info.configure(text="📝 REGISTRAR NUEVO LOCAL", text_color="white")
        self.btn_save.configure(text="💾 Guardar Cliente", fg_color="#28a745")
        self.btn_cancelar.grid_forget()
        for attr in ["ent_nit", "ent_razon", "ent_tel", "ent_rep", "ent_doc_rp", "ent_dir", "ent_ciudad", "ent_depto"]:
            getattr(self, attr).delete(0, 'end')
        self.combo_dist.set("Ninguno")

    def actualizar_tabla_clientes(self, event=None):
        for w in self.frame_tabla.winfo_children(): w.destroy()
        termino = self.ent_buscar.get()
        clientes = obtener_clientes_busqueda(termino) if termino else obtener_todos_los_clientes()
        anchos = {"nit": 110, "razon": 240, "tel": 120, "ciu": 140, "dist": 180, "acc": 120}

        h_frame = ctk.CTkFrame(self.frame_tabla, fg_color="gray30")
        h_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(h_frame, text="NIT", width=anchos["nit"], font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="Razón Social", width=anchos["razon"], font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="Distribuidor", width=anchos["dist"], font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="Acciones", width=anchos["acc"], font=("Arial", 12, "bold")).pack(side="right", padx=10)

        for c in clientes:
            fila = ctk.CTkFrame(self.frame_tabla)
            fila.pack(fill="x", pady=1)
            ctk.CTkLabel(fila, text=c['nit'], width=anchos["nit"]).pack(side="left", padx=5)
            ctk.CTkLabel(fila, text=c['razon_social'][:25], width=anchos["razon"]).pack(side="left", padx=5)
            ctk.CTkLabel(fila, text=c['nombre_vendedor'] or "DIRECTO", width=anchos["dist"]).pack(side="left", padx=5)
            
            btn_f = ctk.CTkFrame(fila, fg_color="transparent")
            btn_f.pack(side="right", padx=10)
            ctk.CTkButton(btn_f, text="🗑️", width=35, fg_color="#721c24", command=lambda n=c['nit']: self.borrar_cliente(n)).pack(side="right", padx=2)
            ctk.CTkButton(btn_f, text="✏️", width=35, fg_color="#1f538d", command=lambda data=c: self.preparar_edicion(data)).pack(side="right", padx=2)

    def borrar_cliente(self, nit):
        if messagebox.askyesno("Confirmar", f"¿Eliminar cliente NIT {nit}?"):
            if eliminar_cliente_db(nit): self.actualizar_tabla_clientes()
            else: messagebox.showerror("Error", "No se puede eliminar (tiene registros asociados)")

    def configurar_tab_distribuidores(self):
        for widget in self.tab_distribuidores.winfo_children(): widget.destroy()

        self.frame_dist = ctk.CTkFrame(self.tab_distribuidores)
        self.frame_dist.pack(pady=20, padx=20, fill="x")

        self.lbl_info_dist = ctk.CTkLabel(self.frame_dist, text="📝 REGISTRAR NUEVO DISTRIBUIDOR", font=("Arial", 13, "bold"))
        self.lbl_info_dist.pack(pady=10)

        f_input = ctk.CTkFrame(self.frame_dist, fg_color="transparent")
        f_input.pack(pady=10)

        ctk.CTkLabel(f_input, text="Nombre:").pack(side="left", padx=5)
        self.ent_nombre_dist = ctk.CTkEntry(f_input, width=300)
        self.ent_nombre_dist.pack(side="left", padx=5)

        self.btn_save_dist = ctk.CTkButton(f_input, text="💾 Guardar", fg_color="#28a745", width=100, command=self.guardar_distribuidor)
        self.btn_save_dist.pack(side="left", padx=10)

        self.btn_cancel_dist = ctk.CTkButton(f_input, text="Cancelar", fg_color="#6c757d", width=80, command=self.limpiar_form_dist)

        self.frame_listado_dist = ctk.CTkScrollableFrame(self.tab_distribuidores, fg_color="transparent")
        self.frame_listado_dist.pack(fill="both", expand=True, padx=40, pady=10)

        self.actualizar_tabla_distribuidores()

    def guardar_distribuidor(self):
        nombre = self.ent_nombre_dist.get().strip()
        if not nombre: return

        if self.editando_vendedor_id:
            exito = actualizar_vendedor_db(self.editando_vendedor_id, nombre)
            msj = "Distribuidor actualizado"
        else:
            exito = registrar_vendedor(nombre)
            msj = "Distribuidor registrado"

        if exito:
            messagebox.showinfo("Éxito", msj)
            self.limpiar_form_dist()
            self.actualizar_tabla_distribuidores()
            self.cargar_distribuidores_en_combo()
        else:
            messagebox.showerror("Error", "No se pudo procesar la solicitud")

    def preparar_edicion_dist(self, v):
        self.editando_vendedor_id = v['id_vendedor']
        self.ent_nombre_dist.delete(0, 'end')
        self.ent_nombre_dist.insert(0, v['nombre_vendedor'])
        self.lbl_info_dist.configure(text=f"⚠️ EDITANDO: {v['nombre_vendedor']}", text_color="#ffc107")
        self.btn_save_dist.configure(text="🔄 Actualizar", fg_color="#1f538d")
        self.btn_cancel_dist.pack(side="left", padx=5)

    def limpiar_form_dist(self):
        self.editando_vendedor_id = None
        self.ent_nombre_dist.delete(0, 'end')
        self.lbl_info_dist.configure(text="📝 REGISTRAR NUEVO DISTRIBUIDOR", text_color="white")
        self.btn_save_dist.configure(text="💾 Guardar", fg_color="#28a745")
        self.btn_cancel_dist.pack_forget()

    def borrar_distribuidor(self, id_v, nombre):
        if messagebox.askyesno("Confirmar", f"¿Eliminar a '{nombre}'?"):
            if eliminar_vendedor_db(id_v):
                self.actualizar_tabla_distribuidores()
                self.cargar_distribuidores_en_combo()
            else:
                messagebox.showerror("Error", "No se puede eliminar (tiene clientes asignados)")

    def actualizar_tabla_distribuidores(self):
        for w in self.frame_listado_dist.winfo_children(): w.destroy()
        vendedores = obtener_vendedores()
        for v in vendedores:
            fila = ctk.CTkFrame(self.frame_listado_dist)
            fila.pack(fill="x", pady=2)
            ctk.CTkLabel(fila, text=f"ID: {v['id_vendedor']}", width=60).pack(side="left", padx=10)
            ctk.CTkLabel(fila, text=v['nombre_vendedor'], anchor="w").pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkButton(fila, text="🗑️", width=35, fg_color="#721c24", command=lambda d=v: self.borrar_distribuidor(d['id_vendedor'], d['nombre_vendedor'])).pack(side="right", padx=5)
            ctk.CTkButton(fila, text="✏️", width=35, fg_color="#1f538d", command=lambda d=v: self.preparar_edicion_dist(d)).pack(side="right", padx=2)

    def cargar_distribuidores_en_combo(self):
        self.distribuidores_db = obtener_vendedores()
        nombres = ["Ninguno"] + [d['nombre_vendedor'] for d in self.distribuidores_db]
        if hasattr(self, 'combo_dist'):
            self.combo_dist.configure(values=nombres)