# PROJECT_MAP — OCR Sécurisé
## [TECH_STACK]
| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11.9 |
| OCR Engine | Tesseract | 5.4.0 |
| OCR Binding | pytesseract | 0.3.13 |
| Web Framework | FastAPI | 0.139.2 |
| ASGI Server | uvicorn | 0.51.0 |
| Image Processing | Pillow | 12.3.0 |
| File Upload | python-multipart | 0.0.32 |
| Templating | Jinja2 | 3.1.6 |
| PII Detection | regex (native) | — |
| OS | Windows | — |

## [SYSTEM_FLOW]
```
[Upload Image] → [OCR Extraction] → [PII Detection] → [Masking] → [Display + Download]
     │                   │                    │              │
     ▼                   ▼                    ▼              ▼
  POST /upload      pytesseract         regex on         Pillow draw
  multipart/form    image_to_data()     text+bboxes      + str.replace
```

### PII Detection Patterns
| Type | Pattern |
|------|---------|
| CIN | `\b\d{8,12}\b` + label triggers (`cin:`, `n°cin`) |
| PHONE | `\b0[1-9](?:\s?\d{2}){4}\b` |
| EMAIL | `\b[\w.+-]+@[\w-]+\.[\w.]+\b` |
| DATE | `\b\d{1,2}[\s/\\-]\d{1,2}[\s/\\-]\d{2,4}\b` |
| ZIP_CODE | `\b\d{5}\b` |
| NOM | label triggers (`nom:`, `prénom:`) → next 2 words |
| ADRESSE | keyword heuristics (`rue`, `avenue`, `N°`, ...) |

## [ARCHITECTURE]
```
ocr-securise/
├── main.py                  # FastAPI app, routes, uvicorn entry (94 lines)
├── core/
│   ├── __init__.py          # empty
│   ├── ocr.py               # OCR: image → text + bounding boxes
│   ├── detector.py          # PII detection: regex → matched regions
│   └── masker.py            # Masking: image blackout + text redaction
├── templates/
│   └── index.html           # Upload form + result display
├── uploads/                 # Temp uploaded files (gitignored)
├── output/                  # Generated masked files (gitignored)
├── integration_test.py      # Self-verification tests (10 test cases)
├── requirements.txt
├── .gitignore
└── PROJECT_MAP.md
```

**Total: 5 source files + 1 template ≈ 260 lines of code**

## [ORPHANS & PENDING]
*(empty — all features complete)*

## [VERIFICATION RESULTS]
All 10 integration tests PASS:
1. Realistic ID card — 8 PII fields detected and masked
2. Public document — 0 false positives on clean text
3. Unsupported file type — correctly rejected
4. Output files — masked PNG + TXT generated
5. End-to-end web upload — 200 OK with masked result
