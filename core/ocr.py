import logging
import platform
from pathlib import Path
from typing import List, Tuple

import pytesseract
from PIL import Image

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

logger = logging.getLogger(__name__)

WordBox = Tuple[int, int, int, int, str]  # x, y, w, h, text


def extract_text_and_boxes(image_path: str | Path, lang: str = "fra") -> tuple[str, List[WordBox]]:
    img = Image.open(image_path)
    data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

    text_parts: List[str] = []
    boxes: List[WordBox] = []
    current_line = ""

    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        if not word:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        if w == 0 or h == 0:
            continue
        boxes.append((x, y, w, h, word))
        text_parts.append(word)

    full_text = " ".join(text_parts)
    logger.info("OCR extracted %d words from %s", len(boxes), image_path)
    return full_text, boxes
