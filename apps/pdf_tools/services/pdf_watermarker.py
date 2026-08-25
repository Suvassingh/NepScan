
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

def create_watermark_pdf(watermark_text: str) -> bytes:
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    c.setFont("Helvetica", 50)
    c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)  
    c.saveState()
    c.translate(300, 400)  
    c.rotate(45)
    c.drawString(0, 0, watermark_text)
    c.restoreState()
    c.save()
    packet.seek(0)
    return packet.read()

def add_watermark(pdf_bytes: bytes, text: str) -> bytes:
    watermark_pdf = PdfReader(io.BytesIO(create_watermark_pdf(text)))
    watermark_page = watermark_pdf.pages[0]

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        # Merge watermark onto page
        page.merge_page(watermark_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()