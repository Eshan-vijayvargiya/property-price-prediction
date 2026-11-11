# Sign-ins: Google Sheet → your Excel file

The app's front page asks for a name, a 10-digit mobile number (+91 is fixed) and an optional email,
or "Skip for now". The app runs in the cloud, so it can't write to a file on your laptop. Instead:

```
App (Streamlit Cloud) --POST--> private Google Sheet --GET with your KEY--> Excel on your laptop (Refresh All)
```

Without this setup the sign-in page still works; it just saves nothing.

## 1. Make the sheet

1. Open [sheets.new](https://sheets.new) and name it `Property Price Lab visitors`.
2. Type these headers in row 1, exactly: `time` · `name` · `mobile` · `email` · `app`.

## 2. Add the script

1. In the sheet: **Extensions → Apps Script**.
2. Delete what's there and paste the whole of [`apps_script.gs`](apps_script.gs).
3. On the `const KEY = ...` line, replace `change-me-to-a-long-secret-word` with your own long secret
   (e.g. three random words and a number). Excel uses it to read the sheet. **Never put your real KEY on GitHub.**
4. Click **Save** (the disk icon).

What it does: `doPost` adds each sign-in as a row (stored as plain text, so `+91…` stays a phone number and
nothing can run as a formula). `doGet` gives all rows to Excel, but only when the right KEY is sent.

## 3. Publish the script as a web app

- **First time:** **Deploy → New deployment**, gear icon → **Web app**. Execute as: **Me**. Who has access:
  **Anyone**. **Deploy**, then **Authorize access** (Google warns about your own unverified script:
  **Advanced → Go to … (unsafe)** is expected). Copy the **Web app URL** (ends in `/exec`).
- **Already deployed once?** **Deploy → Manage deployments → ✎ Edit → Version: New version → Deploy**.
  The URL stays the same.

"Anyone" means anyone with the long secret URL can add a row. Reading the rows also needs your KEY.

## 4. Give the URL to the app

On [share.streamlit.io](https://share.streamlit.io): the app's **⋮ → Settings → Secrets**, paste (your URL):

```toml
signin_webhook = "https://script.google.com/macros/s/XXXXXXXX/exec"
```

Save. The app restarts; the next sign-in appears as a new row in the sheet.

## 5. Connect Excel (once)

Check first: open `YOUR-URL?key=YOUR-KEY` in a browser. You should see `[]` (no sign-ins yet) or a list.

1. Excel → **Blank workbook** → **Data → Get Data → From Other Sources → Blank Query**.
2. In the Power Query window: **Home → Advanced Editor**, delete everything, paste
   [`excel_visitors_query.m`](excel_visitors_query.m), and replace the `Url` and `Key` values with yours. **Done**.
3. If Excel asks how to connect: **Edit Credentials → Anonymous → Connect**.
4. In the right panel, rename the query to `Visitors`. **Home → Close & Load**: a table of sign-ins appears,
   newest first, with time in Indian time.
5. **Data → Queries & Connections**, right-click **Visitors → Properties**: tick **Refresh every 10 minutes** and
   **Refresh data when opening the file** → OK.
6. Save it **outside** the GitHub folder, e.g. `Documents\Property Price Lab visitors.xlsx`: it contains your KEY.

From now on **Data → Refresh All** (or just opening the file) pulls the latest sign-ins.

## Already set up the sheet with the first version?

Replace the script with `apps_script.gs` (step 2), rename the headers to `time, name, mobile, email, app`, and
redeploy as a new version (step 3). In the old rows, clear the `email` column: it held the word "mobile".
