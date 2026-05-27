import os
import datetime
from reportlab.lib.pagesizes import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Tamaño Media Carta
MEDIA_CARTA = (5.5 * inch, 8.5 * inch)

# --- CONFIGURACIÓN ESTÉTICA ---
AZUL_MARCA = colors.HexColor("#0471B1")
AZUL_CLARO = colors.HexColor("#E8F9FF")
TEXTO_OSCURO = colors.HexColor("#2C3E50") 
LINEA_FINA = colors.HexColor("#DDE2E5")
ROJO_FOLIO = colors.HexColor("#E74C3C") # Rojo para el N° de Remisión

try:
    pdfmetrics.registerFont(TTFont('Roboto', os.path.join(os.getcwd(), 'fuentes', 'Roboto-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Roboto-Bold', os.path.join(os.getcwd(), 'fuentes', 'Roboto-Bold.ttf')))
    FONT_REG, FONT_BOLD = 'Roboto', 'Roboto-Bold'
except Exception:
    FONT_REG, FONT_BOLD = 'Helvetica', 'Helvetica-Bold'

def f_moneda(valor):
    try: return f"${float(valor):,.0f}".replace(",", ".")
    except: return "$0"

def marca_de_agua(canvas, doc):
    canvas.saveState()
    ruta_logo = os.path.join(os.getcwd(), "imagenes", "logo.png")
    if os.path.exists(ruta_logo):
        canvas.setFillAlpha(0.05) 
        canvas.drawImage(ruta_logo, (MEDIA_CARTA[0]/2) - 1.2*inch, (MEDIA_CARTA[1]/2) - 1.2*inch, width=2.4*inch, height=2.4*inch, mask='auto')
    canvas.restoreState()

def generar_pdf_remision(ruta_guardado, remision, productos):
    try:
        doc = SimpleDocTemplate(
            ruta_guardado,
            pagesize=MEDIA_CARTA,
            rightMargin=20, leftMargin=20, topMargin=15, bottomMargin=15
        )
        elementos = []

        # --- ESTILOS ---
        st_empresa_nombre = ParagraphStyle('EmpNombre', fontSize=12, fontName=FONT_BOLD, textColor=TEXTO_OSCURO, alignment=1)
        st_empresa_info = ParagraphStyle('EmpInfo', fontSize=7.5, fontName=FONT_REG, textColor=TEXTO_OSCURO, alignment=1, leading=9)
        
        st_datos = ParagraphStyle('Datos', fontSize=7, fontName=FONT_REG, textColor=TEXTO_OSCURO, leading=9)
        st_th = ParagraphStyle('Th', fontSize=6.5, fontName=FONT_BOLD, textColor=colors.white, alignment=1)
        
        # Estilos para el bloque de ID (RED Y CENTRADO)
        st_id_label = ParagraphStyle('IDLbl', fontSize=7, fontName=FONT_BOLD, textColor=TEXTO_OSCURO, alignment=1)
        st_id_num = ParagraphStyle('IDNum', fontSize=16, fontName=FONT_BOLD, textColor=ROJO_FOLIO, alignment=1)
        st_fecha_txt = ParagraphStyle('FechaTxt', fontSize=7, fontName=FONT_REG, alignment=1, textColor=TEXTO_OSCURO)

        # 1. ENCABEZADO
        ruta_logo = os.path.join(os.getcwd(), "imagenes", "logo.png")
        img_logo = Image(ruta_logo, width=0.8*inch, height=0.8*inch) if os.path.exists(ruta_logo) else Paragraph("", st_empresa_nombre)

        info_empresa = [
            [Paragraph("PELUCHES SALEM", st_empresa_nombre)],
            [Paragraph("📍 Bogotá – Colombia", st_empresa_info)],
            [Paragraph("✉ peluchesalem@gmail.com ", st_empresa_info)]
        ]
        tabla_centro = Table(info_empresa, colWidths=[2.8*inch])

        # Bloque ID y Fecha (Centrado y con etiquetas solicitadas)
        fecha_obj = remision.get('fecha_compra', datetime.date.today())
        f_str = fecha_obj.strftime('%d / %m / %Y') if isinstance(fecha_obj, (datetime.date, datetime.datetime)) else str(fecha_obj)
        
        info_id = [
            [Paragraph("N° REMISIÓN", st_id_label)],
            [Paragraph(f"{str(remision.get('id_remision', '000'))}", st_id_num)],
            [Spacer(1, 2)],
            [Paragraph("FECHA DE COMPRA", st_fecha_txt)],
            [Paragraph(f"{f_str}", st_id_label)] # Usamos st_id_label para que la fecha sea bold pero pequeña
        ]
        tabla_id = Table(info_id, colWidths=[1.1*inch])

        header = Table([[img_logo, tabla_centro, tabla_id]], colWidths=[1.0*inch, 2.8*inch, 1.1*inch])
        header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
        elementos.append(header)
        elementos.append(Spacer(1, 15))

        # 2. INFO DEL CLIENTE
        cliente_datos = [
            [Paragraph(f"<b>RAZÓN SOCIAL:</b> {remision.get('razon_social', 'N/A')}", st_datos),
             Paragraph(f"<b>NIT:</b> {remision.get('nit_cliente', 'N/A')}", st_datos),
             Paragraph(f"<b>TELÉFONO:</b> {remision.get('telefono', 'N/A')}", st_datos)],
            
            [Paragraph(f"<b>DIRECCIÓN:</b> {remision.get('direccion', 'N/A')}", st_datos),
             Paragraph("", st_datos),
             Paragraph(f"<b>FORMA PAGO:</b> {remision.get('forma_pago', 'CONTADO')}", st_datos)],
            
            [Paragraph(f"<b>CIUDAD:</b> {remision.get('ciudad', 'BOGOTÁ, D.C.')}", st_datos),
             Paragraph(f"<b>DEPARTAMENTO:</b> {remision.get('departamento', 'N/A')}", st_datos),
             Paragraph(f"<b>PLAZO:</b> {remision.get('plazo_pago_dias', '0')} días", st_datos)],
            
            [Paragraph(f"<b>REP. LEGAL:</b> {remision.get('representante_legal', 'N/A')}", st_datos),
             Paragraph(f"<b>DOCUMENTO RP:</b> {remision.get('documento_rp', 'N/A')}", st_datos),
             Paragraph("", st_datos)]
        ]
        
        tabla_cliente = Table(cliente_datos, colWidths=[1.8*inch, 1.6*inch, 1.5*inch])
        tabla_cliente.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 0.25, LINEA_FINA),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        elementos.append(tabla_cliente)
        elementos.append(Spacer(1, 15))

        # 3. TABLA DE PRODUCTOS
        encabezado_tabla = [
            Paragraph("REFERENCIA", st_th),
            Paragraph("DESCRIPCIÓN DEL PRODUCTO", st_th),
            Paragraph("CANTIDAD", st_th),
            Paragraph("VALOR UNITARIO", st_th),
            Paragraph("TOTAL", st_th)
        ]
        datos_p = [encabezado_tabla]
        
        for p in productos:
            datos_p.append([
                Paragraph(str(p.get('id_producto', '')), ParagraphStyle('Td_c', fontSize=7, fontName=FONT_REG, alignment=1)),
                Paragraph(p.get('nombre', '')[:45], ParagraphStyle('Td', fontSize=7, fontName=FONT_REG)),
                Paragraph(str(p.get('cantidad', 0)), ParagraphStyle('Td_c', fontSize=7, fontName=FONT_REG, alignment=1)),
                Paragraph(f_moneda(p.get('precio_unitario', 0)), ParagraphStyle('Td_r', fontSize=7, fontName=FONT_REG, alignment=2)),
                Paragraph(f_moneda(p.get('subtotal_linea', 0)), ParagraphStyle('Td_r', fontSize=7, fontName=FONT_REG, alignment=2))
            ])

        tabla_prod = Table(datos_p, colWidths=[0.75*inch, 1.85*inch, 0.75*inch, 0.75*inch, 0.8*inch])
        
        estilo_tabla_prod = [
            ('BACKGROUND', (0,0), (-1,0), AZUL_MARCA),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINEBELOW', (0,0), (-1,-1), 0.25, LINEA_FINA),
            ('TOPPADDING', (0,1), (-1,-1), 1.5),
            ('BOTTOMPADDING', (0,1), (-1,-1), 1.5),
        ]
        for i in range(1, len(datos_p)):
            if i % 2 == 0: estilo_tabla_prod.append(('BACKGROUND', (0, i), (-1, i), AZUL_CLARO))
                
        tabla_prod.setStyle(TableStyle(estilo_tabla_prod))
        elementos.append(tabla_prod)
        elementos.append(Spacer(1, 15))

        # 4. TOTALES
        total_final = float(remision.get('total', 0))
        descuento = float(remision.get('descuento', 0))
        sub = total_final + descuento
        
        # --- CÁLCULO INTELIGENTE DEL PORCENTAJE ---
        if sub > 0 and descuento > 0:
            porcentaje = round((descuento / sub) * 100, 1)
            porcentaje_str = int(porcentaje) if porcentaje.is_integer() else porcentaje
            label_descuento = f"<b>DESCUENTO ({porcentaje_str}%):</b>"
        else:
            label_descuento = "<b>DESCUENTO:</b>"
        # -------------------------------------------------
        
        datos_t = [
            [Paragraph("<b>SUB TOTAL:</b>", st_datos), Paragraph(f_moneda(sub), ParagraphStyle('Tr', alignment=2, fontSize=7))],
            [Paragraph(label_descuento, st_datos), Paragraph(f_moneda(descuento), ParagraphStyle('Tr', alignment=2, fontSize=7))],
            [Paragraph("<b>TOTAL A PAGAR:</b>", ParagraphStyle('Tb', fontSize=8, fontName=FONT_BOLD)), 
             Paragraph(f_moneda(total_final), ParagraphStyle('TrB', alignment=2, fontName=FONT_BOLD, fontSize=11, textColor=TEXTO_OSCURO))]
        ]
        
        tabla_totales = Table(datos_t, colWidths=[1.1*inch, 1.0*inch])
        tabla_totales.setStyle(TableStyle([
            ('LINEABOVE', (0,2), (-1,2), 1, TEXTO_OSCURO),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
        ]))

        nota = Paragraph("<b>Peluches Salem</b> • Magia en cada detalle.<br/>Soporte de entrega de mercancía.", 
                         ParagraphStyle('Nota', fontSize=6.5, fontName=FONT_REG, textColor=colors.gray))
        
        footer_final = Table([[nota, tabla_totales]], colWidths=[2.8*inch, 2.1*inch])
        footer_final.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        elementos.append(footer_final)

        doc.build(elementos, onFirstPage=marca_de_agua, onLaterPages=marca_de_agua)
        return True, "PDF generado con éxito"

    except Exception as e:
        return False, f"Error: {str(e)}"