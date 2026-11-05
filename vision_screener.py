import cv2
import numpy as np
import requests

class VisionScreener:
    def __init__(self, max_ratio: float = 55.0):
        # PSA 10 front centering standard is typically 55/45 or better
        self.max_ratio = max_ratio

    def fetch_image(self, image_url: str) -> np.ndarray:
        """Downloads an image from a URL and converts it into an OpenCV BGR array."""
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
        image_array = np.asarray(bytearray(resp.content), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode image from URL.")
        return image

    def detect_card_and_inner_box(self, image: np.ndarray):
        """
        Detects the outer card boundary and the inner frame boundary.
        Returns bounding boxes (x, y, w, h) for both outer and inner contours.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Dilate edges slightly to close micro-gaps in borders
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and rectangularity
        valid_boxes = []
        img_area = image.shape[0] * image.shape[1]

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > img_area * 0.10:  # Ignore tiny noise contours
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                if len(approx) == 4:  # Look for rectangular shapes
                    x, y, w, h = cv2.boundingRect(approx)
                    valid_boxes.append((area, (x, y, w, h)))

        # Sort largest to smallest
        valid_boxes.sort(key=lambda b: b[0], reverse=True)

        if len(valid_boxes) < 2:
            return None, None

        # Largest valid rectangle is outer card edge; look for distinct inner frame
        outer_box = valid_boxes[0][1]
        inner_box = None

        for area, box in valid_boxes[1:]:
            # Ensure the inner box is meaningfully smaller than the outer edge (border thickness)
            if area < valid_boxes[0][0] * 0.92 and area > valid_boxes[0][0] * 0.40:
                inner_box = box
                break

        return outer_box, inner_box

    def calculate_centering(self, outer_box, inner_box) -> dict:
        """Calculates L/R and T/B border pixel widths and percentage ratios."""
        ox, oy, ow, oh = outer_box
        ix, iy, iw, ih = inner_box

        left_border = max(ix - ox, 1)
        right_border = max((ox + ow) - (ix + iw), 1)
        top_border = max(iy - oy, 1)
        bottom_border = max((oy + oh) - (iy + ih), 1)

        total_lr = left_border + right_border
        total_tb = top_border + bottom_border

        left_pct = round((left_border / total_lr) * 100, 1)
        right_pct = round((right_border / total_lr) * 100, 1)
        top_pct = round((top_border / total_tb) * 100, 1)
        bottom_pct = round((bottom_border / total_tb) * 100, 1)

        worst_lr = max(left_pct, right_pct)
        worst_tb = max(top_pct, bottom_pct)

        passes_lr = worst_lr <= self.max_ratio
        passes_tb = worst_tb <= self.max_ratio
        is_gem_candidate = passes_lr and passes_tb

        return {
            "left_pct": left_pct,
            "right_pct": right_pct,
            "top_pct": top_pct,
            "bottom_pct": bottom_pct,
            "lr_ratio_str": f"{left_pct}/{right_pct}",
            "tb_ratio_str": f"{top_pct}/{bottom_pct}",
            "passes_lr": passes_lr,
            "passes_tb": passes_tb,
            "is_gem_candidate": is_gem_candidate,
            "borders_px": {
                "left": left_border,
                "right": right_border,
                "top": top_border,
                "bottom": bottom_border
            }
        }

    def evaluate_from_url(self, image_url: str) -> dict:
        """End-to-end wrapper: fetches image, detects borders, and returns centering metrics."""
        try:
            image = self.fetch_image(image_url)
            outer_box, inner_box = self.detect_card_and_inner_box(image)

            if not outer_box or not inner_box:
                return {
                    "status": "manual_review_needed",
                    "reason": "Could not cleanly isolate inner border from seller photo.",
                    "is_gem_candidate": False
                }

            metrics = self.calculate_centering(outer_box, inner_box)
            metrics["status"] = "success"
            return metrics

        except Exception as e:
            return {
                "status": "error",
                "reason": str(e),
                "is_gem_candidate": False
            }
