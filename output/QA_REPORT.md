# QA Report — CBSE Class 12 Chemistry Chapter-wise Question Bank

Generated: 2026-10-08  |  Final PDF: `output/CBSE_Class_12_Chemistry_2025-26_Chapterwise_Question_Bank.pdf`  (116 pages, 25.3 MB)

## 1. Source

- Source PDF: `26_Chemistry board papers.pdf` — **159 pages verified** (A4 portrait, native vector/text + embedded diagrams; bilingual Hindi/English interleaved per paper).
- Board papers detected: **7** (Series/SET title pages: SQRP1 SET 1, QSR2P SET 1, RPQ3S SET 1, 4SQRP SET 1, QSR5P SET 1, S7PQR SET 1, RPQ3S SET 5 / QP 56(B)).
- Classification reference: `Chemistry_SecP2_2026-27.pdf` — official CBSE Class XII Chemistry curriculum 2026–27 (sole authoritative chapter list; no chapters invented).

## 2. Count reconciliation

| Stage | Count |
|---|---|
| Questions detected (7 papers x 33, numbering verified per paper) | 231 |
| Questions extracted (full native text + crops) | 231 |
| Questions classified (primary chapter assigned) | 231 |
| Questions assigned marks (1M-5M, section structure) | 231 |
| Questions assigned source pages | 231 |
| Questions scheduled for PDF | 231 |
| Questions inserted in PDF (verified by block count) | 231 |

**Detected = Extracted = Classified = Inserted = 231.** No question was silently omitted, duplicated or altered.

## 3. Marks distribution (authoritative: paper section structure)

| Marks | Questions |
|---|---|
| 1M | 112 |
| 2M | 35 |
| 3M | 49 |
| 4M | 14 |
| 5M | 21 |
| **Total** | **231** |

Section structure per paper (stated in each paper's General Instructions): A: Q1-16 MCQ 1M; B: Q17-21 VSA 2M; C: Q22-28 SA 3M; D: Q29-30 case-based 4M; E: Q31-33 LA 5M. Verified: 112x1M + 35x2M + 49x3M + 14x4M + 21x5M = 231. Right-margin printed marks tokens were retained per question as `printed_marks_evidence` (consistent for 114 questions where present; the token scan window can pick up stray adjacent tokens, so the section-implied marks are authoritative).

## 4. Chapter distribution (official CBSE 2026-27 units)

| Unit | Chapter | Questions |
|---|---|---|
| 1 | Solutions | 24 |
| 2 | Electrochemistry | 24 |
| 3 | Chemical Kinetics | 26 |
| 4 | d and f Block Elements | 22 |
| 5 | Coordination Compounds | 25 |
| 6 | Haloalkanes and Haloarenes | 20 |
| 7 | Alcohols, Phenols and Ethers | 22 |
| 8 | Aldehydes, Ketones and Carboxylic Acids | 17 |
| 9 | Amines | 25 |
| 10 | Biomolecules | 26 |
| | **Total** | **231** |

## 5. Classification review

- Every one of the 231 questions was individually reviewed against its full extracted text (native PDF text + OCR of the original-page crops) and the official syllabus chapter list.
- Classifier (weighted concept-pattern scoring): 194 confirmed, 37 adjudicated (judgment calls documented in `scripts/review_adjudications.json`).
- Low-confidence classifications (< 0.75, all manually reviewed and confirmed): 5 — CH02-1M-006, CH02-1M-007, CH05-1M-012, CH06-1M-004, CH06-1M-007.
- Image-only questions resolved by visual crop inspection + OCR: P3 Q6 (strongest base, aniline derivatives), P4 Q21 (dinitrochlorobenzene + NaOH; HBr addition), P4 Q22 (aniline acetylation/bromination; diazonium sequence), P6 Q7 (benzyl phenyl ether + HI).
- Flagged ambiguous (retained, recorded in manifest): CH05-1M-012 (P7 Q7, vitamin B12 = Co3+ complex — assigned Coordination Compounds, Biomolecules is the runner-up; the question is framed around the coordination complex).

## 6. Duplicates

- Exact duplicates (identical normalized text): 0 groups.
- Potential duplicates across papers (similarity >= 0.72, all RETAINED as separate occurrences): 5 pairs —
  - Paper 5 Q15  <->  Paper 7 Q15 (similarity 0.85, both Alcohols, Phenols and Ethers)
  - Paper 1 Q3  <->  Paper 7 Q5 (similarity 0.845, both d and f Block Elements)
  - Paper 1 Q7  <->  Paper 7 Q6 (similarity 0.757, both Coordination Compounds)
  - Paper 2 Q23  <->  Paper 5 Q22 (similarity 0.729, both Electrochemistry)
  - Paper 5 Q27  <->  Paper 7 Q28 (similarity 0.726, both Aldehydes, Ketones and Carboxylic Acids)
- Additionally identified by manual review: Paper 4 Q1 <-> Paper 7 Q8 (chloroform + air/sunlight -> phosgene; reworded stem, reordered options) — retained as separate occurrences.
- Same-type but NOT duplicates (reviewed): P2 Q23 vs P5 Q22 (emf numericals, different cells); P5 Q27 vs P7 Q28 (conversion sets, different conversions).

## 7. Page-spanning questions

12 questions span two English pages of their paper; each is reproduced as two stacked crops (both portions embedded, verified):
P6 Q29 (PDF pp. 128, 130), P1 Q32 (PDF pp. 21, 23), P6 Q32 (PDF pp. 132, 134), P5 Q33 (PDF pp. 111, 113), P4 Q29 (PDF pp. 82, 84), P5 Q29 (PDF pp. 105, 107), P7 Q29 (PDF pp. 151, 153), P6 Q22 (PDF pp. 124, 126), P1 Q31 (PDF pp. 19, 21), P3 Q32 (PDF pp. 65, 67), P7 Q31 (PDF pp. 155, 157), P6 Q33 (PDF pp. 134, 136)

## 8. Assertion/Reason instruction block

All 7 papers carry the block "For Questions number 13 to 16, two statements are given..." between Q12 and Q13. It is attached to Q13 (the first assertion-reason question) in every paper — verified — and trimmed from Q12, so no unrelated material appears in any crop.

## 9. Post-generation validation (independent re-open of the PDF)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | all pages render | PASS | 116 pages rendered at 30 dpi; corrupt: [] |
| 2 | all 231 questions inserted exactly once | PASS | question blocks found in PDF: 231; IDs seen: 231; source labels: 231 |
| 3 | ordering chapter -> marks -> paper -> page -> Q no | PASS | 231 blocks in expected order |
| 4 | marks subsections 1M..5M each start on a new page | PASS | subsection pages per marks: 1M:10, 2M:8, 3M:10, 4M:8, 5M:9 |
| 5 | all crops embedded without recompression | PASS | embedded images: 244; unique crop hashes matched: 244/244; mismatched: [] |
| 6 | PDF outline (bookmarks) valid | PASS | 58 outline entries; targets within 1..116 |
| 7 | visible TOC links resolve | PASS | 55 GOTO links on TOC pages; broken: [] |
| 8 | footer page numbers on all content pages | PASS | missing on: [] |
| 9 | manifest: unique IDs, official chapters, valid marks/pages | PASS | 231 entries valid |
| 10 | counts reconcile (detected=extracted=classified=inserted=231) | PASS | {"detected": 231, "extracted": 231, "classified": 231, "assigned_marks": 231, "assigned_source_pages": 231, "scheduled_for_pdf": 231, "inserted_in_pdf": 231} |
| 11 | page-spanning questions have both portions embedded | PASS | 12 spanning questions: P6Q29, P1Q32, P6Q32, P5Q33, P4Q29, P5Q29, P7Q29, P6Q22, P1Q31, P3Q32, P7Q31, P6Q33 |
| 12 | A/R instruction block retained with Q13 in all 7 papers | PASS | per-paper: [True, True, True, True, True, True, True] |
| 13 | OCR-vs-native spot check (10 questions) | PASS | avg word overlap 97%; [{"id": "CH08-1M-001", "native_words": 16, "ocr_words": 16, "overlap_ratio": 1.0}, {"id": "CH02-1M-005", "native_words": 8, "ocr_words": 12, "overlap_ratio": 0.75}, {"id": "CH01-1M-007", "native_words": 17, "ocr_words": 20, "overlap_ratio": 0.94}, {"id": "CH09-1M-010", "native_words": 13, "ocr_words": 13, "overlap_ratio": 1.0}, {"id": "CH03-3M-004", "native_words": 14, "ocr_words": 14, "overlap_ratio": 1.0}, {"id": "CH03-2M-003", "native_words": 11, "ocr_words": 11, "overlap_ratio": 1.0}, {"id": "CH03-1M-010", "native_words": 8, "ocr_words": 8, "overlap_ratio": 1.0}, {"id": "CH02-3M-001", "native_words": 37, "ocr_words": 36, "overlap_ratio": 0.97}, {"id": "CH09-1M-009", "native_words": 7, "ocr_words": 8, "overlap_ratio": 1.0}, {"id": "CH02-1M-003", "native_words": 13, "ocr_words": 14, "overlap_ratio": 1.0}] |

**Overall: ALL CHECKS PASS** (13/13 checks passed).

## 10. OCR vs native spot check

| Question | native words | OCR words | overlap |
|---|---|---|---|
| CH08-1M-001 | 16 | 16 | 100% |
| CH02-1M-005 | 8 | 12 | 75% |
| CH01-1M-007 | 17 | 20 | 94% |
| CH09-1M-010 | 13 | 13 | 100% |
| CH03-3M-004 | 14 | 14 | 100% |
| CH03-2M-003 | 11 | 11 | 100% |
| CH03-1M-010 | 8 | 8 | 100% |
| CH02-3M-001 | 37 | 36 | 97% |
| CH09-1M-009 | 7 | 8 | 100% |
| CH02-1M-003 | 13 | 14 | 100% |

OCR was used only for classification assist and QA — the visible question content is always the original-page crop, never OCR-reconstructed text.

## 11. Extraction anomalies / notes

- Papers 1-2 Hindi text layer uses a broken PUA ToUnicode map; papers 3-7 Hindi is proper Devanagari. Extraction used the English pages only; Hindi twin pages are recorded per question as supplementary provenance.
- Some formula/diagram content is embedded as images in the source (e.g. graph options, reaction schemes); these are preserved verbatim in the crops. Native text for such questions is partial by nature — OCR of the crop was used for classification assist.
- Papers 6-7 place two section headers on one page (B+C); section boundaries were handled per question token, not per page.
- No out-of-syllabus questions were detected; every question maps to one of the 10 official chapters.

## 12. Validation status

- Final PDF: `output/CBSE_Class_12_Chemistry_2025-26_Chapterwise_Question_Bank.pdf` — 116 pages, 25.3 MB, opens cleanly, every page renders.
- Manifest: `output/manifest.json` — 231 question records with full provenance (question ID, chapter, marks, section, source paper/series/set/QP code, source PDF pages, Hindi twin pages, original question number, portion rects, crop paths, classification confidence, text hash, duplicate info, validation status).
- Pipeline: `scripts/qbank.py` (detection/segmentation/crops/text), `scripts/extract_crops.py` (crops + OCR), `scripts/classify_chapters.py` (classification), `scripts/review_adjudications.json` (manual review), `scripts/build_manifest.py` (ordering/IDs/manifest), `scripts/build_pdf.py` (final PDF), `scripts/qa_report.py` (this QA).
- **Status: VALIDATED — all checks pass**
