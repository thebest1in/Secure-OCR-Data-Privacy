import logging
import uuid
from pathlib import Path

import aiofiles
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.masker import process_image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="OCR Sécurisé")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


@app.exception_handler(StarletteHTTPException)
async def http_exc_handler(request: Request, exc: StarletteHTTPException):
    return templates.TemplateResponse(
        request, "index.html",
        {"error": f"Erreur {exc.status_code}: {exc.detail}"},
        status_code=exc.status_code,
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...)):
    if not file.filename or not _is_supported(file.filename):
        return templates.TemplateResponse(
            request, "index.html",
            {"error": "Format non supporté. Utilisez PNG ou JPEG."}
        )

    session_id = uuid.uuid4().hex
    ext = Path(file.filename).suffix.lower()
    input_path = UPLOAD_DIR / f"{session_id}{ext}"
    output_img = OUTPUT_DIR / f"{session_id}_masked.png"
    output_txt = OUTPUT_DIR / f"{session_id}_masked.txt"

    content = await file.read()
    async with aiofiles.open(input_path, "wb") as f:
        await f.write(content)

    try:
        result = process_image(str(input_path))
        result["masked_image"].save(str(output_img))
        masked_text = result["masked_text"]
        async with aiofiles.open(output_txt, "w", encoding="utf-8") as f:
            await f.write(masked_text)
    except Exception as e:
        logger.error("Processing failed: %s", e)
        return templates.TemplateResponse(
            request, "index.html",
            {"error": f"Erreur lors du traitement: {str(e)}"}
        )
    finally:
        if input_path.exists():
            input_path.unlink()

    return templates.TemplateResponse(request, "index.html", {
        "result": {
            "masked_text": masked_text,
            "masked_image_path": output_img.name,
            "masked_text_path": output_txt.name,
            "sensitive_count": result["sensitive_count"],
        },
    })


def _is_supported(filename: str) -> bool:
    return Path(filename).suffix.lower() in {".png", ".jpg", ".jpeg"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
