import cv2
import numpy as np
from PIL import Image, ImageDraw
import io
import logging

logger = logging.getLogger(__name__)

 
PHOTO_SIZES = {
    'passport': (600, 600),       
    'visa': (600, 600),           
    'passport_eu': (708, 944),     
    'id_card': (492, 630),        
    'driving_license': (630, 788),  
}

def create_id_photo(
    image_bytes: bytes,
    size_type: str = 'passport',
    num_photos: int = 4,
    background_color: tuple = (255, 255, 255)
) -> bytes:
 
    try:
        # Load image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Could not decode image")
        
        # Detect face
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            raise ValueError("No face detected in image")
        
        # Use the largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        
        # Crop to face with margins
        margin = w * 0.5
        x1 = max(0, int(x - margin))
        y1 = max(0, int(y - margin))
        x2 = min(img.shape[1], int(x + w + margin))
        y2 = min(img.shape[0], int(y + h + margin))
        
        cropped = img[y1:y2, x1:x2]
        
        # Resize to target size
        target_size = PHOTO_SIZES.get(size_type, PHOTO_SIZES['passport'])
        resized = cv2.resize(cropped, target_size, interpolation=cv2.INTER_LANCZOS4)
        
        # Add white background if needed
        if background_color != (255, 255, 255):
            # Replace background (simplified)
            mask = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
            mask = cv2.bitwise_not(mask)
            bg = np.full(resized.shape, background_color, dtype=np.uint8)
            resized = np.where(mask[:, :, np.newaxis] == 0, bg, resized)
        
        # Create sheet with multiple photos
        sheet_size = _calculate_sheet_size(num_photos, target_size)
        sheet = Image.new('RGB', sheet_size, (255, 255, 255))
        draw = ImageDraw.Draw(sheet)
        
        # Place photos on sheet
        cols = 2 if num_photos <= 4 else 3
        rows = (num_photos + cols - 1) // cols
        
        photo_img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
        spacing = 20
        
        for i in range(num_photos):
            row = i // cols
            col = i % cols
            x = col * (target_size[0] + spacing) + spacing
            y = row * (target_size[1] + spacing) + spacing
            sheet.paste(photo_img, (x, y))
        
        # Add cut lines
        for i in range(1, cols):
            x = i * (target_size[0] + spacing) + spacing - 5
            draw.line([(x, 0), (x, sheet_size[1])], fill=(200, 200, 200), width=1)
        
        for i in range(1, rows):
            y = i * (target_size[1] + spacing) + spacing - 5
            draw.line([(0, y), (sheet_size[0], y)], fill=(200, 200, 200), width=1)
        
        # Save as JPEG
        output = io.BytesIO()
        sheet.save(output, format='JPEG', quality=92)
        return output.getvalue()
        
    except Exception as e:
        logger.exception(f"Failed to create ID photo: {e}")
        raise


def _calculate_sheet_size(num_photos: int, photo_size: tuple) -> tuple:
    cols = 2 if num_photos <= 4 else 3
    rows = (num_photos + cols - 1) // cols
    spacing = 20
    width = cols * (photo_size[0] + spacing) + spacing
    height = rows * (photo_size[1] + spacing) + spacing
    return (width, height)