import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def detect_and_correct_perspective(image_bytes: bytes) -> bytes | None:
 
    
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        logger.error("Failed to decode image")
        return None

    original = img.copy()
    height, width = img.shape[:2]

     
    max_dim = 800
    scale = max_dim / max(height, width)
    if scale < 1:
        new_w = int(width * scale)
        new_h = int(height * scale)
        img_resized = cv2.resize(img, (new_w, new_h))
    else:
        img_resized = img.copy()

     
    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)

     
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

     
    edged = cv2.Canny(blurred, 50, 150)

     
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

     
    image_area = new_w * new_h
    doc_contour = None

    for cnt in sorted(contours, key=cv2.contourArea, reverse=True):
        area = cv2.contourArea(cnt)
        if area < image_area * 0.05:   
            continue

         
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

         
        if len(approx) == 4:
            doc_contour = approx
            break

     
    if doc_contour is None:
        logger.info("No quadrilateral found, trying alternative method...")
         
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in sorted(contours, key=cv2.contourArea, reverse=True):
            area = cv2.contourArea(cnt)
            if area < image_area * 0.05:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                doc_contour = approx
                break

    
    if doc_contour is None:
        logger.info("No quadrilateral found, trying largest contour...")
         
        for cnt in sorted(contours, key=cv2.contourArea, reverse=True):
            area = cv2.contourArea(cnt)
            if area > image_area * 0.05:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                if len(approx) >= 4:
                    # Use the first 4 points
                    doc_contour = approx[:4]
                    break

     
    if doc_contour is None:
        logger.info("Trying morphological approach...")
         
        kernel = np.ones((5, 5), np.uint8)
        closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in sorted(contours, key=cv2.contourArea, reverse=True):
            area = cv2.contourArea(cnt)
            if area < image_area * 0.05:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) >= 4:
                doc_contour = approx[:4]
                break

    if doc_contour is None:
        logger.warning("No document edges found in the image")
        return None

     
    pts = doc_contour.reshape(4, 2).astype(np.float32)
    if scale < 1:
        pts = pts / scale

     
    rect = order_points(pts)

    
    (tl, tr, br, bl) = rect
    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)
    max_width = max(int(width_top), int(width_bottom))

    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)
    max_height = max(int(height_left), int(height_right))

     
    if max_width < 50 or max_height < 50:
        logger.warning("Detected document is too small")
        return None

     
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype=np.float32)

     
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (max_width, max_height))

     
    _, jpeg = cv2.imencode('.jpg', warped, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return jpeg.tobytes()


def order_points(pts):
     
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # TL
    rect[2] = pts[np.argmax(s)]   # BR
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # TR
    rect[3] = pts[np.argmax(diff)]  # BL
    return rect