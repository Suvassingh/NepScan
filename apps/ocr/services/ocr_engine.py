import tempfile
import os
import logging
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

def perform_ocr(image_bytes: bytes) -> tuple[str, str, float]:
 
    try:
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

         
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        
        img = Image.open(tmp_path)
        text = pytesseract.image_to_string(
            img,
            lang='nep+eng',
            config='--psm 6'   
        )
         
        confidence = 0.95 if len(text.strip()) > 10 else 0.5
         
        from .language_detector import detect_language
        lang = detect_language(text)
        return text.strip(), lang, confidence
    except pytesseract.TesseractNotFoundError:
        logger.warning("Tesseract not found. Using fallback dummy OCR.")
        return "Fallback OCR text (Tesseract not installed)", "unknown", 0.0
    except Exception as e:
        logger.exception("OCR failed")
        raise
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass