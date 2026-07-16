import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from core.masker import process_image
from core.ocr import extract_text_and_boxes
from core.detector import detect_pii
from fastapi.testclient import TestClient
from main import app

failed = 0

def test(name, cond, detail=""):
    global failed
    if cond:
        print(f"  PASS: {name}")
    else:
        print(f"  FAIL: {name} {detail}")
        failed += 1

print("=== Test 1: Realistic ID Card ===")
result = process_image("E:/project traitement dimage/test_id_card.png")
print(f"  Original: {result['original_text']}")
print(f"  Masked:   {result['masked_text']}")
test("sensitive count >= 5", result["sensitive_count"] >= 5, f"got {result['sensitive_count']}")
test("masked text contains [MASKED]", "[MASKED]" in result["masked_text"])
test("masked image is not None", result["masked_image"] is not None)

print("\n=== Test 2: Public Document (No PII) ===")
text, boxes = extract_text_and_boxes("E:/project traitement dimage/test_public.png")
sensitive = detect_pii(text, boxes)
test("no false positives on clean text", len(sensitive) == 0, f"got {len(sensitive)}")

print("\n=== Test 3: Unsupported File Type ===")
client = TestClient(app)
r = client.post("/upload", files={"file": ("test.pdf", b"fake pdf", "application/pdf")})
test("rejects unsupported format", "non support" in r.text, f"status={r.status_code}")

print("\n=== Test 4: Output Files Generated ===")
out_dir = "E:/project traitement dimage/output"
files = os.listdir(out_dir)
png_files = [f for f in files if f.endswith(".png")]
txt_files = [f for f in files if f.endswith(".txt")]
test("generated masked PNG images", len(png_files) > 0)
test("generated masked TXT files", len(txt_files) > 0)

print("\n=== Test 5: End-to-end Web Upload ===")
with open("E:/project traitement dimage/test_input.png", "rb") as f:
    r = client.post("/upload", files={"file": ("test.png", f, "image/png")})
test("upload returns 200", r.status_code == 200, f"got {r.status_code}")
test("result contains masked text", "[MASKED]" in r.text)
test("result contains download links", "T" in r.text)

print(f"\n{'='*40}")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print(f"{failed} TEST(S) FAILED")
    sys.exit(1)
