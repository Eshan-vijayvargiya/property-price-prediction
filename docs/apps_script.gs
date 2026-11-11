// Property Price Lab: sign-ins -> this Google Sheet, and this Google Sheet -> your Excel file.
// Paste the whole file into Extensions -> Apps Script, change KEY, Save, then deploy (see SIGNIN_SETUP.md).

// Your private password for reading the sheet from Excel. Make it long; never put it on GitHub.
const KEY = "change-me-to-a-long-secret-word";

// Text that starts with = + - @ could run as a formula in a spreadsheet, so it is stored as plain text.
// The leading ' also keeps +91 numbers and the time as text instead of being turned into numbers or dates.
function asText(v) {
  return "'" + String(v === undefined || v === null ? "" : v);
}

// The app sends each sign-in here (POST).
function doPost(e) {
  const d = JSON.parse(e.postData.contents);
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  sheet.appendRow([asText(d.time), asText(d.name), asText(d.mobile || d.contact), asText(d.email), asText(d.app)]);
  return ContentService.createTextOutput("ok");
}

// Excel reads every sign-in from here (GET with ?key=...).
function doGet(e) {
  const out = (obj) => ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
  if (!e || !e.parameter || e.parameter.key !== KEY) {
    return out({ error: "wrong or missing key" });
  }
  const values = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0].getDataRange().getDisplayValues();
  const head = values.shift().map((h) => String(h).trim().toLowerCase());
  const rows = values
    .filter((r) => r.some((c) => c !== ""))
    .map((r) => Object.fromEntries(head.map((h, i) => [h, r[i]])));
  return out(rows);
}
