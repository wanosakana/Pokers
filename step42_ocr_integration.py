# step42_ocr_integration.py
import cv2
import numpy as np
from PIL import Image
import pytesseract

class OCRCardRecognizer:
    """画面からカードとチップ額を認識"""
    
    def __init__(self):
        self.card_templates = self._load_card_templates()
        self.digit
