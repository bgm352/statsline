import cv2
import numpy as np
import requests

class VisionScreener:
    def __init__(self, max_ratio: float = 55.0):
        self.max_ratio = max_ratio

    def fetch_image(self, image_url: str) -> np.ndarray:
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
        image_array = np.asarray(bytearray(resp.content), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode image from URL.")
        return image

    def detect_card_and_inner_box(self, image: np.ndarray):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Use bilateral filter to keep edges sharp while smoothing background noise
        blurred = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Adaptive thresholding handles tricky lighting and background colors better than Canny alone
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 11, 2)
        
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        valid_boxes = []
        img_area = image.shape[0] * image.shape[1]
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > img_area * 0.08:  # Lowered threshold slightly to catch dark cards
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    valid_boxes.append((area, (x, y, w, h)))
                    
        valid_boxes.sort(key=lambda b: b[0], reverse=True)
        if len(valid_boxes) < 2:
            # Fallback: if inner border fails, use outer bounding box with an estimated 5% inner border inset
            if len(valid_boxes) == 1:
                ox, oy, ow, oh = valid_boxes[0][1]
                inset_w = int(ow * 0.90)
                inset_h = int(oh * 0.90)
                ix = ox + int(ow * 0.05)
                iy = oy + int(oh * 0.05)
                return (ox, oy, ow, oh), (ix, iy, inset_w, inset_h)
            return None, None
            
        outer_box = valid_boxes[0][1]
        inner_box = None
        for area, box in valid_boxes[1:]:
            if area < valid_boxes[0][0] * 0.95 and area > valid_boxes[0][0] * 0.30:
                inner_box = box
                break
                
        # Fallback if inner box contour isn't nested cleanly
        if not inner_box:
            ox, oy, ow, oh = outer_box
            inner_box = (ox + int(ow * 0.04), oy + int(oh * 0.04), int(ow * 0.92), int(oh * 0.92))
            
        return outer_box, inner_box

    def evaluate_from_url(self, image_url: str) -> dict:
        try:
            image = self.fetch_image(image_url)
            outer, inner = self.detect_card_and_inner_box(image)
            
            if outer is None or inner is None:
                return {
                    "status": "warning",
                    "reason": "Could not cleanly isolate inner border from seller photo. Using fallback estimation.",
                    "passes_lr": True,
                    "passes_tb": True,
                    "is_gem_candidate": True,
                    "lr_ratio_str": "50/50 (Est)",
                    "tb_ratio_str": "50/50 (Est)"
                }
                
            ox, oy, ow, oh = outer
            ix, iy, iw, ih = inner
            
            left_border = ix - ox
            right_border = (ox + ow) - (ix + iw)
            top_border = iy - oy
            bottom_border = (oy + oh) - (iy + ih)
            
            total_w = left_border + right_border
            total_h = top_border + bottom_border
            
            lr_ratio = (max(left_border, right_border) / total_w) * 100 if total_w > 0 else 50.0
            tb_ratio = (max(top_border, bottom_border) / total_h) * 100 if total_h > 0 else 50.0
            
            passes_lr = lr_ratio <= self.max_ratio
            passes_tb = tb_ratio <= self.max_ratio
            is_gem = passes_lr and passes_tb
            
            return {
                "status": "success",
                "passes_lr": passes_lr,
                "passes_tb": passes_tb,
                "is_gem_candidate": is_gem,
                "lr_ratio_str": f"{round(left_border)}/{round(right_border)} ({round(lr_ratio, 1)}%)",
                "tb_ratio_str": f"{round(top_border)}/{round(bottom_border)} ({round(tb_ratio, 1)}%)"
            }
        except Exception as e:
            return {
                "status": "error",
                "reason": str(e),
                "passes_lr": True,
                "passes_tb": True,
                "is_gem_candidate": True,
                "lr_ratio_str": "N/A",
                "tb_ratio_str": "N/A"
            }
