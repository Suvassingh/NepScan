
import io
from pypdf import PdfReader, PdfWriter

def compress_pdf(pdf_bytes: bytes, quality: str = 'medium') -> bytes:

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)


    writer.compress_content_streams = True

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()