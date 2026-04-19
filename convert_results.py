"""
Convert batch_N_results.json files into the evaluation_app format.
Also copies images into evaluation_app/images/ so the web app can display them.

Usage:
    python evaluation_app/convert_results.py

Reads:
    results/batch_1_results.json  (and any other batch_*_results.json files)

Writes:
    evaluation_app/experiment_results.json
    evaluation_app/images/{system}_{qid}.png
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


def copy_image(src_path: str | None, qid: str, system: str) -> str | None:
    """Copy an image to evaluation_app/images/ and return the relative web path."""
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


def convert_row(r: dict) -> dict:
    """Convert one batch row into the evaluation app format."""
    qid = r["question_id"]
    out = {
        "question_id": qid,
        "question": r["question"],
        "expected_answer": r["expected_answer"],
        "topic": r["topic"],
        "difficulty": r.get("difficulty", ""),
        "session_history": r.get("session_history", ""),
    }

    for sys_key in ("plain_llm", "basic_rag", "care_rag"):
        sys_data = r.get(sys_key, {})
        answer = sys_data.get("answer", "") or ""
        img_src = sys_data.get("image_path")
        img_web = copy_image(img_src, qid, sys_key)
        out[sys_key] = {
            "answer": answer,
            "image_path": img_web,
            "answer_length": sys_data.get("answer_length", len(answer)),
            "response_time": sys_data.get("response_time", 0),
        }
        if sys_key == "care_rag":
            out[sys_key]["routing_strategy"] = sys_data.get("routing_strategy")
            out[sys_key]["safety_level"] = sys_data.get("safety_level")
    return out


def main():
    if not os.path.isdir(RESULTS_DIR):
        print(f"Error: {RESULTS_DIR}/ folder not found.")
        sys.exit(1)

    batch_files = sorted(glob.glob(os.path.join(RESULTS_DIR, "batch_*_results.json")))
    if not batch_files:
        print(f"No batch_*_results.json files found in {RESULTS_DIR}/")
        sys.exit(1)

    print(f"Found {len(batch_files)} batch file(s):")
    all_rows = []
    for bf in batch_files:
        print(f"  Loading {bf}...")
        with open(bf) as f:
            data = json.load(f)
        for r in data.get("results", []):
            all_rows.append(r)

    print(f"\nConverting {len(all_rows)} questions...")
    converted = [convert_row(r) for r in all_rows]

    output = {
        "metadata": {
            "total_questions": len(converted),
            "study": "Stroke Rehabilitation RAG Evaluation",
            "guidelines": ["AHA/ASA 2016", "NCGS 2023 UK"],
            "systems_compared": ["plain_llm", "basic_rag", "care_rag"],
        },
        "results": converted,
    }

    os.makedirs(APP_DIR, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    img_count = sum(
        1 for r in converted for s in ("plain_llm", "basic_rag", "care_rag")
        if r[s].get("image_path")
    )

    print(f"\n  Questions: {len(converted)}")
    print(f"  Images copied: {img_count}")
    print(f"  Output: {OUTPUT_JSON}")
    print(f"  Images folder: {IMAGES_OUT}")
    print("\nNext: open evaluation_app/index.html in a browser")
    print("  (or run: python -m http.server 8080  then visit http://localhost:8080/evaluation_app/)")


if __name__ == "__main__":
    main()
