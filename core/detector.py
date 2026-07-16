import logging
import re
from typing import Dict, List, Tuple

from core.ocr import WordBox

logger = logging.getLogger(__name__)

PATTERNS: Dict[str, re.Pattern] = {
    "CIN": re.compile(r"\b\d{1,2}\s?\d{7,10}\b"),
    "PHONE": re.compile(r"\b0[1-9](?:\s?\d{2}){4}\b"),
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
    "DATE": re.compile(r"\b\d{1,2}[\s/\\-]\d{1,2}[\s/\\-]\d{2,4}\b"),
    "ZIP_CODE": re.compile(r"\b\d{5}\b"),
}

LABEL_TRIGGERS: Dict[str, List[str]] = {
    "NOM": ["nom", "nom:", "nom :", "nom de famille"],
    "PRENOM": ["prénom", "prénom:", "prénom :", "prenom", "prenom:"],
    "CIN": ["cin", "cin:", "cin :", "n°cin", "n° cin", "n°carte", "carte identité"],
    "DATE_NAISS": ["né", "née", "né(e)", "né le", "née le", "date naissance", "date de naissance"],
    "ADRESSE": ["adresse", "domicile", "résidence", "habite"],
}

ADDRESS_KEYWORDS = [
    "rue", "avenue", "av.", "boulevard", "bd", "place", "impasse",
    "chemin", "route", "allée", "cours", "square", "passage",
    "n°", "numero", "numéro", "code postal", "f-", "appartement",
]


def _is_address_word(word: str) -> bool:
    return any(kw in word.lower() for kw in ADDRESS_KEYWORDS)


def detect_pii(text: str, boxes: List[WordBox]) -> List[Tuple[WordBox, str]]:
    results: List[Tuple[WordBox, str]] = []
    matched_indices: set = set()

    words_lower = [b[4].lower() for b in boxes]

    # Pass 1: pattern matching on individual words
    for i, box in enumerate(boxes):
        word = box[4]
        if i in matched_indices:
            continue
        for pii_type, pattern in PATTERNS.items():
            if pattern.fullmatch(word):
                results.append((box, pii_type))
                matched_indices.add(i)
                break

    # Pass 2: label-triggered capture (look right after labels)
    for i, box in enumerate(boxes):
        wl = words_lower[i]
        if i in matched_indices:
            continue
        for pii_type, triggers in LABEL_TRIGGERS.items():
            if wl in triggers:
                # capture next 1-3 non-masked words
                captured = 0
                for j in range(i + 1, min(i + 4, len(boxes))):
                    if j in matched_indices:
                        continue
                    bj = boxes[j]
                    # skip small words like prepositions
                    if len(bj[4]) <= 2 and bj[4].lower() in ("le", "la", "de", "du", "à", "au", "aux", "et", "l'"):
                        continue
                    results.append((bj, pii_type))
                    matched_indices.add(j)
                    captured += 1
                    if captured >= 2:
                        break
                matched_indices.add(i)
                break

    # Pass 3: address detection
    for i, box in enumerate(boxes):
        if i in matched_indices:
            continue
        if _is_address_word(box[4]):
            results.append((box, "ADRESSE"))
            matched_indices.add(i)
            for j in range(i + 1, min(i + 5, len(boxes))):
                if j in matched_indices:
                    continue
                bj = boxes[j]
                if bj[4][0].isupper() or bj[4].isdigit():
                    results.append((bj, "ADRESSE"))
                    matched_indices.add(j)
                else:
                    break

    logger.info("PII detection: found %d sensitive fields", len(results))
    return results
