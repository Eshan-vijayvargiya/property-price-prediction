# Saving sign-ins to a private Google Sheet

The app's front page asks for a name and a mobile number or email (or "Skip for now").
Streamlit Community Cloud forgets files when the app restarts, so sign-ins are sent to a Google
Sheet that only you can see. Without this setup the sign-in page still works; it just saves nothing.

## 1. Make the sheet

1. Open [sheets.new](https://sheets.new) and name it `Property Price Lab visitors`.
2. Type these headers in row 1: `time` · `name` · `contact` · `kind` · `app`.

## 2. Add a small script to the sheet

1. In the sheet: **Extensions → Apps Script**.
2. Delete what's there and paste:

```javascript
function doPost(e) {
  const d = JSON.parse(e.postData.contents);
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  sheet.appendRow([d.time, d.name, d.contact, d.kind, d.app]);
  return ContentService.createTextOutput("ok");
}
```

3. Click **Save** (the disk icon).

## 3. Publish the script as a web app

1. **Deploy → New deployment**. Click the gear next to "Select type" and choose **Web app**.
2. Execute as: **Me**. Who has access: **Anyone**.
3. Click **Deploy**, then **Authorize access** and allow it with your Google account
   (Google shows a warning for your own unverified script: **Advanced → Go to … (unsafe)** is expected).
4. Copy the **Web app URL** (it ends in `/exec`).

"Anyone" only means anyone with that long secret URL can add a row. It cannot read the sheet.

## 4. Give the URL to the app

1. On [share.streamlit.io](https://share.streamlit.io), open the app's **⋮ → Settings → Secrets**.
2. Paste, with your URL:

```toml
signin_webhook = "https://script.google.com/macros/s/XXXXXXXX/exec"
```

3. Save. The app restarts; the next sign-in appears as a new row in the sheet.

Never put this URL in the code or on GitHub; the Secrets box keeps it private.
