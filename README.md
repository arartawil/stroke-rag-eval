# Stroke Rehabilitation RAG Evaluation App

A single-file web app for clinicians to rate AI-generated answers
from the Stroke Rehabilitation RAG study. No backend needed — ratings flow
into a Google Sheet via Google Apps Script, with CSV download as backup.

## Files

| File | Purpose |
|---|---|
| `index.html` | The evaluation web app (single file, no build step) |
| `experiment_results.json` | Generated from batch results by `convert_results.py` |
| `convert_results.py` | Converts `results/batch_*_results.json` into the app's format |
| `google_apps_script.gs` | Apps Script for the Google Sheet backend |
| `images/` | Generated exercise illustrations (copied by convert script) |

## Quick Start

### 1. Generate `experiment_results.json` and copy images

```bash
cd "c:/Users/ROG SRTIX/Desktop/RAG"
python evaluation_app/convert_results.py
```

This reads `results/batch_*_results.json` and produces:
- `evaluation_app/experiment_results.json`
- `evaluation_app/images/plain_llm_Q001.png` etc.

### 2. Serve the folder locally

```bash
python -m http.server 8080
```

Then open: **http://localhost:8080/evaluation_app/**

You can fill it in immediately — ratings save in browser localStorage.
The "Submit" button needs the Google Apps Script URL (see setup below).

## Setting up the Google Sheet (one time, ~5 minutes)

### 1. Create a Google Sheet
- https://sheets.google.com → **Blank**
- Rename to **"Stroke Rehab RAG Evaluation Ratings"**

### 2. Add the Apps Script
- In the Sheet → **Extensions → Apps Script**
- Delete the default code
- Paste ALL contents of `google_apps_script.gs`
- **Save** (Ctrl+S), name the project **"Stroke RAG Eval"**

### 3. Deploy as Web App
- **Deploy → New deployment**
- Gear icon → **Web app**
- **Execute as:** Me
- **Who has access:** Anyone (required)
- **Deploy** → authorize
- Copy the Web app URL

### 4. Wire it into the HTML
Open `index.html`, find:
```javascript
const APPS_SCRIPT_URL = "PASTE_YOUR_APPS_SCRIPT_URL_HERE";
```
Replace with your URL.

### 5. Test it
- Open the app, fill in name + email → Start
- Rate one question → Submit at the end
- Check your Google Sheet "Ratings" tab

## Rating Dimensions

Each clinician rates each of 3 AI-generated answers on 5 dimensions (1–5 stars):

| Dimension | What it measures |
|---|---|
| **Accuracy** | Factual correctness vs guidelines |
| **Completeness** | Coverage of relevant aspects |
| **Citation quality** | Source/page references |
| **Clinical safety** | Safe for this patient? |
| **Image quality** | Does the illustration match the recommendation? |

Systems are blinded as **A / B / C** (random order per question) so the clinician
never knows which was Plain LLM, Basic RAG, or CARE-RAG.

## Hosting for Remote Clinicians

### Option A: GitHub Pages
1. Push `evaluation_app/` folder to a public repo
2. Settings → Pages → deploy from `main` branch
3. Send the URL

### Option B: Netlify Drop
1. https://app.netlify.com/drop
2. Drag the `evaluation_app/` folder
3. Share the generated URL

## Data Flow

```
batch_1_results.json         (from run_batch_experiment.py)
      │
      ▼ convert_results.py
evaluation_app/experiment_results.json  +  evaluation_app/images/*.png
      │
      ▼ fetch()
index.html  ──POST──►  Google Apps Script  ──appendRow──►  Google Sheet
   (clinician's browser)
```

## Privacy

- Clinician names/emails saved in: browser localStorage + your Google Sheet only
- No third-party analytics or tracking
- Images contain no patient identifiers (they're AI-generated illustrations)

## Customizing

To change rating dimensions, edit at the top of `index.html`:
```javascript
const RATING_DIMENSIONS = ["accuracy", "completeness", "citations", "safety", "image_quality"];
const RATING_LABELS = { ... };
```
