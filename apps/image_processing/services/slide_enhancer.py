import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def enhance_slide_image(image_bytes: bytes) -> bytes:
 
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return image_bytes
        
        # 1. Apply perspective correction
        img = _correct_perspective(img)
        
        # 2. Enhance contrast using CLAHE
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 3. Sharpening
        kernel = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]])
        img = cv2.filter2D(img, -1, kernel)
        
        # 4. Remove shadows (if whiteboard)
        img = _remove_shadows(img)
        
        # 5. Increase brightness slightly
        img = cv2.convertScaleAbs(img, alpha=1.1, beta=10)
        
        # 6. Convert to JPEG
        _, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        return jpeg.tobytes()
        
    except Exception as e:
        logger.exception(f"Failed to enhance slide: {e}")
        return image_bytes


def _correct_perspective(img):
 
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            pts = approx.reshape(4, 2).astype(np.float32)
            rect = order_points(pts)
            width_top = np.linalg.norm(rect[1] - rect[0])
            width_bottom = np.linalg.norm(rect[2] - rect[3])
            max_width = max(int(width_top), int(width_bottom))
            height_left = np.linalg.norm(rect[3] - rect[0])
            height_right = np.linalg.norm(rect[2] - rect[1])
            max_height = max(int(height_left), int(height_right))
            
            if max_width > 50 and max_height > 50:
                dst = np.array([
                    [0, 0],
                    [max_width - 1, 0],
                    [max_width - 1, max_height - 1],
                    [0, max_height - 1]
                ], dtype=np.float32)
                M = cv2.getPerspectiveTransform(rect, dst)
                return cv2.warpPerspective(img, M, (max_width, max_height))
    
    return img


def _remove_shadows(img):
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply median blur to remove noise
    blur = cv2.medianBlur(gray, 5)
    
    # Detect shadows using morphological operations
    kernel = np.ones((21, 21), np.uint8)
    background = cv2.morphologyEx(blur, cv2.MORPH_OPEN, kernel)
    
    # Normalize
    normalized = cv2.divide(blur, background, scale=255)
    
    # Convert back to color
    result = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)
    
    # Blend with original
    return cv2.addWeighted(img, 0.6, result, 0.4, 0)


def order_points(pts):
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect