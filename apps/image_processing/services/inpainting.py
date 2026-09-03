import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def erase_marks(
    image_bytes: bytes,
    mask_data: list,
    method: str = 'telea'
) -> bytes:
 
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return image_bytes
        
        # Create mask
        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        
        # Draw mask based on input data
        for region in mask_data:
            if region['type'] == 'point':
                # Draw circle around point
                x, y = region['x'], region['y']
                radius = region.get('radius', 20)
                cv2.circle(mask, (x, y), radius, 255, -1)
            elif region['type'] == 'rectangle':
                x1, y1 = region['x1'], region['y1']
                x2, y2 = region['x2'], region['y2']
                cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
            elif region['type'] == 'freehand':
                # Connect points
                points = region['points']
                if len(points) > 1:
                    for i in range(len(points) - 1):
                        cv2.line(
                            mask,
                            (points[i]['x'], points[i]['y']),
                            (points[i+1]['x'], points[i+1]['y']),
                            255,
                            region.get('strokeWidth', 20)
                        )
        
        # Apply inpainting
        if method == 'telea':
            result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
        else:
            result = cv2.inpaint(img, mask, 3, cv2.INPAINT_NS)
        
        # Save as JPEG
        _, jpeg = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 92])
        return jpeg.tobytes()
        
    except Exception as e:
        logger.exception(f"Failed to erase marks: {e}")
        return image_bytes


def smart_erase(
    image_bytes: bytes,
    selection: dict
) -> bytes:
 
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return image_bytes
        
        # Create mask from selection
        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        
        # Draw selection on mask
        if selection['type'] == 'rectangle':
            cv2.rectangle(
                mask,
                (selection['x1'], selection['y1']),
                (selection['x2'], selection['y2']),
                255, -1
            )
        elif selection['type'] == 'freehand':
            points = selection['points']
            if len(points) > 2:
                pts = np.array([[p['x'], p['y']] for p in points], np.int32)
                cv2.fillPoly(mask, [pts], 255)
        
        # Dilate mask slightly for better blending
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        # Use NS inpainting for better results
        result = cv2.inpaint(img, mask, 3, cv2.INPAINT_NS)
        
        _, jpeg = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 92])
        return jpeg.tobytes()
        
    except Exception as e:
        logger.exception(f"Failed to smart erase: {e}")
        return image_bytes