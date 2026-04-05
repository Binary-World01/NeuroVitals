"""
OCR Helper — Extract text from prescription images using PaddleOCR.
Migrated from neurofit_risk_engine14/ocr_helper.py
"""
import numpy as np
from PIL import Image
import io

# Lazy-load PaddleOCR to avoid slow startup if not needed
_ocr_instance = None

def _get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            _ocr_instance = PaddleOCR(use_angle_cls=True, lang='en')
        except ImportError:
            print("[WARN] PaddleOCR not installed. OCR features will be disabled.")
            return None
    return _ocr_instance


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from prescription image using PaddleOCR (offline, free).
    Returns extracted text or empty string if failed.
    """
    ocr = _get_ocr()
    if ocr is None:
        return ""

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)

        result = ocr.ocr(image_np, cls=True)

        text_lines = []
        if result and result[0]:
            for line in result[0]:
                text_lines.append(line[1][0])
        text = ' '.join(text_lines)
        return text.strip()

    except Exception as e:
        print(f"PaddleOCR error: {e}")
        return ""
