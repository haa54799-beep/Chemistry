#!/usr/bin/env python3
"""
build_pdf.py — Stage: final question-bank PDF.

Builds output/CBSE_Class_12_Chemistry_2025-26_Chapterwise_Question_Bank.pdf:

  1. Cover page
  2. Clickable table of contents (visible links + PDF outline/bookmarks)
  3. Master index (every question: ID, chapter, marks, source, page in this PDF)
  4. Chapter sections (each chapter starts on a new divider page)
  5. Marks subsections 1M -> 5M (each starts on a new page)
  6. Questions in original paper/page order within each marks group, each
     shown as the original-page crop image(s) (never re-typeset) with a small
     unobtrusive source label: "Source: Paper X (SET Y) | PDF p. N | Q. n"
  7. Footer page numbers on every content page

Crops are embedded as the original JPEG files (no recompression).
A4 portrait. Layout is deterministic; the master index and TOC links are
filled after the chapter pages are laid out (single assembly pass).
"""

import json
import os
import sys

import pymupdf
from PIL import Image

A4_W, A4_H = 595.32, 841.92
ML, MR, MT, MB = 42.0, 42.0, 46.0, 54.0
CW = A4_W - ML - MR                 # content width 511.32
TOP = MT
BOTTOM = A4_H - MB                  # 787.92
MAX_IMG_H = 650.0                   # max displayed height of one portion
Q_GAP = 18.0                        # gap between question blocks
IMG_GAP = 6.0                       # gap between portions of one question
HDR_H = 16.0                        # question header line height

def S(t):
    """Sanitize text for the base-14 fonts (WinAnsi): PyMuPDF mangles
    en/em dashes, arrows and bullets otherwise."""
    return (t.replace("\u2013", "-").replace("\u2014", "-")
             .replace("\u2192", "->").replace("\u2022", "\u00b7")
             .replace("\u2019", "'").replace("\u2018", "'")
             .replace("\u201c", '"').replace("\u201d", '"'))


GRAY = (0.42, 0.42, 0.42)
LGRAY = (0.60, 0.60, 0.60)
DARK = (0.13, 0.13, 0.13)
RULE = (0.78, 0.78, 0.78)
ACCENT = (0.10, 0.25, 0.45)

SHORT_CHAPTER = {
    "Solutions": "Solutions",
    "Electrochemistry": "Electrochemistry",
    "Chemical Kinetics": "Kinetics",
    "d and f Block Elements": "d & f Block",
    "Coordination Compounds": "Coordination",
    "Haloalkanes and Haloarenes": "Haloalkanes",
    "Alcohols, Phenols and Ethers": "Alcohols/Phenols",
    "Aldehydes, Ketones and Carboxylic Acids": "Ald/Ketones/Acids",
    "Amines": "Amines",
    "Biomolecules": "Biomolecules",
}

OUT_PDF = "output/CBSE_Class_12_Chemistry_2025-26_Chapterwise_Question_Bank.pdf"
CROPS = "work/crops"


class Builder:
    def __init__(self, questions, papers):
        self.qs = questions
        self.papers = papers
        self.doc = pymupdf.open()
        self.page = None
        self.y = TOP
        self.toc = []            # [level, title, page] for set_toc
        self.toc_links = []      # (page_no, rect, target_page)
        self.q_pages = {}        # question_id -> 1-based page in this PDF
        self.ch_pages = {}       # unit -> page
        self.sub_pages = {}      # (unit, marks) -> page
        self.index_rows = []     # dicts for the master index
        self.n_pages_index = 0

    # ---------------- low-level helpers -----------------------------------
    def new_page(self, footer=True):
        self.page = self.doc.new_page(width=A4_W, height=A4_H)
        self.y = TOP
        if footer:
            pn = self.page.number + 1
            fs = f"Page {pn}"
            w = pymupdf.get_text_length(fs, fontname="helv", fontsize=7.5)
            self.page.insert_text(((A4_W - w) / 2, A4_H - 24), fs,
                                  fontname="helv", fontsize=7.5, color=LGRAY)
        return self.page

    def text(self, x, y, s, size=9, bold=False, color=GRAY):
        s = S(s)
        self.page.insert_text((x, y), s,
                              fontname="hebo" if bold else "helv",
                              fontsize=size, color=color)

    def text_right(self, x_right, y, s, size=9, bold=False, color=GRAY):
        s = S(s)
        w = pymupdf.get_text_length(s, fontname="hebo" if bold else "helv",
                                     fontsize=size)
        self.page.insert_text((x_right - w, y),
                              s, fontname="hebo" if bold else "helv",
                              fontsize=size, color=color)

    def hline(self, y, x0=ML, x1=A4_W - MR, color=RULE, width=0.6):
        self.page.draw_line((x0, y), (x1, y), color=color, width=width)

    # ---------------- cover ------------------------------------------------
    def cover(self):
        self.new_page(footer=False)
        cx = A4_W / 2
        self.text_right(cx + 130, 118, "CBSE CLASS 12  •  CHEMISTRY",
                        size=11, bold=True, color=ACCENT)
        r = pymupdf.Rect(ML, 138, A4_W - MR, 208)
        self.page.insert_textbox(r, S("Chapter-wise Question Bank"),
                                 fontname="hebo", fontsize=30, color=DARK,
                                 align=pymupdf.TEXT_ALIGN_CENTER)
        r = pymupdf.Rect(ML, 212, A4_W - MR, 248)
        self.page.insert_textbox(r, S("2025–26 Board Examination Papers"),
                                 fontname="helv", fontsize=14, color=GRAY,
                                 align=pymupdf.TEXT_ALIGN_CENTER)
        self.hline(268, cx - 90, cx + 90, color=ACCENT, width=1.2)
        lines = [
            ("Compiled from", "26_Chemistry board papers.pdf  (159 pages, 7 board papers)"),
            ("Classification ref.", "Chemistry_SecP2_2026-27.pdf  (official CBSE 2026–27 curriculum)"),
            ("Contents", "231 questions  •  10 chapters  •  by chapter, then marks 1M → 5M"),
            ("Fidelity", "Every question is a crop of the original paper page (never re-typeset)"),
            ("Generated", "2026-10-08  •  reproducible pipeline in scripts/"),
        ]
        y = 308
        for k, v in lines:
            self.text(ML + 30, y, k, size=9.5, bold=True, color=ACCENT)
            self.text(ML + 185, y, v, size=9.5, color=GRAY)
            y += 22
        # chapter stats table
        y += 16
        self.text(ML + 30, y, "Chapter distribution", size=10, bold=True, color=DARK)
        y += 20
        from collections import Counter
        dist = Counter(q["chapter"] for q in self.qs)
        items = [(u, q0["chapter"], dist[q0["chapter"]])
                 for u, q0 in sorted({q["unit"]: q for q in self.qs}.items())]
        col_x = [ML + 30, ML + 285]
        for i, (u, name, n) in enumerate(items):
            x = col_x[i % 2]
            yy = y + (i // 2) * 17
            self.text(x, yy, f"Ch {u}", size=8.5, bold=True, color=ACCENT)
            self.text(x + 32, yy, SHORT_CHAPTER[name], size=8.5, color=GRAY)
            self.text_right(x + 215, yy, f"{n} questions", size=8.5, color=GRAY)
        y_end = y + ((len(items) + 1) // 2) * 17 + 30
        r = pymupdf.Rect(ML, y_end, A4_W - MR, y_end + 60)
        self.page.insert_textbox(
            r, S("Master index and clickable table of contents follow. "
                 "Each question carries a small source label: "
                 "\"Source: Paper X (SET Y) | PDF p. N | Q. n\"."),
            fontname="helv", fontsize=8.5, color=LGRAY,
            align=pymupdf.TEXT_ALIGN_CENTER)
        self.toc.append([1, "Cover", 1])

    # ---------------- TOC ---------------------------------------------------
    def toc_pages(self):
        self.new_page()
        self.text(ML, TOP + 6, "Table of Contents", size=16, bold=True, color=DARK)
        self.hline(TOP + 16)
        self.y = TOP + 40
        self._toc_line(0, "Master Index", None, bold=True)
        for u in sorted({q["unit"] for q in self.qs}):
            chap = next(q["chapter"] for q in self.qs if q["unit"] == u)
            n = sum(1 for q in self.qs if q["unit"] == u)
            self._toc_line(0, f"Chapter {u}  —  {chap}", ("chapter", u),
                           bold=True, count=n)
            for m in (1, 2, 3, 4, 5):
                c = sum(1 for q in self.qs
                        if q["unit"] == u and q["marks"] == m)
                if c:
                    self._toc_line(1, f"{m} Mark" + ("s" if m > 1 else "")
                                   + f"  ({c} question" + ("s" if c > 1 else "") + ")",
                                   ("sub", u, m))
        self.toc.append([1, "Table of Contents", 2])

    def _toc_line(self, level, label, target, bold=False, count=None):
        if self.y > BOTTOM - 10:
            self.new_page()
        x = ML + 14 * level
        size = 10 if level == 0 else 9
        s = ("    " * level) + label
        if count is not None:
            s += f"   —   {count} questions"
        self.text(x, self.y, s, size=size, bold=bold,
                  color=DARK if bold else GRAY)
        r = pymupdf.Rect(x, self.y - size - 1, A4_W - MR, self.y + 3)
        if target is not None:
            self.toc_links.append((self.page.number + 1, r, target))
        self.y += 16.5

    # ---------------- master index -----------------------------------------
    def index_pages(self):
        rows_per_page = int((BOTTOM - TOP - 34) // 14.5)
        n_pages = max(1, -(-len(self.qs) // rows_per_page))
        self.n_pages_index = n_pages
        self.index_start = self.doc.page_count + 1
        for i in range(n_pages):
            self.new_page()
            if i == 0:
                self.text(ML, TOP + 6, "Master Index", size=16, bold=True,
                          color=DARK)
                self.text_right(A4_W - MR, TOP + 6,
                                f"{len(self.qs)} questions", size=9,
                                color=LGRAY)
                self.hline(TOP + 16)
                # column headers
                y = TOP + 30
                for x, h, al in [(ML, "Question ID", 0),
                                 (ML + 82, "Chapter", 0),
                                 (ML + 218, "Marks", 0),
                                 (ML + 252, "Source", 0),
                                 (ML + 468, "Page", 1)]:
                    if al:
                        self.text_right(x + 40, y, h, size=7.5, bold=True,
                                        color=LGRAY)
                    else:
                        self.text(x, y, h, size=7.5, bold=True, color=LGRAY)
                self.hline(y + 4, color=(0.6, 0.6, 0.6), width=0.8)
                self.y = y + 18
            else:
                self.y = TOP
        self.toc.append([1, "Master Index", self.index_start])

    def fill_index(self):
        rows_per_page = int((BOTTOM - TOP - 34) // 14.5)
        for i, row in enumerate(self.index_rows):
            pno = self.index_start + i // rows_per_page
            page = self.doc[pno - 1]
            y = (TOP + 48 + (i % rows_per_page) * 14.5) if i // rows_per_page == 0 \
                else (TOP + (i % rows_per_page) * 14.5)
            page.insert_text((ML, y), row["qid"], fontname="hebo", fontsize=7.5,
                             color=DARK)
            page.insert_text((ML + 82, y), row["chapter"], fontname="helv",
                             fontsize=7.5, color=GRAY)
            page.insert_text((ML + 218, y), f"{row['marks']}M",
                             fontname="helv", fontsize=7.5, color=GRAY)
            page.insert_text((ML + 252, y), row["source"], fontname="helv",
                             fontsize=7.5, color=GRAY)
            w = pymupdf.get_text_length(str(row["page"]), fontname="helv",
                                         fontsize=7.5)
            page.insert_text((ML + 508 - w, y), str(row["page"]),
                             fontname="helv", fontsize=7.5, color=ACCENT)
            page.draw_line((ML, y + 3.5), (A4_W - MR, y + 3.5),
                           color=(0.93, 0.93, 0.93), width=0.3)

    # ---------------- chapters ---------------------------------------------
    def build_chapters(self):
        by_unit = {}
        for q in self.qs:
            by_unit.setdefault(q["unit"], []).append(q)
        for u in sorted(by_unit):
            qs_u = by_unit[u]
            chap = qs_u[0]["chapter"]
            self.chapter_divider(u, chap, qs_u)
            for m in (1, 2, 3, 4, 5):
                qs_m = [q for q in qs_u if q["marks"] == m]
                if not qs_m:
                    continue
                self.marks_section(u, m, qs_m)

    def chapter_divider(self, u, chap, qs_u):
        self.new_page()
        self.ch_pages[u] = self.page.number + 1
        self.toc.append([1, f"Chapter {u}: {chap}", self.ch_pages[u]])
        y = TOP + 60
        self.text(ML, y, f"CHAPTER {u}", size=12, bold=True, color=ACCENT)
        y += 34
        self.page.insert_textbox(pymupdf.Rect(ML, y, A4_W - MR, y + 40),
                                 S(chap), fontname="hebo", fontsize=24,
                                 color=DARK)
        y += 48
        self.hline(y, color=ACCENT, width=1.2)
        y += 26
        self.text(ML, y, f"Unit {u} of the official CBSE Class XII Chemistry "
                        f"curriculum (2026–27)", size=9.5, color=GRAY)
        y += 24
        from collections import Counter
        mc = Counter(q["marks"] for q in qs_u)
        s = "   ".join(f"{m}M: {mc[m]}" for m in (1, 2, 3, 4, 5) if mc[m])
        self.text(ML, y, f"{len(qs_u)} questions   •   {s}", size=10.5,
                  bold=True, color=DARK)
        y += 18
        self.text(ML, y, "Questions are ordered by marks (1M → 5M) and, within "
                        "the same marks, by original paper and page order.",
                  size=8.5, color=LGRAY)
        y += 30
        self.hline(y)
        y += 18
        self.text(ML, y, "Question ID format:  CH<unit>-<marks>M-<sequence>",
                  size=8, color=LGRAY)
        # mini list of the chapter's questions
        y += 22
        self.text(ML, y, "Questions in this chapter:", size=9, bold=True,
                  color=DARK)
        y += 16
        for q in qs_u:
            if y > BOTTOM - 8:
                self.new_page()
            src = self.source_label(q)
            self.text(ML, y, q["question_id"], size=8, bold=True, color=ACCENT)
            self.text(ML + 82, y, SHORT_CHAPTER[q["chapter"]], size=8,
                      color=GRAY)
            self.text(ML + 218, y, f"{q['marks']}M", size=8, color=GRAY)
            self.text(ML + 252, y, src, size=8, color=GRAY)
            self.q_pages[q["question_id"]] = None  # filled in marks section
            y += 13.5

    def marks_section(self, u, m, qs_m):
        self.new_page()
        self.sub_pages[(u, m)] = self.page.number + 1
        self.toc.append([2, f"Chapter {u} — {m} Mark" + ("s" if m > 1 else ""),
                         self.sub_pages[(u, m)]])
        self.text(ML, TOP + 8, f"{m} Mark" + ("s" if m > 1 else "") + " Questions",
                  size=14, bold=True, color=DARK)
        self.text_right(A4_W - MR, TOP + 8,
                        f"{len(qs_m)} question" + ("s" if len(qs_m) > 1 else ""),
                        size=9, color=LGRAY)
        self.hline(TOP + 18, color=ACCENT, width=1.0)
        self.y = TOP + 34
        for q in qs_m:
            self.question_block(q)

    # ---------------- question block ----------------------------------------
    def source_label(self, q):
        pages = [str(p["page"]) for p in q["portions"]]
        pp = ("p. " + pages[0]) if len(pages) == 1 else ("pp. " + ", ".join(pages))
        paper = self.papers[q["paper_index"]]
        return (f"Source: Paper {q['paper_index']} (SET {paper['set']}) "
                f"| PDF {pp} | Q. {q['question_number']}")

    def question_block(self, q):
        pno = self.page.number + 1
        self.q_pages[q["question_id"]] = pno
        # header line
        if self.y + HDR_H > BOTTOM:
            self.new_page()
            pno = self.page.number + 1
            self.q_pages[q["question_id"]] = pno
        self.text(ML, self.y, q["question_id"], size=7.5, bold=True,
                  color=ACCENT)
        self.text_right(A4_W - MR, self.y, self.source_label(q), size=7,
                        color=LGRAY)
        self.y += HDR_H
        # portion images
        for img in q["crop_images"]:
            path = os.path.join(CROPS, img)
            with Image.open(path) as im:
                w, h = im.size
            scale = min(CW / w, MAX_IMG_H / h)
            dw, dh = w * scale, h * scale
            if self.y + dh > BOTTOM:
                self.new_page()
            x = ML + (CW - dw) / 2
            self.page.insert_image(pymupdf.Rect(x, self.y, x + dw, self.y + dh),
                                   filename=path)
            self.y += dh + IMG_GAP
        self.y += Q_GAP - IMG_GAP

    # ---------------- assembly ----------------------------------------------
    def build(self):
        self.cover()
        self.toc_pages()
        self.index_pages()
        self.build_chapters()
        # fill master index rows
        for q in self.qs:
            paper = self.papers[q["paper_index"]]
            self.index_rows.append({
                "qid": q["question_id"],
                "chapter": SHORT_CHAPTER[q["chapter"]],
                "marks": q["marks"],
                "source": (f"P{q['paper_index']} SET {paper['set']} | "
                           f"PDF p. {q['start_page']} | Q. {q['question_number']}"),
                "page": self.q_pages[q["question_id"]],
            })
        self.fill_index()
        # TOC links (visible page) — resolve targets now
        for pno, rect, target in self.toc_links:
            tp = None
            if target[0] == "chapter":
                tp = self.ch_pages[target[1]]
            elif target[0] == "sub":
                tp = self.sub_pages[(target[1], target[2])]
            elif target[0] == "index":
                tp = self.index_start
            if tp:
                self.doc[pno - 1].insert_link(
                    {"kind": pymupdf.LINK_GOTO, "from": rect,
                     "page": tp - 1, "to": pymupdf.Point(0, 0)})
        # PDF outline (bookmarks)
        self.doc.set_toc(self.toc)
        os.makedirs("output", exist_ok=True)
        self.doc.save(OUT_PDF, deflate=True, garbage=3)
        self.doc.close()
        return OUT_PDF


def main():
    qs = json.load(open("work/final_questions.json"))
    papers = {pm["paper"]["paper_index"]: pm["paper"]
              for pm in json.load(open("work/papers_meta.json"))}
    b = Builder(qs, papers)
    out = b.build()
    print("wrote", out)
    d = pymupdf.open(out)
    print("pages:", d.page_count, "| size MB:",
          round(os.path.getsize(out) / 1e6, 1))
    print("toc entries:", len(d.get_toc()))
    d.close()


if __name__ == "__main__":
    main()
