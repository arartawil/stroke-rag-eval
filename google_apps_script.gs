/**
 * google_apps_script.gs
 * ======================
 * Receives evaluation submissions from the index.html app and appends
 * each rating as a row in a Google Sheet.
 *
 * SETUP (one time, ~5 minutes):
 * ------------------------------
 * 1. Go to https://sheets.google.com → create a new blank Spreadsheet.
 *    Name it: "Stroke Rehab RAG Evaluation Ratings"
 * 2. Click Extensions → Apps Script.
 * 3. Delete the default code, paste THIS file's contents.
 * 4. Click the "Save" disk icon (Ctrl+S). Name the project: "Stroke RAG Eval".
 * 5. Click "Deploy" (top right) → "New deployment".
 * 6. Click the gear icon next to "Select type" → choose "Web app".
 * 7. Settings:
 *      Description: Stroke RAG Eval Submitter
 *      Execute as:  Me (your_email@gmail.com)
 *      Who has access: Anyone     ← must be "Anyone"
 * 8. Click "Deploy". Authorize when prompted.
 * 9. Copy the "Web app URL" — it looks like:
 *      https://script.google.com/macros/s/AKfycbxxxxxxxxxx/exec
 * 10. Open index.html and replace PASTE_YOUR_APPS_SCRIPT_URL_HERE with that URL.
 */

function doPost(e) {
  try {
    const sheet = getOrCreateSheet();
    const payload = JSON.parse(e.postData.contents);

    const submitTime = payload.submitTime || new Date().toISOString();
    const startTime = payload.startTime || "";
    const doc = payload.doctor || {};
    const ratings = payload.ratings || [];

    const rows = ratings.map(r => [
      submitTime,
      startTime,
      doc.name || "",
      doc.email || "",
      doc.specialty || "",
      doc.experience || "",
      r.question_id || "",
      r.topic || "",
      r.difficulty || "",
      r.session_history || "",
      r.system_letter || "",
      r.system_actual || "",
      r.accuracy || "",
      r.completeness || "",
      r.citations || "",
      r.safety || "",
      r.image_quality || "",
      r.comment || "",
    ]);

    if (rows.length > 0) {
      sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, rows[0].length)
           .setValues(rows);
    }

    return ContentService
      .createTextOutput(JSON.stringify({ ok: true, count: rows.length }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService
    .createTextOutput("Stroke RAG Eval submission endpoint is alive.")
    .setMimeType(ContentService.MimeType.TEXT);
}

function getOrCreateSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName("Ratings");
  if (!sheet) {
    sheet = ss.insertSheet("Ratings");
    const headers = [
      "submit_time", "start_time", "doctor_name", "doctor_email",
      "specialty", "experience_years",
      "question_id", "topic", "difficulty", "session_history",
      "system_letter", "system_actual",
      "accuracy", "completeness", "citations", "safety", "image_quality",
      "comment",
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length)
         .setFontWeight("bold")
         .setBackground("#6b21a8")
         .setFontColor("white");
    sheet.setFrozenRows(1);
    sheet.autoResizeColumns(1, headers.length);
  }
  return sheet;
}
