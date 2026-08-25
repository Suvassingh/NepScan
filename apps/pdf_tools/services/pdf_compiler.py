from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io
from PIL import Image

def merge_images_to_pdf(image_bytes_list: list[bytes]) -> bytes:
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    width, height = letter
    for img_bytes in image_bytes_list:
        img = Image.open(io.BytesIO(img_bytes))
        img_reader = ImageReader(img)
        img_w, img_h = img.size
        scale = min(width / img_w, height / img_h)
        new_w = img_w * scale
        new_h = img_h * scale
        x = (width - new_w) / 2
        y = (height - new_h) / 2
        c.drawImage(img_reader, x, y, new_w, new_h)
        c.showPage()
    c.save()
    packet.seek(0)
    return packet.read()