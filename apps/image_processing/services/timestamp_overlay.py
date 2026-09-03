from PIL import Image, ImageDraw, ImageFont
import io
import datetime
import logging
import fitz  
logger = logging.getLogger(__name__)

def add_timestamp_to_image(
    image_bytes: bytes,
    format: str = "%Y-%m-%d %H:%M:%S",
    position: str = "bottom-right",
    font_size: int = 24,
    color: tuple = (255, 255, 255),
    background_opacity: int = 128
) -> bytes:
 
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # Get current timestamp
        timestamp = datetime.datetime.now().strftime(format)
        
        # Try to load a font, fallback to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), timestamp, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position
        padding = 20
        img_width, img_height = img.size
        
        if position == "top-left":
            x, y = padding, padding
        elif position == "top-right":
            x, y = img_width - text_width - padding, padding
        elif position == "bottom-left":
            x, y = padding, img_height - text_height - padding
        else:  # bottom-right (default)
            x, y = img_width - text_width - padding, img_height - text_height - padding
        
        # Draw semi-transparent background
        bg_x1 = x - 10
        bg_y1 = y - 8
        bg_x2 = x + text_width + 10
        bg_y2 = y + text_height + 8
        
        bg_color = (0, 0, 0, background_opacity)   
        draw.rectangle(
            [bg_x1, bg_y1, bg_x2, bg_y2],
            fill=(0, 0, 0, background_opacity)
        )
        
        # Draw text
        draw.text((x, y), timestamp, fill=color, font=font)
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=92)
        return output.getvalue()
        
    except Exception as e:
        logger.exception(f"Failed to add timestamp: {e}")
        return image_bytes   


def add_timestamp_to_pdf(
    pdf_bytes: bytes,
    format: str = "%Y-%m-%d %H:%M:%S",
) -> bytes:
 
 
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        timestamp = datetime.datetime.now().strftime(format)
        
        for page in doc:
            # Get page dimensions
            rect = page.rect
            # Add text at bottom-right
            page.insert_text(
                point=(rect.width - 150, rect.height - 30),
                text=timestamp,
                fontsize=10,
                color=(0, 0, 0),
                overlay=True
            )
        
        output = io.BytesIO()
        doc.save(output)
        doc.close()
        return output.getvalue()
        
    except Exception as e:
        logger.exception(f"Failed to add timestamp to PDF: {e}")
        return pdf_bytes   