import io
import csv
import os
from pdf2docx import Converter
import pandas as pd
import tabula
from PIL import Image
import fitz   
def pdf_to_docx(pdf_bytes: bytes) -> bytes:
    input_stream = io.BytesIO(pdf_bytes)
    output_stream = io.BytesIO()
    cv = Converter(input_stream)
    cv.convert(output_stream, start=0, end=None)
    cv.close()
    output_stream.seek(0)
    return output_stream.read()

def pdf_to_xlsx(pdf_bytes: bytes) -> bytes:
    dfs = tabula.read_pdf(io.BytesIO(pdf_bytes), pages='all', multiple_tables=True)
    if not dfs:
        return b''
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for i, df in enumerate(dfs):
            df.to_excel(writer, sheet_name=f'Table_{i+1}', index=False)
    output.seek(0)
    return output.read()

def pdf_to_csv(pdf_bytes: bytes) -> bytes:
    dfs = tabula.read_pdf(io.BytesIO(pdf_bytes), pages='all', multiple_tables=True)
    if not dfs:
        return b''
    output = io.StringIO()
     
    for i, df in enumerate(dfs):
        if i > 0:
            output.write('\n\n')
        df.to_csv(output, index=False)
    return output.getvalue().encode('utf-8')

def pdf_to_txt(pdf_bytes: bytes) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text.encode('utf-8')

def pdf_to_jpg(pdf_bytes: bytes, dpi: int = 150) -> bytes:
    # Convert first page to JPG
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
    img_bytes = pix.tobytes("jpeg")
    return img_bytes
def pdf_to_png(pdf_bytes: bytes, dpi: int = 150) -> bytes:
     
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
    return pix.tobytes("png")

def pdf_to_webp(pdf_bytes: bytes, dpi: int = 150, quality: int = 80) -> bytes:
     
    from PIL import Image
    import io
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
     
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    output = io.BytesIO()
    img.save(output, format="WEBP", quality=quality)
    return output.getvalue()