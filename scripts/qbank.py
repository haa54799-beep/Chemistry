#!/usr/bin/env python3
"""
qbank.py — Core library for the CBSE Class 12 Chemistry chapter-wise
question-bank pipeline.

Stages implemented here:
  * source PDF inspection
  * board-paper boundary detection
  * page-language (Hindi/English) detection
  * question detection & segmentation (with page-spanning questions)
  * marks determination (section-authoritative + printed cross-check)
  * high-resolution cropping of original question regions
  * Hindi twin-page provenance mapping

The final visible question always comes from a crop/render of the ORIGINAL
source PDF page (never re-typeset from OCR text).
"""

import hashlib
import json
import os
import re
import unicodedata

import pymupdf

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Official CBSE Class XII Chemistry (2026-27) course structure, as given in
# the supplied curriculum document (Chemistry_SecP2_2026-27.pdf, p. 8).
# (unit_no, official chapter title, marks weightage in theory paper)
OFFICIAL_CHAPTERS = [
    (1,  "Solutions", 7),
    (2,  "Electrochemistry", 9),
    (3,  "Chemical Kinetics", 7),
    (4,  "d and f Block Elements", 7),
    (5,  "Coordination Compounds", 7),
    (6,  "Haloalkanes and Haloarenes", 6),
    (7,  "Alcohols, Phenols and Ethers", 6),
    (8,  "Aldehydes, Ketones and Carboxylic Acids", 8),
    (9,  "Amines", 6),
    (10, "Biomolecules", 7),
]
CHAPTER_BY_UNIT = {u: t for u, t, _ in OFFICIAL_CHAPTERS}

# CBSE question-paper design (stated in the General Instructions of every
# paper in the source PDF): five sections with fixed question ranges.
SECTION_RANGES = [
    ("A", 1, 16, 1, "Multiple Choice"),
    ("B", 17, 21, 2, "Very Short Answer"),
    ("C", 22, 28, 3, "Short Answer"),
    ("D", 29, 30, 4, "Case-Based"),
    ("E", 31, 33, 5, "Long Answer"),
]

RENDER_DPI = 250          # crop/render resolution from the vector source PDF
JPEG_QUALITY = 88         # embedded crop quality (no recompression of vectors)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _is_devanagari_heavy(text):
    """True if the page's text layer is predominantly Devanagari (Hindi).

    Papers 1-2 of the source PDF encode Hindi with a broken ToUnicode map
    (Private-Use-Area codepoints); papers 3-7 encode real Devanagari.
    Both cases are detected here.
    """
    deva = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
    pua = sum(1 for c in text if 0xE000 <= ord(c) <= 0xF8FF)
    asc = sum(1 for c in text if ord(c) < 128 and c.isalpha())
    return (deva + pua) > asc


_HEADER_FOOTER_WORD = re.compile(r"^[{}\[\]*^]$|^\^?56/|^\*.*\*$|^P\.T\.O\.$")
_QTOKEN = re.compile(r"^\d{1,2}\.$")


def normalize_text(t):
    """Normalize text for duplicate detection / indexing."""
    t = unicodedata.normalize("NFKC", t)
    t = t.lower()
    t = re.sub(r"[^a-z0-9\u0900-\u097f]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def text_hash(t):
    return hashlib.sha256(normalize_text(t).encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Stage 1 — source inspection
# ---------------------------------------------------------------------------

def inspect_source(pdf_path):
    doc = pymupdf.open(pdf_path)
    info = {
        "file": os.path.basename(pdf_path),
        "file_size_bytes": os.path.getsize(pdf_path),
        "page_count": doc.page_count,
        "pages": [],
    }
    rect = doc[0].rect
    info["page_dimensions_pt"] = {"width": round(rect.width, 2), "height": round(rect.height, 2)}
    info["orientation"] = "portrait" if rect.height > rect.width else "landscape"
    total_images = 0
    total_text = 0
    for i, page in enumerate(doc):
        text = page.get_text()
        n_img = len(page.get_images(full=True))
        total_images += n_img
        total_text += len(text.strip())
        info["pages"].append({
            "page": i + 1,
            "text_chars": len(text.strip()),
            "images": n_img,
            "language": "hindi" if _is_devanagari_heavy(text) else "english",
        })
    info["total_embedded_images"] = total_images
    info["total_text_chars"] = total_text
    info["has_text_layer"] = total_text > 1000
    info["hindi_text_encoding"] = (
        "broken-PUA (papers 1-2) and proper Devanagari (papers 3-7); "
        "Hindi is not needed for the primary extraction (English twin pages)"
    )
    doc.close()
    return info


# ---------------------------------------------------------------------------
# Stage 2 — paper boundary detection
# ---------------------------------------------------------------------------

def detect_papers(doc):
    """Detect board-paper boundaries via 'Series :'/'SET~' title pages."""
    starts = []
    for i, page in enumerate(doc):
        t = page.get_text()
        if re.search(r"Series\s*:", t) and re.search(r"SET~", t):
            starts.append(i)
    if not starts:
        raise RuntimeError("No board-paper title pages found (Series/SET markers).")
    starts.append(doc.page_count)
    papers = []
    for k in range(len(starts) - 1):
        a, b = starts[k], starts[k + 1] - 1  # 0-based inclusive page range
        title_text = doc[a].get_text()
        series = re.search(r"Series\s*:\s*(\S+)", title_text)
        setm = re.search(r"SET~(\S+)", title_text)
        qp = re.search(r"\^?56[/\(]([0-9A-Za-z()]+)[\)/]\^?", title_text)
        boxed = re.findall(r"\b(2\d{3})\b", title_text)
        # footer code like *5682F11* on an English question page
        code = None
        for pno in range(a, b):
            for w in doc[pno].get_text("words"):
                if re.fullmatch(r"\*[0-9A-Z]+\*", w[4]):
                    code = w[4]
                    break
            if code:
                break
        papers.append({
            "paper_index": k + 1,
            "pdf_pages": [a + 1, b + 1],           # 1-based inclusive
            "series": series.group(1) if series else None,
            "set": setm.group(1) if setm else None,
            "qp_code": ("56/" + qp.group(1)) if qp else None,
            "qp_code_box": boxed[0] if boxed else None,
            "qp_code_stAR": code,
        })
    return papers


# ---------------------------------------------------------------------------
# Stage 3 — per-paper language split, geometry, question segmentation
# ---------------------------------------------------------------------------

def _page_events(page):
    """Return (tokens, sections, words) for a page.

    tokens   : list of dicts {qnum, x0, y0, y1} for 'N.' question numbers
    sections : list of dicts {letter, y0} for 'SECTION – X' headers
    """
    words = page.get_text("words")
    tokens, sections = [], []
    for w in words:
        x0, y0, x1, y1, t = w[0], w[1], w[2], w[3], w[4]
        if _QTOKEN.match(t) and x0 < 85:
            tokens.append({"qnum": int(t.rstrip(".")), "x0": x0, "y0": y0, "y1": y1})
        if t == "SECTION":
            # letter is the next word (possibly after a dash)
            nxt = [ww[4] for ww in words if ww[0] > x0 and abs(ww[1] - y0) < 4]
            letter = None
            for cand in nxt:
                if re.fullmatch(r"[A-E]", cand):
                    letter = cand
                    break
            if letter:
                sections.append({"letter": letter, "y0": y0})
    tokens.sort(key=lambda d: d["y0"])
    sections.sort(key=lambda d: d["y0"])
    return tokens, sections, words


def _paper_geometry(doc, pages_1based, tokens_by_page, sections_by_page):
    """Compute content bounds (in PDF points) for a paper's English pages.

    Only pages that actually carry questions or section headers contribute to
    the vertical bounds (title / instruction / end pages are excluded).
    """
    content_pages = [p for p in pages_1based
                     if tokens_by_page.get(p) or sections_by_page.get(p)]
    if not content_pages:
        content_pages = pages_1based
    min_tok_x, max_word_x = 1e9, 0.0
    min_event_y, footer_y = 1e9, 1e9
    page_width = doc[0].rect.width
    for pno in content_pages:
        page = doc[pno - 1]
        words = page.get_text("words")
        for w in words:
            x0, y0, x1, y1, t = w[0], w[1], w[2], w[3], w[4]
            if _HEADER_FOOTER_WORD.match(t):
                if y0 > 600:
                    footer_y = min(footer_y, y0)
                continue
            max_word_x = max(max_word_x, x1)
            min_tok_x = min(min_tok_x, x0)
            if y0 < 600:
                min_event_y = min(min_event_y, y0)
        for tk in tokens_by_page.get(pno, []):
            min_tok_x = min(min_tok_x, tk["x0"])
            min_event_y = min(min_event_y, tk["y0"])
    if footer_y > 900:  # fallback: no footer pattern found
        footer_y = 690 if min_event_y > 60 else 660
    left = max(10.0, min_tok_x - 9.0)
    right = min(page_width - 30.0, max_word_x + 9.0)
    content_top = min_event_y - 3.0
    content_bottom = footer_y - 4.0
    return {
        "left": round(left, 1), "right": round(right, 1),
        "content_top": round(content_top, 1),
        "content_bottom": round(content_bottom, 1),
    }


def _section_for_qnum(qnum):
    for letter, lo, hi, marks, _kind in SECTION_RANGES:
        if lo <= qnum <= hi:
            return letter, marks
    raise ValueError(f"Question number {qnum} outside known section ranges")


def segment_questions(doc, paper):
    """Segment one paper's ENGLISH page sequence into questions.

    Returns a list of question dicts with portions (page, rect) covering the
    complete question including page-spanning continuations, OR choices,
    case-study passages and subparts.
    """
    a, b = paper["pdf_pages"]
    # language split
    hi_pages, en_pages = [], []
    for pno in range(a, b + 1):
        t = doc[pno - 1].get_text()
        (hi_pages if _is_devanagari_heavy(t) else en_pages).append(pno)

    tokens_by_page, sections_by_page, words_by_page = {}, {}, {}
    for pno in en_pages:
        toks, secs, words = _page_events(doc[pno - 1])
        tokens_by_page[pno] = toks
        sections_by_page[pno] = secs
        words_by_page[pno] = words

    geom = _paper_geometry(doc, en_pages, tokens_by_page, sections_by_page)

    # ordered token stream across the English page sequence
    stream = []  # (page, token)
    for pno in en_pages:
        for tk in tokens_by_page[pno]:
            stream.append((pno, tk))

    # sanity: expect 1..33 in order
    qnums = [tk["qnum"] for _, tk in stream]
    expected = list(range(1, 34))
    numbering_ok = (qnums == expected)

    # content-word lookup helper: any word strictly inside (top, bottom)?
    def content_words(pno):
        out = []
        for w in words_by_page.get(pno, []):
            if _HEADER_FOOTER_WORD.match(w[4]):
                continue
            if geom["left"] - 2 < w[0] < geom["right"] + 25:
                out.append(w)
        return out

    def has_content(pno, top, bottom):
        return any(top < w[1] < bottom for w in content_words(pno))

    def line_bottom_below(pno, y_limit):
        """Max y1 of content words whose box ends at or above y_limit."""
        vals = [w[3] for w in content_words(pno) if w[3] <= y_limit + 0.5]
        return max(vals) if vals else None

    def line_top_above(pno, y_limit):
        """Max y1 of content words strictly above y_limit (previous line)."""
        vals = [w[3] for w in content_words(pno)
                if w[3] <= y_limit and w[1] < y_limit - 0.5]
        return max(vals) if vals else None

    # ---- assertion/reason instruction blocks -------------------------------
    # Blocks such as "For Questions number 13 to 16, two statements are given
    # - one labelled as Assertion (A) ..." sit between two questions. They are
    # intrinsically part of the FIRST question of the referenced range, so they
    # are attached to that question and trimmed from the preceding question.
    AR_BLOCK = re.compile(r"For\s+[Qq]uestions?\s+number\s+(\d+)\s+to\s+(\d+)",
                          re.IGNORECASE)

    def page_lines(pno):
        lines = []
        for w in sorted(content_words(pno), key=lambda w: (w[1], w[0])):
            if lines and abs(w[1] - lines[-1][0]) < 4:
                lines[-1][2].append((w[0], w[4]))
                lines[-1][1] = max(lines[-1][1], w[3])
            else:
                lines.append([w[1], w[3], [(w[0], w[4])]])
        return [(l[0], l[1], " ".join(t for _, t in sorted(l[2])))
                for l in lines]

    ar_blocks = {}  # page -> list of (start_y, first_q, last_q)
    for pno in en_pages:
        blocks = []
        for y0, y1, text in page_lines(pno):
            m = AR_BLOCK.search(text)
            if m:
                blocks.append((y0, int(m.group(1)), int(m.group(2))))
        if blocks:
            ar_blocks[pno] = blocks

    def trim_bottom_for_block(pno, bottom, qnum):
        """If an A/R block for a LATER question starts above `bottom`, trim."""
        for start_y, first_q, last_q in ar_blocks.get(pno, []):
            if first_q <= qnum <= last_q:
                continue  # block belongs to this question
            if start_y < bottom:
                last_y1 = line_bottom_below(pno, start_y)
                if last_y1 is None:
                    return start_y - 4.0
                return max(start_y - 4.0, last_y1 + 0.3)
        return bottom

    # Full regions of the A/R blocks: first_q -> (page, top, bottom).
    # The block is intrinsically part of the FIRST question of its range, so
    # it is attached to that question (as a leading portion when it sits on an
    # earlier page) and trimmed from the preceding question.
    ar_block_regions = {}
    for pno, blocks in ar_blocks.items():
        for start_y, first_q, last_q in blocks:
            nxt = ([t["y0"] for t in tokens_by_page[pno] if t["y0"] > start_y + 1]
                   + [s["y0"] for s in sections_by_page[pno] if s["y0"] > start_y + 1]
                   + [geom["content_bottom"] + 4.0])
            next_event = min(nxt)
            last_y1 = line_bottom_below(pno, next_event)
            if next_event >= geom["content_bottom"] + 3.0:
                b_bottom = geom["content_bottom"]
            elif last_y1 is None:
                b_bottom = next_event - 4.0
            else:
                b_bottom = max(next_event - 4.0, last_y1 + 0.3)
            prev_y1 = line_top_above(pno, start_y)
            b_top = start_y - 4.0 if prev_y1 is None else max(start_y - 4.0, prev_y1 + 0.3)
            if b_bottom > b_top + 6 and has_content(pno, b_top, b_bottom):
                ar_block_regions[first_q] = (pno, b_top, b_bottom)

    def block_on_page_above(pno, qnum):
        """A/R block for a LATER question starting on page pno (top region)."""
        for start_y, first_q, last_q in ar_blocks.get(pno, []):
            if not (first_q <= qnum <= last_q):
                return start_y
        return None

    questions = []
    for idx, (pno, tk) in enumerate(stream):
        qn = tk["qnum"]
        letter, marks = _section_for_qnum(qn)
        portions = []
        # leading A/R instruction block on an earlier page -> leading portion
        blk = ar_block_regions.get(qn)
        if blk and blk[0] != pno:
            portions.append({
                "page": blk[0],
                "rect": [geom["left"], round(blk[1], 1), geom["right"], round(blk[2], 1)],
                "kind": "instruction_block",
            })
        # top: 4pt above the question-number line, but never clip the line
        # above; include a leading assertion/reason instruction block if this
        # question opens the referenced range on the same page.
        prev_y1 = line_top_above(pno, tk["y0"])
        top = tk["y0"] - 4.0 if prev_y1 is None else max(tk["y0"] - 4.0, prev_y1 + 0.3)
        if blk and blk[0] == pno:
            top = min(top, blk[1])
        ref_y = tk["y0"]          # events below this y bound the question
        page = pno
        guard = 0
        while True:
            guard += 1
            if guard > 6:
                break
            # bottom boundary on the current page
            nxt_tok = [t["y0"] for t in tokens_by_page[page] if t["y0"] > ref_y + 1]
            nxt_sec = [s["y0"] for s in sections_by_page[page] if s["y0"] > ref_y + 1]
            cands = nxt_tok + nxt_sec + [geom["content_bottom"] + 4.0]
            next_event = min(cands)
            # bottom: 4pt above the next event, but never clip the last line
            last_y1 = line_bottom_below(page, next_event)
            if next_event >= geom["content_bottom"] + 3.0:
                bottom = geom["content_bottom"]
            elif last_y1 is None:
                bottom = next_event - 4.0
            else:
                bottom = max(next_event - 4.0, last_y1 + 0.3)
            # trim an assertion/reason block that belongs to a later question
            bottom = trim_bottom_for_block(page, bottom, qn)
            if bottom > top + 6 and has_content(page, top, bottom):
                portions.append({
                    "page": page,
                    "rect": [geom["left"], round(top, 1), geom["right"], round(bottom, 1)],
                })
            overflow = bottom >= geom["content_bottom"] - 1.0
            if not overflow:
                break
            # The question ran to the foot of the page: examine the next
            # English page in this paper's sequence for a continuation.
            try:
                nxt_page = en_pages[en_pages.index(page) + 1]
            except IndexError:
                break
            n_toks = tokens_by_page.get(nxt_page, [])
            n_secs = sections_by_page.get(nxt_page, [])
            first_event_y = None
            first_is_section = False
            if n_secs:
                first_event_y = n_secs[0]["y0"]
                first_is_section = True
            if n_toks and (first_event_y is None or n_toks[0]["y0"] < first_event_y):
                first_event_y = n_toks[0]["y0"]
                first_is_section = False
            if first_is_section:
                break  # a new section starts; the question ended at the footer
            c_top = geom["content_top"]
            # an A/R block for a later question ends any continuation here
            blk_start = block_on_page_above(nxt_page, qn)
            if blk_start is not None:
                b_last = line_bottom_below(nxt_page, blk_start)
                c_bot = (blk_start - 4.0) if b_last is None \
                    else max(blk_start - 4.0, b_last + 0.3)
            elif first_event_y is not None:
                c_bot = first_event_y - 4.0
            else:
                c_bot = geom["content_bottom"]
            if c_bot <= c_top + 10 or not has_content(nxt_page, c_top, c_bot):
                break  # nothing that belongs to this question on the next page
            # move to the continuation page; the loop head appends the portion
            page = nxt_page
            top = c_top
            ref_y = -1e9
            continue
        if not portions:
            portions.append({
                "page": pno,
                "rect": [geom["left"], round(top, 1),
                         geom["right"], geom["content_bottom"]],
            })
        content_pages = [p["page"] for p in portions if p.get("kind") != "instruction_block"]
        questions.append({
            "paper_index": paper["paper_index"],
            "question_number": qn,
            "section": letter,
            "marks": marks,
            "start_page": pno,
            "portions": portions,
            "spans_pages": len(set(content_pages)) > 1,
        })

    # Hindi twin pages per question number
    hi_tokens = {}
    for pno in hi_pages:
        toks, _, _ = _page_events(doc[pno - 1])
        for tk in toks:
            hi_tokens.setdefault(tk["qnum"], []).append(pno)
    for q in questions:
        q["hindi_twin_pages"] = hi_tokens.get(q["question_number"], [])

    meta = {
        "english_pages": en_pages,
        "hindi_pages": hi_pages,
        "geometry": geom,
        "numbering_ok": numbering_ok,
        "detected_qnums": qnums,
    }
    return questions, meta


# ---------------------------------------------------------------------------
# Stage 4 — cropping (original visual preservation)
# ---------------------------------------------------------------------------

def crop_question(doc, question, out_dir, dpi=RENDER_DPI):
    """Render each portion of a question from the ORIGINAL source PDF page.

    Returns list of {page, rect, image (relative path), width_px, height_px}.
    The crops are pure renders of the source page — no re-typesetting.
    """
    os.makedirs(out_dir, exist_ok=True)
    pid = question["paper_index"]
    qn = question["question_number"]
    parts = []
    for i, por in enumerate(question["portions"]):
        page = doc[por["page"] - 1]
        x0, y0, x1, y1 = por["rect"]
        clip = pymupdf.Rect(x0, y0, x1, y1)
        pix = page.get_pixmap(dpi=dpi, clip=clip)  # vector render -> crisp
        fname = f"p{pid:02d}_q{qn:02d}_part{i + 1}.jpg"
        path = os.path.join(out_dir, fname)
        pix.save(path, jpg_quality=JPEG_QUALITY)
        parts.append({
            "page": por["page"],
            "rect": por["rect"],
            "image": fname,
            "width_px": pix.width,
            "height_px": pix.height,
        })
    return parts


# ---------------------------------------------------------------------------
# Stage 5 — native text extraction per question (for classification/QA)
# ---------------------------------------------------------------------------

def question_native_text(doc, question):
    """Extract the native (English) text layer content of a question region."""
    chunks = []
    for por in question["portions"]:
        page = doc[por["page"] - 1]
        x0, y0, x1, y1 = por["rect"]
        words = page.get_text("words")
        sel = [w for w in words
               if w[0] >= x0 - 2 and w[2] <= x1 + 25 and w[1] >= y0 - 2 and w[3] <= y1 + 2
               and not _HEADER_FOOTER_WORD.match(w[4])]
        sel.sort(key=lambda w: (round(w[1] / 4), w[0]))
        line, last_y = [], None
        for w in sel:
            if last_y is None or abs(w[1] - last_y) > 4:
                if line:
                    chunks.append(" ".join(line))
                line = [w[4]]
            else:
                line.append(w[4])
            last_y = w[1] if last_y is None else (w[1] if abs(w[1] - last_y) <= 4 else w[1])
        if line:
            chunks.append(" ".join(line))
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# Marks printed-evidence scan (cross-check only; section marks are primary)
# ---------------------------------------------------------------------------

_MARKS_PAT = re.compile(r"^\(?([1-5])(?:\s*[×x+]\s*[1-5])*\)?(?:\s*=\s*([1-5]))?$")


def printed_marks_evidence(doc, question, geom):
    """Scan the question region for marks printed at the right margin.

    Returns dict with any explicit total found (e.g. '3+2=5' -> 5) and the
    raw tokens seen, for QA cross-checking against the section-wise marks.
    """
    evidence = []
    for por in question["portions"]:
        page = doc[por["page"] - 1]
        x0, y0, x1, y1 = por["rect"]
        for w in page.get_text("words"):
            wx0, wy0, wx1, wy1, t = w[0], w[1], w[2], w[3], w[4]
            if wx0 > x1 - 110 and y0 - 2 <= wy0 <= y1 + 2:
                tt = t.replace(" ", "")
                if re.fullmatch(r"[1-5]", tt) or re.fullmatch(
                        r"[1-5]([×x+][1-5])+(=[1-5])?", tt) or re.fullmatch(
                        r"[1-5]×[1-5]", tt):
                    evidence.append({"page": por["page"], "y": round(wy0, 1), "text": t})
    total = None
    for ev in evidence:
        tt = ev["text"].replace(" ", "")
        m = re.search(r"=([1-5])$", tt)
        if m:
            total = int(m.group(1))
            break
    return {"tokens": evidence, "explicit_total": total}


# ---------------------------------------------------------------------------
# Orchestration helper — run detection for the whole source PDF
# ---------------------------------------------------------------------------

def run_detection(pdf_path):
    doc = pymupdf.open(pdf_path)
    papers = detect_papers(doc)
    all_questions = []
    paper_meta = []
    for paper in papers:
        questions, meta = segment_questions(doc, paper)
        for q in questions:
            q["native_text"] = question_native_text(doc, q)
            q["printed_marks"] = printed_marks_evidence(doc, q, meta["geometry"])
            q["text_hash"] = text_hash(q["native_text"])
        all_questions.extend(questions)
        paper_meta.append({
            "paper": paper,
            "meta": {k: v for k, v in meta.items()},
            "question_count": len(questions),
        })
    doc.close()
    return papers, paper_meta, all_questions


if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "26_Chemistry board papers.pdf"
    papers, paper_meta, questions = run_detection(src)
    print(f"papers detected: {len(papers)}")
    for pm in paper_meta:
        p = pm["paper"]
        print(f"  Paper {p['paper_index']}: pages {p['pdf_pages']}, "
              f"series={p['series']} set={p['set']} qp={p['qp_code']}, "
              f"questions={pm['question_count']}, numbering_ok={pm['meta']['numbering_ok']}, "
              f"geom={pm['meta']['geometry']}")
    print(f"total questions: {len(questions)}")
    spans = [q for q in questions if q["spans_pages"]]
    print(f"questions spanning pages: {len(spans)}")
    for q in spans:
        print(f"   paper {q['paper_index']} Q{q['question_number']}: pages "
              f"{[p['page'] for p in q['portions']]}")
    from collections import Counter
    print("marks distribution:", dict(sorted(Counter(q['marks'] for q in questions).items())))
