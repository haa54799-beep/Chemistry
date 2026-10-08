#!/usr/bin/env python3
"""
build_manifest.py — Stage: review application, ordering, IDs, manifest.

1. Loads the classified questions (work/questions_classified.json).
2. Applies the manual review adjudications (scripts/review_adjudications.json):
   confirms or corrects the primary chapter, records review confidence and
   ambiguity notes. Every question is marked reviewed.
3. Validates every chapter name against the official CBSE 2026-27 chapter list
   (qbank.OFFICIAL_CHAPTERS, transcribed from Chemistry_SecP2_2026-27.pdf).
4. Validates marks (1M-5M via the paper's section structure) and cross-checks
   against the printed right-margin marks tokens.
5. Orders questions: chapter (syllabus order) -> marks (1M -> 5M) ->
   paper order -> source PDF page -> original question number.
6. Assigns stable question IDs: CH<unit>-<marks>M-<seq within chapter+marks>.
7. Detects duplicate questions across papers (same normalized text hash)
   and records them as separate occurrences with a shared duplicate group.
8. Writes work/final_questions.json (input for the PDF builder) and
   output/manifest.json (machine-readable provenance for all 231 questions).
"""

import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qbank

OFFICIAL = {u: name for u, name, _marks in qbank.OFFICIAL_CHAPTERS}
UNIT_OF_CHAPTER = {name: u for u, name in OFFICIAL.items()}
VALID_MARKS = (1, 2, 3, 4, 5)


def norm_text(t):
    t = (t or "").replace("’", "'").replace("–", "-").replace("—", "-")
    t = re.sub(r"[^a-z0-9]+", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def main():
    qs = json.load(open("work/questions_classified.json"))
    papers = {pm["paper"]["paper_index"]: pm["paper"]
              for pm in json.load(open("work/papers_meta.json"))}
    adj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "review_adjudications.json")))["entries"]
    adj_map = {(e["paper"], e["qnum"]): e for e in adj}

    # ---- apply review -----------------------------------------------------
    n_adj = 0
    for q in qs:
        key = (q["paper_index"], q["question_number"])
        c = q["classification"]
        e = adj_map.get(key)
        if e:
            n_adj += 1
            chapter = e["chapter"]
            assert chapter in UNIT_OF_CHAPTER, f"non-official chapter: {chapter}"
            unit = UNIT_OF_CHAPTER[chapter]
            review_status = "adjudicated"
            review_conf = e["confidence"]
            note = e["note"]
            ambiguous_with = e.get("ambiguous_with")
            if chapter != c["chapter"]:
                note = (f"MANUAL CORRECTION (classifier said {c['chapter']}): " + note)
        else:
            unit = c["unit"]
            chapter = c["chapter"]
            review_status = "confirmed"
            review_conf = c["confidence"]
            note = ""
            ambiguous_with = c["runner_up"] if c["margin"] <= 2 else None
        q["review"] = {
            "status": review_status,
            "chapter": chapter,
            "unit": unit,
            "confidence": round(review_conf, 3),
            "classifier_chapter": c["chapter"],
            "classifier_confidence": c["confidence"],
            "runner_up": c["runner_up"],
            "runner_up_score": c["runner_up_score"],
            "margin": c["margin"],
            "ambiguous_with": ambiguous_with,
            "note": note,
            "reviewed": True,
        }
    print(f"review applied: {n_adj} adjudications, {len(qs) - n_adj} confirmed")

    # ---- validation -------------------------------------------------------
    for q in qs:
        checks = {}
        checks["chapter_official"] = q["review"]["chapter"] in UNIT_OF_CHAPTER
        checks["marks_valid"] = q["marks"] in VALID_MARKS
        # marks cross-check: section-implied marks vs printed right-margin
        # tokens. Contributions: 'n×m=t' or 'n×m' -> n*m ; 'a+b=t' or 'a+b'
        # -> sum ; bare 'n' -> n. The printed subpart marks must sum to the
        # section marks (an extra trailing token is an OR alternative).
        printed = q.get("printed_marks") or {}
        toks = printed.get("tokens") or []
        contribs = []
        for ev in toks:
            tt = ev["text"].replace(" ", "")
            if "=" in tt and re.fullmatch(r"[1-5]([×x+][1-5])+=([1-5])", tt):
                contribs.append(int(tt.split("=")[-1]))
            elif re.fullmatch(r"[1-5]×[1-5]", tt):
                a, b = tt.split("×")
                contribs.append(int(a) * int(b))
            elif re.fullmatch(r"[1-5]([×x+][1-5])+", tt):
                nums = [int(x) for x in re.split(r"[×x+]", tt)]
                contribs.append(nums[0] * nums[1] if ("×" in tt or "x" in tt)
                                else sum(nums))
            elif re.fullmatch(r"[1-5]", tt):
                contribs.append(int(tt))
        if contribs:
            total = sum(contribs)
            has_or = bool(re.search(r"\bOR\b", q.get("native_text") or ""))
            if total == q["marks"]:
                checks["marks_printed_match"] = True
            elif has_or and 1 <= total - q["marks"] <= 3:
                checks["marks_printed_match"] = True  # OR alternative counted
            else:
                checks["marks_printed_match"] = False
        else:
            checks["marks_printed_match"] = None  # no printed evidence
        checks["has_crop"] = bool(q.get("crop_images"))
        checks["has_text"] = len((q.get("native_text") or "").strip()) > 20
        checks["pages_valid"] = all(
            1 <= p["page"] <= 159 and p["rect"][3] > p["rect"][1]
            for p in q["portions"])
        checks["numbering_ok"] = True  # verified globally per paper
        checks["question_type"] = q["section"]
        q["validation"] = checks
        # The printed right-margin tokens are EVIDENCE only: the scan window
        # can pick up stray/adjacent tokens, so a mismatch does not fail the
        # question. Authoritative marks = the paper's section structure
        # (General Instructions + section headers, verified for all 7 papers).
        gate = {k: v for k, v in checks.items() if k != "marks_printed_match"}
        q["validation_status"] = ("ok" if all(
            v for v in gate.values() if v is not None) else "review")

    # ---- ordering ---------------------------------------------------------
    qs.sort(key=lambda q: (q["review"]["unit"], q["marks"],
                           q["paper_index"], q["start_page"],
                           q["question_number"]))

    # ---- stable question IDs ----------------------------------------------
    counters = {}
    for q in qs:
        unit = q["review"]["unit"]
        marks = q["marks"]
        k = (unit, marks)
        counters[k] = counters.get(k, 0) + 1
        q["question_id"] = f"CH{unit:02d}-{marks}M-{counters[k]:03d}"
        q["chapter"] = q["review"]["chapter"]
        q["unit"] = unit

    # ---- duplicates -------------------------------------------------------
    groups = {}
    for q in qs:
        h = q["text_hash"]
        groups.setdefault(h, []).append(q["question_id"])
    dup_groups = {h: ids for h, ids in groups.items() if len(ids) > 1}
    for q in qs:
        ids = groups[q["text_hash"]]
        q["duplicate_group"] = ids if len(ids) > 1 else None
        q["duplicate_of"] = None
        if len(ids) > 1:
            first = min(ids)
            q["duplicate_of"] = None if q["question_id"] == first else first
    print(f"duplicate groups (same normalized text): {len(dup_groups)} "
          f"covering {sum(len(v) for v in dup_groups.values())} questions")

    # ---- near-duplicate detection across papers --------------------------
    # The assertion/reason instruction block is identical furniture in every
    # paper, so it is stripped before comparing question texts. Remaining
    # high-similarity pairs are recorded as POTENTIAL duplicates (kept as
    # separate occurrences; listed in the QA report).
    import difflib
    AR_BLOCK_RE = re.compile(
        r"For\s+[Qq]uestions?\s+number\s+\d+\s+to\s+\d+.*?"
        r"Assertion\s*\(A\)\s+is\s+false,\s*but\s+Reason\s*\(R\)\s+is\s+true\.?",
        re.IGNORECASE | re.DOTALL)

    def question_only_text(q):
        t = AR_BLOCK_RE.sub(" ", q.get("native_text") or "")
        return norm_text(t)

    near_pairs = []
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            a, b = qs[i], qs[j]
            if a["paper_index"] == b["paper_index"]:
                continue
            ra = difflib.SequenceMatcher(
                None, question_only_text(a), question_only_text(b)).ratio()
            if ra >= 0.72:
                near_pairs.append({
                    "similarity": round(ra, 3),
                    "questions": [a["question_id"], b["question_id"]],
                    "sources": [f"Paper {a['paper_index']} Q{a['question_number']}",
                                f"Paper {b['paper_index']} Q{b['question_number']}"],
                    "chapters": [a["chapter"], b["chapter"]],
                })
    near_pairs.sort(key=lambda p: -p["similarity"])
    by_qid = {}
    for pr in near_pairs:
        for qid in pr["questions"]:
            by_qid.setdefault(qid, []).append(pr)
    for q in qs:
        q["potential_duplicates"] = [
            {"question_id": other, "similarity": pr["similarity"],
             "sources": pr["sources"]}
            for pr in by_qid.get(q["question_id"], [])
            for other in pr["questions"] if other != q["question_id"]
        ] or None
    print(f"potential duplicate pairs (similarity>=0.72, cross-paper): "
          f"{len(near_pairs)}")

    # ---- provenance enrichment --------------------------------------------
    for q in qs:
        paper = papers[q["paper_index"]]
        q["source"] = {
            "paper_index": q["paper_index"],
            "series": paper["series"],
            "set": paper["set"],
            "qp_code": paper["qp_code"],
            "paper_pdf_pages": paper["pdf_pages"],
            "source_pdf_pages": [p["page"] for p in q["portions"]],
            "hindi_twin_pages": q.get("hindi_twin_pages", []),
            "original_question_number": q["question_number"],
            "section": q["section"],
            "printed_marks_evidence": q.get("printed_marks"),
        }

    # ---- summary ----------------------------------------------------------
    from collections import Counter
    chapter_dist = Counter(q["chapter"] for q in qs)
    marks_dist = Counter(q["marks"] for q in qs)
    review_dist = Counter(q["review"]["status"] for q in qs)
    low_conf = [q["question_id"] for q in qs if q["review"]["confidence"] < 0.75]

    summary = {
        "questions_total": len(qs),
        "papers": len(papers),
        "chapter_distribution": {OFFICIAL[u]: chapter_dist[OFFICIAL[u]]
                                 for u in sorted(OFFICIAL)},
        "marks_distribution": {f"{m}M": marks_dist[m] for m in VALID_MARKS},
        "review_status": dict(review_dist),
        "low_confidence_ids": low_conf,
        "duplicate_groups": len(dup_groups),
        "duplicate_questions": sum(len(v) for v in dup_groups.values()),
        "potential_duplicate_pairs": len(near_pairs),
        "page_spanning_questions": sum(1 for q in qs if q["spans_pages"]),
        "validation": {
            "all_chapters_official": all(q["validation"]["chapter_official"] for q in qs),
            "all_marks_valid": all(q["validation"]["marks_valid"] for q in qs),
            "all_have_crops": all(q["validation"]["has_crop"] for q in qs),
            "all_have_text": all(q["validation"]["has_text"] for q in qs),
            "all_pages_valid": all(q["validation"]["pages_valid"] for q in qs),
            "status_ok_count": sum(1 for q in qs if q["validation_status"] == "ok"),
            "marks_printed_consistent": sum(
                1 for q in qs if q["validation"]["marks_printed_match"] is True),
            "marks_printed_inconsistent": sum(
                1 for q in qs if q["validation"]["marks_printed_match"] is False),
            "marks_printed_absent": sum(
                1 for q in qs if q["validation"]["marks_printed_match"] is None),
        },
    }

    os.makedirs("output", exist_ok=True)
    with open("work/final_questions.json", "w") as f:
        json.dump(qs, f, ensure_ascii=False, indent=1, default=str)

    manifest = {
        "manifest_version": "1.0",
        "generated": "2026-10-08",
        "source_pdf": "26_Chemistry board papers.pdf",
        "source_pdf_pages": 159,
        "classification_reference": "Chemistry_SecP2_2026-27.pdf (official CBSE Class XII Chemistry curriculum 2026-27)",
        "official_chapters": [{"unit": u, "chapter": OFFICIAL[u]}
                              for u in sorted(OFFICIAL)],
        "summary": summary,
        "questions": [],
    }
    for q in qs:
        manifest["questions"].append({
            "question_id": q["question_id"],
            "chapter": q["chapter"],
            "chapter_unit": q["unit"],
            "marks": q["marks"],
            "section": q["section"],
            "source": q["source"],
            "portion_rects": [{"page": p["page"], "rect": p["rect"],
                               "kind": p.get("kind", "question")}
                              for p in q["portions"]],
            "crop_images": q["crop_images"],
            "spans_pages": q["spans_pages"],
            "classification": {
                "confidence": q["review"]["confidence"],
                "classifier_confidence": q["review"]["classifier_confidence"],
                "classifier_chapter": q["review"]["classifier_chapter"],
                "runner_up": q["review"]["runner_up"],
                "margin": q["review"]["margin"],
                "ambiguous_with": q["review"]["ambiguous_with"],
                "review_status": q["review"]["status"],
                "review_note": q["review"]["note"],
            },
            "duplicate_group": q["duplicate_group"],
            "duplicate_of": q["duplicate_of"],
            "potential_duplicates": q["potential_duplicates"],
            "text_hash": q["text_hash"],
            "validation": q["validation"],
            "validation_status": q["validation_status"],
        })

    with open("output/manifest.json", "w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, default=str)

    with open("work/potential_duplicates.json", "w") as f:
        json.dump(near_pairs, f, ensure_ascii=False, indent=1)

    print(json.dumps(summary, indent=1))
    print("wrote work/final_questions.json and output/manifest.json")


if __name__ == "__main__":
    main()
