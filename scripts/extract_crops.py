#!/usr/bin/env python3
"""
extract_crops.py — Stage: crop extraction + OCR assist.

1. Runs the full detection/segmentation pipeline (qbank.run_detection).
2. Renders every question portion from the ORIGINAL source PDF pages into
   work/crops/ (250-dpi JPEG, quality 88) — these are the exact images that
   will be embedded in the final question-bank PDF (visual fidelity: the
   question is always shown as a crop of the original page, never re-typeset).
3. OCRs every crop with tesseract (eng) into work/ocr/ — used ONLY for
   classification assist on image-heavy questions and for OCR-vs-native QA
   spot checks. Never used as the visible question content.

Usage: python scripts/extract_crops.py ["26_Chemistry board papers.pdf"]
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qbank

SRC = sys.argv[1] if len(sys.argv) > 1 else "26_Chemistry board papers.pdf"
CROPS = "work/crops"
OCR = "work/ocr"

# tesseract binary + traineddata (pip wheel tesseract-bin / vendored tessdata)
VENV_TESS = "/home/user/venv/lib/python3.11/site-packages/tesseract_bin/data/bin/tesseract"
TESSDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tessdata")


def ocr_image(img_path):
    env = dict(os.environ)
    env["TESSDATA_PREFIX"] = TESSDATA
    try:
        r = subprocess.run(
            [VENV_TESS, img_path, "stdout", "-l", "eng", "--psm", "6"],
            capture_output=True, text=True, timeout=120, env=env)
        return r.stdout.strip()
    except Exception as e:
        return f"[OCR FAILED: {e}]"


def main():
    import pymupdf
    doc = pymupdf.open(SRC)
    papers, paper_meta, questions = qbank.run_detection(SRC)
    doc.close()

    os.makedirs(CROPS, exist_ok=True)
    os.makedirs(OCR, exist_ok=True)

    doc = pymupdf.open(SRC)
    n_parts = 0
    for q in questions:
        parts = qbank.crop_question(doc, q, CROPS)
        q["crop_images"] = [p["image"] for p in parts]
        q["crop_meta"] = [
            {"page": p["page"], "rect": p["rect"],
             "width_px": p["width_px"], "height_px": p["height_px"]}
            for p in parts
        ]
        n_parts += len(parts)
        # OCR each part
        for p in parts:
            ocr_file = os.path.join(
                OCR, p["image"].replace(".jpg", ".txt"))
            if not os.path.exists(ocr_file):
                txt = ocr_image(os.path.join(CROPS, p["image"]))
                with open(ocr_file, "w") as f:
                    f.write(txt)
    doc.close()

    # combined text for classification: native + OCR (OCR assists image-heavy
    # questions; native text remains primary)
    for q in questions:
        ocr_txt = " ".join(
            open(os.path.join(OCR, img.replace(".jpg", ".txt"))).read()
            for img in q["crop_images"])
        q["ocr_text"] = ocr_txt
        q["combined_text"] = q["native_text"] + "\n" + ocr_txt

    # Visual-inspection overrides for image-only questions: OCR of the crop
    # misses structure-only content (options/reagents drawn as images). These
    # notes were produced by inspecting the original page crops and are
    # applied here so the pipeline is fully reproducible.
    overrides_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "ocr_manual_overrides.json")
    if os.path.exists(overrides_path):
        overrides = json.load(open(overrides_path))
        for q in questions:
            key = f"P{q['paper_index']} Q{q['question_number']}"
            if key in overrides:
                q["ocr_text"] = (q.get("ocr_text", "") + "\n"
                                 + overrides[key]).strip()
                q["combined_text"] = q["native_text"] + "\n" + q["ocr_text"]

    with open("work/questions_detected.json", "w") as f:
        json.dump(questions, f, ensure_ascii=False, indent=1, default=str)
    with open("work/papers_meta.json", "w") as f:
        json.dump(paper_meta, f, ensure_ascii=False, indent=1, default=str)

    print(f"questions: {len(questions)}, crop parts: {n_parts}")
    print(f"crops -> {CROPS}/, ocr -> {OCR}/")


if __name__ == "__main__":
    main()
