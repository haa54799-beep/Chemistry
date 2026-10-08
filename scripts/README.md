# CBSE Class 12 Chemistry — Chapter-wise Question Bank pipeline

Reproducible pipeline that turns the repo's board-paper PDF
(`26_Chemistry board papers.pdf`, 159 pages, 7 papers, bilingual
Hindi/English) into a chapter-wise question bank PDF, a machine-readable
manifest, and a QA report.

Classification uses the **official CBSE Class XII Chemistry curriculum
2026–27** (`Chemistry_SecP2_2026-27.pdf`) as the sole authoritative chapter
reference — the 10 units:

1. Solutions · 2. Electrochemistry · 3. Chemical Kinetics · 4. d and f Block
Elements · 5. Coordination Compounds · 6. Haloalkanes and Haloarenes ·
7. Alcohols, Phenols and Ethers · 8. Aldehydes, Ketones and Carboxylic Acids ·
9. Amines · 10. Biomolecules

## Deliverables

| Path | What |
|---|---|
| `output/CBSE_Class_12_Chemistry_2025-26_Chapterwise_Question_Bank.pdf` | Final question bank (cover, clickable TOC + bookmarks, master index, chapter sections, 1M→5M subsections, original-page crop per question with a small `Source: Paper X (SET Y) \| PDF p. N \| Q. n` label, footer page numbers) |
| `output/manifest.json` | Machine-readable manifest: 231 question records with full provenance (question ID `CHxx-mM-nnn`, chapter, marks, section, source paper/series/SET/QP code, source PDF pages, Hindi twin pages, original question number, portion rects, crop paths, classification confidence + runner-up, text hash, duplicate info, validation status) |
| `output/QA_REPORT.md` | QA report: count reconciliation, distributions, review notes, duplicates, anomalies, 13 post-generation validation checks |
| `scripts/tessdata/` | Vendored tesseract `eng` + `hin` traineddata (reproducible OCR, no downloads) |

## Requirements

```
python -m venv venv && venv/bin/pip install -r scripts/requirements.txt
```

Only **PyMuPDF**, **Pillow** and **tesseract-bin** (which bundles the
tesseract binary) are required. The tesseract traineddata is vendored in
`scripts/tessdata/` and used via `TESSDATA_PREFIX` — no system tesseract
install and no model downloads are needed.

## Pipeline (run in order, from the repository root)

```bash
# 1. Detection + segmentation + native text (writes work/questions_detected.json,
#    work/papers_meta.json; prints per-paper question counts and geometry)
venv/bin/python scripts/qbank.py "26_Chemistry board papers.pdf"

# 2. Crops (250-dpi JPEG renders of the ORIGINAL page regions -> work/crops/)
#    + OCR of every crop (work/ocr/) for classification assist and QA
venv/bin/python scripts/extract_crops.py "26_Chemistry board papers.pdf"

# 3. Chapter classification (weighted concept patterns over native+OCR text)
venv/bin/python scripts/classify_chapters.py \
    work/questions_detected.json work/questions_classified.json

# 4. Manual review layer + ordering + stable IDs + duplicate detection
#    (applies scripts/review_adjudications.json; writes work/final_questions.json
#    and output/manifest.json)
venv/bin/python scripts/build_manifest.py

# 5. Final PDF
venv/bin/python scripts/build_pdf.py

# 6. Independent QA (re-opens the PDF; writes output/QA_REPORT.md)
venv/bin/python scripts/qa_report.py
```

## What the pipeline guarantees

- **Coverage**: every question of every paper (7 × 33 = 231) is detected,
  extracted, classified and inserted — detected = extracted = classified =
  inserted = 231 (reconciled in the QA report).
- **Visual fidelity**: each question in the final PDF is a 250-dpi crop
  rendered from the original PDF page (subparts, OR choices, case-study
  passages, diagrams and graphs preserved); crops are embedded without
  recompression (verified byte-identical in QA). OCR is used only for
  classification assist and QA — never as visible content.
- **Classification**: one primary chapter per question from the official
  2026–27 list; all 231 questions were individually reviewed; judgment calls
  are documented in `scripts/review_adjudications.json` and recorded in the
  manifest with confidence and runner-up.
- **Marks**: 1M–5M from each paper's section structure (A: Q1–16 1M,
  B: Q17–21 2M, C: Q22–28 3M, D: Q29–30 4M, E: Q31–33 5M); printed
  right-margin marks tokens retained per question as cross-check evidence.
- **Ordering**: chapter (syllabus order) → marks 1M→5M → original paper →
  source PDF page → question number.
- **Duplicates**: repeated questions across papers are retained as separate
  occurrences and recorded (exact-duplicate groups + potential-duplicate
  pairs listed in the QA report).
- **Provenance**: question ID, chapter, marks, source paper/series/SET/QP
  code, source PDF page(s), Hindi twin page(s), original question number,
  portion bounding boxes, crop file names, text hash, validation status.

## Repository layout

```
scripts/
  qbank.py                  # core library: paper detection, language split,
                            #   geometry, question segmentation (incl. page
                            #   spanning + A/R block handling), crops, text
  extract_crops.py          # stage 2: crops + OCR
  classify_chapters.py      # stage 3: chapter classifier
  review_adjudications.json # manual review layer (judgment calls)
  ocr_manual_overrides.json # visual-inspection notes for image-only questions
  build_manifest.py         # stage 4: review, ordering, IDs, manifest
  build_pdf.py              # stage 5: final PDF
  qa_report.py              # stage 6: independent QA + QA_REPORT.md
  tessdata/                 # vendored eng+hin traineddata
  requirements.txt          # dependencies
  README.md                 # this file
output/                     # final PDF + manifest.json + QA_REPORT.md
work/                       # scratch (gitignored): crops, OCR, intermediates
```
