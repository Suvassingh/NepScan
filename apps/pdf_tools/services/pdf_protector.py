
import io
from pypdf import PdfReader, PdfWriter

def add_password(pdf_bytes: bytes, password: str) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    
    writer.encrypt(
        user_password=password,
        owner_password=password,   
        
        use_128bit=True            
    )

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()