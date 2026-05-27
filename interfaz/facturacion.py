import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
from logica.facturacion import buscar_cliente_remision, buscar_producto_remision, guardar_remision_bd

class VistaFacturacion(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # --- ESTADO DE LA VISTA ---
        self.carrito = [] 
        self.cliente_actual = None
        self.producto_actual = None
        self.ventana_sugerencias = None
        self.id_edicion = None # Si tiene ID, estamos editando una existente
        self.totales = {"subtotal": 0, "descuento": 0, "total": 0}

        # --- CONFIGURACIÓN DE ESTILOS (TABLA) ---
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", 
                        fieldbackground="#2b2b2b", borderwidth=0, rowheight=30)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[('selected', '#1f538d')])

        ctk.CTkLabel(self, text="📑 GENERADOR DE REMISIONES", font=("Arial", 22, "bold")).pack(pady=10)

        # --- SECCIÓN SUPERIOR: CLIENTE Y CONTROL ---
        self.frame_cliente = ctk.CTkFrame(self)
        self.frame_cliente.pack(padx=20, pady=5, fill="x")
        
        self.ent_buscar_cli = ctk.CTkEntry(self.frame_cliente, width=250, placeholder_text="🔍 Buscar cliente (NIT o Nombre)...")
        self.ent_buscar_cli.grid(row=0, column=0, padx=10, pady=10)
        self.ent_buscar_cli.bind("<KeyRelease>", lambda e: self.controlador_busqueda(e, "cliente"))
        
        self.lbl_cliente_sel = ctk.CTkLabel(self.frame_cliente, text="👤 Cliente: No seleccionado", font=("Arial", 12, "italic"), text_color="gray")
        self.lbl_cliente_sel.grid(row=0, column=1, padx=10)

        ctk.CTkLabel(self.frame_cliente, text="Pago:").grid(row=0, column=2, padx=2)
        self.combo_pago = ctk.CTkComboBox(self.frame_cliente, values=["Crédito", "Contado"], width=100)
        self.combo_pago.set("Crédito")
        self.combo_pago.grid(row=0, column=3, padx=5)

        ctk.CTkLabel(self.frame_cliente, text="Plazo (días):").grid(row=0, column=4, padx=2)
        self.ent_plazo = ctk.CTkEntry(self.frame_cliente, width=50)
        self.ent_plazo.insert(0, "0")
        self.ent_plazo.grid(row=0, column=5, padx=5)

        # Fila 2: Fecha y Descuento General
        self.frame_meta = ctk.CTkFrame(self.frame_cliente, fg_color="transparent")
        self.frame_meta.grid(row=1, column=0, columnspan=6, sticky="w", padx=10, pady=(0, 10))

        ctk.CTkLabel(self.frame_meta, text="Fecha:").pack(side="left", padx=5)
        self.ent_fecha = ctk.CTkEntry(self.frame_meta, width=110)
        self.ent_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_fecha.pack(side="left", padx=5)

        ctk.CTkLabel(self.frame_meta, text="% Descuento Global:").pack(side="left", padx=(20, 5))
        self.ent_desc_manual = ctk.CTkEntry(self.frame_meta, width=60)
        self.ent_desc_manual.insert(0, "0")
        self.ent_desc_manual.pack(side="left", padx=5)
        self.ent_desc_manual.bind("<KeyRelease>", lambda e: self.actualizar_totales())

        # --- SECCIÓN MEDIA: BÚSQUEDA DE PRODUCTOS ---
        self.frame_prod = ctk.CTkFrame(self)
        self.frame_prod.pack(padx=20, pady=10, fill="x")

        self.ent_buscar_prod = ctk.CTkEntry(self.frame_prod, width=350, placeholder_text="🧸 Buscar peluche por nombre o código...")
        self.ent_buscar_prod.grid(row=0, column=0, padx=10, pady=10)
        self.ent_buscar_prod.bind("<KeyRelease>", lambda e: self.controlador_busqueda(e, "producto"))
        
        self.ent_cant = ctk.CTkEntry(self.frame_prod, width=70, placeholder_text="Cant")
        self.ent_cant.grid(row=0, column=1, padx=5)
        
        ctk.CTkButton(self.frame_prod, text="➕ Añadir", fg_color="#28a745", hover_color="#218838", 
                      width=100, command=self.agregar_al_carrito).grid(row=0, column=2, padx=10)
        
        self.lbl_stock_disp = ctk.CTkLabel(self.frame_prod, text="Stock: -", font=("Arial", 11, "bold"))
        self.lbl_stock_disp.grid(row=0, column=3, padx=5)

        # --- TABLA DE PRODUCTOS (CARRITO) ---
        self.frame_tabla = ctk.CTkFrame(self)
        self.frame_tabla.pack(padx=20, pady=5, fill="both", expand=True)
        
        cols = ("ref", "desc", "cant", "val_uni", "total")
        self.tabla = ttk.Treeview(self.frame_tabla, columns=cols, show="headings")
        
        self.tabla.heading("ref", text="REF")
        self.tabla.heading("desc", text="DESCRIPCIÓN")
        self.tabla.heading("cant", text="CANT")
        self.tabla.heading("val_uni", text="VAL. UNI")
        self.tabla.heading("total", text="TOTAL")
        
        self.tabla.column("ref", width=100, anchor="center")
        self.tabla.column("desc", width=300, anchor="w")
        self.tabla.column("cant", width=80, anchor="center")
        self.tabla.column("val_uni", width=120, anchor="e")
        self.tabla.column("total", width=120, anchor="e")
        
        self.tabla.pack(side="left", fill="both", expand=True)

        # Botones laterales de la tabla
        self.frame_acciones = ctk.CTkFrame(self.frame_tabla, fg_color="transparent")
        self.frame_acciones.pack(side="right", fill="y", padx=5)
        ctk.CTkButton(self.frame_acciones, text="✏️", width=40, fg_color="#ffc107", text_color="black", command=self.editar_item).pack(pady=5)
        ctk.CTkButton(self.frame_acciones, text="🗑️", width=40, fg_color="#dc3545", command=self.eliminar_item).pack(pady=5)

        # --- FOOTER: TOTALES Y GUARDADO ---
        self.frame_footer = ctk.CTkFrame(self, fg_color="#2b2b2b", height=60)
        self.frame_footer.pack(fill="x", padx=20, pady=15)
        
        self.btn_save = ctk.CTkButton(self.frame_footer, text="💾 GUARDAR REMISIÓN", 
                                      font=("Arial", 14, "bold"), height=45, command=self.procesar_remision)
        self.btn_save.pack(side="left", padx=15)
        
        self.lbl_resumen = ctk.CTkLabel(self.frame_footer, text="TOTAL: $0", font=("Arial", 18, "bold"), text_color="#2ecc71")
        self.lbl_resumen.pack(side="right", padx=20)

    # --- LÓGICA DE FORMATO ---
    def f_moneda(self, valor):
        """Formatea números a pesos colombianos: $15.000"""
        return f"${float(valor):,.0f}".replace(",", ".")

    # --- LÓGICA DE EDICIÓN (EL QUE FALTABA) ---
    def cargar_remision_para_edicion(self, maestra, carrito_db):
        """Prepara la interfaz con los datos de una remisión guardada para editarla"""
        self.limpiar_pantalla()
        
        self.id_edicion = maestra['id_remision']
        self.cliente_actual = {
            'nit': maestra['nit_cliente'], 
            'razon_social': maestra['razon_social'], 
            'descuento_predeterminado': maestra['descuento_predeterminado']
        }
        
        # Llenar campos
        self.ent_buscar_cli.insert(0, maestra['razon_social'])
        self.lbl_cliente_sel.configure(text=f"NIT: {maestra['nit_cliente']}", text_color="white")
        self.combo_pago.set(maestra['forma_pago'])
        self.ent_plazo.delete(0, 'end'); self.ent_plazo.insert(0, maestra['plazo_dias'])
        self.ent_fecha.delete(0, 'end'); self.ent_fecha.insert(0, str(maestra['fecha_compra']))
        
        # Calcular porcentaje de descuento original
        if maestra['subtotal'] > 0:
            porc = (maestra['descuento'] / maestra['subtotal']) * 100
            self.ent_desc_manual.delete(0, 'end'); self.ent_desc_manual.insert(0, f"{porc:.1f}")

        # Cargar productos
        self.carrito = []
        for item in carrito_db:
            self.carrito.append({
                'id_producto': item['id_producto'], 
                'nombre': item['nombre'],
                'cantidad': item['cantidad'], 
                'precio_unitario': float(item['precio_unitario']),
                'subtotal_linea': float(item['subtotal_linea'])
            })
        
        self.actualizar_tabla_carrito()

    # --- MÉTODOS DE TABLA ---
    def actualizar_tabla_carrito(self):
        for i in self.tabla.get_children(): self.tabla.delete(i)
        
        for p in self.carrito:
            self.tabla.insert("", "end", values=(
                p['id_producto'], 
                p['nombre'], 
                p['cantidad'], 
                self.f_moneda(p['precio_unitario']), 
                self.f_moneda(p['subtotal_linea'])
            ))
        self.actualizar_totales()

    def actualizar_totales(self):
        try:
            sub = sum(p['subtotal_linea'] for p in self.carrito)
            d_txt = self.ent_desc_manual.get()
            porc_desc = float(d_txt) if d_txt else 0.0
            val_desc = sub * (porc_desc / 100)
            total = sub - val_desc
            
            self.lbl_resumen.configure(text=f"SUBTOTAL: {self.f_moneda(sub)} | DESC: {self.f_moneda(val_desc)} | TOTAL: {self.f_moneda(total)}")
            self.totales = {"subtotal": sub, "descuento": val_desc, "total": total}
        except: pass

    # --- ACCIONES ---
    def agregar_al_carrito(self):
        if not self.cliente_actual:
            messagebox.showwarning("Atención", "Seleccione un cliente primero.")
            return
        if not self.producto_actual:
            messagebox.showwarning("Atención", "Seleccione un producto.")
            return
            
        cant_txt = self.ent_cant.get()
        if not cant_txt.isdigit() or int(cant_txt) <= 0:
            messagebox.showerror("Error", "Ingrese una cantidad válida.")
            return
        
        cantidad = int(cant_txt)
        
        # Validar Stock
        if cantidad > self.producto_actual['stock']:
            if not messagebox.askyesno("Stock Insuficiente", f"Solo hay {self.producto_actual['stock']} disponibles. ¿Desea agregar de todos modos?"):
                return

        # Si el producto ya existe en el carrito, sumamos cantidad
        for p in self.carrito:
            if p['id_producto'] == self.producto_actual['id_producto']:
                p['cantidad'] += cantidad
                p['subtotal_linea'] = p['cantidad'] * p['precio_unitario']
                self.actualizar_tabla_carrito()
                self.limpiar_busqueda_prod()
                return

        # Si es nuevo
        self.carrito.append({
            "id_producto": self.producto_actual['id_producto'], 
            "nombre": self.producto_actual['nombre'],
            "cantidad": cantidad, 
            "precio_unitario": float(self.producto_actual['precio']),
            "subtotal_linea": cantidad * float(self.producto_actual['precio'])
        })
        self.actualizar_tabla_carrito()
        self.limpiar_busqueda_prod()

    def procesar_remision(self):
        if not self.carrito or not self.cliente_actual: 
            messagebox.showwarning("Atención", "Faltan datos (Cliente o Productos).")
            return
            
        if messagebox.askyesno("Confirmar", "¿Desea guardar esta remisión?"):
            exito, res = guardar_remision_bd(
                self.cliente_actual['nit'], self.carrito, self.combo_pago.get(),
                self.ent_plazo.get(), self.totales['subtotal'], 
                self.totales['descuento'], self.totales['total'], "", 
                self.id_edicion, self.ent_fecha.get()
            )
            if exito:
                messagebox.showinfo("Éxito", f"Remisión #{res} generada correctamente.")
                self.limpiar_pantalla()
            else:
                messagebox.showerror("Error", f"No se pudo guardar: {res}")

    # --- BUSCADORES ---
    def controlador_busqueda(self, event, tipo):
        widget = event.widget
        texto = widget.get().strip()
        if len(texto) < 2: 
            self.cerrar_sugerencias()
            return
        
        datos = buscar_cliente_remision(texto) if tipo == "cliente" else buscar_producto_remision(texto)
        self.mostrar_menu_flotante(widget, datos, self.seleccionar_cliente if tipo == "cliente" else self.seleccionar_producto, tipo)

    def mostrar_menu_flotante(self, widget, datos, callback, tipo):
        self.cerrar_sugerencias()
        if not datos: return
        
        self.ventana_sugerencias = ctk.CTkToplevel(self)
        self.ventana_sugerencias.overrideredirect(True)
        self.ventana_sugerencias.attributes("-topmost", True)
        
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height()
        self.ventana_sugerencias.geometry(f"{widget.winfo_width()}x180+{x}+{y}")
        
        frame = ctk.CTkScrollableFrame(self.ventana_sugerencias, corner_radius=0, fg_color="#333333")
        frame.pack(fill="both", expand=True)
        
        for i in datos:
            nombre = i['razon_social'] if tipo == "cliente" else f"{i['nombre']} ({self.f_moneda(i['precio'])})"
            ctk.CTkButton(frame, text=nombre, fg_color="transparent", anchor="w", 
                          hover_color="#1f538d", command=lambda x=i: callback(x)).pack(fill="x")

    def seleccionar_cliente(self, c):
        self.cliente_actual = c
        self.ent_buscar_cli.delete(0, 'end'); self.ent_buscar_cli.insert(0, c['razon_social'])
        self.lbl_cliente_sel.configure(text=f"👤 Cliente: {c['razon_social']} (NIT: {c['nit']})", text_color="#3498db")
        self.ent_desc_manual.delete(0, 'end'); self.ent_desc_manual.insert(0, str(c['descuento_predeterminado']))
        self.cerrar_sugerencias()
        self.actualizar_totales()

    def seleccionar_producto(self, p):
        self.producto_actual = p
        self.ent_buscar_prod.delete(0, 'end'); self.ent_buscar_prod.insert(0, p['nombre'])
        self.lbl_stock_disp.configure(text=f"Stock: {p['stock']}", text_color="#e67e22" if p['stock'] < 10 else "white")
        self.cerrar_sugerencias()
        self.ent_cant.focus()

    def cerrar_sugerencias(self):
        if self.ventana_sugerencias:
            self.ventana_sugerencias.destroy()
            self.ventana_sugerencias = None

    # --- AUXILIARES ---
    def editar_item(self):
        sel = self.tabla.selection()
        if not sel: return
        ref = self.tabla.item(sel[0], "values")[0]
        for p in self.carrito:
            if str(p['id_producto']) == str(ref):
                nueva = ctk.CTkInputDialog(text=f"Nueva cantidad para {p['nombre']}:", title="Editar").get_input()
                if nueva and nueva.isdigit():
                    p['cantidad'] = int(nueva)
                    p['subtotal_linea'] = p['cantidad'] * p['precio_unitario']
                    self.actualizar_tabla_carrito()
                break

    def eliminar_item(self):
        sel = self.tabla.selection()
        if not sel: return
        ref = self.tabla.item(sel[0], "values")[0]
        self.carrito = [p for p in self.carrito if str(p['id_producto']) != str(ref)]
        self.actualizar_tabla_carrito()

    def limpiar_busqueda_prod(self):
        self.ent_buscar_prod.delete(0, 'end')
        self.ent_cant.delete(0, 'end')
        self.lbl_stock_disp.configure(text="Stock: -")
        self.producto_actual = None

    def limpiar_pantalla(self):
        self.carrito = []; self.id_edicion = None; self.cliente_actual = None; self.producto_actual = None
        for i in self.tabla.get_children(): self.tabla.delete(i)
        self.ent_buscar_cli.delete(0, 'end'); self.ent_buscar_prod.delete(0, 'end')
        self.ent_fecha.delete(0, 'end'); self.ent_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_desc_manual.delete(0, 'end'); self.ent_desc_manual.insert(0, "0")
        self.ent_plazo.delete(0, 'end'); self.ent_plazo.insert(0, "0")
        self.lbl_resumen.configure(text="TOTAL: $0")
        self.lbl_cliente_sel.configure(text="👤 Cliente: No seleccionado", text_color="gray")