 
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import io

def combine_id_images(front_bytes: bytes, back_bytes: bytes) -> bytes:
 
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
     
    front = Image.open(io.BytesIO(front_bytes))
    back = Image.open(io.BytesIO(back_bytes))
   
    half_w = width / 2
     
    front.thumbnail((half_w, height))
    back.thumbnail((half_w, height))
     
    c.drawImage(Image.open(io.BytesIO(front_bytes)), 0, 0, half_w, height)
    c.drawImage(Image.open(io.BytesIO(back_bytes)), half_w, 0, half_w, height)
    c.showPage()
    c.save()
    packet.seek(0)
    return packet.read()