from fastapi import FastAPI, File, UploadFile
import pymupdf
import re

app = FastAPI()

def limpiar_importe(importe_str):
    if not importe_str: return ""
    return importe_str.replace('*', '').replace(' ', '').replace('.', '').replace(',', '.').replace('-', '').strip()

@app.post("/procesar-pdf")
async def procesar_pdf(file: UploadFile = File(...)):
    try:
        # 1. Leer el PDF directamente desde la memoria
        contenido = await file.read()
        doc = pymupdf.open("pdf", contenido)
        texto = ""
        for pagina in doc:
            texto += pagina.get_text()
        
        # 2. Extracción Regex (Documento)
        doc_match = re.search(r'(?i)Documento(?: de pago)?\s+(\d{9,})', texto)
        documento = doc_match.group(1) if doc_match else "NO DETECTADO"
        
        # 3. Extracción Regex (Facturas y Descuentos)
        regex_linea = r'(\d{9,})\s+([A-Z0-9]+)\s+\d{2}\.\d{2}\.\d{4}\s+[\d\.,-]+\s+([\d\.,-]+)'
        lineas = re.findall(regex_linea, texto)
        
        factura = "SIN FACTURA"
        importe_factura = ""
        descuentos_str = "Revisar PDF manual"
        
        if lineas:
            primera_linea = lineas[0]
            factura = primera_linea[1]
            importe_factura = limpiar_importe(primera_linea[2])
            
            lista_descuentos = [f"{linea[1]}: {limpiar_importe(linea[2])}" for linea in lineas[1:]]
            descuentos_str = " | ".join(lista_descuentos) if lista_descuentos else ""

        # 4. Extracción Regex (Importe Pagado)
        todos_importes = re.findall(r'[\d\.,\*-]+', texto)
        importe_pagado = limpiar_importe(todos_importes[-1]) if todos_importes else ""

        # 5. Devolver los datos estructurados a Apps Script
        return {
            "exito": True,
            "documento": documento,
            "factura": factura,
            "importe_factura": importe_factura,
            "importe_pagado": importe_pagado,
            "descuentos": descuentos_str
        }

    except Exception as e:
        return {"exito": False, "error": str(e)}
