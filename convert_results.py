"""
Convert all batch result files into the evaluation_app format.
Handles BOTH formats:
  - Old combined:  results/batch_{N}_results.json        (all 3 systems in one file)
  - New split:     results/batch_{N}_{system}_only.json  (one file per system)

Copies images into evaluation_app/images/ so the web app can display them.

Usage:
    python evaluation_app/convert_results.py
"""

import os
import sys
import json
import glob
import shutil

RESULTS_DIR = "results"
APP_DIR = "evaluation_app"
IMAGES_OUT = os.path.join(APP_DIR, "images")
OUTPUT_JSON = os.path.join(APP_DIR, "experiment_results.json")

SYSTEMS = ("plain_llm", "basic_rag", "care_rag")

# Prefer the most recent / best version when duplicates exist.
COMBINED_PREFERENCE = {
    1: ["batch_1_results_v3.json", "batch_1_results.json"],
    2: ["batch_2_results.json"],
    3: ["batch_3_results.json"],
    4: ["batch_4_results.json"],
    5: ["batch_5_results.json"],
}


def copy_image(src_path: str | None, qid: str, system: str) -> str | None:
    if not src_path or not os.path.exists(src_path):
        return None
    os.makedirs(IMAGES_OUT, exist_ok=True)
    ext = os.path.splitext(src_path)[1] or ".png"
    dest_name = f"{system}_{qid}{ext}"
    dest_path = os.path.join(IMAGES_OUT, dest_name)
    try:
        shutil.copy2(src_path, dest_path)
        return f"./images/{dest_name}"
    except Exception as e:
        print(f"  Could not copy {src_path}: {e}")
        return None


def build_question_entry(r: dict) -> dict:
    return {
        "question_id":     r.get("question_id"),
        "question":        r.get("question", ""),
        "expected_answer": r.get("expected_answer", ""),
        "topic":           r.get("topic", ""),
        "difficulty":      r.get("difficulty", ""),
        "session_history": r.get("session_history", ""),
        "plain_llm":       None,
        "basic_rag":       None,
        "care_rag":        None,
    }


def attach_system(entry: dict, sys_key: str, sys_data: dict):
    answer = sys_data.get("answer", "") or ""
    img_src = sys_data.get("image_path")
    img_web = copy_image(img_src, entry["question_id"], sys_key)
    block = {
        "answer":        answer,
        "image_path":    img_web,
        "answer_length": sys_data.get("answer_length", len(answer)),
        "response_time": sys_data.get("response_time", 0),
    }
    if sys_key == "care_rag":
        block["routing_strategy"] = sys_data.get("routing_strategy")
        block["safety_level"] = sys_data.get("safety_level")
    entry[sys_key] = block


def ingest_combined(path: str, by_qid: dict) -> int:
    """A combined file holds plain_llm + basic_rag + care_rag per row."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("results", [])
    added = 0
    for r in rows:
        if "error" in r:
            continue
        qid = r.get("question_id")
        if not qid:
            continue
        if qid not in by_qid:
            by_qid[qid] = build_question_entry(r)
            added += 1
        for sk in SYSTEMS:
            sd = r.get(sk) or {}
            if sd.get("answer") and by_qid[qid][sk] is None:
                attach_system(by_qid[qid], sk, sd)
    return added


def ingest_split(path: str, sys_key: str, by_qid: dict) -> int:
    """A split file holds only one system per row."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("results", [])
    added = 0
    for r in rows:
        if "error" in r:
            continue
        qid = r.get("question_id")
        if not qid:
            continue
        if qid not in by_qid:
            by_qid[qid] = build_question_entry(r)
            added += 1
        sd = r.get(sys_key) or {}
        if sd.get("answer") and by_qid[qid][sys_key] is None:
            attach_system(by_qid[qid], sys_key, sd)
    return added


def main():
    if not os.path.isdir(RESULTS_DIR):
        print(f"Error: {RESULTS_DIR}/ folder not found.")
        sys.exit(1)

    by_qid: dict = {}

    print("=" * 64)
    print("  CONVERTING BATCH RESULTS -> evaluation_app")
    print("=" * 64)

    for batch in sorted(COMBINED_PREFERENCE):
        # 1. Prefer a combined file for this batch (old format)
        combined = None
        for cand in COMBINED_PREFERENCE[batch]:
            p = os.path.join(RESULTS_DIR, cand)
            if os.path.exists(p):
                combined = p
                break
        if combined:
            n = ingest_combined(combined, by_qid)
            print(f"  Batch {batch}: combined file ({os.path.basename(combined)})  +{n} questions")
            continue

        # 2. Otherwise, ingest one split file per system (new format)
        found_any = False
        for sk in SYSTEMS:
            p = os.path.join(RESULTS_DIR, f"batch_{batch}_{sk}_only.json")
            if not os.path.exists(p):
                continue
            found_any = True
            n = ingest_split(p, sk, by_qid)
            print(f"  Batch {batch}: split {sk}  ({os.path.basename(p)})  +{n} new questions")
        if not found_any:
            print(f"  Batch {batch}: NO RESULT FILES FOUND, skipping")

    questions = sorted(by_qid.values(),
                       key=lambda r: int(r["question_id"].replace("Q", "")))

    # Fill any systems that never got attached with empty placeholders
    for r in questions:
        for sk in SYSTEMS:
            if r[sk] is None:
                r[sk] = {"answer": "", "image_path": None,
                         "answer_length": 0, "response_time": 0}

    # Count images
    img_count = sum(
        1 for r in questions for sk in SYSTEMS if r[sk].get("image_path")
    )

    output = {
        "metadata": {
            "total_questions": len(questions),
            "study": "Stroke Rehabilitation RAG Evaluation",
            "guidelines": [
                "AHA/ASA 2016", "NCGS 2023 UK",
                "ESO 2025 Motor", "AusStrokeFoundation 2025", "NICE NG236 2023",
            ],
            "systems_compared": list(SYSTEMS),
        },
        "results": questions,
    }

    os.makedirs(APP_DIR, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    print()
    print("=" * 64)
    print(f"  Questions: {len(questions)}")
    print(f"  Images copied: {img_count}")
    print(f"  Output: {OUTPUT_JSON}")
    print(f"  Images folder: {IMAGES_OUT}")
    print("=" * 64)
    print("\nNext: open evaluation_app/index.html in a browser")
    print("  (or run: python -m http.server 8080  then visit")
    print("   http://localhost:8080/evaluation_app/)")


if __name__ == "__main__":
    main()
