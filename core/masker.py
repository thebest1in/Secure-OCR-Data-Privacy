import logging
from pathlib import Path
from typing import List, Set, Tuple

from PIL import Image, ImageDraw

from core.detector import detect_pii
from core.ocr import WordBox, extract_text_and_boxes

logger = logging.getLogger(__name__)


def mask_image(image_path: str | Path, sensitive: List[Tuple[WordBox, str]]) -> Image.Image:
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    for box, _pii_type in sensitive:
        x, y, w, h = box[:4]
        # Expand slightly for safety margin
        draw.rectangle([x - 2, y - 2, x + w + 2, y + h + 2], fill="black")
    logger.info("Masked %d regions on image", len(sensitive))
    return img


def mask_text(boxes: List[WordBox], sensitive: List[Tuple[WordBox, str]]) -> str:
    masked_set: Set[int] = set(id(b) for b, _ in sensitive)
    parts: List[str] = []
    for box in boxes:
        if id(box) in masked_set:
            parts.append("[MASKED]")
        else:
            parts.append(box[4])
    return " ".join(parts)


def process_image(image_path: str | Path, lang: str = "fra+eng") -> dict:
    text, boxes = extract_text_and_boxes(image_path, lang=lang)
    sensitive = detect_pii(text, boxes)
    masked_img = mask_image(image_path, sensitive)
    masked_txt = mask_text(boxes, sensitive)
    return {
        "original_text": text,
        "masked_text": masked_txt,
        "masked_image": masked_img,
        "sensitive_count": len(sensitive),
    }
